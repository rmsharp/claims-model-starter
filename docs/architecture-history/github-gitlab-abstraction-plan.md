> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-04-18 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# GitHub/GitLab Abstraction Plan

**Author:** Session 10 (planning session).
**Baseline commit:** `f97b530` — Phase 4B of the Website Agent complete (289 tests, 96.51% coverage, mypy strict clean across 12 files in `agents/website/`).
**Implementation target:** Sessions 11–14 (four phases, one session each).
**Status when adopted:** Draft; verified by grep against the baseline. Each executor session re-runs the grep verification before starting its phase.

---

## 0. What this document is

This plan describes how to adapt the Website Agent — currently GitLab-only via `python-gitlab` — so it can target **either** GitHub **or** GitLab as the host for the generated model project. The work is staged over four implementation sessions so that each session is one bounded, reversible deliverable, matching `SESSION_RUNNER.md`'s Planning Sessions protocol (grep-based inventory, per-phase DONE criteria, explicit session boundaries).

**This plan is the deliverable of Session 10. Session 10 does not write any `src/` or `tests/` code.** Failure mode #18 (planning-to-implementation bleed) is the primary risk for this session.

---

## 1. Scope

### 1.1 In scope
1. Widen the Website Agent's adapter boundary so a GitHub adapter can plug in alongside the existing `PythonGitLabAdapter`.
2. Fix one latent type-level bug in the current `GitLabClient` Protocol (`project_id: int` is a GitHub-incompatible shape) by widening it to `str` in the same rename pass.
3. Branch the governance CI-template layer (`render_gitlab_ci`) into per-platform variants so the generated repo gets `.gitlab-ci.yml` for GitLab targets and `.github/workflows/ci.yml` for GitHub targets.
4. Add a `PyGithubAdapter` that mirrors the exception-translation discipline of `PythonGitLabAdapter`, with an explicit guard for GitLab-specific concepts that don't map (nested groups).
5. Wire a platform flag into `agents/website/cli.py` so callers can run the fake path or either real adapter from one CLI.

### 1.2 Out of scope (do NOT bundle into this work)
- **Phase 5 (Orchestrator + Adapters + End-to-End)** from `architecture-plan.md:916-931`. Phase 5 is **deferred** until Phase D of this plan lands so that orchestrator code reads the post-rename type names directly and does not pay a second rename cost. See §11 below.
- **LangGraph topology changes.** The `CREATE_PROJECT → SCAFFOLD_BASE → SCAFFOLD_GOVERNANCE → SCAFFOLD_ANALYSIS → SCAFFOLD_TESTS → INITIAL_COMMITS` pipeline and the `RETRY_BACKOFF` self-loop stay exactly as they are in `graph.py:66-81`. No new nodes, no removed nodes, no re-routing.
- **Retry/backoff constants.** `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0` in `state.py:61-62` stay.
- **Governance tier fan-out.** `build_governance_files` in `governance_templates.py:653` stays; only the CI-template subsection changes (see Phase B). Tier 1/2/3 gating, regulatory-framework mapping, and cycle-time cadence are untouched.
- **Schema versioning.** The rename is a **1.0.0 → 2.0.0 major bump of the affected types** in `schemas/registry.py:26-32`. Existing `1.0.0` entries are removed, not carried in parallel, because nothing is persisted between sessions yet (no in-flight runs to protect). See §4.6 for the specific registry diff.
- **The data agent's SQL generation, fairness templates, and model-card content.** These are platform-agnostic and stay as-is.

---

## 2. Current state as of `f97b530`

### 2.1 The adapter boundary already exists

`agents/website/protocol.py:35-59` defines `GitLabClient(Protocol)` with exactly two methods: `create_project(group_path, name, visibility) -> ProjectInfo` and `commit_files(project_id, branch, files, message) -> CommitInfo`. All eight nodes in `agents/website/nodes.py` talk to this Protocol, never to `python-gitlab` directly. The production adapter is `PythonGitLabAdapter` in `agents/website/gitlab_adapter.py:41` (174 lines total); the test double is `FakeGitLabClient` in `agents/website/fake_client.py:41`. `WebsiteAgent.__init__` in `agents/website/agent.py:34` takes a `GitLabClient` instance and builds the graph around it.

**This means ~80% of a second-platform integration is already done.** The remaining 20% is the four traps described below plus the PyGithub adapter itself.

### 2.2 What the three traps are

These are issues Session 9's verbatim user notes did not surface. They were found by re-reading `protocol.py`, `gitlab_adapter.py`, and `nodes.py` during Session 10 evidence-gathering.

#### Trap 1 — `project_id: int` is a protocol-level type mismatch
Search: `project_id\s*[:=]` (grep inventory §4.5 below).

`protocol.py:20` declares `ProjectInfo.id: int` and `protocol.py:55` takes `project_id: int`. `state.py:32` mirrors it. `nodes.py:204,330` threads it through. `schemas/v1/gitlab.py:32` has `project_id: int` on the result schema.

GitLab uses integer project IDs (`gitlab_adapter.py:111: id=int(project.id)`). **GitHub does not.** PyGithub identifies repos by `owner/name` string (e.g. `"acme/subrogation-model"`) or by integer node ID that is private API surface. The GitHub adapter cannot return a meaningful `int` from `create_project`. If we keep `int`, the GitHub adapter must fabricate an integer — either a counter, a hash of the repo name, or a database lookup — and every other layer has to un-fabricate it to do anything useful.

**Clean fix:** widen `ProjectInfo.id` and `commit_files(project_id=...)` from `int` → `str`. The GitLab adapter then stringifies its integer ID (`str(project.id)`) on the way out and parses it back (`int(project_id)`) on the way in — one `int(...)` call in two places, contained. The GitHub adapter stores `"owner/name"` directly.

**This fix is bundled into Phase A** (§6) because it touches the same files as the rename — splitting it off would cost a second PR with the same bisect footprint.

#### Trap 2 — multi-file commit asymmetry
`gitlab_adapter.py:116-155`: `PythonGitLabAdapter.commit_files` is literally one API call:

```python
commit = project.commits.create({
    "branch": branch,
    "commit_message": message,
    "actions": [{"action": "create", "file_path": p, "content": c}, ...],
})
```

GitLab's REST API accepts a single "create-many-files-in-one-commit" call. **GitHub's REST API does not.** The PyGithub equivalent is a four-call git dance:

1. `repo.create_git_blob(content, "utf-8")` per file → N calls for N files
2. `repo.create_git_tree([elements], base_tree=parent_tree)` → one call
3. `repo.create_git_commit(message, tree, [parent_commit])` → one call
4. `repo.get_git_ref("heads/main").edit(sha=commit.sha)` → one call

That is **`2 + N` network calls** and three new failure surfaces: a partial blob upload, a tree-creation failure after successful blobs, and a ref-update race if another process pushes between step 3 and step 4. For a typical tier-1 project this is ~30 governance + base files, so ~32 network round-trips per commit attempt.

**Implications for the plan:**
- `PyGithubAdapter.commit_files` is materially more code than `PythonGitLabAdapter.commit_files`. Expect ~50–70 LOC vs 25.
- Transient failures inside the dance (e.g. a blob upload fails on file 15 of 30) must translate to `RepoClientError` so the existing `RETRY_BACKOFF` self-loop in `graph.py:76-80` handles them uniformly. **The retry unit is the whole `commit_files` call, not individual blobs** — the adapter must not retry internally. If one blob fails, the whole dance fails, the node returns `RETRYING`, and the graph's backoff re-enters with the same pending dict.
- Ref-update races (step 4) are classified as transient and re-tried the same way.

This does not require any graph or node changes. It is entirely contained inside `github_adapter.py`.

#### Trap 3 — GitLab nested groups vs GitHub flat orgs
`cli.py:36` defines `DEFAULT_GROUP = "data-science/model-drafts"`. That is a **nested path** — a GitLab group inside a parent group. GitLab supports arbitrary nesting (`a/b/c/d`). **GitHub does not.** GitHub repos live under one and only one owner: `acme/my-repo`, never `acme/team/my-repo`. `group_path` with a `/` in it is unresolvable on GitHub.

Three resolutions:
- **(a) Hard error** when `namespace` contains `/` and the adapter is `PyGithubAdapter`. Fails fast with a clear message.
- **(b) Silent flatten** — join with `-` (`data-science-model-drafts`). Loses information; confusing for the governance audit trail because the generated `model_registry_entry` records a namespace the real owner doesn't have.
- **(c) Prefix-encode** in the repo name — `ds-mdrafts-<project_name>`. Same problems as (b), more bespoke.

**Recommendation: (a) hard error.** Silent flattening is a surprise; an explicit error forces the caller to flatten their config if they want flat hosting. `PyGithubAdapter.__init__` or `create_project` raises `RepoClientError("nested namespace 'data-science/model-drafts' not supported by GitHub adapter — flatten before passing")`. Test coverage: one `pytest.raises(RepoClientError)` case in `test_github_adapter.py`.

---

## 3. Strategic decision — neutral rename vs parallel schema

### 3.1 The two options on the table

**(A) Neutral rename.** Rename `GitLabClient` → `RepoClient`, `GitLabTarget` → `RepoTarget`, `GitLabProjectResult` → `RepoProjectResult`, `GitLabClientError` → `RepoClientError`, `ProjectNameConflictError` → `RepoNameConflictError`, `FakeGitLabClient` → `FakeRepoClient`, `build_gitlab_project_result` → `build_repo_project_result`, `gitlab_target` state key → `repo_target`, `gitlab_url` field → `host_url`, `group_path` field → `namespace`. `PythonGitLabAdapter` keeps its name (it is concrete and GitLab-specific by definition).

**(B) Parallel schema.** Keep `GitLabClient`, `GitLabTarget`, `GitLabProjectResult` etc. as-is. Add a second `GitHubTarget` schema. Dispatch on concrete type. Inside the agent, store whichever target type was passed.

### 3.2 Decision: option (A), the neutral rename

**The rename footprint is 22 files** (14 source, 8 tests — counted in the grep inventory §5 below). `python-gitlab` is still in `pyproject.toml:23` and `PythonGitLabAdapter` keeps its name, so the concrete GitLab surface is preserved. The neutral names avoid a permanent layer of "GitLab" vocabulary wrapping GitHub code; they also prevent the orchestrator work in Phase 5 (`architecture-plan.md:916`) from hardcoding `GitLabTarget` into orchestrator call sites that would cost a second rename later.

### 3.3 Why not option (B)

- **Parallel schemas create permanent two-branch logic.** Every consumer of `target` becomes `if isinstance(target, GitLabTarget): ... elif isinstance(target, GitHubTarget): ...`. That grows every time a new field diverges.
- **`FakeGitLabClient` stays platform-agnostic** (it never touches a real host), so the "Fake" type is the worst name-to-reality mismatch in the parallel-schema world: a GitHub test would use `FakeGitLabClient` to simulate GitHub. In the rename world it becomes `FakeRepoClient` and the mismatch disappears.
- **The 22-file rename is a one-session job.** Across a tree of 289 tests and mypy-strict discipline, the rename is mechanical: the compiler and tests catch every site. The cost is front-loaded.
- **Phase 5 (orchestrator) will call into the Website Agent via these types.** A rename after Phase 5 lands means re-reading hundreds of new lines in `src/model_project_constructor/orchestrator/`. Doing it now, before Phase 5, is ~2–3× cheaper.

### 3.4 Naming table (proposed)

| Current | Proposed | Lives in | Notes |
|---|---|---|---|
| `GitLabClient` (Protocol) | `RepoClient` | `agents/website/protocol.py:35` | Center of the abstraction. |
| `GitLabClientError` | `RepoClientError` | `agents/website/protocol.py:62` | |
| `ProjectNameConflictError` | `RepoNameConflictError` | `agents/website/protocol.py:66` | For symmetry with the base class rename. |
| `ProjectInfo` | `ProjectInfo` (unchanged name) | `agents/website/protocol.py:19` | **But** `id: int` → `id: str` (Trap 1 fix). |
| `CommitInfo` | `CommitInfo` (unchanged) | `agents/website/protocol.py:28` | Already neutral; no shape change. |
| `FakeGitLabClient` | `FakeRepoClient` | `agents/website/fake_client.py:41` | `FakeProject` dataclass keeps its name. |
| `PythonGitLabAdapter` | `PythonGitLabAdapter` (unchanged) | `agents/website/gitlab_adapter.py:41` | Concrete, GitLab-specific. |
| `GitLabTarget` | `RepoTarget` | `schemas/v1/gitlab.py:12` | Field renames below. |
| `GitLabTarget.gitlab_url` | `RepoTarget.host_url` | `schemas/v1/gitlab.py:14` | `"https://gitlab.example.com"` or `"https://github.com"`. |
| `GitLabTarget.group_path` | `RepoTarget.namespace` | `schemas/v1/gitlab.py:15` | GitLab group path or GitHub owner login. |
| `GitLabProjectResult` | `RepoProjectResult` | `schemas/v1/gitlab.py:28` | `project_id: int` → `project_id: str` (Trap 1 fix). |
| `GovernanceManifest` | `GovernanceManifest` (unchanged) | `schemas/v1/gitlab.py:20` | Already neutral; no change. |
| `schemas/v1/gitlab.py` | `schemas/v1/repo.py` | file rename | Git history preserved via `git mv`. |
| `build_gitlab_project_result` | `build_repo_project_result` | `agents/website/nodes.py:279` | |
| `gitlab_target` (state key) | `repo_target` | `state.py:25,69,74`; `nodes.py:91`; `agent.py:69`; every test that sets state | Pure string key; grep-catchable. |
| `gitlab_target` fixture | `repo_target` fixture | `tests/agents/website/conftest.py:38` | Test plumbing. |
| `--fake-gitlab` CLI flag | `--fake` CLI flag | `cli.py:62-68` | Host-neutral. `--fake-gitlab` stays as a deprecated alias for one phase, then dropped in Phase D. |
| `--gitlab-url` CLI flag | `--host-url` | `cli.py:80-83` | |
| `--group-path` | `--namespace` | `cli.py:76-79` | |
| `website::` thread_id prefix | `website::` (unchanged) | `agent.py:64` | Agent identity, not host identity. |

**The PyGithub adapter class will be `PyGithubAdapter`** (new file `agents/website/github_adapter.py`). It satisfies `RepoClient` structurally, same as `PythonGitLabAdapter`.

---

## 4. Grep-based inventory (baseline: commit `f97b530`)

This is the complete list of sites Phase A will touch. Each phase below re-runs its own verification grep; this section is the **starting point**, not the end state. Executors should re-run these commands inside their own session to catch any drift.

### 4.1 Class and type references

**Search:** `GitLabTarget|GitLabProjectResult|GitLabClient|GitLabClientError|ProjectNameConflictError|ProjectInfo|CommitInfo`

**Hits:** 22 files total.

**Source files (14):**
- `src/model_project_constructor/schemas/registry.py` — lines 30, 31 (registry entries keyed `"GitLabTarget"`, `"GitLabProjectResult"`). **Rename requires new keys** `"RepoTarget"`, `"RepoProjectResult"`. See §4.6 for the registry migration.
- `src/model_project_constructor/schemas/v1/__init__.py` — lines 22–26, 52–54 (imports + `__all__`).
- `src/model_project_constructor/schemas/v1/gitlab.py` — lines 12, 20, 28–36 (the three schema classes). **File itself renames to `schemas/v1/repo.py`.**
- `src/model_project_constructor/agents/website/protocol.py` — lines 19–66 (Protocol definition, dataclasses, error classes).
- `src/model_project_constructor/agents/website/fake_client.py` — lines 1, 6, 17–21, 41, 59–86, 99, 106 (imports, class, method signatures, returns).
- `src/model_project_constructor/agents/website/gitlab_adapter.py` — lines 1, 9–10, 22, 32–37, 41–42, 47, 49, 68, 77, 81, 85, 101, 102, 106, 110, 123, 127, 148, 152, 174 (imports, class, methods, error translation, `__all__`).
- `src/model_project_constructor/agents/website/graph.py` — lines 30, 35 (import + parameter type).
- `src/model_project_constructor/agents/website/nodes.py` — lines 10, 18, 36–40, 53, 80, 103, 106, 209, 279–280, 300, 327 (imports, `make_nodes` parameter, exception catches, `build_gitlab_project_result` signature and body).
- `src/model_project_constructor/agents/website/agent.py` — lines 5, 13, 14, 18, 19, 34, 42, 43, 79, 81, 91 (imports, class signature, `run` signature, `_precondition_result` helper).
- `src/model_project_constructor/agents/website/cli.py` — lines 28–31, 66, 89, 105, 112, 114 (imports, help text, `target = GitLabTarget(...)` construction, `client: GitLabClient` annotation, `FakeGitLabClient()` instantiation).
- `src/model_project_constructor/agents/website/__init__.py` — lines 6–8, 15–42, 56–66 (imports and `__all__`).
- `src/model_project_constructor/agents/website/governance_templates.py` — docstring mention only (no code path). Verify during Phase A.
- `src/model_project_constructor/agents/website/templates.py` — no direct references (confirmed clean).
- `src/model_project_constructor/agents/website/state.py` — indirectly via `gitlab_target` state key (see §4.2).

**Test files (8):**
- `tests/schemas/fixtures.py` — lines 18, 19, 156–163, 178, 182, 188 (`make_gitlab_target`, `make_gitlab_project_result` helpers).
- `tests/schemas/test_envelope_and_registry.py` — lines 19, 20, 27, 97–98, 106–107, 151–162 (registry membership tests that name the string keys).
- `tests/schemas/test_gitlab.py` — lines 9, 10, 15, 20, 22, 28, 33, 36, 37, 70, 87 (class-level tests). **File renames to `test_repo.py`.**
- `tests/agents/website/conftest.py` — lines 9, 11, 38, 39, 48, 49 (fixture factories).
- `tests/agents/website/test_agent.py` — lines 8, 9, 15–18, 31–34, 84–87, 103, 139–142, 160–166, 173–176, 191–194, 206–209 (many `fake_client`, `gitlab_target` fixture references).
- `tests/agents/website/test_nodes.py` — lines 9, 11, 16–19, 28, 31–33, 38, 42, 50, 53–54, 62, 66–67, 72, 96, 122, 155, 180, 203, 233, 287, 291, 316, 319, 350 (extensive).
- `tests/agents/website/test_governance.py` — lines 13, 24, 26, 62–66, 92, 297, 354 (tier fixtures constructing `GitLabTarget`, `.gitlab-ci.yml` assertions — which move to Phase B).
- `tests/agents/website/test_gitlab_adapter.py` — lines 8, 20, 23, 24, 30, 33, 46, 85, 103, 118, 132, 148 (adapter-specific tests; this file stays named `test_gitlab_adapter.py`).
- `tests/agents/website/test_retry.py` — lines 19, 23–26, 34, 41, 46, 52, 64, 68, 96, 100, 128, 130, 146, 149, 160, 178, 192 (retry tests that import Protocol types and the fake client).
- `tests/agents/website/test_fake_client.py` — lines 1, 7, 9, 13, 15, 26, 36, 37, 45, 49, 55, 73, 74, 87, 95 (fake client tests; class name `TestFakeGitLabClient` → `TestFakeRepoClient`).

### 4.2 Field names and state key

**Search:** `gitlab_url|group_path|gitlab_target`

**Hits in source:**
- `schemas/v1/gitlab.py:14-15` — the two field declarations.
- `agents/website/protocol.py:47` — `group_path: str` in `create_project` signature.
- `agents/website/state.py:25,69,74` — `gitlab_target` state key (TypedDict field + `initial_state` parameter + assignment).
- `agents/website/agent.py:30,42,55,60,69` — `gitlab_target` parameter in `WebsiteAgent.run` plus all internal uses.
- `agents/website/fake_client.py:29,38,66,70,78,79` — `FakeProject.group_path` field + `create_project` parameter.
- `agents/website/gitlab_adapter.py:50,59,64,74,79,82,86` — `gitlab_url` + `group_path` uses.
- `agents/website/nodes.py:91,99` — `state["gitlab_target"]`, `target["group_path"]`.
- `agents/website/cli.py:76,80,106,107,124` — typer option names + target construction.

**Hits in tests:** `tests/schemas/fixtures.py:158-159`; `tests/agents/website/conftest.py:38-44`; `tests/agents/website/test_gitlab_adapter.py:34,47,86,105,120,134`; `tests/agents/website/test_governance.py:65-66`; `tests/agents/website/test_retry.py:51,54,96,105,128,134,149,154,160,166,178,182,192,200`; `tests/agents/website/test_nodes.py:31,53,56,72,78,94,103,113,127,139,145,158,164,183,189,206,210,215,236,242,253,262,267`; `tests/agents/website/test_fake_client.py:17,28,31,39,47,51,57,75,76,88,97`.

### 4.3 CI template and adapter references

**Search:** `render_gitlab_ci|\.gitlab-ci\.yml|PythonGitLabAdapter|FakeGitLabClient|FakeProject`

**Hits in source:** `agents/website/governance_templates.py:14` (docstring), `511` (`def render_gitlab_ci`), `683` (call site), `795` (`is_governance_artifact` check). `agents/website/gitlab_adapter.py:41,47,49,174` (class + `__all__`). `agents/website/__init__.py:7,17,18,20,63,64,65` (re-exports). `agents/website/cli.py:28,66,114,119,123` (imports and instantiation). `agents/website/protocol.py:5` (docstring). `agents/website/templates.py:12` (docstring). `agents/website/fake_client.py:6,26,41,59,75,114` (class + dataclass + method).

**Hits in tests:** `test_agent.py:8,15,31,84,103,139,160,162,173,191,206`; `test_fake_client.py:1,7,13,15,26,36,45,55,73,74,87,95`; `test_governance.py:24,62,63,92,297,354`; `test_retry.py:19,41,46,100,130`; `test_gitlab_adapter.py:8,20,33,46,84,85`; `test_nodes.py:9,50,72,96,122,155,180,203,233,310,329`; `test_templates.py:213`; `conftest.py:9,48,49`.

### 4.4 Cross-cutting helpers

**Search:** `is_governance_artifact|build_gitlab_project_result|website::`

**Hits:** `agents/website/governance_templates.py:784,812`; `agents/website/nodes.py:34,279,285,300`; `agents/website/__init__.py:9,27,31,67,73`; `agents/website/agent.py:13,64,74`; `tests/agents/website/test_nodes.py:11,291,316,350`; `tests/agents/website/test_governance.py:13,347-364`.

`is_governance_artifact` stays as the function name. **Phase B adds `.github/workflows/ci.yml` to its recognized set** (`governance_templates.py:795` currently only lists `.gitlab-ci.yml`). `build_gitlab_project_result` renames in Phase A. `website::` thread prefix stays unchanged.

### 4.5 `project_id` type footprint (Trap 1 fix, bundled into Phase A)

**Search:** `project_id\s*[:=]`

**Source sites (`int` that becomes `str`):**
- `schemas/v1/gitlab.py:32` — `project_id: int` on `GitLabProjectResult`.
- `agents/website/state.py:32` — `project_id: int` on `WebsiteState`.
- `agents/website/protocol.py:55` — `project_id: int` parameter on `GitLabClient.commit_files`.
- `agents/website/fake_client.py:95,110` — `project_id: int` on `commit_files` + `get_files`.
- `agents/website/gitlab_adapter.py:119` — `project_id: int` on `commit_files`.
- `agents/website/nodes.py:204,330` — `project_id=state["project_id"]`, `project_id=state.get("project_id", 0)` (second site becomes `""`).
- `agents/website/agent.py:94` — `project_id=0` on `_precondition_result` (becomes `""`).

**Test sites** (will need the new `str` shape): `tests/schemas/fixtures.py:182` (`project_id=12345` → `project_id="12345"`); `tests/agents/website/test_agent.py:26` (`assert result.project_id == 1000` → `== "1000"`); `tests/agents/website/test_nodes.py:38,62,319`; `tests/agents/website/test_fake_client.py:60,79,82,100,103`; `tests/agents/website/test_retry.py:60,72,78`; `tests/agents/website/test_gitlab_adapter.py:150,166`.

**Adapter translation points:** `gitlab_adapter.py:111` currently does `id=int(project.id)` — change to `id=str(project.id)`. `gitlab_adapter.py:125` does `self._gl.projects.get(project_id)` — change to `self._gl.projects.get(int(project_id))` (python-gitlab still wants an int).

### 4.6 Schema registry

**Baseline** (`schemas/registry.py:26-32`):
```python
REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("GitLabTarget", "1.0.0"): v1.GitLabTarget,
    ("GitLabProjectResult", "1.0.0"): v1.GitLabProjectResult,
}
```

**Phase A target:**
```python
REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("RepoTarget", "1.0.0"): v1.RepoTarget,
    ("RepoProjectResult", "1.0.0"): v1.RepoProjectResult,
}
```

**Justification for a clean break (no parallel registration of both keys):** the registry docstring at `schemas/registry.py:7-13` describes minor/major version policy, but the repo currently has nothing persisted between sessions. No envelope referencing `"GitLabTarget"` will exist outside of in-flight test runs in Phase A itself, and those will be updated in the same pass. Adding a parallel `("GitLabTarget", "1.0.0")` entry that aliases to `RepoTarget` would be accommodation for a migration that has no consumer — dead code on day one.

**If this changes** — e.g. a subsequent session lands envelope persistence before Phase A ships — the executor must stop and re-evaluate: either re-scope Phase A to register both keys in parallel for one release, or write a migration script. Mark this as a precondition check in Phase A's §6.2 pre-flight.

### 4.7 Documentation references

Grep for `GitLab`, `.gitlab-ci.yml`, `python-gitlab`, `--fake-gitlab`, `--private-token` across `*.md`:
- `README.md` lines 3, 18, 19, 40, 49, 69, 70, 71, 152, 156, 158, 164 (repo description, phase table, repo layout, getting-started examples).
- `docs/planning/architecture-plan.md` §§4.3 (line 183), 5.4 (347), 8.2 (506), 11 (665), 14 Phase 4 (884), 14 Phase 5 (916).
- `docs/planning/architecture-approaches.md` — historical alternatives document; **does NOT need rewriting** per §1.2 scope boundary.
- `SESSION_NOTES.md` — session history; **does NOT need retroactive updates**, new session entries will use the new names.

**Phase A scope for docs:** `README.md` lines listed above + brief notes in `architecture-plan.md` §§4.3, 5.4 (schema block), 11 (repo structure). Phase B updates the CI filename mentions. Phase D does the final README pass with both `--host gitlab` and `--host github` examples.

### 4.8 Summary: files touched by each phase

| Phase | File count | Of which: source | Of which: tests | Of which: docs |
|---|---|---|---|---|
| **A — Neutral rename + `int`→`str`** | **~28** | 14 | 11 | 3 (README.md + 2 architecture-plan sections) |
| **B — CI template branching** | **~6** | 2 (`governance_templates.py`, `__init__.py` if new exports) | 2 (`test_governance.py`, `test_nodes.py`) | 2 (README.md, architecture-plan §8.2 + §11) |
| **C — `PyGithubAdapter`** | **~4** | 2 new (`github_adapter.py`, update `__init__.py`), 1 update (`pyproject.toml`) | 1 new (`test_github_adapter.py`) | 0 (deferred to Phase D docs pass) |
| **D — CLI `--host` flag + docs** | **~5** | 1 (`cli.py`) | 1 (`test_cli.py`) | 2 (README.md rewrite, architecture-plan Phase 5 section re-reads) + 1 (BACKLOG.md / SESSION_NOTES cross-links) |

The high count for Phase A reflects the front-loaded nature of the neutral rename. Phase B-D are small.

---

## 5. The decision on `PythonGitLabAdapter` naming

Keep `PythonGitLabAdapter` as the class name. It is the concrete GitLab-specific implementation; the name is accurate. Mirror discipline for the new adapter: `PyGithubAdapter` (in `agents/website/github_adapter.py`). **Only the Protocol and the transport-agnostic schema types rename.**

---

## 6. Phase A — Neutral rename + `project_id` widening

**Session:** 11. **Estimated effort:** 1 session. **Risk:** medium — largest footprint, but mechanical; tests and mypy catch drift.

### 6.1 What DONE looks like

- All 22+ files in the grep inventory §4.1–§4.2–§4.3 renamed to the §3.4 table. `agents/website/gitlab_adapter.py` and `tests/agents/website/test_gitlab_adapter.py` keep their filenames; their class name `PythonGitLabAdapter` is unchanged; their imports now use `RepoClient`, `RepoClientError`, `RepoNameConflictError`, `ProjectInfo`, `CommitInfo`.
- `schemas/v1/gitlab.py` moved to `schemas/v1/repo.py` via `git mv` (preserves blame). `schemas/v1/__init__.py` re-exports updated. `schemas/registry.py` keys updated per §4.6.
- `ProjectInfo.id` and `RepoClient.commit_files(project_id=...)` both typed `str`. `PythonGitLabAdapter.create_project` returns `ProjectInfo(id=str(project.id), ...)`; `PythonGitLabAdapter.commit_files` does `self._gl.projects.get(int(project_id))` to keep python-gitlab happy.
- `FakeRepoClient` stringifies `self._next_id` the same way.
- `state.py` renamed `project_id: int` → `project_id: str`. `agent.py:_precondition_result` defaults `project_id=""`.
- `tests/agents/website/conftest.py:38-44` fixture renamed `gitlab_target` → `repo_target`; every test that used the old fixture name updated. Same for `tests/schemas/fixtures.py` `make_gitlab_target` → `make_repo_target`.
- CLI option rename: `--fake-gitlab` → `--fake`, `--gitlab-url` → `--host-url`, `--group-path` → `--namespace`. `--fake-gitlab`, `--gitlab-url`, `--group-path` kept as **hidden deprecated aliases** (one-line typer decorator) until Phase D drops them.
- **All 289 tests pass.** No test is skipped or deleted. If a test was pinning old names, it is updated, not removed.
- `uv run mypy src/model_project_constructor/agents/website/` returns `Success: no issues found in 12 source files` (or more, if new modules were created).
- Coverage stays ≥ 90% (current floor per `pyproject.toml` — confirm the exact value during Phase A pre-flight).

### 6.2 Pre-flight

Before touching any code:
1. `uv run pytest -q` — expected 289 passing, 96.51% coverage.
2. `uv run mypy src/model_project_constructor/agents/website/` — expected `Success`.
3. `git status` — must be clean.
4. Re-run all grep commands in §6.4 below to confirm the inventory matches this plan. If Session 11 finds drift (new files referencing `GitLabTarget` landed between `f97b530` and Phase A start), update the plan in the same commit as Phase A, or close Phase A and re-plan.

### 6.3 Execution order

Order matters because mypy must keep passing between substeps if possible (cleaner bisect):

1. **Schemas first** — `schemas/v1/gitlab.py` → `schemas/v1/repo.py` with class renames and field renames. Update `schemas/v1/__init__.py` re-exports, `schemas/registry.py` keys. Run `uv run pytest tests/schemas/ -q` — this isolates schema-layer breakage.
2. **Protocol + dataclasses** — `agents/website/protocol.py`. This is the only file that can be updated without downstream already-renamed callers, because the `Protocol` is structural. Widening `project_id` to `str` goes in this step.
3. **Fake client** — `agents/website/fake_client.py`. Update class name, imports, method signatures, `id=str(...)` in the return.
4. **Production adapter** — `agents/website/gitlab_adapter.py`. Update imports + method signatures. Preserve existing class name `PythonGitLabAdapter`. Add `int(project_id)` conversion on the way into python-gitlab's commits API.
5. **State + nodes** — `agents/website/state.py`, `agents/website/nodes.py`. Update `gitlab_target` → `repo_target`, `project_id: int` → `str`, `build_gitlab_project_result` → `build_repo_project_result`, all exception class renames. Run `uv run pytest tests/agents/website/test_nodes.py -q` after this step.
6. **Graph + agent + CLI** — `agents/website/graph.py`, `agent.py`, `cli.py`. `cli.py` adds the deprecated aliases for the old flags.
7. **`__init__.py`** — update all re-exports + `__all__` in one pass.
8. **Tests** — `tests/schemas/fixtures.py`, `tests/schemas/test_gitlab.py` → `test_repo.py`, `tests/schemas/test_envelope_and_registry.py`, `tests/agents/website/conftest.py`, then every test file in alphabetical order. Run `uv run pytest -q` between each test-file update is ideal but not mandatory — one final full run at the end is sufficient if intermediate mypy/syntax passes.
9. **Docs** — README.md + architecture-plan.md §4.3 + §5.4 pass. `docs/planning/architecture-plan.md` Phase 4 section at line 884 gets a one-sentence note that the schema names used in the text are the post-rename names.

### 6.4 Verification commands

Run **all** of these; each must match the expected output:

```bash
# 1. Zero occurrences of the old names
grep -rn 'GitLabClient\|GitLabTarget\|GitLabProjectResult\|GitLabClientError\|ProjectNameConflictError\|FakeGitLabClient\|build_gitlab_project_result\|gitlab_target' src/ tests/ | grep -v '^Binary\|gitlab_adapter.py\|PythonGitLabAdapter\|test_gitlab_adapter\|python-gitlab'
# Expected: zero lines of output

# 2. Old field names gone from schemas/CLI
grep -rn 'gitlab_url\|group_path' src/ tests/ | grep -v 'gitlab_adapter\.py'
# Expected: zero lines of output

# 3. project_id type is now str everywhere it's annotated
grep -rn 'project_id\s*:\s*int' src/ tests/
# Expected: zero lines of output

# 4. Tests pass
uv run pytest -q
# Expected: 289 passed (same as baseline — no new tests in Phase A)

# 5. mypy strict is clean
uv run mypy src/model_project_constructor/agents/website/
# Expected: Success: no issues found in 12 source files

# 6. Coverage holds
uv run pytest --cov=src/model_project_constructor/agents/website --cov-fail-under=90
# Expected: pass with ≥ 96% (baseline 96.51%; Phase A changes only names/types)

# 7. Fake CLI smoke test (tier 1, 2, 3 fixtures)
uv run python -m model_project_constructor.agents.website --intake tests/fixtures/tier1_intake.json --data tests/fixtures/sample_datareport.json --fake
uv run python -m model_project_constructor.agents.website --intake tests/fixtures/tier2_intake.json --data tests/fixtures/sample_datareport.json --fake
uv run python -m model_project_constructor.agents.website --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json --fake
# Expected: each prints status=COMPLETE and a non-empty file tree

# 8. Deprecated flag aliases still work
uv run python -m model_project_constructor.agents.website --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json --fake-gitlab
# Expected: same as above (deprecation warning optional)
```

### 6.5 Rollback

Phase A is one commit (or at most one commit per numbered substep in §6.3). If any verification command fails at close-out, `git reset --hard HEAD~N` and fix in a follow-up session. Do NOT land a partial rename — mypy will fail and the next session inherits a broken state.

### 6.6 Session boundary

**This phase is one session. Close out when done. Session 12 starts Phase B.**

Do NOT start Phase B even if Phase A finishes early. Failure mode #18 is the specific risk.

---

## 7. Phase B — CI template branching

**Session:** 12. **Estimated effort:** 1 session. **Risk:** low — small surface.

### 7.1 What DONE looks like

- `agents/website/governance_templates.py:511 render_gitlab_ci()` is joined by a sibling `render_github_actions_ci() -> str` that emits YAML equivalent in shape to the existing GitLab CI template (stages: `lint`, `test`, `governance`; installs `uv`; runs `ruff check`, `pytest`, `python -c "import json; json.load(open('governance/model_registry.json'))"`).
- `build_governance_files` in `governance_templates.py:653` takes a new parameter `ci_platform: Literal["gitlab", "github"]` (default `"gitlab"` for backwards compatibility). When `"gitlab"` it emits `.gitlab-ci.yml`; when `"github"` it emits `.github/workflows/ci.yml`. The `.pre-commit-config.yaml` is emitted in both cases, unchanged.
- `is_governance_artifact` in `governance_templates.py:784` is extended: `.github/workflows/ci.yml` joins the recognized set alongside `.gitlab-ci.yml`. The classifier is platform-agnostic — it recognizes BOTH filenames regardless of which platform actually produced the repo, because the classifier is also used by executor-side tools that may inspect cloned repos.
- `scaffold_governance` node in `agents/website/nodes.py:141` reads `ci_platform` from state (new key — see next bullet) and forwards it to `build_governance_files`. Default `"gitlab"` preserved.
- `state.py` gets a new field `ci_platform: Literal["gitlab", "github"]` (default `"gitlab"`). Set by the CLI in Phase D; for now always `"gitlab"` unless a test overrides it.
- `WebsiteAgent.__init__` or `WebsiteAgent.run` takes an optional `ci_platform` parameter (recommend: constructor parameter, so the agent is "configured for a platform" once and all runs use it). Defaults `"gitlab"`.
- `test_governance.py` grows a `@pytest.mark.parametrize("ci_platform", ["gitlab", "github"])` decorator on at least one tier-3 exercise. For the `"github"` case, assert: (a) `.github/workflows/ci.yml` exists in `files_created`, (b) `.gitlab-ci.yml` does NOT, (c) `is_governance_artifact(".github/workflows/ci.yml") is True`, (d) regulatory mapping is unchanged vs the GitLab path. Shape: ~5–10 new test cases.
- `test_nodes.py:310,329` governance-artifact assertions updated so the test also passes on the GitHub CI path (parametrize or add a second test).

### 7.2 Pre-flight

1. Phase A closed out — `grep -rn 'GitLabClient' src/` returns zero hits (other than the concrete adapter file).
2. Baseline tests green: `uv run pytest -q` → 289+ passing.
3. `uv run mypy` clean.

### 7.3 Design notes

- **Do NOT infer `ci_platform` from the adapter class.** That couples artifact generation to the adapter and makes it impossible to scaffold a GitHub project with `FakeRepoClient` for testing, which we need to do for the Phase B unit tests. Make it an explicit parameter.
- **Do NOT merge `render_gitlab_ci` and `render_github_actions_ci` behind a single renderer.** The YAML shapes are different enough (top-level `stages:` in GitLab vs `jobs:` in GitHub Actions) that a shared abstraction would be more code than two parallel functions. Keep them independent.
- The `GovernanceManifest.artifacts_created` list ends up platform-specific (contains either `.gitlab-ci.yml` or `.github/workflows/ci.yml`, never both). Test the count is unchanged across platforms at each tier.

### 7.4 Verification commands

```bash
# 1. Both CI renderers exist
grep -n 'def render_gitlab_ci\|def render_github_actions_ci' src/model_project_constructor/agents/website/governance_templates.py
# Expected: two lines

# 2. is_governance_artifact recognizes both
grep -n "\.github/workflows/ci\.yml\|\.gitlab-ci\.yml" src/model_project_constructor/agents/website/governance_templates.py
# Expected: at least two hits including in is_governance_artifact body

# 3. New parametrized governance tests pass
uv run pytest tests/agents/website/test_governance.py -v -k "ci_platform"
# Expected: all parametrized cases pass

# 4. Tier-1/2/3 exercises cover both platforms
uv run pytest tests/agents/website/test_governance.py -v
# Expected: all tier tests pass on BOTH platform values

# 5. Full suite still green
uv run pytest -q
# Expected: 289 + N passing (N = new parametrized cases)

# 6. mypy clean
uv run mypy src/model_project_constructor/agents/website/
# Expected: Success
```

### 7.5 Session boundary

**One session. Close out. Do NOT start Phase C in the same session.**

---

## 8. Phase C — `PyGithubAdapter`

**Session:** 13. **Estimated effort:** 1 session. **Risk:** medium — the 4-call git dance (Trap 2) is new code with new failure modes.

### 8.1 What DONE looks like

- New file `src/model_project_constructor/agents/website/github_adapter.py` (~200 LOC, larger than `gitlab_adapter.py` due to the git dance).
- `class PyGithubAdapter(RepoClient)` with:
  - `__init__(self, *, host_url: str = "https://api.github.com", private_token: str)` — wraps `github.Github(private_token, base_url=host_url)`. For GitHub Enterprise, `host_url` is the enterprise API URL. For github.com, it's `https://api.github.com`.
  - `create_project(*, group_path: str, name: str, visibility: str) -> ProjectInfo`:
    - **Nested group guard** (Trap 3): if `"/" in group_path`, raise `RepoClientError(f"nested namespace {group_path!r} not supported by GitHub adapter — flatten before passing")`.
    - Resolve owner: `org = self._gh.get_organization(group_path)` (try org first), falling back to `user = self._gh.get_user(group_path)` if `UnknownObjectException` on the org call.
    - `repo = org.create_repo(name=name, private=(visibility != "public"))`. GitHub has no "internal" — map `"internal"` to `private=True`.
    - On `GithubException` with `status == 422` and `"name already exists"` substring in the body: `raise RepoNameConflictError(name)`.
    - On any other `GithubException`: `raise RepoClientError(...)`.
    - Return `ProjectInfo(id=repo.full_name, url=repo.html_url, default_branch=repo.default_branch or "main")`.
  - `commit_files(*, project_id: str, branch: str, files: dict[str, str], message: str) -> CommitInfo`:
    - `repo = self._gh.get_repo(project_id)` (`project_id` is the `"owner/name"` string set by `create_project`).
    - Get parent: `ref = repo.get_git_ref(f"heads/{branch}")`; `parent_commit = repo.get_git_commit(ref.object.sha)`.
    - Create blobs: `blob_entries = [repo.create_git_blob(content, "utf-8") for content in files.values()]` — one API call per file.
    - Build tree elements: for each path + blob, `InputGitTreeElement(path=path, mode="100644", type="blob", sha=blob.sha)`. **Sort by path** to match `gitlab_adapter.py`'s behavior.
    - Create tree: `tree = repo.create_git_tree(tree_elements, base_tree=parent_commit.tree)`.
    - Create commit: `commit = repo.create_git_commit(message, tree, [parent_commit])`.
    - Update ref: `ref.edit(sha=commit.sha)`.
    - Return `CommitInfo(sha=commit.sha, files_committed=sorted(files))`.
    - **Every step wraps a try/except GithubException → RepoClientError** so the RETRY_BACKOFF loop handles transient errors identically to the GitLab path.
- `pyproject.toml` `[project.optional-dependencies] agents` list gains `"PyGithub>=2,<3"` alongside `"python-gitlab>=4"`.
- `agents/website/__init__.py` re-exports `PyGithubAdapter`.
- New file `tests/agents/website/test_github_adapter.py` (~10 tests mirroring `test_gitlab_adapter.py`):
  1. Import smoke test (module imports without error).
  2. Adapter has `create_project` and `commit_files` as callables.
  3. Constructor does not make a network call (PyGithub defers until first API hit — verify by constructing with a bogus URL).
  4. `_is_name_conflict` classification (or inline equivalent): 422 + "name already exists" → conflict; other statuses → not.
  5. Nested namespace guard: `create_project(group_path="a/b", ...)` raises `RepoClientError`.
  6. `MagicMock`-based exception translation for `create_project`: mock the `Github` client so `get_organization` → `get_user` fallback is exercised.
  7. `MagicMock`-based test for `commit_files` happy path: stub `repo.create_git_blob`, `create_git_tree`, `create_git_commit`, `ref.edit` and assert all four are called in order with the expected inputs.
  8. `MagicMock`-based test for `commit_files` blob failure: blob call raises `GithubException` → `RepoClientError` bubbles up.
  9. `MagicMock`-based test for `commit_files` tree failure.
  10. `MagicMock`-based test for `commit_files` ref.edit failure.
- **No live-network tests.** Same discipline as `test_gitlab_adapter.py` per `gitlab_adapter.py:14-18` docstring (live-GitLab tests are a Phase 5 concern).

### 8.2 PyGithub type stub check

Before writing the adapter, run `uv run python -c "import github; print(github.__version__)"` to confirm install. Then:
```bash
uv run mypy -c "import github; g: github.Github = github.Github()"
```
If mypy complains about missing stubs, PyGithub lacks type stubs and the adapter file needs a module-level `# type: ignore[import-untyped]` on the import. If it's clean, no ignore is needed. (`python-gitlab` DID ship stubs per Session 9 handoff — `PyGithub` historically has NOT, so expect to need the ignore.)

### 8.3 Pre-flight

1. Phase B closed out — `render_github_actions_ci` exists, `ci_platform` parameter works.
2. `PyGithub` not yet installed — this phase installs it via `uv sync` after editing `pyproject.toml`.

### 8.4 Verification commands

```bash
# 1. PyGithub installed
uv run python -c "import github; print(github.__version__)"
# Expected: some 2.x version

# 2. Adapter module imports
uv run python -c "from model_project_constructor.agents.website import PyGithubAdapter; print(PyGithubAdapter)"
# Expected: <class '...PyGithubAdapter'>

# 3. New tests all pass
uv run pytest tests/agents/website/test_github_adapter.py -v
# Expected: ~10 passing

# 4. Full suite still green (including new adapter tests)
uv run pytest -q
# Expected: baseline + B + C total passing

# 5. mypy clean
uv run mypy src/model_project_constructor/agents/website/
# Expected: Success (may need one `# type: ignore[import-untyped]` on `import github`)

# 6. Coverage floor
uv run pytest --cov=src/model_project_constructor/agents/website --cov-fail-under=90
# Expected: pass. github_adapter.py coverage will be lower than gitlab_adapter.py's 85% because it has more branches; acceptable if total suite stays ≥ 90%.
```

### 8.5 Session boundary

**One session. Close out. Do NOT start Phase D.**

---

## 9. Phase D — CLI `--host` flag + docs

**Session:** 14. **Estimated effort:** 1 session (small). **Risk:** low.

### 9.1 What DONE looks like

- `agents/website/cli.py` gains a `--host` typer option: `typer.Option("--host", help="Repository host: 'gitlab' or 'github'.")` with default `"gitlab"`. Exit code 2 if invalid.
- Rewire the adapter selection:
  - If `fake` → `FakeRepoClient()`.
  - Elif `host == "gitlab"` → lazy-import `PythonGitLabAdapter`, construct with `host_url` and `private_token`.
  - Elif `host == "github"` → lazy-import `PyGithubAdapter`, construct with `host_url` (default `"https://api.github.com"`) and `private_token`.
  - Else → exit 2 with a helpful error.
- `ci_platform` state field (from Phase B) derived from `host` and passed into `WebsiteAgent` — when `host == "gitlab"`, `ci_platform = "gitlab"`; when `host == "github"`, `ci_platform = "github"`; when `host` omitted (fake path), default is `"gitlab"` for backwards compatibility. A CLI flag `--ci-platform` overrides this for the fake path (useful for testing GitHub CI emission against a fake client).
- `--fake-gitlab`, `--gitlab-url`, `--group-path` deprecated aliases from Phase A are **removed**. Update the deprecation note in Phase A's README additions.
- `tests/agents/website/test_cli.py` grows parametrized cases:
  - `--host gitlab --fake` → uses `FakeRepoClient`, emits `.gitlab-ci.yml`.
  - `--host github --fake` → uses `FakeRepoClient`, emits `.github/workflows/ci.yml`.
  - `--host gitlab --private-token fake-token` → would call `PythonGitLabAdapter` (monkeypatched).
  - `--host github --private-token fake-token` → would call `PyGithubAdapter` (monkeypatched).
  - `--host bogus` → exit 2.
- `README.md` full rewrite of the getting-started section with **both** GitLab and GitHub examples side-by-side. Phase-table row 4B updated to reflect the abstraction landing.
- `docs/planning/architecture-plan.md` §14 Phase 5 section (line 916) re-read and updated: the orchestrator work now operates on `RepoTarget` / `RepoProjectResult`, not `GitLabTarget` / `GitLabProjectResult`. One-paragraph amendment noting that the abstraction plan (this doc) landed before Phase 5.
- **Session 15+ can now start Phase 5** of the original architecture plan (orchestrator + adapters + end-to-end) without having to pay any `GitLab*` rename cost.

### 9.2 Pre-flight

1. Phase C closed out — `PyGithubAdapter` importable, tests green.
2. Both adapters lazy-importable without eager side effects.

### 9.3 Verification commands

```bash
# 1. CLI help advertises --host
uv run python -m model_project_constructor.agents.website --help | grep -- '--host'
# Expected: a line mentioning --host

# 2. Fake GitLab path still works
uv run python -m model_project_constructor.agents.website --host gitlab --fake --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json
# Expected: status=COMPLETE, .gitlab-ci.yml in file tree

# 3. Fake GitHub path works (NEW)
uv run python -m model_project_constructor.agents.website --host github --fake --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json
# Expected: status=COMPLETE, .github/workflows/ci.yml in file tree, no .gitlab-ci.yml

# 4. Deprecated flags removed
uv run python -m model_project_constructor.agents.website --fake-gitlab --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json 2>&1 | grep -i 'no such option\|unrecognized'
# Expected: match (flag is gone)

# 5. Test CLI cases green
uv run pytest tests/agents/website/test_cli.py -v
# Expected: all parametrized cases pass

# 6. Full suite green
uv run pytest -q

# 7. README examples check
grep -n 'host github\|host gitlab' README.md
# Expected: at least one of each

# 8. Phase 5 can be unblocked — architecture-plan.md Phase 5 references the new names
grep -n 'RepoTarget\|RepoProjectResult' docs/planning/architecture-plan.md
# Expected: at least one hit each (after the §14 Phase 5 amendment)
```

### 9.4 Session boundary

**One session. Close out. Session 15+ starts Phase 5 of the original architecture plan.**

---

## 10. Do-not-change list

This plan is a rename and extension. The following are **explicitly preserved** across all four phases:

1. **LangGraph topology.** `agents/website/graph.py:66-81` wiring: `CREATE_PROJECT → SCAFFOLD_BASE → SCAFFOLD_GOVERNANCE → SCAFFOLD_ANALYSIS → SCAFFOLD_TESTS → INITIAL_COMMITS`, `INITIAL_COMMITS → RETRY_BACKOFF → INITIAL_COMMITS` self-loop, `route_after_create`, `route_after_commit`. **No new nodes. No removed nodes. No re-routing.**
2. **Retry constants.** `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0`, `MAX_NAME_CONFLICT_ATTEMPTS = 5` in `state.py:60-62`.
3. **The `sleep` injection pattern.** `make_nodes(client, *, sleep=...)` in `nodes.py:79-83`. Tests rely on this. Production uses `time.sleep`.
4. **The `files_pending` accumulator.** All four scaffold nodes (`scaffold_base`, `scaffold_governance`, `scaffold_analysis`, `scaffold_tests`) merge into the same dict and `INITIAL_COMMITS` flushes it once. See the state docstring at `state.py:1-12`.
5. **Governance tier fan-out.** `_tier_at_least` helper + every branch in `build_governance_files` at `governance_templates.py:653-758`. Tier 1/2/3 gating, consumer/fairness flags, regulatory-framework mapping, cycle-time cadence text. Phase B only adds a second CI renderer; it does not change any tier-gated logic.
6. **`GovernanceManifest` shape.** `schemas/v1/gitlab.py:20-26` fields (`model_registry_entry`, `artifacts_created`, `risk_tier`, `cycle_time`, `regulatory_mapping`). Name `GovernanceManifest` is neutral and survives the rename.
7. **`is_governance_artifact` externally visible behavior.** Phase B adds `.github/workflows/ci.yml` to the recognized set — additive, not replacing `.gitlab-ci.yml`.
8. **The precondition guard.** `WebsiteAgent.run` in `agent.py:52-62` refuses `intake.status != COMPLETE` and `data.status != COMPLETE` with a `FAILED` result. Helper `_precondition_result` unchanged in behavior.
9. **The Phase 4A/4B test fixtures** (`tier1_intake.json`, `tier2_intake.json`, `subrogation_intake.json`, `sample_datareport.json`). Intake/data reports are platform-agnostic and need no change.
10. **`FakeGitLabClient` internals.** Logic preserved verbatim. Only the class name changes (`→ FakeRepoClient`), the imported error types change, and the `id` field stringifies.
11. **Docstrings referencing "GitLab"** in modules other than `gitlab_adapter.py` get updated; inside `gitlab_adapter.py`, docstrings still describe GitLab because the module IS the GitLab concrete implementation.
12. **The `website::` thread_id prefix** in `agent.py:64`. It identifies the agent, not the host.

---

## 11. Phase 5 ordering decision

The original architecture plan at `docs/planning/architecture-plan.md:916-931` describes **Phase 5: Orchestrator + Adapters + End-to-End** as one session that builds `src/model_project_constructor/orchestrator/` with `pipeline.py`, `adapters.py`, and `checkpoints.py`, plus an end-to-end test against a real GitLab instance.

**This plan defers Phase 5 until Phase D closes.** Justification:

1. **Orchestrator code will import `RepoTarget` / `RepoProjectResult`.** If Phase 5 lands first, those imports hardcode `GitLabTarget` / `GitLabProjectResult`, and the rename executor pays an extra cost updating orchestrator call sites.
2. **The end-to-end test** in the Phase 5 description uses `GitLabTarget` via the adapter. Post-abstraction, the same test can run against either adapter — meaning Phase 5's end-to-end test coverage is *better* if it lands after the abstraction, not worse.
3. **Phase 5's "1 session" estimate assumes no rename friction.** The original plan was written before the GitHub/GitLab abstraction was on the table. Running Phase 5 first and then the abstraction is strictly more work than the reverse order.

**Order of sessions from here:**
- Session 11: Phase A of this plan (rename + `int`→`str`).
- Session 12: Phase B of this plan (CI template branching).
- Session 13: Phase C of this plan (`PyGithubAdapter`).
- Session 14: Phase D of this plan (CLI `--host` flag + docs).
- Session 15: Phase 5 of the original architecture plan (orchestrator + adapters + end-to-end).
- Session 16: Phase 6 of the original architecture plan (production hardening).

**Total through Phase 6: ~6 more sessions after this planning session.** The original architecture-plan.md §14 total of 9 sessions (1 planning + 8 implementation) therefore grows to 13: 2 planning (original + this one) + 11 implementation. If the user prefers to skip the GitHub abstraction and stay on Phase 5, this plan can be shelved and Phase 5 can proceed with `GitLab*` names; the tradeoff is the expensive post-Phase-5 rename described above.

---

## 12. Provenance: the missing point #1

Session 9's handoff captured the user's GitHub/GitLab abstraction notes verbatim, starting at numbered point #2. The session note at `SESSION_NOTES.md:148` reads: *"the user's numbering starts at 2 — point 1 wasn't included in the message."*

Session 10 learned from the user at the start of this session that the notes came from a `/btw` (by-the-way) request whose response was truncated. The original question was paraphrased as: *"what can be done to allow this project's product to use either GitHub or GitLab?"*

**Point #1 is reconstructed for this plan as:**

> **1. The `GitLabClient` Protocol in `agents/website/protocol.py` is already the adapter boundary.** It defines two methods (`create_project`, `commit_files`) that describe host-agnostic concepts; the pattern allows plugging in any concrete adapter. Rename the Protocol to `RepoClient` (or `GitHostClient`) to make its neutrality explicit. Widen `ProjectInfo.id` from `int` to `str` in the same pass because GitHub does not use integer repo IDs (python-gitlab does). The rest of the work (points 2–5 below) is the schema rename, the CI template branch, the `PyGithubAdapter`, and the tests.

The reconstruction is marked as such in this document; if the user ever regenerates the original response, this section should be updated with the verbatim text.

**Other traps Session 9 did not surface** — multi-file commit asymmetry (Trap 2, §2.2) and GitLab nested groups (Trap 3, §2.2) — were discovered during Session 10's grep-and-read pass. Both are documented in this plan in case the original point #1 did not cover them.

---

## 13. Open questions (for a future session to resolve)

These are not blocking for Phases A–D but should be answered before Phase 5 (orchestrator) lands:

1. **GitHub enterprise hosting.** Does the target deployment use github.com or GitHub Enterprise? If enterprise, `host_url` points at `https://github.<customer>.com/api/v3` and `PyGithubAdapter` needs to handle the trailing `/api/v3`. The adapter as specified in §8 takes `host_url` as-is and passes it to `github.Github(base_url=...)`, which is the documented PyGithub pattern — should work for both, but needs a real enterprise verification in Phase 5's end-to-end test.
2. **Org vs user namespace.** `PyGithubAdapter.create_project` tries `get_organization(group_path)` first, falls back to `get_user(group_path)` on `UnknownObjectException`. Is the claims org using a GitHub organization (expected) or a personal/user account (unlikely, but possible in early testing)? The fallback handles both; no design change, just a deployment-time verification.
3. **Branch default.** New GitHub repos use `main` by default since 2020. GitLab also defaults to `main` in recent versions. The agent's `default_branch` field reads what the host returns. Are there any existing repos on either host with `master` as default? If so, the commit-files dance in `PyGithubAdapter` resolves `ref.get_git_ref("heads/main")` and will fail — update the ref name from `ProjectInfo.default_branch`.
4. **Visibility mapping.** GitLab has `private | internal | public`. GitHub has `private | public` (plus org-internal which PyGithub exposes as `visibility="internal"` on newer versions). Phase C maps `"internal"` → `private=True` as a conservative default. Is this the right mapping for the claims org's policy? If there's a distinction between "private to org" and "private to team" that matters, surface it before Phase 5.
5. **The missing original point #1 from the `/btw` response.** If the user regenerates it, §12 of this document should be updated with the verbatim text, and any disagreement with the reconstruction should be raised as a new planning amendment rather than a silent code change in Phases A–D.

---

## 14. Close-out protocol for each executor session

Each of Sessions 11–14 MUST:

1. **Phase 0** — read `SAFEGUARDS.md`, `SESSION_NOTES.md` ACTIVE TASK, this plan's relevant §6/§7/§8/§9 section, and run `git status`.
2. **Phase 1B** — write a Session N stub to `SESSION_NOTES.md` before touching any code.
3. **Execute** — follow the Execution order in §6.3 (or the equivalent for later phases). Run verification commands at every checkpoint.
4. **Phase 3A** — evaluate the previous session's handoff (Session 11 evaluates Session 10's plan; Session 12 evaluates Session 11's implementation; etc.).
5. **Phase 3B–3F** — self-assess, document learnings, write the next handoff, commit, report, STOP.
6. **Do NOT bundle two phases.** Close out at the end of the phase even if time remains. Failure mode #18.

Each session's DONE criterion is the verification block in its phase section of this plan. Any verification command failing = session not DONE; fix in the same session or roll back and re-plan.

---

## 15. Risk register

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | Rename introduces test drift mypy doesn't catch (e.g. dict key typo in a test that uses `.get`) | Medium | §6.4 verification command 1 greps for old names across `src/ tests/`. |
| 2 | `schemas/registry.py` rename breaks an envelope test that pins the string key | High | §4.6 documents the registry migration explicitly; Phase A touches `tests/schemas/test_envelope_and_registry.py:97-107` in the same commit as the registry change. |
| 3 | PyGithub lacks type stubs, mypy fails on import | Medium | §8.2 pre-flight check; one `# type: ignore[import-untyped]` acceptable. |
| 4 | `PyGithubAdapter.commit_files` 4-call dance races another push between commit and ref.edit | Low | Translate GithubException on ref.edit to `RepoClientError`; retry loop handles it via RETRY_BACKOFF. Document in `github_adapter.py` module docstring. |
| 5 | `is_governance_artifact` over-broadens and classifies unrelated `.yml` files | Low | Phase B uses an exact-path check, not a pattern match; test covers both inclusion and non-inclusion. |
| 6 | Phase 5 starts before this plan closes, hardcoding old names | High if not tracked | This plan §11 explicitly defers Phase 5 until Phase D. Session 10's handoff will update `SESSION_NOTES.md` ACTIVE TASK to point at Phase A. |
| 7 | A later session adds envelope persistence and expects `"GitLabTarget"` keys in the registry | Low | §4.6 notes the "no parallel registration" decision is conditional; if persistence lands, Phase A pre-flight must re-evaluate. |
| 8 | `--fake-gitlab` deprecation alias from Phase A confuses users who skipped Phase D | Very low | Phase D removes the alias and updates README. Only one release window has both flags. |

---

## 16. Why this plan is a single document, not four

A previous version of this plan could have split into four shorter phase-specific documents. This version keeps everything in one file because:

1. **The rename has cross-phase invariants.** The do-not-change list (§10), the strategic decision (§3), and the Phase 5 ordering argument (§11) apply to every phase and would be duplicated across four documents.
2. **The grep inventory (§4) is load-bearing for Phase A but informative for B–D.** Splitting the inventory across documents would duplicate the big sections or require cross-document references; one document is cleaner.
3. **Executors read one document per session anyway.** Each executor reads this plan + the relevant phase section. The plan is long but navigable via §numbers; executors don't read end-to-end every session.

If Sessions 11–14 find this single-document structure unwieldy, the first executor can split it. Not a blocking concern for Session 10.

---

*End of plan.*
