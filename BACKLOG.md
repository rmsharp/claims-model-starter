# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

## Open Items

### CLI-adapter portability — spec the `OpenCodeLLMClient` adapter

**Decision accepted by the operator, 2026-08-01:** extend the LLM provider seam (`LLMProvider` in both agents'
`factory.py` modules — currently `"anthropic"` | `"bedrock"`) with a new `"opencode"` branch, shelling out to the
`opencode` CLI (`github.com/anomalyco/opencode`) rather than calling an SDK directly. OpenCode is itself a
vendor-agnostic multiplexer (75+ model providers via the Vercel AI SDK / Models.dev), so one adapter unlocks many
underlying vendors through OpenCode's own config — the actual goal being prepared for is an enterprise environment
that may standardize on a different AI CLI than Anthropic's. Full research (four candidates compared: OpenCode,
Codex CLI, Gemini CLI, GitHub Copilot CLI — headless-mode syntax, structured-output support, auth mechanics,
portability verdicts, citations) and the decision record live in
`docs/wiki/claims-model-starter/AI-Dependencies.md` §9 and `docs/wiki/claims-model-starter/Architecture-Decisions.md`
AD-11 — read both before starting, so the next session doesn't re-derive the comparison.

**The spec is DONE (Session 211, 2026-08-01): `docs/planning/opencode-adapter-spec.md`.** It specifies
`OpenCodeLLMClient` for both packages as a **transport-method override** — subclass each package's
`AnthropicLLMClient` and replace only `__init__` plus `_call_json` (intake) / `_call_claude` (data agent), so every
prompt, dataclass builder, and `_extract_json` is inherited and prompt drift across providers is structurally
impossible. It carries the full interface contract, the error-mapping table (spawn failure / non-zero exit /
timeout / no-assistant-text / malformed JSON → `IntakeLLMError`/`LLMParseError`), a grep-based file inventory with
line numbers at `a3f33d8`, the test plan (including the drift guard C4 forces for the *new* duplicated helper
pair), a risk register, and four build phases. **AI-Dependencies.md §9.2's prerequisite is discharged:** the
`--format json` event stream is JSONL of shape `{type, timestamp, sessionID, ...payload}` with types
`text`/`reasoning`/`tool_use`/`step_start`/`step_finish`/`error`, pinned from OpenCode's own emitter source at a
recorded commit — see spec §3.2.

**Phase 1 (the live verification spike) is DONE (Session 212, 2026-08-01)** — `opencode` **v1.18.11** installed
(`npm i -g opencode-ai`), all seven probes run, six verbatim fixtures committed to `tests/fixtures/opencode/`, and
findings recorded as spec **§13 Appendix A** with §3/§4 annotated inline. Cost: $0.1295 over 16 billed calls. All
four `[unverified]` markers resolved — notably the replace-vs-append question behind the spec's largest design
risk: **partial replace**, a custom agent's prompt drops ~4,720 tokens of built-in persona but a constant
**~4,830-token scaffold survives** every call. D2 (folding the system prompt into the user message) was validated
end-to-end: the real `next_question` payload produced schema-valid output that parses with the project's own
unmodified `_extract_json`.

**⚠ Phase 1 also produced seven corrections to the spec (Appendix A.4), one of them a safety defect.** Hazard
H4's claim that "the default is already safe" is **false**: without `--auto`, a live run listed the sandbox, **read
a file and disclosed its contents**, exit 0. The tool-denying agent definition (with `read: deny`) is therefore
**mandatory, not defence-in-depth**, and the "caller supplied their own agent ⇒ adapter writes nothing" escape
hatch in §4.4 must be removed or hard-gated. Also corrected: stderr is empty on the error path (so §4.7's
`{stderr_tail}` message yields `""` — build it from the stdout `error` event's `name`/`message`/`ref`);
`step_finish` exposes `reason`/`tokens`/`cost`, which restores the truncation guard §3.3 declared impossible;
blind concatenation of `text` events picks up narration on multi-step runs; a malformed agent file fails as
usage-help-on-stderr with empty stdout; the sandbox needs a **runtime npm install** (so npm reachability is a
deployment prerequisite, sharpening §11 Q3); and sessions persist prompt/response text in a **global SQLite DB**
that survives sandbox deletion.

**Phase 2 (both clients, both factory branches, the registry entry, the deterministic tier) is DONE (Session 213,
2026-08-01)** — `"opencode"` is a live provider in both packages, shipped with all seven Appendix A corrections
applied. See `CHANGELOG.md`'s 2026-08-01 entry. Gate: **1100 passed + 8 live-skipped @ 97.79%**, mypy and ruff
clean. **Two as-built deviations**, both recorded in the spec: §4.4/§5.1's `agent=` escape hatch was **removed**
(not merely hard-gated) in favour of `agent_name`, which renames the generated tool-denying definition rather than
substituting a caller-owned one — so no constructor path reaches an unlocked agent; and §5.3's twin helpers take
the parsed event list rather than raw `stdout`.

**⚠ The adapter is wired but entirely unmeasured.** `anthropic` remains the default everywhere, and it must stay
that way: spec risk #1 (parses fine, quality silently degrades under the D2 prompt-role change) is untouched, and
no data-agent method has been exercised against OpenCode at all.

**Phase 3 (eval wiring + documentation) is DONE (Session 214, 2026-08-01)** — `"opencode"` is a candidate in the
Phase E cutover gate with all eight thresholds PENDING, and thirteen wiki pages plus `README.md`, `OPERATIONS.md`,
`.env.example` and the published `docs/tutorial.md` now describe a shipped third provider. Gate: **1110 passed + 12 live-skipped @ 97.79%**, mypy and ruff clean. **One deliberate
deviation from spec §7.4, chosen by the operator before implementation:** the credential probe requires the
`opencode` binary **and** `OPENCODE_EVAL_MODEL`, not the binary alone. Binary-only was unsafe — the binary is
installed globally on this machine and `addopts` carries no `-m 'not live'`, so it would have turned every
`uv run pytest -q` here into a billable live run while CI still looked hermetic. The same variable is the pinned
model id (new `provider_eval_model`, threaded through `test_eval_live.py` and `shadow_run.py`), which makes D6's
"every evaluated run passes an explicit model" true and discharges Phase 4's "operator names the model to pin"
pre-flight. Both the spec's §7.4 and its Phase 3 entry carry the correction inline.

**Phase 3b (unplanned — the eval harness could not drive the provider at all) is DONE (Session 215, 2026-08-01)**
— `a0c3930`. Phase 4 was blocked and nobody knew, because the live tier skips so no test could see it. The
stakeholder simulator reached through to `intake_client._client.messages.create`, which for this provider is the
`_UNUSED_SDK_CLIENT` placeholder that raises by design; the resulting bare `AttributeError` is not in
`interview_sweep._TRANSIENT_ERRORS`, so a shadow run would have **billed ~31 live calls and then aborted with no
report**, leaving `interview_convergence` and `interview_premature` unmeasurable. A second defect on the same path
would have run the simulated-stakeholder half of every interview on **no model** while the interviewer half ran
pinned. Fixed with a transport-shape-resolved `TextCompleter` seam; no production code touched; +11 hermetic
tests. Gate: **1121 passed + 12 live-skipped @ 97.79%**, mypy and ruff clean. See `CHANGELOG.md`'s 2026-08-01
entry and spec §9 Phase 3b.

**Next session's deliverable is spec Phase 4 — the live shadow run + cutover decision. It is operator-gated.**
**§11 Q2 is now ANSWERED (operator, 2026-08-01): measure an Anthropic model through `opencode` first** — holding
the model constant makes the A/B against the recorded baseline isolate the transport change, which is what tests
risk #1 (quality degrading under the D2 prompt-role fold); a simultaneous model-family change would confound it.
The non-Anthropic run that delivers `AI-Dependencies.md` §6.7's diversification is a **second** measurement, after
the adapter is cleared. **Still needed live at that session's start:** the **model id to pin** (it becomes
`OPENCODE_EVAL_MODEL`) and credentials for that vendor, configured in the operator's own OpenCode config — this
project reads none. The run must report **cost per interview** alongside quality — the adapter carries a constant
~4,830-token scaffold per call (spec risk #12) that no §3.4 threshold can see. **No cutover on an unmet or
unmeasured threshold**; that rule is encoded in `evaluate_cutover` and must not be relaxed to produce a green
report. Spec §11 Q1 (`DEFAULT_MODEL` shipped as `None`) remains open and is reversible in one line.

### Enterprise migration (`docs/planning/enterprise-migration.md`)

Land the `feat/bedrock-mantle-migration` branch on `origin/master`, converge the three
documentation surfaces, and provision a one-time enterprise clone of the repository + wiki.
**Goals 1 and 2 (land the branch, close the public exposure) are complete** — Phases A1–A4 done
(Sessions 186–189, `41ab834`/`b27cc98`/A3's `35ccbd9`/A4's landing PR #2 → `master@9cabe0e`).
**Correction:** the prior version of this entry (written by Session 188) claimed A4 was still
open and that a later session would mark "Goals 1–2 done" here — that update never actually
landed (Session 189's close-out claimed it did; `git log -- BACKLOG.md` shows no commit between
Session 188's `35ccbd9` and this one touched this file). Fixed by Session 190.

**Plan-revision session done (Session 194, 2026-07-28):** `enterprise-migration.md` §1.3 now
reconciles the operator's 2026-07-27 sequencing decision (D3 + the "platform team" bucket — D4,
D5, D8, D9, D14, D15, D16 — resolved post-fork, inside the clone, not reported back to this
repository; the "security" bucket, D10/D13, is unaffected and stays live) with the plan's phase
gates, §3 Decision Register, dragon #20, §6, and §7. The phase list below reflects the revised
plan; the bullets below are a summary — `enterprise-migration.md` is authoritative.

**Phase C4's gate is now fully satisfied (Session 195, 2026-07-28):** B2 (below) is DONE. C4 can
run as soon as the operator supplies D9 (destination host), D5 (import strategy), D4 (DCO), D8
(wiki destination), and D16 (release disposition) live at that session's start — see
`enterprise-migration.md` Phase C4's "Before step 1" note and dragons #22/#24. This repository does
not pre-answer those five; whoever runs C4 gets them from the operator directly.

- **B1 — The legal packet.** **D3-independent core: DONE (Session 190)** — wiki LGPL mislabeling
  fixed, root `SECURITY.md`/`CODEOWNERS`/`THIRD-PARTY-LICENSES`/baseline `CONTRIBUTING.md`/`NOTICE`
  added, D1 attribution in place. **Full B1 (the corporate DCO/CLA mechanism section) is no longer
  a session this repository schedules** — per §1.3, it depends on D3/D4/D9, all deferred post-fork;
  it will be authored inside the enterprise clone, not here. B1's D3-independent core is the actual
  gate on Phase C4, and it's satisfied.
- **B2 — Import readiness.** **DONE (Session 195).** `.gitleaksignore` + classification table +
  secrets attestation + external-asset register at `audits/2026-07-28-b2-import-readiness.md`;
  `releases-export.json`/`prs-export.json` at repo root. The three GitLab pilot projects
  (`subrogation-pilot`, `-v2`, `-v3`) and the two GitHub Releases + tags are registered with a named
  disposition (undecided/D16 for the Releases and pilot projects — recreate-vs-pointer and
  migrate-vs-leave stay live D16/operator calls, not pre-decided). **The three `.env` credential
  rotations, originally flagged here as not done: RESOLVED as not required (Session 198)** — the
  rationale ("so the clone never depends on personal dev credentials") was wrong; Phase C4 step 1's
  `git clone --mirror` already carries zero credential values, so rotation was neither necessary
  nor sufficient. See `docs/planning/enterprise-migration.md` §1.4 and Phase C4 step 9 (corrected):
  the real requirement is provisioning `<enterprise-clone>` with enterprise-owned credentials at
  C4 time, not rotating the personal ones beforehand — no pre-fork action needed. The 162 MB
  `.git`/loose-objects fact from §2.9 is pre-existing repo state, not a B2 action item — `git clone
  --mirror` (C4 step 1) repacks on push regardless.
- **B3 — LGPL removal.** **DONE** (both LGPL SDKs removed via `docs/planning/httpx-adapter-migration.md`,
  Sessions 191–193 — see `CHANGELOG.md`'s 2026-07-27/2026-07-28 entries). D11 is moot; no further action.
- **C1 — Bedrock enterprise correctness.** **Narrowed by §1.3.** **D10 RESOLVED (Session 199):
  Regional. D13 RESOLVED (Session 200):** `require_sigv4` sub-scope only (guard completeness + env
  wiring), not `http_client`. **`bedrock-enterprise.md` §0's three security questions RESOLVED
  (Session 201, 2026-07-29, operator):** Guardrails not mandated, FIPS not mandated (mantle path
  confirmed correct — the plan's scope, which assumed "no" to both, was right), runtime quota
  expected yes (established enterprise account) but not independently verified. **Phase C1's own
  bundled scope is DONE (Session 202, 2026-07-29):** fixed the stale/false `base_url` claims in
  `bedrock-enterprise.md` §4 (it wrongly said the override "does not yet" exist, and wrongly cited
  `ANTHROPIC_BASE_URL` — the SDK's Bedrock-mantle client actually reads a different, mantle-specific
  var, `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`, verified against the installed SDK 0.94.1 source);
  documented that var in `.env.example` and §7; extracted the §3 IAM policy into two standalone
  applyable JSON artifacts — `docs/deployment/bedrock-mantle-execution-role-permissions.json` (the
  real permissions policy) and `docs/deployment/bedrock-mantle-execution-role-trust.json` (the
  trust policy, `Principal` left an explicit D14-blocked placeholder, not guessed). **Phase C1 is
  now fully complete** — no scope remains; D14's trust-relationship fill-in is the enterprise
  clone's own post-fork work, per §1.3.
- **C2 — Runtime, network, and data-at-rest readiness.** **Narrowed by §1.3.** **D13 RESOLVED
  (Session 200) — D13 was this phase's only gate, so C2 is now fully ungated and schedulable.**
  D15's dependency (index-variable documentation) is carved out and deferred post-fork.
- **C2b — Deployment artifact.** **Out of scope for this repository (§1.3)** — its only gate (D14)
  is unanswerable here; this is now the enterprise clone's own future work, not a session this
  repository will schedule.
- **C3 — CI and supply-chain hardening** (targets the enterprise clone's own CI). Gated on **C4
  complete only** — D9/D15 no longer need a written answer here, but the operator must supply both
  live at C3's session start (same pattern C4 uses for D9/D5/D4). Still a session this repository
  schedules, even though its edits land inside `<enterprise-clone>`.
- **C3b — Generated-project CI portability.** **DONE (Session 205, 2026-07-29).** New `CIHostConfig`
  dataclass (base image, index URL, action prefix, pre-commit repo — default to today's public
  values) threaded through `governance_templates.py` → `WebsiteAgent` → the website agent CLI →
  `scripts/run_pipeline.py`'s new `MPC_CI_*` env vars, so pipeline-generated projects can target
  enterprise-internal hosts instead of Docker Hub / the public GitHub Actions marketplace / public
  PyPI / the public `astral-sh/ruff-pre-commit` mirror. Verified: fake-mode run with all four env
  vars set → 0 public-host matches across 39 generated files; unset → public values unchanged.
  See `docs/planning/enterprise-migration.md` Phase C3b for the full breakdown.
- **C4 — Enterprise clone provisioning ("the fork").** Gated on **A1–A4 complete (done), B1's
  D3-independent core complete (done), and B2 complete (done, Session 195) — the gate is fully
  satisfied**. D4/D5/D8/D9/D16 no longer need written answers here; the operator supplies them live
  at C4's session start.
- **C5 — Fork independence verification.** Gated on **C4 complete only** — D16 no longer a written
  pre-req; C5 records whatever the operator decided, live, inside the clone (not back into this
  repository's own tracking).
- **Executive summary / stakeholder readiness dossier — DONE (Session 196).** Requested by the
  operator, 2026-07-28; produced Session 196, 2026-07-28/29. Delivered as
  `executive-summaries/stakeholder-readiness-dossier.qmd` (+ reproducible `.html`/`.pdf` renders,
  gitignored per the `business-value-capture` precedent — the `.qmd` is the committed source of
  truth), covering all three requested sections: (1) business benefit of the pipeline, with an
  honest evidence/limits split (real engineering smoke-test traction vs. no claims-team adoption
  yet); (2) legal safety, re-derived fresh against D1/D2/D3 and the §2.7 licence table (MIT
  consistent, zero LGPL/GPL/AGPL, third-party methodology material under a documented permission
  grant) plus two open items surfaced independently — the generated-project license gap and the
  published wiki's own lack of a license (**both closed, Session 197** — see the dossier's own
  "Open items and owners" table); (3) enterprise-environment readiness across security,
  testing, data readiness, and Bedrock readiness, each split into resolved vs. genuinely open with
  named owners cross-referenced to the plan's §3 decision register and C1-C3 phases. Built via a
  research → draft → 4-lens adversarial verify → fix workflow; verify found 1 blocking gap (the
  wiki-license omission) and 4 minor gaps (an unsubstantiated third disposition option, and three
  "Unassigned"-owner claims that actually duplicate already-scoped C2/C3 phase items) — all fixed
  and spot-checked live before commit (commit counts, license files, LGPL-freedom, wiki license
  absence, and test-collection count independently re-verified, not just trusted from the
  sub-agent). **Phase-structure decision (resolved by this session, as the prior note left open):
  standalone document, not a new lettered A/B/C phase** — it does not gate or get gated by any
  phase; Phase C4's gate (A1–A4, B1-core, B2) remains independently satisfied. Recommendation
  stated in the document: proceed to the fork, carrying the open-items table forward.

**Open decisions this repository still tracks:** none, from either the D-numbered register or
`bedrock-enterprise.md` §0's three (non-D-numbered) security questions — **everything in the
security bucket is now answered.** **D10 (Bedrock endpoint Regional vs Global) is RESOLVED (Session
199, 2026-07-29): Regional** — operator accepted the recommendation; recorded in
`enterprise-migration.md`'s Decision Register and `bedrock-enterprise.md` §5, with the hard-block
residency SCP templated at `docs/deployment/bedrock-residency-scp.json` (specific region allowlist
still an open platform-team placeholder). **D13 (wire `require_sigv4`/`http_client` to app/env) is
RESOLVED (Session 200, 2026-07-29)** — its `require_sigv4` sub-scope only: the guard now checks
both SDK-recognized bearer-token env vars (`AWS_BEARER_TOKEN_BEDROCK` and `ANTHROPIC_AWS_API_KEY`,
was only the first) and defaults from a new `BEDROCK_REQUIRE_SIGV4` env var when not passed
explicitly; recorded in `enterprise-migration.md`'s Decision Register and `bedrock-enterprise.md`
§7. `http_client` wiring remains undone, as the recommendation itself deferred it pending
TLS-inspection confirmation. **`bedrock-enterprise.md` §0's three security questions are RESOLVED
too (Session 201, 2026-07-29, operator):** Guardrails not mandated, FIPS not mandated (mantle path
confirmed correct), runtime quota expected yes (established enterprise account) but **not
independently verified** — that verification needs live access to the actual enterprise account
and is carried forward as a flag, not a blocker, since C1's own remaining scope makes no live AWS
calls. **Phase C1 is now fully complete (Session 202, 2026-07-29)** — its own bundled scope (the
stale `base_url`/`ANTHROPIC_BASE_URL` doc fix, the §3 IAM-permissions-policy extraction into
applyable JSON artifacts) is done; see the C1 bullet above for the full breakdown. No scope remains
in this repository for C1. **Phase C2's gate was already cleared by D13 alone** (D13 was C2's sole
listed gate) — C2's own
scope (htmx vendoring, intake UI auth posture, the `MPC_HOST_URL` gap, plaintext-at-rest,
`run_pipeline.py:450`) is itself untouched but no longer blocked from starting.

**Decisions no longer tracked here (§1.3):** D1, D2, D6, D7, D11, D12 are already answered;
**D3, D4, D5, D8, D9, D14, D15, D16** are resolved by the operator after Phase C4 runs, inside the
enterprise clone, live — not written up in this repository's Decision Register, `BACKLOG.md`, or
`SESSION_NOTES.md`. Whoever runs C3/C4/C5 must get the relevant answers directly from the operator
at that session's start (`enterprise-migration.md` §4's "Before step 1" notes and dragon #22/#24).
See `docs/planning/enterprise-migration.md` §3 for the full Recommendation-column text, preserved
as forward context for whoever eventually answers these inside the clone.

---

Most recently completed: **`httpx-adapter-migration`** (`docs/planning/httpx-adapter-migration.md`)
— all three phases DONE and LANDED (Phase 1 GitLab: Session 191; Phase 2 GitHub: Session 193; Phase
3 optional rename: Session 203). Zero direct dependencies are LGPL as of Session 193's `9aad76b`.
Full per-commit breakdown in `CHANGELOG.md`'s 2026-07-27/2026-07-28/2026-07-29 entries.

Previously completed: **harden the `cycle_time` cadence definitions and corpus**
(gap #2 robustness follow-up) — Session 177 refined `CYCLE_TIME_DEFINITIONS` to
discriminate `tactical`/`operational` on **output purpose** (not run frequency) and
added the role≠frequency corpus case `claim_workqueue_triage` (live cycle_time 60/60 =
100%, gate assert PASS). The operator **deferred** the optional event-driven/episodic
`CycleTime` member (YAGNI — no corpus case needs it; a schema-`Literal` change with a
larger blast radius); reopen only if such a case arises. See `CHANGELOG.md` and
`tests/eval/PHASE_E_AGREEMENT_REPORT.md`.
