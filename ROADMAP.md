# Roadmap

## Current Milestone
**M1: Architecture & Pipeline Design**

Design the multi-agent pipeline that takes a business model idea from intake interview through data collection, validation, and initial model website creation. The output is a GitLab project ready for a data science team to begin work.

**Why:** The pipeline has 4 distinct agents with handoff protocols between them. Getting the architecture right — agent boundaries, data formats, handoff reports, error handling — determines the quality of everything built on top.

### Pipeline Overview (6 Steps)

| Step | Owner | Input | Output |
|------|-------|-------|--------|
| 1 | Business stakeholder | Model idea | Visits go/modelintake |
| 2 | **Intake Agent** | Guided interview (up to 10 questions) | Structured report: Business Problem, Proposed Solution, Model Solution, Estimated Value |
| 3 | **Data Agent** | Intake report | SQL queries for data collection + quality-check queries + data validation results |
| 4 | (handoff) | Data report + queries | Packaged handoff to website agent |
| 5 | **Website Agent** | Data report + queries + intake report | GitLab project with draft model website (Business Understanding, Implementation Plans, Data section with EDA, Initial model build & evaluation) |
| 6 | Data science team | GitLab project | Refined model (human-driven from here) |

### Domain Context

All agents operate within the context of a **claims organization in a property & casualty insurance company** selling auto and property policies. The intake agent acts as expert data scientist, business analyst, and consultant in this domain.

## Planned

### Phase 1: Architecture (Current)
- Define agent boundaries and responsibilities
- Design inter-agent handoff protocol (report format, required fields, validation)
- Define output document schemas for each step
- Choose technology stack for agent orchestration

### Phase 2: Intake Agent (Step 2)
- Build the guided interview agent for go/modelintake
- Implement one-question-at-a-time interview flow (max 10 questions)
- Generate structured output document with 4 sections: Business Problem, Proposed Solution, Model Solution (target variable + inputs), Estimated Value
- Domain-specific prompt engineering for P&C insurance claims context

### Phase 3: Data Agent (Step 3)
- Build the data collection agent that receives intake reports
- SQL query generation for relevant data collection
- Quality-check query generation (data validation, expectation confirmation)
- Data summary report generation

### Phase 4: Website Agent (Steps 4-5)
- Build the model website generator agent
- Draft website sections: Business Understanding, Implementation Plans & Measuring Value, Data section (query explanation, validation, EDA), Model build & evaluation (feature engineering, selection, initial models)
- GitLab project scaffolding and creation
- Package results from steps 2-4 with ideas for additional tests and extensions

### Phase 5: Integration & End-to-End Pipeline
- Wire agents together with handoff protocols
- End-to-end testing with sample business ideas
- Error handling and recovery between agent steps

## What's Built

### Methodology
- Iterative Session Methodology installed (SESSION_RUNNER, SAFEGUARDS, SESSION_NOTES)
- Task tracking (BACKLOG, CHANGELOG, ROADMAP)
- Framework reference docs in docs/methodology/

### Project Foundation
- `initial_purpose.txt` — Original vision document with pipeline description and worked examples for Steps 2 and 3

## Completed Milestones

*None yet — project is in initial setup.*
