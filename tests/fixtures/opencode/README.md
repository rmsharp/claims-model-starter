# OpenCode `--format json` fixtures

**These are verbatim captures of real `opencode run` stdout.** They were not written by hand and
must not be edited by hand. Phase 2's deterministic tests parse these instead of spawning a process,
so a test that passes against a hand-written fixture would be testing the spec rather than OpenCode.

## Provenance

| Field | Value |
|---|---|
| Captured | 2026-08-01 (Session 212, spec Phase 1) |
| Binary | `opencode` **v1.18.11**, installed via `npm i -g opencode-ai` |
| Upstream source pin | `anomalyco/opencode`, default branch `dev` @ `32f278b48f1a`; `run.ts` last modified `20445ca03133` |
| Model | `anthropic/claude-haiku-4-5` |
| Credential path | `ANTHROPIC_API_KEY` via the child environment only — no `opencode auth login`, no `auth.json` written |
| Invocation | prompt on **stdin**, `--format json`, `--dir <ephemeral temp dir>`, **never** `--auto` |
| Spec | `docs/planning/opencode-adapter-spec.md` — findings in its §13 Appendix A |

## Files

| File | What it captures | Why Phase 2 needs it |
|---|---|---|
| `success_single_step.jsonl` | Trivial prompt, **no** custom agent. `step_start` / `text` / `step_finish`. | The canonical happy path. Note `cache.write: 9552` — OpenCode's built-in framing. |
| `success_with_agent.jsonl` | Same prompt **with** the locked-down agent definition. | Happy path under the configuration the adapter actually ships. `cache.write` drops to 4837. |
| `success_realistic_intake.jsonl` | The real `next_question` payload (`SYSTEM_INTERVIEWER` + a 10-pair transcript) folded per decision D2. | Proves the fold produces schema-valid output. This text parses with the project's own unmodified `_extract_json`. |
| `error_invalid_model.jsonl` | An invalid `--model` id. Single `error` event, exit 1. | The error path. **stderr was empty** — all diagnostics arrive here on stdout. |
| `multistep_tool_use.jsonl` | An agentic multi-step run: 3 steps, 3 `text` events, 2 `tool_use` events. | The interleaved-narration case. Naive concatenation of all `text` events yields narration + answer, not the answer. |
| `usage_error_nonjson_stdout.txt` | ANSI-coloured `Error: You must provide a message...` printed to **stdout**, exit 1. | Proves non-JSON lines reach stdout, so the parser must skip unparseable lines rather than fail on them. |

## Cautions

- `sessionID` values are real but inert — sessions live in a local SQLite database
  (`~/.local/share/opencode/opencode.db`), not in these files, and not in the sandbox.
- These fixtures pin **v1.18.11**. OpenCode ships releases daily and its event shape is an
  implementation detail, not a stability contract. If a Phase 2 test fails after an upgrade, suspect
  the schema before suspecting the test — and re-capture rather than editing.
- Verified free of credential material at capture time.
