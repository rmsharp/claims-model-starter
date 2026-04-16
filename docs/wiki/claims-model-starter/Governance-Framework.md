# Governance Framework

Model governance is not a bolt-on -- it is captured at intake and scaffolded proportional to model risk. The intake agent assesses governance metadata during the interview, and the website agent emits artifacts accordingly.

## Governance metadata (captured at intake)

| Field | Values | What it controls |
|-------|--------|-----------------|
| `risk_tier` | `tier_1_critical`, `tier_2_high`, `tier_3_moderate`, `tier_4_low` | Depth of governance artifact checklist |
| `cycle_time` | `strategic`, `tactical`, `operational`, `continuous` | Monitoring cadence |
| `regulatory_frameworks` | `SR_11_7`, `NAIC_AIS`, `EU_AI_ACT_ART_9`, `ASOP_56` | Regulatory mapping document |
| `affects_consumers` | boolean | EU AI Act compliance scaffold |
| `uses_protected_attributes` | boolean | Fairness testing scaffold |

## Risk tier definitions

| Tier | Severity | Example | Governance depth |
|------|----------|---------|-----------------|
| Tier 1 (Critical) | Highest | Consumer pricing model, claims fraud detection | Full governance suite + audit trail + LCP integration |
| Tier 2 (High) | High | Subrogation prediction, reserve estimation | Core suite + impact assessment + regulatory mapping |
| Tier 3 (Moderate) | Moderate | Adjuster workload optimization | Core suite + validation plan + monitoring + deployment gates |
| Tier 4 (Low) | Lowest | Internal reporting dashboard | Core suite only |

## Artifact inventory

### Always emitted (all tiers)

| Artifact | Path | Standard |
|----------|------|----------|
| Model registry entry | `governance/model_registry.json` | Internal |
| Model card | `governance/model_card.md` | Mitchell et al. 2019 |
| Change log | `governance/change_log.md` | Internal |
| CI pipeline | `.gitlab-ci.yml` or `.github/workflows/ci.yml` | -- |
| Pre-commit hooks | `.pre-commit-config.yaml` | -- |
| Datasheets (per query) | `data/datasheet_<query>.md` | Gebru et al. 2021 |

### Tier 3+ (moderate and above)

| Artifact | Path | Purpose |
|----------|------|---------|
| Three-pillar validation | `governance/three_pillar_validation.md` | Conceptual soundness, ongoing monitoring, outcomes analysis |
| Ongoing monitoring | `governance/ongoing_monitoring.md` | Cadence, metrics, trigger conditions |
| Deployment gates | `governance/deployment_gates.md` | Staged rollout: shadow, limited, full production |

### Tier 2+ (high and above)

| Artifact | Path | Purpose |
|----------|------|---------|
| Impact assessment | `governance/impact_assessment.md` | Value narrative, risks, mitigations |
| Regulatory mapping | `governance/regulatory_mapping.md` | Framework-to-artifact mapping |

### Tier 1 only (critical)

| Artifact | Path | Purpose |
|----------|------|---------|
| LCP integration | `governance/lcp_integration.md` | Life Cycle Process: 5 review gates |
| Audit log scaffold | `governance/audit_log/README.md` | Evidence directory for review events |

### Conditional artifacts

| Condition | Artifact | Path |
|-----------|----------|------|
| `affects_consumers=true` | EU AI Act compliance | `governance/eu_ai_act_compliance.md` |
| `uses_protected_attributes=true` | Fairness audit notebook | `analysis/fairness_audit.qmd` |
| `uses_protected_attributes=true` | Fairness module | `src/<slug>/fairness/audit.py` |
| `uses_protected_attributes=true` | Fairness tests | `tests/test_fairness.py` |

## Monitoring cadence

The `cycle_time` field determines how often the model is reviewed:

| Cycle time | Monitoring cadence |
|-----------|-------------------|
| Strategic | Annual review |
| Tactical | Quarterly review |
| Operational | Monthly monitoring |
| Continuous | Automated continuous monitoring with monthly human review |

This cadence is written into `governance/ongoing_monitoring.md` with specific metrics to track and trigger conditions for re-review.

## Regulatory framework mapping

When `regulatory_frameworks` are declared in the intake report, the website agent generates a `governance/regulatory_mapping.md` that maps each framework to the specific artifacts satisfying its requirements.

Supported frameworks:

| Framework | Full name |
|-----------|-----------|
| `SR_11_7` | Federal Reserve SR 11-7 (Guidance on Model Risk Management) |
| `NAIC_AIS` | NAIC Model Bulletin on AI Systems |
| `EU_AI_ACT_ART_9` | EU AI Act Articles 9-15 |
| `ASOP_56` | Actuarial Standard of Practice No. 56 (Modeling) |

The mapping only includes artifacts that are actually emitted for the project's risk tier -- it will not reference an artifact that wasn't generated.

## Model registry entry

The `model_registry.json` is a machine-readable registry entry validated by the CI pipeline:

```json
{
  "schema_version": "1.0.0",
  "model_id": "<generated>",
  "project_name": "<from intake>",
  "owner_stakeholder_id": "<from intake>",
  "intake_session_id": "<from intake>",
  "created_at": "<ISO timestamp>",
  "target_variable": "<from intake>",
  "model_type": "<from intake>",
  "risk_tier": "<from intake>",
  "cycle_time": "<from intake>",
  "regulatory_frameworks": ["<from intake>"],
  "affects_consumers": true/false,
  "uses_protected_attributes": true/false
}
```

## Maintaining governance artifacts

All governance artifacts are **drafts**. The data science team is expected to:

1. Review the model card and update it as the model evolves
2. Fill in the three-pillar validation plan with actual methodology
3. Track changes in the change log as the project progresses
4. Update the model registry entry when model type or risk assessment changes
5. Complete datasheets with actual data characteristics after running queries

The CI pipeline validates the model registry schema on every push, ensuring the registry entry stays well-formed.
