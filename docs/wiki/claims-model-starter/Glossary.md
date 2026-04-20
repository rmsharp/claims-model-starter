# Glossary

## Domain terms (P&C claims)

| Term | Definition |
|------|-----------|
| **P&C** | Property and Casualty insurance. Covers auto and property policies. |
| **Claims organization** | The division responsible for receiving, investigating, adjusting, and paying insurance claims. |
| **Subrogation** | The process of recovering costs from an at-fault party after paying a claim. The insurer "steps into the shoes" of the insured to pursue recovery. |
| **Adjuster** | A claims professional who investigates claims, determines coverage, and settles payments. |
| **Reserve** | The estimated future cost of a claim, set by the adjuster and updated as information changes. |
| **Loss** | The amount paid out on a claim. |
| **First Notice of Loss (FNOL)** | The initial report of a claim by the insured to the insurance company. |
| **Claimant** | The person making a claim (may be the insured or a third party). |
| **Coverage** | The specific protections and limits defined in an insurance policy. |

## Pipeline terms

| Term | Definition |
|------|-----------|
| **Intake Agent** | The first agent in the pipeline. Conducts a guided interview with a business stakeholder. |
| **Data Agent** | The second agent. Generates SQL queries and quality checks from a data request. |
| **Website Agent** | The third agent. Scaffolds a repository project from intake and data reports. |
| **IntakeReport** | Structured output of the Intake Agent: business problem, proposed solution, model solution, estimated value, governance metadata. |
| **DataReport** | Structured output of the Data Agent: primary queries, quality checks, confirmed/unconfirmed expectations, data quality concerns. |
| **RepoProjectResult** | Structured output of the Website Agent: project URL, commit SHA, files created, governance manifest. |
| **HandoffEnvelope** | Versioned wrapper for inter-agent payloads. Contains metadata (run ID, source/target agent, schema version) plus the payload. |
| **Checkpoint** | A persisted JSON envelope representing a completed inter-agent handoff. Used for inspection and potential resumption. |
| **Run ID** | UUID assigned by the orchestrator to a single pipeline execution. All checkpoints for one run share the same run ID. |

## Governance terms

| Term | Definition |
|------|-----------|
| **Risk tier** | Classification of model risk severity. Tier 1 (critical) through Tier 4 (low). Determines governance artifact depth. |
| **Cycle time** | How frequently the model's decisions are acted upon. Strategic (annual), tactical (quarterly), operational (monthly), continuous (real-time). |
| **Model card** | Standardized documentation of a model's purpose, performance, and limitations (Mitchell et al. 2019). |
| **Datasheet** | Standardized documentation of a dataset's composition, collection process, and biases (Gebru et al. 2021). |
| **Three-pillar validation** | Validation framework: conceptual soundness, ongoing monitoring, outcomes analysis. |
| **Deployment gates** | Staged rollout checklist: shadow mode, limited production, full production. |
| **LCP** | Life Cycle Process. A structured review framework with gates at concept, development, validation, deployment, and post-deployment. |
| **Model registry** | Machine-readable record of a model's identity, owner, risk tier, and governance status. |

## Regulatory frameworks

| Framework | Full name | Scope |
|-----------|-----------|-------|
| **SR 11-7** | Federal Reserve Supervisory Letter 11-7 | Guidance on Model Risk Management. Applies to banking organizations. Requires model validation, documentation, and governance. |
| **NAIC AIS** | NAIC Model Bulletin on Artificial Intelligence Systems | National Association of Insurance Commissioners guidance on AI/ML in insurance. |
| **EU AI Act** | European Union Artificial Intelligence Act | Regulation on AI systems. Articles 9-15 cover risk management, data governance, transparency, human oversight. |
| **ASOP 56** | Actuarial Standard of Practice No. 56 | Modeling standard for actuaries. Covers model selection, implementation, and communication of results. |

## Statistical terms

> **Curated subset.** See [`docs/style/statistical_terms.md`](../../style/statistical_terms.md) for the full glossary, authoritative sources, and amendment process.

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Probability** | The chance of an event occurring, expressed as a number between 0 and 1. | Often conflated with "likelihood" in casual usage. In this project, use "probability" when referring to P(event). |
| **Likelihood** | In statistical inference, the likelihood function measures how well a set of parameter values explains observed data. It is not a probability of the event. | "Likelihood" has a precise technical meaning distinct from "probability." Do not use interchangeably. |
| **Target variable** | The outcome the model is trained to predict. | Sometimes called "dependent variable" or "response variable." |
| **Feature** | An input variable used to predict the target. | Sometimes called "independent variable," "predictor," or "covariate." |
| **Supervised learning** | ML approach where the model learns from labeled examples (known target values). | Contrasted with unsupervised learning (no target variable). |

## Technology terms

| Term | Definition |
|------|-----------|
| **LangGraph** | Python framework for building stateful, multi-step LLM applications as directed graphs. Provides built-in checkpointing. |
| **Quarto** | Open-source publishing system for scientific and technical documents. Supports `.qmd` files with embedded Python/R code. |
| **Pydantic** | Python library for data validation using type annotations. v2 provides high-performance validation via a Rust core. |
| **uv** | Fast Python package installer and resolver. Used as the project's package manager with workspace support. |
| **RepoClient** | Python protocol defining the interface for repository operations (`create_project`, `commit_files`). |
| **SSE** | Server-Sent Events. HTTP-based protocol for streaming data from server to client. Used by the intake web UI. |
| **HTMX** | Lightweight JavaScript library for building dynamic UIs using HTML attributes instead of JavaScript. |
