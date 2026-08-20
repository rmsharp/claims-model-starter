# Contributing

This page documents how to contribute to the Model Project Constructor: development environment setup, code-quality gates, testing conventions, commit-message format, and the session discipline expected for non-trivial changes.

The project is MIT-licensed (see `LICENSE` at the repository root). External contributions are welcome; by opening a pull request you agree to license your contribution under the same terms.

---

## 1. Development environment

### Prerequisites

- **Python ≥ 3.11** — `requires-python = ">=3.11"` in `pyproject.toml` (under `[project]`).
- **[uv](https://docs.astral.sh/uv/)** — the project is a `uv` workspace (the `[tool.uv.workspace]` table in `pyproject.toml`). The root `pyproject.toml` declares `packages/*` as workspace members and resolves `model-project-constructor-data-agent` from the workspace rather than PyPI.

### First-time setup

```bash
git clone https://github.com/rmsharp/model_project_constructor.git
cd model_project_constructor
uv sync --extra agents --extra ui --extra dev
```

That single `uv sync` resolves every runtime and development dependency into `.venv/`; only the optional `docs` extra (the MkDocs tutorial-site toolchain) is omitted — add `--extra docs` when building the documentation site. Subsequent runs use the cached resolution.

### Optional-dependency groups

From the `[project.optional-dependencies]` table in `pyproject.toml`:

| Extra | Installs | Why |
|---|---|---|
| `agents` | `langgraph`, `anthropic[bedrock]`, `sqlparse`, `sqlalchemy`, `httpx`, `typer` | Agent runtimes and host adapters. The `[bedrock]` marker adds the AWS transitive stack (boto3 / botocore) used by the `bedrock` LLM provider. |
| `ui` | `fastapi`, `uvicorn`, `sse-starlette`, `langgraph-checkpoint-sqlite`, `python-multipart` | Intake web UI |
| `dev` | `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff` | Developer toolchain |
| `docs` | `mkdocs`, `mkdocs-material` | MkDocs tutorial-site build (`mkdocs.yml` at the repository root) |

A minimal install (`uv sync` with no extras) is only useful for consumers of the schema package — it does not include the agents themselves.

---

## 2. Code-quality gates

All four gates run in CI on every push and every pull request to `master` (the `on:` trigger in `.github/workflows/ci.yml`). A change that fails any gate cannot merge.

### 2.1 Lint (`ruff`)

Configuration in the `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.lint.per-file-ignores]` tables in `pyproject.toml`:

- `target-version = "py311"`
- `line-length = 100`
- Rules: `["E", "F", "I", "UP", "B", "SIM"]`
  - **E/F** — pycodestyle errors + pyflakes (the baseline)
  - **I** — isort-compatible import ordering
  - **UP** — pyupgrade (modern Python syntax)
  - **B** — flake8-bugbear (likely bugs and design issues)
  - **SIM** — flake8-simplify (code simplification suggestions)
- Per-file ignore: `"**/cli.py" = ["B008"]` — typer's `typer.Option()` in default arguments is the canonical pattern and tripping B008 is a false positive.

Run locally:

```bash
uv run ruff check src/ tests/ packages/ scripts/
uv run ruff format src/ tests/ packages/ scripts/   # apply formatting
```

### 2.2 Type check (`mypy --strict`)

Configuration in the `[tool.mypy]` table in `pyproject.toml`:

- `python_version = "3.11"`
- **`strict = true`** — enables every strictness flag (no-implicit-optional, check-untyped-defs, disallow-untyped-defs, disallow-incomplete-defs, warn-redundant-casts, warn-unused-ignores, etc.)
- `packages = ["model_project_constructor", "model_project_constructor_data_agent"]` — both the main package and the data-agent workspace package are type-checked.
- `mypy_path = ["src", "packages/data-agent/src"]` — resolves the workspace layout.

Run locally:

```bash
uv run mypy
```

### 2.3 Tests (`pytest --cov`)

Configuration in the `[tool.pytest.ini_options]`, `[tool.coverage.run]`, and `[tool.coverage.report]` tables in `pyproject.toml`:

- `testpaths = ["tests"]`
- `pythonpath = ["src", "packages/data-agent/src"]`
- `addopts = "-ra --cov=model_project_constructor --cov=model_project_constructor_data_agent --cov-report=term-missing --cov-fail-under=95"`
- Coverage floor: **95%** across both packages combined, branch coverage enabled.
- Excluded from coverage by pragma: `pragma: no cover`, `raise NotImplementedError`, `if TYPE_CHECKING:`.

Run locally:

```bash
uv run pytest -q                    # full suite
uv run pytest tests/agents/intake/  # one subdir
uv run pytest -k "test_envelope"    # by name pattern
uv run pytest -m "not live"         # skip the live-LLM eval tier (see below)
```

**The `live` tier.** `tests/eval/` holds the LLM eval corpus. Most of it is hermetic, but `tests/eval/test_eval_live.py` is marked `live` file-wide (four test functions, each parametrized over every shadow provider) and calls a **real** LLM. The marker is registered under `[tool.pytest.ini_options]` in `pyproject.toml`. A `live` test auto-skips when the provider it targets has no credentials (`anthropic` → `ANTHROPIC_API_KEY`; `bedrock` → the AWS credential chain; `opencode` → its binary on `PATH` **and** `OPENCODE_EVAL_MODEL` naming the model to pin), which is how CI stays hermetic — CI runs with none. If you have provider credentials exported, a bare `uv run pytest -q` **will make billable API calls**: pass `-m "not live"` to deselect the tier, or `-m live` to run it deliberately.

`opencode` takes two signals rather than one for exactly that reason. Its binary is installed globally on any machine that has worked on the adapter, so gating on the binary alone would silently turn every `uv run pytest -q` on a contributor's machine into a billable run while CI, which has no binary, still looked hermetic. Setting `OPENCODE_EVAL_MODEL` is the deliberate opt-in — and it is also the model id the run pins, since that provider ships no default model.

Current snapshot: **997 test functions** across `tests/` subdirectories (`orchestrator/` 211, `data_agent_package/` 199, `agents/website/` 191, `agents/intake/` 150, `schemas/` 81, `eval/` 75, `ui/intake/` 32, `scripts/` 22, `agents/data/` 16), plus 20 across the top-level files `test_data_agent_decoupling.py`, `test_llm_json_parity.py`, `test_vocab_guard.py`, and `test_wiki_no_line_citations.py`. (Test *functions*, not collected tests — parametrization makes the collected count higher; `pytest -q` currently reports 1110 passed plus 12 credential-gated `live` cases that skip.) This number drifts as tests are added; recompute it with:

```bash
grep -rhE '^\s*(async )?def test_' tests/ | wc -l   # 997 at time of writing
```

### 2.4 Data-agent decoupling

Configuration: the `decoupling` job in `.github/workflows/ci.yml`. A standalone CI job invokes `tests/test_data_agent_decoupling.py` with `--no-cov`:

```bash
uv run pytest tests/test_data_agent_decoupling.py -v --no-cov
```

This test AST-walks the standalone `packages/data-agent/` package and asserts zero imports of `IntakeReport` or any intake-schema module. It enforces `docs/architecture-history/architecture-plan.md` §7 / constraint C4: the Data Agent is reusable outside the full pipeline. A contribution that adds such an import will fail this job even if coverage and types are clean.

---

## 3. Pre-commit hooks

There is **no** `.pre-commit-config.yaml` in the repository and no pre-commit gate on code. There *is* one checked-in project-wide hook: `.githooks/post-commit`, which republishes the GitHub Wiki whenever a commit touches `docs/wiki/claims-model-starter/` (it delegates to `scripts/publish_wiki.sh`; set `MPC_SKIP_WIKI_PUBLISH=1` for a deliberate skip). It is opt-in per clone — enable it once with `git config core.hooksPath .githooks`. **If you edit any wiki page, install it.** Otherwise contributors are expected to run `ruff` and `pytest` locally before pushing. The CI pipeline is the enforcement boundary; hooks are a convenience, not a requirement.

If you want local hooks, the recommended pattern is a personal `.git/hooks/pre-push` script that runs `uv run ruff check src/ tests/ packages/ scripts/ && uv run mypy && uv run pytest -q`. Do not commit another project-wide hook configuration without first proposing it as a separate design change.

---

## 4. Commit-message convention

Observed from `git log --oneline -50`, the project uses the **Conventional Commits** subset with optional session scopes:

```
<type>(<scope>): <subject>
```

### Type taxonomy

| Type | When to use | Example |
|---|---|---|
| `feat` | New feature or phase implementation | `feat(phase-6): production hardening — logging, metrics, config, CI, runbooks` |
| `fix` | Bug fix | `fix(ci): use click.unstyle to strip ANSI codes in CLI help test` |
| `docs` | Documentation only | `docs(session-20a): add intake design, schema, security wiki pages` |
| `chore` | Dependency, config, or housekeeping | `chore(coverage): raise pytest coverage floor 93% → 94%` |
| `refactor` | Internal restructuring, no external behavior change | `refactor(phase-2b): move data agent to standalone package` |
| `test` | Test-only additions | (rare in recent history) |

### Scope conventions

- **`(phase-N)` / `(phase-X)`** — implementation phases from `docs/architecture-history/architecture-plan.md` §14 (e.g., `phase-1`, `phase-4b`, `phase-a`).
- **`(session-N)`** — documentation commits that land at the end of a session; pairs with the session stub in `SESSION_NOTES.md`.
- **`(ci)` / `(lint)` / `(coverage)` / `(docs)` / `(backlog)` / `(readme)`** — area tags for maintenance commits.

### Subject line

- Imperative mood, no trailing period ("add X", not "added X" or "adds X").
- Keep under ~72 characters. If you need detail, use the body.
- For phase work, name the user-visible outcome, not the internal change (compare `feat(phase-6): production hardening — logging, metrics, config, CI, runbooks` with a terse `feat: Phase 6`).

### Co-author trailer

Machine-generated commits use a `Co-Authored-By:` trailer naming the assistant model. External contributions do not need a trailer.

---

## 5. Test-writing conventions

### Organization

- One `test_<module>.py` per production module — mirror the source layout inside `tests/`.
- Contract tests (behavioral invariants) go at the top of the file; happy-path scenarios below; edge cases last.
- Fixtures live in `tests/fixtures/` as JSON or YAML files and are loaded by helper functions, not hand-constructed in each test.

### Invariant tests

Some existing tests are **structural guards** that fail CI if a contract is broken:

- `tests/test_data_agent_decoupling.py` — AST-walks for forbidden imports (see §2.4).
- `tests/schemas/test_envelope_and_registry.py` — every `REGISTRY` entry round-trips through `HandoffEnvelope` → `load_payload`.
- `tests/agents/website/test_governance.py` — per-tier fan-out asserts both **positive** (`artifact in files`) *and* **negative** (`artifact not in files`) for each tier × consumer × protected-attributes combination. A positive-only assertion will pass silently if a tier starts emitting the wrong artifact (see [Extending the Pipeline](Extending-the-Pipeline) §4).

When adding a new contract, add a structural guard alongside it. CI enforcement beats code review for long-lived invariants.

### Mocking external services

- The Anthropic SDK is stubbed with module-local `_FakeAnthropic` / `_FakeMessages` classes defined inside each client test file — `tests/agents/intake/test_anthropic_client.py`, `tests/agents/intake/test_bedrock_client.py`, their `tests/data_agent_package/` twins, and `tests/test_llm_json_parity.py` — that return canned JSON. They are plain classes, not shared pytest fixtures. At the protocol seam, `FakeLLMClient` (in `tests/agents/data/test_data_agent.py`) and `FixtureLLMClient` (in `src/model_project_constructor/agents/intake/fixture.py`) stand in for a real client. Do not hit the real API in unit tests.
- Both repo-host adapters are tested via `httpx.MockTransport` at the wire boundary (GitLab migrated off `python-gitlab`/`MagicMock` in Session 191, GitHub off `PyGithub`/`MagicMock` in Session 193 — both per `docs/planning/httpx-adapter-migration.md`). An end-to-end `FakeRepoClient` is provided for Website Agent tests — see `tests/agents/website/conftest.py`.
- Database tests use in-memory SQLite; there is no integration test requiring a live database.

---

## 6. Session discipline (for non-trivial changes)

Non-trivial changes (anything touching more than ~5 files, any refactor, any new agent, any schema change) should follow the session protocol documented at:

- `SESSION_RUNNER.md` — operating procedure: orient → execute → close out.
- `SAFEGUARDS.md` — commit discipline, blast-radius limits, mode-switching rules.
- `CLAUDE.md` — project overview and session protocol reference.

Key rules that apply to human contributors as well:

1. **One deliverable per session.** If you find yourself thinking "while I'm at it…" — stop, commit what you have, and open a separate branch or PR for the new scope.
2. **Commit before any multi-file change.** Disaster recovery becomes a `git checkout` instead of a multi-hour unwind.
3. **Never refactor across module boundaries without a plan.** Cross-module refactors need a written plan (in `docs/planning/`) before code changes.
4. **No hook bypasses.** Never use `--no-verify` on commit or push unless explicitly authorized.

These aren't style preferences — they are documented responses to specific past failures. Reading `SAFEGUARDS.md` once before your first non-trivial PR is worth the 10 minutes.

---

## 7. Pull request workflow

1. **Fork and branch.** Branch from `master`. Use a descriptive name (`feat-bitbucket-adapter`, `fix-envelope-correlation-id`, not `patch-1`).
2. **Run the four CI gates locally** before pushing:
   ```bash
   uv run ruff check src/ tests/ packages/ scripts/
   uv run mypy
   uv run pytest -q
   uv run pytest tests/test_data_agent_decoupling.py -v --no-cov
   ```
3. **Open the PR against `master`**. Reference any related `docs/planning/` (active) or `docs/architecture-history/` (archived) document. If you introduce a new extension surface, add a test per [Extending the Pipeline](Extending-the-Pipeline) §5.
4. **Expect review feedback on `docs/` as strictly as on `src/`.** Architecture plans, wiki pages, and schema docstrings are load-bearing; they are reviewed with the same rigor as code.
5. **Squash-merge is the norm.** Preserve a clean `master` history. The PR description is the canonical commit message for the merge commit.

---

## 8. Licenses, attribution, and dependency hygiene

- **Project license:** MIT (`LICENSE` at repository root). Copyright © 2026 R. Mark Sharp. This published wiki is a separate repository and states the same MIT terms for its own content on the [License](License) page.
- **Dependency licenses:** the full per-dependency license table is `THIRD-PARTY-LICENSES` at the repository root. Direct dependencies are predominantly MIT / BSD / Apache 2.0. **Zero are LGPL** as of Session 193 — both repo-host adapters (GitLab in Session 191, GitHub in Session 193) dropped their LGPL SDKs for direct `httpx` calls (`docs/planning/httpx-adapter-migration.md`).
- **New dependencies:** prefer zero-new-dep solutions when the stdlib or existing deps can do the job (per learning #13). Each added dependency is a maintenance commitment — version conflicts, CI install time, and security-review surface all grow. If you need a new dep, include justification in the PR description.

---

## 9. Reporting issues

There is no public issue tracker actively in use for pre-UAT development — `gh issue list` is expected to return empty. Open work items are tracked in `BACKLOG.md` at the repository root. Once UAT begins, the tracker at `https://github.com/rmsharp/model_project_constructor/issues` will be the submission target.

For security-sensitive reports, please do not open a public issue. See `SECURITY.md` at the repository root for the disclosure process.

---

## See also

- [Getting Started](Getting-Started) — install, first run, verify
- [Extending the Pipeline](Extending-the-Pipeline) — design-level extension surfaces and the tests that guard them
- [Changelog](Changelog) — phase-by-phase history of notable changes
- [Architecture Decisions](Architecture-Decisions) — the rationale behind each design choice you'd encounter while contributing
- [Software Bill of Materials](Software-Bill-of-Materials) — current dependency versions and constraints
