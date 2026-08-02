# Claims Model Starter Wiki

The **Model Project Constructor** is a multi-agent pipeline that turns a business stakeholder's model idea into a governance-ready repository project, scaffolded for a data science team to refine.

## What it does

A stakeholder has a rough idea for a predictive model (e.g., "predict subrogation success on auto claims"). The pipeline conducts a guided interview, generates SQL queries for data collection, and scaffolds a complete project repository with draft analyses, tested Python modules, CI configuration, and governance artifacts proportional to model risk.

It also captures the **business value** end-to-end: the interview elicits a business case and a value-measurement plan (baseline metric, counterfactual design, success criteria), the data step measures the current-state baseline, and the generated repository carries both a pre-construction business case and a post-production measurement plan — so a deployed model's realised value can be measured, not just estimated.

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

## What it depends on

The constructor itself runs on Python 3.11+ with `uv` and `git`. No JavaScript build, no Docker required for development, no database server. External services in scope are an LLM backend (one of three, one per run) and a git host (GitLab *or* GitHub — one per run). Each is gated by one credential, except the two alternative LLM backends, which authenticate by other means:

| Service | Credential | When required |
|---|---|---|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Any live run that uses the intake or data agents (the default provider) |
| **AWS Bedrock** *(alternative Claude backend)* | AWS credential chain (IAM role, SSO, or profile) plus a region (`AWS_REGION`) — not a single API-key env var | Instead of the Anthropic API, when a run selects the `bedrock` provider (`--provider bedrock` on the pipeline script, or `INTAKE_LLM_PROVIDER=bedrock` for the intake web UI). Implemented and unit-tested, but **never exercised live** — every measured result in this project is `anthropic`-only |
| **OpenCode CLI** *(alternative, vendor-agnostic backend)* | None read by this project — whatever the `opencode` binary's own configuration uses. Requires the binary on `PATH` (`npm i -g opencode-ai`) and an explicitly chosen model, since this provider pins no default | When a run selects the `opencode` provider. Which vendor it actually reaches is decided by your OpenCode config, not by this repository. Shipped and unit-tested, but its **output quality is unmeasured** — see [AI Dependencies](AI-Dependencies) before relying on it |
| **GitLab** *or* **GitHub** | `GITLAB_TOKEN` or `GITHUB_TOKEN` | When the website agent targets that host (one host per run, not both) |

The **generated downstream project** is deliberately small (pandas + scikit-learn + sqlalchemy) and has **zero AI runtime dependency** — the data-science team can run it with no API key. AI-generated content is materialised as static markdown, SQL, and Quarto analysis narratives at construction time.

See [Software Bill of Materials](Software-Bill-of-Materials) for full dependency tables and [Security Considerations](Security-Considerations) for credential handling.

## Wiki contents

- [Getting Started](Getting-Started) -- Install, first run, verify
- [Architecture Overview](Architecture-Overview) -- System architecture, tech/vendor posture, and honest enterprise-readiness status, for architects and technical decision-makers
- [Pipeline Overview](Pipeline-Overview) -- How the agents work together
- [Intake Interview Design](Intake-Interview-Design) -- Interview strategy, caps, tips for stakeholders
- [Generated Project Structure](Generated-Project-Structure) -- What the output repository contains
- [Governance Framework](Governance-Framework) -- Risk tiers, regulatory mapping, artifact inventory
- [Development Workflow](Development-Workflow) -- How the data science team uses the generated project
- [Data Guide](Data-Guide) -- Queries, datasheets, data loading
- [Agent Reference](Agent-Reference) -- Details on each agent's inputs, outputs, and behavior
- [Schema Reference](Schema-Reference) -- Every Pydantic schema, field by field
- [Worked Examples](Worked-Examples) -- End-to-end traces: subrogation (tier-3) and renewal profitability (tier-1)
- [Extending the Pipeline](Extending-the-Pipeline) -- Adding agents, adapters, governance artifacts, regulatory frameworks
- [Monitoring and Operations](Monitoring-and-Operations) -- Deployment, checkpoints, operations
- [Security Considerations](Security-Considerations) -- Credentials, network boundaries, what the LLM sees
- [Software Bill of Materials](Software-Bill-of-Materials) -- All dependencies, versions, and constraints
- [AI Dependencies](AI-Dependencies) -- The AI/LLM dependencies, how each is used, and the risks they pose
- [Architecture Decisions](Architecture-Decisions) -- Key design choices and rationale
- [Evolution](Evolution) -- How the project grew from concept to current state
- [Changelog](Changelog) -- Phase-by-phase history of notable changes
- [Contributing](Contributing) -- Dev setup, code-quality gates, commit convention, PR workflow
- [License](License) -- This wiki's own license terms (MIT, mirroring the repository)
- [Glossary](Glossary) -- Domain and technical terminology
- [Content Recommendations](Content-Recommendations) -- Suggested additions and priorities for this wiki
