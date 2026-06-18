"""Phase B eval thresholds (multi-provider LLM plan §3.4).

These are the **proposed** pass thresholds for the provider-quality gate. The
Anthropic baseline was measured in Session 165, but it did **not** calibrate them:
the incumbent failed 5/8 on harness/corpus artifacts (fragile interview replay,
governance references that disagree with live output, a QC max_tokens truncation),
so the run measured the *harness*, not the providers. The thresholds were
deliberately **not** lowered to match a broken harness; they stay proposed until
the harness-fix follow-ups land (see ``PHASE_E_AGREEMENT_REPORT.md`` §"Baseline
findings" and ``README.md`` §"Live baseline").

The deterministic tier asserts the *scorers* behave correctly with respect to
these constants (e.g. a laxer-tier prediction is caught); it does **not** assert
that any live provider meets them — that is the ``live`` tier's job.
"""

from __future__ import annotations

# capability → threshold (see §3.4 table)
JSON_PARSE_MIN = 0.99
SQL_PARSE_VALID_MIN = 1.00
SQL_EXECUTABLE_MIN = 0.95
GOVERNANCE_AGREEMENT_MIN = 0.90
GOVERNANCE_LAXER_MISSES_MAX = 0
QUALITY_CHECKS_STRUCTURAL_MIN = 1.00
INTERVIEW_CONVERGENCE_MIN = 0.95
INTERVIEW_PREMATURE_MAX = 0

# RiskTier strictness ordering — index 0 is the STRICTEST tier; a larger index is
# laxer. A prediction is a "laxer-tier miss" (the §3.4 zero-tolerance failure)
# when its tier index is strictly greater than the reference's. The prompt's
# rule is "if in doubt, pick the stricter tier", so erring stricter is allowed;
# erring laxer is the load-bearing failure.
RISK_TIER_STRICTNESS: dict[str, int] = {
    "tier_1_critical": 0,
    "tier_2_high": 1,
    "tier_3_moderate": 2,
    "tier_4_low": 3,
}
