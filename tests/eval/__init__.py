"""Phase B eval / parity harness (multi-provider LLM plan §5 Phase B).

This package holds the golden-input corpus, the deterministic scorers, and
the two-tier test battery that gates a second LLM provider on output quality
rather than mere parse success:

* a **deterministic CI tier** (``test_eval_*.py``, no marker) that proves the
  scorers and oracles measure correctly using fakes + reference data — runs on
  every PR with **no** ``ANTHROPIC_API_KEY`` (CI hermeticity preserved);
* a **``live``-marked tier** (``test_eval_live.py``) that runs the same corpus
  through a real provider client to record the baseline and check the §3.4
  thresholds — deselected by default (``pytest -m 'not live'``) and auto-skipped
  when no key is present.

See ``tests/eval/README.md`` for the methodology, the threshold table, and the
governance reference-label provenance.

Non-test modules in this package (``eval_corpus``, ``eval_scoring``,
``eval_thresholds``) are imported by the tests via ``from tests.eval.… import``;
they are not collected (no ``test_`` prefix).
"""
