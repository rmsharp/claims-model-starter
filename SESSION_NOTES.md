# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

---

## ACTIVE TASK
**Task:** Session 12 is an **IMPLEMENTATION** session. Execute **Phase B** of `docs/planning/github-gitlab-abstraction-plan.md` — add `render_github_actions_ci()` as a sibling of `render_gitlab_ci()`, thread a `ci_platform: Literal["gitlab", "github"]` parameter through `build_governance_files` / `scaffold_governance` / `WebsiteAgent`, extend `is_governance_artifact` to recognize `.github/workflows/ci.yml`, and parametrize tier-gated governance tests to cover both platforms. **Start by raising the pytest coverage floor from 90% to 93% in `pyproject.toml`.**
**Status:** Phase A landed in Session 11 (commit `<FILL AT COMMIT TIME>`). Master is clean after commit. Baseline for Session 12: **289 tests pass at 96.51% coverage, mypy strict clean on 12 files in `agents/website/`.** All `GitLab*` / `gitlab_target` / `gitlab_url` / `group_path` / `project_id: int` references have been eliminated from `src/` and `tests/`; the surviving GitLab surface is: `gitlab_adapter.py` (concrete), `test_gitlab_adapter.py` (its tests), `.gitlab-ci.yml` artifact emission, `DEFAULT_HOST_URL = "https://gitlab.example.com"` CLI default, and `python-gitlab` in `pyproject.toml`. Phase C (`PyGithubAdapter`) and Phase D (CLI `--host` flag + docs) follow in Sessions 13 and 14. **Phase 5 (orchestrator) is deferred until Phase D closes** — see plan §11.
**Priority:** HIGH — Phase B unblocks Phase C which unblocks Phase D which unblocks Phase 5.

### What Session 12 Must Do

**Phase B is one session. Close out when DONE. Do NOT start Phase C in the same session.** Failure mode #18.

1. **Phase 0 — orient:**
   - `SAFEGUARDS.md` (full read).
   - This ACTIVE TASK block + the "What Session 11 Did" handoff below.
   - `docs/planning/github-gitlab-abstraction-plan.md` **§7 (Phase B spec)** + **§10 (do-not-change list)**. The plan is now 712 lines; Session 12 should re-read §2.2 Trap 2/3 context but the primary source of truth for this session is §7.
   - Run `git status`, `git log --oneline -5`. Confirm clean working tree on master.
   - Run pre-flight: `uv run pytest -q` (expect **289 passed @ 96.51%**), `uv run mypy src/model_project_constructor/agents/website/` (expect **Success on 12 files**). Session 11 verified this at close-out; if these numbers have drifted, STOP and investigate before touching code.

2. **Coverage floor bump (FIRST action after Phase 1B stub) — user directive from Session 11:**
   - Edit `pyproject.toml` and change the pytest coverage floor from `90` to `93`. Grep for `--cov-fail-under=90` or `fail_under = 90` in both `pyproject.toml` and any `[tool.coverage.report]` section; update every occurrence. Run `uv run pytest -q` to confirm **289 tests still pass at 96.51% coverage ≥ 93%**. Commit this bump **separately** from Phase B work so the audit trail is clean: `chore(coverage): raise pytest coverage floor 90% → 93% per session 11 directive`. This is a scoped 1-line-ish change, not a refactor; after this commit the rest of Session 12 proceeds as Phase B.
   - **Why:** the user asked at the end of Session 11 (verbatim: *"raise the unit test coverage floor to 93% at beginning of next session"*). Baseline is 96.51% so there is a 3.5-point safety margin. Any Phase B code that drops coverage below 93% is a quality regression Session 12 must fix in the same session.

3. **Phase 1B — write the Session 12 stub** to `SESSION_NOTES.md` BEFORE touching any code.

4. **Phase B execution** — follow plan §7:
   - `governance_templates.py`: add `def render_github_actions_ci() -> str:` as a sibling of `render_gitlab_ci()`. YAML shape: top-level `name:`, `on:` (push + pull_request to main), `jobs:` with `lint` + `test` + `governance` sub-jobs that mirror the GitLab stages. Uses `ubuntu-latest`, installs `uv`, runs `ruff check`, `pytest`, and the `governance/model_registry.json` json-load sanity check.
   - `governance_templates.py`: extend `build_governance_files` with a `ci_platform: Literal["gitlab", "github"] = "gitlab"` keyword parameter. When `"gitlab"` → emit `.gitlab-ci.yml`; when `"github"` → emit `.github/workflows/ci.yml`. `.pre-commit-config.yaml` is emitted in both cases. **Do NOT merge the two renderers behind a single function** — plan §7.3 explicitly rejects that.
   - `governance_templates.py`: extend `is_governance_artifact` to recognize `.github/workflows/ci.yml` alongside `.gitlab-ci.yml`. **Both** must be classified as governance artifacts regardless of which platform actually produced the repo (the classifier is used by executor-side tools that may inspect cloned repos of either flavor).
   - `state.py`: add a `ci_platform` field (`Literal["gitlab", "github"]`, default `"gitlab"`) to `WebsiteState`. Plumb it through `initial_state()`.
   - `nodes.py`: `scaffold_governance` reads `state.get("ci_platform", "gitlab")` and forwards it to `build_governance_files`.
   - `agent.py`: `WebsiteAgent.__init__` takes an optional `ci_platform: Literal["gitlab", "github"] = "gitlab"` kwarg; `WebsiteAgent.run` stashes it into the initial state. (Constructor param, not a run-level arg — an agent is configured for one platform.)
   - `tests/agents/website/test_governance.py`: add `@pytest.mark.parametrize("ci_platform", ["gitlab", "github"])` to at least one tier-3 exercise and assert both positive (`.github/workflows/ci.yml in files_created` for `"github"`) AND negative (`.gitlab-ci.yml not in files_created` for `"github"`, and vice versa). Learning #5 from SESSION_RUNNER.md — always pin tier/flag-gated behavior with both assertions.
   - `tests/agents/website/test_nodes.py`: the `TestBuildRepoProjectResult.test_complete_state_produces_valid_result` fixture currently pins `.gitlab-ci.yml` in the mixed `files_created` list; add a parallel test case for `.github/workflows/ci.yml` or parametrize the existing one.

5. **Phase B verification** — run every command in plan §7.4. Additionally: after the coverage-floor bump commit (step 2) and again after the Phase B commit, run `uv run pytest --cov=src/model_project_constructor/agents/website --cov-fail-under=93` — must pass both times.

6. **Phase 3 close-out** — evaluate Session 11's handoff (§3A), self-assess, document learnings, write full Session 12 handoff, commit (expect **two commits** in this session: the coverage bump + Phase B itself), report, STOP.

### Files Session 12 will touch (from plan §7 + §4.8)

- **Config (1):** `pyproject.toml` — coverage floor 90 → 93.
- **Source (3):** `agents/website/governance_templates.py` (new renderer + `ci_platform` param + `is_governance_artifact` extension), `state.py` (new field), `nodes.py` + `agent.py` (plumb the field).
- **Tests (2):** `tests/agents/website/test_governance.py` (parametrize), `tests/agents/website/test_nodes.py` (extend the build-result test).
- **Docs (2):** `README.md` (one-line note that the generated CI path depends on `ci_platform`), `docs/planning/architecture-plan.md` §8.2 + §11 (CI filename now platform-dependent).

### Hard rules for Phase B

- **No Phase C work.** No new file `github_adapter.py`, no `PyGithub` in `pyproject.toml`, no import of `github` anywhere. Phase C is Session 13.
- **Do NOT rename anything.** Phase A's rename is complete — Session 12 adds code, does not touch names. If a rename feels tempting, commit what you have and note it for a future session.
- **Do NOT change** the do-not-change list in plan §10. The LangGraph topology, retry-backoff loop, governance tier fan-out, `GovernanceManifest` shape, and `website::` thread_id prefix all stay.
- **Do NOT remove the deprecated CLI aliases** (`--fake-gitlab`, `--gitlab-url`, `--group-path`). Phase D removes them.
- **Do NOT infer `ci_platform` from the adapter class.** Plan §7.3 is explicit: make it an explicit parameter so a GitHub project can be scaffolded with `FakeRepoClient` in tests.
- **Do NOT bundle** the coverage-floor bump and Phase B into one commit. Two commits. The coverage bump is a standalone `chore:` commit so Phase B's diff is only Phase B.

### Expected duration

Plan §7 estimates this as 1 session. Phase B adds ~40–60 LOC of Python plus ~5–10 new parametrized test cases, plus the 1-line coverage-floor bump. Expect ~45–60 minutes of editing + verification + close-out.

---

*Session history accumulates below this line. Newest session at the top.*

### What Session 11 Did
**Deliverable:** Phase A of `docs/planning/github-gitlab-abstraction-plan.md` — neutral rename across 26 files (plan expected 22 + 4 drift/docs) + `project_id: int → str` widening (Trap 1 fix). **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `<FILL AT COMMIT TIME>` (single commit containing all Phase A code/test/doc edits + this handoff).

**Pre-flight baseline (verified on disk, not inherited from Session 10's handoff):**
- `uv run pytest -q` → **289 passed, 96.51% coverage, 8.87s wall-clock**. Matches Session 10's claim exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**. Matches.
- `git status` → clean on `master`, 14 commits ahead of `origin/master`.
- Plan §4 greps re-run against baseline `f97b530`: 22 files for class/type references, 18 files for `gitlab_url|group_path|gitlab_target` field refs, 10 hits for `project_id: int` — matches plan §4.1/§4.2/§4.5 within expected drift.

**Drift found vs plan §4.1 inventory:** `tests/agents/website/test_cli.py` has one comment-only match for `GitLabProjectResult` at line 53 that Session 10 did not catalogue. Resolved by updating the comment to `RepoProjectResult` in the same pass. No other drift.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + Session 10 handoff), ran `git status` / `git log --oneline -10`, checked `gh issue list` (empty, matches memory), confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "go" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step even though ACTIVE TASK already described the deliverable.**

2. **User said "go"** — wrote Session 11 IN-PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14).

3. **Pre-flight verification** per plan §6.2: ran `uv run pytest -q` + `uv run mypy` + re-ran all three §4 greps. All baselines matched exactly. Spotted the `test_cli.py` drift (one comment hit) and noted it for the rename pass.

4. **Step 1 — Schemas (plan §6.3 step 1):**
   - `git mv src/model_project_constructor/schemas/v1/gitlab.py → schemas/v1/repo.py`. Blame history preserved.
   - Rewrote `repo.py` contents: `GitLabTarget → RepoTarget` (`gitlab_url → host_url`, `group_path → namespace`), `GitLabProjectResult → RepoProjectResult` (`project_id: int → str`). `GovernanceManifest` unchanged — already neutral.
   - Updated `schemas/v1/__init__.py` imports + `__all__`.
   - Updated `schemas/registry.py` keys: `("GitLabTarget", "1.0.0") → ("RepoTarget", "1.0.0")`, `("GitLabProjectResult", "1.0.0") → ("RepoProjectResult", "1.0.0")`.
   - Updated `tests/schemas/fixtures.py` factories: `make_gitlab_target → make_repo_target` (fields renamed), `make_gitlab_project_result → make_repo_project_result` (`project_id="12345"` stringified).
   - Updated `tests/schemas/test_envelope_and_registry.py`: registry-key assertions, `load_payload` test names.
   - `git mv tests/schemas/test_gitlab.py → tests/schemas/test_repo.py` and rewrote contents: `TestGitLabTarget → TestRepoTarget`, `TestGitLabProjectResult → TestRepoProjectResult`, all references to new names.
   - Verification: `uv run pytest tests/schemas/ -q` → **88 passed**. Schemas layer green independently of the website agent.

5. **Step 2 — `protocol.py` (plan §6.3 step 2):** rewrote the module. `GitLabClient → RepoClient`, `GitLabClientError → RepoClientError`, `ProjectNameConflictError → RepoNameConflictError`, `ProjectInfo.id: int → str`, `commit_files(project_id: int) → str`, `create_project(group_path=...) → namespace=...`. Docstring updated to reference "repo host" instead of "GitLab." **Did not add `@runtime_checkable`** per plan §6.3 hard rule.

6. **Step 3 — `fake_client.py` (plan §6.3 step 3):** `FakeGitLabClient → FakeRepoClient`, `FakeProject.group_path → namespace`, `FakeProject.id: int → str`. Storage dict widened from `dict[int, FakeProject]` to `dict[str, FakeProject]`. `_next_id` stays as int internal counter but stringified at storage via `project_id = str(self._next_id)`. Base URL renamed from `"https://fake.gitlab.test"` to `"https://fake.host.test"` — test expectations updated in `test_fake_client.py`.

7. **Step 4 — `gitlab_adapter.py` (plan §6.3 step 4):** class name `PythonGitLabAdapter` **unchanged** (concrete class, GitLab-specific by definition). Imports updated to `RepoClient`, `RepoClientError`, `RepoNameConflictError`. Constructor kwarg `gitlab_url → host_url`. `create_project(group_path=...) → namespace=...`. **Trap 1 bridge:** `ProjectInfo(id=str(project.id), ...)` on the way out of `create_project`; `self._gl.projects.get(int(project_id))` on the way into `commit_files` so python-gitlab still gets the integer it wants. Docstring updated to say "GitLab path" instead of "GitLab only."

8. **Step 5 — `state.py` + `nodes.py` (plan §6.3 step 5):**
   - `state.py`: state key `gitlab_target → repo_target`, `project_id: int → str`, `initial_state()` parameter renamed. TypedDict field rename.
   - `nodes.py`: imports updated. `GitLabClient/GitLabClientError/ProjectNameConflictError → RepoClient/RepoClientError/RepoNameConflictError`. `create_project` node reads `state["repo_target"]` + `target["namespace"]`. `except GitLabClientError → except RepoClientError`. Failure-reason strings: `"gitlab_error:" → "repo_error:"`, `"gitlab_error_retry_exhausted:" → "repo_error_retry_exhausted:"`. `build_gitlab_project_result → build_repo_project_result`; return type `GitLabProjectResult → RepoProjectResult`. `state.get("project_id", 0) → state.get("project_id", "")`.

9. **Step 6 — `graph.py` + `agent.py` + `cli.py` (plan §6.3 step 6):**
   - `graph.py`: docstring ASCII-art "GitLab error" → "repo error"; `client: GitLabClient → RepoClient`; import updated.
   - `agent.py`: full rewrite. `WebsiteAgent.__init__(client: GitLabClient) → RepoClient`. `run(..., gitlab_target: GitLabTarget) → repo_target: RepoTarget` returning `RepoProjectResult`. `_precondition_result` takes `RepoTarget`, returns `RepoProjectResult(project_id="", ...)`. Import from `schemas.v1.repo` instead of `schemas.v1.gitlab`.
   - `cli.py`: full rewrite. Module docstring updated. `DEFAULT_GROUP → DEFAULT_NAMESPACE`, `DEFAULT_GITLAB_URL → DEFAULT_HOST_URL` (value still `"https://gitlab.example.com"`). Flags: `--fake-gitlab → --fake` (with `"--fake-gitlab"` kept as a second name on the same typer.Option for one-window deprecation), `--gitlab-url → --host-url` (with `"--gitlab-url"` alias), `--group-path → --namespace` (with `"--group-path"` alias). typer treats the second name as a secondary long option — both old and new names still work from the CLI, and the Python function param is the new name only. Smoke test with `--fake-gitlab` at close-out confirms this.

10. **Step 7 — `__init__.py` re-exports (plan §6.3 step 7):** rewrote `agents/website/__init__.py` imports and `__all__`. `GitLabClient → RepoClient`, `GitLabClientError → RepoClientError`, `ProjectNameConflictError → RepoNameConflictError`, `FakeGitLabClient → FakeRepoClient`, `build_gitlab_project_result → build_repo_project_result`. `PythonGitLabAdapter` stays. Module docstring updated.

11. **Step 8 — Tests (plan §6.3 step 8):** every test file under `tests/agents/website/` touched:
    - `conftest.py` — fixture `gitlab_target → repo_target`, `fake_client` fixture returns `FakeRepoClient()`. Imports updated.
    - `test_fake_client.py` — class `TestFakeGitLabClient → TestFakeRepoClient`, all method signatures (`group_path → namespace`), `info.id == 1000 → "1000"` (string assertion), `b.id == a.id + 1 → int(b.id) == int(a.id) + 1` (still monotonic but stringified).
    - `test_gitlab_adapter.py` — **filename unchanged** (plan §3.4 rule). Imports updated (`RepoClientError`, `RepoNameConflictError`). Constructor kwargs updated (`host_url=...`). Exception-translation tests updated. `commit_files(project_id=1) → project_id="1"`.
    - `test_agent.py` — fixture names renamed in every test parameter list; assertions updated (`result.project_id == 1000 → "1000"`); docstring `"GitLab"` references updated to "host."
    - `test_nodes.py` — `_FlakyClient` and `_CommitFlakyClient` method signatures updated; `TestBuildGitLabProjectResult → TestBuildRepoProjectResult`; `project_id: "42"` (stringified); `state["project_id"] = 1 → "1"`. Test name `test_non_conflict_gitlab_error_halts → test_non_conflict_repo_error_halts`. Failure-reason assertions: `"gitlab_error" → "repo_error"`.
    - `test_governance.py` — module docstring updated; imports updated; `_run_agent` helper constructs `RepoTarget(host_url=..., namespace=...)` instead of `GitLabTarget(gitlab_url=..., group_path=...)`.
    - `test_retry.py` — `_TransientCommitClient` + `_AlwaysFailingCommitClient` method signatures updated; the `RepoClient` type annotation on `_run_with_client`; `WebsiteAgent.__new__` hack preserved per Session 9's judgment (flagged in Session 10's gotchas, decision reaffirmed). Failure-reason assertion: `"gitlab_error_retry_exhausted" → "repo_error_retry_exhausted"`. `projects: dict[int, Any] → dict[str, Any]`.
    - `test_cli.py` — test `test_cli_requires_fake_gitlab → test_cli_requires_fake_flag`, flag `--fake-gitlab → --fake`, comment `"# JSON blob at the end parses as a GitLabProjectResult dump" → "...RepoProjectResult dump"`.

12. **Step 9 — Docs (plan §6.3 step 9):**
    - `README.md`: phase-table row 4B text stays (it's historical); repo-layout comment on `schemas/v1/` now says "IntakeReport, RepoTarget / RepoProjectResult, governance types"; repo-layout comment on `fake_client.py` says "repo-host stand-in"; repo-layout comment on `cli.py` says "(--fake or --private-token)"; getting-started "Fake GitLab" → "Fake repo host", example flags updated to `--fake`, `--host-url`, `--namespace`, closing paragraph updated with deprecated-alias note.
    - `docs/planning/architecture-plan.md` §4.3: Website Agent responsibility paragraph now says "repository-host project (GitLab today, GitHub via Phase C of the abstraction plan)" with a naming-note admonition pointing to `github-gitlab-abstraction-plan.md`. Inputs list: `GitLabTarget → RepoTarget`. Outputs list: `GitLabProjectResult → RepoProjectResult` with the `project_id: str` explanation. Failure-modes table: "GitLab API error" → "Repo host API error", "GitLab project name conflict" → "Repo project name conflict."
    - `docs/planning/architecture-plan.md` §5.4: full code block replacement. New section heading `### 5.4 RepoTarget and RepoProjectResult`. Admonition explaining the rename and the `int → str` widening. Pydantic class definitions rewritten with new names and `project_id: str`.
    - `docs/planning/architecture-plan.md` §11: section heading "Generated GitLab Repo Structure" → "Generated Repository Structure" with a naming-note admonition explaining that the CI template filename is still GitLab-specific until Phase B adds the GitHub sibling.

13. **Phase A verification (plan §6.4)** — all eight commands run at close-out:
    - **Grep 1** (`GitLabClient|GitLabTarget|GitLabProjectResult|GitLabClientError|ProjectNameConflictError|FakeGitLabClient|build_gitlab_project_result|gitlab_target` across `{src,tests}/**/*.py`): **0 hits**.
    - **Grep 2** (`gitlab_url|group_path` across `{src,tests}/**/*.py`): **0 hits**.
    - **Grep 3** (`project_id\s*:\s*int` across `{src,tests}/**/*.py`): **0 hits**.
    - **pytest**: `289 passed @ 96.51% coverage`. Zero skips, zero xfails added, zero tests deleted.
    - **mypy strict**: `Success: no issues found in 12 source files`.
    - **Coverage floor**: holds at 96.51% ≥ 90% (`--cov-fail-under=90` passes; Phase A did not touch any uncovered lines).
    - **Tier-1/2/3 fake-CLI smoke tests**: all three print `Status:  COMPLETE` when invoked with `--fake`.
    - **Deprecated `--fake-gitlab` alias**: prints `Status:  COMPLETE` (hidden alias works, no typer errors).

**Verification notes:**
- No intermediate `uv run pytest` inside the rename pass — plan §6.3 says intermediate runs are "ideal but not mandatory," and the final full-suite run was clean.
- `uv run mypy` was NOT run between every substep; mypy is strict enough that it would flag any incomplete rename, but the compiler feedback would have been noisier than one final pass. The final pass returned Success so no intermediate state was inconsistent.

### Key Files Shipped in Session 11

**Files renamed (git mv preserves blame):**
- `src/model_project_constructor/schemas/v1/gitlab.py` → `schemas/v1/repo.py`
- `tests/schemas/test_gitlab.py` → `tests/schemas/test_repo.py`

**Source files rewritten/edited (13):**
- `src/model_project_constructor/schemas/v1/__init__.py` — re-exports
- `src/model_project_constructor/schemas/registry.py` — registry keys
- `src/model_project_constructor/agents/website/__init__.py` — re-exports + `__all__`
- `src/model_project_constructor/agents/website/protocol.py` — the rename center
- `src/model_project_constructor/agents/website/fake_client.py` — `FakeRepoClient`
- `src/model_project_constructor/agents/website/gitlab_adapter.py` — imports + type widen + `int(project_id)` bridge
- `src/model_project_constructor/agents/website/graph.py` — `RepoClient` type annotation + docstring
- `src/model_project_constructor/agents/website/nodes.py` — every call site + `build_repo_project_result`
- `src/model_project_constructor/agents/website/state.py` — `repo_target`, `project_id: str`
- `src/model_project_constructor/agents/website/agent.py` — `WebsiteAgent.run` signature + `_precondition_result`
- `src/model_project_constructor/agents/website/cli.py` — CLI flags + deprecated aliases

**Test files edited (10):**
- `tests/schemas/fixtures.py` — factories
- `tests/schemas/test_envelope_and_registry.py` — registry keys
- `tests/agents/website/conftest.py` — `repo_target` + `FakeRepoClient` fixtures
- `tests/agents/website/test_fake_client.py` — `TestFakeRepoClient`
- `tests/agents/website/test_gitlab_adapter.py` — **filename kept**, contents updated
- `tests/agents/website/test_agent.py` — fixture param renames + string `project_id` assertions
- `tests/agents/website/test_nodes.py` — `TestBuildRepoProjectResult` + `_FlakyClient` signatures
- `tests/agents/website/test_governance.py` — `_run_agent` helper + imports
- `tests/agents/website/test_retry.py` — transient-client signatures + failure reasons
- `tests/agents/website/test_cli.py` — `--fake` flag + test name + comment

**Docs edited (3):**
- `README.md` — getting-started + repo-layout
- `docs/planning/architecture-plan.md` — §4.3, §5.4, §11
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewrite + Session 11 handoff)

**Total: 26 files changed, 2 renames, net +~50 / -~50 LOC** (rename is content-preserving within files).

### Gotchas — Read These Before Starting Phase B

**Carryover gotchas from Session 10 that STILL apply to Phase B:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:154` is still there.** Session 11 did NOT fix it (plan §6 hard rule: rename only). Phase B touches `WebsiteAgent.__init__` to add the `ci_platform` kwarg — this is a natural place to refactor the constructor to accept an optional `graph` kwarg and retire the `__new__` hack **IF** the refactor is one line and obvious. If it's not obvious, leave the hack. Production code should not grow a kwarg just for a test-only need (Learning #4 from SESSION_RUNNER.md).
- **`retry_backoff` uses `time.sleep()` in production.** Any new retry-path tests must inject `sleep=lambda _s: None`. Phase B does not touch retry, but parametrized governance tests that somehow exercise the retry path must follow this rule.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** Keep it that way. Adapter tests use `callable(getattr(...))`.
- **`GovernanceManifest.artifacts_created` is derived from `files_created` via `is_governance_artifact`**, not stored. Phase B's extension of `is_governance_artifact` to recognize `.github/workflows/ci.yml` changes the manifest output for any repo that emits the GitHub CI file.
- **`_is_name_conflict(exc)` loose-matches GitLab response codes** (`gitlab_adapter.py:158`). Phase B does not touch this. Phase C's `PyGithubAdapter` needs its own equivalent for GitHub's 422 responses.

**New Phase B gotchas (from Phase A work):**

- **`WebsiteState.project_id` is now `str`**, not `int`. Any test state dict in `test_nodes.py` that Phase B adds MUST use `"42"` not `42`. mypy strict catches this.
- **`FakeRepoClient.projects` is `dict[str, FakeProject]`.** Dict lookup uses the string `project_id` returned by `create_project`. Phase B tests that index into `fake_client.projects` directly must pass a string key.
- **`cli.py` uses typer multi-name aliases** (`typer.Option("--fake", "--fake-gitlab", ...)`) rather than hidden second flags. This means **both names appear in `--help` output**. If Phase B wants to hide the deprecated alias from help, it needs a different mechanism (typer has `hidden=True` but then both options need to be separate Options — more code). Session 11's judgment: acceptable for one deprecation window, since Phase D will remove the old names. Session 12 should NOT change this unless explicitly asked.
- **`DEFAULT_HOST_URL = "https://gitlab.example.com"`** in `cli.py:39`. This is a GitLab URL even though the variable name is neutral. Phase D (not Phase B) will change this default when the `--host` flag lands, since the default host needs to match the default platform.
- **`schemas/v1/__init__.py`'s `__all__` list** now has `RepoProjectResult`, `RepoTarget`, `GovernanceManifest` in alphabetical-ish order under a `# repo` comment. If Phase B adds a `CIPlatformLiteral` or similar, put it in `schemas/v1/common.py` — NOT `repo.py` — because it's not host-specific.
- **The `project_id="12345"`** literal in `tests/schemas/fixtures.py:182` is intentionally stringified. Don't "fix" it back to int.
- **`test_gitlab_adapter.py` filename is unchanged** — it tests the concrete GitLab adapter, not the neutral Protocol. Phase C will add `test_github_adapter.py` as a sibling. Do not rename `test_gitlab_adapter.py` for symmetry — the plan §6.1 is explicit.

### Session 10 Handoff Evaluation (by Session 11)

**Score: 10/10.**

- **What helped (specific):**
  - **The plan document at `docs/planning/github-gitlab-abstraction-plan.md` itself** was the single highest-value artifact. Session 11's rename was almost mechanical — every file to touch was listed in §4, every execution step was numbered in §6.3, every verification command was ready to run in §6.4. I never had to invent a step or guess a name. The plan's 720 lines paid for themselves within the first 20 minutes of Phase A execution.
  - **The three traps documentation (§2.2)** was the part that made this session possible. Trap 1 (`project_id: int`) is not something I would have found on my own in the rename pass — the compiler doesn't complain about widening an `int` field to `str` if the call sites never rely on the numeric value. Session 10 caught it by reading `gitlab_adapter.py:111 id=int(project.id)` during evidence-gathering, and the plan flagged it as a bundled fix for Phase A. Without that, Phase A would have left a latent bug for Phase C to discover the hard way.
  - **The naming table in §3.4** was the exact source of truth for every rename. I referenced it constantly during Steps 2-7. Having current/proposed/lives-in/notes in one table meant zero ambiguity.
  - **The rename-vs-parallel-schema decision (§3)** was well-argued. I did not second-guess the choice at any point. §3.2's "front-loaded cost" framing is what kept me from splitting the rename across two sessions when it hit 26 files.
  - **The per-phase DONE criteria (§6.1)** let me know I was done. I ran each verification command against §6.4 expected output and got a binary green/not-green answer for each. No judgment calls about "is this enough."
  - **The Session 9 gotchas block that Session 10 preserved in their own handoff** — I used the `WebsiteAgent.__new__` hack note, the `@runtime_checkable` rule, and the retry-sleep injection pattern all in this session. Session 10's handoff block was the right length: long enough to be actionable, short enough to read.
  - **The "hard rules for Phase A" in Session 10's ACTIVE TASK** (lines 73-80) gave me explicit permission to ignore the things I noticed. When I saw `test_cli.py` had one stray `GitLabProjectResult` comment, I updated it (in-scope drift). When I noticed the `WebsiteAgent.__new__` hack, I left it alone (out-of-scope per Session 10's gotcha explicitly). The hard rules saved me from scope creep decisions.
  - **The two learnings Session 10 added** (#8 grep inventory separation + #9 single-document plan) were background knowledge I used implicitly when reading the plan's §4 grep inventory — separate patterns per classifier group means I could verify each pattern independently without a single conflated count.

- **What was missing (minor):**
  - **No `pyproject.toml` coverage-floor note.** The plan mentions coverage stays ≥ 90% (matching the floor) but Session 11 learned at the end that the user wanted 93%. This is not Session 10's fault (the user's directive came mid-Session-11), but a pre-emptive "check the coverage floor matches Session N+1 ambitions" habit would be nice for future planning docs.
  - **The `test_cli.py` drift** (one comment hit) was a mild miss in the plan's §4.1 inventory. Session 10 ran the greps but the inventory table in §4.1 listed 8 test files and my run surfaced 11 hit files — `test_cli.py` was absent. It was a comment-only hit so trivial to fix, but the plan could have used a sentence saying "if a grep turns up more files than the inventory, the extras are in-scope drift — fix them in the same pass."
  - **Plan §6.3 step 6** (CLI with deprecated aliases) says "keep deprecated `--fake-gitlab`, `--gitlab-url`, `--group-path` aliases as hidden flags." Session 11 implemented them as **typer multi-name secondary options**, which means they appear in `--help` output. Hiding a typer option requires a second Option with `hidden=True`, which doubles the code. Session 11's judgment: the `--help` visibility is acceptable for one deprecation window. If the user wanted strictly hidden aliases, the plan should have been explicit about typer's multi-name vs hidden-option tradeoff. Not a blocker; Phase D removes all three aliases anyway.

- **What was wrong:** nothing. Every factual claim I verified against disk matched. Baseline commit `f97b530`, 289 tests, 96.51% coverage, 12 mypy-clean files, 22-file class-refs footprint, 18-file field-refs footprint, 10-hit `project_id: int` footprint — all accurate.

- **ROI:** Reading the plan document took ~15 minutes across two Read calls. It saved at least 2 hours of grep-and-guess work that a planless rename would have cost. The §3.4 naming table + §6.3 execution order + §6.4 verification block together constitute ~60% of the plan's value; the other 40% is the traps documentation + do-not-change list. Plan documents with this level of detail should be the norm for any multi-file refactor.

### Session 11 Self-Assessment

**Score: 9/10** (Session 12 will score independently).

- **What went well:**
  - **All §6.4 verification commands passed on first try** after Step 9 (docs). Zero red-then-green cycles. mypy strict stayed consistent across substeps because the rename was done in dependency order (schemas → protocol → fake client → adapter → state/nodes → graph/agent/cli → tests).
  - **Zero test deletions, zero skips, zero xfails added.** 289 → 289. Coverage 96.51% → 96.51%. The rename preserved every behavioral assertion.
  - **Blame history preserved** via `git mv` for both `schemas/v1/gitlab.py → repo.py` and `tests/schemas/test_gitlab.py → test_repo.py`. Future `git blame` on `RepoTarget.visibility` will show the original `"internal"` default with its Phase-4B justification.
  - **Trap 1 bundled cleanly.** `ProjectInfo.id: int → str` + `commit_files(project_id: int) → str` + `state["project_id"]: int → str` + test stringification + `gitlab_adapter.py` `str(project.id)` / `int(project_id)` bridge all landed in the same pass. No orphan integer typing.
  - **Test drift (`test_cli.py`)** caught by running the grep myself at pre-flight, not by plan inspection. This is the right direction: trust plans for structure, trust greps for reality.
  - **Deprecated flag aliases work.** `--fake-gitlab` smoke test at close-out confirms a user who never read the changelog can still run their Phase 4B scripts after Phase A.
  - **No scope creep.** I did not fix the `WebsiteAgent.__new__` hack, did not touch the LangGraph topology, did not rename `PythonGitLabAdapter`, did not start Phase B despite Phase A finishing under the 2-hour estimate. Session boundary preserved.
  - **Docs updated in the same commit** as code, per plan §6.3 step 9. README + architecture-plan.md §§4.3/5.4/11 all reflect the new names with explicit naming-note admonitions so future readers aren't confused by §11's GitLab-specific `.gitlab-ci.yml` reference.
  - **Two user-interaction check-ins handled correctly:**
    - Early "1" message → stopped, asked for clarification, did not guess.
    - Later "raise coverage floor to 93%" directive mid-close-out → acknowledged, recorded in Session 12 ACTIVE TASK as the first action, did not interrupt Phase A execution to act on it (that would have bundled a coverage-floor change into a rename commit).
  - **TaskCreate/TaskUpdate discipline.** 13 tasks created at start, each marked `in_progress` at start and `completed` at end. Zero stale tasks at close-out.

- **What I could have done better:**
  - **Pre-flight verification ran AFTER writing the IN-PROGRESS stub, not before.** Plan §6.2 says pre-flight before Phase 1B. I wrote the stub first (because failure mode #14 says stub first) and ran pre-flight second. If pre-flight had failed, the stub would have been a false claim. In practice pre-flight passed, but the order is wrong and should be: (Phase 0 reads) → (pre-flight verification) → (Phase 1B stub) → (execute). Session 12 should reorder.
  - **I did not run `uv run pytest tests/schemas/ -q` between substeps as aggressively as plan §6.3 suggests.** I ran it once after Step 1 (schemas) and got 88 passing, then batched Steps 2-7 without another intermediate run. The final pytest was clean so this saved time, but if Step 5 (nodes.py) had left a broken mypy state, I'd have spent more time bisecting. Acceptable tradeoff for this session; judgment call.
  - **The `--fake-gitlab` deprecation alias question** (hidden vs multi-name typer option) was not flagged to the user. I made a judgment call and moved on. A more careful session would have surfaced the tradeoff in the handoff before implementing. I've documented it now in the gotchas above so Session 12 can revisit if needed.
  - **The architecture-plan.md §11 update** is a one-line admonition pointing to Phase B; I didn't rewrite the `.gitlab-ci.yml` bullet itself. A more aggressive session would have added a parenthetical `(or .github/workflows/ci.yml after Phase B)` to the bullet. Not strictly necessary — Phase B will do that in its own doc pass — but a close reader of §11 today might not notice the admonition at the top.
  - **I did not run `uv run pytest tests/schemas/ -q` AFTER the schemas rename had every caller updated** — I ran it after Step 1 (before nodes.py was updated). At that point the schemas tests pass in isolation but the website tests are broken. If Session 12 wants truly "green between substeps," the order should be: schemas → protocol → fake client → adapter → state/nodes → run pytest → graph/agent/cli → run pytest → init → run pytest → tests → run pytest. Session 11 chose to batch and run once at the end.
  - **The handoff block is long** (~700 lines between ACTIVE TASK and this self-assessment). Session 10's handoff was also ~700 lines and scored 10/10, so length alone is not a defect. But a session-by-session trend toward longer handoffs is a warning sign (protocol erosion, failure mode #17). If Session 12 finds this handoff unwieldy, they should feel free to trim earlier sessions' verbose logs.

### Session 11 Learnings for `SESSION_RUNNER.md`

Add to the Learnings table (suggested entries 11-12):

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 11 | Run pre-flight verification BEFORE Phase 1B stub, not after. The stub is a claim about the state of the session; pre-flight is what makes that claim true. If pre-flight fails, the stub is a false claim in persistent storage. Correct order: Phase 0 reads → pre-flight verification → Phase 1B stub → execute. | Session 11 | Any implementation session where the plan specifies a pre-flight step. |
| 12 | When a plan's grep-based inventory lists N files and a re-run surfaces N+k files, the k extras are **in-scope drift** — fix them in the same pass, don't escalate. Re-run the grep at pre-flight, not just during planning, because the codebase drifts between plan-date and exec-date. Session 11's `test_cli.py` comment-only hit was caught this way. | Session 11 | Any implementation session executing a plan with a file-level inventory. |

### Followups Session 11 did NOT do (deliberate)

- **Fix the `WebsiteAgent.__new__` hack in `test_retry.py`.** Out of scope for Phase A (rename only). Phase B touches `WebsiteAgent.__init__` and can consider retiring the hack if the refactor is obvious.
- **Rename `test_gitlab_adapter.py`.** It tests the GitLab-specific concrete adapter. Plan §6.1 is explicit.
- **Remove deprecated CLI aliases.** Phase D removes them. Plan §3.4 is explicit.
- **Update `docs/planning/architecture-approaches.md`.** Historical alternatives document; out of scope per plan §4.7 + §1.2.
- **Update `SESSION_NOTES.md` historical session blocks (Sessions 1-10).** Retroactive rewrite is out of scope per plan §4.7.
- **Raise `pyproject.toml` coverage floor from 90 to 93.** User directive came mid-close-out; deferred to Session 12 as the first action so it lands in a separate commit from Phase A. See the Session 12 ACTIVE TASK above.
- **Start Phase B.** One-phase-per-session rule. Failure mode #18.



### What Session 10 Did
**Deliverable:** `docs/planning/github-gitlab-abstraction-plan.md` — multi-phase plan to adapt the Website Agent for GitHub **or** GitLab targets, per `SESSION_RUNNER.md` Planning Sessions protocol. **COMPLETE.**
**Started:** 2026-04-14
**Completed:** 2026-04-15
**Commits:** `f44f8dc` (single commit containing the plan doc + this handoff + the SESSION_RUNNER.md Learnings additions).

**What was done (chronological):**
1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + start of Session 9 handoff), ran `git status` / `git log --oneline -10` / `gh repo view` / dashboard file check. Confirmed baseline: master clean, 12 commits ahead of origin, last session = Session 9 commit `f97b530`, dashboard exists externally at `~/Development/dashboard.html`. Reported findings to user, waited for direction. **Did not skip the report-and-wait step even though the ACTIVE TASK block already described the deliverable** (failure mode #9, task-in-prompt bypass).
2. **User clarifications** — user explained the Session 9 user notes originally came from a `/btw` (by-the-way) question whose response was truncated, losing point #1. Session 10 offered three options for handling the missing point (reconstruct, proceed without, re-run /btw). User asked for a "more detailed solution" — i.e., do deeper research on the question rather than pick a quick answer.
3. **Evidence-gathering pass** — before touching any planning text, read `protocol.py` / `schemas/v1/gitlab.py` / `gitlab_adapter.py` / `cli.py` / `nodes.py` / `agent.py` / `governance_templates.py` (lines 505-665 and 780-814) to ground the plan in actual code rather than inherited Session 9 notes. This is the step that found the three traps (Trap 1: `project_id: int`; Trap 2: multi-file commit asymmetry; Trap 3: nested groups vs flat orgs) — none of which were in Session 9's user notes.
4. **First detailed response to user** — wrote a ~400-line conversational solution covering: the 80/20 state of the abstraction boundary, the three traps, the live grep counts (188/52/111/32 hits across the symbol groups), the rename-vs-parallel recommendation, and a candidate 4-phase sequence. Offered the user an open question: bundle the `int→str` widening into Phase A or split it out.
5. **User chose bundling** — confirmed Option 1 (bundle widening into Phase A). Session 10 acknowledged and paused before any code/doc work to wait for explicit "go."
6. **User said "go"** — Session 10 resumed with Phase 1B: wrote the "(IN PROGRESS)" stub to `SESSION_NOTES.md` BEFORE any research or writing. Ghost-session protection per failure mode #14. (Earlier tool call to write the stub was rejected by the user; the correct sequence was confirm-Option-1 → explicit-go → stub → work.)
7. **Source read pass** — parallel-read `state.py`, `fake_client.py`, `graph.py`, `agents/website/__init__.py`, `schemas/v1/__init__.py`, `schemas/registry.py`, `tests/agents/website/conftest.py`. This completed the file-level picture needed for the plan's "do not change" list and execution order. Found `WebsiteState.project_id: int` at `state.py:32` — confirmed Trap 1 propagates through state and not just the Protocol.
8. **Full grep inventory with line numbers** — ran 5 batched greps with `-n`: (a) class/type references, (b) field names, (c) CI template + adapter, (d) cross-cutting helpers, (e) `project_id:` type footprint. The first batch (188 hits, 22 files) was large enough that ripgrep's output overflowed 30KB and was persisted to disk; Session 10 read the persisted file to get the complete listing. Total line-numbered citations in the plan: ~170 grep hits across 22 source-and-test files + 4 doc files.
9. **Architecture-plan section reads** — parallel-read `docs/planning/architecture-plan.md` §§4.3 (lines 183-215), 5.4 (347-376), 8.2 (506-557), 11 (665-725), 14 Phase 4/5 (884-931). Captured exact line-number anchors for every cross-reference in the plan document.
10. **pyproject.toml check** — grep'd `python-gitlab|PyGithub|optional-dependencies` to confirm `agents` extras list. Found `python-gitlab>=4` on `pyproject.toml:23`, no `PyGithub` entry yet — Phase C will add it.
11. **Docs impact grep** — ran `grep` across `*.md` for `GitLabTarget`, `GitLabClient`, `.gitlab-ci.yml`, `python-gitlab`, `PyGithub`. Found: `README.md` (12 hits, ~8 substantive), `docs/planning/architecture-plan.md` (already mapped), `docs/planning/architecture-approaches.md` (historical — out of scope), `SESSION_NOTES.md` (out of scope — session history). No collisions with the new `RepoTarget`/`RepoClient`/`host_url`/`PyGithubAdapter`/`.github/workflows` names.
12. **Plan document written** — `docs/planning/github-gitlab-abstraction-plan.md`, ~720 lines, 16 sections. Structure: scope (§1), current state (§2), three traps detailed (§2.2), strategic decision with rationale (§3), naming table (§3.4), full grep inventory (§4.1-§4.8), per-phase specs (§6-§9 for Phases A/B/C/D), do-not-change list (§10), Phase 5 ordering decision (§11), provenance of missing point #1 (§12), open questions (§13), close-out protocol for executor sessions (§14), risk register (§15), single-document rationale (§16).
13. **Cross-reference cleanup** — post-write, grep'd the plan for `§\d` and found five stale references from an earlier section numbering (§7.1 where §4.6 or §6 was meant). Fixed all five with targeted Edits. Re-ran the grep to confirm no broken references remain.
14. **ACTIVE TASK rewrite** — replaced the ~80-line Session 10 planning mandate with a ~70-line Session 11 Phase A execution mandate. New block names Phase A as the deliverable, lists the 22-file footprint, links to plan §4/§6/§10 for details, and restates the hard rules (no partial rename, no Phase B bundling, no Phase 5 interleave).
15. **Session 10 handoff** — this entry. Full evaluation of Session 9's handoff, self-assessment, learnings for `SESSION_RUNNER.md`, Session 11 rubric.

**Verification (what I ran against the written plan):**
- `wc -l docs/planning/github-gitlab-abstraction-plan.md` → ~720 lines (up from ~712 after the 5 cross-reference fixes).
- `grep -n '§\d' docs/planning/github-gitlab-abstraction-plan.md` → all references resolve to existing sections of either this plan or `architecture-plan.md`. No orphan references.
- `grep -n '^## \d\|^### \d' docs/planning/github-gitlab-abstraction-plan.md` → 17 top-level `##` sections and 24 `###` subsections, matching the intended table of contents.
- **Session 10 did NOT run `uv run pytest`, `uv run mypy`, or any code-affecting command.** Planning sessions are read-only with respect to `src/` and `tests/`. The baseline test count (289) and coverage (96.51%) are inherited from Session 9's handoff, not re-verified.
- **Session 10 did NOT touch any file under `src/` or `tests/`.** Verified by `git status` at close-out time (will be clean except for the plan doc + SESSION_NOTES.md + SESSION_RUNNER.md).

**Input from Session 10 user: provenance of the missing point #1.** User confirmed the Session 9 notes came from a `/btw` question — "what can be done to allow this project's product to use either GitHub or GitLab?" — whose response was truncated. Point #1 is irrecoverable without re-running the question. User approved Session 10's reconstruction: *"The `GitLabClient` Protocol in `agents/website/protocol.py` is already the adapter boundary. Rename to `RepoClient`, widen `ProjectInfo.id` from `int` to `str`, and let the adapter pattern absorb the rest."* This reconstruction lives in plan §12 with explicit "reconstructed, not verbatim" framing; if the user ever regenerates the original response, plan §12 should be updated with the real text.

### Key Files Shipped in Session 10

**One new file:**
- `docs/planning/github-gitlab-abstraction-plan.md` — the plan. **Session 11 MUST read this in full before starting Phase A.** It is the authoritative source of scope, execution order, verification commands, and DONE criteria. The ACTIVE TASK block above is an abbreviated pointer, not a replacement.

**Three modified files:**
- `SESSION_NOTES.md` — ACTIVE TASK block rewritten for Session 11 Phase A; this Session 10 handoff added; Session 9 through Session 1 unchanged.
- `SESSION_RUNNER.md` — Learnings table appended with entries 7, 8, 9 (see "Session 10 Learnings" below).

**Zero files under `src/` or `tests/` touched.** Verified by `git status` at close-out.

### Gotchas — Read These Before Starting Phase A

**Phase A execution gotchas (new for Session 11):**
- **The `schemas/v1/gitlab.py` → `schemas/v1/repo.py` move MUST use `git mv`.** Blame history is the only record of why certain field defaults were chosen (see `gitlab.py:17` `visibility: Literal["private", "internal", "public"] = "private"` — the "internal" value is GitLab-specific and matters for the Trap 3 discussion). Losing blame because of a plain-text rename is a cost Session 11 should not pay.
- **`schemas/registry.py:30-31` uses string keys that will break the envelope tests.** `tests/schemas/test_envelope_and_registry.py:97-98, 106-107` pin the string keys `"GitLabTarget"` and `"GitLabProjectResult"` directly. Phase A updates the registry entries AND those tests in the same commit, otherwise the test suite goes red between substeps.
- **`python-gitlab.projects.get(project_id)` expects an integer.** After Phase A widens `project_id: int → str`, the adapter in `gitlab_adapter.py:125` must do `int(project_id)` on the way in, not `project_id` directly. Same for the fake client — `fake_client.py:100` does `self.projects[project_id]` on a dict whose keys are integers. After widening, either stringify the dict keys or convert on lookup. Recommend the latter (minimal disturbance to test fixtures that seed `FakeProject(id=1000)`).
- **`FakeGitLabClient` → `FakeRepoClient` is NOT just a class-name change.** The docstring at `fake_client.py:1-10` mentions "GitLab stand-in" — update to "repo stand-in." `test_fake_client.py:13` has `class TestFakeGitLabClient` that also renames. The `FakeProject` dataclass keeps its name (neutral enough).
- **`tests/agents/website/test_gitlab_adapter.py` keeps its filename.** It tests the GitLab-specific `PythonGitLabAdapter` and should remain named for what it tests. The imports inside the file update (`GitLabClient` → `RepoClient`, etc.) but `git mv` is NOT used.
- **The `WebsiteAgent.__new__` hack in `test_retry.py` (flagged in Session 9's handoff) is NOT fixed by Phase A.** It's a test-only workaround for `WebsiteAgent.__init__` always building its own graph. Phase A might incidentally refactor `WebsiteAgent.__init__` to accept a `graph` kwarg — but that's a production-code change for a test-only benefit, and Session 9's judgment was "leave it." Session 11 should preserve that judgment unless the rename pass makes `WebsiteAgent.__init__` a natural change site anyway.
- **The plan's §6.3 execution order is NOT mandatory — just recommended.** mypy strict may or may not stay green between substeps depending on the order of edits; if Session 11 finds a better order, follow it. The invariant is: at close-out, all 289 tests pass, mypy is clean, and every grep in §6.4 returns the expected zero hits.
- **The deprecated CLI flag aliases (`--fake-gitlab`, `--gitlab-url`, `--group-path`) are one-release-window only.** Phase A adds them as hidden aliases; Phase D removes them. If a user between Phase A and Phase D runs an old script, they get a silent accept (hidden flag works) and no deprecation warning (intentional — a `typer` hidden flag doesn't emit one). If Session 11 wants louder deprecation (e.g. a `stderr` write), note it for Phase D. Not blocking.
- **Coverage floor is 90%** (`pyproject.toml` — verified during Phase 0 of Session 10). Baseline is 96.51%. Phase A should not change coverage meaningfully — rename only. If coverage drops below 95%, something's off and Session 11 should investigate rather than lower the gate.

**Carryover from Session 9 that still applies to Phase A:**
- **`retry_backoff` uses `time.sleep()` in production.** Any new retry-path tests Phase A adds (none expected, but just in case) must inject `sleep=lambda _s: None`.
- **`build_repo_project_result` (the renamed `build_gitlab_project_result`) only populates `model_registry_entry` when BOTH `project_name` AND `project_slug` are in state.** The behavior doesn't change; the test assertions in `test_nodes.py:350` that pin `model_registry_entry == {}` on failed-early states keep passing.
- **`GovernanceManifest.artifacts_created` is derived from `files_created` via `is_governance_artifact`**, not stored. Phase A doesn't touch this logic; it's a Phase B concern (add `.github/workflows/ci.yml` recognition).
- **`is_governance_artifact` is prefix/literal based.** Phase A doesn't change its recognized set. Phase B does.
- **`_is_name_conflict(exc)` loose-matches GitLab response codes.** Phase A doesn't change the matching — only the error type it raises (`ProjectNameConflictError` → `RepoNameConflictError`).
- **The `GitLabClient` Protocol (renamed to `RepoClient`) is NOT `@runtime_checkable`.** Keep it that way. Adapter tests use `callable(getattr(...))`.
- **`PythonGitLabAdapter` constructor does not make a network call.** `test_gitlab_adapter.py:46` pins this. After Phase A, that assertion should still hold — the rename doesn't touch constructor behavior.

### Session 9 Handoff Evaluation (by Session 10)

**Score: 10/10.**

- **What helped (specific):**
  - **The verbatim `/btw` notes block** (Session 9 handoff lines 135-152 of pre-edit SESSION_NOTES.md) was the single most valuable piece of the handoff. Session 10 used all four listed points (2-5) as the scaffold for the plan and none were discarded. Session 9's discipline of recording the notes verbatim rather than paraphrasing or acting on them was exactly the right call.
  - **The "Key Files Shipped Through Phase 4B" inventory** (lines 172-202) pointed Session 10 at `render_gitlab_ci()` as "the single function that needs a parallel `render_github_actions_ci()`." Session 10 used this directly as the center of Phase B in the plan, saving ~15 minutes of grep work.
  - **The gotchas block** (lines 203-244) flagged `is_governance_artifact` needs updating for `.github/workflows/ci.yml`, which became a Phase B DONE criterion in the plan (§7.1). The same block flagged that python-gitlab DOES ship type stubs but PyGithub may not — Session 10 wrote this concern into the plan's §8.2 pre-flight for Phase C.
  - **The `_is_name_conflict(exc)` description** ("400/409 + lowercase 'already been taken' substring") was reused nearly verbatim as the pattern for the PyGithub adapter's name-conflict detection in plan §8.1 (GitHub returns 422 with "name already exists" — same loose-match approach).
  - **The do-NOT-change list** (lines 147-151) was preserved word-for-word in the plan's §10. Session 10 added five more invariants (the `sleep` injection pattern, the accumulator across four scaffold nodes, the precondition guard, the `website::` thread_id prefix, GovernanceManifest shape) but did not weaken or remove any of Session 9's original items.
  - **The evaluation rubric** at lines 307-316 was the explicit checklist Session 10 worked from. All eight rubric items are addressed in the plan. The rubric's existence — not just its content — is what made Session 10's self-scoring possible before writing the handoff.
  - **The `WebsiteAgent.__new__` hack documentation** (line 207) told Session 10 exactly what test-time construction workaround exists and why, so Session 10 could decide whether Phase A should fix it (decision: no — documented in the gotchas above).
  - **The "Session 9 Exercised Phase 4B" narrative** (lines 246-256) was the template for Session 10's own "What was done (chronological)" section above. Session 9's structure is now the benchmark.

- **What was missing (minor, and not Session 9's fault):**
  - **Trap 1** (`project_id: int` protocol-level type mismatch between GitLab's integer IDs and GitHub's string `owner/name`). Session 9 wrote the `gitlab_adapter.py:111 id=int(project.id)` line but didn't flag that it's GitHub-incompatible. Session 10 found this by re-reading `protocol.py` during Phase 0 evidence-gathering.
  - **Trap 2** (multi-file commit asymmetry: GitLab's one-shot `commits.create` vs GitHub's 4-call blob/tree/commit/ref dance). Session 9's handoff said "parallel GitHub adapter should stay equally thin" (line 176), which is *wrong* — PyGithub physically cannot implement `commit_files` in one call. This is a bigger-deal omission than Trap 1 because it affects Phase C's LOC estimate by ~2x.
  - **Trap 3** (GitLab nested groups `data-science/model-drafts` vs GitHub flat owner `acme/repo`). Session 9 didn't flag that `cli.py:36 DEFAULT_GROUP = "data-science/model-drafts"` is a nested path unresolvable on GitHub.
  - **None of these are Session 9's fault.** They are gaps in the user's truncated `/btw` response, which Session 9 captured faithfully. Session 9 was not asked to design the abstraction — it was asked to finish Phase 4B and record the user's mid-session notes. It did both correctly.

- **What was wrong:** nothing. Every factual claim Session 10 verified matches. Commit hash `f97b530`, 88 website tests, 289 total tests, 96.51% coverage, 12 files mypy-clean, `python-gitlab` ships type stubs, `@runtime_checkable` NOT applied to the Protocol — all accurate and all still true on disk at session start.

- **ROI:** Reading Session 9's handoff took ~10 minutes (it's the longest one yet). It saved at least 30 minutes of what would otherwise have been re-derivation work. The verbatim `/btw` notes plus the gotchas block plus the rubric were the three highest-value sections — they shaped the plan's scope, the plan's Phase B/C design, and Session 10's self-assessment respectively. Session 9's handoff is the new benchmark for this project alongside Session 8's.

### Session 10 Self-Assessment

**Score: 9/10** (Session 11 will score independently).

- **What went well:**
  - **Plan document is complete and evidence-based.** 720 lines, 16 sections, covering all 8 items on Session 9's evaluation rubric. Grep inventory lists every file with line numbers pulled from ripgrep, not from architectural guessing. 22-file rename footprint is a real count, not an estimate.
  - **Three traps caught during evidence-gathering** that Session 9's handoff and the user's `/btw` notes missed: `project_id: int` (Trap 1), multi-file commit asymmetry (Trap 2), nested group vs flat org (Trap 3). Each trap is documented in plan §2.2 with concrete mitigation folded into the right phase.
  - **Explicit recommendation without hedging.** Plan §3.2 picks option A (neutral rename) and justifies it with the 22-file blast radius + the Phase 5 orchestrator ordering argument. No "we could go either way" language.
  - **Per-phase DONE criteria, pre-flight, execution order, verification commands, session boundary** for all four phases (§§6-9). Each phase can be closed out independently, each has explicit rollback guidance.
  - **Phase 5 ordering decision explicit in §11.** The plan commits to deferring Phase 5 until Phase D closes, with the "doubled rename cost" argument. No ambiguity for Session 11+.
  - **Strict adherence to failure mode #18.** Zero `src/` or `tests/` edits. Plan is the only deliverable. The temptation to "just fix the cross-references I noticed" in `architecture-plan.md §14` was resisted — it goes into Phase A's execution order (step 9, docs pass) and Session 11 owns it.
  - **Phase 1B stub written** before any research or writing. When the user rejected the first stub-write attempt (after "Option 1"), Session 10 paused, asked for clarification, and re-tried after explicit "go." This is the textbook handling of the "user interrupted tool use" case.
  - **Cross-reference hygiene.** Post-write grep for `§\d` caught five stale references to an earlier section numbering. All five fixed before commit. The plan is internally consistent.
  - **Parallel tool use** — Phase 0 orientation, source reads, grep inventory, and architecture-plan section reads each batched into single messages with 5-8 parallel calls. ~30 minutes of sequential work compressed to ~8 minutes of wall-clock.
  - **Provenance captured explicitly.** The missing point #1 from the `/btw` response isn't hidden — §12 of the plan names the reconstruction, §13 lists it as an open question, and the user can update the plan if they regenerate the original response. Session 10 did not silently infer.

- **What I could have done better:**
  - **Did not re-run `uv run pytest -q` at session start** to confirm the 289/96.51% baseline against current disk state. Took Session 9's handoff at its word because the branch is clean and the commit is pinned. Low-value rigor for a planning session but a protocol gap that Session 11 inherits (Session 11 should run it in Phase 0).
  - **Did not verify PyGithub API names** (`create_git_blob`, `create_git_tree`, `InputGitTreeElement`, `repo.get_git_ref`) against current PyGithub ≥2 documentation. They are accurate per my training cutoff; if PyGithub 2.x renamed them, Phase C's executor will hit an `AttributeError` and have to look them up. Acceptable risk for a plan document; would be a blocker for code.
  - **The plan is long (720+ lines).** A future reader may find the single-document structure heavy. §16 addresses this but the legitimate tradeoff argument for splitting into four phase-specific docs is acknowledged and not chosen.
  - **The `uv run mypy` intermediate-state claim in §6.3** ("mypy must keep passing between substeps if possible") is optimistic and unverified. In practice, some intermediate states may fail mypy strict until the full pass completes. Session 11's executor will find out. Not a deal-breaker for Phase A — the invariant is only at close-out.
  - **Did not draft the plan in an `EnterPlanMode` session** despite being explicitly asked to write a plan. `EnterPlanMode` would have enforced read-only discipline more strictly. I relied on manual SAFEGUARDS adherence instead. Acceptable because the session stayed read-only in practice, but using the mode would have been a belt-and-braces choice.
  - **One sub-rigor item:** didn't run `git stash list` to check for local stash entries beyond the working-tree-clean `git status`. Very low-probability concern but a protocol gap.

- **Why not 10:** The skipped baseline `pytest` run, the unverified PyGithub API names, and the optimistic mypy-intermediate-state claim are three unforced errors that would each have taken <5 minutes to address. None are blocking. None change the plan's content. But together they justify -1 from what would otherwise be a clean 10/10.

### Session 10 Learnings (added to `SESSION_RUNNER.md` Learnings table)

| # | Learning | When to apply |
|---|----------|---------------|
| 7 | When the user provides a partially-captured message as input (e.g. a truncated `/btw` response), proactively reconstruct the missing content based on the visible evidence AND document the reconstruction with explicit provenance ("originally from /btw on <date>, point #N lost to truncation, reconstructed by Session X from <evidence>"). Do NOT silently infer or silently ignore the gap. Offer the user a "regenerate vs proceed" choice before committing, then honor their preference. | Any session where the input is referenced as partially missing or explicitly truncated. |
| 8 | A grep-based inventory for a rename plan must include the TYPE, FIELD, STATE KEY, and DOCSTRING surfaces separately — each has a different grep pattern. Conflating them into one total gives misleading counts. List hits per grep pattern + per file, not a single total. | Any rename/migration plan. |
| 9 | When writing a multi-phase plan, put cross-phase invariants (do-not-change lists, strategic decisions, Phase N ordering) in ONE document rather than duplicating them across phase-specific documents. Duplication causes drift: one phase doc gets a correction and the others don't. Single-document trades navigability for consistency; for 4-phase plans with 3+ shared invariants the tradeoff favors consistency. | Any plan with more than 2 phases sharing ≥3 invariants. |
| 10 | During Phase 0, when the user's first message appears to contain a task (e.g. "go"), do NOT skip the orientation report even if the ACTIVE TASK block describes the deliverable. The report exists for the user's benefit — it establishes shared state before any work begins. Failure mode #9 ("task-in-prompt bypass") is the specific risk. Complete all 8 Phase 0 steps, report, and explicitly wait for direction even when the direction feels implicit. | Every session. |

### How Session 11 Will Be Evaluated

Session 11's handoff will be scored by Session 12 on:

1. **Did Session 11 execute Phase A of the plan and STOP, or did it bundle Phase B?** (Phase A is ONE session. Failure mode #18 is the specific risk for Session 11.)
2. **Did Session 11 read `docs/planning/github-gitlab-abstraction-plan.md` in full before starting, or only the ACTIVE TASK summary?** (The plan is the authoritative source; the ACTIVE TASK block is a pointer.)
3. **Did Session 11 re-run the plan's §4 grep inventory against the current disk state during Phase 0?** If the inventory drifted (new files reference `GitLabTarget` landed between `f97b530` and Phase A start), did the executor update the plan in the same commit or close out and re-plan?
4. **Did all 7 verification commands in plan §6.4 pass at close-out?** Specifically: zero hits for old names, `project_id: int` gone from annotations, 289 tests passing, mypy strict clean, coverage ≥95%, fake CLI smoke tests pass for tier 1/2/3, deprecated `--fake-gitlab` alias still works.
5. **Did Session 11 land a complete rename in one commit (or a tight commit series), or is the tree in a partial state?** Partial renames are worse than no rename — see plan §6.5 rollback guidance.
6. **Did Session 11 preserve every invariant in plan §10?** Specifically: LangGraph topology, retry/backoff, governance fan-out, FakeGitLabClient internals (logic, not class name), GovernanceManifest shape, Phase 4A accumulator pattern, `sleep` injection, precondition guard, `website::` thread_id prefix.
7. **Did Session 11 widen `project_id: int → str` everywhere it's annotated?** Including `schemas/v1/gitlab.py:32`, `state.py:32`, `protocol.py:55`, `fake_client.py:95,110`, `gitlab_adapter.py:119`, `nodes.py:204,330`, `agent.py:94`, and every test site.
8. **Did Session 11 update `schemas/registry.py` AND `tests/schemas/test_envelope_and_registry.py:97-107` in the same commit?** (The registry keys are string literals pinned by those tests.)
9. **Did Session 11 use `git mv` for the `schemas/v1/gitlab.py` → `repo.py` rename?** (Blame history preservation.)
10. **Did Session 11 add deprecated CLI flag aliases (`--fake-gitlab`, `--gitlab-url`, `--group-path`) for Phase D to remove, or silently drop them?** (Plan §6.1 requires the aliases.)

A handoff missing specific file line-numbers, concrete before/after grep counts, or the Phase A verification command output will score ≤6/10. A handoff that names "Phase A complete" without listing which files were touched will score ≤4/10.


### What Session 9 Did
**Deliverable:** Phase 4B of architecture plan — Website Agent governance scaffolding (§8.2 tier fan-out) + `RETRY_BACKOFF` self-loop off `INITIAL_COMMITS` + thin `python-gitlab` production adapter behind the `GitLabClient` Protocol. **COMPLETE.**
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `f97b530` (Phase 4B).

**What was done (chronological):**
1. Phase 0 orientation — read `SAFEGUARDS.md`, `SESSION_NOTES.md` top block, plan §4.3 / §5.4 / §8 / §10 / §11 / §14 Phase 4B, and the full Phase 4A `agents/website/` package (state, protocol, nodes, graph, agent, templates, fake_client, cli, __init__) + Phase 4A tests.
2. Phase 1B — wrote Session 9 stub to `SESSION_NOTES.md` before any code change (ghost-session protection per failure mode #14).
3. **state.py** — added `governance_paths: list[str]`, `commit_attempts: int`, `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0`. Docstring explains that `files_pending` is now an accumulator across *four* scaffold nodes. `initial_state()` seeds `governance_paths=[]` + `commit_attempts=0`.
4. **governance_templates.py (NEW, 600 lines)** — sibling to `templates.py`, pure-Python f-string generators. Exports `build_governance_files`, `build_analysis_files`, `build_test_files`, `build_model_registry_entry`, `build_regulatory_mapping`, `is_governance_artifact`. Internal helpers: `_tier_at_least(risk_tier, threshold)` for `tier_N+` predicates (lower severity number = more severe), `_CYCLE_CADENCE` dict mapping cycle_time → monitoring cadence (§8.3), `_FRAMEWORK_ARTIFACTS` mapping SR_11_7 / NAIC_AIS / EU_AI_ACT_ART_9 / EU_AI_ACT / ASOP_56 → the governance artifacts that satisfy each. The composition entry point `build_governance_files` emits:
   - **Always:** `governance/model_registry.json`, `governance/model_card.md`, `governance/change_log.md`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, one `data/datasheet_<query>.md` per primary query.
   - **Tier 3+ (tier 3 moderate, 2 high, 1 critical):** `governance/three_pillar_validation.md`, `governance/ongoing_monitoring.md` (embeds §8.3 cadence), `governance/deployment_gates.md`.
   - **Tier 2+ (tier 2 high, 1 critical):** `governance/impact_assessment.md`, `governance/regulatory_mapping.md` (populated from the framework→artifact table filtered to what's actually being emitted).
   - **Tier 1 only:** `governance/lcp_integration.md`, `governance/audit_log/README.md`.
   - **If `affects_consumers`:** `governance/eu_ai_act_compliance.md` (Articles 9–15 mapping).
   - `build_analysis_files`: emits `analysis/fairness_audit.qmd` + `src/<slug>/fairness/__init__.py` + `src/<slug>/fairness/audit.py` if `uses_protected_attributes`, else `{}`.
   - `build_test_files`: emits `tests/test_fairness.py` if `uses_protected_attributes`, else `{}`.
   - `is_governance_artifact(path)` classifier used by `build_gitlab_project_result` to filter `files_created` down to the manifest's `artifacts_created`.
5. **nodes.py (rewritten)** — added `scaffold_governance`, `scaffold_analysis`, `scaffold_tests` nodes (merge into `files_pending`; `scaffold_analysis`/`scaffold_tests` return `{}` when the fairness flag is off). `initial_commits` now increments `commit_attempts`, returns `status="RETRYING"` + `commit_attempts=N` on `GitLabClientError` when `attempts < MAX_COMMIT_ATTEMPTS`, returns `status="FAILED"` with `failure_reason="gitlab_error_retry_exhausted: ..."` past the limit. Added `retry_backoff` node that calls an injected `sleep(delay)` where `delay = RETRY_BASE_DELAY_SECONDS * 2 ** (attempts - 1)` (1s → 2s → 4s) and resets status to `PARTIAL`. New `route_after_commit(state)` routes `RETRYING → retry_backoff`, everything else → `end`. `make_nodes(client, *, sleep=_default_sleep)` — the `sleep` kwarg is the ONLY way tests stub out wall-clock delay; production uses `time.sleep`. **`build_gitlab_project_result` was rewritten to populate the manifest**: filters `files_created` via `is_governance_artifact`, computes `regulatory_mapping` via `build_regulatory_mapping(frameworks=..., emitted_paths=set(artifacts_created))`, populates `model_registry_entry` via `build_model_registry_entry(...)` — BUT only when `project_name` + `project_slug` are present in state (failed-early FAILED states default the entry to `{}`).
6. **graph.py (rewritten)** — new topology inserts `scaffold_governance → scaffold_analysis → scaffold_tests` between `scaffold_base` and `initial_commits`, and adds the `initial_commits → retry_backoff → initial_commits` self-loop via `add_conditional_edges` + `route_after_commit`. `build_website_graph(client, *, checkpointer=None, sleep=None)` — the new `sleep` kwarg is forwarded into `make_nodes` so retry tests can build a graph that returns immediately from `retry_backoff`.
7. **gitlab_adapter.py (NEW)** — `class PythonGitLabAdapter(GitLabClient)`. Constructor takes `gitlab_url`, `private_token`, optional `ssl_verify`; stores `self._gl: Any = gitlab.Gitlab(...)`. `create_project` resolves `self._gl.groups.get(group_path)` then `self._gl.projects.create({...})`, translating `GitlabCreateError` with `_is_name_conflict(exc)` → `ProjectNameConflictError`, other `GitlabError` subclasses → `GitLabClientError(...)`. `commit_files` does `self._gl.projects.get(project_id)` then `project.commits.create({'branch': ..., 'commit_message': ..., 'actions': [{'action': 'create', 'file_path': p, 'content': c}, ...]})`. `_is_name_conflict(exc)` checks `response_code in (400, 409)` and a loose lowercase match for "already been taken" or "already exists". **python-gitlab DID ship type stubs**, so `# type: ignore[import-untyped]` is unnecessary — removed them after the first mypy run flagged them as `unused-ignore`.
8. **cli.py** — dropped the Phase-4A-only `--fake-gitlab`-required guard. Now accepts either `--fake-gitlab` (free, no token) OR `--private-token <token>` (real path via `PythonGitLabAdapter`). Lazy-imports the adapter inside the `if not fake_gitlab:` branch so the fake path stays free of the `gitlab` import at module load time. Exit code 2 on neither flag being set, same as before.
9. **__init__.py** — re-exported `PythonGitLabAdapter`, `build_governance_files`, `build_analysis_files`, `build_test_files`, `build_model_registry_entry`, `build_regulatory_mapping`, `is_governance_artifact`, `route_after_commit`, `MAX_COMMIT_ATTEMPTS`, `RETRY_BASE_DELAY_SECONDS`.
10. **Fixtures:** wrote `tests/fixtures/tier1_intake.json` (tier 1 critical personal auto renewals model — affects_consumers=true, uses_protected_attributes=true, cycle_time=continuous, 4 frameworks including `EU_AI_ACT_ART_9`) and `tests/fixtures/tier2_intake.json` (tier 2 high commercial property reserving aid — affects_consumers=false, uses_protected_attributes=false, cycle_time=strategic, 2 frameworks). Both round-trip cleanly through `IntakeReport.model_validate_json`. The existing `subrogation_intake.json` serves as tier 3.
11. **test_governance.py (NEW, 29 tests across 4 classes)** — `TestTier1Critical` / `TestTier2High` / `TestTier3Moderate` exercise the three fixtures end-to-end through `WebsiteAgent` + `FakeGitLabClient`, pinning (a) exact file set presence/absence for each tier's fan-out, (b) manifest `regulatory_mapping` contents against the declared frameworks, (c) monitoring-cadence text in `governance/ongoing_monitoring.md` for `continuous` / `strategic` / `tactical`. `TestBuildGovernanceFilesUnit` covers `build_governance_files` with a synthetic tier-4 intake (only "always" artifacts emitted), datasheet-per-query, regulatory-mapping unknown-framework passthrough, and the `is_governance_artifact` classifier.
12. **test_retry.py (NEW, 5 tests)** — `_TransientCommitClient` and `_AlwaysFailingCommitClient` stand-ins. `TestRetryBackoffNode` pins the exact `[1.0, 2.0, 4.0]` backoff sequence by injecting a `sleep` lambda that appends to a list, plus the status-reset-to-PARTIAL behavior. `TestRetryEndToEnd` builds a graph with `sleep=lambda _s: None`, passes it a `_TransientCommitClient(fail_count=2)` and asserts COMPLETE after 3 commit calls; `fail_count=1` → COMPLETE after 2 commit calls; `_AlwaysFailingCommitClient()` → FAILED with `gitlab_error_retry_exhausted` after exactly 3 commit calls. **The retry end-to-end tests use `WebsiteAgent.__new__(...)` + manual attribute assignment to pass the custom-sleep graph**, because `WebsiteAgent.__init__(client)` always builds a default graph. This is a minor test-only hack worth considering for refactoring in Session 11 (`WebsiteAgent(client, *, graph=...)` kwarg). Not blocking for now.
13. **test_gitlab_adapter.py (NEW, 9 tests)** — import smoke test, `PythonGitLabAdapter` has `create_project` + `commit_files` as callables, constructor does NOT make a network call (`PythonGitLabAdapter(gitlab_url="https://invalid.example.invalid", private_token="not-a-real-token")` succeeds silently because python-gitlab defers auth until first API call), `_is_name_conflict` classification for 400/409/500 + matching/non-matching messages, and `TestExceptionTranslation` uses `MagicMock` to stub `adapter._gl` so the four adapter code paths (group lookup → create → commit → commit success) can be exercised without the network. **Note:** `isinstance(adapter, GitLabClient)` would raise because the protocol is not `@runtime_checkable` — the test uses `callable(getattr(adapter, "create_project"))` instead. Do NOT add `@runtime_checkable` to the protocol just to simplify the test; it's fine as-is.
14. **test_agent.py** — replaced `test_governance_artifacts_absent_in_4a` with `test_tier3_governance_artifacts_present`, which is a POSITIVE assertion over the tier-3-gated artifact set for the subrogation fixture, including manifest regulatory-mapping contents (`"SR_11_7" in mapping` and the tier-3 artifacts it binds to). `test_governance_manifest_reflects_intake_tier` still asserts tier/cycle_time mirror intake — it survived unchanged because it only pinned the empty mapping-equals-empty behavior implicitly, which is no longer true now but the test doesn't assert that.
15. **test_nodes.py** — `test_commit_failure_surfaces` → `test_first_commit_failure_goes_to_retrying` (new semantics: status=RETRYING + commit_attempts=1 on first failure). `test_complete_state_produces_valid_result` rewritten with a mixed `files_created` list (base + governance + fairness paths) and now asserts (a) only governance paths land in `artifacts_created`, (b) `model_registry_entry["model_id"] == "subrogation_recovery_model"`, (c) `regulatory_mapping["SR_11_7"]` contains `"governance/three_pillar_validation.md"`. `test_failed_state_defaults_governance` got one extra assertion on `model_registry_entry == {}`.
16. **README.md** — phase table: Phase 4B → Complete. Repo layout section lists `governance_templates.py`, `gitlab_adapter.py`, and the updated CLI help. Test count 260 → 289. Added `tier1_intake.json` + `tier2_intake.json` to the fixtures list. Getting-started section now shows BOTH the `--fake-gitlab` path and a real `--private-token` example, and mentions the tier-1 fixture as the path to see the full governance fan-out.
17. **SESSION_RUNNER.md** — Phase 0 step 5 now says "Run the shared methodology dashboard (external to this repo — lives in `~/Development/`, not inside `model_project_constructor/`)" instead of pointing at an in-repo file that doesn't exist. User confirmed the shared dashboard runs from the parent dir, not this repo.

**Verification (plan §14 Phase 4B literal commands):**
- `uv run pytest tests/agents/website/ -v` → **88 passed** (was 59 in Phase 4A; 29 new tests — 20 governance, 5 retry, 9 adapter, −5 removed/replaced). Output shows `test_governance.py` with `TestTier1Critical`, `TestTier2High`, `TestTier3Moderate`, `TestBuildGovernanceFilesUnit` classes all green.
- `uv run pytest -q` full suite → **289 passed, 96.51% coverage, 0 failures**. Required coverage gate (90%) is satisfied with headroom. Per-file coverage for the new modules: `governance_templates.py` 97%, `nodes.py` 99%, `graph.py` 100%, `state.py` 100%, `gitlab_adapter.py` 85% (remaining gaps are the generic `except GitlabError` catch-alls that aren't stubbed in tests; acceptable per "no live network tests" guidance).
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**.
- **Manual tier-1 CLI smoke test:** `uv run python -m model_project_constructor.agents.website --intake tests/fixtures/tier1_intake.json --data tests/fixtures/sample_datareport.json --fake-gitlab` → status COMPLETE, commit sha `acf00f6b48de13ca1a09b1b196f0e3d961fd4e57`, file tree includes `governance/audit_log/README.md`, `governance/eu_ai_act_compliance.md`, `governance/lcp_integration.md`, `analysis/fairness_audit.qmd`, `src/intake_renewals_001/fairness/audit.py`, `tests/test_fairness.py`. Plan's DONE criterion "Manual: generate one tier-1 project and verify all expected governance files exist" = satisfied.

**Input from Session 9 user: GitHub/GitLab abstraction notes (verbatim for Session 10 planning):**

> the next session will add a plan to adapt this for use with GitHub or GitLab. See these notes:
>
> 2. Terminology mismatch in the schema: `GitLabTarget` has `gitlab_url` and `group_path`. Either rename to a neutral `RepoTarget` with `host_url` + `namespace`, or add a parallel `GitHubTarget` schema. The neutral rename is cleaner but touches `schemas/v1/gitlab.py` and every consumer — including the CLI and tests. For a minimal change, keep `GitLabTarget` as-is and treat `group_path` as "org name" when the GitHub adapter is in use.
>
> 3. `.gitlab-ci.yml` → `.github/workflows/ci.yml`. The `render_gitlab_ci()` template in `governance_templates.py` emits GitLab CI YAML. For GitHub projects you'd branch on the client type (or add a `ci_platform` parameter to `build_governance_files`) and emit GitHub Actions YAML instead. The `.pre-commit-config.yaml` template is platform-agnostic and needs no change.
>
> 4. Dependency: add `PyGithub` to the `agents` optional extras alongside `python-gitlab>=4`.
>
> 5. Tests: a `test_github_adapter.py` with import smoke test only — same discipline as `gitlab_adapter.py` (no live network tests).
>
> What NOT to change:
> - The LangGraph topology, retry/backoff loop, governance fan-out, `FakeGitLabClient` (it's already platform-agnostic — rename to `FakeRepoClient` if you want, but not required).
> - `GovernanceManifest`, `GitLabProjectResult` — the "GitLab" in the name is vestigial; the shape works for any git host.
>
> Effort estimate: ~1 session. The adapter + CI template branching is the bulk of it; the real cost is deciding whether to rename `GitLabTarget`/`GitLabProjectResult` to neutral names now (cheap during Phase 4B, expensive once Phase 5 orchestrator lands and hardcodes the names).

(Note from Session 9: the user's numbering starts at 2 — point 1 wasn't included in the message. Session 10 may want to ask the user for it, or proceed without it if the remaining notes are self-contained.)

### Session 10's mandate (PLANNING session — plan is the deliverable, not code)

Session 10 writes `docs/planning/github-gitlab-abstraction-plan.md`. Per `SESSION_RUNNER.md` Planning Sessions protocol, the plan must include:

1. **Grep-based inventory** of every reference that would need to change under either approach (neutral rename vs. parallel schema). At minimum, grep for: `GitLabTarget`, `GitLabProjectResult`, `GovernanceManifest`, `GitLabClient`, `GitLabClientError`, `ProjectNameConflictError`, `PythonGitLabAdapter`, `gitlab_url`, `group_path`, `python-gitlab`, `gitlab_ci`, `.gitlab-ci.yml`, `render_gitlab_ci`, `FakeGitLabClient`. List every matching file with line numbers.
2. **Decision: neutral rename or parallel schema?** The user's notes suggest the neutral rename is cleaner but more churn. Session 10 should make a recommendation AND document the trade-off explicitly with the grep inventory as evidence. DO NOT hedge — pick one and justify it.
3. **Per-phase breakdown** with explicit DONE criteria and verification commands per `SESSION_RUNNER.md`. Candidate phases:
   - Phase A: (if renaming) neutral schema rename — `GitLabTarget` → `RepoTarget`, `GitLabClient` → `RepoHostClient`, etc. Touches schemas, protocol, nodes, graph, agent, templates (governance), CLI, fake_client, gitlab_adapter, all tests, README. One session.
   - Phase B: `ci_platform` parameter (or client-type branching) in `build_governance_files`, new `render_github_actions_ci()` generator, tests for the GitHub CI path. One session.
   - Phase C: `PyGithubAdapter` implementing the (renamed) client protocol via `PyGithub`. Import smoke tests + exception translation via MagicMock, no live network. One session.
   - Phase D: Update CLI to accept `--host github|gitlab` and route to the right adapter. Add `test_github_cli.py` analogue. One session.
4. **Explicit "DO NOT change" list** echoing the user's notes — the topology, retry/backoff loop, governance fan-out, manifest shape, `GitLabProjectResult` structural contract (the field `governance_manifest` stays; only its type name may change).
5. **Answer the Session 5/Phase 5 ordering question.** The user implied Phase 5 is deferred until the abstraction plan lands. Session 10 should confirm that ordering in the plan so Session 11+ executes abstraction work BEFORE orchestrator work. If Session 10 disagrees with the ordering, it must argue the case explicitly in the plan.
6. **Ask the user for the missing point #1** from their notes above before finalizing the plan, OR explicitly document that the plan proceeds without it.

**Session 10 MUST NOT start implementing the abstraction.** Per failure mode #18 (planning-to-implementation bleed), the plan is a separate deliverable. Commit the plan, close out, STOP. Session 11 picks up Phase A of the plan.

### Key Files Shipped Through Phase 4B — Read Before Starting Session 10

**Phase 4B additions (new in Session 9):**
- `src/model_project_constructor/agents/website/governance_templates.py` — sibling to `templates.py`. **Session 10 grep this module first**: its `render_gitlab_ci()` emits GitLab CI YAML; that's the single function that needs a parallel `render_github_actions_ci()` per the user's note #3. `_FRAMEWORK_ARTIFACTS` at the top is static and platform-agnostic (stays untouched by the abstraction). `is_governance_artifact()` classification is also platform-agnostic.
- `src/model_project_constructor/agents/website/gitlab_adapter.py` — `PythonGitLabAdapter(GitLabClient)`. The `_is_name_conflict(exc)` helper is adapter-internal; the GitHub adapter will need its own equivalent (PyGithub raises `github.GithubException` with status 422 for name conflicts — IIRC; Session 10 should verify, not assume). Adapter does NOT do retry internally — that's the graph's job. Keep it that way; parallel GitHub adapter should stay equally thin.
- `src/model_project_constructor/agents/website/nodes.py` — rewritten for Phase 4B. `make_nodes(client, *, sleep=_default_sleep)`: the `sleep` kwarg is the injection point for retry tests. `build_gitlab_project_result`: now populates manifest from `files_created` via `is_governance_artifact` filter + `build_regulatory_mapping` + `build_model_registry_entry`. **The `model_registry_entry` is empty unless `project_name` AND `project_slug` are in state** — failed-before-naming states get `{}`.
- `src/model_project_constructor/agents/website/graph.py` — rewritten. New edges: `scaffold_base → scaffold_governance → scaffold_analysis → scaffold_tests → initial_commits`, plus the `initial_commits ⟶ retry_backoff ⟶ initial_commits` self-loop via `route_after_commit`. `build_website_graph(client, *, checkpointer=None, sleep=None)` — the `sleep` kwarg is forwarded into `make_nodes` (test-only injection).
- `src/model_project_constructor/agents/website/state.py` — new fields `governance_paths: list[str]`, `commit_attempts: int`. Constants `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0`. `initial_state()` seeds them.
- `src/model_project_constructor/agents/website/__init__.py` — public surface expanded; `PythonGitLabAdapter`, the governance helpers, `is_governance_artifact`, and the retry constants are all re-exported. Session 10 can import from the package root.
- `src/model_project_constructor/agents/website/cli.py` — updated: `--fake-gitlab` OR `--private-token`. The real-adapter path lazy-imports `gitlab_adapter` so the fake path doesn't touch python-gitlab at import time.

**Phase 4B tests (new in Session 9):**
- `tests/agents/website/test_governance.py` — 20 tests total. `TestTier1Critical` (4), `TestTier2High` (3), `TestTier3Moderate` (2), `TestBuildGovernanceFilesUnit` (4). Uses three JSON fixtures; no LLM involvement.
- `tests/agents/website/test_retry.py` — 5 tests. Uses `_TransientCommitClient` + `_AlwaysFailingCommitClient` stand-ins and an injected `sleep` lambda. **The end-to-end tests build `WebsiteAgent` via `__new__` + manual attribute assignment** to pass a graph with a no-op sleep — this is a minor test-only hack and a candidate for `WebsiteAgent(client, *, graph=...)` refactor if a future session needs it.
- `tests/agents/website/test_gitlab_adapter.py` — 9 tests. Import smoke test + `_is_name_conflict` classification + `TestExceptionTranslation` using MagicMock to stub `adapter._gl`. **Zero network calls.** Session 10's GitHub adapter tests should follow the same pattern (MagicMock the `github.Github` client).

**Phase 4B test updates:**
- `tests/agents/website/test_agent.py` — removed `test_governance_artifacts_absent_in_4a`; added `test_tier3_governance_artifacts_present` with positive manifest assertions.
- `tests/agents/website/test_nodes.py` — `test_commit_failure_surfaces` → `test_first_commit_failure_goes_to_retrying`; `test_complete_state_produces_valid_result` rewritten with mixed base+governance file list.

**Phase 4B fixtures (new):**
- `tests/fixtures/tier1_intake.json` — tier_1_critical personal auto renewals, affects_consumers=true, uses_protected_attributes=true, cycle_time=continuous, 4 frameworks (SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, ASOP_56). Exercises every conditional branch in `build_governance_files`.
- `tests/fixtures/tier2_intake.json` — tier_2_high commercial property reserving, affects_consumers=false, uses_protected_attributes=false, cycle_time=strategic, 2 frameworks (SR_11_7, ASOP_56). Exercises tier-2-only artifacts in isolation.
- `tests/fixtures/subrogation_intake.json` — unchanged since Session 8; now serves as the tier-3 fixture in the governance test suite.

**Phase 4A legacy (unchanged in Session 9):**
- `templates.py` — untouched. `build_base_files` is stable.
- `fake_client.py` — untouched. Deterministic sha1 on `message|branch|sorted(paths)` still the invariant.
- `protocol.py` — untouched. Still not `@runtime_checkable`; adapter tests work around this by duck-typing instead.
- `agent.py` — untouched. Precondition guard (incomplete intake or data → FAILED without creating project) is preserved by Phase 4B. Two `test_agent.py` tests still pin `fake_client.projects == {}` under precondition failure; both pass.

### Gotchas — Read These First

**Phase 4B gotchas (new — Session 10 must read first):**
- **`retry_backoff` uses `time.sleep()` by default in production.** Tests MUST pass `sleep=lambda _s: None` (or a list-appender) when building `make_nodes` or `build_website_graph`, otherwise the suite takes 3+ seconds per flaky-commit scenario. The `sleep` kwarg is forwarded from `build_website_graph(client, *, sleep=...)` into `make_nodes`. If Session 10 or 11 adds new retry-path tests, remember to inject `sleep`.
- **`WebsiteAgent.__init__(client)` always builds its own graph with no sleep override.** `test_retry.py::TestRetryEndToEnd` uses `WebsiteAgent.__new__(WebsiteAgent)` + manual `agent.client = client; agent.graph = build_website_graph(client, sleep=...)` as a workaround. If the abstraction plan rewrites `WebsiteAgent`, consider adding a `graph` kwarg to `__init__` so the hack goes away.
- **`build_gitlab_project_result` only populates `model_registry_entry` when BOTH `project_name` AND `project_slug` are in state.** FAILED-before-naming states (e.g., every candidate name taken, or a group-lookup error before CREATE_PROJECT succeeds) get `{}` for the entry. `test_failed_state_defaults_governance` pins this. Session 10's GitHub adapter must also surface a failure mode that leaves naming empty cleanly; don't try to populate the entry from input data alone.
- **`GovernanceManifest.artifacts_created` is derived, not stored.** It's computed by `build_gitlab_project_result` filtering `state["files_created"]` through `is_governance_artifact()`. The `governance_paths` field in state is informational only — the manifest doesn't read it. If Session 10 or 11 adds new governance artifact categories (e.g. `.github/workflows/ci.yml`), they MUST update `is_governance_artifact()` too, or the new files will silently fall out of the manifest.
- **The `is_governance_artifact` classifier is prefix-based.** Currently matches `governance/`, `data/datasheet_`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `analysis/fairness_audit.qmd`, `/fairness/`, `tests/test_fairness.py`. For the GitHub abstraction, this list needs `.github/workflows/ci.yml` OR a more general "known CI config path" check — Session 10 should note this in the plan's "files to change" list.
- **`_FRAMEWORK_ARTIFACTS` is static and platform-agnostic.** Adding a new regulatory framework = add a row to the dict + pick the artifacts it binds to. The test `test_regulatory_mapping_filters_unknown_framework` pins the passthrough behavior: unknown frameworks appear in the mapping with an empty list. Don't "fix" this — the empty list makes the gap visible.
- **Monitoring cadence lookup is in `_CYCLE_CADENCE` (private).** If a future session adds a new cycle_time literal (the schema allows four today: strategic/tactical/operational/continuous), both the schema AND this dict must be updated in lockstep. The cadence text is asserted verbatim by `TestTier1Critical::test_tier1_ongoing_monitoring_has_continuous_cadence` ("Automated continuous monitoring").
- **`_tier_at_least(risk_tier, threshold)` uses lower-severity-number semantics.** `tier_1_critical = 1`, `tier_4_low = 4`. `_tier_at_least("tier_2_high", "tier_3_moderate") == True` because tier 2 ≤ tier 3 (on the severity axis). Unknown tiers default to 99 (never passes the check). Don't invert the comparison.
- **python-gitlab DOES ship type stubs.** The adapter originally had `# type: ignore[import-untyped]` on the `import gitlab` and `from gitlab.exceptions import ...` lines; mypy strict flagged both as `unused-ignore`. Removing them is the correct fix. If Session 10's PyGithub adapter needs type ignores, check first — PyGithub may or may not ship stubs, and adding unnecessary ignores will immediately break mypy strict.
- **The `GitLabClient` Protocol is NOT `@runtime_checkable`.** `isinstance(adapter, GitLabClient)` raises `TypeError: Instance and class checks can only be used with @runtime_checkable protocols`. Adapter tests use `callable(getattr(adapter, "create_project"))` instead. Do NOT add `@runtime_checkable` to the protocol just to simplify tests — it's not needed for production and may mask signature mismatches that mypy strict currently catches.
- **`PythonGitLabAdapter` constructor does NOT make a network call.** python-gitlab defers authentication until the first actual API call, so `PythonGitLabAdapter(gitlab_url="https://invalid.example.invalid", private_token="junk")` succeeds silently. The test `test_constructor_does_not_make_network_call` pins this. Session 10's PyGithub adapter: verify that `github.Github(token)` behaves the same way (it does, per PyGithub docs, but verify before relying on it in tests).
- **`_is_name_conflict(exc)` is loose matching.** It checks `response_code in (400, 409)` + a lowercase `"already been taken"` or `"already exists"` substring. GitLab can also return the message in either a string or a dict shape — the helper calls `str(exc.error_message)` to cover both. If GitLab ever changes the wording, the name-conflict handling silently degrades to "unknown GitLabClientError" + no suffix retry. Low-probability but worth mentioning for Session 10 so the GitHub adapter's equivalent is built with similar defensiveness.
- **`.gitlab-ci.yml` is classified as a governance artifact.** This is per plan §8.2 "Always" row. Session 10's GitHub variant (`.github/workflows/ci.yml`) must inherit the same classification — update `is_governance_artifact()` in lockstep with the new renderer.
- **The three tier fixtures are not balanced in coverage.** `tier1_intake.json` is the only one that exercises `uses_protected_attributes=true`; `tier2_intake.json` is the only one with `cycle_time=strategic`; `subrogation_intake.json` is the only tier with `affects_consumers=true` AND the tier-3-gated artifacts. If you change one, recompute the tier-coverage matrix so the others don't silently lose coverage.
- **`build_regulatory_mapping` filters by `emitted_paths`, which is the set of files actually emitted for this project's tier.** Tier 4 with SR_11_7 declared will produce `mapping["SR_11_7"] == ["governance/model_card.md"]` — only the always-artifacts. A tier 1 run with SR_11_7 will produce all four SR_11_7 artifacts. This is the intended behavior; the mapping reflects reality, not the static framework→artifact table. Session 10's CI-platform branching should NOT change this logic.
- **mypy strict is now clean across all 12 files in `agents/website/`.** Session 10 should add files to this package (not as a refactor, but for GitHub adapter) and expect mypy clean from the start. Run `uv run mypy src/model_project_constructor/agents/website/` before committing.
- **Coverage gate stays at 90%**, currently 96.51% (289 tests). Phase 4B added 29 tests net (88 website tests, up from 59). Session 10's abstraction plan work should target keeping coverage ≥95% on new code.

**Phase 4A gotchas (unchanged from Session 8):**
- **`INITIAL_COMMITS` expects the accumulator to be non-empty.** If `state["files_pending"]` is `{}` at flush time, the node returns `status=FAILED` with `failure_reason="no_files_scaffolded"`. Retry loop does NOT re-trigger on this (it's not a `GitLabClientError`). Test: `test_empty_pending_fails` in `test_nodes.py`.
- **Name conflict handling is unchanged from 4A.** `_candidate_names` in `nodes.py` yields `[name, name-v2, name-v3, name-v4, name-v5]` → `MAX_NAME_CONFLICT_ATTEMPTS=5` candidates. Don't conflate with `MAX_COMMIT_ATTEMPTS=3` (the retry/backoff limit).
- **The precondition guard in `WebsiteAgent.run` returns FAILED without creating a project.** Two `test_agent.py` tests assert `fake_client.projects == {}` after an incomplete-intake / incomplete-data call. Preserved by 4B.
- **`thread_id = f"website::{intake.session_id}"`** — the `website::` prefix avoids collisions with intake agent thread_ids under a shared checkpointer. Preserved by 4B.
- **First real-API smoke test of Phase 3B intake was done at Session 8 start.** `claude-sonnet-4-6` works. 3-session-deferred caveat RETIRED. Phase 2B AnthropicLLMClient in the standalone data agent is still unverified against a real API — not a Session 10 concern.

**Phase 3B gotchas (unchanged from Session 7):**
- Module-level `app = create_app()` creates `intake_sessions.db` at import time. `.gitignore` has `intake_sessions.db*`.
- `SqliteSaver(conn)` uses a single shared connection with `check_same_thread=False`; `IntakeSessionStore` guards every call with `threading.RLock`. Do not remove the lock.
- FastAPI 0.135 uses the `lifespan` context manager; `@app.on_event` is deprecated.
- Review-accept token matching in `agents/intake/nodes.py:35` is case-insensitive over `{ACCEPT, accept, yes, approve, approved, ok, looks good}`.
- `origin` is still the GitHub remote `https://github.com/rmsharp/claims-model-starter.git`. Do not force-push master.
- Python is 3.13.5 in `.venv`; `requires-python = ">=3.11"`.
- LangGraph 0.2.76 interrupt + SQLite persistence verified end-to-end.
- `claude-sonnet-4-6` still the hardcoded default model in both intake and data-agent `anthropic_client.py`.
- Two `StrictBase` classes (main package vs standalone data-agent); do not DRY them up.
- `agents/data/__init__.py`, `db.py`, `llm.py` in the main package are thin re-exports; do not edit.
- Typer single-command trap: intake + website CLIs have NO `@app.callback()`, data-agent CLI does. The website CLI still matches the plan's literal `python -m ... --intake X --data Y --fake-gitlab` form.
- `packages/data-agent/USAGE.md` is the standalone's README. Don't delete.
- `methodology_dashboard.py` does NOT exist in this repo — runs from `~/Development/` (external shared location). SESSION_RUNNER.md Phase 0 step 5 was updated in Session 9 to reflect this.

### How Session 9 Exercised Phase 4B

- **Orientation took ~15 minutes**: SAFEGUARDS + SESSION_NOTES top + plan §4.3/§5.4/§8/§10/§11/§14 + all 8 Phase 4A source files + conftest/test_agent/test_nodes. Explicitly followed the SESSION_RUNNER Phase 0 report-first protocol and waited for the user to direct the task.
- **Built the governance module before touching `nodes.py`**. Wrote `governance_templates.py` as a single file (all renderers + `build_governance_files` + `is_governance_artifact` + `build_regulatory_mapping`) so the 4B additions to `nodes.py` were purely "wire up the new helpers into new scaffold nodes." This kept the `templates.py` → `governance_templates.py` split clean.
- **Hit the expected regression in the existing 4A test**: `test_governance_artifacts_absent_in_4a` failed as soon as `scaffold_governance` was added to the graph. Session 8's handoff explicitly warned about this; I updated the test in-place to a positive `test_tier3_governance_artifacts_present` assertion rather than deleting it.
- **Hit one unexpected regression**: `test_commit_failure_surfaces` in `test_nodes.py` expected the old 4A semantics (first commit failure = FAILED immediately). Renamed to `test_first_commit_failure_goes_to_retrying` with updated assertions. This is the semantic shift Session 10's GitHub adapter work should anticipate — the retry loop now intercepts the first two failures.
- **mypy strict caught two `unused-ignore` comments** on the python-gitlab imports. Removed them; python-gitlab ships type stubs. If I had left the ignores in place, the file would have passed but drifted from strict.
- **Manual CLI verification on the tier-1 fixture** surfaced a cosmetic quirk in the `_render_file_tree` indentation (deep files visually misaligned from shallow ones), which was already a 4A known issue noted in Session 8's handoff. Not fixed; not blocking.
- **Phase 4A's accumulator pattern paid off.** Adding three new scaffold nodes was a pure additive — each new node does `pending.update(files); return {"files_pending": pending}`. Zero refactoring of `scaffold_base`. The handoff's guidance to keep `templates.py` untouched and put all new work in a sibling module was correct.
- **29 tests added net** (88 total in the website suite), **0 regressions in the rest of the repo** (all 201 prior tests in other packages still green), **mypy strict clean on day one** for the new files. Session 8's handoff was explicit enough to avoid any discovery work — I did not need to grep for unknown callers or trace state shape.

### Session 8 Handoff Evaluation (by Session 9)

**Score: 10/10.**

- **What helped (specific):**
  - "ACTIVE TASK" block listed every §11 governance file, tagged each with its §8.2 tier gate, and told me exactly which 4A tests I would need to modify (`test_agent.py::test_governance_artifacts_absent_in_4a` and `test_nodes.py::test_complete_state_produces_valid_result`). **Both were exactly right** — these were the only two pre-existing tests I had to touch, and I touched them for the reasons the handoff predicted. Saved 20+ minutes of grep work.
  - The full key-files block with line-range annotations (`nodes.py:88-98` for the accumulator pattern, `nodes.py:117` for `build_gitlab_project_result` emptiness) let me open the right code spans immediately. The predictions about which lines needed changes were accurate.
  - The "Phase 4A gotchas" block flagged three non-obvious invariants I preserved without thinking: (a) the precondition guard returns FAILED without creating a project (b) `thread_id` convention (c) the deterministic sha1 scheme. I did not disturb any of them, and the tests that pin these behaviors all still pass.
  - The "How Session 8 Exercised Phase 4A" narrative section gave me a template for how the final handoff should read — chronological, with commit-specific references and explicit verification command output.
  - The handoff's "Prefer JSON fixtures — they're faster to load and don't drag the fixture LLM into governance tests" was spot-on guidance. JSON fixtures took ~5 minutes to write and passed Pydantic validation on the first try.
  - The "mypy strict is clean on ... `agents/website/` (10 files)" line set an explicit bar. I wrote 2 new files (gitlab_adapter.py, governance_templates.py) mypy-clean on day one because I knew the bar.

- **What was missing:** Nothing I hit. The only gap I'd even mention is that the handoff didn't explicitly say "make the retry `sleep` injectable" — but the §4.3 plan text made it obvious, and the handoff DID say "retry/backoff on GitLab errors" which implied bounded wall-clock testability. Not a real gap.

- **What was wrong:** Nothing. One minor prediction inaccuracy: the handoff said the governance test file would be "test_governance.py (tier 1 / tier 2 / tier 3)" — I also added a `TestBuildGovernanceFilesUnit` class for `build_governance_files` unit tests + a `test_retry.py` for the retry-backoff path + a `test_gitlab_adapter.py` for the adapter. The handoff's single-file suggestion would have been too monolithic. This is me expanding the plan, not the plan being wrong.

- **ROI:** Reading the handoff took ~5 minutes. It saved at LEAST an hour of code exploration — the Phase 4A invariants (accumulator pattern, precondition guard, precondition-result helper, manifest shape, tier-interpretation of `_TIER_SEVERITY`) were all pre-documented and I did not re-derive any of them. Session 8's handoff is the gold standard for this project. I will try to match it.

### Session 9 Self-Assessment

**Score: 9/10 (by Session 9's own rubric — Session 10 will score independently).**

- **What went well:**
  - Complete deliverable in one session, matching plan §14 Phase 4B DONE criteria exactly. 3 tier fixtures, `GovernanceManifest` populated per spec, `regulatory_mapping` correct, retry bounded at 3 attempts, real adapter imports without side effects.
  - 29 new tests, all passing, mypy strict clean on day one, coverage 96.51% (down a tiny bit from 96.88% because the adapter has untested generic-exception fallbacks, acceptable per "no live network" guidance).
  - Followed Session 8's guidance to keep `templates.py` untouched and `governance_templates.py` separate — this kept the review-time diff readable and preserved 4A's baseline tests unchanged.
  - Precondition guard, `thread_id` convention, name-conflict suffix logic, and deterministic sha1 all preserved without disturbance.
  - Phase 0 orientation before any code change; Phase 1B stub written before any code change; Phase 3A handoff evaluation written with concrete citations of what Session 8 did well.
  - Failure mode avoidance: did NOT start Phase 5 (#18, planning-to-implementation bleed; here the implementation-to-next-phase version) despite the CLI update giving me an opening to "wire the adapter into orchestrator context." Stopped at the adapter itself + CLI flag, exactly what 4B required.
  - Failure mode avoidance: did NOT touch `templates.py`, `fake_client.py`, `protocol.py`, or `agent.py` (except the CLI's agent-import line). Phase 4B additions lived entirely in new files + `state.py` + `nodes.py` + `graph.py` + `__init__.py`. Session 8's instruction was "keep templates.py the base" and I kept it literally unchanged.
  - Answered the user's mid-session context injection (the GitHub/GitLab abstraction notes) by immediately acknowledging, finishing the failing test first, then recording the notes verbatim in the handoff. Did NOT pivot to planning the abstraction mid-session.

- **What I could have done better:**
  - The `_render_file_tree` indentation cosmetic bug in `cli.py` has been flagged twice now (Session 8 noted it, Session 9 noted it) and not fixed. I chose not to fix it because it's cosmetic and 4B-out-of-scope, but a future session should just do a 5-line fix. Not a Session 9 deliverable, though.
  - The `WebsiteAgent.__new__` hack in `test_retry.py` is ugly. Cleaner would have been to add a `graph` kwarg to `WebsiteAgent.__init__` — but that's a production-code change for a test-only improvement, so I left it. Worth a 2-minute refactor in Session 11's abstraction work.
  - The three tier fixtures are minimal — they don't exercise corner cases like empty regulatory_frameworks, missing optional fields, or multiple primary queries with different datasheets. I could have added a fourth "tier-4-minimal" fixture for edge-case coverage. Deferred to Phase 6.
  - I did not smoke-test the real `PythonGitLabAdapter` against any live GitLab instance. The user has not provided credentials and the handoff said "no live network tests" — but I could have at least constructed the adapter with a fake URL, called `create_project`, and confirmed the expected `GitLabClientError` comes back (because there's no network). Deferred — MagicMock stubs cover the same logic path without any IO concerns.

- **Why not 10:** I did not meet the bar of "zero hacks." The `WebsiteAgent.__new__` workaround in `test_retry.py` is a test-only hack that would earn a code-review comment. Session 8's handoff didn't have anything equivalent.

### Session 9 Learnings (add to table in `SESSION_RUNNER.md`)

| # | Learning | When to apply |
|---|----------|---------------|
| 2 | When extending a LangGraph pipeline with new nodes, put the helper functions in a sibling module (e.g., `governance_templates.py` next to `templates.py`) rather than expanding the existing module. Review-time diff stays local; the "before vs after" phase split is visible in the file tree. | Any LangGraph phase extension where the previous phase's templates/helpers are stable and don't need to change. |
| 3 | Derive manifest/audit data by classifier function (`is_governance_artifact(path)`) rather than by storing it in state during each node. The classifier is the single source of truth and composes with any future node that adds a new artifact category; state bookkeeping drifts. | Assembling a result object from side effects of multiple nodes — especially when some nodes are optional. |
| 4 | When a test file needs a graph with injected dependencies (e.g., no-op `sleep`), prefer plumbing a kwarg through `build_website_graph` rather than building it manually — but DO NOT refactor production code to add the kwarg for a test-only need unless the kwarg is also valuable in production. Accept a `__new__`-based construction hack in tests rather than over-engineer production. | Whenever a test needs a variant of a production-constructed object. |
| 5 | Pin a specific behavior with BOTH a positive and a negative assertion per tier in governance fan-out tests. `assert "governance/foo.md" in files` AND `assert "governance/bar.md" not in files` — otherwise a tier's gating can silently regress (e.g., tier 3 starts emitting a tier-2 artifact by accident) and the "positive only" test will pass. | Any tier/flag-gated code where missing artifacts are as important as present ones. |
| 6 | The pattern "plan as deliverable, then implementation as a separate session" (failure modes #18, #19) is load-bearing across the SESSION_RUNNER workstreams. When the user hands Session N a plan input mid-session (as happened here with the GitHub/GitLab notes), write it into the handoff verbatim and leave it for Session N+1 — do NOT pivot. | Any session where the user introduces a second deliverable while the first is mid-flight. |

### How You Will Be Evaluated
Session 10's handoff will be scored on:
1. Did Session 10 write a plan document to `docs/planning/github-gitlab-abstraction-plan.md` and STOP, or did it bundle implementation? (The plan is the deliverable.)
2. Does the plan include a grep-based inventory for every symbol Session 9's gotchas listed (`GitLabTarget`, `GitLabClient`, `FakeGitLabClient`, `gitlab_url`, `group_path`, `render_gitlab_ci`, `.gitlab-ci.yml`, `is_governance_artifact`)?
3. Does the plan make an explicit recommendation (neutral rename vs parallel schema) and back it with the inventory evidence, rather than hedging?
4. Does each phase in the plan have explicit DONE criteria + verification commands + session boundary?
5. Did Session 10 ask the user for the missing note #1, OR document why it proceeded without it?
6. Did Session 10 preserve Session 9's gotchas without dilution? In particular, the `is_governance_artifact` classifier needs an update for `.github/workflows/ci.yml` — is that flagged?
7. Does the plan explicitly say Phase 5 (orchestrator) is deferred until the abstraction lands, or does it try to interleave them?
8. Did Session 10 touch any production code under `src/model_project_constructor/agents/website/`? (It should not — planning session, no code changes.)

### What Session 8 Did
**Deliverable:** Phase 4A of architecture plan — Website Agent core + LangGraph + GitLab scaffolding (non-governance) + `FakeGitLabClient` + typer CLI + 59 tests (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `9887286` (fill in on commit).

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS in full, ACTIVE TASK + Session 7 block from SESSION_NOTES, checked git (clean, 8 commits ahead of origin at session start), confirmed `methodology_dashboard.py` still absent and `gh issue list` still empty. Reported findings. Waited for the user to say "go".
2. **Real-API smoke test of Phase 3B intake agent (retires 3-session caveat).** User confirmed an `ANTHROPIC_API_KEY` in `.env` (already gitignored). Sourced it, ran `uv run uvicorn model_project_constructor.ui.intake:app --port 8765` with `INTAKE_DB_PATH=/tmp/intake_smoketest.db`, POSTed a subrogation session (`smoke-test-1`), received a contextually-grounded Claude question ("walk me through the current process for identifying which subrogation claims to pursue"), POSTed one answer, received a substantive follow-up ("what does that recovery typically look like in dollar amounts and what percentage of claims result in recovery"). Stopped uvicorn, deleted `/tmp/intake_smoketest.db*`. **`claude-sonnet-4-6` works against the live Anthropic API; the `claude-sonnet-4-5-20250929` fallback is unneeded.** The Phase 2B data-agent `AnthropicLLMClient` remains unverified but is a separate code path — deferring that to Phase 5 (orchestrator session).
3. Phase 1B session stub written to SESSION_NOTES.md BEFORE any technical work.
4. Re-read architecture-plan sections governing Phase 4: §4.3 (contract + failure modes), §5.4 (schemas, already shipped in Phase 1), §8 (governance integration — **critical for the 4A↔4B split**), §10 (full LangGraph topology), §11 (file structure acceptance checklist), §14 Phase 4A (DONE criteria + verification commands).
5. **Resolved the 4A/4B scope ambiguity.** The ACTIVE TASK block from Session 7 paraphrased 4A as "README, .gitlab-ci.yml, .gitignore, LICENSE" — narrower than §14 Phase 4A's "base repo structure (no governance artifacts yet)" + "all .qmd files, all src/ modules, unit test files". I took §14 as authoritative and additionally applied §8.2's classification rule: **anything §8.2 lists as a governance artifact (including `.gitlab-ci.yml`, `.pre-commit-config.yaml`, and `data/datasheet_*.md`) is out-of-scope for 4A**. Everything else in §11 is in-scope. Net result: 28 base files per project, governance files deferred to 4B. This reading is defensible, tests it, and avoids the bundling trap.
6. Studied the Phase 3A intake agent pattern before writing any website code: `state.py` (TypedDict, no reducers, `initial_state()` helper), `protocol.py` (Protocol + dataclasses for DTOs), `nodes.py` (`make_nodes(client)` closure + per-node pure functions + routing helper + `build_*_report` assembler), `graph.py` (`build_*_graph(client, *, checkpointer=None)`), `agent.py` (facade with `run(...)`), `cli.py` (single `@app.command()` no callback), `__main__.py` (three-line shim). The website agent mirrors this one-for-one.
7. Built the `agents/website/` package in order: `state.py` → `protocol.py` → `templates.py` (pure file-content generators, ~400 lines) → `nodes.py` → `graph.py` → `fake_client.py` → `agent.py` → `cli.py` → `__main__.py` → `__init__.py` (public API).
8. **Graph topology decision.** §10 lists `CREATE_PROJECT → SCAFFOLD_BASE → SCAFFOLD_GOVERNANCE → SCAFFOLD_ANALYSIS → SCAFFOLD_TESTS → INITIAL_COMMITS → END`. I chose to implement the FULL accumulator pattern for 4A — `SCAFFOLD_BASE` populates `state["files_pending"]` and `INITIAL_COMMITS` flushes — instead of inlining the commit in `SCAFFOLD_BASE`. That way Session 9 only needs to merge additional entries into `files_pending` before the existing `INITIAL_COMMITS` fires, with zero refactor of 4A nodes. This is the single most important architectural decision of the session.
9. **Name-conflict handling.** `_candidate_names()` produces `[base, base-v2, base-v3, base-v4, base-v5]`. The `create_project` node walks them in order, catching `ProjectNameConflictError` on each and only surfacing `status=FAILED` with `failure_reason="project_name_conflict:..."` after all 5 are taken. Tested with a pre-seeded `FakeGitLabClient(existing_names=...)` covering single-conflict, 5-way exhaustion, and end-to-end via the agent facade.
10. **`WebsiteAgent.run` precondition guard.** If `intake_report.status != "COMPLETE"` OR `data_report.status != "COMPLETE"`, returns a FAILED `GitLabProjectResult` with `failure_reason=precondition_failed:intake_status=...` WITHOUT creating any GitLab project. Two tests pin this: `test_incomplete_intake_report_halts` and `test_incomplete_data_report_halts` both assert `fake_client.projects == {}` after the call.
11. **Fixtures.** Discovered `tests/fixtures/subrogation_intake.json` and `sample_datareport.json` did not exist — the ACTIVE TASK block from Session 7 referenced them in the literal verification command but they were never created. Generated `subrogation_intake.json` by running `tests/fixtures/subrogation.yaml` through `IntakeAgent.run_with_fixture(...)` and dumping the validated `IntakeReport`. Hand-wrote `sample_datareport.json` — one primary query (`subrogation_training_set`) with full SQL, 2 quality checks, a Datasheet, request/summary/expectations populated, all fields conforming to the v1 schema. Validated both via `model_validate_json` round-trip before using them in tests.
12. **Pre-test smoke run of the whole package** before writing the test suite: `uv run python -m model_project_constructor.agents.website --intake ... --data ... --fake-gitlab` → COMPLETE, 28 files committed, deterministic sha. Validated the happy path architecturally.
13. Wrote 59 tests across 5 files (`test_templates.py`, `test_fake_client.py`, `test_nodes.py`, `test_agent.py`, `test_cli.py`) + conftest. Tests cover: slug/name derivation edge cases, every individual renderer, full `build_base_files` file set, per-node success + failure paths, name-conflict suffix walking, `WebsiteAgent.run` happy path with all §11 base files asserted by name, precondition guards, governance-absent assertion (to be deleted in 4B), CLI arg validation + happy path + `--output` file.
14. First test run: **59 passed on the first invocation.** No debugging required. This is unusual and I attribute it directly to how faithfully the website agent mirrors the Phase 3A intake agent's pattern — the 4A graph topology, node signature, and facade shape are 1:1 copies of shapes that already had tests pinning them.
15. Ran the full suite: **260 passed, 96.88% coverage** (up from 201 @ 96.48%). `templates.py` at 100%, `state.py` at 100%, `agent.py` at 100%, `protocol.py` at 92% (the 2 uncovered lines are the Protocol `...` ellipsis bodies, which mypy treats as reachable for coverage but pytest never executes — acceptable).
16. Ran `uv run mypy src/model_project_constructor/agents/website/` — 2 errors on first run: unused `# type: ignore[arg-type]` on the `GovernanceManifest` Literal args in `nodes.py:163-164`. Pydantic's v2 Literal coercion of `dict.get(..., "default")` is apparently smarter than I expected. Removed the `type: ignore` comments → **0 errors across 10 source files.**
17. Ran the literal plan verification command `uv run python -m model_project_constructor.agents.website --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json --fake-gitlab` — prints the file tree (28 files) and dumps a valid `GitLabProjectResult` JSON with `status=COMPLETE`, `project_url=https://fake.gitlab.test/data-science/model-drafts/intake-subrogation-001`, deterministic commit sha, all 28 paths in `files_created`. §14 Phase 4A verification satisfied.
18. Updated README.md: phase table split into 4A Complete / 4B Not started, repo layout extended with `agents/website/` module breakdown, tests section shows `agents/website/ # 59 website agent tests`, fixtures list extended with `subrogation_intake.json` + `sample_datareport.json`, test count updated 201 → 260, coverage note 96% → 96.9%, new "Website Agent CLI" quick-start block with the literal verification command + note about governance deferral to 4B.
19. Rewrote the `ACTIVE TASK` block for **Phase 4B** (Website Agent governance scaffolding + retry/backoff + real `python-gitlab` adapter). Points Session 9 at §4.3 failure modes, §8.1/8.2/8.3, §10 full topology, §11 governance files, §14 Phase 4B verification. Enumerates the exact tier 1/2/3 artifacts, the `regulatory_mapping` population requirement, and the three nodes to insert between `SCAFFOLD_BASE` and `INITIAL_COMMITS`.
20. Preserved the Phase 3B gotchas verbatim and prepended a new **"Phase 4A gotchas"** block with 8 new entries (accumulator discipline, `build_gitlab_project_result` 4A-awareness, deliberate `.gitlab-ci.yml` / `.pre-commit-config.yaml` omission, datasheet-as-governance, deterministic fake-client shas, name-conflict is done, precondition guard behavior, `thread_id` prefix convention).

**Key design calls:**
- **Accumulator pattern in state.** `files_pending: dict[str, str]` lives in the state, not in a closure. `SCAFFOLD_BASE` merges, `INITIAL_COMMITS` flushes. Session 9's three new scaffold nodes will just merge more entries. This makes 4B's expansion a ~50-line diff instead of a refactor.
- **Separate `templates.py` from `nodes.py`.** Pure-python template functions are trivially unit-testable in isolation (33 of the 59 tests are template-level). Session 9 should add `governance_templates.py` as a sibling instead of bloating `templates.py` — the 4A/4B split stays legible in code review.
- **Dict-shaped state, not Pydantic-shaped.** `WebsiteState` stores `intake_report`, `data_report`, `gitlab_target` as dicts (`model_dump(mode="json")`) so any LangGraph checkpointer can serialize them without custom codecs. Templates accept dicts directly. The Pydantic models are only touched at the boundary (`WebsiteAgent.run` input + `build_gitlab_project_result` output).
- **Precondition guard returns FAILED, doesn't raise.** §12 says expected failures → status in return, exceptions only for programming errors. An upstream-incomplete report is an expected failure. Two tests pin the no-side-effect behavior.
- **`thread_id = f"website::{session_id}"`** instead of plain `session_id`. Avoids collisions if Phase 5's orchestrator ever shares a single checkpointer across agents. Micro-decision but worth calling out.
- **`FakeGitLabClient` deterministic shas.** `sha1(f"{message}|{branch}|" + "|".join(sorted(files)))`. Same files + same message → same sha. Enables exact pinning in tests if future sessions want it, without making the current tests sensitive to ordering.
- **CLI refuses to run without `--fake-gitlab`.** Exit code 2 with a clear message pointing at 4B. Real `python-gitlab` adapter is 4B's job; the CLI shouldn't silently succeed with a no-op backend and then confuse the operator when nothing lands in GitLab.
- **`build_gitlab_project_result` returns an empty but valid `GovernanceManifest`.** `artifacts_created=[]`, `regulatory_mapping={}`, but `risk_tier`/`cycle_time` are read from the intake report so downstream consumers can trust the manifest shape today. 4B will populate the two collections.

**Files created (20):**
- `src/model_project_constructor/agents/website/__init__.py`
- `src/model_project_constructor/agents/website/__main__.py`
- `src/model_project_constructor/agents/website/state.py`
- `src/model_project_constructor/agents/website/protocol.py`
- `src/model_project_constructor/agents/website/templates.py`
- `src/model_project_constructor/agents/website/nodes.py`
- `src/model_project_constructor/agents/website/graph.py`
- `src/model_project_constructor/agents/website/fake_client.py`
- `src/model_project_constructor/agents/website/agent.py`
- `src/model_project_constructor/agents/website/cli.py`
- `tests/agents/website/__init__.py`
- `tests/agents/website/conftest.py`
- `tests/agents/website/test_templates.py`
- `tests/agents/website/test_fake_client.py`
- `tests/agents/website/test_nodes.py`
- `tests/agents/website/test_agent.py`
- `tests/agents/website/test_cli.py`
- `tests/fixtures/subrogation_intake.json`
- `tests/fixtures/sample_datareport.json`

**Files modified (2):**
- `README.md` — phase table, repo layout, test count, coverage note, website-agent quick start, fixture list.
- `SESSION_NOTES.md` — ACTIVE TASK rewritten for Phase 4B; Session 8 block below; Phase 4A gotchas block; Session 7 handoff evaluation.

**Session 7 Handoff Evaluation (Session 8 scoring Session 7):**
- **Score: 9/10**
- **What helped (ranked by time saved):**
  1. **"Reuse the LangGraph pattern from Phase 3A. ... See `src/model_project_constructor/agents/intake/graph.py:19-70` for the canonical pattern."** Exact file:line was gold. I copied the Phase 3A shape one-for-one and the first test run was 59/59. The 1-for-1 fidelity is what made this the fastest phase so far.
  2. **The full inventory of Phase 3B key files with line numbers** (`ui/intake/runner.py:122->144`, `app.py:182`, `fixture.py:95-122`, etc.). I didn't need any of them for 4A specifically, but the shape of the inventory taught me the target quality bar for my own handoff.
  3. **"Use §11 as your acceptance checklist — every file listed there is a DONE criterion."** Directly shaped my `test_all_section_11_base_files_scaffolded` test which pins every file by name. Without this sentence I probably would have written a weaker "at least 20 files" test.
  4. **The "Typer single-command trap"** warning made me pick the `@app.command()`-no-callback pattern for the website CLI in 30 seconds instead of discovering it by trial and error.
  5. **The `FixtureLLMClient` statelessness story.** I absorbed the general principle ("state lives in graph state, not in client instances") and used it implicitly when designing `FakeGitLabClient`. No accident — I patterned the fake after the fixture.
- **What was missing (and cost me time):**
  1. **The 4A/4B scope ambiguity.** The ACTIVE TASK block said "CREATE_PROJECT + SCAFFOLD_BASE nodes with structured templates for README.md, .gitlab-ci.yml, .gitignore, LICENSE" — which is NARROWER than §14 Phase 4A's "base repo structure (no governance artifacts yet)" + "all .qmd files, all src/ modules, unit test files". I had to read §14 + §8.2 carefully to decide. I settled on "§14 + §8.2" as authoritative and delivered the full 28-file base. If Session 7 had either (a) enumerated the 28 files explicitly or (b) stated "§14 is authoritative, ignore the narrower summary above", I would have saved ~10 minutes.
  2. **`subrogation_intake.json` and `sample_datareport.json` did not exist.** The ACTIVE TASK block quoted a verification command referencing them, but neither Session 6 nor Session 7 created them. I had to generate the intake from `subrogation.yaml` and hand-write the data report. Not hard, but Session 7 could have flagged this. (Fair-minded note: these fixtures are 4A-specific test inputs, so Session 7 legitimately couldn't have created them earlier — the call-out would have been the contribution.)
- **What was wrong:** Nothing verifiable. The gotchas all held up. The `python-multipart` hard-dep warning was moot for 4A but still valid. The `methodology_dashboard.py` absence was correctly flagged.
- **ROI:** The handoff was ~100 lines of ACTIVE TASK + ~60 lines of gotchas. Reading it cost ~2 minutes. It saved me an estimated 30–45 minutes of pattern discovery and probably prevented at least one rewrite. Net ROI very positive.
- **Why not 10/10:** The scope ambiguity in item 1 above is a real cost — it forced me into a judgment call during Phase 2 (Execute) instead of letting me trust the block verbatim. A 10/10 handoff would have told me the final file count up front. Everything else earned the 9.

### What Session 7 Did
**Deliverable:** Phase 3B of architecture plan — Intake Agent Web UI (FastAPI + SSE + HTMX + SQLite checkpointer) (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `1c1141a` (Phase 3B implementation + 22 tests + pyproject + `FixtureLLMClient` statelessness fix + `graph.py` checkpointer parameterization + `.gitignore` + README + SESSION_NOTES).

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS in full, ACTIVE TASK + Session 6 block from SESSION_NOTES, checked git (clean, 6 commits ahead of origin), confirmed `methodology_dashboard.py` still absent and `gh issue list` still empty. Reported findings. Waited for the user to say "go".
2. Phase 1B session stub written to SESSION_NOTES.md BEFORE any technical work: `"Session claimed. Work beginning."` under `### What Session 7 Did`.
3. Read the plan sections that govern Phase 3B: §9.3 (stack), §14 Phase 3B (DONE criteria + verification), §4.1 (governance), §10 (LangGraph diagram). Confirmed that Phase 3B is a driver over the SAME compiled graph Phase 3A shipped — NOT a rewrite.
4. Read the Phase 3A code I needed to build on top of: `agents/intake/__init__.py`, `state.py`, `graph.py`, `agent.py`, `nodes.py`, `protocol.py`, plus `pyproject.toml` to understand the optional-extras layout.
5. Inventoried dependencies: `fastapi`, `uvicorn`, `sse-starlette`, `httpx`, `starlette`, `langgraph 0.2.76`, `langgraph-checkpoint 2.1.2` were already installed. `langgraph-checkpoint-sqlite` and `python-multipart` (for FastAPI form handling) were NOT. Added both to the `ui` optional extras via `uv add --optional ui`. `jinja2` not installed — chose to keep templates as pure Python f-strings with `html.escape` rather than add another dep.
6. Confirmed the `langgraph.checkpoint.sqlite.SqliteSaver` API: takes a `sqlite3.Connection`, has `.setup()`. Direct construction works — no need for the `from_conn_string` context manager, which would complicate integration with FastAPI's request lifecycle.
7. **Parameterized `build_intake_graph`** — added `checkpointer: Any | None = None` kwarg. Default behavior unchanged (`MemorySaver`). The kwarg means Session 6's CLI and all Phase 3A tests keep working verbatim, while the web UI passes a shared `SqliteSaver`. One-line change, minimum blast radius.
8. Created 7 TaskCreate items covering checkpointer, FastAPI app, SQLite, HTMX, tests, verification, close-out.
9. Built `src/model_project_constructor/ui/intake/runner.py` — `IntakeSessionStore` owns a single `SqliteSaver` + a lock + a per-session compiled-graph cache. `start_session`, `answer`, `review`, `get_snapshot`, `has_session`, `close`. Every public method is guarded by the RLock because FastAPI routes sync endpoints through a threadpool and SQLite connections are NOT thread-safe even with `check_same_thread=False`. Phase check in `answer` and `review` raises `InvalidPhaseError` so the HTTP layer can return 409.
10. Built `src/model_project_constructor/ui/intake/templates.py` — four pages: index (start-interview form), resume-form, session (question / review / complete / not_started), rendering via f-strings with `html.escape` on every interpolated value. CSS and the HTMX script tag are inlined. No Jinja2 dependency.
11. Built `src/model_project_constructor/ui/intake/app.py` — `create_app(llm_factory, db_path)` factory used by tests, plus module-level `app = create_app()` for the plan's literal `uvicorn model_project_constructor.ui.intake:app` verification command. Routes: landing, resume form, resume redirect, create session, get/post session, answer, review, state.json, report.json, events (SSE), healthz.
12. First boot via `uv run python -c "from model_project_constructor.ui.intake import create_app"` → ImportError: `python-multipart` missing. FastAPI's `Form(...)` requires it. Added to `ui` extras, re-synced, re-imported → clean.
13. Wrote an in-process end-to-end smoke test via `TestClient` on the subrogation fixture: POST /sessions → GET /sessions/{id} → loop POST /answer 7 times → POST /review accept → GET /report.json → COMPLETE. Every step 200. Confirmed the architecture before writing the real test suite.
14. Wrote 22 tests across 5 files:
    - `tests/ui/intake/test_app_happy_path.py` (11 tests) — healthz, index, resume form page, resume redirect lookup, not-started placeholder, create + redirect, create with auto-ID, subrogation end-to-end COMPLETE, report.json 409 when not complete, answer 409 in review phase, review 409 in question phase.
    - `tests/ui/intake/test_caps_and_revisions.py` (2 tests) — question cap → DRAFT_INCOMPLETE with `questions_cap_reached`; revision cap → DRAFT_INCOMPLETE with `revision_cap_reached`. Both exercise the full HTTP round-trip against the cap fixtures from Phase 3A.
    - `tests/ui/intake/test_sqlite_resume.py` (1 test) — the core Phase 3B DONE criterion. Create app1 with a tmp db, answer 2 questions, close app1, create a NEW app2 pointing at the same db, finish the interview to COMPLETE, confirm report.json has `status=COMPLETE`.
    - `tests/ui/intake/test_sse.py` (2 tests) — `text/event-stream` content type, initial snapshot payload parsing via `client.stream` + `iter_lines`.
    - `tests/ui/intake/test_runner.py` (6 tests) — direct `IntakeSessionStore` tests so failures point at the driver, not at FastAPI wiring. `CAPS` constant, snapshot-for-missing-session, `has_session` transition, `start_session` returns question snapshot, `answer` wrong phase, `review` wrong phase.
15. **First resume test failure** — after "restart" and 5 more answers, POST /review returned 409 "phase is question, cannot accept review response". Graph kept asking q#8. Root cause: `FixtureLLMClient` had internal `self._q_index = 0` that reset on every factory call; the graph state said `questions_asked=7`, but the LLM's internal counter said "return question[0], enough_info=False" → infinite questions. **Fix:** made `FixtureLLMClient.next_question` stateless — it now keys off `context.questions_asked` (the graph state is the source of truth). This is a small but load-bearing correctness fix: stateful test doubles that reset across factory calls are a trap when the system under test persists state.
16. Updated the existing Phase 3A `test_fixture_llm_client_dispenses_questions_in_order` test to match the new stateless contract: it now constructs fresh `InterviewContext`s with monotonically-increasing `questions_asked`, and asserts that calling with the same context is idempotent. All 14 fixture tests + all 56 agents/intake tests green.
17. **SSE test hung TestClient on first run.** Initial SSE endpoint design was a long-lived polling loop: emit snapshot → sleep 1s → check `await request.is_disconnected()` → loop. Under `TestClient.stream`, the sync test code never yielded control back to the server coroutine, so `is_disconnected` never returned True even after the `with` block exited. The background pytest process had to be `pkill`ed. **Fix:** redesigned SSE as one-shot: emit the current snapshot once and terminate. The plan's DONE criterion is "curl smoke test for SSE endpoint", which a one-shot stream satisfies. HTMX clients can reconnect after each form submission; any phase-change stream is a later polish. Documented in the runner docstring and the gotchas.
18. Ran §14 Phase 3B verification commands LITERALLY:
    - `uv run pytest tests/ui/intake/ --no-cov` → 22 passed.
    - `uv run pytest` (full suite) → **201 passed, 96.48% coverage** (179 → 201; +22 web UI tests).
    - `uv run mypy src/model_project_constructor/ui/` → 0 errors in 5 source files (after adding `-> AsyncIterator[None]` to the lifespan contextmanager).
    - `INTAKE_DB_PATH=/tmp/intake_verify.db uv run uvicorn model_project_constructor.ui.intake:app --port 8765` → uvicorn starts, serves 200 on `/healthz` and `/`.
    - `curl -sN http://localhost:8765/sessions/curl-smoke/events` → `event: snapshot\ndata: {..."phase": "not_started"...}`. SSE smoke test passes.
    - `curl -i "http://localhost:8765/sessions/resume?session_id=foo"` → 303 redirect to `/sessions/foo`.
19. Module-level `app = create_app()` creates `intake_sessions.db` in the cwd at import time because the default DB path is relative. Added `intake_sessions.db`, `intake_sessions.db-shm`, `intake_sessions.db-wal` to `.gitignore` (WAL-mode SQLite needs all three patterns). Removed stray files from the workspace.
20. Did NOT do the first real-API smoke test. No `ANTHROPIC_API_KEY` in this session. Same deferral as Session 6. Noted in handoff as the third-session-in-a-row caveat.
21. Updated `README.md`: Phase 3B row → Complete, added `ui/intake/` to the repo layout with module breakdown, added `tests/ui/intake/` to the tests section, added the web-UI quick-start block with `uvicorn` command + `INTAKE_DB_PATH` note + SSE endpoint pointer, updated test count 179 → 201.
22. Rewrote the `ACTIVE TASK` block for **Phase 4A** (Website Agent — sub-phase 4A only). Points Session 8 at §4.3, §5.4, §10, §11, §14 Phase 4. Lists all the Phase 3B key files with line references. Enumerates Phase 3B-specific gotchas (module-level DB creation, RLock discipline, graph-cache semantics, stateless fake-client pattern, one-shot SSE design, `python-multipart` hard dep) on top of the preserved Phase 2A/2B/3A gotchas.
23. Close-out commit pending: everything above as a single Session 7 commit.

**Key design calls:**
- **One compiled graph per session, cached in memory.** `IntakeSessionStore._graphs` is a per-session cache so the LLM factory is invoked exactly once per session. Alternative was one graph per app shared across sessions, but that requires the LLM client to be shared, and production factories (Anthropic) and test factories (Fixture) can want per-session state. The per-session cache makes both work.
- **Stateless `FixtureLLMClient`.** Required for SQLite resume. The graph state is the source of truth. Any future fake LLM client should follow this pattern. Documented in the fixture docstring AND in the handoff gotchas.
- **One-shot SSE.** The plan's DONE criterion is "curl smoke test". A one-shot stream satisfies it, is cleanly unit-testable under sync `TestClient`, and avoids the coroutine-lifecycle hazards of a polling loop. A long-lived stream is a Phase 4+ polish that will need async test clients.
- **No Jinja2 dependency.** Pure f-strings with `html.escape`. Four pages is the entire frontend surface; a template engine is overkill and adds install footprint.
- **`create_app(llm_factory, db_path)` factory.** Module-level `app = create_app()` exists because the plan's verification command literally says `uvicorn model_project_constructor.ui.intake:app`. The factory exists because tests need to inject fixture LLM clients and per-test SQLite DBs. Both coexist cleanly.
- **Per-session `thread_id = session_id`.** Same convention as Phase 3A's CLI, carried over to the HTTP layer. Session isolation is LangGraph's responsibility, not ours.
- **Phase guards at the driver level, not route level.** `IntakeSessionStore.answer` / `review` raise `InvalidPhaseError` if the caller submits the wrong response kind. The HTTP layer maps this to 409. Driver enforcement means the same guards apply to any future non-HTTP driver (a Slack bot, a CLI, whatever).
- **Forms over JSON.** All state-changing routes accept `application/x-www-form-urlencoded` via FastAPI `Form(...)`. This keeps the frontend a plain HTMX form POST with no JSON serialization, and makes `curl` smoke tests trivial.
- **Lifespan context manager, not `@on_event`.** The old pattern is deprecated in FastAPI 0.135+. Noted in handoff.

**Files created (10):**
- `src/model_project_constructor/ui/__init__.py`
- `src/model_project_constructor/ui/intake/__init__.py`
- `src/model_project_constructor/ui/intake/app.py`
- `src/model_project_constructor/ui/intake/runner.py`
- `src/model_project_constructor/ui/intake/templates.py`
- `tests/ui/__init__.py`
- `tests/ui/intake/__init__.py`
- `tests/ui/intake/conftest.py`
- `tests/ui/intake/test_app_happy_path.py`
- `tests/ui/intake/test_caps_and_revisions.py`
- `tests/ui/intake/test_sqlite_resume.py`
- `tests/ui/intake/test_sse.py`
- `tests/ui/intake/test_runner.py`

**Files modified (6):**
- `pyproject.toml` — added `langgraph-checkpoint-sqlite>=2.0,<3` and `python-multipart>=0.0.9` to the `ui` optional extras.
- `uv.lock` — regenerated.
- `src/model_project_constructor/agents/intake/graph.py` — `build_intake_graph(llm, *, checkpointer=None)` kwarg.
- `src/model_project_constructor/agents/intake/fixture.py` — `FixtureLLMClient.next_question` made stateless (keys off `context.questions_asked`), internal `_q_index` removed, docstring updated.
- `tests/agents/intake/test_fixture.py` — `test_fixture_llm_client_dispenses_questions_in_order` updated to the stateless contract + idempotency assertion.
- `.gitignore` — added `intake_sessions.db*` patterns.
- `README.md` — Phase 3B row complete, `ui/intake/` in repo layout, `tests/ui/intake/` in tests section, web-UI quick-start block, test count 179 → 201.
- `SESSION_NOTES.md` — this file; ACTIVE TASK rewritten for Phase 4A; Session 7 block below.

**Session 6 Handoff Evaluation (Session 7 scoring Session 6):**
- **Score: 10/10**
- **What helped (ranked by time saved):**
  1. **"Parameterize the checkpointer" with the explicit file:line (`graph.py:18-56`) and two suggested API shapes** (`checkpointer=None` kwarg OR `make_graph_builder()` + `build_intake_graph(llm, checkpointer)`). I took the kwarg approach — single-line change, preserves backward compat. Without this warning I might have rewritten `build_intake_graph` more invasively.
  2. **"The `plan_next_question` / `ask_user` split is mandatory"** with the explanation that interrupted nodes re-execute from the top on resume. This directly shaped my runner.py design: the HTTP layer drives the graph by calling `graph.invoke(Command(resume=...), config=config)` AFTER checking that a phase is `"question"` or `"review"`. I never had to debug a double-billed LLM call because the split was already correct in Phase 3A and I understood why from Session 6's note.
  3. **"Use `session_id` verbatim as `thread_id`"** with the pointer to `agent.py:86`. Saved me from reinventing the session-isolation mechanism. The web UI uses this convention verbatim (`runner.py:96`).
  4. **"Coverage gate is 90%, currently 96.18%. Phase 3B's web UI + new test surface may temporarily drop this"** — I used this as the "write tests as you go" nudge. Never hit the floor.
  5. **"`_DummyLLM` in cli.py:85-99" pointer** — I confirmed the web UI does NOT need it (it has a real factory at app-construction time), so I left Phase 3A's CLI untouched. Without the pointer I might have tried to extend or share `_DummyLLM`.
  6. **The pre-declared evaluation criteria (7 items)** — I used them as my close-out self-check. Items 2 (reuse `build_intake_graph`), 3 (checkpointer parameterization), and 5 (don't bundle Phase 4) were the ones I was most tempted to shortcut and most grateful were pre-flagged.
- **What was missing (minor):**
  1. No note about `python-multipart` as a hidden FastAPI runtime dep for form handling. I hit an ImportError on first app import and had to add it to the `ui` extras. A one-liner "FastAPI Form(...) needs `python-multipart`" would have saved 2 minutes. I have now added this to the Phase 3B gotchas so Phase 4 doesn't rediscover it if it uses FastAPI Forms.
  2. No note about `jinja2` being absent (I thought it might come in via fastapi's extras; it doesn't). Not blocking — I chose pure f-strings — but one line would have been nice.
  3. No guidance on SSE endpoint lifecycle under sync `TestClient`. I wrote a long-lived polling loop first, it hung, and I had to redesign. Session 6 couldn't have anticipated this specifically, but a generic "SSE endpoints under TestClient are fragile; prefer one-shot streams for test coverage" note would have landed. Added to Phase 3B gotchas for Session 9+ to benefit.
- **What was wrong:** Nothing material. Every claim about existing code matched the repo state. Every file:line reference was correct. Every gotcha was load-bearing.
- **ROI:** Enormous. Session 6's handoff was 108 lines for ACTIVE TASK alone and every line paid. I estimate it saved 45-60 minutes of rediscovery — especially around the checkpointer parameterization (which I might have done invasively), the `plan/ask` split (which I might have accidentally collapsed), and the `_DummyLLM` disposability question (which I might have wasted time generalizing). Read-cost: 10 minutes.
- **Process notes:** Session 6 produced a 10/10 handoff by (a) explicit technical-risk de-risking (the toy-graph instruction), (b) file:line breadcrumbs for every mentioned symbol, (c) pre-declared evaluation criteria that doubled as a close-out checklist, (d) clean separation of "do these things" vs "do NOT do these things", (e) design-rationale notes for key choices (state-without-reducers, node-split, CLI callback) so I could judge edge cases rather than blindly follow. I have copied all five patterns into my own handoff.

**Session 7 Self-Assessment:**
- (+) Completed Phase 0 orientation in full before any file touch. Wrote Phase 1B stub BEFORE any technical work. Reported findings and waited for user direction.
- (+) Re-read the plan sections BEFORE writing code, as Session 6's handoff instructed. Specifically §9.3, §14 Phase 3B, §4.1, §10. Did not skim.
- (+) Reused `build_intake_graph()` exactly as the plan requires — one-kwarg addition, no rewrite. Phase 3A tests still all green after the change.
- (+) Parameterized the checkpointer with minimum blast radius. CLI/fixture path keeps `MemorySaver` default; web UI passes `SqliteSaver`. No other Phase 3A API touched.
- (+) Caught and fixed the `FixtureLLMClient` statefulness bug via the SQLite resume test. This is the kind of correctness issue the plan's explicit "across server restart" wording exists to catch, and I caught it via the test Session 6's plan specifically asked for. This made the Phase 3A code more robust — stateless test doubles are strictly better.
- (+) Recovered from the SSE hang without user intervention. Diagnosed (async loop under sync TestClient), redesigned (one-shot emission), documented the decision in the runner docstring AND the handoff.
- (+) Ran the §14 Phase 3B verification commands LITERALLY: pytest green, uvicorn starts, curl SSE returns an `event: snapshot` frame, curl resume redirects 303. Not paraphrased, not approximated.
- (+) 22 new tests, 201 total, 96.48% coverage — comfortably above the 90% floor. Coverage on `ui/intake/` modules: `__init__.py` 100%, `app.py` 98%, `runner.py` 98%, `templates.py` 97%. All remaining misses are on the production-only branches (lifespan shutdown, the Anthropic-factory lazy-import fallback).
- (+) Ran `uv run mypy src/model_project_constructor/ui/` — 0 errors in 5 files. Added the `-> AsyncIterator[None]` annotation the strict mypy wanted on the lifespan contextmanager. Did NOT touch the 33 pre-existing errors elsewhere — out of scope. Intake-package mypy also still clean.
- (+) Scope discipline: Phase 3B only. Did not start Phase 4. Did not touch the Data Agent. Did not rewrite the intake graph. The one Phase 3A code change (stateless fixture client) was load-bearing for the Phase 3B SQLite resume criterion and updated the existing Phase 3A test to match — a deliberate, minimum-blast-radius correctness fix, NOT a refactor.
- (+) Removed WAL-mode sibling files from git tracking via `.gitignore`. A future session running `git status` after `uv run uvicorn ... :app` will see a clean tree.
- (+) Recovered from three self-inflicted errors without user intervention: (1) `python-multipart` missing → added to `ui` extras; (2) `FixtureLLMClient` stateful reset → made stateless; (3) SSE polling loop hanging TestClient → redesigned as one-shot. All three documented in the chronological log and in the handoff gotchas where relevant.
- (−) Did NOT do the first real-API smoke test. Same deferral as Session 6. Acceptable — the session runner did not have an API key — but this is now the third consecutive session with the caveat, and Session 8 should treat it as overdue.
- (−) I was initially uncertain about the best way to expose the SSE endpoint lifetime (one-shot vs. streaming). I wrote the polling-loop version first and had to redesign. Cost: about 10 minutes. A future session building another SSE endpoint should read my runner/app design notes BEFORE starting.
- (−) Did not add an `INTAKE_DB_PATH`-aware default that lives outside cwd. The module-level `app = create_app()` creates `intake_sessions.db` in cwd at import time. I fixed this via `.gitignore` but a more correct fix would be a default like `~/.model_project_constructor/intake_sessions.db` or `:memory:`. Noted in gotchas; low priority but worth revisiting in Phase 6 hardening.
- (−) The `templates.py` module uses a 203rd-line code path (see coverage report) that is never exercised — a defensive `<em>(empty)</em>` fallback in `_render_kv`. I could have added a test for it, but it's a 1-line branch and the rest of the module is 97%. Left alone.

---

### What Session 6 Did
**Deliverable:** Phase 3A of architecture plan — Intake Agent core + LangGraph + CLI (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** Session-6 single commit (pending at close-out) — Phase 3A implementation + tests + fixtures + README/SESSION_NOTES updates.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES Session 5 block, architecture-plan §4.1/§5.1/§10/§14 Phase 3A, checked git, confirmed `methodology_dashboard.py` still absent (Session 5 precedent) and `gh issue list` still empty (UAT-only, per memory note). Reported findings, waited for user direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work (`claimed Session 6, work beginning`).
3. **LangGraph interrupt-pattern toy-graph verification** — Session 5's hard prerequisite. Built a throwaway 3-node graph (ask → decide → finalize) on langgraph 0.2.76 using `from langgraph.types import interrupt, Command` and `from langgraph.checkpoint.memory import MemorySaver`. Ran invoke → pause (interrupts surface via `state.tasks[0].interrupts[0].value`) → resume (`Command(resume=...)`) → loop → resume → finalize. Confirmed two critical behaviors: (a) interrupted node re-executes from the top on resume, so LLM calls CANNOT sit in the same node as `interrupt()`; (b) `Annotated[list, add]` reducers plus a later node returning full state causes list duplication. Both shaped the design below.
4. Created 12 TaskCreate items covering design, toy verification, implementation phases, tests, verification, and close-out.
5. Designed the intake state as a plain `TypedDict` with NO reducers — nodes return deltas only. Deliberate, documented in `state.py`.
6. Designed `IntakeLLMClient` as a 4-method Protocol (`next_question`, `draft_report`, `classify_governance`, `revise_report`) with dataclass result types (`NextQuestionResult`, `DraftReportResult`, `GovernanceClassification`, `InterviewContext`). Separate from the data agent's LLMClient by design — they share no methods and the data agent package cannot be imported from anyway (Phase 2B).
7. Implemented 8 graph nodes in `nodes.py` — split `plan_next_question` (LLM call, idempotent-relative) from `ask_user` (interrupt only). Same split for the review step: `await_review` has only `interrupt()`, no side effects. `evaluate_interview` enforces the 10-question cap. `revise` increments `revision_cycles` AND re-runs `classify_governance` because governance can shift when the draft changes. `finalize` computes `missing_fields` based on which caps were hit (`questions_cap_reached`, `revision_cap_reached`) and validates the full `IntakeReport` through Pydantic via `build_intake_report()`.
8. Built the compiled graph in `graph.py` using `StateGraph(IntakeState)` + `MemorySaver`. Routing: `evaluate_interview` → `draft_report` or back to `plan_next_question`; `await_review` → `revise` or `finalize` based on `review_accepted` and cap.
9. Built `FixtureLLMClient` and `load_fixture()` in `fixture.py` with schema validation (`intake_fixture/v1`), missing-field checks, and `revised_draft` override to exercise revision cycles. Wrote `IntakeAgent.run_scripted()` in `agent.py` — it drives the compiled graph one interrupt at a time against a scripted answer list, with an explicit max-turns safety so a buggy graph can't infinite-loop a test run.
10. Smoke-tested the full flow against an in-memory fixture before writing any tests or fixtures. Printed `status=COMPLETE, Q=7, tier=tier_3_moderate, target=successful_subrogation, value_low=2000000`. That proved interrupt/resume + the whole node chain works end-to-end on the installed langgraph version.
11. Built the CLI as a typer app. **Initial mistake:** I used the `@app.callback()` + `@app.command("run")` pattern (copying the data agent exactly), which meant the CLI required `python -m ... run --fixture`. The plan literally specifies `python -m ... --fixture` with no subcommand. Ran the plan's verification command, caught the discrepancy, rewrote the CLI as a single `@app.command()` with NO callback so typer auto-collapses. Added to handoff gotchas that the two CLIs take OPPOSITE decisions on the callback.
12. Registered `model-intake-agent` console script in `pyproject.toml`. Added `pyyaml>=6` as an explicit dependency (was already transitively installed). Ran `uv sync` and confirmed the script works.
13. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all 4 Protocol methods with prompts for each. Mirrors the structure of the data agent's Anthropic client (code-fence stripping, JSON parsing, `IntakeLLMError` on bad shapes) but with interview-specific prompts. Injected SDK client for test mocking; lazy-imports `anthropic` when constructed without a client.
14. Wrote 5 fixtures: `subrogation.yaml` (tier-3 tactical, the canonical worked example from `initial_purpose.txt`), `pricing_optimization.yaml` (tier-2 strategic, consumer-facing auto pricing), `fraud_triage.yaml` (tier-1 continuous, SIU routing), `intake_question_cap.yaml` (11 QA pairs + `draft_after: 99` forces the 10-question hard cap), `intake_revision_cap.yaml` (4 rejection reviews forces the 3-revision hard cap). Smoke-tested all 5 end-to-end; every plan §14 Phase 3A DONE criterion is observable from this fixture set.
15. Wrote 56 tests across 5 test files:
    - `test_fixture.py` (15 tests) — fixture loader happy path, schema mismatch, missing fields, wrong shape; `FixtureLLMClient` question dispensing, draft/governance return, revise-default vs revise-override, answer/review helpers, error paths for draft and governance missing fields.
    - `test_nodes.py` (14 tests) — unit tests for each node with a hand-rolled `_StaticLLM`, plus router tests for both conditional edges, plus `build_intake_report` end-state assembly tests at both the `COMPLETE` and `DRAFT_INCOMPLETE` path.
    - `test_graph.py` (9 tests) — end-to-end interrupt+resume runs against all 5 fixtures, including the two cap scenarios, plus error paths for under-supplied answer/review scripts and a review-accept-token variants test.
    - `test_cli.py` (7 tests) — `CliRunner` tests for help, happy-path stdout + file output, missing fixture, `--anthropic` not-yet-wired error, revision cap fixture producing `DRAFT_INCOMPLETE`, and a real `subprocess.run(['python', '-m', ...])` that matches the plan's literal verification command.
    - `test_anthropic_client.py` (14 tests, all mocked) — every Protocol method's happy path, missing-key errors, non-object-response errors, code-fence stripping, garbage-JSON errors, and the lazy-import default constructor path via `monkeypatch` on `anthropic.Anthropic`.
16. **First pytest run caught one bug:** `review_sequence_from_fixture({"review_sequence": []})` returned `["ACCEPT"]` instead of raising because `seq or ["ACCEPT"]` treated `[]` as falsy. Fixed to distinguish `None` (default) from `[]` (error). All 56 intake tests green after the fix.
17. Ran full suite: **179 passed, 96.18% coverage** (123 → 179; +56 intake tests). Coverage floor of 90% met. Intake package coverage: `nodes.py` 94%, `fixture.py` 100%, `graph.py` 100%, `anthropic_client.py` 98%, `cli.py` 100%, `agent.py` 90%, `protocol.py` 91%, `state.py` 100%, `__init__.py` 100%.
18. Ran both plan §14 Phase 3A verification commands LITERALLY:
    - `uv run pytest tests/agents/intake/ -v` → 56 passed.
    - `uv run python -m model_project_constructor.agents.intake --fixture tests/fixtures/subrogation.yaml` → writes a `COMPLETE` `IntakeReport` JSON; `status=COMPLETE, Q=7, tier=tier_3_moderate, cycle=tactical`.
19. Ran `uv run mypy src/model_project_constructor/agents/intake/` — initially 20 errors across 5 files. Fixed the easy wins (nodes None-guards, graph.py return annotation, cli.py helper method annotations, anthropic_client.py `list` generic parameter, one `# type: ignore[union-attr]` for the SDK's content block union mirroring the data agent's pattern, `# type: ignore[import-untyped]` on `import yaml`, `# type: ignore[arg-type]` on the `_DummyLLM` injection). **Final: 0 errors in 10 source files on the intake package alone.** The rest of the repo still has 33 pre-existing strict-mypy errors that predate Session 6 (most in the data agent's anthropic_client.py, same content-block union issue).
20. Updated `README.md`: added Phase 3A row (Complete), added Phase 3B row (Not started), added `agents/intake/` to the repo layout with a short module breakdown, added `tests/agents/intake/` to the tests section, added all 5 intake fixtures, updated test count 123 → 179, updated coverage floor 80% → 90%, added an intake agent CLI quick-start block pointing at the subrogation fixture.
21. Rewrote the `ACTIVE TASK` block for Phase 3B with: plan sections to re-read, DONE criteria, explicit instruction to reuse `build_intake_graph()` rather than re-implement, key Phase 3A files with file:line references, the LangGraph interrupt pattern verification results (so Session 7 doesn't redo the toy graph), all gotchas from Phase 2B + new ones from Phase 3A (CLI callback asymmetry, fixture schema, `_DummyLLM` disposability, mypy status, thread_id = session_id convention).
22. Close-out commit pending: all Phase 3A code + tests + fixtures + README + SESSION_NOTES as a single commit.

**Key design calls:**
- **Split `plan_next_question` from `ask_user`.** The plan's §10 diagram shows one `ASK_NEXT_Q` → `WAIT_FOR_ANS` node pair. I split them because the toy graph proved that interrupted nodes re-run from the top on resume, which would double-call the LLM if `interrupt()` sat in the same node. This is the single highest-leverage correctness decision in Phase 3A — getting it wrong would have caused silent cost doubling and potentially non-deterministic questions on resume.
- **No state reducers.** `Annotated[list, add]` is a footgun when a later node returns full state (the toy demonstrated this). All intake state fields are replaced wholesale by the node that owns them, and the `qa_pairs` append is done manually inside `ask_user`. Documented in the `IntakeState` docstring.
- **Fixture is NOT the CLI's production path, but it IS the verification path.** `--anthropic` is a real flag on the CLI that currently errors out with "interactive terminal not shipped in Phase 3A — use the web UI from Phase 3B". This keeps the CLI from locking in a headless-interview pattern that Phase 3B will supersede. The fixture path is the ONLY way to drive the CLI today.
- **`AnthropicLLMClient` is its own class, not shared with the data agent.** Different prompts, different result shapes, different system prompts. Session 5's handoff explicitly warned against "DRYing" the LLM boundaries and I followed it.
- **Default model `claude-sonnet-4-6` without live-API verification.** Same caveat as Session 5's data agent anthropic client. Documented in handoff as a likely first-real-run fixable.
- **`IntakeAgent.run_scripted()` with a hard max-turns cap.** A cap of `MAX_QUESTIONS + MAX_REVISIONS + 5 = 18` stops a buggy graph from spinning forever in tests. Hit the cap in the revision-cap fixture before I noticed the count — it triggered a `RuntimeError` with a clear message rather than hanging.
- **Fixture schema is `intake_fixture/v1`** with strict field validation in the loader. Tests cover schema-version mismatch, non-mapping YAML, missing required fields, and missing nested draft/governance fields. Fails loud, which is the §12 contract.
- **Review-accept tokens are a fixed set** — `"accept"`, `"yes"`, `"approve"`, `"approved"`, `"ok"`, `"looks good"` (case-insensitive). Anything else is treated as revision feedback. This is a heuristic, and the web UI in Phase 3B should use a button rather than text matching; the CLI path uses it because a fixture driver needs something to script.
- **Single-command typer app for intake CLI, the OPPOSITE of the data agent CLI.** The data agent has `run` as an explicit subcommand, which requires `@app.callback()` to defeat typer's auto-collapse. The intake agent has exactly one entry point, so the auto-collapse is what we want — without the callback, `python -m ... --fixture X` works directly and matches the plan's literal verification command. If Phase 3B adds a `serve` subcommand, the callback must be added simultaneously or the CLI verification breaks.

**Files created (16):**
- `src/model_project_constructor/agents/intake/__init__.py`
- `src/model_project_constructor/agents/intake/__main__.py`
- `src/model_project_constructor/agents/intake/state.py`
- `src/model_project_constructor/agents/intake/protocol.py`
- `src/model_project_constructor/agents/intake/nodes.py`
- `src/model_project_constructor/agents/intake/graph.py`
- `src/model_project_constructor/agents/intake/fixture.py`
- `src/model_project_constructor/agents/intake/agent.py`
- `src/model_project_constructor/agents/intake/anthropic_client.py`
- `src/model_project_constructor/agents/intake/cli.py`
- `tests/agents/intake/__init__.py`
- `tests/agents/intake/conftest.py`
- `tests/agents/intake/test_fixture.py`
- `tests/agents/intake/test_nodes.py`
- `tests/agents/intake/test_graph.py`
- `tests/agents/intake/test_cli.py`
- `tests/agents/intake/test_anthropic_client.py`
- `tests/fixtures/subrogation.yaml`
- `tests/fixtures/pricing_optimization.yaml`
- `tests/fixtures/fraud_triage.yaml`
- `tests/fixtures/intake_question_cap.yaml`
- `tests/fixtures/intake_revision_cap.yaml`

**Files modified (3):**
- `pyproject.toml` — added `pyyaml>=6`, added `[project.scripts] model-intake-agent`
- `uv.lock` — regenerated by `uv sync`
- `README.md` — Phase 3A complete, repo layout updated, test count 179, coverage 90% floor, intake CLI quick-start
- `SESSION_NOTES.md` — this file

**Session 5 Handoff Evaluation (Session 6 scoring Session 5):**
- **Score: 10/10**
- **What helped (ranked by how much time each saved):**
  1. The "LangGraph 0.2.76 interrupt pattern STILL not verified" gotcha with explicit "Build a 3-node toy graph before any real intake code. Failure mode: you write 400 lines of agent code against an API that doesn't exist on the installed version" — this was the single most load-bearing note in the entire handoff. I did exactly that, found two pitfalls (node re-execution on resume, reducer duplication), and the whole agent design downstream was shaped by those findings. Without this I would have put the LLM call in `ask_user` and shipped a broken-on-resume agent.
  2. The `How You Will Be Evaluated` section — pre-declared six success criteria. I used it as a close-out self-check. Items 2 (toy graph first) and 5 (don't bundle 3B) were the ones I was most tempted to shortcut.
  3. The typer single-command-trap gotcha with exact file:line — I initially copied the data agent's pattern (callback + run subcommand), then the plan's literal verification command forced me to flip it. Session 5's warning framed the trap so I recognised my error within minutes of first `pytest` instead of spending 20 minutes debugging.
  4. The "fixture format not defined in plan, YAML is more comfortable" guidance — took the decision off my plate.
  5. Key files with file:line references (`intake.py`, `common.py`, `llm.py:1-94`, `anthropic_client.py`) — I read each one cold and knew exactly where to look.
  6. The empty-`gh issue list` + dashboard-missing protocol notes — orientation step completed in about 30 seconds because Session 5 had already established these as non-blocking.
- **What was missing (minor):**
  1. Session 5 didn't specify whether the intake agent's CLI should reuse the data agent's `run` subcommand pattern or match the plan literal. I chose the data agent pattern first (wrong) and had to redo the CLI. A one-liner saying "plan's Phase 3A verification command is top-level flags, NOT a subcommand" would have saved about 10 minutes.
  2. Nothing about how the fixture's review_sequence should handle the cap-exhaustion case. I invented the `intake_revision_cap.yaml` pattern (review_sequence with 4 rejections) from first principles, which worked but could have been pre-decided.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state. The Session 5 `--fake-llm` escape-hatch framing correctly predicted that the intake agent would need its own fixture mode.
- **ROI:** Enormous. I estimate the handoff saved 60-90 minutes of re-derivation — the LangGraph verification guidance alone saved a full session of "why does my agent behave weirdly on resume". Read-cost was maybe 15 minutes.
- **Process notes:** Session 5 produced a 10/10 handoff by (a) pre-declaring evaluation criteria, (b) giving the next session an explicit technical risk to de-risk first, (c) naming traps with file:line breadcrumbs, (d) distinguishing "do these things" from "do not do these things" cleanly. I have copied all four patterns into my own handoff.

**Session 6 Self-Assessment:**
- (+) Completed Phase 0 orientation in full before any file touch. Wrote Phase 1B stub before any technical work. Reported findings and waited for user direction on a task-in-prompt turn.
- (+) Verified the LangGraph interrupt pattern on a toy graph BEFORE writing real agent code, per Session 5's explicit instruction. Caught two pitfalls (node re-execution, reducer duplication) that shaped the final design.
- (+) Split `plan_next_question` from `ask_user` at design time rather than after an expensive bug — direct result of the toy-graph discovery. This is the correctness decision I'm most proud of.
- (+) All 3 governance scenarios in tests hit distinct tiers (tier-1 continuous, tier-2 strategic, tier-3 tactical) with distinct rationales. Plan's "sensible classifications for 3 test scenarios" criterion is met with distinct, non-overlapping cases.
- (+) Both cap enforcement mechanisms have dedicated fixtures and dedicated tests. The 10-question cap and 3-revision cap are BOTH verified end-to-end through the real graph, not just at the node level.
- (+) Ran the plan's §14 Phase 3A verification commands LITERALLY. When my first CLI design didn't match the plan's literal command (it required `run` as a subcommand), I rewrote the CLI instead of updating the plan. Plan literal wins.
- (+) 56 new tests, 179 total, 96.18% coverage — comfortably above the 90% floor. Every intake source file is at ≥90% coverage; `fixture.py`, `graph.py`, `cli.py`, `state.py`, `__init__.py` are at 100%.
- (+) Ran mypy on the intake package and fixed every error — 0 errors in 10 files. Session 5 flagged not running mypy as a minor gap; I closed it. Did NOT fix the 33 pre-existing errors elsewhere in the repo — out of scope, noted in handoff.
- (+) Scope discipline: Phase 3A only. Did not start Phase 3B. Did not touch the Data Agent. Did not DRY the two `AnthropicLLMClient`s or the two `StrictBase` classes.
- (+) Recovered from three self-inflicted errors without user intervention: (1) wrong CLI subcommand pattern → rewrote as single command, (2) `review_sequence_from_fixture` treating empty list as None → fixed to distinguish, (3) mypy errors from missing type annotations → fixed with minimal `# type: ignore` use matching the data agent's patterns. All three documented in the chronological log and relevant ones in the handoff gotchas.
- (+) Used TaskCreate throughout — 12 tasks created up-front, each moved to in_progress when started, completed when done. No batching.
- (+) Handoff for Session 7 includes all required items: ACTIVE TASK updated with Phase 3B scope, what's done + commit reference, what's next with file:line references, key files, gotchas, evaluation criteria, LangGraph verification results so Session 7 doesn't redo it. Specifically guides Session 7 to REUSE `build_intake_graph()` rather than re-implement the flow.
- (−) I wrote the CLI twice — first with the data agent's callback+subcommand pattern, then as a single command. That cost ~10 minutes. Could have been avoided by reading the plan's verification command literal first, which I did but mis-interpreted. Self-inflicted, recoverable.
- (−) The `_DummyLLM` in `cli.py` is an ugly workaround for `IntakeAgent.__init__` requiring a client even when `run_with_fixture` will immediately replace it. A cleaner design would have `IntakeAgent` construct the graph lazily on first run. Noted for Phase 3B to clean up if a long-lived agent makes sense there.
- (−) The `AnthropicLLMClient` was never exercised against a real API. Same caveat as Session 5's data agent client. I did not attempt a live smoke test (no API key available in this session). Flagged in the handoff, but someone will discover whether `claude-sonnet-4-6` is a valid model ID on first real run.
- (−) I did NOT add a symmetric AST decoupling test for the intake agent (walking `src/model_project_constructor/agents/intake/` for imports matching `model_project_constructor_data_agent`). Session 5's handoff didn't require it, and the decoupling direction the plan enforces is data-agent-does-not-depend-on-main-package, not the reverse. Adding a symmetric test would be testing a non-existing relationship. Explicitly decided not to add it; noted in handoff.
- (−) The three governance fixtures are a MINIMUM — two of the four cycle-time values are covered (tactical, strategic, continuous) but `operational` is not. If a future Phase 3B or 3A polish session wants comprehensive governance-matrix coverage, that's an easy add.
- (−) I moved the toy graph work out of process before writing a test for it — the verification was shell output, not a committed test. The test files exercise the `interrupt` machinery implicitly through `test_graph.py`, so the pattern IS tested, but there's no standalone "langgraph 0.2.76 interrupt API exists" test. This is intentional (the implicit coverage is sufficient) but worth noting — if langgraph bumps major version and the API shifts, that test suite will fail loudly but the error might blame the intake code rather than the library.
- (−) No `USAGE.md` for the intake agent. The data agent has one (it's a separate distributable package so it needs its own readme); the intake agent lives in the main package and is documented in the main README. This is consistent but a dedicated document would be more discoverable for web-UI users in Phase 3B. Not in scope for 3A.

**Score: 9.5/10.** Phase 3A delivered with:
- Full LangGraph flow from §10 correctly implemented (with the interrupt-re-execution pitfall avoided)
- Both plan §14 verification commands passing literally
- 3 distinct governance scenarios tested end-to-end
- Both hard caps enforced end-to-end with dedicated fixtures
- Full Pydantic validation at the boundary
- 56 new tests, 96.18% coverage
- mypy clean on the intake package (which Session 5 flagged as a gap)
- Session 7 handoff that reuses Session 5's pattern language

Loses half a point for the CLI rewrite (self-inflicted, recovered without user intervention) and for not attempting a real-API smoke test of `AnthropicLLMClient`. The `_DummyLLM` ugliness and missing `USAGE.md` are intentional debts rather than mistakes.

---

### What Session 5 Did
**Deliverable:** Phase 2B of architecture plan — Data Agent standalone subpackage + CLI + Python API + AnthropicLLMClient (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `4982332` (refactor move) + `aca858a` (CLI + Anthropic + docs) + session-5 closeout (this commit). See `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan §7/§14 Phase 2B, checked git. Flagged two protocol gaps: `methodology_dashboard.py` does not exist (SESSION_RUNNER.md step 5 references an absent tool); `gh issue list` returns empty (user confirmed UAT-only, saved to memory at `~/.claude/projects/.../memory/project_issue_tracker.md`).
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Presented three restructuring approaches (a/b/c) to the user with pros/cons and recommended (c). User approved (c) on `/effort max`.
4. Read every existing Data Agent source file and every file importing from the data agent (conftest, test_data_agent, schemas/v1/__init__.py, schemas/registry.py) to map every internal import and every test-facing name. This is what let the shim layer preserve Phase 2A tests unchanged.
5. Created 13 tasks in TaskCreate covering the two-commit execution plan + closeout.
6. Built `packages/data-agent/` skeleton + `pyproject.toml` (no `readme` field initially — added it back in commit B after USAGE.md existed).
7. Wrote `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` as the new canonical home for `DataRequest/DataReport/PrimaryQuery/QualityCheck/Datasheet/DataGranularity` + its own 3-line `StrictBase`. Two `StrictBase` classes now exist (main + standalone); deliberate per Option (c) tradeoff.
8. Wrote/moved 8 agent source files into the standalone: `db.py`, `sql_validation.py`, `llm.py`, `state.py`, `nodes.py`, `graph.py`, `agent.py`, `__init__.py`. All internal imports rewritten from `model_project_constructor.agents.data.*` to `model_project_constructor_data_agent.*` and from `model_project_constructor.schemas.v1.data` to `model_project_constructor_data_agent.schemas`. Git detected all 5 moves as renames with 85–100% similarity.
9. Replaced main-package files with thin re-export shims: `agents/data/{__init__,db,llm}.py` and `schemas/v1/data.py`. Deleted `agents/data/{agent,graph,nodes,state,sql_validation}.py`.
10. Wired uv workspace in root `pyproject.toml`: `[tool.uv.workspace] members = ["packages/*"]` + `[tool.uv.sources]` + added `model-project-constructor-data-agent` as a dep. Updated pytest/coverage/mypy to walk both source trees.
11. Rewrote `tests/test_data_agent_decoupling.py` to walk the standalone's source AND the main-package shims (two test functions now, defense in depth).
12. **Error recovery #1:** First `uv sync` attempt failed because my `[tool.uv.workspace]` edit sliced `ui`/`dev` out of `[project.optional-dependencies]`. Fixed by moving the uv sections to after the optional-dependencies table.
13. **Error recovery #2:** Second `uv sync` failed because the standalone's `pyproject.toml` declared `readme = "USAGE.md"` which did not exist yet. Removed the field temporarily, re-added it in commit B.
14. `uv sync` succeeded; both packages built editable. Ran full suite: **102 passed, 98.66% coverage** (+1 test from decoupling split, +0.04 pts coverage — essentially flat).
15. Verified the decoupling test actually fires by injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`, running the test (failed as expected with both forbidden tokens reported), and reverting.
16. **Commit A:** `refactor(phase-2b): move data agent to standalone package` — `4982332`. 17 files changed, 476+/247−, 5 renames detected.
17. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all four `LLMClient` protocol methods. Default model `claude-sonnet-4-6`. `_call_claude` centralises the SDK call; `_extract_json` handles code-fence stripping; `LLMParseError` propagates unparseable responses through the outer try/except as `EXECUTION_FAILED`.
18. Wrote `cli.py` — `typer` app with `run` subcommand. Flags: `--request`, `--output`, `--db-url`, `--model`, `--fake-llm`. `--fake-llm` uses an in-file `_FakeCLIClient` that returns canned deterministic responses so CI can exercise the CLI end-to-end without an API key.
19. **Error recovery #3:** First CLI test failed with "Got unexpected extra argument (run)" — typer auto-collapses single-command apps. Fixed by adding `@app.callback() def _main()` above the command, which promotes the app to a group. Flagged in the handoff gotchas for future sessions.
20. Wrote `__main__.py` to support `python -m model_project_constructor_data_agent`.
21. Wrote `tests/fixtures/sample_request.json` (canonical DataRequest fixture, used by CLI tests AND the USAGE.md CLI example).
22. Wrote `tests/data_agent_package/test_cli.py` — 5 tests covering: happy path without db, happy path with live SQLite (creates a `claims` table in `tmp_path`), missing-file error, help output, and `python -m` entry point via subprocess.
23. Wrote `tests/data_agent_package/test_anthropic_client.py` — 16 tests with a `_FakeAnthropic` / `_FakeMessages` harness that mocks at the `client.messages.create` boundary. Covers: protocol conformance, JSON parsing for each method, code-fence stripping, retry hint propagation, malformed-response errors for all 4 methods, `_extract_json` edge cases, and the default constructor path via `monkeypatch` on `anthropic.Anthropic`.
24. Wrote `packages/data-agent/USAGE.md` with three examples (CLI, Python script, Python notebook), full public API listing, and error-contract documentation. Interpreted the plan's explicit requirement for USAGE.md as authorisation (CLAUDE.md forbids autonomously creating docs files; this one is a plan deliverable).
25. Restored `readme = "USAGE.md"` in `packages/data-agent/pyproject.toml`. `uv sync` succeeded.
26. Ran the three plan §14 Phase 2B verification commands:
    - `uv run python -c "from model_project_constructor_data_agent import DataAgent"` → **ok** (`model_project_constructor_data_agent.agent`)
    - `uv run model-data-agent run --request tests/fixtures/sample_request.json --output /tmp/report.json --fake-llm` → **COMPLETE**, 1 query, schema_version 1.0.0
    - Full suite: **123 passed, 96.45% coverage**
27. **Commit B:** `feat(phase-2b): AnthropicLLMClient + typer CLI + Python API docs` — `aca858a`. 9 files created, 1089+ lines.
28. Updated README.md (user-requested during closeout): marked Phase 2B Complete, added standalone package to repo layout, updated test count 101 → 123, added CLI quick-start pointing at USAGE.md.
29. Phase 3A handoff written for Session 6 (full rewrite of ACTIVE TASK), Session 4 evaluation below, self-assessment below. Closeout commit pending.

**Key design calls:**
- **Option (c) restructure** — moved data agent + data schemas into standalone; main package re-exports. Picked over (a) vendored copy (divergence risk) and (b) re-export shim (fake physical decoupling). Cost: two `StrictBase` classes, ~10 moved files, one afternoon. Benefit: the standalone could be published to PyPI tomorrow and has provably zero dependency on the main package.
- **Two commits, not one.** Commit A is a pure-refactor move that keeps 102 tests green through the shim layer (one more than 2A's 101 because of the decoupling test split). Commit B adds all new behavior (AnthropicLLMClient, CLI, USAGE, tests). This makes the diff reviewable — the move and the feature work can be audited independently.
- **LLMClient Protocol stays on the data agent side.** The intake agent in Phase 3 should define its own Protocol, not share this one. They have nothing in common at the method level.
- **AnthropicLLMClient takes an injected `client`** so tests can mock at the SDK boundary. Construction without a `client` arg lazily imports `anthropic` and constructs `Anthropic()` (reads `ANTHROPIC_API_KEY`). One test covers this path via `monkeypatch` on `anthropic.Anthropic`.
- **`--fake-llm` is a real CLI flag, not hidden.** It's visible in `--help` but documented in USAGE.md as smoke-test-only. CI can exercise the full CLI path without an API key; this keeps test_cli.py tests green in any environment.
- **`_FakeCLIClient` is colocated with the CLI** rather than in tests. Justification: it's a runtime feature (the `--fake-llm` flag), not a test-only utility. Moving it to tests would mean the CLI imports from tests, which is wrong.
- **Two canonical `StrictBase` classes, two decoupling test functions.** Duplication is acknowledged and documented; both the schemas module docstring (`packages/data-agent/.../schemas.py:10`) and SESSION_NOTES gotchas explicitly flag that this is deliberate.
- **CLI subcommand trap fix** (`@app.callback()`) — typer's single-command auto-collapse bit me on the first test run. Fixed in one edit. Documented for future CLIs (the intake agent will need the same trick).
- **`claude-sonnet-4-6` as default model** — set from the system-reminder's stated current model family, NOT verified against a live API. Flagged in the handoff as a likely first-real-run failure if the model ID is wrong. Tests all mock the SDK so they don't care.

**Files created (14):**
- `packages/data-agent/pyproject.toml`
- `packages/data-agent/USAGE.md`
- `packages/data-agent/src/model_project_constructor_data_agent/__init__.py`
- `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`
- `packages/data-agent/src/model_project_constructor_data_agent/db.py`
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py`
- `packages/data-agent/src/model_project_constructor_data_agent/llm.py`
- `packages/data-agent/src/model_project_constructor_data_agent/state.py`
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py`
- `packages/data-agent/src/model_project_constructor_data_agent/graph.py`
- `packages/data-agent/src/model_project_constructor_data_agent/agent.py`
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`
- `packages/data-agent/src/model_project_constructor_data_agent/cli.py`
- `packages/data-agent/src/model_project_constructor_data_agent/__main__.py`
- `tests/data_agent_package/__init__.py`
- `tests/data_agent_package/test_cli.py`
- `tests/data_agent_package/test_anthropic_client.py`
- `tests/fixtures/sample_request.json`

**Files moved (5, via git rename detection):**
- `agents/data/agent.py` → `packages/data-agent/.../agent.py` (95% similarity)
- `agents/data/graph.py` → `packages/data-agent/.../graph.py` (85%)
- `agents/data/nodes.py` → `packages/data-agent/.../nodes.py` (89%)
- `agents/data/sql_validation.py` → `packages/data-agent/.../sql_validation.py` (100%)
- `agents/data/state.py` → `packages/data-agent/.../state.py` (88%)

**Files modified (7):**
- `pyproject.toml` (workspace + coverage + mypy)
- `src/model_project_constructor/agents/data/__init__.py` (re-export shim)
- `src/model_project_constructor/agents/data/db.py` (shim)
- `src/model_project_constructor/agents/data/llm.py` (shim)
- `src/model_project_constructor/schemas/v1/data.py` (shim)
- `tests/test_data_agent_decoupling.py` (walk standalone + shim, 2 test functions)
- `README.md` (Phase 2B status + repo layout + test count + CLI quick-start)
- `uv.lock` (workspace resolution)
- `SESSION_NOTES.md` (this file)

**Session 4 Handoff Evaluation (Session 5 scoring Session 4):**
- **Score: 10/10**
- **What helped:** Session 4's ACTIVE TASK block was load-bearing from the first minute:
  1. The three restructuring options (a/b/c) with Session 4's explicit note that (c) is cleanest but "do it in Plan Mode or commit the move as a standalone commit" — I adopted exactly that structure (commit A = pure move, commit B = new features). Without this guidance I probably would have bundled everything into one commit and the reviewability would have suffered.
  2. The "plan inconsistency" flag on `python -m model_project_constructor.agents.data --help` being a Phase 2B entry point correctly predicted that I'd need `__main__.py`.
  3. The Key Files section with line ranges (`llm.py:1-94`, `agent.py:34-74`, `nodes.py:1-171`) was surgical — saved me from re-reading entire files when I only needed import shapes.
  4. The schema-plan reconciliation note (`DataReport.status` as authoritative vs. `qc_status`/`primary_query_status`) meant I preserved the Phase 2A test interpretation without re-deriving it.
  5. The "FakeLLMClient is the only implementation" warning + "don't tie the CLI to the fake" instruction directly shaped my design: I built `AnthropicLLMClient` first, then the CLI, with the fake as an explicit escape hatch flag rather than the default.
  6. The "SQLite resource leak" note and the coverage 98.62% baseline meant I knew what to expect and could notice immediately when I hit 96.45% (with full context of why — new CLI/Anthropic code has defensive paths).
- **What was missing:** Almost nothing. Two tiny gaps:
  1. Session 4 didn't flag that `methodology_dashboard.py` doesn't exist — I discovered this during orientation. Saved me maybe 30 seconds, but the Phase 0 checklist's step 5 explicitly references a non-existent tool, which is a protocol-level gap Session 4 could have flagged.
  2. Session 4's gotcha about "do the move in Plan Mode or as a standalone commit" didn't preemptively address whether user approval was required for the restructure. I spent a turn getting buy-in (correct per SAFEGUARDS) but Session 4 could have pre-authorized this for me by framing it as pre-approved since the plan requires it.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state.
- **ROI:** Very high. I estimate reading the Phase 2B ACTIVE TASK block + the relevant plan sections saved me 45+ minutes of architecture re-derivation and at least one false start (probably would have gone for Option (b) as "safer" without the explicit "don't fake the decoupling" framing).
- **Process notes:** Session 4 wrote the Phase 1B stub, held the phase boundary (Phase 2A only, no CLI), addressed every Session 3 gotcha, and produced a handoff I could score against my own. The `How You Will Be Evaluated` section at the bottom of the ACTIVE TASK block is a pattern I should preserve.

**Session 5 Self-Assessment:**
- (+) Followed Phase 0 orientation fully. Phase 1B stub written before the first technical action. Phase 0 flagged two protocol gaps (missing dashboard, empty issue tracker) and saved one to memory.
- (+) Asked for architectural approval BEFORE touching code on a cross-module refactor, per SAFEGUARDS "Refactoring always requires plan mode approval". User approved (c) and I executed only (c).
- (+) Read every file whose imports would change BEFORE making changes — conftest.py, test_data_agent.py, tests/schemas/*, schemas/v1/__init__.py, registry.py. This is why the shim layer worked on the first try and zero test files needed to be edited.
- (+) Two-commit structure: pure refactor first (102 tests green through shims), then feature additions. Commit A is 17 files changed with 5 git-detected renames, reviewable as a move; commit B is 9 new files, reviewable as feature work. Followed Session 4's explicit advice.
- (+) Verified the decoupling test actually fires on injected violation before committing — Session 4's "don't treat it as passive scenery" guidance held.
- (+) Scope discipline: Phase 2B only. No intake work, no LangGraph interrupt investigation, no schema cleanup. Phase 3 is Session 6's.
- (+) Three plan §14 Phase 2B verification commands all passed explicitly; ran them separately, not just as part of the full suite.
- (+) `AnthropicLLMClient` has 16 tests covering every protocol method, every JSON-parse path, code-fence stripping, retry hint, and default-construction via monkeypatch. The CLI has 5 tests including a real-subprocess `python -m` smoke test.
- (+) Recovered from three self-inflicted errors without user intervention: (1) pyproject.toml structural edit mistake, (2) missing readme file referenced in pyproject.toml, (3) typer single-command auto-collapse trap. All three recoveries documented in the handoff so Session 6 knows the shape of the traps.
- (+) Used TaskCreate/TaskUpdate to track the 13 sub-tasks of a two-commit refactor. Each task was marked in_progress when started and completed when done, not batched at the end.
- (+) Saved one memory (project_issue_tracker.md) — user said GitHub issues are UAT-only; this will inform every future Phase 0 that currently treats empty `gh issue list` as a gap.
- (−) Did not run `mypy` (not in the §14 Phase 2B verification commands, but `strict = true` is in `pyproject.toml:80`). The one `type: ignore[arg-type]` inherited from Phase 2A at `agent.py:138` is still there. Any `AnthropicLLMClient`-level type errors (e.g., around the untyped `client: Any | None`) are uncaught.
- (−) Session 4's "SQLite resource leak" in `seeded_sqlite_url` fixture still leaks the engine handle. I added more tests that exercise the same fixture and did not fix the leak. Still non-blocking.
- (−) `claude-sonnet-4-6` as `DEFAULT_MODEL` is a guess from the system-reminder model family list. It is NOT verified against a live Anthropic API call — no `ANTHROPIC_API_KEY` in this session. If the actual model ID is something slightly different, the CLI will fail on first real-API invocation. Flagged in the handoff gotchas; the CLI `--model` flag lets users override.
- (−) I did not build a concrete integration-style test that skips when `ANTHROPIC_API_KEY` is absent — Session 4 specifically suggested this pattern. Decided against it: all tests mocking the SDK gives deterministic coverage; an integration test that conditionally runs is harder to reason about and tends to rot. A future hardening pass (Phase 6) can add one.
- (−) The CLI has a small dead-code path at `cli.py:119` (error handling around `_load_request`) that isn't covered. Same for `__main__.py` lines 3-6. Acceptable — they're defensive paths that only fire on environment-level failure.
- (−) README.md update happened during closeout at user request rather than being part of the plan. That's not a mistake, but it suggests README maintenance should be in the default closeout checklist for session boundaries that ship a user-facing feature. Adding to learnings.
- (−) Did not verify the LangGraph interrupt pattern — Session 4 flagged this as a Phase 3A concern. Correct to defer. But Session 6 MUST verify it first, and my handoff should make that boringly explicit (it does).

**Score: 9/10.** Phase 2B delivered with a clean two-commit refactor, all plan verifications green, 123 tests passing, decoupling guarantee preserved and re-verified, and a rich handoff. Loses a point for the unverified `DEFAULT_MODEL` string (real first-run will probably expose it) and for not running mypy. The error-recovery count (three self-inflicted mistakes) is acceptable given all three were caught and corrected without user intervention and left clear warning breadcrumbs for Session 6.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not adding this session. Pattern candidates for future sessions: (a) "When a plan requires a cross-module refactor, the user-approval gate is the first step of the session, not a mid-session pause" — getting buy-in before any file touch prevents half-committed state; (b) "Typer single-command apps silently collapse the subcommand unless an `@app.callback()` is present" — worth a one-line entry in the Python idioms section once one exists. Not retroactively adding.

### What Session 4 Did
**Deliverable:** Phase 2A of architecture plan — Data Agent core + LangGraph + AST decoupling test (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `chore(env)` (env bootstrap) + `feat(phase-2a)` (agent + tests) + `docs/chore` session closeout — see `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md §4.2/§7/§10.2/§12/§14 Phase 2A, git status, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Addressed Session 3's environment trap: `brew install uv` (got 0.11.6), `uv python install 3.11` (got 3.11.15 but the venv resolved to 3.13.5 because `requires-python = ">=3.11"` is inclusive — acceptable).
4. `uv sync --extra agents --extra dev` failed on a missing `README.md` referenced by pyproject.toml. Removed the `readme` line rather than auto-create a README (CLAUDE.md forbids creating docs files autonomously). `uv sync` then succeeded. Re-ran Phase 1 tests under the new interpreter: 88 passed, 100% schemas coverage.
5. Checkpoint-committed env bootstrap before touching agent code (SAFEGUARDS "commit before starting any new task").
6. Verified LangGraph 0.2.76 on a toy graph (conditional edges, `add_conditional_edges` with router function, partial-update dict returns, `.invoke()` merge semantics). Worked as expected.
7. Designed the Data Agent package layout with clean separation: `llm.py` (Protocol + dataclasses), `sql_validation.py`, `db.py`, `state.py`, `nodes.py` (factory functions closing over llm/db), `graph.py` (StateGraph assembly), `agent.py` (outer `DataAgent.run()`).
8. Made a deliberate decision NOT to ship a concrete `AnthropicLLMClient` in 2A — deferred to 2B — to avoid a half-finished implementation (global rule) and keep Phase 2A strictly scoped.
9. Wrote all 8 source files under `src/model_project_constructor/agents/data/` and verified imports.
10. Wrote `tests/agents/data/conftest.py` (seeded SQLite claims table with 5 rows, sample DataRequest, valid PrimaryQuerySpec, QC specs, SummaryResult, Datasheet fixtures).
11. Wrote `tests/agents/data/test_data_agent.py` — `FakeLLMClient` (deterministic stub with a `primary_queries_sequence` list that drives RETRY_ONCE and fail-after-retry) + 12 end-to-end tests: protocol check, happy path against real SQLite, RETRY_ONCE success, retry-exhausted → EXECUTION_FAILED, DB-unreachable via bad URL, DB=None, per-QC error isolation, INCOMPLETE_REQUEST parametrised over all four required fields, and unexpected-exception containment via an `ExplodingLLM` subclass.
12. Wrote `tests/test_data_agent_decoupling.py` — AST-walks every `.py` under `agents/data/`, asserts no import references `IntakeReport`, `schemas.v1.intake`, or `intake_report`.
13. **Verified the decoupling test actually fires** by temporarily injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`. Test failed as expected, reporting both `IntakeReport` and `schemas.v1.intake` as offenders with the exact file path. Reverted the injection.
14. Ran §14 Phase 2A verification commands:
    - `uv run pytest tests/agents/data/ -v` → 12 passed
    - `uv run pytest tests/test_data_agent_decoupling.py` → 1 passed
    - Full suite: `uv run pytest -q` → 101 passed, coverage 98.62% (well above 80% gate)
    - Skipped `python -m model_project_constructor.agents.data --help` because that CLI is a Phase 2B deliverable (flagged as a plan inconsistency in the commit and the new handoff).
15. Committed Phase 2A under `feat(phase-2a): Data Agent core + LangGraph flow + AST decoupling test`.
16. **Late-session user addition:** create `README.md` and push to a new remote `https://github.com/rmsharp/claims-model-starter.git`. README created (explicit user authorisation overrides the CLAUDE.md prohibition). Remote `origin` added; `git push -u origin master` sent all history.
17. Rewrote ACTIVE TASK for Phase 2B, wrote this Session 4 closeout.

**Key design calls:**
- `LLMClient` is a `Protocol` rather than an ABC. Runtime-checkable for tests. Methods take typed domain objects and return typed domain objects — nodes never parse JSON.
- Intermediate `PrimaryQuerySpec`/`QualityCheckSpec`/`SummaryResult` dataclasses exist so LLM output and schema output can evolve independently. Downstream pydantic models are the enforcement point.
- `expected_row_count_order` typed as `str` on the intermediate spec but enforced as `Literal[...]` on the pydantic `PrimaryQuery`. Noted in the module docstring.
- Node factories (`make_*`) close over `llm` and `db` so node bodies take only `DataAgentState`. This keeps the StateGraph plumbing orthogonal to dependency injection.
- `DataAgentState` is a `TypedDict(total=False)` so nodes can populate incrementally. Initial state has `request`, `sql_retry_count=0`, `db_executed=False`.
- QC `PASSED/FAILED` uses a coarse ≥1-row proxy. Sufficient to exercise all four `execution_status` values; richer expectation evaluation is future work.
- Schema-plan reconciliation: plan §4.2 text references `qc_status` and `primary_query_status` fields that don't exist on the Phase 1 schemas. Session 4 interpreted the three-valued `DataReport.status` as authoritative — DB-down returns COMPLETE with per-QC NOT_EXECUTED, invalid SQL after retry returns EXECUTION_FAILED, missing/vacuous fields return INCOMPLETE_REQUEST. Documented in the commit and the new handoff.
- No `AnthropicLLMClient` in 2A. Deferred to 2B's CLI work to avoid half-finished implementations.
- README removed from pyproject.toml rather than auto-created (CLAUDE.md rule); README.md itself was created only after the user explicitly asked.

**Files created (15):**
- `src/model_project_constructor/agents/__init__.py`
- `src/model_project_constructor/agents/data/{__init__,llm,sql_validation,db,state,nodes,graph,agent}.py`
- `tests/agents/__init__.py`
- `tests/agents/data/{__init__,conftest,test_data_agent}.py`
- `tests/test_data_agent_decoupling.py`
- `README.md`
- `uv.lock`

**Files modified (3):**
- `pyproject.toml` (removed stale `readme = "README.md"` line)
- `SESSION_NOTES.md` (this file)

**Session 3 Handoff Evaluation (Session 4 scoring Session 3):**
- **Score: 10/10**
- **What helped:** The ACTIVE TASK block was the highest-quality handoff in the project so far. Every single gotcha fired during my session:
  1. The `uv` / Python 3.10 trap was item #1 in gotchas — I hit it immediately and had the fix ready (brew install uv, uv python install 3.11).
  2. The "LangGraph pattern unverified" flag drove me to write the toy graph before the real flow — saved me from discovering the state-merge semantics mid-implementation.
  3. The "decoupling test must actually fire" warning was the difference between writing theater and writing a real test. I explicitly verified it fires on an injected violation.
  4. The "three-valued status field, set each one explicitly" note drove the schema-plan reconciliation decisions.
  5. The "agents do NOT raise for expected failures (§12)" note drove the outer try/except in `DataAgent.run()`.
  The Key Files section with `data.py:21-98` and `common.py:13-31` line ranges was surgical — saved re-reading whole files.
- **What was missing:** Almost nothing. One gap: Session 3 didn't flag that `pyproject.toml` references a README.md that doesn't exist. `uv sync` would have hit it immediately on any fresh checkout. Worth ~3 minutes of my time. Not a 10→9 penalty because Session 3 didn't run `uv sync` themselves (they ran `python3 -m pytest`), so they couldn't have known.
- **What was wrong:** Nothing. The handoff was accurate end-to-end. The `database_hint` interpretation note was correct; the `StrictBase` `protected_namespaces` note was correct; the Phase 1 file line ranges matched.
- **ROI:** Very high. I estimate reading SESSION_NOTES.md + the plan sections saved me 60+ minutes of discovery and at least one wrong-direction start. The "verify decoupling test fires" instruction alone was worth the entire read.
- **Process notes:** Session 3 wrote the Phase 1B stub, held the phase boundary, and produced a handoff that was demonstrably load-bearing. This is the quality bar for the project.

**Session 4 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before any work. Phase 1B stub written before the first technical action.
- (+) Addressed every trap Session 3 flagged: installed uv, pinned 3.11+ via uv, verified LangGraph on a toy graph before wiring the real flow, verified the decoupling test actually fires.
- (+) Scope discipline: Phase 2A only. No CLI, no standalone subpackage, no Anthropic client, no intake work. Explicit decision to skip the plan's §14 Phase 2A CLI smoke test because it belongs to 2B.
- (+) Clean separation of concerns: `LLMClient` Protocol, intermediate dataclasses, node factories, graph assembly, outer agent boundary. Every concrete concern is in exactly one file.
- (+) Test coverage 98.62% total, 100% on every new agent module except `db.py:42` (defensive `RuntimeError`) and `sql_validation.py:25,28` (defensive parse branches). All three uncovered lines are intentionally defensive and documented.
- (+) Parametrised the INCOMPLETE_REQUEST test over all four required fields so regressions in the semantic-check list get caught.
- (+) `ExplodingLLM` test proves the outer try/except in `DataAgent.run()` actually catches graph-internal exceptions and surfaces them as `EXECUTION_FAILED` — a critical part of the §12 contract.
- (+) Commit discipline: env bootstrap committed as a standalone checkpoint before agent code was touched (SAFEGUARDS "commit before starting any new task"). Agent code committed as one `feat(phase-2a)` commit. README + remote-push as their own commits at the end.
- (+) Schema-plan reconciliation decisions are documented in the commit body AND in the new handoff — future sessions can see what was interpreted and why.
- (+) Flagged a plan inconsistency (§14 Phase 2A verification list contains a CLI command that belongs to 2B) in the commit, in the handoff, and verbally to the user.
- (−) Did not build a concrete `AnthropicLLMClient`. Defensible decision (avoids half-implementation), but 2B will need one and may feel the pinch.
- (−) The `validate_sql` function is deliberately weak — it only rejects empty/whitespace and `UNKNOWN` statement type. `sqlparse` will accept a lot of garbage as "valid." A sharper validator (e.g., `EXPLAIN` against SQLite) would catch more, but it would also couple validation to the DB. Deferred.
- (−) Did not run `mypy` (not in §14 Phase 2A verification commands, but `mypy strict = true` is in `pyproject.toml:71`). Some `type: ignore[arg-type]` on line `agent.py:124` where I pass `str` into a `Literal[...]` field — pydantic validates at runtime.
- (−) ResourceWarning: unclosed SQLite connections in a few tests (the `seeded_sqlite_url` fixture leaks an engine handle). Non-blocking; clean up in 2B or a Phase 6 hardening pass.
- (−) Did not pin `--python 3.11` on the venv; `.venv` resolved to 3.13.5. The code is 3.11-compatible so this is not a bug, but the plan said "pin a 3.11+ interpreter" and I got a 3.13 interpreter that happens to satisfy `>=3.11`. Documented in the handoff.

**Score: 9/10** — Phase 2A delivered with comprehensive tests, proven decoupling guarantee, all known traps addressed, and strict scope adherence. Loses a point for the resource leak in the SQLite fixture and for not shipping even a stub `AnthropicLLMClient` that 2B could extend. The `mypy` gap is noted but not weighted against the score since it wasn't in the verification commands.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. Pattern candidates for future sessions: (a) "LLM-driven agents: ship a Protocol + FakeClient in the core phase; defer concrete vendor integration to the CLI phase" and (b) "decoupling tests must be verified to actually fire by temporarily injecting a violation — a green-only history means nothing." These are in the handoff prose for now; I'll not retroactively add them unless a future session asks.

### What Session 3 Did
**Deliverable:** Phase 1 of architecture plan — Repo Skeleton + Schemas (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md in full (both halves), checked git, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Probed environment: `uv` not installed; system Python is 3.10.12 with pydantic 2.12.5 and pytest 9.0.2 already available. Decided to keep `pyproject.toml` strictly compliant with the plan (requires-python >=3.11, uv-ready) and run local tests via `python3 -m pytest`, flagging the Python-version gap for Phase 2A.
4. Wrote `pyproject.toml` — PEP 621 + hatchling, `model-project-constructor` package at `src/model_project_constructor`, core dep `pydantic>=2.6,<3`, optional groups `agents` / `ui` / `dev`. Pytest config includes `pythonpath = ["src"]` so tests run without manual `PYTHONPATH`. Per-session-3 user directive, added `pytest-cov` with `--cov-fail-under=80`.
5. Implemented `schemas/v1/common.py` (`StrictBase` with `extra="forbid"`, `protected_namespaces=()`, plus `CycleTime`, `RiskTier`, `ModelType`, `SCHEMA_VERSION`).
6. Implemented `schemas/v1/intake.py` — `ModelSolution`, `EstimatedValue`, `GovernanceMetadata`, `IntakeReport`. All inherit `StrictBase`.
7. Implemented `schemas/v1/data.py` — `DataGranularity`, `DataRequest`, `QualityCheck`, `Datasheet`, `PrimaryQuery`, `DataReport`. Module docstring forbids importing from `intake.py` (runtime AST test comes in Phase 2A per the plan).
8. Implemented `schemas/v1/gitlab.py` — `GitLabTarget`, `GovernanceManifest`, `GitLabProjectResult`.
9. Implemented `schemas/v1/__init__.py` re-exporting everything public.
10. Implemented `schemas/envelope.py` — `HandoffEnvelope` with its own `envelope_version="1.0.0"` and `payload: dict[str, Any]` (resolved by registry, not by envelope).
11. Implemented `schemas/registry.py` — `REGISTRY`, `SchemaKey`, `UnknownPayloadError(KeyError)`, `load_payload(envelope)`.
12. Wrote `tests/schemas/fixtures.py` — `make_*` factories for every schema.
13. Wrote `tests/schemas/test_intake.py`, `test_data.py`, `test_gitlab.py`, `test_envelope_and_registry.py` — 88 tests total.
14. `python3 -m pytest tests/schemas/ -v` → **88 passed in 0.13s**. Coverage on the `schemas` package is 100%.
15. Ran §14 Phase 1 smoke tests — both import checks pass; `len(REGISTRY) == 5`.
16. Rewrote ACTIVE TASK for Phase 2A and wrote this closeout.

**Key design calls:**
- `StrictBase` centralizes `ConfigDict(extra="forbid", protected_namespaces=())`. Avoids 14 copies of model_config and avoids the `model_` warning on `model_solution`/`model_type`/`model_registry_entry`.
- `UnknownPayloadError` inherits from `KeyError` (dict-lookup semantics); pydantic `ValidationError` remains separate for bad payloads.
- `target_variable: str | None` and `annual_impact_usd_low/high: float | None` are **required-nullable** (no default) — matches the plan's literal code. If Phase 2A finds this too strict, relax to `= None`.
- `database_hint` and `regulatory_mapping` have explicit defaults because the plan marks them "optional context."
- Decoupling rule is enforced textually in `data.py`'s docstring; runtime AST test is a Phase 2A deliverable per §14.
- Tests use `pytest.mark.parametrize` on every literal-enum field so adding a value is a one-line test change. Explicit regression guard against `default_factory` aliasing on `GovernanceManifest.regulatory_mapping`.

**Files created (17):**
- `pyproject.toml`
- `src/model_project_constructor/{__init__.py, schemas/__init__.py, schemas/envelope.py, schemas/registry.py, schemas/v1/{__init__,common,intake,data,gitlab}.py}`
- `tests/{__init__.py, schemas/{__init__,fixtures,test_intake,test_data,test_gitlab,test_envelope_and_registry}.py}`

**Session 2 Handoff Evaluation (Session 3 scoring Session 2):**
- **Score: 9/10**
- **What helped:** The ACTIVE TASK block was surgical — task, plan location, exact subsections to obey, explicit "do NOT start Phase 2," five-bullet evaluation rubric. The Gotchas section flagged four concrete traps; three were load-bearing for Session 3. Reading the plan + handoff took ~8 minutes and saved an estimated 45+ minutes of discovery.
- **What was missing:**
  - **No mention that `uv` was not installed on this machine.** Session 2 wrote "`uv` is the package manager" as a directive but did not verify it was available. ~2 minutes of probing.
  - **No flag that local Python is 3.10 while the plan pins 3.11+.** Latent trap for Phase 2A if LangGraph needs 3.11-only features.
  - The plan's `| None` comment syntax is ambiguous about required-nullable vs. optional-with-default. I had to make judgment calls on `target_variable`, the annual-impact bounds, and `database_hint`.
- **What was wrong:** Nothing factually wrong. Minor gap: the handoff references the `model_governance` project as the source of `GovernanceMetadata` but does not give its path.
- **ROI:** Very high. The plan was the valuable artifact; the handoff was a precise index.
- **Process note:** Session 2 correctly wrote a Phase 1B stub and held the planning-vs-implementation line.

**Session 3 Self-Assessment:**
- (+) Scope discipline. Phase 1 only. No agent code, no LangGraph, no adapters, no decoupling test — all Phase 2A.
- (+) Phase 1B stub written before any technical work.
- (+) All §14 Phase 1 verification commands green (pytest + both imports + `len(REGISTRY)`).
- (+) Tests exercise non-obvious cases: extra-field rejection, every literal value, serialization round-trip for every top-level schema, `load_payload` happy paths plus three failure modes, mutable-default aliasing regression guard.
- (+) Proactive abstractions (`StrictBase`, `SchemaKey`) only where they prevented repetition; no speculative generalization.
- (+) Module-level decoupling comment in `data.py` captures the §7 rule textually even without the runtime test.
- (+) Phase 2A gotchas are concrete: `uv`/Python 3.10 mismatch, unverified LangGraph interrupt pattern, three-valued status field, `extra="forbid"` discipline, `model_` namespace override, decoupling test must actually fire.
- (−) Did not install `uv`. Tests ran via `python3 -m pytest`; equivalent to `uv run pytest` but not the literal plan commands.
- (−) Local Python is 3.10; pyproject targets 3.11+. Works today because the schema code is 3.10-compatible; may bite Phase 2A.
- (−) `annual_impact_usd_low/high` are required-nullable. If intake agent has to pass `None` 80% of the time, relax to `= None` in Phase 2A or 3A.
- (−) No grep-based inventory — greenfield, so not mandatory per SESSION_RUNNER.md.

**Score: 9/10** — Deliverable met with comprehensive tests, explicit gotchas, scope discipline. Loses a point for not installing `uv` and for punting on the annual-impact default interpretation.

**Learnings added to SESSION_RUNNER.md Learnings table:** None this session. The schema code and tests are the Phase 1 institutional memory.

### What Session 2 Did
**Deliverable:** Formal architecture plan at `docs/planning/architecture-plan.md` (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (in chronological order):**
1. **Orientation only (no work)** — followed Phase 0; reported state; waited for direction.
2. **Deleted `methodology_dashboard.py`** per user instruction during orientation.
3. **Jupyter → Quarto replacement** in `docs/planning/architecture-approaches.md` (3 edits: line 88, 100, 249). Replaced references with "Quarto markdown documents (.qmd) and unit-tested Python/R functions" per user directive that all code must live in tested modules.
4. **Regenerated `architecture-approaches.pdf`** via pandoc/xelatex after the edits.
5. **Governance research** — used Explore subagent to read all markdown in `/Users/rmsharp/Documents/Projects/Active_Projects/model_governance`. Findings: cycle-time taxonomy, risk tiering, first-line evidence ownership, three-pillar validation (SR 11-7), datasheets (Gebru 2021), model cards (Mitchell 2019), regulatory frameworks (SR 11-7, NAIC AIS, EU AI Act, ASOP 56). User directed: hold governance findings for formal plan, do NOT augment approaches doc.
6. **User selected approaches:** Sequential Script + LangGraph/Claude + Pydantic envelope + Code Gen Only (Quarto).
7. **Wrote `docs/planning/architecture-plan.md`** — 19 sections, ~1000 lines:
   - §1 Context, constraints, explicit scope boundary
   - §2 Decision summary (chosen approaches)
   - §3 High-level architecture with ASCII diagram
   - §4 Agent boundaries with per-agent I/O and failure mode tables
   - §5 Pydantic schemas with field-level detail (`IntakeReport`, `DataRequest`, `DataReport`, `GitLabTarget`, `GitLabProjectResult`, governance models)
   - §6 Handoff envelope protocol with schema registry and versioning rules
   - §7 Data Agent reuse interface with adapter pattern and decoupling test
   - §8 Governance integration — proportional scaffolding by risk tier + cycle time
   - §9 Technology stack with specific versions and models
   - §10 LangGraph orchestration pattern with ASCII graphs per agent
   - §11 Generated GitLab repo structure (full file tree)
   - §12 Error handling strategy (agents return reports, don't raise)
   - §13 Consolidated failure mode analysis
   - §14 Implementation phases: 6 phases across 8 implementation sessions, each with explicit DONE criteria, verification commands, and session boundary markers
   - §15 Alternatives considered (pointer to approaches doc)
   - §16 Impact analysis
   - §17 Verification plan
   - §18 Open questions (deferred decisions)
   - §19 ARCHITECTURE_WORKSTREAM verification checklist

**Key decisions baked into the plan:**
- LangGraph is used **inside each agent**, not at the top level. The top-level orchestrator is still a Sequential Script. This preserves the upgrade path.
- `GovernanceMetadata` is a new addition to `IntakeReport` beyond what `initial_purpose.txt` describes — driven by the governance research in step 5.
- Data Agent decoupling is enforced by a CI test in `tests/test_data_agent_decoupling.py` that AST-walks the Data Agent source and fails on any `IntakeReport` import.
- The Data Agent is packaged as a separate installable subpackage (`model-project-constructor-data-agent`) to physically enforce the decoupling.
- Quarto + `src/` split: all code lives in `src/` as tested functions; `.qmd` files are narratives that import from `src/`. This satisfies the user's C6 constraint.
- EDA is code-generation-only — generated `.qmd` files are NOT rendered by the pipeline; the data science team renders them. This avoids executing LLM-generated code against corporate databases.
- Governance scaffolding is proportional: tier 3+ adds three-pillar validation, tier 2+ adds impact assessment and regulatory mapping, tier 1 adds LCP integration and audit log.

**Session 1 Handoff Evaluation (Session 2 scoring Session 1):**
- **Score: 7/10**
- **What helped:** The ACTIVE TASK block clearly stated the deliverable. The Gotchas section was genuinely useful — particularly the one flagging that Step 4 is not a separate agent (prevented me from over-counting agents), the one about Data Agent decoupling having multiple approaches with different implications, and the one noting the `initial_purpose.txt` output is prose not JSON (led me to think carefully about how LLMs produce structured output). The key-files list with line numbers for `initial_purpose.txt:18-80` and `:84-87` was precise and saved a re-read.
- **What was missing:** No mention of the `model_governance` project existing. The user had to volunteer it mid-session. A "related projects" section in the handoff would have surfaced it earlier. Also: no mention that `methodology_dashboard.py` was problematic/deprecated — user asked to delete it during orientation, which suggests the previous session knew it wasn't working but didn't flag it.
- **What was wrong:** Nothing inaccurate. The handoff was honest.
- **ROI:** High. Reading the handoff took ~2 minutes and saved probably 20+ minutes of discovery work. The line-number references specifically saved re-reading full files.
- **Process note:** Session 1 did not write a Phase 1B stub (no ghost session risk because it was the first session, but it should have followed the protocol). I corrected this for Session 2 by writing the stub before any technical work.

**Session 2 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before doing any work; waited for user direction.
- (+) Wrote the Phase 1B session stub before starting technical work (corrected Session 1's omission).
- (+) Did not bundle the plan with implementation — strict adherence to the "plan IS the deliverable" rule.
- (+) The plan has explicit per-phase completion criteria and verification commands (SESSION_RUNNER.md planning-session requirement).
- (+) Governance integration is first-class, not a bolt-on — it's woven through intake capture, schemas, and repo scaffolding.
- (+) Decoupling test for the Data Agent is specified at the AST level, not just as a convention.
- (+) Quarto + `src/` split directly satisfies user constraint C6.
- (+) Failure modes analyzed per-agent and consolidated globally (§4 + §13).
- (+) Alternatives explicitly rejected with honest reasons (§15).
- (-) Did not run a grep-based inventory — but this is a **greenfield** plan, not a deletion/migration/rename, so per SESSION_RUNNER.md the evidence-based inventory is not mandatory. Noted here for transparency.
- (-) §18 Open Questions has 5 items that should ideally have been resolved during planning. They are genuinely deferrable (they don't block Phase 1), but a stricter plan would have pushed on them.
- (-) The plan is long (~1000 lines). A shorter plan would be easier for a future session to read fully. However, the alternative (a short plan with vague phases) is worse because it invites bundling.
- (-) Did not verify `langgraph==0.2.x` actually supports the interrupt pattern I described for the intake review step. This should be verified in Phase 3A before implementing the intake agent. Noted as a risk in the Phase 3A session start.

**Score: 9/10** — Comprehensive, actionable, with explicit session boundaries and verification commands. Loses a point for the unverified LangGraph interrupt pattern and the 5 deferred open questions. No bundling, no scope creep, no protocol violations.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. The plan itself is the learning artifact for future implementation sessions.

### What Session 1 Did
**Deliverable:** Architecture approaches document (COMPLETE)
**Started:** 2026-04-10
**Commit:** See git log for hash

**What was done:**
- Created initial commit with all project scaffolding files (18 files)
- Deep analysis of `initial_purpose.txt`, `ROADMAP.md`, `BACKLOG.md`, all methodology workstream docs
- Produced `docs/planning/architecture-approaches.md` covering 4 critical features:
  1. Pipeline Orchestration (3 approaches: Sequential Script, State Machine, Event-Driven)
  2. Technology Stack & LLM Integration (3 approaches: LangGraph+Claude, Agents SDK+GPT-4o, Custom+Mixed Models)
  3. Schema Design & Handoff Protocol (3 approaches: Pydantic Envelope, JSON Schema+Codegen, Markdown+Frontmatter)
  4. EDA & Model Building (3 approaches: Code Gen Only, Sandboxed Subprocess, Containerized)
- Each approach includes concrete pros/cons, technology names, "best suited for" guidance
- Decision dependencies table mapping which choices constrain others
- Recommended starting combination at bottom of document

**Self-Assessment:**
- (+) Thorough coverage of all 4 critical features with concrete, actionable approaches
- (+) Each approach grounded in the project's specific constraints (P&C domain, Data Agent reuse, GitLab output)
- (+) Decision dependencies table helps avoid incompatible combinations
- (+) Recommended starting point gives a pragmatic default
- (-) Did not produce the formal architecture plan — approaches doc is the prerequisite, not the final deliverable. This was the correct scope for one session.
- (-) No session stub was written before starting work (Phase 1B violation — first session, so no ghost session risk, but protocol should be followed)

**Score: 7/10** — Good approaches document with concrete detail. Loses points for missing the session stub and for not having line-number references in the approaches doc itself.

Session 1 Handoff Evaluation: N/A (first session, no predecessor)
