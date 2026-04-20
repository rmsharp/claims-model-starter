# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

- [ ] **Tutorial renderer: migrate to MkDocs (or equivalent) with copy-button plugin** — The prose/code splits shipped in Session 55 give each command its own fenced block so GFM/pandoc readers can copy one command at a time, but neither renderer provides per-block copy buttons. A renderer with a copy-button plugin (MkDocs Material's `copy_button`, Docusaurus's default Prism theme, etc.) would close the UX loop. Scope: renderer migration only; tutorial prose stays put. **Plan filed:** `docs/planning/tutorial-renderer-migration-plan.md` (Session 65). Phase 1 (local MkDocs setup) in progress Session 66; Phase 2 (CI publish to GitHub Pages) is a separate future session.
- [ ] **Data source inventory — Phase 4 (optional): Intake coupling** — Add a converter in the orchestrator that reads `IntakeReport.qa_pairs` and emits interview-sourced `DataSourceEntry` items (`producer_type="interview"`, provenance cites Session 56's SYSTEM_INTERVIEWER-probed systems). Opt-in flag (e.g. `--inventory-from-intake`). Default off. Defer indefinitely unless pilot demand surfaces — the contract supports it without Phase 4 landing. See plan §9 Phase 4.
