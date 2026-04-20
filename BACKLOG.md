# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

- [ ] **Data source inventory — Phase 4 (optional): Intake coupling** — Add a converter in the orchestrator that reads `IntakeReport.qa_pairs` and emits interview-sourced `DataSourceEntry` items (`producer_type="interview"`, provenance cites Session 56's SYSTEM_INTERVIEWER-probed systems). Opt-in flag (e.g. `--inventory-from-intake`). Default off. Defer indefinitely unless pilot demand surfaces — the contract supports it without Phase 4 landing. See plan §9 Phase 4.
- [ ] **Statistical glossary — agent system prompt injection** — The glossary itself shipped in Session 61 at `docs/style/statistical_terms.md` (with amendment process and wiki integration instructions). This follow-up wires the glossary (or a curated subset) into the intake / data / website agent system prompts so generated reports use the precise statistical terminology natively, instead of relying on review-time enforcement.
- [ ] **Tutorial renderer: migrate to MkDocs (or equivalent) with copy-button plugin** — The prose/code splits shipped in Session 55 give each command its own fenced block so GFM/pandoc readers can copy one command at a time, but neither renderer provides per-block copy buttons. A renderer with a copy-button plugin (MkDocs Material's `copy_button`, Docusaurus's default Prism theme, etc.) would close the UX loop. Scope: renderer migration only; tutorial prose stays put.
