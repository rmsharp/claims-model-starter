# Technical-Debt & Refactoring-Viability Audit

**Role:** Senior Software Architect (read-only assessment — no code modified)
**Date:** 2026-06-01 · **Session:** 97 · **Effort:** `ultracode` (33-agent workflow)
**Subject:** `model_project_constructor` — the 6-step multi-agent LangGraph pipeline (intake → data → website), ~9,160 lines of Python across `src/model_project_constructor/` + `packages/data-agent/`.

---

## 1. Audit Summary

| | |
|---|---|
| **Scope** | All production modules under `src/model_project_constructor/` (intake, website, data-shim, orchestrator, schemas, ui) + the standalone `packages/data-agent/` + `scripts/run_pipeline.py`. Tests and docs excluded by design (auditing *reality*, per AUDIT_WORKSTREAM anti-pattern #6). |
| **Criteria** | Three dimensions: (1) cognitive complexity, (2) duplication / DRY, (3) extensibility / rigid architecture. |
| **Coverage** | ~50 Python files / ~9,160 LOC. 7 module slices + 3 cross-cutting sweeps + an architecture map + a roadmap-grounded feature inventory. |
| **Method** | 13 parallel auditors read the actual code; **one adversarial verifier per file re-read the file in full** and confirmed/corrected every finding's line range and severity. 44 raw findings → **44 confirmed, 0 refuted**, but the verifiers down-calibrated 6 findings (moderate→minor) and corrected ~12 line ranges. |
| **Finding count** | **0 critical · 15 moderate · 29 minor.** By risk class: **37 Quick Wins · 7 Architectural Overhauls.** By dimension: 20 duplication · 15 extensibility · 9 complexity. |
| **Headline verdict** | **A healthy, well-layered codebase with low absolute debt.** The debt that exists is concentrated and *predictable*: every Architectural Overhaul sits on a seam the published roadmap is about to push through. There is **one latent correctness bug** (a known-and-fixed parser bug still live in a copy) and **two stakeholder-facing correctness defects** (UI advertises the wrong question cap; a regulatory framework the intake agent emits has no governance artifact). |

---

## 2. Method — Chain-of-Thought

The audit was reasoned in five explicit steps (AUDIT_WORKSTREAM Phase 2):

1. **Map before judging.** Before flagging anything, an agent mapped module responsibilities, the import graph, and the abstraction seams. This established the *intended* design so that "rigid" could be distinguished from "deliberately decoupled." Key output: layering is clean and one-directional, there are **no import cycles**, and the data-agent package has **zero** imports of the main package (AST-enforced by `tests/test_data_agent_decoupling.py`).

2. **Ground "extensibility" in real upcoming work, not taste.** A second agent read `ROADMAP.md`, `docs/planning/*`, and `docs/architecture-history/architecture-plan.md` to enumerate 12 concrete planned/likely features. Extensibility findings are then judged by *how many files each real feature forces you to touch* — not by abstract preference.

3. **Read the code, three ways.** Seven auditors read coherent module slices end-to-end; three cross-cutting auditors swept the whole tree for (a) duplication that spans files, (b) rigidity at the seams, and (c) the worst complexity hotspots. The multi-angle sweep is deliberate — module auditors can't see cross-file duplication; the cross-cutting auditors can't go as deep.

4. **Adversarially verify every finding against the file.** Each finding was re-checked by an independent agent that re-read the cited file in full, with instructions to **default to "not real" if it could not confirm the issue at the cited lines.** This is what makes the file:line evidence below trustworthy rather than plausible-sounding. The verifiers refuted 0 but *corrected* many (severity deflation, line-range fixes, factual nits) — those corrections are folded in.

5. **Find the forest.** 44 individual findings were collapsed into ~6 structural themes (AUDIT_WORKSTREAM anti-pattern #5: don't ship 44 instances when 6 root causes explain them). The recommendations target the causes.

> **On "0 refuted":** This is not a rubber stamp. Auditors were forced to anchor every claim to a line range and were told empty findings are respectable; verifiers re-read each file and down-graded 6 severities and corrected ~12 ranges. The signal is that the *findings* are real — but several are deliberately-documented trade-offs (noted inline as "by design"), and the recommendation for those is a one-line guard/test, not a rewrite.

---

## 3. Healthy Baseline (Reference Implementations)

A debt audit that only lists problems mis-calibrates the reader. The following are **well-designed and should be the template for new code**:

- **The orchestrator is the cleanest seam in the codebase.** `orchestrator/pipeline.py:48-50` injects agents as plain callables (`IntakeRunner`/`DataRunner`/`WebsiteRunner`); `run_pipeline` has **zero import-time dependency on any agent, LLM client, DB, or repo SDK** (grep-confirmed). Heavy vendor imports (`anthropic`, `gitlab`, `github`, `langgraph`) never reach the orchestration layer. This is why the pipeline is trivially testable with stubs.
- **The RepoClient adapter seam is correct.** `agents/website/protocol.py:42` defines `RepoClient`; GitLab/GitHub/fake adapters implement it and normalize host errors to a shared `RepoClientError`/`RepoNameConflictError` taxonomy. The *adapter* layer is right — only the *selection* of which adapter is rigid (Theme E1).
- **The data-agent decoupling holds.** Exactly **one** data-agent implementation exists (`packages/data-agent/`); `src/.../agents/data/` is a documented 3-file re-export shim, **not** a competing implementation. The standalone-wheel boundary is real and CI-enforced.
- **No duplicated agent skeleton.** The three LangGraph agents share only the `build_*_graph` + `make_nodes(...)` library idiom, not copied node code — their topologies genuinely differ.
- **Resume-from-checkpoint is sophisticated and correct** (`pipeline.determine_resume_point:80`): a documented truth table, status-aware stage demotion, and a deliberate "operator config always wins over a saved RepoTarget" rule. Its only debt is *how* it's expressed (Theme C1), not *what* it does.

---

## 4. Dimension 1 — Cognitive Complexity

9 findings, no critical. Control flow is shallow almost everywhere; the complexity is **length + concern-count**, not deep nesting. One cluster dominates.

### C1 — `run_pipeline` is a ~170-line god-function `[overhaul]`
`orchestrator/pipeline.py:224-392` (findings #10, #38, #40 are the same function; #44 is its sibling). One body drives all four stages inline. Each stage repeats an *execute-or-load* branch gated by a **hand-spelled, growing membership tuple**: `resume is None or resume == "intake"` (L253), `resume in (None, "intake", "intake_to_data_adapter")` (L285), `resume in (None, "intake", "intake_to_data_adapter", "data")` (L321). Three near-identical `FAILED` early-returns rebuild a `PipelineResult` (L266-275, L334-342, L369-382); four near-identical `checkpoint_store.save(_envelope(...))` blocks repeat the orchestrator-source invariant (L255-264, L304-313, L323-332, L352-361). The "which stages run for resume point X" rule is encoded **twice** — here as inclusion tuples, and in `determine_resume_point` (L139-157) as the inverse demotion ladder — and they must be kept in lockstep by hand.
**Impact:** the resume gating is the single most error-prone part of the orchestrator; a wrong tuple silently skips or double-runs a stage. *Mitigated today* by heavy comments + full test coverage, hence moderate-not-critical.
**Recommendation:** introduce an ordered `STAGE_ORDER` tuple and derive "should this stage run" from `index(resume) <= index(stage)` in one helper; extract a `_run_or_load_stage(...)` and a `_halt(status, **reports)` helper. `run_pipeline` collapses to a short linear sequence and the resume semantics live in one tested place. (See Overhaul O1 — this is the same fix that resolves Theme E3.)

### C2 — `main()` in `scripts/run_pipeline.py` is a ~240-line procedure `[quick_win]`
`scripts/run_pipeline.py:405-644` (#41) interleaves six concerns: 11 argparse args (L406-500), cross-arg validation, resume side-effects, a multi-branch banner with its own `llm_label` if/elif/else (L515-533), staged fixture preview (L536-552), runner wiring (L554-592), and five `print` reporting blocks (L604-641). The `[1/5]`…`[5/5]` banners literally announce five phases stuffed into one function, and the `llm`-mode interpretation is re-derived here in addition to `build_intake_runner`/`build_data_runner`.
**Recommendation:** mechanical extraction — `_build_parser()`, `_print_banner(...)`, `_print_preview(...)`, `_report(...)`. `main()` becomes ~30 lines. The file already has good helper discipline elsewhere; this just continues it.

### C3 — `_render_production_measurement_plan` is a 107-line renderer `[quick_win]`
`agents/website/templates.py:464-570` (#3, #43). Two unrelated concerns in one body: a nested baseline-snapshot interpretation block with a provenance footnote (L484-524) and six ValueMeasurementPlan field-defaulting blocks feeding a ~25-line assembly f-string (L527-570). The `str(... or "").strip()` / `value or "(placeholder)"` idiom recurs ~12× here and again in `_render_business_case_block` (L327-377).
**Recommendation:** extract `_render_baseline_block(snapshot, vmp)` (isolates the only branch with real logic) and add `_text_or(value, ph)` / `_bullets_or(items, ph)` helpers. Every `render_*` is byte-pinned by tests, so drift is caught immediately. This is the value-measurement narrative the business-value-capture plan keeps extending — it will only grow.

### C4 — `build_governance_files` tier/flag branch ladder `[quick_win]`
`agents/website/governance_templates.py:762-845` (#42). The one branchy function in an otherwise-flat 931-line file of independent f-string renderers. Five gated emit sections (always / tier-3+ / tier-2+ / tier-1 / consumer) interleave emit decisions, artifact path strings, and per-tier rationale, so "which tier emits which artifact" is implicit in control flow. `build_regulatory_mapping` is called mid-stream against an in-progress `tentative_paths` set (L821-829) — a latent footgun for anyone adding artifacts after it.
**Recommendation:** a declarative `[(predicate, path, renderer)]` emission table iterated once; the datasheet loop and the regulatory-mapping stay as the two special cases. Lower-effort: lift the tier thresholds into named constants.

### C5/C6 — Smaller complexity nits `[quick_win]`
- **`finalize_node`** (`agents/intake/nodes.py:123-163`, #18) concentrates four completeness rules + a validate-by-side-effect `build_intake_report(...)` call whose return is discarded (L161). Extract a pure, unit-testable `compute_missing_fields(...)`; make the validation gate explicit. This is the agent's most policy-laden decision and where future governance rules will accrete.
- **`_format_qa`** (`agents/intake/anthropic_client.py:255-263`, #17) carries a dead `dict | dataclass` union + `getattr` branch that the `list[QAPair]` TypedDict contract (`protocol.py:25`) forbids. Narrow the signature, index by key, drop the branch.

---

## 5. Dimension 2 — Duplication / DRY

20 findings — the largest dimension. One latent **bug** hides in the duplication; the rest is maintenance drag.

### D1 — The two Anthropic clients duplicate LLM plumbing, and the copies have *diverged on a known bug* `[overhaul for full dedup / quick_win for the bug]`
`agents/intake/anthropic_client.py:115-319` vs `packages/data-agent/.../anthropic_client.py:99-492` (#31, #16). Four concerns are independently reimplemented in both: client construction (`anthropic.Anthropic()` + `_model`/`_max_tokens`), the single Claude round-trip, a `_CODE_FENCE` regex + `_extract_json` parser, and a per-method parse guard.
**The latent bug (HIGH VALUE):** the two `_extract_json` copies diverged. The data-agent version (L460-492) was **hardened after a tracked live-LLM crash** (Session 51, `run_id=run_b1_resume_live_1776570556`) to try a bare parse first, then `.search()` for a fence *anywhere* in the response. The intake copy (L306-319) **still uses the old anchored `^…$` `.match()` regex that the data-agent docstring explicitly documents as the cause of that crash.** The first real `--anthropic` interview that returns prose around a code fence (documented sonnet-4-6 behaviour) will raise `IntakeLLMError` where the data agent now succeeds.
**Recommendation:** *Quick win (30 min, #16)* — port the hardened ~12-line `_extract_json`/`_CODE_FENCE` into the intake client now + add a fence+prose regression test. *Overhaul (O2)* — extract a provider-neutral `llm_json` helper, mindful that the data-agent ships as a standalone wheel (put the shared helper inside the data-agent package, or carve a third tiny shared package).

### D2 — LLM-method scaffold repeated 6× (data) + 4× (intake) `[quick_win]`
`packages/data-agent/.../anthropic_client.py:113-354` (#22, #34). Every public method repeats `call_claude → extract_json → isinstance-guard-or-raise → dataclass-map`; the guard block is near-verbatim 6× (L148-151, 187-190, 227-230, 257-260, 298-301, 343-346) and the same shape mirrors 4× in the intake client.
**Recommendation:** two thin helpers `_parse_json_object(raw, method)` / `_parse_json_array(raw, method)` bundling extract + guard + standardized error. Field coercion stays per-method (genuinely method-specific).

### D3 — Draft↔dict converters triplicated `[quick_win]`
`agents/intake/{nodes.py:192-211, anthropic_client.py:266-288, fixture.py:148-159}` (#15). The 6-field `DraftReportResult`↔dict conversion is implemented three times (plus the governance 7-field pair). A converter that misses a newly-added field silently drops data on the round-trip (exactly how `value_measurement_plan` could be erased and then reported as `value_measurement_plan_incomplete` with no obvious cause).
**Recommendation:** one `to_dict`/`from_dict` pair (or classmethods on `DraftReportResult` in `protocol.py`) imported by all three.

### D4 — USD-band formatter byte-duplicated `[quick_win]`
`templates.py:303-312` (`_format_usd_band`) ≡ `governance_templates.py:364-374` (`_usd_band`) (#1, #32). Byte-identical bodies; feeds the customer-visible business case in both the README/QMD and the governance impact assessment, so drift yields inconsistent dollar figures in the same generated repo. The "kept local for 4A/4B decoupling" rationale is thin for a 3-line pure formatter living in the same package directory.
**Recommendation:** one `website/_format.py` helper imported by both. Intra-package — does not cross the data-agent boundary.

### D5–D10 — Localized DRY (all `quick_win`, mostly `minor`)
- **List-or-placeholder idiom** repeated ~8× across both template modules, with a subtly different `or`-on-joined-string variant for biases (`governance_templates.py:543`) → `_bullet_list(items, empty=...)` helper (#4).
- **Four scaffold nodes** repeat the `files_pending` merge + a byte-identical `governance_paths` sorted-set union (`agents/website/nodes.py:130-191`) → `_merge_scaffold(...)` helper or LangGraph additive channels (#7).
- **Four `_envelope` save blocks** in `run_pipeline` (`pipeline.py:255-361`) → a bound `_save(target, type, model)` closure (#13). (Folds into O1.)
- **Two timing wrappers** (`metrics.py:132-138` + `logging.py:84-117`) duplicate the `perf_counter` try/finally; in production they're nested so each runner is timed twice with two slightly different durations → one `timed_call(...)` helper (#11).
- **UI review/complete render** duplication + the **LangGraph interrupt-extraction idiom** copied between `ui/intake/runner.py:119-139` and `agents/intake/agent.py:89-95` → `parse_pending_interrupt(state)` + a shared `kind` enum so the interrupt contract lives in one place (#21, #20).
- **`QualityCheck` constructor 3×** (`data-agent/nodes.py:94-149`), **two deterministic fake LLM clients** (`cli.py` vs the test suite), **column-preview logic** (`data-agent/anthropic_client.py:326-432`), **`HandoffEnvelope` re-declaring `extra="forbid"`** instead of sharing `StrictBase` — all small, all extract-a-helper (#23, #25, #26, #29).
- **Adapter symmetry (#33) is *not* a defect:** `github_adapter`/`gitlab_adapter` share the exception-mapping idiom and `_is_name_conflict` shape, but the work bodies hit genuinely different SDK surfaces and are correctly *not* merged. Extract only the shared `_raise_repo_error(...)` message helper; leave the bodies.

---

## 6. Dimension 3 — Extensibility / Rigid Architecture

15 findings. **This is the most important dimension** because every rigid point lines up with a published roadmap item — the audit cross-checked each against `ROADMAP.md` / `docs/planning/`.

> **The pattern:** the codebase abstracts *behavior* well (Protocols for repo hosts and LLM clients are clean) but abstracts *selection and vocabulary* poorly. Choosing which adapter/provider/stage, and the controlled vocabularies, are hardcoded enumerations scattered across files with no single source of truth.

### E1 — Repo-platform selection is a hardcoded `gitlab/github` binary across 6+ files `[overhaul]`
(#35, #8, #9, #12, #6) — **Roadmap: "3rd repo platform (Bitbucket/Gitea/Azure DevOps)."** The `RepoClient` Protocol is clean, but *platform selection* is an explicit `if host == "gitlab" / else github` branch plus a `frozenset({"gitlab","github"})` allow-list, repeated in: `agents/website/cli.py:42-43,167-190`, `scripts/run_pipeline.py:113-127,285-296`, `orchestrator/config.py:92-103,140`. The `Literal["gitlab","github"]` is **independently re-declared in 5 files** (`config.py:29`, `governance_templates.py:30`, `agent.py:38`, `state.py:31,76`, + the `cli.py:192` cast). mypy catches Literal mismatches but **not** the runtime `else: # github` fall-through that silently treats any unknown host as GitHub. Adding a host is a ~6-file, ~12-branch shotgun edit.
**Recommendation (O3):** one `REPO_PLATFORMS: dict[str, PlatformSpec]` registry (default API URL, token env var, adapter factory). Replace each if/else with a dict lookup; derive the single `Literal`/allow-list from `REPO_PLATFORMS.keys()`. Adapters already conform to `RepoClient`, so a new platform becomes **one registry entry + one adapter module**.

### E2 — Controlled vocabularies have no single source of truth — and have *already drifted* `[overhaul + correctness]`
(#14, #2, #39, #27, #24, #19) — **Roadmap: governance-matrix + value-measurement features.** The same enums exist three times — as prompt prose (producer), as Pydantic `Literal` (validator), and as `dict.get()` fallbacks (consumer) — with nothing linking them. Confirmed drift, two of which are **correctness defects**:
- **`#19` (stakeholder-facing bug, quick win):** `ui/intake/templates.py:64,121` tell stakeholders "up to **10** questions" but `state.py:57` sets `MAX_QUESTIONS = 20` — the UI advertises *half* the real interview length. The single source already exists (`runner.py:239-242 CAPS`) and is simply not consumed. *(The "of 3" revision cap at L163 is hardcoded but coincidentally correct.)*
- **`#39` (governance bug, quick win):** `governance_templates.py:77-103 _FRAMEWORK_ARTIFACTS` keys `{SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, EU_AI_ACT, ASOP_56}`, but the intake prompt (`anthropic_client.py:107-108`) tells the model the frameworks are `{…, GDPR_ART_22}`. So **`GDPR_ART_22` is emitted by intake but maps to no governance artifact** (silently → `[]`), while `ASOP_56`/`EU_AI_ACT` are mapped but never prompted. `regulatory_frameworks` is a bare `list[str]` (`intake.py:72`) so the drift is invisible to mypy and Pydantic. For a P&C compliance tool, a silently-dropped regulatory framework is correctness-adjacent.
- **`#2`:** `_TIER_SEVERITY`/`_CYCLE_CADENCE` (`governance_templates.py:39-66`) hardcode the `RiskTier`/`CycleTime` members with silent `.get(..., default)` fallbacks; an added critical tier would get severity 99 (least-severe) and **skip all tier-gated governance artifacts** — a quiet compliance gap.
- **`#14`/`#27`/`#24`:** model-type / counterfactual-design / review-cadence / row-count-order / measurement-unit vocabularies are all prose-in-prompt + `Literal`-in-schema with no shared constant.
**Recommendation:** promote each vocabulary to a named `Literal` in `schemas/v1/common.py` (next to the existing `CycleTime`/`RiskTier`/`ModelType`), type the fields against it, and **derive the prompt's enumerations from `typing.get_args(...)`**. Add import-time `assert set(dict.keys()) == set(get_args(Literal))` guards so drift fails loudly. *Quick wins available immediately:* fix #19 and #39 and add the two assertion tests regardless of the larger reconciliation.

### E3 — The pipeline is a fixed 3-stage sequence, not a composed step list `[overhaul]`
`orchestrator/pipeline.py:224-392` (#38) — **Roadmap: "wire the real data-collection step by default," plus plausible validation/review stages.** Same root as C1: there is no `Stage` abstraction (name, runner, payload_type, halt-predicate) the driver iterates. Adding a stage means a new `ResumePoint` literal + a new `PipelineStatus` literal + a new inline save/halt block + an entry in `scripts/run_pipeline.py:319-325 _SKIPPED_STAGES_BY_RESUME_POINT` + extending `determine_resume_point`'s cascade + editing every resume membership tuple at the right position.
**Recommendation (O1):** model the pipeline as an ordered `[Stage]` list and drive save/halt/resume generically by index. One fix resolves C1, D5(envelope), E3, and the resume-tuple drift simultaneously — **the single highest-leverage refactor in the codebase.**

### E4 — No LLM-provider seam at construction `[quick_win, speculative]`
(#36) — **Roadmap: "non-Anthropic provider."** The `LLMClient`/`IntakeLLMClient` Protocols are good provider-agnostic seams, but there is no factory mapping a provider name to a concrete client: every site builds `AnthropicLLMClient(...)` directly (`run_pipeline.py:149,243`; `cli.py:192-195`) and `DEFAULT_MODEL="claude-sonnet-4-6"` is baked in. Provider choice is implicit in which symbol you import.
**Recommendation:** a small `make_llm_client(provider, model)` factory + a `--provider` flag defaulting to `anthropic`. Low urgency (one provider exists today) but cheap insurance; the Protocols already did the hard part.

### E5 — Schema versioning is advertised but unimplemented `[quick_win]`
`schemas/registry.py` (#30, #37, #28) — **Roadmap: "v2 schema + migrations."** The *read* path is genuinely pluggable (`load_payload` keys on `(payload_type, version)`), but the docstring promises a `schemas/migrations/` workflow that **does not exist** (only `v1/`), the *write* path hardcodes `payload_schema_version="1.0.0"` (`pipeline.py:409`), `HandoffEnvelope.envelope_version` is a frozen `Literal["1.0.0"]`, and the `SCHEMA_VERSION` constant (`common.py:9`) is **dead** — every model restates the literal by hand.
**Recommendation:** *honest minimal* — trim the docstring to match reality and delete the dead `SCHEMA_VERSION` export. *Or build the seam now* — derive `payload_schema_version` from the model class, widen `envelope_version`, and create an empty `schemas/migrations/` with a `migrate(payload, from_v, to_v)` stub so the path is real before the v2 bump arrives under deadline pressure.

### E6/E7 — Governance tier ladder & base manifest `[quick_win]`
- **#6/#42:** CI-platform file selection is an inline `if ci_platform == "gitlab" / else` (`governance_templates.py:793-796`) with the path set independently hardcoded in `is_governance_artifact` (L908-913). The schema's `RiskTier` already includes a **`tier_4_low` member with no artifact set** — a half-built extension point. → a `_CI_RENDERERS` registry + a declarative tier→artifact table (folds into C4/E2).
- **#5:** `build_base_files` (`templates.py:769-807`) hardcodes the 36-entry scaffold manifest; the `src/<module>.py` ↔ `tests/test_<module>.py` pairing is by-hand with nothing enforcing it. → drive both from a `BASE_MODULES` list in a loop. (Mild — a flat manifest is a reasonable, readable pattern.)

---

## 7. Prioritized Refactoring Targets

> Ordered within each group by **value ÷ risk**. "Quick Win" = localized, low-risk, byte-tests or unit-tests pin behavior. "Architectural Overhaul" = cross-module, requires extensive regression testing.

### 🟢 Quick Wins (do these first — low risk, high reward)

**Tier 1 — correctness (fix this week):**
1. **Port the hardened `_extract_json` into the intake client** (#16) — `agents/intake/anthropic_client.py:306-319`. Kills a latent crash already fixed elsewhere. ~30 min + 1 regression test. *Highest value/risk ratio in the audit.*
2. **Fix the UI question cap** (#19) — `ui/intake/templates.py:64,121`: consume `runner.CAPS`/`MAX_QUESTIONS` instead of the literal "10". Stakeholder-trust defect. ~30 min.
3. **Reconcile the regulatory-framework drift** (#39) — align `_FRAMEWORK_ARTIFACTS` keys with the intake prompt set (resolve `GDPR_ART_22`) + add an `assert prompt_set == _FRAMEWORK_ARTIFACTS.keys()` test. Governance correctness. ~1 session.

**Tier 2 — drift guards (cheap insurance):**
4. **Import-time assertions tying `_TIER_SEVERITY`/`_CYCLE_CADENCE` to the schema `Literal`s** (#2) — converts a silent governance gap into a loud failure. ~30 min.
5. **Single `RepoHost` Literal + `SUPPORTED_HOSTS` source** consumed by all 5 sites (#8) — ~30 min; also the first step of Overhaul O3.
6. **Delete the dead `SCHEMA_VERSION` export or trim the registry docstring** to match reality (#28, #30) — removes a false "multi-version is supported" signal. ~30 min.

**Tier 3 — readability / DRY (steady cleanup, all byte/unit-test-pinned):**
7. Extract the USD-band formatter (#1/#32) and the `_bullet_list` / `_text_or` / `_bullets_or` markdown helpers (#4, #43) into `website/_format.py`.
8. Collapse the four `run_pipeline` `_envelope` saves into a `_save(...)` closure (#13).
9. Unify the draft↔dict converters (#15) and the data-agent LLM-method guard helpers (#22/#34).
10. Extract `main()` into `_build_parser`/`_print_banner`/`_print_preview`/`_report` (#41); split `_render_baseline_block` out of `_render_production_measurement_plan` (#3).
11. Remaining minor DRY: `parse_pending_interrupt` (#20), `_merge_scaffold` (#7), `timed_call` (#11), `QualityCheck` outcome helper (#23), shared fake client (#25), `_format_qa` narrowing (#17), `_raise_repo_error` message helper (#33).

### 🔴 Architectural Overhauls (plan deliberately — high risk, regression-heavy, do as scoped sessions)

- **O1 — `Stage`-list pipeline driver** (#10/#38/#40/#44, `orchestrator/pipeline.py`). *Single highest-leverage refactor.* Replaces the god-function, the four save blocks, the resume tuples, and the dual stage-ordering encodings with one ordered stage list. **Prerequisite for cleanly wiring the real data step and any new pipeline stage.** Regression risk: resume-from-checkpoint is the load-bearing, side-effect-sensitive path — needs the full existing resume test matrix green plus new per-stage tests. *Multi-session.*
- **O2 — Shared `llm_json` helper across the two Anthropic clients** (#31). Must respect the standalone-wheel boundary (helper lives in the data-agent package, or a new shared micro-package). Do **after** quick-win #16 so the bug is gone first. *~1 session.*
- **O3 — `REPO_PLATFORMS` registry** (#35 + #8/#9/#12/#6). Centralizes platform selection so a 3rd host is one registry entry. Touches CLI, config, run_pipeline, governance CI renderers. Start from quick-win #5. *~1 session.*
- **O4 — Controlled-vocabulary single-source-of-truth** (#14 + #27/#24). Promote all enums to `common.py` Literals and derive prompts via `get_args`. Cross-package (data-agent vocabularies too). Best sequenced *after* the Tier-1/Tier-2 quick wins have fixed the live drift. *~1 session.*

> **Sequencing note:** O1 and O3 share a philosophy (replace scattered hardcoded enumerations with one registry/ordered-list). Doing O1 first establishes the pattern; O3/O4 then follow the same shape. None of the overhauls are urgent — the binary/fixed forms work correctly today. They become urgent the moment the corresponding roadmap item is picked up, which is precisely why this audit flags them now.

---

## 8. Structural Observations

1. **The debt is a "selection vs behavior" asymmetry.** Behavioral seams (Protocols, callable injection) are excellent; *selection* seams (which adapter, which provider, which stage) and *vocabularies* are hardcoded enumerations. Every overhaul is an instance of this one root cause. The structural fix is uniform: **derive scattered enumerations from one registry / `get_args(Literal)` source.**
2. **Documented decoupling is sometimes over-applied.** The 4A/4B "no cross-import" rule correctly protects scaffold modules but is invoked to justify byte-duplicating a 3-line formatter (#1) and re-declaring a Literal in 5 files. Decoupling *scaffolds* ≠ refusing to share *leaf utilities* in the same package.
3. **Drift is invisible because vocabularies bypass the type system.** `regulatory_frameworks: list[str]` and `expected_row_count_order: str` are typed loosely, so producer/consumer disagreements (the `GDPR_ART_22` gap, the `MAX_QUESTIONS` UI lie) survive mypy and most tests. Tightening these to `Literal`s + import-time assertions would have caught both at build time.
4. **Complexity is length, not depth.** No deeply-nested spaghetti was found; the "god-functions" are long-but-shallow and well-commented. They're maintainability and merge-friction risks, not correctness traps — which is why most are quick wins.
5. **Test coverage is the safety net that makes these refactors viable.** Every `render_*` function is byte-pinned and the resume matrix is thorough; the audit's "quick win" classifications lean on that. Preserve the byte-tests as the acceptance gate for any extraction.

---

## Appendix A — All 44 Confirmed Findings

*Sorted by severity, then risk (overhauls first), then dimension. Locations are post-verification (line ranges corrected by the per-file verifiers). `data-agent/` = `packages/data-agent/src/model_project_constructor_data_agent/`; other paths relative to `src/model_project_constructor/`.*

| # | Dim | Sev | Risk | Location | Finding |
|---|-----|-----|------|----------|---------|
| 10 | Complexity | moderate | overhaul | `orchestrator/pipeline.py:224-392` | run_pipeline is a 170-line god-function gating four stages by repeated literal tuples |
| 40 | Complexity | moderate | overhaul | `orchestrator/pipeline.py:224-392` | run_pipeline carries the entire 4-stage orchestration sequence inline |
| 31 | Duplication | moderate | overhaul | `agents/intake/anthropic_client.py:115-319` | JSON-extraction + Claude-call + client-construction logic duplicated (and divergent) across the two Anthropic clients |
| 35 | Extensibility | moderate | overhaul | `agents/website/cli.py:166-191` | Repo-platform selection is a hardcoded gitlab/github binary scattered across 6+ files |
| 38 | Extensibility | moderate | overhaul | `orchestrator/pipeline.py:224-392` | Pipeline is a fixed 3-stage Intake→Data→Website sequence, not a composed step list |
| 14 | Extensibility | moderate | overhaul | `agents/intake/anthropic_client.py:103-191` | Enum vocabularies hardcoded inline in prompt prose, duplicating the v1 schema Literals |
| 3 | Complexity | moderate | quick_win | `agents/website/templates.py:464-570` | `_render_production_measurement_plan` mixes baseline interpolation with methodology rendering |
| 41 | Complexity | moderate | quick_win | `scripts/run_pipeline.py:405-644` | main() is a 240-line procedure mixing parsing, banner, wiring, execution, reporting |
| 1 | Duplication | moderate | quick_win | `agents/website/governance_templates.py:364-374` | USD-band formatter duplicated verbatim across the two template modules |
| 16 | Duplication | moderate | quick_win | `agents/intake/anthropic_client.py:306-319` | Intake's _extract_json is a stale, known-buggy copy of the data-agent helper |
| 15 | Duplication | moderate | quick_win | `agents/intake/nodes.py:192-211` | Draft↔dict round-trip helpers triplicated across anthropic_client, nodes, and fixture |
| 19 | Duplication | moderate | quick_win | `ui/intake/templates.py:64-163` | User-facing question cap is hardcoded and factually wrong vs. MAX_QUESTIONS (says 10, is 20) |
| 2 | Extensibility | moderate | quick_win | `agents/website/governance_templates.py:39-66` | Risk-tier and cycle-time enum members re-hardcoded, decoupled from the schema literals |
| 39 | Extensibility | moderate | quick_win | `agents/website/governance_templates.py:77-103` | Regulatory-framework dict has already drifted from the intake prompt (GDPR_ART_22 unmapped) |
| 8 | Extensibility | moderate | quick_win | `agents/website/cli.py:42-43` | {gitlab, github} platform enumeration duplicated across five files, no single source |
| 44 | Complexity | minor | overhaul | `orchestrator/pipeline.py:80-173` | determine_resume_point encodes a multi-row truth table as a manual nested-if cascade |
| 42 | Complexity | minor | quick_win | `agents/website/governance_templates.py:762-845` | build_governance_files concentrates the only tier/flag branch ladder in a flat module |
| 43 | Complexity | minor | quick_win | `agents/website/templates.py:464-570` | _render_production_measurement_plan: nested baseline branch + field-defaulting blocks |
| 17 | Complexity | minor | quick_win | `agents/intake/anthropic_client.py:255-263` | _format_qa carries a dead dict\|dataclass union the type contract forbids |
| 18 | Complexity | minor | quick_win | `agents/intake/nodes.py:123-163` | finalize_node concentrates four completeness rules + a discarded validate-by-side-effect call |
| 4 | Duplication | minor | quick_win | `agents/website/templates.py:348-358` | 'list-or-placeholder' Markdown idiom repeated across ~8 sites (one variant differs) |
| 32 | Duplication | minor | quick_win | `agents/website/templates.py:303-312` | _format_usd_band / _usd_band are byte-identical formatters in sibling modules |
| 7 | Duplication | minor | quick_win | `agents/website/nodes.py:130-191` | Four scaffold_* nodes repeat the pending-dict + governance_paths merge boilerplate |
| 13 | Duplication | minor | quick_win | `orchestrator/pipeline.py:255-361` | Four near-identical _envelope save blocks inline in run_pipeline |
| 11 | Duplication | minor | quick_win | `orchestrator/metrics.py:132-138` | make_logged_runner and make_measured_runner duplicate the perf_counter timing wrapper |
| 21 | Duplication | minor | quick_win | `ui/intake/templates.py:132-198` | Draft/governance rendering duplicated between _render_review and _render_complete |
| 20 | Duplication | minor | quick_win | `ui/intake/runner.py:119-139` | LangGraph interrupt-extraction idiom duplicated between runner.py and agent.py |
| 22 | Duplication | minor | quick_win | `data-agent/anthropic_client.py:113-354` | Six LLM methods repeat the same prompt→call→extract→typecheck→map scaffold |
| 26 | Duplication | minor | quick_win | `data-agent/anthropic_client.py:326-432` | Inventory-block and table-summary rendering duplicate column-preview logic |
| 34 | Duplication | minor | quick_win | `data-agent/anthropic_client.py:146-163` | extract_json + isinstance-guard + coercion block repeated across 6 data + 4 intake methods |
| 23 | Duplication | minor | quick_win | `data-agent/nodes.py:94-149` | QualityCheck constructor copy-pasted three times inside nested execute_qc loops |
| 25 | Duplication | minor | quick_win | `data-agent/cli.py:198-296` | _FakeCLIClient duplicates the test-suite FakeLLMClient (5 shared methods) |
| 28 | Duplication | minor | quick_win | `schemas/v1/common.py:9` | SCHEMA_VERSION constant is dead — every schema hardcodes "1.0.0" independently |
| 29 | Duplication | minor | quick_win | `schemas/envelope.py:20-23` | HandoffEnvelope re-declares extra="forbid" instead of sharing StrictBase config |
| 33 | Duplication | minor | quick_win | `agents/website/gitlab_adapter.py:158-171` | github/gitlab adapters share an exception-mapping idiom (bodies correctly NOT merged) |
| 6 | Extensibility | minor | quick_win | `agents/website/governance_templates.py:793-796` | CI-platform handled by string if/else + hardcoded path set rather than a registry |
| 5 | Extensibility | minor | quick_win | `agents/website/templates.py:769-807` | build_base_files hardcodes the 4A file manifest; src/test pairing unenforced |
| 9 | Extensibility | minor | quick_win | `agents/website/cli.py:167-190` | CLI hardcodes host→adapter dispatch with inline lazy imports instead of a factory |
| 12 | Extensibility | minor | quick_win | `orchestrator/config.py:91-144` | host enumeration + derived url/token mappings hardcoded as parallel ternaries |
| 24 | Extensibility | minor | quick_win | `data-agent/llm.py:40-44` | row_count_order / unit enumerations duplicated as bare strings outside their schema Literal |
| 36 | Extensibility | minor | quick_win | `data-agent/cli.py:192-195` | No LLM-provider seam — every real client is hardwired to AnthropicLLMClient |
| 27 | Extensibility | minor | quick_win | `schemas/v1/intake.py:48-62` | ValueMeasurementPlan inline enums hand-copied into the prompt, read as untyped strings |
| 30 | Extensibility | minor | quick_win | `schemas/registry.py:7-58` | Registry advertises multi-version/migration support but provides no version-resolution seam |
| 37 | Extensibility | minor | quick_win | `schemas/registry.py:9-32` | Schema versioning advertises v2/migrations but only v1 exists; versions hardcoded at emit sites |

---

## Appendix B — Audit Provenance

- **Workflow:** `tech-debt-audit` (run `wf_f0a9344e-6b7`), 33 agents, ~1.56M tokens, 379 tool calls, ~71 min wall-clock.
- **Auditors (13):** arch-map, features-context, 7 module slices (website-templates, website-orchestration, orchestrator, intake-agent, ui-intake, data-agent-package, schemas+data-stub), 3 cross-cutting (duplication, extensibility, complexity).
- **Verification:** one adversarial verifier per file (re-read in full; default-refute). 44 raw → 44 confirmed, 0 refuted, 6 severity-deflations, ~12 line-range corrections.
- **Limitations:** static read-only review — no runtime profiling, no live-LLM execution. Test code and documentation were excluded from scope. "Upcoming features" are grounded in `ROADMAP.md` + `docs/planning/` as of 2026-06-01; some listed phases may already be partially shipped (noted per-item in the workflow output).
