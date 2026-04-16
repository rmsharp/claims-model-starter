# Content Recommendations

This page documents what this wiki contains, what additional content would add value, and prioritized recommendations for future additions.

## Current wiki pages

| Page | Audience | Purpose |
|------|----------|---------|
| [Home](Home) | All | Landing page and navigation |
| [Getting Started](Getting-Started) | New users | Install, first run, verify |
| [Pipeline Overview](Pipeline-Overview) | All | How the three agents work together |
| [Generated Project Structure](Generated-Project-Structure) | Data science teams | What the output repository contains |
| [Governance Framework](Governance-Framework) | Governance/compliance, data science teams | Risk tiers, regulatory mapping, artifact inventory |
| [Development Workflow](Development-Workflow) | Data science teams | How to implement stubs and iterate |
| [Data Guide](Data-Guide) | Data science teams, analysts | Queries, datasheets, data loading |
| [Agent Reference](Agent-Reference) | Developers, operators | Detailed agent specs and schemas |
| [Monitoring and Operations](Monitoring-and-Operations) | Operators | Deployment, checkpoints, troubleshooting |
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

#### 2. Intake interview design guide

**What:** A page explaining the intake agent's interview strategy: how it decides which questions to ask, how it converges toward the four required sections, how governance metadata is assessed, and tips for stakeholders on preparing for the interview.

**Why:** The intake interview is the stakeholder's primary touchpoint. Understanding the agent's approach helps stakeholders prepare better answers and set expectations about the interview length and depth.

**Audience:** Business stakeholders, intake agent operators.

#### 3. Extending the pipeline

**What:** A developer guide for adding new agents to the pipeline, creating new governance artifacts, adding new host adapters, or modifying the generated project structure.

**Why:** As the tool matures, teams will want to customize it. Currently, extension requires reading the source code. A guide covering the extension points (HandoffEnvelope, RepoClient protocol, governance tier gates) would lower the barrier.

**Audience:** Developers.

### Medium priority

These would improve completeness and usability:

#### 4. Schema reference (auto-generated)

**What:** Auto-generated documentation of all Pydantic schemas: IntakeReport, DataReport, RepoProjectResult, HandoffEnvelope, GovernanceMetadata, ModelSolution, etc. Include field types, constraints, and examples.

**Why:** The Agent Reference page summarizes schemas in pseudocode. A full reference with every field, validator, and default value would be authoritative. Pydantic v2 can export JSON Schema; a build step could render these to wiki pages.

**Audience:** Developers, integrators.

#### 5. Security considerations

**What:** A page documenting: credential handling (env vars, no hardcoded secrets), network boundaries (which agents make external calls and to where), data sensitivity (LLM sees interview content and schema details), and the read-only database constraint for the Data Agent.

**Why:** Enterprise adoption requires security review. A dedicated page accelerates that process.

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
