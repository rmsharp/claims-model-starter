# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

### Enterprise migration (`docs/planning/enterprise-migration.md`)

Land the `feat/bedrock-mantle-migration` branch on `origin/master`, converge the three
documentation surfaces, and provision a one-time enterprise clone of the repository + wiki.
Phases A1–A3 are complete (Sessions 186–188, `41ab834`/`b27cc98`/A3's commit); each remaining
phase is its own session per `SESSION_RUNNER.md`:

- **A4 — Land it.** Push branch → PR → CI → single fast-forward push to `master` → publish wiki →
  verify. The phase the operator originally asked for; everything before it exists to make this
  phase safe.
- **B1 — The legal packet** (gates the corporate push). Resolve D1 (third-party methodology
  material) and D3 (IP disposition) first.
- **B2 — Import readiness**: secret-scanner allowlist, dev-credential rotation, external-asset
  audit (3 GitLab pilot projects invisible to git; a 162 MB `.git` with loose objects).
- **B3 — LGPL removal** (conditional on D11 — confirm the corporate copyleft policy first; may be
  deferred if the policy permits unmodified, dynamically-imported LGPL libraries).
- **C1 — Bedrock enterprise correctness.** Gated on D10 (Regional vs Global endpoint — Regional
  recommended for P&C residency), D13 (wire `require_sigv4`/`http_client` to app/env), D14
  (runtime shape).
- **C2 — Runtime, network, and data-at-rest readiness.** Gated on D13, D15.
- **C2b — Deployment artifact** — no Dockerfile, manifest, or IaC exists today. Gated on D14.
- **C3 — CI and supply-chain hardening** (targets the enterprise clone's own CI, not the
  original's). Gated on D9, D15, and **C4 complete**.
- **C4 — Enterprise clone provisioning.**
- **C5 — Fork independence verification.**

**Open decisions blocking the above** (owners per `enterprise-migration.md` §3; D2/D6/D7/D12
already answered): **D1** third-party methodology material — remove or get written permission
(operator + legal); **D3** IP disposition (legal); **D4** signed commits/DCO requirement
(operator → platform team); **D5** import history as-is vs. rewrite vs. squash (operator +
platform team); **D8** wiki destination + auto-publish in the enterprise clone (operator +
platform team); **D9** repo-host target — self-hosted GitLab or GHES (operator); **D10** Bedrock
endpoint Regional vs Global (security + operator); **D11** LGPL-removal timing (operator + legal);
**D13** wire `require_sigv4`/`http_client` to app/env (operator + platform team); **D14** runtime
shape — EKS/ECS/EC2/on-prem (operator + platform team); **D15** package index — internal or
proxied PyPI (operator + platform team); **D16** enterprise clone disposition/access model
(operator + legal). See `docs/planning/enterprise-migration.md` §3 for full text and
recommendations.

---

Most recently completed: **harden the `cycle_time` cadence definitions and corpus**
(gap #2 robustness follow-up) — Session 177 refined `CYCLE_TIME_DEFINITIONS` to
discriminate `tactical`/`operational` on **output purpose** (not run frequency) and
added the role≠frequency corpus case `claim_workqueue_triage` (live cycle_time 60/60 =
100%, gate assert PASS). The operator **deferred** the optional event-driven/episodic
`CycleTime` member (YAGNI — no corpus case needs it; a schema-`Literal` change with a
larger blast radius); reopen only if such a case arises. See `CHANGELOG.md` and
`tests/eval/PHASE_E_AGREEMENT_REPORT.md`.
