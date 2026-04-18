# Intake Interview Design

This page explains how the Intake Agent conducts its interview: the role it plays, how it decides what to ask, when it stops, and how a stakeholder should prepare. It is aimed at two audiences:

- **Business stakeholders** who will be interviewed — so they know what to expect and how to get a strong draft on the first pass.
- **Operators and developers** who run or extend the agent — so they understand the state machine, budgets, and extension points.

For the full agent entry-point reference (CLI, fixture mode, programmatic use) see the [Agent Reference](Agent-Reference). For schema details see the [Schema Reference](Schema-Reference).

---

## 1. The role the agent plays

The interviewer is prompted as **"an expert data scientist, business analyst, and consultant focused on a claims organization within a property & casualty insurance company that sells auto and property policies."** It is not a transcription bot — it brings domain framing to the conversation and drives toward a defensible draft.

The system prompt (verbatim from `src/model_project_constructor/agents/intake/anthropic_client.py:33-42`):

> You are an expert data scientist, business analyst, and consultant focused on a claims organization within a property & casualty insurance company that sells auto and property policies. You are interviewing a business stakeholder to draft an intake document covering: business problem, proposed solution, model solution (target and inputs), and estimated value. Ask ONE question at a time. Drive toward the four required sections and toward a defensible governance classification (cycle time + risk tier).

Two rules are load-bearing and worth flagging:

- **One question per turn.** The agent is explicitly forbidden from batching questions. This keeps each turn digestible and avoids the "which half of the compound question did you actually answer?" problem.
- **Drive toward four sections.** Every question should move the conversation closer to completing `business_problem`, `proposed_solution`, `model_solution`, or `estimated_value` — plus a governance classification. Exploratory small talk is out of scope.

A second system prompt covers governance classification (`anthropic_client.py:44-50`):

> You classify model projects against an internal governance matrix. cycle_time ∈ {strategic, tactical, operational, continuous}. risk_tier ∈ {tier_1_critical, tier_2_high, tier_3_moderate, tier_4_low}. Regulatory frameworks include SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, GDPR_ART_22. Be conservative: if in doubt, pick the stricter tier.

The conservative-bias heuristic is deliberate. Under-classifying a model's risk produces downstream governance gaps that are expensive to detect. Over-classifying only costs some extra documentation.

---

## 2. Interview flow at a glance

The agent is a LangGraph `StateGraph` (see `src/model_project_constructor/agents/intake/graph.py`). There are eight nodes and two loops:

```
START → plan_next_question → ask_user → evaluate_interview
                                                │
                      ┌─────────────────────────┴───┐
                      │ (not enough info yet)       │ (enough info)
                      ▼                             ▼
             plan_next_question              draft_report
                                                     │
                                                     ▼
                                           classify_governance
                                                     │
                                                     ▼
                                              await_review
                                                     │
                                 ┌───────────────────┴────────────┐
                                 │ (rejected, under cap)          │ (accepted OR at cap)
                                 ▼                                ▼
                              revise                          finalize → END
                                 │
                                 └──→ back to await_review
```

Two phases, two budgets:

| Phase | Loop | Cap | Constant |
|---|---|---|---|
| **Interview** | `plan_next_question → ask_user → evaluate_interview` | 20 questions | `MAX_QUESTIONS = 20` in `state.py:57` |
| **Review** | `await_review → revise → await_review` | 3 revisions | `MAX_REVISIONS = 3` in `state.py:58` |

Caps are hard — the agent will always stop at them, whether or not the stakeholder is satisfied. When a cap is hit without a clean finish, the report is emitted with `status="DRAFT_INCOMPLETE"` and a `missing_fields` entry documenting which cap tripped (`questions_cap_reached` or `revision_cap_reached`).

---

## 3. How the agent decides what to ask next

Every turn, the agent calls `next_question(context)` on its LLM client (`nodes.py:52-57`). The context it receives contains:

- The `domain` (defaults to `"pc_claims"`).
- The `initial_problem` statement from the session opener (optional).
- Every question and answer so far (the full `qa_pairs` list).
- The current `questions_asked` count.

The LLM returns two fields (`NextQuestionResult` in `protocol.py:30-39`):

- `question: str` — the next single question to ask, or `""` if none.
- `believe_enough_info: bool` — the agent's own judgment that it now has enough to draft all four required sections *and* classify governance.

`evaluate_interview` then decides whether to loop or drop through (`nodes.py:78-82`):

```python
complete = enough or asked >= MAX_QUESTIONS
```

In practice:

- **If the agent still needs information**, it asks another question.
- **If the agent believes it has enough**, it proceeds to drafting.
- **If 20 questions have been asked regardless**, it proceeds to drafting and marks the report `DRAFT_INCOMPLETE` with `"questions_cap_reached"` appended to `missing_fields`.

The soft and hard stops are independent signals. An agent that reaches question 8 and says "I have enough" will stop at question 8. An agent that reaches question 20 without feeling complete will stop at question 20 anyway.

---

## 4. What the four required sections look like

After the interview loop exits, `draft_report` asks the LLM to emit a full draft (`nodes.py` draft node + `anthropic_client.py:94-119`). The four sections are:

### `business_problem` (prose)

What is broken today, why it matters, and what success would feel like. One to two paragraphs.

### `proposed_solution` (prose)

How a model or system change would address the problem. This is the stakeholder's hypothesis, not the agent's — but the agent drives for specifics (what triggers the model, what it does with the prediction).

### `model_solution` (structured — `ModelSolution` schema)

Target variable, target definition, candidate features, evaluation metrics, model type, and whether it is supervised. `model_type` must be one of:

- `supervised_classification`, `supervised_regression`
- `unsupervised_clustering`, `unsupervised_anomaly`
- `time_series`, `reinforcement`, `other`

### `estimated_value` (structured — `EstimatedValue` schema)

Annual impact band (low–high USD, both nullable), confidence (`low | medium | high`), prose narrative, and a list of assumptions. The low/high range is deliberately a band, not a point estimate — stakeholders should resist the temptation to over-precision.

Full field definitions are in the [Schema Reference](Schema-Reference).

---

## 5. Governance classification

Right after the draft, `classify_governance` asks the LLM to classify the project on the governance matrix (`nodes.py:88-92` + `anthropic_client.py:121-137`). This produces:

- **`cycle_time`** — `strategic` (months/quarters), `tactical` (weeks), `operational` (days/hours), or `continuous` (real-time).
- **`risk_tier`** — `tier_1_critical`, `tier_2_high`, `tier_3_moderate`, or `tier_4_low`.
- **`regulatory_frameworks`** — a list (e.g., `["SR_11_7", "NAIC_AIS"]` for US prudential/insurance; `EU_AI_ACT_ART_9`, `GDPR_ART_22` for EU).
- **`affects_consumers`** — does the output shape a decision that touches an end consumer?
- **`uses_protected_attributes`** — are protected-class attributes in the feature set?

Each classification carries a `_rationale` string explaining the choice. Those rationales survive into the final `GovernanceMetadata` on the report and downstream into the generated project's `model_registry.json`, so they must be defensible — not filler.

**Governance is recomputed on every revision.** If a stakeholder says "actually this will affect consumers," the revised draft triggers a fresh governance pass (`nodes.py:108-119`). The agent cannot end up with a revised draft that disagrees with its own governance classification.

---

## 6. The review loop

After the classification, the draft and governance are handed to the stakeholder for review (`await_review`, `nodes.py:94-106`). The stakeholder responds with either an **accept token** or a **revision request**.

Accept tokens (case-insensitive, whitespace-trimmed; `nodes.py:35`):

```
accept | yes | approve | approved | ok | looks good
```

Anything else is treated as revision feedback. The feedback string is passed to `revise_report`, which asks the LLM to produce a new draft incorporating the feedback. Governance is recomputed immediately. Control returns to `await_review` and the loop repeats.

After three revisions without an accept, the loop exits with `status="DRAFT_INCOMPLETE"` and `"revision_cap_reached"` in `missing_fields`. The final report still contains the latest draft — the stakeholder can pick it up manually and take it the rest of the way.

---

## 7. Terminal status rules

`finalize` computes the final status (`nodes.py:121-151`):

| Accepted? | At questions cap? | At revisions cap? | Status | `missing_fields` additions |
|---|---|---|---|---|
| ✅ | — | — | `COMPLETE` | — |
| — | ✅ | — | `DRAFT_INCOMPLETE` | `"questions_cap_reached"` |
| ❌ | — | ✅ | `DRAFT_INCOMPLETE` | `"revision_cap_reached"` |
| ❌ | — | ❌ | *impossible — loop continues* | — |

`COMPLETE` requires two things simultaneously: the stakeholder accepted, AND no cap was tripped. Anything else is `DRAFT_INCOMPLETE`.

The orchestrator halts on `DRAFT_INCOMPLETE` — the pipeline does not proceed to the Data Agent until an intake draft is formally accepted. See [Monitoring and Operations §5](Monitoring-and-Operations) for resume recipes.

---

## 8. Tips for stakeholders

### Before the interview

1. **Write one sentence** describing the business problem and have it ready for the `initial_problem` field. The agent will ask for it anyway; prepared stakeholders save 1–2 questions.
2. **Know your rough value band.** "Tens of thousands per year" vs "tens of millions per year" is the most important distinction — point precision within a band matters less than getting the order of magnitude right.
3. **Know your target population.** If the model is about auto subrogation, be ready to say whether it covers all 50 states or just a subset, all coverage types or only collision, etc.
4. **Have one example of the prediction's downstream consumer.** Is it an adjuster? An automated triage system? A monthly leadership report? The agent's `proposed_solution` hinges on this.

### During the interview

- **One question per turn** is real — don't race ahead. A three-paragraph answer to a narrow question often introduces new questions the agent won't ask, because it's already moved on.
- **If the question is too broad, say so.** The agent will narrow. Don't guess at what it meant.
- **If you don't know, say "I don't know."** That's a valid answer. The agent will adjust. Guessing produces a confidently wrong draft.
- **Watch for `missing_fields` after the draft.** If the agent couldn't extract e.g. `target_definition`, it will list the gap rather than hallucinate. That's your cue to add it in the review cycle.

### At review time

- **One accept token ends the interview.** Don't type `"yes but also..."` — the first six characters already trip the accept match, and the rest is silently discarded.
- **Revision feedback should be specific.** "Change cycle_time to operational because adjusters trigger the model on every new claim" works. "This is wrong" does not.
- **You have three revisions.** Plan accordingly — if the first draft is wildly off, the second should be recognizably closer, and the third should be a polish pass. If you're not converging by revision 2, the interview probably needed more questions.

---

## 9. Running the agent

### Fixture mode (Phase 3A, shipped)

The shipped CLI replays canned answers from a YAML fixture — it does not call an LLM or take live input. This is the CI path and the recommended smoke test (`cli.py:30-60`):

```bash
uv run python -m model_project_constructor.agents.intake \
    --fixture tests/fixtures/subrogation.yaml \
    --output my_intake_report.json
```

Useful fixtures ship in `tests/fixtures/`:

| Fixture | What it demonstrates |
|---|---|
| `subrogation.yaml` | Happy path: 7 questions, immediate accept, `tactical` / `tier_3_moderate` |
| `fraud_triage.yaml` | High-governance: `continuous` / `tier_1_critical`, `EU_AI_ACT_ART_9` |
| `pricing_optimization.yaml` | `strategic` / `tier_2_high` |
| `intake_question_cap.yaml` | Forces the `MAX_QUESTIONS` cap (→ `DRAFT_INCOMPLETE`) |
| `intake_revision_cap.yaml` | Forces the 3-revision cap (→ `DRAFT_INCOMPLETE`) |

### Web UI mode (Phase 3B, FastAPI)

The FastAPI web UI in `src/model_project_constructor/ui/intake/` reuses the same compiled graph but supplies a live `AnthropicLLMClient` and a `SqliteSaver` checkpointer so interview state survives server restart. The UI is what `go/modelintake` points to in a deployed environment. Environment variables:

- `ANTHROPIC_API_KEY` (required)
- `INTAKE_DB_PATH` (optional; defaults to `./intake_sessions.db`)

See [Monitoring and Operations](Monitoring-and-Operations) for deployment specifics.

### Programmatic use

```python
from model_project_constructor.agents.intake import IntakeAgent
from model_project_constructor.agents.intake.anthropic_client import AnthropicLLMClient

agent = IntakeAgent(AnthropicLLMClient())
report = agent.run_scripted(
    stakeholder_id="jane@example.com",
    session_id="2026-04-16-001",
    interview_answers=[...],   # your answers
    review_responses=["ACCEPT"],
)
```

The `IntakeLLMClient` is a `Protocol` (`protocol.py:71-89`), so you can swap in a different LLM provider by implementing `next_question`, `draft_report`, `classify_governance`, and `revise_report`.

---

## 10. Extending the agent

Four extension points, ordered by effort:

1. **Swap the LLM provider** — implement `IntakeLLMClient` (4 methods). Do not modify the nodes; they are provider-agnostic.
2. **Change the caps** — edit `MAX_QUESTIONS` / `MAX_REVISIONS` in `state.py:57-58`. These are hard-coded by design; changing them is a deliberate policy decision.
3. **Add governance dimensions** — extend `GovernanceClassification` in `protocol.py:59-68` and `GovernanceMetadata` in `schemas/v1/intake.py:35-43`. Update the classification prompt in `anthropic_client.py:44-50` and the classification node in `nodes.py`. Downstream governance artifact templates in `governance_templates.py` may also need updates.
4. **Add a new interview phase** — add a node, wire edges in `graph.py`, extend `IntakeState` in `state.py`. This is the largest change and should go through a planning session — the current two-phase shape (interview → review) is load-bearing for the CLI, the web UI, and the fixture format.

---

## 11. Key files

| File | Role |
|---|---|
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Anthropic-backed LLM client + system prompts |
| `src/model_project_constructor/agents/intake/graph.py` | LangGraph `StateGraph` wiring |
| `src/model_project_constructor/agents/intake/nodes.py` | Node implementations + routers + accept-token matching |
| `src/model_project_constructor/agents/intake/state.py` | `IntakeState` TypedDict + `MAX_QUESTIONS` / `MAX_REVISIONS` |
| `src/model_project_constructor/agents/intake/protocol.py` | `IntakeLLMClient` protocol + intermediate dataclasses |
| `src/model_project_constructor/agents/intake/agent.py` | `IntakeAgent` public entry points |
| `src/model_project_constructor/agents/intake/fixture.py` | Fixture schema + `FixtureLLMClient` |
| `src/model_project_constructor/agents/intake/cli.py` | Typer CLI (fixture-only in Phase 3A) |
| `src/model_project_constructor/ui/intake/app.py` | FastAPI web UI (Phase 3B) |
| `src/model_project_constructor/schemas/v1/intake.py` | `IntakeReport`, `ModelSolution`, `EstimatedValue`, `GovernanceMetadata` |
