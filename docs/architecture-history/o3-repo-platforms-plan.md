> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/model_project_constructor/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# O3 — `REPO_PLATFORMS` Registry: Host-Vocabulary Consolidation Plan

> **Status:** Draft for executor review (Session 115, planning/architecture workstream). The plan is the deliverable; implementation is separate sessions.
> **Author:** Session 115 — 2026-06-05.
> **Implements:** Audit `docs/audits/2026-06-01-technical-debt-audit.md` — E1 (`:115-119`), Overhaul **O3** (`:174`), quick-win **#5** (`:160`, = audit item **#8**); table rows #8/#9/#12/#35/#6 (`:232`).
> **Predecessor / first step:** quick-win #5 (audit #8) — the single host `Literal` + allow-list source — is **not yet landed**; it becomes **Phase O3-1** of this plan. O1 (Stage-list driver) is the audit's pattern-establishing precedent (`:177` sequencing note) but is **not** a prerequisite.
> **Decision (Session 115, three-lens panel + adversarial verify unanimous):** **Option B — one `REPO_PLATFORMS` host registry**, with #8 absorbed as Phase O3-1. The **CI-platform** vocabulary is a *separate* controlled vocabulary and stays **out of O3** (it is the audit's C4/E2 / #6/#42).
> **Out of scope (say it twice):** the CI-platform file-selection renderer (`governance_templates.py:809,834-837,949-953`, `VALID_CI_PLATFORMS`, the `ci_platform` plumbing) — folded into **C4/E2 (#6/#42)**, **NOT O3**. See §11.

---

## 1. Context

### 1.1 What O3 is

Audit E1 (`docs/audits/2026-06-01-technical-debt-audit.md:115-119`):

> *The codebase abstracts behavior well (Protocols for repo hosts and LLM clients are clean) but abstracts selection and vocabulary poorly… Adding a host is a ~6-file, ~12-branch shotgun edit.*
> **Recommendation (O3):** one `REPO_PLATFORMS: dict[str, PlatformSpec]` registry (default API URL, token env var, adapter factory). Replace each `if host=='gitlab'/else github` with a dict lookup; derive the single `Literal`/allow-list from `REPO_PLATFORMS.keys()`. Adapters already conform to `RepoClient`, so a new platform becomes **one registry entry + one adapter module**.

O3 collapses the **host vocabulary** — the controlled set `{gitlab, github}` that selects *which `RepoClient` adapter to build, which default API URL to use, and which token env var to read* — from its current **4 independent membership declarations + ~8 `if host==…` branches across 3 files** down to one registry whose `.keys()` are the single source of truth.

### 1.2 Why this is an architecture decision, not a quick win

The behavioral seam is already clean: `RepoClient` is a `typing.Protocol` (`agents/website/protocol.py:42-66`, exactly `create_project` + `commit_files`), and both production adapters subclass it (`gitlab_adapter.py:41`, `github_adapter.py:48`). What is *not* abstracted is **selection + vocabulary**: the host string is re-validated, re-mapped to a URL, re-mapped to a token var, and re-branched into an adapter constructor in five different places, each an independent copy. Two consequences make this more than cosmetic:

1. **A silent `else: # github` fall-through.** `cli.py:180`, `run_pipeline.py:285` (`if host=="github": … else:` → GitLab), and the duplicated token ternaries all treat *any unrecognized host* as the `else` branch rather than failing closed. mypy catches a bad `Literal`, but not a runtime host string that slips past validation. A registry lookup (`REPO_PLATFORMS[host]`) replaces the fall-through with a loud `KeyError`.
2. **Two must-agree copies that can silently diverge.** The host→token-env mapping is written *twice* (`config.py:103` reads the token; `config.py:140` names it in the error message). Nothing ties them together; a future edit to one is a latent bug.

These are correctness hazards, not just DRY violations — which is why the audit classes O3 as an *overhaul*, not a quick win.

### 1.3 The reframe — there are **two** controlled vocabularies, not one

**This is the load-bearing finding of this plan.** The string `Literal["gitlab", "github"]` appears in the codebase under **two different meanings** that happen to share identical membership today:

| Vocabulary | Means | Selects | Carrier |
|---|---|---|---|
| **HOST** | *where the repo lives* | `RepoClient` adapter, default API URL, token env var | `HostLiteral` (`config.py:29`), `VALID_HOSTS` (`cli.py:42`) |
| **CI-PLATFORM** | *which CI manifest the website agent emits* | `.gitlab-ci.yml` vs `.github/workflows/ci.yml` | `CIPlatform` (`governance_templates.py:32`), `VALID_CI_PLATFORMS` (`cli.py:43`) |

They are **separable, not identical**, and the codebase already treats them so:

- **Two distinct allow-lists** sit on adjacent lines: `VALID_HOSTS` (`cli.py:42`) and `VALID_CI_PLATFORMS` (`cli.py:43`). Someone wrote *two* frozensets, not one.
- **CI defaults to host but is independently overridable.** `cli.py:135-136` is `if ci_platform is None: ci_platform = host` — a *default*, not an identity. `--ci-platform` (`cli.py:107-116`, documented at `cli.py:14`) lets them diverge: `--host gitlab --ci-platform github` is a valid, supported combination (GitLab adapter + GitHub Actions CI).
- **It is test-pinned.** `test_cli_ci_platform_overrides_host` (`tests/agents/website/test_cli.py:134`, asserts at `:158-159`) checks that `--host gitlab --fake --ci-platform github` emits `.github/workflows/ci.yml` and **not** `.gitlab-ci.yml`. The `state.py:27-30` comment block makes the separability load-bearing for testing ("a GitHub project can be scaffolded with a `FakeRepoClient`").
- **Disjoint consumers.** Host drives adapter/URL/token (`cli.py:153-190`, `config.py:98/103/140`); `ci_platform` drives *only* the renderer branch (`governance_templates.py:834-837`) and never touches adapter/URL/token.

**The decisive thought experiment (the roadmap's "3rd repo platform"):** adding **Azure DevOps** as a *host* means one adapter + `api.dev.azure.com` + `AZURE_DEVOPS_TOKEN` (one `REPO_PLATFORMS` row). But its CI is **Azure Pipelines** (`azure-pipelines.yml`) — a *different* renderer member, not implied by the host. The 1:1 `host==ci` coincidence that holds for `{gitlab, github}` **breaks at the third platform**. The `PlatformSpec` O3 builds (URL + token + adapter factory) has **no slot for a CI renderer** — folding CI in would be a category error.

**Scope consequence:** O3 unifies the **HOST** vocabulary only. The **CI-PLATFORM** vocabulary (#6/#42) is the audit's C4/E2 overhaul and is explicitly excluded here (§11). The audit's own split of O3 (host) from C4/E2 (CI renderer) is structurally correct; one internal audit-wording tension (`:174` says O3 "Touches … governance CI renderers") is resolved in §11.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **Host vocabulary** | The controlled set of repo-host tokens (`gitlab`, `github`) selecting adapter + default API URL + token env var. O3's subject. |
| **CI-platform vocabulary** | The controlled set selecting which CI manifest is emitted. **Out of O3** (C4/E2). |
| **`REPO_PLATFORMS`** | The new registry: `dict[str, PlatformSpec]` keyed by host token. Its `.keys()` are the single source of host membership. |
| **`PlatformSpec`** | A frozen dataclass: `default_api_url`, `token_env_var`, and (Phase O3-3) `adapter_factory`. |
| **adapter factory** | A module-level function with a uniform `(*, host_url, private_token) -> RepoClient` signature that lazy-imports its SDK adapter inside the body. |
| **`RepoClient`** | The `typing.Protocol` (`protocol.py:42-66`) both adapters already implement. **Unchanged by O3.** |
| **allow-list** | A runtime membership check (`VALID_HOSTS` frozenset, the inline `("gitlab","github")` tuple, argparse `choices`). O3 derives all from `REPO_PLATFORMS`. |
| **`HostLiteral`** | The static type `Literal["gitlab","github"]` (`config.py:29`). Stays hand-written (mypy can't read a runtime-derived `Literal`); pinned to `REPO_PLATFORMS` by an import-time drift guard. |
| **drift guard** | An import-time `raise`-based parity check (the existing `_assert_vocab_parity`, governance_templates.py:35) asserting the hand-written `Literal` matches the registry keys. |
| **SDK-free** | A module whose import pulls neither `python-gitlab` (`import gitlab`) nor `PyGithub` (`import github`). `orchestrator/config.py` is SDK-free; everything under `agents.website` is not (§6.4). |

---

## 3. Evidence Inventory (grep-based — MANDATORY for a refactor plan)

All counts below were produced by **direct `grep` against the working tree at HEAD `9cf9f74`** (Session 115), then cross-checked against a research workflow (§12). **The executor MUST re-run these in their Phase 0** — symbols drift (Learnings #19/#28). The exact re-run block is §13. One **per-pattern surface** per subsection (Learning #8: TYPE, allow-list, branch, and literal-filename are different greps — never one conflated total).

> **Path correction (provenance hygiene).** The 2026-06-01 audit cites repo-root paths (`cli.py:42`, `run_pipeline.py:113`). The website CLI actually lives at **`src/model_project_constructor/agents/website/cli.py`** — there is **no top-level `cli.py`**. `orchestrator/config.py` and `scripts/run_pipeline.py` line numbers are current; the website-CLI *path* is the drift. All sites below use verified `src/…`/`scripts/…` paths. Do **not** "correct" them back to the audit's roots.

### 3.1 Host membership declarations — **4 independent copies, none derived** (3 files)

`grep -rnE 'HostLiteral *= *Literal|not in \("gitlab", "github"\)|VALID_HOSTS *: *frozenset|choices=\["gitlab", "github"\]' src/ scripts/` (4 rows; a bare `VALID_HOSTS` over-matches its two consumers at `cli.py:128,130`)

| Copy | Site | Form |
|---|---|---|
| Canonical `Literal` | `orchestrator/config.py:29` | `HostLiteral = Literal["gitlab", "github"]` |
| Inline tuple | `orchestrator/config.py:92` | `if host_raw not in ("gitlab", "github"):` |
| Frozenset | `agents/website/cli.py:42` | `VALID_HOSTS: frozenset[str] = frozenset({"gitlab", "github"})` |
| argparse choices | `scripts/run_pipeline.py:416` | `choices=["gitlab", "github"]` |

**4 host-membership declarations.** (`cli.py:43 VALID_CI_PLATFORMS` is the *CI* vocabulary — §3.5, do not touch.)

### 3.2 Default API URL copies — **4 named constants (two naming schemes) + 4 inline literals** (3 files)

| Copy | Site | Form |
|---|---|---|
| `DEFAULT_GITLAB_URL` / `DEFAULT_GITHUB_URL` | `config.py:33-34` | `"https://gitlab.com"` / `"https://api.github.com"` |
| `GITLAB_DEFAULT_HOST_URL` / `GITHUB_DEFAULT_HOST_URL` | `cli.py:39-40` | same two values, **different constant names** |
| inline literals (build_repo_target) | `run_pipeline.py:114,117` | `os.environ.get("MPC_HOST_URL", "https://…")` |
| inline literals (build_website_runner) | `run_pipeline.py:289,295` | `os.environ.get("MPC_HOST_URL", "https://…")` |

Consumption branches: `config.py:98`, `cli.py:154`. **8 URL literal occurrences for 2 distinct URLs.**

### 3.3 Host→token-env mapping — **2 must-agree copies** (1 file)

| Copy | Site | Purpose |
|---|---|---|
| reads the token | `config.py:103` | `token_var = "GITLAB_TOKEN" if host == "gitlab" else "GITHUB_TOKEN"` |
| names it in the error | `config.py:140` | `var = "GITLAB_TOKEN" if self.host == "gitlab" else "GITHUB_TOKEN"` |

**2 ternaries that must agree but are not linked.**

### 3.4 Host selection branches & adapter constructions

`if host==…/else` host branches (3 files): `config.py:96` (narrowing ternary), `config.py:98` (URL), `config.py:103` + `:140` (token), `cli.py:154` (URL), `cli.py:169` (`elif host=="gitlab"`), `cli.py:180` (`else:  # github`), `run_pipeline.py:113` (URL+namespace), `run_pipeline.py:285` (adapter). **~8-9 host branches.**

Real adapter constructions (2 files, excluding the two docstring examples at `gitlab_adapter.py:49` / `github_adapter.py:56`): `cli.py:177` (`PythonGitLabAdapter`), `cli.py:188` (`PyGithubAdapter`), `run_pipeline.py:290` (`PyGithubAdapter`), `run_pipeline.py:296` (`PythonGitLabAdapter`). **4 real adapter constructions across 2 files** — the two arms of two if/else branches.

**Silent `else` fall-throughs (the correctness target):** `cli.py:180` (→ github), `run_pipeline.py:285`'s `else` (→ gitlab). Both vanish under `REPO_PLATFORMS[host]` (KeyError on unknown).

### 3.5 CI-platform sites — **OUT of O3 scope; inventoried only to prove O3 leaves them untouched**

`grep -rnE 'CIPlatform|ci_platform|VALID_CI_PLATFORMS' src/ scripts/` → **27 sites**: `governance_templates.py` (`:32,809,834-837,949-953`, 4), `cli.py` (`:43,107-116,135-143,192-193`, 9), `state.py` (`:31,76,82`, 3), `agent.py` (`:38,41,76`, 3), `nodes.py:147` (1), `run_pipeline.py` (`:274,278,298`, 3 — the host-derived `ci_platform` passed to `WebsiteAgent`), `github_adapter.py:60` (1, docstring), plus **3 docstring/prose mentions** in `orchestrator/__init__.py:14` and `pipeline.py:181,236`. **None of these may be edited by O3.** They are the audit's C4/E2 (#6/#42).

### 3.6 Test blast radius (gates every phase — re-run as written, mind §10's coverage trap)

| Test | Pins | Implication |
|---|---|---|
| `tests/orchestrator/test_config.py:15-16` | imports `DEFAULT_GITLAB_URL`/`DEFAULT_GITHUB_URL` **by name** | Phase O3-2 must keep those `__all__` exports as **live aliases**, not drop them. |
| `test_config.py:~105` | `MPC_HOST=bitbucket` raises `ConfigError` matching `"MPC_HOST"` | registry-generated error string MUST still contain substring `MPC_HOST`. |
| `test_config.py:~138` | token error matches `"GITHUB_TOKEN"` | collapsing `config.py:140` must keep the token-var **value** in the message. |
| `test_config.py:~55` | case-insensitive `GitHub` normalization | `.strip().lower()` at `config.py:91` must survive. |
| `tests/scripts/test_run_pipeline_adapter.py:175-222` | Session-30 regression: `token=`/`private_token=` kwargs **and** `MPC_HOST_URL` override flows to GHE | Phase O3-3 factory must keep these green; **compute `host_url` before calling the factory** (§6.3). |
| `test_cli_ci_platform_overrides_host` (`test_cli.py:134`, asserts `:158-159`) | host↔ci **divergence** (`--host gitlab --ci-platform github`) | the executable proof the two vocabularies are separable — must not break. |
| `test_cli.py:~251-368` | per-host `host_url` defaulting + `--host-url` override (GHE, self-hosted GitLab) | monkeypatched adapter-selection tests gate Phase O3-3. |

---

## 4. Decision

**Adopt Option B — a single `REPO_PLATFORMS: dict[str, PlatformSpec]` host registry, with audit quick-win #5 (#8) absorbed as Phase O3-1. The CI-platform vocabulary stays separate (C4/E2).** Unanimous across a three-lens design panel (minimalist/YAGNI, extensibility, testability) and an adversarial completeness critic (§12).

Rationale:

1. **It targets the actual harm, not just LoC.** The win is eliminating the silent `else: # github` fall-through (§3.4) and the two must-agree token ternaries (§3.3) — correctness hazards — not merely deduping the allow-list.
2. **The single source of truth becomes real, not advisory.** `VALID_HOSTS`, the inline tuple, and the argparse `choices` all derive from `REPO_PLATFORMS`; `HostLiteral` is pinned to the keys by an import-time `raise` guard (reusing the existing `_assert_vocab_parity` pattern, §6.2). Drift fails the build, not production.
3. **A 3rd host becomes one registry entry + one adapter module.** Adapters already conform to `RepoClient` (unchanged); the uniform adapter-factory signature (§6.3) makes the Session-30 kwarg-mismatch bug class structurally unreachable.
4. **It is a deep module (Tulip/Ousterhout heuristic, `ARCHITECTURE_WORKSTREAM.md:191-212`).** A tiny interface (`REPO_PLATFORMS[host]`) hides the selection complexity that is currently smeared across three files. The *deletion test* (`:204-212`): the ~8 host branches do not move elsewhere — they are deleted into one lookup.
5. **It explicitly preserves the HOST/CI separation** rather than collapsing two genuinely-separable vocabularies (§1.3) — and bounds scope against the resume-driven / astronaut anti-patterns (`:226-227`): O3 builds the registry for the *two* hosts that exist today (the duplication that already bites), **not** a speculative 3rd adapter.

---

## 5. Alternatives Considered

| Option | What it does | Coupling / blast radius | Verdict |
|---|---|---|---|
| **B — host registry (+ #8 as Phase 1)** | one `REPO_PLATFORMS`; derive Literal/allow-list from keys; fold URL/token/adapter | medium, but pays for itself at N=2 hosts | **CHOSEN** |
| A — narrow #8 only | single-source just the `Literal` + allow-list (the ~30-min quick-win); defer the registry | small | **Rejected** — dedups only the 4 allow-list copies; leaves the ~6 URL copies, the 2 must-agree token ternaries, the 2 adapter branches, and the silent `else: # github` fall-through. Forces a second overhaul to clean what actually causes runtime bugs. Becomes Phase O3-1, not the whole job. |
| C — two registries now (host + CI renderer) | also build a `CI_RENDERERS` registry in this overhaul | large; doubles blast radius | **Rejected** — the CI renderer is a separable vocabulary (§1.3); its selection is a *single* branch (`governance_templates.py:834`) with no must-agree duplicate, so it has near-zero drift risk and fails YAGNI. It is the audit's C4/E2 (#6/#42); bundling violates "1 and done." |
| D — `StrEnum`/`Enum` instead of a dict registry | model hosts as an enum | medium | **Rejected** — an enum carries members but not the *per-member data* (URL, token var, factory). You'd still need a side-table mapping enum→spec, i.e. a dict. The dict registry *is* the data; an enum adds a layer without removing one. |
| E — do nothing | keep the if/else fan-out | none now; ~6-file shotgun edit when a 3rd host lands | **Rejected** — but note the audit's own framing: "*none of the overhauls are urgent*." This plan is right-sized, not urgent; each phase is independently shippable so a partial landing is a strict improvement. |

**Re-open trigger:** a concrete request for a **3rd repo host** (Bitbucket/Gitea/Azure DevOps) re-opens the new-adapter-module question (and, separately, the Azure-Pipelines CI renderer in C4/E2). Until then, the registry serves the two hosts that exist.

---

## 6. Interface / Target Design

### 6.1 `PlatformSpec` and `REPO_PLATFORMS`

```python
# Final shape after Phase O3-3 (grown across phases — see §7).
from collections.abc import Callable
from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformSpec:
    default_api_url: str                       # Phase O3-1 (data)
    token_env_var: str                         # Phase O3-1 (data)
    adapter_factory: Callable[..., "RepoClient"]  # added in Phase O3-3

REPO_PLATFORMS: dict[str, PlatformSpec] = {
    "gitlab": PlatformSpec(
        default_api_url="https://gitlab.com",
        token_env_var="GITLAB_TOKEN",
        adapter_factory=_make_gitlab_adapter,   # Phase O3-3
    ),
    "github": PlatformSpec(
        default_api_url="https://api.github.com",
        token_env_var="GITHUB_TOKEN",
        adapter_factory=_make_github_adapter,    # Phase O3-3
    ),
}
```

The **dict key is the host token** — no separate `key` field. Derivations:

```python
SUPPORTED_HOSTS = frozenset(REPO_PLATFORMS)          # replaces VALID_HOSTS, the inline tuple, argparse choices
# host validation:  if host not in REPO_PLATFORMS:  raise/echo  (error string built from sorted(REPO_PLATFORMS))
HostLiteral = Literal["gitlab", "github"]            # stays hand-written; pinned by the guard below
```

### 6.2 The import-time drift guard (reuse, don't reinvent)

`HostLiteral` cannot be *derived* from `REPO_PLATFORMS.keys()` because a runtime-built `Literal` is invisible to mypy/pyright. Instead, pin them with the **existing** `raise`-based parity check — `_assert_vocab_parity(members, literal, *, name)` (`governance_templates.py:35-56`, a real `raise AssertionError`, so `python -O` keeps it live; precedent: Audit #2 / Session 113):

```python
_assert_vocab_parity(set(REPO_PLATFORMS), HostLiteral, name="REPO_PLATFORMS")
```

Today `_assert_vocab_parity` lives in `governance_templates.py`, which is **SDK-eager** (§6.4) — importing it into `config.py` would regress `config.py` from SDK-free to SDK-eager. **Extract it to a new dependency-free module** `src/model_project_constructor/_vocab_guard.py` (it needs only `typing.get_args`/`Any`); `config.py` imports it from there. **Parameterize the remediation hint when extracting:** the current body hardcodes *"Reconcile the dict with the Literal in schemas/v1/common.py"*, which is wrong for the host case (host vocabulary lives in `config.py`, not `schemas/v1/common.py`, and pins a hand-written `Literal` to *registry keys*, not a schema dict). Add a `*, reconcile_hint: str` argument (or drop the schema sentence and let callers supply it) so the host call emits an accurate message; assert in the guard test that the host failure text does **not** mention `schemas/v1/common.py`. The existing `governance_templates.py` callers keep the schema-specific hint (they *are* schema-backed) — the two messages legitimately differ. Leaving `governance_templates.py`'s local copy in place is fine for O3 (migrating it to the shared module is an **optional** follow-up — do not touch the CI module in O3). This makes O3's host guard the **first registry-keys-backed** parity check (the existing two are schema-`Literal`-backed).

### 6.3 Adapter factory — uniform signature, lazy import

`RepoClient` (`protocol.py:42-66`) is already uniform; the only divergence is the **constructor** (which a Protocol cannot constrain):

- GitLab: `__init__(*, host_url, private_token, ssl_verify=True)` (`gitlab_adapter.py:56-65`)
- GitHub: `__init__(*, private_token, host_url="https://api.github.com")` (`github_adapter.py:66-72`) — **different kwarg order**, **bakes a URL default**, **no `ssl_verify`**.

> **Verified (Learning #23):** both call sites already use `host_url=`/`private_token=` — the historic `url=`/`token=` *name* mismatches were call-site bugs fixed in Sessions 22 & 30. The residual asymmetry is order + GitHub's baked URL default + GitLab's `ssl_verify`.

Factories present **one** signature and absorb the asymmetry; each lazy-imports inside the body:

```python
def _make_gitlab_adapter(*, host_url: str, private_token: str) -> "RepoClient":
    from model_project_constructor.agents.website.gitlab_adapter import PythonGitLabAdapter
    return PythonGitLabAdapter(host_url=host_url, private_token=private_token)

def _make_github_adapter(*, host_url: str, private_token: str) -> "RepoClient":
    from model_project_constructor.agents.website.github_adapter import PyGithubAdapter
    return PyGithubAdapter(host_url=host_url, private_token=private_token)
```

Before → after at the call sites:

```diff
- if fake:
-     client = FakeRepoClient()
- elif host == "gitlab":
-     from ...gitlab_adapter import PythonGitLabAdapter
-     client = PythonGitLabAdapter(host_url=resolved_host_url, private_token=private_token)
- else:  # host == "github"
-     from ...github_adapter import PyGithubAdapter
-     client = PyGithubAdapter(host_url=resolved_host_url, private_token=private_token)
+ if fake:
+     client = FakeRepoClient()
+ else:
+     client = REPO_PLATFORMS[host].adapter_factory(
+         host_url=resolved_host_url, private_token=private_token
+     )
```

> **Session-30 invariant (regression-pinned at `test_run_pipeline_adapter.py:175-222`):** the factory takes `host_url` as a **param**; the `run_pipeline` call site must compute `host_url = os.environ.get("MPC_HOST_URL", REPO_PLATFORMS[host].default_api_url)` **before** calling the factory. If the factory baked the default, the `MPC_HOST_URL` override (GHE) would break. `ssl_verify` is intentionally dropped from the uniform signature (no caller passes it — documented YAGNI; escape hatch = optional per-spec construct-kwargs later).

### 6.4 Registry home — the SDK-free invariant (verified, corrects the research)

**Empirically verified at HEAD `9cf9f74`** (`.venv/bin/python`, `PYTHONPATH=src`):

| Importing… | Pulls `gitlab` + `github` SDKs? |
|---|---|
| `orchestrator.config` | **NO — SDK-free** ✅ |
| `agents.website` (`__init__`) | YES (eager re-export, `__init__.py:20-21`) |
| `agents.website.cli` | **YES** (runs the package `__init__` first) |
| `agents.website.governance_templates` | YES |
| `scripts/run_pipeline.py` | YES (imports from `agents.website`) |

**Correction to the research/lens framing.** The lenses proposed verification commands like `import agents.website.cli; assert "gitlab" not in sys.modules`. **That assertion fails *today*, before any O3 change** — the `agents/website/__init__.py:20-21` eager re-export pulls both SDKs on any website-package import, so the CLI/pipeline import paths are **already SDK-eager**. The lazy `import` statements inside the adapter branches are real but moot at module-import time.

The **only** genuinely SDK-free surface is `orchestrator/config.py`. Therefore the operative invariant for O3 is narrow and verifiable:

> **`REPO_PLATFORMS`, `PlatformSpec`, and the factories MUST live in an SDK-free module (recommended: `orchestrator/config.py` inline — its natural home, where `HostLiteral` already lives), and the factories MUST lazy-import inside the body, so that importing the registry pulls no SDK.** Verify with `import …orchestrator.config; assert 'gitlab' not in sys.modules and 'github' not in sys.modules`. **Do NOT** place the registry under `agents/website/` (the package `__init__` is SDK-eager) and **do NOT** assert SDK-freeness of the CLI/pipeline import (already false).

**Recommended home: `orchestrator/config.py` inline** (no new module, no circular import — `config.py` defines `HostLiteral` and can define `REPO_PLATFORMS` beside it; factories lazy-import the website adapters at *call* time only). Alternative: a new `orchestrator/platforms.py` (cleaner separation, but `config.py` then imports it for the keys — fine, no cycle, since `platforms.py` need not import `config`). **Open contract question for Phase O3-1 (Learning #40):** confirm `config.py`-inline vs `orchestrator/platforms.py` before writing code.

**Discovered adjacent issue (deferred, do NOT fix in O3):** the `agents/website/__init__.py:20-21` eager adapter re-export makes the website CLI pull *both* SDKs at startup even for `--help`/`--fake`. Making it lazy is a real improvement but changes the package's public import surface — a separate, opt-in cleanup, not O3.

---

## 7. Implementation Plan (per-phase)

**Three phases, one session each.** Each phase leaves the tree green and is **independently shippable** (Phase O3-1 alone closes Audit #8; Phase O3-2 alone kills the token-ternary divergence bug). Expect **4 sessions minimum** (this planning session + 3). **Do NOT bundle phases** (FM #18). The CI-platform renderer is excluded from **every** phase (§11).

`PlatformSpec` is **grown across phases** to keep each diff minimal: O3-1 introduces it with the two **data** fields; O3-3 adds the `adapter_factory` field. Each phase consumes the field(s) it adds.

### 7.1 Phase O3-1 — Single-source the host vocabulary + drift guard (= Audit #8 / quick-win #5)

- **Goal:** the host membership set lives in exactly one place (`REPO_PLATFORMS.keys()`), pinned to `HostLiteral` by an import-time guard; an unknown host fails closed at validation. **No behavior change for valid hosts.**
- **Why first:** it lands the single `Literal`/allow-list SoT the registry's later phases derive from, and it is independently valuable (closes audit #8).
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `src/model_project_constructor/_vocab_guard.py` (new) | extract `_assert_vocab_parity` (dependency-free); **parameterize the remediation hint** (current body hardcodes `schemas/v1/common.py`, wrong for the host registry — §6.2) | +30 |
| `orchestrator/config.py` | add `PlatformSpec` (2 data fields) + `REPO_PLATFORMS`; `from .._vocab_guard import assert_vocab_parity`; pin `HostLiteral`; `:92` inline tuple → `host_raw not in REPO_PLATFORMS`; error string from `sorted(REPO_PLATFORMS)` (keep substring `MPC_HOST`) | ~30 |
| `agents/website/cli.py` | `VALID_HOSTS = frozenset(REPO_PLATFORMS)` (import from config); `:130` error from `sorted(REPO_PLATFORMS)` | ~6 |
| `scripts/run_pipeline.py` | `:416` argparse `choices=sorted(REPO_PLATFORMS)` | ~2 |
| `tests/orchestrator/test_host_registry_guard.py` (new) | guard fires on a stub mismatched `Literal` vs stub dict (non-vacuous, like S113's `TestVocabularyDriftGuards`) | +40 |

- **Wiring:** see §6.1–6.2. Registry carries real `default_api_url`/`token_env_var` values **but Phase O3-1 consumes only the keys**; the URL/token *call sites* are untouched until O3-2.
- **What DONE looks like:** (1) the 4 host-membership copies (§3.1) all derive from `REPO_PLATFORMS`; (2) `import orchestrator.config` succeeds **and** pulls no SDK; (3) adding a bogus key to `REPO_PLATFORMS` without updating `HostLiteral` raises `AssertionError` at import (proven by the new guard test, not just by a clean import); (4) `MPC_HOST=bitbucket` still raises `ConfigError` matching `MPC_HOST`; (5) no `CIPlatform`/`ci_platform`/`VALID_CI_PLATFORMS` site changed; (6) full suite green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor
PY=.venv/bin/python
# (a) registry import is SDK-free (the real invariant — NOT the CLI):
$PY -c "import sys; import model_project_constructor.orchestrator.config as c; \
  assert 'gitlab' not in sys.modules and 'github' not in sys.modules, 'registry pulled an SDK'; \
  from typing import get_args; assert set(get_args(c.HostLiteral))==set(c.REPO_PLATFORMS); print('parity+SDK-free OK', sorted(c.REPO_PLATFORMS))"
# (b) guard is live under -O (raise, not stripped assert) — proven by the NEGATIVE test, not a clean import:
$PY -m pytest tests/orchestrator/test_host_registry_guard.py -q --no-cov
# (c) the 4 host-membership copies are gone (CI frozenset at cli.py:43 is expected to remain):
grep -rnE 'frozenset\(\{"gitlab", "github"\}\)' src/ scripts/   # expect ONLY cli.py:43 (VALID_CI_PLATFORMS)
grep -rnE 'not in \("gitlab", "github"\)|choices=\["gitlab", "github"\]' src/ scripts/   # expect ZERO
# (d) full suite (coverage gate applies ONLY to the full run — see §10):
$PY -m pytest -q
```

- **Session boundary:** **This phase is one session. Close out when the four host-membership copies derive from `REPO_PLATFORMS`, the guard test is green, and the full suite passes. STOP.**

### 7.2 Phase O3-2 — Fold `default_api_url` + `token_env_var`; retire URL copies & token ternaries

- **Goal:** every host→URL and host→token-env mapping is a single `REPO_PLATFORMS[host]` lookup; the two must-agree token ternaries (§3.3) become one.
- **Why second:** removes the highest-value duplication (the silent-divergence token bug) without yet touching adapter construction.
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `orchestrator/config.py` | add `from typing import Literal, cast` (`cast` not currently imported — mypy-strict); `:98` URL branch → `REPO_PLATFORMS[host].default_api_url`; `:103` **and** `:140` token ternaries → `REPO_PLATFORMS[self.host].token_env_var` (keep `GITHUB_TOKEN` substring in the `:140` error); `:96` redundant narrowing → `cast(HostLiteral, host_raw)`; keep `DEFAULT_*_URL` in `__all__` as **aliases** over registry values | ~20 |
| `agents/website/cli.py` | `:39-40` constants → registry aliases (or remove + repoint `:102-103,154`); `:154` ternary → `REPO_PLATFORMS[host].default_api_url` | ~10 |
| `scripts/run_pipeline.py` | `:114,117,289,295` inline literals → `os.environ.get("MPC_HOST_URL", REPO_PLATFORMS[host].default_api_url)`; in `build_repo_target` (`:113-120`) **hoist** the now-identical `host_url=…` line above the `if/else` (only the namespace ternary stays inside — avoids a fresh duplicate) | ~6 |

- **What DONE looks like:** (1) `"https://gitlab.com"`/`"https://api.github.com"` appear **only** inside the `REPO_PLATFORMS` literal; (2) zero host→token ternaries remain; (3) `DEFAULT_GITLAB_URL`/`DEFAULT_GITHUB_URL`/`DEFAULT_HOST` still importable by name (test_config.py:15-16) with identical values; (4) the `run_pipeline.py:113-120` per-host default **namespace** ternary is **left as-is** with a comment (deployment policy, not host wiring — §11); (5) full suite green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python
grep -rnE 'https://(gitlab\.com|api\.github\.com)' src/ scripts/ | grep -v REPO_PLATFORMS   # expect ZERO outside the registry literal
grep -rnE '"GITLAB_TOKEN" if .* else "GITHUB_TOKEN"' src/ scripts/                          # expect ZERO
$PY -m pytest tests/orchestrator/test_config.py -q --no-cov   # token/URL pins green (NOTE --no-cov for subset, §10)
$PY -m pytest -q                                              # full suite + coverage
```

- **Session boundary:** **One session. Close out when URL + token mappings are single-sourced and the full suite passes. STOP.**

### 7.3 Phase O3-3 — Route adapter construction through `REPO_PLATFORMS[host].adapter_factory`; prove extensibility

- **Goal:** the two adapter branches (§3.4) collapse to one registry call each; the silent `else` fall-through and the Session-30 kwarg-bug class are eliminated; a regression test proves a 3rd host needs only a registry row + adapter module.
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `orchestrator/config.py` | add `adapter_factory` field to `PlatformSpec`; define `_make_gitlab_adapter`/`_make_github_adapter` (lazy import inside body); populate the two registry entries | ~20 |
| `agents/website/cli.py` | `:166-190` gitlab/github arms → `REPO_PLATFORMS[host].adapter_factory(...)` (`fake` arm stays special) | ~12 |
| `scripts/run_pipeline.py` | `:284-299` live arms → same factory call; compute `host_url` **before** the call (§6.3) | ~12 |
| `tests/orchestrator/test_host_registry_extensibility.py` (new) | a stub `PlatformSpec` under a fake key drives the full path with zero call-site edits; assert `REPO_PLATFORMS` contains **no** CI field and `ci_platform` plumbing still derives from `VALID_CI_PLATFORMS` (host/CI non-fusion pin) | +60 |

- **What DONE looks like:** (1) no `PythonGitLabAdapter(`/`PyGithubAdapter(` construction outside the factory bodies + the two docstring examples; (2) no `elif host == "gitlab"` / `else: # github` adapter branch remains; (3) `import orchestrator.config` still SDK-free (factories defined, not called); (4) `test_run_pipeline_adapter.py` Session-30 + `MPC_HOST_URL`-to-GHE regressions green; (5) `test_cli_ci_platform_overrides_host` (`test_cli.py:134`) divergence still green; (6) the extensibility + non-fusion tests green; (7) full suite green, mypy clean, ruff clean, decoupling 2/2.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python
grep -rnE 'PythonGitLabAdapter\(|PyGithubAdapter\(' src/ scripts/ | grep -vE 'docstring|adapter\.py:'   # expect: only inside factory bodies
grep -rnE 'elif host == "gitlab"|else:.*# host == "github"' src/ scripts/                                # expect ZERO adapter branches
$PY -c "import sys; import model_project_constructor.orchestrator.config; assert not any(m in ('gitlab','github') for m in sys.modules), 'registry import pulled an SDK'"
$PY -m pytest tests/scripts/test_run_pipeline_adapter.py tests/agents/website/test_cli.py tests/orchestrator/test_host_registry_extensibility.py -q --no-cov
$PY -m pytest -q && .venv/bin/ruff check src/ tests/ packages/ scripts/ && .venv/bin/mypy src   # full suite + lint (exact CI scope, §10) + types
```

- **Session boundary:** **One session. Close out when both adapter branches route through the registry, the Session-30 regression + divergence tests stay green, and the full suite + mypy + ruff pass. STOP.**

---

## 8. Impact Analysis

| Surface | Impact | Action |
|---|---|---|
| `RepoClient` Protocol + adapter bodies | **none** | unchanged — the constructor asymmetry is absorbed by the factory, not the Protocol |
| Host `Literal` (`config.py:29`) | stays hand-written | pinned to `REPO_PLATFORMS` by the import-time guard |
| Host allow-lists (`config.py:92`, `cli.py:42`, `run_pipeline.py:416`) | collapse to `REPO_PLATFORMS` derivations | Phase O3-1 |
| `VALID_CI_PLATFORMS` (`cli.py:43`) | **none** | explicit scope boundary — CI vocabulary, untouched |
| URL constants / token ternaries (`config.py:33-34,103,140`; `cli.py:39-40`) | replaced by registry fields; constants kept as aliases | Phase O3-2; preserve `__all__` exports |
| Adapter dispatch (`cli.py:166-190`, `run_pipeline.py:284-299`) | one factory call each | Phase O3-3 |
| `run_pipeline.py` per-host **namespace** default (`:113-120`) | **left as-is** (deployment policy, not host wiring) | comment only; revisit only if `default_namespace` ever justified (YAGNI) |
| Tests pinning host vocab (§3.6) | gate every phase | re-run as written, mind the `--no-cov` coverage trap (§10) |
| `_assert_vocab_parity` | extracted to shared `_vocab_guard.py` | governance_templates copy left in place (optional later migration) |

**What does NOT change:** any `ci_platform` site (§3.5, all 27); the `RepoClient` Protocol; adapter constructor bodies; the website-package eager-import behavior (`__init__.py:20-21`).

**What might break (risk):** dropping rather than aliasing the `DEFAULT_*_URL` exports (test_config.py imports them by name); a factory that bakes the URL default (breaks `MPC_HOST_URL`→GHE); placing the registry in an SDK-eager module (regresses `config.py` SDK-freeness). All three are guarded by §7 verification commands.

---

## 9. Failure-Mode Analysis

| Failure | Surfaces in | Caught by | Result |
|---|---|---|---|
| Unknown host string post-registry | `REPO_PLATFORMS[host]` lookup | `KeyError` at lookup (was silent `else: # github`) | **fails closed** — the headline correctness win |
| `HostLiteral` drifts from registry keys | edit-time | import-time `_assert_vocab_parity` `raise` (survives `-O`) | build fails loudly |
| Registry placed in SDK-eager module | `import config` | §7 SDK-free assertion | caught in phase verify |
| Factory bakes URL default → `MPC_HOST_URL` ignored | GHE users | `test_run_pipeline_adapter.py:175-222` | regression test fails |
| Reviewer folds CI vocab into registry | diff touches `governance_templates.py`/`cli.py:43` | §3.5 non-fusion test (O3-3) + scope rule | rejected |
| `_vocab_guard` imported from `governance_templates` | `import config` | §7 SDK-free assertion | caught (extract to dependency-free module) |
| Guard weakened to bare `assert` | future edit | `python -O` would strip it; phase test imports under `-O` | negative test fails |

---

## 10. Verification Plan

"Verified-complete" for each implementation session:

1. **Full suite green:** `.venv/bin/python -m pytest -q`. **Re-confirm the passing count — do NOT hardcode** (Session-114 baseline was 667/667 @ 97.13%, but it drifts — Learnings #19/#28). Each new test added by a phase raises the count.
2. **⚠ Coverage-gate trap (verified):** `pyproject.toml:65` sets `addopts = "… --cov-fail-under=95"`, so **any pytest *subset* run reports `FAIL Required test coverage of 95% not reached`** even when every selected test passes. **For subset runs, append `--no-cov`** (as in §7); for the coverage gate itself, run the **full** suite. "pytest … green" is only literally true full-suite or with `--no-cov`.
3. **mypy clean:** run the **exact CI command** (see CI workflow / `pyproject.toml [tool.mypy]`) — CI scope can diverge from the tool's natural scope (Learning #18). Baseline 0/48 + 0/13.
4. **ruff clean:** the exact CI invocation is `ruff check src/ tests/ packages/ scripts/` (`.github/workflows/ci.yml:23`). `scripts/` **is** included — O3 edits `run_pipeline.py` in every phase, so lint it.
5. **Decoupling 2/2** (the repo's decoupling check) green.
6. **Positive fall-through proof:** an unknown host now **raises** (analogue of o2's "prove it RED") — asserted by the §7.1 guard test and the §7.3 extensibility test, not merely by a clean import.
7. **CI-vocabulary untouched:** `grep -rnE 'CIPlatform|ci_platform|VALID_CI_PLATFORMS' src/ scripts/` still returns its 27 sites unchanged (§3.5).

> **Corrected/rejected verification commands** the executor must NOT copy from the research notes: (a) `assert "gitlab" not in sys.modules` after importing **cli** — false today, the registry/config import is the right target (§6.4); (b) BRE/ERE-mixed greps with `\|` + unescaped parens — use `grep -E` with proper escaping (as in §13); (c) a clean `python -O -c 'import config'` proves the guard runs but **not** that it fires — only a mismatched-vocab negative test proves that; (d) the pattern `host == "gitlab" else "github"` does **not** match `config.py:96` (actual text: `"gitlab" if host_raw == "gitlab" else "github"`).

---

## 11. Out of Scope (explicit)

- **THE CI-platform file-selection renderer (#6/#42) — folded into C4/E2, NOT O3.** `governance_templates.py:809,834-837` (the `if ci_platform == "gitlab"/else` branch), `:949-953` (the hardcoded CI-path set — **audit line-drift: audit said `:908-913`**), the `render_gitlab_ci`/`render_github_actions_ci` functions, `VALID_CI_PLATFORMS` (`cli.py:43`), the `--ci-platform` flag + default-from-host (`cli.py:107-143`), and all `ci_platform` state/agent/nodes plumbing (§3.5). When C4/E2 lands, it should get its **own** `_assert_vocab_parity` guard. **Resolving the audit-wording tension:** `:174` lists O3 as touching "governance CI renderers" and references #6, but `:119`'s `PlatformSpec` (URL + token + factory) has **no CI slot** and `:142` places the CI registry in C4/E2. The structurally-correct reading — host-only O3 — is adopted here; the `:174` wording is **not** license to touch `governance_templates.py`.
- **Building the 3rd adapter module** (Bitbucket/Gitea/Azure DevOps). The registry makes it cheap; actually adding one is a separate session (and its CI renderer is a C4/E2 concern).
- **The per-host default namespace** (`run_pipeline.py:113-120`, `my-org` vs `data-science/model-drafts`) — deployment policy, not host wiring; leave the ternary, add a comment. Optional `default_namespace` field is YAGNI for two hosts.
- **Making `agents/website/__init__.py` lazy** (the eager re-export at `:20-21`) — a real adjacent improvement, but changes the package's public import surface; opt-in cleanup, not O3.
- **Controlled-vocabulary single-source for governance/model-type enums** — that is Overhaul **O4** (audit #14/#24/#27).
- **The LLM-provider factory** (audit E4) and **the Stage-list pipeline driver** (O1).
- **Bundling any other backlog item** in an implementation session (FM #18).

---

## 12. Provenance

- **Audit:** `docs/audits/2026-06-01-technical-debt-audit.md` — E1 `:115-119`, E2 `:121-142`, quick-win #5 `:160`, O3 `:174`, sequencing `:177`, table row #6 `:232`.
- **`RepoClient` Protocol:** `agents/website/protocol.py:42-66` (read; `create_project` + `commit_files`; both adapters subclass at `gitlab_adapter.py:41` / `github_adapter.py:48`).
- **Two-vocabulary separation evidence:** `cli.py:42-43` (two frozensets), `cli.py:135-136` (`ci_platform` defaults to host), `--ci-platform` doc `cli.py:14`, divergence test `test_cli_ci_platform_overrides_host` (`test_cli.py:134`), separability comment `state.py:27-30`.
- **Evidence inventory (§3):** produced by direct `grep` against the working tree at **HEAD `9cf9f74`** (Session 115); cross-checked against an 8-agent research workflow (4 mappers + 3-lens design panel + adversarial completeness critic). Per **Learning #45**, every count entering this doc was re-derived by direct grep; per **Candidate #82**, every code claim (guard location/signature, SDK-import topology, divergence test, coverage gate) was confirmed against canonical source before being written.
- **Corrections made during verification (provenance hygiene, mirroring o2 §2.1):** (1) the research/lenses claimed the **CLI import is SDK-free** and proposed it as a verification target — **falsified** by direct import-topology check (`import agents.website.cli` and `scripts/run_pipeline.py` both pull both SDKs via `__init__.py:20-21`); the only SDK-free surface is `orchestrator/config.py` (§6.4). (2) Several proposed grep/`-O` verification commands were non-runnable or non-proving and were rewritten (§10). (3) audit CI-path line drift `:908-913` → `:949-953` confirmed.
- **Guard precedent:** `_assert_vocab_parity` (`governance_templates.py:35-56`, raises not asserts), Audit #2 / Session 113 (`TestVocabularyDriftGuards`). Candidate #77 (parseable producer for drift-guard tests) — this is its likely 3rd instance.
- **Methodology:** `ARCHITECTURE_WORKSTREAM.md` (Interface-First `:126`, Refactor Heuristics `:191-212`, anti-patterns `:226-227`); house-style mirror of `docs/planning/o2-shared-llm-json-plan.md` + `scope-b-plan.md`.

---

## 13. Appendix — Full grep inventory (executor re-run block)

Run in Phase 0 **before** starting any phase. If counts drift, investigate before implementing.

```bash
cd /Users/rmsharp/Development/model_project_constructor   # verified 2026-06-05 @ HEAD 9cf9f74
# §3.1 — host membership declarations
grep -rnE 'HostLiteral *= *Literal'                  src/ scripts/   # Expected: 1  (config.py:29)
grep -rnE 'not in \("gitlab", "github"\)'            src/ scripts/   # Expected: 1  (config.py:92)
grep -rnE 'VALID_HOSTS *: *frozenset'                src/ scripts/   # Expected: 1  (def cli.py:42; consumers at cli.py:128,130)
grep -rnE 'choices=\["gitlab", "github"\]'           src/ scripts/   # Expected: 1  (run_pipeline.py:416)
# §3.2 — default API URL copies (named-constant DEFINITIONS only)
grep -rnE '^(DEFAULT_GIT(LAB|HUB)_URL|GIT(LAB|HUB)_DEFAULT_HOST_URL) *=' src/         # Expected: 4 (config.py:33-34 + cli.py:39-40)
grep -nE  '"https://(api\.github\.com|gitlab\.com)"' scripts/run_pipeline.py           # Expected: 4 (inline literals)
# §3.3 — host->token ternaries (must-agree)
grep -rnE '"GITLAB_TOKEN" if .* else "GITHUB_TOKEN"' src/ scripts/   # Expected: 2  (config.py:103,140)
# §3.4 — adapter constructions (anchored on `= …Adapter(` to exclude the 2 class defs)
grep -rnE '= (PythonGitLabAdapter|PyGithubAdapter)\(' src/ scripts/  # Expected: 6  (4 real + 2 docstring)
# §3.5 — CI vocabulary GUARD (must stay constant across all phases)
grep -rncE 'CIPlatform|ci_platform|VALID_CI_PLATFORMS' src/ scripts/ | awk -F: '{s+=$2} END{print s}'   # Expected: 27
```

## 14. Appendix — File reference map

| Concern | File:Line |
|---|---|
| Registry home (recommended) | `orchestrator/config.py` (inline, beside `HostLiteral:29`) |
| Shared drift guard (new) | `src/model_project_constructor/_vocab_guard.py` |
| `RepoClient` Protocol | `agents/website/protocol.py:42-66` |
| Host `Literal` | `orchestrator/config.py:29` |
| Host allow-lists | `config.py:92`, `cli.py:42`, `run_pipeline.py:416` |
| URL constants | `config.py:33-34`, `cli.py:39-40` |
| Token ternaries | `config.py:103`, `config.py:140` |
| Adapter dispatch | `cli.py:166-190`, `run_pipeline.py:284-299` |
| Adapter constructors (asymmetry) | `gitlab_adapter.py:56-65`, `github_adapter.py:66-72` |
| Namespace default (leave) | `run_pipeline.py:113-120` |
| **CI vocabulary — DO NOT TOUCH (C4/E2)** | `governance_templates.py:32,809,834-837,949-953`; `cli.py:43,107-143,192-193`; `state.py:31,76,82`; `agent.py:38,41,76`; `nodes.py:147` |

---

## Sign-off checklist for the executor

- [ ] Re-read this whole plan.
- [ ] Re-ran §13 grep inventory; counts match (or deltas understood).
- [ ] Confirmed the host/CI separation still holds (`test_cli_ci_platform_overrides_host`, `test_cli.py:134`, green).
- [ ] Confirmed quick-win #5 status (Phase O3-1 = not yet landed unless a prior session did it).
- [ ] Resolved the §6.4 open question: registry home = `config.py` inline **or** `orchestrator/platforms.py`.
- [ ] Pre-flight green: `pytest && ruff && mypy` (full suite for coverage; `--no-cov` for subsets — §10).
- [ ] Phase 1B stub written to `SESSION_NOTES.md` **before** any code.
- [ ] Doing **exactly one** phase this session (FM #18 is the active risk).
