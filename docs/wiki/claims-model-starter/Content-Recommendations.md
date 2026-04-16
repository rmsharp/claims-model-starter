# Content Recommendations

This page documents what this wiki contains, what additional content would add value, and prioritized recommendations for future additions.

## Current wiki pages

| Page | Audience | Purpose |
|------|----------|---------|
| [Home](Home) | All | Landing page and navigation |
| [Getting Started](Getting-Started) | New users | Install, first run, verify |
| [Pipeline Overview](Pipeline-Overview) | All | How the three agents work together |
| [Intake Interview Design](Intake-Interview-Design) | Stakeholders, operators | Interview strategy, caps, governance pass, tips |
| [Generated Project Structure](Generated-Project-Structure) | Data science teams | What the output repository contains |
| [Governance Framework](Governance-Framework) | Governance/compliance, data science teams | Risk tiers, regulatory mapping, artifact inventory |
| [Development Workflow](Development-Workflow) | Data science teams | How to implement stubs and iterate |
| [Data Guide](Data-Guide) | Data science teams, analysts | Queries, datasheets, data loading |
| [Agent Reference](Agent-Reference) | Developers, operators | Detailed agent specs and schemas |
| [Schema Reference](Schema-Reference) | Developers, integrators | Every Pydantic schema — field by field |
| [Monitoring and Operations](Monitoring-and-Operations) | Operators | Deployment, checkpoints, troubleshooting |
| [Security Considerations](Security-Considerations) | Security reviewers, compliance | Credentials, network boundaries, LLM data exposure, read-only DB |
| [Software Bill of Materials](Software-Bill-of-Materials) | Security, compliance, operators | All dependencies and versions |
| [Architecture Decisions](Architecture-Decisions) | Developers, architects | Key design choices and rationale |
| [Glossary](Glossary) | All | Domain, pipeline, governance, and technical terms |

## Recommended additions (prioritized)

### High priority

These would fill gaps that real users will hit:

#### 1. Worked examples page

**What:** Two or three complete worked examples showing the pipeline end-to-end for different model types (classification, regression, unsupervised). Include the intake YAML fixture, the generated IntakeReport, the DataReport, and a screenshot or listing of the generated repository.

**Why:** The current documentation describes what happens; worked examples show it. Users learn faster from concrete examples than abstract descriptions. The `initial_purpose.txt` already contains a subrogation example that could be the first worked example.

**Audience:** New users, business stakeholders evaluating the tool.

#### 2. Intake interview design guide ✅ *shipped in Session 20A*

See [Intake Interview Design](Intake-Interview-Design) — the page now covers the interviewer and governance system prompts, the two-phase LangGraph state machine with its 10-question and 3-revision caps, how the agent decides what to ask next, how governance classification is derived (and recomputed on every revision), and tips for both stakeholders preparing for the interview and operators running or extending the agent.

**Audience:** Business stakeholders, intake agent operators.

#### 3. Extending the pipeline

**What:** A developer guide for adding new agents to the pipeline, creating new governance artifacts, adding new host adapters, or modifying the generated project structure.

**Why:** As the tool matures, teams will want to customize it. Currently, extension requires reading the source code. A guide covering the extension points (HandoffEnvelope, RepoClient protocol, governance tier gates) would lower the barrier.

**Audience:** Developers.

### Medium priority

These would improve completeness and usability:

#### 4. Schema reference ✅ *shipped in Session 20A*

See [Schema Reference](Schema-Reference) — the page covers all 5 registered payload schemas + `HandoffEnvelope` field-by-field with types, defaults, Literal enums, file:line citations, the `StrictBase` contract (`extra="forbid"`), the registry and `load_payload`, checkpoint layout, and versioning strategy.

A future auto-generated pass (Pydantic v2 JSON Schema → markdown) is still worth considering — it would keep the page in lockstep with the code without manual editing. For now the page is hand-written against v1.0.0.

**Audience:** Developers, integrators.

#### 5. Security considerations ✅ *shipped in Session 20A*

See [Security Considerations](Security-Considerations) — the page documents credential handling (every secret via `OrchestratorSettings.from_env()`, no hardcoded values), network boundaries (Anthropic, GitLab, GitHub, optional read-only DB), what the LLM sees (stakeholder answers verbatim; no query result rows ever sent to Claude), the database contract (SELECT-only role is an operator responsibility, not in-process filtering), checkpoint/log sensitivity, CI pipeline (no secrets), and a 9-item review checklist.

**Audience:** Security reviewers, compliance.

#### 6. FAQ

**What:** Common questions from users, operators, and data science teams. Seed with questions from the tutorial testing sessions (e.g., "Why doesn't the pipeline run queries against my database?", "Can I use this with a different LLM?", "How do I add a new regulatory framework?").

**Why:** Reduces support burden and surfaces non-obvious design decisions.

**Audience:** All.

#### 7. Comparison with alternatives

**What:** A brief comparison of this approach vs. alternatives: manual project setup, cookiecutter templates, Kedro, MLflow project scaffolding. Focus on what this tool adds (interview-driven, governance-proportional, domain-specific).

**Why:** Helps evaluators understand the tool's niche and when it is (or isn't) the right choice.

**Audience:** Decision-makers, architects.

### Lower priority

These are valuable but less urgent:

#### 8. Changelog

**What:** A page tracking significant changes to the tool: new agents, schema changes, new governance artifacts, dependency updates. Can be auto-generated from git tags or maintained manually.

**Why:** Users upgrading need to know what changed and whether it affects their generated projects.

**Audience:** Operators, developers.

#### 9. Contributing guide

**What:** How to contribute to the Model Project Constructor: development setup, testing conventions, commit message format, PR process, code quality standards (ruff rules, mypy strict, 94% coverage floor).

**Why:** Standard for any project that may accept external contributions.

**Audience:** Developers.

#### 10. Deployment guide (self-hosted)

**What:** How to deploy the intake web UI and pipeline runner in a production environment: containerization, reverse proxy setup, secret management, monitoring integration.

**Why:** The current documentation covers running locally. Production deployment has additional concerns (TLS, auth, log aggregation) that are environment-specific but benefit from guidance.

**Audience:** Operators, platform teams.

## Recommendations for the SBOM page

The current SBOM page covers all direct and key transitive dependencies. To strengthen it for compliance review:

1. **Add license information** for each dependency. Most are MIT, BSD, or Apache 2.0, but `cryptography` uses Apache/BSD dual license and `PyGithub` uses LGPL-3.0. LGPL compliance requires that the application can be re-linked with a modified version of the library, which is automatically satisfied by Python's import mechanism.

2. **Add a dependency update policy** stating how often dependencies are reviewed and updated, and what testing is performed after updates.

3. **Consider SPDX or CycloneDX format** for machine-readable SBOM export. `uv` can generate a `requirements.txt` export; tools like `cyclonedx-bom` can convert it.

4. **Track vulnerability scanning** -- note whether dependencies are checked against CVE databases (e.g., via `pip-audit` or GitHub Dependabot).

## Wiki maintenance

This wiki should be updated when:

- A new agent is added to the pipeline
- Schema fields are added or removed
- Dependencies are updated (SBOM page)
- New governance artifacts are introduced
- The generated project structure changes
- New regulatory frameworks are supported

Consider adding a CI check that flags wiki staleness when key source files change.
