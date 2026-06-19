# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

### Harden the `cycle_time` cadence definitions and corpus (gap #2 robustness follow-up, ready-for-agent)

**Why:** the S175 cadence definitions are validated on the 4 governance corpus cases (cycle_time 100%), but an S175 adversarial review found they are fit to anchors where **cadence is co-linear with frequency** — so the intended `tactical` (per-case workflow decision support) vs `operational` (periodic institutional close-step) distinction is **never actually exercised** by a case where role and frequency diverge. A model that is BOTH workflow-embedded AND batch-scheduled (e.g. an overnight-scored adjuster workqueue) is genuinely ambiguous under the current text, which leads with frequency cues. There is also no vocabulary member for **event-driven/episodic** cadences (e.g. a catastrophe-surge model triggered by a hurricane landfall), and the `subrogation` reference rationale prose ("operational would imply streaming auto-decisioning") is now mildly inconsistent with the canonical `operational` definition (the label `tactical` is correct; the prose predates the definitions).

**Acceptance criteria (pick the subset the operator prioritises):**
- Add a governance corpus case where **role and frequency diverge** (workflow-embedded decision support on a fixed batch cadence) to actually test the `tactical`/`operational` boundary; bless its reference label.
- Consider refining `CYCLE_TIME_DEFINITIONS` to lead with the **output-purpose** discriminator (per-case decision support → tactical; periodic portfolio/institutional artifact → operational) rather than frequency, then re-measure (must still hold on the existing 4 and classify the new divergent case correctly).
- Consider whether `CycleTime` needs an **event-driven/episodic** member (a schema `Literal` change — larger blast radius; weigh against YAGNI).
- Optionally align the `subrogation` rationale prose with the canonical `operational` definition (label unchanged).
- `src/`/corpus/eval workstream; do **NOT** lower thresholds (#129).

<!-- Completed Session 172 (2026-06-19): Quarto explainer for the live interview-convergence
     test. Delivered per operator override as a PDF *document* (not a slide deck) at
     docs/explainers/interview-convergence-explainer.qmd (+ .pdf). See CHANGELOG.md. -->
