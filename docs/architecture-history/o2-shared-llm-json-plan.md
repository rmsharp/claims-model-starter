> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/model_project_constructor/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# O2 — Shared `llm_json` Helper: Drift-Guard Plan

> **Status:** Draft for executor review (Session 102 of project, planning/architecture workstream).
> **Author:** Session 102 — 2026-06-03.
> **Implements:** Technical-debt audit `docs/audits/2026-06-01-technical-debt-audit.md` §5 / §8 item **O2** (audit finding #31, #16). Standing handoff option #1.
> **Predecessor:** Quick-win **#16/#16b/#16c** (Sessions 98/99/100) — the prerequisite the audit named ("do O2 *after* #16 so the bug is gone first"). All three twin-hardening fixes are landed; the twins are now guard-identical.
> **Decision (resolved with operator, Session 102):** **Option C — behavioral-parity test, no merge.** Do **not** consolidate the two clients into a shared module. Instead, pin their behavioral parity with a test that fails CI on drift. Rationale in §3–§4.
> **Out of scope:** any consolidation into a shared module/package (Options A/B — analysed and rejected in §4, preserved for a future architect); any change to the two clients' production code; any change to the error contract. See §10.

---

## 1. Context

### 1.1 What "O2" is

The Session-97 technical-debt audit (`docs/audits/2026-06-01-technical-debt-audit.md:84-86,173`) found that the two Anthropic LLM clients —

- intake: `src/model_project_constructor/agents/intake/anthropic_client.py`
- data-agent: `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`

— independently reimplement **four** concerns: (1) client construction (`anthropic.Anthropic()` + `_model`/`_max_tokens`), (2) the single Claude round-trip (`messages.create(...)`), (3) a `_CODE_FENCE` regex + `_extract_json` parser, and (4) a per-method content/parse guard. The audit logged a quick-win (#16: port the hardened parser into the stale intake copy) and an overhaul (**O2**: "extract a provider-neutral `llm_json` helper, mindful that the data-agent ships as a standalone wheel — put the shared helper inside the data-agent package, or carve a third tiny shared package").

Quick-win #16 and its two siblings #16b/#16c are **done** (Sessions 98/99/100): the two copies are now byte-identical modulo the raised error class (see §2.1). O2 is the remaining question: *should we consolidate the now-identical twins, and if so, where?*

### 1.2 Why this is an architecture decision, not a quick win

The data-agent is a **separately installable, deliberately decoupled** package. Constraint **C4** (`docs/architecture-history/architecture-plan.md:36`, sourced from `initial_purpose.txt:84-87`) requires it be "**reusable as a standalone query tool** for analysts." The plan makes the decoupling physical (`architecture-plan.md:532`): *"the standalone package cannot import from the orchestrator,"* enforced by `tests/test_data_agent_decoupling.py` — described as *"the single most important structural guarantee"* (`architecture-plan.md:1078`) and run in CI.

The package dependency is **one-way**: the root `model-project-constructor` package **depends on** `model-project-constructor-data-agent` (`pyproject.toml:14`); the data-agent depends on neither it nor the orchestrator (`packages/data-agent/pyproject.toml:11-18`). Therefore a shared helper **cannot** live in `src/model_project_constructor/` and be imported by the data-agent — that would invert the dependency (circular) and break C4. This is what makes O2 an architecture decision rather than a mechanical extract-method.

### 1.3 The reframe — O2's value is drift-prevention, not LoC

The duplicated surface is small: `_extract_json` is **14 lines of body** (plus a 1-line regex), differing across the two copies by **exactly one line** (the `raise` class). A consolidation removes ~50 lines net. That is not, by itself, a compelling return.

The *real* harm of the duplication is **drift**: the two copies already diverged once. The intake copy was a **stale pre-hardening version** whose anchored `^…$` regex crashed on prose-wrapped fences — a live-LLM crash tracked from Session 51 (`run_id=run_b1_resume_live_1776570556`), fixed in the data-agent first and only ported to intake in Session 98 (#16), with the empty-content and non-`TextBlock` guards following in #16b/#16c. **Three sessions of latent-bug remediation** trace to these twins drifting.

This reframes the decision: the objective is **make it impossible for the twins to silently drift again**, at the lowest cost and without eroding C4. A behavioral-parity test buys exactly that — for near-zero cost and **zero new coupling** — which is why it is the chosen path (§3). Consolidation (Options A/B) also prevents drift but pays a coupling/packaging cost the drift-prevention benefit does not require.

---

## 2. Evidence Inventory (grep-based — MANDATORY for a refactor plan)

All counts below were produced by direct `grep`/`diff`/read against the working tree at Session 102 (HEAD `e4bf6f5`), and cross-checked against a 4-reader research workflow. Where the two disagreed, the direct command wins (one subagent count was corrected — see the note on test counts).

### 2.1 The duplication surface (`_extract_json` + `_CODE_FENCE`)

| Item | intake | data-agent |
|------|--------|------------|
| `_CODE_FENCE` regex | `anthropic_client.py:319` | `anthropic_client.py:462` |
| `_extract_json` def + docstring + body | `:322-353` (body 340-353) | `:465-494` (body 480-494) |
| Raised error class | `IntakeLLMError` (`:351`) | `LLMParseError` (`:492`) |
| Direct `_extract_json` unit tests | **9** (`tests/agents/intake/test_anthropic_client.py:292-347`) | **9** (`tests/data_agent_package/test_anthropic_client.py:281-323`) |
| `_extract_json` call sites | 1 (`:262`, inside `_call_json`) | 6 (`:147,186,226,256,297,342`) |

**Verified byte-identity:** a normalized `diff` of the two function bodies (docstrings stripped) yields **a single hunk**:

```diff
-        raise IntakeLLMError(
+        raise LLMParseError(
```

The `_CODE_FENCE` regex line is identical (`re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)`). The docstrings differ in narrative only (intake cites "ported from the data agent in Session 98"; data-agent cites the Session-51 live run). **This one-line-modulo-error-class identity is the load-bearing premise of the parity test in §5.**

> Count correction (provenance hygiene): the research workflow's structured `count` field reported "8" direct `_extract_json` tests per package while listing 9 test names; direct `grep -c "def test_extract_json"` returns **9** in each suite. The plan uses 9. (Per the Session-101 candidate learning: cross-check subagent-extracted counts against the authoritative grep before they enter a permanent artifact.)

### 2.2 The guard / round-trip surface (`_call_json` vs `_call_claude`)

| Item | intake `_call_json` | data-agent `_call_claude` |
|------|---------------------|---------------------------|
| Definition | `:240-262` | `:356-370` |
| Return shape | **parsed JSON** (`-> Any`; calls `_extract_json` internally, `:262`) | **raw text** (`-> str`; callers call `_extract_json` separately) |
| Empty-content guard | `:255-256` `IntakeLLMError("Claude returned an empty content list")` | `:363-364` `LLMParseError("Claude returned an empty content list")` |
| Non-`TextBlock` guard | `:258-261` `IntakeLLMError(f"expected TextBlock from Claude, got {…}")` | `:366-369` `LLMParseError(f"expected TextBlock from Claude, got {…}")` |
| Call sites | 4 (`:146,195,213,231`) | 6 (`:146,185,225,255,296,341`) |
| Guard tests | 2 (`test_call_json_rejects_non_text_block` `:243-265`, `…_empty_content` `:268-286`) | 2 (`test_call_claude_rejects_non_text_block` `:84-99`, `…_empty_content` `:102-117`) |

The two guards are identical modulo error class (same condition, same message). **Structural asymmetry:** intake fuses round-trip + guards + extract → *parsed*; data-agent does round-trip + guards → *raw*, each caller extracting separately. This asymmetry is the wrinkle that makes a *full* merge (audit concern 2+4) more invasive than the parser merge — relevant only to the rejected Option A/B (§4), not to the chosen Option C. Happy-path test fakes in **both** suites use real `anthropic.types.TextBlock`, so the guard tests are credible.

### 2.3 The error-contract blast radius

| Item | `IntakeLLMError` | `LLMParseError` |
|------|------------------|-----------------|
| Definition | `agents/intake/protocol.py:96` — `class IntakeLLMError(RuntimeError)` | `data-agent/anthropic_client.py:92` — `class LLMParseError(ValueError)` |
| Base class | **`RuntimeError`** | **`ValueError`** |
| Raise sites | 16 (incl. 6 in `fixture.py`, 1 in `nodes.py:269` — **not all LLM-parse**; it is a general intake error) | 9 (all in the data-agent client) |
| Explicit `except` sites | **0** | **0** |
| Implicit catch | `nodes.py:268` (`except Exception` → re-wraps as `IntakeLLMError`) | `agent.py:51-54` (`except Exception` → `status="EXECUTION_FAILED"`) |
| Tests asserting the type | **16** (`test_fixture.py` ×6, `test_anthropic_client.py` ×10) | **8** (`test_anthropic_client.py`) |

Two consequences for any design:

1. **Different bases (`RuntimeError` vs `ValueError`)** mean the two errors share no common ancestor below `Exception`. A shared helper cannot raise one unified type without changing one package's error contract — it must be **parametrized with the error class** (`error_cls`). (This confirms, with a sharper reason, the handoff's "inject an error factory" wrinkle.)
2. **24 tests pin the exact raised type**, and `IntakeLLMError` is reused broadly in intake beyond the LLM client (`fixture.py`). The error divergence is **intentional and load-bearing** — the chosen design preserves it untouched.

### 2.4 The placement-wiring surface (relevant only to rejected Option A)

A new `packages/llm-json/` workspace package (Option A) would require these **7 edits** to root `pyproject.toml`, plus a new package `pyproject.toml`:

| # | Location | Current (line) | Add |
|---|----------|----------------|-----|
| 1 | `[project].dependencies` | `:14` lists `model-project-constructor-data-agent` | `+ "model-project-constructor-llm-json"` |
| 2 | `[tool.uv.sources]` | `:53` | `+ model-project-constructor-llm-json = { workspace = true }` |
| 3 | `[tool.pytest.ini_options] pythonpath` | `:64` `["src", "packages/data-agent/src"]` | `+ "packages/llm-json/src"` |
| 4 | `[tool.pytest…] addopts --cov` | `:65` | `+ --cov=model_project_constructor_llm_json` |
| 5 | `[tool.coverage.run] source` | `:68` | `+ new src path` |
| 6 | `[tool.mypy] packages` | `:97` | `+ "model_project_constructor_llm_json"` |
| 7 | `[tool.mypy] mypy_path` | `:98` | `+ "packages/llm-json/src"` |

`[tool.uv.workspace] members = ["packages/*"]` (`:50`) already globs the new dir; CI ruff scans `packages/` (`.github/workflows/ci.yml:23`) so lint auto-covers; mypy/pytest run off the config edited above. The data-agent's own `pyproject.toml` would also gain the new dependency + source. **Net: ~9 config edits across 3 files + a new package skeleton + an `anthropic` dependency on the new package** — for a 14-line function. (This wiring cost is a major input to rejecting Option A; it is inventoried here so a future architect who revisits A/B does not re-derive it.)

---

## 3. Decision

**Adopt Option C: a behavioral-parity test that guards the two `_extract_json` copies (and their content guards) against drift. Do not merge.**

Rationale:

1. **It targets the actual harm.** The only concrete cost the duplication ever imposed is drift (§1.3). A parity test converts drift from a *latent live-LLM crash discovered three sessions later* into a *deterministic CI failure on the offending commit*. That is the entire benefit of consolidation, delivered directly.
2. **Zero erosion of C4.** No new cross-package import, no new package, no change to the data-agent's single-wheel standalone property. C4 is "the single most important structural guarantee"; Option C leaves it pristine.
3. **The shared module would be shallow.** Per the workstream's refactor heuristics (`ARCHITECTURE_WORKSTREAM.md:191-212`), a shared `extract_json(raw, *, error_cls)` has an interface about as complex as its 14-line implementation — a shallow module, which "imposes a cost without paying back in hidden complexity." The deletion test concurs: deleting a hypothetical shared module disperses only ~14 lines into two call sites — marginal abstraction.
4. **Avoids astronaut/resume-driven architecture** (`ARCHITECTURE_WORKSTREAM.md:226-227`): a new workspace package (9 config edits) for a 14-line function is disproportionate.
5. **Lowest blast radius of any option** — a single new test file, no production-code change, no error-contract change, no risk to the 24 type-asserting tests.

The error-class divergence (§2.3) is **preserved and asserted as intentional**: the parity test pins that each copy raises its *own* error type, not that they raise the same one.

---

## 4. Alternatives Considered

| Option | What it does | DRY | Coupling added | Blast radius | Verdict |
|--------|--------------|-----|----------------|--------------|---------|
| **C — Parity test (CHOSEN)** | Keep both copies; test pins behavioral parity, fails CI on drift | 0 LoC removed | **none** | 1 new test file | **Chosen** — buys drift-prevention at near-zero cost; respects C4 |
| **A — New shared micro-package** | `packages/llm-json/`; both packages depend on it | ~50 LoC | both pkgs → neutral util; data-agent wheel needs a 2nd pkg | ~9 config edits + new pkg + edit 7 `extract_json` sites (Full: 10 call sites) | Rejected — disproportionate wiring for 14 lines; shallow module; mild C4 erosion (data-agent no longer single-wheel) |
| **B — Helper inside data-agent** | `model_project_constructor_data_agent/llm_json.py`; intake imports it | ~50 LoC | intake → data-agent internals | edit 7 `extract_json` sites; intake docstring "share no methods" must change | Rejected — semantically backwards (intake reaching into the data agent); asymmetric; the audit's first-listed option but still pays coupling for marginal gain |
| **D — Do nothing** | Status quo | 0 | none | 0 | Rejected — leaves the drift risk that bit #16/#16b/#16c unguarded |

Notes:

- **A and B are the audit's two suggestions.** They are recorded here in full (with the §2.4 wiring inventory) so that **if the project later grows a third LLM-calling client** (e.g. the website agent, which today has **no** LLM surface), the consolidation case strengthens — three copies make a shared module *deep* — and a future architect can re-open A/B without redoing this analysis. **Re-open trigger: a 3rd `_extract_json` copy.**
- **Full-merge depth** (round-trip + guards + parser into one `call_and_parse(client, model, max_tokens, system, user, error_cls)`) was the recommended depth *if* A/B were chosen; it would edit all 10 `_call_*` call sites and unify the parsed-vs-raw asymmetry (§2.2). Not pursued under Option C.

---

## 5. Test Design (the deliverable's shape)

A single new file `tests/test_llm_json_parity.py` with three concerns. It imports the private `_extract_json` from **both** packages (legal in the test tree — `pyproject.toml:64` puts both `src` roots on `pythonpath`; this import does **not** run in either package's runtime, so it does not touch C4 / the decoupling test, which only walks the package source trees, not `tests/`).

**5.1 Parse parity (the core).** Run an identical input battery through both copies; assert equal results. The battery MUST include the historically-divergent case (prose-wrapped fence) so the exact Session-51 drift is covered:

```python
PARSE_CASES = [
    '{"a": 1}', '  {"a": 1}  ', '[1, 2, 3]',
    '```json\n{"a": 1}\n```', '```\n{"a": 1}\n```',
    'Here is the JSON:\n```json\n{"a": 1}\n```',          # prose-before (Session 51)
    '```json\n[{"k": "v"}]\n```\n\nExplanation: ...',     # prose-after
    'Response below:\n```json\n{"x": [1, 2]}\n```\nok',   # prose-both
    'Sure:\n```\n{"ok": true}\n```',                      # plain fence + prose
]
# assert intake_extract(raw) == da_extract(raw) for each
```

**5.2 Raise parity (pins the intentional divergence).** For malformed inputs, assert intake raises `IntakeLLMError` **and** data-agent raises `LLMParseError` — i.e. both reject, each with its *own* type:

```python
RAISE_CASES = ['this is not json', '```json\nnot valid json\n```', '']
# with pytest.raises(IntakeLLMError): intake_extract(raw)
# with pytest.raises(LLMParseError): da_extract(raw)
```

**5.3 Guard-message parity (covers audit concern 4).** Construct each client with a fake Anthropic client returning (a) empty `content=[]` and (b) a non-`TextBlock` first block; assert both clients' methods (`_call_json` / `_call_claude`) raise with the **same message text** modulo error class. Reuse the existing fakes' shape from `tests/agents/intake/test_anthropic_client.py:45-48` and `tests/data_agent_package/test_anthropic_client.py:49-52`.

**5.4 Recommended backstop — normalized source identity.** Optionally add one test that uses `inspect.getsource` on both `_extract_json`, strips the docstring, normalizes the two error-class names to a sentinel, and asserts the normalized sources are identical. This is strictly stronger than behavioral parity (it catches drift on inputs not in the battery) and directly encodes the §2.1 invariant. Recommended but not required; behavioral parity (5.1–5.3) is the must-have because it is robust to benign reformatting.

The file's module docstring must explain *why* the twins are separate (C4) and *why* the test exists (drift history #16), so a future reader does not "fix" the duplication by merging.

---

## 6. Implementation Plan

**This is a single-phase plan. One session implements it, then closes out. Do not bundle other backlog items (FM #18).**

### Phase 1 — Write `tests/test_llm_json_parity.py`

- **Work:** Create the test file per §5: parse parity (5.1), raise parity (5.2), guard-message parity (5.3); optionally the source-identity backstop (5.4). Module docstring per §5 closing note. No production code changes. No `pyproject.toml` changes (both `src` roots are already on `pythonpath`).
- **What DONE looks like:** a new test file with ≥3 parametrized parity tests, all green; both `_extract_json` copies exercised through one battery; the intentional error divergence asserted; the file documents the C4 + drift rationale.
- **Verification commands** (re-confirm exact line numbers first — Learning #28):
  - `.venv/bin/pytest tests/test_llm_json_parity.py -v` → all pass.
  - **Drift-detection proof (the test's whole point):** temporarily revert intake's `_extract_json` to the pre-hardening anchored regex (`git stash`-style local edit, or a throwaway one-char break to the regex) and re-run → the parse-parity test must **FAIL**. Restore. This proves the guard actually catches drift (analogue of the TDD "prove it RED" discipline — a parity test that can't fail on real divergence is worthless).
  - `.venv/bin/pytest -q` → full suite still green (expect 645 + N new).
  - `.venv/bin/ruff check tests/test_llm_json_parity.py` → clean.
  - `.venv/bin/mypy` (config-driven — `[tool.mypy] packages = [two modules]`; checks the **two packages only**, 61 source files. **`tests/` is NOT in the default scope**, verified Session 102.) → still 0 errors; CI's `mypy` will not type-check the new test file at all. *Optional:* `.venv/bin/mypy tests/test_llm_json_parity.py` to check it explicitly — importing the module-level private `_extract_json` from both packages is legal and should pass; document the access only if mypy objects.
  - `.venv/bin/pytest tests/test_data_agent_decoupling.py -v` → still green (this test walks package source, not `tests/`, so the new file cannot affect it — confirm, do not assume).
- **Session boundary:** This phase is one session. Close out when the file is green and the drift-detection proof is demonstrated. **STOP.**

---

## 7. Impact Analysis

| Surface | Impact | Action |
|---------|--------|--------|
| Production code (`src/`, `packages/`) | **None** | unchanged — explicit scope boundary |
| Error contract (`IntakeLLMError`/`LLMParseError`) | **None** | preserved; asserted intentional |
| Existing 24 type-asserting tests | **None** | untouched |
| `pyproject.toml` / CI | **None** | both `src` roots already on `pythonpath`; ruff already scans `tests/` |
| Decoupling test / C4 | **None** | parity test lives in `tests/`, imports both private fns at test time only; does not add any package-source import |
| New test file | +1 | `tests/test_llm_json_parity.py` |
| Coverage | neutral/up | adds assertions over existing lines; cannot lower the `--cov-fail-under=95` floor |

**What might break:** essentially nothing in production. The only failure mode is the *intended* one — a future commit that diverges the twins will now fail CI. The secondary risk is a brittle test (e.g. an over-specific source-identity assertion that trips on benign reformatting); §5.4 is marked optional precisely to bound that risk, with behavioral parity as the robust core.

---

## 8. Verification Plan

The plan is verified-complete when, in the implementation session:

1. `pytest tests/test_llm_json_parity.py` is green.
2. The **drift-detection proof** (§6) demonstrably turns the parity test RED when one copy is reverted to the stale regex, and GREEN again when restored.
3. Full suite, ruff, mypy, and the decoupling test are all green.
4. The file documents the C4 + #16 rationale so the duplication is not "helpfully" merged later.

---

## 9. Out of Scope (explicit)

- Any consolidation into a shared module or package (Options A/B). Analysed and rejected in §4; re-open only on a 3rd LLM client.
- Any change to `_extract_json`, `_call_json`, `_call_claude`, the `_CODE_FENCE` regex, or the two error classes.
- The other three audit-identified duplications (client construction, round-trip, guards) beyond what the §5.3 guard-message parity test *observes* — the test pins them, it does not de-duplicate them.
- Cosmetic items (e.g. the data-agent `_call_claude` empty-content comment asymmetry, standing option #4) — separate, if ever.

---

## 10. Provenance

- Audit source: `docs/audits/2026-06-01-technical-debt-audit.md:84-86,154,173,206`.
- Decoupling constraint: `docs/architecture-history/architecture-plan.md:36 (C4), :346, :532, :1078`; `tests/test_data_agent_decoupling.py`.
- Drift history: audit #16 (Sessions 98/99/100); Session-51 live crash `run_id=run_b1_resume_live_1776570556`.
- Evidence inventory: §2, produced by direct grep/diff at HEAD `e4bf6f5` + a 4-reader research workflow (`wf_7d5529b2-ed6`), with one subagent count corrected against direct grep (§2.1 note).
