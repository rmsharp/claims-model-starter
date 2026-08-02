# `OpenCodeLLMClient` — Adapter Specification

**Author:** Session 211 (spec session) — 2026-08-01.
**Baseline commit:** `a3f33d8` — tree clean on `master`. Last full gate (Session 209): 989 passed + 8 skipped @ 97.78%, ruff clean, mypy clean. This session changes no `src/`, `packages/`, `scripts/`, or `tests/` file.
**Status:** Specification for executor review. **This document is the deliverable of Session 211.** Failure modes #18 (planning-to-implementation bleed) and #19 (plan-mode bypass) are the primary risks for the sessions that follow.
**✅ Phase 2 is COMPLETE (Session 213, 2026-08-01)** — both clients, both factory branches, the registry entry and the deterministic tier are shipped and on `master`; see `CHANGELOG.md`'s 2026-08-01 entry for the full breakdown and the two as-built deviations (§4.4/§5.1's `agent=` escape hatch removed; §5.3's helper signatures take parsed events). **Phase 3 (eval wiring + docs) is next.** Gate: 1100 passed + 8 live-skipped @ 97.79%, mypy and ruff clean.

**⚠ Phase 1 is COMPLETE (Session 212, 2026-08-01) — read [Appendix A](#appendix-a--phase-1-live-verification-findings-session-212-2026-08-01) BEFORE Phase 2.** All four `[unverified]` markers are resolved and §3/§4 are annotated inline, but Phase 1 also produced **seven corrections to this spec, one of them a safety defect**: §3.5's hazard H4 claim that "the default is already safe" is **false** — a live run read a file and disclosed its contents without `--auto`. Fixtures: `tests/fixtures/opencode/`.
**Decision being implemented:** AD-11 (`docs/wiki/claims-model-starter/Architecture-Decisions.md`) — accepted by the operator 2026-08-01. Research behind it: `docs/wiki/claims-model-starter/AI-Dependencies.md` §9.
**Governing workstream:** `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md` (interface-first design, failure-mode analysis, honest alternatives). *Not* `DESIGN_WORKSTREAM.md`, which is UI/UX-specific.

**Headline decisions (each argued in §4):**

- **D1 — Transport-method override, not a from-scratch client.** `OpenCodeLLMClient` subclasses each package's `AnthropicLLMClient` and overrides **only** `__init__` and the one transport method (`_call_json` for intake, `_call_claude` for the data agent). Every prompt, every JSON-shape instruction, every dataclass builder, and `_extract_json` are inherited unchanged — so prompt drift across providers is structurally impossible, exactly as it is for `BedrockLLMClient`.
- **D2 — The per-call `system` prompt is folded into the user message.** `opencode run` has **no** per-invocation system-prompt flag (verified against the CLI source, §3.1). Both seams pass a *different* system prompt per method, so a static agent definition cannot carry it. **This is the single largest output-quality risk in the adapter** and is why the eval gate is mandatory, not optional.
- **D3 — Process-per-call (`opencode run`), not a long-lived server.** `opencode serve` + `--attach` is the documented optimisation path and needs no adapter rewrite (`--attach` is a flag on the same `run` command).
- **D4 — Hermetic sandbox by default.** The adapter runs `opencode` with `--dir <ephemeral temp dir>`, `stdin=DEVNULL`, the prompt on **stdin not argv**, and **never** `--auto`. Each of these closes a concrete, source-verified hazard (§3.5).
- **D5 — Zero new Python dependencies; one new *non-Python* runtime dependency.** The client imports only `json`, `os`, `shutil`, `subprocess`, `tempfile`. It requires the `opencode` **binary** on `PATH` — a class of dependency this project has never had before. §4.5 and §8 treat that as a first-class risk, not a footnote.
- **D6 — `DEFAULT_MODEL = None`** — defer to the operator's own OpenCode config, because "the operator's config picks the vendor" *is* the portability goal. Any evaluated or production run must still pin an explicit model (§4.6).

**Out of scope (do NOT bundle):** implementing any of this in the spec session; native structured output (`--json <schema>` is an open OpenCode feature request, not a shipped feature — §3.3); replacing `_extract_json` anywhere; retry/back-off/rate-limit policy (Trap 5 of the prior plan is still open, Q4); any change to the LangGraph topology, the intake `MAX_QUESTIONS=20` / `MAX_REVISIONS=3` caps, the governance vocabularies, or the C4 decoupling boundary; the website agent (it uses no LLM).

---

## 0. What this document is

`BACKLOG.md`'s "CLI-adapter portability" item asks for a **spec, not an implementation**, of an `OpenCodeLLMClient` that extends both agents' provider seams with an `"opencode"` branch. `AI-Dependencies.md` §9.2 flagged one prerequisite: *"OpenCode's `--format json` event schema is not yet published/verified — that verification is prerequisite spec work, not an assumption to carry into the design."*

**That prerequisite is discharged in §3 of this document** — not by a live invocation, but by reading the emitter in OpenCode's own source at a pinned commit, which is *stronger* evidence than one live run for the schema question specifically (a live run shows one sample; the source shows the complete set of emitted event types and the exact envelope). A live smoke run is still required, for the things source-reading cannot settle, and is scheduled as Phase 1 (§9) with its exact commands. §3 marks every claim as either **[source-verified]**, **[docs]**, or **[unverified — Phase 1 must confirm]**.

House-style precedent: `docs/architecture-history/multi-provider-llm-plan.md` (Sessions 159–164), which introduced this seam's first second provider. This spec deliberately reuses its section numbering habits, its Trap/dragon framing, and its per-phase DONE criteria.

---

## 1. Scope

### 1.1 In scope

1. A new `"opencode"` member in both agents' `LLMProvider` `Literal`s and one branch in each `make_llm_client`.
2. Two new client modules — `agents/intake/opencode_client.py` and `packages/data-agent/.../opencode_client.py` — implementing `IntakeLLMClient` / `LLMClient` by shelling out to `opencode run --format json`.
3. One `LLM_PROVIDERS` registry entry in `orchestrator/config.py`.
4. The deterministic test tier for both clients, plus the drift guards C4 forces (§7).
5. Wiring the new provider into the existing eval / shadow-run / cutover machinery (`tests/eval/`), so the §3.4 thresholds of the prior plan gate any cutover.

### 1.2 Out of scope

- **Choosing which *underlying* vendor OpenCode routes to.** That is the operator's config (`opencode.json` / `--model provider/model`), which is the entire point of the adapter. This project ships no opinion on it beyond the eval requirement that a measured run pin its model.
- **Native schema-constrained output.** Not a shipped OpenCode feature (§3.3).
- **A shared subprocess helper spanning both packages.** C4 forbids it (Trap 1 of the prior plan). The duplication is deliberate and gets a drift guard instead (§7.2).
- **Retry / back-off / rate-limit mapping.** The existing clients have none; the new one inherits that thinness by design. Do not fix it here (it is Q4 of the prior plan, still open).
- **Making `opencode` a hard install requirement.** It stays optional — absent binary ⇒ a clear error only when the `opencode` provider is selected.

---

## 2. Current state — the seam, as built (verified at `a3f33d8`)

Everything in this section was read this session, not recalled.

### 2.1 The two seams

| | Intake | Data agent (standalone wheel) |
|---|---|---|
| Protocol | `IntakeLLMClient` — 4 methods (`agents/intake/protocol.py:75-93`) | `LLMClient` — 5 required + 1 optional `rank_candidate_tables` (`.../llm.py:101-160`) |
| Error class | `IntakeLLMError(RuntimeError)` (`protocol.py:96-98`) | `LLMParseError(ValueError)` (`.../anthropic_client.py:112-113`) |
| Transport method | `_call_json(system, user) -> Any` — **returns parsed JSON** (`anthropic_client.py:363-401`) | `_call_claude(system, user) -> str` — **returns raw text**; each caller parses (`.../anthropic_client.py:376-405`) |
| Factory | `factory.py:32` Literal, branches at `:52`/`:63` | `factory.py:33` Literal, branches at `:53`/`:63` |

**The structural asymmetry is load-bearing** and must be preserved: intake fuses the round-trip and the parse; the data agent keeps them apart. A single shared transport shape would break one of them.

### 2.2 What is provider-specific today — and it is remarkably little

In `AnthropicLLMClient` (both packages), *only* `__init__` and the one transport method touch the provider. Prompts, JSON-shape instructions, the `_build_draft` / `_build_governance` / `PrimaryQuerySpec` constructors, and `_extract_json` are all provider-agnostic. `BedrockLLMClient` exploits exactly this: it overrides `__init__` and `DEFAULT_MODEL` and inherits everything else (`agents/intake/bedrock_client.py:86-145`).

**This is why D1 works.** OpenCode is not an SDK drop-in the way `AnthropicBedrockMantle` is, so the override moves one level down — from *the client object* to *the transport method* — but the inheritance argument is identical.

### 2.3 The three guards inside the current transport

`_call_json` / `_call_claude` raise their seam's error class for:

1. `stop_reason == "max_tokens"` → `"Claude response truncated at max_tokens=16384 (stop_reason='max_tokens'); the response is incomplete. Raise max_tokens for this client."`
2. empty `response.content` → `"Claude returned an empty content list"`
3. first block not a `TextBlock` → `"expected TextBlock from Claude, got {type}"`

All three messages are pinned byte-identical across the twins by `tests/test_llm_json_parity.py:226-267`. **None of the three has an OpenCode analogue** — they are SDK-response-shaped. §4.7 specifies what replaces them.

### 2.4 Provider-selection surfaces (all default to `anthropic`)

- `scripts/run_pipeline.py:488-489` (`--provider`), `:479-480` (`--model`, default `PILOT_DEFAULT_MODEL = "claude-opus-4-7"` at `:111` — an **intentional** two-tier default, Learning #20; do not collapse it).
- `packages/data-agent/.../cli.py:108`/`:177` (`--provider`, help generated from `KNOWN_PROVIDERS` at `:66`).
- `src/model_project_constructor/ui/intake/app.py:74` — resolves `provider` argument → `INTAKE_LLM_PROVIDER` env → `DEFAULT_LLM_PROVIDER`.

All three route through `make_llm_client`, so **none of them needs an edit** for a new provider. The data-agent CLI help updates itself from `KNOWN_PROVIDERS`.

### 2.5 Trap check against the prior plan's traps

| Prior trap | Status for `"opencode"` |
|---|---|
| **Trap 1** — C4 forces double implementation | **Applies.** Two client modules, two copies of the JSONL-extraction helper. §7.2 adds the drift guard. |
| **Trap 2** — the `"openai"` unknown-provider sentinel | **Not triggered.** The sentinel is the literal string `"openai"` (`tests/agents/intake/test_factory.py:103-107`, `tests/data_agent_package/test_factory.py:104-106`, `tests/ui/intake/test_provider_selection.py:137-139`, `tests/data_agent_package/test_cli.py:111`/`:310`). `"opencode"` is a different string and neither contains nor is contained by it, so every sentinel assertion still holds. **Verify with `rg '"openai"' tests/` at Phase 2 pre-flight anyway** — the check is cheap and the failure mode is silent. |
| **Trap 3** — the intake UI hardcodes a provider | **Already fixed** (Session 163). `app.py:74` resolves through env/arg. No work. |
| **Trap 4** — model-default inconsistency | **Applies in a new form.** `run_pipeline.py --model` defaults to a first-party Anthropic id, which is meaningless to OpenCode (it wants `provider/model`). Same known gap the Bedrock provider has; operators pass `--model` explicitly. Do **not** "fix" it by collapsing the two-tier default (Learning #20). |
| **Trap 5** — thin clients, no retry/rate-limit/error mapping | **Applies, and is larger here.** A subprocess has failure modes an SDK call does not. §4.7 is the mapping table; retry policy stays out of scope. |

---

## 3. The external contract — what `opencode run` actually is

**Provenance.** All **[source-verified]** claims below come from `packages/opencode/src/cli/cmd/run.ts` in `anomalyco/opencode`, fetched this session via the GitHub API. Repo state at fetch: default branch `dev` @ `32f278b48f1a` (2026-08-01), latest release **v1.18.11** (2026-08-01), MIT, TypeScript, 192k stars, actively developed. `run.ts` itself was last modified in `20445ca03133` (2026-06-30). **This landscape moves fast — Phase 1 must re-fetch and diff before trusting any line below.**

### 3.1 Invocation and flags **[source-verified]**

```
opencode run [message..]
```

Flags relevant to this adapter (`run.ts:160-260`):

| Flag | Meaning | Adapter uses it? |
|---|---|---|
| `--format default\|json` | `"format: default (formatted) or json (raw JSON events)"`, default `default` | **Yes — always `json`** |
| `--model, -m` | `"model to use in the format of provider/model"` | Yes, when a model is configured |
| `--agent` | `"agent to use"` | Yes (§4.4) |
| `--dir` | `"directory to run in..."` | **Yes — the sandbox** |
| `--auto` (aliases `--yolo`, `--dangerously-skip-permissions`) | `"auto-approve permissions that are not explicitly denied (dangerous!)"` | **Never** |
| `--continue, -c` / `--session, -s` / `--fork` | session resumption | No — every call is stateless by design |
| `--attach` | attach to a running `opencode serve` | Not in v1; the forward path (§4.3) |
| `--file, -f`, `--share`, `--title`, `--variant`, `--thinking`, `--port`, `--username`, `--password`, `--command` | — | No |

**There is no `--system` / `--system-prompt` flag.** This is the load-bearing absence behind D2.

**The prompt may be supplied on stdin.** `run.ts:416-418`:

```ts
const piped = process.stdin.isTTY ? undefined : await Bun.stdin.text()
message = resolveRunInput(message, piped) ?? ""
```

and `resolveRunInput` (`run.ts:40-50`) returns `piped` when no positional message is given, `value` when nothing is piped, and `value + "\n" + piped` when both are present. **So `opencode run --format json` with the prompt on stdin and no positional argument is a supported invocation.** §4.4 uses it.

### 3.2 The `--format json` event stream **[source-verified]** — this is what §9.2 asked for

The emitter (`run.ts:678-691`):

```ts
function emit(type: string, data: Record<string, unknown>) {
  if (args.format === "json") {
    process.stdout.write(
      JSON.stringify({ type, timestamp: Date.now(), sessionID, ...data }) + EOL,
    )
    return true
  }
  return false
}
```

**Shape: JSONL — one JSON object per line on stdout**, each with `type` (string), `timestamp` (epoch ms), `sessionID` (string), plus a per-type payload. The complete set of emitted types:

| `type` | Payload | Emitted when | Source |
|---|---|---|---|
| `text` | `{part}` | a text part completes (`part.type === "text" && part.time?.end`) | `run.ts:748-749` |
| `reasoning` | `{part}` | a reasoning part completes **and** `--thinking` was passed | `run.ts:761-762` |
| `tool_use` | `{part}` | a tool part reaches `completed` or `error` | `run.ts:719-720` |
| `step_start` | `{part}` | a `step-start` part appears | `run.ts:740-741` |
| `step_finish` | `{part}` | a `step-finish` part appears | `run.ts:744-745` |
| `error` | `{error}` | a `session.error` event, or the `session.prompt` / `session.command` call itself returns an error | `run.ts:784`, `:850`, `:867` |

**The assistant's answer is the concatenation, in emission order, of `part.text` over every `type == "text"` event.** Multiple `text` events per run are possible (a multi-step agent turn), so the adapter must join them, not take the first.

⚠ **Phase 1 amends this (Appendix A.4 C4): blind concatenation is unsafe once tools fire.** An observed 3-step run emitted three `text` events, two of them narration (`"I'll list the files…"`, `"Now let me read…"`) ahead of the real answer. Prefer the text of the **final step** — the one whose `step_finish.reason == "stop"` — and rely on tool denial to keep runs single-step. Also note `step_finish`'s part carries more than this table records: **`reason`** (`"stop"` / `"tool-calls"`), **`tokens{input,output,total,cache{write,read}}`**, and **`cost`** (Appendix A.4 C3).

**Termination and exit status** (`run.ts:788-794`, `:828-872`): the event loop breaks on `session.status` with `status.type === "idle"`. `process.exitCode` is set to `1` when the loop recorded a session error, when the prompt/command call returned an error, or when the stream threw. **Success ⇒ exit 0; any of those failures ⇒ exit 1.** There is no richer documented exit-code vocabulary — treat "non-zero" as the failure signal, not just `1`.

**Non-JSON lines can appear on stdout.** Early `UI.error(...)` / `die(...)` paths (e.g. `run.ts:420-423`, `:425-428`) run *before* any JSON is emitted. The parser must therefore **skip unparseable lines rather than fail on them**, and use the exit code — not stream contents — as the authority on success.

### 3.3 What has no OpenCode equivalent

| Concept in the current clients | OpenCode | Consequence |
|---|---|---|
| per-call `system=` | **absent** — no flag **[source-verified]** | D2: fold into the message. The largest quality risk. |
| `max_tokens=16384` | no `run` flag **[source-verified]** | `max_tokens` becomes **inert** for this provider. ⚠ **Amended by Phase 1 (Appendix A.4 C3): the truncation guard DOES have an analogue** — `step_finish.reason` (observed `"stop"` and `"tool-calls"`). Prefer it over letting truncation surface as an opaque `_extract_json` failure. The same part also exposes `tokens` and `cost`, i.e. **per-call telemetry the SDK clients do not provide** — surface it. (No truncation was forced in Phase 1, so the exact `length`-style value is inferred, not observed.) |
| `temperature` | not a `run` flag; settable per-agent in config **[docs]** | Out of scope; note for the eval's non-determinism policy. |
| schema-constrained output | **not shipped** — an open feature request (`anomalyco/opencode` issue #9320) proposes `--json <schema>` **[verified: the issue is a request, not documentation of existing behaviour]** | Decision C of the prior plan carries unchanged: keep fenced-text + `_extract_json`. |

### 3.4 Auth and configuration **[docs]**

- OpenCode resolves credentials from **provider-specific environment variables** and from a credential store written by its interactive `/connect` flow at `~/.local/share/opencode/auth.json`. The providers page explicitly names, among others, `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_PROFILE` / `AWS_REGION` / `AWS_BEARER_TOKEN_BEDROCK`, `AZURE_RESOURCE_NAME`, `CLOUDFLARE_API_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS` / `GOOGLE_CLOUD_PROJECT`, `NVIDIA_API_KEY`, `GITLAB_TOKEN`, `SNOWFLAKE_CORTEX_TOKEN`.
  **[RESOLVED — Phase 1, Appendix A.1 #1]** `ANTHROPIC_API_KEY` **is** honoured; the docs page was merely incomplete. Verified free of charge: `opencode models` returns 7 ids without a credential and 24 (incl. 17 `anthropic/*`) with the env var set. Supplying it through the child environment writes **no** `auth.json`, which is how Phase 1 avoided creating the second at-rest credential store §11 Q4 asks about.
- Config lives in `opencode.json` (`$schema: https://opencode.ai/config.json`), with a `provider` block naming the `@ai-sdk/...` npm package, `options.baseURL`, and a `models` map — i.e. **an enterprise can point OpenCode at an internal gateway**, which is the enterprise-migration-relevant property.
- Provider registry: *"OpenCode uses the AI SDK and Models.dev to support 75+ LLM providers."*
- Agents are defined in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project), as markdown with YAML frontmatter — `description`, `mode: primary|subagent|all`, `model`, `temperature`, and `permission: {edit|bash|write: allow|ask|deny}` (the older `tools` key is deprecated in favour of `permission`). **The file's basename is the agent id.** The frontmatter body is the agent's system prompt (`prompt` may instead point at a file via `{file:./path}`).
  **[RESOLVED — Phase 1, Appendix A.1 #2]** **Partial replace.** A custom agent's prompt replaces ~4,720 tokens of built-in *persona*, but a **constant ~4,830-token scaffold survives** and cannot be removed via the agent file (`--pure` does not help). Measured by token accounting: 9,552 → 4,832 cache-write tokens, with a 2,000-token-longer prompt landing at 6,836 (delta exactly the added text).

### 3.5 Hazards — each one closed by a specific adapter decision

| # | Hazard | Evidence | Closed by |
|---|---|---|---|
| H1 | **Indefinite hang.** `const piped = process.stdin.isTTY ? undefined : await Bun.stdin.text()` (`run.ts:416`) — a child spawned with an inherited non-TTY stdin that never closes blocks forever, *before* any timeout inside the model call. | [source-verified] | Always spawn with `stdin` bound to a pipe the adapter closes (writing the prompt then closing), or `DEVNULL`. **Never inherit stdin.** Plus a hard `subprocess` timeout. |
| H2 | **Prompt content leaks into the process table.** Interview transcripts and `DataRequest` free text may contain PII (`AI-Dependencies.md` §6.3). Anything in `argv` is world-readable via `ps`. | Standard POSIX | Pass the prompt on **stdin**, never as a positional argument (§3.1 shows this is supported). |
| H3 | **The agent reads or writes the host repository.** `opencode` is a coding agent; by default `--dir` is the cwd, and it discovers `AGENTS.md` / project config by walking the tree. | [docs] + `run.ts:820` | `--dir <ephemeral temp dir outside the repo>` + an agent definition denying `edit`/`write`/`bash`. |
| H4 | **`--auto` auto-approves tool permissions.** Its own help string says `(dangerous!)`. | `run.ts:242-244` [source-verified] | Never pass it. ⚠ **THE CLAIM THAT "THE DEFAULT IS ALREADY SAFE" IS FALSE — DISPROVEN IN PHASE 1 (Appendix A.4 C1).** Without `--auto`, a live run still listed the directory, **read a file, and disclosed its contents**, exit 0. Permission auto-reject does **not** cover the `read` tool. Headless runs do not hang — but they also do not refuse reads. **The tool-denying agent definition (with `read: deny`) is therefore MANDATORY, not defence-in-depth.** Verified to work: with it, zero `tool_use` events and an explicit refusal. |
| H5 | **Session state accumulates on disk.** Every `run` creates a session (`run.ts:671-676`); `--continue`/`--session` exist to resume them. One interview is ~25 calls ⇒ ~25 sessions. | [source-verified] | Not blocking, but the operator checklist must mention it. Phase 1 measures where sessions are stored and how large they get. |
| H6 | **Agentic multi-step behaviour.** The model may emit `tool_use` / `step_*` events instead of a single text answer, and text may arrive in several parts. | [source-verified] | Concatenate all `text` events; deny tools via the agent definition; treat a run with **zero** `text` events as an error (§4.7). |

---

## 4. Design decisions

### 4.1 D1 — Transport-method override (chosen) vs. two alternatives

| Option | What it is | Prompt-drift surface | Honesty | Verdict |
|---|---|---|---|---|
| **A — subclass, override the transport method (CHOSEN)** | `class OpenCodeLLMClient(AnthropicLLMClient)` overriding `__init__` + `_call_json` / `_call_claude` | **Zero** — prompts, builders, `_extract_json` inherited | The transport *is* the thing that differs; overriding exactly it says so | **Chosen** |
| B — SDK-shaped transport shim | Build a duck-typed object exposing `.messages.create(...)` returning something with `.content == [TextBlock(...)]` and `.stop_reason`, then reuse `AnthropicLLMClient` unchanged | Zero | Poor — it fabricates a `stop_reason` OpenCode does not have and dresses a subprocess as an SDK response; the three inherited guards (§2.3) would be checking invented fields | Rejected |
| C — standalone client implementing the protocol from scratch | A new class duplicating all prompts | **Very high** — prompts would exist in 4 copies with no guard (`test_llm_json_parity.py` guards `_extract_json`, **not** prompts) | — | Rejected |

**Why A over B.** B is tempting because it maximises reuse — it is literally the shape of the existing test double `_FakeAnthropic` (`tests/test_llm_json_parity.py:97-99`). But reuse of *guards that no longer mean anything* is not reuse, it is camouflage. A subprocess fails by exiting non-zero, timing out, or emitting an `error` event; none of those is "an empty content list". A's fresh guards say what actually went wrong.

**Naming caveat to document in the module docstring:** `OpenCodeLLMClient` inherits from a class named `AnthropicLLMClient` while not necessarily talking to Anthropic. That reads oddly and *will* prompt a future "fix". Pre-empt it: the base class is the project's **prompt-and-parse** layer that happens to carry an Anthropic transport; the subclass replaces the transport. Say so in the docstring, as `bedrock_client.py:28-38` says the analogous thing.

### 4.2 D2 — Folding `system` into the message

Both seams pass a per-method system prompt (intake: `SYSTEM_INTERVIEWER`, `SYSTEM_GOVERNANCE`; data agent: a distinct one per method). OpenCode has no per-call system slot.

| Option | Mechanics | Verdict |
|---|---|---|
| **A — prepend `system` to the user message (CHOSEN)** | one string: `f"{system}\n\n{user}"` | **Chosen** — no filesystem writes, no per-call config, identical text reaches the model, just in a different role |
| B — write one agent file per distinct system prompt | 6+ generated `.md` files under the sandbox's `.opencode/agents/`, selected per call via `--agent` | Rejected for v1: more moving parts, and the agent prompt's replace-vs-append semantics are unverified (§3.4) — so it might not even isolate the prompt |
| C — `opencode serve` + HTTP API | may expose a richer per-session prompt surface | Deferred with D3 |

**Exact separator to use: `system + "\n\n" + user`.** Fix it in a module constant so both packages' copies are identical and the parity guard can pin it.

**The residual risk is real and must not be hand-waved.** A prompt engineered as a system instruction and delivered as user text can behave differently, and OpenCode wraps everything in its own coding-agent framing besides. That risk is *measurable* with machinery this project already owns — the golden corpus and the §3.4 thresholds of the prior plan — which is exactly why Phase 3/4 exist and why no cutover may happen on unmeasured thresholds.

### 4.3 D3 — Process-per-call

`opencode run` spawns a fresh Bun process, creates a session, subscribes to the event stream, and tears down — per call. An interview is ~20-25 calls. **[MEASURED — Phase 1, Appendix A.1 #4]** per-call process overhead is **~0.77 s** (0.77/0.77/0.76 over three billing-free runs) — ~24 % on top of a 3.2 s call, or **~19 s per 25-call interview**. Real, but not enough on its own to justify the `serve` lifecycle.

`opencode serve` + `run --attach http://localhost:PORT` amortises startup. Deliberately deferred: it adds a server lifecycle (start, health-check, shutdown, port allocation, auth via `OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD`) for a latency win that has not been measured. Because `--attach` is a flag on the *same* command, adopting it later is a constructor argument, not a rewrite. Record the measured per-call overhead in Phase 1 so the decision to revisit has a number behind it.

### 4.4 D4 — The invocation, exactly

```
opencode run --format json [--model <provider/model>] [--agent <name>] --dir <sandbox>
```

with:

- **prompt on stdin**, then stdin closed (H1, H2);
- **`--dir <sandbox>`** — a `tempfile.mkdtemp()` directory owned by the client instance, created lazily on first call, well outside the repository tree (H3). The client writes `.opencode/agents/<agent>.md` into it. ⚠ **Phase 1 amends this twice.** (a) The original "unless the caller supplied an `agent=` name, in which case the adapter writes nothing" escape hatch is **unsafe and must be removed or hard-gated** — per Appendix A.4 C1 the tool denial is the only thing preventing file reads, so an operator-supplied agent must still be validated as denying tools. **AS BUILT (Session 213): removed.** The parameter is now `agent_name`, which renames the generated definition; the adapter always writes and selects its own (see §5.1's as-built note). (b) The sandbox is **not free**: an empty `--dir` stays 0 bytes, but once an agent file is present OpenCode materialises `.opencode/node_modules` (~1 MB, up to 62 MB observed) and therefore **needs npm-registry reachability**. **Create it once per client instance and reuse it — never per call** (Appendix A.4 C6);
- the bundled agent definition denying every mutating tool:

  ```yaml
  ---
  description: Non-interactive structured-output adapter for Model Project Constructor
  mode: primary
  permission:
    edit: deny
    write: deny
    bash: deny
  ---
  ```

  **[RESOLVED — Phase 1, Appendix A.1 #3]** accepted keys at v1.18.11: `description`, `mode`, and `permission:` with `edit`/`write`/`bash`/`read`/`webfetch`. Agent id = file basename; `.opencode/agents/` (plural) alone suffices. **The YAML must be block-style — flow-style `permission: {edit: deny, …}` silently breaks agent loading and makes `opencode` print usage help to stderr with empty stdout and a non-zero exit (Appendix A.4 C5).** Whether `mode: primary` is strictly *required* was never isolated — keep setting it. **Add `read: deny`: Appendix A.4 C1 proves the default is NOT safe and reads succeed without it.** **AS BUILT (Session 213):** the shipped definition denies all five accepted keys — `edit`, `write`, `bash`, `read` **and `webfetch`**. `webfetch` goes beyond the spec's instruction deliberately: it is the one remaining tool that could move prompt content (interview transcripts, `DataRequest` free text) off the machine, and denying it costs nothing for a structured-output adapter that should never browse;
- **no `--auto`** (H4);
- `env` passed through unchanged — OpenCode needs the operator's provider credentials (§3.4), and the adapter has no business filtering them.

### 4.5 D5 — Dependency posture

**Python side: nothing new.** `json`, `os`, `shutil`, `subprocess`, `tempfile` only. Neither `pyproject.toml` changes. This is a genuine advantage over every SDK-based provider and should be stated as such: the `anthropic[bedrock]` extra dragged `boto3`/`botocore` into every install (`AI-Dependencies.md` §6.8); this adapter drags in nothing.

**Non-Python side: a new dependency class.** The `opencode` binary (npm `opencode-ai`, `curl -fsSL https://opencode.ai/install | bash`, `brew install anomalyco/tap/opencode`, Docker, and others). Implications the executor must handle:

1. **Discovery + a good error.** `shutil.which(executable)` at construction; if absent, raise the seam's error class naming the executable and one install command. Fail at construction, not mid-interview.
2. **Version skew.** The CLI is on a fast release train (v1.18.11 shipped the same day this spec was written). The event schema is not a stability contract. **Record the version.** Run `opencode --version` at construction (or once per client) and include it in the error text of any parse failure — a future breakage should be one line away from "you're on a version we haven't validated".
3. **CI stays hermetic.** No CI job installs `opencode`; the deterministic tier injects a fake runner and never spawns a process (§7.1).
4. **Enterprise install path** is a real question for the migration (`docs/planning/enterprise-migration.md`): an internal npm mirror or a vendored binary. Out of scope here; flagged in §11.

### 4.6 D6 — `DEFAULT_MODEL = None`

The other clients pin a model id. This one should not:

- OpenCode model ids are `provider/model` strings drawn from Models.dev; picking one here would silently re-introduce vendor choice into *this* repository, which is the opposite of the adapter's purpose.
- The operator's `opencode.json` already expresses the intended default, and an enterprise standardising on OpenCode will manage it there.
- Inventing a plausible-looking id without verifying it against `opencode models` would be exactly the "documentation-level verification" anti-pattern the architecture workstream names.

So: `DEFAULT_MODEL: str | None = None` ⇒ **omit `--model` entirely** and let OpenCode decide. The factory's `model=None → provider default` contract is unchanged; the branch reads `OpenCodeLLMClient(model=DEFAULT_MODEL if model is None else model)` exactly like the others.

**The cost, stated plainly:** this weakens reproducibility, which `AI-Dependencies.md` §6.5 names as a live risk. **Mitigation, mandatory:** every eval and every shadow run must pass an explicit `--model`, and the cutover report must record it (the prior plan's Trap-4 discipline: *"the eval pins the exact `(provider, model)` it measures"*). §11 puts the alternative — pin a verified id — to the operator.

### 4.7 D7 — Error mapping (Trap 5, discharged)

Every failure below maps to the **seam's own** error class (`IntakeLLMError` for intake, `LLMParseError` for the data agent) — the intentional divergence is preserved and is pinned by `test_llm_json_parity.py:273-294`.

| Failure | Detection | Message shape |
|---|---|---|
| binary missing | `shutil.which(...) is None` at construction | `"opencode executable not found on PATH (looked for {name!r}); install it or pass executable=..."` |
| timeout | `subprocess.TimeoutExpired` | `"opencode run timed out after {timeout}s"` — chain the original via `from exc` |
| spawn failure | `OSError` from `subprocess.run` | `"failed to spawn opencode: {exc}"` |
| non-zero exit | `returncode != 0` | ⚠ **Amended by Phase 1 (Appendix A.4 C2): stderr is EMPTY on this path** — `{stderr_tail}` would yield `""`. Build the message from the stdout `error` event: `error.name`, `error.data.message`, and **`error.data.ref`** (the payload is otherwise generic — `"Unexpected server error"` — so the `ref` is the only distinguishing detail). Keep a stderr tail only as a fallback. |
| non-zero exit with **zero stdout lines** | `returncode != 0` and no parseable line | **New in Phase 1 (Appendix A.4 C5).** This is the malformed-agent-definition path: OpenCode prints usage help to *stderr* and emits nothing on stdout. Diagnose it distinctly — `"opencode rejected its invocation (likely a malformed agent definition); stderr: {stderr_tail}"` — because it is a bug in the adapter's own generated file, not a provider failure. |
| `error` event with exit 0 | an `error`-typed line was emitted but the process exited 0 | same as above; do not silently succeed |
| no `text` events | zero `type == "text"` lines | `"opencode returned no assistant text"` — the structural analogue of the old empty-content guard |
| malformed JSON in the assistant text | the inherited `_extract_json` raises | unchanged, inherited |

**Do not add retry.** The existing clients have none (Trap 5); adding it only here would make the providers behave differently under load, which corrupts the eval comparison.

### 4.8 D8 — The `LLM_PROVIDERS` registry entry

```python
"opencode": LLMProviderSpec(api_key_env_var=None),
```

`api_key_env_var=None` is not a shrug — it is *correct*, and for a better reason than Bedrock's. OpenCode's credential depends on which underlying provider the operator configured, and may live in `~/.local/share/opencode/auth.json` rather than any environment variable at all. There is no single env var to name, so `require_llm_api_key("opencode")` should refuse with a pointed message the way it does for `bedrock` (`config.py:302-331`).

**Side benefit:** this is why the unverified `ANTHROPIC_API_KEY`-on-OpenCode question (§3.4) does not block the design.

**Lockstep warning:** `LLM_PROVIDERS` (`config.py:158-161`) and the two `LLMProvider` `Literal`s are kept in sync **by convention, not by a test** — the module comment at `config.py:152-157` and `Extending-the-Pipeline.md` both say so explicitly, because the wheel cannot import the orchestrator (C4). Three edits, by hand, in the same session.

---

## 5. Interface contract

### 5.1 Intake — `src/model_project_constructor/agents/intake/opencode_client.py`

```python
DEFAULT_MODEL: str | None = None
DEFAULT_TIMEOUT_S: float = 600.0          # matches the Anthropic SDK's own default request timeout
DEFAULT_EXECUTABLE = "opencode"
DEFAULT_AGENT_NAME = "mpc-structured"

class OpenCodeLLMClient(AnthropicLLMClient):
    def __init__(
        self,
        model: str | None = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,   # inert; kept for signature parity — document it
        *,
        executable: str = DEFAULT_EXECUTABLE,
        agent: str | None = None,               # ⚠ AS BUILT: REMOVED — see the note below
        workdir: str | None = None,             # None -> ephemeral mkdtemp sandbox
        timeout: float = DEFAULT_TIMEOUT_S,
        runner: Callable[..., CompletedProcess[str]] | None = None,   # test seam
    ) -> None: ...

    def _call_json(self, system: str, user: str) -> Any: ...          # override
```

- `__init__` must **not** construct `anthropic.Anthropic()`. Pass an unused sentinel to `super().__init__(client=..., model=..., max_tokens=...)` so `self._model` / `self._max_tokens` are still set by the parent — a `None` would trigger the parent's SDK construction (`anthropic_client.py:278-281`) and demand an `ANTHROPIC_API_KEY` that this provider does not need.
- **⚠ AS BUILT (Session 213) — `agent=` was removed, not hard-gated.** Appendix A.4 C1 required one or the other; removal is the stronger choice, because a caller-supplied agent name cannot be validated (the definition may live in the caller's `~/.config/opencode/agents/`, outside the sandbox the adapter owns). The shipped signature carries **`agent_name: str = DEFAULT_AGENT_NAME`**, which renames the *generated* tool-denying definition; the adapter always writes it and always passes `--agent`. There is deliberately no path to an unlocked agent. Pinned by `test_the_tool_denial_cannot_be_switched_off` in both packages.
- **⚠ AS BUILT (Session 213) — `max_tokens` inertness is now partial.** It still never reaches the argv (no flag exists), but Appendix A.4 C3's `step_finish.reason` gives the truncation guard an analogue, so a truncated response raises rather than silently reaching `_extract_json`. The error text deliberately does **not** say "raise max_tokens" — that would send the operator somewhere with no effect; it points at the OpenCode model config instead.
- `runner` defaults to `subprocess.run` and is the **only** thing tests replace. No test spawns a process.
- `_call_json` returns `_extract_json(text)` — same return contract as the parent (parsed JSON), so all four interview methods are inherited untouched.
- The four `IntakeLLMClient` methods, `_build_draft`, `_build_governance`, `_format_qa`, `_draft_as_dict`, `_extract_json`, and every prompt constant: **inherited, not overridden.**

### 5.2 Data agent — `packages/data-agent/src/model_project_constructor_data_agent/opencode_client.py`

Identical in shape, except:

- it subclasses the **wheel's** `AnthropicLLMClient` and overrides **`_call_claude`**, returning **raw text** (`str`), not parsed JSON — preserving the §2.1 asymmetry;
- it raises `LLMParseError`;
- it inherits `rank_candidate_tables`, so the optional protocol method works for free (`discovery.probe_information_schema` `hasattr`-dispatches it);
- **it imports only the wheel and the stdlib.** No orchestrator import — C4.

### 5.3 The duplicated helper pair (C4-forced)

Each module carries its own copy of:

```python
def _extract_assistant_text(stdout: str) -> str:
    """Join `part.text` across every ``type == "text"`` JSONL event, in order.

    Skips lines that are not valid JSON (OpenCode writes some human-readable
    output to stdout before the event stream starts) and lines whose ``type``
    is not ``"text"``. Returns "" when no text event is present — the caller
    turns that into the seam's error.
    """
```

plus a small `_error_payloads(stdout) -> list[str]` for the `error`-typed lines. **These are the new twins.** The `_extract_json` twins drifted once and cost three sessions to repair (Sessions 98-100, traceable to Session 51's live crash) — that is precisely why §7.2 requires a parity battery for these two *at the moment they are created*, not later.

### 5.4 Factory branches

```python
LLMProvider = Literal["anthropic", "bedrock", "opencode"]
...
    if provider == "opencode":
        from ...opencode_client import DEFAULT_MODEL, OpenCodeLLMClient
        return OpenCodeLLMClient(model=DEFAULT_MODEL if model is None else model)
```

Lazy import inside the branch, matching the existing convention (`factory.py:52-72`) — even though this module imports no heavy SDK, the convention is what `test_factory_import_does_not_load_anthropic` pins, and consistency is cheaper than an exception.

---

## 6. Grep-based inventory (baseline `a3f33d8`)

Every line number below was produced by an actual search this session. **Re-run each search at the start of the session that edits it** — line numbers drift, and this project's own plan-execution discipline is to re-confirm them before editing rather than trust a plan's snapshot.

### 6.1 Files created

| Path | Purpose |
|---|---|
| `src/model_project_constructor/agents/intake/opencode_client.py` | intake client |
| `packages/data-agent/src/model_project_constructor_data_agent/opencode_client.py` | data-agent client |
| `tests/agents/intake/test_opencode_client.py` | intake client tests |
| `tests/data_agent_package/test_opencode_client.py` | data-agent client tests |

### 6.2 Files edited

| Path | Line(s) at `a3f33d8` | Edit |
|---|---|---|
| `src/model_project_constructor/agents/intake/factory.py` | `:32` Literal; new branch after `:72` | add `"opencode"` + branch |
| `packages/data-agent/.../factory.py` | `:33` Literal; new branch after `:72` | add `"opencode"` + branch |
| `src/model_project_constructor/orchestrator/config.py` | `:158-161` (`LLM_PROVIDERS`) | one registry entry |
| `tests/test_llm_json_parity.py` | `_SEAMS` at `:145-156` | 2 rows + a new helper-parity battery (§7.2) |
| `tests/agents/intake/test_factory.py` | `:110-113` | assert `"opencode" in KNOWN_PROVIDERS` |
| `tests/data_agent_package/test_factory.py` | `:110-115` | same |
| `tests/eval/eval_cutover.py` | `:36` `CANDIDATE_PROVIDERS`; `:41-60` `provider_creds_available` | add the provider + its runnability probe |
| `tests/orchestrator/test_config.py` | `:195-204` | assert the new registry entry |

### 6.3 Files verified as needing **no** edit

- `scripts/run_pipeline.py` — routes through the factory; `--provider` accepts any string (`:488-489`).
- `packages/data-agent/.../cli.py` — `_PROVIDER_HELP` is generated from `KNOWN_PROVIDERS` (`:66`).
- `src/model_project_constructor/ui/intake/app.py` — resolves through env/arg (`:74`).
- Both packages' `__init__.py` — re-export symbol *names*, which do not change.
- Both `pyproject.toml` — no new Python dependency (D5).
- `.github/workflows/ci.yml` — no `opencode` install; hermeticity preserved.

### 6.4 Sentinel check

`rg '"openai"' tests/` → `tests/agents/intake/test_factory.py:103,105`; `tests/data_agent_package/test_factory.py:104,106`; `tests/ui/intake/test_provider_selection.py:137,139,194`; `tests/data_agent_package/test_cli.py:111,116,310,317`; `tests/eval/test_eval_cutover.py:185`; `tests/orchestrator/test_config.py:168`. **All remain valid** — `"opencode"` ≠ `"openai"`. Re-verify at pre-flight.

---

## 7. Test plan

### 7.1 Deterministic tier (hermetic, every PR)

Per client, with `runner` injected — **no process is ever spawned**:

1. **argv construction** — asserts `--format json` present, `--auto` **absent** (a dedicated negative test; this is a safety property, not a detail), `--dir` present and outside the repo, `--model` present only when a model is configured.
2. **prompt on stdin** — the prompt text appears in the `input=` kwarg and **not** in the argv list (H2 as an executable assertion).
3. **stdin is never inherited** — `stdin` is DEVNULL or the adapter's own pipe (H1).
4. **happy path** — a JSONL fixture with `step_start` + two `text` events + `step_finish` yields the concatenated text; intake's `_call_json` returns parsed JSON, the data agent's `_call_claude` returns the raw string.
5. **non-JSON preamble tolerated** — a fixture with a leading human-readable line still parses.
6. **each row of the §4.7 error table** — one test per failure mode, asserting the seam's error class and the message.
7. **construction fails fast** when `shutil.which` returns `None`.
8. **`max_tokens` is inert** — pinned so a future reader does not assume it is honoured.
9. **factory** — `make_llm_client("opencode")` constructs; `KNOWN_PROVIDERS` includes it; unknown-provider error lists it.

Capture the JSONL fixtures **from the Phase 1 live run** and commit them. Fixtures invented from this spec would test the spec, not OpenCode.

### 7.2 Drift guards (C4 — mandatory, same session as the clients)

- **`_SEAMS` rows** in `tests/test_llm_json_parity.py:145-156`: `_Seam("intake", "opencode", intake_client._extract_json, IntakeLLMError)` and `_Seam("data_agent", "opencode", da_client._extract_json, LLMParseError)`. Both reuse the package parser (the clients inherit it), exactly like the Bedrock rows — the comment at `:148-153` explains this pattern and should be extended, not duplicated.
- **A new parity battery for `_extract_assistant_text`** — the same input battery through both copies, asserting identical output, plus identical behaviour on: no `text` events, several `text` events, non-JSON lines, `error` lines, and unknown event types. Without this, the twins have no guard on the day they are born.

### 7.3 Structural invariants (already exist — must stay green)

| Invariant | Test |
|---|---|
| wheel imports no orchestrator | `tests/test_data_agent_decoupling.py` |
| factory import loads no SDK | `test_factory_import_does_not_load_anthropic` (`tests/agents/intake/test_factory.py:130`, `tests/data_agent_package/test_factory.py:132`) |
| unknown provider constructs no SDK | `test_unknown_provider_does_not_construct_sdk` |
| CI hermetic without keys | the four `ci.yml` jobs |

### 7.4 Eval / cutover tier

- `CANDIDATE_PROVIDERS` (`tests/eval/eval_cutover.py:36`) gains `"opencode"`; `provider_creds_available` (`:41-60`) gains a branch — for this provider "runnable" means **`shutil.which("opencode") is not None`**, plus whatever credential the operator's config needs, which the adapter cannot introspect. Keep it best-effort and side-effect-free, as the docstring at `:42-51` requires (no process spawn at collection time).
  > ⚠ **Corrected as built (Session 214) — the `shutil.which` test alone was NOT implemented, deliberately.** It is unsafe: the binary is installed globally on any machine that ran Phase 1 and `addopts` carries no `-m 'not live'`, so a binary-only probe makes a bare `uv run pytest -q` *there* execute and bill four live cases while CI (no binary) still looks hermetic. The shipped probe requires the binary **and** `OPENCODE_EVAL_MODEL`; the same variable is the pinned model id, read by the new `provider_eval_model` and passed to the factory by both `test_eval_live.py` and `shadow_run.py` — which is also what makes D6's "every evaluated run must pass an explicit model" true rather than aspirational. Operator-chosen before implementation.
- `tests/eval/conftest.py:52-54` then skips the provider's live cases automatically when it is not runnable — CI stays hermetic with no change.
- The eight §3.4 thresholds are unchanged. **A cutover requires every one measured and met**; an unmeasured threshold resolves to PENDING and keeps `anthropic` primary — that rule is already encoded in `eval_cutover.evaluate_cutover` and must not be relaxed.

---

## 8. Failure-mode analysis

| Component | If it fails | Blast radius | Containment |
|---|---|---|---|
| `opencode` binary missing/wrong version | every call for this provider fails | one run, at construction | fail-fast in `__init__` with the install hint; version in error text (§4.5) |
| Event schema changes upstream | text extraction returns "" or garbage | every call | "no assistant text" error; fixtures committed from a known version; version recorded in the error |
| Model routes to a weak underlying vendor | JSON parses but content is subtly worse | **whole pipeline output** | **the eval gate — the reason it exists**; no cutover on unmeasured thresholds |
| Timeout too low for a 16k-token draft | mid-interview failure | one call; the intake checkpoint allows resume | 600s default, constructor-tunable; Phase 1 measures real latency |
| Sandbox temp dir not cleaned | disk growth | host | own the `TemporaryDirectory` on the instance; document that a long-lived process should hold one client, not one per call |
| Operator sets `--auto` out of band | agent gains tool permissions | host filesystem | the adapter never passes it; the negative test pins that; the agent definition denies the tools independently |
| Credentials in `~/.local/share/opencode/auth.json` | a second at-rest credential store | host | operator checklist item in the wiki (§9 Phase 3 doc work) |

---

## 9. Phases

**Each phase is one session with its own close-out. Do not bundle (FM #18).**

> ⚠ **Here be dragons: Phase 1 and Phase 4.** Phase 2 is mechanical once Phase 1's facts are in hand. Phase 1 is where the unverified claims get settled — if it finds that agent prompts *append* rather than replace, or that `--agent` behaves differently on a top-level `run`, D2 and D4 need revisiting **before** any client is written. Phase 4 is the quality judgement.

### Phase 1 — Live verification spike (no production code) — ✅ **DONE (Session 212, 2026-08-01)**

**Outcome:** all seven probes run against v1.18.11; four `[unverified]` markers resolved; six fixtures committed to `tests/fixtures/opencode/`; findings in **Appendix A**; **seven corrections to this spec recorded (A.4), one a safety defect (C1)**. Spend: $0.1295 over 16 billed calls. What Phase 1 deliberately did *not* settle is listed in A.5 — chiefly that the eval gate remains entirely undischarged.

**Work.** Install `opencode`, run the probe set below in a scratch directory, and commit the captured outputs as test fixtures plus a short findings note. Settle every **[unverified]** marker in §3.

Probe set (run each with the prompt on stdin, `--dir` a temp dir):

1. `opencode --version` — record it.
2. `opencode run --format json` with a trivial prompt (`Reply with the JSON object {"ok": true} and nothing else.`) — capture raw stdout **verbatim**; confirm the envelope `{type,timestamp,sessionID,...}`, the `text` event, and exit 0.
3. The same with a deliberately failing model id — confirm exit 1 and the `error` event payload.
4. A prompt that would normally make a coding agent reach for tools (e.g. "list the files here") **without** `--auto` — confirm the permission auto-reject path and that the run still terminates.
5. The same prompt with the locked-down agent definition in `<dir>/.opencode/agents/` and `--agent <name>` — confirm the agent is found, and inspect whether the built-in coding-agent framing is still present in the answer (the replace-vs-append question).
6. A realistic-size prompt (paste an actual `SYSTEM_INTERVIEWER` + a 10-pair transcript) — confirm stdin handles it and record wall-clock latency and per-call process overhead.
7. `opencode models | head` — record the exact id string for at least one Anthropic model and one non-Anthropic model, for §11 and for the eval's pinned model.

**DONE looks like:** committed JSONL fixtures under `tests/` (or a fixtures dir the Phase 2 tests will import), a findings note appended to this document as **§13 Appendix A**, and every `[unverified]` marker in §3 resolved to a verified statement or an explicit "still unknown, here is the consequence".
**Verification:** the captured stdout is real terminal output, pasted verbatim, not reconstructed. Version and date recorded.
**Session boundary:** one session. Close out. **No client code.**

### Phase 2 — Both clients, both factory branches, the registry entry, the deterministic tier — ✅ **DONE (Session 213, 2026-08-01)**

**Outcome:** shipped as specified, with the seven Appendix A corrections applied and **two as-built deviations** (both recorded in place below): §4.4/§5.1's `agent=` escape hatch was **removed**, not merely hard-gated — replaced by `agent_name: str`, which renames the generated tool-denying definition rather than substituting a caller-owned one, so no constructor path reaches an unlocked agent; and §5.3's helpers take the already-parsed event list rather than raw `stdout`, so the skip-unparseable-lines rule lives in one place. +111 tests (43 intake, 42 data agent, the rest factory/registry/parity). Every verification command below was run and passed. One assumption of the executor's own was disproven by its own test and is documented rather than dropped — see the `CHANGELOG.md` entry's "wrong assumption" bullet.

**Work.** Everything in §5, §6.1-6.2, §7.1-7.3. Both packages in **one** session — precedent: Session 162 shipped both Bedrock clients together, and the §7.2 twin guard is only writable once both copies exist.
**DONE looks like:** `make_llm_client("opencode")` constructs in both packages; `KNOWN_PROVIDERS` auto-includes it; the deterministic tier is green with no process spawned; the `_SEAMS` rows and the new helper-parity battery are in; C4 and the lazy-import invariants are green.
**Pre-flight:** Phase 1 merged. Re-run every §6 search. `rg '"openai"' tests/`. Read both `anthropic_client.py` and both `bedrock_client.py` as the structural template.
**Verification:**
- `uv run pytest -q` → no regression against the 989/8-skipped baseline, plus the new tests.
- `uv run mypy` → 0 errors. `uv run ruff check src/ tests/ packages/ scripts/` → clean.
- `uv run pytest tests/test_data_agent_decoupling.py --no-cov` → green.
- `uv run pytest tests/test_llm_json_parity.py --no-cov` → green.
- `python -c "import model_project_constructor_data_agent.factory"` imports no SDK.
- `rg -n "subprocess" packages/data-agent/src/` → only the new client.
- **Earns a `CHANGELOG.md` entry** (shipped code, `docs/methodology/PROJECT_CONVENTIONS.md` §2).

**Session boundary:** one session. Close out. **No eval wiring, no docs sweep.**

### Phase 3 — Eval wiring + documentation — ✅ **DONE (Session 214, 2026-08-01)**

**Outcome:** shipped, with **one deliberate deviation from §7.4** and a wider doc sweep than the list below named.

*The deviation (operator-chosen before any code was written).* §7.4 specified that "runnable" for this provider means `shutil.which("opencode") is not None`. **That test alone is unsafe and was not implemented.** The binary is installed globally on any machine that ran Phase 1, and `pyproject.toml`'s `addopts` carries no `-m 'not live'` — so a binary-only probe would have made a bare `uv run pytest -q` on this machine *execute and bill* four live cases (the convergence sweep alone is hundreds of model calls), while CI, which has no binary, still looked hermetic. `provider_creds_available("opencode")` therefore requires the binary **and** `OPENCODE_EVAL_MODEL`. The same variable is the pinned model id: `provider_eval_model` (new) reads it and both `test_eval_live.py` and `shadow_run.py` pass it to the factory, so opting in and pinning a model are one gesture. This also satisfies D6's standing requirement that *every evaluated run pass an explicit model* — which a binary-only gate would have left unmet — and discharges Phase 4's "the operator names the model to pin" pre-flight with one variable. The SDK providers receive `None` and keep their native default ids.

*The doc sweep was wider than the four surfaces listed below.* Shipping a third provider falsified present-tense claims on eight more wiki pages ("Two providers are implemented", `Literal["anthropic", "bedrock"]`, the `INTAKE_LLM_PROVIDER` value list, the credential-surface summary, the live-tier description, the `IntakeLLMClient` glossary entry). All were corrected. Two additions the phase list did not anticipate but a reader needs: a new **§6.9** in `AI-Dependencies.md` for the risks specific to having a *subprocess agent* in the call path (prompt-role demotion, filesystem reach, schema instability), and a **non-Python-dependency** subsection in the SBOM, since the `opencode` binary is a real supply-chain dependency that `uv.lock` does not pin and a Python-tree vulnerability scan will not see. `Evolution.md` was deliberately **not** touched (its convention is a user-requested full rewrite, not incremental edits) and neither was the wiki `Changelog.md` (episodic/curated cadence).

**Verification:** 1110 passed + 12 live-skipped @ 97.79% (from 1100 + 8 @ 97.79%); `-m 'not live'` green; `-m live` collects 12 and skips all 12 **on a machine where the binary is present**, and the probe flips to runnable once the model variable is set; mypy clean (68 files); ruff clean; the wiki no-line-citation guard green.

**Work.** §7.4. Then the doc surfaces: flip `AI-Dependencies.md` §9 from "planned" to as-built (and update §6.7's residual paragraph — this is the diversification it forecast), add an as-built note under `Architecture-Decisions.md` AD-11, extend `Extending-the-Pipeline.md`'s provider recipe with the subprocess-client variant, and add the operator-checklist items (§8: binary version pinning, `auth.json` at-rest credentials, session-state accumulation).
**DONE looks like:** `pytest -m 'not live'` green offline; the live tier auto-skips `opencode` when the binary is absent; the wiki pages describe a shipped provider; `PHASE_E_AGREEMENT_REPORT.md` lists `opencode` with all thresholds PENDING.
**Session boundary:** one session. Close out.

### Phase 3b — Eval-harness transport gap (Session 215, 2026-08-01) — ✅ **DONE**

**Not in the original phase list.** Phase 4's pre-flight below listed the binary, the credentials and the pinned
model — but never *"the eval harness can actually drive this provider."* Nobody had checked, because the live tier
skips, so no test could see it. Session 215 checked before spending, and it could not.

**The defect.** `tests/eval/stakeholder_sim.py` reached through to `intake_client._client.messages.create(...)`,
assuming every provider is SDK-backed. `OpenCodeLLMClient` sets `_client` to the `_UNUSED_SDK_CLIENT` placeholder
whose `__getattr__` raises (D5, and `test_opencode_client.py` pins it) — so the simulator died with a bare
`AttributeError`, which is **not** in `interview_sweep._TRANSIENT_ERRORS` and therefore **aborted the whole run**
instead of being retried. `measure_provider` orders governance → sql → interview, so Phase 4 would have **billed
~31 `opencode` calls and then crashed with no report**. Two of the eight gate keys (`interview_convergence`,
`interview_premature`) were unmeasurable for this provider.

**Second defect, same path.** `shadow_run.py` and `test_eval_live.py` both called `stakeholder_simulator_for(...)`
with **no `model=`**, so the *simulated stakeholder* half of every interview would have run unpinned — and for this
provider unpinned means no `--model` flag at all (D6's `DEFAULT_MODEL = None`) — while the interviewer half ran on
the pinned model. Two model tiers in one measured conversation, invisible in the report.

**The fix.** A provider-agnostic `TextCompleter` seam (`(system, user) -> str`), resolved per **transport shape**
rather than per provider name: the client's own `_run` for subprocess transports, a closure over `messages.create`
for SDK ones. A client with neither shape now raises `TypeError` at *construction* — deliberately not
`StakeholderSimError`, which the sweep would retry-then-exclude, converting an untaught-provider bug into a
silently empty result set. The pinned model is threaded to both halves at both call sites. **No production code
changed** — the `_UNUSED_SDK_CLIENT` guard that made this loud is untouched.

**Verification:** +11 tests, all hermetic (the end-to-end case drives the *real* client through the committed
`tests/fixtures/opencode/success_with_agent.jsonl` with a stubbed runner — no binary, no network, no spend). The
five pre-existing simulator tests pass **unmodified**, which is the evidence that SDK-provider behaviour is
unchanged and the recorded `anthropic` baseline stays valid. Gate: **1121 passed + 12 live-skipped @ 97.79%**,
mypy and ruff clean.

### Phase 4 — Live shadow run + cutover decision (operator-gated)

**Work.** Run the golden corpus against `opencode` with an explicitly pinned model, side by side with the `anthropic` baseline; fill the §3.4 thresholds; produce the go/no-go.
**Pre-flight:** Phases 1-3 merged; **Phase 3b merged** (without it the run aborts mid-way, after billing); the binary installed; credentials for whichever underlying vendor is being measured; **the operator names the model to pin**.
> **§11 Q2 answered by the operator (2026-08-01): measure an *Anthropic* model through `opencode` first** — it holds the model constant so the A/B against the recorded baseline actually isolates the transport change, which is what tests risk #1 (quality degrading under the D2 prompt-role fold). The non-Anthropic run that delivers `AI-Dependencies.md` §6.7's model-family diversification follows once the adapter itself is cleared.
> **Before spending, re-run the cheap pre-flight Session 215 wishes had existed:** build the simulator for the provider and resolve its completer (no process spawn, no cost). If that raises, the sweep will abort mid-run.
**DONE looks like:** every threshold has a measured number and a verdict; the recommendation follows the numbers. **No cutover on an unmet or unmeasured threshold.**
**Session boundary:** one session. Close out. Flipping any production default is a separate, operator-gated action.

---

## 10. Here be dragons

1. **Prompt-role change (D2).** System instructions delivered as user text, inside OpenCode's own agent framing. This is the difference between "the adapter runs" and "the adapter is usable". **Phase 1 resolved the open question and the answer is in between (Appendix A.1 #2): a custom agent's prompt *partially* replaces the built-in one — ~4,720 tokens of persona go, a constant ~4,830-token scaffold stays and cannot be removed.** So this project's prompts are never the only instruction the model sees. Mitigating evidence: the real `next_question` payload ran three times under the fold and produced on-domain, schema-valid output that parses with the project's own `_extract_json` (A.3). **That is a smoke test, not a quality measurement** — one method, one model, three runs. The eval remains the only thing standing between a plausible-looking adapter and quietly degraded intake reports.
2. **Schema stability.** The JSON event shape is an implementation detail of a project shipping releases daily. It is pinned here by source at a known commit and will be pinned by fixtures at a known version — but it is not a contract. Expect to re-verify.
3. **The agentic loop.** Everything else in this project calls a completion API. This calls an *agent*, which may take steps, call tools, and decide to do something other than answer. The tool denial and the "no text events ⇒ error" rule are the guards; neither is a proof.
4. **Silent quality regression is the actual risk, not breakage.** Breakage is loud and cheap. A provider that parses perfectly and mis-tiers governance risk is the failure this whole apparatus exists to catch — see the prior plan's §3.4 and risk #1.

---

## 11. Open questions for the operator

1. **`DEFAULT_MODEL = None`, or pin a verified id?** (§4.6.) `None` maximises portability and defers to the operator's own OpenCode config; a pinned id maximises reproducibility. The spec recommends `None` **plus** a mandatory explicit model for every evaluated run. This is a reversible one-line decision either way.
2. **Which underlying vendor should the first measured run target?** Choosing a non-Anthropic model is the only way this adapter delivers the *model-family* diversification `AI-Dependencies.md` §6.7 says is still missing; choosing Anthropic isolates the transport change from the model change and makes the eval a cleaner A/B. The spec has no preference — it is a measurement-design call.
   > ✅ **RESOLVED (operator, 2026-08-01): Anthropic first.** Holding the model constant is what makes the first run a test of *the adapter* — risk #1 is that the D2 prompt-role fold degrades quality, and a simultaneous model-family change would confound it beyond diagnosis. The non-Anthropic run that discharges §6.7 is a **second** measurement, once the transport is cleared. Q1 (`DEFAULT_MODEL = None`) stays open and is unaffected.
3. **How does `opencode` get installed in the enterprise environment?** Internal npm mirror, vendored binary, or container base image. This connects directly to `docs/planning/enterprise-migration.md` Phase C3 and to the `CIHostConfig` work from Session 205.
   **⚠ Sharpened by Phase 1 (Appendix A.4 C6): this is no longer only a packaging question.** OpenCode installs `.opencode/node_modules` into the sandbox at *runtime* whenever an agent definition is present, so it needs **npm-registry reachability from wherever the pipeline runs** — not just at image-build time. An air-gapped runtime would need the sandbox pre-seeded or the registry mirrored.
4. **Is the credential store at `~/.local/share/opencode/auth.json` acceptable at-rest?** A second on-disk credential location beyond the AWS/Anthropic paths already reviewed.
   **⚠ Largely defused by Phase 1:** passing the credential through the **child environment** works and writes **no** `auth.json` (verified by absence). The adapter should therefore never invoke `opencode auth login`, and this question narrows to "does any *operator* workflow need it?" **Note a separate at-rest fact did surface (A.4 C7): session content — i.e. prompt and response text, which may contain claim data — persists in a global SQLite database at `~/.local/share/opencode/opencode.db`, and it survives deletion of the sandbox.** That is the at-rest question worth the operator's attention now.

---

## 12. Risk register

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | Adapter parses fine but output quality degrades (D2 prompt-role change) | **High** | The eval gate; no cutover on unmeasured thresholds |
| 2 | OpenCode event schema changes between versions | **Medium-High** | Fixtures captured from a pinned version; version recorded in error text; Phase 1 re-fetch before trusting §3 |
| 3 | The `_extract_assistant_text` twins drift (the `_extract_json` story repeating) | Medium | §7.2 parity battery, written the same session as the twins |
| 4 | Subprocess hangs forever on inherited stdin (H1) | Medium if unguarded | Never inherit stdin; hard timeout; explicit test |
| 5 | Prompt content leaks via `ps` (H2) | Medium if unguarded | Prompt on stdin; explicit test asserting it is not in argv |
| 6 | The agent touches the host repo (H3/H4) | ⚠ **RAISED to High by Phase 1** — reads succeed by default (Appendix A.4 C1); only the sandbox and the tool-denying agent stand in the way | Ephemeral `--dir`; tool-denying agent **with `read: deny`, now mandatory not optional**; never `--auto`; explicit negative test asserting a read request is refused |
| 7 | `LLM_PROVIDERS` / `LLMProvider` lockstep broken (no parity test exists — C4) | Medium | Three named edits in one session, listed in §6.2; call it out in the commit message |
| 8 | Binary absent in a deployment that selected the provider | Medium | Fail fast at construction with an install hint |
| 9 | Session state accumulates on disk (H5) | Low | **Measured (A.4 C7): a global SQLite DB, 576 KB + WAL after ~20 runs — not files, not in the sandbox, and it survives sandbox deletion.** Operator checklist item; note it holds prompt/response text. |
| 10 | **New (A.4 C6): the sandbox needs a runtime npm install** — `.opencode/node_modules` is materialised whenever an agent file is present (~1 MB, 62 MB observed) | Medium | Create the sandbox **once per client instance**, never per call; treat npm reachability as a deployment prerequisite (§11 Q3) |
| 11 | **New (A.4 C5): the adapter's own generated agent file is malformed** → usage help on stderr, empty stdout, non-zero exit | Medium | Emit **block-style** YAML (flow-style breaks it); diagnose "non-zero exit + zero stdout lines" distinctly; cover with a test |
| 12 | **New (A.2): per-call token overhead** — ~4,830 scaffold tokens survive even with a custom agent, ~120 k extra input tokens per 25-call interview, invisible to quality thresholds | Medium-High on expensive models | Phase 4 must report **cost per interview** alongside quality, not quality alone |

---

## 13. Provenance

- **Decision being implemented:** `docs/wiki/claims-model-starter/Architecture-Decisions.md` AD-11; research in `AI-Dependencies.md` §9 (both Session 210, 2026-08-01).
- **Seam design intent:** the factory docstrings at `agents/intake/factory.py:1-19` and `packages/data-agent/.../factory.py:1-20`; the provider recipe in `docs/wiki/claims-model-starter/Extending-the-Pipeline.md` §"Files to add or edit".
- **Structural template:** `docs/architecture-history/multi-provider-llm-plan.md` (Sessions 159-164) — its Decisions A/C/D, Traps 1-5, and §3.4 threshold table are carried forward here rather than restated.
- **Code evidence:** every file and line number in §2 and §6 was read or searched during Session 211 at `a3f33d8`.
- **External evidence:** `anomalyco/opencode` — `packages/opencode/src/cli/cmd/run.ts` fetched via the GitHub API (default branch `dev` @ `32f278b48f1a`, 2026-08-01; the file itself last modified in `20445ca03133`, 2026-06-30); release `v1.18.11` (2026-08-01); MIT. Docs pages `opencode.ai/docs/cli/`, `/docs/agents/`, `/docs/providers/`, `/docs/`. Issue `anomalyco/opencode#9320` for the schema-constrained-output status. **No claim in §3 comes from training-data memory** — this tooling post-dates and out-paces it.
- **What this spec did NOT do:** run `opencode`. The binary is not installed on this machine (`which opencode` → not found), and a live invocation costs provider tokens and an install decision that belongs to the operator. The schema question §9.2 raised is answered from source, which is stronger for that question; everything a live run answers *better* is Phase 1's explicit job and is marked `[unverified]` above rather than assumed.

---

## Appendix A — Phase 1 live-verification findings (Session 212, 2026-08-01)

**Status: Phase 1 COMPLETE.** `opencode` **v1.18.11** installed via `npm i -g opencode-ai`. All seven probes in §9
Phase 1 ran against `anthropic/claude-haiku-4-5`, prompt on stdin, `--dir` an ephemeral temp dir, never `--auto`.
Credential supplied through the child environment only — **no `opencode auth login`, and no `~/.local/share/opencode/auth.json` was created** (verified by absence after the runs), so §11 Q4's second at-rest credential store was avoided entirely rather than accepted.

**Cost of the whole spike: $0.1295 across 16 billed model calls.** Fixtures: `tests/fixtures/opencode/` (verbatim
captures + a provenance README).

**Upstream drift check, run first per Session 211's handoff:** none. At capture time the repo was still default
branch `dev` @ `32f278b48f1a`, `run.ts` still last modified `20445ca03133`, release still v1.18.11 — identical to
the spec's pins. **Every [source-verified] claim in §3 held.** The flag table in §3.1 was additionally re-confirmed
against `opencode run --help` on the installed binary, including the load-bearing absence: **there is no
`--system` flag.**

### A.1 The four `[unverified]` markers — all resolved

| # | Question (§) | Resolution | Evidence |
|---|---|---|---|
| 1 | Is `ANTHROPIC_API_KEY` honoured? (§3.4) | **YES.** The docs page that omitted it was simply incomplete. | `opencode models` returns **7** ids (all `opencode/*`) with no credential, and **24** ids incl. **17 `anthropic/*`** with the env var set. The model list is credential-gated, which made this free to test. |
| 2 | Does a custom agent's prompt **replace** or **append to** the built-in coding-agent prompt? (§3.4, dragon 1) | **PARTIAL REPLACE — quantified.** The custom prompt replaces ~4,720 tokens of built-in *persona*, but a **constant ~4,830-token scaffold survives** and is not removable via the agent file. | No agent: `cache.write` **9,552**. Custom agent (short prompt): **4,832**. Custom agent with ~2,000 extra prompt tokens: **6,836** — a delta of 2,004, exactly the added text. So base is constant and the custom prompt adds linearly on top. `--pure` does **not** reduce it (9,539). |
| 3 | Which frontmatter keys are accepted; is `mode: primary` required? (§4.4) | **Partially resolved.** Accepted, block-style: `description`, `mode: primary`, and `permission:` with `edit`/`write`/`bash`/`read`/`webfetch`. Agent id = file basename. `.opencode/agents/` (plural) alone is sufficient. **Still unknown: whether `mode: primary` is strictly required** — every successful run set it, so this was never isolated. *Consequence: harmless — Phase 2 should keep setting it.* | Probes 5, 5b, 5c and a controlled cold-sandbox run. |
| 4 | Per-call process overhead (§4.3) | **~0.77 s**, very stable (0.77 / 0.77 / 0.76 over three runs with no model call). | Timed runs against an invalid model id, which creates a session but bills nothing. |

### A.2 Measured behaviour

- **Latency.** Trivial prompt 2.13–2.28 s. Realistic `next_question` payload (`SYSTEM_INTERVIEWER` + 10-pair
  transcript, 4,655 bytes) **3.20 / 3.28 / 4.41 s** over three runs. Cold sandbox costs ~1.5 s extra on first use.
- **Startup floor ~0.77 s** ⇒ roughly **24 % overhead** on a 3.2 s call, or **~19 s per 25-call interview**. This is
  the number §4.3 said to measure before revisiting `opencode serve`; it is real but not alarming.
- **Token overhead is the more significant cost.** Even with the locked-down agent, every call carries ~4,830
  tokens of OpenCode scaffold — **~120 k extra input tokens per 25-call interview**. On Haiku this is fractions of a
  cent per call ($0.0061–0.0081 measured); **on an Opus-class model it becomes material**, and it is invisible to
  the existing eval's quality thresholds. Phase 4 must report cost per interview alongside quality.

### A.3 D2 validated end-to-end — the spec's largest risk is materially reduced

The real `next_question` payload was folded exactly as D2 prescribes (`system + "\n\n" + user`) and run three times.
All three: exit 0, `reason: "stop"`, correctly fenced JSON, and — the decisive check — **all three parse with the
project's own unmodified `_extract_json`**, yielding exactly `{question, believe_enough_info}`. The generated
questions were on-domain and followed `SYSTEM_INTERVIEWER`'s specific instructions (probing the value-measurement
plan and concrete data sources), i.e. **the system prompt is being honoured despite arriving as user text.**

This does **not** discharge the eval gate — three runs on one method with one model is a smoke test, not a quality
measurement, and dragon 4 (silent quality regression) is untouched. But D1 and D2 are now demonstrated rather than
merely argued.

### A.4 Corrections to this specification — read before Phase 2

Seven things the spec got wrong or did not know. **C1 is a safety defect.**

- **C1 — §3.5 H4 is WRONG. "The default is already safe" is false.** Without `--auto`, the agent successfully
  listed the sandbox, **read a file, and disclosed its contents**, exiting 0 (`multistep_tool_use.jsonl`; reproduced
  with no agent in a second probe). Permission auto-reject does **not** cover the `read` tool. **Consequence: the
  tool-denying agent definition is MANDATORY, not optional** — §4.4's "unless the caller supplied an `agent=` name,
  in which case the adapter writes nothing" is an unsafe escape hatch and must be removed or hard-gated. The
  ephemeral `--dir` is the only other barrier between this adapter and the host repository, including `.env`.
  **The mitigation is verified to work:** with `read: deny`, the same request produced zero `tool_use` events and an
  explicit refusal.
- **C2 — §4.7's error message shape is unusable as written.** It prescribes `{stderr_tail}`; **stderr is empty** on
  the error path. Every diagnostic arrives on *stdout* as an `error` event. Build the message from
  `error.name`, `error.data.message`, and `error.data.ref` instead. (Observed payload is generic —
  `"Unexpected server error"` + a `ref` id — so include the `ref`, it is the only distinguishing detail.)
- **C3 — `step_finish` carries more than §3.2 records**, and it repairs a gap §3.3 declared unfixable. The part
  includes `reason` (`"stop"` / `"tool-calls"`), `tokens{input,output,total,cache{write,read}}`, and `cost`. §3.3
  says `max_tokens` is inert with "no analogue" for the inherited truncation guard — **`reason` is that analogue**,
  and `tokens`/`cost` give per-call telemetry the SDK clients do not expose. Phase 2 should surface both.
- **C4 — §3.2's extraction rule is unsafe when tools fire.** "Concatenate every `text` event" is correct for
  single-step runs but on a 3-step agentic run produced narration + answer:
  `"I'll list the files…" + "Now let me read…" + "<the actual answer>"`. Prefer the text of the **final step**
  (the one whose `step_finish.reason == "stop"`), and rely on tool denial to keep runs single-step.
- **C5 — A malformed agent definition fails in a shape nothing in the spec anticipates:** OpenCode prints its
  **usage help to stderr, emits nothing on stdout, and exits non-zero**. It is not an `error` event. **Flow-style
  YAML** (`permission: {edit: deny, …}`) triggers this; block-style works. Since the adapter *generates* this file,
  Phase 2 must emit block-style YAML and treat "non-zero exit with zero stdout lines" as its own diagnosed error.
- **C6 — Writing the agent definition into the sandbox is not free.** A virgin `--dir` stays **0 bytes**, but once
  `.opencode/agents/*.md` is present OpenCode materialises `.opencode/node_modules` and a `.gitignore` (**~1 MB** in
  a controlled cold run; one longer-lived sandbox reached **62 MB** with a `package.json` pinning
  `@opencode-ai/plugin`). **This implies npm-registry reachability at runtime** — which turns §11 Q3 (enterprise
  install path) from a packaging question into a runtime-network question. **Create the sandbox once per client
  instance and reuse it; never per call.**
- **C7 — H5 answered: sessions are not files.** They live in a global SQLite database
  (`~/.local/share/opencode/opencode.db`, 576 KB + WAL after ~20 runs), not as JSON, and not in the sandbox. Growth
  is modest but unbounded and **survives sandbox deletion** — so an operator-facing cleanup note is still warranted.

### A.5 What Phase 1 did NOT settle

- Whether `mode: primary` is strictly required (A.1 #3) — never isolated; keep setting it.
- Quality under D2 at scale: three runs, one method (`next_question`), one model. `draft_report` and the governance
  path were not exercised. **The eval gate stands entirely undischarged.**
- Non-Anthropic providers were not exercised at all — the whole portability premise (§11 Q2) is still unmeasured.
- Whether a `length`-style `reason` value appears on truncation (C3 infers the mechanism; no truncation was forced).
- Timeout behaviour under a genuinely slow model, and the concurrency story if interviews ever run in parallel.

---

*End of specification.*
