# Claims Model Starter Wiki

The **Model Project Constructor** is a multi-agent pipeline that turns a business stakeholder's model idea into a governance-ready repository project, scaffolded for a data science team to refine.

## What it does

A stakeholder has a rough idea for a predictive model (e.g., "predict subrogation success on auto claims"). The pipeline conducts a guided interview, generates SQL queries for data collection, and scaffolds a complete project repository with draft analyses, tested Python modules, CI configuration, and governance artifacts proportional to model risk.

## The 6-step process

| Step | Who | What happens |
|------|-----|-------------|
| 1 | Stakeholder | Has an idea for a model |
| 2 | **Intake Agent** | Guided interview at `go/modelintake` producing an `IntakeReport` |
| 3 | **Data Agent** | Generates SQL queries, quality checks, and data expectations producing a `DataReport` |
| 4-5 | **Website Agent** | Scaffolds a GitLab/GitHub repository with draft model website |
| 6 | Data Science Team | Begins refinement work in the generated repo |

## Domain context

This tool serves a **claims organization within a property & casualty insurance company** (auto and property policies). The intake agent acts as an expert data scientist, business analyst, and consultant focused on this domain.

## Wiki contents

- [Getting Started](Getting-Started) -- Install, first run, verify
- [Pipeline Overview](Pipeline-Overview) -- How the agents work together
- [Intake Interview Design](Intake-Interview-Design) -- Interview strategy, caps, tips for stakeholders
- [Generated Project Structure](Generated-Project-Structure) -- What the output repository contains
- [Governance Framework](Governance-Framework) -- Risk tiers, regulatory mapping, artifact inventory
- [Development Workflow](Development-Workflow) -- How the data science team uses the generated project
- [Data Guide](Data-Guide) -- Queries, datasheets, data loading
- [Agent Reference](Agent-Reference) -- Details on each agent's inputs, outputs, and behavior
- [Schema Reference](Schema-Reference) -- Every Pydantic schema, field by field
- [Monitoring and Operations](Monitoring-and-Operations) -- Deployment, checkpoints, operations
- [Security Considerations](Security-Considerations) -- Credentials, network boundaries, what the LLM sees
- [Software Bill of Materials](Software-Bill-of-Materials) -- All dependencies, versions, and licenses
- [Architecture Decisions](Architecture-Decisions) -- Key design choices and rationale
- [Glossary](Glossary) -- Domain and technical terminology
- [Content Recommendations](Content-Recommendations) -- Suggested additions and priorities for this wiki
