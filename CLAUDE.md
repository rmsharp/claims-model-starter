# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## SESSION PROTOCOL — FOLLOW BEFORE DOING ANYTHING

**Read and follow `SESSION_RUNNER.md` step by step.** It is your operating procedure for every session. It tells you what to read, when to stop, and how to close out.

**Three rules you will be tempted to violate:**
1. **Orient first** — Read SAFEGUARDS.md -> SESSION_NOTES.md -> run `methodology_dashboard.py` -> git status -> report findings -> WAIT FOR THE USER TO SPEAK
2. **1 and done** — One deliverable per session. When it's complete, close out. Do not start the next thing.
3. **Auto-close** — When done: evaluate previous handoff, self-assess, document learnings, write handoff notes, commit, report, STOP.

`SESSION_RUNNER.md` documents known failure modes and their countermeasures. The protocol compensates for documented tendencies to skip orientation, skip close-out, and continue past the deliverable.

## What This Project Is

**Model Project Constructor** — A multi-agent pipeline that takes a business idea from intake interview through data collection, validation, and initial model website creation, delivered as a GitLab project.

### The 6-Step Pipeline

1. **Business Intake Interview** — An agent conducts a guided discussion at go/modelintake to capture: business problem, proposed solution, model solution (target + inputs), estimated value
2. **Intake Report** — The intake agent writes a summary report and hands off to the data collection agent
3. **Data Collection & Validation** — An agent creates queries to collect relevant data, writes quality-check queries, and confirms expectations about data
4. **Data Report & Handoff** — The data agent summarizes queries and hands off (with queries) to the model website agent
5. **Initial Model Website** — An agent creates a GitLab project with a draft website containing: Business Understanding, Implementation Plans & Measuring Value, Data section (query explanation, validation, EDA), Initial model build & evaluation (feature engineering, selection, initial models)
6. **Data Science Team Handoff** — The GitLab project includes results from steps 2-4, plus ideas for additional tests and potential extensions

### Domain Context

This tool serves a **claims organization within a property & casualty insurance company** (auto and property policies). The intake agent acts as an expert data scientist, business analyst, and consultant focused on this domain.

### Agent Design Principles

Each agent in the pipeline follows these principles (derived from `initial_purpose.txt`):

1. **Agents produce structured reports, not free-form text.** Every agent's output has a defined schema with required sections. The receiving agent should be able to parse and act on the report without ambiguity.

2. **Agents hand off explicitly.** Step N writes a report, then hands it (and any artifacts like queries) to Step N+1. There is no shared state — everything the next agent needs must be in the handoff.

3. **The intake agent interviews, not interrogates.** It asks one question at a time (max 10), converging on the 4 output sections. It guides the business stakeholder with its own domain expertise — it doesn't just transcribe answers.

4. **The data agent is potentially reusable.** The `initial_purpose.txt` notes that this agent "would likely be useful for just writing queries in general" for analyst teams. Design it with reuse in mind.

5. **The website agent produces a draft, not a finished product.** The model website is an initial scaffold for the data science team to refine. It should contain reasonable defaults and clearly mark areas that need human judgment.

### Worked Examples (from initial_purpose.txt)

**Step 2 example:** The intake agent interviews a stakeholder about subrogation recovery in P&C claims. The output document describes: the business problem (lower subrogation outcomes due to new claims system), proposed solution (prompts/external systems to guide adjusters), model solution (supervised classification predicting successful subrogation), and estimated value (10% improvement in recovery rates = hundreds of thousands to millions annually).

**Step 3 note:** The data agent should be designed so it can also serve as a standalone query-writing tool for analyst teams (especially DAs) who spend significant time writing queries. Speeding up query work enables exploratory analysis that is currently infeasible.

## Key Files

- `initial_purpose.txt` — Original project vision with pipeline description and worked examples for Steps 2 and 3
- `BACKLOG.md` — Active and upcoming tasks, broken down by milestone
- `ROADMAP.md` — Pipeline overview table, milestone sequence, feature inventory
- `SESSION_NOTES.md` — Session continuity: active task, handoff notes, session history
- `SESSION_RUNNER.md` — Operating procedure for every session (customized Phase 1 mapping for this project)
- `SAFEGUARDS.md` — Commit discipline, blast radius limits, mode-switching rules
- `docs/methodology/` — Framework reference (ITERATIVE_METHODOLOGY.md, HOW_TO_USE.md, workstreams/)
