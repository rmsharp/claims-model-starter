# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

- [ ] **Data agent: metadata discovery mode** — Add a discovery mode to the data agent that queries database metadata (`information_schema`, catalog tables) to identify relevant tables before generating training set queries. The data agent was designed to be reusable as a standalone query tool (per `docs/architecture-history/initial_purpose.txt`); discovery mode extends that to data exploration.
- [ ] **Statistical terminology glossary** — Create `docs/style/statistical_terms.md` defining terms like probability vs likelihood, and inject it into agent system prompts so LLM-generated content uses correct statistical terminology instead of reproducing common conflations from training data.
- [ ] **Tutorial renderer: migrate to MkDocs (or equivalent) with copy-button plugin** — The prose/code splits shipped in Session 55 give each command its own fenced block so GFM/pandoc readers can copy one command at a time, but neither renderer provides per-block copy buttons. A renderer with a copy-button plugin (MkDocs Material's `copy_button`, Docusaurus's default Prism theme, etc.) would close the UX loop. Scope: renderer migration only; tutorial prose stays put.
