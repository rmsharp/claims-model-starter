# Contributing

This page documents how to contribute to the Model Project Constructor: development environment setup, code-quality gates, testing conventions, commit-message format, and the session discipline expected for non-trivial changes.

The project is MIT-licensed (see `LICENSE` at the repository root). External contributions are welcome; by opening a pull request you agree to license your contribution under the same terms.

---

## 1. Development environment

### Prerequisites

- **Python ≥ 3.11** — `requires-python = ">=3.11"` in `pyproject.toml:6`.
- **[uv](https://docs.astral.sh/uv/)** — the project is a `uv` workspace (`pyproject.toml:45-49`). The root `pyproject.toml` declares `packages/*` as workspace members and resolves `model-project-constructor-data-agent` from the workspace rather than PyPI.

### First-time setup

```bash
git clone https://github.com/rmsharp/claims-model-starter.git
cd claims-model-starter
uv sync --extra agents --extra ui --extra dev
```

That single `uv sync` resolves every runtime and development dependency into `.venv/`. Subsequent runs use the cached resolution.

### Optional-dependency groups

From `pyproject.toml:17-40`:

| Extra | Installs | Why |
|---|---|---|
| `agents` | `langgraph`, `anthropic`, `sqlparse`, `sqlalchemy`, `python-gitlab`, `PyGithub`, `typer` | Agent runtimes and host adapters |
| `ui` | `fastapi`, `uvicorn`, `sse-starlette`, `langgraph-checkpoint-sqlite`, `python-multipart` | Intake web UI |
| `dev` | `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff` | Developer toolchain |

A minimal install (`uv sync` with no extras) is only useful for consumers of the schema package — it does not include the agents themselves.

---

## 2. Code-quality gates

All four gates run in CI on every push and every pull request to `master` (`.github/workflows/ci.yml:3-7`). A change that fails any gate cannot merge.

### 2.1 Lint (`ruff`)

Configuration at `pyproject.toml:79-88`:

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
uv run ruff check src/ tests/ packages/
uv run ruff format src/ tests/ packages/   # apply formatting
```

### 2.2 Type check (`mypy --strict`)

Configuration at `pyproject.toml:90-94`:

- `python_version = "3.11"`
- **`strict = true`** — enables every strictness flag (no-implicit-optional, check-untyped-defs, disallow-untyped-defs, disallow-incomplete-defs, warn-redundant-casts, warn-unused-ignores, etc.)
- `packages = ["model_project_constructor", "model_project_constructor_data_agent"]` — both the main package and the data-agent workspace package are type-checked.
- `mypy_path = ["src", "packages/data-agent/src"]` — resolves the workspace layout.

Run locally:

```bash
uv run mypy src/
```

### 2.3 Tests (`pytest --cov`)

Configuration at `pyproject.toml:58-77`:

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
```

Current snapshot: **131 test functions** across `tests/` subdirectories (`agents/intake/`, `agents/data/`, `agents/website/`, `orchestrator/`, `schemas/`, `ui/intake/`, `data_agent_package/`, `fixtures/`, `scripts/`, plus the top-level `test_data_agent_decoupling.py`).

### 2.4 Data-agent decoupling

Configuration at `.github/workflows/ci.yml:54-63`. A standalone CI job invokes `tests/test_data_agent_decoupling.py` with `--no-cov`:

```bash
uv run pytest tests/test_data_agent_decoupling.py -v --no-cov
```

This test AST-walks the standalone `packages/data-agent/` package and asserts zero imports of `IntakeReport` or any intake-schema module. It enforces architecture-plan §7 / constraint C4: the Data Agent is reusable outside the full pipeline. A contribution that adds such an import will fail this job even if coverage and types are clean.

---

## 3. Pre-commit hooks

There is **no** `.pre-commit-config.yaml` or equivalent git-hook configuration in the repository. Contributors are expected to run `ruff` and `pytest` locally before pushing. The CI pipeline is the enforcement boundary; hooks are a convenience, not a requirement.

If you want local hooks, the recommended pattern is a personal `.git/hooks/pre-push` script that runs `uv run ruff check src/ tests/ packages/ && uv run mypy src/ && uv run pytest -q`. Do not commit a project-wide hook configuration without first proposing it as a separate design change.

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

- **`(phase-N)` / `(phase-X)`** — implementation phases from `architecture-plan.md` §14 (e.g., `phase-1`, `phase-4b`, `phase-a`).
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
- `tests/schemas/test_registry.py` — every `REGISTRY` entry round-trips through `HandoffEnvelope` → `load_payload`.
- `tests/agents/website/test_governance.py` — per-tier fan-out asserts both **positive** (`artifact in files`) *and* **negative** (`artifact not in files`) for each tier × consumer × protected-attributes combination. A positive-only assertion will pass silently if a tier starts emitting the wrong artifact (see [Extending the Pipeline](Extending-the-Pipeline) §4).

When adding a new contract, add a structural guard alongside it. CI enforcement beats code review for long-lived invariants.

### Mocking external services

- The Anthropic client is mocked via fixtures that inject a `FakeAnthropicClient` returning canned JSON. Do not hit the real API in unit tests.
- The GitLab and GitHub adapters are tested via `MagicMock` at the `python-gitlab` / `PyGithub` boundary. An end-to-end `FakeRepoClient` is provided for Website Agent tests — see `tests/agents/website/conftest.py`.
- Database tests use in-memory SQLite; there is no integration test requiring a live database.

---

## 6. Session discipline (for non-trivial changes)

Non-trivial changes (anything touching more than ~5 files, any refactor, any new agent, any schema change) should follow the session protocol documented at:

- `SESSION_RUNNER.md` (321 lines) — operating procedure: orient → execute → close out.
- `SAFEGUARDS.md` (183 lines) — commit discipline, blast-radius limits, mode-switching rules.
- `CLAUDE.md` (61 lines) — project overview and session protocol reference.

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
   uv run ruff check src/ tests/ packages/
   uv run mypy src/
   uv run pytest -q
   uv run pytest tests/test_data_agent_decoupling.py -v --no-cov
   ```
3. **Open the PR against `master`**. Reference any related `docs/planning/` (active) or `docs/architecture-history/` (archived) document. If you introduce a new extension surface, add a test per [Extending the Pipeline](Extending-the-Pipeline) §5.
4. **Expect review feedback on `docs/` as strictly as on `src/`.** Architecture plans, wiki pages, and schema docstrings are load-bearing; they are reviewed with the same rigor as code.
5. **Squash-merge is the norm.** Preserve a clean `master` history. The PR description is the canonical commit message for the merge commit.

---

## 8. Licenses, attribution, and dependency hygiene

- **Project license:** MIT (`LICENSE` at repository root). Copyright © 2026 R. Mark Sharp.
- **Dependency licenses:** tracked on the [Software Bill of Materials](Software-Bill-of-Materials) page. Direct dependencies are predominantly MIT / BSD / Apache 2.0. `PyGithub` is LGPL-3.0; LGPL compliance is satisfied by Python's import mechanism allowing re-linking against modified library versions.
- **New dependencies:** prefer zero-new-dep solutions when the stdlib or existing deps can do the job (per learning #13). Each added dependency is a maintenance commitment — version conflicts, CI install time, and security-review surface all grow. If you need a new dep, include justification in the PR description.

---

## 9. Reporting issues

There is no public issue tracker actively in use for pre-UAT development — `gh issue list` is expected to return empty. Open work items are tracked in `BACKLOG.md` at the repository root. Once UAT begins, the tracker at `https://github.com/rmsharp/claims-model-starter/issues` will be the submission target.

For security-sensitive reports, please do not open a public issue. Contact the maintainer directly; see `README.md` for the current contact path.

---

## See also

- [Getting Started](Getting-Started) — install, first run, verify
- [Extending the Pipeline](Extending-the-Pipeline) — design-level extension surfaces and the tests that guard them
- [Changelog](Changelog) — phase-by-phase history of notable changes
- [Architecture Decisions](Architecture-Decisions) — the rationale behind each design choice you'd encounter while contributing
- [Software Bill of Materials](Software-Bill-of-Materials) — current dependency versions and licenses
