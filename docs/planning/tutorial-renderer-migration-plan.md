# Tutorial Renderer Migration — MkDocs + GitHub Pages

**Provenance:** Planning session (Session 65, 2026-04-20). Consumes BACKLOG item 2 ("Tutorial renderer: migrate to MkDocs"). Operator decisions captured in §3; technical claims in §4 were verified against live MkDocs + Material documentation at plan-write time (see §11 References).

**Status:** DRAFT. Implementation is **two separate sessions** (Phase 1 + Phase 2); this document is the deliverable of Session 65 and is not itself a code change.

---

## 1. Goal

Replace the current `pandoc` → standalone-HTML tutorial renderer (`scripts/render_tutorial.sh` → `docs/tutorial.html`) with a **MkDocs + Material** site generator that provides per-block copy buttons on code blocks. Phase 1 ships local generation; Phase 2 publishes the built site to GitHub Pages via CI so no rendered artifact is checked into the repo.

## 2. Problem

The current renderer (Session 54) wraps `pandoc` with inline CSS for readable output, but pandoc's HTML has no per-block copy button. Session 55 split every multi-command block into individually-copyable fenced blocks so readers could select-and-copy one command at a time, but the UX still requires text selection. MkDocs Material's `content.code.copy` feature renders a clickable copy button on every code block — closes the UX gap without further tutorial prose changes.

## 3. Operator decisions (from Session 65 pre-claim alignment)

| # | Decision | Resolution |
|---|----------|------------|
| 1 | **Which generator?** | **MkDocs** (with Material theme). |
| 2 | **Keep or retire `scripts/render_tutorial.sh`?** | **Retire.** One renderer, no CSS drift, no toolchain fork. GitHub's native `.md` view already shows copy buttons for quick-read cases. |
| 3 | **CI publication?** | **Yes, eventually.** No rendered artifact lives in the repo. Phase 1 = local build only (`site/` gitignored). Phase 2 = CI deploys to GitHub Pages. |
| 4 | **Wiki migration to same tool?** | **Deferred.** Wiki continues via `scripts/publish_wiki.sh` (Session 64). Out of scope for this plan. |

## 4. Technical claims (verified 2026-04-20)

| Claim | Source |
|-------|--------|
| Material's copy button is enabled via `theme.features: [content.code.copy]` | https://squidfunk.github.io/mkdocs-material/reference/code-blocks/ |
| Minimum Material version: 9.0.0 | same |
| MkDocs `exclude_docs:` directive exists, uses `.gitignore` pattern format, added in MkDocs 1.5 | https://www.mkdocs.org/user-guide/configuration/ |
| `mkdocs gh-deploy` uses `ghp-import`, pushes build output to `gh-pages` branch | https://www.mkdocs.org/user-guide/deploying-your-docs/ |

## 5. Scope

### In scope (Phase 1)

- New `mkdocs.yml` at repo root.
- New `docs` optional-dependency group in `pyproject.toml` (mkdocs + mkdocs-material).
- Delete `scripts/render_tutorial.sh`.
- `.gitignore` — remove `docs/tutorial.html` line (obsolete), add `/site/`.
- Verify `mkdocs build` + `mkdocs serve` produce the expected single-page site with copy buttons.
- Update any non-historical prose that points contributors at `render_tutorial.sh` (none found; see §6).

### In scope (Phase 2)

- New `.github/workflows/publish-tutorial.yml` that runs `mkdocs gh-deploy` on push to `master`.
- GitHub Pages enablement for `rmsharp/claims-model-starter` repo (source: `gh-pages` branch).
- Update tutorial + README (if applicable) to point readers at the published URL.
- BACKLOG item 2 removed per Learning #26 at Phase 2 close.

### Out of scope (both phases)

- **Tutorial prose changes.** `docs/tutorial.md` stays put. Content is not rewritten.
- **Wiki migration.** `docs/wiki/claims-model-starter/*.md` continues via `scripts/publish_wiki.sh` (Session 64).
- **Other docs migrations.** `docs/methodology/`, `docs/planning/`, `docs/architecture-history/`, `docs/style/` do NOT become MkDocs pages.
- **Custom theming beyond copy button.** Use Material defaults. No logo, no color customization, no extra plugins. If the published site needs branding later, a separate session handles it.

## 6. Evidence-based inventory (grep at plan-write time, 2026-04-20)

Patterns: `render_tutorial\.sh`, `tutorial\.html`, `docs/tutorial\.md`, `pandoc`, `mkdocs`, `MkDocs`.

### Files to MODIFY or DELETE in Phase 1

| File | Line(s) | Current content | Phase 1 action |
|------|---------|-----------------|----------------|
| `scripts/render_tutorial.sh` | whole file | pandoc wrapper, 100 lines | **DELETE** |
| `.gitignore` | 21 | `docs/tutorial.html` | **REPLACE** line with `/site/` |
| `pyproject.toml` | `[project.optional-dependencies]` | `agents`, `ui`, `dev` groups exist | **ADD** new `docs` group |
| **NEW** `mkdocs.yml` | N/A | (does not exist) | **CREATE** — see §7 for proposed content |

### Files that REFERENCE the renderer but should NOT change

| File | Line(s) | Reason to leave alone |
|------|---------|----------------------|
| `CHANGELOG.md` | 20, 22, 27, 157, 158, 161, 165, 167, 168, 181, 194, 511, … | Append-only historical record (Learning #32). Historical sessions correctly describe the state at the time. |
| `SESSION_NOTES.md` | 32, 33, 36, 49, 57, 170, 240, 1396ff, 1522, 1545, 1562, 1691, 1693, … | Historical session records (Learning #32). |
| `docs/wiki/claims-model-starter/Evolution.md` | 211 | Session 45 BACKLOG snapshot (historical record per `PROJECT_CONVENTIONS.md §1`). Learning #32 — freshness-tracked but historical entries stay. |
| `BACKLOG.md` | 8 | The MkDocs-migration item itself. Removed at **Phase 2** close per Learning #26 (delete on completion, don't flip). Remains during Phase 1. |
| `scripts/run_pipeline.py` | 9 | Docstring references `docs/tutorial.md` (the source file, unchanged). No renderer reference. |
| `docs/tutorial.md` | — | The source file. Stays put. No renderer references inside. |
| `README.md` | — | No matches for `render_tutorial`, `tutorial.html`, `mkdocs`, `MkDocs`. |

### Confirmed absent (zero hits)

- No `mkdocs.yml` anywhere in the repo.
- No `docusaurus.config.js` anywhere in the repo.
- No `site/` directory (will be created by `mkdocs build`).

**Grep inventory completeness:** The patterns above cover the script name, output file, source file, underlying tool, and both candidate successors. Further implementation-time greps should re-run these patterns to catch any drift since plan-write time.

## 7. Proposed `mkdocs.yml` (starting point)

```yaml
site_name: Model Project Constructor — Tutorial
site_description: Walkthrough of the multi-agent pipeline from intake interview to initial model website
site_url: https://rmsharp.github.io/claims-model-starter/
repo_url: https://github.com/rmsharp/claims-model-starter
repo_name: rmsharp/claims-model-starter

docs_dir: docs
site_dir: site

# docs/ contains non-site subdirs; exclude all except tutorial.md.
# Pattern: .gitignore format (MkDocs >= 1.5).
exclude_docs: |
  /methodology/
  /planning/
  /architecture-history/
  /style/
  /wiki/

nav:
  - Tutorial: tutorial.md

theme:
  name: material
  features:
    - content.code.copy
```

**Design choices worth flagging for the implementer:**

- **`exclude_docs:` uses explicit directory list rather than a `*` + `!tutorial.md` whitelist.** Rationale: if a new file is added to `docs/` later, the implementer sees MkDocs start including it and adds an explicit exclusion — a maintainable failure mode. A `*` whitelist silently hides anything new, which is fragile.
- **No `plugins:` block.** MkDocs' built-in search is on by default. Adding plugins is out of scope.
- **No custom CSS.** Material defaults match (or exceed) the readability of `render_tutorial.sh`'s inline CSS.
- **`site_url` named for GitHub Pages default.** If Phase 2 ends up publishing elsewhere, the implementer updates this.

## 8. Phase 1 — Local MkDocs setup

**Deliverable:** A `mkdocs build` run from a clean checkout produces a single-page `site/` containing `tutorial.md` with copy buttons on every code block, and nothing else.

### Work items

1. **Retire the pandoc wrapper.**
   - `git rm scripts/render_tutorial.sh`.
   - `.gitignore`: remove line 21 (`docs/tutorial.html`); add line `/site/` in its place.
2. **Add `docs` optional dependency group to `pyproject.toml`:**
   ```toml
   [project.optional-dependencies]
   docs = [
       "mkdocs>=1.5",
       "mkdocs-material>=9.0",
   ]
   ```
   Rationale for explicit version floors: MkDocs 1.5 for `exclude_docs:`; Material 9.0 for `content.code.copy`.
3. **Write `mkdocs.yml`** per §7 at repo root.
4. **Local verification:**
   - `uv sync --all-extras` to install (see note below).
   - `uv run mkdocs build --strict` — must exit 0 with no warnings. `--strict` catches missing cross-references, orphaned excluded files, etc.

   **`uv sync` note (Session 66 erratum):** `uv sync --extra docs` is *replacing*, not *additive* — running it on a dev environment that already has `agents` / `ui` / `dev` extras installed will **remove** those extras. Use `uv sync --all-extras` locally (or enumerate: `uv sync --extra docs --extra agents --extra ui --extra dev`). The Phase 2 CI workflow (§9) intentionally keeps `uv sync --extra docs` because CI runs in a fresh container where there are no pre-installed extras to remove.
   - Inspect `site/index.html` or `site/tutorial/index.html` (whichever MkDocs generates for a single-page nav) in a browser. Confirm copy buttons appear on code blocks.
   - `uv run mkdocs serve` — confirm live-reload serves at `http://127.0.0.1:8000`.
5. **Update contributor guidance (if any found).**
   - Session 65 grep (see §6) found no non-historical references to `render_tutorial.sh` in README or other user-facing docs. Implementer re-verifies at Phase 1 open: `grep -rn "render_tutorial" README.md docs/tutorial.md`. Zero expected.
6. **Gate verification:**
   - `pytest`, `ruff`, `mypy` — all unchanged (no `src/`, `packages/`, or `tests/` files touched). Pre-commit state per Session 64 close-out: pytest 576/576 @ 97.28%; ruff clean; mypy 0 issues in 61 files.

### Phase 1 completion criteria

- [ ] `scripts/render_tutorial.sh` deleted.
- [ ] `.gitignore` updated: `docs/tutorial.html` removed, `/site/` added.
- [ ] `mkdocs.yml` exists at repo root and matches §7 (modulo implementer-validated tweaks).
- [ ] `pyproject.toml` has `[project.optional-dependencies].docs`.
- [ ] `uv run mkdocs build --strict` succeeds from a clean checkout with zero warnings.
- [ ] `site/` directory is gitignored; `git status` clean after a build.
- [ ] Copy buttons visually confirmed in a browser on at least two distinct code blocks.
- [ ] pytest/ruff/mypy still at Session 64 numbers (no regression).
- [ ] CHANGELOG Phase 1 entry; BACKLOG item 2 **not yet removed** (Phase 2 removes it).

### Phase 1 verification commands

```bash
# Clean state
git status --porcelain | grep -c . # expect 0 after commit
ls scripts/render_tutorial.sh      # expect "No such file"

# Config + build
grep -c "content.code.copy" mkdocs.yml              # expect 1
uv sync --all-extras                                 # see §8.4 note — NOT --extra docs (that removes other extras)
uv run mkdocs build --strict                        # expect exit 0, no warnings
test -f site/tutorial/index.html || test -f site/index.html  # expect 0

# Gates unchanged
uv run pytest -q                                    # expect 576/576
uv run ruff check src/ tests/ packages/ scripts/    # expect clean
uv run mypy                                         # expect 0 issues
```

**Session boundary:** This phase is one session. Close out when all criteria above are checked and verified. CI publication is a separate session.

## 9. Phase 2 — CI publication to GitHub Pages

**Deliverable:** A GitHub Actions workflow that builds and publishes the tutorial to `https://rmsharp.github.io/claims-model-starter/` on every push to `master`. No rendered site in the repo.

### Work items

1. **Write `.github/workflows/publish-tutorial.yml`:**
   ```yaml
   name: Publish Tutorial
   on:
     push:
       branches: [master]
       paths:
         - docs/tutorial.md
         - mkdocs.yml
         - .github/workflows/publish-tutorial.yml
         - pyproject.toml
   permissions:
     contents: write  # gh-deploy pushes to gh-pages
   jobs:
     publish:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v3
         - run: uv sync --extra docs
         - run: uv run mkdocs gh-deploy --force --clean
   ```
   **Design choices worth flagging:**
   - **`paths:` filter** — workflow only runs when tutorial-relevant files change, not on every push. Saves CI minutes.
   - **`permissions: contents: write`** — required for `mkdocs gh-deploy` to push to `gh-pages` branch using the default `GITHUB_TOKEN`.
   - **`--force`** — required because `gh-pages` branch history is owned by the tool, not preserved commit-by-commit.
   - **`setup-uv`** — matches the project's existing CI pattern. Implementer verifies current CI action version at Phase 2 open.
2. **Enable GitHub Pages** in `rmsharp/claims-model-starter` settings: Source = `gh-pages` branch, `/ (root)`. This is a one-time GitHub web-UI action — cannot be done via the workflow. Document the click-path in the Phase 2 handoff.
3. **Update `docs/tutorial.md` (one-liner)** or `README.md` with a "published at" pointer. Candidate wording: "Published rendering: https://rmsharp.github.io/claims-model-starter/". Scope-sensitive — the operator can reject this if tutorial prose is too stable to touch.
4. **Remove BACKLOG item 2** per Learning #26 (delete the line; do not flip to `[x]`).
5. **First push verification:**
   - Trigger the workflow (push a trivial change or manual dispatch).
   - Workflow succeeds; `gh-pages` branch has the built site; Pages URL returns HTTP 200 with copy buttons visible.

### Phase 2 completion criteria

- [ ] `.github/workflows/publish-tutorial.yml` exists and matches §9 workflow shape (modulo implementer-validated tweaks).
- [ ] GitHub Pages is enabled on the repo, serving the `gh-pages` branch.
- [ ] Workflow has run successfully at least once; `gh-pages` branch exists; Pages URL reachable.
- [ ] Copy buttons visible on the live site.
- [ ] Tutorial/README updated (if scope-approved) with the published URL.
- [ ] BACKLOG item 2 line removed.
- [ ] CHANGELOG Phase 2 entry.
- [ ] pytest/ruff/mypy still at Session 64 numbers (no regression).

### Phase 2 verification commands

```bash
# Workflow file exists and is valid
test -f .github/workflows/publish-tutorial.yml
# GitHub Pages URL reachable + has copy button marker
curl -sf https://rmsharp.github.io/claims-model-starter/ | grep -q 'md-clipboard'

# Workflow run succeeded
gh run list --workflow publish-tutorial.yml --limit 1 --json conclusion --jq '.[0].conclusion'
# expect "success"

# gh-pages branch exists
git ls-remote --heads origin gh-pages | grep -c .
# expect 1

# BACKLOG item removed
grep -c "migrate to MkDocs" BACKLOG.md
# expect 0
```

**Session boundary:** Separate session from Phase 1. Do not bundle. The "commit Phase 1" and "commit Phase 2" hashes must be in different sessions' commit logs.

## 10. Open considerations (resolve in implementation sessions)

1. **Does the site's URL path structure match `docs/tutorial/index.html` (Material's default for a single-page site) or `docs/index.html` (if `tutorial.md` is renamed to `index.md`)?** Implementer verifies the first `mkdocs build` output and updates `site_url` + Pages configuration accordingly. Plan's §7 does NOT rename `tutorial.md` to `index.md` — consistency with the source-file convention matters more than URL aesthetics.

2. **Does the Material default theme collide with any accessibility constraints?** Out-of-the-box Material is WCAG-AA compliant by default. If the operator has a specific accessibility requirement not yet mentioned, Phase 1's "visual check" surfaces it.

3. **CI-side dependency caching.** The Phase 2 workflow does not cache `uv` dependencies. First run installs cleanly; subsequent runs re-install. Acceptable for low-frequency tutorial updates (runs only on `docs/tutorial.md` change). Optimize only if CI minute cost is material.

4. **Published URL lifetime.** GitHub Pages URLs are public and persistent. If the tutorial eventually gets sensitive content, Phase 2 operator revisits publication scope. Current tutorial content (walkthrough of a public open-source pipeline) has no sensitivity concern.

5. **Plan deltas if the operator later reverses decision 3 (no CI publish).** Phase 2 is skipped; Phase 1 stands alone. The `mkdocs.yml` in Phase 1 still includes `site_url:` — update that line if publication target changes.

## 11. Risks

| # | Risk | Mitigation |
|---|------|------------|
| 1 | **Material theme upgrade breaks rendering.** | `pyproject.toml` pins `mkdocs-material>=9.0`; version floor is the Material 9-series. A future Material 10 would be a separate review pass. Implementer may choose a tighter ceiling (`<10`) for safety. |
| 2 | **`exclude_docs:` misconfiguration leaks internal docs to the site.** | Phase 1 verification includes `test -f site/methodology/index.html` (expect `No such file or directory`). If that test fails, `exclude_docs:` pattern is wrong — implementer iterates. |
| 3 | **GitHub Pages URL mismatch with `site_url`.** | Canonical URL embedded in HTML may differ from actual Pages URL if the repo is renamed. `site_url:` is a one-line fix; rediscovery cost is low. |
| 4 | **`gh-deploy` dirty-state error.** | `mkdocs gh-deploy` refuses to deploy with uncommitted changes. Workflow runs after checkout with no staged changes, so this is a non-issue in CI. Locally, a contributor running `mkdocs gh-deploy` themselves would hit this — documented in Phase 2 tutorial update. |
| 5 | **CI workflow has wrong permissions.** | `permissions: contents: write` in the YAML is the canonical setting. Implementer verifies against the GitHub Actions docs at Phase 2 open. |
| 6 | **Pandoc users lose the quick `render_tutorial.sh` path.** | Mitigation: GitHub renders `tutorial.md` natively with copy buttons, covering the "quick glance" case. Contributors who want local HTML can install the MkDocs toolchain (one `uv sync --extra docs`) or re-introduce a personal pandoc script outside the repo. Operator accepted this tradeoff in decision 2. |

## 12. Change summary by phase

### Phase 1 (one session)

- **Files created:** `mkdocs.yml`
- **Files deleted:** `scripts/render_tutorial.sh`
- **Files modified:** `.gitignore` (1 line), `pyproject.toml` (+1 optional-deps group), `CHANGELOG.md` (+ Phase 1 entry), `SESSION_NOTES.md` (close-out)
- **BACKLOG.md:** unchanged (item 2 still open; Phase 2 removes it)
- **CI:** unchanged
- **Runtime code:** unchanged
- **Tests:** unchanged

### Phase 2 (one session)

- **Files created:** `.github/workflows/publish-tutorial.yml`
- **Files modified:** `BACKLOG.md` (−1 line, item 2 removed), `CHANGELOG.md` (+ Phase 2 entry), `SESSION_NOTES.md` (close-out); optionally `docs/tutorial.md` or `README.md` (+1 URL pointer)
- **GitHub repo:** Pages enabled (one-time web-UI click); `gh-pages` branch created on first workflow run
- **Runtime code:** unchanged
- **Tests:** unchanged

## 13. Non-goals (explicit)

- Do **not** rewrite any tutorial prose.
- Do **not** migrate the wiki.
- Do **not** migrate other `docs/` subdirectories (methodology, planning, architecture-history, style).
- Do **not** introduce plugins beyond what Material ships by default.
- Do **not** customize Material's color palette, logo, or CSS. Defaults suffice.
- Do **not** couple the GitHub Pages publish to wiki publish (they are distinct mechanisms per operator decision 4).

## 14. References

- **Source BACKLOG entry:** `BACKLOG.md:8`.
- **Tutorial source:** `docs/tutorial.md` (650 lines; 33 fenced code blocks; 12 `##` sections).
- **Current renderer:** `scripts/render_tutorial.sh` (100 lines; pandoc wrapper; filed Session 54; CHANGELOG §2026-04-19).
- **Adjacent plan — wiki publish:** `scripts/publish_wiki.sh` (Session 64). Mechanism stays separate per decision 4.
- **MkDocs docs (verified 2026-04-20):**
  - Config reference (exclude_docs, MkDocs 1.5+): https://www.mkdocs.org/user-guide/configuration/
  - Deployment (gh-deploy → gh-pages): https://www.mkdocs.org/user-guide/deploying-your-docs/
- **Material docs (verified 2026-04-20):**
  - Code blocks (content.code.copy, Material 9+): https://squidfunk.github.io/mkdocs-material/reference/code-blocks/
- **Session history:**
  - Session 54 (render_tutorial.sh): CHANGELOG §2026-04-19; SESSION_NOTES Session 54 block.
  - Session 55 (per-block splits): CHANGELOG §2026-04-19; SESSION_NOTES Session 55 block.
  - Session 64 (wiki publish — distinct mechanism): CHANGELOG §Unreleased top.
- **Methodology references:**
  - Planning Sessions discipline: `SESSION_RUNNER.md` Phase 2 "Planning Sessions".
  - Learnings load-bearing for this plan: #1 (plan-mode output is a draft), #9 (single-document shared invariants), #17 (methodology README authoritative — `PROJECT_CONVENTIONS.md §1` for wiki discipline), #19 (grep inventory evidence), #26 (BACKLOG removal on completion), #32 (historical-record files excluded from find-and-replace).

---

**End of plan.** Implementation Session 66 (or later) executes Phase 1. Phase 2 follows in a third session. No implementation actions are authorized by this document alone.
