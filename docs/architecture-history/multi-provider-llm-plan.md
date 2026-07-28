# Multi-Provider LLM Support — Planning Document

> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-07-27 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

**Author:** Session 159 (planning session) — 2026-06-17.
**Baseline commit:** `517d35b` — Session 159 claim stub; tree clean, `origin/master` synced. Test baseline (last fresh confirm S155): 797 passed @ 97.28%, mypy 0/64, ruff clean, decoupling 2/2.
**Implementation target:** five phases, **one session each** (Sessions 160–164 minimum). Each phase is a separate session with its own close-out (`SESSION_RUNNER.md` Planning Sessions protocol; FM #18).
**Status:** Draft for executor review. **This plan is the deliverable of Session 159. Session 159 writes no `src/`, `packages/`, `scripts/`, or `tests/` code.** Failure mode #18 (planning-to-implementation bleed) and #19 (plan-mode bypass) are the primary risks for this session.
**Strategic decisions (resolved with evidence in §3; operator-gated items flagged):**
- **(A) Architecture — `concrete clients`, not an adapter layer.** The provider seam was *built* for one-new-client-per-provider (factory docstrings, §2.1). The large majority of the LLM-calling code is already provider-agnostic (14 of 20 LLM-touching production files need zero edits — §2.1). An adapter (LiteLLM / LangChain `init_chat_model`) only pays off at 3+ heterogeneous providers and inflates the standalone data-agent wheel's dependency surface. See §3.1.
- **(B) Driver/provider — operator's call; recommended first second-source is AWS Bedrock-hosted Claude.** Lowest prompt-portability cost (prompts + `_extract_json` transport intact), relieves single-provider concentration (`AI-Dependencies.md` §6.7) and keeps data in the org's cloud tenant (§6.3). See §3.2.
- **(C) JSON parsing — keep the fenced-text `_extract_json` path for the first provider; treat native structured output as an opt-in follow-up, not a precondition.** See §3.3.
- **(D) Eval/parity gating is the load-bearing risk** — no second provider ships to production until it clears the golden-corpus thresholds (§3.4, Phase B, Phase E). **Here be dragons.**
**Out of scope (do NOT bundle):** implementing any provider this session; an adapter layer (analysed and rejected in §3.1, preserved for a future architect); replacing `_extract_json` with native structured output across the existing Anthropic clients (a separate quality decision — §3.3, Open Question Q3); streaming, tool-use, token-counting, or Managed-Agents adoption (none currently used); any change to the LangGraph topology, the intake 20-question / 3-revision caps, or the data-agent decoupling boundary (C4). See §1.2.

---

## 0. What this document is

This plan describes how to add a **second, non-Anthropic LLM provider** to the Model Project Constructor pipeline so the tool is not single-sourced on Anthropic. It is the planning response to the **AI Dependencies** wiki page (`docs/wiki/claims-model-starter/AI-Dependencies.md`, Session 157), whose §6.7 names single-provider concentration as a live, unmitigated risk for a tool serving a P&C insurer's claims org.

The work is staged over **five implementation sessions** so each is one bounded, reversible deliverable, matching the Planning Sessions protocol (grep-based inventory, per-phase DONE criteria, explicit session boundaries). The first two phases (config reconciliation, eval harness) deliver value **even if no second provider is ever wired** — they harden the existing single-provider setup and make any future swap measurable.

House-style precedent for this document: `docs/architecture-history/github-gitlab-abstraction-plan.md` (the closest analogue — a multi-backend abstraction behind an existing protocol seam) and `docs/architecture-history/o2-shared-llm-json-plan.md` (the prior analysis of these exact LLM clients).

---

## 1. Scope

### 1.1 In scope

1. **Reconcile the LLM configuration** so a second provider has a clean place to plug in: single-source the default model (the `run_pipeline.py --model` default and the clients' `DEFAULT_MODEL` currently disagree — §2.5 Trap 4), and generalise the API-key lookup and default-model resolution from Anthropic-specific to per-provider.
2. **Build the eval / parity harness first** — a golden-case corpus per LLM capability with concrete pass thresholds, a `live` pytest marker that keeps CI hermetic, and a cross-provider extension of the existing `tests/test_llm_json_parity.py` drift-guard. Calibrate thresholds against an Anthropic baseline.
3. **Add one second provider behind the existing protocol/factory seams** — a new concrete client per agent (intake + data-agent), one branch per `make_llm_client`, one `LLMProvider` Literal extension per package. No call-site edits.
4. **Parameterise the intake web UI** so the second provider is reachable from it (today `ui/intake/app.py` hardcodes `"anthropic"` — §2.5 Trap 3).
5. **Define the shadow-run → cutover gate** — run the candidate provider side-by-side on the golden corpus, report agreement, and gate any production cutover on the §3.4 thresholds.

### 1.2 Out of scope (do NOT bundle into this work)

- **Choosing *which* provider** beyond the recommendation in §3.2 — that is the operator's compliance/business decision (`AI-Dependencies.md:119` states the PII/data-handling choice "is a policy decision the operator owns, not something the code resolves").
- **An adapter layer (LiteLLM / LangChain `init_chat_model`).** Analysed and rejected in §3.1; re-open only if the project commits to 3+ heterogeneous providers. Preserved for a future architect.
- **Replacing the duplicated `_extract_json` fence-stripper with native structured output** across the existing Anthropic clients. This is a separate quality decision (§3.3 / Open Question Q3), not a precondition for a second provider, and it would rewrite the load-bearing `tests/test_llm_json_parity.py` invariant.
- **Streaming, tool-use, server-side tools, token-counting, retry/back-off, Managed Agents.** None are used today (the clients are plain `messages.create` text-in/JSON-out). Adding production hardening (retry, rate-limit mapping) is noted as a risk (§2.5 Trap 5) and an Open Question (Q4), not built here.
- **LangGraph topology, the intake `MAX_QUESTIONS=20` / `MAX_REVISIONS=3` caps, the governance controlled vocabularies, the data-agent SQL/datasheet logic.** All provider-agnostic; untouched.
- **The C4 decoupling boundary.** The standalone data-agent wheel must not import the orchestrator (`tests/test_data_agent_decoupling.py`); this plan preserves it (it is the reason the two clients are duplicated rather than shared — §2.5 Trap 1).
- **The website agent.** It uses **no LLM** (only the `RepoClient` seam); nothing to do.

---

## 2. Current state as of `517d35b`

### 2.1 The provider seam already exists — and was built for exactly this

There are **two parallel, deliberately-separate** LLM seams, one per agent. Both already have a factory whose docstring states the intent verbatim:

> *"a second provider becomes one new client module plus one branch here — no edits at the call sites."*
> — `src/model_project_constructor/agents/intake/factory.py:6-9` **and** `packages/data-agent/src/model_project_constructor_data_agent/factory.py:6-9`

Each factory single-sources its known-provider list from a `Literal` via `typing.get_args`, so the unknown-provider error cannot drift from the set the factory handles:

```python
LLMProvider = Literal["anthropic"]                 # intake/factory.py:30 ; data .../factory.py:31
KNOWN_PROVIDERS: tuple[str, ...] = get_args(LLMProvider)   # :32 / :33
def make_llm_client(provider="anthropic", *, model=None): # :35-64 / :36-64
    if provider == "anthropic": ...                # branch at :50 / :51
    raise ValueError(f"Unknown LLM provider {provider!r}. Known providers: {...}.")
```

Both packages **re-export `make_llm_client` and `LLMProvider` by name** (`agents/intake/__init__.py:17-18,59-60`; `data_agent/__init__.py:21-22,58,67`). Because the symbols' *names* don't change when a provider is added (only the `Literal`'s value and the factory body), **`__init__.py` needs no edit** for a new provider. (This corrects an over-count in the Session-159 investigation, which listed `__init__.py ×2` among edited files.)

**Investigation summary (verified at `517d35b`):** the `anthropic` SDK is imported in exactly **2 production files** (the two `anthropic_client.py`), lazily inside `__init__` so factory import stays SDK-free (pinned by `test_factory_import_does_not_load_anthropic`). **14 of 20** production files that touch LLM logic use only the protocol methods and need **zero** edits for a provider change. **A hand-written second provider touches ~4 core production files** (2 new client modules + 2 factory edits) plus the UI-reachability and config-reconcile edits in §4.8 — i.e. **14 of 20 (≈70%) of the LLM-touching production files are provider-agnostic and untouched.** (The "≈70%" is a file count, not a line count — a rough magnitude, not a precise metric; the point is that the seam localises the change.)

### 2.2 The intake seam

- Protocol `IntakeLLMClient` — **4 methods**: `next_question`, `draft_report`, `classify_governance`, `revise_report` (`agents/intake/protocol.py:75-93`). Error class `IntakeLLMError(RuntimeError)` (`protocol.py:96-98`).
- Concrete `AnthropicLLMClient` (`agents/intake/anthropic_client.py`): `anthropic.Anthropic()` constructed with **no args** (`:192`, lazy import `:190`) — the SDK reads `ANTHROPIC_API_KEY` from the environment. `DEFAULT_MODEL = "claude-sonnet-4-6"` (`:39`), `DEFAULT_MAX_TOKENS = 4096` (`:40`), both hardcoded class constants.
- Each method builds a prompt, calls `_call_json(system, user)` (`:274-296`) → `messages.create(model, max_tokens, system, messages=[{role:"user", content:user}])`, guards empty content (`:290`) and non-`TextBlock` (`:294`), then `_extract_json(block.text)` (`:296`). `_extract_json` (`:356-388`) tries a bare `json.loads` first, then strips a ```` ``` ```` fence via `_CODE_FENCE` (`:353`), raising `IntakeLLMError` on final failure.

### 2.3 The data-agent seam (standalone wheel)

- Protocol `LLMClient` — **5 required methods** (`generate_primary_queries`, `generate_quality_checks`, `summarize`, `generate_datasheet`, `generate_baseline_query`; `.../llm.py:101-160`) **+ 1 optional** `rank_candidate_tables` (`hasattr`-dispatched by `discovery.probe_information_schema`; concrete at `anthropic_client.py:318`). Error class `LLMParseError(ValueError)` (`anthropic_client.py:102-103`).
- Concrete `AnthropicLLMClient` (`.../anthropic_client.py`): `DEFAULT_MODEL = "claude-sonnet-4-6"` (`:53`), `max_tokens=4096` (`:54`), lazy `anthropic.Anthropic()` in `__init__` (`:109-121`). `_call_claude` (`:366-380`) returns **raw text**; each caller runs its **own** `_extract_json` (`:475-505`; `_CODE_FENCE` `:472`). A `_sanitize_prompt_field` helper (`:396-414`) strips control chars + bounds length on **inventory metadata** before prompt injection — a prompt-injection / token-budget guard (`AI-Dependencies.md` §6.4), **not** PII redaction.
- **Structural asymmetry vs intake:** data-agent returns raw text and parses per-method; intake returns parsed JSON from a fused round-trip. A second provider must satisfy each seam on its own terms.

### 2.4 Configuration & call-site wiring

- `ANTHROPIC_API_KEY` is read in `src/model_project_constructor/orchestrator/config.py:207` and validated at `:237-240` (`require_anthropic_api_key`). The concrete clients don't read it explicitly — the SDK self-discovers it. The data-agent wheel does **not** import `orchestrator/config.py` (C4); any per-provider key logic for the wheel must live inside the wheel.
- `scripts/run_pipeline.py` exposes `--provider` (default `"anthropic"`, ~`:447-449`) and `--model` (default `"claude-opus-4-7"`, **`:440`**). The data-agent CLI exposes both (`cli.py` `--provider` ~`:106-109`, `--model` ~`:101-104`, `_build_llm` ~`:216`).
- The intake **web UI** `ui/intake/app.py` hardcodes `make_llm_client("anthropic")` in `_default_llm_factory` (`:62`); `create_app` (`:76`) accepts an injectable `llm_factory` (tests use it) but exposes **no provider selection** at runtime.

### 2.5 What is NOT provider-agnostic — the traps

These were found by reading the clients and config during Session-159 evidence-gathering; the backlog/handoff did not surface them. Each is contained and is bundled into the phase noted.

#### Trap 1 — C4 forces *double* implementation, not shared code
The standalone data-agent wheel must not import the orchestrator (`tests/test_data_agent_decoupling.py`). A shared `OpenAIClient`/`BedrockClient` helper therefore **cannot** live in the main package and be imported by the wheel — exactly why the two `AnthropicLLMClient`s (and their two `_extract_json` copies) are already duplicated. **Budget two client modules + two factory branches per provider, not one.** The drift guard for the duplication is `tests/test_llm_json_parity.py` (Session 102 / `o2-shared-llm-json-plan.md`); a second provider extends, does not replace, that guard (§Phase B).

#### Trap 2 — the `"openai"` unknown-provider sentinel collision
Both `make_llm_client` unknown-provider tests use the literal string `"openai"` as the sentinel "unknown" value and assert it appears in the error message:
- `tests/agents/intake/test_factory.py:69,71` (`make_llm_client("openai")`; `assert "openai" in message`)
- `tests/data_agent_package/test_factory.py:66,68`

**If the chosen first provider is literally `"openai"`,** adding it as a *real* provider breaks these 4 assertions — they must be re-pointed to a still-unknown sentinel (e.g. `"nonexistent"`). **If the first provider is `"bedrock"` (the §3.2 recommendation), `"openai"` remains a valid unknown sentinel and these tests are untouched.** Handle this conditionally in Phase C's pre-flight, not blindly.

#### Trap 3 — the intake UI hardcodes `"anthropic"`
`ui/intake/app.py:62` hardcodes the provider; the CLI paths (`run_pipeline.py`, data-agent `cli.py`) already expose `--provider`. A second provider is **unreachable from the web UI** until `create_app`/`runner` thread a provider/model through (Phase D). The data agent and `run_pipeline.py` need no such work.

#### Trap 4 — model-default inconsistency (valid IDs, wrong consistency)
`run_pipeline.py:440` defaults `--model` to **`"claude-opus-4-7"`** (Opus 4.7) while both clients hardcode `DEFAULT_MODEL = "claude-sonnet-4-6"` (Sonnet 4.6). Both are **valid, current** model IDs — but they are different tiers and prices (Opus 4.7 ≈ $5/$25 per MTok; Sonnet 4.6 ≈ $3/$15), so the model actually run depends on which entrypoint you use. A second provider has **no Anthropic default to inherit**, so per-provider default-model resolution must be designed (the factory's `model=None` → provider-default contract already exists at `factory.py:60`). Reconcile in Phase A; the eval baseline (Phase B) must pin the exact `(provider, model)` it measures.

> ⚠ **Resolved by Session 160 (executor) — this was NOT an accidental inconsistency.** The plan diagnosed the `run_pipeline.py` Opus default vs the clients' Sonnet default as "wrong consistency," but did not surface **`PROJECT_LEARNINGS.md` #20** (Session 24): the operator *deliberately overrode a Sonnet recommendation* so the **pilot entrypoint** (`run_pipeline.py`) uses the **highest-quality** model for first-impression runs — keeping "was it the model?" out of the quality judgement — while the **library/CLI clients** default to the cheaper Sonnet for iteration. This is documented in `docs/tutorial.md` §6c and `OPERATIONS.md` §4.4. The operator confirmed (S160) this is an **intentional two-tier default**. S160 therefore kept `run_pipeline.py` on Opus, single-sourcing the literal into a named `PILOT_DEFAULT_MODEL = "claude-opus-4-7"` constant (with a Learning-#20 comment) so the value is written once and is not re-flagged as drift. **Do not collapse the two tiers to one model.** The Phase B eval baseline still pins the exact `(provider, model)` it measures.

#### Trap 5 — thin clients: no retry / rate-limit / error mapping
Both clients call `messages.create` with **no** retry, back-off, rate-limit handling, or exception mapping (`AI-Dependencies.md` §6.6). A hand-written second client that mirrors this inherits the same thinness. Production hardening (retry, mapping provider exceptions onto `IntakeLLMError`/`LLMParseError`) is **Open Question Q4**, deliberately *not* built in this plan — but a second provider's SDK raises *different* native exceptions, so each new client must at minimum map its parse/empty-response failures onto its seam's error class (Phase C DONE criteria).

---

## 3. Strategic decisions

### 3.1 Decision (A): concrete clients, not an adapter layer

| Option | What it is | Deps added (incl. the standalone wheel) | Blast radius | Debuggability | Verdict |
|---|---|---|---|---|---|
| **A — concrete client per provider (CHOSEN)** | New `<provider>_client.py` per agent behind the existing protocol/factory | Only the provider's own SDK (e.g. `anthropic[bedrock]` extra → boto3; or `openai`) | ~4 core production files (§4.8) | unchanged — the SDK call stays a readable one-liner | **Chosen** — the seam was built for it; 14 of 20 LLM-touching files need no edit |
| **B1 — LiteLLM adapter** | `litellm.completion(model="…/…")` replaces the `messages.create` round-trip | `litellm` (heavy: pulls `openai`, `tiktoken`, its own httpx stack) into **both** `pyproject.toml`, incl. the wheel | similar core + 2 manifest churns; `_extract_json` survives as fallback | regresses — opaque param translation, wrapped errors, fast/breaking release cadence | Rejected for a 1–2 provider goal |
| **B2 — LangChain `init_chat_model` / `with_structured_output`** | `BaseChatModel` per provider; structured output retires `_extract_json` cleanly | `langchain-anthropic` + `langchain-openai` (**not installed today**; `langchain-core 0.3.84` is present transitively via `langgraph 0.2.76`) | similar core + manifest churn + rewrites `test_llm_json_parity` | regresses — hides tool-call mechanics; couples the wheel to LangChain's major-version cadence | Rejected for a 1–2 provider goal |

**Why A.** The factory docstrings (§2.1) committed the project to A. The duplicated `_extract_json` is only 14 lines and is already drift-guarded (`o2-shared-llm-json-plan.md`); an adapter does **not** eliminate the duplication unless it also adopts structured output (Decision C), and the C4 boundary means an adapter wrapper would itself be duplicated across the two packages exactly as `_extract_json` is. An adapter genuinely wins only when (a) **3+** providers are planned **and** (b) they're heterogeneous in API shape — neither holds for the stated goal. Per the workstream's anti-astronaut-architecture heuristic (`ARCHITECTURE_WORKSTREAM.md`; echoed in `o2-shared-llm-json-plan.md` §3.4), a heavy abstraction for a 1–2 provider need is disproportionate.

> ⚠ **Correction recorded for the executor:** the Session-159 adapter analysis claimed the installed tree was at "langgraph 1.2.2 / langchain-core 1.4.0 / anthropic 0.75.0" and that the pins were "years stale." **This is false.** Verified installed versions at `517d35b`: `langgraph 0.2.76`, `langchain-core 0.3.84`, `anthropic 0.94.1`, `langgraph-checkpoint-sqlite 2.0.11` — all *within* the declared pins (`langgraph>=0.2,<0.3`, `anthropic>=0.40`, `langgraph-checkpoint-sqlite>=2.0,<3`). The real B2 risk is the *future* churn of the LangChain ecosystem and the **new** `langchain-anthropic`/`langchain-openai` dependencies, not a present version drift. Do not propagate the hallucinated numbers.

**Re-open trigger for B:** a committed decision to support **3+ heterogeneous providers**. If A is chosen and that day comes, prefer **B2** over B1 for the wheel (leans on already-present `langchain-core`, lighter than LiteLLM, and `with_structured_output` actually retires `_extract_json`) — accepting LangChain version-churn as the named residual risk.

### 3.2 Decision (B): which provider first — operator's call; **recommend AWS Bedrock-hosted Claude**

The technical seam is provider-neutral; *which* risk to prioritise is a business/compliance decision the operator owns (`AI-Dependencies.md:119`). The candidates, mapped to the wiki's named risks (§6.3 PII egress, §6.6 availability/cost, §6.7 concentration):

| Candidate | Risk addressed | Prompt-portability cost | New dependency surface | Notes |
|---|---|---|---|---|
| **AWS Bedrock (Claude) — RECOMMENDED FIRST** | §6.7 (provider/account/region concentration); partially §6.3 (data stays in the org's AWS tenant under enterprise/no-train terms) | **Lowest** — same Claude family; the Claude-tuned prompts **and** the `_extract_json` fence-stripper transport essentially unchanged | only the `anthropic[bedrock]` **extra** (boto3) — *no new top-level SDK*; same `messages.create` Messages-API shape, model IDs gain an `anthropic.` prefix (e.g. `anthropic.claude-sonnet-4-6`) | Does **not** address a Claude *model-family* outage (§6.6) |
| Azure OpenAI (compliant tenant) | §6.3 (org Azure tenant, no-train terms) + §6.7 (true vendor + model-family diversity) | High — GPT-family prompts behave differently; re-tune + re-validate the interviewer/governance/datasheet prompts against the parity battery | `openai` SDK (Azure config) | Native structured output is a strength (Decision C / Q3) |
| OpenAI / Google Gemini direct | §6.7 + §6.6 (independent availability pool) | High — prompt re-tune | `openai` / `google-genai` SDK | **Worsens §6.3** — a second external PII egress destination + a second data-terms negotiation |
| Self-hosted open-weight (vLLM) | **Eliminates §6.3 egress entirely** + fully owns §6.6/§6.7 | Highest — open models are weakest at strict-JSON-without-prose; stresses `_extract_json` and the parity battery hardest | GPU infra + MLOps ownership (cost flips per-token → infra) | The only option that keeps interview answers / `DataRequest` free-text inside the org boundary |

**Recommendation: stand up AWS Bedrock-hosted Claude first.** It is the cheapest to validate against *this exact seam* (prompts and parser transport intact, only the `anthropic[bedrock]` extra is new), directly relieves §6.7 concentration, and meaningfully improves §6.3 (PII stays in the org's cloud tenant under enterprise terms) — de-risking the migration *mechanics* before a harder vendor-diversity or self-hosting effort. It is a governance second-source that keeps prompts tuned — exactly the wiki's framing. **The operator decides;** Phases A/B/D are provider-agnostic, so this choice only binds Phase C.

> Note on AWS surfaces: "Amazon Bedrock" (partner-operated; `anthropic.`-prefixed IDs; Messages-API shape; no server-side Anthropic tools / Managed Agents) is distinct from "Claude Platform on AWS" (Anthropic-operated; bare model IDs; full parity). Either works for this seam since we use only plain `messages.create`. The executor confirms the exact `anthropic` SDK Bedrock client binding (`AnthropicBedrock` / `AnthropicBedrockMantle` per the installed SDK version) and the `anthropic.`-prefixed model-id mapping at implementation time — see Phase C pre-flight.

### 3.3 Decision (C): keep fenced-text `_extract_json` for the first provider

The current clients obtain JSON by asking for fenced text and stripping it (`_extract_json`). Both Anthropic (`output_config: {format: {type:"json_schema", ...}}`) and OpenAI (`response_format`) offer **native structured output** that would make the fence-stripper unnecessary. That is tempting but **out of scope for a second provider** because:

1. Adopting it asymmetrically (new provider uses native JSON; Anthropic keeps fenced text) makes the parsers diverge, which the existing `tests/test_llm_json_parity.py` (which compares the two *Anthropic* copies) does not cover.
2. Adopting it everywhere rewrites the load-bearing parity invariant and the Anthropic clients — a separate quality decision (Open Question Q3).

**Decision:** the first second-provider client uses the same fenced-text + `_extract_json` convention as today, so the parity battery extends naturally (Phase B). Revisit native structured output as a follow-up once a second provider is proven (Q3). Anthropic structured outputs are GA on the models in use (Sonnet 4.6 / Opus 4.8), so this door stays open.

### 3.4 Decision (D): eval/parity is the gate — **here be dragons**

The factory seam makes *swapping* a provider trivial; **all** the risk is in **output quality**. A plausible-but-wrong provider that parses fine but writes subtly worse SQL, mis-labels governance tiers, or fails to converge the interview is the failure this plan exists to prevent. CI is **hermetic today** — all four `.github/workflows/ci.yml` jobs (lint/mypy/test/decoupling) run offline with **no `ANTHROPIC_API_KEY`**, and `test_llm_json_parity.py` uses a `_FakeAnthropic` (`:90-107`). Therefore:

- **Live-provider eval cannot gate CI** without breaking hermeticity. Split into a **deterministic CI tier** (fakes only, every PR) and a **`live`-marked periodic/manual tier** (real keys, run pre-cutover) — `pytest -m 'not live'` stays the CI default.
- **No second provider reaches production until it clears every threshold in the table below on the live corpus** (Phase E gate).

**Proposed pass thresholds** (capability → metric → threshold), grounded in the existing oracles:

| Capability | Metric | Threshold | Oracle that already exists |
|---|---|---|---|
| Any JSON method | parse success via both `_extract_json` copies | **≥ 99%** | `tests/test_llm_json_parity.py` battery (extend per-provider) |
| `generate_primary_queries` / baseline | SQL parse-valid **100%** + **executable ≥ 95%** on a seeded SQLite P&C schema | matches the in-pipeline `RETRY_ONCE` tolerance | `sql_validation.validate_sql` (`sqlparse`, `sql_validation.py:16`) + `ReadOnlyDB.execute` (`db.py:22`, accepts `sqlite:///:memory:`) |
| `classify_governance` | exact label agreement vs a human-blessed reference | **≥ 90%**, **0 laxer-tier misses** (the prompt says "if in doubt pick the stricter tier") | closed vocabularies: `CycleTime`/`RiskTier` (`common.py`), `GOVERNANCE_FRAMEWORKS` |
| `generate_quality_checks` | outer array length == #primary queries | **100%** (hard structural contract) | shape assertion |
| Intake interview | `believe_enough_info=true` within the 20-question cap; **0 premature convergence** | **≥ 95%** of golden interviews | `MAX_QUESTIONS`/`MAX_REVISIONS` (`state.py`), YAML fixture replay (`agents/intake/fixture.py`) |

> **Refined in Session 173 (faithfulness fix, not a threshold change).**
> `classify_governance`'s "exact label agreement" is scored **per-label**:
> `cycle_time` on exact agreement (gated ≥ 90%), `risk_tier` on match-or-stricter
> with the zero-tolerance laxer-miss as its hard gate. The original exact-*both*
> metric counted the prompt-instructed stricter `risk_tier` direction as a
> disagreement and so scored even the incumbent 0% (a gap #2 artifact). The
> 0.90 / 0 thresholds are unchanged. See `tests/eval/README.md` §"Per-label
> scoring" and `tests/eval/eval_scoring.py`.

**Non-determinism handling:** `messages.create` is called with no `temperature` today (provider default applies). Eval assertions must **not** assert exact text — run each golden case **N ≥ 5** times and assert a **pass-rate** threshold + structural/semantic invariants (parses / label-in-vocab / SQL-executes). For the live tier, pin `temperature=0` *where the provider supports it* to shrink variance while still sampling N times. (Note: Claude Opus 4.7/4.8 and Fable 5 reject `temperature` — so "pin temperature=0" applies to providers that accept it; for Claude-family models, sample N times and rely on invariants.)

**Error-class divergence is load-bearing and preserved per seam:** intake raises `IntakeLLMError(RuntimeError)`, data-agent raises `LLMParseError(ValueError)` (`o2-shared-llm-json-plan.md` §2.3; pinned by `test_llm_json_parity.py:202-215`). A new provider's client must raise the **same** class as its seam, so the cross-provider parity test asserts *error-class-by-seam*, not a unified error.

---

## 4. Grep-based inventory (baseline `517d35b`)

This is the starting list of sites the phases touch. **Each phase re-runs its own verification greps** (the github-gitlab plan's discipline; Learning #28 — re-confirm line numbers before editing, they drift).

### 4.1 `anthropic` SDK imports
**Search:** `import anthropic|from anthropic|anthropic\.`
- Production (4 hits, 2 files): `agents/intake/anthropic_client.py` (`from anthropic.types import TextBlock` top-level `:21`; lazy `import anthropic` in `__init__` `:190`); `data_agent/anthropic_client.py` (top-level type import `:35`; lazy `:~116`).
- Tests: the two `test_anthropic_client.py` + the two `test_factory.py` (monkeypatch the SDK). Keep counts separate when re-grepping.

### 4.2 `_extract_json` / `_CODE_FENCE`
- intake `anthropic_client.py:353` (`_CODE_FENCE`), `:356-388` (`_extract_json`).
- data `anthropic_client.py:472` (`_CODE_FENCE`), `:475-505` (`_extract_json`, per-caller).
- guard: `tests/test_llm_json_parity.py` (~216 lines; `_FakeAnthropic` `:90-107`; error-class assertions `:202-215`).

### 4.3 `LLMProvider` / `KNOWN_PROVIDERS` / `make_llm_client`
- intake `factory.py:30,32,35-64` (branch `:50`); data `factory.py:31,33,36-64` (branch `:51`).
- re-exports: `agents/intake/__init__.py:17-18,59-60`; `data_agent/__init__.py:21-22,58,67` (**no edit needed** — names stable).
- call sites that pick a provider: `run_pipeline.py:~154` (data), `:~248` (intake); `data_agent/cli.py:~216` (`_build_llm`); `ui/intake/app.py:62` (`_default_llm_factory`, hardcoded).

### 4.4 model defaults / `MAX_TOKENS` / API key
- `DEFAULT_MODEL="claude-sonnet-4-6"`: intake `anthropic_client.py:39`, data `:53`. `MAX_TOKENS=4096`: intake `:40`, data `:54`.
- `run_pipeline.py:440` `--model` default `"claude-opus-4-7"` (**Trap 4**).
- `ANTHROPIC_API_KEY`: `orchestrator/config.py:207` (read), `:237-240` (validate). Also referenced in `data_agent/USAGE.md`, `data_agent/cli.py` docstring, `run_pipeline.py` help text.

### 4.5 `--provider` / `--model` CLI flags
- `run_pipeline.py` (`--provider` `:~447-449`, `--model` `:440`); `data_agent/cli.py` (`--provider` `:~106-109`, `--model` `:~101-104`).

### 4.6 tests touching the seam
- ~13 test files exercise LLM logic (of ~47 `test_*.py`). Direct seam tests: `tests/agents/intake/test_factory.py`, `tests/data_agent_package/test_factory.py` (**Trap 2 sentinel** `:69,71` / `:66,68`), the two `test_anthropic_client.py`, `tests/test_llm_json_parity.py`, `tests/test_data_agent_decoupling.py` (C4). Fakes: `_FakeAnthropic` (parity test), `FakeLLMClient` (data-agent protocol fake), `FixtureLLMClient` (intake UI).

### 4.7 dependency manifests
- `pyproject.toml`: `langgraph>=0.2,<0.3` (`:19`), `anthropic>=0.40` (`:20`), `langgraph-checkpoint-sqlite>=2.0,<3` (`:31`).
- `packages/data-agent/pyproject.toml`: `langgraph>=0.2,<0.3` (`:13`), `anthropic>=0.40` (`:16`).
- **Installed (verified):** `langgraph 0.2.76`, `langchain-core 0.3.84`, `anthropic 0.94.1`, `langgraph-checkpoint-sqlite 2.0.11`. **Not installed:** `litellm`, `openai`, `langchain-anthropic`, `langchain-openai`.

### 4.8 Summary: files touched by each phase

| Phase | Production files | Test files | Manifests |
|---|---|---|---|
| **A — config reconcile** | `orchestrator/config.py`, both `factory.py`, `run_pipeline.py`, (maybe both `anthropic_client.py` for default-model resolution) | both `test_factory.py`, config tests | — |
| **B — eval harness** | none (test-tree only) | **new** `tests/eval/` corpus + harness; extend `tests/test_llm_json_parity.py` | maybe a `live` marker in `pyproject.toml [tool.pytest]` |
| **C — second provider** | **2 new** `<provider>_client.py`; both `factory.py` (Literal + branch) | new client tests; both `test_factory.py` *iff provider=="openai"* (Trap 2) | both `pyproject.toml` (provider SDK / `anthropic[bedrock]` extra) |
| **D — UI parameterise** | `ui/intake/app.py`, `ui/intake/runner.py` | UI tests | — |
| **E — shadow/cutover** | none (harness + docs) | shadow-run report under `tests/eval/` | — |

---

## 5. Phases

**Ordering rationale.** Config reconciliation (A) removes the model-default confound before any baseline is measured. The eval harness (B) is built and calibrated against Anthropic **before** a second provider exists, so the second provider (C) is measured against a known-good bar. UI parameterisation (D) makes the provider reachable. The shadow/cutover gate (E) is the production go/no-go. Phases A and B deliver value even if C never ships.

> ⚠ **Here be dragons:** Phase B (eval harness design + threshold calibration) and Phase E (shadow run + cutover judgement) carry the real risk. Phases A, C, D are mechanical given the seam. Budget the most caution for B and E.

### Phase A — Reconcile LLM configuration

- **Work:** (1) Single-source the default model so `run_pipeline.py --model` and the clients' `DEFAULT_MODEL` agree (Trap 4). Recommended shape: `run_pipeline.py --model` defaults to `None` and falls through to the client/provider default (the `factory.py:60` `model=None` → provider-default contract already exists), eliminating the duplicated literal. (2) Generalise the API-key lookup: a per-provider key resolver (e.g. `anthropic → ANTHROPIC_API_KEY`, `bedrock → AWS creds chain`) — in `orchestrator/config.py` for the main package, and **inside the wheel** for the data agent (C4). (3) Generalise per-provider default-model resolution so each provider names its own default. **No new provider; the `anthropic` path's observable behaviour is unchanged.**

> ★ **As built (Session 160) — two deviations from the recommended shape, both deliberate:**
> - **(1) revised:** the Trap-4 "single source to one model" recommendation was **rejected** once Learning #20 surfaced (see the Trap-4 correction box). `run_pipeline.py` keeps its **Opus** pilot default, single-sourced into a named `PILOT_DEFAULT_MODEL = "claude-opus-4-7"` constant; the clients keep their Sonnet `DEFAULT_MODEL`. "Single-sourced" is satisfied as *each value written once under a name* (no bare duplicated literal), not *one model everywhere* — the two-tier split is intentional. Observable behaviour of every entrypoint is therefore **unchanged**.
> - **(2) shipped for the main package; (2-wheel) DEFERRED to Phase C.** `orchestrator/config.py` gained the provider-keyed seam — an `LLMProviderSpec`/`LLM_PROVIDERS` registry (mirrors `PlatformSpec`/`REPO_PLATFORMS`), `require_llm_api_key(provider)`, and a back-compat `anthropic_api_key` property / `require_anthropic_api_key()` alias. The **wheel-side** resolver was **not** built: the wheel has no key-lookup code today (the SDK self-discovers `ANTHROPIC_API_KEY`), and the §3.2-recommended next provider (**Bedrock**) authenticates via the **boto3 credential chain — not a single api-key env var**, so a Phase-A `provider→env_var` resolver in the wheel would be a speculative, ill-fitting abstraction with nothing to consume it. It is the natural, non-speculative job of **Phase C**, designed against the real provider's auth model. **(3)** needed no code: the factories already resolve `model=None → DEFAULT_MODEL` per provider branch.
- **What DONE looks like:** model default single-sourced (grep shows no second hardcoded default model string); key lookup and default-model resolution are provider-keyed; the `anthropic` path produces identical results; all tests green.
- **Pre-flight:** `git status` clean; re-grep §4.3/§4.4 to confirm line numbers; read `config.py:200-245`, both `factory.py`, `run_pipeline.py:430-455` before editing.
- **Verification:**
  - `uv run pytest -q` → 797+ pass (no regression).
  - `uv run mypy` → 0 errors. `uv run ruff check src/ tests/ packages/ scripts/` → clean.
  - `rg "claude-opus-4-7|claude-sonnet-4-6" scripts/ src/ packages/` → exactly one canonical default location remains (document where).
  - Smoke: `python scripts/run_pipeline.py --help` shows the reconciled `--model` default; the fake/fixture pipeline path still runs.
  - `uv run pytest tests/test_data_agent_decoupling.py --no-cov` → green (C4 intact).
- **Session boundary:** one session. Close out. **No second provider, no eval harness.**

### Phase B — Eval / parity harness + Anthropic baseline (load-bearing)

- **Work:** Create `tests/eval/` — a golden-input corpus per capability (intake interviews; data-agent `DataRequest`s), reference outputs/labels, and a seeded SQLite P&C DDL for SQL-executability checks. Add a `live` pytest marker so `pytest -m 'not live'` stays the hermetic CI default and `pytest -m live` is the keyed periodic tier. Extend `tests/test_llm_json_parity.py` to a cross-**provider** parity notion (every provider's raw output parses, via both `_extract_json` copies, to the same structure; error-class-by-seam preserved). Reuse the existing `FakeLLMClient` / YAML fixture replay for the deterministic tier. Run the `live` tier against **Anthropic** to calibrate the §3.4 thresholds and capture reference labels.

> ★ **As built (Session 161) — delivered; live Anthropic baseline DEFERRED (operator decision).**
> Shipped `tests/eval/`: a golden corpus (governance reference labels reusing the three project intake fixtures + one authored `tier_4_low`/`operational` case completing the `RiskTier` vocabulary; SQL cases over a seeded P&C schema `pc_schema.sql`; interview goldens), **pure deterministic scorers** (governance exact-label agreement + **0-laxer-tier-miss**, SQL parse/executability via the existing `validate_sql`/`ReadOnlyDB` oracle, structural QC, interview convergence), a **deterministic CI tier** (24 tests, hermetic, no key) and a **wired `live` tier** (`test_eval_live.py`, `@pytest.mark.live`, auto-skipped without `ANTHROPIC_API_KEY`). Registered the `live` marker (`pytest -m 'not live'` stays the CI default). Extended `tests/test_llm_json_parity.py` to a provider-parametrized `_SEAMS` registry — **Phase C adds one row per `(seam, provider)`, no test-body edits**. Methodology + the §3.4 table + governance-label provenance + the deferred-baseline gap are in `tests/eval/README.md`.
> **Deferred (logged, not skipped):** no `ANTHROPIC_API_KEY` this session → the **measured Anthropic baseline + threshold calibration** are a follow-up; the §3.4 thresholds in `tests/eval/eval_thresholds.py` are **proposed** until a live run confirms them. The interview live test needs a robust stakeholder-answer strategy before its number is trusted; `GDPR_ART_22` is under-sampled. See README §"Live baseline (deferred)".
> **Governance reference methodology (operator decision):** single SME reviewer — the operator ratifies rule-derived labels (3 reused project goldens + 1 authored, rule-derived with per-field rationale). **Trap 4 stays corrected:** the eval pins the exact `(provider, model)` it measures; it does NOT collapse the intentional two-tier model default (Phase A as-built / Learning #20).
- **What DONE looks like:** `tests/eval/` exists with corpus + harness + seed DDL; deterministic tier green in CI offline; `live` tier runs against Anthropic and records the reference baseline + calibrated thresholds in a committed `tests/eval/README.md` (or similar); the §3.4 threshold table is concretised with measured Anthropic numbers.
- **Pre-flight:** Phase A merged. Read `sql_validation.py`, `db.py`, `agents/intake/fixture.py`, `tests/test_llm_json_parity.py` in full. Decide **how the "human-blessed reference" governance labels are agreed** during corpus construction (single reviewer vs consensus) — the ≥90% agreement / 0-laxer-miss threshold (§3.4) is only meaningful against a defensible reference, so this is a corpus-construction dependency, not an afterthought. Confirm a real `ANTHROPIC_API_KEY` is available for the `live` run (otherwise deliver the deterministic tier + corpus and mark the live baseline as a follow-up — **log the gap, do not silently skip**).
- **Verification:**
  - `uv run pytest -m 'not live' -q` → green offline (no key set).
  - `ANTHROPIC_API_KEY=… uv run pytest -m live -q` → runs; records pass-rates; (expected: Anthropic clears its own thresholds — if it doesn't, the thresholds are miscalibrated, fix them).
  - CI config unchanged in behaviour: the four jobs still pass with no key (the `live` tests are deselected by default).
- **Session boundary:** one session. Close out. **This is the gate's foundation — do not also start wiring a provider.**

### Phase C — Add one second provider behind the seam

- **Work:** Add `agents/intake/<provider>_client.py` (implements the 4 `IntakeLLMClient` methods; raises `IntakeLLMError`) and `data_agent/<provider>_client.py` (implements the 5 required `LLMClient` methods + optionally `rank_candidate_tables`; raises `LLMParseError`), each reusing the fenced-text + `_extract_json` convention (Decision C) and mapping the provider SDK's native parse/empty-response failures onto the seam error class (Trap 5). Extend each `LLMProvider` Literal (`"anthropic"` → `"anthropic", "<provider>"`) and add one `elif` branch per `make_llm_client` (lazy SDK import, matching the anthropic convention so `test_factory_import_does_not_load_*` holds). Add the provider SDK to both `pyproject.toml` (for Bedrock-Claude: the `anthropic[bedrock]` **extra**, not a new top-level SDK). **If the provider is `"openai"`,** re-point the Trap 2 sentinel tests to a still-unknown value.

> ★ **As built (Session 162) — provider = AWS Bedrock-hosted Claude (`"bedrock"`); delivered; live run deferred.**
> **Operator decision:** the target deployment customer is on **AWS Bedrock with no direct Anthropic contract** (one may come later). Bedrock-Claude runs for them today via the AWS Marketplace EULA + AWS-account billing (not a direct Anthropic contract — "Amazon Bedrock" is partner-operated, `anthropic.`-prefixed model ids, AWS auth; distinct from "Claude Platform on AWS"). A future first-party Anthropic contract needs **no new provider work** — the existing `anthropic` provider already covers it, so Phase C is purely additive.
> **Deviation from "one new client module" — both Bedrock clients are thin SUBCLASSES.** The installed `anthropic 0.94.1` exposes `AnthropicBedrock`, whose `messages.create` is **signature-identical** to the base client, so `BedrockLLMClient(AnthropicLLMClient)` in each package overrides only construction (`anthropic.AnthropicBedrock(...)`, AWS/boto3 chain, optional `aws_region`) and an `anthropic.`-prefixed `DEFAULT_MODEL = "anthropic.claude-sonnet-4-6"`. Every method, `_call_*`, and `_extract_json` are inherited — so **Decision C and Trap 5 hold by construction with zero parser-drift surface.** (Cross-package duplication is forced by C4; intra-package subclassing of a drop-in is the honest expression — not the gratuitous copy the parity guard exists to police.) The parity `_SEAMS` gains `("intake","bedrock")` + `("data_agent","bedrock")` rows that reuse the package parser (documented inline).
> **Phase-A-deferred wheel/config key resolver — resolved as a NO-OP for Bedrock.** Bedrock authenticates via the boto3 credential chain, self-discovered by the SDK in **both** packages (mirroring `anthropic.Anthropic()` self-discovering `ANTHROPIC_API_KEY`) — so there is no `provider→env_var` resolver to write. `config.py` instead made `LLMProviderSpec.api_key_env_var` Optional, registered `"bedrock"` with `api_key_env_var=None`, and had `require_llm_api_key("bedrock")` raise a clear AWS-credential-chain error.
> **Trap 2 not triggered** (provider is `"bedrock"`; `"openai"` stays a valid unknown sentinel — sentinel tests untouched). **Trap 4 / Learning #20 preserved** (pilot stays first-party Opus; the Bedrock default is the Sonnet tier, `anthropic.`-prefixed — the two-tier split is *not* collapsed).
> **Deferred (logged, not skipped):** the **live Bedrock corpus run** — no AWS creds this session ("preparing for a user"). DONE bar met = constructible + the deterministic tier proves the harness + gaps documented; the candidate's live pass-rates + the threshold gate are Phase E's job (`tests/eval/README.md`).
> **Known cross-provider usage gap (for a future phase, NOT a Phase C blocker):** `scripts/run_pipeline.py --model` defaults to the first-party id `claude-opus-4-7` (no `anthropic.` prefix), which would 400 on the Bedrock client if `run_pipeline --provider bedrock` is run without `--model`. Call sites are intentionally not edited in Phase C (the factory contract is `model=None → provider default`); operators pass `--model anthropic.claude-…` for Bedrock until a future phase makes the entrypoint default provider-aware. Gates at delivery: **850 passed + 4 live skipped @ 97.33%**, mypy **0/66**, ruff clean, C4 2/2, lazy-import invariant green (now also asserts `boto3`/`botocore` absence). Adversarial verify `wf_599b5922-501` (5 read-only lenses): **5/5 PASS**.
- **What DONE looks like:** `make_llm_client("<provider>")` constructs a working client in both packages; `KNOWN_PROVIDERS` auto-includes it; factory import still loads no SDK; `pytest -m live --provider <p>` (corpus from Phase B) runs and the candidate's pass-rates are recorded — **meeting the thresholds is the Phase E gate, not a Phase C blocker**; Phase C's bar is "constructible + corpus runs + gaps documented."
- **Pre-flight:** Phases A+B merged. **Re-grep Trap 2** (`rg '"openai"' tests/`) and decide whether the sentinel must move (only if provider=="openai"). Confirm the exact provider SDK binding and credential mechanism (for Bedrock: the `anthropic` SDK Bedrock client name + `anthropic.`-prefixed model-id mapping + AWS creds chain). Read both existing `anthropic_client.py` as the structural template.
- **Verification:**
  - `uv run pytest -q` → green (new client unit tests + unchanged suite).
  - `uv run pytest tests/agents/intake/test_factory.py tests/data_agent_package/test_factory.py --no-cov` → green (sentinel handled).
  - `uv run mypy` → 0 errors (a `# type: ignore[import-untyped]` is acceptable if the provider SDK lacks stubs — document it).
  - `uv run pytest tests/test_data_agent_decoupling.py --no-cov` → green (the new wheel client imports only the wheel + its SDK; **no orchestrator import**).
  - `python -c "import model_project_constructor_data_agent.factory"` loads without importing the provider SDK (lazy-import invariant).
  - `<keys> uv run pytest -m live -q` (provider selected) → corpus runs; pass-rates recorded.
- **Session boundary:** one session. Close out. **Do not also parameterise the UI or run the cutover analysis.**

### Phase D — Parameterise the intake web UI

- **Work:** Thread `provider`/`model` through `ui/intake/app.py` `create_app` and `ui/intake/runner.py` so `_default_llm_factory` (`:62`) no longer hardcodes `"anthropic"` — read the provider/model from config/env/UI input and pass to `make_llm_client`. Preserve the injectable `llm_factory` test seam.

> ★ **As built (Session 163) — delivered; `runner.py` untouched + per-app (not per-session) selection, both deliberate.**
> **Selection is per-app (operator-level), not per-session form-driven.** `create_app` gains `provider`/`model` keyword args resolved by precedence — argument, then `INTAKE_LLM_PROVIDER`/`INTAKE_LLM_MODEL` env (mirroring the existing `INTAKE_DB_PATH` convention), then `DEFAULT_LLM_PROVIDER` (`anthropic`) for the provider and the provider's own default (`model=None`) for the model. This satisfies the DONE bar ("the UI can run any `KNOWN_PROVIDERS` member; default stays `anthropic` unless overridden") without a form field; a per-session picker (threading provider through `start_session` + the templates form + session state) is intentionally **not** built (FM #18 — the CLIs already expose `--provider`, and operator-level selection is the smaller, sufficient blast radius).
> **`runner.py` is untouched — deviation from the literal "thread through ... `runner.py`" wording.** `_default_llm_factory` is replaced by `_make_default_llm_factory(provider, model)`, an `LLMFactory` closure that captures provider/model once at app construction while the concrete client is still built **lazily, per session**, in `IntakeSessionStore._get_graph`. The store's `LLMFactory = Callable[[str], IntakeLLMClient]` seam already abstracts the provider, so threading provider/model into the store would leak the concept past its boundary; the closure binds them at the app layer instead. (Same meta-pattern as Phase C's thin-subclass call: the plan's literal touch-list over-specifies; ship the minimal honest expression that meets DONE and document the deviation.)
> **`model=None` default is deliberate** — it lets `make_llm_client` pick each provider's native default id, so the UI **avoids the cross-provider 400 gap** (a Bedrock-selected UI gets `anthropic.claude-sonnet-4-6`, never a bare first-party id). The `anthropic` path is observably unchanged (still Sonnet; the UI is not the pilot entrypoint, so Learning #20's Opus default is untouched).
> **Fail-fast + invariants:** an unknown provider raises `ValueError` (message identical to the factory's) at `create_app`, before any session; an injected `llm_factory` (the test seam) **bypasses resolution entirely**; `create_app` stays SDK-free (the closure defers the `make_llm_client` import), preserving `test_factory_import_does_not_load_anthropic`. **10 hermetic tests** (`tests/ui/intake/test_provider_selection.py`, monkeypatched `make_llm_client` recorder). Gates at delivery: **860 passed + 4 live skipped @ 97.41%**, mypy **0/66**, ruff clean, decoupling 2/2, lazy-import green. Adversarial verify `wf_77e637a3-5fb` (5 read-only lenses): **5/5 PASS, 0 blockers** (two test-coverage nits added). **Held scope:** no Phase E. Docs: `OPERATIONS.md` env-var table + `README.md` UI section.
- **What DONE looks like:** the UI can run any `KNOWN_PROVIDERS` member; the default remains `anthropic` unless overridden; the `llm_factory` injection point still works for tests.
- **Pre-flight:** Phases A–C merged. Read `ui/intake/app.py` and `ui/intake/runner.py` in full; trace how `create_app` → `runner` build the client.
- **Verification:** `uv run pytest tests/` (UI tests) → green; `uv run mypy`/`ruff` clean; manual: launch the UI with the provider overridden and confirm it constructs the second client (fake path acceptable if no keys).
- **Session boundary:** one session. Close out.

### Phase E — Shadow run + cutover gate

- **Work:** Run the candidate provider **side-by-side** with Anthropic on the Phase B golden corpus (same inputs, no production traffic); produce an **agreement report** (per-capability pass-rates, governance-label agreement, SQL-executability deltas) against the §3.4 thresholds. Define the cutover decision: **production cutover only if the candidate meets every threshold**; otherwise document the gaps and keep Anthropic primary. Keep the shadow run as a periodic regression after any cutover.
- **What DONE looks like:** a committed agreement report under `tests/eval/`; an explicit go/no-go against each threshold; if go, a documented cutover procedure (flip the default provider via the Phase A config); if no-go, a gap list.
- **Pre-flight:** Phases A–D merged; both providers runnable; keys available for both.
- **Verification:** the report reproduces from `pytest -m live` runs of both providers; every threshold has a measured number and a pass/fail; the recommendation follows the numbers (no cutover on an unmet threshold).
- **Session boundary:** one session. Close out. **The cutover itself (flipping the production default), if approved, is operator-gated and may be its own follow-up.**

> ★ **As built (Session 164) — delivered (harness + gate + report); live run deferred (no creds).**
> **Test-tree + docs only** (per §4.8 — no production code changed). The live tier (`test_eval_live.py`) is parametrized over `eval_cutover.SHADOW_PROVIDERS` (`anthropic` baseline + `bedrock` candidate) — one `pytest -m live` is the side-by-side **shadow run**; `conftest.py` skips each case when *its* provider's creds are absent (CI with no creds skips the whole tier; a Bedrock-only env runs only the Bedrock half). `model=None` is passed so each provider uses its native default id (sidesteps the cross-provider 400 gap).
> **The cutover gate is a new pure module** (`tests/eval/eval_cutover.py`; 18 deterministic tests). `evaluate_cutover` scores each provider against the eight §3.4 thresholds (single-sourced from `eval_thresholds`, drift-guarded) → per-threshold PASS/FAIL/PENDING + an overall GO/NO-GO/PENDING. The §5 "cutover only if the candidate meets *every* threshold" rule is encoded as **an unmeasured threshold cannot certify GO** — it resolves to PENDING → keep `anthropic` primary. Measurement (live tier) and gating (this module) are kept separate (mirroring `eval_scoring`), so the gate is fully verifiable with no creds.
> **The committed report is `tests/eval/PHASE_E_AGREEMENT_REPORT.md`** — current decision **NO-GO by default** (all thresholds PENDING, no creds), plus the runnable shadow-run procedure, the per-metric fill recipe, the cutover procedure, and the gap list.
> **Cutover-procedure correction (verified this session):** the DONE bar's "flip the default provider via the Phase A config" flips only the intake **web UI**; `scripts/run_pipeline.py` (`:459`) and data-agent `cli.py` (`:107`) **hardcode** `--provider` to `anthropic`, so a real cutover touches three entrypoints and must address the `run_pipeline` model-id gap. Documented in the report's cutover table.
> **`json_parse` is measured deterministically:** §3.4's oracle for it is the provider-parametrized `test_llm_json_parity.py` battery, **not** the live tier; the report/gate/README flag its different provenance (this was the one verify blocker — resolved by clarifying the source and the fill recipe; **no** live `json_parse` test added, faithful to §3.4's stated oracle).
> **Deferred (logged, not skipped):** the live shadow run itself — no `ANTHROPIC_API_KEY` / AWS creds this session (operator chose "defer" via `AskUserQuestion`). DONE bar met = committed report + explicit go/no-go logic + runnable procedure + gap list; the measured numbers + threshold calibration are the operational follow-up. Gates: **878 passed + 8 live skipped @ 97.41%**, mypy 0/66, ruff clean, C4 2/2. Adversarial verify `wf_f157b547-859` (5 read-only `Explore` lenses): **4/5 PASS + 1 blocker resolved**.

---

## 6. Do-not-change list

Explicitly preserved across all phases:

1. **The protocol seams** — `IntakeLLMClient` (4 methods) and `LLMClient` (5 + 1 optional). New providers *implement* them; the protocols don't change.
2. **The two error classes and their divergence** — `IntakeLLMError(RuntimeError)` / `LLMParseError(ValueError)`. Each new client raises its seam's class (pinned by `test_llm_json_parity.py:202-215`).
3. **C4 decoupling** — the data-agent wheel imports only the wheel + SDKs, never the orchestrator (`tests/test_data_agent_decoupling.py`). New wheel clients live in the wheel.
4. **The lazy-SDK-import-in-`__init__` convention** — keeps factory import SDK-free (`test_factory_import_does_not_load_*`). New branches follow it.
5. **CI hermeticity** — the four `ci.yml` jobs run offline with no API key. Live eval is `live`-marked and never gates CI.
6. **LangGraph topology, intake caps (`MAX_QUESTIONS=20`, `MAX_REVISIONS=3`), governance vocabularies, data-agent SQL/datasheet logic.** Provider-agnostic; untouched.
7. **The fenced-text `_extract_json` convention** for the first second-provider (Decision C). Native structured output is a separate decision (Q3).
8. **The website agent** — no LLM; nothing changes.

---

## 7. Open questions (for the operator / a future session)

1. **Which provider first?** §3.2 recommends AWS Bedrock-hosted Claude; the operator owns the compliance call (PII egress vs vendor diversity vs concentration). Phases A/B/D are provider-agnostic; only Phase C binds this.
2. **Is a real API key (and, for Bedrock, AWS credentials) available for the `live` eval tier?** If not, Phase B delivers the deterministic tier + corpus and defers the live baseline (logged, not skipped).
3. **Adopt native structured output (`output_config.format` / `response_format`) and retire `_extract_json`?** A quality/maintenance decision that rewrites the parity invariant — deferred to a follow-up after a second provider is proven (Decision C).
4. **Add production hardening (retry/back-off, rate-limit + exception mapping)?** The clients have none today (Trap 5). A second provider's SDK raises different native exceptions; the minimum (map parse/empty failures onto the seam error class) is in Phase C, but a uniform retry/rate-limit policy is a separate effort.
5. **Per-provider `max_tokens` and `temperature`?** Both clients hardcode `max_tokens=4096`; Claude Opus 4.7/4.8 reject `temperature` while other providers accept it. The eval (§3.4) handles non-determinism by sampling N times; a per-provider sampling policy may be wanted at cutover.

---

## 8. Risk register

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | A second provider parses fine but writes subtly worse SQL / mis-labels governance | **High** (the whole point) | The eval gate (§3.4, Phases B/E). No cutover on an unmet threshold. |
| 2 | `live` eval accidentally wired into CI, breaking hermeticity | Medium | The `live` marker + `pytest -m 'not live'` CI default; do-not-change item 5; Phase B verification asserts the four jobs pass with no key. |
| 3 | Adding `"openai"` breaks the Trap 2 sentinel tests | Medium (only if provider=="openai") | Phase C pre-flight re-greps and conditionally re-points the sentinel. Bedrock-first avoids it entirely. |
| 4 | A new wheel client accidentally imports the orchestrator (C4 violation) | Low | `tests/test_data_agent_decoupling.py` in every phase's verification; do-not-change item 3. |
| 5 | Prompt portability: Claude-tuned prompts degrade on a non-Claude provider | Medium–High (low for Bedrock-Claude) | §3.2 recommends Bedrock-Claude first (prompts transport); the eval measures degradation before cutover. |
| 6 | Executor trusts the hallucinated "langchain 1.x / stale pins" claim and rejects A on bad grounds | Low (flagged) | §3.1 correction box with verified installed versions; this risk is documented, not latent. |
| 7 | New provider SDK lacks type stubs → mypy fails | Medium | Phase C allows a documented `# type: ignore[import-untyped]`. |
| 8 | Lazy-import invariant broken (factory loads the SDK at import) | Low | Phase C verification asserts `import …factory` loads no SDK (`test_factory_import_does_not_load_*`). |
| 9 | Model-default reconciliation (Phase A) silently changes the model run in production | Medium | Phase A DONE requires the `anthropic` path to produce identical results; pin the canonical default and document it. |

---

## 9. Close-out protocol for each executor session

Each of the implementing sessions MUST:

1. **Phase 0** — read `SAFEGUARDS.md`, `SESSION_NOTES.md` ACTIVE TASK, **this plan's relevant §5 phase**, run `git status`/dashboard, ghost-check.
2. **Phase 1B** — write a Session-N stub to `SESSION_NOTES.md` before any code.
3. **Execute** — follow the phase's Work + Execution; **re-run the verification block at every checkpoint**; re-grep the inventory (§4) for line-number drift before editing.
4. **Phase 3A** — evaluate the previous session's handoff (Session 160 evaluates this plan; 161 evaluates 160's implementation; …).
5. **Phase 3B–3F** — self-assess, document learnings, write the next handoff, commit, report, STOP.
6. **Do NOT bundle two phases** (FM #18). Close out at the end of the phase even if time remains.
7. **CHANGELOG cadence (`PROJECT_CONVENTIONS.md` §2):** Phases A, C, D change shipped code → **earn a `CHANGELOG.md` entry**. Phase B is test-tree only (+ corpus) — by §2, adding/changing `tests/` test logic earns an entry; the executor judges (the corpus + harness are test logic, so likely yes). Phase E is a report (docs) → no entry. **This planning session (159) is docs-only → no entry.**

Each session's DONE criterion is its phase's verification block. Any verification command failing = not DONE; fix in the same session or roll back and re-plan.

---

## 10. Provenance

- **Motivation:** `docs/wiki/claims-model-starter/AI-Dependencies.md` (Session 157) §6.3 / §6.6 / §6.7.
- **Seam design intent:** the factory docstrings at `agents/intake/factory.py:6-9` and `data_agent/factory.py:6-9`; the prior LLM-client analysis in `docs/architecture-history/o2-shared-llm-json-plan.md` (Session 102).
- **House-style template:** `docs/architecture-history/github-gitlab-abstraction-plan.md` (Session 10).
- **Evidence:** Session-159 investigation — a read-only Workflow fan-out (`wf_3bfd79c0-fa7`: 4 investigation + 4 design agents) **plus direct verification** of every load-bearing claim (installed package versions; the Trap 2 sentinel; the model-default at `run_pipeline.py:440`; `_sanitize_prompt_field`'s purpose; CI hermeticity; the `__init__` re-export). The investigation's hallucinated "langchain 1.x / stale pins" claim was caught and corrected (§3.1 box). Authoritative Claude/Anthropic facts (model IDs, Bedrock client + `anthropic.`-prefixed IDs, native structured-output APIs) from the `claude-api` reference, not from memory.
- **Baseline:** `517d35b`. Verified installed deps: `langgraph 0.2.76`, `langchain-core 0.3.84`, `anthropic 0.94.1`, `langgraph-checkpoint-sqlite 2.0.11`; `litellm`/`openai`/`langchain-anthropic`/`langchain-openai` not installed.

---

## 11. Why this is one document, not five

The strategic decisions (§3), the do-not-change list (§6), the eval thresholds (§3.4), and the grep inventory (§4) are cross-phase invariants every executor needs. Splitting them across five phase docs would duplicate the load-bearing sections or require cross-document references. Executors read this plan + their phase section per session; the plan is long but navigable by §number. If a later session finds the single-document structure unwieldy, the first executor may split it — not a blocking concern for Session 159.

---

*End of plan.*
