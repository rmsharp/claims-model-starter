# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

---

## ACTIVE TASK
**Task:** Session 25 — open. Session 24 shipped Scope B-1 (real Anthropic data agent wired into `scripts/run_pipeline.py --llm data`). Session 25 is user's choice between continuing Scope B (Phase B2 — scripted-answers intake) and picking any of the carryover findings.
**Status:** Session 24 complete. Session 25 ready.
**Priority:** If Session 25 picks B2, user should re-confirm plan §8.3 (B3 in scope?) and §8.4 (adapter location). For B1 we used opus-4-7; B2 should pick a model for the intake side.

### What Session 25 should do

Seven candidates, ranked by readiness and value:

1. **Execute Phase B2 of `docs/planning/scope-b-plan.md`** — Scripted-answers intake with real Anthropic, activated by `--llm both --intake-fixture path/to/sub.yaml`. Plan §7.2 specifies ~+35 LOC in `scripts/run_pipeline.py` + ~+25 LOC for the `RuntimeError → DRAFT_INCOMPLETE` adapter (inline per plan §8.4 (a)). The adapter is the load-bearing piece — §7.2.2 has the reference implementation; the data agent's `agent.py:50-53` try/except is the template. **Hard stop:** do NOT bundle B3 in the same session — failure mode #18 risk.

2. **Clearer `MPC_NAMESPACE` validation + docs** (Session 22 finding). Add a validator to `OrchestratorSettings.from_env()` that detects a leading `http://`/`https://` and raises `ConfigError("MPC_NAMESPACE must be a group path, not a URL; got '...'")`. Update `.env.example`, `OPERATIONS.md` §1, `docs/tutorial.md` §5a. ~5 small edits + one new test. One session.

3. **CI lint coverage extension to `scripts/`** (Session 22 finding, **re-surfaced in Session 24**). Add `scripts/` to the ruff CI command in `.github/workflows/ci.yml`. Fix 10 pre-existing errors (6 × E402, 4 × F541 — Session 24 confirmed the count). Simplest: `# noqa: E402` on 6 imports + `ruff check scripts/ --fix` on the F541s. Cleaner: drop `sys.path.insert` hack (lines 38-40) and rely on `uv run` resolving the editable install. One session.

4. **CI typecheck coverage extension to `packages/`** (Session 22 finding). `pyproject.toml` declares both packages under `[tool.mypy]` but CI runs `mypy src/` only. Extend CI to `mypy src/ packages/data-agent/src/`. Fix ~13 errors — largest cluster is `packages/data-agent/.../anthropic_client.py:218` (Anthropic SDK content-block union; needs `TextBlock` type-guard). One session.

5. **Self-hosted GitHub URL override** (Session 22 finding, code-read only). `docs/tutorial.md` §5c claims `MPC_HOST_URL` works for GHE, but `scripts/run_pipeline.py:109-113` constructs `PyGithubAdapter(token=token)` with no URL argument. Fix parallels Session 22's `host_url=` fix for GitLab. Untested live; small scope. One session.

6. **Re-audit `OPERATIONS.md` §4.2/4.3 recipes** (Session 22 finding; Session 23's claim was WRONG — see gotcha #2 below). Session 24 discovered that `src/model_project_constructor/agents/website/__main__.py` and `cli.py` BOTH exist (added in commit `e9f0d10` during Phase D / Session 17). The OPERATIONS recipes may actually work. Session 25 should try each invocation, document what works vs. what's stale, and reconcile with `scripts/run_pipeline.py --live` as the canonical entry point. One session.

7. **Wiki freshness sweep** (Session 24 finding). Update `docs/wiki/claims-model-starter/` pages so each reads as a description of the current tool rather than a record of its evolution. Delete "Recommended additions" that are already implemented; rewrite partially-implemented ones to describe the remaining gap only. Drift hotspots: `Content-Recommendations.md`, `Home.md`, `Pipeline-Overview.md`, `Getting-Started.md`, `Agent-Reference.md`. One session.

**Recommend #1** for Session 25 to complete Scope B. If the user wants quick wins first, #3 is the lowest-risk (~20 min + commit boundary).

---

## Session 23 Handoff Evaluation (by Session 24)
**Score: 8/10.** Strong planning handoff, but two notable claims turned out to be wrong — one was load-bearing enough to cost time in verification.

- **What helped:** (a) Key-files block for candidate #1 listed `scripts/run_pipeline.py:201-206` (stubbed lambdas), `packages/data-agent/.../cli.py:99-119` (the mirror pattern), and `packages/data-agent/.../agent.py:32-61` (shows `DataAgent.run` already matches `DataRunner`). I went straight to those files; the B1 wiring was ~15 minutes of typing once I confirmed the plan's signatures. (b) Gotcha #2 ("plan §8 has 5 open decisions, all (a)") correctly put user sign-off before the stub write — prevented a costly mid-session pivot. (c) Gotcha #5 about the live GitLab project from Session 22 still existing explained why B1's run produced `subrogation-pilot-v2` (auto-suffix). (d) Note that `.env` is already populated (gotcha at bottom of #1 block) saved ~5 minutes of first-live-run setup. (e) Plan §7.1.3 verification commands were copy-pastable and produced the expected output; the `DataReport.json` inspection snippet caught that live SQL differs from fixture on the first try.
- **What was missing:** (a) No mention that pre-flight was last-green at Session 22's commit `bb52915` — I did re-run it, but a note "Session 23 did NOT run pre-flight" (which IS there, as gotcha #3) would be more prominent if it were a first-class checklist line rather than a gotcha. Small issue — the gotchas section was read. (b) No note that the live run takes ~5 minutes because the data agent makes ~4-8 sequential Anthropic calls per primary query. My first reaction was "is it hung?" around 4 minutes in. One-line note would save that. (c) The plan's cost estimate in §7.1.4 (~$0.05–0.10/run at sonnet rates) didn't get translated into "multiply by ~5 for opus" when the user picked opus — trivial but would have been useful context for the first invoice.
- **What was wrong:** (a) **Gotcha #5 and plan §3.9 both claim `agents/website/__main__.py` and `cli.py` do not exist.** Both DO exist (`git log` shows `e9f0d10 feat(phase-d): website CLI`). Session 23 either mis-greped or the `ls -la` check returned negative on a working-dir state I can't reproduce. Cost me ~3 minutes of "wait, which is true?" before checking `git log`. This makes candidate #6 (reconcile OPERATIONS §4.2/4.3) an audit task, not a rewrite task — but Session 23's handoff directed Session 25 to "replace §4.2/4.3 with scripts/ recipe." That direction is based on a false premise. (b) Plan §17 grep expectations: "runner contract: 16" matches; "run_pipeline(: 13" matches; "IntakeAgent(: 4" matches; "DataAgent(: 9" matches. "AnthropicLLMClient( production: 2" — my naive re-run returned 4, but those extras are a class definition and a docstring mention. The plan's "2 instantiations" was correct; the executor (me) had to distinguish instantiations from symbol occurrences. Minor — cost ~30 seconds.
- **ROI:** ~3× return. Reading the plan + handoff (~10 min total) saved ~30 min of implementation discovery. The two wrong claims cost ~3 min combined — not enough to tank the score, but enough to drop from 9 to 8.

## Session 22 Handoff Evaluation (by Session 23)
**Score: 9/10.** Session 22's handoff was unusually well-suited to a planning session — the ACTIVE TASK named six pre-scoped candidates, ranked by readiness, and the candidate-#1 "key files for each candidate" block (`scripts/run_pipeline.py:201-206`, `intake/anthropic_client.py`, `data-agent/.../anthropic_client.py`, `pipeline.py`, `tests/orchestrator/test_pipeline.py`) was exactly the file set I needed for the plan's evidence-based inventory.

- **What helped:** (a) The candidate-#1 block listed `scripts/run_pipeline.py:201-206` as the stubbed call site — I went straight to those 6 lines, confirmed the lambdas, and understood the wiring scope inside the first 5 minutes of Phase 0. (b) Gotcha #6 ("intake agent runs a LangGraph with human-in-the-loop review (max 10 questions, max 3 revisions) — it's not a single `() -> IntakeReport` call. Either wrap it in an adapter that executes the graph to termination and returns the final state's `IntakeReport`, or change `run_pipeline`'s intake contract") was the single most important note in the handoff. It directly drove plan §3.6 (the runner-shape gap) and §5 (the three implementation shapes). Without it I would have had to discover the gap experimentally. (c) Gotcha #1 (Session 22's live GitLab project still exists at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot`) is a Session 24+ concern but I verified the URL during plan §1 and used it as the predecessor reference. (d) The explicit recommendation that Scope B should be a planning session first (failure mode #18) anchored my opening framing to the user; saved a round-trip on "is this a plan or an impl session." (e) Gotcha #3 (`.env` populated with real credentials, gitignored) made it clear the next live run can re-use the same `.env` — incorporated into plan §3.8 and §13. (f) Learning #18 (CI gate scope can diverge from declared tool scope) is referenced in plan §3.9 to explain why OPERATIONS §4.2/4.3 has gone undetected. (g) The "five remaining candidates" framing meant I could preserve them as Session 24 carryovers without re-stating each one's value.
- **What was missing:** (a) No file-level pointer to `IntakeAgent.run_with_fixture` / `run_scripted` — I had to grep for `class IntakeAgent` and read the facade myself. A line like "intake facade has `run_with_fixture` and `run_scripted` — neither matches `IntakeRunner`'s `() -> IntakeReport` shape" would have saved ~5 minutes. (b) No mention that `DataAgent.run` already matches `DataRunner` exactly — Session 22 might not have noticed, and finding this was the single most decision-shaping fact in the plan (it made B1 the obvious first phase). (c) No mention that the OPERATIONS §4.2/4.3 invocations are LITERALLY broken (no `__main__.py` exists). Session 22 deferred the audit to a Session 23 candidate (#6) but the plan needed to know this to avoid documenting the wrong canonical entry point.
- **What was wrong:** Nothing factually wrong. Every cited file path, line range, and BACKLOG-item-number correspondence held up.
- **ROI:** ~5× return. Reading the handoff (~3 min) saved ~15 min of orientation, scope-definition, and "is this plan or implementation?" round-trips with the user.

### What Session 24 Did
**Deliverable:** Scope B Phase B1 — real Anthropic data agent wired into `scripts/run_pipeline.py` via `--llm data`. Per plan `docs/planning/scope-b-plan.md` §7.1. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Live run ID:** `run_b1_live` → project `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot-v2` (auto-suffixed past Session 22's v1).
**Commits:** (pending this session's commit) — single `feat(session-24): scope-b1 real data agent` commit.

**What was done:**

1. **Phase 0 orientation** — Read `SAFEGUARDS.md` + `SESSION_RUNNER.md` in full, `SESSION_NOTES.md` ACTIVE TASK + Session 23 handoff in full, ran `git status`/`git log -6`/`git diff --stat`, ran `python methodology_dashboard.py` (project at 91/100, medium risk, active). No ghost sessions. Reported state to user.

2. **Phase 1B stub** — Wrote the IN-PROGRESS stub to SESSION_NOTES.md ACTIVE TASK before any technical work (failure mode #14 protection). Stated commitment back to user: "deliverable is Phase B1 only; no B2 bundling."

3. **User-decision round-trip** — Presented plan §8's 5 open decisions with recommendations; user confirmed all (a) except §8.2 → **opus-4-7** instead of sonnet-4-6 (to remove "was it the model?" as a confounding variable on the first pilot run). Added `--model` to the B1 surface (not in original plan §8.2 recommendation; documented as an approved deviation).

4. **Plan re-read + grep re-verification** — Re-read `docs/planning/scope-b-plan.md` §1–§8 in full; re-ran §17's 5 grep inventories. Runner-contract/run_pipeline/IntakeAgent/DataAgent counts matched; `AnthropicLLMClient(` returned 4 (not plan's 2) but the extras were a class def + a docstring, not instantiations. Discovered **website `__main__.py` and `cli.py` DO exist** (plan §3.9 and Session 23 gotcha #5 both wrong) — flagged in handoff, NOT acted on (not blocking for B1, belongs in candidate #6 re-audit).

5. **Pre-flight before code changes** — `uv run pytest -q` → 422 passed, 97.24% coverage. `uv run ruff check src/ tests/ packages/` → clean. `uv run mypy src/` → clean. `.env` verified to have `ANTHROPIC_API_KEY`, `GITLAB_TOKEN`, `MPC_HOST`, `MPC_HOST_URL`, `MPC_NAMESPACE`.

6. **Implemented §7.1 changes:**
   - `scripts/run_pipeline.py`: added `--llm {none,data}` (default `none`), `--model` (default `claude-opus-4-7`), `--db-url` (default `None`). New helper `build_data_runner(*, llm_mode, db_url, model)` mirrors `build_website_runner`'s shape; returns fixture closure on `none` or `DataAgent(AnthropicLLMClient(model=...), db=...).run` on `data`. Replaced the `lambda _req: data` call at line 205-206 with the helper's return. Updated banner + `[1/5]` section to announce LLM mode. ~+40 / -5 LOC.
   - `--llm both` deliberately NOT added; Session 25's B2 work will extend `choices=["none","data"]` to `choices=["none","data","both"]`. Keeping the CLI schema truthful to implemented behavior.
   - `OPERATIONS.md` §4.4 added with the B1 recipe, model-selection table, disconnected-DB default explanation, and a copy-pasteable checkpoint-inspection snippet for confirming real Claude output. ~+75 lines.
   - `docs/tutorial.md` §6 "Real LLM-backed run" added with §6a (run command), §6b (verification snippet), §6c (model table + rationale for opus as pilot default), §6d (optional DB connection). The previous §6 "Using the orchestrator programmatically" renumbered to §7. ~+65 lines.
   - `CHANGELOG.md` [Unreleased] entry at top with explicit "Deviation from plan: §8.2 opus instead of sonnet" callout.
   - `BACKLOG.md` "Up Next" item #1 rewritten as a 3-sub-bullet hierarchy (B-1 ✓, B-2 open, B-3 optional) with plan section pointers.

7. **Scope A regression verified** — Ran `--llm none --run-id run_b1_fake_llm` against fresh baseline `run_b1_fake_baseline` (no flags). Checkpoint envelope payloads are byte-identical; only envelope metadata (run_id, timestamps) differs. Scope A behavior confirmed unchanged.

8. **Live B1 run verified** — `set -a; source .env; set +a; uv run python scripts/run_pipeline.py --live --host gitlab --llm data --model claude-opus-4-7 --run-id run_b1_live`. Result: `COMPLETE` in 5m22s. Data stage latency 317,738 ms (real Claude — 4+ sequential API calls); website stage 4,371 ms (matches Session 22's baseline). Project created at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot-v2` (auto-suffixed). `DataReport.json`: 19,745 bytes, status `COMPLETE`, 1 primary query with 11 quality checks + full 7-section datasheet, 12 unconfirmed expectations (db=None), 5 data quality concerns, summary mentions `run_b1_live` by name (proves Claude actually ran). Primary query SQL is structurally different from the fixture — Claude added `policy_id`, `fnol_date`, `fault_evidence_level`, `information_completeness_score` columns and used SQL Server `DATEDIFF(DAY, ...)` syntax vs the fixture's BigQuery `DATEDIFF('day', ...)`.

9. **Wiki freshness BACKLOG item added** — Per user mid-session request, added candidate #7 covering wiki drift (Content-Recommendations, Home, Pipeline-Overview, Getting-Started, Agent-Reference). Rule: remove completed "Recommended additions"; rewrite partial ones to describe the remaining gap only.

10. **Final pre-commit green check** — `pytest -q` → 422 passed. `ruff check` on CI scope → clean. `mypy src/` → clean.

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. Re-read the entire plan + Session 23 handoff + grep-inventory verification BEFORE writing the Phase 1B stub. Did NOT start typing code until the user signed off on §8 decisions and the pre-flight was green.
- **Implementations read, not just descriptions:** Yes. Read `DataAgent.__init__` + `DataAgent.run` bodies, `AnthropicLLMClient.__init__` body, and the data agent CLI's `_build_llm` + `ReadOnlyDB` construction to confirm the plan's "mirror the CLI" direction was accurate. Did NOT trust "the shape matches" without checking.
- **Stakeholder corrections needed:** 1 (the model question — user challenged sonnet-4-6 vs opus-4-7, I presented tradeoffs, user chose opus). This is a GOOD correction — it's the kind a plan should surface by default; Session 23's plan framed §8.2 as "recommend (a), defer quality conversation" which skirted the actual cost/benefit. Not a process failure. Zero corrections on scope, workstream, or implementation approach.
- **What I got right:** (a) Phase 1B stub written before any technical work. (b) User-decision round-trip happened BEFORE pre-flight → before code edits; commit boundary preserved. (c) Did NOT bundle candidate #3 (the ruff errors I noticed mid-session) into the B1 commit, per SAFEGUARDS + failure mode #18 — explicitly told the user why and got confirmation. (d) Caught Session 23's gotcha #5 being wrong during grep re-verification, flagged it, did NOT act on it (carryover #6's territory). (e) Caught the `AnthropicLLMClient(` count discrepancy, traced it to "instantiations vs symbol occurrences," did NOT waste time on further investigation. (f) Kept the `--llm` choices to `{none,data}` (truthful surface) instead of accepting `both` and erroring — simpler schema for B2 to extend. (g) Reused Session 22's `subrogation-pilot` project name via auto-suffix rather than polluting the namespace with a new name. (h) Tutorial §6 + OPERATIONS §4.4 both explain WHY opus is the default (confounding-variable argument) — pilot readers need the reasoning, not just the command.
- **What I got wrong:** (a) Initial `scripts/run_pipeline.py --help` scan missed that my banner `print(f"...{args.run_id}")` would become F541 if I'd written it without the placeholder; I got lucky it actually uses a placeholder. No actual error, but I didn't proactively lint my new `print(f"...")` lines to confirm. -0.3. (b) Did not parameterize the tutorial §6c model table with actual cost-per-run numbers for opus — I stated "5×" as a ratio, not `~$0.25–$0.50 at opus`. Plan §7.1.4 had the sonnet estimate (~$0.05–$0.10); scaling to opus is arithmetic but would have been more useful. -0.3. (c) Did not test `--llm data --live --host github` — only verified GitLab. Risk is low (the data side is host-independent), but it's an untested path. -0.4.
- **Quality bar vs previous sessions:** Matches Session 22 (executed a live-host run + carryover findings) and improves on Session 23 (caught and corrected a load-bearing claim in the predecessor plan). The B1 deliverable is smaller than Session 22's fix + audit package but equally well-verified.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #20:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 20 | When a plan asks "which model?" in an open-decisions section, **do NOT default to the cheapest option for a pilot's first real run**. The plan's rationale — "defer the quality conversation to after the first real run produces output we can judge" — is weak when output quality is literally what the pilot is evaluating. If the model turns out to be limiting, the first-run impression is contaminated and "was it the model?" becomes a confounding variable forever after. Recommend the highest-quality option for the *first* run; fall back to cheaper models for iteration once output shape is validated. For a ~$0.50 vs ~$0.10 tradeoff on a pilot, the marginal cost is trivial compared to the cost of a muddled conclusion. | Session 24 (user challenged plan §8.2's sonnet-4-6 → switched to opus-4-7) | Any session where a plan recommends a cheaper/faster model for a first-impression pilot run. |

### What Session 23 Did
**Deliverable:** `docs/planning/scope-b-plan.md` — 822 lines, 18 sections — the planning artifact for BACKLOG #1 (Scope B real LLM-backed intake + data agents). **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:** (pending this session's commit) — single `docs(session-23): scope-b plan` commit landing the new plan document + this SESSION_NOTES close-out.

**What was done:**

1. **Phase 0 orientation** — Read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` ACTIVE TASK + Session 22 handoff in full, ran `git status`/`git log -10`/`git diff --stat`, ran `python methodology_dashboard.py` (project at 91/100, medium risk, active). No ghost sessions. Reported state to user.

2. **Phase 1B stub** — Wrote the IN-PROGRESS stub to SESSION_NOTES.md ACTIVE TASK before any technical work (failure mode #14 protection). Stated commitment back to user: "deliverable is a plan, not implementation."

3. **Evidence-based research** — Parallel reads of the 8 load-bearing files: `scripts/run_pipeline.py` (the lone production call site), `orchestrator/pipeline.py` (runner-contract source of truth), `agents/intake/anthropic_client.py`, `packages/data-agent/.../anthropic_client.py`, `agents/intake/agent.py` (the facade with `run_scripted` / `run_with_fixture`), `packages/data-agent/.../agent.py` (the facade where `.run` already matches `DataRunner`), `agents/intake/graph.py` + `state.py` (the LangGraph + caps), `packages/data-agent/.../llm.py` + `db.py` (the LLMClient protocol + optional DB).

4. **Ran 5 grep inventories** for §17 of the plan: `IntakeRunner|DataRunner|WebsiteRunner` (16 in `.py`, ~5 more in docs), `run_pipeline\(` (13 in `.py`), `IntakeAgent\(` (4), `DataAgent\(` (9), `AnthropicLLMClient` (39 across packages, tests, docs, UI). Confirmed `agents/website/__main__.py` and `cli.py` do NOT exist — verifies that OPERATIONS §4.2/4.3 references a phantom entry point.

5. **Read related infra**: `IntakeSessionStore` (Web UI runner), `OrchestratorSettings.from_env()`, `CheckpointStore`, `intake/fixture.py` (YAML fixture format + `answers_from_fixture` + `review_sequence_from_fixture` helpers), `OPERATIONS.md` (full read), `docs/tutorial.md` §5/6, `tests/orchestrator/test_pipeline.py` (the test pattern using `lambda: intake`/`lambda _req: data`).

6. **Wrote `docs/planning/scope-b-plan.md`** with 18 sections covering: context, glossary, evidence inventory, current-vs-target state, three implementation shapes (I-1 fixture, I-2 scripted-answers, I-3 Web UI bridge), recommended sequence (B1 → B2 → optionally B3), per-phase implementation plans with LOC estimates and verification commands, 5 user-decisions to resolve before B1, failure-mode handling matrix, checkpoint/resume strategy, test strategy, consolidated verification commands per phase, risk register (7 items), anti-scope (7 do-NOTs), per-phase session boundaries, file reference map, full grep inventory for executor verification, and a sign-off checklist.

7. **Verified plan claims** — re-ran the grep counts after writing; one count (runner contract) was off (claimed 11 in §17, actual 16 in `.py`). Corrected via Edit.

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. Did all 8 file reads + all 5 grep inventories + the OPERATIONS/tutorial doc surface BEFORE drafting the plan. The plan's §3 (evidence inventory) cites file:line for every claim and was assembled from the read pass, not from memory.
- **Implementations read, not just descriptions:** Yes. Read `IntakeAgent.run_scripted` body in full to find the `RuntimeError` raise sites at lines 100-104 and 117-120 — these became the load-bearing safety gap in plan §3.6 and §7.2.2 (the adapter the executor must add). Read `DataAgent.run` body in full to confirm the try/except at lines 50-53 — became the basis for "data side is mechanical." Did NOT just read class names and trust signatures.
- **Stakeholder corrections needed:** 0. User said "go" → orientation report given, "work on item 1" → restated the planning-vs-impl distinction and got implicit confirmation by proceeding. No round-trips on scope or workstream.
- **What I got right:** (a) Phase 1B stub written before any technical work — failure mode #14 protection held. (b) Stated commitment back to user explicitly: "deliverable is a plan, not implementation. I'll close out when the plan is committed." This makes the contract observable. (c) Plan §14 (anti-scope) explicitly forbids the four scope-creep patterns the executor will be tempted by (new CLI, modifying graphs, bundling resume, fixing carryover findings). (d) Plan §15 specifies the per-phase session boundary so Session 24 cannot accidentally bundle B1+B2. (e) Three implementation shapes (§5) presented with comparison table and per-shape pros/cons rather than picking one and forcing the user's hand. (f) Five user-decisions section (§8) makes the decisions explicit and recommends defaults so the user can sign off in one pass. (g) Per-phase verification commands (§7.x.3) are copy-pastable, with expected outputs. (h) §17 grep inventory ends with `ls -la` checks for the phantom website entry points so the executor can verify the plan's §3.9 claim independently. (i) Verified the §17 numbers myself after writing — caught the 11→16 mistake and fixed it.
- **What I got wrong:** (a) The duplicated "What Session 23 should do" block in SESSION_NOTES.md after my Phase 1B edit — I inserted the new ACTIVE TASK above the old one without removing the old one, then noticed during close-out and had to consolidate in this big edit. -0.5 point; pure operator error. (b) Plan §17's first grep estimate was wrong (11 vs 16) — caught and fixed, but it shouldn't have been wrong on the first pass. The numbers section should always be filled in AFTER running the greps, not from memory of my earlier pass. -0.5 point. (c) Did not read `tests/orchestrator/test_metrics.py:246` (the second `run_pipeline(` test call site) — it's listed in the grep but I assumed it was a metrics test wrapping the same pattern. Probably true, but uninvestigated. Low risk; the executor will see it if it matters.
- **Quality bar vs previous sessions:** Meets Session 22's bar. Planning-session deliverable rather than implementation, but the discipline (grep-based inventory, per-phase completion criteria, explicit anti-scope, explicit user-decisions block, file-reference map) is at least as rigorous as Session 22's audit + bug fix.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #19:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 19 | When writing a planning document with a grep-based inventory, **fill in the expected counts AFTER running the greps**, not from memory of an earlier pass. Memory of "I saw 11 matches" is unreliable; the actual count was 16 (5 doc references I had glossed over). Rule: write the section with `XX` placeholders, run the greps, paste the numbers in. The executor's first verification step should be re-running the greps and confirming the plan's numbers — if the plan's numbers are wrong by a non-trivial amount, the executor's first action is to question the plan's accuracy. Don't waste that trust on an avoidable mistake. | Session 23 (plan §17 first draft said "11" for runner contract; actual 16) | Any planning session that writes a grep inventory or evidence count. |

### Phase 3D: Handoff to Session 24

Full "What Session 24 should do" content is in the **ACTIVE TASK** block at the top of this file. Six candidates — #1 is Phase B1 of `scope-b-plan.md` (one session); #2–#6 are Session 22's carryover findings.

**Key files for each candidate:**

For #1 (Phase B1 — real data agent wiring):
- `docs/planning/scope-b-plan.md` — **read in full first**. §1–§4 establish context; §6–§7.1 specify Phase B1; §8 lists the 5 user-decisions; §15 has the session-boundary contract.
- `scripts/run_pipeline.py:201-206` — the stubbed lambdas to replace
- `scripts/run_pipeline.py:92-122` — `build_website_runner` is the structural template for `build_data_runner`
- `packages/data-agent/src/model_project_constructor_data_agent/cli.py:99-119` — production-tested `DataAgent + AnthropicLLMClient + ReadOnlyDB` wiring; mirror this
- `packages/data-agent/src/model_project_constructor_data_agent/agent.py:32-61` — `DataAgent.run` already matches `DataRunner` exactly — no adapter needed
- `OPERATIONS.md` §4 — extend with a new §4.4 per plan §7.1.1
- `docs/tutorial.md` §5 — extend with a new §6 per plan §7.1.1
- `.env` — already populated with `ANTHROPIC_API_KEY`, `GITLAB_TOKEN`, `MPC_HOST=gitlab`, `MPC_HOST_URL=https://gitlab.com`, `MPC_NAMESPACE=rmsharp-modelpilot` (Session 22). Re-use via `set -a; source .env; set +a` before any live invocation.

For #2 (`MPC_NAMESPACE` validator + docs):
- `src/model_project_constructor/orchestrator/config.py:98,111` — env-var validators live here
- `.env.example:47` — MPC_NAMESPACE template line
- `OPERATIONS.md` §1 env-var table
- `docs/tutorial.md` §5c MPC_NAMESPACE section
- `src/model_project_constructor/agents/website/gitlab_adapter.py:79` — where the generic 404 error originates (improve the message?)

For #3 (CI lint extension to `scripts/`):
- `.github/workflows/ci.yml:19` — `uv run ruff check src/ tests/ packages/`
- `scripts/run_pipeline.py:34-54` — `sys.path.insert` + imports that trigger E402
- Choice: per-line `# noqa: E402` vs drop the sys.path hack (relies on `uv run` resolving the editable install)

For #4 (CI typecheck extension to `packages/`):
- `.github/workflows/ci.yml:28` — `uv run mypy src/`
- `pyproject.toml` `[tool.mypy]` — already declares both packages
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:218` — `TextBlock` type-guard cluster
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py:142` — `execution_status` literal narrowing
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py:26` — untyped `get_type` call

For #5 (self-hosted GitHub URL override):
- `scripts/run_pipeline.py:109-113` — the broken branch (`PyGithubAdapter(token=token)` no URL)
- `docs/tutorial.md` §5c — the false documentation
- `src/model_project_constructor/agents/website/github_adapter.py` — verify `base_url` constructor kwarg exists
- Untested live; code-read only.

For #6 (reconcile OPERATIONS §4.2/4.3):
- `OPERATIONS.md:174-208` — the broken §4.2/4.3 (Session 23 confirmed the entry points don't exist)
- `docs/tutorial.md` §5 — the canonical recipe to mirror in OPERATIONS
- Plan §3.9 of `scope-b-plan.md` documents the verification commands (`ls -la src/model_project_constructor/agents/website/__main__.py` etc.) so a re-verification is one command

### Gotchas for Session 24

1. **The plan IS the contract.** If the user picks #1, do not deviate from `scope-b-plan.md` §7.1 without a re-planning round-trip. Failure mode #11 (gaps from memory) and #19 (plan-mode bypass) both apply: Session 24 should re-read the plan in Phase 0, not assume it knows the plan from this handoff.

2. **Plan §8 has 5 open decisions.** All five recommendations are option (a). Confirm with the user before B1 starts. The most consequential is §8.4 (where the `RuntimeError → DRAFT_INCOMPLETE` adapter lives — recommendation: in `scripts/run_pipeline.py`, NOT `agents/intake/agent.py`). For Phase B1 only §8.1, §8.2, §8.5 are immediately relevant; §8.3 and §8.4 surface in B2.

3. **Session 23 did NOT execute any code.** Pre-flight (ruff/mypy/pytest) was NOT re-run this session — last green confirmed by Session 22 (commit `bb52915`). Session 24 should run it in Phase 0 before touching `scripts/run_pipeline.py`.

4. **The live GitLab project from Session 22 is still live** at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot`. Phase B1 will create a new one (auto-suffixed if `project_name_hint="subrogation_pilot"` is unchanged); plan §15 names the run IDs `run_b1_live` etc. so checkpoints stay disambiguated.

5. **`OPERATIONS.md` §4.2/4.3 are confirmed broken** (Session 23 verified `__main__.py` and `cli.py` for `agents/website/` do not exist). The plan deliberately routes through `scripts/run_pipeline.py` to avoid extending broken docs. Carryover #6 is the cleanup. Do NOT try to make §4.2/4.3 work in B1.

6. **Plan §13 and §16 cite line ranges** based on the codebase as of commit `bb52915` (Session 22). If Session 24 runs after a different session lands first, re-verify with the §17 grep inventory.

7. **`probability` vs `likelihood`** — durable user correction, still applies. Any LLM-adjacent prose or prompt edits should use `probability` for `P(event)`.

8. **Re-read `SAFEGUARDS.md` and `SESSION_RUNNER.md`** at Session 24 start. Failure modes #14 (ghost session), #18 (plan-to-impl bleed — high risk for B1→B2 bundling), and #19 (plan-mode bypass — Session 24's job IS to follow the plan, but the plan is a draft until verified) all apply.

9. **Plan §17's grep inventory is the executor's single best Phase-0 verification.** Re-run those 5 commands. If counts have drifted by more than a small margin, do not start implementation — the plan's claims may be stale.

10. **`docs/planning/scope-b-plan.md` is not yet linked from anywhere** (no entry in BACKLOG.md "Up Next" preamble pointing to it; no entry in CHANGELOG.md). Session 24 should add a one-line BACKLOG note pointing item #1 at the plan, and a CHANGELOG `[Unreleased]` entry per plan §7.1.1. This is small but easy to forget.

### Session 23 close-out checklist

- [x] Phase 0 orientation report given, waited for user direction
- [x] Phase 1B stub written to SESSION_NOTES.md before technical work
- [x] Evidence-based research: 8 file reads + 5 grep inventories + verification of phantom entry points
- [x] Plan written to `docs/planning/scope-b-plan.md` (822 lines, 18 sections)
- [x] Plan §17 numbers verified post-draft; one count corrected (11 → 16)
- [x] Phase 3A: Session 22 handoff evaluated and scored above
- [x] Phase 3B: Self-assessment scored and written above
- [x] Phase 3C: Learning #19 queued for SESSION_RUNNER.md
- [x] Phase 3D: Handoff to Session 24 above (ACTIVE TASK + 6 candidates + key files + 10 gotchas)
- [x] Phase 3E: Commit main-repo changes (`docs/planning/scope-b-plan.md` + `SESSION_NOTES.md`) — commit `14dc53f`
- [x] Phase 3F: Verbal report to user

---

### Phase 3D: Handoff to Session 25 (continued)

Full "What Session 25 should do" content is in the **ACTIVE TASK** block at the top of this file. Seven candidates — #1 is Phase B2 (the natural sequel); #2–#6 are carryover findings from Sessions 22 & 24; #7 is the new wiki-freshness item.

**Key files for each candidate:**

For #1 (Phase B2 — scripted-answers intake):
- `docs/planning/scope-b-plan.md` §7.2 — **read in full first**. §7.2.1 lists files to change; §7.2.2 has the adapter reference implementation; §7.2.3 has the per-phase completion criteria (happy path + failure-injection test).
- `scripts/run_pipeline.py:92-128` — `build_data_runner` (Session 24) is the structural template for `build_intake_runner`. Mirror the same shape.
- `scripts/run_pipeline.py:170-200` (approximately — re-check post-Session-24 line numbers) — CLI flag block; add `--intake-fixture path/to/sub.yaml`.
- `src/model_project_constructor/agents/intake/agent.py:48-125` — `IntakeAgent.run_scripted(...)`. The `RuntimeError` raise sites at lines 100-104 and 117-120 are the failure surface the adapter must catch.
- `src/model_project_constructor/agents/intake/fixture.py:9-75` — `load_fixture`, `answers_from_fixture`, `review_sequence_from_fixture` helpers. Use directly.
- `src/model_project_constructor/agents/intake/anthropic_client.py:53-170` — `AnthropicLLMClient` constructor (reads `ANTHROPIC_API_KEY` from env).
- `tests/fixtures/subrogation.yaml` — the canonical fixture for the happy-path live run.
- For the failure-injection test (plan §7.2.3 criterion #3): create a small fixture `tests/fixtures/_b2_failmode.yaml` with only 1 `qa_pairs` entry but `draft_after: 99` — this exhausts the answer script before the graph can converge, triggering the `RuntimeError`.

For #2 (`MPC_NAMESPACE` validator + docs):
- `src/model_project_constructor/orchestrator/config.py:98,111` — env-var validators live here
- `.env.example:47` — `MPC_NAMESPACE` template line
- `OPERATIONS.md` §1 env-var table
- `docs/tutorial.md` §5c — `MPC_NAMESPACE` section
- `src/model_project_constructor/agents/website/gitlab_adapter.py:79` — where the generic 404 error originates

For #3 (CI lint extension to `scripts/`):
- `.github/workflows/ci.yml:19` — current `uv run ruff check src/ tests/ packages/`
- `scripts/run_pipeline.py:38-40` — the `sys.path.insert(...)` hack that causes E402s
- Exact pre-existing errors (confirmed by Session 24): **6 × E402** at lines 53-55, 63-65; **4 × F541** at lines 231, 294, 296, 306. F541s are auto-fixable via `uv run ruff check scripts/ --fix`. E402s need either `# noqa: E402` per-line or dropping the `sys.path.insert` (relies on `uv run` resolving the editable install — verify bare `python scripts/run_pipeline.py` is OK to drop).

For #4 (CI typecheck extension to `packages/`):
- `.github/workflows/ci.yml:28` — current `uv run mypy src/`
- `pyproject.toml` `[tool.mypy]` — already declares both packages
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:218` — `TextBlock` type-guard cluster (largest error cluster)
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py:142` — `execution_status` literal narrowing
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py:26` — untyped `get_type` call

For #5 (self-hosted GitHub URL override):
- `scripts/run_pipeline.py:109-113` — the broken branch (`PyGithubAdapter(token=token)` no URL). Note: post-Session-24 these lines may have shifted; grep for `PyGithubAdapter(`.
- `docs/tutorial.md` §5c — the misleading documentation
- `src/model_project_constructor/agents/website/github_adapter.py` — verify `base_url` constructor kwarg exists (PyGithub's `Github(base_url=...)` pattern)

For #6 (re-audit OPERATIONS §4.2/4.3):
- `OPERATIONS.md:174-208` — the recipes to re-verify (Session 24 confirmed the entry points DO exist despite Session 23's claim)
- `src/model_project_constructor/agents/website/__main__.py` (exists) — entry point
- `src/model_project_constructor/agents/website/cli.py` (exists, 7225 bytes) — Typer CLI
- `docs/tutorial.md` §5 — the `scripts/run_pipeline.py --live` canonical recipe to reconcile with
- Git history: `git log --oneline -- src/model_project_constructor/agents/website/cli.py` shows `e9f0d10 feat(phase-d): website CLI`; Phase-D was Session 17.

For #7 (wiki freshness sweep):
- `docs/wiki/claims-model-starter/Content-Recommendations.md` — likely has "Recommended additions" that have shipped
- `docs/wiki/claims-model-starter/Home.md` — front-page, drift-prone
- `docs/wiki/claims-model-starter/Pipeline-Overview.md` — may still describe B-1 as future
- `docs/wiki/claims-model-starter/Getting-Started.md` — may reference old CLI patterns
- `docs/wiki/claims-model-starter/Agent-Reference.md` — Session 23 handoff noted this has wrong API docs (`IntakeAgent().run(config)` and `DataAgent().run(...)` — both wrong since agents require `llm=`)

### Gotchas for Session 25

1. **The plan IS the contract for B2.** Re-read `docs/planning/scope-b-plan.md` §7.2 and §8.4 in Phase 0. Failure modes #11 and #19 apply. B2's load-bearing novelty is the `RuntimeError → DRAFT_INCOMPLETE` adapter — plan §7.2.2 has the reference implementation; do NOT reinvent it.

2. **Session 23's claim that `agents/website/__main__.py` and `cli.py` do not exist is WRONG.** Both files exist (added in commit `e9f0d10` during Phase D / Session 17). OPERATIONS.md §4.2/4.3 may actually work. This affects candidate #6 (was "rewrite §4.2/4.3", now "audit and document which invocations actually work"). Do NOT delete §4.2/4.3 without first running each invocation.

3. **Session 24 deviated from plan §8.2** — used `claude-opus-4-7` for B1 instead of the plan's recommended `claude-sonnet-4-6`. Session 25 should decide which model to use for the intake side in B2. Arguments: (a) opus if you want to hold quality constant vs. B1; (b) sonnet if you want to see whether the intake workflow is sonnet-robust. Pilot cost is not the constraint; "what do we learn from this run?" is.

4. **Session 24 added `--model` to the B1 surface** (not in original plan §8.2). B2 should either (a) reuse `--model` for both intake and data sides (single-model run), or (b) add `--intake-model` and `--data-model` (asymmetric). Recommend (a) for simplicity; revisit if asymmetric testing becomes interesting.

5. **The `--llm` choices set is currently `{none, data}`** in `scripts/run_pipeline.py`. B2 must extend this to `{none, data, both}`. The argparse `choices=` is the single place to change.

6. **Live B1 produced `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot-v2`** — auto-suffixed past Session 22's `subrogation-pilot`. B2's live run will produce `subrogation-pilot-v3` (or higher) by the same mechanism. Acceptable.

7. **`.env` is already populated** (`ANTHROPIC_API_KEY`, `GITLAB_TOKEN`, `MPC_HOST=gitlab`, `MPC_HOST_URL=https://gitlab.com`, `MPC_NAMESPACE=rmsharp-modelpilot`). Re-use via `set -a; source .env; set +a`.

8. **Session 24's pre-commit state is green** (pytest 422/422, ruff on CI scope clean, mypy clean). Session 25 should re-run pre-flight in Phase 0 to confirm no drift.

9. **The 10 pre-existing ruff errors in `scripts/run_pipeline.py`** (6 E402, 4 F541) are NOT a regression — they're Session 22 finding #3 and were already present when Session 24 started. CI scope (`src/ tests/ packages/`) does not include `scripts/`, so they do not block CI. See candidate #3.

10. **Live data-agent run takes ~5 minutes per primary query** (B1 was 5m17s for 1 primary query). B2 will add intake time on top — plan §7.2.4 estimates ~$0.10–$0.20 per B2 run at sonnet rates; at opus add ~5× markup. Sessions 25+ should budget wall time accordingly — the "is it hung?" moment is ~3–4 minutes in.

11. **`probability` vs `likelihood`** — durable user correction, still applies. Any LLM-adjacent prose or prompt edits should use `probability` for `P(event)`.

12. **Re-read `SAFEGUARDS.md` and `SESSION_RUNNER.md`** at Session 25 start. Failure modes #14 (ghost session), #18 (plan-to-impl bleed — high risk for B2→B3 bundling), and #19 (plan-mode bypass — follow the plan, but verify each claim against current code) all apply.

### Session 24 close-out checklist

- [x] Phase 0 orientation report given, waited for user direction
- [x] Phase 1B stub written to SESSION_NOTES.md before technical work
- [x] User-decision round-trip on plan §8 completed (opus-4-7 deviation approved)
- [x] Grep inventory re-verified per plan §17 (counts match modulo instantiation-vs-symbol interpretation; website entry points DO exist contrary to plan §3.9)
- [x] Pre-flight green before code changes (pytest 422/422, ruff on CI scope, mypy)
- [x] `build_data_runner` + CLI flags implemented in `scripts/run_pipeline.py`
- [x] `OPERATIONS.md` §4.4 added
- [x] `docs/tutorial.md` §6 added, old §6 renumbered to §7
- [x] `CHANGELOG.md` `[Unreleased]` entry added
- [x] `BACKLOG.md` "Up Next" item #1 rewritten as 3-sub-bullet hierarchy
- [x] Scope A regression verified (`--llm none` byte-identical to no-flag baseline on payload)
- [x] Live B1 run → `COMPLETE` at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot-v2`
- [x] Live DataReport verified: real Claude SQL ≠ fixture, 11 quality checks + full datasheet, 12 unconfirmed expectations, summary mentions `run_b1_live`
- [x] BACKLOG item for wiki freshness added (candidate #7)
- [x] Phase 3A: Session 23 handoff evaluated (8/10 with 2 wrong claims flagged)
- [x] Phase 3B: Self-assessment written (9/10)
- [x] Phase 3C: Learning #20 queued for SESSION_RUNNER.md
- [x] Phase 3D: Handoff to Session 25 above (ACTIVE TASK + 7 candidates + key files + 12 gotchas)
- [ ] Phase 3E: Commit main-repo changes — pending
- [ ] Phase 3F: Verbal report to user — pending

---

## Session 21 Handoff Evaluation (by Session 22)
**Score: 9/10.** Session 21's handoff was exceptional — the ACTIVE TASK block named three pre-scoped candidates with a clear "user picks" framing, key-files lists for each, and 9 gotchas that anticipated the exact friction I'd hit.

- **What helped:** (a) Gotcha #2 established `CHANGELOG.md` as authoritative and the wiki Changelog as audience-facing + possibly drift-prone — so when I recorded Session 22's findings I landed them in CHANGELOG first without re-scoping that question. Zero round-trip with the user on "where does this go." (b) Candidate #1's key-files list (`scripts/run_pipeline.py`, `OPERATIONS.md`, `.env.example`, `config.py`, `docs/tutorial.md`) was literally the list I needed — I read all five during Phase 0 and every one was load-bearing. (c) Gotcha #8 (`probability` vs `likelihood` preference) isn't a Session 22 concern but was correctly preserved as a durable correction. (d) Learning #17's "read `docs/methodology/README.md` first before proposing options on shared files" saved me an identical round-trip when deciding whether to update CHANGELOG from Session 22's findings or wait — I read the methodology and knew to update CHANGELOG directly. (e) The explicit note that `scripts/run_pipeline.py` uses `scripts/run_pipeline.py:201-206` stubbed intake/data runners was exactly the fact I needed to split Scope A vs Scope B cleanly; without it I would have assumed `--live` was a true end-to-end run and my initial Phase-0 tutorial audit would have been scoped wrong.
- **What was missing:** (a) Session 21 could not have known the `url=` → `host_url=` bug in `scripts/run_pipeline.py:119` was latent. But a note like "live path is untested end-to-end since Phase 5" would have set expectations. Gotcha #5 *did* say "live GitLab path hasn't been exercised since Phase 5" but mentioned `python-gitlab version-resolution pain` rather than kwarg-mismatch — close, but the specific failure mode was different. (b) No explicit callout that `MPC_NAMESPACE` takes a path, not a URL — but that's a repo-wide doc gap, not a 21-specific omission.
- **What was wrong:** Nothing factually wrong. Every file path, line reference, and BACKLOG-item-number correspondence held up.
- **ROI:** ~6× return. Reading the handoff (~4 min) saved ~25 min of orientation, scope-definition, and docs-precedence questioning. The candidate list directly shaped the session's opening assessment ("Are the tutorial instructions appropriate for…").

### What Session 22 Did
**Deliverable:** Scope A of BACKLOG #1 — live repo-creation smoke test via `scripts/run_pipeline.py --live --host gitlab` against public GitLab, with captured findings. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:** (pending this session's commit) — single `feat(session-22): fix live GitLab path + Scope A smoke test findings` commit landing the `scripts/run_pipeline.py` fix + CHANGELOG + BACKLOG + this SESSION_NOTES close-out.

**Live artifact produced:** `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot` (project ID `81385820`, initial commit `3dec5424d561df7f78d5d44807a39ed4b6ad7bf3`). Still live — kept as evidence for Scope B planning. Not deleted by Session 22.

**What was done:**

1. **Audited `docs/tutorial.md` §5 against the actual live code path** during Phase 0. Identified two gaps before any live call: (a) self-hosted GitHub URL override not wired through `scripts/run_pipeline.py:109-113`; (b) drift between tutorial §5 and `OPERATIONS.md` §4.2/4.3 on the canonical live-run command. Also framed Scope A vs Scope B distinction — tutorial §5 documents Scope A (live website stage with fixture intake/data), not the BACKLOG-#1 "real LLM-backed" phrasing.

2. **Found and fixed a blocking bug in `scripts/run_pipeline.py:119`.** Call site passed `url=host_url` but `PythonGitLabAdapter.__init__` (`gitlab_adapter.py:58-64`) is keyword-only and accepts `host_url=`. `--live --host gitlab` would have raised `TypeError: __init__() got an unexpected keyword argument 'url'` on the first real invocation. Two-character fix. This is the most important artifact of Session 22 — tutorial §5 had never successfully run.

3. **Ran CI-matching pre-flight.** `uv run ruff check src/ tests/ packages/` → clean; `uv run mypy src/` → clean; `uv run pytest -q` → 422/422, 97.24% coverage. Running ruff over `scripts/` OR mypy over `packages/` surfaces pre-existing issues that CI doesn't gate (filed as findings).

4. **Ran fake-mode baseline** with `--run-id run_preflight_fake`. Result `COMPLETE`, 38 files, ~4ms website stage. Confirmed the script's output envelope for comparison against the live run.

5. **Ran first live attempt** (`run_live_001`). **Failed** at website stage with `repo_error: group lookup failed for 'https://gitlab.com/rmsharp-modelpilot': 404`. Root cause: user set `MPC_NAMESPACE` to the full URL rather than the group path — but the failure mode surfaced a real documentation gap (none of `.env.example`, `OPERATIONS.md` §1, `docs/tutorial.md` §5 state that `MPC_NAMESPACE` is a path).

6. **Ran second live attempt** (`run_live_002`) after user set `MPC_NAMESPACE=rmsharp-modelpilot`. **Result `COMPLETE`.** Project created, 38 files committed, initial commit SHA `3dec542`, website stage latency 3,501ms (vs ~4ms in fake mode — ~875× expected network overhead). All 5 checkpoint files persisted: `IntakeReport.json`, `DataRequest.json`, `DataReport.json`, `RepoTarget.json`, `RepoProjectResult.result.json`.

7. **Verified live project via GitLab REST API** (`/projects/.../repository/tree?recursive=true`). Tree contains the expected directories (`analysis/`, `data/`, `governance/`, `queries/primary/`, `queries/quality/subrogation_training_set/`, `reports/`, `src/subrogation_pilot/`, `tests/`) and 11+ blobs at root incl. `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `README.md`. Governance manifest in `RepoProjectResult.result.json` shows all 10 tier-3-moderate artifacts and correct regulatory mapping (`SR_11_7` → 4 files, `NAIC_AIS` → 2 files).

8. **Recorded findings in `CHANGELOG.md` [Unreleased]** and added 6 new "Up Next" items to `BACKLOG.md` (Scope B + 5 findings).

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. Phase 0 audit of tutorial §5 against code caught Gap 1 (GHE URL override) and Gap 2 (OPERATIONS drift) before touching the live path. Reading `scripts/run_pipeline.py` + `gitlab_adapter.py` side-by-side before the first run caught the `url=` vs `host_url=` mismatch — prevented the TypeError from surfacing in the live run output, which would have forced a failure-diagnose-retry cycle.
- **Implementations read, not just descriptions:** Yes. Read `scripts/run_pipeline.py` in full, `gitlab_adapter.py` in full, `config.py` grep for env-var names, `ci.yml` to understand CI gate scope, `.env.example` + `OPERATIONS.md` + `docs/tutorial.md` for the doc surface. Verified live project via direct GitLab API call (not just the returned `project_url`).
- **Stakeholder corrections needed:** 2 small — (a) user corrected me that `.env` would hold credentials (I had offered `!`-prefixed shell option but they chose `.env`); (b) the first live run's `MPC_NAMESPACE=<URL>` mistake required one round-trip (though that surfaced finding #2, so net positive).
- **What I got right:** (a) Recognized Scope A vs Scope B distinction in the BACKLOG item BEFORE claiming the session — avoided falsely promising LLM-backed end-to-end when the script doesn't do that. (b) Phase 1B stub written before any technical work (failure mode #14 protection held). (c) CI-matching pre-flight discipline — ran the exact command matrix CI runs, not a broader local-only version; when I initially ran broader and saw failures I correctly identified them as CI-gap findings, not regressions. (d) Two `run_id`s for two attempts — keeps the failure and the success both inspectable in `.orchestrator/checkpoints/`. (e) Never committed the token; verified `.env` gitignored before running. (f) Verified live project independently via GitLab REST API rather than trusting the returned URL alone — caught that the tree is real, not just that a URL was returned. (g) Filed all 5 findings in CHANGELOG + BACKLOG with specific file:line pointers so Session 23 can pick any up as a one-session deliverable.
- **What I got wrong:** (a) Initial proposal to the user for credential handling offered `!`-prefixed shell input as Option 3 — but the user's `.env` approach was simpler and equally safe since `.env` is gitignored. Not wrong, just not the first suggestion. (b) Did not check whether `python -m model_project_constructor.agents.website` (the OPERATIONS §4.2 invocation) is actually a registered entry point; filed as finding rather than investigating. Defensible scope decision but leaves a small unknown. (c) Could have tried `--host github` too as a second data point, but that would have doubled the session scope. Scope A with one host (GitLab, as chosen by user) is legitimate completion.
- **Quality bar vs previous sessions:** Meets Session 21. Small-scope execution with rigorous pre-flight, two real runs (one intentional failure-surface), live API verification, and 5 findings filed with executor-ready specifics.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #18:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 18 | **CI gate scope can diverge from declared tool scope.** `pyproject.toml` may declare `[tool.mypy] packages = [A, B]` but CI only runs `mypy A`. Similarly `ruff` CI command may pass `src/ tests/ packages/` while excluding `scripts/`. Local "green pre-flight" using the tool's natural scope will surface failures that CI isn't gating — these are CI-gap findings, not regressions. Before declaring pre-flight failed: re-run with the EXACT command the CI workflow executes, compare. If CI-matching is green but broader-scope fails, file the CI gap + the underlying errors as findings, don't treat as a blocker. | Session 22 (ruff on `scripts/` + mypy on `packages/` surfaced pre-existing errors CI doesn't gate) | Any session where local pre-flight diverges from CI green-status. |

### Phase 3D: Handoff to Session 23

Full "What Session 23 should do" content is in the **ACTIVE TASK** block at the top of this file. Six candidates — #1 is Scope B (needs planning session first); #2–#6 are findings from Session 22 each sized as one session.

**Key files for each candidate:**

For #1 (Scope B — real LLM-backed intake + data agents):
- `scripts/run_pipeline.py:201-206` — current stubbed intake/data runners that need replacement
- `src/model_project_constructor/agents/intake/anthropic_client.py` — real intake runner signature
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` — real data runner signature
- `src/model_project_constructor/orchestrator/pipeline.py` — `run_pipeline` callable contract (intake: `() -> IntakeReport`, data: `(DataRequest) -> DataReport`)
- `tests/orchestrator/test_pipeline.py` — test pattern for pipeline wiring
- Plan must address: (a) do we run intake in one-question-at-a-time mode against an interactive user, or batch-from-fixture? (b) does the data agent need a live DB or can it run against fixtures? (c) checkpoint strategy for partial-LLM failures (Anthropic rate limit, token exhaustion).

For #2 (`MPC_NAMESPACE` validation + docs):
- `src/model_project_constructor/orchestrator/config.py:98,111` — where env-var validators live
- `.env.example:47` — MPC_NAMESPACE template line
- `OPERATIONS.md` §1 env-var table
- `docs/tutorial.md` §5c `MPC_NAMESPACE` section
- `src/model_project_constructor/agents/website/gitlab_adapter.py:79` — where the generic 404 error is raised

For #3 (CI lint extension to `scripts/`):
- `.github/workflows/ci.yml:19` — `uv run ruff check src/ tests/ packages/`
- `scripts/run_pipeline.py:34-54` — `sys.path.insert` + imports that trigger E402
- Choice: per-line `# noqa: E402` vs drop the sys.path hack entirely

For #4 (CI typecheck extension to `packages/`):
- `.github/workflows/ci.yml:28` — `uv run mypy src/`
- `pyproject.toml` `[tool.mypy]` — already declares both packages
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:218` — the bit-rot cluster; `TextBlock` type-guard needed
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py:142` — `execution_status` literal narrowing
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py:26` — untyped `get_type` call

For #5 (self-hosted GitHub URL override):
- `scripts/run_pipeline.py:109-113` — the broken branch (`PyGithubAdapter(token=token)` no URL)
- `docs/tutorial.md` §5c — the false documentation
- `src/model_project_constructor/agents/website/github_adapter.py` — verify `base_url` constructor kwarg exists
- Session 22 did NOT live-test this; code-read only.

For #6 (reconcile OPERATIONS §4.2/4.3 with script):
- `OPERATIONS.md` §4.2/4.3 — the two-command-alternative
- Grep for `__main__.py` or `[project.scripts]` in `src/model_project_constructor/agents/website/` — is `python -m model_project_constructor.agents.website` actually wired?
- `docs/tutorial.md` §5 — the canonical live-run recipe if we pick that one

### Gotchas for Session 23

1. **Session 22's live GitLab project is still live** at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot` (project ID `81385820`). If Session 23 does another live run with the same `project_name_hint="subrogation_pilot"` and same namespace, the adapter will auto-suffix (e.g., `subrogation-pilot-2`). Alternatively: delete the existing project via the GitLab UI or API before retrying. For Scope B planning this doesn't matter; for a second live run it does.

2. **Checkpoint directory contains `run_live_001` (failed) and `run_live_002` (succeeded).** `.orchestrator/` is gitignored so these won't commit, but they're useful reference state while Session 23 runs. Both have the same `IntakeReport.json` / `DataRequest.json` / `DataReport.json` envelopes; only `RepoProjectResult.result.json` differs (505 bytes for failed vs 3,146 bytes for succeeded).

3. **`.env` is populated with real credentials** (`ANTHROPIC_API_KEY`, `GITLAB_TOKEN`, `MPC_HOST=gitlab`, `MPC_HOST_URL=https://gitlab.com`, `MPC_NAMESPACE=rmsharp-modelpilot`). Gitignored. Session 23 can re-use by `set -a; source .env; set +a` before any live invocation. **Do not cat or echo these values** — if debugging is needed, print only the key names.

4. **The `url=` → `host_url=` fix in `scripts/run_pipeline.py:119` is the first change to the script since Session 18 shipped it.** Don't expect a test for this — the live path is not covered by any pytest test. The verification is the successful `run_live_002` recorded here and in `CHANGELOG.md`.

5. **CI-gap findings (3 and 4) are NOT blockers for any other work.** CI is green on the current master tree (confirmed via `gh run list`). Extending CI scope will reveal the underlying bit-rot but won't break the current green state until the new ruff/mypy commands are merged.

6. **For Scope B planning:** the real intake agent runs a LangGraph with human-in-the-loop review (max 10 questions, max 3 revisions) — it's not a single `() -> IntakeReport` call. Either wrap it in an adapter that executes the graph to termination and returns the final state's `IntakeReport`, or change `run_pipeline`'s intake contract. The data agent is closer to a single call but still needs a LangGraph runner and potentially a DB connection. Plan the wiring on paper first.

7. **`probability` vs `likelihood`** — durable user correction, still applies. Any LLM-adjacent prose or prompt edits should use `probability` for `P(event)`.

8. **Re-read `SAFEGUARDS.md` and `SESSION_RUNNER.md`** at Session 23 start. Failure modes #14 (ghost session), #18 (plan-to-impl bleed — relevant for Scope B), and #19 (plan-mode bypass) remain high-risk.

### Session 22 close-out checklist

- [x] Phase 0 orientation report given, waited for user direction
- [x] Phase 1B stub written to SESSION_NOTES.md before technical work
- [x] Tutorial §5 audited; 2 pre-existing gaps surfaced
- [x] Blocking bug in `scripts/run_pipeline.py:119` found and fixed (`url=` → `host_url=`)
- [x] CI-matching pre-flight run (ruff src/tests/packages/ + mypy src/ + pytest) — clean
- [x] Fake-mode baseline run captured as `run_preflight_fake`
- [x] First live run attempted (`run_live_001`) — failed with 404 group-lookup; finding recorded
- [x] Second live run (`run_live_002`) after user fixed `MPC_NAMESPACE` — `COMPLETE`
- [x] Live project verified via GitLab REST API
- [x] 5 findings recorded in CHANGELOG.md [Unreleased] + added to BACKLOG.md "Up Next"
- [x] Phase 3A: Session 21 handoff evaluated and scored above
- [x] Phase 3B: Self-assessment scored and written above
- [x] Phase 3C: Learning #18 queued for SESSION_RUNNER.md
- [x] Phase 3D: Handoff to Session 23 above (ACTIVE TASK + 6 candidates + key files + gotchas)
- [ ] Phase 3E: Commit main-repo changes (scripts/run_pipeline.py + CHANGELOG.md + BACKLOG.md + SESSION_NOTES.md) — pending
- [ ] Phase 3F: Verbal report to user — pending

---

## Session 20B Handoff Evaluation (by Session 21)
**Score: 9/10.** Session 20B's handoff was highly actionable — the ACTIVE TASK block gave me three pre-scoped candidates with file pointers, and the Gotchas list at lines 107-115 named the exact three cleanup items that became this session's deliverable when the user redirected with "clean up gotchas."

- **What helped:** (a) Gotcha #2 (stale `CHANGELOG.md`) not only flagged the problem but enumerated three resolution options (refresh / delete / leave-and-mark) — this shortened the scoping conversation with the user to one question. (b) Gotcha #3 (BACKLOG items #1 and #4 complete per Session 17) named the exact items and pointed to the authoritative source (Session 17's close-out at line 305), so I verified in one grep rather than re-auditing. (c) Gotcha #4 (duplicate "What Session 18 Did" blocks) gave the approximate line and attributed the origin ("carried from Session 18"), pointing me at Session 19's handoff evaluation at line 199 which confirmed which block was draft and which was polished. (d) The "Key files for any of the three candidates" section, even though I didn't pursue any candidate, established that the handoff author had anticipated the alternate paths. (e) Learning #15 and Learning #16 (added by 20A and 20B respectively) gave me a disciplined bias toward `Grep` + `Read` over speculative agent launches for a small cleanup task.
- **What was missing:** (a) No explicit note that the methodology mandates CHANGELOG.md as authoritative — the user had to redirect me when I proposed "refresh / delete / mark stale" as open options. Reading `docs/methodology/README.md:99` and `:215` (which I did after the redirect) would have preempted the question. This is on me more than on 20B, since the methodology guidance is in `docs/methodology/README.md`, not in the gotchas — but a single line in the gotcha pointing there would have saved a round-trip. (b) Gotcha #2's "option (c)" suggested "leave it as a developer-only commit log and mark it as such in its header" — this option **contradicts methodology** (CHANGELOG is authoritative, not a subordinate to the wiki). A handoff should not propose options that violate project conventions.
- **What was wrong:** Nothing factually wrong. The duplicate Session 18 blocks were at approximately the line numbers 20B described; BACKLOG items #1 and #4 were indeed complete per Session 17; `CHANGELOG.md` was indeed stale.
- **ROI:** ~4× return. Reading the handoff (~4 min) saved ~15 min of discovery on what needed cleanup and where.

### What Session 21 Did
**Deliverable:** Gotcha cleanup — refreshed `CHANGELOG.md` to authoritative/complete per methodology, migrated two completed BACKLOG items to CHANGELOG, and collapsed duplicate Session 18 blocks in this file. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:** (pending this session's doc commit) — single `docs(session-21): clean up gotchas` commit landing CHANGELOG refresh + BACKLOG trim + SESSION_NOTES dedupe + this close-out.

**What was done:**

1. **Refreshed `CHANGELOG.md`** from the Session 0 stub (19 lines) to a full authoritative record (155 lines of net additions). Structure follows Keep a Changelog with `[Unreleased]`, `[0.1.0 — Pilot Ready]`, `[0.0.1 — Project bootstrap]` sections. Covers every phase (1, 2A, 2B, 3A, 3B, 4A, 4B, A, B, C, D, 5, 6), every post-phase session (17 audit + CI fix, 18 tutorial, 19/20A/20B wiki), coverage-floor progressions (80→90→93→94), and the license change. Every entry cites commit hashes from `git log --reverse`. Added a leading paragraph establishing CHANGELOG.md as authoritative and the wiki Changelog as audience-facing and subject to drift (per user's direction that the "wiki page characteristics may change over time and level of detail").

2. **Removed BACKLOG "Up Next" items** "Pilot readiness audit" and "Ruff cleanup sweep" — both completed in Session 17 (`17f661d` resolved all 62 ruff errors; `b9c87c7` published the audit and declared PILOT-READY). Added a note in the "Up Next" preamble pointing readers to CHANGELOG.md for that history. `BACKLOG.md` now lists 8 open items (down from 10).

3. **Collapsed duplicate Session 18 blocks in SESSION_NOTES.md.** Replaced the Session 17 Handoff Evaluation stub ("Score: 9/10. (Unchanged from mid-session write — see below.)") with the full evaluation content from the "Previous Session 17 Handoff Evaluation" block below. Then deleted the entire "Previous ..." block and the draft "What Session 18 Did" block (Commits: TBD, brief self-assessment). The polished "What Session 18 Did" block at line 258 is preserved as the single source of truth.

**Verification:**

- `grep -c "Pilot readiness audit\|Ruff cleanup sweep" BACKLOG.md` → `0` (confirmed removed).
- `grep "What Session 18 Did" SESSION_NOTES.md` → three matches, but only **one** is an active block header (line 270). The other two are historical references inside 20B's gotcha #4 (line 117, a now-resolved TODO) and Session 19's handoff-eval text (line 199, an historical observation). No duplicate blocks remain.
- `git diff --stat` → `BACKLOG.md | 4 +-`, `CHANGELOG.md | 155 +++++++++++++++++++++++++++++++++++++++++++++++++++----`, `SESSION_NOTES.md | 33 +++++-------` (net +3 insertions, excluding this close-out write-up).

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. Re-read `SAFEGUARDS.md` in full, read methodology guidance for CHANGELOG (`docs/methodology/README.md:99,215,225`, `SESSION_RUNNER.md:15`, `SAFEGUARDS.md:77`), verified Session 17's close-out claims before migrating items, read both duplicate blocks before choosing which to delete, read the wiki Changelog to avoid duplicating audience-facing tone.
- **Implementations read, not just descriptions:** Yes. Ran `git log --reverse --pretty=format:'%ad %h %s'` to enumerate every commit; cross-referenced commit hashes against Session 17's self-assessment (which says "Fixed all ruff errors (56 auto + 6 manual)" and lists `66b44c8 17f661d d62efc2 b8d8d7e`) before migrating items.
- **Stakeholder corrections needed:** 1. User had to redirect my initial scoping question ("which of three options for CHANGELOG?") by pointing me at the methodology. Resolved in one round-trip.
- **What I got right:** (a) Wrote Phase 1B stub **before** technical work (failure mode #14 protection held). (b) Single `docs(session-21)` commit planned — avoids failure mode #18 (planning-to-implementation bleed). (c) CHANGELOG refresh includes a leading paragraph making the authority relationship explicit so future sessions don't repeat my initial scoping confusion. (d) BACKLOG removal preserves a preamble pointer to CHANGELOG so readers who remember the old items can find them. (e) SESSION_NOTES dedupe preserved the polished block and eliminated the draft — the opposite would have been a silent regression. (f) Verified via grep counts, not memory. (g) Scoped tightly — did NOT refactor unrelated BACKLOG items, did NOT update ROADMAP.md (even though it has a related "Task tracking (BACKLOG, CHANGELOG, ROADMAP)" reference), did NOT touch the wiki Changelog (user's parallel track / audience-facing layer). One deliverable, close out.
- **What I got wrong:** (a) Initially offered the user three open options (refresh / delete / mark-stale) on CHANGELOG before reading the methodology. Should have read `docs/methodology/README.md` first and arrived at the correct scoping directly. -1 point. (b) BACKLOG renumbering cascades: removing items #1 and #4 shifts items #2, #3, #9 (the three candidates referenced in the prior ACTIVE TASK) to #1, #2, #7. I updated the ACTIVE TASK references but cannot retroactively update historical handoffs that cite the old numbers. I mitigated by using the candidate **names** in the updated ACTIVE TASK text, not just numbers. (c) The `CHANGELOG.md` Phase 2A entry attributes the AST-walk decoupling test to Session 4 based on the commit message — verified the file exists (`tests/agents/data/test_data_agent_decoupling.py` per earlier grep output) but did not read the actual test to confirm the AST-walk description holds. Low risk because the commit message is definitive on what was added.
- **Quality bar vs previous sessions:** Meets 20A/20B. Small-scope cleanup delivered in a single session with rigorous verification. The CHANGELOG is now the canonical record; the wiki is free to drift without losing authority.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #17:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 17 | Methodology guidance for shared files (CHANGELOG, BACKLOG, ROADMAP, docs/methodology/*) lives primarily in `docs/methodology/README.md` and secondarily in `SESSION_RUNNER.md`/`SAFEGUARDS.md` inline notes. Before proposing options on how a shared file should be maintained, **read `docs/methodology/README.md` first** — specifically its "templates" section (`:99,:215`). A handoff that offers options including one that contradicts methodology (e.g., "mark CHANGELOG as subordinate to wiki") is a protocol violation; methodology outranks handoff suggestions. | Session 21 (CHANGELOG scoping round-trip) | Any session that is about to modify CHANGELOG.md, BACKLOG.md, ROADMAP.md, SESSION_NOTES.md, SAFEGUARDS.md, SESSION_RUNNER.md, or the methodology docs themselves. |

### Phase 3D: Handoff to Session 22

Full "What Session 22 should do" content is in the **ACTIVE TASK** block at the top of this file. Three candidates, ranked by readiness and value — identical to the list Session 21 inherited.

**Key files for each candidate** (unchanged from 20B's handoff, re-listed for convenience):

For candidate #1 (live run):
- `scripts/run_pipeline.py` — has `--live` flag; needs `ANTHROPIC_API_KEY` + `GITLAB_PRIVATE_TOKEN` or `GITHUB_PRIVATE_TOKEN`
- `OPERATIONS.md` — operator runbook
- `src/model_project_constructor/config.py` — `OrchestratorSettings.from_env()` and `require_*` guards
- `.env.example` — required env-var template
- `docs/tutorial.md` §5 "Live host"

For candidate #2 (resume-from-checkpoint):
- `src/model_project_constructor/orchestrator/pipeline.py` — current `run_pipeline` and `CheckpointStore`
- `src/model_project_constructor/orchestrator/checkpoints.py` — checkpoint layout
- `scripts/run_pipeline.py` — CLI entry point to extend with `--resume`
- `PipelineStatus` literal — `FAILED_AT_*` values are the resume points
- Tests: `tests/orchestrator/test_pipeline.py` — pattern for pipeline tests

For candidate #3 (statistical terminology glossary):
- `src/model_project_constructor/agents/intake/anthropic_client.py:33-50` — system prompt
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` — data-agent system prompt
- `initial_purpose.txt` — has prior "likelihood → probability" edits (Session 18)
- `tests/fixtures/subrogation.yaml` — has prior edits; a regression test would check the glossary terms don't appear misused in fixtures

### Gotchas for Session 22

1. **Wiki is live and fully up to date** as of 20B's commit `2fa274a` on `master` of `claims-model-starter.wiki`. If doing more wiki work, pull first — user is producing #6/#7/#10 in parallel.
2. **`CHANGELOG.md` is now authoritative and complete** as of Session 21 (commit pending). Treat it as the source of truth. Wiki Changelog at `docs/wiki/claims-model-starter/Changelog.md` is the audience-facing mirror and may drift; do not use it as a canonical reference. When completing work, add an entry here **first**, then consider updating the wiki mirror if the audience-facing summary would benefit.
3. **`BACKLOG.md` "Up Next" items renumbered** after Session 21's cleanup. If any historical handoff or wiki page cites old BACKLOG item numbers (e.g., 20B handoff's "item 2", "item 3", "item 9"), the current numbers are 1, 2, 7 respectively. The ACTIVE TASK block above uses the **current** numbers and the candidate **names** to be robust.
4. **If doing live run (candidate #1):** the fake-adapter path is solid but the live GitLab path hasn't been exercised since Phase 5. Expect some `python-gitlab` version-resolution pain; check `OPERATIONS.md` §"Credentials" first.
5. **If doing resume (candidate #2):** the existing `CheckpointStore` writes per-stage; verify it also writes pre-stage markers (so you can tell "`FAILED_AT_DATA` with DataRequest persisted" apart from "`FAILED_AT_DATA` before DataRequest was computed"). The resume strategy depends on this distinction.
6. **If doing glossary (candidate #3):** Session 18 already did a "likelihood → probability" sweep across fixtures. New glossary terms can land as system-prompt extensions without touching fixtures — but add a regression test that runs the data-agent prompt against a known-safe input and asserts the output uses "probability" not "likelihood".
7. **Re-read `SAFEGUARDS.md` and `SESSION_RUNNER.md`** at the start of Session 22. Failure modes #14 (ghost sessions) and #18 (planning-to-implementation bleed) remain the highest-risk patterns for this project.
8. **The user's preference for "probability" over "likelihood"** (when referring to `P(event)`) is a durable correction — see `Session 18` handoff. Honor it in all new LLM-adjacent prose.
9. **Methodology guidance for shared files lives in `docs/methodology/README.md`** — read it before proposing options on CHANGELOG, BACKLOG, ROADMAP, or any methodology doc. See Learning #17.

### Session 21 close-out checklist

- [x] Phase 0 orientation report given, waited for user direction
- [x] Phase 1B stub written to SESSION_NOTES.md before technical work
- [x] CHANGELOG.md refreshed with commit-level authoritative history
- [x] BACKLOG.md "Up Next" pruned of completed items (#1 and #4)
- [x] SESSION_NOTES.md duplicate Session 18 blocks collapsed
- [x] Phase 3A: Session 20B handoff evaluated, scored, written above
- [x] Phase 3B: Self-assessment scored and written above
- [x] Phase 3C: Learning #17 queued for SESSION_RUNNER.md
- [x] Phase 3D: Handoff to Session 22 above (ACTIVE TASK + candidates + key files + gotchas)
- [ ] Phase 3E: Commit main-repo changes (CHANGELOG.md + BACKLOG.md + SESSION_NOTES.md) — pending
- [ ] Phase 3F: Verbal report to user — pending

---

## Session 20A Handoff Evaluation (by Session 20B)
**Score: 9/10.** Session 20A's handoff was excellent — the ACTIVE TASK at the top of this file gave me per-page scope definitions (1–2 lines each), a complete per-page key-files list, and 9 actionable gotchas. I spent ~4 minutes reading it and was in the research phase within 5 minutes of "go."

- **What helped:** (a) Per-page key-files lists meant each of my 3 parallel research agents got a pre-scoped target set — no agent needed to figure out "which files" for its page. (b) Gotcha #6 (exact annual-impact numbers `$2M/$4M`) I quoted verbatim in Worked-Examples without re-reading. (c) Gotcha #2 (Session 20A's commit hash `8a41789`) let me verify no duplication. (d) Gotcha #5 (MIT license) landed directly in Contributing's §8. (e) The scope split ("20B gets cross-cutting pages") matched what I actually needed — the four pages really are cross-cutting (examples/extension/history/contribution) and not overlapping with 20A's agent-internals pages. (f) Learning #14 (parallel research agents) held up: all 3 agents completed this time, no timeouts — a ~5× research speedup over sequential reads.
- **What was missing:** (a) No page-length target (same gap 20A flagged for Session 19). I ended up at 172/222/205/200 lines for the four pages — defensible but not anchored by a spec. (b) Gotcha #3 said "3 page slots remain" then listed four (#1/#3/#8/#9) — off-by-one. Easy to ignore, but if I'd been on autopilot it could have caused me to miss one. (c) No mention of `tests/agents/website/test_templates.py:176-205` as the canonical generated-file listing. I found it myself via grep but naming it in the key-files list would have saved ~3 minutes.
- **What was wrong:** Nothing factually wrong. Every file path in the key-files list held up; every gotcha was accurate.
- **ROI:** ~6× return. Reading the handoff (~4 min) saved ~25 min of orientation and scope-definition.

### What Session 20B Did
**Deliverable:** 4 wiki pages + 3 updated nav files + live wiki publish. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:**
- Main repo: (pending this session's doc commit) — the 4 new pages, 3 nav updates, and SESSION_NOTES close-out will land together as `docs(session-20b)`.
- Wiki repo: `2fa274a` — `docs(session-20b): add worked examples, extending, changelog, contributing`. **Pushed to `origin/master`.** Live at `https://github.com/rmsharp/claims-model-starter/wiki`.

**What was done:**

1. **Worked-Examples.md** (~205 lines) — traces two end-to-end scenarios: **subrogation recovery** (tier-3 moderate, advisory) and **renewal profitability** (tier-1 critical, fairness-constrained). Sources: `initial_purpose.txt`, `tests/fixtures/subrogation.yaml`, `tests/fixtures/subrogation_intake.json`, `tests/fixtures/sample_request.json`, `tests/fixtures/sample_datareport.json`, `tests/fixtures/tier1_intake.json`. Generated-project file listing derived from `tests/agents/website/test_templates.py:176-205` (canonical assertion) + `governance_templates.py:708-785` (tier-gate branches). Includes table of all 7 shipped intake fixtures + the 2 cap-test fixtures. Reproducibility instructions via `scripts/run_pipeline.py`.

2. **Extending-the-Pipeline.md** (~222 lines) — four extension surfaces: **new agent** (envelope.py:27-28 literals + registry.py:26-32 entry + pipeline.py:41-43 runner + orchestrator wiring), **new RepoClient adapter** (protocol.py:42-78 contract + gitlab_adapter.py / github_adapter.py template + CI template sibling), **new governance artifact** (governance_templates.py:708-785 tier gates + is_governance_artifact classifier at :837-858 + positive-and-negative test per Learning #5), **new regulatory framework** (`_FRAMEWORK_ARTIFACTS` at :77-103 + `build_regulatory_mapping` at :106-121). Closes with an "Invariants enforced by tests" table citing the decoupling test, registry round-trip, artifact classifier, and tier-positive/negative tests.

3. **Changelog.md** (~172 lines) — phase-by-phase history from `git log --reverse`. Covers Phases 1–6 (schemas/envelope, data-agent core/polish, intake core/UI, website core/governance, orchestrator, production hardening), Phases A–D (GitHub/GitLab abstraction), pilot-readiness fixes (Session 17), tutorial + script (Session 18), wiki expansion (Sessions 19/20A/20B), license change. Also documents the coverage-floor progression (80% → 90% → 93% → 94%) and the schema versioning policy. Structured under `[Unreleased]` and `[0.1.0 — Pilot Ready]`.

4. **Contributing.md** (~200 lines) — 9 sections: dev env (uv workspace + extras matrix), four CI gates (ruff E/F/I/UP/B/SIM + cli.py B008 exception, mypy strict over both packages, pytest 94% floor, data-agent decoupling AST-walk), no pre-commit hooks (enforcement is CI), commit convention (conventional commits with `(phase-N)` / `(session-N)` scopes), test-writing conventions (structural guards, positive-and-negative tier fan-out, MagicMock boundary), session discipline pointers to `SESSION_RUNNER.md` / `SAFEGUARDS.md`, PR workflow, licenses (MIT project + LGPL-3.0 PyGithub compliance note), and issue-reporting pointer to pre-UAT `BACKLOG.md`.

5. **Home.md** — added links to the 4 new pages, inserted in topical order.

6. **_Sidebar.md** — added Worked Examples under "Using the Tool", Extending/Contributing/Changelog under a new "Development" section.

7. **Content-Recommendations.md** — added 4 new rows to the current-wiki table, marked recommendations #1, #3, #8, #9 as ✅ shipped with summaries of what each page covers.

8. **Published to live wiki** at `/Users/rmsharp/Development/claims-model-starter.wiki/`. Pulled first (clean, up-to-date with 20A's `8a41789`). Copied 7 files (4 new + 3 nav). Committed as `2fa274a`. Pushed to `origin/master`.

**Workflow note:** Launched 3 parallel research agents (worked-example trace, extension-points, contributing-config). All 3 completed without timeout — a direct validation of Learning #14 when scopes are kept narrow (Learning #15). Wrote the Changelog directly from `git log --reverse` without an agent. Before writing each page, spot-verified the load-bearing claims: `envelope.py` (verified Literal unions), `registry.py` (verified dict entries), `protocol.py` (verified RepoClient methods), `governance_templates.py:710-785` + `:837-858` (verified tier blocks + classifier), `subrogation_intake.json` (verified numbers), `sample_datareport.json` (verified structure), `test_templates.py:176-205` (verified generated file listing), `ci.yml` (verified 4 jobs), `pyproject.toml:58-94` (verified ruff/mypy/pytest config), `tier1_intake.json` (verified tier-1 example).

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. 3 parallel agents + 8 direct Read calls to verify load-bearing claims. All 3 agents completed successfully; all verifiable claims in the research briefs held up.
- **Implementations read, not just descriptions:** Yes. Every file:line citation in the four pages was either produced by my direct reads or spot-verified after the agent briefs. One minor trust gap: the Extending page cites `governance_templates.py:733-736` for the CI-platform dispatch from the agent's research; I verified the surrounding function (`build_governance_files` at 708-785) directly but not those specific four lines.
- **Stakeholder corrections needed:** 0.
- **What I got right:** (a) Four pages that cross-reference each other and the existing 14 pages — no dead ends in the navigation. (b) Every load-bearing claim has a file:line citation. (c) The Worked-Examples tier-3 vs. tier-1 contrast *shows* the risk-proportional governance rather than describing it in the abstract. (d) The Extending page's "Invariants enforced by tests" table names exactly the guards a contributor needs to not break. (e) The Changelog groups by phase, not by session, matching how a user would actually want to reason about upgrades. (f) The Contributing page derives everything from current config (no invented rules). (g) Published to live wiki on first attempt, clean pull before copy. (h) Marked exactly 4 content recommendations as shipped with concrete page summaries. (i) Phase 3 compliance: Phase 1B stub written before research, evaluated predecessor, self-scored, now writing full handoff.
- **What I got wrong:** (a) Did not run `scripts/run_pipeline.py --fake` to capture a live file listing — I used the test-assertion listing at `test_templates.py:176-205` instead. The test IS the spec so this is defensible, but a fresh run would have shown the user exactly what their pipeline would produce in their environment today. (b) Page lengths (205/222/172/200) are all longer than Session 19's 100-150 average — consistent with 20A's 225/370/230 range but not a terseness win. Contributing could have been ~170 lines by consolidating §§7 and 9. (c) Did not proactively check if the existing `CHANGELOG.md` at repo root should be updated to reflect Sessions 18/19/20; the wiki Changelog is audience-facing but the in-repo one hasn't been touched since Session 0. Flagged it for Session 21 consideration but didn't act. (d) Task-tool reminder fired twice mid-session despite diligently marking tasks completed — possibly because I batched 2-3 file writes between task updates. Minor.
- **Quality bar vs previous sessions:** Meets Session 20A. Four dense pages with rigorous citations, live wiki pushed on first attempt, Phase 3 close-out formal on first attempt.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #16:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 16 | When the canonical "what gets generated" spec is a test assertion (e.g., `tests/agents/website/test_templates.py:176-205`), prefer reading the test over running the pipeline to capture the file listing. The test IS the spec — any divergence would fail CI before the listing could drift. Running the pipeline with fake adapters just re-derives the same set of filenames at the cost of setup + environment risk. Cite the test file:line in the doc so future readers can verify independently. | Session 20B (Worked-Examples generated-file listing) | Any documentation that needs to enumerate outputs of a generator function — prefer the test over the run. |

### Phase 3D: Handoff to Session 21

Full "What Session 21 should do" content is in the **ACTIVE TASK** block at the top of this file. Three candidates listed, ranked by readiness and value. Any is one session.

**Key files for any of the three candidates:**

For #1 (live run):
- `scripts/run_pipeline.py` — has `--live` flag; needs `ANTHROPIC_API_KEY` + `GITLAB_PRIVATE_TOKEN` or `GITHUB_PRIVATE_TOKEN`
- `OPERATIONS.md` — operator runbook
- `src/model_project_constructor/config.py` — `OrchestratorSettings.from_env()` and `require_*` guards
- `.env.example` — required env-var template
- `docs/tutorial.md` §5 "Live host"

For #2 (resume-from-checkpoint):
- `src/model_project_constructor/orchestrator/pipeline.py` — current `run_pipeline` and `CheckpointStore`
- `src/model_project_constructor/orchestrator/checkpoints.py` — checkpoint layout
- `scripts/run_pipeline.py` — CLI entry point to extend with `--resume`
- `PipelineStatus` literal at `pipeline.py:45-50` — `FAILED_AT_*` values are the resume points
- Tests: `tests/orchestrator/test_pipeline.py` — pattern for pipeline tests

For #3 (statistical terminology glossary):
- `src/model_project_constructor/agents/intake/anthropic_client.py:33-50` — system prompt
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` — data-agent system prompt
- `initial_purpose.txt` — has prior "likelihood → probability" edits (Session 18)
- `tests/fixtures/subrogation.yaml` — has prior edits; a regression test would check the glossary terms don't appear misused in fixtures

### Gotchas for Session 21

1. **Wiki is live and fully up to date as of this handoff.** Wiki repo at `/Users/rmsharp/Development/claims-model-starter.wiki/`, last commit `2fa274a` (20B), pushed. If doing more wiki work, pull first — user is producing #6/#7/#10 in parallel.
2. **`CHANGELOG.md` at repo root is stale.** It was last touched 2026-04-10 in Session 0 and doesn't reflect any of Phases 1–6 or the wiki work. The new wiki Changelog page covers the same ground but with a different audience. Session 21 may want to either (a) refresh `CHANGELOG.md` from the wiki Changelog, (b) delete it in favor of the wiki, or (c) leave it as a "developer-only commit log" and mark it as such in its header. Not blocking — just stale.
3. **BACKLOG.md "Up Next" items #1 ("Pilot readiness audit") and #4 ("Ruff cleanup sweep") are actually complete** per Session 17's close-out. Low-priority cleanup.
4. **Duplicate "What Session 18 Did" blocks** in this file below line ~120 (carried from Session 18). Known clutter.
5. **If doing live run (candidate #1):** the fake-adapter path is solid but the live GitLab path hasn't been exercised since Phase 5. Expect some `python-gitlab` version-resolution pain; check `OPERATIONS.md` §"Credentials" first.
6. **If doing resume (candidate #2):** the existing `CheckpointStore` writes per-stage; verify it also writes pre-stage markers (so you can tell "`FAILED_AT_DATA` with DataRequest persisted" apart from "`FAILED_AT_DATA` before DataRequest was computed"). The resume strategy depends on this distinction.
7. **If doing glossary (candidate #3):** Session 18 already did a "likelihood → probability" sweep across fixtures. New glossary terms can land as system-prompt extensions without touching fixtures — but add a regression test that runs the data-agent prompt against a known-safe input and asserts the output uses "probability" not "likelihood".
8. **Fresh session 21 should re-read `SAFEGUARDS.md` and `SESSION_RUNNER.md`.** They are 183 + 306 lines; the countermeasure patterns (especially failure modes #14 ghost sessions and #18 planning-to-implementation bleed) are load-bearing.
9. **The user's preference for "probability" over "likelihood"** (when referring to `P(event)`) is a durable correction — see `Session 18` handoff. Honor it in all new LLM-adjacent prose.

### Session 20B close-out checklist

- [x] Phase 0 orientation report given, waited for user direction
- [x] Phase 1B stub written to SESSION_NOTES.md before technical work
- [x] All 4 wiki pages written with file:line citations verified against source
- [x] Content-Recommendations, Home, _Sidebar updated
- [x] Live wiki pulled, copied, committed (`2fa274a`), pushed
- [x] Phase 3A: Session 20A handoff evaluated, scored, written above
- [x] Phase 3B: Self-assessment scored and written above
- [x] Phase 3C: Learning #16 queued for SESSION_RUNNER.md
- [x] Phase 3D: Handoff to Session 21 above (ACTIVE TASK + candidates + key files + gotchas)
- [ ] Phase 3E: Commit main-repo changes (this SESSION_NOTES update + the 4 new wiki pages + 3 nav updates) — pending
- [ ] Phase 3F: Verbal report to user — pending

---

## Session 19 Handoff Evaluation (by Session 20A)
**Score: 8/10.** Session 19's handoff was thorough — the ACTIVE TASK block split Session 20 into clear 20A / 20B deliverables with 1–2 line scope definitions per page, a complete key-files list, and actionable gotchas.

- **What helped:** (a) The page-split (20A gets agent-internals, 20B gets cross-cutting) meant I didn't have to think about scope — the deliverable was three specific pages with three specific codebase surfaces. (b) Gotcha #1 (pull wiki first to avoid conflicts) saved real time; the wiki was already clean but the habit mattered. (c) Gotcha #5 (update both repos) kept me from a common failure mode. (d) Learning #14 (parallel research agents) directly informed my approach — I launched 3 agents for intake/schema/security in parallel. (e) The key-files list under "Key files for Session 20A" pointed to the exact right places (`schemas/v1/`, `envelope.py`, `registry.py`, `config.py`, adapters). Every file I needed was in the list.
- **What was missing:** (a) No warning that the security research was the broadest scope and most likely to time out in an agent — mine did ("API Error: Stream idle timeout"). Cost ~2–3 min of redirecting to direct reads. (b) No rough page-length target; the three pages I wrote are ~225/370/230 lines vs Session 19's 100–150 average. Not wrong, but a "target ~200 lines each" note would have anchored the scope earlier.
- **What was wrong:** Nothing factually wrong. Every file path held up.
- **ROI:** ~5× return. Reading the handoff (~4 min) saved ~20 min of orientation.

### What Session 20A Did
**Deliverable:** 3 wiki pages + 3 updated nav files + live wiki publish. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:**
- Main repo: (pending this session's doc commit) — SESSION_NOTES update only. The 3 new wiki pages and 3 updated nav files are still staged when this is written; the feat commit will land `docs(session-20a)`.
- Wiki repo: `8a41789` — `docs(session-20a): add intake design, schema reference, security pages`. **Pushed to `origin/master`.**

**What was done:**

1. **Intake-Interview-Design.md** (~225 lines) — 11 sections covering: the two system prompts verbatim (interviewer + governance), the eight-node LangGraph graph with diagram, the two budgets (`MAX_QUESTIONS=10` / `MAX_REVISIONS=3` in `state.py:57-58`), `plan_next_question` and `evaluate_interview` logic, the four `IntakeReport` sections and their schemas, governance classification with re-derivation on every revision, the review loop with six accept tokens (`nodes.py:35`), terminal status truth table, stakeholder tips (before/during/review), operator modes (fixture/web/programmatic), extension points, key files table.

2. **Schema-Reference.md** (~370 lines) — 13 sections covering: layout table (5 payload schemas + envelope), `StrictBase` contract (`extra="forbid"`, `protected_namespaces=()`), shared Literal types (`CycleTime` / `RiskTier` / `ModelType`), `IntakeReport` with all nested types (`ModelSolution`, `EstimatedValue`, `GovernanceMetadata`), Data Agent schemas (`DataRequest`, `DataReport`, `DataGranularity`, `PrimaryQuery`, `QualityCheck`, `Datasheet`), repo schemas (`RepoTarget`, `GovernanceManifest`, `RepoProjectResult`), `HandoffEnvelope` with the invariant-test explanation, `schemas/registry.py` + `load_payload`, checkpoint storage layout, versioning strategy, hand-construction checklist, round-trip guarantees, key files.

3. **Security-Considerations.md** (~230 lines) — 12 sections covering: `OrchestratorSettings.from_env()` + `require_*` guards, the complete env-var matrix with required/default/purpose, outbound network boundaries (Anthropic, GitLab, GitHub, optional DB), what the LLM sees (stakeholder answers verbatim for intake; no query result rows for data), DB read-only contract enforced at credential-layer not in-process, SQL parse-level validation caveat, checkpoint sensitivity (interview prose + SQL yes; tokens no), logging (no credential exposure, context dict bound to `run_id`/`correlation_id`), CI (no secrets in workflow), generated-project secrets (templates emit `.env.example` with placeholders), dependency trust surface, 8 known-gaps items, 9-item review checklist, key files.

4. **Home.md** — added three new links (Intake Interview Design, Schema Reference, Security Considerations) to Wiki contents.

5. **_Sidebar.md** — added Intake Interview Design under "Using the Tool"; Security Considerations under "Operations"; Schema Reference under "Reference".

6. **Content-Recommendations.md** — added three new rows to the current-wiki table; marked recommendations #2, #4, #5 as ✅ shipped with summaries of what the pages cover.

7. **Published to live wiki** at `/Users/rmsharp/Development/claims-model-starter.wiki/`. Pulled first (clean). Copied 6 files. Committed as `8a41789`. Pushed to `origin/master`. Live at `https://github.com/rmsharp/claims-model-starter/wiki`.

**Workflow note:** Launched 3 parallel research agents (intake internals, schema surfaces, security surfaces). Agents #1 and #2 completed with thorough reports; agent #3 (security) timed out with `Stream idle timeout - partial response received`. I pivoted to direct reads via `Glob` + `Read` + `Grep` for the security research — `config.py`, `.env.example`, `OPERATIONS.md`, `logging.py`, `metrics.py`, both adapters, `db.py`, `sql_validation.py`, `anthropic_client.py` (both), `cli.py` (data), `ui/intake/app.py` (startup), `ci.yml`, `.gitignore`, `pyproject.toml`. Also spot-checked agent claims post-write (nodes.py:35 for accept tokens, envelope.py for the Literal unions) per Learning #11.

**Self-assessment score: 9/10**

- **Research before creative work:** Yes. 3 parallel agents + direct reads for the timed-out agent. Verified verbatim-quoted prompts against `anthropic_client.py:33-50`.
- **Implementations read, not just descriptions:** Yes for every load-bearing claim. After writing, spot-checked `nodes.py:35` (accept tokens) and `envelope.py` (Literal values) directly — both held up. Cited file:line for every factual claim.
- **Stakeholder corrections needed:** 0.
- **What I got right:** (a) Three pages are self-contained, cross-reference each other and existing pages. (b) Every claim has a file:line citation. (c) Handled the agent timeout gracefully — didn't re-launch, didn't guess; did direct reads with the remaining time budget. (d) Pulled wiki before copy, avoiding the conflict gotcha. (e) Updated both repos as instructed. (f) Phase 3 compliance: self-scored, evaluated predecessor, wrote stub before work (Phase 1B), now writing full handoff.
- **What I got wrong:** (a) Relied on agent report for a few citations (nodes.py:78-82 for `evaluate_interview`, nodes.py:94-106 for `await_review`) without direct re-reads before final write — partial Learning #11 regression. Spot-checked the two most load-bearing claims post-write, but not all. (b) Page lengths are larger than Session 19's average; could have trimmed Schema-Reference by consolidating the Literal-enum summary table. Not a correctness issue but a terseness gap. (c) One task-tool reminder showed my tasks were drifting stale mid-session — I updated status but only when pushed. Should mark tasks completed immediately after each finish.
- **Quality bar vs previous sessions:** Meets or slightly exceeds Session 19. Three dense pages, rigorous citations, live wiki published on first attempt, Phase 3 close-out formal.

### Phase 3C: Learnings

Adding to the `Learnings` table in SESSION_RUNNER.md as #15:

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 15 | When a parallel research agent times out, do NOT re-launch — the failure mode is usually scope breadth (too many angles per agent) and a re-launch burns the same budget. Instead, pivot to direct reads with targeted `Grep` + `Read` for just the citations you need, then write. A timed-out agent costs ~3 min; a re-launched timed-out agent costs ~6 min. This is a special case of the "trust but verify" principle — the first agent already did enough research for you to know what to read. | Session 20A (security research agent timed out) | Any session using parallel research agents when one times out. |

---

*Session history accumulates below this line. Newest session at the top.*

### Session 18 Handoff Evaluation (by Session 19)
**Score: 8/10.** Session 18's handoff was solid — the ACTIVE TASK described the state well, the key files list was useful, and the gotchas were accurate.

- **What helped:** (a) The key files list pointed to `scripts/run_pipeline.py` and `docs/tutorial.md`, which I referenced to understand the user-facing flow when writing the Getting Started and Pipeline Overview wiki pages. (b) Gotcha #1 (fixture data for intake/data stages) was useful context when documenting the Data Agent's standalone capability. (c) The self-assessment's "corrections needed: 4" set my expectation that the codebase was stable but the documentation had been actively refined — good signal that documentation quality matters to this user. (d) The backlog items from user feedback (data discovery, glossary) directly informed the Glossary and Content Recommendations pages.
- **What was missing:** (a) The handoff has two "What Session 18 Did" blocks (lines 38-54 and lines 64-73 in SESSION_NOTES.md) with slightly different content — the first is the polished version, the second appears to be the mid-session draft that wasn't cleaned up. Didn't cost time, but clutters the notes. (b) No mention of the governance template file (`governance_templates.py`) which I needed to read for accurate governance artifact documentation. Cost ~2 min of discovery.
- **What was wrong:** Nothing factually wrong. All file paths and claims verified.
- **ROI:** ~3x return. Reading the handoff (~5 min) saved ~15 min of orientation.

### What Session 19 Did
**Deliverable:** Wiki documentation for claims-model-starter — 14 markdown pages (1,512 lines) covering the full pipeline, generated project structure, governance framework, SBOM, architecture decisions, glossary, and content recommendations. **COMPLETE.**
**Started:** 2026-04-16
**Completed:** 2026-04-16

**What was done:**
1. Created `docs/wiki/claims-model-starter/` with 14 wiki pages ready for GitHub wiki publication.
2. **Home.md** — Landing page with pipeline summary and navigation links.
3. **Getting-Started.md** — Install, first dry run, live run instructions.
4. **Pipeline-Overview.md** — 3-agent architecture, handoff protocol, orchestrator, error handling.
5. **Generated-Project-Structure.md** — Full directory layout with file counts by risk tier, component descriptions.
6. **Governance-Framework.md** — Risk tiers, monitoring cadence, full artifact inventory by tier gate, regulatory framework mapping.
7. **Development-Workflow.md** — How the data science team implements stubs, fills narratives, runs tests.
8. **Data-Guide.md** — Queries, datasheets, data loading, Data Agent standalone usage.
9. **Agent-Reference.md** — Detailed specs for all 3 agents: input/output schemas, behavior, interfaces, failure modes.
10. **Monitoring-and-Operations.md** — Env vars, checkpoints, observability, CI, troubleshooting.
11. **Software-Bill-of-Materials.md** — Two-part SBOM: constructor (15 direct + key transitive deps) and generated project (6 deps). Locked version snapshot of 87 packages.
12. **Architecture-Decisions.md** — 10 architecture decisions with rationale (AD-1 through AD-10).
13. **Glossary.md** — 40+ terms across domain (P&C claims), pipeline, governance, regulatory, statistical, and technology categories.
14. **Content-Recommendations.md** — 10 prioritized additions grouped by high/medium/low priority, plus SBOM enhancement recommendations and wiki maintenance guidance.
15. **_Sidebar.md** — GitHub wiki sidebar navigation structure.

**Commits:**
- `0acdd37` — 14 wiki pages + session notes + learning #14
- `f2f2a70` — License change: Proprietary -> MIT (`LICENSE` file, both `pyproject.toml`, SBOM page)
- `06ef12f` — Close-out with 20A/20B handoff plan

**Additional work (same session, after initial wiki creation):**
16. Changed license from Proprietary to MIT per user direction. `LICENSE` file at project root, both `pyproject.toml` files, SBOM wiki page.
17. Published all 14 wiki pages to GitHub wiki repo at `/Users/rmsharp/Development/claims-model-starter.wiki/`. Wiki is live at `https://github.com/rmsharp/claims-model-starter/wiki`.
18. Planned 7 additional wiki pages across 2 follow-up sessions (20A and 20B), approved by user. User is separately producing pages #6 (FAQ), #7 (Comparison), #10 (Deployment guide).

**Self-assessment score: 8/10**

Compared to the standard set by previous sessions:
- **Research before creative work:** Yes. Launched 3 parallel research agents before writing any wiki page. Read `templates.py:148-178`, `governance_templates.py:1-80`, both `pyproject.toml` files, `ci.yml`, `OPERATIONS.md`, `initial_purpose.txt`, `tutorial.md:1-50` directly. No page was written from memory of agent summaries alone.
- **Implementations read, not just descriptions:** Yes. Verified generated project structure against the actual f-string templates in `templates.py` and `governance_templates.py`, not against the architecture plan's descriptions.
- **Stakeholder corrections needed:** 1 — user corrected my close-out procedure (insufficient Phase 3 compliance). No corrections to the wiki content itself.
- **What I got right:** (a) Comprehensive coverage — 14 pages spanning all audiences (stakeholders, data science teams, developers, operators, security, compliance). (b) SBOM is two-part (constructor + generated project) with locked versions. (c) Content Recommendations gives the next session a clear priority queue. (d) Parallel research agents made orientation fast.
- **What I got wrong:** (a) First close-out attempt was not a formal Phase 3 — missing self-assessment score, structured comparison, and proper 3F verbal report. User had to correct me. This is failure mode #6 (skip close-out) and #17 (protocol erosion). (b) Could have included license info in the SBOM during the initial write — instead left it as a recommendation, then the user asked for the license change anyway. (c) Initially asked the user to confirm push when they had already said yes.
- **Quality bar vs previous sessions:** Meets the bar for documentation deliverables. The 14-page wiki is the largest documentation deliverable in the project's history. Below the bar on close-out discipline — Session 18 and Session 17 both closed out correctly on first attempt.
- `BACKLOG.md` — 6 open items including: data discovery (intake + data agents), statistical terminology glossary, render script, tutorial UX, SQLite warnings.
- `OPERATIONS.md` — production runbook (complements the tutorial).
- `.env.example` — env var template for live runs.

### Gotchas for Session 19

1. **The script uses fixture data for intake/data stages**, even in `--live` mode. A true LLM-backed end-to-end run would need real `IntakeAgent` + `DataAgent` runners wired in — the script is structured to make this swap straightforward (replace the `lambda` runners in `main()`).
2. **`--live` mode constructs `PythonGitLabAdapter` / `PyGithubAdapter` directly** — verify the constructor signatures haven't changed if adapters were modified since Session 14.
3. **`.orchestrator/`, `my_intake.yaml`, `my_intake_report.json` are gitignored** — tutorial-generated artifacts won't be committed.
4. **CI is still green but only tested on master push**, not on a PR (same as Session 17's gotcha #1).
5. **Pandoc rendering needs `-V header-includes` CSS** to avoid hr/code-block overlap. The backlog item for `scripts/render_tutorial.sh` captures this.
6. **~20 ResourceWarning from unclosed SQLite connections** in data agent tests (Python 3.13 strictness). Not a correctness issue. Backlog item exists.
7. **User prefers "probability" not "likelihood"** when referring to P(event). All fixture occurrences fixed in this session. Backlog item for a statistical terminology glossary to enforce this in LLM-generated content.

---

*Session history accumulates below this line. Newest session at the top.*

### Session 17 Handoff Evaluation (by Session 18)
**Score: 9/10.** Session 17's handoff was thorough and actionable — the ACTIVE TASK was clear about being user-directed, the gotchas were accurate, and the key files pointed to exactly what I needed.

- **What helped:** (a) The key files list included `OPERATIONS.md` and `.env.example`, which were essential references when writing the script and tutorial. (b) Gotcha #4 (coverage at 97.24%) let me skip pre-flight coverage checks. (c) The "Up Next" candidates in the ACTIVE TASK gave clear context for what the user might ask for. (d) Session 17's self-assessment confirmed zero stakeholder corrections — set expectations that the codebase was stable.
- **What was missing:** No mention of the `MetricsSnapshot` field names (`run_count` / `agent_latency`, not `total_runs` / `agent_latencies`). Cost ~2 min of debugging. Minor since I should have read the source directly rather than guessing field names.
- **What was wrong:** Nothing factually wrong. Every file path and claim held up.
- **ROI:** ~4x return. Reading the handoff (~4 min) saved ~15 min of orientation and discovery.

### What Session 18 Did
**Deliverable:** End-to-end pipeline run script + tutorial, user-tested from a fresh clone with iterative fixes.
**Started:** 2026-04-16
**Completed:** 2026-04-16
**Commits:** `4dc2f5d` script+tutorial, `883935a` fix missing --extra ui, `1613d60` tutorial restructure + likelihood→probability, `1f9c28a` backlog: data discovery items, `9f3399c` backlog: render script item.

**What was done:**
1. Created `scripts/run_pipeline.py` — 265-line script driving the full pipeline with fixture data + FakeRepoClient, with `--live` flag for real hosts. Tested both `--host gitlab` and `--host github`.
2. Created `docs/tutorial.md` — 6-step tutorial restructured during user testing: (1) create intake YAML fixture (full content inline), (2) generate IntakeReport JSON via CLI, (3) run pipeline, (4) inspect checkpoints, (5) live host, (6) programmatic API.
3. Fixed `--extra ui` missing from install command (caught by user testing from fresh clone).
4. Fixed likelihood→probability in 5 files (fixtures, tests, initial_purpose.txt) per user's statistical terminology correction.
5. Added `.orchestrator/`, `my_intake.yaml`, `my_intake_report.json` to `.gitignore`.
6. Added 6 backlog items from user feedback: data discovery (intake + data agents), statistical terminology glossary, render script, tutorial UX, SQLite warnings.

**Self-assessment:**
- **What went well:** (a) User-tested the tutorial from a fresh clone and caught real issues (missing ui extra, unpushed commits, copy-paste UX). (b) The iterative fix cycle was fast — each issue was a 1-commit fix. (c) The tutorial restructuring (adding YAML fixture inline + JSON generation step) was a significant UX improvement driven by user feedback. (d) The likelihood→probability fix was thorough — grepped the entire repo, found all 5 occurrences.
- **What could be better:** (a) Should have pushed commits immediately after the initial commit — the user's fresh clone didn't have the script. (b) Initial script had 2 wrong field names (`target_name`, `total_runs`) from relying on agent research instead of reading source. (c) The tutorial originally started at "load pre-built JSON" which skipped the most important user-facing step (creating the intake fixture).
- **Corrections needed:** 4 from user testing (missing ui extra, unpushed commits, likelihood→probability, tutorial needs YAML generation step). All addressed.

### Session 16 Handoff Evaluation (by Session 17)
**Score: 9/10.** Session 16's handoff was thorough and actionable — the ACTIVE TASK block described the state precisely, the gotchas were accurate, and the key files list was complete.

- **What helped:** (a) Gotcha #1 accurately predicted the ruff error scope (62 errors, 43 auto-fixable) and gave the exact fix command. Saved ~5 min of discovery. (b) Gotcha #2 correctly predicted CI would fail on first push and identified the likely culprit (`uv` availability). The actual failures were different (missing `--extra ui` in typecheck, coverage floor on decoupling, ANSI codes in CLI test) but the warning to expect CI failure on first push was valuable. (c) The baseline numbers (422 tests, 97.18% coverage, mypy 48 files) matched exactly on first run. (d) The "observability is opt-in" note (gotcha #5) was directly useful during audit — I verified `pipeline.py` has zero imports from `logging.py` or `metrics.py` without needing to investigate.
- **What was missing:** The gotchas didn't predict the mypy typecheck CI failure (missing `--extra ui` in the typecheck job's `uv sync`). The handoff said "verify" the `ui` extra in the test job, but the typecheck job was the one that needed it. Also didn't predict the ANSI code issue with `CliRunner` on Linux. These are edge cases the handoff couldn't reasonably predict. -1 for minor imprecision in gotcha #2.
- **What was wrong:** Nothing factually wrong. Every file path, line number, and baseline claim held up.
- **ROI:** ~5× return. Reading the handoff (~5 min) saved ~25 min of audit setup and ruff discovery.

### What Session 17 Did
**Deliverable:** Pilot readiness audit + CI fix. Reviewed all 46 acceptance criteria from `architecture-plan.md` §14 against the actual codebase. Found 2 issues: 62 ruff lint errors blocking CI, and `tests/e2e/` path deviation. Fixed all ruff errors (56 auto + 6 manual), fixed 3 CI workflow issues (mypy deps, decoupling coverage, CLI ANSI codes), pushed, confirmed CI green. Updated `BACKLOG.md` to reflect all completed phases. Wrote comprehensive audit report to `docs/planning/pilot-readiness-audit.md`. **PILOT-READY declared.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `66b44c8` docs(backlog): mark all 6 phases complete. `17f661d` fix(lint): resolve all 62 ruff errors. `d62efc2` fix(ci): mypy deps, decoupling coverage, CLI color. `b8d8d7e` fix(ci): click.unstyle for ANSI codes.

**Self-assessment:**
- **What went well:** (a) Thorough audit — verified every §14 criterion with actual commands, file reads, and test runs, not from memory. Used 5 parallel sub-agents for deep file-level inspection per phase. (b) Fixed all CI issues in 2 iterations (ruff + 3 CI bugs). (c) Clean separation of audit report (read-only findings) from fixes (commits). (d) Zero stakeholder corrections needed.
- **What could be better:** (a) The first CI fix attempt (`NO_COLOR` env var for CliRunner) didn't work because click's `CliRunner(env=...)` replaces the full environment. Required a second push with `click.unstyle()`. Should have tested more carefully before pushing. (b) The initial ruff auto-fix replaced `{{` f-string escapes with `{_MODEL_SOL}` variables but forgot to adjust the brace escaping in the constants — caused 3 test failures that required a second edit. More careful about f-string mechanics next time.
- **Quality bar:** Matches previous sessions. The audit is the most comprehensive single-session deliverable to date — 46 criteria verified with evidence.

### Session 15 Handoff Evaluation (by Session 16)
**Score: 9/10.** Session 15's handoff was extremely thorough — the ACTIVE TASK block was a near-complete Phase 6 spec with file-by-file instructions, hard rules, and expected duration. This is the fifth consecutive high-quality handoff.

- **What helped:** (a) The "cleanest integration point is wrapping the three runners" guidance in ACTIVE TASK told me immediately that `pipeline.py` should NOT import observability modules — I wrote the `make_logged_runner` / `make_measured_runner` wrappers as external composition without hesitation. (b) The explicit "no structlog required" signal ("likely `structlog`" with alternatives acknowledged) let me make the simpler choice of stdlib logging without second-guessing. (c) The "coverage floor bump is a separate commit, Session 12 precedent" instruction replicated exactly — `c3943a8` mirrors the `e91c9f2` pattern. (d) The Phase 5 checkpoint layout documentation (envelope vs terminal-result channels) was directly reusable for `TROUBLESHOOTING.md` and `OPERATIONS.md` — I didn't need to reverse-engineer the file layout. (e) Pre-flight numbers (368 @ 96.97%, mypy 17 files) matched exactly on first run.
- **What was missing:** The ACTIVE TASK mentioned "likely `structlog`" and "possibly `pydantic-settings`" as deps, but Session 15's handoff didn't flag the tradeoff of adding new deps vs. using stdlib-only solutions. I chose stdlib logging + a plain dataclass config to avoid dependency bloat — this was the right call but would have been faster with an explicit "prefer zero new deps" note. Minor deduction: -1.
- **What was wrong:** Nothing. Every file path, line number, and invariant claim held up on inspection.
- **ROI:** ~6× return. Reading the handoff (~4 min) saved ~25 min of Phase 6 discovery, primarily the callable-runner wrapping strategy and the doc structure.

### What Session 16 Did
**Deliverable:** Phase 6 of `docs/planning/architecture-plan.md` §14 — production hardening. Added structured logging (`make_logged_runner` with `agent.start` / `agent.end` / `agent.error` events carrying `run_id` + `correlation_id`), in-memory metrics (`MetricsRegistry` with run counts, status distribution, per-agent latency + `make_measured_runner` wrapper), env-var config (`OrchestratorSettings.from_env()` with validation and `require_*` guards), `.env.example` template, `OPERATIONS.md` runbook, `TROUBLESHOOTING.md` diagnostic walkthroughs for each `FAILED_AT_*` path, `.github/workflows/ci.yml` (lint + test + typecheck + decoupling), and README sweep. 54 new tests across 3 new test files. **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `c3943a8` chore(coverage): raise pytest coverage floor 93% → 94%. Phase 6 feat commit hash TBD (to be filled by Session 17).

**Self-assessment:**
- **What went well:** (a) Zero-dep design: used stdlib logging + plain dataclass config instead of structlog + pydantic-settings. No new dependencies added. (b) Clean separation: `pipeline.py` has zero imports from the new modules — observability is purely opt-in via runner composition. (c) The integration test (`test_instrumented_happy_path`) proves the composition works end-to-end with a real `WebsiteAgent` + `FakeRepoClient`. (d) All Phase 6 files are ruff-clean (auto-fixes applied to Phase 5's `pipeline.py` for modern imports; zero behavioral change). (e) Comprehensive docs: `OPERATIONS.md` covers env vars + checkpoint layout + resume procedure + observability integration; `TROUBLESHOOTING.md` covers every `FAILED_AT_*` path with code snippets an operator can paste.
- **What could be better:** (a) The CI workflow has not been tested on a real push. Local verification passed, but the `astral-sh/setup-uv@v4` action hasn't been exercised live. (b) The 62 pre-existing ruff errors in `ui/intake/` and other files remain untouched — they're outside Phase 6 scope but should be cleaned up in a future session.
- **Corrections needed:** Zero stakeholder corrections.
- **Quality bar:** Matches or exceeds previous sessions. The observability layer is clean and well-tested, the docs are actionable, and the CI workflow mirrors exactly what the plan specified.

### Session 14 Handoff Evaluation (by Session 15)
**Score: 10/10.** Fourth consecutive 10. Phase 5 was a pure step-execution session because Session 14 left no ambiguity about the orchestrator's contract.

- **What helped:** (a) The "`WebsiteAgent(client, ci_platform=...)` is the canonical construction" line in ACTIVE TASK told me the website runner closure could just be `agent.run` without any ceremony — I wrote `website_runner=agent.run` in every test on first attempt. (b) The Phase D amendment paragraph in `architecture-plan.md` §14 Phase 5 (added by Session 14) told me upfront that `RepoTarget` / `RepoProjectResult` were the correct imports — I never reached for `GitLabTarget`. (c) The gotchas section explicitly flagged that `WebsiteAgent.run(intake, data, repo_target)` returns a `RepoProjectResult` with `status ∈ {"COMPLETE","FAILED","PARTIAL"}` — I branched on this in `pipeline.py` without inspecting the agent source. (d) Gotcha #6 in Session 14's handoff ("`HandoffEnvelope` + `schemas/registry.py` are the persistence layer for inter-agent handoffs") told me to persist inter-agent handoffs as envelopes but didn't prescribe how to handle the terminal result, which let me notice the Phase 1 invariant on my own (target_agent excludes "orchestrator") before shipping a broken widening. (e) Pre-flight baseline numbers (323 @ 96.77%, mypy 13 files clean) matched exactly — zero drift detected in ~10 seconds.
- **What was missing:** One genuine gap: Session 14's handoff anticipated that Phase 5's orchestrator would need `RepoTarget.host_url` populated and noted "the orchestrator config is the canonical place to resolve '--host github' + no --host-url → set RepoTarget.host_url='https://api.github.com'". However it did NOT flag the Phase 1 envelope invariant (`test_target_agent_cannot_be_orchestrator` in `tests/schemas/test_envelope_and_registry.py:63-66`) — I discovered this the hard way by widening `HandoffEnvelope.target_agent` to include "orchestrator" and watching the schema test fail. The right fix (introducing a sibling `save_result()` method on `CheckpointStore` that bypasses envelopes for terminal artifacts) was cleaner than my first instinct, so the gap cost me ~3 minutes but improved the design. **Not deducting — this is a Phase 1 invariant, not Session 14's responsibility to document.**
- **What was wrong:** Nothing observable. Every gotcha held up on inspection. The "`PyGithubAdapter` + `PythonGitLabAdapter` both expose the same `RepoClient` Protocol surface" claim was load-bearing — I could write a single test for both hosts without branching.
- **ROI:** Reading the handoff (~6 min) saved an estimated 40–50 min of Phase 5 discovery: the callable-runner shape (implied by the "three agents with incompatible `.run()` signatures" problem), the fixture-based end-to-end approach (implied by "end-to-end tests must use `FakeRepoClient` by default"), and the Phase 1 envelope invariant I had to discover on my own was the only friction. ~7× ROI, matching the Phase D session.

**Commit hash backfill for Session 14 (per ACTIVE TASK's Phase 3A directive):**
- `e9f0d10` feat(phase-d): website CLI `--host gitlab|github` + dual-adapter selection
- `9f20e95` docs(readme): mention GitHub alongside GitLab in tagline + diagram

Both hashes verified via `git log --oneline -10` at Phase 0 start. The Session 14 handoff's "Commits: TBD" placeholder is updated below.

### What Session 15 Did
**Deliverable:** Phase 5 of `docs/planning/architecture-plan.md` §14 — new `src/model_project_constructor/orchestrator/` package with `pipeline.py` (sequential `run_pipeline` driver per §12), `adapters.py` (the sole `IntakeReport`↔`DataRequest` bridge), and `checkpoints.py` (`CheckpointStore` with envelope save/load + `save_result` for terminal artifacts). 45 new tests across `tests/orchestrator/` covering: happy path for both `ci_platform="gitlab"` and `ci_platform="github"` with `.gitlab-ci.yml` / `.github/workflows/ci.yml` positive + negative assertions; halt behavior for each `FAILED_AT_*` path; downstream-agent-not-called guards on halt; adapter inference rules for all `model_type` variants; envelope round-trip with registry resolution; terminal-result filename-namespace isolation; run-directory isolation. README phase-table row 5 → "Complete", repo-layout block updated with `orchestrator/` + `tests/orchestrator/` entries, total test count bumped 323 → 368. **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `b94cb47` feat(phase-5): orchestrator package with run_pipeline + checkpoints + adapters. (Backfilled by Session 16.)

**Pre-flight baseline (verified on disk):**
- `uv run pytest -q` → **323 passed, 96.77% coverage**. Matches Session 14 exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 13 source files**. Matches.
- `git status` → clean on `master`, 0 commits ahead of `origin/master`.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-280 (ACTIVE TASK + Session 14 handoff + gotchas + Session 13 handoff for context), ran `git status` / `git log --oneline -5` / pre-flight pytest + mypy in parallel, confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "work on Phase 5" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step even though ACTIVE TASK already described the deliverable.**

2. **User said "work on Phase 5; do not forget Housekeeping note toward end of this session"** — wrote Session 15 IN_PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14). The housekeeping note refers to backfilling Session 14's `Commits: TBD` placeholder to `e9f0d10` + `9f20e95` during Phase 3A; I tracked this as close-out task #6 explicitly.

3. **Phase 5 step 1 — §12 + §14 Phase 5 re-read + agent signature inventory:**
   - Read `architecture-plan.md` §12 (`run_pipeline` pseudocode showing `_persist` hooks after each agent + `if status != "COMPLETE": return PipelineResult(status="FAILED_AT_*")` halt logic), §14 Phase 5 (including the Session 14 amendment paragraph widening "test GitLab instance" to "test host (GitLab or GitHub)"), §7 (decoupling invariant — the adapter is the ONLY allowed `IntakeReport ↔ DataRequest` site).
   - Read `src/model_project_constructor/schemas/envelope.py` + `schemas/registry.py` — noted `HandoffEnvelope.target_agent` is `Literal["intake", "data", "website"]` (excludes "orchestrator"), `source_agent` includes "orchestrator". Noted registry has 5 entries: `IntakeReport`, `DataRequest`, `DataReport`, `RepoTarget`, `RepoProjectResult`.
   - Read `schemas/v1/intake.py` + `schemas/v1/repo.py` + `packages/data-agent/.../schemas.py` for field-level contracts.
   - Read `agents/intake/agent.py` (`IntakeAgent.run_with_fixture(path)` and `run_scripted(...)`), `packages/data-agent/.../agent.py` (`DataAgent.run(DataRequest)`), `agents/website/agent.py` (`WebsiteAgent.run(intake, data, repo_target)`). **Noted the three `.run()` signatures are incompatible** — this is what drove the decision to use callable runners instead of concrete agent classes in `run_pipeline`.
   - Read `agents/website/cli.py` end-to-end (the lazy-import pattern, the `cast(Literal[...], ci_platform)` pattern for passing `str`-after-parsing into `WebsiteAgent`, the `resolved_host_url` per-host default).
   - Read `agents/website/fake_client.py` (`FakeRepoClient` with `projects` dict + `get_files` test helper).
   - Read the existing fixtures `tests/fixtures/subrogation_intake.json` + `tests/fixtures/sample_datareport.json` — these are the pre-baked `IntakeReport` + `DataReport` I'd use to stub intake/data runners in the end-to-end test.

4. **Phase 5 step 2 — `orchestrator/` package (4 new source files):**
   - `__init__.py` (48 LOC) — re-exports the public surface: `run_pipeline`, `PipelineConfig`, `PipelineResult`, `CheckpointStore`, `intake_report_to_data_request`, `infer_target_granularity`, and the three `IntakeRunner` / `DataRunner` / `WebsiteRunner` callable type aliases. Module docstring describes the sequential-script pattern + the §7 decoupling responsibility.
   - `adapters.py` (82 LOC) — `infer_target_granularity(intake) -> DataGranularity` maps `model_solution.model_type` ("time_series" → monthly grain; everything else → event grain, unit="claim"). `intake_report_to_data_request(intake, run_id) -> DataRequest` copies `target_description` verbatim from `model_solution.target_definition`, copies `candidate_features` into `required_features`, synthesizes `population_filter` from the target definition, defaults `time_range` to `"last 5 calendar years of historical records"`, sets `database_hint=None`, `data_quality_concerns=[]`, `source="pipeline"`, `source_ref=run_id`. The adapter is deliberately conservative — downstream `DataAgent` diagnoses ambiguous requests via `status=INCOMPLETE_REQUEST` so the adapter doesn't try to be clever.
   - `checkpoints.py` (104 LOC) — `CheckpointStore(base_dir)` with two artifact channels:
     - **Envelope channel** (for inter-agent handoffs): `save(envelope)`, `load(run_id, payload_type)`, `load_payload(run_id, payload_type)` (resolves via `schemas/registry.py`), `has(run_id, payload_type)`, `list_payload_types(run_id)`. Files named `<payload_type>.json` under `<base_dir>/<run_id>/`.
     - **Terminal result channel** (for the orchestrator's own outputs, most importantly `RepoProjectResult`): `save_result(run_id, name, model)`, `has_result(run_id, name)`, `list_result_names(run_id)`. Files named `<name>.result.json` so they never collide with envelope filenames even if a terminal name happens to match a registered payload type. The docstring explicitly references the Phase 1 invariant (`test_target_agent_cannot_be_orchestrator`) as the reason the terminal channel exists — envelopes are strictly for agent-to-agent transport.
   - `pipeline.py` (205 LOC) — `PipelineConfig` dataclass (`run_id`, `repo_target`, `checkpoint_dir`, `correlation_id` defaulting to `run_id` via `__post_init__`), `PipelineResult` dataclass (`run_id`, `status`, and optional `intake_report` / `data_request` / `data_report` / `project_result` / `failure_reason`; a `project_url` property extracts from `project_result`), `PipelineStatus = Literal["COMPLETE","FAILED_AT_INTAKE","FAILED_AT_DATA","FAILED_AT_WEBSITE"]`. `run_pipeline(config, *, intake_runner, data_runner, website_runner, store=None)` is the single public entry point. Sequence: call `intake_runner()` → save `IntakeReport` envelope → halt if `status != "COMPLETE"` → call `intake_report_to_data_request` → save `DataRequest` envelope → call `data_runner(request)` → save `DataReport` envelope → halt if `status != "COMPLETE"` → save `RepoTarget` envelope → call `website_runner(intake, data, target)` → save terminal `RepoProjectResult` via `save_result` → halt if `status != "COMPLETE"` → return `PipelineResult(status="COMPLETE", ...)`. The halt-paths retain every report produced so far so the operator can inspect partial state. A private `_envelope(...)` helper builds `HandoffEnvelope` instances with `source_agent="orchestrator"` for the intake/data/website-target envelopes.

5. **Phase 5 step 3 — mypy probe on the new package (before writing tests):**
   - `uv run mypy src/model_project_constructor/orchestrator/` → **Success: no issues found in 4 source files**. Zero `# type: ignore` comments. The only narrowing issue was the `dict` → `dict[str, Any]` parameter on `_envelope` which I caught on first mypy run.

6. **Phase 5 step 4 — Envelope widening attempt + rollback (design correction):**
   - Initial draft of `pipeline.py` persisted the terminal `RepoProjectResult` as an envelope with `target_agent="orchestrator"` (since the website agent sends it back to the orchestrator). Widened `HandoffEnvelope.target_agent` to include `"orchestrator"`.
   - Ran `uv run pytest tests/schemas/ -q` → **1 failed: `test_target_agent_cannot_be_orchestrator`**. The Phase 1 test explicitly codifies "the orchestrator never *receives* an envelope — it only sends them" as a design invariant.
   - **Reverted the envelope widening** and added the `save_result` / `has_result` / `list_result_names` sibling API on `CheckpointStore`. The terminal `RepoProjectResult` is a plain JSON Pydantic dump, not an envelope — which matches the Phase 1 intent exactly. Ran schema tests again → **88 passed** (was 87 passing + 1 failing before my change; now 88/88). The terminal-result channel is cleaner than the envelope widening would have been and is documented in the `CheckpointStore` class docstring.

7. **Phase 5 step 5 — `tests/orchestrator/` (4 new test files):**
   - `__init__.py` — empty marker.
   - `test_adapters.py` (163 LOC, 11 tests) — helper `_make_intake(...)` builds a minimal `IntakeReport` with override kwargs for `model_type` / `candidate_features` / `target_definition` / `status`. **`TestInferTargetGranularity`** (4 tests): `supervised_classification` / `supervised_regression` / `unsupervised_clustering` all map to event grain; `time_series` maps to monthly. **`TestIntakeReportToDataRequest`** (7 tests + 1 parametrized over status): features copied verbatim + defensive-copy regression (mutating `request.required_features` does NOT affect `intake.model_solution.candidate_features`); `target_description` + `population_filter` pull from `target_definition`; `source="pipeline"` + `source_ref=run_id`; `time_range` is non-empty and mentions "year"; `database_hint is None`; `data_quality_concerns == []`; round-trip (`model_dump` → `model_validate` → equality); `time_series` end-to-end; the parametrize covers `["COMPLETE", "DRAFT_INCOMPLETE"]` because §12 halts DRAFT_INCOMPLETE before the adapter runs, but the adapter must still produce a valid `DataRequest` for direct-use callers.
   - `test_checkpoints.py` (220 LOC, 15 tests) — helper `_make_data_request_envelope(run_id)` + `_make_repo_project_result()`. **`TestEnvelopeRoundTrip`** (7 tests): save/load round-trip, run directory creation, `has` before/after save, `load_payload` resolves via registry and returns a `DataRequest` instance, `load` on missing file raises `FileNotFoundError`, overwrite-on-resave (re-saving with a different `correlation_id` overwrites rather than suffixes). **`TestListing`** (4 tests): `list_payload_types` returns `[]` for missing run, sorted after two saves, excludes terminal `.result.json` files, `list_result_names` also `[]` for missing run. **`TestTerminalResults`** (4 tests): `save_result` writes the `.result.json` suffix, creates the run directory, `has_result` reports existence, envelope + terminal result with the same logical name coexist in different files. **`TestRunIsolation`** (3 tests): two run IDs do not share files, `base_dir` accepts both `str` and `Path`, a `RepoTarget` envelope round-trips through `load_payload` and resolves to the correct Pydantic class.
   - `test_pipeline.py` (352 LOC, 13 tests + 2 parametrized cases = 14 test functions, 15 actual runs counting parametrize) — helpers `_load_intake` / `_load_data` (from the existing fixtures), `_make_config`, `_failed_repo_project_result`, `_incomplete_data_report`, `_draft_incomplete_intake`. **`TestHappyPath`** (4 tests): `test_run_pipeline_happy_path_emits_correct_ci_file[gitlab|github]` (parametrized, positive + negative CI-file assertions matching Learning #5); `test_happy_path_persists_all_checkpoints` (asserts IntakeReport / DataRequest / DataReport / RepoTarget envelopes + terminal RepoProjectResult + `list_payload_types` sorted exactly); `test_happy_path_data_request_copies_candidate_features` (round-trips through `load_payload` to verify the DataRequest is both correct and Pydantic-valid after disk round-trip); `test_happy_path_terminal_result_file_is_valid_repo_project_result` (reads `RepoProjectResult.result.json` from disk, validates, asserts GitHub CI file is present). **`TestHaltPaths`** (5 tests): halt at intake on DRAFT_INCOMPLETE (asserts `data_request is None` + only IntakeReport envelope persisted); halt at data on EXECUTION_FAILED (asserts IntakeReport + DataRequest + DataReport persisted, no RepoTarget, no terminal result); halt at website on FAILED (asserts terminal result IS persisted even on failure — operator needs to inspect it); downstream-agent-not-called guard on intake halt (both data_runner and website_runner closure-count == 0); downstream-not-called guard on data halt (website_runner closure-count == 0). **`TestPipelineConfig`** (3 tests): correlation_id defaults to run_id; correlation_id override; `project_url` property returns None when no project_result.

8. **Phase 5 verification — every verification command run:**
   - `uv run pytest tests/orchestrator/ -v` → **45 passed** in 0.82s. Orchestrator package itself at **100% line + 100% branch coverage** (adapters 15/15, checkpoints 47/47, pipeline 59/59, __init__ 5/5).
   - `uv run pytest -q` → **368 passed @ 96.97% coverage** (was 323 @ 96.77%; +45 tests, +0.20%). Zero skips, zero xfails, zero regressions.
   - `uv run mypy src/model_project_constructor/orchestrator/ src/model_project_constructor/agents/website/` → **Success: no issues found in 17 source files** (was 13; +4 new orchestrator files). Zero `# type: ignore` comments added anywhere.

9. **Phase 5 step 6 — Doc updates:**
   - `README.md` phase-table row 5: "Not started" → "Complete".
   - `README.md` repo-layout block: added `orchestrator/` sub-block with one-line annotations for `pipeline.py` (`run_pipeline(config, *, intake_runner, data_runner, website_runner)`), `adapters.py` (the §7 decoupling site), `checkpoints.py` (`CheckpointStore` + envelope / terminal channels).
   - `README.md` test-tree: added `tests/orchestrator/` line ("45 orchestrator tests (pipeline halt paths, adapters, checkpoints)").
   - `README.md` getting-started line: "All 323 tests should pass with coverage above 93% (currently ≈96.8%)" → "All 368 tests should pass with coverage above 93% (currently ≈97.0%)".
   - `architecture-plan.md` unchanged — the §14 Phase 5 amendment paragraph Session 14 added was already accurate.

### Key Files Shipped in Session 15

**Schema tweak (temporarily + reverted):**
- `src/model_project_constructor/schemas/envelope.py` — no net change. Widened `target_agent` Literal to include `"orchestrator"`, then reverted when the Phase 1 test flagged the invariant. The final `checkpoints.py` design uses a sibling `save_result` channel instead, which is strictly cleaner.

**Source files (4 NEW):**
- `src/model_project_constructor/orchestrator/__init__.py` (48 LOC) — public surface re-exports.
- `src/model_project_constructor/orchestrator/adapters.py` (82 LOC) — `intake_report_to_data_request` + `infer_target_granularity`.
- `src/model_project_constructor/orchestrator/checkpoints.py` (104 LOC) — `CheckpointStore` with dual envelope / terminal-result channels.
- `src/model_project_constructor/orchestrator/pipeline.py` (205 LOC) — `run_pipeline` + `PipelineConfig` / `PipelineResult` / callable runner type aliases.

**Test files (4 NEW):**
- `tests/orchestrator/__init__.py` (empty marker).
- `tests/orchestrator/test_adapters.py` (163 LOC, 11 tests).
- `tests/orchestrator/test_checkpoints.py` (220 LOC, 15 tests).
- `tests/orchestrator/test_pipeline.py` (352 LOC, 19 tests after parametrize expansion).

**Docs (2):**
- `README.md` — phase-table row 5 → "Complete", repo-layout `orchestrator/` sub-block, test-tree `tests/orchestrator/` line, total-test-count line.
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewritten for Session 16 + Session 15 handoff + Phase 3A evaluation of Session 14 + Session 14 `Commits: TBD` backfill).

**Total: 11 files changed (10 new + 1 README) in one feat commit.**

### Gotchas — Read These Before Starting Session 16 / Phase 6

**Carryover from Sessions 11–14 that STILL applies to Phase 6:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:151-154` is still there** and manually sets `agent.ci_platform = "gitlab"`. Phase 6 does NOT need to touch it.
- **`retry_backoff` uses `time.sleep()` in production.** Phase 6 observability wrappers should NOT log inside the retry loop on every attempt — log the final outcome via the `make_nodes(client, *, sleep=...)` injection seam or the `WebsiteAgent.run` return value, not inside the node itself.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** Both production adapters inherit from it. Phase 6 observability decorators on the `RepoClient` surface must preserve the duck-typed Protocol conformance (no `isinstance(client, RepoClient)` checks).
- **Both adapters are kwarg-only.** `PythonGitLabAdapter(*, host_url, private_token)` and `PyGithubAdapter(*, host_url="https://api.github.com", private_token)`. Phase 6's env-var config code must use kwargs when constructing them.
- **PyGithub ships `py.typed`.** No `# type: ignore[import-untyped]` needed anywhere in the tree.
- **`cli.py` is 100% line + branch covered.** Any Phase 6 changes to `agents/website/cli.py` (e.g. to wire env-var defaults) should maintain 100% coverage on that file.

**New Phase 6 gotchas (from Phase 5 work):**

- **`HandoffEnvelope.target_agent` is `Literal["intake", "data", "website"]` — it CANNOT be "orchestrator".** I tried this during Phase 5 and `tests/schemas/test_envelope_and_registry.py:63-66` flagged it immediately. This is a Phase 1 design invariant: the orchestrator sends envelopes between agents but never receives one. **If Phase 6 observability wants to log "the orchestrator received X", use the `CheckpointStore.save_result` path (which writes `<name>.result.json`), NOT a new envelope type.** The dual-channel design of `CheckpointStore` exists precisely to preserve this invariant.
- **`run_pipeline` takes callable runners, not concrete agent instances.** The three runner type aliases are `IntakeRunner = Callable[[], IntakeReport]`, `DataRunner = Callable[[DataRequest], DataReport]`, `WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]`. Phase 6's production wrapper should construct real `IntakeAgent` / `DataAgent` / `WebsiteAgent` instances in a factory, then pass bound methods or lambdas as the runners. This is the designated injection seam for logging decorators — wrap the runner, don't modify `pipeline.py`.
- **The orchestrator already threads `correlation_id` through every envelope it saves.** `PipelineConfig.correlation_id` defaults to `run_id` but can be set independently. Phase 6 structured logging should use `correlation_id` (not `run_id`) as the trace-ID field so that a single operator-initiated job that fans out into multiple runs stays traceable.
- **The terminal `RepoProjectResult` is persisted via `CheckpointStore.save_result("RepoProjectResult", result)`, NOT via `save(envelope)`.** The resulting file is `<base_dir>/<run_id>/RepoProjectResult.result.json`. Phase 6's OPERATIONS.md + TROUBLESHOOTING.md must document this location because "where do I find the project result after a crash?" is the #1 operator question.
- **`run_pipeline` halts on website failure AFTER persisting the terminal result.** On `FAILED_AT_WEBSITE`, `store.has_result(run_id, "RepoProjectResult")` returns True — the operator can read the failed project result from disk. On `FAILED_AT_DATA` or `FAILED_AT_INTAKE`, the terminal result is NOT written (there's nothing to write). This asymmetry is tested in `test_pipeline.py` (`test_halt_at_data_when_execution_failed` asserts `not store.has_result(...)`). Phase 6 troubleshooting docs should note this.
- **Adapter inference is conservative.** `intake_report_to_data_request` defaults `time_range` to `"last 5 calendar years of historical records"` and derives `population_filter` from `target_definition` — these are BEST-EFFORT defaults, not domain-intelligent extractions. Phase 6 should NOT add config knobs to override these in `PipelineConfig`; instead, a future iteration can have the intake agent capture `time_range` as a dedicated field and the adapter pull from there. For Phase 6, document the default in OPERATIONS.md as a known limitation.
- **`CheckpointStore.list_payload_types` excludes `.result.json` files.** Phase 6's "list all checkpoints for a run" CLI (if it adds one) should call BOTH `list_payload_types` and `list_result_names` and merge. There's a `test_list_excludes_terminal_results` test pinning this.
- **The four orchestrator source files are at 100% line + branch coverage.** Phase 6 changes to any of them must maintain this — if a new branch is added, add a test in the same PR. The coverage floor bump 93 → 94 (the Phase 0 chore commit) is not load-bearing against the orchestrator specifically, but it does mean a regression in `agents/intake/` or `ui/intake/` coverage could tip the suite below floor.
- **No new `pyproject.toml` deps were added in Phase 5.** Phase 6 will likely add `structlog` (or `loguru`) + `pydantic-settings`. Both ship `py.typed`; expect zero mypy friction.

### Session 13 Handoff Evaluation (by Session 14)
**Score: 10/10.** Third consecutive 10. Phase D was a pure step-execution session because Session 13 left no guesswork.

- **What helped:** (a) The "Carryover gotchas + new Phase D gotchas" split was the single highest-leverage artifact. The note "**`PyGithubAdapter.__init__` is kwarg-only and defaults `host_url='https://api.github.com'`**" in contrast to "`PythonGitLabAdapter.__init__` requires `host_url` (no default)" told me before I touched any code that the CLI needed an `Optional[str]` for `--host-url` with a per-host default — I wrote the resolved-host-url branch directly without ever instantiating either adapter to discover the asymmetry. (b) The lazy-import gotcha ("**The adapter selection branch must lazy-import** both `PyGithubAdapter` and `PythonGitLabAdapter`. Neither `import github` nor `import gitlab` should happen at `cli.py` import time") was load-bearing — I never even considered moving the imports up. (c) The pre-flight baseline numbers matched exactly (313 @ 96.55%, 13 mypy files), so I detected zero drift in 8 seconds. (d) The do-not-touch list (`gitlab_adapter.py`, `github_adapter.py`, `protocol.py`, `state.py`, `nodes.py`, `agent.py`, `graph.py`, `governance_templates.py`) gave me explicit permission to ignore everything outside the CLI/test/docs surface — Phase D really was a one-file source change. (e) The "test_github_adapter.py mocks `adapter._gh` directly" gotcha steered me toward the `_StandinAdapter(FakeRepoClient)` monkeypatch pattern instead of trying to instantiate real PyGithub/python-gitlab clients with fake tokens.
- **What was missing:** Genuinely nothing required for Phase D. The handoff anticipated the `--ci-platform` override flag question (plan §9.1 already specified it), the `CIPlatform` promotion question (Session 13 explicitly left it to Phase D's judgment — I chose to spell `Literal["gitlab", "github"]` inline because the CLI was the only new consumer and the diff stays self-contained), and even the `uv.lock` churn from Phase C (no new churn this session because Phase D added no deps). **Not deducting.**
- **What was wrong:** Nothing. Every claim verified on disk. Pre-flight numbers matched. The "PyGithub ships `py.typed`" correction from Session 13 was load-bearing — I added zero `# type: ignore` comments and mypy stayed clean across the new lazy-import line.
- **ROI:** Reading the handoff (~5 min) saved an estimated 30–40 min of Phase D discovery: the host-url asymmetry, the lazy-import pattern, the monkeypatch approach for adapter selection tests, the deprecated-alias removal scope. ~6× ROI, identical to Sessions 12 and 13.

### What Session 14 Did
**Deliverable:** Phase D of `docs/planning/github-gitlab-abstraction-plan.md` — `--host {gitlab,github}` typer flag in `agents/website/cli.py` with lazy-imported adapter selection, `--ci-platform` override flag, removal of Phase A deprecated aliases (`--fake-gitlab`, `--gitlab-url`, `--group-path`), parametrized CLI tests covering both fake paths, both monkeypatched real-adapter paths, the bogus-host case, and the removed-alias regression. Plus README getting-started rewrite (both GitLab and GitHub examples), README phase-table row 4B update, README repo-layout update, and a one-paragraph amendment to `architecture-plan.md` §14 Phase 5 noting the abstraction landed first. **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `e9f0d10` (Phase D feat), `9f20e95` (README docs follow-on). Backfilled by Session 15's Phase 3A.

**Pre-flight baseline (verified on disk):**
- `uv run pytest -q` → **313 passed, 96.55% coverage**. Matches Session 13 exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 13 source files**. Matches.
- `git status` → clean on `master`, 21 commits ahead of `origin/master`.
- **Pushed to `origin/master`** at the start of the session per user request — `5c73ed0..72ac527`. After that the branch was 0 commits ahead until Phase D's commit.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-280 (ACTIVE TASK + Session 13 handoff + gotchas + Session 12 handoff for comparison), ran `git status` / `git log --oneline -5` / pre-flight pytest + mypy in parallel, confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "yes" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step even though ACTIVE TASK already described the deliverable.**

2. **User asked about pushed state** — reported the 21 unpushed commits, asked for explicit authorization (push is shared-state per SAFEGUARDS), pushed on confirmation. Branch is now 0 ahead of `origin/master` until Phase D's feat commit.

3. **User said "yes" to Phase D** — wrote Session 14 IN-PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14).

4. **Phase D step 1 — Plan re-read + read every Phase D input file:**
   - Plan §9 (Phase D spec) + §10 (do-not-change list).
   - `agents/website/cli.py` end-to-end (the existing `--fake-gitlab` / `--gitlab-url` / `--group-path` aliases at lines 17-19 + 69 + 84 + 92, the existing if/else adapter selection at lines 124-137).
   - `agents/website/github_adapter.py` (constructor signature `(*, private_token: str, host_url: str = "https://api.github.com")` — confirms the kwarg-only + default-host-url contract).
   - `agents/website/agent.py` (`WebsiteAgent.__init__` signature already accepts `ci_platform: Literal["gitlab", "github"] = "gitlab"` from Phase B — Phase D just needs to pass it).
   - `tests/agents/website/conftest.py` (the `intake_report_path` / `data_report_path` fixtures used by `test_cli.py`).
   - `tests/agents/website/test_cli.py` (the existing 3 tests — preserved, not deleted).
   - `README.md` (full file — getting-started lines 149-169 + repo layout + phase table).
   - `docs/planning/architecture-plan.md` §14 Phase 4-5 block (lines 880-960).

5. **Phase D step 2 — `cli.py` rewrite (the source-side change):**
   - Replaced the 168-line file with a 219-line rewrite. Top-level changes:
     - Added module-level constants `GITLAB_DEFAULT_HOST_URL = "https://gitlab.example.com"`, `GITHUB_DEFAULT_HOST_URL = "https://api.github.com"`, `VALID_HOSTS = frozenset({"gitlab", "github"})`, `VALID_CI_PLATFORMS = frozenset({"gitlab", "github"})`.
     - **Removed** `"--fake-gitlab"` from the `--fake` typer.Option, `"--group-path"` from `--namespace`, `"--gitlab-url"` from `--host-url`. Phase A's deprecated aliases are gone entirely.
     - Added `host: str = "gitlab"` typer option with `--host` flag.
     - Added `ci_platform: Optional[str] = None` typer option with `--ci-platform` flag — defaults to `host` value, can be overridden independently (per plan §9.1).
     - Made `host_url: Optional[str] = None` (was `str = DEFAULT_HOST_URL`) so the per-host default applies only when the user doesn't explicitly pass `--host-url`.
     - Validation: `host not in VALID_HOSTS` → exit 2 with sorted-choices error message; `ci_platform not in VALID_CI_PLATFORMS` (when explicitly provided) → exit 2; the existing `not fake and not private_token` guard kept.
     - `resolved_host_url` computed inline as `host_url if host_url is not None else (GITHUB_DEFAULT_HOST_URL if host == "github" else GITLAB_DEFAULT_HOST_URL)`.
     - Adapter selection rewritten as `if fake → FakeRepoClient(); elif host == "gitlab" → lazy-import PythonGitLabAdapter; else (host == "github") → lazy-import PyGithubAdapter`. Both lazy imports live INSIDE their respective branches (matches the Phase A pattern, extends it to GitHub).
     - `WebsiteAgent(client, ci_platform=cast(Literal["gitlab", "github"], ci_platform))` — the `cast` is necessary because `ci_platform` is a `str` after CLI parsing and mypy strict won't narrow it to a `Literal`.
   - Module docstring rewritten to describe Phase D's new behavior; the "deprecated aliases" paragraph from Phase A is gone.

6. **Phase D step 3 — mypy probe on `cli.py`:**
   - `uv run mypy src/model_project_constructor/agents/website/cli.py` → `Success: no issues found in 1 source file`. Zero `# type: ignore` comments needed. The `cast` covers the only narrowing site.

7. **Phase D step 4 — CLI smoke checks before writing tests** (sanity check that the rewrite is functional):
   - `--help` → shows `--host`, `--ci-platform`, `--host-url` with correct help text + per-host default in the `--host-url` description.
   - `--host gitlab --fake` + subrogation fixture → `Status: COMPLETE`, `.gitlab-ci.yml` in output, no `.github/workflows/ci.yml`.
   - `--host github --fake` + subrogation fixture → `Status: COMPLETE`, `.github/workflows/ci.yml` in output, no `.gitlab-ci.yml`.
   - `--host bogus --fake` → exit 2 with `ERROR: --host must be one of ['github', 'gitlab'] (got 'bogus').` (sorted alphabetical).
   - `--fake-gitlab` (the removed alias) → typer/click rejects with `No such option: --fake-gitlab Did you mean --fake?`.

8. **Phase D step 5 — `tests/agents/website/test_cli.py` rewrite (the test-side change):**
   - Preserved all 3 baseline tests (`test_cli_requires_fake_or_token`, `test_cli_happy_path_prints_tree_and_result`, `test_cli_writes_output_file`). Renamed the first from `test_cli_requires_fake_flag` to `test_cli_requires_fake_or_token` to reflect Phase D's wording (the error message now mentions both).
   - Added 10 new tests organized under three section headers:
     - **Phase D `--host` fan-out (4 tests):**
       - `test_cli_host_fake_emits_correct_ci_file[gitlab]` and `[github]` — parametrized over `(host, expected_ci, forbidden_ci)`. Asserts the CLI run completes AND the `files_created` list contains the expected CI artifact AND does NOT contain the other one. Mirrors the positive+negative assertion pattern from Learning #5.
       - `test_cli_ci_platform_overrides_host` — exercises `--host gitlab --fake --ci-platform github` and asserts the CI file is `.github/workflows/ci.yml` (the override wins). Pins the orthogonality of `--host` vs `--ci-platform`.
       - `test_cli_host_bogus_exits_2` — `--host bogus --fake` → exit code 2.
       - `test_cli_ci_platform_bogus_exits_2` — `--ci-platform bogus --fake` → exit code 2.
     - **Phase D real-adapter selection (2 tests, monkeypatched):**
       - `test_cli_host_gitlab_with_token_invokes_python_gitlab_adapter` — monkeypatches `model_project_constructor.agents.website.gitlab_adapter.PythonGitLabAdapter` to a `_StandinGitLabAdapter` (a `FakeRepoClient` subclass that records `__init__` kwargs in a class-level dict). Invokes the CLI with `--host gitlab --private-token fake-gitlab-token --host-url https://gitlab.example.com`. Asserts `Status: COMPLETE` AND the recorded kwargs are exactly `{"host_url": "https://gitlab.example.com", "private_token": "fake-gitlab-token"}`.
       - `test_cli_host_github_with_token_invokes_pygithub_adapter` — same pattern for `PyGithubAdapter`. Omits `--host-url` to verify the GitHub default kicks in (`"https://api.github.com"`). Also asserts the resulting `files_created` contains `.github/workflows/ci.yml` (default ci_platform follows `--host github`).
     - **Phase D removed-alias regression (3 parametrized cases):**
       - `test_cli_removed_phase_a_aliases[--fake-gitlab|--gitlab-url|--group-path]` — invokes the CLI with each old alias and asserts a non-zero exit + `"no such option"` substring in the combined stdout/stderr. Pins that the removal is permanent.
   - Added module-level helper class `_StandinAdapter(FakeRepoClient)` with two trivial subclasses (`_StandinGitLabAdapter`, `_StandinGitHubAdapter`) so each test has its own `last_init_kwargs` slot and can run in any order without state pollution.
   - 13 tests total in `test_cli.py` (was 3 — added 10).

9. **Phase D step 6 — Phase D verification (plan §9.3) — every command run sequentially:**
   - `uv run python -m model_project_constructor.agents.website --help | grep -- '--host'` → matches the `--host` line + the `--host-url` description's "for --host" mention. Multiple hits ✓.
   - `uv run python -m model_project_constructor.agents.website --host gitlab --fake ...` → `Status: COMPLETE` + `.gitlab-ci.yml` ✓.
   - `uv run python -m model_project_constructor.agents.website --host github --fake ...` → `Status: COMPLETE` + `.github/workflows/ci.yml` ✓.
   - `uv run python -m model_project_constructor.agents.website --fake-gitlab ...` → `No such option: --fake-gitlab Did you mean --fake?` ✓.
   - `uv run pytest tests/agents/website/test_cli.py -v` → **13 passed**. cli.py at **100% line coverage** in this isolated run.
   - `uv run pytest -q` → **323 passed @ 96.77% coverage** (was 313 @ 96.55%; +10 tests, +0.22% coverage). Zero skips, zero xfails, zero deletions.
   - `uv run mypy src/model_project_constructor/agents/website/` → `Success: no issues found in 13 source files` (unchanged from baseline — Phase D added no new source files).

10. **Phase D step 7 — Doc updates:**
    - `README.md` phase-table row 4B: "...python-gitlab adapter" → "...repo-host adapter (GitHub/GitLab abstraction)".
    - `README.md` repo-layout block: added `github_adapter.py` line, updated `cli.py` annotation to mention `--host gitlab|github`, updated test count to "122 website agent tests".
    - `README.md` total test count line: "All 289 tests should pass with coverage above 90%" → "All 323 tests should pass with coverage above 93%" with new percentage "(currently ≈96.8%)".
    - `README.md` getting-started: full rewrite of the website agent section. Was 4 fenced examples (1 fake + 1 real GitLab) + 2 paragraphs. Now: 4 fenced examples (fake gitlab default, fake github, real GitLab via `--host gitlab`, real GitHub via `--host github`) + 1 consolidated paragraph describing `--host` / `--ci-platform` / governance fan-out. Removed the deprecated-alias paragraph entirely. Removed the forward-reference paragraph that said "Phase D will surface a `--ci-platform` CLI flag" (it now exists).
    - `docs/planning/architecture-plan.md` §14 Phase 5: inserted a one-paragraph **Amendment** block immediately under the Phase 5 heading. The amendment notes that the GitHub/GitLab abstraction plan landed first (Sessions 11–14), that orchestrator code now imports `RepoTarget` / `RepoProjectResult` from `schemas.v1.repo`, that `WebsiteAgent` accepts a `RepoClient` + `ci_platform` constructor kwarg, that `agents/website/cli.py` is the model for the `--host` plumbing pattern, and that end-to-end testing can run against either real adapter or `FakeRepoClient`. The original Phase 5 bullets are preserved verbatim except that "real GitLab project on test instance" is widened to "real repo project on a test host (GitLab or GitHub)."
    - `grep -n 'host github\|host gitlab' README.md` → 5+ hits ✓. `grep -n 'RepoTarget\|RepoProjectResult' docs/planning/architecture-plan.md` → multiple hits across §4, §5.4, §14 amendment ✓.

### Key Files Shipped in Session 14

**Source files edited (1):**
- `src/model_project_constructor/agents/website/cli.py` — rewritten end-to-end (168 → 219 lines). `--host`, `--ci-platform`, lazy-imported dual adapter selection, deprecated-alias removal, per-host `--host-url` default.

**Test files edited (1):**
- `tests/agents/website/test_cli.py` — 3 baseline tests preserved (one renamed); 10 new tests added across three sections (`--host` fan-out, real-adapter monkeypatched selection, removed-alias regression). Module helper `_StandinAdapter(FakeRepoClient)` + two empty subclasses.

**Docs (3):**
- `README.md` — phase table row 4B, repo layout block (+`github_adapter.py`, updated `cli.py` annotation, test count), total-test-count sentence, getting-started full rewrite (+ GitHub example), removed deprecated-alias paragraph.
- `docs/planning/architecture-plan.md` — §14 Phase 5 amendment paragraph.
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewritten for Session 15 + Session 14 handoff + Phase 3A evaluation of Session 13).

**Total: 5 files changed in one feat commit (no new source modules — the `orchestrator/` package is Session 15's job).**

### Gotchas — Read These Before Starting Session 15 / Phase 5

**Carryover from Sessions 11–13 that STILL applies to Phase 5:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:151-154` is still there**, and manually sets `agent.ci_platform = "gitlab"`. If Phase 5 ever needs to also construct a `WebsiteAgent` via `__new__` (it shouldn't — orchestrator should use the normal factory), remember to set `ci_platform` manually.
- **`retry_backoff` uses `time.sleep()` in production.** Phase 5 end-to-end tests should mock at the adapter level (or use `FakeRepoClient`) to avoid wall-clock waits. The `make_nodes(client, *, sleep=...)` injection pattern in `nodes.py:79-83` is preserved.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** Both production adapters (`PythonGitLabAdapter`, `PyGithubAdapter`) explicitly inherit from it. Don't worry about this — both inherit-and-not-inherit patterns work; the codebase has chosen "inherit" for both adapters.
- **`_is_name_conflict` lives in each adapter module separately.** Don't refactor these into a common helper — they inspect platform-specific exception shapes.
- **PyGithub ships `py.typed`.** No `# type: ignore[import-untyped]` is needed when importing `github` anywhere in the tree. If a future session sees a mypy complaint about it, that's a regression in the dep, not in our code.
- **Both adapters are kwarg-only.** `PythonGitLabAdapter(*, host_url, private_token)` and `PyGithubAdapter(*, host_url="https://api.github.com", private_token)`. Phase 5's orchestrator construction code must use kwargs.

**New Phase 5 gotchas (from Phase D work):**

- **`cli.py` is now 100% line-covered (66/66 statements) and 100% branch-covered (16/16 branches) per the isolated `pytest tests/agents/website/test_cli.py` run.** Phase 5's orchestrator should aim for similar discipline. The orchestrator will likely need lower branch coverage on the actual pipeline-running paths because the end-to-end tests are slower, but the adapter/config/halt-logic surface should stay near 100%.
- **The `cast(Literal["gitlab", "github"], ci_platform)` pattern** at `cli.py:191` is the canonical way to take a `str` from CLI/config and pass it into `WebsiteAgent(ci_platform=...)`. Phase 5's orchestrator config will hit the same need — copy this pattern, don't try to make the agent take `str` (that would weaken its typing contract).
- **Lazy imports of both adapters live INSIDE the if/elif branches in `cli.py:165-187`.** This is load-bearing for `--help` performance — eager imports would pull in `gitlab` and `github` packages on every invocation. Phase 5's orchestrator should follow the same pattern: lazy-import the concrete adapter in the branch that selects it, not at module top.
- **The `_StandinAdapter(FakeRepoClient)` monkeypatch pattern** in `test_cli.py:194-216` is the canonical way to test "the CLI invoked the right adapter constructor with the right kwargs" without instantiating a real adapter. Phase 5's orchestrator tests should copy this pattern when testing adapter selection. Each subclass needs its own `last_init_kwargs` class slot (NOT `last_init_kwargs: dict[str, Any] = {}` shared via the parent — see `_StandinGitLabAdapter` and `_StandinGitHubAdapter` for the per-subclass override pattern).
- **`--host-url` is now `Optional[str]` with a per-host default.** Phase 5's orchestrator config schema should mirror this — if a user/config omits `host_url`, derive it from `host` (gitlab → `https://gitlab.example.com`, github → `https://api.github.com`). The two constants live in `cli.py:42-43` (`GITLAB_DEFAULT_HOST_URL`, `GITHUB_DEFAULT_HOST_URL`); Phase 5 should either import them or duplicate them in `orchestrator/pipeline.py` (judge based on whether the orchestrator needs to depend on `agents/website/cli.py`).
- **`RepoTarget` requires `host_url`.** It's a Pydantic field with no default. Phase 5's adapter (intake → orchestrator → website) must populate it; the orchestrator config is the canonical place to resolve "user passed `--host github` and no `--host-url`" → "set `RepoTarget.host_url = 'https://api.github.com'`" before constructing the website agent.
- **`agent.run(intake_report, data_report, repo_target)` is the canonical website-agent entry point.** It returns a `RepoProjectResult` with `status` ∈ `{"COMPLETE", "FAILED", "PARTIAL"}`. The pipeline orchestrator should branch on this to set its own halt state. Look at `agent.py:44-81` for the exact flow.
- **`HandoffEnvelope` + `schemas/registry.py` are the persistence layer for inter-agent handoffs.** The registry currently has 5 entries: `IntakeReport`, `DataRequest`, `DataReport`, `RepoTarget`, `RepoProjectResult`. Phase 5 will use these in `checkpoints.py` to round-trip envelopes between agents.
- **No new `pyproject.toml` deps required for Phase 5** — all the orchestrator's needs are already satisfied by `[project.optional-dependencies].agents` (which includes `python-gitlab`, `PyGithub`, `langgraph`, etc.). No `uv.lock` churn expected.
**Score: 10/10.** Second consecutive 10. Phase C was a pure step-execution session because Session 12 left no guesswork.

- **What helped:** (a) The "Mirror, don't merge" framing + the explicit note that `_is_name_conflict` in `gitlab_adapter.py:158` loose-matches GitLab's response shape told me exactly what the GitHub equivalent's contract should be — loose match on "already exists" substring inside a 422 payload. I knew the helper shape before I typed a character of adapter code. (b) The "`PyGithub` historically has NOT shipped stubs — expect to need `# type: ignore[import-untyped]`" warning in Phase B's handoff set my expectation appropriately; when the probe returned clean, I had high confidence it wasn't a false negative because I was watching for it. (c) The pre-flight baseline numbers (295 @ 96.53%, mypy 12 files) let me detect drift in seconds — both matched exactly. (d) The "Coverage floor is 93%, not 90%" reminder + the prediction "adapter will likely be ~100% if tests are written carefully" framed the test-design target before I wrote a line of tests.
- **What was missing:** One small gap: the Session 12 gotcha "`PyGithubAdapter` should NOT inherit from `RepoClient`; structural conformance is enough" contradicts the actual pattern in `gitlab_adapter.py:41` (`class PythonGitLabAdapter(RepoClient):` — it DOES inherit). I mirrored the gitlab adapter's inheritance pattern rather than the gotcha, because consistency with the existing module felt more defensible than following a note contradicted by code in the same package. Either reading is valid (Protocol subclassing is fine when not `@runtime_checkable`), but the gotcha should be updated or removed in future handoffs so the next session doesn't waste cycles resolving the contradiction. **Not deducting a point** — the gotcha warned me to think about it, which is half the value.
- **What was wrong:** One minor correction: Phase B's handoff described `WebsiteAgent.ci_platform` as a "public attribute... because the `__new__` hack in `test_retry.py` sets it directly." Phase C never touched `WebsiteAgent` and never needed to read the attribute, so this turned out to be dead context for Phase C specifically. Not a protocol violation — just a note that didn't apply here. **No deduction.**
- **ROI:** Reading the handoff (~6 min) saved an estimated 35–45 min of Phase C discovery: the `_is_name_conflict` loose-match strategy, the 422/"already exists" substring, the "mirror don't merge" framing, and the Phase B baseline numbers. Easily 6× ROI.

### What Session 13 Did
**Deliverable:** Phase C of `docs/planning/github-gitlab-abstraction-plan.md` — new `agents/website/github_adapter.py` with `PyGithubAdapter` (a `RepoClient`-subclassing concrete class wrapping `PyGithub`), `PyGithub>=2,<3` added to `pyproject.toml` `agents` extras, re-export from `agents/website/__init__.py`, new `tests/agents/website/test_github_adapter.py` with 18 tests covering the adapter surface. **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `55745ed` (Phase C). One commit as predicted by the plan §8.5 session boundary.

**Pre-flight baseline (verified on disk):**
- `uv run pytest -q` → **295 passed, 96.53% coverage**. Matches Session 12 exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**. Matches.
- `git status` → clean on `master`, 19 commits ahead of `origin/master`.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + Session 12 handoff + gotchas), ran `git status` / `git log --oneline -5` / pre-flight pytest + mypy in parallel, confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "pursue active task" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step.**

2. **User said "pursue active task"** — wrote Session 13 IN-PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14).

3. **Phase C step 1 — plan re-read + GitLab adapter + protocol baseline:**
   - Read plan §8 (Phase C spec) in full + §10 (do-not-change list). Confirmed the protocol signature is `(*, namespace, name, visibility)` (not `group_path` — plan §8.1 used the pre-Phase-A name in one bullet, but the actual `protocol.py:51` is `namespace`). Kept the plan's semantic intent, used the current protocol names.
   - Read `gitlab_adapter.py` end-to-end. Noted: (a) `class PythonGitLabAdapter(RepoClient):` DOES inherit from the Protocol (see above — resolved the Session 12 gotcha contradiction in favor of consistency); (b) `_is_name_conflict` is a module-level helper called from `create_project`'s `except` block; (c) constructor is kwarg-only, wraps `gitlab.Gitlab(...)` eagerly; (d) `create_project` returns `ProjectInfo(id=str(...), url, default_branch)`, and the `id` stringification is what enables `project_id: str` on the protocol.
   - Read `protocol.py` to re-verify `RepoClient` signatures and `RepoClientError` / `RepoNameConflictError` class shapes.
   - Read `test_gitlab_adapter.py` for test-shape mirroring. Noted: (a) the `_build_adapter_with_fake_gl` helper pattern stubs `adapter._gl` directly; (b) `TestImport` uses `callable(getattr(...))` duck-typing (not `isinstance`) because the Protocol is not `@runtime_checkable`; (c) there's a dedicated `TestNameConflictSniffing` class for `_is_name_conflict` coverage.

4. **Phase C step 2 — `pyproject.toml` dependency add:**
   - Added `"PyGithub>=2,<3"` to `[project.optional-dependencies].agents`, immediately after `"python-gitlab>=4"`. Same ordering as the plan §8.1 spec.
   - Ran `uv sync --extra agents --extra ui --extra dev` — resolved in 421ms, installed `pygithub==2.9.1` + 6 transitive deps (`cffi`, `cryptography`, `pycparser`, `pyjwt`, `pynacl`, `PyGithub`). All wheels; no source builds.

5. **Phase C step 3 — PyGithub type-stub probe (plan §8.2):**
   - Wrote a throw-away probe script exercising `github.Github`, `GithubException`, `UnknownObjectException`, and `InputGitTreeElement` under `uv run mypy --strict`. **Result: `Success: no issues found in 1 source file`.** PyGithub 2.9.1 ships `py.typed` — **no `# type: ignore[import-untyped]` needed**. (Contradicts Phase B's prediction but in a good way.)
   - Probed the `Github` constructor signature via `inspect.signature`: v2.x uses `Github(auth=Auth.Token(token), base_url=...)` as the modern idiom; positional `login_or_token` still works but is deprecated. **Chose `Auth.Token`** for the new adapter because this is fresh code — no backwards-compatibility concern — and the Auth API is PyGithub's documented v2.x direction.
   - Probed `GithubException` instantiation: `GithubException(status, data=..., headers={})`. Verified `.status` is int and `.data` exposes the parsed JSON body dict. This shape drives `_is_name_conflict`.

6. **Phase C step 4 — `github_adapter.py` (the new 172-LOC module):**
   - Header docstring mirrors `gitlab_adapter.py`'s (purpose, thinness, exception-translation contract, "not unit-tested against live GitHub", lazy-import note). Added a paragraph about nested namespaces being explicitly rejected — GitLab supports `"org/sub/sub"`, GitHub has a single owner level, so I fail loudly with `RepoClientError` rather than silently flattening.
   - `class PyGithubAdapter(RepoClient):` — inherits from the Protocol to match `gitlab_adapter.py`'s pattern (see handoff evaluation above).
   - `__init__(self, *, private_token: str, host_url: str = "https://api.github.com")` — kwarg-only. `host_url` defaults to public GitHub; GitHub Enterprise callers pass `"https://github.example.com/api/v3"`. Wraps `Github(auth=Auth.Token(private_token), base_url=host_url)`, stored as `self._gh: Any = ...` (the `Any` annotation matches `gitlab_adapter.py`'s `self._gl: Any` pattern so tests can monkeypatch freely).
   - `create_project(*, namespace, name, visibility) -> ProjectInfo`:
     - **Nested-namespace guard** (plan §8.1 Trap 3): if `"/" in namespace`, raise `RepoClientError` with a clear message.
     - **Owner resolution**: try `self._gh.get_organization(namespace)` first. On `UnknownObjectException` (404), fall back to `self._gh.get_user(namespace)`. On any other `GithubException` from the org lookup, bubble up as `RepoClientError`. On any `GithubException` from the user fallback, also bubble up.
     - `private = visibility != "public"` — GitHub has no "internal" visibility, so `"internal"` maps to private, matching plan §8.1.
     - Call `owner.create_repo(name=name, private=private)`. On `GithubException`, check `_is_name_conflict`; if true, raise `RepoNameConflictError(name)`; otherwise raise `RepoClientError` with a descriptive message.
     - Return `ProjectInfo(id=str(repo.full_name), url=str(repo.html_url), default_branch=str(getattr(repo, "default_branch", None) or "main"))`. The `full_name` is `"owner/name"` — this is the opaque token callers pass back to `commit_files`, which is consistent with the `ProjectInfo.id` docstring on `protocol.py:19-27`.
   - `commit_files(*, project_id, branch, files, message) -> CommitInfo`:
     - Separate try/except for `get_repo(project_id)` — a missing repo is its own error message ("project lookup failed").
     - One big try/except around the 4-call git dance: `get_git_ref(f"heads/{branch}")` → `get_git_commit(ref.object.sha)` → list-comp of `create_git_blob(content, "utf-8")` calls (one per file, sorted by path) → `create_git_tree(tree_elements, base_tree=parent_commit.tree)` → `create_git_commit(message, tree, [parent_commit])` → `ref.edit(sha=commit.sha)`. Any `GithubException` inside this block raises `RepoClientError` with project_id + branch context.
     - Tree elements are `InputGitTreeElement(path=path, mode="100644", type="blob", sha=blob.sha)`. **Sorted by path** to match `gitlab_adapter.py`'s sorted-actions behavior — this is what keeps the two adapters' commit bytes deterministic across hosts.
     - Return `CommitInfo(sha=str(commit.sha), files_committed=[path for path, _ in sorted_items])`.
   - `_is_name_conflict(exc: GithubException) -> bool`:
     - Returns `False` if `exc.status != 422`.
     - If `exc.data` is a dict, iterate `data.get("errors", []) or []`; for each dict entry, lowercase `err.get("message", "")` and check for `"already exists"` substring. Return `True` on first hit.
     - Fallback: return `"already exists" in str(exc).lower()`. This catches wording drift where the error is somewhere else in the payload but the stringified exception still mentions "already exists".
     - Mirrors `gitlab_adapter._is_name_conflict`'s loose-match philosophy: match the substring, not the exact wording, so a minor GitHub API message change doesn't break the adapter.
   - `__all__ = ["PyGithubAdapter"]`.

7. **Phase C step 5 — `__init__.py` re-export:**
   - Added `from model_project_constructor.agents.website.github_adapter import PyGithubAdapter` immediately above the existing `gitlab_adapter` import (alphabetical: `github_adapter` < `gitlab_adapter`).
   - Added `"PyGithubAdapter"` to `__all__` immediately above `"PythonGitLabAdapter"`, same alphabetical ordering.

8. **Phase C step 6 — `test_github_adapter.py` (the new 306-LOC, 18-test module):**
   - Header docstring enumerates what's tested: import smoke, protocol-method callability, constructor non-network, `_is_name_conflict` classification, nested-namespace guard, exception translation with org/user fallback, and the full `commit_files` git dance against mocks.
   - Module-level helper `_make_github_exc(status, data) -> GithubException` for terse exception construction.
   - **`TestImport`** (2 tests): adapter has `create_project` + `commit_files` as callables; constructor with bogus URL + token does not make a network call.
   - **`TestNameConflictSniffing`** (4 tests): 422 with `errors[0].message == "name already exists..."` → True; 422 with `{"message": "Repository already exists"}` → True (fallback to stringified exception); 500 → False; 422 with unrelated message → False.
   - **`TestExceptionTranslation`** (7 tests): nested namespace raises `RepoClientError`; name conflict raises `RepoNameConflictError` with `.name` set; generic 500 raises `RepoClientError`; org-missing falls back to user and succeeds with full `ProjectInfo` assertions (including the `create_repo` call args); user lookup 500 raises `RepoClientError`; non-404 org-lookup error (e.g. 500) raises `RepoClientError`; `visibility="internal"` passes `private=True`.
   - **`TestCommitFiles`** (5 tests): helper `_wire_happy_path` stubs `get_repo`, `get_git_ref`, `get_git_commit`, `create_git_blob` (side_effect with per-content SHA), `create_git_tree`, `create_git_commit`. **Happy-path test** asserts: `get_repo("acme/foo")` called once; `get_git_ref("heads/main")` called once; `get_git_commit("parent-sha")` called once; `create_git_blob` called with sorted contents (`["x", "y"]` for files `{"b.txt": "y", "a.txt": "x"}`); `create_git_tree` called with 2 elements + `base_tree=parent_commit.tree`; `create_git_commit(message, tree, [parent_commit])`; `ref.edit(sha="commit-sha")`; returned `CommitInfo.sha == "commit-sha"` and `files_committed == ["a.txt", "b.txt"]` (sorted). **Four error-branch tests** verify each failure point in the git dance (repo lookup, blob, tree, ref.edit) raises `RepoClientError`.

9. **Phase C verification (plan §8.4)** — all six commands run at close-out:
    - **PyGithub version**: `uv run python -c "from github import Github; print(Github)"` → `<class 'github.MainClass.Github'>` (version probe via `inspect` confirmed 2.9.1).
    - **Adapter import**: `uv run python -c "from model_project_constructor.agents.website import PyGithubAdapter, PythonGitLabAdapter"` → both classes printed. Both are importable from the package root.
    - **New tests**: `uv run pytest tests/agents/website/test_github_adapter.py -v` → **18 passed** (predicted ~10; actual 18 because I split `TestExceptionTranslation` into 7 granular tests and `TestCommitFiles` into 5 instead of bundling).
    - **Full suite**: `uv run pytest -q` → **313 passed @ 96.55% coverage** (was 295 @ 96.53%; +18 tests, +0.02% coverage). Zero skips, zero xfails.
    - **mypy strict**: `uv run mypy src/model_project_constructor/agents/website/` → `Success: no issues found in 13 source files` (was 12; +1 new adapter).
    - **Coverage floor**: 96.55% ≫ 93% floor. `github_adapter.py` itself is at **97% line coverage** — the uncovered branches are two fallthrough paths in `_is_name_conflict` (e.g. `data` not a dict) that aren't worth synthetic coverage.

### Key Files Shipped in Session 13

**Config (1):**
- `pyproject.toml` — added `"PyGithub>=2,<3"` to `[project.optional-dependencies].agents`

**Source files (2):**
- **NEW** `src/model_project_constructor/agents/website/github_adapter.py` (172 LOC) — `PyGithubAdapter` + module-level `_is_name_conflict` helper
- `src/model_project_constructor/agents/website/__init__.py` — added `PyGithubAdapter` import + `__all__` entry

**Test files (1):**
- **NEW** `tests/agents/website/test_github_adapter.py` (306 LOC) — 18 tests across `TestImport`, `TestNameConflictSniffing`, `TestExceptionTranslation`, `TestCommitFiles`

**Docs (1):**
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewrite for Session 14 + Session 13 handoff + Phase 3A evaluation of Session 12)

**Total: 5 files changed in one feat commit.**

### Gotchas — Read These Before Starting Phase D

**Carryover from Sessions 11/12 that STILL applies to Phase D:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:151-154` is still there**, and manually sets `agent.ci_platform = "gitlab"`. Phase D does NOT touch `WebsiteAgent`. If Phase D ever needs to also construct a `WebsiteAgent` via `__new__` (it shouldn't — tests should use the normal factory), remember to set `ci_platform` manually.
- **`retry_backoff` uses `time.sleep()` in production.** Phase D tests for the CLI should continue to mock at the adapter level (or use `FakeRepoClient`), NOT go through the graph, so `time.sleep` is not an issue.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** But the existing adapters (`PythonGitLabAdapter`, `PyGithubAdapter`) both explicitly inherit from it. That is fine for Protocols when not `@runtime_checkable` — Python allows it as a form of documentation, and mypy strict enforces the real contract. **Correction to Session 12's gotcha:** the note that said "`PyGithubAdapter` should NOT inherit from `RepoClient`" was contradicted by `gitlab_adapter.py:41`. Phase D should simply not worry about this — both patterns (inherit vs don't) work; the codebase has chosen "inherit" twice in a row.
- **`_is_name_conflict` lives in each adapter module separately** (`gitlab_adapter.py:158` and `github_adapter.py:168`). They share no helper code. If Phase D is tempted to factor them into a common helper, **don't** — the two functions inspect platform-specific exception shapes (GitLab: `response_code` + `error_message` dict; GitHub: `.status` + `.data.errors[].message`), and merging would erase the per-platform loose-match logic.

**New Phase D gotchas (from Phase C work):**

- **PyGithub ships `py.typed`.** Phase B's handoff predicted we'd need `# type: ignore[import-untyped]` on the `import github`. **That turned out to be wrong — PyGithub 2.9.1 is fully typed and mypy strict clean.** Phase D should NOT re-add a type-ignore comment. If the CLI lazy-imports `PyGithubAdapter`, the import chain pulls in `github` transparently with no mypy friction.
- **`PyGithubAdapter.__init__` is kwarg-only and defaults `host_url="https://api.github.com"`.** Phase D's CLI should pass `--host-url` (or whatever the flag is called) explicitly only when the user overrides it — otherwise rely on the default. **Contrast:** `PythonGitLabAdapter.__init__` requires `host_url` (no default) because there's no canonical public GitLab host in this codebase. Phase D's adapter-selection branch must account for this asymmetry.
- **`ProjectInfo.id` for GitHub is `"owner/name"`**, for GitLab is `"<integer>"` (stringified). Both are opaque to callers per `protocol.py:19-27`. Phase D's CLI doesn't need to know the difference — it just passes whatever `create_project` returned back into `commit_files`.
- **Nested namespaces are rejected by `PyGithubAdapter` but accepted by `PythonGitLabAdapter`.** If Phase D's CLI exposes a `--namespace` flag, the error messages from each adapter differ: GitLab will try to `groups.get("a/b")` (which might succeed for nested GitLab groups or fail with `GitlabGetError`); GitHub will fail loudly with `RepoClientError("nested namespace ...")`. This asymmetry is by design (plan §8.1 Trap 3). Phase D does NOT need to add a pre-flight check in the CLI — let each adapter decide.
- **The adapter selection branch must lazy-import** both `PyGithubAdapter` and `PythonGitLabAdapter`. Neither `import github` nor `import gitlab` should happen at `cli.py` import time — both should be inside the branch that constructs the concrete adapter. The Phase A work already did this for `PythonGitLabAdapter`; Phase D just needs to match the pattern for `PyGithubAdapter`.
- **`test_github_adapter.py` mocks `adapter._gh` directly** (same pattern as `test_gitlab_adapter.py` with `adapter._gl`). If Phase D's CLI tests need to exercise "`--host github --private-token ...` end-to-end without hitting the network," the cleanest path is to monkeypatch `PyGithubAdapter.__init__` to no-op and then monkeypatch `adapter._gh` — do NOT try to instantiate a real `Github` client with a fake token in a test (PyGithub defers network calls until first API hit, so it won't fail, but it's fragile).
- **Three new dependencies landed transitively via `PyGithub`:** `cryptography`, `pyjwt`, `pynacl`. Phase D does not interact with these but `uv.lock` changed — if Phase D is reviewing its own diff, expect to see lockfile churn from Phase C even though Phase C's commit already includes it.

### Session 11 Handoff Evaluation (by Session 12)
**Score: 10/10.** Best handoff in this workstream so far. Phase B was a pure step-execution session because Session 11 left literally nothing to discover.

- **What helped:** (a) The "Carryover gotchas from Session 10 that STILL apply to Phase B" + "New Phase B gotchas" split was the single most valuable artifact — the `WebsiteAgent.__new__` hack note in `test_retry.py:154` told me exactly how Phase B's new `ci_platform` constructor kwarg would interact with the test (an `AttributeError`, which is exactly what happened on the first test run), so I knew the one-line fix immediately instead of diagnosing it. (b) The "every test file under `tests/agents/website/` touched" enumeration in Session 11 step 11 told me which files would *also* need parametrization in Phase B without a separate audit. (c) The verbatim quote of the user's Session 11 directive (*"raise the unit test coverage floor to 93% at beginning of next session"*) made the standalone `chore:` commit decision unambiguous. (d) The pre-flight baseline numbers (289 @ 96.51%, mypy 12 files) let me detect drift in seconds.
- **What was missing:** Genuinely nothing required for Phase B. The only minor improvement would have been a sentence about the `cast(Literal[...], ...)` pattern needed for tests that take `ci_platform` as a `str` parameter — but that's standard mypy hygiene, not a Phase A quirk. Not deducting.
- **What was wrong:** Nothing. Every claim verified on disk. Pre-flight numbers matched exactly; gotchas all turned out to be live; the `WebsiteAgent.__new__` warning was load-bearing.
- **ROI:** Reading the handoff (~5 min) saved at least 30 min of ghost-debugging the test_retry attribute error and the schema/state plumbing surface. Easily 6× ROI.

### What Session 12 Did
**Deliverable:** Phase B of `docs/planning/github-gitlab-abstraction-plan.md` — `render_github_actions_ci()` sibling renderer + `ci_platform` plumbing through `WebsiteState`/`WebsiteAgent`/`build_governance_files`, `is_governance_artifact` extension for `.github/workflows/ci.yml`, parametrized governance + nodes tests with positive AND negative assertions per platform. Plus standalone coverage-floor bump 90 → 93. **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `e91c9f2` (chore: coverage floor 90 → 93 + Session 12 IN PROGRESS stub), `9b2ab5e` (feat: Phase B — `render_github_actions_ci()` + `ci_platform` plumbing).

**Pre-flight baseline (verified on disk):**
- `uv run pytest -q` → **289 passed, 96.51% coverage**. Matches Session 11 exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**. Matches.
- `git status` → clean on `master`, 16 commits ahead of `origin/master`.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + Session 11 handoff), ran `git status` / `git log --oneline -5` / pre-flight pytest + mypy in parallel, confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "go" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step even though ACTIVE TASK already described the deliverable.**

2. **User said "go" + clarification on README scoping** — the user added "update README.md near end of this session" as scope clarification on top of the existing ACTIVE TASK; treated that as confirmation to proceed with full Phase B + the README touch deferred until after the source/test work was green. Wrote Session 12 IN-PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14).

3. **Step 1 — Coverage floor bump (separate `chore:` commit per Session 11 directive):**
   - `pyproject.toml:60` — `--cov-fail-under=90` → `--cov-fail-under=93`. Single occurrence; no `[tool.coverage.report] fail_under` to update. Verified with `uv run pytest -q` → 289 passed @ 96.51% ≥ 93%.
   - Committed as `chore(coverage): raise pytest coverage floor 90% → 93%` (`e91c9f2`), bundled with the session stub so the audit trail shows both as "infrastructure / not Phase B."

4. **Step 2 — `governance_templates.py` (the renderer + emitter + classifier):**
   - Added `from typing import ... Literal` and a module-level `CIPlatform = Literal["gitlab", "github"]` type alias just below the existing imports.
   - Added `def render_github_actions_ci() -> str:` immediately above `render_pre_commit_config`. YAML shape: top-level `name: ci`, `on: { push: { branches: [main] }, pull_request: { branches: [main] } }`, three jobs (`lint`, `test`, `governance`) on `ubuntu-latest`, each running `actions/checkout@v4` + `actions/setup-python@v5` (Python 3.11) + `pip install uv` + `uv sync` + the stage-specific command (`ruff check .`, `pytest -q`, the `model_registry.json` json-load sanity check). String-literal style mirrors `render_gitlab_ci()` for review-time symmetry.
   - Extended `build_governance_files` signature with `ci_platform: CIPlatform = "gitlab"` keyword parameter. Inside the function, replaced the unconditional `files[".gitlab-ci.yml"] = render_gitlab_ci()` with an `if ci_platform == "gitlab": ... else: files[".github/workflows/ci.yml"] = render_github_actions_ci()` branch. **Did NOT merge the two renderers** per plan §7.3.
   - Extended `is_governance_artifact` to recognize `.github/workflows/ci.yml` alongside `.gitlab-ci.yml` (set-membership check, both classified as governance regardless of which the host produced).
   - Updated `__all__` to export `CIPlatform`, `render_github_actions_ci`, and (for completeness) `render_gitlab_ci`.

5. **Step 3 — `state.py` (TypedDict + initial_state):**
   - Added `Literal` to the import line.
   - Added a new TypedDict field `ci_platform: Literal["gitlab", "github"]` with a 4-line comment explaining that it's independent of the `RepoClient` adapter (so a GitHub project can be scaffolded with `FakeRepoClient` in tests, per plan §7.3).
   - Added `ci_platform: Literal["gitlab", "github"] = "gitlab"` kwarg to `initial_state()` and threaded it into the returned `WebsiteState` dict.

6. **Step 4 — `nodes.py` (`scaffold_governance` reads state and forwards):**
   - Single-line edit: `scaffold_governance` now passes `ci_platform=state.get("ci_platform", "gitlab")` into `build_governance_files`. The `.get(..., "gitlab")` default protects against state dicts written by tests that don't set the field.

7. **Step 5 — `agent.py` (`WebsiteAgent.__init__` accepts the constructor kwarg):**
   - Added `Literal` to the import line.
   - `WebsiteAgent.__init__` signature: `def __init__(self, client: RepoClient, *, ci_platform: Literal["gitlab", "github"] = "gitlab"):`. The kwarg is keyword-only so positional callers (the existing `WebsiteAgent(client)` pattern) still work without modification.
   - Stored as `self.ci_platform` and passed into `initial_state(...)` inside `run()`.

8. **Step 6 — `tests/agents/website/test_retry.py` (the `__new__` hack fix):**
   - The `_run_with_client` helper at line 151 uses `WebsiteAgent.__new__(WebsiteAgent)` to bypass `__init__` and inject a graph with no-op sleep. Adding `ci_platform` to `__init__` meant `agent.ci_platform` was never set, so `agent.run()` raised `AttributeError: 'WebsiteAgent' object has no attribute 'ci_platform'` on all 3 retry tests.
   - **Decision: patched the test, did NOT refactor production code.** Per Session 11's gotcha + Learning #4 from SESSION_RUNNER.md ("don't add a kwarg to production code just for a test-only need"), the hack was already test-only, so the minimal fix is `agent.ci_platform = "gitlab"` immediately after `agent.client = client`. One-line surgical patch. Did not retire the `__new__` hack — it would have required adding an optional `graph` kwarg to production `WebsiteAgent.__init__` for a test-only need, which the gotcha explicitly rejected.

9. **Step 7 — `tests/agents/website/test_governance.py` (parametrize + new tests):**
   - Added `Literal, cast` to the typing import; added `cast(Literal["gitlab", "github"], ci_platform)` inside `_run_agent` so the helper accepts a `str` parameter (which `pytest.mark.parametrize` produces) and forwards a typed value to `WebsiteAgent`. mypy strict required this.
   - `_run_agent` signature extended: `_run_agent(intake, data, *, ci_platform: str = "gitlab")`. Default preserves all existing call sites.
   - Added two new tests inside `TestTier3Moderate`:
     - `test_tier3_ci_platform_branches[gitlab|github]` — exercises the full agent end-to-end with each platform. Asserts both **positive** (`.github/workflows/ci.yml in files` for `"github"`, `.gitlab-ci.yml in files` for `"gitlab"`) AND **negative** (the other CI file is NOT present), per Learning #5. Also asserts `.pre-commit-config.yaml` is always present and that the tier-3 fan-out (`three_pillar_validation.md` etc.) is unaffected by the switch. Final assertion: exactly one of the two CI artifacts ends up in `governance_manifest.artifacts_created`.
     - `test_tier3_ci_artifact_in_manifest[gitlab|github]` — narrower assertion that the platform-specific CI file shows up in `GovernanceManifest.artifacts_created` and the other does not. Pins the classifier behavior independently of the file-list assertion.
   - Parametrized `TestBuildGovernanceFilesUnit.test_tier4_emits_only_always_artifacts` over `ci_platform` — was the only existing test that asserted `".gitlab-ci.yml" in files` directly against `build_governance_files`. Updated to use the parametrized platform with cast, and added negative assertion for the absent CI file.
   - Extended `test_is_governance_artifact_classification` to assert `is_governance_artifact(".github/workflows/ci.yml")` is True alongside the existing `.gitlab-ci.yml` assertion.

10. **Step 8 — `tests/agents/website/test_nodes.py` (extend the build-result test):**
    - Added `import pytest` (was not previously imported in this file).
    - Parametrized `TestBuildRepoProjectResult.test_complete_state_produces_valid_result` over `ci_path: [".gitlab-ci.yml", ".github/workflows/ci.yml"]`. The existing `files_created` mixed list now uses the parametrized value, the corresponding artifact assertion is parametrized, and a new **negative** assertion ensures the OTHER platform's CI file does NOT hallucinate into `artifacts_created` (the classifier could in principle match both — this pins that real `files_created` controls what ends up in the manifest).

11. **Step 9 — Docs:**
    - `README.md` getting-started section: added a paragraph after the existing Phase 4B description explaining that the generated CI file is platform-dependent, that `WebsiteAgent` accepts `ci_platform: Literal["gitlab", "github"]` (default `"gitlab"`), and that Phase D will surface this as a CLI flag.
    - `docs/planning/architecture-plan.md` §8.2: replaced the unconditional `.gitlab-ci.yml` bullet under "Always" with a nested bullet structure: "One CI manifest, selected by `WebsiteAgent(ci_platform=...)`" → `gitlab` default → `.gitlab-ci.yml`, `github` → `.github/workflows/ci.yml`, and a third sub-bullet noting both files are classified as governance artifacts.
    - `docs/planning/architecture-plan.md` §11: rewrote the "Naming note" admonition above the file tree. Old text said "the CI template filename (`.gitlab-ci.yml`) is still GitLab-specific and stays that way until Phase B...adds `.github/workflows/ci.yml`"; new text says Phase B (Session 12) HAS added the GitHub sibling, that the tree shows `.gitlab-ci.yml` because it's the default, that `WebsiteAgent(ci_platform="github")` substitutes the GitHub Actions file, and that the two never coexist in the same generated repo. Updated the inline file-tree comment on the `.gitlab-ci.yml` line to reflect the parenthetical alternative.

12. **Phase B verification (plan §7.4)** — all six commands run at close-out:
    - **Grep 1** (`def render_gitlab_ci|def render_github_actions_ci`): two hits — `governance_templates.py:513` and `:544`.
    - **Grep 2** (`\.github/workflows/ci\.yml|\.gitlab-ci\.yml` in `governance_templates.py`): five hits — module docstring (1), the `if/else` in `build_governance_files` (2), the set-membership in `is_governance_artifact` (2). Both renderer-side and classifier-side covered.
    - **Parametrized governance tests** (`pytest -k "ci_platform"`): 2 passed (the second new test doesn't match the keyword filter; explicit `pytest tests/agents/website/test_governance.py` shows 18 passed including all 4 parametrized cases × 2 tests + the 4 parametrized tier-4 unit cases).
    - **Full suite**: **295 passed @ 96.53% coverage** (was 289, +6 new parametrized cases). Zero skips, zero xfails, zero deletions.
    - **mypy strict**: `Success: no issues found in 12 source files`.
    - **Coverage floor at 93**: explicit `uv run pytest --cov=src/model_project_constructor/agents/website --cov-fail-under=93` passes (96.53% ≥ 93%).
    - **Tier-1/2/3 fake-CLI smoke**: all three print `Status:  COMPLETE`. Tier-3 emits `.gitlab-ci.yml` (default) — the `.github/workflows/ci.yml` path is exercised exclusively by the parametrized tests since the CLI default is GitLab and Phase D will be the first place a CLI user picks it.

### Key Files Shipped in Session 12

**Config (1):**
- `pyproject.toml` — `--cov-fail-under=90` → `--cov-fail-under=93` (commit `e91c9f2`)

**Source files edited (4):**
- `src/model_project_constructor/agents/website/governance_templates.py` — added `CIPlatform`, `render_github_actions_ci`, `ci_platform` param on `build_governance_files`, `.github/workflows/ci.yml` classification, `__all__` updates
- `src/model_project_constructor/agents/website/state.py` — added `ci_platform` TypedDict field + `initial_state` kwarg
- `src/model_project_constructor/agents/website/nodes.py` — `scaffold_governance` forwards `state.get("ci_platform", "gitlab")` to `build_governance_files`
- `src/model_project_constructor/agents/website/agent.py` — `WebsiteAgent.__init__` keyword-only `ci_platform` kwarg, stored as `self.ci_platform`, passed into `initial_state` from `run`

**Test files edited (3):**
- `tests/agents/website/test_governance.py` — parametrized helper + 2 new tier-3 tests + extended tier-4 unit test + extended `is_governance_artifact` test
- `tests/agents/website/test_nodes.py` — added `pytest` import, parametrized `test_complete_state_produces_valid_result` over both CI paths
- `tests/agents/website/test_retry.py` — one-line fix to `__new__` hack helper to set `agent.ci_platform = "gitlab"`

**Docs edited (3):**
- `README.md` — getting-started note about platform-dependent CI file
- `docs/planning/architecture-plan.md` §8.2 + §11 — CI file is now per-`ci_platform`; naming note rewritten to reflect Phase B is done
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewrite for Session 13 + Session 12 handoff + Phase 3A evaluation of Session 11)

**Total: 11 source/test/doc files changed across two commits + the chore commit's 2-file diff.**

### Gotchas — Read These Before Starting Phase C

**Carryover from Session 11 that STILL applies to Phase C:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:151-154` is still there**, and now also manually sets `agent.ci_platform = "gitlab"`. Phase C does not touch `WebsiteAgent`, so this carries forward unchanged. If a future session adds *another* `WebsiteAgent.__init__` attribute, the hack will need *another* manual line — the cost of not refactoring it grows monotonically. Not Phase C's problem.
- **`retry_backoff` uses `time.sleep()` in production.** Phase C does not touch retry, but any new adapter tests that exercise the create→commit happy path through the LangGraph build_website_graph helper would inherit this — Phase C's tests should mock at the `github.Github` level, NOT through the graph, so this is irrelevant in practice.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** Keep it that way. `PyGithubAdapter` should NOT inherit from `RepoClient`; structural conformance is enough. Adapter tests use `callable(getattr(adapter, "create_project"))` patterns.
- **`_is_name_conflict(exc)` in `gitlab_adapter.py:158` loose-matches GitLab's response shape.** `PyGithubAdapter` needs its own equivalent for GitHub's 422 responses — see plan §8.1 hard rule. GitHub returns `github.GithubException` with `.status == 422` and a JSON body containing `errors[0].message == "name already exists on this account"` (or close variants). Mirror the GitLab pattern: a private `_is_name_conflict` helper returning bool, called from `create_project`'s `except` block.

**New Phase C gotchas (from Phase B work):**

- **`CIPlatform` lives in `governance_templates.py`, not `state.py` or `schemas/v1/common.py`.** I considered putting the `Literal` alias in `common.py` per Session 11's gotcha "If Phase B adds a `CIPlatformLiteral` or similar, put it in `schemas/v1/common.py`," but it's only used inside `governance_templates.py` itself (the WebsiteState/Agent layers spell out the Literal inline because they import from `typing`, not from `governance_templates`). If Phase D needs to surface this on the CLI as `--ci-platform`, the right place to centralize the type alias is then, not now — premature centralization would force `state.py` to import from `governance_templates.py` which it currently does not. **Phase C should not need to touch `CIPlatform`.**
- **Two test files now use parametrized `ci_platform`.** Phase C's new `test_github_adapter.py` should NOT parametrize anything over `ci_platform` — adapters are platform-bound by definition. The platform-neutral parametrization is exclusively for `governance_templates` / `WebsiteAgent` / `WebsiteState`.
- **`WebsiteAgent.ci_platform` is a public attribute** (no underscore prefix) because the `__new__` hack in `test_retry.py` sets it directly. If Phase C touches `WebsiteAgent` (it shouldn't), the attribute name must stay `ci_platform`, not `_ci_platform`.
- **Coverage floor is 93%, not 90%.** Phase C's adapter is plain Python with no LangGraph involvement, so coverage of the new file will likely be ~100% if the tests are written carefully (mocked GitHub client + happy-path + 2 error paths). If coverage drops below 93% it's a Phase C quality regression and must be fixed in the same session.
- **The `chore:` coverage bump (`e91c9f2`) is a separate commit from Phase B.** This is the second time in the workstream a non-feature commit was bundled in the same session as a feature commit — both times by user directive. The audit trail looks like `chore: ... → feat: ...`, not `feat: ... + bump`. Phase D may include a similar split if there are doc/CLI bumps that need pre-Phase commits.

### What Session 11 Did
**Deliverable:** Phase A of `docs/planning/github-gitlab-abstraction-plan.md` — neutral rename across 26 files (plan expected 22 + 4 drift/docs) + `project_id: int → str` widening (Trap 1 fix). **COMPLETE.**
**Started:** 2026-04-15
**Completed:** 2026-04-15
**Commits:** `8c00e1a` (single commit containing all Phase A code/test/doc edits + this handoff).

**Pre-flight baseline (verified on disk, not inherited from Session 10's handoff):**
- `uv run pytest -q` → **289 passed, 96.51% coverage, 8.87s wall-clock**. Matches Session 10's claim exactly.
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**. Matches.
- `git status` → clean on `master`, 14 commits ahead of `origin/master`.
- Plan §4 greps re-run against baseline `f97b530`: 22 files for class/type references, 18 files for `gitlab_url|group_path|gitlab_target` field refs, 10 hits for `project_id: int` — matches plan §4.1/§4.2/§4.5 within expected drift.

**Drift found vs plan §4.1 inventory:** `tests/agents/website/test_cli.py` has one comment-only match for `GitLabProjectResult` at line 53 that Session 10 did not catalogue. Resolved by updating the comment to `RepoProjectResult` in the same pass. No other drift.

**What was done (chronological):**

1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + Session 10 handoff), ran `git status` / `git log --oneline -10`, checked `gh issue list` (empty, matches memory), confirmed `~/Development/dashboard.html` exists. Reported findings to user and waited for explicit "go" per failure mode #9 + Learning #10. **Did not skip the report-and-wait step even though ACTIVE TASK already described the deliverable.**

2. **User said "go"** — wrote Session 11 IN-PROGRESS stub to `SESSION_NOTES.md` (Phase 1B ghost-session protection per failure mode #14).

3. **Pre-flight verification** per plan §6.2: ran `uv run pytest -q` + `uv run mypy` + re-ran all three §4 greps. All baselines matched exactly. Spotted the `test_cli.py` drift (one comment hit) and noted it for the rename pass.

4. **Step 1 — Schemas (plan §6.3 step 1):**
   - `git mv src/model_project_constructor/schemas/v1/gitlab.py → schemas/v1/repo.py`. Blame history preserved.
   - Rewrote `repo.py` contents: `GitLabTarget → RepoTarget` (`gitlab_url → host_url`, `group_path → namespace`), `GitLabProjectResult → RepoProjectResult` (`project_id: int → str`). `GovernanceManifest` unchanged — already neutral.
   - Updated `schemas/v1/__init__.py` imports + `__all__`.
   - Updated `schemas/registry.py` keys: `("GitLabTarget", "1.0.0") → ("RepoTarget", "1.0.0")`, `("GitLabProjectResult", "1.0.0") → ("RepoProjectResult", "1.0.0")`.
   - Updated `tests/schemas/fixtures.py` factories: `make_gitlab_target → make_repo_target` (fields renamed), `make_gitlab_project_result → make_repo_project_result` (`project_id="12345"` stringified).
   - Updated `tests/schemas/test_envelope_and_registry.py`: registry-key assertions, `load_payload` test names.
   - `git mv tests/schemas/test_gitlab.py → tests/schemas/test_repo.py` and rewrote contents: `TestGitLabTarget → TestRepoTarget`, `TestGitLabProjectResult → TestRepoProjectResult`, all references to new names.
   - Verification: `uv run pytest tests/schemas/ -q` → **88 passed**. Schemas layer green independently of the website agent.

5. **Step 2 — `protocol.py` (plan §6.3 step 2):** rewrote the module. `GitLabClient → RepoClient`, `GitLabClientError → RepoClientError`, `ProjectNameConflictError → RepoNameConflictError`, `ProjectInfo.id: int → str`, `commit_files(project_id: int) → str`, `create_project(group_path=...) → namespace=...`. Docstring updated to reference "repo host" instead of "GitLab." **Did not add `@runtime_checkable`** per plan §6.3 hard rule.

6. **Step 3 — `fake_client.py` (plan §6.3 step 3):** `FakeGitLabClient → FakeRepoClient`, `FakeProject.group_path → namespace`, `FakeProject.id: int → str`. Storage dict widened from `dict[int, FakeProject]` to `dict[str, FakeProject]`. `_next_id` stays as int internal counter but stringified at storage via `project_id = str(self._next_id)`. Base URL renamed from `"https://fake.gitlab.test"` to `"https://fake.host.test"` — test expectations updated in `test_fake_client.py`.

7. **Step 4 — `gitlab_adapter.py` (plan §6.3 step 4):** class name `PythonGitLabAdapter` **unchanged** (concrete class, GitLab-specific by definition). Imports updated to `RepoClient`, `RepoClientError`, `RepoNameConflictError`. Constructor kwarg `gitlab_url → host_url`. `create_project(group_path=...) → namespace=...`. **Trap 1 bridge:** `ProjectInfo(id=str(project.id), ...)` on the way out of `create_project`; `self._gl.projects.get(int(project_id))` on the way into `commit_files` so python-gitlab still gets the integer it wants. Docstring updated to say "GitLab path" instead of "GitLab only."

8. **Step 5 — `state.py` + `nodes.py` (plan §6.3 step 5):**
   - `state.py`: state key `gitlab_target → repo_target`, `project_id: int → str`, `initial_state()` parameter renamed. TypedDict field rename.
   - `nodes.py`: imports updated. `GitLabClient/GitLabClientError/ProjectNameConflictError → RepoClient/RepoClientError/RepoNameConflictError`. `create_project` node reads `state["repo_target"]` + `target["namespace"]`. `except GitLabClientError → except RepoClientError`. Failure-reason strings: `"gitlab_error:" → "repo_error:"`, `"gitlab_error_retry_exhausted:" → "repo_error_retry_exhausted:"`. `build_gitlab_project_result → build_repo_project_result`; return type `GitLabProjectResult → RepoProjectResult`. `state.get("project_id", 0) → state.get("project_id", "")`.

9. **Step 6 — `graph.py` + `agent.py` + `cli.py` (plan §6.3 step 6):**
   - `graph.py`: docstring ASCII-art "GitLab error" → "repo error"; `client: GitLabClient → RepoClient`; import updated.
   - `agent.py`: full rewrite. `WebsiteAgent.__init__(client: GitLabClient) → RepoClient`. `run(..., gitlab_target: GitLabTarget) → repo_target: RepoTarget` returning `RepoProjectResult`. `_precondition_result` takes `RepoTarget`, returns `RepoProjectResult(project_id="", ...)`. Import from `schemas.v1.repo` instead of `schemas.v1.gitlab`.
   - `cli.py`: full rewrite. Module docstring updated. `DEFAULT_GROUP → DEFAULT_NAMESPACE`, `DEFAULT_GITLAB_URL → DEFAULT_HOST_URL` (value still `"https://gitlab.example.com"`). Flags: `--fake-gitlab → --fake` (with `"--fake-gitlab"` kept as a second name on the same typer.Option for one-window deprecation), `--gitlab-url → --host-url` (with `"--gitlab-url"` alias), `--group-path → --namespace` (with `"--group-path"` alias). typer treats the second name as a secondary long option — both old and new names still work from the CLI, and the Python function param is the new name only. Smoke test with `--fake-gitlab` at close-out confirms this.

10. **Step 7 — `__init__.py` re-exports (plan §6.3 step 7):** rewrote `agents/website/__init__.py` imports and `__all__`. `GitLabClient → RepoClient`, `GitLabClientError → RepoClientError`, `ProjectNameConflictError → RepoNameConflictError`, `FakeGitLabClient → FakeRepoClient`, `build_gitlab_project_result → build_repo_project_result`. `PythonGitLabAdapter` stays. Module docstring updated.

11. **Step 8 — Tests (plan §6.3 step 8):** every test file under `tests/agents/website/` touched:
    - `conftest.py` — fixture `gitlab_target → repo_target`, `fake_client` fixture returns `FakeRepoClient()`. Imports updated.
    - `test_fake_client.py` — class `TestFakeGitLabClient → TestFakeRepoClient`, all method signatures (`group_path → namespace`), `info.id == 1000 → "1000"` (string assertion), `b.id == a.id + 1 → int(b.id) == int(a.id) + 1` (still monotonic but stringified).
    - `test_gitlab_adapter.py` — **filename unchanged** (plan §3.4 rule). Imports updated (`RepoClientError`, `RepoNameConflictError`). Constructor kwargs updated (`host_url=...`). Exception-translation tests updated. `commit_files(project_id=1) → project_id="1"`.
    - `test_agent.py` — fixture names renamed in every test parameter list; assertions updated (`result.project_id == 1000 → "1000"`); docstring `"GitLab"` references updated to "host."
    - `test_nodes.py` — `_FlakyClient` and `_CommitFlakyClient` method signatures updated; `TestBuildGitLabProjectResult → TestBuildRepoProjectResult`; `project_id: "42"` (stringified); `state["project_id"] = 1 → "1"`. Test name `test_non_conflict_gitlab_error_halts → test_non_conflict_repo_error_halts`. Failure-reason assertions: `"gitlab_error" → "repo_error"`.
    - `test_governance.py` — module docstring updated; imports updated; `_run_agent` helper constructs `RepoTarget(host_url=..., namespace=...)` instead of `GitLabTarget(gitlab_url=..., group_path=...)`.
    - `test_retry.py` — `_TransientCommitClient` + `_AlwaysFailingCommitClient` method signatures updated; the `RepoClient` type annotation on `_run_with_client`; `WebsiteAgent.__new__` hack preserved per Session 9's judgment (flagged in Session 10's gotchas, decision reaffirmed). Failure-reason assertion: `"gitlab_error_retry_exhausted" → "repo_error_retry_exhausted"`. `projects: dict[int, Any] → dict[str, Any]`.
    - `test_cli.py` — test `test_cli_requires_fake_gitlab → test_cli_requires_fake_flag`, flag `--fake-gitlab → --fake`, comment `"# JSON blob at the end parses as a GitLabProjectResult dump" → "...RepoProjectResult dump"`.

12. **Step 9 — Docs (plan §6.3 step 9):**
    - `README.md`: phase-table row 4B text stays (it's historical); repo-layout comment on `schemas/v1/` now says "IntakeReport, RepoTarget / RepoProjectResult, governance types"; repo-layout comment on `fake_client.py` says "repo-host stand-in"; repo-layout comment on `cli.py` says "(--fake or --private-token)"; getting-started "Fake GitLab" → "Fake repo host", example flags updated to `--fake`, `--host-url`, `--namespace`, closing paragraph updated with deprecated-alias note.
    - `docs/planning/architecture-plan.md` §4.3: Website Agent responsibility paragraph now says "repository-host project (GitLab today, GitHub via Phase C of the abstraction plan)" with a naming-note admonition pointing to `github-gitlab-abstraction-plan.md`. Inputs list: `GitLabTarget → RepoTarget`. Outputs list: `GitLabProjectResult → RepoProjectResult` with the `project_id: str` explanation. Failure-modes table: "GitLab API error" → "Repo host API error", "GitLab project name conflict" → "Repo project name conflict."
    - `docs/planning/architecture-plan.md` §5.4: full code block replacement. New section heading `### 5.4 RepoTarget and RepoProjectResult`. Admonition explaining the rename and the `int → str` widening. Pydantic class definitions rewritten with new names and `project_id: str`.
    - `docs/planning/architecture-plan.md` §11: section heading "Generated GitLab Repo Structure" → "Generated Repository Structure" with a naming-note admonition explaining that the CI template filename is still GitLab-specific until Phase B adds the GitHub sibling.

13. **Phase A verification (plan §6.4)** — all eight commands run at close-out:
    - **Grep 1** (`GitLabClient|GitLabTarget|GitLabProjectResult|GitLabClientError|ProjectNameConflictError|FakeGitLabClient|build_gitlab_project_result|gitlab_target` across `{src,tests}/**/*.py`): **0 hits**.
    - **Grep 2** (`gitlab_url|group_path` across `{src,tests}/**/*.py`): **0 hits**.
    - **Grep 3** (`project_id\s*:\s*int` across `{src,tests}/**/*.py`): **0 hits**.
    - **pytest**: `289 passed @ 96.51% coverage`. Zero skips, zero xfails added, zero tests deleted.
    - **mypy strict**: `Success: no issues found in 12 source files`.
    - **Coverage floor**: holds at 96.51% ≥ 90% (`--cov-fail-under=90` passes; Phase A did not touch any uncovered lines).
    - **Tier-1/2/3 fake-CLI smoke tests**: all three print `Status:  COMPLETE` when invoked with `--fake`.
    - **Deprecated `--fake-gitlab` alias**: prints `Status:  COMPLETE` (hidden alias works, no typer errors).

**Verification notes:**
- No intermediate `uv run pytest` inside the rename pass — plan §6.3 says intermediate runs are "ideal but not mandatory," and the final full-suite run was clean.
- `uv run mypy` was NOT run between every substep; mypy is strict enough that it would flag any incomplete rename, but the compiler feedback would have been noisier than one final pass. The final pass returned Success so no intermediate state was inconsistent.

### Key Files Shipped in Session 11

**Files renamed (git mv preserves blame):**
- `src/model_project_constructor/schemas/v1/gitlab.py` → `schemas/v1/repo.py`
- `tests/schemas/test_gitlab.py` → `tests/schemas/test_repo.py`

**Source files rewritten/edited (13):**
- `src/model_project_constructor/schemas/v1/__init__.py` — re-exports
- `src/model_project_constructor/schemas/registry.py` — registry keys
- `src/model_project_constructor/agents/website/__init__.py` — re-exports + `__all__`
- `src/model_project_constructor/agents/website/protocol.py` — the rename center
- `src/model_project_constructor/agents/website/fake_client.py` — `FakeRepoClient`
- `src/model_project_constructor/agents/website/gitlab_adapter.py` — imports + type widen + `int(project_id)` bridge
- `src/model_project_constructor/agents/website/graph.py` — `RepoClient` type annotation + docstring
- `src/model_project_constructor/agents/website/nodes.py` — every call site + `build_repo_project_result`
- `src/model_project_constructor/agents/website/state.py` — `repo_target`, `project_id: str`
- `src/model_project_constructor/agents/website/agent.py` — `WebsiteAgent.run` signature + `_precondition_result`
- `src/model_project_constructor/agents/website/cli.py` — CLI flags + deprecated aliases

**Test files edited (10):**
- `tests/schemas/fixtures.py` — factories
- `tests/schemas/test_envelope_and_registry.py` — registry keys
- `tests/agents/website/conftest.py` — `repo_target` + `FakeRepoClient` fixtures
- `tests/agents/website/test_fake_client.py` — `TestFakeRepoClient`
- `tests/agents/website/test_gitlab_adapter.py` — **filename kept**, contents updated
- `tests/agents/website/test_agent.py` — fixture param renames + string `project_id` assertions
- `tests/agents/website/test_nodes.py` — `TestBuildRepoProjectResult` + `_FlakyClient` signatures
- `tests/agents/website/test_governance.py` — `_run_agent` helper + imports
- `tests/agents/website/test_retry.py` — transient-client signatures + failure reasons
- `tests/agents/website/test_cli.py` — `--fake` flag + test name + comment

**Docs edited (3):**
- `README.md` — getting-started + repo-layout
- `docs/planning/architecture-plan.md` — §4.3, §5.4, §11
- `SESSION_NOTES.md` — this file (ACTIVE TASK rewrite + Session 11 handoff)

**Total: 26 files changed, 2 renames, net +~50 / -~50 LOC** (rename is content-preserving within files).

### Gotchas — Read These Before Starting Phase B

**Carryover gotchas from Session 10 that STILL apply to Phase B:**

- **`WebsiteAgent.__new__` hack in `test_retry.py:154` is still there.** Session 11 did NOT fix it (plan §6 hard rule: rename only). Phase B touches `WebsiteAgent.__init__` to add the `ci_platform` kwarg — this is a natural place to refactor the constructor to accept an optional `graph` kwarg and retire the `__new__` hack **IF** the refactor is one line and obvious. If it's not obvious, leave the hack. Production code should not grow a kwarg just for a test-only need (Learning #4 from SESSION_RUNNER.md).
- **`retry_backoff` uses `time.sleep()` in production.** Any new retry-path tests must inject `sleep=lambda _s: None`. Phase B does not touch retry, but parametrized governance tests that somehow exercise the retry path must follow this rule.
- **`RepoClient` Protocol is NOT `@runtime_checkable`.** Keep it that way. Adapter tests use `callable(getattr(...))`.
- **`GovernanceManifest.artifacts_created` is derived from `files_created` via `is_governance_artifact`**, not stored. Phase B's extension of `is_governance_artifact` to recognize `.github/workflows/ci.yml` changes the manifest output for any repo that emits the GitHub CI file.
- **`_is_name_conflict(exc)` loose-matches GitLab response codes** (`gitlab_adapter.py:158`). Phase B does not touch this. Phase C's `PyGithubAdapter` needs its own equivalent for GitHub's 422 responses.

**New Phase B gotchas (from Phase A work):**

- **`WebsiteState.project_id` is now `str`**, not `int`. Any test state dict in `test_nodes.py` that Phase B adds MUST use `"42"` not `42`. mypy strict catches this.
- **`FakeRepoClient.projects` is `dict[str, FakeProject]`.** Dict lookup uses the string `project_id` returned by `create_project`. Phase B tests that index into `fake_client.projects` directly must pass a string key.
- **`cli.py` uses typer multi-name aliases** (`typer.Option("--fake", "--fake-gitlab", ...)`) rather than hidden second flags. This means **both names appear in `--help` output**. If Phase B wants to hide the deprecated alias from help, it needs a different mechanism (typer has `hidden=True` but then both options need to be separate Options — more code). Session 11's judgment: acceptable for one deprecation window, since Phase D will remove the old names. Session 12 should NOT change this unless explicitly asked.
- **`DEFAULT_HOST_URL = "https://gitlab.example.com"`** in `cli.py:39`. This is a GitLab URL even though the variable name is neutral. Phase D (not Phase B) will change this default when the `--host` flag lands, since the default host needs to match the default platform.
- **`schemas/v1/__init__.py`'s `__all__` list** now has `RepoProjectResult`, `RepoTarget`, `GovernanceManifest` in alphabetical-ish order under a `# repo` comment. If Phase B adds a `CIPlatformLiteral` or similar, put it in `schemas/v1/common.py` — NOT `repo.py` — because it's not host-specific.
- **The `project_id="12345"`** literal in `tests/schemas/fixtures.py:182` is intentionally stringified. Don't "fix" it back to int.
- **`test_gitlab_adapter.py` filename is unchanged** — it tests the concrete GitLab adapter, not the neutral Protocol. Phase C will add `test_github_adapter.py` as a sibling. Do not rename `test_gitlab_adapter.py` for symmetry — the plan §6.1 is explicit.

### Session 10 Handoff Evaluation (by Session 11)

**Score: 10/10.**

- **What helped (specific):**
  - **The plan document at `docs/planning/github-gitlab-abstraction-plan.md` itself** was the single highest-value artifact. Session 11's rename was almost mechanical — every file to touch was listed in §4, every execution step was numbered in §6.3, every verification command was ready to run in §6.4. I never had to invent a step or guess a name. The plan's 720 lines paid for themselves within the first 20 minutes of Phase A execution.
  - **The three traps documentation (§2.2)** was the part that made this session possible. Trap 1 (`project_id: int`) is not something I would have found on my own in the rename pass — the compiler doesn't complain about widening an `int` field to `str` if the call sites never rely on the numeric value. Session 10 caught it by reading `gitlab_adapter.py:111 id=int(project.id)` during evidence-gathering, and the plan flagged it as a bundled fix for Phase A. Without that, Phase A would have left a latent bug for Phase C to discover the hard way.
  - **The naming table in §3.4** was the exact source of truth for every rename. I referenced it constantly during Steps 2-7. Having current/proposed/lives-in/notes in one table meant zero ambiguity.
  - **The rename-vs-parallel-schema decision (§3)** was well-argued. I did not second-guess the choice at any point. §3.2's "front-loaded cost" framing is what kept me from splitting the rename across two sessions when it hit 26 files.
  - **The per-phase DONE criteria (§6.1)** let me know I was done. I ran each verification command against §6.4 expected output and got a binary green/not-green answer for each. No judgment calls about "is this enough."
  - **The Session 9 gotchas block that Session 10 preserved in their own handoff** — I used the `WebsiteAgent.__new__` hack note, the `@runtime_checkable` rule, and the retry-sleep injection pattern all in this session. Session 10's handoff block was the right length: long enough to be actionable, short enough to read.
  - **The "hard rules for Phase A" in Session 10's ACTIVE TASK** (lines 73-80) gave me explicit permission to ignore the things I noticed. When I saw `test_cli.py` had one stray `GitLabProjectResult` comment, I updated it (in-scope drift). When I noticed the `WebsiteAgent.__new__` hack, I left it alone (out-of-scope per Session 10's gotcha explicitly). The hard rules saved me from scope creep decisions.
  - **The two learnings Session 10 added** (#8 grep inventory separation + #9 single-document plan) were background knowledge I used implicitly when reading the plan's §4 grep inventory — separate patterns per classifier group means I could verify each pattern independently without a single conflated count.

- **What was missing (minor):**
  - **No `pyproject.toml` coverage-floor note.** The plan mentions coverage stays ≥ 90% (matching the floor) but Session 11 learned at the end that the user wanted 93%. This is not Session 10's fault (the user's directive came mid-Session-11), but a pre-emptive "check the coverage floor matches Session N+1 ambitions" habit would be nice for future planning docs.
  - **The `test_cli.py` drift** (one comment hit) was a mild miss in the plan's §4.1 inventory. Session 10 ran the greps but the inventory table in §4.1 listed 8 test files and my run surfaced 11 hit files — `test_cli.py` was absent. It was a comment-only hit so trivial to fix, but the plan could have used a sentence saying "if a grep turns up more files than the inventory, the extras are in-scope drift — fix them in the same pass."
  - **Plan §6.3 step 6** (CLI with deprecated aliases) says "keep deprecated `--fake-gitlab`, `--gitlab-url`, `--group-path` aliases as hidden flags." Session 11 implemented them as **typer multi-name secondary options**, which means they appear in `--help` output. Hiding a typer option requires a second Option with `hidden=True`, which doubles the code. Session 11's judgment: the `--help` visibility is acceptable for one deprecation window. If the user wanted strictly hidden aliases, the plan should have been explicit about typer's multi-name vs hidden-option tradeoff. Not a blocker; Phase D removes all three aliases anyway.

- **What was wrong:** nothing. Every factual claim I verified against disk matched. Baseline commit `f97b530`, 289 tests, 96.51% coverage, 12 mypy-clean files, 22-file class-refs footprint, 18-file field-refs footprint, 10-hit `project_id: int` footprint — all accurate.

- **ROI:** Reading the plan document took ~15 minutes across two Read calls. It saved at least 2 hours of grep-and-guess work that a planless rename would have cost. The §3.4 naming table + §6.3 execution order + §6.4 verification block together constitute ~60% of the plan's value; the other 40% is the traps documentation + do-not-change list. Plan documents with this level of detail should be the norm for any multi-file refactor.

### Session 11 Self-Assessment

**Score: 9/10** (Session 12 will score independently).

- **What went well:**
  - **All §6.4 verification commands passed on first try** after Step 9 (docs). Zero red-then-green cycles. mypy strict stayed consistent across substeps because the rename was done in dependency order (schemas → protocol → fake client → adapter → state/nodes → graph/agent/cli → tests).
  - **Zero test deletions, zero skips, zero xfails added.** 289 → 289. Coverage 96.51% → 96.51%. The rename preserved every behavioral assertion.
  - **Blame history preserved** via `git mv` for both `schemas/v1/gitlab.py → repo.py` and `tests/schemas/test_gitlab.py → test_repo.py`. Future `git blame` on `RepoTarget.visibility` will show the original `"internal"` default with its Phase-4B justification.
  - **Trap 1 bundled cleanly.** `ProjectInfo.id: int → str` + `commit_files(project_id: int) → str` + `state["project_id"]: int → str` + test stringification + `gitlab_adapter.py` `str(project.id)` / `int(project_id)` bridge all landed in the same pass. No orphan integer typing.
  - **Test drift (`test_cli.py`)** caught by running the grep myself at pre-flight, not by plan inspection. This is the right direction: trust plans for structure, trust greps for reality.
  - **Deprecated flag aliases work.** `--fake-gitlab` smoke test at close-out confirms a user who never read the changelog can still run their Phase 4B scripts after Phase A.
  - **No scope creep.** I did not fix the `WebsiteAgent.__new__` hack, did not touch the LangGraph topology, did not rename `PythonGitLabAdapter`, did not start Phase B despite Phase A finishing under the 2-hour estimate. Session boundary preserved.
  - **Docs updated in the same commit** as code, per plan §6.3 step 9. README + architecture-plan.md §§4.3/5.4/11 all reflect the new names with explicit naming-note admonitions so future readers aren't confused by §11's GitLab-specific `.gitlab-ci.yml` reference.
  - **Two user-interaction check-ins handled correctly:**
    - Early "1" message → stopped, asked for clarification, did not guess.
    - Later "raise coverage floor to 93%" directive mid-close-out → acknowledged, recorded in Session 12 ACTIVE TASK as the first action, did not interrupt Phase A execution to act on it (that would have bundled a coverage-floor change into a rename commit).
  - **TaskCreate/TaskUpdate discipline.** 13 tasks created at start, each marked `in_progress` at start and `completed` at end. Zero stale tasks at close-out.

- **What I could have done better:**
  - **Pre-flight verification ran AFTER writing the IN-PROGRESS stub, not before.** Plan §6.2 says pre-flight before Phase 1B. I wrote the stub first (because failure mode #14 says stub first) and ran pre-flight second. If pre-flight had failed, the stub would have been a false claim. In practice pre-flight passed, but the order is wrong and should be: (Phase 0 reads) → (pre-flight verification) → (Phase 1B stub) → (execute). Session 12 should reorder.
  - **I did not run `uv run pytest tests/schemas/ -q` between substeps as aggressively as plan §6.3 suggests.** I ran it once after Step 1 (schemas) and got 88 passing, then batched Steps 2-7 without another intermediate run. The final pytest was clean so this saved time, but if Step 5 (nodes.py) had left a broken mypy state, I'd have spent more time bisecting. Acceptable tradeoff for this session; judgment call.
  - **The `--fake-gitlab` deprecation alias question** (hidden vs multi-name typer option) was not flagged to the user. I made a judgment call and moved on. A more careful session would have surfaced the tradeoff in the handoff before implementing. I've documented it now in the gotchas above so Session 12 can revisit if needed.
  - **The architecture-plan.md §11 update** is a one-line admonition pointing to Phase B; I didn't rewrite the `.gitlab-ci.yml` bullet itself. A more aggressive session would have added a parenthetical `(or .github/workflows/ci.yml after Phase B)` to the bullet. Not strictly necessary — Phase B will do that in its own doc pass — but a close reader of §11 today might not notice the admonition at the top.
  - **I did not run `uv run pytest tests/schemas/ -q` AFTER the schemas rename had every caller updated** — I ran it after Step 1 (before nodes.py was updated). At that point the schemas tests pass in isolation but the website tests are broken. If Session 12 wants truly "green between substeps," the order should be: schemas → protocol → fake client → adapter → state/nodes → run pytest → graph/agent/cli → run pytest → init → run pytest → tests → run pytest. Session 11 chose to batch and run once at the end.
  - **The handoff block is long** (~700 lines between ACTIVE TASK and this self-assessment). Session 10's handoff was also ~700 lines and scored 10/10, so length alone is not a defect. But a session-by-session trend toward longer handoffs is a warning sign (protocol erosion, failure mode #17). If Session 12 finds this handoff unwieldy, they should feel free to trim earlier sessions' verbose logs.

### Session 11 Learnings for `SESSION_RUNNER.md`

Add to the Learnings table (suggested entries 11-12):

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 11 | Run pre-flight verification BEFORE Phase 1B stub, not after. The stub is a claim about the state of the session; pre-flight is what makes that claim true. If pre-flight fails, the stub is a false claim in persistent storage. Correct order: Phase 0 reads → pre-flight verification → Phase 1B stub → execute. | Session 11 | Any implementation session where the plan specifies a pre-flight step. |
| 12 | When a plan's grep-based inventory lists N files and a re-run surfaces N+k files, the k extras are **in-scope drift** — fix them in the same pass, don't escalate. Re-run the grep at pre-flight, not just during planning, because the codebase drifts between plan-date and exec-date. Session 11's `test_cli.py` comment-only hit was caught this way. | Session 11 | Any implementation session executing a plan with a file-level inventory. |

### Followups Session 11 did NOT do (deliberate)

- **Fix the `WebsiteAgent.__new__` hack in `test_retry.py`.** Out of scope for Phase A (rename only). Phase B touches `WebsiteAgent.__init__` and can consider retiring the hack if the refactor is obvious.
- **Rename `test_gitlab_adapter.py`.** It tests the GitLab-specific concrete adapter. Plan §6.1 is explicit.
- **Remove deprecated CLI aliases.** Phase D removes them. Plan §3.4 is explicit.
- **Update `docs/planning/architecture-approaches.md`.** Historical alternatives document; out of scope per plan §4.7 + §1.2.
- **Update `SESSION_NOTES.md` historical session blocks (Sessions 1-10).** Retroactive rewrite is out of scope per plan §4.7.
- **Raise `pyproject.toml` coverage floor from 90 to 93.** User directive came mid-close-out; deferred to Session 12 as the first action so it lands in a separate commit from Phase A. See the Session 12 ACTIVE TASK above.
- **Start Phase B.** One-phase-per-session rule. Failure mode #18.



### What Session 10 Did
**Deliverable:** `docs/planning/github-gitlab-abstraction-plan.md` — multi-phase plan to adapt the Website Agent for GitHub **or** GitLab targets, per `SESSION_RUNNER.md` Planning Sessions protocol. **COMPLETE.**
**Started:** 2026-04-14
**Completed:** 2026-04-15
**Commits:** `f44f8dc` (single commit containing the plan doc + this handoff + the SESSION_RUNNER.md Learnings additions).

**What was done (chronological):**
1. **Phase 0 orientation** — read `SAFEGUARDS.md` in full, `SESSION_NOTES.md` lines 1-200 (ACTIVE TASK + start of Session 9 handoff), ran `git status` / `git log --oneline -10` / `gh repo view` / dashboard file check. Confirmed baseline: master clean, 12 commits ahead of origin, last session = Session 9 commit `f97b530`, dashboard exists externally at `~/Development/dashboard.html`. Reported findings to user, waited for direction. **Did not skip the report-and-wait step even though the ACTIVE TASK block already described the deliverable** (failure mode #9, task-in-prompt bypass).
2. **User clarifications** — user explained the Session 9 user notes originally came from a `/btw` (by-the-way) question whose response was truncated, losing point #1. Session 10 offered three options for handling the missing point (reconstruct, proceed without, re-run /btw). User asked for a "more detailed solution" — i.e., do deeper research on the question rather than pick a quick answer.
3. **Evidence-gathering pass** — before touching any planning text, read `protocol.py` / `schemas/v1/gitlab.py` / `gitlab_adapter.py` / `cli.py` / `nodes.py` / `agent.py` / `governance_templates.py` (lines 505-665 and 780-814) to ground the plan in actual code rather than inherited Session 9 notes. This is the step that found the three traps (Trap 1: `project_id: int`; Trap 2: multi-file commit asymmetry; Trap 3: nested groups vs flat orgs) — none of which were in Session 9's user notes.
4. **First detailed response to user** — wrote a ~400-line conversational solution covering: the 80/20 state of the abstraction boundary, the three traps, the live grep counts (188/52/111/32 hits across the symbol groups), the rename-vs-parallel recommendation, and a candidate 4-phase sequence. Offered the user an open question: bundle the `int→str` widening into Phase A or split it out.
5. **User chose bundling** — confirmed Option 1 (bundle widening into Phase A). Session 10 acknowledged and paused before any code/doc work to wait for explicit "go."
6. **User said "go"** — Session 10 resumed with Phase 1B: wrote the "(IN PROGRESS)" stub to `SESSION_NOTES.md` BEFORE any research or writing. Ghost-session protection per failure mode #14. (Earlier tool call to write the stub was rejected by the user; the correct sequence was confirm-Option-1 → explicit-go → stub → work.)
7. **Source read pass** — parallel-read `state.py`, `fake_client.py`, `graph.py`, `agents/website/__init__.py`, `schemas/v1/__init__.py`, `schemas/registry.py`, `tests/agents/website/conftest.py`. This completed the file-level picture needed for the plan's "do not change" list and execution order. Found `WebsiteState.project_id: int` at `state.py:32` — confirmed Trap 1 propagates through state and not just the Protocol.
8. **Full grep inventory with line numbers** — ran 5 batched greps with `-n`: (a) class/type references, (b) field names, (c) CI template + adapter, (d) cross-cutting helpers, (e) `project_id:` type footprint. The first batch (188 hits, 22 files) was large enough that ripgrep's output overflowed 30KB and was persisted to disk; Session 10 read the persisted file to get the complete listing. Total line-numbered citations in the plan: ~170 grep hits across 22 source-and-test files + 4 doc files.
9. **Architecture-plan section reads** — parallel-read `docs/planning/architecture-plan.md` §§4.3 (lines 183-215), 5.4 (347-376), 8.2 (506-557), 11 (665-725), 14 Phase 4/5 (884-931). Captured exact line-number anchors for every cross-reference in the plan document.
10. **pyproject.toml check** — grep'd `python-gitlab|PyGithub|optional-dependencies` to confirm `agents` extras list. Found `python-gitlab>=4` on `pyproject.toml:23`, no `PyGithub` entry yet — Phase C will add it.
11. **Docs impact grep** — ran `grep` across `*.md` for `GitLabTarget`, `GitLabClient`, `.gitlab-ci.yml`, `python-gitlab`, `PyGithub`. Found: `README.md` (12 hits, ~8 substantive), `docs/planning/architecture-plan.md` (already mapped), `docs/planning/architecture-approaches.md` (historical — out of scope), `SESSION_NOTES.md` (out of scope — session history). No collisions with the new `RepoTarget`/`RepoClient`/`host_url`/`PyGithubAdapter`/`.github/workflows` names.
12. **Plan document written** — `docs/planning/github-gitlab-abstraction-plan.md`, ~720 lines, 16 sections. Structure: scope (§1), current state (§2), three traps detailed (§2.2), strategic decision with rationale (§3), naming table (§3.4), full grep inventory (§4.1-§4.8), per-phase specs (§6-§9 for Phases A/B/C/D), do-not-change list (§10), Phase 5 ordering decision (§11), provenance of missing point #1 (§12), open questions (§13), close-out protocol for executor sessions (§14), risk register (§15), single-document rationale (§16).
13. **Cross-reference cleanup** — post-write, grep'd the plan for `§\d` and found five stale references from an earlier section numbering (§7.1 where §4.6 or §6 was meant). Fixed all five with targeted Edits. Re-ran the grep to confirm no broken references remain.
14. **ACTIVE TASK rewrite** — replaced the ~80-line Session 10 planning mandate with a ~70-line Session 11 Phase A execution mandate. New block names Phase A as the deliverable, lists the 22-file footprint, links to plan §4/§6/§10 for details, and restates the hard rules (no partial rename, no Phase B bundling, no Phase 5 interleave).
15. **Session 10 handoff** — this entry. Full evaluation of Session 9's handoff, self-assessment, learnings for `SESSION_RUNNER.md`, Session 11 rubric.

**Verification (what I ran against the written plan):**
- `wc -l docs/planning/github-gitlab-abstraction-plan.md` → ~720 lines (up from ~712 after the 5 cross-reference fixes).
- `grep -n '§\d' docs/planning/github-gitlab-abstraction-plan.md` → all references resolve to existing sections of either this plan or `architecture-plan.md`. No orphan references.
- `grep -n '^## \d\|^### \d' docs/planning/github-gitlab-abstraction-plan.md` → 17 top-level `##` sections and 24 `###` subsections, matching the intended table of contents.
- **Session 10 did NOT run `uv run pytest`, `uv run mypy`, or any code-affecting command.** Planning sessions are read-only with respect to `src/` and `tests/`. The baseline test count (289) and coverage (96.51%) are inherited from Session 9's handoff, not re-verified.
- **Session 10 did NOT touch any file under `src/` or `tests/`.** Verified by `git status` at close-out time (will be clean except for the plan doc + SESSION_NOTES.md + SESSION_RUNNER.md).

**Input from Session 10 user: provenance of the missing point #1.** User confirmed the Session 9 notes came from a `/btw` question — "what can be done to allow this project's product to use either GitHub or GitLab?" — whose response was truncated. Point #1 is irrecoverable without re-running the question. User approved Session 10's reconstruction: *"The `GitLabClient` Protocol in `agents/website/protocol.py` is already the adapter boundary. Rename to `RepoClient`, widen `ProjectInfo.id` from `int` to `str`, and let the adapter pattern absorb the rest."* This reconstruction lives in plan §12 with explicit "reconstructed, not verbatim" framing; if the user ever regenerates the original response, plan §12 should be updated with the real text.

### Key Files Shipped in Session 10

**One new file:**
- `docs/planning/github-gitlab-abstraction-plan.md` — the plan. **Session 11 MUST read this in full before starting Phase A.** It is the authoritative source of scope, execution order, verification commands, and DONE criteria. The ACTIVE TASK block above is an abbreviated pointer, not a replacement.

**Three modified files:**
- `SESSION_NOTES.md` — ACTIVE TASK block rewritten for Session 11 Phase A; this Session 10 handoff added; Session 9 through Session 1 unchanged.
- `SESSION_RUNNER.md` — Learnings table appended with entries 7, 8, 9 (see "Session 10 Learnings" below).

**Zero files under `src/` or `tests/` touched.** Verified by `git status` at close-out.

### Gotchas — Read These Before Starting Phase A

**Phase A execution gotchas (new for Session 11):**
- **The `schemas/v1/gitlab.py` → `schemas/v1/repo.py` move MUST use `git mv`.** Blame history is the only record of why certain field defaults were chosen (see `gitlab.py:17` `visibility: Literal["private", "internal", "public"] = "private"` — the "internal" value is GitLab-specific and matters for the Trap 3 discussion). Losing blame because of a plain-text rename is a cost Session 11 should not pay.
- **`schemas/registry.py:30-31` uses string keys that will break the envelope tests.** `tests/schemas/test_envelope_and_registry.py:97-98, 106-107` pin the string keys `"GitLabTarget"` and `"GitLabProjectResult"` directly. Phase A updates the registry entries AND those tests in the same commit, otherwise the test suite goes red between substeps.
- **`python-gitlab.projects.get(project_id)` expects an integer.** After Phase A widens `project_id: int → str`, the adapter in `gitlab_adapter.py:125` must do `int(project_id)` on the way in, not `project_id` directly. Same for the fake client — `fake_client.py:100` does `self.projects[project_id]` on a dict whose keys are integers. After widening, either stringify the dict keys or convert on lookup. Recommend the latter (minimal disturbance to test fixtures that seed `FakeProject(id=1000)`).
- **`FakeGitLabClient` → `FakeRepoClient` is NOT just a class-name change.** The docstring at `fake_client.py:1-10` mentions "GitLab stand-in" — update to "repo stand-in." `test_fake_client.py:13` has `class TestFakeGitLabClient` that also renames. The `FakeProject` dataclass keeps its name (neutral enough).
- **`tests/agents/website/test_gitlab_adapter.py` keeps its filename.** It tests the GitLab-specific `PythonGitLabAdapter` and should remain named for what it tests. The imports inside the file update (`GitLabClient` → `RepoClient`, etc.) but `git mv` is NOT used.
- **The `WebsiteAgent.__new__` hack in `test_retry.py` (flagged in Session 9's handoff) is NOT fixed by Phase A.** It's a test-only workaround for `WebsiteAgent.__init__` always building its own graph. Phase A might incidentally refactor `WebsiteAgent.__init__` to accept a `graph` kwarg — but that's a production-code change for a test-only benefit, and Session 9's judgment was "leave it." Session 11 should preserve that judgment unless the rename pass makes `WebsiteAgent.__init__` a natural change site anyway.
- **The plan's §6.3 execution order is NOT mandatory — just recommended.** mypy strict may or may not stay green between substeps depending on the order of edits; if Session 11 finds a better order, follow it. The invariant is: at close-out, all 289 tests pass, mypy is clean, and every grep in §6.4 returns the expected zero hits.
- **The deprecated CLI flag aliases (`--fake-gitlab`, `--gitlab-url`, `--group-path`) are one-release-window only.** Phase A adds them as hidden aliases; Phase D removes them. If a user between Phase A and Phase D runs an old script, they get a silent accept (hidden flag works) and no deprecation warning (intentional — a `typer` hidden flag doesn't emit one). If Session 11 wants louder deprecation (e.g. a `stderr` write), note it for Phase D. Not blocking.
- **Coverage floor is 90%** (`pyproject.toml` — verified during Phase 0 of Session 10). Baseline is 96.51%. Phase A should not change coverage meaningfully — rename only. If coverage drops below 95%, something's off and Session 11 should investigate rather than lower the gate.

**Carryover from Session 9 that still applies to Phase A:**
- **`retry_backoff` uses `time.sleep()` in production.** Any new retry-path tests Phase A adds (none expected, but just in case) must inject `sleep=lambda _s: None`.
- **`build_repo_project_result` (the renamed `build_gitlab_project_result`) only populates `model_registry_entry` when BOTH `project_name` AND `project_slug` are in state.** The behavior doesn't change; the test assertions in `test_nodes.py:350` that pin `model_registry_entry == {}` on failed-early states keep passing.
- **`GovernanceManifest.artifacts_created` is derived from `files_created` via `is_governance_artifact`**, not stored. Phase A doesn't touch this logic; it's a Phase B concern (add `.github/workflows/ci.yml` recognition).
- **`is_governance_artifact` is prefix/literal based.** Phase A doesn't change its recognized set. Phase B does.
- **`_is_name_conflict(exc)` loose-matches GitLab response codes.** Phase A doesn't change the matching — only the error type it raises (`ProjectNameConflictError` → `RepoNameConflictError`).
- **The `GitLabClient` Protocol (renamed to `RepoClient`) is NOT `@runtime_checkable`.** Keep it that way. Adapter tests use `callable(getattr(...))`.
- **`PythonGitLabAdapter` constructor does not make a network call.** `test_gitlab_adapter.py:46` pins this. After Phase A, that assertion should still hold — the rename doesn't touch constructor behavior.

### Session 9 Handoff Evaluation (by Session 10)

**Score: 10/10.**

- **What helped (specific):**
  - **The verbatim `/btw` notes block** (Session 9 handoff lines 135-152 of pre-edit SESSION_NOTES.md) was the single most valuable piece of the handoff. Session 10 used all four listed points (2-5) as the scaffold for the plan and none were discarded. Session 9's discipline of recording the notes verbatim rather than paraphrasing or acting on them was exactly the right call.
  - **The "Key Files Shipped Through Phase 4B" inventory** (lines 172-202) pointed Session 10 at `render_gitlab_ci()` as "the single function that needs a parallel `render_github_actions_ci()`." Session 10 used this directly as the center of Phase B in the plan, saving ~15 minutes of grep work.
  - **The gotchas block** (lines 203-244) flagged `is_governance_artifact` needs updating for `.github/workflows/ci.yml`, which became a Phase B DONE criterion in the plan (§7.1). The same block flagged that python-gitlab DOES ship type stubs but PyGithub may not — Session 10 wrote this concern into the plan's §8.2 pre-flight for Phase C.
  - **The `_is_name_conflict(exc)` description** ("400/409 + lowercase 'already been taken' substring") was reused nearly verbatim as the pattern for the PyGithub adapter's name-conflict detection in plan §8.1 (GitHub returns 422 with "name already exists" — same loose-match approach).
  - **The do-NOT-change list** (lines 147-151) was preserved word-for-word in the plan's §10. Session 10 added five more invariants (the `sleep` injection pattern, the accumulator across four scaffold nodes, the precondition guard, the `website::` thread_id prefix, GovernanceManifest shape) but did not weaken or remove any of Session 9's original items.
  - **The evaluation rubric** at lines 307-316 was the explicit checklist Session 10 worked from. All eight rubric items are addressed in the plan. The rubric's existence — not just its content — is what made Session 10's self-scoring possible before writing the handoff.
  - **The `WebsiteAgent.__new__` hack documentation** (line 207) told Session 10 exactly what test-time construction workaround exists and why, so Session 10 could decide whether Phase A should fix it (decision: no — documented in the gotchas above).
  - **The "Session 9 Exercised Phase 4B" narrative** (lines 246-256) was the template for Session 10's own "What was done (chronological)" section above. Session 9's structure is now the benchmark.

- **What was missing (minor, and not Session 9's fault):**
  - **Trap 1** (`project_id: int` protocol-level type mismatch between GitLab's integer IDs and GitHub's string `owner/name`). Session 9 wrote the `gitlab_adapter.py:111 id=int(project.id)` line but didn't flag that it's GitHub-incompatible. Session 10 found this by re-reading `protocol.py` during Phase 0 evidence-gathering.
  - **Trap 2** (multi-file commit asymmetry: GitLab's one-shot `commits.create` vs GitHub's 4-call blob/tree/commit/ref dance). Session 9's handoff said "parallel GitHub adapter should stay equally thin" (line 176), which is *wrong* — PyGithub physically cannot implement `commit_files` in one call. This is a bigger-deal omission than Trap 1 because it affects Phase C's LOC estimate by ~2x.
  - **Trap 3** (GitLab nested groups `data-science/model-drafts` vs GitHub flat owner `acme/repo`). Session 9 didn't flag that `cli.py:36 DEFAULT_GROUP = "data-science/model-drafts"` is a nested path unresolvable on GitHub.
  - **None of these are Session 9's fault.** They are gaps in the user's truncated `/btw` response, which Session 9 captured faithfully. Session 9 was not asked to design the abstraction — it was asked to finish Phase 4B and record the user's mid-session notes. It did both correctly.

- **What was wrong:** nothing. Every factual claim Session 10 verified matches. Commit hash `f97b530`, 88 website tests, 289 total tests, 96.51% coverage, 12 files mypy-clean, `python-gitlab` ships type stubs, `@runtime_checkable` NOT applied to the Protocol — all accurate and all still true on disk at session start.

- **ROI:** Reading Session 9's handoff took ~10 minutes (it's the longest one yet). It saved at least 30 minutes of what would otherwise have been re-derivation work. The verbatim `/btw` notes plus the gotchas block plus the rubric were the three highest-value sections — they shaped the plan's scope, the plan's Phase B/C design, and Session 10's self-assessment respectively. Session 9's handoff is the new benchmark for this project alongside Session 8's.

### Session 10 Self-Assessment

**Score: 9/10** (Session 11 will score independently).

- **What went well:**
  - **Plan document is complete and evidence-based.** 720 lines, 16 sections, covering all 8 items on Session 9's evaluation rubric. Grep inventory lists every file with line numbers pulled from ripgrep, not from architectural guessing. 22-file rename footprint is a real count, not an estimate.
  - **Three traps caught during evidence-gathering** that Session 9's handoff and the user's `/btw` notes missed: `project_id: int` (Trap 1), multi-file commit asymmetry (Trap 2), nested group vs flat org (Trap 3). Each trap is documented in plan §2.2 with concrete mitigation folded into the right phase.
  - **Explicit recommendation without hedging.** Plan §3.2 picks option A (neutral rename) and justifies it with the 22-file blast radius + the Phase 5 orchestrator ordering argument. No "we could go either way" language.
  - **Per-phase DONE criteria, pre-flight, execution order, verification commands, session boundary** for all four phases (§§6-9). Each phase can be closed out independently, each has explicit rollback guidance.
  - **Phase 5 ordering decision explicit in §11.** The plan commits to deferring Phase 5 until Phase D closes, with the "doubled rename cost" argument. No ambiguity for Session 11+.
  - **Strict adherence to failure mode #18.** Zero `src/` or `tests/` edits. Plan is the only deliverable. The temptation to "just fix the cross-references I noticed" in `architecture-plan.md §14` was resisted — it goes into Phase A's execution order (step 9, docs pass) and Session 11 owns it.
  - **Phase 1B stub written** before any research or writing. When the user rejected the first stub-write attempt (after "Option 1"), Session 10 paused, asked for clarification, and re-tried after explicit "go." This is the textbook handling of the "user interrupted tool use" case.
  - **Cross-reference hygiene.** Post-write grep for `§\d` caught five stale references to an earlier section numbering. All five fixed before commit. The plan is internally consistent.
  - **Parallel tool use** — Phase 0 orientation, source reads, grep inventory, and architecture-plan section reads each batched into single messages with 5-8 parallel calls. ~30 minutes of sequential work compressed to ~8 minutes of wall-clock.
  - **Provenance captured explicitly.** The missing point #1 from the `/btw` response isn't hidden — §12 of the plan names the reconstruction, §13 lists it as an open question, and the user can update the plan if they regenerate the original response. Session 10 did not silently infer.

- **What I could have done better:**
  - **Did not re-run `uv run pytest -q` at session start** to confirm the 289/96.51% baseline against current disk state. Took Session 9's handoff at its word because the branch is clean and the commit is pinned. Low-value rigor for a planning session but a protocol gap that Session 11 inherits (Session 11 should run it in Phase 0).
  - **Did not verify PyGithub API names** (`create_git_blob`, `create_git_tree`, `InputGitTreeElement`, `repo.get_git_ref`) against current PyGithub ≥2 documentation. They are accurate per my training cutoff; if PyGithub 2.x renamed them, Phase C's executor will hit an `AttributeError` and have to look them up. Acceptable risk for a plan document; would be a blocker for code.
  - **The plan is long (720+ lines).** A future reader may find the single-document structure heavy. §16 addresses this but the legitimate tradeoff argument for splitting into four phase-specific docs is acknowledged and not chosen.
  - **The `uv run mypy` intermediate-state claim in §6.3** ("mypy must keep passing between substeps if possible") is optimistic and unverified. In practice, some intermediate states may fail mypy strict until the full pass completes. Session 11's executor will find out. Not a deal-breaker for Phase A — the invariant is only at close-out.
  - **Did not draft the plan in an `EnterPlanMode` session** despite being explicitly asked to write a plan. `EnterPlanMode` would have enforced read-only discipline more strictly. I relied on manual SAFEGUARDS adherence instead. Acceptable because the session stayed read-only in practice, but using the mode would have been a belt-and-braces choice.
  - **One sub-rigor item:** didn't run `git stash list` to check for local stash entries beyond the working-tree-clean `git status`. Very low-probability concern but a protocol gap.

- **Why not 10:** The skipped baseline `pytest` run, the unverified PyGithub API names, and the optimistic mypy-intermediate-state claim are three unforced errors that would each have taken <5 minutes to address. None are blocking. None change the plan's content. But together they justify -1 from what would otherwise be a clean 10/10.

### Session 10 Learnings (added to `SESSION_RUNNER.md` Learnings table)

| # | Learning | When to apply |
|---|----------|---------------|
| 7 | When the user provides a partially-captured message as input (e.g. a truncated `/btw` response), proactively reconstruct the missing content based on the visible evidence AND document the reconstruction with explicit provenance ("originally from /btw on <date>, point #N lost to truncation, reconstructed by Session X from <evidence>"). Do NOT silently infer or silently ignore the gap. Offer the user a "regenerate vs proceed" choice before committing, then honor their preference. | Any session where the input is referenced as partially missing or explicitly truncated. |
| 8 | A grep-based inventory for a rename plan must include the TYPE, FIELD, STATE KEY, and DOCSTRING surfaces separately — each has a different grep pattern. Conflating them into one total gives misleading counts. List hits per grep pattern + per file, not a single total. | Any rename/migration plan. |
| 9 | When writing a multi-phase plan, put cross-phase invariants (do-not-change lists, strategic decisions, Phase N ordering) in ONE document rather than duplicating them across phase-specific documents. Duplication causes drift: one phase doc gets a correction and the others don't. Single-document trades navigability for consistency; for 4-phase plans with 3+ shared invariants the tradeoff favors consistency. | Any plan with more than 2 phases sharing ≥3 invariants. |
| 10 | During Phase 0, when the user's first message appears to contain a task (e.g. "go"), do NOT skip the orientation report even if the ACTIVE TASK block describes the deliverable. The report exists for the user's benefit — it establishes shared state before any work begins. Failure mode #9 ("task-in-prompt bypass") is the specific risk. Complete all 8 Phase 0 steps, report, and explicitly wait for direction even when the direction feels implicit. | Every session. |

### How Session 11 Will Be Evaluated

Session 11's handoff will be scored by Session 12 on:

1. **Did Session 11 execute Phase A of the plan and STOP, or did it bundle Phase B?** (Phase A is ONE session. Failure mode #18 is the specific risk for Session 11.)
2. **Did Session 11 read `docs/planning/github-gitlab-abstraction-plan.md` in full before starting, or only the ACTIVE TASK summary?** (The plan is the authoritative source; the ACTIVE TASK block is a pointer.)
3. **Did Session 11 re-run the plan's §4 grep inventory against the current disk state during Phase 0?** If the inventory drifted (new files reference `GitLabTarget` landed between `f97b530` and Phase A start), did the executor update the plan in the same commit or close out and re-plan?
4. **Did all 7 verification commands in plan §6.4 pass at close-out?** Specifically: zero hits for old names, `project_id: int` gone from annotations, 289 tests passing, mypy strict clean, coverage ≥95%, fake CLI smoke tests pass for tier 1/2/3, deprecated `--fake-gitlab` alias still works.
5. **Did Session 11 land a complete rename in one commit (or a tight commit series), or is the tree in a partial state?** Partial renames are worse than no rename — see plan §6.5 rollback guidance.
6. **Did Session 11 preserve every invariant in plan §10?** Specifically: LangGraph topology, retry/backoff, governance fan-out, FakeGitLabClient internals (logic, not class name), GovernanceManifest shape, Phase 4A accumulator pattern, `sleep` injection, precondition guard, `website::` thread_id prefix.
7. **Did Session 11 widen `project_id: int → str` everywhere it's annotated?** Including `schemas/v1/gitlab.py:32`, `state.py:32`, `protocol.py:55`, `fake_client.py:95,110`, `gitlab_adapter.py:119`, `nodes.py:204,330`, `agent.py:94`, and every test site.
8. **Did Session 11 update `schemas/registry.py` AND `tests/schemas/test_envelope_and_registry.py:97-107` in the same commit?** (The registry keys are string literals pinned by those tests.)
9. **Did Session 11 use `git mv` for the `schemas/v1/gitlab.py` → `repo.py` rename?** (Blame history preservation.)
10. **Did Session 11 add deprecated CLI flag aliases (`--fake-gitlab`, `--gitlab-url`, `--group-path`) for Phase D to remove, or silently drop them?** (Plan §6.1 requires the aliases.)

A handoff missing specific file line-numbers, concrete before/after grep counts, or the Phase A verification command output will score ≤6/10. A handoff that names "Phase A complete" without listing which files were touched will score ≤4/10.


### What Session 9 Did
**Deliverable:** Phase 4B of architecture plan — Website Agent governance scaffolding (§8.2 tier fan-out) + `RETRY_BACKOFF` self-loop off `INITIAL_COMMITS` + thin `python-gitlab` production adapter behind the `GitLabClient` Protocol. **COMPLETE.**
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `f97b530` (Phase 4B).

**What was done (chronological):**
1. Phase 0 orientation — read `SAFEGUARDS.md`, `SESSION_NOTES.md` top block, plan §4.3 / §5.4 / §8 / §10 / §11 / §14 Phase 4B, and the full Phase 4A `agents/website/` package (state, protocol, nodes, graph, agent, templates, fake_client, cli, __init__) + Phase 4A tests.
2. Phase 1B — wrote Session 9 stub to `SESSION_NOTES.md` before any code change (ghost-session protection per failure mode #14).
3. **state.py** — added `governance_paths: list[str]`, `commit_attempts: int`, `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0`. Docstring explains that `files_pending` is now an accumulator across *four* scaffold nodes. `initial_state()` seeds `governance_paths=[]` + `commit_attempts=0`.
4. **governance_templates.py (NEW, 600 lines)** — sibling to `templates.py`, pure-Python f-string generators. Exports `build_governance_files`, `build_analysis_files`, `build_test_files`, `build_model_registry_entry`, `build_regulatory_mapping`, `is_governance_artifact`. Internal helpers: `_tier_at_least(risk_tier, threshold)` for `tier_N+` predicates (lower severity number = more severe), `_CYCLE_CADENCE` dict mapping cycle_time → monitoring cadence (§8.3), `_FRAMEWORK_ARTIFACTS` mapping SR_11_7 / NAIC_AIS / EU_AI_ACT_ART_9 / EU_AI_ACT / ASOP_56 → the governance artifacts that satisfy each. The composition entry point `build_governance_files` emits:
   - **Always:** `governance/model_registry.json`, `governance/model_card.md`, `governance/change_log.md`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, one `data/datasheet_<query>.md` per primary query.
   - **Tier 3+ (tier 3 moderate, 2 high, 1 critical):** `governance/three_pillar_validation.md`, `governance/ongoing_monitoring.md` (embeds §8.3 cadence), `governance/deployment_gates.md`.
   - **Tier 2+ (tier 2 high, 1 critical):** `governance/impact_assessment.md`, `governance/regulatory_mapping.md` (populated from the framework→artifact table filtered to what's actually being emitted).
   - **Tier 1 only:** `governance/lcp_integration.md`, `governance/audit_log/README.md`.
   - **If `affects_consumers`:** `governance/eu_ai_act_compliance.md` (Articles 9–15 mapping).
   - `build_analysis_files`: emits `analysis/fairness_audit.qmd` + `src/<slug>/fairness/__init__.py` + `src/<slug>/fairness/audit.py` if `uses_protected_attributes`, else `{}`.
   - `build_test_files`: emits `tests/test_fairness.py` if `uses_protected_attributes`, else `{}`.
   - `is_governance_artifact(path)` classifier used by `build_gitlab_project_result` to filter `files_created` down to the manifest's `artifacts_created`.
5. **nodes.py (rewritten)** — added `scaffold_governance`, `scaffold_analysis`, `scaffold_tests` nodes (merge into `files_pending`; `scaffold_analysis`/`scaffold_tests` return `{}` when the fairness flag is off). `initial_commits` now increments `commit_attempts`, returns `status="RETRYING"` + `commit_attempts=N` on `GitLabClientError` when `attempts < MAX_COMMIT_ATTEMPTS`, returns `status="FAILED"` with `failure_reason="gitlab_error_retry_exhausted: ..."` past the limit. Added `retry_backoff` node that calls an injected `sleep(delay)` where `delay = RETRY_BASE_DELAY_SECONDS * 2 ** (attempts - 1)` (1s → 2s → 4s) and resets status to `PARTIAL`. New `route_after_commit(state)` routes `RETRYING → retry_backoff`, everything else → `end`. `make_nodes(client, *, sleep=_default_sleep)` — the `sleep` kwarg is the ONLY way tests stub out wall-clock delay; production uses `time.sleep`. **`build_gitlab_project_result` was rewritten to populate the manifest**: filters `files_created` via `is_governance_artifact`, computes `regulatory_mapping` via `build_regulatory_mapping(frameworks=..., emitted_paths=set(artifacts_created))`, populates `model_registry_entry` via `build_model_registry_entry(...)` — BUT only when `project_name` + `project_slug` are present in state (failed-early FAILED states default the entry to `{}`).
6. **graph.py (rewritten)** — new topology inserts `scaffold_governance → scaffold_analysis → scaffold_tests` between `scaffold_base` and `initial_commits`, and adds the `initial_commits → retry_backoff → initial_commits` self-loop via `add_conditional_edges` + `route_after_commit`. `build_website_graph(client, *, checkpointer=None, sleep=None)` — the new `sleep` kwarg is forwarded into `make_nodes` so retry tests can build a graph that returns immediately from `retry_backoff`.
7. **gitlab_adapter.py (NEW)** — `class PythonGitLabAdapter(GitLabClient)`. Constructor takes `gitlab_url`, `private_token`, optional `ssl_verify`; stores `self._gl: Any = gitlab.Gitlab(...)`. `create_project` resolves `self._gl.groups.get(group_path)` then `self._gl.projects.create({...})`, translating `GitlabCreateError` with `_is_name_conflict(exc)` → `ProjectNameConflictError`, other `GitlabError` subclasses → `GitLabClientError(...)`. `commit_files` does `self._gl.projects.get(project_id)` then `project.commits.create({'branch': ..., 'commit_message': ..., 'actions': [{'action': 'create', 'file_path': p, 'content': c}, ...]})`. `_is_name_conflict(exc)` checks `response_code in (400, 409)` and a loose lowercase match for "already been taken" or "already exists". **python-gitlab DID ship type stubs**, so `# type: ignore[import-untyped]` is unnecessary — removed them after the first mypy run flagged them as `unused-ignore`.
8. **cli.py** — dropped the Phase-4A-only `--fake-gitlab`-required guard. Now accepts either `--fake-gitlab` (free, no token) OR `--private-token <token>` (real path via `PythonGitLabAdapter`). Lazy-imports the adapter inside the `if not fake_gitlab:` branch so the fake path stays free of the `gitlab` import at module load time. Exit code 2 on neither flag being set, same as before.
9. **__init__.py** — re-exported `PythonGitLabAdapter`, `build_governance_files`, `build_analysis_files`, `build_test_files`, `build_model_registry_entry`, `build_regulatory_mapping`, `is_governance_artifact`, `route_after_commit`, `MAX_COMMIT_ATTEMPTS`, `RETRY_BASE_DELAY_SECONDS`.
10. **Fixtures:** wrote `tests/fixtures/tier1_intake.json` (tier 1 critical personal auto renewals model — affects_consumers=true, uses_protected_attributes=true, cycle_time=continuous, 4 frameworks including `EU_AI_ACT_ART_9`) and `tests/fixtures/tier2_intake.json` (tier 2 high commercial property reserving aid — affects_consumers=false, uses_protected_attributes=false, cycle_time=strategic, 2 frameworks). Both round-trip cleanly through `IntakeReport.model_validate_json`. The existing `subrogation_intake.json` serves as tier 3.
11. **test_governance.py (NEW, 29 tests across 4 classes)** — `TestTier1Critical` / `TestTier2High` / `TestTier3Moderate` exercise the three fixtures end-to-end through `WebsiteAgent` + `FakeGitLabClient`, pinning (a) exact file set presence/absence for each tier's fan-out, (b) manifest `regulatory_mapping` contents against the declared frameworks, (c) monitoring-cadence text in `governance/ongoing_monitoring.md` for `continuous` / `strategic` / `tactical`. `TestBuildGovernanceFilesUnit` covers `build_governance_files` with a synthetic tier-4 intake (only "always" artifacts emitted), datasheet-per-query, regulatory-mapping unknown-framework passthrough, and the `is_governance_artifact` classifier.
12. **test_retry.py (NEW, 5 tests)** — `_TransientCommitClient` and `_AlwaysFailingCommitClient` stand-ins. `TestRetryBackoffNode` pins the exact `[1.0, 2.0, 4.0]` backoff sequence by injecting a `sleep` lambda that appends to a list, plus the status-reset-to-PARTIAL behavior. `TestRetryEndToEnd` builds a graph with `sleep=lambda _s: None`, passes it a `_TransientCommitClient(fail_count=2)` and asserts COMPLETE after 3 commit calls; `fail_count=1` → COMPLETE after 2 commit calls; `_AlwaysFailingCommitClient()` → FAILED with `gitlab_error_retry_exhausted` after exactly 3 commit calls. **The retry end-to-end tests use `WebsiteAgent.__new__(...)` + manual attribute assignment to pass the custom-sleep graph**, because `WebsiteAgent.__init__(client)` always builds a default graph. This is a minor test-only hack worth considering for refactoring in Session 11 (`WebsiteAgent(client, *, graph=...)` kwarg). Not blocking for now.
13. **test_gitlab_adapter.py (NEW, 9 tests)** — import smoke test, `PythonGitLabAdapter` has `create_project` + `commit_files` as callables, constructor does NOT make a network call (`PythonGitLabAdapter(gitlab_url="https://invalid.example.invalid", private_token="not-a-real-token")` succeeds silently because python-gitlab defers auth until first API call), `_is_name_conflict` classification for 400/409/500 + matching/non-matching messages, and `TestExceptionTranslation` uses `MagicMock` to stub `adapter._gl` so the four adapter code paths (group lookup → create → commit → commit success) can be exercised without the network. **Note:** `isinstance(adapter, GitLabClient)` would raise because the protocol is not `@runtime_checkable` — the test uses `callable(getattr(adapter, "create_project"))` instead. Do NOT add `@runtime_checkable` to the protocol just to simplify the test; it's fine as-is.
14. **test_agent.py** — replaced `test_governance_artifacts_absent_in_4a` with `test_tier3_governance_artifacts_present`, which is a POSITIVE assertion over the tier-3-gated artifact set for the subrogation fixture, including manifest regulatory-mapping contents (`"SR_11_7" in mapping` and the tier-3 artifacts it binds to). `test_governance_manifest_reflects_intake_tier` still asserts tier/cycle_time mirror intake — it survived unchanged because it only pinned the empty mapping-equals-empty behavior implicitly, which is no longer true now but the test doesn't assert that.
15. **test_nodes.py** — `test_commit_failure_surfaces` → `test_first_commit_failure_goes_to_retrying` (new semantics: status=RETRYING + commit_attempts=1 on first failure). `test_complete_state_produces_valid_result` rewritten with a mixed `files_created` list (base + governance + fairness paths) and now asserts (a) only governance paths land in `artifacts_created`, (b) `model_registry_entry["model_id"] == "subrogation_recovery_model"`, (c) `regulatory_mapping["SR_11_7"]` contains `"governance/three_pillar_validation.md"`. `test_failed_state_defaults_governance` got one extra assertion on `model_registry_entry == {}`.
16. **README.md** — phase table: Phase 4B → Complete. Repo layout section lists `governance_templates.py`, `gitlab_adapter.py`, and the updated CLI help. Test count 260 → 289. Added `tier1_intake.json` + `tier2_intake.json` to the fixtures list. Getting-started section now shows BOTH the `--fake-gitlab` path and a real `--private-token` example, and mentions the tier-1 fixture as the path to see the full governance fan-out.
17. **SESSION_RUNNER.md** — Phase 0 step 5 now says "Run the shared methodology dashboard (external to this repo — lives in `~/Development/`, not inside `model_project_constructor/`)" instead of pointing at an in-repo file that doesn't exist. User confirmed the shared dashboard runs from the parent dir, not this repo.

**Verification (plan §14 Phase 4B literal commands):**
- `uv run pytest tests/agents/website/ -v` → **88 passed** (was 59 in Phase 4A; 29 new tests — 20 governance, 5 retry, 9 adapter, −5 removed/replaced). Output shows `test_governance.py` with `TestTier1Critical`, `TestTier2High`, `TestTier3Moderate`, `TestBuildGovernanceFilesUnit` classes all green.
- `uv run pytest -q` full suite → **289 passed, 96.51% coverage, 0 failures**. Required coverage gate (90%) is satisfied with headroom. Per-file coverage for the new modules: `governance_templates.py` 97%, `nodes.py` 99%, `graph.py` 100%, `state.py` 100%, `gitlab_adapter.py` 85% (remaining gaps are the generic `except GitlabError` catch-alls that aren't stubbed in tests; acceptable per "no live network tests" guidance).
- `uv run mypy src/model_project_constructor/agents/website/` → **Success: no issues found in 12 source files**.
- **Manual tier-1 CLI smoke test:** `uv run python -m model_project_constructor.agents.website --intake tests/fixtures/tier1_intake.json --data tests/fixtures/sample_datareport.json --fake-gitlab` → status COMPLETE, commit sha `acf00f6b48de13ca1a09b1b196f0e3d961fd4e57`, file tree includes `governance/audit_log/README.md`, `governance/eu_ai_act_compliance.md`, `governance/lcp_integration.md`, `analysis/fairness_audit.qmd`, `src/intake_renewals_001/fairness/audit.py`, `tests/test_fairness.py`. Plan's DONE criterion "Manual: generate one tier-1 project and verify all expected governance files exist" = satisfied.

**Input from Session 9 user: GitHub/GitLab abstraction notes (verbatim for Session 10 planning):**

> the next session will add a plan to adapt this for use with GitHub or GitLab. See these notes:
>
> 2. Terminology mismatch in the schema: `GitLabTarget` has `gitlab_url` and `group_path`. Either rename to a neutral `RepoTarget` with `host_url` + `namespace`, or add a parallel `GitHubTarget` schema. The neutral rename is cleaner but touches `schemas/v1/gitlab.py` and every consumer — including the CLI and tests. For a minimal change, keep `GitLabTarget` as-is and treat `group_path` as "org name" when the GitHub adapter is in use.
>
> 3. `.gitlab-ci.yml` → `.github/workflows/ci.yml`. The `render_gitlab_ci()` template in `governance_templates.py` emits GitLab CI YAML. For GitHub projects you'd branch on the client type (or add a `ci_platform` parameter to `build_governance_files`) and emit GitHub Actions YAML instead. The `.pre-commit-config.yaml` template is platform-agnostic and needs no change.
>
> 4. Dependency: add `PyGithub` to the `agents` optional extras alongside `python-gitlab>=4`.
>
> 5. Tests: a `test_github_adapter.py` with import smoke test only — same discipline as `gitlab_adapter.py` (no live network tests).
>
> What NOT to change:
> - The LangGraph topology, retry/backoff loop, governance fan-out, `FakeGitLabClient` (it's already platform-agnostic — rename to `FakeRepoClient` if you want, but not required).
> - `GovernanceManifest`, `GitLabProjectResult` — the "GitLab" in the name is vestigial; the shape works for any git host.
>
> Effort estimate: ~1 session. The adapter + CI template branching is the bulk of it; the real cost is deciding whether to rename `GitLabTarget`/`GitLabProjectResult` to neutral names now (cheap during Phase 4B, expensive once Phase 5 orchestrator lands and hardcodes the names).

(Note from Session 9: the user's numbering starts at 2 — point 1 wasn't included in the message. Session 10 may want to ask the user for it, or proceed without it if the remaining notes are self-contained.)

### Session 10's mandate (PLANNING session — plan is the deliverable, not code)

Session 10 writes `docs/planning/github-gitlab-abstraction-plan.md`. Per `SESSION_RUNNER.md` Planning Sessions protocol, the plan must include:

1. **Grep-based inventory** of every reference that would need to change under either approach (neutral rename vs. parallel schema). At minimum, grep for: `GitLabTarget`, `GitLabProjectResult`, `GovernanceManifest`, `GitLabClient`, `GitLabClientError`, `ProjectNameConflictError`, `PythonGitLabAdapter`, `gitlab_url`, `group_path`, `python-gitlab`, `gitlab_ci`, `.gitlab-ci.yml`, `render_gitlab_ci`, `FakeGitLabClient`. List every matching file with line numbers.
2. **Decision: neutral rename or parallel schema?** The user's notes suggest the neutral rename is cleaner but more churn. Session 10 should make a recommendation AND document the trade-off explicitly with the grep inventory as evidence. DO NOT hedge — pick one and justify it.
3. **Per-phase breakdown** with explicit DONE criteria and verification commands per `SESSION_RUNNER.md`. Candidate phases:
   - Phase A: (if renaming) neutral schema rename — `GitLabTarget` → `RepoTarget`, `GitLabClient` → `RepoHostClient`, etc. Touches schemas, protocol, nodes, graph, agent, templates (governance), CLI, fake_client, gitlab_adapter, all tests, README. One session.
   - Phase B: `ci_platform` parameter (or client-type branching) in `build_governance_files`, new `render_github_actions_ci()` generator, tests for the GitHub CI path. One session.
   - Phase C: `PyGithubAdapter` implementing the (renamed) client protocol via `PyGithub`. Import smoke tests + exception translation via MagicMock, no live network. One session.
   - Phase D: Update CLI to accept `--host github|gitlab` and route to the right adapter. Add `test_github_cli.py` analogue. One session.
4. **Explicit "DO NOT change" list** echoing the user's notes — the topology, retry/backoff loop, governance fan-out, manifest shape, `GitLabProjectResult` structural contract (the field `governance_manifest` stays; only its type name may change).
5. **Answer the Session 5/Phase 5 ordering question.** The user implied Phase 5 is deferred until the abstraction plan lands. Session 10 should confirm that ordering in the plan so Session 11+ executes abstraction work BEFORE orchestrator work. If Session 10 disagrees with the ordering, it must argue the case explicitly in the plan.
6. **Ask the user for the missing point #1** from their notes above before finalizing the plan, OR explicitly document that the plan proceeds without it.

**Session 10 MUST NOT start implementing the abstraction.** Per failure mode #18 (planning-to-implementation bleed), the plan is a separate deliverable. Commit the plan, close out, STOP. Session 11 picks up Phase A of the plan.

### Key Files Shipped Through Phase 4B — Read Before Starting Session 10

**Phase 4B additions (new in Session 9):**
- `src/model_project_constructor/agents/website/governance_templates.py` — sibling to `templates.py`. **Session 10 grep this module first**: its `render_gitlab_ci()` emits GitLab CI YAML; that's the single function that needs a parallel `render_github_actions_ci()` per the user's note #3. `_FRAMEWORK_ARTIFACTS` at the top is static and platform-agnostic (stays untouched by the abstraction). `is_governance_artifact()` classification is also platform-agnostic.
- `src/model_project_constructor/agents/website/gitlab_adapter.py` — `PythonGitLabAdapter(GitLabClient)`. The `_is_name_conflict(exc)` helper is adapter-internal; the GitHub adapter will need its own equivalent (PyGithub raises `github.GithubException` with status 422 for name conflicts — IIRC; Session 10 should verify, not assume). Adapter does NOT do retry internally — that's the graph's job. Keep it that way; parallel GitHub adapter should stay equally thin.
- `src/model_project_constructor/agents/website/nodes.py` — rewritten for Phase 4B. `make_nodes(client, *, sleep=_default_sleep)`: the `sleep` kwarg is the injection point for retry tests. `build_gitlab_project_result`: now populates manifest from `files_created` via `is_governance_artifact` filter + `build_regulatory_mapping` + `build_model_registry_entry`. **The `model_registry_entry` is empty unless `project_name` AND `project_slug` are in state** — failed-before-naming states get `{}`.
- `src/model_project_constructor/agents/website/graph.py` — rewritten. New edges: `scaffold_base → scaffold_governance → scaffold_analysis → scaffold_tests → initial_commits`, plus the `initial_commits ⟶ retry_backoff ⟶ initial_commits` self-loop via `route_after_commit`. `build_website_graph(client, *, checkpointer=None, sleep=None)` — the `sleep` kwarg is forwarded into `make_nodes` (test-only injection).
- `src/model_project_constructor/agents/website/state.py` — new fields `governance_paths: list[str]`, `commit_attempts: int`. Constants `MAX_COMMIT_ATTEMPTS = 3`, `RETRY_BASE_DELAY_SECONDS = 1.0`. `initial_state()` seeds them.
- `src/model_project_constructor/agents/website/__init__.py` — public surface expanded; `PythonGitLabAdapter`, the governance helpers, `is_governance_artifact`, and the retry constants are all re-exported. Session 10 can import from the package root.
- `src/model_project_constructor/agents/website/cli.py` — updated: `--fake-gitlab` OR `--private-token`. The real-adapter path lazy-imports `gitlab_adapter` so the fake path doesn't touch python-gitlab at import time.

**Phase 4B tests (new in Session 9):**
- `tests/agents/website/test_governance.py` — 20 tests total. `TestTier1Critical` (4), `TestTier2High` (3), `TestTier3Moderate` (2), `TestBuildGovernanceFilesUnit` (4). Uses three JSON fixtures; no LLM involvement.
- `tests/agents/website/test_retry.py` — 5 tests. Uses `_TransientCommitClient` + `_AlwaysFailingCommitClient` stand-ins and an injected `sleep` lambda. **The end-to-end tests build `WebsiteAgent` via `__new__` + manual attribute assignment** to pass a graph with a no-op sleep — this is a minor test-only hack and a candidate for `WebsiteAgent(client, *, graph=...)` refactor if a future session needs it.
- `tests/agents/website/test_gitlab_adapter.py` — 9 tests. Import smoke test + `_is_name_conflict` classification + `TestExceptionTranslation` using MagicMock to stub `adapter._gl`. **Zero network calls.** Session 10's GitHub adapter tests should follow the same pattern (MagicMock the `github.Github` client).

**Phase 4B test updates:**
- `tests/agents/website/test_agent.py` — removed `test_governance_artifacts_absent_in_4a`; added `test_tier3_governance_artifacts_present` with positive manifest assertions.
- `tests/agents/website/test_nodes.py` — `test_commit_failure_surfaces` → `test_first_commit_failure_goes_to_retrying`; `test_complete_state_produces_valid_result` rewritten with mixed base+governance file list.

**Phase 4B fixtures (new):**
- `tests/fixtures/tier1_intake.json` — tier_1_critical personal auto renewals, affects_consumers=true, uses_protected_attributes=true, cycle_time=continuous, 4 frameworks (SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, ASOP_56). Exercises every conditional branch in `build_governance_files`.
- `tests/fixtures/tier2_intake.json` — tier_2_high commercial property reserving, affects_consumers=false, uses_protected_attributes=false, cycle_time=strategic, 2 frameworks (SR_11_7, ASOP_56). Exercises tier-2-only artifacts in isolation.
- `tests/fixtures/subrogation_intake.json` — unchanged since Session 8; now serves as the tier-3 fixture in the governance test suite.

**Phase 4A legacy (unchanged in Session 9):**
- `templates.py` — untouched. `build_base_files` is stable.
- `fake_client.py` — untouched. Deterministic sha1 on `message|branch|sorted(paths)` still the invariant.
- `protocol.py` — untouched. Still not `@runtime_checkable`; adapter tests work around this by duck-typing instead.
- `agent.py` — untouched. Precondition guard (incomplete intake or data → FAILED without creating project) is preserved by Phase 4B. Two `test_agent.py` tests still pin `fake_client.projects == {}` under precondition failure; both pass.

### Gotchas — Read These First

**Phase 4B gotchas (new — Session 10 must read first):**
- **`retry_backoff` uses `time.sleep()` by default in production.** Tests MUST pass `sleep=lambda _s: None` (or a list-appender) when building `make_nodes` or `build_website_graph`, otherwise the suite takes 3+ seconds per flaky-commit scenario. The `sleep` kwarg is forwarded from `build_website_graph(client, *, sleep=...)` into `make_nodes`. If Session 10 or 11 adds new retry-path tests, remember to inject `sleep`.
- **`WebsiteAgent.__init__(client)` always builds its own graph with no sleep override.** `test_retry.py::TestRetryEndToEnd` uses `WebsiteAgent.__new__(WebsiteAgent)` + manual `agent.client = client; agent.graph = build_website_graph(client, sleep=...)` as a workaround. If the abstraction plan rewrites `WebsiteAgent`, consider adding a `graph` kwarg to `__init__` so the hack goes away.
- **`build_gitlab_project_result` only populates `model_registry_entry` when BOTH `project_name` AND `project_slug` are in state.** FAILED-before-naming states (e.g., every candidate name taken, or a group-lookup error before CREATE_PROJECT succeeds) get `{}` for the entry. `test_failed_state_defaults_governance` pins this. Session 10's GitHub adapter must also surface a failure mode that leaves naming empty cleanly; don't try to populate the entry from input data alone.
- **`GovernanceManifest.artifacts_created` is derived, not stored.** It's computed by `build_gitlab_project_result` filtering `state["files_created"]` through `is_governance_artifact()`. The `governance_paths` field in state is informational only — the manifest doesn't read it. If Session 10 or 11 adds new governance artifact categories (e.g. `.github/workflows/ci.yml`), they MUST update `is_governance_artifact()` too, or the new files will silently fall out of the manifest.
- **The `is_governance_artifact` classifier is prefix-based.** Currently matches `governance/`, `data/datasheet_`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `analysis/fairness_audit.qmd`, `/fairness/`, `tests/test_fairness.py`. For the GitHub abstraction, this list needs `.github/workflows/ci.yml` OR a more general "known CI config path" check — Session 10 should note this in the plan's "files to change" list.
- **`_FRAMEWORK_ARTIFACTS` is static and platform-agnostic.** Adding a new regulatory framework = add a row to the dict + pick the artifacts it binds to. The test `test_regulatory_mapping_filters_unknown_framework` pins the passthrough behavior: unknown frameworks appear in the mapping with an empty list. Don't "fix" this — the empty list makes the gap visible.
- **Monitoring cadence lookup is in `_CYCLE_CADENCE` (private).** If a future session adds a new cycle_time literal (the schema allows four today: strategic/tactical/operational/continuous), both the schema AND this dict must be updated in lockstep. The cadence text is asserted verbatim by `TestTier1Critical::test_tier1_ongoing_monitoring_has_continuous_cadence` ("Automated continuous monitoring").
- **`_tier_at_least(risk_tier, threshold)` uses lower-severity-number semantics.** `tier_1_critical = 1`, `tier_4_low = 4`. `_tier_at_least("tier_2_high", "tier_3_moderate") == True` because tier 2 ≤ tier 3 (on the severity axis). Unknown tiers default to 99 (never passes the check). Don't invert the comparison.
- **python-gitlab DOES ship type stubs.** The adapter originally had `# type: ignore[import-untyped]` on the `import gitlab` and `from gitlab.exceptions import ...` lines; mypy strict flagged both as `unused-ignore`. Removing them is the correct fix. If Session 10's PyGithub adapter needs type ignores, check first — PyGithub may or may not ship stubs, and adding unnecessary ignores will immediately break mypy strict.
- **The `GitLabClient` Protocol is NOT `@runtime_checkable`.** `isinstance(adapter, GitLabClient)` raises `TypeError: Instance and class checks can only be used with @runtime_checkable protocols`. Adapter tests use `callable(getattr(adapter, "create_project"))` instead. Do NOT add `@runtime_checkable` to the protocol just to simplify tests — it's not needed for production and may mask signature mismatches that mypy strict currently catches.
- **`PythonGitLabAdapter` constructor does NOT make a network call.** python-gitlab defers authentication until the first actual API call, so `PythonGitLabAdapter(gitlab_url="https://invalid.example.invalid", private_token="junk")` succeeds silently. The test `test_constructor_does_not_make_network_call` pins this. Session 10's PyGithub adapter: verify that `github.Github(token)` behaves the same way (it does, per PyGithub docs, but verify before relying on it in tests).
- **`_is_name_conflict(exc)` is loose matching.** It checks `response_code in (400, 409)` + a lowercase `"already been taken"` or `"already exists"` substring. GitLab can also return the message in either a string or a dict shape — the helper calls `str(exc.error_message)` to cover both. If GitLab ever changes the wording, the name-conflict handling silently degrades to "unknown GitLabClientError" + no suffix retry. Low-probability but worth mentioning for Session 10 so the GitHub adapter's equivalent is built with similar defensiveness.
- **`.gitlab-ci.yml` is classified as a governance artifact.** This is per plan §8.2 "Always" row. Session 10's GitHub variant (`.github/workflows/ci.yml`) must inherit the same classification — update `is_governance_artifact()` in lockstep with the new renderer.
- **The three tier fixtures are not balanced in coverage.** `tier1_intake.json` is the only one that exercises `uses_protected_attributes=true`; `tier2_intake.json` is the only one with `cycle_time=strategic`; `subrogation_intake.json` is the only tier with `affects_consumers=true` AND the tier-3-gated artifacts. If you change one, recompute the tier-coverage matrix so the others don't silently lose coverage.
- **`build_regulatory_mapping` filters by `emitted_paths`, which is the set of files actually emitted for this project's tier.** Tier 4 with SR_11_7 declared will produce `mapping["SR_11_7"] == ["governance/model_card.md"]` — only the always-artifacts. A tier 1 run with SR_11_7 will produce all four SR_11_7 artifacts. This is the intended behavior; the mapping reflects reality, not the static framework→artifact table. Session 10's CI-platform branching should NOT change this logic.
- **mypy strict is now clean across all 12 files in `agents/website/`.** Session 10 should add files to this package (not as a refactor, but for GitHub adapter) and expect mypy clean from the start. Run `uv run mypy src/model_project_constructor/agents/website/` before committing.
- **Coverage gate stays at 90%**, currently 96.51% (289 tests). Phase 4B added 29 tests net (88 website tests, up from 59). Session 10's abstraction plan work should target keeping coverage ≥95% on new code.

**Phase 4A gotchas (unchanged from Session 8):**
- **`INITIAL_COMMITS` expects the accumulator to be non-empty.** If `state["files_pending"]` is `{}` at flush time, the node returns `status=FAILED` with `failure_reason="no_files_scaffolded"`. Retry loop does NOT re-trigger on this (it's not a `GitLabClientError`). Test: `test_empty_pending_fails` in `test_nodes.py`.
- **Name conflict handling is unchanged from 4A.** `_candidate_names` in `nodes.py` yields `[name, name-v2, name-v3, name-v4, name-v5]` → `MAX_NAME_CONFLICT_ATTEMPTS=5` candidates. Don't conflate with `MAX_COMMIT_ATTEMPTS=3` (the retry/backoff limit).
- **The precondition guard in `WebsiteAgent.run` returns FAILED without creating a project.** Two `test_agent.py` tests assert `fake_client.projects == {}` after an incomplete-intake / incomplete-data call. Preserved by 4B.
- **`thread_id = f"website::{intake.session_id}"`** — the `website::` prefix avoids collisions with intake agent thread_ids under a shared checkpointer. Preserved by 4B.
- **First real-API smoke test of Phase 3B intake was done at Session 8 start.** `claude-sonnet-4-6` works. 3-session-deferred caveat RETIRED. Phase 2B AnthropicLLMClient in the standalone data agent is still unverified against a real API — not a Session 10 concern.

**Phase 3B gotchas (unchanged from Session 7):**
- Module-level `app = create_app()` creates `intake_sessions.db` at import time. `.gitignore` has `intake_sessions.db*`.
- `SqliteSaver(conn)` uses a single shared connection with `check_same_thread=False`; `IntakeSessionStore` guards every call with `threading.RLock`. Do not remove the lock.
- FastAPI 0.135 uses the `lifespan` context manager; `@app.on_event` is deprecated.
- Review-accept token matching in `agents/intake/nodes.py:35` is case-insensitive over `{ACCEPT, accept, yes, approve, approved, ok, looks good}`.
- `origin` is still the GitHub remote `https://github.com/rmsharp/claims-model-starter.git`. Do not force-push master.
- Python is 3.13.5 in `.venv`; `requires-python = ">=3.11"`.
- LangGraph 0.2.76 interrupt + SQLite persistence verified end-to-end.
- `claude-sonnet-4-6` still the hardcoded default model in both intake and data-agent `anthropic_client.py`.
- Two `StrictBase` classes (main package vs standalone data-agent); do not DRY them up.
- `agents/data/__init__.py`, `db.py`, `llm.py` in the main package are thin re-exports; do not edit.
- Typer single-command trap: intake + website CLIs have NO `@app.callback()`, data-agent CLI does. The website CLI still matches the plan's literal `python -m ... --intake X --data Y --fake-gitlab` form.
- `packages/data-agent/USAGE.md` is the standalone's README. Don't delete.
- `methodology_dashboard.py` does NOT exist in this repo — runs from `~/Development/` (external shared location). SESSION_RUNNER.md Phase 0 step 5 was updated in Session 9 to reflect this.

### How Session 9 Exercised Phase 4B

- **Orientation took ~15 minutes**: SAFEGUARDS + SESSION_NOTES top + plan §4.3/§5.4/§8/§10/§11/§14 + all 8 Phase 4A source files + conftest/test_agent/test_nodes. Explicitly followed the SESSION_RUNNER Phase 0 report-first protocol and waited for the user to direct the task.
- **Built the governance module before touching `nodes.py`**. Wrote `governance_templates.py` as a single file (all renderers + `build_governance_files` + `is_governance_artifact` + `build_regulatory_mapping`) so the 4B additions to `nodes.py` were purely "wire up the new helpers into new scaffold nodes." This kept the `templates.py` → `governance_templates.py` split clean.
- **Hit the expected regression in the existing 4A test**: `test_governance_artifacts_absent_in_4a` failed as soon as `scaffold_governance` was added to the graph. Session 8's handoff explicitly warned about this; I updated the test in-place to a positive `test_tier3_governance_artifacts_present` assertion rather than deleting it.
- **Hit one unexpected regression**: `test_commit_failure_surfaces` in `test_nodes.py` expected the old 4A semantics (first commit failure = FAILED immediately). Renamed to `test_first_commit_failure_goes_to_retrying` with updated assertions. This is the semantic shift Session 10's GitHub adapter work should anticipate — the retry loop now intercepts the first two failures.
- **mypy strict caught two `unused-ignore` comments** on the python-gitlab imports. Removed them; python-gitlab ships type stubs. If I had left the ignores in place, the file would have passed but drifted from strict.
- **Manual CLI verification on the tier-1 fixture** surfaced a cosmetic quirk in the `_render_file_tree` indentation (deep files visually misaligned from shallow ones), which was already a 4A known issue noted in Session 8's handoff. Not fixed; not blocking.
- **Phase 4A's accumulator pattern paid off.** Adding three new scaffold nodes was a pure additive — each new node does `pending.update(files); return {"files_pending": pending}`. Zero refactoring of `scaffold_base`. The handoff's guidance to keep `templates.py` untouched and put all new work in a sibling module was correct.
- **29 tests added net** (88 total in the website suite), **0 regressions in the rest of the repo** (all 201 prior tests in other packages still green), **mypy strict clean on day one** for the new files. Session 8's handoff was explicit enough to avoid any discovery work — I did not need to grep for unknown callers or trace state shape.

### Session 8 Handoff Evaluation (by Session 9)

**Score: 10/10.**

- **What helped (specific):**
  - "ACTIVE TASK" block listed every §11 governance file, tagged each with its §8.2 tier gate, and told me exactly which 4A tests I would need to modify (`test_agent.py::test_governance_artifacts_absent_in_4a` and `test_nodes.py::test_complete_state_produces_valid_result`). **Both were exactly right** — these were the only two pre-existing tests I had to touch, and I touched them for the reasons the handoff predicted. Saved 20+ minutes of grep work.
  - The full key-files block with line-range annotations (`nodes.py:88-98` for the accumulator pattern, `nodes.py:117` for `build_gitlab_project_result` emptiness) let me open the right code spans immediately. The predictions about which lines needed changes were accurate.
  - The "Phase 4A gotchas" block flagged three non-obvious invariants I preserved without thinking: (a) the precondition guard returns FAILED without creating a project (b) `thread_id` convention (c) the deterministic sha1 scheme. I did not disturb any of them, and the tests that pin these behaviors all still pass.
  - The "How Session 8 Exercised Phase 4A" narrative section gave me a template for how the final handoff should read — chronological, with commit-specific references and explicit verification command output.
  - The handoff's "Prefer JSON fixtures — they're faster to load and don't drag the fixture LLM into governance tests" was spot-on guidance. JSON fixtures took ~5 minutes to write and passed Pydantic validation on the first try.
  - The "mypy strict is clean on ... `agents/website/` (10 files)" line set an explicit bar. I wrote 2 new files (gitlab_adapter.py, governance_templates.py) mypy-clean on day one because I knew the bar.

- **What was missing:** Nothing I hit. The only gap I'd even mention is that the handoff didn't explicitly say "make the retry `sleep` injectable" — but the §4.3 plan text made it obvious, and the handoff DID say "retry/backoff on GitLab errors" which implied bounded wall-clock testability. Not a real gap.

- **What was wrong:** Nothing. One minor prediction inaccuracy: the handoff said the governance test file would be "test_governance.py (tier 1 / tier 2 / tier 3)" — I also added a `TestBuildGovernanceFilesUnit` class for `build_governance_files` unit tests + a `test_retry.py` for the retry-backoff path + a `test_gitlab_adapter.py` for the adapter. The handoff's single-file suggestion would have been too monolithic. This is me expanding the plan, not the plan being wrong.

- **ROI:** Reading the handoff took ~5 minutes. It saved at LEAST an hour of code exploration — the Phase 4A invariants (accumulator pattern, precondition guard, precondition-result helper, manifest shape, tier-interpretation of `_TIER_SEVERITY`) were all pre-documented and I did not re-derive any of them. Session 8's handoff is the gold standard for this project. I will try to match it.

### Session 9 Self-Assessment

**Score: 9/10 (by Session 9's own rubric — Session 10 will score independently).**

- **What went well:**
  - Complete deliverable in one session, matching plan §14 Phase 4B DONE criteria exactly. 3 tier fixtures, `GovernanceManifest` populated per spec, `regulatory_mapping` correct, retry bounded at 3 attempts, real adapter imports without side effects.
  - 29 new tests, all passing, mypy strict clean on day one, coverage 96.51% (down a tiny bit from 96.88% because the adapter has untested generic-exception fallbacks, acceptable per "no live network" guidance).
  - Followed Session 8's guidance to keep `templates.py` untouched and `governance_templates.py` separate — this kept the review-time diff readable and preserved 4A's baseline tests unchanged.
  - Precondition guard, `thread_id` convention, name-conflict suffix logic, and deterministic sha1 all preserved without disturbance.
  - Phase 0 orientation before any code change; Phase 1B stub written before any code change; Phase 3A handoff evaluation written with concrete citations of what Session 8 did well.
  - Failure mode avoidance: did NOT start Phase 5 (#18, planning-to-implementation bleed; here the implementation-to-next-phase version) despite the CLI update giving me an opening to "wire the adapter into orchestrator context." Stopped at the adapter itself + CLI flag, exactly what 4B required.
  - Failure mode avoidance: did NOT touch `templates.py`, `fake_client.py`, `protocol.py`, or `agent.py` (except the CLI's agent-import line). Phase 4B additions lived entirely in new files + `state.py` + `nodes.py` + `graph.py` + `__init__.py`. Session 8's instruction was "keep templates.py the base" and I kept it literally unchanged.
  - Answered the user's mid-session context injection (the GitHub/GitLab abstraction notes) by immediately acknowledging, finishing the failing test first, then recording the notes verbatim in the handoff. Did NOT pivot to planning the abstraction mid-session.

- **What I could have done better:**
  - The `_render_file_tree` indentation cosmetic bug in `cli.py` has been flagged twice now (Session 8 noted it, Session 9 noted it) and not fixed. I chose not to fix it because it's cosmetic and 4B-out-of-scope, but a future session should just do a 5-line fix. Not a Session 9 deliverable, though.
  - The `WebsiteAgent.__new__` hack in `test_retry.py` is ugly. Cleaner would have been to add a `graph` kwarg to `WebsiteAgent.__init__` — but that's a production-code change for a test-only improvement, so I left it. Worth a 2-minute refactor in Session 11's abstraction work.
  - The three tier fixtures are minimal — they don't exercise corner cases like empty regulatory_frameworks, missing optional fields, or multiple primary queries with different datasheets. I could have added a fourth "tier-4-minimal" fixture for edge-case coverage. Deferred to Phase 6.
  - I did not smoke-test the real `PythonGitLabAdapter` against any live GitLab instance. The user has not provided credentials and the handoff said "no live network tests" — but I could have at least constructed the adapter with a fake URL, called `create_project`, and confirmed the expected `GitLabClientError` comes back (because there's no network). Deferred — MagicMock stubs cover the same logic path without any IO concerns.

- **Why not 10:** I did not meet the bar of "zero hacks." The `WebsiteAgent.__new__` workaround in `test_retry.py` is a test-only hack that would earn a code-review comment. Session 8's handoff didn't have anything equivalent.

### Session 9 Learnings (add to table in `SESSION_RUNNER.md`)

| # | Learning | When to apply |
|---|----------|---------------|
| 2 | When extending a LangGraph pipeline with new nodes, put the helper functions in a sibling module (e.g., `governance_templates.py` next to `templates.py`) rather than expanding the existing module. Review-time diff stays local; the "before vs after" phase split is visible in the file tree. | Any LangGraph phase extension where the previous phase's templates/helpers are stable and don't need to change. |
| 3 | Derive manifest/audit data by classifier function (`is_governance_artifact(path)`) rather than by storing it in state during each node. The classifier is the single source of truth and composes with any future node that adds a new artifact category; state bookkeeping drifts. | Assembling a result object from side effects of multiple nodes — especially when some nodes are optional. |
| 4 | When a test file needs a graph with injected dependencies (e.g., no-op `sleep`), prefer plumbing a kwarg through `build_website_graph` rather than building it manually — but DO NOT refactor production code to add the kwarg for a test-only need unless the kwarg is also valuable in production. Accept a `__new__`-based construction hack in tests rather than over-engineer production. | Whenever a test needs a variant of a production-constructed object. |
| 5 | Pin a specific behavior with BOTH a positive and a negative assertion per tier in governance fan-out tests. `assert "governance/foo.md" in files` AND `assert "governance/bar.md" not in files` — otherwise a tier's gating can silently regress (e.g., tier 3 starts emitting a tier-2 artifact by accident) and the "positive only" test will pass. | Any tier/flag-gated code where missing artifacts are as important as present ones. |
| 6 | The pattern "plan as deliverable, then implementation as a separate session" (failure modes #18, #19) is load-bearing across the SESSION_RUNNER workstreams. When the user hands Session N a plan input mid-session (as happened here with the GitHub/GitLab notes), write it into the handoff verbatim and leave it for Session N+1 — do NOT pivot. | Any session where the user introduces a second deliverable while the first is mid-flight. |

### How You Will Be Evaluated
Session 10's handoff will be scored on:
1. Did Session 10 write a plan document to `docs/planning/github-gitlab-abstraction-plan.md` and STOP, or did it bundle implementation? (The plan is the deliverable.)
2. Does the plan include a grep-based inventory for every symbol Session 9's gotchas listed (`GitLabTarget`, `GitLabClient`, `FakeGitLabClient`, `gitlab_url`, `group_path`, `render_gitlab_ci`, `.gitlab-ci.yml`, `is_governance_artifact`)?
3. Does the plan make an explicit recommendation (neutral rename vs parallel schema) and back it with the inventory evidence, rather than hedging?
4. Does each phase in the plan have explicit DONE criteria + verification commands + session boundary?
5. Did Session 10 ask the user for the missing note #1, OR document why it proceeded without it?
6. Did Session 10 preserve Session 9's gotchas without dilution? In particular, the `is_governance_artifact` classifier needs an update for `.github/workflows/ci.yml` — is that flagged?
7. Does the plan explicitly say Phase 5 (orchestrator) is deferred until the abstraction lands, or does it try to interleave them?
8. Did Session 10 touch any production code under `src/model_project_constructor/agents/website/`? (It should not — planning session, no code changes.)

### What Session 8 Did
**Deliverable:** Phase 4A of architecture plan — Website Agent core + LangGraph + GitLab scaffolding (non-governance) + `FakeGitLabClient` + typer CLI + 59 tests (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `9887286` (fill in on commit).

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS in full, ACTIVE TASK + Session 7 block from SESSION_NOTES, checked git (clean, 8 commits ahead of origin at session start), confirmed `methodology_dashboard.py` still absent and `gh issue list` still empty. Reported findings. Waited for the user to say "go".
2. **Real-API smoke test of Phase 3B intake agent (retires 3-session caveat).** User confirmed an `ANTHROPIC_API_KEY` in `.env` (already gitignored). Sourced it, ran `uv run uvicorn model_project_constructor.ui.intake:app --port 8765` with `INTAKE_DB_PATH=/tmp/intake_smoketest.db`, POSTed a subrogation session (`smoke-test-1`), received a contextually-grounded Claude question ("walk me through the current process for identifying which subrogation claims to pursue"), POSTed one answer, received a substantive follow-up ("what does that recovery typically look like in dollar amounts and what percentage of claims result in recovery"). Stopped uvicorn, deleted `/tmp/intake_smoketest.db*`. **`claude-sonnet-4-6` works against the live Anthropic API; the `claude-sonnet-4-5-20250929` fallback is unneeded.** The Phase 2B data-agent `AnthropicLLMClient` remains unverified but is a separate code path — deferring that to Phase 5 (orchestrator session).
3. Phase 1B session stub written to SESSION_NOTES.md BEFORE any technical work.
4. Re-read architecture-plan sections governing Phase 4: §4.3 (contract + failure modes), §5.4 (schemas, already shipped in Phase 1), §8 (governance integration — **critical for the 4A↔4B split**), §10 (full LangGraph topology), §11 (file structure acceptance checklist), §14 Phase 4A (DONE criteria + verification commands).
5. **Resolved the 4A/4B scope ambiguity.** The ACTIVE TASK block from Session 7 paraphrased 4A as "README, .gitlab-ci.yml, .gitignore, LICENSE" — narrower than §14 Phase 4A's "base repo structure (no governance artifacts yet)" + "all .qmd files, all src/ modules, unit test files". I took §14 as authoritative and additionally applied §8.2's classification rule: **anything §8.2 lists as a governance artifact (including `.gitlab-ci.yml`, `.pre-commit-config.yaml`, and `data/datasheet_*.md`) is out-of-scope for 4A**. Everything else in §11 is in-scope. Net result: 28 base files per project, governance files deferred to 4B. This reading is defensible, tests it, and avoids the bundling trap.
6. Studied the Phase 3A intake agent pattern before writing any website code: `state.py` (TypedDict, no reducers, `initial_state()` helper), `protocol.py` (Protocol + dataclasses for DTOs), `nodes.py` (`make_nodes(client)` closure + per-node pure functions + routing helper + `build_*_report` assembler), `graph.py` (`build_*_graph(client, *, checkpointer=None)`), `agent.py` (facade with `run(...)`), `cli.py` (single `@app.command()` no callback), `__main__.py` (three-line shim). The website agent mirrors this one-for-one.
7. Built the `agents/website/` package in order: `state.py` → `protocol.py` → `templates.py` (pure file-content generators, ~400 lines) → `nodes.py` → `graph.py` → `fake_client.py` → `agent.py` → `cli.py` → `__main__.py` → `__init__.py` (public API).
8. **Graph topology decision.** §10 lists `CREATE_PROJECT → SCAFFOLD_BASE → SCAFFOLD_GOVERNANCE → SCAFFOLD_ANALYSIS → SCAFFOLD_TESTS → INITIAL_COMMITS → END`. I chose to implement the FULL accumulator pattern for 4A — `SCAFFOLD_BASE` populates `state["files_pending"]` and `INITIAL_COMMITS` flushes — instead of inlining the commit in `SCAFFOLD_BASE`. That way Session 9 only needs to merge additional entries into `files_pending` before the existing `INITIAL_COMMITS` fires, with zero refactor of 4A nodes. This is the single most important architectural decision of the session.
9. **Name-conflict handling.** `_candidate_names()` produces `[base, base-v2, base-v3, base-v4, base-v5]`. The `create_project` node walks them in order, catching `ProjectNameConflictError` on each and only surfacing `status=FAILED` with `failure_reason="project_name_conflict:..."` after all 5 are taken. Tested with a pre-seeded `FakeGitLabClient(existing_names=...)` covering single-conflict, 5-way exhaustion, and end-to-end via the agent facade.
10. **`WebsiteAgent.run` precondition guard.** If `intake_report.status != "COMPLETE"` OR `data_report.status != "COMPLETE"`, returns a FAILED `GitLabProjectResult` with `failure_reason=precondition_failed:intake_status=...` WITHOUT creating any GitLab project. Two tests pin this: `test_incomplete_intake_report_halts` and `test_incomplete_data_report_halts` both assert `fake_client.projects == {}` after the call.
11. **Fixtures.** Discovered `tests/fixtures/subrogation_intake.json` and `sample_datareport.json` did not exist — the ACTIVE TASK block from Session 7 referenced them in the literal verification command but they were never created. Generated `subrogation_intake.json` by running `tests/fixtures/subrogation.yaml` through `IntakeAgent.run_with_fixture(...)` and dumping the validated `IntakeReport`. Hand-wrote `sample_datareport.json` — one primary query (`subrogation_training_set`) with full SQL, 2 quality checks, a Datasheet, request/summary/expectations populated, all fields conforming to the v1 schema. Validated both via `model_validate_json` round-trip before using them in tests.
12. **Pre-test smoke run of the whole package** before writing the test suite: `uv run python -m model_project_constructor.agents.website --intake ... --data ... --fake-gitlab` → COMPLETE, 28 files committed, deterministic sha. Validated the happy path architecturally.
13. Wrote 59 tests across 5 files (`test_templates.py`, `test_fake_client.py`, `test_nodes.py`, `test_agent.py`, `test_cli.py`) + conftest. Tests cover: slug/name derivation edge cases, every individual renderer, full `build_base_files` file set, per-node success + failure paths, name-conflict suffix walking, `WebsiteAgent.run` happy path with all §11 base files asserted by name, precondition guards, governance-absent assertion (to be deleted in 4B), CLI arg validation + happy path + `--output` file.
14. First test run: **59 passed on the first invocation.** No debugging required. This is unusual and I attribute it directly to how faithfully the website agent mirrors the Phase 3A intake agent's pattern — the 4A graph topology, node signature, and facade shape are 1:1 copies of shapes that already had tests pinning them.
15. Ran the full suite: **260 passed, 96.88% coverage** (up from 201 @ 96.48%). `templates.py` at 100%, `state.py` at 100%, `agent.py` at 100%, `protocol.py` at 92% (the 2 uncovered lines are the Protocol `...` ellipsis bodies, which mypy treats as reachable for coverage but pytest never executes — acceptable).
16. Ran `uv run mypy src/model_project_constructor/agents/website/` — 2 errors on first run: unused `# type: ignore[arg-type]` on the `GovernanceManifest` Literal args in `nodes.py:163-164`. Pydantic's v2 Literal coercion of `dict.get(..., "default")` is apparently smarter than I expected. Removed the `type: ignore` comments → **0 errors across 10 source files.**
17. Ran the literal plan verification command `uv run python -m model_project_constructor.agents.website --intake tests/fixtures/subrogation_intake.json --data tests/fixtures/sample_datareport.json --fake-gitlab` — prints the file tree (28 files) and dumps a valid `GitLabProjectResult` JSON with `status=COMPLETE`, `project_url=https://fake.gitlab.test/data-science/model-drafts/intake-subrogation-001`, deterministic commit sha, all 28 paths in `files_created`. §14 Phase 4A verification satisfied.
18. Updated README.md: phase table split into 4A Complete / 4B Not started, repo layout extended with `agents/website/` module breakdown, tests section shows `agents/website/ # 59 website agent tests`, fixtures list extended with `subrogation_intake.json` + `sample_datareport.json`, test count updated 201 → 260, coverage note 96% → 96.9%, new "Website Agent CLI" quick-start block with the literal verification command + note about governance deferral to 4B.
19. Rewrote the `ACTIVE TASK` block for **Phase 4B** (Website Agent governance scaffolding + retry/backoff + real `python-gitlab` adapter). Points Session 9 at §4.3 failure modes, §8.1/8.2/8.3, §10 full topology, §11 governance files, §14 Phase 4B verification. Enumerates the exact tier 1/2/3 artifacts, the `regulatory_mapping` population requirement, and the three nodes to insert between `SCAFFOLD_BASE` and `INITIAL_COMMITS`.
20. Preserved the Phase 3B gotchas verbatim and prepended a new **"Phase 4A gotchas"** block with 8 new entries (accumulator discipline, `build_gitlab_project_result` 4A-awareness, deliberate `.gitlab-ci.yml` / `.pre-commit-config.yaml` omission, datasheet-as-governance, deterministic fake-client shas, name-conflict is done, precondition guard behavior, `thread_id` prefix convention).

**Key design calls:**
- **Accumulator pattern in state.** `files_pending: dict[str, str]` lives in the state, not in a closure. `SCAFFOLD_BASE` merges, `INITIAL_COMMITS` flushes. Session 9's three new scaffold nodes will just merge more entries. This makes 4B's expansion a ~50-line diff instead of a refactor.
- **Separate `templates.py` from `nodes.py`.** Pure-python template functions are trivially unit-testable in isolation (33 of the 59 tests are template-level). Session 9 should add `governance_templates.py` as a sibling instead of bloating `templates.py` — the 4A/4B split stays legible in code review.
- **Dict-shaped state, not Pydantic-shaped.** `WebsiteState` stores `intake_report`, `data_report`, `gitlab_target` as dicts (`model_dump(mode="json")`) so any LangGraph checkpointer can serialize them without custom codecs. Templates accept dicts directly. The Pydantic models are only touched at the boundary (`WebsiteAgent.run` input + `build_gitlab_project_result` output).
- **Precondition guard returns FAILED, doesn't raise.** §12 says expected failures → status in return, exceptions only for programming errors. An upstream-incomplete report is an expected failure. Two tests pin the no-side-effect behavior.
- **`thread_id = f"website::{session_id}"`** instead of plain `session_id`. Avoids collisions if Phase 5's orchestrator ever shares a single checkpointer across agents. Micro-decision but worth calling out.
- **`FakeGitLabClient` deterministic shas.** `sha1(f"{message}|{branch}|" + "|".join(sorted(files)))`. Same files + same message → same sha. Enables exact pinning in tests if future sessions want it, without making the current tests sensitive to ordering.
- **CLI refuses to run without `--fake-gitlab`.** Exit code 2 with a clear message pointing at 4B. Real `python-gitlab` adapter is 4B's job; the CLI shouldn't silently succeed with a no-op backend and then confuse the operator when nothing lands in GitLab.
- **`build_gitlab_project_result` returns an empty but valid `GovernanceManifest`.** `artifacts_created=[]`, `regulatory_mapping={}`, but `risk_tier`/`cycle_time` are read from the intake report so downstream consumers can trust the manifest shape today. 4B will populate the two collections.

**Files created (20):**
- `src/model_project_constructor/agents/website/__init__.py`
- `src/model_project_constructor/agents/website/__main__.py`
- `src/model_project_constructor/agents/website/state.py`
- `src/model_project_constructor/agents/website/protocol.py`
- `src/model_project_constructor/agents/website/templates.py`
- `src/model_project_constructor/agents/website/nodes.py`
- `src/model_project_constructor/agents/website/graph.py`
- `src/model_project_constructor/agents/website/fake_client.py`
- `src/model_project_constructor/agents/website/agent.py`
- `src/model_project_constructor/agents/website/cli.py`
- `tests/agents/website/__init__.py`
- `tests/agents/website/conftest.py`
- `tests/agents/website/test_templates.py`
- `tests/agents/website/test_fake_client.py`
- `tests/agents/website/test_nodes.py`
- `tests/agents/website/test_agent.py`
- `tests/agents/website/test_cli.py`
- `tests/fixtures/subrogation_intake.json`
- `tests/fixtures/sample_datareport.json`

**Files modified (2):**
- `README.md` — phase table, repo layout, test count, coverage note, website-agent quick start, fixture list.
- `SESSION_NOTES.md` — ACTIVE TASK rewritten for Phase 4B; Session 8 block below; Phase 4A gotchas block; Session 7 handoff evaluation.

**Session 7 Handoff Evaluation (Session 8 scoring Session 7):**
- **Score: 9/10**
- **What helped (ranked by time saved):**
  1. **"Reuse the LangGraph pattern from Phase 3A. ... See `src/model_project_constructor/agents/intake/graph.py:19-70` for the canonical pattern."** Exact file:line was gold. I copied the Phase 3A shape one-for-one and the first test run was 59/59. The 1-for-1 fidelity is what made this the fastest phase so far.
  2. **The full inventory of Phase 3B key files with line numbers** (`ui/intake/runner.py:122->144`, `app.py:182`, `fixture.py:95-122`, etc.). I didn't need any of them for 4A specifically, but the shape of the inventory taught me the target quality bar for my own handoff.
  3. **"Use §11 as your acceptance checklist — every file listed there is a DONE criterion."** Directly shaped my `test_all_section_11_base_files_scaffolded` test which pins every file by name. Without this sentence I probably would have written a weaker "at least 20 files" test.
  4. **The "Typer single-command trap"** warning made me pick the `@app.command()`-no-callback pattern for the website CLI in 30 seconds instead of discovering it by trial and error.
  5. **The `FixtureLLMClient` statelessness story.** I absorbed the general principle ("state lives in graph state, not in client instances") and used it implicitly when designing `FakeGitLabClient`. No accident — I patterned the fake after the fixture.
- **What was missing (and cost me time):**
  1. **The 4A/4B scope ambiguity.** The ACTIVE TASK block said "CREATE_PROJECT + SCAFFOLD_BASE nodes with structured templates for README.md, .gitlab-ci.yml, .gitignore, LICENSE" — which is NARROWER than §14 Phase 4A's "base repo structure (no governance artifacts yet)" + "all .qmd files, all src/ modules, unit test files". I had to read §14 + §8.2 carefully to decide. I settled on "§14 + §8.2" as authoritative and delivered the full 28-file base. If Session 7 had either (a) enumerated the 28 files explicitly or (b) stated "§14 is authoritative, ignore the narrower summary above", I would have saved ~10 minutes.
  2. **`subrogation_intake.json` and `sample_datareport.json` did not exist.** The ACTIVE TASK block quoted a verification command referencing them, but neither Session 6 nor Session 7 created them. I had to generate the intake from `subrogation.yaml` and hand-write the data report. Not hard, but Session 7 could have flagged this. (Fair-minded note: these fixtures are 4A-specific test inputs, so Session 7 legitimately couldn't have created them earlier — the call-out would have been the contribution.)
- **What was wrong:** Nothing verifiable. The gotchas all held up. The `python-multipart` hard-dep warning was moot for 4A but still valid. The `methodology_dashboard.py` absence was correctly flagged.
- **ROI:** The handoff was ~100 lines of ACTIVE TASK + ~60 lines of gotchas. Reading it cost ~2 minutes. It saved me an estimated 30–45 minutes of pattern discovery and probably prevented at least one rewrite. Net ROI very positive.
- **Why not 10/10:** The scope ambiguity in item 1 above is a real cost — it forced me into a judgment call during Phase 2 (Execute) instead of letting me trust the block verbatim. A 10/10 handoff would have told me the final file count up front. Everything else earned the 9.

### What Session 7 Did
**Deliverable:** Phase 3B of architecture plan — Intake Agent Web UI (FastAPI + SSE + HTMX + SQLite checkpointer) (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `1c1141a` (Phase 3B implementation + 22 tests + pyproject + `FixtureLLMClient` statelessness fix + `graph.py` checkpointer parameterization + `.gitignore` + README + SESSION_NOTES).

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS in full, ACTIVE TASK + Session 6 block from SESSION_NOTES, checked git (clean, 6 commits ahead of origin), confirmed `methodology_dashboard.py` still absent and `gh issue list` still empty. Reported findings. Waited for the user to say "go".
2. Phase 1B session stub written to SESSION_NOTES.md BEFORE any technical work: `"Session claimed. Work beginning."` under `### What Session 7 Did`.
3. Read the plan sections that govern Phase 3B: §9.3 (stack), §14 Phase 3B (DONE criteria + verification), §4.1 (governance), §10 (LangGraph diagram). Confirmed that Phase 3B is a driver over the SAME compiled graph Phase 3A shipped — NOT a rewrite.
4. Read the Phase 3A code I needed to build on top of: `agents/intake/__init__.py`, `state.py`, `graph.py`, `agent.py`, `nodes.py`, `protocol.py`, plus `pyproject.toml` to understand the optional-extras layout.
5. Inventoried dependencies: `fastapi`, `uvicorn`, `sse-starlette`, `httpx`, `starlette`, `langgraph 0.2.76`, `langgraph-checkpoint 2.1.2` were already installed. `langgraph-checkpoint-sqlite` and `python-multipart` (for FastAPI form handling) were NOT. Added both to the `ui` optional extras via `uv add --optional ui`. `jinja2` not installed — chose to keep templates as pure Python f-strings with `html.escape` rather than add another dep.
6. Confirmed the `langgraph.checkpoint.sqlite.SqliteSaver` API: takes a `sqlite3.Connection`, has `.setup()`. Direct construction works — no need for the `from_conn_string` context manager, which would complicate integration with FastAPI's request lifecycle.
7. **Parameterized `build_intake_graph`** — added `checkpointer: Any | None = None` kwarg. Default behavior unchanged (`MemorySaver`). The kwarg means Session 6's CLI and all Phase 3A tests keep working verbatim, while the web UI passes a shared `SqliteSaver`. One-line change, minimum blast radius.
8. Created 7 TaskCreate items covering checkpointer, FastAPI app, SQLite, HTMX, tests, verification, close-out.
9. Built `src/model_project_constructor/ui/intake/runner.py` — `IntakeSessionStore` owns a single `SqliteSaver` + a lock + a per-session compiled-graph cache. `start_session`, `answer`, `review`, `get_snapshot`, `has_session`, `close`. Every public method is guarded by the RLock because FastAPI routes sync endpoints through a threadpool and SQLite connections are NOT thread-safe even with `check_same_thread=False`. Phase check in `answer` and `review` raises `InvalidPhaseError` so the HTTP layer can return 409.
10. Built `src/model_project_constructor/ui/intake/templates.py` — four pages: index (start-interview form), resume-form, session (question / review / complete / not_started), rendering via f-strings with `html.escape` on every interpolated value. CSS and the HTMX script tag are inlined. No Jinja2 dependency.
11. Built `src/model_project_constructor/ui/intake/app.py` — `create_app(llm_factory, db_path)` factory used by tests, plus module-level `app = create_app()` for the plan's literal `uvicorn model_project_constructor.ui.intake:app` verification command. Routes: landing, resume form, resume redirect, create session, get/post session, answer, review, state.json, report.json, events (SSE), healthz.
12. First boot via `uv run python -c "from model_project_constructor.ui.intake import create_app"` → ImportError: `python-multipart` missing. FastAPI's `Form(...)` requires it. Added to `ui` extras, re-synced, re-imported → clean.
13. Wrote an in-process end-to-end smoke test via `TestClient` on the subrogation fixture: POST /sessions → GET /sessions/{id} → loop POST /answer 7 times → POST /review accept → GET /report.json → COMPLETE. Every step 200. Confirmed the architecture before writing the real test suite.
14. Wrote 22 tests across 5 files:
    - `tests/ui/intake/test_app_happy_path.py` (11 tests) — healthz, index, resume form page, resume redirect lookup, not-started placeholder, create + redirect, create with auto-ID, subrogation end-to-end COMPLETE, report.json 409 when not complete, answer 409 in review phase, review 409 in question phase.
    - `tests/ui/intake/test_caps_and_revisions.py` (2 tests) — question cap → DRAFT_INCOMPLETE with `questions_cap_reached`; revision cap → DRAFT_INCOMPLETE with `revision_cap_reached`. Both exercise the full HTTP round-trip against the cap fixtures from Phase 3A.
    - `tests/ui/intake/test_sqlite_resume.py` (1 test) — the core Phase 3B DONE criterion. Create app1 with a tmp db, answer 2 questions, close app1, create a NEW app2 pointing at the same db, finish the interview to COMPLETE, confirm report.json has `status=COMPLETE`.
    - `tests/ui/intake/test_sse.py` (2 tests) — `text/event-stream` content type, initial snapshot payload parsing via `client.stream` + `iter_lines`.
    - `tests/ui/intake/test_runner.py` (6 tests) — direct `IntakeSessionStore` tests so failures point at the driver, not at FastAPI wiring. `CAPS` constant, snapshot-for-missing-session, `has_session` transition, `start_session` returns question snapshot, `answer` wrong phase, `review` wrong phase.
15. **First resume test failure** — after "restart" and 5 more answers, POST /review returned 409 "phase is question, cannot accept review response". Graph kept asking q#8. Root cause: `FixtureLLMClient` had internal `self._q_index = 0` that reset on every factory call; the graph state said `questions_asked=7`, but the LLM's internal counter said "return question[0], enough_info=False" → infinite questions. **Fix:** made `FixtureLLMClient.next_question` stateless — it now keys off `context.questions_asked` (the graph state is the source of truth). This is a small but load-bearing correctness fix: stateful test doubles that reset across factory calls are a trap when the system under test persists state.
16. Updated the existing Phase 3A `test_fixture_llm_client_dispenses_questions_in_order` test to match the new stateless contract: it now constructs fresh `InterviewContext`s with monotonically-increasing `questions_asked`, and asserts that calling with the same context is idempotent. All 14 fixture tests + all 56 agents/intake tests green.
17. **SSE test hung TestClient on first run.** Initial SSE endpoint design was a long-lived polling loop: emit snapshot → sleep 1s → check `await request.is_disconnected()` → loop. Under `TestClient.stream`, the sync test code never yielded control back to the server coroutine, so `is_disconnected` never returned True even after the `with` block exited. The background pytest process had to be `pkill`ed. **Fix:** redesigned SSE as one-shot: emit the current snapshot once and terminate. The plan's DONE criterion is "curl smoke test for SSE endpoint", which a one-shot stream satisfies. HTMX clients can reconnect after each form submission; any phase-change stream is a later polish. Documented in the runner docstring and the gotchas.
18. Ran §14 Phase 3B verification commands LITERALLY:
    - `uv run pytest tests/ui/intake/ --no-cov` → 22 passed.
    - `uv run pytest` (full suite) → **201 passed, 96.48% coverage** (179 → 201; +22 web UI tests).
    - `uv run mypy src/model_project_constructor/ui/` → 0 errors in 5 source files (after adding `-> AsyncIterator[None]` to the lifespan contextmanager).
    - `INTAKE_DB_PATH=/tmp/intake_verify.db uv run uvicorn model_project_constructor.ui.intake:app --port 8765` → uvicorn starts, serves 200 on `/healthz` and `/`.
    - `curl -sN http://localhost:8765/sessions/curl-smoke/events` → `event: snapshot\ndata: {..."phase": "not_started"...}`. SSE smoke test passes.
    - `curl -i "http://localhost:8765/sessions/resume?session_id=foo"` → 303 redirect to `/sessions/foo`.
19. Module-level `app = create_app()` creates `intake_sessions.db` in the cwd at import time because the default DB path is relative. Added `intake_sessions.db`, `intake_sessions.db-shm`, `intake_sessions.db-wal` to `.gitignore` (WAL-mode SQLite needs all three patterns). Removed stray files from the workspace.
20. Did NOT do the first real-API smoke test. No `ANTHROPIC_API_KEY` in this session. Same deferral as Session 6. Noted in handoff as the third-session-in-a-row caveat.
21. Updated `README.md`: Phase 3B row → Complete, added `ui/intake/` to the repo layout with module breakdown, added `tests/ui/intake/` to the tests section, added the web-UI quick-start block with `uvicorn` command + `INTAKE_DB_PATH` note + SSE endpoint pointer, updated test count 179 → 201.
22. Rewrote the `ACTIVE TASK` block for **Phase 4A** (Website Agent — sub-phase 4A only). Points Session 8 at §4.3, §5.4, §10, §11, §14 Phase 4. Lists all the Phase 3B key files with line references. Enumerates Phase 3B-specific gotchas (module-level DB creation, RLock discipline, graph-cache semantics, stateless fake-client pattern, one-shot SSE design, `python-multipart` hard dep) on top of the preserved Phase 2A/2B/3A gotchas.
23. Close-out commit pending: everything above as a single Session 7 commit.

**Key design calls:**
- **One compiled graph per session, cached in memory.** `IntakeSessionStore._graphs` is a per-session cache so the LLM factory is invoked exactly once per session. Alternative was one graph per app shared across sessions, but that requires the LLM client to be shared, and production factories (Anthropic) and test factories (Fixture) can want per-session state. The per-session cache makes both work.
- **Stateless `FixtureLLMClient`.** Required for SQLite resume. The graph state is the source of truth. Any future fake LLM client should follow this pattern. Documented in the fixture docstring AND in the handoff gotchas.
- **One-shot SSE.** The plan's DONE criterion is "curl smoke test". A one-shot stream satisfies it, is cleanly unit-testable under sync `TestClient`, and avoids the coroutine-lifecycle hazards of a polling loop. A long-lived stream is a Phase 4+ polish that will need async test clients.
- **No Jinja2 dependency.** Pure f-strings with `html.escape`. Four pages is the entire frontend surface; a template engine is overkill and adds install footprint.
- **`create_app(llm_factory, db_path)` factory.** Module-level `app = create_app()` exists because the plan's verification command literally says `uvicorn model_project_constructor.ui.intake:app`. The factory exists because tests need to inject fixture LLM clients and per-test SQLite DBs. Both coexist cleanly.
- **Per-session `thread_id = session_id`.** Same convention as Phase 3A's CLI, carried over to the HTTP layer. Session isolation is LangGraph's responsibility, not ours.
- **Phase guards at the driver level, not route level.** `IntakeSessionStore.answer` / `review` raise `InvalidPhaseError` if the caller submits the wrong response kind. The HTTP layer maps this to 409. Driver enforcement means the same guards apply to any future non-HTTP driver (a Slack bot, a CLI, whatever).
- **Forms over JSON.** All state-changing routes accept `application/x-www-form-urlencoded` via FastAPI `Form(...)`. This keeps the frontend a plain HTMX form POST with no JSON serialization, and makes `curl` smoke tests trivial.
- **Lifespan context manager, not `@on_event`.** The old pattern is deprecated in FastAPI 0.135+. Noted in handoff.

**Files created (10):**
- `src/model_project_constructor/ui/__init__.py`
- `src/model_project_constructor/ui/intake/__init__.py`
- `src/model_project_constructor/ui/intake/app.py`
- `src/model_project_constructor/ui/intake/runner.py`
- `src/model_project_constructor/ui/intake/templates.py`
- `tests/ui/__init__.py`
- `tests/ui/intake/__init__.py`
- `tests/ui/intake/conftest.py`
- `tests/ui/intake/test_app_happy_path.py`
- `tests/ui/intake/test_caps_and_revisions.py`
- `tests/ui/intake/test_sqlite_resume.py`
- `tests/ui/intake/test_sse.py`
- `tests/ui/intake/test_runner.py`

**Files modified (6):**
- `pyproject.toml` — added `langgraph-checkpoint-sqlite>=2.0,<3` and `python-multipart>=0.0.9` to the `ui` optional extras.
- `uv.lock` — regenerated.
- `src/model_project_constructor/agents/intake/graph.py` — `build_intake_graph(llm, *, checkpointer=None)` kwarg.
- `src/model_project_constructor/agents/intake/fixture.py` — `FixtureLLMClient.next_question` made stateless (keys off `context.questions_asked`), internal `_q_index` removed, docstring updated.
- `tests/agents/intake/test_fixture.py` — `test_fixture_llm_client_dispenses_questions_in_order` updated to the stateless contract + idempotency assertion.
- `.gitignore` — added `intake_sessions.db*` patterns.
- `README.md` — Phase 3B row complete, `ui/intake/` in repo layout, `tests/ui/intake/` in tests section, web-UI quick-start block, test count 179 → 201.
- `SESSION_NOTES.md` — this file; ACTIVE TASK rewritten for Phase 4A; Session 7 block below.

**Session 6 Handoff Evaluation (Session 7 scoring Session 6):**
- **Score: 10/10**
- **What helped (ranked by time saved):**
  1. **"Parameterize the checkpointer" with the explicit file:line (`graph.py:18-56`) and two suggested API shapes** (`checkpointer=None` kwarg OR `make_graph_builder()` + `build_intake_graph(llm, checkpointer)`). I took the kwarg approach — single-line change, preserves backward compat. Without this warning I might have rewritten `build_intake_graph` more invasively.
  2. **"The `plan_next_question` / `ask_user` split is mandatory"** with the explanation that interrupted nodes re-execute from the top on resume. This directly shaped my runner.py design: the HTTP layer drives the graph by calling `graph.invoke(Command(resume=...), config=config)` AFTER checking that a phase is `"question"` or `"review"`. I never had to debug a double-billed LLM call because the split was already correct in Phase 3A and I understood why from Session 6's note.
  3. **"Use `session_id` verbatim as `thread_id`"** with the pointer to `agent.py:86`. Saved me from reinventing the session-isolation mechanism. The web UI uses this convention verbatim (`runner.py:96`).
  4. **"Coverage gate is 90%, currently 96.18%. Phase 3B's web UI + new test surface may temporarily drop this"** — I used this as the "write tests as you go" nudge. Never hit the floor.
  5. **"`_DummyLLM` in cli.py:85-99" pointer** — I confirmed the web UI does NOT need it (it has a real factory at app-construction time), so I left Phase 3A's CLI untouched. Without the pointer I might have tried to extend or share `_DummyLLM`.
  6. **The pre-declared evaluation criteria (7 items)** — I used them as my close-out self-check. Items 2 (reuse `build_intake_graph`), 3 (checkpointer parameterization), and 5 (don't bundle Phase 4) were the ones I was most tempted to shortcut and most grateful were pre-flagged.
- **What was missing (minor):**
  1. No note about `python-multipart` as a hidden FastAPI runtime dep for form handling. I hit an ImportError on first app import and had to add it to the `ui` extras. A one-liner "FastAPI Form(...) needs `python-multipart`" would have saved 2 minutes. I have now added this to the Phase 3B gotchas so Phase 4 doesn't rediscover it if it uses FastAPI Forms.
  2. No note about `jinja2` being absent (I thought it might come in via fastapi's extras; it doesn't). Not blocking — I chose pure f-strings — but one line would have been nice.
  3. No guidance on SSE endpoint lifecycle under sync `TestClient`. I wrote a long-lived polling loop first, it hung, and I had to redesign. Session 6 couldn't have anticipated this specifically, but a generic "SSE endpoints under TestClient are fragile; prefer one-shot streams for test coverage" note would have landed. Added to Phase 3B gotchas for Session 9+ to benefit.
- **What was wrong:** Nothing material. Every claim about existing code matched the repo state. Every file:line reference was correct. Every gotcha was load-bearing.
- **ROI:** Enormous. Session 6's handoff was 108 lines for ACTIVE TASK alone and every line paid. I estimate it saved 45-60 minutes of rediscovery — especially around the checkpointer parameterization (which I might have done invasively), the `plan/ask` split (which I might have accidentally collapsed), and the `_DummyLLM` disposability question (which I might have wasted time generalizing). Read-cost: 10 minutes.
- **Process notes:** Session 6 produced a 10/10 handoff by (a) explicit technical-risk de-risking (the toy-graph instruction), (b) file:line breadcrumbs for every mentioned symbol, (c) pre-declared evaluation criteria that doubled as a close-out checklist, (d) clean separation of "do these things" vs "do NOT do these things", (e) design-rationale notes for key choices (state-without-reducers, node-split, CLI callback) so I could judge edge cases rather than blindly follow. I have copied all five patterns into my own handoff.

**Session 7 Self-Assessment:**
- (+) Completed Phase 0 orientation in full before any file touch. Wrote Phase 1B stub BEFORE any technical work. Reported findings and waited for user direction.
- (+) Re-read the plan sections BEFORE writing code, as Session 6's handoff instructed. Specifically §9.3, §14 Phase 3B, §4.1, §10. Did not skim.
- (+) Reused `build_intake_graph()` exactly as the plan requires — one-kwarg addition, no rewrite. Phase 3A tests still all green after the change.
- (+) Parameterized the checkpointer with minimum blast radius. CLI/fixture path keeps `MemorySaver` default; web UI passes `SqliteSaver`. No other Phase 3A API touched.
- (+) Caught and fixed the `FixtureLLMClient` statefulness bug via the SQLite resume test. This is the kind of correctness issue the plan's explicit "across server restart" wording exists to catch, and I caught it via the test Session 6's plan specifically asked for. This made the Phase 3A code more robust — stateless test doubles are strictly better.
- (+) Recovered from the SSE hang without user intervention. Diagnosed (async loop under sync TestClient), redesigned (one-shot emission), documented the decision in the runner docstring AND the handoff.
- (+) Ran the §14 Phase 3B verification commands LITERALLY: pytest green, uvicorn starts, curl SSE returns an `event: snapshot` frame, curl resume redirects 303. Not paraphrased, not approximated.
- (+) 22 new tests, 201 total, 96.48% coverage — comfortably above the 90% floor. Coverage on `ui/intake/` modules: `__init__.py` 100%, `app.py` 98%, `runner.py` 98%, `templates.py` 97%. All remaining misses are on the production-only branches (lifespan shutdown, the Anthropic-factory lazy-import fallback).
- (+) Ran `uv run mypy src/model_project_constructor/ui/` — 0 errors in 5 files. Added the `-> AsyncIterator[None]` annotation the strict mypy wanted on the lifespan contextmanager. Did NOT touch the 33 pre-existing errors elsewhere — out of scope. Intake-package mypy also still clean.
- (+) Scope discipline: Phase 3B only. Did not start Phase 4. Did not touch the Data Agent. Did not rewrite the intake graph. The one Phase 3A code change (stateless fixture client) was load-bearing for the Phase 3B SQLite resume criterion and updated the existing Phase 3A test to match — a deliberate, minimum-blast-radius correctness fix, NOT a refactor.
- (+) Removed WAL-mode sibling files from git tracking via `.gitignore`. A future session running `git status` after `uv run uvicorn ... :app` will see a clean tree.
- (+) Recovered from three self-inflicted errors without user intervention: (1) `python-multipart` missing → added to `ui` extras; (2) `FixtureLLMClient` stateful reset → made stateless; (3) SSE polling loop hanging TestClient → redesigned as one-shot. All three documented in the chronological log and in the handoff gotchas where relevant.
- (−) Did NOT do the first real-API smoke test. Same deferral as Session 6. Acceptable — the session runner did not have an API key — but this is now the third consecutive session with the caveat, and Session 8 should treat it as overdue.
- (−) I was initially uncertain about the best way to expose the SSE endpoint lifetime (one-shot vs. streaming). I wrote the polling-loop version first and had to redesign. Cost: about 10 minutes. A future session building another SSE endpoint should read my runner/app design notes BEFORE starting.
- (−) Did not add an `INTAKE_DB_PATH`-aware default that lives outside cwd. The module-level `app = create_app()` creates `intake_sessions.db` in cwd at import time. I fixed this via `.gitignore` but a more correct fix would be a default like `~/.model_project_constructor/intake_sessions.db` or `:memory:`. Noted in gotchas; low priority but worth revisiting in Phase 6 hardening.
- (−) The `templates.py` module uses a 203rd-line code path (see coverage report) that is never exercised — a defensive `<em>(empty)</em>` fallback in `_render_kv`. I could have added a test for it, but it's a 1-line branch and the rest of the module is 97%. Left alone.

---

### What Session 6 Did
**Deliverable:** Phase 3A of architecture plan — Intake Agent core + LangGraph + CLI (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** Session-6 single commit (pending at close-out) — Phase 3A implementation + tests + fixtures + README/SESSION_NOTES updates.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES Session 5 block, architecture-plan §4.1/§5.1/§10/§14 Phase 3A, checked git, confirmed `methodology_dashboard.py` still absent (Session 5 precedent) and `gh issue list` still empty (UAT-only, per memory note). Reported findings, waited for user direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work (`claimed Session 6, work beginning`).
3. **LangGraph interrupt-pattern toy-graph verification** — Session 5's hard prerequisite. Built a throwaway 3-node graph (ask → decide → finalize) on langgraph 0.2.76 using `from langgraph.types import interrupt, Command` and `from langgraph.checkpoint.memory import MemorySaver`. Ran invoke → pause (interrupts surface via `state.tasks[0].interrupts[0].value`) → resume (`Command(resume=...)`) → loop → resume → finalize. Confirmed two critical behaviors: (a) interrupted node re-executes from the top on resume, so LLM calls CANNOT sit in the same node as `interrupt()`; (b) `Annotated[list, add]` reducers plus a later node returning full state causes list duplication. Both shaped the design below.
4. Created 12 TaskCreate items covering design, toy verification, implementation phases, tests, verification, and close-out.
5. Designed the intake state as a plain `TypedDict` with NO reducers — nodes return deltas only. Deliberate, documented in `state.py`.
6. Designed `IntakeLLMClient` as a 4-method Protocol (`next_question`, `draft_report`, `classify_governance`, `revise_report`) with dataclass result types (`NextQuestionResult`, `DraftReportResult`, `GovernanceClassification`, `InterviewContext`). Separate from the data agent's LLMClient by design — they share no methods and the data agent package cannot be imported from anyway (Phase 2B).
7. Implemented 8 graph nodes in `nodes.py` — split `plan_next_question` (LLM call, idempotent-relative) from `ask_user` (interrupt only). Same split for the review step: `await_review` has only `interrupt()`, no side effects. `evaluate_interview` enforces the 10-question cap. `revise` increments `revision_cycles` AND re-runs `classify_governance` because governance can shift when the draft changes. `finalize` computes `missing_fields` based on which caps were hit (`questions_cap_reached`, `revision_cap_reached`) and validates the full `IntakeReport` through Pydantic via `build_intake_report()`.
8. Built the compiled graph in `graph.py` using `StateGraph(IntakeState)` + `MemorySaver`. Routing: `evaluate_interview` → `draft_report` or back to `plan_next_question`; `await_review` → `revise` or `finalize` based on `review_accepted` and cap.
9. Built `FixtureLLMClient` and `load_fixture()` in `fixture.py` with schema validation (`intake_fixture/v1`), missing-field checks, and `revised_draft` override to exercise revision cycles. Wrote `IntakeAgent.run_scripted()` in `agent.py` — it drives the compiled graph one interrupt at a time against a scripted answer list, with an explicit max-turns safety so a buggy graph can't infinite-loop a test run.
10. Smoke-tested the full flow against an in-memory fixture before writing any tests or fixtures. Printed `status=COMPLETE, Q=7, tier=tier_3_moderate, target=successful_subrogation, value_low=2000000`. That proved interrupt/resume + the whole node chain works end-to-end on the installed langgraph version.
11. Built the CLI as a typer app. **Initial mistake:** I used the `@app.callback()` + `@app.command("run")` pattern (copying the data agent exactly), which meant the CLI required `python -m ... run --fixture`. The plan literally specifies `python -m ... --fixture` with no subcommand. Ran the plan's verification command, caught the discrepancy, rewrote the CLI as a single `@app.command()` with NO callback so typer auto-collapses. Added to handoff gotchas that the two CLIs take OPPOSITE decisions on the callback.
12. Registered `model-intake-agent` console script in `pyproject.toml`. Added `pyyaml>=6` as an explicit dependency (was already transitively installed). Ran `uv sync` and confirmed the script works.
13. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all 4 Protocol methods with prompts for each. Mirrors the structure of the data agent's Anthropic client (code-fence stripping, JSON parsing, `IntakeLLMError` on bad shapes) but with interview-specific prompts. Injected SDK client for test mocking; lazy-imports `anthropic` when constructed without a client.
14. Wrote 5 fixtures: `subrogation.yaml` (tier-3 tactical, the canonical worked example from `initial_purpose.txt`), `pricing_optimization.yaml` (tier-2 strategic, consumer-facing auto pricing), `fraud_triage.yaml` (tier-1 continuous, SIU routing), `intake_question_cap.yaml` (11 QA pairs + `draft_after: 99` forces the 10-question hard cap), `intake_revision_cap.yaml` (4 rejection reviews forces the 3-revision hard cap). Smoke-tested all 5 end-to-end; every plan §14 Phase 3A DONE criterion is observable from this fixture set.
15. Wrote 56 tests across 5 test files:
    - `test_fixture.py` (15 tests) — fixture loader happy path, schema mismatch, missing fields, wrong shape; `FixtureLLMClient` question dispensing, draft/governance return, revise-default vs revise-override, answer/review helpers, error paths for draft and governance missing fields.
    - `test_nodes.py` (14 tests) — unit tests for each node with a hand-rolled `_StaticLLM`, plus router tests for both conditional edges, plus `build_intake_report` end-state assembly tests at both the `COMPLETE` and `DRAFT_INCOMPLETE` path.
    - `test_graph.py` (9 tests) — end-to-end interrupt+resume runs against all 5 fixtures, including the two cap scenarios, plus error paths for under-supplied answer/review scripts and a review-accept-token variants test.
    - `test_cli.py` (7 tests) — `CliRunner` tests for help, happy-path stdout + file output, missing fixture, `--anthropic` not-yet-wired error, revision cap fixture producing `DRAFT_INCOMPLETE`, and a real `subprocess.run(['python', '-m', ...])` that matches the plan's literal verification command.
    - `test_anthropic_client.py` (14 tests, all mocked) — every Protocol method's happy path, missing-key errors, non-object-response errors, code-fence stripping, garbage-JSON errors, and the lazy-import default constructor path via `monkeypatch` on `anthropic.Anthropic`.
16. **First pytest run caught one bug:** `review_sequence_from_fixture({"review_sequence": []})` returned `["ACCEPT"]` instead of raising because `seq or ["ACCEPT"]` treated `[]` as falsy. Fixed to distinguish `None` (default) from `[]` (error). All 56 intake tests green after the fix.
17. Ran full suite: **179 passed, 96.18% coverage** (123 → 179; +56 intake tests). Coverage floor of 90% met. Intake package coverage: `nodes.py` 94%, `fixture.py` 100%, `graph.py` 100%, `anthropic_client.py` 98%, `cli.py` 100%, `agent.py` 90%, `protocol.py` 91%, `state.py` 100%, `__init__.py` 100%.
18. Ran both plan §14 Phase 3A verification commands LITERALLY:
    - `uv run pytest tests/agents/intake/ -v` → 56 passed.
    - `uv run python -m model_project_constructor.agents.intake --fixture tests/fixtures/subrogation.yaml` → writes a `COMPLETE` `IntakeReport` JSON; `status=COMPLETE, Q=7, tier=tier_3_moderate, cycle=tactical`.
19. Ran `uv run mypy src/model_project_constructor/agents/intake/` — initially 20 errors across 5 files. Fixed the easy wins (nodes None-guards, graph.py return annotation, cli.py helper method annotations, anthropic_client.py `list` generic parameter, one `# type: ignore[union-attr]` for the SDK's content block union mirroring the data agent's pattern, `# type: ignore[import-untyped]` on `import yaml`, `# type: ignore[arg-type]` on the `_DummyLLM` injection). **Final: 0 errors in 10 source files on the intake package alone.** The rest of the repo still has 33 pre-existing strict-mypy errors that predate Session 6 (most in the data agent's anthropic_client.py, same content-block union issue).
20. Updated `README.md`: added Phase 3A row (Complete), added Phase 3B row (Not started), added `agents/intake/` to the repo layout with a short module breakdown, added `tests/agents/intake/` to the tests section, added all 5 intake fixtures, updated test count 123 → 179, updated coverage floor 80% → 90%, added an intake agent CLI quick-start block pointing at the subrogation fixture.
21. Rewrote the `ACTIVE TASK` block for Phase 3B with: plan sections to re-read, DONE criteria, explicit instruction to reuse `build_intake_graph()` rather than re-implement, key Phase 3A files with file:line references, the LangGraph interrupt pattern verification results (so Session 7 doesn't redo the toy graph), all gotchas from Phase 2B + new ones from Phase 3A (CLI callback asymmetry, fixture schema, `_DummyLLM` disposability, mypy status, thread_id = session_id convention).
22. Close-out commit pending: all Phase 3A code + tests + fixtures + README + SESSION_NOTES as a single commit.

**Key design calls:**
- **Split `plan_next_question` from `ask_user`.** The plan's §10 diagram shows one `ASK_NEXT_Q` → `WAIT_FOR_ANS` node pair. I split them because the toy graph proved that interrupted nodes re-run from the top on resume, which would double-call the LLM if `interrupt()` sat in the same node. This is the single highest-leverage correctness decision in Phase 3A — getting it wrong would have caused silent cost doubling and potentially non-deterministic questions on resume.
- **No state reducers.** `Annotated[list, add]` is a footgun when a later node returns full state (the toy demonstrated this). All intake state fields are replaced wholesale by the node that owns them, and the `qa_pairs` append is done manually inside `ask_user`. Documented in the `IntakeState` docstring.
- **Fixture is NOT the CLI's production path, but it IS the verification path.** `--anthropic` is a real flag on the CLI that currently errors out with "interactive terminal not shipped in Phase 3A — use the web UI from Phase 3B". This keeps the CLI from locking in a headless-interview pattern that Phase 3B will supersede. The fixture path is the ONLY way to drive the CLI today.
- **`AnthropicLLMClient` is its own class, not shared with the data agent.** Different prompts, different result shapes, different system prompts. Session 5's handoff explicitly warned against "DRYing" the LLM boundaries and I followed it.
- **Default model `claude-sonnet-4-6` without live-API verification.** Same caveat as Session 5's data agent anthropic client. Documented in handoff as a likely first-real-run fixable.
- **`IntakeAgent.run_scripted()` with a hard max-turns cap.** A cap of `MAX_QUESTIONS + MAX_REVISIONS + 5 = 18` stops a buggy graph from spinning forever in tests. Hit the cap in the revision-cap fixture before I noticed the count — it triggered a `RuntimeError` with a clear message rather than hanging.
- **Fixture schema is `intake_fixture/v1`** with strict field validation in the loader. Tests cover schema-version mismatch, non-mapping YAML, missing required fields, and missing nested draft/governance fields. Fails loud, which is the §12 contract.
- **Review-accept tokens are a fixed set** — `"accept"`, `"yes"`, `"approve"`, `"approved"`, `"ok"`, `"looks good"` (case-insensitive). Anything else is treated as revision feedback. This is a heuristic, and the web UI in Phase 3B should use a button rather than text matching; the CLI path uses it because a fixture driver needs something to script.
- **Single-command typer app for intake CLI, the OPPOSITE of the data agent CLI.** The data agent has `run` as an explicit subcommand, which requires `@app.callback()` to defeat typer's auto-collapse. The intake agent has exactly one entry point, so the auto-collapse is what we want — without the callback, `python -m ... --fixture X` works directly and matches the plan's literal verification command. If Phase 3B adds a `serve` subcommand, the callback must be added simultaneously or the CLI verification breaks.

**Files created (16):**
- `src/model_project_constructor/agents/intake/__init__.py`
- `src/model_project_constructor/agents/intake/__main__.py`
- `src/model_project_constructor/agents/intake/state.py`
- `src/model_project_constructor/agents/intake/protocol.py`
- `src/model_project_constructor/agents/intake/nodes.py`
- `src/model_project_constructor/agents/intake/graph.py`
- `src/model_project_constructor/agents/intake/fixture.py`
- `src/model_project_constructor/agents/intake/agent.py`
- `src/model_project_constructor/agents/intake/anthropic_client.py`
- `src/model_project_constructor/agents/intake/cli.py`
- `tests/agents/intake/__init__.py`
- `tests/agents/intake/conftest.py`
- `tests/agents/intake/test_fixture.py`
- `tests/agents/intake/test_nodes.py`
- `tests/agents/intake/test_graph.py`
- `tests/agents/intake/test_cli.py`
- `tests/agents/intake/test_anthropic_client.py`
- `tests/fixtures/subrogation.yaml`
- `tests/fixtures/pricing_optimization.yaml`
- `tests/fixtures/fraud_triage.yaml`
- `tests/fixtures/intake_question_cap.yaml`
- `tests/fixtures/intake_revision_cap.yaml`

**Files modified (3):**
- `pyproject.toml` — added `pyyaml>=6`, added `[project.scripts] model-intake-agent`
- `uv.lock` — regenerated by `uv sync`
- `README.md` — Phase 3A complete, repo layout updated, test count 179, coverage 90% floor, intake CLI quick-start
- `SESSION_NOTES.md` — this file

**Session 5 Handoff Evaluation (Session 6 scoring Session 5):**
- **Score: 10/10**
- **What helped (ranked by how much time each saved):**
  1. The "LangGraph 0.2.76 interrupt pattern STILL not verified" gotcha with explicit "Build a 3-node toy graph before any real intake code. Failure mode: you write 400 lines of agent code against an API that doesn't exist on the installed version" — this was the single most load-bearing note in the entire handoff. I did exactly that, found two pitfalls (node re-execution on resume, reducer duplication), and the whole agent design downstream was shaped by those findings. Without this I would have put the LLM call in `ask_user` and shipped a broken-on-resume agent.
  2. The `How You Will Be Evaluated` section — pre-declared six success criteria. I used it as a close-out self-check. Items 2 (toy graph first) and 5 (don't bundle 3B) were the ones I was most tempted to shortcut.
  3. The typer single-command-trap gotcha with exact file:line — I initially copied the data agent's pattern (callback + run subcommand), then the plan's literal verification command forced me to flip it. Session 5's warning framed the trap so I recognised my error within minutes of first `pytest` instead of spending 20 minutes debugging.
  4. The "fixture format not defined in plan, YAML is more comfortable" guidance — took the decision off my plate.
  5. Key files with file:line references (`intake.py`, `common.py`, `llm.py:1-94`, `anthropic_client.py`) — I read each one cold and knew exactly where to look.
  6. The empty-`gh issue list` + dashboard-missing protocol notes — orientation step completed in about 30 seconds because Session 5 had already established these as non-blocking.
- **What was missing (minor):**
  1. Session 5 didn't specify whether the intake agent's CLI should reuse the data agent's `run` subcommand pattern or match the plan literal. I chose the data agent pattern first (wrong) and had to redo the CLI. A one-liner saying "plan's Phase 3A verification command is top-level flags, NOT a subcommand" would have saved about 10 minutes.
  2. Nothing about how the fixture's review_sequence should handle the cap-exhaustion case. I invented the `intake_revision_cap.yaml` pattern (review_sequence with 4 rejections) from first principles, which worked but could have been pre-decided.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state. The Session 5 `--fake-llm` escape-hatch framing correctly predicted that the intake agent would need its own fixture mode.
- **ROI:** Enormous. I estimate the handoff saved 60-90 minutes of re-derivation — the LangGraph verification guidance alone saved a full session of "why does my agent behave weirdly on resume". Read-cost was maybe 15 minutes.
- **Process notes:** Session 5 produced a 10/10 handoff by (a) pre-declaring evaluation criteria, (b) giving the next session an explicit technical risk to de-risk first, (c) naming traps with file:line breadcrumbs, (d) distinguishing "do these things" from "do not do these things" cleanly. I have copied all four patterns into my own handoff.

**Session 6 Self-Assessment:**
- (+) Completed Phase 0 orientation in full before any file touch. Wrote Phase 1B stub before any technical work. Reported findings and waited for user direction on a task-in-prompt turn.
- (+) Verified the LangGraph interrupt pattern on a toy graph BEFORE writing real agent code, per Session 5's explicit instruction. Caught two pitfalls (node re-execution, reducer duplication) that shaped the final design.
- (+) Split `plan_next_question` from `ask_user` at design time rather than after an expensive bug — direct result of the toy-graph discovery. This is the correctness decision I'm most proud of.
- (+) All 3 governance scenarios in tests hit distinct tiers (tier-1 continuous, tier-2 strategic, tier-3 tactical) with distinct rationales. Plan's "sensible classifications for 3 test scenarios" criterion is met with distinct, non-overlapping cases.
- (+) Both cap enforcement mechanisms have dedicated fixtures and dedicated tests. The 10-question cap and 3-revision cap are BOTH verified end-to-end through the real graph, not just at the node level.
- (+) Ran the plan's §14 Phase 3A verification commands LITERALLY. When my first CLI design didn't match the plan's literal command (it required `run` as a subcommand), I rewrote the CLI instead of updating the plan. Plan literal wins.
- (+) 56 new tests, 179 total, 96.18% coverage — comfortably above the 90% floor. Every intake source file is at ≥90% coverage; `fixture.py`, `graph.py`, `cli.py`, `state.py`, `__init__.py` are at 100%.
- (+) Ran mypy on the intake package and fixed every error — 0 errors in 10 files. Session 5 flagged not running mypy as a minor gap; I closed it. Did NOT fix the 33 pre-existing errors elsewhere in the repo — out of scope, noted in handoff.
- (+) Scope discipline: Phase 3A only. Did not start Phase 3B. Did not touch the Data Agent. Did not DRY the two `AnthropicLLMClient`s or the two `StrictBase` classes.
- (+) Recovered from three self-inflicted errors without user intervention: (1) wrong CLI subcommand pattern → rewrote as single command, (2) `review_sequence_from_fixture` treating empty list as None → fixed to distinguish, (3) mypy errors from missing type annotations → fixed with minimal `# type: ignore` use matching the data agent's patterns. All three documented in the chronological log and relevant ones in the handoff gotchas.
- (+) Used TaskCreate throughout — 12 tasks created up-front, each moved to in_progress when started, completed when done. No batching.
- (+) Handoff for Session 7 includes all required items: ACTIVE TASK updated with Phase 3B scope, what's done + commit reference, what's next with file:line references, key files, gotchas, evaluation criteria, LangGraph verification results so Session 7 doesn't redo it. Specifically guides Session 7 to REUSE `build_intake_graph()` rather than re-implement the flow.
- (−) I wrote the CLI twice — first with the data agent's callback+subcommand pattern, then as a single command. That cost ~10 minutes. Could have been avoided by reading the plan's verification command literal first, which I did but mis-interpreted. Self-inflicted, recoverable.
- (−) The `_DummyLLM` in `cli.py` is an ugly workaround for `IntakeAgent.__init__` requiring a client even when `run_with_fixture` will immediately replace it. A cleaner design would have `IntakeAgent` construct the graph lazily on first run. Noted for Phase 3B to clean up if a long-lived agent makes sense there.
- (−) The `AnthropicLLMClient` was never exercised against a real API. Same caveat as Session 5's data agent client. I did not attempt a live smoke test (no API key available in this session). Flagged in the handoff, but someone will discover whether `claude-sonnet-4-6` is a valid model ID on first real run.
- (−) I did NOT add a symmetric AST decoupling test for the intake agent (walking `src/model_project_constructor/agents/intake/` for imports matching `model_project_constructor_data_agent`). Session 5's handoff didn't require it, and the decoupling direction the plan enforces is data-agent-does-not-depend-on-main-package, not the reverse. Adding a symmetric test would be testing a non-existing relationship. Explicitly decided not to add it; noted in handoff.
- (−) The three governance fixtures are a MINIMUM — two of the four cycle-time values are covered (tactical, strategic, continuous) but `operational` is not. If a future Phase 3B or 3A polish session wants comprehensive governance-matrix coverage, that's an easy add.
- (−) I moved the toy graph work out of process before writing a test for it — the verification was shell output, not a committed test. The test files exercise the `interrupt` machinery implicitly through `test_graph.py`, so the pattern IS tested, but there's no standalone "langgraph 0.2.76 interrupt API exists" test. This is intentional (the implicit coverage is sufficient) but worth noting — if langgraph bumps major version and the API shifts, that test suite will fail loudly but the error might blame the intake code rather than the library.
- (−) No `USAGE.md` for the intake agent. The data agent has one (it's a separate distributable package so it needs its own readme); the intake agent lives in the main package and is documented in the main README. This is consistent but a dedicated document would be more discoverable for web-UI users in Phase 3B. Not in scope for 3A.

**Score: 9.5/10.** Phase 3A delivered with:
- Full LangGraph flow from §10 correctly implemented (with the interrupt-re-execution pitfall avoided)
- Both plan §14 verification commands passing literally
- 3 distinct governance scenarios tested end-to-end
- Both hard caps enforced end-to-end with dedicated fixtures
- Full Pydantic validation at the boundary
- 56 new tests, 96.18% coverage
- mypy clean on the intake package (which Session 5 flagged as a gap)
- Session 7 handoff that reuses Session 5's pattern language

Loses half a point for the CLI rewrite (self-inflicted, recovered without user intervention) and for not attempting a real-API smoke test of `AnthropicLLMClient`. The `_DummyLLM` ugliness and missing `USAGE.md` are intentional debts rather than mistakes.

---

### What Session 5 Did
**Deliverable:** Phase 2B of architecture plan — Data Agent standalone subpackage + CLI + Python API + AnthropicLLMClient (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `4982332` (refactor move) + `aca858a` (CLI + Anthropic + docs) + session-5 closeout (this commit). See `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan §7/§14 Phase 2B, checked git. Flagged two protocol gaps: `methodology_dashboard.py` does not exist (SESSION_RUNNER.md step 5 references an absent tool); `gh issue list` returns empty (user confirmed UAT-only, saved to memory at `~/.claude/projects/.../memory/project_issue_tracker.md`).
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Presented three restructuring approaches (a/b/c) to the user with pros/cons and recommended (c). User approved (c) on `/effort max`.
4. Read every existing Data Agent source file and every file importing from the data agent (conftest, test_data_agent, schemas/v1/__init__.py, schemas/registry.py) to map every internal import and every test-facing name. This is what let the shim layer preserve Phase 2A tests unchanged.
5. Created 13 tasks in TaskCreate covering the two-commit execution plan + closeout.
6. Built `packages/data-agent/` skeleton + `pyproject.toml` (no `readme` field initially — added it back in commit B after USAGE.md existed).
7. Wrote `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` as the new canonical home for `DataRequest/DataReport/PrimaryQuery/QualityCheck/Datasheet/DataGranularity` + its own 3-line `StrictBase`. Two `StrictBase` classes now exist (main + standalone); deliberate per Option (c) tradeoff.
8. Wrote/moved 8 agent source files into the standalone: `db.py`, `sql_validation.py`, `llm.py`, `state.py`, `nodes.py`, `graph.py`, `agent.py`, `__init__.py`. All internal imports rewritten from `model_project_constructor.agents.data.*` to `model_project_constructor_data_agent.*` and from `model_project_constructor.schemas.v1.data` to `model_project_constructor_data_agent.schemas`. Git detected all 5 moves as renames with 85–100% similarity.
9. Replaced main-package files with thin re-export shims: `agents/data/{__init__,db,llm}.py` and `schemas/v1/data.py`. Deleted `agents/data/{agent,graph,nodes,state,sql_validation}.py`.
10. Wired uv workspace in root `pyproject.toml`: `[tool.uv.workspace] members = ["packages/*"]` + `[tool.uv.sources]` + added `model-project-constructor-data-agent` as a dep. Updated pytest/coverage/mypy to walk both source trees.
11. Rewrote `tests/test_data_agent_decoupling.py` to walk the standalone's source AND the main-package shims (two test functions now, defense in depth).
12. **Error recovery #1:** First `uv sync` attempt failed because my `[tool.uv.workspace]` edit sliced `ui`/`dev` out of `[project.optional-dependencies]`. Fixed by moving the uv sections to after the optional-dependencies table.
13. **Error recovery #2:** Second `uv sync` failed because the standalone's `pyproject.toml` declared `readme = "USAGE.md"` which did not exist yet. Removed the field temporarily, re-added it in commit B.
14. `uv sync` succeeded; both packages built editable. Ran full suite: **102 passed, 98.66% coverage** (+1 test from decoupling split, +0.04 pts coverage — essentially flat).
15. Verified the decoupling test actually fires by injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`, running the test (failed as expected with both forbidden tokens reported), and reverting.
16. **Commit A:** `refactor(phase-2b): move data agent to standalone package` — `4982332`. 17 files changed, 476+/247−, 5 renames detected.
17. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all four `LLMClient` protocol methods. Default model `claude-sonnet-4-6`. `_call_claude` centralises the SDK call; `_extract_json` handles code-fence stripping; `LLMParseError` propagates unparseable responses through the outer try/except as `EXECUTION_FAILED`.
18. Wrote `cli.py` — `typer` app with `run` subcommand. Flags: `--request`, `--output`, `--db-url`, `--model`, `--fake-llm`. `--fake-llm` uses an in-file `_FakeCLIClient` that returns canned deterministic responses so CI can exercise the CLI end-to-end without an API key.
19. **Error recovery #3:** First CLI test failed with "Got unexpected extra argument (run)" — typer auto-collapses single-command apps. Fixed by adding `@app.callback() def _main()` above the command, which promotes the app to a group. Flagged in the handoff gotchas for future sessions.
20. Wrote `__main__.py` to support `python -m model_project_constructor_data_agent`.
21. Wrote `tests/fixtures/sample_request.json` (canonical DataRequest fixture, used by CLI tests AND the USAGE.md CLI example).
22. Wrote `tests/data_agent_package/test_cli.py` — 5 tests covering: happy path without db, happy path with live SQLite (creates a `claims` table in `tmp_path`), missing-file error, help output, and `python -m` entry point via subprocess.
23. Wrote `tests/data_agent_package/test_anthropic_client.py` — 16 tests with a `_FakeAnthropic` / `_FakeMessages` harness that mocks at the `client.messages.create` boundary. Covers: protocol conformance, JSON parsing for each method, code-fence stripping, retry hint propagation, malformed-response errors for all 4 methods, `_extract_json` edge cases, and the default constructor path via `monkeypatch` on `anthropic.Anthropic`.
24. Wrote `packages/data-agent/USAGE.md` with three examples (CLI, Python script, Python notebook), full public API listing, and error-contract documentation. Interpreted the plan's explicit requirement for USAGE.md as authorisation (CLAUDE.md forbids autonomously creating docs files; this one is a plan deliverable).
25. Restored `readme = "USAGE.md"` in `packages/data-agent/pyproject.toml`. `uv sync` succeeded.
26. Ran the three plan §14 Phase 2B verification commands:
    - `uv run python -c "from model_project_constructor_data_agent import DataAgent"` → **ok** (`model_project_constructor_data_agent.agent`)
    - `uv run model-data-agent run --request tests/fixtures/sample_request.json --output /tmp/report.json --fake-llm` → **COMPLETE**, 1 query, schema_version 1.0.0
    - Full suite: **123 passed, 96.45% coverage**
27. **Commit B:** `feat(phase-2b): AnthropicLLMClient + typer CLI + Python API docs` — `aca858a`. 9 files created, 1089+ lines.
28. Updated README.md (user-requested during closeout): marked Phase 2B Complete, added standalone package to repo layout, updated test count 101 → 123, added CLI quick-start pointing at USAGE.md.
29. Phase 3A handoff written for Session 6 (full rewrite of ACTIVE TASK), Session 4 evaluation below, self-assessment below. Closeout commit pending.

**Key design calls:**
- **Option (c) restructure** — moved data agent + data schemas into standalone; main package re-exports. Picked over (a) vendored copy (divergence risk) and (b) re-export shim (fake physical decoupling). Cost: two `StrictBase` classes, ~10 moved files, one afternoon. Benefit: the standalone could be published to PyPI tomorrow and has provably zero dependency on the main package.
- **Two commits, not one.** Commit A is a pure-refactor move that keeps 102 tests green through the shim layer (one more than 2A's 101 because of the decoupling test split). Commit B adds all new behavior (AnthropicLLMClient, CLI, USAGE, tests). This makes the diff reviewable — the move and the feature work can be audited independently.
- **LLMClient Protocol stays on the data agent side.** The intake agent in Phase 3 should define its own Protocol, not share this one. They have nothing in common at the method level.
- **AnthropicLLMClient takes an injected `client`** so tests can mock at the SDK boundary. Construction without a `client` arg lazily imports `anthropic` and constructs `Anthropic()` (reads `ANTHROPIC_API_KEY`). One test covers this path via `monkeypatch` on `anthropic.Anthropic`.
- **`--fake-llm` is a real CLI flag, not hidden.** It's visible in `--help` but documented in USAGE.md as smoke-test-only. CI can exercise the full CLI path without an API key; this keeps test_cli.py tests green in any environment.
- **`_FakeCLIClient` is colocated with the CLI** rather than in tests. Justification: it's a runtime feature (the `--fake-llm` flag), not a test-only utility. Moving it to tests would mean the CLI imports from tests, which is wrong.
- **Two canonical `StrictBase` classes, two decoupling test functions.** Duplication is acknowledged and documented; both the schemas module docstring (`packages/data-agent/.../schemas.py:10`) and SESSION_NOTES gotchas explicitly flag that this is deliberate.
- **CLI subcommand trap fix** (`@app.callback()`) — typer's single-command auto-collapse bit me on the first test run. Fixed in one edit. Documented for future CLIs (the intake agent will need the same trick).
- **`claude-sonnet-4-6` as default model** — set from the system-reminder's stated current model family, NOT verified against a live API. Flagged in the handoff as a likely first-real-run failure if the model ID is wrong. Tests all mock the SDK so they don't care.

**Files created (14):**
- `packages/data-agent/pyproject.toml`
- `packages/data-agent/USAGE.md`
- `packages/data-agent/src/model_project_constructor_data_agent/__init__.py`
- `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`
- `packages/data-agent/src/model_project_constructor_data_agent/db.py`
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py`
- `packages/data-agent/src/model_project_constructor_data_agent/llm.py`
- `packages/data-agent/src/model_project_constructor_data_agent/state.py`
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py`
- `packages/data-agent/src/model_project_constructor_data_agent/graph.py`
- `packages/data-agent/src/model_project_constructor_data_agent/agent.py`
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`
- `packages/data-agent/src/model_project_constructor_data_agent/cli.py`
- `packages/data-agent/src/model_project_constructor_data_agent/__main__.py`
- `tests/data_agent_package/__init__.py`
- `tests/data_agent_package/test_cli.py`
- `tests/data_agent_package/test_anthropic_client.py`
- `tests/fixtures/sample_request.json`

**Files moved (5, via git rename detection):**
- `agents/data/agent.py` → `packages/data-agent/.../agent.py` (95% similarity)
- `agents/data/graph.py` → `packages/data-agent/.../graph.py` (85%)
- `agents/data/nodes.py` → `packages/data-agent/.../nodes.py` (89%)
- `agents/data/sql_validation.py` → `packages/data-agent/.../sql_validation.py` (100%)
- `agents/data/state.py` → `packages/data-agent/.../state.py` (88%)

**Files modified (7):**
- `pyproject.toml` (workspace + coverage + mypy)
- `src/model_project_constructor/agents/data/__init__.py` (re-export shim)
- `src/model_project_constructor/agents/data/db.py` (shim)
- `src/model_project_constructor/agents/data/llm.py` (shim)
- `src/model_project_constructor/schemas/v1/data.py` (shim)
- `tests/test_data_agent_decoupling.py` (walk standalone + shim, 2 test functions)
- `README.md` (Phase 2B status + repo layout + test count + CLI quick-start)
- `uv.lock` (workspace resolution)
- `SESSION_NOTES.md` (this file)

**Session 4 Handoff Evaluation (Session 5 scoring Session 4):**
- **Score: 10/10**
- **What helped:** Session 4's ACTIVE TASK block was load-bearing from the first minute:
  1. The three restructuring options (a/b/c) with Session 4's explicit note that (c) is cleanest but "do it in Plan Mode or commit the move as a standalone commit" — I adopted exactly that structure (commit A = pure move, commit B = new features). Without this guidance I probably would have bundled everything into one commit and the reviewability would have suffered.
  2. The "plan inconsistency" flag on `python -m model_project_constructor.agents.data --help` being a Phase 2B entry point correctly predicted that I'd need `__main__.py`.
  3. The Key Files section with line ranges (`llm.py:1-94`, `agent.py:34-74`, `nodes.py:1-171`) was surgical — saved me from re-reading entire files when I only needed import shapes.
  4. The schema-plan reconciliation note (`DataReport.status` as authoritative vs. `qc_status`/`primary_query_status`) meant I preserved the Phase 2A test interpretation without re-deriving it.
  5. The "FakeLLMClient is the only implementation" warning + "don't tie the CLI to the fake" instruction directly shaped my design: I built `AnthropicLLMClient` first, then the CLI, with the fake as an explicit escape hatch flag rather than the default.
  6. The "SQLite resource leak" note and the coverage 98.62% baseline meant I knew what to expect and could notice immediately when I hit 96.45% (with full context of why — new CLI/Anthropic code has defensive paths).
- **What was missing:** Almost nothing. Two tiny gaps:
  1. Session 4 didn't flag that `methodology_dashboard.py` doesn't exist — I discovered this during orientation. Saved me maybe 30 seconds, but the Phase 0 checklist's step 5 explicitly references a non-existent tool, which is a protocol-level gap Session 4 could have flagged.
  2. Session 4's gotcha about "do the move in Plan Mode or as a standalone commit" didn't preemptively address whether user approval was required for the restructure. I spent a turn getting buy-in (correct per SAFEGUARDS) but Session 4 could have pre-authorized this for me by framing it as pre-approved since the plan requires it.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state.
- **ROI:** Very high. I estimate reading the Phase 2B ACTIVE TASK block + the relevant plan sections saved me 45+ minutes of architecture re-derivation and at least one false start (probably would have gone for Option (b) as "safer" without the explicit "don't fake the decoupling" framing).
- **Process notes:** Session 4 wrote the Phase 1B stub, held the phase boundary (Phase 2A only, no CLI), addressed every Session 3 gotcha, and produced a handoff I could score against my own. The `How You Will Be Evaluated` section at the bottom of the ACTIVE TASK block is a pattern I should preserve.

**Session 5 Self-Assessment:**
- (+) Followed Phase 0 orientation fully. Phase 1B stub written before the first technical action. Phase 0 flagged two protocol gaps (missing dashboard, empty issue tracker) and saved one to memory.
- (+) Asked for architectural approval BEFORE touching code on a cross-module refactor, per SAFEGUARDS "Refactoring always requires plan mode approval". User approved (c) and I executed only (c).
- (+) Read every file whose imports would change BEFORE making changes — conftest.py, test_data_agent.py, tests/schemas/*, schemas/v1/__init__.py, registry.py. This is why the shim layer worked on the first try and zero test files needed to be edited.
- (+) Two-commit structure: pure refactor first (102 tests green through shims), then feature additions. Commit A is 17 files changed with 5 git-detected renames, reviewable as a move; commit B is 9 new files, reviewable as feature work. Followed Session 4's explicit advice.
- (+) Verified the decoupling test actually fires on injected violation before committing — Session 4's "don't treat it as passive scenery" guidance held.
- (+) Scope discipline: Phase 2B only. No intake work, no LangGraph interrupt investigation, no schema cleanup. Phase 3 is Session 6's.
- (+) Three plan §14 Phase 2B verification commands all passed explicitly; ran them separately, not just as part of the full suite.
- (+) `AnthropicLLMClient` has 16 tests covering every protocol method, every JSON-parse path, code-fence stripping, retry hint, and default-construction via monkeypatch. The CLI has 5 tests including a real-subprocess `python -m` smoke test.
- (+) Recovered from three self-inflicted errors without user intervention: (1) pyproject.toml structural edit mistake, (2) missing readme file referenced in pyproject.toml, (3) typer single-command auto-collapse trap. All three recoveries documented in the handoff so Session 6 knows the shape of the traps.
- (+) Used TaskCreate/TaskUpdate to track the 13 sub-tasks of a two-commit refactor. Each task was marked in_progress when started and completed when done, not batched at the end.
- (+) Saved one memory (project_issue_tracker.md) — user said GitHub issues are UAT-only; this will inform every future Phase 0 that currently treats empty `gh issue list` as a gap.
- (−) Did not run `mypy` (not in the §14 Phase 2B verification commands, but `strict = true` is in `pyproject.toml:80`). The one `type: ignore[arg-type]` inherited from Phase 2A at `agent.py:138` is still there. Any `AnthropicLLMClient`-level type errors (e.g., around the untyped `client: Any | None`) are uncaught.
- (−) Session 4's "SQLite resource leak" in `seeded_sqlite_url` fixture still leaks the engine handle. I added more tests that exercise the same fixture and did not fix the leak. Still non-blocking.
- (−) `claude-sonnet-4-6` as `DEFAULT_MODEL` is a guess from the system-reminder model family list. It is NOT verified against a live Anthropic API call — no `ANTHROPIC_API_KEY` in this session. If the actual model ID is something slightly different, the CLI will fail on first real-API invocation. Flagged in the handoff gotchas; the CLI `--model` flag lets users override.
- (−) I did not build a concrete integration-style test that skips when `ANTHROPIC_API_KEY` is absent — Session 4 specifically suggested this pattern. Decided against it: all tests mocking the SDK gives deterministic coverage; an integration test that conditionally runs is harder to reason about and tends to rot. A future hardening pass (Phase 6) can add one.
- (−) The CLI has a small dead-code path at `cli.py:119` (error handling around `_load_request`) that isn't covered. Same for `__main__.py` lines 3-6. Acceptable — they're defensive paths that only fire on environment-level failure.
- (−) README.md update happened during closeout at user request rather than being part of the plan. That's not a mistake, but it suggests README maintenance should be in the default closeout checklist for session boundaries that ship a user-facing feature. Adding to learnings.
- (−) Did not verify the LangGraph interrupt pattern — Session 4 flagged this as a Phase 3A concern. Correct to defer. But Session 6 MUST verify it first, and my handoff should make that boringly explicit (it does).

**Score: 9/10.** Phase 2B delivered with a clean two-commit refactor, all plan verifications green, 123 tests passing, decoupling guarantee preserved and re-verified, and a rich handoff. Loses a point for the unverified `DEFAULT_MODEL` string (real first-run will probably expose it) and for not running mypy. The error-recovery count (three self-inflicted mistakes) is acceptable given all three were caught and corrected without user intervention and left clear warning breadcrumbs for Session 6.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not adding this session. Pattern candidates for future sessions: (a) "When a plan requires a cross-module refactor, the user-approval gate is the first step of the session, not a mid-session pause" — getting buy-in before any file touch prevents half-committed state; (b) "Typer single-command apps silently collapse the subcommand unless an `@app.callback()` is present" — worth a one-line entry in the Python idioms section once one exists. Not retroactively adding.

### What Session 4 Did
**Deliverable:** Phase 2A of architecture plan — Data Agent core + LangGraph + AST decoupling test (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `chore(env)` (env bootstrap) + `feat(phase-2a)` (agent + tests) + `docs/chore` session closeout — see `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md §4.2/§7/§10.2/§12/§14 Phase 2A, git status, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Addressed Session 3's environment trap: `brew install uv` (got 0.11.6), `uv python install 3.11` (got 3.11.15 but the venv resolved to 3.13.5 because `requires-python = ">=3.11"` is inclusive — acceptable).
4. `uv sync --extra agents --extra dev` failed on a missing `README.md` referenced by pyproject.toml. Removed the `readme` line rather than auto-create a README (CLAUDE.md forbids creating docs files autonomously). `uv sync` then succeeded. Re-ran Phase 1 tests under the new interpreter: 88 passed, 100% schemas coverage.
5. Checkpoint-committed env bootstrap before touching agent code (SAFEGUARDS "commit before starting any new task").
6. Verified LangGraph 0.2.76 on a toy graph (conditional edges, `add_conditional_edges` with router function, partial-update dict returns, `.invoke()` merge semantics). Worked as expected.
7. Designed the Data Agent package layout with clean separation: `llm.py` (Protocol + dataclasses), `sql_validation.py`, `db.py`, `state.py`, `nodes.py` (factory functions closing over llm/db), `graph.py` (StateGraph assembly), `agent.py` (outer `DataAgent.run()`).
8. Made a deliberate decision NOT to ship a concrete `AnthropicLLMClient` in 2A — deferred to 2B — to avoid a half-finished implementation (global rule) and keep Phase 2A strictly scoped.
9. Wrote all 8 source files under `src/model_project_constructor/agents/data/` and verified imports.
10. Wrote `tests/agents/data/conftest.py` (seeded SQLite claims table with 5 rows, sample DataRequest, valid PrimaryQuerySpec, QC specs, SummaryResult, Datasheet fixtures).
11. Wrote `tests/agents/data/test_data_agent.py` — `FakeLLMClient` (deterministic stub with a `primary_queries_sequence` list that drives RETRY_ONCE and fail-after-retry) + 12 end-to-end tests: protocol check, happy path against real SQLite, RETRY_ONCE success, retry-exhausted → EXECUTION_FAILED, DB-unreachable via bad URL, DB=None, per-QC error isolation, INCOMPLETE_REQUEST parametrised over all four required fields, and unexpected-exception containment via an `ExplodingLLM` subclass.
12. Wrote `tests/test_data_agent_decoupling.py` — AST-walks every `.py` under `agents/data/`, asserts no import references `IntakeReport`, `schemas.v1.intake`, or `intake_report`.
13. **Verified the decoupling test actually fires** by temporarily injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`. Test failed as expected, reporting both `IntakeReport` and `schemas.v1.intake` as offenders with the exact file path. Reverted the injection.
14. Ran §14 Phase 2A verification commands:
    - `uv run pytest tests/agents/data/ -v` → 12 passed
    - `uv run pytest tests/test_data_agent_decoupling.py` → 1 passed
    - Full suite: `uv run pytest -q` → 101 passed, coverage 98.62% (well above 80% gate)
    - Skipped `python -m model_project_constructor.agents.data --help` because that CLI is a Phase 2B deliverable (flagged as a plan inconsistency in the commit and the new handoff).
15. Committed Phase 2A under `feat(phase-2a): Data Agent core + LangGraph flow + AST decoupling test`.
16. **Late-session user addition:** create `README.md` and push to a new remote `https://github.com/rmsharp/claims-model-starter.git`. README created (explicit user authorisation overrides the CLAUDE.md prohibition). Remote `origin` added; `git push -u origin master` sent all history.
17. Rewrote ACTIVE TASK for Phase 2B, wrote this Session 4 closeout.

**Key design calls:**
- `LLMClient` is a `Protocol` rather than an ABC. Runtime-checkable for tests. Methods take typed domain objects and return typed domain objects — nodes never parse JSON.
- Intermediate `PrimaryQuerySpec`/`QualityCheckSpec`/`SummaryResult` dataclasses exist so LLM output and schema output can evolve independently. Downstream pydantic models are the enforcement point.
- `expected_row_count_order` typed as `str` on the intermediate spec but enforced as `Literal[...]` on the pydantic `PrimaryQuery`. Noted in the module docstring.
- Node factories (`make_*`) close over `llm` and `db` so node bodies take only `DataAgentState`. This keeps the StateGraph plumbing orthogonal to dependency injection.
- `DataAgentState` is a `TypedDict(total=False)` so nodes can populate incrementally. Initial state has `request`, `sql_retry_count=0`, `db_executed=False`.
- QC `PASSED/FAILED` uses a coarse ≥1-row proxy. Sufficient to exercise all four `execution_status` values; richer expectation evaluation is future work.
- Schema-plan reconciliation: plan §4.2 text references `qc_status` and `primary_query_status` fields that don't exist on the Phase 1 schemas. Session 4 interpreted the three-valued `DataReport.status` as authoritative — DB-down returns COMPLETE with per-QC NOT_EXECUTED, invalid SQL after retry returns EXECUTION_FAILED, missing/vacuous fields return INCOMPLETE_REQUEST. Documented in the commit and the new handoff.
- No `AnthropicLLMClient` in 2A. Deferred to 2B's CLI work to avoid half-finished implementations.
- README removed from pyproject.toml rather than auto-created (CLAUDE.md rule); README.md itself was created only after the user explicitly asked.

**Files created (15):**
- `src/model_project_constructor/agents/__init__.py`
- `src/model_project_constructor/agents/data/{__init__,llm,sql_validation,db,state,nodes,graph,agent}.py`
- `tests/agents/__init__.py`
- `tests/agents/data/{__init__,conftest,test_data_agent}.py`
- `tests/test_data_agent_decoupling.py`
- `README.md`
- `uv.lock`

**Files modified (3):**
- `pyproject.toml` (removed stale `readme = "README.md"` line)
- `SESSION_NOTES.md` (this file)

**Session 3 Handoff Evaluation (Session 4 scoring Session 3):**
- **Score: 10/10**
- **What helped:** The ACTIVE TASK block was the highest-quality handoff in the project so far. Every single gotcha fired during my session:
  1. The `uv` / Python 3.10 trap was item #1 in gotchas — I hit it immediately and had the fix ready (brew install uv, uv python install 3.11).
  2. The "LangGraph pattern unverified" flag drove me to write the toy graph before the real flow — saved me from discovering the state-merge semantics mid-implementation.
  3. The "decoupling test must actually fire" warning was the difference between writing theater and writing a real test. I explicitly verified it fires on an injected violation.
  4. The "three-valued status field, set each one explicitly" note drove the schema-plan reconciliation decisions.
  5. The "agents do NOT raise for expected failures (§12)" note drove the outer try/except in `DataAgent.run()`.
  The Key Files section with `data.py:21-98` and `common.py:13-31` line ranges was surgical — saved re-reading whole files.
- **What was missing:** Almost nothing. One gap: Session 3 didn't flag that `pyproject.toml` references a README.md that doesn't exist. `uv sync` would have hit it immediately on any fresh checkout. Worth ~3 minutes of my time. Not a 10→9 penalty because Session 3 didn't run `uv sync` themselves (they ran `python3 -m pytest`), so they couldn't have known.
- **What was wrong:** Nothing. The handoff was accurate end-to-end. The `database_hint` interpretation note was correct; the `StrictBase` `protected_namespaces` note was correct; the Phase 1 file line ranges matched.
- **ROI:** Very high. I estimate reading SESSION_NOTES.md + the plan sections saved me 60+ minutes of discovery and at least one wrong-direction start. The "verify decoupling test fires" instruction alone was worth the entire read.
- **Process notes:** Session 3 wrote the Phase 1B stub, held the phase boundary, and produced a handoff that was demonstrably load-bearing. This is the quality bar for the project.

**Session 4 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before any work. Phase 1B stub written before the first technical action.
- (+) Addressed every trap Session 3 flagged: installed uv, pinned 3.11+ via uv, verified LangGraph on a toy graph before wiring the real flow, verified the decoupling test actually fires.
- (+) Scope discipline: Phase 2A only. No CLI, no standalone subpackage, no Anthropic client, no intake work. Explicit decision to skip the plan's §14 Phase 2A CLI smoke test because it belongs to 2B.
- (+) Clean separation of concerns: `LLMClient` Protocol, intermediate dataclasses, node factories, graph assembly, outer agent boundary. Every concrete concern is in exactly one file.
- (+) Test coverage 98.62% total, 100% on every new agent module except `db.py:42` (defensive `RuntimeError`) and `sql_validation.py:25,28` (defensive parse branches). All three uncovered lines are intentionally defensive and documented.
- (+) Parametrised the INCOMPLETE_REQUEST test over all four required fields so regressions in the semantic-check list get caught.
- (+) `ExplodingLLM` test proves the outer try/except in `DataAgent.run()` actually catches graph-internal exceptions and surfaces them as `EXECUTION_FAILED` — a critical part of the §12 contract.
- (+) Commit discipline: env bootstrap committed as a standalone checkpoint before agent code was touched (SAFEGUARDS "commit before starting any new task"). Agent code committed as one `feat(phase-2a)` commit. README + remote-push as their own commits at the end.
- (+) Schema-plan reconciliation decisions are documented in the commit body AND in the new handoff — future sessions can see what was interpreted and why.
- (+) Flagged a plan inconsistency (§14 Phase 2A verification list contains a CLI command that belongs to 2B) in the commit, in the handoff, and verbally to the user.
- (−) Did not build a concrete `AnthropicLLMClient`. Defensible decision (avoids half-implementation), but 2B will need one and may feel the pinch.
- (−) The `validate_sql` function is deliberately weak — it only rejects empty/whitespace and `UNKNOWN` statement type. `sqlparse` will accept a lot of garbage as "valid." A sharper validator (e.g., `EXPLAIN` against SQLite) would catch more, but it would also couple validation to the DB. Deferred.
- (−) Did not run `mypy` (not in §14 Phase 2A verification commands, but `mypy strict = true` is in `pyproject.toml:71`). Some `type: ignore[arg-type]` on line `agent.py:124` where I pass `str` into a `Literal[...]` field — pydantic validates at runtime.
- (−) ResourceWarning: unclosed SQLite connections in a few tests (the `seeded_sqlite_url` fixture leaks an engine handle). Non-blocking; clean up in 2B or a Phase 6 hardening pass.
- (−) Did not pin `--python 3.11` on the venv; `.venv` resolved to 3.13.5. The code is 3.11-compatible so this is not a bug, but the plan said "pin a 3.11+ interpreter" and I got a 3.13 interpreter that happens to satisfy `>=3.11`. Documented in the handoff.

**Score: 9/10** — Phase 2A delivered with comprehensive tests, proven decoupling guarantee, all known traps addressed, and strict scope adherence. Loses a point for the resource leak in the SQLite fixture and for not shipping even a stub `AnthropicLLMClient` that 2B could extend. The `mypy` gap is noted but not weighted against the score since it wasn't in the verification commands.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. Pattern candidates for future sessions: (a) "LLM-driven agents: ship a Protocol + FakeClient in the core phase; defer concrete vendor integration to the CLI phase" and (b) "decoupling tests must be verified to actually fire by temporarily injecting a violation — a green-only history means nothing." These are in the handoff prose for now; I'll not retroactively add them unless a future session asks.

### What Session 3 Did
**Deliverable:** Phase 1 of architecture plan — Repo Skeleton + Schemas (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md in full (both halves), checked git, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Probed environment: `uv` not installed; system Python is 3.10.12 with pydantic 2.12.5 and pytest 9.0.2 already available. Decided to keep `pyproject.toml` strictly compliant with the plan (requires-python >=3.11, uv-ready) and run local tests via `python3 -m pytest`, flagging the Python-version gap for Phase 2A.
4. Wrote `pyproject.toml` — PEP 621 + hatchling, `model-project-constructor` package at `src/model_project_constructor`, core dep `pydantic>=2.6,<3`, optional groups `agents` / `ui` / `dev`. Pytest config includes `pythonpath = ["src"]` so tests run without manual `PYTHONPATH`. Per-session-3 user directive, added `pytest-cov` with `--cov-fail-under=80`.
5. Implemented `schemas/v1/common.py` (`StrictBase` with `extra="forbid"`, `protected_namespaces=()`, plus `CycleTime`, `RiskTier`, `ModelType`, `SCHEMA_VERSION`).
6. Implemented `schemas/v1/intake.py` — `ModelSolution`, `EstimatedValue`, `GovernanceMetadata`, `IntakeReport`. All inherit `StrictBase`.
7. Implemented `schemas/v1/data.py` — `DataGranularity`, `DataRequest`, `QualityCheck`, `Datasheet`, `PrimaryQuery`, `DataReport`. Module docstring forbids importing from `intake.py` (runtime AST test comes in Phase 2A per the plan).
8. Implemented `schemas/v1/gitlab.py` — `GitLabTarget`, `GovernanceManifest`, `GitLabProjectResult`.
9. Implemented `schemas/v1/__init__.py` re-exporting everything public.
10. Implemented `schemas/envelope.py` — `HandoffEnvelope` with its own `envelope_version="1.0.0"` and `payload: dict[str, Any]` (resolved by registry, not by envelope).
11. Implemented `schemas/registry.py` — `REGISTRY`, `SchemaKey`, `UnknownPayloadError(KeyError)`, `load_payload(envelope)`.
12. Wrote `tests/schemas/fixtures.py` — `make_*` factories for every schema.
13. Wrote `tests/schemas/test_intake.py`, `test_data.py`, `test_gitlab.py`, `test_envelope_and_registry.py` — 88 tests total.
14. `python3 -m pytest tests/schemas/ -v` → **88 passed in 0.13s**. Coverage on the `schemas` package is 100%.
15. Ran §14 Phase 1 smoke tests — both import checks pass; `len(REGISTRY) == 5`.
16. Rewrote ACTIVE TASK for Phase 2A and wrote this closeout.

**Key design calls:**
- `StrictBase` centralizes `ConfigDict(extra="forbid", protected_namespaces=())`. Avoids 14 copies of model_config and avoids the `model_` warning on `model_solution`/`model_type`/`model_registry_entry`.
- `UnknownPayloadError` inherits from `KeyError` (dict-lookup semantics); pydantic `ValidationError` remains separate for bad payloads.
- `target_variable: str | None` and `annual_impact_usd_low/high: float | None` are **required-nullable** (no default) — matches the plan's literal code. If Phase 2A finds this too strict, relax to `= None`.
- `database_hint` and `regulatory_mapping` have explicit defaults because the plan marks them "optional context."
- Decoupling rule is enforced textually in `data.py`'s docstring; runtime AST test is a Phase 2A deliverable per §14.
- Tests use `pytest.mark.parametrize` on every literal-enum field so adding a value is a one-line test change. Explicit regression guard against `default_factory` aliasing on `GovernanceManifest.regulatory_mapping`.

**Files created (17):**
- `pyproject.toml`
- `src/model_project_constructor/{__init__.py, schemas/__init__.py, schemas/envelope.py, schemas/registry.py, schemas/v1/{__init__,common,intake,data,gitlab}.py}`
- `tests/{__init__.py, schemas/{__init__,fixtures,test_intake,test_data,test_gitlab,test_envelope_and_registry}.py}`

**Session 2 Handoff Evaluation (Session 3 scoring Session 2):**
- **Score: 9/10**
- **What helped:** The ACTIVE TASK block was surgical — task, plan location, exact subsections to obey, explicit "do NOT start Phase 2," five-bullet evaluation rubric. The Gotchas section flagged four concrete traps; three were load-bearing for Session 3. Reading the plan + handoff took ~8 minutes and saved an estimated 45+ minutes of discovery.
- **What was missing:**
  - **No mention that `uv` was not installed on this machine.** Session 2 wrote "`uv` is the package manager" as a directive but did not verify it was available. ~2 minutes of probing.
  - **No flag that local Python is 3.10 while the plan pins 3.11+.** Latent trap for Phase 2A if LangGraph needs 3.11-only features.
  - The plan's `| None` comment syntax is ambiguous about required-nullable vs. optional-with-default. I had to make judgment calls on `target_variable`, the annual-impact bounds, and `database_hint`.
- **What was wrong:** Nothing factually wrong. Minor gap: the handoff references the `model_governance` project as the source of `GovernanceMetadata` but does not give its path.
- **ROI:** Very high. The plan was the valuable artifact; the handoff was a precise index.
- **Process note:** Session 2 correctly wrote a Phase 1B stub and held the planning-vs-implementation line.

**Session 3 Self-Assessment:**
- (+) Scope discipline. Phase 1 only. No agent code, no LangGraph, no adapters, no decoupling test — all Phase 2A.
- (+) Phase 1B stub written before any technical work.
- (+) All §14 Phase 1 verification commands green (pytest + both imports + `len(REGISTRY)`).
- (+) Tests exercise non-obvious cases: extra-field rejection, every literal value, serialization round-trip for every top-level schema, `load_payload` happy paths plus three failure modes, mutable-default aliasing regression guard.
- (+) Proactive abstractions (`StrictBase`, `SchemaKey`) only where they prevented repetition; no speculative generalization.
- (+) Module-level decoupling comment in `data.py` captures the §7 rule textually even without the runtime test.
- (+) Phase 2A gotchas are concrete: `uv`/Python 3.10 mismatch, unverified LangGraph interrupt pattern, three-valued status field, `extra="forbid"` discipline, `model_` namespace override, decoupling test must actually fire.
- (−) Did not install `uv`. Tests ran via `python3 -m pytest`; equivalent to `uv run pytest` but not the literal plan commands.
- (−) Local Python is 3.10; pyproject targets 3.11+. Works today because the schema code is 3.10-compatible; may bite Phase 2A.
- (−) `annual_impact_usd_low/high` are required-nullable. If intake agent has to pass `None` 80% of the time, relax to `= None` in Phase 2A or 3A.
- (−) No grep-based inventory — greenfield, so not mandatory per SESSION_RUNNER.md.

**Score: 9/10** — Deliverable met with comprehensive tests, explicit gotchas, scope discipline. Loses a point for not installing `uv` and for punting on the annual-impact default interpretation.

**Learnings added to SESSION_RUNNER.md Learnings table:** None this session. The schema code and tests are the Phase 1 institutional memory.

### What Session 2 Did
**Deliverable:** Formal architecture plan at `docs/planning/architecture-plan.md` (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (in chronological order):**
1. **Orientation only (no work)** — followed Phase 0; reported state; waited for direction.
2. **Deleted `methodology_dashboard.py`** per user instruction during orientation.
3. **Jupyter → Quarto replacement** in `docs/planning/architecture-approaches.md` (3 edits: line 88, 100, 249). Replaced references with "Quarto markdown documents (.qmd) and unit-tested Python/R functions" per user directive that all code must live in tested modules.
4. **Regenerated `architecture-approaches.pdf`** via pandoc/xelatex after the edits.
5. **Governance research** — used Explore subagent to read all markdown in `/Users/rmsharp/Documents/Projects/Active_Projects/model_governance`. Findings: cycle-time taxonomy, risk tiering, first-line evidence ownership, three-pillar validation (SR 11-7), datasheets (Gebru 2021), model cards (Mitchell 2019), regulatory frameworks (SR 11-7, NAIC AIS, EU AI Act, ASOP 56). User directed: hold governance findings for formal plan, do NOT augment approaches doc.
6. **User selected approaches:** Sequential Script + LangGraph/Claude + Pydantic envelope + Code Gen Only (Quarto).
7. **Wrote `docs/planning/architecture-plan.md`** — 19 sections, ~1000 lines:
   - §1 Context, constraints, explicit scope boundary
   - §2 Decision summary (chosen approaches)
   - §3 High-level architecture with ASCII diagram
   - §4 Agent boundaries with per-agent I/O and failure mode tables
   - §5 Pydantic schemas with field-level detail (`IntakeReport`, `DataRequest`, `DataReport`, `GitLabTarget`, `GitLabProjectResult`, governance models)
   - §6 Handoff envelope protocol with schema registry and versioning rules
   - §7 Data Agent reuse interface with adapter pattern and decoupling test
   - §8 Governance integration — proportional scaffolding by risk tier + cycle time
   - §9 Technology stack with specific versions and models
   - §10 LangGraph orchestration pattern with ASCII graphs per agent
   - §11 Generated GitLab repo structure (full file tree)
   - §12 Error handling strategy (agents return reports, don't raise)
   - §13 Consolidated failure mode analysis
   - §14 Implementation phases: 6 phases across 8 implementation sessions, each with explicit DONE criteria, verification commands, and session boundary markers
   - §15 Alternatives considered (pointer to approaches doc)
   - §16 Impact analysis
   - §17 Verification plan
   - §18 Open questions (deferred decisions)
   - §19 ARCHITECTURE_WORKSTREAM verification checklist

**Key decisions baked into the plan:**
- LangGraph is used **inside each agent**, not at the top level. The top-level orchestrator is still a Sequential Script. This preserves the upgrade path.
- `GovernanceMetadata` is a new addition to `IntakeReport` beyond what `initial_purpose.txt` describes — driven by the governance research in step 5.
- Data Agent decoupling is enforced by a CI test in `tests/test_data_agent_decoupling.py` that AST-walks the Data Agent source and fails on any `IntakeReport` import.
- The Data Agent is packaged as a separate installable subpackage (`model-project-constructor-data-agent`) to physically enforce the decoupling.
- Quarto + `src/` split: all code lives in `src/` as tested functions; `.qmd` files are narratives that import from `src/`. This satisfies the user's C6 constraint.
- EDA is code-generation-only — generated `.qmd` files are NOT rendered by the pipeline; the data science team renders them. This avoids executing LLM-generated code against corporate databases.
- Governance scaffolding is proportional: tier 3+ adds three-pillar validation, tier 2+ adds impact assessment and regulatory mapping, tier 1 adds LCP integration and audit log.

**Session 1 Handoff Evaluation (Session 2 scoring Session 1):**
- **Score: 7/10**
- **What helped:** The ACTIVE TASK block clearly stated the deliverable. The Gotchas section was genuinely useful — particularly the one flagging that Step 4 is not a separate agent (prevented me from over-counting agents), the one about Data Agent decoupling having multiple approaches with different implications, and the one noting the `initial_purpose.txt` output is prose not JSON (led me to think carefully about how LLMs produce structured output). The key-files list with line numbers for `initial_purpose.txt:18-80` and `:84-87` was precise and saved a re-read.
- **What was missing:** No mention of the `model_governance` project existing. The user had to volunteer it mid-session. A "related projects" section in the handoff would have surfaced it earlier. Also: no mention that `methodology_dashboard.py` was problematic/deprecated — user asked to delete it during orientation, which suggests the previous session knew it wasn't working but didn't flag it.
- **What was wrong:** Nothing inaccurate. The handoff was honest.
- **ROI:** High. Reading the handoff took ~2 minutes and saved probably 20+ minutes of discovery work. The line-number references specifically saved re-reading full files.
- **Process note:** Session 1 did not write a Phase 1B stub (no ghost session risk because it was the first session, but it should have followed the protocol). I corrected this for Session 2 by writing the stub before any technical work.

**Session 2 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before doing any work; waited for user direction.
- (+) Wrote the Phase 1B session stub before starting technical work (corrected Session 1's omission).
- (+) Did not bundle the plan with implementation — strict adherence to the "plan IS the deliverable" rule.
- (+) The plan has explicit per-phase completion criteria and verification commands (SESSION_RUNNER.md planning-session requirement).
- (+) Governance integration is first-class, not a bolt-on — it's woven through intake capture, schemas, and repo scaffolding.
- (+) Decoupling test for the Data Agent is specified at the AST level, not just as a convention.
- (+) Quarto + `src/` split directly satisfies user constraint C6.
- (+) Failure modes analyzed per-agent and consolidated globally (§4 + §13).
- (+) Alternatives explicitly rejected with honest reasons (§15).
- (-) Did not run a grep-based inventory — but this is a **greenfield** plan, not a deletion/migration/rename, so per SESSION_RUNNER.md the evidence-based inventory is not mandatory. Noted here for transparency.
- (-) §18 Open Questions has 5 items that should ideally have been resolved during planning. They are genuinely deferrable (they don't block Phase 1), but a stricter plan would have pushed on them.
- (-) The plan is long (~1000 lines). A shorter plan would be easier for a future session to read fully. However, the alternative (a short plan with vague phases) is worse because it invites bundling.
- (-) Did not verify `langgraph==0.2.x` actually supports the interrupt pattern I described for the intake review step. This should be verified in Phase 3A before implementing the intake agent. Noted as a risk in the Phase 3A session start.

**Score: 9/10** — Comprehensive, actionable, with explicit session boundaries and verification commands. Loses a point for the unverified LangGraph interrupt pattern and the 5 deferred open questions. No bundling, no scope creep, no protocol violations.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. The plan itself is the learning artifact for future implementation sessions.

### What Session 1 Did
**Deliverable:** Architecture approaches document (COMPLETE)
**Started:** 2026-04-10
**Commit:** See git log for hash

**What was done:**
- Created initial commit with all project scaffolding files (18 files)
- Deep analysis of `initial_purpose.txt`, `ROADMAP.md`, `BACKLOG.md`, all methodology workstream docs
- Produced `docs/planning/architecture-approaches.md` covering 4 critical features:
  1. Pipeline Orchestration (3 approaches: Sequential Script, State Machine, Event-Driven)
  2. Technology Stack & LLM Integration (3 approaches: LangGraph+Claude, Agents SDK+GPT-4o, Custom+Mixed Models)
  3. Schema Design & Handoff Protocol (3 approaches: Pydantic Envelope, JSON Schema+Codegen, Markdown+Frontmatter)
  4. EDA & Model Building (3 approaches: Code Gen Only, Sandboxed Subprocess, Containerized)
- Each approach includes concrete pros/cons, technology names, "best suited for" guidance
- Decision dependencies table mapping which choices constrain others
- Recommended starting combination at bottom of document

**Self-Assessment:**
- (+) Thorough coverage of all 4 critical features with concrete, actionable approaches
- (+) Each approach grounded in the project's specific constraints (P&C domain, Data Agent reuse, GitLab output)
- (+) Decision dependencies table helps avoid incompatible combinations
- (+) Recommended starting point gives a pragmatic default
- (-) Did not produce the formal architecture plan — approaches doc is the prerequisite, not the final deliverable. This was the correct scope for one session.
- (-) No session stub was written before starting work (Phase 1B violation — first session, so no ghost session risk, but protocol should be followed)

**Score: 7/10** — Good approaches document with concrete detail. Loses points for missing the session stub and for not having line-number references in the approaches doc itself.

Session 1 Handoff Evaluation: N/A (first session, no predecessor)
