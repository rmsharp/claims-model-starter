# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

### Define the `cycle_time` cadence vocabulary in `SYSTEM_GOVERNANCE` (gap #2 follow-up, ready-for-agent)

**Why:** the S174 live re-measure found governance `cycle_time` agreement at 50%. Both misses (`fraud_triage` model `operational` vs ref `continuous`; `reserving_adequacy` model `tactical` vs ref `operational`) are a **prompt-definition gap**: `SYSTEM_GOVERNANCE` (`src/model_project_constructor/agents/intake/anthropic_client.py:140`) lists the bare vocab `cycle_time ∈ {strategic, tactical, operational, continuous}` with **no definitions**, so the model and the (defensible, operator-ratified) references use the words differently. Operator ruling (S174): keep the references; close the gap by defining the terms.

**Acceptance criteria:**
- Each of `{strategic, tactical, operational, continuous}` gets a concise boundary definition in `SYSTEM_GOVERNANCE` (e.g. continuous = real-time/streaming per-event; operational = recurring routine within ongoing operations; tactical = time-boxed/periodic intervention; strategic = multi-quarter/business-cycle).
- Preserve the O4 controlled-vocabulary single-sourcing — members still DERIVE from the `CycleTime` `Literal` via `join_members` (add definitions as prose; do NOT hand-list the enum — see `docs/architecture-history/o4-controlled-vocabulary-plan.md`).
- Update the `SYSTEM_GOVERNANCE` substring pins in `tests/agents/intake/test_anthropic_client.py`.
- Re-measure governance live afterwards (cheap: ~20 `classify_governance` calls, no interview sweep — see the S174 method in `SESSION_NOTES.md`) and record the new `cycle_time` agreement in `PHASE_E_AGREEMENT_REPORT.md`. Do **NOT** lower thresholds (#129).
- `src/` change → DEVELOPMENT workstream, its own session.

### Investigate `fraud_triage` governance under-rating (gap #2 model-quality signal, needs-investigation)

**Why:** S174 found the live model (anthropic default) rates `fraud_triage` — a consumer-facing FNOL fraud-routing model — `risk_tier=tier_2_high` (5/5), citing the human-in-the-loop SIU gate, where the governance-correct tier is `tier_1_critical` (operator-confirmed S174; the prompt's own "be conservative, pick the stricter tier" rule favours tier_1). This is the gap #2 `laxer_miss` (5) — a genuine **model-quality** signal: the classifier is insufficiently conservative on exactly the high-stakes consumer-facing case where it matters most. The reference is correct and **kept**; this is about the model, not the corpus.

**Acceptance criteria (investigate, then a scoped fix):**
- Determine whether stronger `SYSTEM_GOVERNANCE` guidance (e.g. "a human-in-the-loop review gate does NOT by itself lower the tier when the output is consumer-facing and adverse-action-adjacent") and/or a few-shot example closes the gap without over-flagging the other cases.
- Re-measure governance live; `fraud_triage` should reach `tier_1_critical` and `laxer_miss` → 0 with no regression on the stricter-but-credited cases.
- Do **NOT** lower the reference to chase the metric (#129 spirit — that would mask a real model weakness).
- `src/` (prompt) change → DEVELOPMENT workstream, its own session.

<!-- Completed Session 172 (2026-06-19): Quarto explainer for the live interview-convergence
     test. Delivered per operator override as a PDF *document* (not a slide deck) at
     docs/explainers/interview-convergence-explainer.qmd (+ .pdf). See CHANGELOG.md. -->
