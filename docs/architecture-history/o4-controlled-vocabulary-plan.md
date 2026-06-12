> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# O4 — Controlled-Vocabulary Single-Source: Producer-Prose Derivation Plan

> **Status:** Draft for executor review (Session 123, planning/architecture workstream). The plan is the deliverable; implementation is separate sessions.
> **Author:** Session 123 — 2026-06-07 (HEAD `a8ff836`).
> **Implements:** Audit `docs/audits/2026-06-01-technical-debt-audit.md` — E2 (`:121-127`), Overhaul **O4** (`:175`); table findings **#14 / #27 / #24** (model-type / counterfactual-design + review-cadence / row-count-order + measurement-unit).
> **Predecessors (all COMPLETE — the live-drift prerequisites the audit `:175` requires):** #19 (UI question-cap lie, S104/105), #39 (regulatory-framework drift + the `GOVERNANCE_FRAMEWORKS` producer-single-source pattern, S108/109), #2 (`_TIER_SEVERITY`/`_CYCLE_CADENCE` consumer-dict guards, S113), #8→**O3** (`REPO_PLATFORMS`, S116–118). O1/O2/O3 establish the plan-first + `_vocab_guard` pattern this plan reuses.
> **Decision (Session 123, evidence inventory §3 + 13-agent fan-out §12):** **Single-source each LLM prompt's enumeration by deriving it from its canonical `Literal` via `", ".join(get_args(...))`** (the audit's "derive prompts via `get_args`" half). **Decline** the audit's "move all enums to `common.py`" half — it is *orthogonal* to single-sourcing, *cosmetic* for the intake Literals, and *forbidden* for the data-agent Literals (the standalone-wheel decoupling boundary, §1.4). **Exclude `measurement_unit`** — it is genuinely free-form, not a controlled vocabulary (§1.5).
> **Out of scope (say it twice):** moving any `Literal` to a new home; tightening `measurement_unit` to a closed set; the consumer `dict.get` fallback values are minor hygiene (NOT correctness bugs — §1.6), addressed only as opt-in alignment. See §11.

---

## 1. Context

### 1.1 What O4 is

Audit E2 (`docs/audits/2026-06-01-technical-debt-audit.md:121-127`):

> *The same enums exist three times — as prompt prose (producer), as Pydantic `Literal` (validator), and as `dict.get()` fallbacks (consumer) — with nothing linking them… `#14`/`#27`/`#24`: model-type / counterfactual-design / review-cadence / row-count-order / measurement-unit vocabularies are all prose-in-prompt + `Literal`-in-schema with no shared constant.*
> **Recommendation:** promote each vocabulary to a named `Literal` in `schemas/v1/common.py`, type the fields against it, and **derive the prompt's enumerations from `typing.get_args(...)`**. Add import-time `assert set(dict.keys()) == set(get_args(Literal))` guards so drift fails loudly.

O4 closes the **producer surface** of every controlled vocabulary: the LLM prompts that hand-list a vocabulary's members as prose, with nothing tying the prose to the schema `Literal` the response is validated against. When a member is added to the `Literal`, the prompt still offers the old set — a **silent capability gap** (the model is never told the new option exists). #39 already proved this is real (a prompted-but-unmapped framework silently produced zero artifacts); O4 generalizes the fix #39 pioneered to the rest of the prompt enumerations.

### 1.2 Why this is an architecture decision, not a quick win

The validator surface is already clean: members are named `Literal`s (`common.py:23/25/32`, `intake.py:31/48/62`, data-agent `schemas.py:96`), and Pydantic rejects non-members at parse time (`test_invalid_*_rejected` tests, §3.6). The consumer surface was hardened in #2/#39 (the `_TIER_SEVERITY`/`_CYCLE_CADENCE`/`_FRAMEWORK_ARTIFACTS` dicts are guarded against their `Literal`s, `governance_templates.py:98-99` + `test_governance.py:588/:598`). What is **not** linked is the **producer**: seven prompt-prose enumerations re-list a `Literal`'s members by hand (§3.1), and the `regulatory_frameworks` case (#39) was *already a live correctness defect* before it was fixed. This is the same "selection/vocabulary is hardcoded across files with no single source" root cause the audit names for O1/O3 (§8.1) — an extensibility/correctness overhaul, not a localized cleanup, because:

1. **The harm is silent and roadmap-aligned.** The governance-matrix + value-measurement features (ROADMAP) will add `Literal` members. Each addition that doesn't also hand-edit every prompt is a silently-degraded capability — exactly #39, which the audit flags as "correctness-adjacent for a P&C compliance tool."
2. **It is cross-package.** Two of the five named vocabularies live in the data-agent standalone wheel (§1.4); the fix must respect a decoupling boundary that an AST test enforces — not a mechanical find/replace.
3. **The audit's own prescription is partly wrong.** "Move all enums to `common.py`" is forbidden for the cross-package vocabularies and cosmetic for the intake ones (§1.3). Distinguishing *single-sourcing* (the win) from *home location* (orthogonal) is the load-bearing reframe — a design call, not a typing pass.

### 1.3 The reframe — **single-sourcing ≠ relocation; derivation > guard**

**This is the load-bearing finding of this plan.** The audit conflates two independent things:

| Concern | What it means | O4's stance |
|---|---|---|
| **Single-sourcing** | the producer prose *derives* from the canonical `Literal` so it cannot drift | **the actual O4 win** — do it for every controlled prompt enumeration |
| **Home location** | *which module* the `Literal` physically lives in (`common.py` vs inline vs data-agent) | **orthogonal** — does not affect single-sourcing; do not move Literals |

A prompt enumeration built as `", ".join(get_args(ModelType))` is single-sourced **regardless of where `ModelType` lives** — `get_args` reads the members wherever they are. So the audit's "promote to `common.py`" step is neither necessary nor sufficient for the goal; it is a separable cosmetic refactor that (a) for the intake Literals adds churn for vocabularies used by exactly one schema family, and (b) for the data-agent Literals is **forbidden** (§1.4).

**Derivation beats the guarded-tuple pattern when a `Literal` exists.** #39 introduced a *separate producer tuple* (`GOVERNANCE_FRAMEWORKS`, `anthropic_client.py:113-119`) joined into the prompt (`:126`) and a parity *test* (`test_governance.py:541`) — because `regulatory_frameworks` is a bare `list[str]` with **no** `Literal` to derive from. Every O4 vocabulary **already has a `Literal`**, so the cleaner single source is the `Literal` itself: `", ".join(get_args(TheLiteral))`. This makes drift *structurally impossible* (the prose is computed from the members), which is strictly stronger than a tuple + guard that merely *catches* drift. The remaining test obligation is a regression pin that the prose stays derived (member-presence, §6.3), not a parity reconciliation.

### 1.4 The cross-package wall — why two of the five can't go to `common.py`

The data agent is a **standalone wheel** with a decoupling boundary (`tests/test_data_agent_decoupling.py:26-30`, architecture-plan §7). **Be precise about what is *test-enforced* vs *architectural*:** the AST test walks `packages/data-agent/` + the `src/.../agents/data/` shim and fails only on three forbidden import substrings — `IntakeReport`, `schemas.v1.intake`, `intake_report`. The *intent* (architecture-plan §7) is broader: the wheel `pip install`s and runs with **zero** main-package dependency. So the test catches intake-schema coupling specifically, while the "no main import at all" invariant is an architectural convention the test only **partially** guards (an `import model_project_constructor.orchestrator`, say, would pass the test yet break standalone distribution — §9). Import directions (verified §12):

```
✓ main → data-agent        (main re-exports data-agent schemas via schemas/v1/data.py:16-28)
✓ data-agent (internal)    (imports within packages/data-agent/ itself)
✗ data-agent → main        FORBIDDEN (AST test; covers schemas + domain objects)
```

Consequences for O4:

- `expected_row_count_order` and `measurement_unit` live in `packages/data-agent/.../schemas.py` and **cannot** be promoted to the main `common.py` — that would require either the wheel importing the main package (forbidden) or the main package owning a data-agent concept (inverts the dependency). They single-source **within the wheel**: their producer prose (data-agent `anthropic_client.py`) derives from the data-agent `Literal` (data-agent `schemas.py`) — both inside `packages/data-agent/`, no boundary crossing.
- The drift-guard primitive `assert_vocab_parity` (and the §6.1 `join_members` helper) live in the **main** package (`_vocab_guard.py`). The wheel must **not** import them — and **note the AST test would NOT catch such an import** (`_vocab_guard` is not among its three forbidden substrings), so the prohibition rests on the standalone-wheel invariant, not the test. If a belt-and-suspenders guard is wanted for the data-agent vocabulary, **copy** the 30-line pure-`typing` primitive into the wheel (the documented twin-copy pattern, cf. O2's twin `_extract_json`); do **not** import it from main. But derivation (§1.3) makes a guard largely redundant here; prefer derivation + a member-presence prompt test inside the wheel (§7.2).

### 1.5 `measurement_unit` is free-form — not an O4 target

The audit groups `measurement_unit` under #24, but the evidence (§3.5, verified §12) shows it is **genuinely open-ended**:

- Schema: `BaselineSnapshot.measurement_unit: str` — a **bare `str`**, no `Literal` (`packages/data-agent/.../schemas.py:105`).
- Prompt: `'"measurement_unit" (one of "percent", "USD", "count", "ratio", "days", **or another short free-form unit string**)'` (`packages/data-agent/.../anthropic_client.py:292-294`) — the "or another …" clause makes the set explicitly **open**.
- Docstring: `llm.py:75` — *"`measurement_unit` is free-form prose echoed onto the `BaselineSnapshot`."*

There is no closed member set to single-source. Tightening it to a `Literal` would be a **behavior-restricting** change (domain units are unbounded — "claims", "policies", "basis points", …) and is rejected (§5 option D). **O4 excludes `measurement_unit`.** The plan documents this so a future reader does not "complete" the audit by force-fitting a `Literal`. (The prompt's slightly misleading "one of …" phrasing is a cosmetic wording nit, not O4.)

### 1.6 The consumer fallbacks are hygiene, not correctness bugs

The inventory found two `dict.get` fallbacks that are **not** members of their `Literal` (§3.3): `expected_row_count_order` → `"unknown"` (`templates.py:674`) and `review_cadence` → `""` (`governance_templates.py:329`, vs `templates.py:565` → `"ad_hoc"`). Unlike #39 (a prompted member silently mapping to zero artifacts), these are **not** silent correctness defects:

- `expected_row_count_order` is a **required** field of `PrimaryQuery` (`Literal`, no default) — a validly-serialized `DataReport` always carries a member; the `"unknown"` fallback only renders on malformed/partial input.
- `review_cadence` is **Optional** (`null` allowed); `governance_templates.py:329` uses `""` as an "absent" sentinel inside `if review_cadence:` (omit the note), while `templates.py:565` defaults absent → `"ad_hoc"` (render a default). Both handle "absent" safely; the inconsistency is a UX nit.

O4 treats fallback alignment as **opt-in** (§7, decision Q5), not a correctness deliverable — being honest that the producer drift is the real harm (Learning #82).

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **Controlled vocabulary** | A fixed member set carried by a Pydantic `Literal` (the validator), referenced in a prompt (the producer) and consumed via `dict.get` (the consumer). |
| **Producer prose** | The LLM-prompt text that enumerates a vocabulary's members so the model emits a valid value (e.g. `"model_type [one of supervised_classification, …]"`). O4's subject. |
| **Validator** | The Pydantic `Literal` that rejects non-members at parse time. Already clean; O4 does not change member sets. |
| **Consumer** | A `dict.get(key, fallback)` site in a website renderer reading a deserialized payload. Hygiene only (§1.6). |
| **Single-sourcing** | The producer prose is *derived* from the validator `Literal` (`", ".join(get_args(L))`) so the two cannot drift. The O4 goal. |
| **`get_args(L)`** | `typing.get_args` returns a `Literal`'s members in **definition order** — the same order the current prose lists them, so a derived join is byte-identical to today's text. |
| **Loose twin** | A second, deliberately-untyped copy of a field (data-agent `llm.py:43/82`, the LLM-intermediate `str` shapes). Intentional; not a drift target. |
| **The wheel** | The `packages/data-agent/` standalone package + its `src/.../agents/data/` shim, decoupled from the main package by an AST test (§1.4). |
| **`assert_vocab_parity`** | The shared, dependency-free import-time `raise` guard (`_vocab_guard.py:25-52`); pins a runtime member set to a `Literal`. Lives in the **main** package (do not import from the wheel). |
| **#39 pattern** | Producer single-source via a tuple + `", ".join(...)` + a parity test (`GOVERNANCE_FRAMEWORKS`). O4 supersedes it with `get_args`-derivation where a `Literal` exists (§1.3). |

---

## 3. Evidence Inventory (grep-based — MANDATORY for a refactor plan)

All sites below were produced by **direct `grep`/read against the working tree at HEAD `a8ff836`** (Session 123) and cross-checked by a 13-agent inventory+adversarial-verify fan-out (§12). **The executor MUST re-run §13 in their Phase 0** — symbols drift (Learnings #19/#28). One **per-surface** subsection (Learning #8: producer, validator, consumer, twin are different greps). Line numbers were adversarially re-verified; multi-line prompt strings are cited at their first line.

### 3.1 Producer prose — **7 hand-listed `Literal` enumerations across 2 files** (the O4 target)

| # | Vocabulary | `Literal` (validator) | Prompt-prose site | In audit? |
|---|---|---|---|---|
| 1 | `model_type` | `ModelType` (`common.py:32`, 7) | `agents/intake/anthropic_client.py:182` (`draft_report` JSON-shape) | **#14** |
| 2 | `confidence` | `Literal` (`intake.py:31`, low/medium/high) | `agents/intake/anthropic_client.py:188` (`draft_report`) | adjacent |
| 3 | `counterfactual_design` | `Literal` (`intake.py:48`, 7) | `agents/intake/anthropic_client.py:200-202` (`draft_report`; field label on `:199`) | **#27** |
| 4 | `review_cadence` | `Literal` (`intake.py:62`, 4) | `agents/intake/anthropic_client.py:206-207` (`draft_report`) | **#24** |
| 5 | `cycle_time` | `CycleTime` (`common.py:23`, 4) | `agents/intake/anthropic_client.py:123` (`SYSTEM_GOVERNANCE`, `∈ {…}`) | adjacent (#2 consumer done) |
| 6 | `risk_tier` | `RiskTier` (`common.py:25`, 4) | `agents/intake/anthropic_client.py:124` (`SYSTEM_GOVERNANCE`, `∈ {…}`) | adjacent (#2 consumer done) |
| 7 | `expected_row_count_order` | `Literal` (data-agent `schemas.py:96`, 4) | data-agent `anthropic_client.py:140`; data-agent `llm.py:30-31` (docstring) | **#24** (cross-package) |

> **Reframe in numbers:** the audit named 4 (#1,#3,#4,#7); reading the prompts found **3 more of the identical drift class** (#2,#5,#6) — `confidence`, `cycle_time`, `risk_tier` are `Literal`s whose members are hand-listed in the same two prompts. #2 guarded their *consumer dicts* but **not** the *producer prose*. Fixing #1's prose while leaving #5/#6's hand-listed in the very same `anthropic_client.py` is arbitrary; the complete principle ("derive every prompt enumeration from its `Literal`") is the recommended scope (§4, Q1).

The intake enumerations #1–#4 are embedded **mid-sentence inside one contiguous `draft_report` JSON-shape string** (`anthropic_client.py:~180-210`, implicit-concatenation literals) — **4 splice points in one string**, unlike #39's single clean `+ ", ".join(...)` insert into `SYSTEM_GOVERNANCE`. #5/#6 are the cleaner `SYSTEM_GOVERNANCE` `∈ {…}` form. This shapes the O4-1 diff.

### 3.2 Validators — **already clean; member sets are NOT changed by O4**

| Vocabulary | Site | Members |
|---|---|---|
| `ModelType` | `schemas/v1/common.py:32` (exported `__init__.py`) | supervised_classification, supervised_regression, unsupervised_clustering, unsupervised_anomaly, time_series, reinforcement, other |
| `confidence` | `schemas/v1/intake.py:31` (inline, `EstimatedValue`) | low, medium, high |
| `counterfactual_design` | `schemas/v1/intake.py:48-56` (inline, `ValueMeasurementPlan`) | champion_challenger, ab_test, geographic_split, historical_baseline_with_detrending, synthetic_control, regression_discontinuity, none_declared |
| `review_cadence` | `schemas/v1/intake.py:62` (inline, `ValueMeasurementPlan`) | weekly, monthly, quarterly, ad_hoc |
| `CycleTime` | `schemas/v1/common.py:23` | strategic, tactical, operational, continuous |
| `RiskTier` | `schemas/v1/common.py:25` | tier_1_critical, tier_2_high, tier_3_moderate, tier_4_low |
| `expected_row_count_order` | data-agent `schemas.py:96` (inline, `PrimaryQuery`) | tens, hundreds, thousands, millions |
| `measurement_unit` | data-agent `schemas.py:105` (`BaselineSnapshot`) | **bare `str` — no `Literal`** (§1.5, excluded) |

### 3.3 Consumers — `dict.get` fallbacks (hygiene only, §1.6)

| Vocabulary | Consumer site(s) | Fallback | Member? |
|---|---|---|---|
| `model_type` | `governance_templates.py:207,232`; `templates.py:103,250,452,705` | `"other"` | ✅ yes (6 sites, all safe) |
| `model_type` | `orchestrator/adapters.py:64-65` (`if model_type == "time_series"`) | n/a (reads typed field) | magic-string branch (note, §11) |
| `counterfactual_design` | `templates.py:555` | `"none_declared"` | ✅ yes |
| `review_cadence` | `templates.py:565` | `"ad_hoc"` | ✅ yes |
| `review_cadence` | `governance_templates.py:329` | `""` | ⚠ no (absent-sentinel, safe — §1.6) |
| `expected_row_count_order` | `templates.py:674` | `"unknown"` | ⚠ no (defensive — field is required, §1.6) |
| `measurement_unit` | `templates.py:488`; data-agent `nodes.py:197` | `""` / `"unknown"` | n/a (free-form) |

### 3.4 Loose twins — **intentional, NOT drift targets**

| Field | Twin site | Form | Why it exists |
|---|---|---|---|
| `expected_row_count_order` | data-agent `llm.py:43` | bare `str` in `PrimaryQuerySpec` | LLM-intermediate shape before Pydantic validation |
| `measurement_unit` | data-agent `llm.py:82` | bare `str` in `BaselineQuerySpec` | same; field is free-form anyway (§1.5) |

These are the unvalidated LLM-output dataclasses; the validated `Literal` is the schema. O4 does **not** type the twins (that would couple the intermediate to the schema for no gain).

### 3.5 `measurement_unit` — the excluded case (verified, §1.5)

Schema bare `str` (`schemas.py:105`) + open-ended prompt ("…or another short free-form unit string", `anthropic_client.py:292-294`) + free-form docstring (`llm.py:75`). **Not a controlled vocabulary; excluded from O4.**

### 3.6 Reuse targets & test blast radius (gates every phase)

**Precedents to reuse (do not reinvent):**
- `assert_vocab_parity` (`_vocab_guard.py:25-52`, pure `typing`, `raise`-based → survives `-O`).
- #39 producer single-source: `GOVERNANCE_FRAMEWORKS` tuple (`anthropic_client.py:113-119`) → `", ".join(...)` (`:126`) → parity test `test_prompt_framework_set_equals_artifact_map_keys` (`test_governance.py:541`).
- #2 consumer guards: `_TIER_SEVERITY`/`_CYCLE_CADENCE` (`governance_templates.py:64-69/86-91`) pinned at `:98-99`; `get_args` parity tests `test_tier_severity_matches_risk_tier_literal` (`test_governance.py:588`) + `test_cycle_cadence_matches_cycle_time_literal` (`:598`).

**Tests that gate O4 (must stay green; the safety net for a prose-deriving change):**
- **Validators (unit):** `tests/schemas/test_intake.py` (`test_invalid_model_type_rejected:51`, `test_invalid_counterfactual_design_rejected:131`, `test_invalid_review_cadence_rejected:135`, happy-path member asserts `:28/:118/:119`); `tests/schemas/test_data.py` (`test_invalid_row_count_order_rejected:95-97` — rejects `"billions"`).
- **Producer (prompt pins — substring, NOT full-byte):** `tests/agents/intake/test_anthropic_client.py` (`SYSTEM_INTERVIEWER`/`SYSTEM_GOVERNANCE` substring pins `:350-435`, incl. `:429` "emits regulatory labels (cycle_time, risk_tier)"); data-agent `tests/data_agent_package/test_anthropic_client.py` (`expected_row_count_order` parse `:120/:143`).
- **Round-trip/integration:** `tests/agents/intake/test_graph.py:44/54`; data-agent `tests/agents/data/test_data_agent.py`.
- **Consumer render (byte-pinned markdown):** `tests/agents/website/test_templates.py` (`model_type` `:89-95`, `counterfactual` `:210`, baseline `measurement_unit` `:205/:241`).
- **Fixtures (default members):** `tests/schemas/fixtures.py:38/79/93/111/202`.
- **Decoupling:** `tests/test_data_agent_decoupling.py` (O4-2 must keep it green — §1.4).

> **Substring pins, not byte pins:** the prompt tests assert *substrings* (e.g. a member appears), so deriving the enumeration via `", ".join(get_args(L))` — which reproduces the current definition-order text byte-for-byte — keeps them green. The executor should **add** a member-presence assertion per vocabulary (§6.3) so a future hardcode-revert fails the build.

---

## 4. Decision

**Adopt the producer-prose `get_args`-derivation approach, COMPLETE scope, Literals left in place.** Specifically:

1. **Derive** every controlled prompt enumeration from its canonical `Literal` via `", ".join(get_args(L))` (or the data-agent-local equivalent inside the wheel), so the producer cannot drift from the validator. This is the audit's "derive prompts via `get_args`" half (`:127`), and supersedes #39's tuple+guard where a `Literal` exists (§1.3).
2. **Scope = complete (7 enumerations):** the 4 audit-named (`model_type`, `counterfactual_design`, `review_cadence`, `expected_row_count_order`) **plus** the 3 same-class adjacents found in the same prompts (`confidence`, `cycle_time`, `risk_tier`). Leaving the latter hand-listed in the very file O4 edits is arbitrary (§3.1, Q1).
3. **Do NOT relocate any `Literal`** — single-sourcing is independent of home (§1.3); the cross-package ones cannot move (§1.4); the intake ones moving to `common.py` is cosmetic churn (Q2).
4. **Exclude `measurement_unit`** — free-form, not controlled (§1.5).
5. **Consumer fallbacks** = opt-in alignment, not a correctness deliverable (§1.6, Q5).

Rationale:

1. **It targets the actual harm.** The producer drift is the *only* live, silent, roadmap-aligned defect class left in the vocabularies (#39 was its first casualty). The validator and consumer surfaces are already guarded (#2/#39).
2. **The single source becomes real, not advisory.** A derived prompt cannot drift from the `Literal`; this is *stronger* than #39's catch-it-after guard (§1.3). The deletion test (Ousterhout, `ARCHITECTURE_WORKSTREAM.md`): the 7 hand-typed member lists are **deleted into** `get_args` reads — they do not move elsewhere.
3. **It respects the wheel.** The data-agent vocabulary single-sources *inside* `packages/data-agent/` (§1.4); no import inversion, decoupling test stays green.
4. **It is honest about scope.** `measurement_unit` is excluded (not force-`Literal`'d); consumer fallbacks are flagged as hygiene, not inflated to bugs (Learning #82).
5. **Each phase is independently shippable** and bounded against the astronaut/resume anti-patterns: O4-1 (intake prompts) ships alone; O4-2 (data-agent + consumer hygiene) ships alone.

---

## 5. Alternatives Considered

| Option | What it does | Verdict |
|---|---|---|
| **B — `get_args`-derivation, complete scope, Literals in place** | derive all 7 prompt enumerations; no relocation; exclude `measurement_unit` | **CHOSEN** |
| A — minimal (only the 4 audit-named) | derive `model_type`/`counterfactual`/`review_cadence`/`row_count_order` only | **Rejected** — leaves `confidence`/`cycle_time`/`risk_tier` hand-listed *in the same prompts O4 edits*, same drift class; arbitrary subset. (Available as a reduced scope if the operator prefers — Q1.) |
| C — complete + relocate all intake Literals to `common.py` | also move `confidence`/`counterfactual_design`/`review_cadence` to `common.py` | **Rejected** — orthogonal to single-sourcing (§1.3); churn across schema+test+import for vocabularies used by one schema family; forbidden for the data-agent pair (§1.4). |
| D — tighten `measurement_unit` to a `Literal` | close the free-form unit set | **Rejected** — behavior-restricting; domain units are unbounded (§1.5). |
| E — producer tuple + parity guard (the #39 pattern) instead of `get_args` | add a `*_MEMBERS` tuple per vocab + a guard test | **Rejected when a `Literal` exists** — derivation *prevents* drift; a parallel tuple *re-introduces* a second copy to keep in sync. The #39 pattern is correct only where there is no `Literal` (n/a here). |
| F — do nothing | keep the 7 hand-listed prompts | **Rejected** — but note the audit's framing ("none of the overhauls are urgent"); this is right-sized, not urgent. Each phase is a strict improvement. |

**Re-open trigger:** adding a member to any controlled `Literal` (a governance-matrix / value-measurement roadmap item) is exactly when an *underived* prompt silently fails to offer it — the moment O4's value is realized. Until then, the binary forms work.

---

## 6. Interface / Target Design

### 6.1 The derivation helper (one tiny shared formatter)

`get_args` returns a `tuple`; the prompts want a human-readable comma list. Introduce **one** trivial formatter rather than scattering `", ".join(get_args(...))` (and to centralize the "or null" / brace-vs-bracket styling):

```python
# src/model_project_constructor/_vocab_guard.py  (beside assert_vocab_parity — same dependency-free home)
def literal_members(literal: Any) -> tuple[str, ...]:
    """The members of a Literal, in definition order (a thin, typed get_args)."""
    return tuple(str(m) for m in get_args(literal))

def join_members(literal: Any, *, sep: str = ", ") -> str:
    """Comma-joined members for prompt prose, e.g. 'a, b, c'."""
    return sep.join(literal_members(literal))
```

- **Home:** `_vocab_guard.py` (main package) — it already owns `get_args` usage and is dependency-free. The intake prompts (main package) import it freely. These two functions are **additive**; `assert_vocab_parity` is untouched. **O4's derivation path does NOT call a parity guard** — deriving the prose *prevents* drift, so there is nothing to reconcile (the guard remains relevant only as the precedent and the optional in-wheel belt-and-suspenders, §6.4/Q4).
- **The wheel:** must **not** import this (§1.4). The data-agent prompt derives via its own local `", ".join(get_args(...))` (or a copied two-line helper inside `packages/data-agent/`). Keep it inline/local in O4-2; do not share across the boundary.
- **Byte-identity:** `get_args(ModelType)` → definition order → `"supervised_classification, supervised_regression, …"`, identical to the current prose. The rendered prompt is unchanged; only its *construction* changes (literal → derived).

### 6.2 Before → after (intake `SYSTEM_GOVERNANCE`, the clean case)

```diff
+ from model_project_constructor._vocab_guard import join_members
+ from model_project_constructor.schemas.v1.common import CycleTime, RiskTier
  SYSTEM_GOVERNANCE = (
      "You classify model projects against an internal governance matrix. "
-     "cycle_time ∈ {strategic, tactical, operational, continuous}. "
-     "risk_tier ∈ {tier_1_critical, tier_2_high, tier_3_moderate, tier_4_low}. "
+     f"cycle_time ∈ {{{join_members(CycleTime)}}}. "
+     f"risk_tier ∈ {{{join_members(RiskTier)}}}. "
      "Regulatory frameworks include " + ", ".join(GOVERNANCE_FRAMEWORKS) + ". …"
  )
```

The `draft_report` enumerations (#1–#4) are the **harder** case: 4 splice points inside one big implicit-concatenation string. Convert the affected fragments to f-strings interpolating `join_members(...)`, preserving the surrounding `"[one of … , or null]"` framing (the "or null" reflects an Optional field and stays literal). Mind that `ModelType` is imported from `common.py` while `confidence`/`counterfactual_design`/`review_cadence` are inline in `intake.py` — import them where the prompt builder lives.

> **⚠ Byte-identity is per-site: `get_args` fixes the *members and order*, but each prompt keeps its own *separator* and *decoration*.** `get_args` guarantees the right members in definition order — but a single `", ".join` does **not** reproduce every site verbatim. Match each:
>
> | Site(s) | Separator | Decoration | Derivation |
> |---|---|---|---|
> | `model_type`, `counterfactual_design`, `review_cadence` | `, ` | `[one of … , or null]` | `join_members(L)` |
> | **`confidence`** | **`/`** (current prose is `low/medium/high`, *no commas*) | `[one of …]` | `join_members(confidence_lit, sep="/")` |
> | `cycle_time`, `risk_tier` | `, ` | `∈ {…}` (braces) | `f"… {{{join_members(L)}}} …"` |
> | `expected_row_count_order` (O4-2, in-wheel) | `, ` | `(one of "x", "y", …)` — **members are double-quoted** | local `'"' + '", "'.join(get_args(L)) + '"'` (the wheel cannot import `join_members` — §1.4) |
>
> A naive `", ".join` would silently turn `confidence`'s slashes into commas and drop the data-agent quotes — changing the rendered prompt and breaking the substring pins (`test_anthropic_client.py:350-435`). The member-presence tests (§6.3) only check membership, **not** separators, so the executor must eyeball each rendered fragment (or pin the exact decoration) before declaring byte-identity.

### 6.3 The regression pin (per vocabulary)

Derivation makes drift impossible, but a future edit could re-hardcode. Pin each with a cheap member-presence test (the safety net, not a parity reconciliation):

```python
# tests/agents/intake/test_anthropic_client.py  (extend the existing prompt-pin block)
from typing import get_args
def test_prompt_enumerates_all_model_types():
    for m in get_args(ModelType):
        assert m in SYSTEM_INTAKE_CLASSIFICATION_or_draft_report_prompt   # the actual prompt constant/string
```

One such test per vocabulary (or one parametrized test over `(Literal, prompt)` pairs). **Non-vacuity:** mutate the prompt to drop a member → the test goes RED (prove it, per Learning #89: one discriminating assertion per derived site). For the data-agent vocabulary the equivalent test lives **inside the wheel** (`packages/data-agent/tests/`), deriving from the data-agent `Literal`.

### 6.4 Cross-package guard strategy (O4-2)

`expected_row_count_order`'s producer (`anthropic_client.py:140`) and validator (`schemas.py:96`) are **both in the wheel** → derive the prompt from the wheel's own `Literal`; no main import, no boundary issue. A standalone `assert_vocab_parity`-style guard is **optional** and, if wanted, must be a **copy** inside `packages/data-agent/` (never an import from main, §1.4). **Recommended:** derivation + the in-wheel member-presence test (§6.3); skip the copied guard (YAGNI — derivation already prevents drift). Decision Q4.

### 6.5 Open contract questions for Phase 1A (Learning #40 — resolve before code)

- **Q1 (scope):** complete-7 (recommended) vs minimal-4 (audit-literal).
- **Q2 (intake Literal home):** leave inline (recommended) vs promote `confidence`/`counterfactual_design`/`review_cadence` to `common.py` (cosmetic).
- **Q3 (`measurement_unit`):** exclude as free-form (recommended) vs tighten to `Literal`+escape (rejected, §5-D).
- **Q4 (data-agent guard):** derivation + in-wheel member-presence test (recommended) vs also copy a parity guard into the wheel.
- **Q5 (consumer fallbacks):** leave defensive + document (recommended) vs align `templates.py:674` `"unknown"`→a member and `governance_templates.py:329` `""`→`"ad_hoc"`.

---

## 7. Implementation Plan (per-phase)

**Two phases, one session each** (+ this planning session). Each leaves the tree green and is independently shippable. **Do NOT bundle phases** (FM #18). **ZERO change to any `Literal` member set** — O4 only changes how prompts are *constructed*, so rendered prompts and validation behavior are byte-/behavior-identical (the prompt pins prove it).

### 7.1 Phase O4-1 — Single-source the intake producer prose (main package)

- **Goal:** the 6 intake prompt enumerations (`SYSTEM_GOVERNANCE`: `cycle_time`, `risk_tier`; `draft_report`: `model_type`, `confidence`, `counterfactual_design`, `review_cadence`) derive from their `Literal`s. No member-set change; rendered prompts byte-identical.
- **Why first:** all main-package, no decoupling concerns; lands the `_vocab_guard.join_members` helper the data-agent phase mirrors.
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `src/model_project_constructor/_vocab_guard.py` | add `literal_members` + `join_members` (§6.1); export in `__all__` | +10 |
| `agents/intake/anthropic_client.py` | import the helper + the 6 `Literal`s; replace the 6 hand-listed enumerations (`:123,124,182,188,200-202,206-207`) with `join_members(...)` (f-string fragments; keep each site's separator + decoration per §6.2 — esp. **`confidence` uses `sep="/"`**, and the `∈ {…}`/`[one of …, or null]` framing stays literal) | ~20 |
| `tests/agents/intake/test_anthropic_client.py` | +1 parametrized member-presence test over the 6 `(Literal, prompt)` pairs (§6.3), mutation-proven | +25 |
| `tests/test_vocab_guard.py` (new, or extend) | unit-test `literal_members`/`join_members` (order + join) | +15 |

- **(Optional, Q5):** align `governance_templates.py:329` `""`→`"ad_hoc"` (+ update the byte-pinned render test).
- **What DONE looks like:** (1) zero hand-listed members for the 6 vocabularies in `anthropic_client.py` (grep, §13); (2) each prompt still contains every `Literal` member (new test green); (3) dropping a member from any prompt fragment → the new test RED (non-vacuity proven); (4) the existing `SYSTEM_GOVERNANCE`/`SYSTEM_INTERVIEWER` substring pins still green (byte-identity); (5) full suite + mypy + ruff green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor
PY=.venv/bin/python   # 3.13.5 — NOT bare python (3.10 → UTC ImportError)
# (a) no hand-listed enumerations remain for the 6 intake vocabularies:
grep -nE 'one of supervised_classification|∈ \{strategic|∈ \{tier_1|one of low/medium/high|one of champion_challenger|one of weekly, monthly' \
  src/model_project_constructor/agents/intake/anthropic_client.py    # expect ZERO
# (b) the new member-presence + helper tests (subset → --no-cov, §10):
$PY -m pytest tests/agents/intake/test_anthropic_client.py tests/test_vocab_guard.py -q --no-cov
# (c) existing prompt pins survive (byte-identity):
$PY -m pytest tests/agents/intake/ -q --no-cov
# (d) full suite (coverage gate is FULL-suite only, §10) + types + lint:
$PY -m pytest -q && $PY -m mypy && ruff check src/ tests/ packages/ scripts/
```

- **Session boundary:** **One session. Close out when the 6 intake enumerations derive from their `Literal`s, the new member-presence test is green + mutation-proven, and the full suite passes. STOP.**

### 7.2 Phase O4-2 — Single-source the data-agent producer prose (in-wheel) + consumer hygiene

- **Goal:** `expected_row_count_order`'s prompt (data-agent `anthropic_client.py:140`) derives from the data-agent `Literal` (data-agent `schemas.py:96`), **inside the wheel**; `measurement_unit` documented as excluded; the website `"unknown"` consumer fallback resolved (Q5).
- **Why second:** isolates the cross-package/decoupling work; depends on no O4-1 symbol (the helper is not shared across the wheel — §1.4).
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| data-agent `anthropic_client.py` | derive the `:140` enumeration **in-wheel** (cannot import the main helper — §1.4); the prose **double-quotes** its members (`(one of "tens", "hundreds", …)`), so reproduce quoting for byte-identity: `'"' + '", "'.join(get_args(<PrimaryQuery field Literal>)) + '"'` — a bare `", ".join` would drop the quotes. The docstring at `llm.py:30-31` may also point at the `Literal`. | ~8 |
| data-agent `tests/.../test_anthropic_client.py` | +1 in-wheel member-presence test for `expected_row_count_order` (§6.3), mutation-proven | +15 |
| `agents/website/templates.py` (Q5, opt-in) | `:674` `"unknown"`→a member (e.g. `"tens"`) **or** a clearly non-member display label; update the byte-pinned render test | ~4 |
| data-agent `schemas.py` / `llm.py` | **comment only** — note `measurement_unit` is intentionally free-form (§1.5); no type change | ~2 |

- **What DONE looks like:** (1) no hand-listed `tens/hundreds/thousands/millions` in the data-agent prompt (grep, §13); (2) the in-wheel member-presence test green + RED on a dropped member; (3) **`tests/test_data_agent_decoupling.py` green** (no new main-package import from the wheel — the headline constraint); (4) `measurement_unit` left `str` with an explanatory comment; (5) full suite + mypy + ruff green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python
# (a) data-agent prompt no longer hand-lists the members:
grep -nE 'one of "tens", "hundreds"' packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py   # expect ZERO
# (b) the wheel did NOT grow a main-package import (decoupling — the load-bearing gate):
$PY -m pytest tests/test_data_agent_decoupling.py -v --no-cov
# (c) in-wheel member-presence + parsing tests:
$PY -m pytest packages/data-agent/tests -q --no-cov
# (d) full suite + types + lint:
$PY -m pytest -q && $PY -m mypy && ruff check src/ tests/ packages/ scripts/
```

- **Session boundary:** **One session. Close out when the data-agent enumeration derives in-wheel, the decoupling test is green, and the full suite passes. STOP. After O4-2 the committed O4 scope is COMPLETE.**

---

## 8. Impact Analysis

| Surface | Impact | Action |
|---|---|---|
| `Literal` member sets (all 7) | **none** — O4 never changes membership | unchanged |
| Rendered prompt text | **none** — `get_args` order = current prose order (byte-identical) | proven by substring pins + new member-presence tests |
| Validation behavior | **none** — validators untouched | `test_invalid_*_rejected` stay green |
| Intake prompts (`anthropic_client.py`) | construction: literal → derived | O4-1 |
| `_vocab_guard.py` | +`literal_members`/`join_members` (additive) | O4-1; keep `assert_vocab_parity` unchanged |
| Data-agent prompt | construction: literal → in-wheel derived | O4-2 |
| Decoupling boundary | **none** — wheel derives from its own `Literal`, no main import | O4-2 gate (`test_data_agent_decoupling.py`) |
| Consumer fallbacks | opt-in alignment only (Q5) | O4-2; otherwise unchanged |
| `measurement_unit` | **none** — excluded, comment only | O4-2 |
| Byte-pinned render tests | sensitive to any rendered change | unchanged renders → green; Q5 edits update them |

**What does NOT change:** any `Literal`'s members; the validators; the loose twins (`llm.py:43/82`); `measurement_unit`'s type; the `orchestrator/adapters.py:64` `time_series` branch (note only, §11).

**What might break (risk):** a derived join whose order/spacing differs from the prose (broken substring pin) — mitigated by `get_args` definition-order = current order; a wheel that imports the main helper (decoupling RED) — mitigated by the O4-2 gate; an Optional field's "or null" framing dropped during splicing — mitigated by keeping it literal.

---

## 9. Failure-Mode Analysis

| Failure | Surfaces in | Caught by | Result |
|---|---|---|---|
| Prompt re-hardcodes a member list later | edit-time | per-vocab member-presence test (§6.3) | RED if prose omits a member |
| `Literal` gains a member, prompt not regenerated | impossible (derived) | n/a — derivation prevents it | the O4 win |
| Wheel imports main `_vocab_guard`/`join_members` | `import` in `packages/data-agent/` | **NOT** the AST test (`_vocab_guard` ∉ its 3 intake substrings — §1.4); only code review + the twin-copy convention | would pass the test yet break the standalone wheel → copy the primitive instead |
| Wheel imports any other main module (e.g. `orchestrator`) | `import` in `packages/data-agent/` | **NOT** the AST test (only the 3 intake substrings); code review | breaks standalone distribution; a broader import-origin check is a separate hardening, not O4 |
| `get_args` order ≠ prose order → broken pin | O4-1 build | existing substring pins + diff review | caught in phase verify |
| "or null"/Optional framing lost in splice | review/runtime | render/parse tests + prompt pins | caught |
| Someone "completes" O4 by `Literal`-izing `measurement_unit` | future edit | §1.5 + the schema comment (O4-2) | documented as intentional |
| Member-presence test passes vacuously | O4-1/O4-2 | mutation proof (drop a member → RED) | required before close-out |

---

## 10. Verification Plan

"Verified-complete" for each implementation session:

1. **Full suite green:** `.venv/bin/python -m pytest -q`. **Re-confirm the count — do NOT hardcode** (baseline 759/759 @ 97.18% at HEAD `a8ff836`; each new test raises it — Learnings #19/#28).
2. **⚠ Coverage-gate trap:** `--cov-fail-under` makes any *subset* run report a coverage FAIL even when selected tests pass. **Subset runs append `--no-cov`** (as in §7); the coverage gate is the **full** suite.
3. **mypy clean:** `.venv/bin/python -m mypy` (no-arg = CI scope; baseline 0/62).
4. **ruff clean:** `ruff check src/ tests/ packages/ scripts/` (the exact CI invocation; `packages/` + `scripts/` included).
5. **Decoupling green:** `.venv/bin/python -m pytest tests/test_data_agent_decoupling.py -v --no-cov` (the load-bearing gate for O4-2).
6. **Non-vacuity:** each new member-presence test is proven RED by dropping a member from its prompt (Learning #89), not merely added.
7. **Byte-identity:** the pre-existing prompt substring pins (`test_anthropic_client.py:350-435`) stay green, proving the derived prose equals the old prose.

> **⚠ Interpreter:** use `.venv/bin/python` (3.13.5). Bare `python` (3.10) raises `UTC` ImportError. CI uses `uv run pytest/mypy/ruff`; both are equivalent for these gates.

---

## 11. Out of Scope (explicit)

- **Relocating any `Literal`** to a new home (`common.py` or elsewhere) — orthogonal to single-sourcing (§1.3), forbidden cross-package (§1.4). NOT O4.
- **`measurement_unit`** — free-form by design (§1.5); not `Literal`-ized; comment only. The prompt's "one of … or another …" wording nit is not O4.
- **Tightening / changing any `Literal`'s member set** — O4 preserves membership exactly.
- **The loose twins** (`llm.py:43/82`) — intentional LLM-intermediate `str` shapes; not typed by O4.
- **Consumer-fallback values** beyond the opt-in Q5 alignment — they are hygiene, not bugs (§1.6).
- **The `orchestrator/adapters.py:64` `if model_type == "time_series"` magic-string branch** — a single typed-field comparison (not a `dict.get`), low-risk; note for a future micro, not O4 (Learning #43).
- **Migrating `governance_templates.py`'s local `_assert_vocab_parity`** to the shared module (a separate O-series tidy).
- **Bundling any other backlog item** in an implementation session (FM #18).

---

## 12. Provenance

- **Audit:** `docs/audits/2026-06-01-technical-debt-audit.md` — E2 `:121-127`, O4 `:175`, sequencing `:177`, structural obs `:183-185`.
- **Evidence inventory (§3):** produced by direct `grep`/read at **HEAD `a8ff836`** (Session 123), cross-checked by a 13-agent fan-out (`wf_8e7ef86a-a83`): 5 read-only vocabulary readers (each inventory → adversarial re-grep/verify) + 3 readers for precedents, the decoupling boundary, and the test blast radius. Per **Learning #45**, every site entering this doc was re-derived by direct grep; per **Candidate #82**, every code claim (the free-form `measurement_unit` prompt, the `"unknown"` consumer fallback, the decoupling forbidden-substrings, the 7th `confidence`/`cycle_time`/`risk_tier` prose sites) was confirmed against canonical source before being written.
- **Corrections made during verification (provenance hygiene):** (1) the audit's 5-vocabulary grouping was **refined** — `measurement_unit` is genuinely free-form (excluded, §1.5) and **3 additional** same-class prose sites (`confidence`/`cycle_time`/`risk_tier`) were found that the audit did not name (§3.1). (2) The audit's "promote all to `common.py`" was **falsified** for the cross-package pair (decoupling AST test, §1.4) and reframed as orthogonal for the intake pair (§1.3). (3) The "derive via `get_args`" prescription was **confirmed** and shown to supersede #39's tuple+guard where a `Literal` exists (§1.3).
- **Guard precedent:** `assert_vocab_parity` (`_vocab_guard.py:25-52`, raises not asserts); #2 consumer guards (`governance_templates.py:98-99`, `test_governance.py:588/:598`); #39 producer single-source (`GOVERNANCE_FRAMEWORKS` + join + `test_governance.py:541`). Candidate #77 (parseable producer for drift-guard tests) — relevant lineage.
- **Decoupling evidence:** `tests/test_data_agent_decoupling.py:26-30` (forbidden substrings); main re-export `schemas/v1/data.py:16-28`; architecture-plan §7.
- **Methodology:** house-style mirror of `docs/planning/o3-repo-platforms-plan.md` + `o1-stage-driver-plan.md`; `ARCHITECTURE_WORKSTREAM.md` (Interface-First, Refactor Heuristics, anti-patterns).

---

## 13. Appendix — Full grep inventory (executor re-run block)

Run in Phase 0 **before** starting any phase. If sites drift, investigate before implementing.

```bash
cd /Users/rmsharp/Development/model_project_constructor   # verified 2026-06-07 @ HEAD a8ff836
# §3.1 — producer prose hand-listings (the O4 target) — expect the 7 sites in 2 files:
grep -nE 'one of supervised_classification' src/model_project_constructor/agents/intake/anthropic_client.py   # model_type  (#1)
grep -nE 'one of low/medium/high'           src/model_project_constructor/agents/intake/anthropic_client.py   # confidence  (#2)
grep -nE 'one of champion_challenger'        src/model_project_constructor/agents/intake/anthropic_client.py   # counterfactual_design (#3)
grep -nE 'one of weekly, monthly'            src/model_project_constructor/agents/intake/anthropic_client.py   # review_cadence (#4)
grep -nE '∈ \{strategic'                     src/model_project_constructor/agents/intake/anthropic_client.py   # cycle_time  (#5)
grep -nE '∈ \{tier_1_critical'               src/model_project_constructor/agents/intake/anthropic_client.py   # risk_tier   (#6)
grep -nE 'one of "tens", "hundreds"'         packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py  # row_count (#7)
# §3.2 — validators (must NOT change member sets):
grep -nE '^(ModelType|CycleTime|RiskTier) *= *Literal' src/model_project_constructor/schemas/v1/common.py     # 3
grep -nE 'confidence: Literal|counterfactual_design: Literal|review_cadence: Literal' src/model_project_constructor/schemas/v1/intake.py  # 3
grep -nE 'expected_row_count_order: Literal|measurement_unit: str' packages/data-agent/src/model_project_constructor_data_agent/schemas.py  # 1 Literal + 1 bare str
# §3.3 — consumer fallbacks (hygiene; Q5):
grep -nE 'expected_row_count_order", "unknown"' src/model_project_constructor/agents/website/templates.py     # 1 (non-member)
grep -nE 'review_cadence"\) or "' src/model_project_constructor/agents/website/governance_templates.py        # 1 ("" sentinel)
# §3.6 — reuse + safety net:
grep -nE 'def (assert_vocab_parity|literal_members|join_members)' src/model_project_constructor/_vocab_guard.py
grep -nE 'GOVERNANCE_FRAMEWORKS|set\(get_args' tests/agents/website/test_governance.py
grep -nE 'FORBIDDEN_SUBSTRINGS|IntakeReport' tests/test_data_agent_decoupling.py
```

## 14. Appendix — File reference map

| Concern | File:Line |
|---|---|
| Derivation helper (new) | `src/model_project_constructor/_vocab_guard.py` (beside `assert_vocab_parity:25`) |
| Intake prompts (O4-1 target) | `agents/intake/anthropic_client.py:123,124,182,188,200-202,206-207` |
| Data-agent prompt (O4-2 target) | `packages/data-agent/.../anthropic_client.py:140` |
| Validators (unchanged) | `schemas/v1/common.py:23/25/32`; `schemas/v1/intake.py:31/48/62`; data-agent `schemas.py:96` |
| `measurement_unit` (excluded) | data-agent `schemas.py:105`; prompt `anthropic_client.py:292-294`; docstring `llm.py:75` |
| Consumer fallbacks (Q5) | `templates.py:674` (`"unknown"`); `governance_templates.py:329` (`""`) |
| Loose twins (leave) | data-agent `llm.py:43/82` |
| `#39` producer precedent | `agents/intake/anthropic_client.py:113-119/126`; `test_governance.py:541` |
| `#2` consumer precedent | `governance_templates.py:64-69/86-91/98-99`; `test_governance.py:588/:598` |
| Decoupling gate | `tests/test_data_agent_decoupling.py:26-30`; re-export `schemas/v1/data.py:16-28` |
| Prompt pins (safety net) | `tests/agents/intake/test_anthropic_client.py:350-435` |

---

## Sign-off checklist for the executor

- [ ] Re-read this whole plan.
- [ ] Re-ran §13 grep inventory; the 7 producer sites + reuse targets match (or deltas understood).
- [ ] Resolved §6.5 Phase-1A questions (Q1 scope, Q2 home, Q3 measurement_unit, Q4 wheel guard, Q5 fallbacks) via `AskUserQuestion` **before** code.
- [ ] Confirmed `get_args` definition order reproduces each current prose enumeration byte-for-byte.
- [ ] Pre-flight green: `pytest && mypy && ruff` (full suite for coverage; `--no-cov` for subsets — §10).
- [ ] Phase 1B stub written to `SESSION_NOTES.md` **before** any code.
- [ ] Each new member-presence test mutation-proven RED (Learning #89) before close-out.
- [ ] Doing **exactly one** phase this session (FM #18 is the active risk).
- [ ] (O4-2) `test_data_agent_decoupling.py` green — the wheel grew no main-package import.
