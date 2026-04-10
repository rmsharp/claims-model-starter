# Backlog

## Active

### Architecture Plan (Milestone 1)
- [ ] **Define agent boundaries** — Specify each agent's responsibilities, inputs, outputs, and failure modes. Agents: Intake Agent (Step 2), Data Agent (Step 3), Website Agent (Steps 4-5).
- [ ] **Design inter-agent handoff protocol** — Define the structured report format passed between agents. Must include: required fields, validation rules, versioning. Each handoff report should be self-contained enough that the receiving agent needs no other context.
- [ ] **Define output document schemas** — Formal schemas for: Intake Report (4 sections: Business Problem, Proposed Solution, Model Solution, Estimated Value), Data Report (queries, quality checks, validation results), Website sections (Business Understanding, Implementation Plans, Data/EDA, Model Build).
- [ ] **Choose technology stack** — Agent orchestration framework, LLM provider/model selection, GitLab API integration approach, database/query execution strategy.

## Up Next

### Intake Agent (Milestone 2 — Step 2)
- [ ] **Design interview flow** — One-question-at-a-time guided discussion, max 10 questions, domain-specific to P&C insurance claims. Must converge on the 4 output sections.
- [ ] **Build intake agent system prompt** — Expert data scientist / business analyst / consultant persona for claims organization context. See `initial_purpose.txt` for the example prompt.
- [ ] **Implement document generation** — Agent produces structured report with: Business Problem, Proposed Solution, Model Solution (target variable, concept to model, candidate features, model type, evaluation metrics), Estimated Value.
- [ ] **Add review loop** — After drafting, agent presents document to user for confirmation/adjustment before finalizing.

### Data Agent (Milestone 3 — Step 3)
- [ ] **Build query generation agent** — Receives intake report, generates SQL queries to collect relevant data for the model described in the report.
- [ ] **Implement quality-check query generation** — Automated queries that validate data quality: null rates, distribution checks, expected ranges, join integrity, row counts.
- [ ] **Implement data expectation confirmation** — Agent verifies that collected data matches expectations from the intake report (correct granularity, time range, population).
- [ ] **Generate data summary report** — Document summarizing: queries written, data quality findings, confirmed/unconfirmed expectations, recommendations.

### Website Agent (Milestone 4 — Steps 4-5)
- [ ] **Build website section generator** — Creates draft content for each website section from intake + data reports.
- [ ] **Implement initial model build** — Feature engineering, feature selection, initial model training (classification/regression based on intake report), evaluation metrics.
- [ ] **GitLab project scaffolding** — Create GitLab project with proper structure, include all reports, queries, website, and ideas for extensions.
- [ ] **Package extension ideas** — Generate suggestions for additional tests, alternative approaches, and potential extensions based on all prior steps.

### Integration (Milestone 5)
- [ ] **Wire pipeline end-to-end** — Connect agents with handoff protocol, test with sample business ideas.
- [ ] **Error handling between steps** — What happens when an agent fails or produces incomplete output? Retry, escalate, or partial handoff?
- [ ] **End-to-end test suite** — At least 2 complete pipeline runs with different business ideas (e.g., subrogation prediction, fraud detection).
