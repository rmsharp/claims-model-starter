# Session Runner

**This is your operating procedure. Follow it step by step. Do not improvise.**

Every session has exactly ONE deliverable. When it's done, you close out. You do not start the next thing.

---

## Phase 0: Orient

**Change nothing. Read only.**

1. Read `SAFEGUARDS.md` — **in full, not skimmed. Every section.**
2. Read `SESSION_NOTES.md` — focus on the ACTIVE TASK section at the top
3. Check GitHub Issues (`gh issue list`) if the project has a repo — understand current priorities. Fall back to `BACKLOG.md` if no repo exists. (BACKLOG.md should contain only open work items — for history see `CHANGELOG.md`, for feature inventory see `ROADMAP.md`.)
4. Run: `git status`, `git log --oneline -5`, `git diff --stat`
5. Run the shared methodology dashboard (external to this repo — lives in `~/Development/`, not inside `model_project_constructor/`). Leave `dashboard.html` open in a browser; it auto-refreshes every 60 seconds. If the dashboard is not running, note it and continue — do not create a copy in this repo.
6. **Check for ghost sessions:** Compare the session number in SESSION_NOTES.md against `git log`. If there are commits between the last documented session and now that don't correspond to any session notes, report: "Detected [N] undocumented session(s) between Session [X] and now. Commits: [list]. No session notes exist for this work."
7. **Report findings to the user:**
   - Current branch and clean/dirty state
   - What the last session was doing
   - Current milestone and active task from GitHub Issues (or BACKLOG.md if no repo)
   - Any uncommitted changes
   - Ghost session detection results (step 6)
   - Dashboard health score and any risk flags
   - Build status if known
8. **STOP. Wait for the user to give you a task.**

DO NOT skip the report. DO NOT start working. DO NOT assume you know what to do.

**Even if the user's first message contains a task** (e.g., "Implement the following plan"), Phase 0 is still mandatory. That phrase comes from Plan Mode's auto-generated preamble — it does NOT mean start coding. The orientation report exists for the user's benefit — it establishes shared understanding of the current state. The user needs to see the report and confirm before work begins. A task in the prompt does not mean Phase 0 is complete. Complete all 8 steps, then the user will re-state or confirm the task in Phase 1.

**Steps 1-3 are READS, not skims.** Every step exists because a session failed without it.

---

## Phase 1: Receive Task

The user will direct you. Interpret their prompt and identify:

- **The deliverable:** What ONE thing are you producing this session?
- **The workstream doc:** Which methodology document governs this work?

Common task-to-workstream mappings:

| User Says | Deliverable | Workstream Document |
|-----------|-------------|---------------------|
| "Plan/design the pipeline architecture" | Architecture plan document | `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md` |
| "Build the intake agent" / "Build the data agent" / "Build the website agent" | One agent implementation | `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md` |
| "Design the interview flow" / "Design the handoff protocol" | One design document | `docs/methodology/workstreams/DESIGN_WORKSTREAM.md` |
| "Write the system prompt for [agent]" | One prompt + test | `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md` |
| "Define the output schema for [step]" | One schema document | `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md` |
| "Wire agents together" / "Integrate [step]" | One integration pass | `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md` |
| "Audit [agent/output/pipeline]" | One audit report | `docs/methodology/workstreams/AUDIT_WORKSTREAM.md` |
| "Fix [bug campaign]" | One fix campaign pass | `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md` |
| "Review [code/PR]" | One review document | The review produces a plan; follow DEVELOPMENT_WORKSTREAM for structure |
| Multi-phase plan appears in prompt (from Plan Mode or user) | Plan document written to `docs/planning/` with evidence-based inventory | Planning workstream |

**⚠ Plan Mode exit trap.** Plan Mode generates "Implement the following plan" as its preamble. **This does NOT mean "start coding."** When a multi-phase plan appears in the prompt — regardless of the preamble wording — the deliverable is writing the plan document with grep-based evidence and per-phase criteria. Orient first. The plan is a DRAFT until evidence-verified. See Planning Sessions below.

**If no workstream document exists for the task type, follow the master framework:** `docs/methodology/ITERATIVE_METHODOLOGY.md`, phases 1-6.

State your understanding back to the user: *"I'm going to [deliverable] following [workstream doc]. I'll close out when that's done."*

### 1B: Claim the Session (MANDATORY)

**Immediately after receiving a task — before any technical work — write a stub to `SESSION_NOTES.md`:**

```markdown
### What Session [N] Did
**Deliverable:** [task description] (IN PROGRESS)
**Started:** [date/time]
**Status:** Session claimed. Work beginning.
```

**Why this exists:** Ghost sessions — sessions that crash, hit context limits, or end without writing notes — leave zero trace. The next session has no idea what happened, what was attempted, or what state was left behind. By writing a stub FIRST, even a catastrophic failure leaves evidence. This stub is overwritten during Phase 3D with the full handoff.

---

## Phase 2: Execute

1. Read the workstream document identified in Phase 1
2. Follow its phases sequentially, respecting hard gates
3. Execute ONE deliverable only
4. If blocked, ask. Don't improvise around blockers.
5. If you catch yourself thinking "while I'm at it..." — STOP. That's scope creep. Commit what you have and note it for a future session.

### Planning Sessions

**⚠ The plan is the deliverable. Do not start implementing it.** Write the plan document to `docs/planning/`, commit it, close out. Implementation happens in a separate session.

**A plan is a deliverable, not a preamble.** When the session's deliverable is a plan (architecture doc, migration plan, multi-phase implementation plan), additional discipline applies:

#### Evidence-Based Inventory (MANDATORY for deletion/migration/rename plans)

For any plan that involves deleting, renaming, migrating, or moving code:

1. The plan MUST include a **grep-based inventory** of all references to the affected symbols, files, components, keys, imports, and type names.
2. Run the actual searches. List every matching file. The plan's "files to change" list comes from search results, not architectural knowledge.
3. Search terms should include: file names, class names, function names, import paths, key prefixes, component registration names, and any aliases.
4. The inventory IS the plan's verification step — equivalent to "grep for dangling references" in execution sessions.

**A plan that lists files to change without having searched for them is an assumption, not an inventory.** The executor will trust the plan. If it's wrong, they'll miss files — exactly the failure this requirement prevents.

#### Per-Phase Completion Criteria

Every phase in a multi-phase plan must state:
- **What DONE looks like** — concrete output, not "implement Phase N"
- **Verification commands** — how the executor confirms completion (build, test, grep)
- **Session boundary** — "This phase is one session. Close out when done."

Without explicit completion criteria, executors don't know when to stop and tend to bundle adjacent phases.

#### Planning Session Checklist

Before closing out a planning session, verify:

- [ ] Plan document written with file paths and line numbers
- [ ] Grep-based inventory completed for all affected symbols (if deletion/migration/rename)
- [ ] Each phase has explicit completion criteria and verification commands
- [ ] Each phase marked as "separate session" with a STOP point
- [ ] Close-out: evaluate predecessor, self-assess, commit, STOP

---

## Phase 3: Close Out

**This phase is AUTOMATIC. When your deliverable is complete, execute ALL of these steps without being asked.**

**Do not ask "shall I continue?" Do not offer to start the next thing.**

**The close-out is not cleanup — it is the compounding mechanism.** The quality of your close-out directly determines the quality of the next session. You will be judged on how well you set up your successor, just as you judged your predecessor in step 3A.

### 3A: Evaluate the Previous Session's Handoff

**This step comes FIRST, before self-assessment.** Read what the previous session left you in `SESSION_NOTES.md` and score it:

- **Score (1-10):** How well did the previous session's handoff prepare you for success?
- **What helped:** Which specific notes, file references, or warnings saved you time?
- **What was missing:** What did you have to figure out that should have been documented?
- **What was wrong:** Any claims in the handoff that turned out to be inaccurate?
- **ROI:** Did reading the handoff save more time than it cost?

**Write this evaluation to `SESSION_NOTES.md`** under a "Session N Handoff Evaluation (by Session N+1)" heading. The previous session's author cannot improve if they never see the score.

**Re-read the actual files before writing claims.** Do not write gap analysis from memory of files you read earlier in the session. Memory degrades across a long session. If you haven't read the file in the last 5 minutes, read it again now.

*Note: Skip this step on Session 1 — there is no previous handoff to evaluate.*

### 3B: Self-Assess

Compare your work to the standard set by previous sessions in this workstream:

- Did you complete all research before creative work?
- Did you read implementations, not just descriptions?
- How many stakeholder corrections were needed?
- What did you get right? What did you get wrong?
- Did you meet or exceed the quality bar of previous sessions?

### 3C: Document Learnings

Update the workstream document and/or the Learnings table below:

- What you did, how you did it, and why
- Files referenced during this session
- Initial mistakes and how you recovered
- New patterns discovered (named, with "when to use")
- New anti-patterns discovered (numbered, with root cause)
- Performance metrics compared to previous sessions

**The goal: the next session performs better by learning from yours.**

### 3D: Write Handoff Notes

Update `SESSION_NOTES.md`. **You will be judged on this.** The next session will score your handoff in their Phase 3A, just as you scored your predecessor's. Write notes that would earn a 9 or 10.

**Write to files FIRST, then summarize verbally.** A verbal summary that isn't written down is worthless — the next session can't read the conversation.

#### Minimum Handoff Requirements (ALL mandatory)

A handoff that doesn't include ALL of the following is a protocol violation. "Pick next from backlog" is not a handoff — it's an abdication.

| # | Requirement | Bad Example | Good Example |
|---|-------------|-------------|--------------|
| 1 | **ACTIVE TASK updated** with current state | "Done." | "Task: Auth refactor. Status: Phase 1 complete. Phase 2 not started." |
| 2 | **What was done** with commit hashes | "Fixed stuff" | "Fixed 3 auth bugs (token refresh, session expiry, CORS). Commit `a1b2c3d`." |
| 3 | **What's next** — specific and actionable | "Pick next from backlog" | "Implement Phase 2 of auth-plan.md. Start with `SessionManager.java:245`." |
| 4 | **Key files** with full paths and line numbers | (none) | "SessionManager.java:245-320 (token logic), AuthFilter.java:88-95 (CORS)" |
| 5 | **Gotchas** the next session should watch for | (none) | "Token refresh has a 5s race window — see SessionManager.java:267" |
| 6 | **Self-assessment score** written to file | (verbal only) | Written to SESSION_NOTES.md with +/- breakdown |

**A handoff missing items 1-5 will score ≤4/10 by the next session.** This directly causes the next session to waste time on discovery that should have been documented.

#### Evidence requirement

**Never claim credit for work you didn't do.** If a plan was provided as input, say "Plan was input, not output." If you didn't produce a deliverable, say "No deliverable produced." Fabricating accomplishments or attributing quotes the user didn't say is a trust-destroying failure.

**Never write "need to verify" in a handoff gap.** If you don't know, read the file NOW. Deferred verification is deferred work — it belongs in your session, not the next one.

### 3E: Commit

Commit all changes with a descriptive message.

### 3F: Report and STOP

Tell the user:

- Summary of the deliverable
- Self-assessment highlights (what went well, what didn't)
- Previous session's handoff score and key findings
- What the next session should do

**Then STOP. The session is over.**

---

## Known Failure Modes

These are documented tendencies. The agent must actively guard against them.

| # | Tendency | What Happens | Countermeasure |
|---|----------|-------------|----------------|
| 1 | **Eager to start** | Skip Orient and jump to doing things | Phase 0 is mandatory. The user must speak before work begins. |
| 2 | **Keep going** | Finish the deliverable and immediately start the next thing | "1 and done." Close-out fires when the deliverable is complete. |
| 3 | **Skim documents** | Read 500 lines and retain the gist, not the steps | Follow the checklist step by step, not from memory of the gist. |
| 4 | **Assume context after compaction** | Think "I remember what I was doing." Don't. | Trust SESSION_NOTES.md, not memory. Re-read the files. |
| 5 | **Equate helpfulness with volume** | Do more because more feels more helpful | Quality > quantity. One excellent deliverable beats two mediocre ones. |
| 6 | **Skip close-out** | Self-assessment and prompt updates feel like cleanup, not real work | Close-out is the most valuable phase. It's how the system improves. |
| 7 | **Ask the user to solve process problems** | "What should I do?" instead of reading the docs | Read the docs. Follow the process. Only ask when genuinely blocked on content. |
| 8 | **Redesign during implementation** | See something to improve and act on it mid-task | Commit first. Note it for a future session. Stay on the approved plan. |
| 9 | **Task-in-prompt bypass** | User's first message contains a task, so Phase 0 feels implicitly complete | Phase 0 exists for the USER, not the agent. Complete all 8 steps even when the task is obvious. |
| 10 | **Skip handoff evaluation** | Self-assessment feels sufficient; evaluating the previous session feels like extra work | Phase 3A is a mandatory structural step. The evaluation IS the compounding mechanism. |
| 11 | **Gaps from memory** | During close-out, write gap analysis from memory of files read earlier. Memory degrades. Claims turn out wrong. | Before writing ANY claim in close-out: "Have I read the file that confirms this in the last 5 minutes?" If no → read it now. |
| 12 | **Workstream transfer amnesia** | Build good discipline on one workstream, then switch and repeat old mistakes | Discipline doesn't auto-transfer. When switching workstreams, consciously re-apply the close-out checklist. |
| 13 | **Literal minimum** | When asked to do X, do exactly X and nothing logically implied by X | Before acting: "What is the user's UNDERLYING intent?" Do the complete job on the first pass. |
| 14 | **Ghost session** | Session crashes, hits context limits, or ends without writing ANY session notes. Next session has zero context. | Phase 1B (Claim the Session) is mandatory — write a stub to SESSION_NOTES.md BEFORE starting technical work. Even catastrophic failures leave a trace. |
| 15 | **Minimal handoff** | Session writes "Done. Pick next from backlog." — technically a handoff, functionally useless. Next session starts blind. | Phase 3D has 6 minimum requirements. A handoff missing key files, specific next steps, or gotchas is a protocol violation that will score ≤4/10. |
| 16 | **False credit / fabrication** | Session claims credit for work it didn't do, or attributes quotes the user never said. Trust destruction. | Never claim deliverables you didn't produce. If a plan was input, say so. If you produced nothing, say so. |
| 17 | **Protocol erosion** | Each session shaves off "just one" protocol step. Individually minor. Over 5-10 sessions, the whole protocol collapses. Scores drift from 9/10 to 1/10. | The protocol is not optional, advisory, or improvable-by-subtraction during a session. Every step exists because a previous session failed without it. If you think a step is unnecessary, that's the erosion happening. Do the step. |
| 18 | **Planning-to-implementation bleed** | A session produces a plan, then immediately begins implementing it. Or the next session bundles multiple phases because "the plan is done, implementation is easy." | A planning session's deliverable IS the plan. Close out after the plan. The next session implements ONE phase. If a plan has N phases, expect N+1 sessions minimum (1 planning + N implementation). If a session's commit history shows both "docs: plan" and "feat: implement," it bundled. |
| 19 | **Plan-mode bypass** | Plan-mode output arrives in the prompt with "implement." Session treats it as an implementation task and starts coding, skipping the planning workstream entirely. The plan hasn't been evidence-verified. | Plan-mode output is a DRAFT. The first session writes it to `docs/planning/` with evidence-based inventory. Implementation is a separate session. If the prompt contains a multi-phase plan and says "implement," the deliverable is the plan document, not code. |

---

## Degradation Detection

**How to recognize the protocol is eroding — warning signs that predict ghost sessions and failed deliveries:**

| Warning Sign | What It Means | Response |
|--------------|---------------|----------|
| Handoff is <5 lines | Failure mode #15 (minimal handoff) is active | Expand to meet all 6 minimum requirements |
| No handoff evaluation of predecessor | Failure mode #10 (skip evaluation) is active | Stop. Write the evaluation before self-assessing |
| "I'll just skip the stub" | Failure mode #14 (ghost session) is imminent | Write the stub. It takes 30 seconds. |
| Self-assessment not written to file | Failure mode #6 (skip close-out) is active | Write to SESSION_NOTES.md before summarizing verbally |
| Session number gap in SESSION_NOTES.md | Ghost session already happened | Note it. Document what you can infer from git log. |
| Score dropping session-over-session | Multiple failure modes compounding | Re-read this entire document. Reset to full protocol. |
| "This step doesn't apply to my session" | Failure mode #17 (protocol erosion) is active | The step applies. Do it. Every step exists because a session failed without it. |
| Plan commit + implementation commit in same session | Failure mode #18 (planning-to-implementation bleed) is active | The plan was the deliverable. Close out. Implementation is a separate session. |
| Session starts coding from plan-mode output | Failure mode #19 (plan-mode bypass) is active | The plan is a draft. Write it to `docs/planning/` with evidence-based inventory first. |

**If you detect 2+ warning signs: STOP.** Re-read this document from the top. Do not continue until you've re-internalized the protocol. The cost of pausing to re-read is 2 minutes. The cost of a ghost session or failed delivery is the user's trust.

---

## Learnings (added by sessions)

*This table starts empty. Each session adds learnings here. Over time, this becomes the project's institutional memory.*

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 1 | Plan-mode output is a draft, not a verified plan. When a prompt contains a multi-phase plan with "implement," the deliverable is a plan document with evidence-based inventory, not Phase 1 code. The gap: Phase 1's task mapping had no entry for plan-mode handoffs, so the session defaulted to "implement." Structural fix: new mapping row + FM #19. | FM #19 discovery | When a prompt contains a multi-phase plan with "implement" — recognize this as a planning workstream. |
| 2 | When extending a LangGraph pipeline with new nodes, put the helper functions in a sibling module (e.g. `governance_templates.py` next to `templates.py`) rather than expanding the existing module. Review-time diff stays local; the "before vs after" phase split is visible in the file tree. | Session 9 (Phase 4B governance extension) | Any LangGraph phase extension where the previous phase's templates/helpers are stable and do not need to change. |
| 3 | Derive manifest/audit data by classifier function (`is_governance_artifact(path)`) rather than by storing it in state during each node. The classifier is the single source of truth and composes with any future node that adds a new artifact category; state bookkeeping drifts. | Session 9 (Phase 4B GovernanceManifest assembly) | Assembling a result object from side effects of multiple nodes — especially when some nodes are optional. |
| 4 | When a test file needs a graph with injected dependencies (e.g. no-op `sleep`), prefer plumbing a kwarg through the production factory (`build_website_graph`) rather than building it manually — but do NOT refactor production code to add the kwarg for a test-only need unless the kwarg is also valuable in production. Accept a `__new__`-based construction hack in tests rather than over-engineer production. | Session 9 (`test_retry.py` construction) | Whenever a test needs a variant of a production-constructed object. |
| 5 | Pin tier/flag-gated behavior with BOTH a positive AND a negative assertion per tier: `assert "governance/foo.md" in files` AND `assert "governance/bar.md" not in files`. A positive-only test passes silently if a tier starts emitting the wrong artifact. | Session 9 (`test_governance.py` tier fan-out) | Any tier/flag-gated code where missing artifacts are as important as present ones. |
| 6 | The pattern "plan as deliverable, then implementation as a separate session" (failure modes #18, #19) is load-bearing across the SESSION_RUNNER workstreams. When the user hands Session N a plan input mid-session, write it into the handoff verbatim and leave it for Session N+1 — do NOT pivot. | Session 9 (GitHub/GitLab notes mid-Phase-4B) | Any session where the user introduces a second deliverable while the first is mid-flight. |
| 7 | When the user provides a partially-captured message as input (e.g. a truncated `/btw` response), proactively reconstruct the missing content based on the visible evidence AND document the reconstruction with explicit provenance: "originally from /btw on <date>, point #N lost to truncation, reconstructed by Session X from <evidence>." Do NOT silently infer or silently ignore the gap. Offer the user a "regenerate vs proceed" choice before committing, then honor their preference. | Session 10 (missing point #1 in Session 9's verbatim `/btw` notes) | Any session where the input is referenced as partially missing or explicitly truncated. |
| 8 | A grep-based inventory for a rename plan must include the TYPE, FIELD, STATE KEY, and DOCSTRING surfaces **separately** — each has a different grep pattern. Conflating them into one total gives misleading counts. List hits per grep pattern + per file, not a single total. Classes (`GitLabClient`), field names (`gitlab_url`), state keys (`gitlab_target`), and literal filenames (`.gitlab-ci.yml`) are four different greps. | Session 10 (GitHub/GitLab abstraction plan §4) | Any rename/migration plan. |
| 9 | When writing a multi-phase plan, put cross-phase invariants (do-not-change lists, strategic decisions, Phase N ordering) in ONE document rather than duplicating them across phase-specific documents. Duplication causes drift: one phase doc gets a correction and the others do not. Single-document trades navigability for consistency; for 4-phase plans with 3+ shared invariants the tradeoff favors consistency. | Session 10 (GitHub/GitLab abstraction plan §16) | Any plan with more than 2 phases sharing ≥3 invariants. |
| 10 | During Phase 0, when the user's first message appears to contain a task (e.g. "go"), do NOT skip the orientation report even if the ACTIVE TASK block already describes the deliverable. The report exists for the user's benefit — it establishes shared state before any work begins. Failure mode #9 (task-in-prompt bypass) is the specific risk. Complete all 8 Phase 0 steps, report, and explicitly wait for direction even when the direction feels implicit. | Session 10 ("go" → still did Phase 0 report) | Every session. |
| 11 | When a plan section's signatures or field names contradict the actual protocol/source code (because the plan was written before a rename or refactor), **trust the code, not the plan**. Plan §8.1 for Phase C used `group_path` in one bullet, but `protocol.py:51` uses `namespace` — the Phase A rename had already landed. Mirror the current code's signatures; keep the plan's semantic intent. A plan that names a specific symbol is a claim that it existed when the plan was written, not a guarantee that it still exists. | Session 13 (Phase C plan had `group_path`, protocol had `namespace`) | Any implementation session working off a plan written more than one session ago. |
| 12 | When a previous handoff's gotcha contradicts the actual pattern in the codebase (e.g. "X should NOT inherit from Y" when sibling code already inherits), **mirror the codebase pattern, not the gotcha**. Consistency with existing code is more defensible than following a note that the source already contradicts. Document the resolution in your own handoff so the next session doesn't waste cycles. | Session 13 (Session 12 gotcha said `PyGithubAdapter` should not inherit from `RepoClient`; `gitlab_adapter.py:41` inherits) | Any session where a gotcha and the codebase disagree. |
| 13 | When a handoff suggests "likely X" or "possibly Y" for a new dependency (e.g. "likely `structlog`", "possibly `pydantic-settings`"), prefer the zero-new-dep alternative if the stdlib or existing deps can do the job. Adding a dep is a one-way door (future sessions must maintain it, CI must install it, version conflicts can surface). For Phase 6, stdlib `logging` with `extra={"context": ...}` satisfied "structured logging" without `structlog`; a plain `dataclass` + `os.environ` satisfied "env-var-driven config" without `pydantic-settings`. Both choices were validated by 54 new tests + mypy strict + ruff clean. The handoff should explicitly flag the tradeoff so the implementing session can make the call quickly. | Session 16 (Phase 6: zero new deps despite plan suggesting structlog + pydantic-settings) | Any implementation session where the plan or handoff suggests adding a new dependency. |
| 14 | For documentation-heavy deliverables (wiki, reference docs), use parallel research agents to explore the codebase from different angles simultaneously (e.g., generated output structure, dependencies, architecture). This front-loads all discovery into ~3 minutes of wall time instead of sequential reads. Each agent should have a specific angle — avoid overlap. Then verify every claim against source code before writing (read the actual templates, schemas, and config files, not just summaries). | Session 19 (claims-model-starter wiki, 3 parallel agents for structure/deps/architecture) | Any session producing documentation that spans multiple codebase concerns. |
| 15 | When a parallel research agent times out (e.g., "Stream idle timeout - partial response received"), do NOT re-launch — the failure mode is usually scope breadth (too many angles packed into one agent) and a re-launch burns the same budget. Instead, pivot to direct `Grep` + `Read` for just the citations you actually need for the page you're writing. The sibling agents that DID complete already gave you enough map to know which files to open. A timed-out agent costs ~3 min to recover; a re-launched timed-out agent costs ~6 min. Special case of "trust but verify." | Session 20A (security research agent timed out; direct reads of config/adapters/LLM clients for ~10 files completed the page) | Any documentation session using parallel research agents when one times out. |
| 16 | When the canonical "what gets generated" spec is a test assertion (e.g., `tests/agents/website/test_templates.py:176-205`), prefer reading the test over running the pipeline to capture the file listing. The test IS the spec — any divergence would fail CI before the listing could drift. Running the pipeline with fake adapters just re-derives the same set of filenames at the cost of setup + environment risk. Cite the test file:line in the doc so future readers can verify independently. | Session 20B (Worked-Examples generated-file listing) | Any documentation that needs to enumerate outputs of a generator function — prefer the test over the run. |
| 17 | Methodology guidance for shared files (`CHANGELOG.md`, `BACKLOG.md`, `ROADMAP.md`, `docs/methodology/*`) lives primarily in `docs/methodology/README.md` and secondarily as inline notes in `SESSION_RUNNER.md` / `SAFEGUARDS.md`. Before proposing options on how a shared file should be maintained, **read `docs/methodology/README.md` first** — its "templates" section at `:99` and `:215` is load-bearing. A handoff that offers options including one that contradicts methodology (e.g., "mark CHANGELOG as subordinate to the wiki") is a protocol violation; methodology outranks handoff suggestions. | Session 21 (CHANGELOG scoping round-trip) | Any session that is about to modify `CHANGELOG.md`, `BACKLOG.md`, `ROADMAP.md`, `SESSION_NOTES.md`, `SAFEGUARDS.md`, `SESSION_RUNNER.md`, or the methodology docs themselves. |
| 18 | **CI gate scope can diverge from declared tool scope.** `pyproject.toml` may declare `[tool.mypy] packages = [A, B]` but CI runs `mypy A` only. Similarly `ruff` CI may scan `src/ tests/ packages/` while excluding `scripts/`. Local "green pre-flight" using the tool's natural scope will surface failures that CI isn't gating — these are CI-gap findings, not regressions. Before declaring pre-flight failed, re-run the EXACT command CI executes and compare. If CI-matching is green but broader-scope fails, file the CI gap + the underlying errors as findings, don't block on them. | Session 22 (ruff on `scripts/` + mypy on `packages/` surfaced pre-existing errors CI doesn't gate) | Any session where local pre-flight diverges from CI green-status. |
| 19 | **Fill grep-inventory counts AFTER running the greps, not from memory of an earlier pass.** Memory of "I saw N matches" degrades within minutes — by the time the inventory section is being written, the count has fuzzed. Discipline: write the section with `XX` placeholders, run the greps in sequence, paste the actual numbers. The executor will re-run those greps in their Phase 0; if the plan's numbers are visibly wrong they lose trust in everything else the plan claims. The cost of running the grep again is one tool call; the cost of an inaccurate inventory is the plan's credibility. | Session 23 (Scope B plan §17 first draft said "11" for runner contract; actual 16; caught + fixed in close-out) | Any planning session whose deliverable includes a grep inventory or evidence count. |
| 20 | **When a plan asks "which model?" in an open-decisions section, do NOT default to the cheapest option for a pilot's first real run.** The common rationale "defer the quality conversation to after we see output" is weak when output quality is literally what the pilot is evaluating. If the model turns out to be limiting, the first-run impression is contaminated and "was it the model?" becomes a confounding variable. Recommend the highest-quality option (e.g. `claude-opus-4-7`) for the *first* run to eliminate that variable; fall back to cheaper models (sonnet, haiku) for iteration once the output shape is validated. Pilot cost at ~$0.50 vs ~$0.10 per run is trivial compared to the cost of a muddled conclusion. | Session 24 (user challenged plan §8.2's sonnet-4-6 recommendation; opus-4-7 used instead for B1) | Any session where a plan recommends a cheaper/faster model for a first-impression pilot run that will be judged on output quality. |
| 21 | **Before writing a plan criterion like "live LLM + fixture → COMPLETE status", read the status-decision code.** Terminal-state logic is usually one tight function at the end of a graph (in this project: `src/model_project_constructor/agents/intake/nodes.py:142`). In the intake agent, `status = "COMPLETE" if accepted and not missing else "DRAFT_INCOMPLETE"`, AND `nodes.py:129-134` auto-appends `questions_cap_reached` whenever `questions_asked >= MAX_QUESTIONS and not believe_enough_info`. "Happy path = COMPLETE" against a real LLM therefore requires the LLM to flip `believe_enough_info=true` BEFORE hitting `MAX_QUESTIONS`. Plan §7.2.3 criterion #1 assumed this would just happen; in practice, Claude Opus 4.7 against a 10-qa-pair fixture asks 10 substantive questions and still wants more — producing a rich DRAFT_INCOMPLETE report, not COMPLETE. When planning, pay for the read once; when executing, forecast the gap rather than discovering it after a $0.30 live run. | Session 26 (B2 happy-path run `run_b2_live` returned DRAFT_INCOMPLETE despite a rich Claude-drafted envelope because of the status-decision invariant). | Any planning session whose success criteria depend on an agent's terminal state. |
| 22 | **When auditing a production constant's blast radius, grep for BOTH the UPPER_CASE constant name AND the lower_case field form.** Constants leak through two indirect coupling paths that plain `grep MAX_QUESTIONS` misses: (a) test fixtures whose CONTENT is sized to the constant by arithmetic (e.g. `intake_question_cap.yaml` needs `qa_pairs >= MAX_QUESTIONS + 1` to demonstrate the cap firing — the fixture's size IS the contract), and (b) dict-literal exports that rename the constant through a public API (e.g. `runner.py:CAPS = {"max_questions": MAX_QUESTIONS}` → `test_runner.py:assert CAPS == {"max_questions": 10}` — the grep for `MAX_QUESTIONS` misses the far side of the rename). Second-pass grep for the dict-form field name (`max_questions`, case-insensitive) catches both. Read the fixture file top-comments by purpose, not by name — their size-invariant is load-bearing. | Session 27 (MAX_QUESTIONS 10→20 bump — pre-change grep caught `intake_question_cap.yaml` by reading the fixture's top-comment, missed `test_caps_constants_exposed` because of the dict-form rename; pytest surfaced the second one). | Any session bumping a production constant that is referenced in test fixtures or cross-file dict exports. |
| 23 | **When a handoff describes a fix as "parallel to Session X's fix," read both sibling call sites side-by-side before editing.** The parallel often runs deeper than the named symbol — if sibling code has had "the same class of bug" on one branch, the untouched branch may have multiple instances. Session 30 was framed as "add `host_url=` to the GitHub branch, parallel to Session 22's GitLab `url=` → `host_url=` fix." The parallel was correct but incomplete: the GitHub branch ALSO had `token=` vs `private_token=` wrong (same shape as the Session 22 kwarg mismatch). Both bugs together meant `--live --host github` had never worked. Reading `github_adapter.py:66-72` (constructor signature) + `scripts/run_pipeline.py:273-278` (call site) together caught both in one pass; reading the call site alone would have produced a half-fix that still raised `TypeError`. Countermeasure: 10-second grep of both adapters' constructor signatures + both call sites before editing. | Session 30 (`PyGithubAdapter(token=token)` at `run_pipeline.py:277` had TWO bugs; Session 29's handoff named only the second). | Any implementation session where the handoff frames the task as "parallel to Session X" — read both sibling call sites side-by-side before editing either. |

---

## Launch Prompt Templates

The user can paste any of these to start a session reliably. The session runner handles the rest — the user does not need to include methodology instructions, close-out instructions, or stop conditions.

**Design:**
> Design the [name/component].

**Implementation:**
> Implement [feature/phase N of plan].

**Continuation:**
> Continue where last session stopped.

**Audit:**
> Audit [target].

**Free-form:**
> [Description of task]. *(Session runner will assess scope and pick the right workstream.)*
