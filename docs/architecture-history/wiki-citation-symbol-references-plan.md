> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-11 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# Plan: Migrate wiki `file:line` citations to grep-locatable symbol references

**Status:** DRAFT — this is a **planning deliverable**. It is not implemented. Implementation happens in separate sessions, one phase each (FM #18/#19).
**Created:** 2026-06-10 (Session 137)
**Author:** Session 137
**Approach:** **Symbol references** — chosen by the operator via `AskUserQuestion` over the two alternatives in audit §8 (publish-time line-number generation; hybrid). See §2.
**Source of the problem:** `docs/audits/2026-06-10-wiki-vs-code-accuracy-audit.md` §8 ("Recurrence Prevention").
**Evidence base:** read-only inventory workflow `wf_22ad61bd-50b` (16 `Explore` agents: per-page inventory → adversarial verify), 2026-06-10, run against HEAD. Full result archived at the run's transcript dir; the complete 166-row inventory is **Appendix A** of this document.

---

## 1. Problem & root cause

The single largest source of recurring wiki↔code drift is **hardcoded `file:line` citations** ("verbatim from `anthropic_client.py:35-51`"). A citation is wrong the moment the cited file gains a line above the cited range. The Session 134 audit traced the bulk of its low-severity findings to exactly this: O3's insertion of `REPO_PLATFORMS` shifted citations across `Security-Considerations`, `Worked-Examples`, and `Intake-Interview-Design` by tens of lines (audit §1, §8).

**This plan's inventory proves the model is fragile even at rest.** All 79 audit findings were remediated in Sessions 135–136 (line numbers re-verified against HEAD). Yet a fresh adversarial pass *days later* found **31 of 166 occurrences already need correction**, and **13 of those have a line range that points at the wrong (or an absent) named construct** — not merely off-by-a-few. Examples the verifier caught:

- `src/model_project_constructor/agents/intake/anthropic_client.py:150-162` is cited as `next_question` — but those lines are the `_DRAFT_REPORT_INSTRUCTIONS` constant; `next_question` is at 199-220.
- `anthropic_client.py:121-128` is cited as `SYSTEM_GOVERNANCE` — but that range is the end of `GOVERNANCE_FRAMEWORKS`; `SYSTEM_GOVERNANCE` is at 128-135.
- `src/model_project_constructor/schemas/v1/intake.py:67-75` is cited as `GovernanceMetadata` — that range is `ValueMeasurementPlan`; `GovernanceMetadata` is at 78-85.
- `Schema-Reference` class citations are off by 9 (`QualityCheck`, `Datasheet`), 19 (`ModelSolution`), and 43 (`GovernanceMetadata`) lines.
- `Evolution.md` cites `GITLAB_DEFAULT_HOST_URL` (`cli.py:39`) — a symbol that **no longer exists** (refactored into `REPO_PLATFORMS`).

**Scale:** 166 citation occurrences across 8 wiki pages.

| Page | Occurrences | clean | multi | non_symbol | verify-flagged |
|------|-------------|-------|-------|-----------|----------------|
| Extending-the-Pipeline.md | 38 | 32 | 2 | 4 | 6 |
| Security-Considerations.md | 29 | 13 | 6 | 10 | 16 |
| Intake-Interview-Design.md | 29 | 24 | 3 | 2 | 7 |
| Schema-Reference.md | 29 | 26 | 1 | 2 | 7 |
| Worked-Examples.md | 19 | 7 | 4 | 8 | 0 |
| Evolution.md | 12 | 2 | 8 | 2 | 3 |
| Contributing.md | 8 | 0 | 0 | 8 | 3 |
| Changelog.md | 2 | 1 | 0 | 1 | 1 |
| **Total** | **166** | **105** | **24** | **37** | **43** |

> The 166 count is the authoritative live read; a surface `grep` undercounts (it misses citations split across prose vs. tables and bare-filename forms). Each occurrence is a separate edit site.

---

## 2. Decision: symbol references (and why)

Audit §8 offered two options "in increasing robustness." The operator chose **symbol references** via `AskUserQuestion` (Session 137). The alternatives and the rationale:

| Option | What it is | Pros | Cons | Verdict |
|--------|-----------|------|------|---------|
| **Symbol references** *(chosen)* | Replace `path.py:35-51` with `` `SYMBOL` in `path.py` `` — a grep-locatable name | Pure docs edit; **no new tooling**; the rsync source↔clone **0-drift parity model is untouched**; survives all line drift; the migration is self-correcting (re-deriving fixes the 31 already-wrong citations) | Loses exact line ranges (the symbol name is the anchor); can still drift on symbol **rename** (rare; `grep` finds it, unlike silent line drift) | **Adopt** |
| Publish-time generation | A `{{lines:path#symbol}}` transclusion resolved to live line numbers by an extended publish hook | Most robust — citations literally cannot drift; could inline live code | **Breaks the source↔clone 0-drift invariant** every session has relied on (published ≠ source); builds a resolver + hook changes; in-repo readers see `{{...}}` placeholders | Rejected (over-engineered for a docs problem; YAGNI; parity cost) |
| Hybrid | Symbols now, publish-time gen later if renames recur | Keeps the robustness path open | Two-stage; Phase 2 may never be needed | Folded in: §7's Phase 6 guard makes renames visible, so the gen path can be revisited only if data warrants |

**Why symbol references is the right call here:** the cons are minor and the pros directly preserve what the project values. Symbol renames are far rarer than line drift, and unlike line drift they are *loud* — a `grep` for the old symbol returns nothing, which the recurrence guard (§6) turns into a failing test. The chosen approach also needs **zero code** in the publish path, so the well-understood `rsync`-parity publish model stays exactly as-is.

---

## 3. The citation convention (what the migration applies)

Every migrated citation drops the `:line` suffix and names a **grep-locatable anchor**. Use the **full repo-relative path** in every case — this also kills the bare-filename ambiguity the verifier flagged repeatedly (e.g. `anthropic_client.py` exists under `agents/intake/`, `agents/data/`, *and* `packages/data-agent/`).

| Cited thing | Convention | Example |
|-------------|-----------|---------|
| Class / function / method / module constant | `` `Symbol` in `full/path.py` `` | `` `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py` `` |
| Pydantic / dataclass **field** | `` `Model.field` in `full/path.py` `` | `` `EstimatedValue.annual_impact_usd_low` in `src/model_project_constructor/schemas/v1/intake.py` `` |
| **Multi-symbol span** (range covers several constructs) | Anchor to the **primary** symbol; name the others in prose if load-bearing | `` `RepoClientError` and `RepoNameConflictError` in `.../website/protocol.py` `` |
| **Config file** (`pyproject.toml`) | The TOML **table path** in backticks (grep-locatable structural anchor), full path, no line | `` `[tool.ruff.lint]` in `pyproject.toml` `` |
| **CI workflow** (`ci.yml`) | The **job or step name** in backticks, full path, no line | `` the `lint` job in `.github/workflows/ci.yml` `` |
| **Test module** | Full path, **no line** (the module IS the anchor) | `` `tests/schemas/test_envelope_and_registry.py` `` |
| **Markdown / doc file** (`OPERATIONS.md`) | Full path + **section heading** if useful, no line | `` `OPERATIONS.md` §5 `` |
| **Module docstring** | Describe it; no line | `` the module docstring in `src/.../schemas/registry.py` `` |
| Inline verification command (e.g. a `grep -R ...` example) | Not a citation — **leave unchanged** | — |

**Hard rule for the executor:** re-derive every symbol from the **live code at execution time** — do not trust the `current` line numbers in Appendix A, because 31 of them are already wrong (§1). Appendix A's `proposed_replacement` and the verifier's `corrected_replacement` are *starting points*; confirm each symbol exists and `grep -rn '<symbol>' src packages` locates it before writing.

---

## 4. Evidence-based inventory

The complete per-occurrence inventory — page, wiki line, current citation, resolved file, classification, proposed replacement, and the adversarial verdict — is **Appendix A** (166 rows). It is the migration checklist: a phase is done when every Appendix-A row for its pages is migrated and the page contains no `path:line` strings.

Classification totals: **105 clean** (map to one symbol) · **24 multi** (span several; anchor to primary) · **37 non_symbol** (config / test / doc / docstring / arbitrary region — use the §3 alternative-anchor rules).

Verify-flag split (43 total): **31 need real correction** (the proposed symbol or its location was wrong — 13 of these because the *current* line range already mis-points), **12 are non-symbol file references that are correct as-is** (the verifier marks them "not grep-locatable" only because there is no code symbol — a file/section anchor is the right answer per §3).

Non-symbol breakdown (37): test modules 10 · other no-symbol code regions 10 · module docstrings 6 · `pyproject.toml` 6 · CI YAML 3 · markdown docs 2.

---

## 5. Here be dragons

Not all pages are equally tractable. Where the executor must slow down:

1. **Security-Considerations.md (16/29 flagged) — highest risk.** Heavy use of **bare filenames** (`cli.py`, `db.py`, `logging.py`, `github_adapter.py`) that resolve to *different files* in intake vs. data-agent vs. website. The verifier disambiguated each (see Appendix A / its verdicts), but the executor must confirm the path before naming the symbol. Also contains non-citations: a `grep -R "ghp_|glpat_|sk-ant-|..."` example command — **leave it alone**.

2. **Evolution.md — DO NOT auto-migrate in the mechanical phases.** The page's own banner (`Evolution.md:3`, `:183`) declares it a **user-triggered full-rewrite** document; the audit explicitly says "Do NOT auto-rewrite §8." It also cites `GITLAB_DEFAULT_HOST_URL`, a symbol that no longer exists. Treat Evolution as **Phase 5: deferred** — migrate its citations only as part of its next operator-triggered rewrite, or as an explicitly approved exception. Most of its 12 occurrences are `multi` spans anyway.

3. **Contributing.md — 0 code symbols.** All 8 occurrences are config/CI/test references. This page exercises the §3 alternative-anchor conventions exclusively (TOML table paths, CI job names, test-module paths). Good page to **ratify the non-symbol conventions** on, because there is no code-symbol work to distract.

4. **The 13 already-mis-pointing citations** (§1). These are load-bearing: a naive "keep the line number, add the symbol name" migration would *preserve a wrong line number*. The convention (§3) drops the line entirely, so re-deriving the symbol is mandatory and self-correcting. The verifier's `corrected_replacement` for each is in Appendix A — but re-confirm against live code.

5. **`multi` spans (24).** A range like `protocol.py:69-78` covers two exception classes. Anchor to the primary symbol; if the prose genuinely needs both, name both (§3). Do not silently drop the second symbol if the sentence depends on it.

6. **Residual drift risk after migration.** Symbol *renames* still break a citation — but visibly (grep returns nothing), which the §6 guard catches in CI. This is strictly better than silent line drift, and is the trigger that would justify revisiting publish-time generation (§2) if renames ever become frequent.

---

## 6. Recurrence guard (the actual "prevention")

Migrating the existing 166 is a one-time sweep. **Prevention** requires a structural check so new `file:line` citations cannot silently reappear. Add a lightweight test to the constructor's own suite (it tests the docs in-repo, runs in CI):

- **New test** `tests/test_wiki_no_line_citations.py`: scan `docs/wiki/claims-model-starter/*.md` for the pattern `[\w./-]+\.(py|toml|ya?ml):\d+(-\d+)?` and **fail** with the offending file:line:match if any are found.
- **Scope the regex** to avoid false positives: require a code-ish extension immediately before `:digits`. This excludes version strings (`3.11`), times, and prose colons. Spot-check against the migrated pages before committing the test (it must pass once the migration is done).
- **Transition allowlist:** while pages are migrated incrementally, the test takes an allowlist set (pages not yet migrated, plus `Evolution.md` until its rewrite). Each migration phase **removes its pages from the allowlist** as part of that phase's DONE criteria. When the allowlist is empty, the invariant is fully enforced.
- **Optional, lower priority:** also emit a warning from `scripts/publish_wiki.sh` on the same pattern, so a stray citation is caught at publish time even if tests are skipped. The test is the primary mechanism; the hook warning is belt-and-suspenders.

This converts "drifted citation" from a recurring manual-sweep chore into a CI-enforced invariant — which is the whole point of §8.

---

## 7. Phased execution plan

Each phase is **one session**. Each ends with its verification passing and a close-out. The clean code-symbol pages (Phases 1–2) MAY be batched into fewer sessions by an executor using the Session-136-style author→verify→apply workflow (read-only `Explore` stages — Candidate #102), **provided** each page still independently passes its grep check and the work is diff-reviewed before publish (Candidate #103). Security and Evolution each warrant a dedicated session.

> **Publish note:** every phase edits `docs/wiki/claims-model-starter/`, which **auto-publishes to the live GitHub Wiki** via the `post-commit` hook (Learning #40). Confirm publish intent before committing each phase, exactly as Sessions 135–136 did.

### Phase 0 — Ratify the convention (no edits)
- **DONE:** operator confirms §3's conventions, especially the non-symbol anchor forms (TOML table path, CI job name, test-module path, doc-file §section). Resolve any "anchor style" preferences here so later phases are mechanical.
- **Verification:** §3 table reflects the agreed forms.
- **Session boundary:** can be folded into the start of Phase 1 if the operator is satisfied with §3 as written.

### Phase 1 — Schema-Reference (29) + Changelog (2) + Extending-the-Pipeline (38) — clean code symbols
- **What:** the highest-clean-ratio pages; validates the code-symbol convention at volume. Fixes the Schema-Reference off-by-9/19/43 citations and the Changelog off-by-2 by re-deriving.
- **DONE:** all Appendix-A rows for these 3 pages migrated; each page re-derived from live code; diff-reviewed; published.
- **Verification:** `grep -rnE '[A-Za-z0-9_./-]+\.(py|toml|ya?ml):[0-9]+' docs/wiki/claims-model-starter/{Schema-Reference,Changelog,Extending-the-Pipeline}.md` returns nothing; fences balanced; wiki publish parity 0-drift.
- **STOP. Close out.**

### Phase 2 — Intake-Interview-Design (29) + Worked-Examples (19)
- **What:** intake-graph symbols + fixture-key references (Worked-Examples has 8 non_symbol fixture keys — apply the anchor convention). Fixes the `SYSTEM_GOVERNANCE` (121-128→128-135) and nested-function (`plan_next_question`) mis-points.
- **DONE / Verification:** as Phase 1, for these 2 pages.
- **STOP. Close out.**

### Phase 3 — Security-Considerations (29) — the hot spot
- **What:** dedicated session. Disambiguate every bare filename to a full path before naming the symbol; fix the `next_question` (150-162→199-220) mis-point; leave the inline `grep -R` example command untouched; apply doc-file (`OPERATIONS.md` §section) and module-docstring conventions.
- **DONE / Verification:** as Phase 1, for this page. Extra care: confirm each disambiguated path with `grep`/glob.
- **STOP. Close out.**

### Phase 4 — Contributing (8) — non-symbol anchors only
- **What:** the pure config/CI/test page. Apply TOML table paths, CI job names, test-module paths. Refine the three flagged TOML ranges (`[project.optional-dependencies]` 17-44, `[tool.ruff]`/`[tool.ruff.lint]`, `[tool.coverage.*]`).
- **DONE / Verification:** as Phase 1, for this page.
- **STOP. Close out.**

### Phase 5 — Evolution (12) — DEFERRED (here be dragons §5.2)
- **What:** do **not** migrate mechanically. Migrate Evolution's citations only inside its next **operator-triggered full rewrite**, honoring the page's stated discipline. Flag `GITLAB_DEFAULT_HOST_URL` as already-stale during that rewrite.
- **DONE:** either (a) operator triggers the rewrite and citations are migrated within it, or (b) operator approves an explicit exception to migrate now. Until then Evolution stays on the §6 allowlist.
- **STOP. Close out (or defer indefinitely per operator).**

### Phase 6 — Recurrence guard (capstone)
- **What:** add `tests/test_wiki_no_line_citations.py` per §6, with an allowlist that is empty except for any page deferred in Phase 5. Optionally add the publish-hook warning.
- **DONE:** the test exists, passes against the migrated pages, and fails on a deliberately-injected `foo.py:10` (verify the guard actually guards). `uv run pytest tests/test_wiki_no_line_citations.py` green. Test count and CI updated.
- **Verification:** `uv run pytest -q` still green; new test present; injecting a fake citation makes it red.
- **STOP. Close out.**

**Phase count:** 1 planning (this) + up to 6 execution = 7 sessions minimum, fewer if clean pages are workflow-batched. Do not bundle a migration phase with the guard phase (FM #18).

---

## 8. Verification commands (reference)

```bash
# Per-page: confirm no line citations remain on a migrated page
grep -rnE '[A-Za-z0-9_./-]+\.(py|toml|ya?ml):[0-9]+(-[0-9]+)?' docs/wiki/claims-model-starter/<Page>.md   # → no output

# Whole wiki: count remaining line citations (drops to 0 + allowlist as phases land)
grep -rhoE '[A-Za-z0-9_./-]+\.(py|toml|ya?ml):[0-9]+(-[0-9]+)?' docs/wiki/claims-model-starter/*.md | wc -l

# Confirm a proposed symbol is grep-locatable before using it
grep -rn '<Symbol>' src packages

# Fences still balanced on an edited page (must be even)
grep -c '```' docs/wiki/claims-model-starter/<Page>.md

# After migration: the guard test
uv run pytest tests/test_wiki_no_line_citations.py -q

# Publish parity (existing 0-drift check) still holds after each phase
scripts/publish_wiki.sh   # idempotent; "no changes to publish" when in parity
```

---

## 9. Load-bearing assumptions & risks

- **Appendix A's line numbers are a snapshot (2026-06-10, HEAD) and 31 are already wrong.** Symbol *names* are stable; re-derive lines/symbols at execution time. This is the single most important caveat for the executor.
- **The migration is the audit's own §8 recommendation** — but the audit's pointers can be wrong (Sessions 135–136 found the audit's fix pointers contained factual errors). Treat Appendix A and the verifier's corrections as proposals to re-verify (Learning #45, Candidate #103), not gospel.
- **Symbol renames remain a (rare, loud) drift vector.** The §6 guard makes them CI-visible; that visibility is the trigger to revisit publish-time generation (§2) only if renames prove frequent.
- **Non-symbol anchors** (TOML tables, CI job names) can themselves be renamed, but are far more stable than line numbers and are grep-locatable.
- **Evolution.md** must not be mechanically rewritten (§5.2).
- **Parity invariant preserved:** because this approach touches no publish code, the rsync source↔clone 0-drift model is unchanged; the only new automation is a read-only test (§6).

---

## Appendix A — Full inventory (166 occurrences)

Generated from inventory workflow `wf_22ad61bd-50b` (2026-06-10, HEAD). Columns: **Page** · **Wiki line** (approx) · **Current citation** · **Resolved file** · **Class** (clean/multi/non_symbol) · **Proposed replacement** · **Verdict** (✓ ok, or the verifier's correction). **Re-derive line numbers from live code at execution time — 31 rows below are already wrong (§1, §9).**


### Extending-the-Pipeline.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 11 | `src/model_project_constructor/schemas/envelope.py:20-33` | `src/model_project_constructor/schemas/envelope.py` | clean | `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py` | ✓ |
| 32 | `src/model_project_constructor/schemas/registry.py:26-32` | `src/model_project_constructor/schemas/registry.py` | clean | `REGISTRY` in `src/model_project_constructor/schemas/registry.py` | ✓ |
| 44 | `registry.py:39-58` | `src/model_project_constructor/schemas/registry.py` | clean | `load_payload` in `src/model_project_constructor/schemas/registry.py` | ✓ |
| 46 | `registry.py:7-13` | `src/model_project_constructor/schemas/registry.py` | non_symbol | module docstring in `src/model_project_constructor/schemas/registry.py` (lines 7-13 of file, after opening quotes) | **not-greppable** — Module docstring (non-symbol) — grep won't reliably locate it, but replacement text is accurate |
| 63 | `src/model_project_constructor/schemas/registry.py:26-32` | `src/model_project_constructor/schemas/registry.py` | clean | `REGISTRY` in `src/model_project_constructor/schemas/registry.py` | ✓ |
| 64 | `src/model_project_constructor/schemas/envelope.py:27-28` | `src/model_project_constructor/schemas/envelope.py` | clean | `HandoffEnvelope.source_agent` and `HandoffEnvelope.target_agent` fields in `src/model_project_constructor/schemas/envelope.py` | ✓ |
| 66 | `src/model_project_constructor/orchestrator/pipeline.py:51-53` | `src/model_project_constructor/orchestrator/pipeline.py` | clean | `IntakeRunner`, `DataRunner`, `WebsiteRunner` type aliases in `src/model_project_constructor/orchestrator/pipeline.py` | ✓ |
| 74 | `pipeline.py:60-65` | `src/model_project_constructor/orchestrator/pipeline.py` | clean | `PipelineStatus` in `src/model_project_constructor/orchestrator/pipeline.py` | ✓ |
| 84 | `src/model_project_constructor/agents/website/protocol.py:42-66` | `src/model_project_constructor/agents/website/protocol.py` | clean | `RepoClient` in `src/model_project_constructor/agents/website/protocol.py` | ✓ |
| 106 | `protocol.py:19-31` | `src/model_project_constructor/agents/website/protocol.py` | clean | `ProjectInfo` in `src/model_project_constructor/agents/website/protocol.py` | ✓ |
| 108 | `protocol.py:34-39` | `src/model_project_constructor/agents/website/protocol.py` | clean | `CommitInfo` in `src/model_project_constructor/agents/website/protocol.py` | ✓ |
| 112 | `protocol.py:69-78` | `src/model_project_constructor/agents/website/protocol.py` | multi | `RepoClientError` and `RepoNameConflictError` in `src/model_project_constructor/agents/website/protocol.py` | ✓ |
| 140 | `src/model_project_constructor/agents/website/governance_templates.py` | `src/model_project_constructor/agents/website/governance_templates.py` | multi | `render_gitlab_ci` and `render_github_actions_ci` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 140 | `governance_templates.py:834-837` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_governance_files` in `src/model_project_constructor/agents/website/governance_templates.py` (ci_platform dispatch) | ✓ |
| 144 | `src/model_project_constructor/orchestrator/config.py` | `src/model_project_constructor/orchestrator/config.py` | clean | `REPO_PLATFORMS` in `src/model_project_constructor/orchestrator/config.py` | ✓ |
| 144 | `config.py:56` | `src/model_project_constructor/orchestrator/config.py` | clean | `PlatformSpec.adapter_factory` in `src/model_project_constructor/orchestrator/config.py` | **FIX** — `PlatformSpec` dataclass in `src/model_project_constructor/orchestrator/config.py` (adapter_factory field at line 56) |
| 144 | `scripts/run_pipeline.py:295` | `scripts/run_pipeline.py` | clean | `build_website_runner` in `scripts/run_pipeline.py` (adapter factory call) | ✓ |
| 144 | `agents/website/cli.py:177` | `src/model_project_constructor/agents/website/cli.py` | clean | `run` command in `src/model_project_constructor/agents/website/cli.py` (adapter factory call) | ✓ |
| 146 | `config.py:109` | `src/model_project_constructor/orchestrator/config.py` | clean | `assert_vocab_parity` call in `src/model_project_constructor/orchestrator/config.py` | ✓ |
| 146 | `cli.py:44` | `src/model_project_constructor/agents/website/cli.py` | clean | `VALID_HOSTS` in `src/model_project_constructor/agents/website/cli.py` | ✓ |
| 146 | `run_pipeline.py:406` | `scripts/run_pipeline.py` | clean | `main` function in `scripts/run_pipeline.py` (argparse choices) | ✓ |
| 158 | `src/model_project_constructor/agents/website/governance_templates.py:803-886` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_governance_files` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 175 | `governance_templates.py:72-79` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `_tier_at_least` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 180 | `governance_templates.py:820-886` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_governance_files` in `src/model_project_constructor/agents/website/governance_templates.py` (tier blocks) | ✓ |
| 181 | `governance_templates.py:938-959` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `is_governance_artifact` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 197 | `src/model_project_constructor/agents/website/governance_templates.py:110-144` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `_FRAMEWORK_ARTIFACTS` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 230 | `governance_templates.py:114-129` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_regulatory_mapping` in `src/model_project_constructor/agents/website/governance_templates.py` | **FIX** — `build_regulatory_mapping` in `src/model_project_constructor/agents/website/governance_templates.py` (function defined at line 147, not 114-129) |
| 236 | `src/model_project_constructor/agents/intake/anthropic_client.py` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `GOVERNANCE_FRAMEWORKS` in `src/model_project_constructor/agents/intake/anthropic_client.py` | ✓ |
| 257 | `agents/intake/protocol.py:75-93` | `src/model_project_constructor/agents/intake/protocol.py` | clean | `IntakeLLMClient` in `src/model_project_constructor/agents/intake/protocol.py` | ✓ |
| 258 | `model_project_constructor_data_agent/llm.py` | `packages/data-agent/src/model_project_constructor_data_agent/llm.py` | clean | `LLMClient` in `packages/data-agent/src/model_project_constructor_data_agent/llm.py` | ✓ |
| 275 | `agents/intake/anthropic_client.py` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `AnthropicLLMClient` in `src/model_project_constructor/agents/intake/anthropic_client.py` | ✓ |
| 295 | `model_project_constructor_data_agent/anthropic_client.py` | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | clean | `AnthropicLLMClient` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | ✓ |
| 303 | `scripts/run_pipeline.py` | `scripts/run_pipeline.py` | clean | `main` function in `scripts/run_pipeline.py` (--provider argument) | ✓ |
| 303 | `run_pipeline.py:447-455` | `scripts/run_pipeline.py` | clean | `main` function in `scripts/run_pipeline.py` (--provider argument) | ✓ |
| 304 | `cli.py:106-110` | `packages/data-agent/src/model_project_constructor_data_agent/cli.py` | clean | `run` command in data-agent CLI (--provider option) | ✓ |
| 315 | `tests/test_data_agent_decoupling.py` | `tests/test_data_agent_decoupling.py` | non_symbol | `tests/test_data_agent_decoupling.py` (entire test module) | **not-greppable** — Test module (non-symbol) — grep won't reliably locate by name alone, but module exists and is correctly referenced |
| 316 | `tests/schemas/test_envelope_and_registry.py` | `tests/schemas/test_envelope_and_registry.py` | non_symbol | `tests/schemas/test_envelope_and_registry.py` (entire test module) | **not-greppable** — Test module (non-symbol) — grep won't reliably locate by name alone, but module exists and is correctly referenced |
| 317 | `tests/agents/website/test_governance.py` | `tests/agents/website/test_governance.py` | non_symbol | `tests/agents/website/test_governance.py` (entire test module) | **not-greppable** — Test module (non-symbol) — grep won't reliably locate by name alone, but module exists and is correctly referenced |

### Security-Considerations.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 20 | `src/model_project_constructor/orchestrator/config.py:165-220` | `src/model_project_constructor/orchestrator/config.py` | clean | `OrchestratorSettings.from_env` in `orchestrator/config.py` | ✓ |
| 20 | `config.py:1-19` | `src/model_project_constructor/orchestrator/config.py` | non_symbol | Module docstring in `orchestrator/config.py` | **not-greppable** — non-symbol docstring; grep would find 'config.py' everywhere, but line range is specific |
| 28 | `OPERATIONS.md:11-30` | `OPERATIONS.md` | non_symbol | Section 11-30 in `OPERATIONS.md` | **not-greppable** — non-symbol documentation file; not grep-locatable as code |
| 44 | `src/model_project_constructor/ui/intake/app.py:77` | `src/model_project_constructor/ui/intake/app.py` | multi | `create_app` in `ui/intake/app.py` | ✓ |
| 45 | `scripts/run_pipeline.py:119, 123, 126, 290` | `scripts/run_pipeline.py` | multi | `build_repo_target` in `scripts/run_pipeline.py` | ✓ |
| 47 | `src/model_project_constructor/agents/website/gitlab_adapter.py:56-65` | `src/model_project_constructor/agents/website/gitlab_adapter.py` | clean | `PythonGitLabAdapter.__init__` in `agents/website/gitlab_adapter.py` | ✓ |
| 47 | `github_adapter.py:66-72` | `src/model_project_constructor/agents/website/github_adapter.py` | clean | `PyGithubAdapter.__init__` in `agents/website/github_adapter.py` | **FIX** — `PyGithubAdapter.__init__` in `src/model_project_constructor/agents/website/github_adapter.py:66-72` |
| 54 | `src/model_project_constructor/orchestrator/config.py:222-240` | `src/model_project_constructor/orchestrator/config.py` | clean | `OrchestratorSettings.require_host_token` in `orchestrator/config.py` | ✓ |
| 94 | `src/model_project_constructor/agents/intake/anthropic_client.py:39, 110` | `src/model_project_constructor/agents/intake/anthropic_client.py` | multi | `DEFAULT_MODEL` in `agents/intake/anthropic_client.py` | ✓ |
| 95 | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:53, 106` | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | multi | `DEFAULT_MODEL` in `packages/data-agent/.../anthropic_client.py` | ✓ |
| 99 | `src/model_project_constructor/agents/intake/factory.py:35-64` | `src/model_project_constructor/agents/intake/factory.py` | clean | `make_llm_client` in `agents/intake/factory.py` | ✓ |
| 99 | `packages/data-agent/src/model_project_constructor_data_agent/factory.py:31-64` | `packages/data-agent/src/model_project_constructor_data_agent/factory.py` | clean | `make_llm_client` in `packages/data-agent/.../factory.py` | ✓ |
| 115 | `src/model_project_constructor/agents/website/gitlab_adapter.py:41-155` | `src/model_project_constructor/agents/website/gitlab_adapter.py` | clean | `PythonGitLabAdapter` in `agents/website/gitlab_adapter.py` | ✓ |
| 126 | `src/model_project_constructor/agents/website/github_adapter.py:48-161` | `src/model_project_constructor/agents/website/github_adapter.py` | clean | `PyGithubAdapter` in `agents/website/github_adapter.py` | ✓ |
| 137 | `packages/data-agent/src/model_project_constructor_data_agent/db.py:29-37` | `packages/data-agent/src/model_project_constructor_data_agent/db.py` | clean | `ReadOnlyDB.connect` in `packages/data-agent/.../db.py` | ✓ |
| 139 | `cli.py:10-13` | `packages/data-agent/src/model_project_constructor_data_agent/cli.py` | non_symbol | Section 10-13 in `packages/data-agent/.../cli.py` | **not-greppable/FIX** — `packages/data-agent/src/model_project_constructor_data_agent/cli.py:10-13` |
| 158 | `src/model_project_constructor/agents/intake/anthropic_client.py:150-162` | `src/model_project_constructor/agents/intake/anthropic_client.py` | multi | `AnthropicLLMClient.next_question` in `agents/intake/anthropic_client.py` | **symbol✗/FIX** — `AnthropicLLMClient.next_question` in `agents/intake/anthropic_client.py:199-220` |
| 166 | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:123-364` | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | multi | `AnthropicLLMClient` in `packages/data-agent/.../anthropic_client.py` | **FIX** — `AnthropicLLMClient` methods in `packages/data-agent/.../anthropic_client.py:123-365` |
| 172 | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:449-460` | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | clean | `_dump_qc_status` in `packages/data-agent/.../anthropic_client.py` | **FIX** — `_dump_qc_status` in `packages/data-agent/.../anthropic_client.py:459-469` |
| 184 | `db.py:22-45` | `packages/data-agent/src/model_project_constructor_data_agent/db.py` | clean | `ReadOnlyDB` in `packages/data-agent/.../db.py` | **not-greppable/FIX** — `packages/data-agent/src/model_project_constructor_data_agent/db.py:22-45` |
| 184 | `lines 4-8` | `packages/data-agent/src/model_project_constructor_data_agent/db.py` | non_symbol | Module docstring lines 4-8 in `packages/data-agent/.../db.py` | **not-greppable/FIX** — Lines 4-8 in `packages/data-agent/src/model_project_constructor_data_agent/db.py` |
| 192 | `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py:16-29` | `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py` | clean | `validate_sql` in `packages/data-agent/.../sql_validation.py` | ✓ |
| 250 | `logging.py:58-117` | `src/model_project_constructor/orchestrator/logging.py` | clean | `make_logged_runner` in `orchestrator/logging.py` | **not-greppable/FIX** — `src/model_project_constructor/orchestrator/logging.py:58-117` |
| 266 | `OPERATIONS.md:81-107` | `OPERATIONS.md` | non_symbol | Section 81-107 in `OPERATIONS.md` | **not-greppable** — non-symbol documentation file reference; appropriate as-is |
| 274 | `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | non_symbol | `ci.yml` workflow file | **not-greppable** — file reference, not a code symbol; path is unambiguous |
| 287 | `src/model_project_constructor/agents/website/templates.py` | `src/model_project_constructor/agents/website/templates.py` | non_symbol | `agents/website/templates.py` module | **not-greppable** — module reference (no symbol); file exists and is appropriately cited |
| 290 | `src/model_project_constructor/agents/website/governance_templates.py` | `src/model_project_constructor/agents/website/governance_templates.py` | non_symbol | `agents/website/governance_templates.py` module | **not-greppable** — module reference (no symbol); file exists and is appropriately cited |
| 298 | `grep -R "ghp_\\|glpat_\\|sk-ant-\\|AKIA\\|-----BEGIN" src/model_project_constructor/agents/website/` | `src/model_project_constructor/agents/website/` | non_symbol | `agents/website/` directory (verification by grep) | **not-greppable** — verification command (not a code symbol); correctly references directory; command returns zero hits as expected |
| 335 | `intake/anthropic_client.py:8-12` | `src/model_project_constructor/agents/intake/anthropic_client.py` | non_symbol | Module docstring lines 1-13 in `agents/intake/anthropic_client.py` | **not-greppable/FIX** — Module docstring lines 1-13 in `src/model_project_constructor/agents/intake/anthropic_client.py` |

### Intake-Interview-Design.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 16 | `anthropic_client.py:110` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `SYSTEM_INTERVIEWER` in `anthropic_client.py` | ✓ |
| 16 | `anthropic_client.py:42-71` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `_INTERVIEWER_BASE` in `anthropic_client.py` | ✓ |
| 16 | `anthropic_client.py:80-108` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `_STATISTICAL_TERMS_NOTE` in `anthropic_client.py` | ✓ |
| 16 | `anthropic_client.py:42-58` | `src/model_project_constructor/agents/intake/anthropic_client.py` | multi | `_INTERVIEWER_BASE` in `anthropic_client.py` | ✓ |
| 20 | `anthropic_client.py:59-70` | `src/model_project_constructor/agents/intake/anthropic_client.py` | multi | `_INTERVIEWER_BASE` in `anthropic_client.py` | ✓ |
| 20 | `anthropic_client.py:80-108` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `_STATISTICAL_TERMS_NOTE` in `anthropic_client.py` | ✓ |
| 28 | `anthropic_client.py:128-135` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `SYSTEM_GOVERNANCE` in `anthropic_client.py` | ✓ |
| 38 | `src/model_project_constructor/agents/intake/graph.py` | `src/model_project_constructor/agents/intake/graph.py` | clean | graph module or `build_intake_graph` in `graph.py` | ✓ |
| 66 | `state.py:57` | `src/model_project_constructor/agents/intake/state.py` | clean | `MAX_QUESTIONS` in `state.py` | ✓ |
| 67 | `state.py:58` | `src/model_project_constructor/agents/intake/state.py` | clean | `MAX_REVISIONS` in `state.py` | ✓ |
| 75 | `nodes.py:52-57` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `plan_next_question` in `nodes.py` | **FIX** — `plan_next_question` nested function in `nodes.py` (line 54) |
| 82 | `protocol.py:30-39` | `src/model_project_constructor/agents/intake/protocol.py` | clean | `NextQuestionResult` in `protocol.py` | **FIX** — `NextQuestionResult` in `protocol.py` (lines 29-39 with decorator) |
| 87 | `nodes.py:80-84` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `evaluate_interview` in `nodes.py` | ✓ |
| 105 | `anthropic_client.py:147-177` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `_DRAFT_REPORT_INSTRUCTIONS` in `anthropic_client.py` | ✓ |
| 105 | `anthropic_client.py:222-234` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `draft_report` in `anthropic_client.py` | ✓ |
| 149 | `nodes.py:90-94` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `classify_governance_node` in `nodes.py` | ✓ |
| 149 | `anthropic_client.py:121-128` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `SYSTEM_GOVERNANCE` in `anthropic_client.py` | **symbol✗/not-greppable/FIX** — `SYSTEM_GOVERNANCE` in `anthropic_client.py` (lines 128-135) |
| 159 | `nodes.py:110-121` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `revise_node` in `nodes.py` | ✓ |
| 165 | `nodes.py:96-108` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `await_review` in `nodes.py` | ✓ |
| 167 | `nodes.py:37` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `REVIEW_ACCEPT_TOKENS` in `nodes.py` | ✓ |
| 181 | `nodes.py:123-163` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `finalize_node` in `nodes.py` | ✓ |
| 225 | `cli.py:30-60` | `src/model_project_constructor/agents/intake/cli.py` | clean | `run` in `cli.py` | **FIX** — `run` in `cli.py` (lines 30-60 including @app.command() decorator) |
| 267 | `protocol.py:75-93` | `src/model_project_constructor/agents/intake/protocol.py` | clean | `IntakeLLMClient` in `protocol.py` | ✓ |
| 276 | `state.py:57-58` | `src/model_project_constructor/agents/intake/state.py` | multi | `MAX_QUESTIONS` and `MAX_REVISIONS` in `state.py` | ✓ |
| 277 | `protocol.py:63-72` | `src/model_project_constructor/agents/intake/protocol.py` | clean | `GovernanceClassification` in `protocol.py` | **FIX** — `GovernanceClassification` in `protocol.py` (lines 62-72 with decorator) |
| 277 | `schemas/v1/intake.py:67-75` | `src/model_project_constructor/schemas/v1/intake.py` | clean | `GovernanceMetadata` in `schemas/v1/intake.py` | **FIX** — `GovernanceMetadata` in `schemas/v1/intake.py` (lines 78-85) |
| 277 | `anthropic_client.py:121-128` | `src/model_project_constructor/agents/intake/anthropic_client.py` | clean | `SYSTEM_GOVERNANCE` in `anthropic_client.py` | **symbol✗/not-greppable/FIX** — `SYSTEM_GOVERNANCE` in `anthropic_client.py` (lines 128-135) |
| 278 | `graph.py` | `src/model_project_constructor/agents/intake/graph.py` | non_symbol | graph module or `build_intake_graph` in `graph.py` | ✓ |
| 278 | `state.py` | `src/model_project_constructor/agents/intake/state.py` | non_symbol | `IntakeState` in `state.py` | ✓ |

### Schema-Reference.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 17 | `schemas/v1/intake.py:97-116` | `src/model_project_constructor/schemas/v1/intake.py` | clean | `IntakeReport` in `src/model_project_constructor/schemas/v1/intake.py` | ✓ |
| 18 | `packages/data-agent/.../schemas.py:46-68` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `DataRequest` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | ✓ |
| 19 | `packages/data-agent/.../schemas.py:113-123` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `DataReport` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | **FIX** — `DataReport` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` (lines 129-139) |
| 20 | `schemas/v1/repo.py:12-17` | `src/model_project_constructor/schemas/v1/repo.py` | clean | `RepoTarget` in `src/model_project_constructor/schemas/v1/repo.py` | ✓ |
| 21 | `schemas/v1/repo.py:28-37` | `src/model_project_constructor/schemas/v1/repo.py` | clean | `RepoProjectResult` in `src/model_project_constructor/schemas/v1/repo.py` | ✓ |
| 22 | `schemas/envelope.py:20-34` | `src/model_project_constructor/schemas/envelope.py` | clean | `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py` | ✓ |
| 24 | `tests/test_data_agent_decoupling.py` | `tests/test_data_agent_decoupling.py` | non_symbol | test file `tests/test_data_agent_decoupling.py` | ✓ |
| 33 | `src/model_project_constructor/schemas/v1/common.py:10-21` | `src/model_project_constructor/schemas/v1/common.py` | clean | `StrictBase` in `src/model_project_constructor/schemas/v1/common.py` | ✓ |
| 43 | `packages/data-agent/.../schemas.py:29-38` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `StrictBase` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | ✓ |
| 53 | `line 23` | `src/model_project_constructor/schemas/v1/common.py` | clean | `CycleTime` in `src/model_project_constructor/schemas/v1/common.py` | ✓ |
| 64 | `lines 25-30` | `src/model_project_constructor/schemas/v1/common.py` | clean | `RiskTier` in `src/model_project_constructor/schemas/v1/common.py` | **FIX** — RiskTier literal spans lines 25-30 in common.py, but that range includes the opening 'Literal[' and closing ']' on separate lines. RiskTier = Literal[ (line 25) |
| 82 | `lines 32-40` | `src/model_project_constructor/schemas/v1/common.py` | clean | `ModelType` in `src/model_project_constructor/schemas/v1/common.py` | ✓ |
| 96 | `orchestrator/adapters.py:55` | `src/model_project_constructor/orchestrator/adapters.py` | clean | `infer_target_granularity` in `src/model_project_constructor/orchestrator/adapters.py` | ✓ |
| 114 | `lines 18-25` | `src/model_project_constructor/schemas/v1/intake.py` | clean | `ModelSolution` in `src/model_project_constructor/schemas/v1/intake.py` | **FIX** — `ModelSolution` in `src/model_project_constructor/schemas/v1/intake.py` (lines 37-43) |
| 144 | `lines 24, 25–33, 34` | `src/model_project_constructor/schemas/v1/intake.py` | multi | `Confidence`, `CounterfactualDesign`, `ReviewCadence` in `src/model_project_constructor/schemas/v1/intake.py` | ✓ |
| 192 | `lines 35-43` | `src/model_project_constructor/schemas/v1/intake.py` | clean | `GovernanceMetadata` in `src/model_project_constructor/schemas/v1/intake.py` | **FIX** — `GovernanceMetadata` in `src/model_project_constructor/schemas/v1/intake.py` (lines 78-85) |
| 236 | `orchestrator/adapters.py` | `src/model_project_constructor/orchestrator/adapters.py` | clean | `intake_qa_pairs_to_inventory` in `src/model_project_constructor/orchestrator/adapters.py` | ✓ |
| 248 | `orchestrator/adapters.py` | `src/model_project_constructor/orchestrator/adapters.py` | clean | `intake_qa_pairs_to_inventory` in `src/model_project_constructor/orchestrator/adapters.py` | ✓ |
| 258 | `lines 41-43` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `DataGranularity` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | ✓ |
| 376 | `lines 62-68` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `QualityCheck` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | **FIX** — `QualityCheck` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` (lines 71-77) |
| 390 | `lines 71-80` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | clean | `Datasheet` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | **FIX** — `Datasheet` in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` (lines 80-89) |
| 469 | `lines 12-17` | `src/model_project_constructor/schemas/v1/repo.py` | clean | `RepoTarget` in `src/model_project_constructor/schemas/v1/repo.py` | ✓ |
| 480 | `github_adapter.py:85-89` | `src/model_project_constructor/agents/website/github_adapter.py` | non_symbol | code block in `src/model_project_constructor/agents/website/github_adapter.py` lines 85-89 | **not-greppable** — Non-symbol code block reference; 'github_adapter.py:85-89' is the error-raising conditional but not a named function/class. Cannot grep to uniquely locate this  |
| 482 | `lines 20-25` | `src/model_project_constructor/schemas/v1/repo.py` | clean | `GovernanceManifest` in `src/model_project_constructor/schemas/v1/repo.py` | ✓ |
| 496 | `lines 28-37` | `src/model_project_constructor/schemas/v1/repo.py` | clean | `RepoProjectResult` in `src/model_project_constructor/schemas/v1/repo.py` | ✓ |
| 521 | `lines 20-34` | `src/model_project_constructor/schemas/envelope.py` | clean | `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py` | ✓ |
| 540 | `tests/schemas/test_envelope_and_registry.py — test_target_agent_cannot_be_orchestrator` | `tests/schemas/test_envelope_and_registry.py` | clean | `test_target_agent_cannot_be_orchestrator` in `tests/schemas/test_envelope_and_registry.py` | ✓ |
| 553 | `lines 26-32` | `src/model_project_constructor/schemas/registry.py` | clean | `REGISTRY` in `src/model_project_constructor/schemas/registry.py` | ✓ |
| 568 | `lines 39-58 (abbreviated)` | `src/model_project_constructor/schemas/registry.py` | clean | `load_payload` in `src/model_project_constructor/schemas/registry.py` | ✓ |

### Worked-Examples.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 36 | `tests/fixtures/subrogation_intake.json:5` | `tests/fixtures/subrogation_intake.json` | non_symbol | `business_problem` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 40 | `:6` | `tests/fixtures/subrogation_intake.json` | non_symbol | `proposed_solution` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 44 | `:7-25` | `tests/fixtures/subrogation_intake.json` | non_symbol | `model_solution` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 52 | `:26-47` | `tests/fixtures/subrogation_intake.json` | non_symbol | `estimated_value` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 59 | `:48-71` | `tests/fixtures/subrogation_intake.json` | non_symbol | `value_measurement_plan` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 61 | `:72-83` | `tests/fixtures/subrogation_intake.json` | non_symbol | `governance` in `tests/fixtures/subrogation_intake.json` | ✓ |
| 115 | `src/model_project_constructor/orchestrator/adapters.py:133` | `src/model_project_constructor/orchestrator/adapters.py` | clean | `intake_qa_pairs_to_inventory` in `src/model_project_constructor/orchestrator/adapters.py` | ✓ |
| 115 | `scripts/run_pipeline.py:477` | `scripts/run_pipeline.py` | non_symbol | `--inventory-from-intake` flag in `scripts/run_pipeline.py` | ✓ |
| 130 | `tests/agents/website/test_templates.py:294-341` | `tests/agents/website/test_templates.py` | clean | `TestBuildBaseFiles.test_returns_expected_file_set` in `tests/agents/website/test_templates.py` | ✓ |
| 172 | `src/model_project_constructor/agents/website/governance_templates.py:803-886` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_governance_files` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 183 | `governance_templates.py:846-855` | `src/model_project_constructor/agents/website/governance_templates.py` | multi | Tier-3+ scaffold block in `build_governance_files` (lines 846-855) | ✓ |
| 189 | `governance_templates.py:881-884` | `src/model_project_constructor/agents/website/governance_templates.py` | multi | Consumer-facing scaffold block in `build_governance_files` (lines 881-884) | ✓ |
| 199 | `src/model_project_constructor/agents/website/templates.py` | `src/model_project_constructor/agents/website/templates.py` | clean | `render_qmd_business_understanding` in `src/model_project_constructor/agents/website/templates.py` | ✓ |
| 214 | `src/model_project_constructor/agents/website/templates.py` | `src/model_project_constructor/agents/website/templates.py` | clean | `render_qmd_implementation_plan` in `src/model_project_constructor/agents/website/templates.py` | ✓ |
| 252 | `governance_templates.py` | `src/model_project_constructor/agents/website/governance_templates.py` | non_symbol | `build_governance_files`, `build_analysis_files`, and `build_test_files` in `src/model_project_constructor/agents/website/governance_templates.py` | ✓ |
| 254 | `governance_templates.py:858-873` | `src/model_project_constructor/agents/website/governance_templates.py` | multi | Tier-2+ scaffold block in `build_governance_files` (lines 858-873) | ✓ |
| 259 | `governance_templates.py:876-878` | `src/model_project_constructor/agents/website/governance_templates.py` | multi | Tier-1 scaffold block in `build_governance_files` (lines 876-878) | ✓ |
| 264 | `governance_templates.py:889-909` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_analysis_files` in `src/model_project_constructor/agents/website/governance_templates.py` (lines 889-909) | ✓ |
| 264 | `governance_templates.py:912-930` | `src/model_project_constructor/agents/website/governance_templates.py` | clean | `build_test_files` in `src/model_project_constructor/agents/website/governance_templates.py` (lines 912-930) | ✓ |

### Evolution.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 65 | `nodes.py:142` | `src/model_project_constructor/agents/intake/nodes.py` | multi | `finalize_node` in `src/model_project_constructor/agents/intake/nodes.py` | ✓ |
| 71 | `nodes.py:129-134` | `src/model_project_constructor/agents/intake/nodes.py` | multi | `finalize_node` in `src/model_project_constructor/agents/intake/nodes.py` | ✓ |
| 75 | `nodes.py:142` | `src/model_project_constructor/agents/intake/nodes.py` | multi | `finalize_node` in `src/model_project_constructor/agents/intake/nodes.py` | ✓ |
| 125 | `gitlab_adapter.py:41` | `src/model_project_constructor/agents/website/gitlab_adapter.py` | clean | `PythonGitLabAdapter` in `src/model_project_constructor/agents/website/gitlab_adapter.py` | ✓ |
| 129 | `scripts/run_pipeline.py:119` | `scripts/run_pipeline.py` | multi | `build_repo_target` in `scripts/run_pipeline.py` | ✓ |
| 133 | `scripts/run_pipeline.py:273-278` | `scripts/run_pipeline.py` | multi | `build_website_runner` in `scripts/run_pipeline.py` | ✓ |
| 135 | `src/model_project_constructor/agents/website/cli.py:39` | `src/model_project_constructor/agents/website/cli.py` | non_symbol | module-level constant in `src/model_project_constructor/agents/website/cli.py` (historical reference) | **symbol✗/not-greppable/FIX** — Historical reference — symbol no longer exists. Current equivalent: `REPO_PLATFORMS['gitlab'].default_api_url` in `src/model_project_constructor/orchestrator/co |
| 135 | `orchestrator/config.py:33` | `src/model_project_constructor/orchestrator/config.py` | multi | `REPO_PLATFORMS` in `src/model_project_constructor/orchestrator/config.py` | ✓ |
| 135 | `scripts/run_pipeline.py:105,283` | `scripts/run_pipeline.py` | non_symbol | `REPO_PLATFORMS[host].default_api_url` usage in `build_repo_target` (line ~119) and `build_website_runner` (line ~289) | ✓ |
| 173 | `state.py:57` | `src/model_project_constructor/agents/intake/state.py` | clean | `MAX_QUESTIONS` in `src/model_project_constructor/agents/intake/state.py` | ✓ |
| 173 | `protocol.py:34` | `src/model_project_constructor/agents/intake/protocol.py` | multi | `NextQuestionResult` docstring in `src/model_project_constructor/agents/intake/protocol.py` | **FIX** — `NextQuestionResult` class definition (with docstring at lines 29-39) in `src/model_project_constructor/agents/intake/protocol.py` |
| 262 | `protocol.py:34` | `src/model_project_constructor/agents/intake/protocol.py` | multi | `NextQuestionResult` in `src/model_project_constructor/agents/intake/protocol.py` | **FIX** — `NextQuestionResult` class definition (with docstring at lines 29-39) in `src/model_project_constructor/agents/intake/protocol.py` |

### Contributing.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 13 | `pyproject.toml:6` | `pyproject.toml` | non_symbol | `requires-python` in `pyproject.toml` (under `[project]`) | ✓ |
| 14 | `pyproject.toml:49-50` | `pyproject.toml` | non_symbol | `[tool.uv.workspace]` in `pyproject.toml` | ✓ |
| 28 | `pyproject.toml:17-40` | `pyproject.toml` | non_symbol | `[project.optional-dependencies]` in `pyproject.toml` | **FIX** — `[project.optional-dependencies]` in `pyproject.toml` (lines 17-44) |
| 42 | `.github/workflows/ci.yml:3-7` | `.github/workflows/ci.yml` | non_symbol | `on:` trigger section in `.github/workflows/ci.yml` | ✓ |
| 46 | `pyproject.toml:83-92` | `pyproject.toml` | non_symbol | `[tool.ruff]` and `[tool.ruff.lint]` in `pyproject.toml` | **FIX** — `[tool.ruff]` and `[tool.ruff.lint]` sections in `pyproject.toml` (lines 83-88) |
| 67 | `pyproject.toml:94-98` | `pyproject.toml` | non_symbol | `[tool.mypy]` in `pyproject.toml` | ✓ |
| 82 | `pyproject.toml:58-77` | `pyproject.toml` | non_symbol | `[tool.pytest.ini_options]` and `[tool.coverage.*]` in `pyproject.toml` | **FIX** — `[tool.pytest.ini_options]` (lines 62-65) and `[tool.coverage.run]` and `[tool.coverage.report]` (lines 67-81) in `pyproject.toml` |
| 106 | `.github/workflows/ci.yml:54-63` | `.github/workflows/ci.yml` | non_symbol | `decoupling` job in `.github/workflows/ci.yml` | ✓ |

### Changelog.md

| Wiki ln | Current citation | Resolved file | Class | Proposed replacement | Verdict |
|---|---|---|---|---|---|
| 137 | `nodes.py:35` | `src/model_project_constructor/agents/intake/nodes.py` | clean | `REVIEW_ACCEPT_TOKENS` in `src/model_project_constructor/agents/intake/nodes.py` | **FIX** — `REVIEW_ACCEPT_TOKENS` in `src/model_project_constructor/agents/intake/nodes.py` (line 37) |
| 203 | `src/model_project_constructor/schemas/registry.py:7-13` | `src/model_project_constructor/schemas/registry.py` | non_symbol | `REGISTRY` in `src/model_project_constructor/schemas/registry.py` | ✓ |
