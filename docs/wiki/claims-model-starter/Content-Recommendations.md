# Content Recommendations

This page lists the wiki's current pages (with audiences) and known gaps where a new page would add value.

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
| [Worked Examples](Worked-Examples) | New users, stakeholders | End-to-end traces of the subrogation and renewal-profitability scenarios |
| [Extending the Pipeline](Extending-the-Pipeline) | Developers | Four extension surfaces: new agents, adapters, governance artifacts, regulatory frameworks |
| [Monitoring and Operations](Monitoring-and-Operations) | Operators | Deployment, checkpoints, troubleshooting |
| [Security Considerations](Security-Considerations) | Security reviewers, compliance | Credentials, network boundaries, LLM data exposure, read-only DB |
| [Software Bill of Materials](Software-Bill-of-Materials) | Security, compliance, operators | All dependencies and versions |
| [Architecture Decisions](Architecture-Decisions) | Developers, architects | Key design choices and rationale |
| [Evolution](Evolution) | Onboarding readers, code-sharing context | Design-decision arc from concept to current state |
| [Changelog](Changelog) | Operators, developers | Phase-by-phase history of notable changes |
| [Contributing](Contributing) | Developers | Dev env, code-quality gates, tests, commit convention, session discipline |
| [Glossary](Glossary) | All | Domain, pipeline, governance, and technical terms |

## Known gaps

The wiki has no coverage of the following. Candidates for future pages.

### FAQ

Common questions from users, operators, and data science teams — e.g., "Why doesn't the pipeline run queries against my database?", "Can I use this with a different LLM?", "How do I add a new regulatory framework?". Would reduce support burden and surface non-obvious design decisions.

**Audience:** All.

### Comparison with alternatives

A brief comparison of this approach vs. manual project setup, cookiecutter templates, Kedro, MLflow project scaffolding. Focuses on what this tool adds: interview-driven, governance-proportional, domain-specific.

**Audience:** Decision-makers, architects.

### Self-hosted deployment guide

The [Monitoring and Operations](Monitoring-and-Operations) page covers local runs and environment-variable configuration. A production deployment guide would add containerization, reverse proxy setup, secret management, and monitoring integration (TLS, auth, log aggregation).

**Audience:** Operators, platform teams.

### Auto-generated schema reference

The [Schema Reference](Schema-Reference) page is hand-written against v1.0.0. An auto-generated pass (Pydantic v2 JSON Schema → markdown) would keep the page in lockstep with the code without manual editing.

**Audience:** Developers, integrators.

### Release-tag-driven changelog refresh

The [Changelog](Changelog) is phase-organized. Once the first tagged release cuts, a script that emits a new section per `git tag` would avoid manual phase-curation.

**Audience:** Operators, developers.

### Additional worked example

[Worked Examples](Worked-Examples) traces two scenarios (subrogation — tier-3 supervised classification; renewal profitability — tier-1 fairness-constrained). A third example covering regression or an unsupervised scenario would improve coverage once a corresponding fixture lands.

**Audience:** New users, business stakeholders evaluating the tool.

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
