"""Minimal HTML + HTMX templates for the intake web UI.

We deliberately avoid a template engine (no Jinja2 dependency). Every
interpolated value is passed through ``html.escape`` so stakeholder input
cannot inject markup. The templates are small, form-based, and easy to
read top-to-bottom.
"""

from __future__ import annotations

from html import escape
from typing import Any

from model_project_constructor.ui.intake.runner import SessionSnapshot

_BASE_CSS = """
<style>
body { font-family: -apple-system, system-ui, sans-serif; max-width: 720px;
       margin: 2em auto; padding: 0 1em; color: #1a1a1a; line-height: 1.5; }
h1 { font-size: 1.4em; }
h2 { font-size: 1.15em; color: #444; margin-top: 1.5em; }
form { margin-top: 1em; }
label { display: block; margin-top: 0.5em; font-weight: 600; }
input[type=text], textarea {
  width: 100%; padding: 0.5em; font-size: 1em; border: 1px solid #bbb;
  border-radius: 4px; font-family: inherit;
}
textarea { min-height: 6em; }
button { margin-top: 0.75em; padding: 0.5em 1em; font-size: 1em;
         border: 1px solid #0a66c2; background: #0a66c2; color: #fff;
         border-radius: 4px; cursor: pointer; }
button.secondary { background: #fff; color: #0a66c2; }
.meta { color: #666; font-size: 0.9em; }
.draft { background: #f6f8fa; padding: 1em; border-radius: 6px;
         border: 1px solid #d0d7de; margin: 1em 0; }
.draft h3 { margin-top: 0; font-size: 1em; color: #0a66c2; }
.tag { display: inline-block; padding: 0.1em 0.5em; background: #e0e7ff;
       color: #1e3a8a; border-radius: 3px; font-size: 0.85em;
       margin-right: 0.3em; }
.warn { color: #a04000; background: #fff4e0; padding: 0.5em;
        border-radius: 4px; border: 1px solid #e0b070; }
</style>
"""

_HTMX = (
    '<script src="https://unpkg.com/htmx.org@1.9.12" '
    'integrity="sha384-ujb1lZYygJmzgSwoxRggbCHcjc0rB2XoQrxeTUQyRjrOnlCoYta87iKBWq3EsdM2" '
    'crossorigin="anonymous"></script>'
)


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        f"<title>{escape(title)}</title>{_BASE_CSS}{_HTMX}"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"</head><body>{body}</body></html>"
    )


def render_index() -> str:
    body = """
<h1>Model Project Intake</h1>
<p class=meta>Start a guided intake interview. The agent will ask up to 10
questions and produce a draft intake report for your review.</p>
<form action="/sessions" method="post">
  <label for=stakeholder_id>Your name or ID</label>
  <input id=stakeholder_id name=stakeholder_id type=text required>
  <label for=session_id>Session ID (leave blank to auto-generate)</label>
  <input id=session_id name=session_id type=text>
  <label for=domain>Domain</label>
  <input id=domain name=domain type=text value="pc_claims">
  <label for=initial_problem>Optional: one-line problem statement</label>
  <input id=initial_problem name=initial_problem type=text>
  <button type=submit>Start interview</button>
</form>
<p class=meta>Already have a session? <a href="/sessions/">Resume by ID</a>.</p>
"""
    return _page("Intake", body)


def render_resume_form() -> str:
    body = """
<h1>Resume Interview</h1>
<form action="/sessions/resume" method="get">
  <label for=session_id>Session ID</label>
  <input id=session_id name=session_id type=text required>
  <button type=submit>Resume</button>
</form>
<p class=meta><a href="/">Back</a></p>
"""
    return _page("Resume intake", body)


def _session_header(session_id: str) -> str:
    return (
        f"<p class=meta>Session <code>{escape(session_id)}</code> &middot; "
        f'<a href="/sessions/{escape(session_id)}/events" target="_blank">SSE events</a></p>'
    )


def render_session(snap: SessionSnapshot) -> str:
    if snap.phase == "question":
        return _page("Interview", _render_question(snap))
    if snap.phase == "review":
        return _page("Draft review", _render_review(snap))
    if snap.phase == "complete":
        return _page("Intake complete", _render_complete(snap))
    body = (
        f"<h1>Session not started</h1>{_session_header(snap.session_id)}"
        '<p>This session has no state yet. <a href="/">Start a new interview</a>.</p>'
    )
    return _page("Intake", body)


def _render_question(snap: SessionSnapshot) -> str:
    qnum = snap.question_number or 0
    question = escape(snap.question or "")
    sid = escape(snap.session_id)
    return f"""
<h1>Question {qnum} of up to 10</h1>
{_session_header(snap.session_id)}
<p><strong>{question}</strong></p>
<form action="/sessions/{sid}/answer" method="post">
  <label for=answer>Your answer</label>
  <textarea id=answer name=answer required autofocus></textarea>
  <button type=submit>Submit answer</button>
</form>
"""


def _render_review(snap: SessionSnapshot) -> str:
    df = snap.draft_fields or {}
    gov = snap.governance_fields or {}
    sid = escape(snap.session_id)

    model_sol = df.get("model_solution") or {}
    est_val = df.get("estimated_value") or {}

    gov_block = (
        "<h3>Governance</h3>"
        f"<p><span class=tag>cycle: {escape(str(gov.get('cycle_time', '?')))}</span>"
        f"<span class=tag>tier: {escape(str(gov.get('risk_tier', '?')))}</span></p>"
        f"<p class=meta><em>Cycle:</em> {escape(str(gov.get('cycle_time_rationale', '')))}</p>"
        f"<p class=meta><em>Tier:</em> {escape(str(gov.get('risk_tier_rationale', '')))}</p>"
    ) if gov else ""

    draft_html = (
        "<h3>Business problem</h3>"
        f"<p>{escape(str(df.get('business_problem', '')))}</p>"
        "<h3>Proposed solution</h3>"
        f"<p>{escape(str(df.get('proposed_solution', '')))}</p>"
        "<h3>Model solution</h3>"
        f"<p>{_render_kv(model_sol)}</p>"
        "<h3>Estimated value</h3>"
        f"<p>{_render_kv(est_val)}</p>"
        f"{gov_block}"
    )

    return f"""
<h1>Review draft</h1>
{_session_header(snap.session_id)}
<p class=meta>Revision cycle {snap.revision_cycles} of 3. Reply
<code>accept</code> to finalize, or describe what should change.</p>
<div class=draft>{draft_html}</div>
<form action="/sessions/{sid}/review" method="post">
  <label for=review>Your review</label>
  <textarea id=review name=review required autofocus>accept</textarea>
  <button type=submit>Submit review</button>
</form>
"""


def _render_complete(snap: SessionSnapshot) -> str:
    sid = escape(snap.session_id)
    status = escape(snap.status or "")
    missing = snap.missing_fields or []
    missing_html = (
        f"<p class=warn>missing_fields: {escape(', '.join(missing))}</p>"
        if missing
        else ""
    )
    rep_json_href = f"/sessions/{sid}/report.json"
    df = snap.draft_fields or {}
    gov = snap.governance_fields or {}
    return f"""
<h1>Intake {status}</h1>
{_session_header(snap.session_id)}
{missing_html}
<p><a href="{rep_json_href}">Download report JSON</a></p>
<div class=draft>
  <h3>Business problem</h3><p>{escape(str(df.get('business_problem', '')))}</p>
  <h3>Proposed solution</h3><p>{escape(str(df.get('proposed_solution', '')))}</p>
  <h3>Governance</h3>
  <p><span class=tag>cycle: {escape(str(gov.get('cycle_time', '?')))}</span>
     <span class=tag>tier: {escape(str(gov.get('risk_tier', '?')))}</span></p>
</div>
"""


def _render_kv(d: dict[str, Any]) -> str:
    if not d:
        return "<em>(empty)</em>"
    rows = "".join(
        f"<li><strong>{escape(str(k))}:</strong> {escape(str(v))}</li>"
        for k, v in d.items()
    )
    return f"<ul>{rows}</ul>"
