# Plan: Migrate the Website Agent repo adapters from LGPL SDKs to direct `httpx`

**Status:** DRAFT plan (deliverable of a planning session). Not yet approved for
implementation. Implementation is a *separate* session per phase.

**Author context:** Written after a verified research pass (license landscape +
actual dependency licenses + exact code surface). All "files to change" below
come from `grep`, not from memory (per the planning protocol's evidence
requirement).

---

## 1. Goal & motivation

Remove the **two LGPL‑3.0 dependencies** from the project by reimplementing the
Website Agent's two repository‑host adapters against **`httpx`** (BSD‑3‑Clause),
which is **already in the tree** (transitive via the Anthropic SDK, resolved at
`0.28.1`).

| Package | Current license | Role | Replacement |
|---|---|---|---|
| `python-gitlab` (8.x) | **LGPL‑3.0‑or‑later** | GitLab adapter | direct `httpx` |
| `PyGithub` (2.x) | **LGPL** (LGPLv3) | GitHub adapter | direct `httpx` |

**Why direct `httpx` and not a permissive SDK** (verified 2026‑07‑17):
- **GitLab:** there is *no* actively‑maintained, permissively‑licensed full SDK
  comparable to `python-gitlab`. The needed surface is **4 REST calls** — a
  direct `httpx` rewrite is ~60–80 lines and adds **zero** new dependencies.
- **GitHub:** permissive SDKs exist (`githubkit` = MIT, `github3.py` = BSD‑3,
  `ghapi` = Apache‑2.0), but the needed surface is the standard git‑database
  "dance" (~9 REST calls) that you orchestrate the same way with or without an
  SDK. Direct `httpx` is ~150 lines and adds **zero** new dependencies. Choosing
  `httpx` for *both* keeps one HTTP style across the codebase.

### 1.1 Honest scope of the licensing win (set expectations)

This migration removes **all copyleft SDK dependencies (the two LGPLs)**. It does
**not** make the tree "fully MIT," and **no achievable state is "fully MIT":**

- After the swap the direct + transitive tree is **permissive** (MIT / BSD‑3 /
  Apache‑2.0 / PSF‑2.0 / ISC) **plus `certifi` (MPL‑2.0)**.
- `certifi` is the Mozilla CA bundle and is a **hard dependency of `httpx`**
  (and of `requests`); it is present regardless of library choice. MPL‑2.0 is
  weak, file‑level copyleft; consumed unmodified it imposes only "keep the
  notice," which packaging already satisfies. `truststore` (MIT) can switch TLS
  verification to the OS trust store but does **not** remove `certifi` from the
  graph — **not worth engineering around.**

**Accurate post‑migration claim:** *"MIT‑licensed project with a permissive
dependency tree (no copyleft SDKs; the only weak‑copyleft component is the
unavoidable `certifi` CA bundle, MPL‑2.0)."* This directly enables the
license‑compliance CI gate / badge discussed in the licensing advisory
(cross‑reference: the `licensecheck` recommendation) — configure its allow‑list
for permissive + MPL, and it goes green.

---

## 2. Evidence‑based inventory (grepped 2026‑07‑17)

### 2.1 MUST change — production source (the LGPL import sites)

| File | LGPL reference | Action |
|---|---|---|
| `src/model_project_constructor/agents/website/gitlab_adapter.py` (174 ln) | `import gitlab`; `from gitlab.exceptions import GitlabCreateError, GitlabError, GitlabGetError` | Rewrite body against `httpx`; keep the `RepoClient` contract |
| `src/model_project_constructor/agents/website/github_adapter.py` (185 ln) | `from github import Auth, Github, GithubException, InputGitTreeElement, UnknownObjectException` | Rewrite body against `httpx` |

Both are **the only two production files that import the LGPL packages** (grep
confirmed). Everything else references only the *adapter class names*.

### 2.2 Wiring / exports (reference class names — touch only if renaming, DP1)

| File | Reference | Action |
|---|---|---|
| `src/model_project_constructor/agents/website/__init__.py:20‑21, 66‑67` | imports + `__all__` of `PyGithubAdapter`, `PythonGitLabAdapter` | No change unless renaming (DP1) |
| `src/model_project_constructor/orchestrator/config.py:59‑84` | `_make_gitlab_adapter` / `_make_github_adapter` lazy‑import the classes; docstrings say "pulls `python-gitlab` / `PyGithub`" (lines 50‑51, 63, 76) | Update the SDK‑name comments; rename call only if DP1 |

The CLI (`cli.py`) and `scripts/run_pipeline.py` construct adapters **only through
the `REPO_PLATFORMS` factory** in `config.py` — no direct construction elsewhere
(grep for `PythonGitLabAdapter(|PyGithubAdapter(` returns only the class defs, the
`__init__` re‑exports, and the two factory bodies).

### 2.3 MUST change — tests (mock the SDKs / import SDK exceptions)

| File | What it does today | Action |
|---|---|---|
| `tests/agents/website/test_gitlab_adapter.py` (172 ln) | imports `PythonGitLabAdapter` + `_is_name_conflict`; stubs `adapter._gl = MagicMock()`; imports `gitlab.exceptions.*` inside 3 tests | Rewrite to drive `httpx` via `httpx.MockTransport` (DP4); re‑target `_is_name_conflict` tests at the new signature |
| `tests/agents/website/test_github_adapter.py` (330 ln) | imports `PyGithubAdapter` + `_is_name_conflict`; imports `github.GithubException/UnknownObjectException`; `MagicMock` git‑dance + per‑failure‑point translation | Rewrite against `httpx.MockTransport`; preserve the per‑call failure‑point coverage |
| `tests/agents/website/test_cli.py:211, 240, 276, 310, 351` | monkeypatches adapters by dotted string (`...gitlab_adapter.PythonGitLabAdapter`, `...github_adapter.PyGithubAdapter`) | **No change if class names + module paths kept.** Update the 4 patch strings + helper docstring only if renaming (DP1) |

No other test references the classes (grep of `tests/` for the class names returns
only these three files). `tests/scripts/test_run_pipeline_adapter.py` does **not**
currently reference the class names.

### 2.4 Packaging

| File | Action |
|---|---|
| `pyproject.toml:23‑24` (`agents` extra) | Remove `python-gitlab>=4` and `PyGithub>=2,<3`; **add** `httpx>=0.27,<1` as a direct dep (we now import it directly) |
| `uv.lock` | Regenerate with `uv lock`; prunes `python-gitlab`, `PyGithub` + their now‑unique transitive deps (`requests`, `requests-toolbelt`, `PyJWT`, `PyNaCl`, `Deprecated`, `wrapt`, and `cryptography`/`urllib3` **if unshared** — confirm with `uv tree`). `certifi` stays (httpx needs it). |

### 2.5 Docs — current‑state prose to update (NOT history)

Split by "describes current architecture" (update) vs "historical record" (leave).

**Update (current‑state):**
- `README.md:74‑75` ("adapter via python-gitlab" / "via PyGithub"), `:182` / `:191`
  ("creates … via python-gitlab/PyGithub" comments).
- `src/model_project_constructor/agents/website/protocol.py:6‑7` (docstring: "thin
  wrapper around `python-gitlab` or `PyGithub`").
- Wiki (auto‑published — see §6 dragon): `docs/wiki/claims-model-starter/`
  - `Software-Bill-of-Materials.md:34‑35, 85, 89‑91, 187, 202‑203` (drops
    `python-gitlab`, `PyGithub`, `requests`, `pynacl`, `pyjwt`; add `httpx`).
  - `Security-Considerations.md:124‑128, 314‑315` (GitHub adapter now `httpx`;
    the `PyGithub … LGPL‑3.0` SBOM row goes away).
  - `Agent-Reference.md:239‑240` (backing‑lib column → `httpx`).
  - `Contributing.md:32, 183, 226` (extras list; "tested via MagicMock at the
    `python-gitlab`/`PyGithub` boundary" → httpx MockTransport; the LGPL‑compliance
    paragraph becomes obsolete — **remove**).
  - `Extending-the-Pipeline.md:126, 133`, `Schema-Reference.md:480`,
    `Architecture-Decisions.md:31` (class‑name mentions — only if renaming, DP1;
    otherwise the surrounding prose is still accurate).
  - `Content-Recommendations.md:75` (the "`PyGithub` uses LGPL‑3.0" note is now
    obsolete — remove/adjust).
- `CHANGELOG.md` — **add** an `[Unreleased]` entry (do not edit historical rows).

**Leave (historical record — do NOT edit):**
- `CHANGELOG.md` existing entries, `SESSION_NOTES.md`, `docs/architecture-history/`,
  and the *historical* wiki pages `Changelog.md:32,111`, `Evolution.md:137,283`.
- `docs/audits/2026-06-10-*.md:351` (a dated audit snapshot — historical).

---

## 3. Decision points (resolve at plan approval)

- **DP1 — Rename the adapter classes?** `PyGithubAdapter` / `PythonGitLabAdapter`
  literally name the LGPL libraries; after the swap they are misnomers. The module
  filenames (`github_adapter.py` / `gitlab_adapter.py`) are already host‑neutral
  and stay. **Recommendation: KEEP the class names during the swap (Phases 1–2)**
  to keep each swap a pure, low‑risk implementation change, then do a **pure,
  fully‑greppable rename as optional Phase 3** (`GitLabAdapter` / `GitHubAdapter`).
  Renaming touches `__init__.py`, `config.py`, `test_cli.py` (4 patch strings), the
  two adapter test files, and ~5 wiki pages — all mechanical.
- **DP2 — Sync `httpx.Client` (not async).** Non‑negotiable: `RepoClient`'s methods
  are sync and the LangGraph nodes call them synchronously. Use `httpx.Client`.
- **DP3 — Add `httpx` as a direct `agents` dependency** with `httpx>=0.27,<1`
  (already resolved to 0.28.1). Depend directly on what we import.
- **DP4 — Test double = `httpx.MockTransport`** (built into httpx, **no new dep**).
  It lets tests assert exact requests (method/URL/headers/body) and return canned
  responses/errors — strictly better wire‑level coverage than today's SDK
  `MagicMock`. (Alternative `respx` adds a dev dep — not recommended.)

---

## 4. Target design (applies to both adapters)

- Construct one `httpx.Client` on the adapter instance: `base_url`, default auth
  headers, `verify=ssl_verify` (GitLab already exposes `ssl_verify`; keep it —
  GitHub can default `verify=True`). Reuse it across calls.
- **Wrap every failure** so nothing raw escapes: any non‑2xx or
  `httpx.HTTPError`/`httpx.RequestError` → `RepoClientError`; a create‑project
  "already exists" → `RepoNameConflictError`. This preserves identical semantics
  for the nodes' `RETRY_BACKOFF` loop across both hosts (the current contract).
- Keep the `_is_name_conflict(...)` helper but **re‑signature it** to inspect
  `(status_code, parsed_json_body)` (or the `httpx.Response`) instead of an SDK
  exception. Keep the loose matching ("already been taken" / "already exists").

**GitLab (`/api/v4`, header `PRIVATE-TOKEN: <token>`):**
1. `GET /groups/{url‑encoded namespace}` → `group.id`
2. `POST /projects` `{name, path, namespace_id, visibility}` → `id`, `web_url`, `default_branch`
3. `GET /projects/{id}`
4. `POST /projects/{id}/repository/commits` `{branch, commit_message, actions:[{action:"create", file_path, content}]}` → `id` (one‑shot multi‑file commit)

**GitHub (base `https://api.github.com` or GHE `.../api/v3`, headers
`Authorization: Bearer <token>`, `Accept: application/vnd.github+json`):**
1. Resolve owner: `GET /orgs/{ns}` (200 ⇒ org) else treat as user. **Dragon (§6):**
   repo creation is `POST /orgs/{org}/repos` for an org, or `POST /user/repos`
   for the **authenticated user only** (not an arbitrary third‑party user) —
   preserve the existing "org first, else user" behavior and the nested‑namespace
   (`"a/b"`) guard.
2. Create repo (`{name, private}`) → `full_name`, `html_url`, `default_branch`.
3. `GET /repos/{owner}/{repo}`.
4. Atomic multi‑file commit (git database): `GET /repos/{o}/{r}/git/ref/heads/{branch}`
   → `GET …/git/commits/{sha}` → `POST …/git/blobs` ×N → `POST …/git/trees`
   (`base_tree`) → `POST …/git/commits` → `PATCH …/git/refs/heads/{branch}`.
   Each step is a failure point that must map to `RepoClientError`.

---

## 5. Phased plan (each phase = ONE session; close out after each)

> **Prerequisite (branching):** this migration is unrelated to the current
> `feat/bedrock-mantle-migration` branch (which carries uncommitted Session‑179
> mantle WIP). Do the httpx work on a **dedicated branch off a clean `master`**
> (e.g. `feat/httpx-adapters`). Do **not** commingle it with the bedrock WIP, and
> do **not** touch that WIP. Resolve the branch decision before Phase 1.

### Phase 1 — GitLab adapter → `httpx`
**Scope:** `gitlab_adapter.py` rewrite + `test_gitlab_adapter.py` rewrite + drop
`python-gitlab` + add `httpx` dep + GitLab‑specific docs.
**Steps:** rewrite the 4‑call body per §4; re‑signature `_is_name_conflict`;
rewrite the 9 tests with `httpx.MockTransport`; edit `pyproject.toml` (remove
`python-gitlab`, add `httpx`); `uv lock`; update `README.md:74,182`, protocol
docstring (GitLab clause), SBOM/Contributing GitLab rows.
**DONE looks like:** GitLab adapter contains no `import gitlab`; `python-gitlab`
gone from `pyproject.toml` + `uv.lock`; suite green; coverage ≥95%.
**Verify:**
```
grep -rn "import gitlab" src/ tests/            # → 0
grep -rn "python-gitlab" pyproject.toml uv.lock # → 0
uv run pytest -q tests/agents/website/test_gitlab_adapter.py tests/agents/website/test_cli.py
uv run pytest -q && uv run ruff check src/ tests/ && uv run mypy
uv tree | grep -i gitlab                        # → 0
```
**Boundary:** one session. Close out. GitHub still on PyGithub — that's a valid
intermediate state (the two libs are independent).

### Phase 2 — GitHub adapter → `httpx`
**Scope:** `github_adapter.py` rewrite + `test_github_adapter.py` rewrite + drop
`PyGithub` + GitHub‑specific docs. Mirrors Phase 1.
**Steps:** rewrite the git‑database dance per §4 (mind the org‑vs‑user create +
nested‑namespace guard); rewrite tests with `MockTransport` preserving each
failure point; remove `PyGithub` from `pyproject.toml`; `uv lock`; update
`README.md:75,191`, protocol docstring (GitHub clause), SBOM/Security/Agent‑Ref
GitHub rows; remove the now‑obsolete LGPL‑compliance notes
(`Contributing.md:226`, `Content-Recommendations.md:75`, `Security-Considerations.md:315`).
**DONE looks like:** no `from github import …`; `PyGithub` gone from
`pyproject.toml` + `uv.lock`; suite green; coverage ≥95%.
**Verify:**
```
grep -rn "from github import\|import github" src/ tests/  # → 0
grep -rn -i "pygithub" pyproject.toml uv.lock             # → 0
uv run pytest -q && uv run ruff check src/ tests/ && uv run mypy
uv tree | grep -iE "pygithub|pynacl|pyjwt|requests-toolbelt"  # → 0 (unless shared)
```
**Boundary:** one session. Close out. At end of Phase 2 **both LGPLs are gone.**

### Phase 3 — (optional) rename classes + final SBOM/CHANGELOG sweep
**Only if DP1 = rename.** Pure mechanical rename `PythonGitLabAdapter → GitLabAdapter`,
`PyGithubAdapter → GitHubAdapter` across `__init__.py`, `config.py`, `test_cli.py`
(4 patch strings + docstring), the two adapter test files, and the wiki
class‑name mentions (`Extending-the-Pipeline.md`, `Schema-Reference.md`,
`Architecture-Decisions.md`, `Agent-Reference.md`). Finalize the `CHANGELOG.md`
`[Unreleased]` entry and reconcile the SBOM version table.
**Verify:** `grep -rn "PyGithubAdapter\|PythonGitLabAdapter" src/ tests/ docs/wiki` → 0;
suite green.
**Boundary:** one session. If DP1 = keep names, fold the CHANGELOG/SBOM finalize
into Phase 2 and skip Phase 3.

---

## 6. Here be dragons

1. **GitHub org‑vs‑user repo creation.** `POST /user/repos` creates under the
   **token's own account only** — you cannot create under an arbitrary third‑party
   user. The current PyGithub path (`get_user(ns).create_repo`) already behaves
   this way; the httpx rewrite must reproduce "org → `/orgs/{org}/repos`, else
   authenticated user → `/user/repos`," keep the nested‑namespace guard, and not
   silently create in the wrong place.
2. **Name‑conflict detection moves from SDK exceptions to HTTP responses.** GitHub
   returns **422** with `{"errors":[{"message":"name already exists…"}]}`; GitLab
   returns **400/409** with `{"name":["has already been taken"]}`. Re‑implement the
   loose match on the parsed body; the existing tests pin these shapes.
3. **The GitHub commit is 6 sequential calls, each a failure point.** Today's test
   asserts blob/tree/commit/ref each map to `RepoClientError`. Preserve that — a
   `MockTransport` router keyed by `(method, path)` makes this clean.
4. **Semantics parity for `RETRY_BACKOFF`.** Both adapters must keep "one commit
   per call" and raise only `RepoClientError`/`RepoNameConflictError` — never let a
   raw `httpx` exception escape, or the LangGraph retry loop sees different behavior
   per host.
5. **Wiki auto‑publish.** Editing any `docs/wiki/claims-model-starter/*` file fires
   the tracked `.githooks/post-commit` hook → `scripts/publish_wiki.sh` syncs the
   **live GitHub Wiki** on commit. Expect the push; it's idempotent. (Suppress for a
   single commit with `MPC_SKIP_WIKI_PUBLISH=1` only if deliberately staging.)
6. **`uv lock` prune is the real license win — verify it.** Removing a line from
   `pyproject.toml` is not enough; run `uv lock` and confirm with `uv tree` that
   `python-gitlab`/`PyGithub` **and their unique transitive deps** are actually
   gone. `cryptography`/`urllib3` may be shared — don't assume they prune.
7. **Coverage gate is `--cov-fail-under=95`.** The rewrites must keep coverage; the
   `MockTransport` tests should exercise every error branch and the full git dance.
8. **Not "fully MIT" after this (see §1.1).** Don't let the CHANGELOG/README claim
   "MIT‑only deps" — the accurate claim is "permissive + `certifi` (MPL‑2.0)."

---

## 7. Out of scope / explicit non‑goals

- **The Session‑179 bedrock‑mantle WIP** on `feat/bedrock-mantle-migration` — do
  not touch; this migration lives on its own branch.
- **`certifi` / MPL‑2.0** — unavoidable; not addressed (see §1.1).
- **The license‑compliance CI gate + badges** (`licensecheck`, shields.io, FOSSA)
  and **the static‑analysis stack** (CodeQL / Sonar / Scorecard) — separate
  follow‑ups from the licensing/audit advisory; this plan only removes the LGPL
  deps so those can then certify a permissive tree.
- **Live GitLab/GitHub integration tests** — still a Phase‑5/credentials concern;
  this plan keeps the "unit‑tested against mocks only" posture (now mocking the
  wire instead of the SDK).

---

## 8. Final done‑greps (all must return 0 after Phase 2)

```
grep -rn -E "import gitlab|from gitlab|from github import|import github" src/ tests/
grep -rn -iE "python-gitlab|pygithub" pyproject.toml uv.lock
uv tree | grep -iE "python-gitlab|pygithub"
```
Plus: full `uv run pytest -q` green at coverage ≥95%, `uv run ruff check src/ tests/`
clean, `uv run mypy` clean.
