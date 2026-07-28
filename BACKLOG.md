# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

### Enterprise migration (`docs/planning/enterprise-migration.md`)

Land the `feat/bedrock-mantle-migration` branch on `origin/master`, converge the three
documentation surfaces, and provision a one-time enterprise clone of the repository + wiki.
**Goals 1 and 2 (land the branch, close the public exposure) are complete** — Phases A1–A4 done
(Sessions 186–189, `41ab834`/`b27cc98`/A3's `35ccbd9`/A4's landing PR #2 → `master@9cabe0e`).
**Correction:** the prior version of this entry (written by Session 188) claimed A4 was still
open and that a later session would mark "Goals 1–2 done" here — that update never actually
landed (Session 189's close-out claimed it did; `git log -- BACKLOG.md` shows no commit between
Session 188's `35ccbd9` and this one touched this file). Fixed by Session 190.

**Operator sequencing decision (2026-07-27, Session 190):** D3 (IP disposition) and Phase C4's own
gates (D4, D5, D8, D9, D14, D15, D16) will be resolved **after** the fork, inside the enterprise
clone, and **not reported back to this repository**. `enterprise-migration.md` as currently
written has C4 gated on B1 complete specifically *because* the fork is one-time with no sync-back
(dragon #20) — this sequencing decision inverts that, and the plan document itself has not yet
been revised to reflect it. **A dedicated plan-revision session is still owed** — do not treat the
phase list below as current until `enterprise-migration.md` §1.2/§3/§4/dragon-#20 are reconciled
with this decision.

- **B1 — The legal packet.** **Partially done (Session 190):** wiki LGPL mislabeling fixed (both
  `python-gitlab` and `PyGithub` now correctly named); root `SECURITY.md`, `CODEOWNERS`,
  `THIRD-PARTY-LICENSES`, baseline `CONTRIBUTING.md`, and `NOTICE` (methodology attribution +
  AI-provenance statement) added. **Still open:** the corporate DCO/CLA mechanism section in
  `CONTRIBUTING.md` (explicitly left TBD — depends on D3/D4/D9, deferred per the operator's
  sequencing decision above). D1 is resolved (Terrell Deppe granted MIT permission per the
  operator); note the plan's own D1 verify command (`grep` for the attribution string inside
  `SESSION_RUNNER.md`/`SAFEGUARDS.md` themselves) will not pass — attribution lives in `NOTICE` +
  `CLAUDE.md` instead, since those two files are synced from canonical and must not be edited
  locally. This is a plan-text correction still needed, not done this session.
- **B2 — Import readiness**: secret-scanner allowlist, dev-credential rotation, external-asset
  audit (3 GitLab pilot projects invisible to git; a 162 MB `.git` with loose objects).
- **B3 — LGPL removal** (conditional on D11 — confirm the corporate copyleft policy first; may be
  deferred if the policy permits unmodified, dynamically-imported LGPL libraries).
- **C1 — Bedrock enterprise correctness.** Gated on D10 (Regional vs Global endpoint — Regional
  recommended for P&C residency), D13 (wire `require_sigv4`/`http_client` to app/env), D14
  (runtime shape). Per the operator's sequencing decision, likely resolved post-fork.
- **C2 — Runtime, network, and data-at-rest readiness.** Gated on D13, D15.
- **C2b — Deployment artifact** — no Dockerfile, manifest, or IaC exists today. Gated on D14.
- **C3 — CI and supply-chain hardening** (targets the enterprise clone's own CI, not the
  original's). Gated on D9, D15, and **C4 complete**.
- **C4 — Enterprise clone provisioning ("the fork").** Per the operator, this is now expected to
  run *before* D3/D4/D5/D8/D9/D14/D15/D16 are resolved, contingent on the plan-revision session
  above actually reconciling that with dragon #20's stated reasoning.
- **C5 — Fork independence verification.**

**Open decisions** (owners per `enterprise-migration.md` §3; D2/D6/D7/D12/D1 already answered):
**D3** IP disposition (legal) — deferred to post-fork per operator; **D4** signed commits/DCO
requirement (operator → platform team) — deferred to post-fork; **D5** import history as-is vs.
rewrite vs. squash (operator + platform team) — deferred to post-fork; **D8** wiki destination +
auto-publish in the enterprise clone (operator + platform team) — deferred to post-fork; **D9**
repo-host target — self-hosted GitLab or GHES (operator) — deferred to post-fork; **D10** Bedrock
endpoint Regional vs Global (security + operator); **D11** LGPL-removal timing (operator + legal);
**D13** wire `require_sigv4`/`http_client` to app/env (operator + platform team); **D14** runtime
shape — EKS/ECS/EC2/on-prem (operator + platform team) — deferred to post-fork; **D15** package
index — internal or proxied PyPI (operator + platform team) — deferred to post-fork; **D16**
enterprise clone disposition/access model (operator + legal) — deferred to post-fork. See
`docs/planning/enterprise-migration.md` §3 for full text and recommendations.

### httpx adapter migration (`docs/planning/httpx-adapter-migration.md`)

Replace both LGPL SDK dependencies (`python-gitlab`, `PyGithub`) in the Website Agent's repo-host
adapters with direct `httpx` REST calls. **Phase 1 (GitLab) is DONE** (Session 191, branch
`feat/httpx-adapters`, 5 commits — `9af715b`/`09f80a4`/`348dff1`/`41445b9`/`7b9b05e` —
**not yet merged to `master` or pushed; awaiting operator decision**, see SESSION_NOTES.md). One
of the two LGPL-3.0 direct dependencies is gone; `PyGithub` remains.

- **Phase 2 — GitHub adapter → `httpx`.** Mirrors Phase 1: rewrite `github_adapter.py`'s git-database
  commit dance (6 sequential calls, each a failure point) against `httpx`, rewrite
  `test_github_adapter.py` against `httpx.MockTransport`, drop `PyGithub` from `pyproject.toml`,
  update GitHub-specific docs (`README.md:75,191`, protocol docstring, SBOM/Security/Agent-Ref
  GitHub rows, remove the now-obsolete LGPL-compliance notes). At completion, both LGPL
  dependencies are gone. **Session 191 gotcha for whoever runs Phase 2:** the first Phase 1 draft
  checked `status_code >= 400` instead of `_is_2xx` (`200 <= status < 300`) and left the
  post-success `.json()` calls unguarded — both let a raw exception escape on a 3xx redirect or a
  malformed-JSON 2xx body (`httpx.Client` doesn't follow redirects by default, unlike the
  `requests`-based transport under both old SDKs). Apply the same `_is_2xx`/guarded-parse pattern
  in the GitHub rewrite from the start rather than rediscovering it.
- **Phase 3 (optional)** — rename `PythonGitLabAdapter`/`PyGithubAdapter` to drop the SDK names
  now baked into misnomers. Plan recommends deferring this; only do it if DP1 is revisited.

Overlaps `B3` (LGPL removal) in the Enterprise migration section above — B3 is now partially
satisfied (GitLab's LGPL dep is gone) but B3's own text hasn't been reconciled with this plan; not
done this session (would be scope creep into the enterprise-migration plan-revision session already
flagged as owed).

---

Most recently completed: **harden the `cycle_time` cadence definitions and corpus**
(gap #2 robustness follow-up) — Session 177 refined `CYCLE_TIME_DEFINITIONS` to
discriminate `tactical`/`operational` on **output purpose** (not run frequency) and
added the role≠frequency corpus case `claim_workqueue_triage` (live cycle_time 60/60 =
100%, gate assert PASS). The operator **deferred** the optional event-driven/episodic
`CycleTime` member (YAGNI — no corpus case needs it; a schema-`Literal` change with a
larger blast radius); reopen only if such a case arises. See `CHANGELOG.md` and
`tests/eval/PHASE_E_AGREEMENT_REPORT.md`.
