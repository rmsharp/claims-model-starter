"""Tests for the ``STAGE_ORDER`` descriptor single-source (Overhaul O1, Phase O1-1).

``STAGE_ORDER`` (``orchestrator/pipeline.py``) is a frozen tuple of :class:`Stage`
metadata records — the single source of stage *order* + per-stage status/target
metadata. The hand-written ``ResumePoint`` / ``PipelineStatus`` Literals (which
mypy can read but cannot derive from a runtime tuple) are pinned to it by
import-time ``raise`` guards, mirroring the ``REPO_PLATFORMS`` / ``HostLiteral``
guard O3-1 established (``test_host_registry_guard.py``).

Phase O1-1 introduces all of this **dormant** — ``run_pipeline`` /
``determine_resume_point`` / the CLI banner are unchanged, so nothing yet
consumes ``STAGE_ORDER``. These tests therefore:

* pin the descriptor field table incl. the three load-bearing asymmetries
  (adapter is runner-less + halt-less; website is terminal + always-runs + last);
* prove ``_should_run`` reproduces the three current resume-membership gates in
  ``run_pipeline`` (the ``resume in (...)`` conditionals) **row for row** — the
  equivalence O1-2 relies on;
* prove ``skipped_stages`` reproduces ``_SKIPPED_STAGES_BY_RESUME_POINT``
  (``scripts/run_pipeline.py:317``) for **every** row incl. the unpinned
  ``website`` + ``already_complete`` rows, BEFORE O1-2 deletes that dict;
* prove each drift guard is **non-vacuous** (a deliberately-mismatched member set
  raises), and that the live parity holds;
* prove the single source **scales** — inserting a synthetic 5th descriptor row
  partitions load-vs-run correctly with no change to the gate logic.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import cast, get_args

import pytest

from model_project_constructor._vocab_guard import assert_vocab_parity
from model_project_constructor.orchestrator import pipeline

# Resume values that can actually reach the gates. ``already_complete`` is
# rejected by run_pipeline before any gate, so it is NOT a valid ``_should_run``
# input (``_STAGE_INDEX`` does not contain it).
_GATE_RESUMES: list[pipeline.ResumePoint | None] = [
    None,
    "intake",
    "intake_to_data_adapter",
    "data",
    "website",
]


# --- (a) Descriptor field table + asymmetries -------------------------------


class TestStageOrderFieldTable:
    def test_order_and_per_stage_metadata(self) -> None:
        assert [s.name for s in pipeline.STAGE_ORDER] == [
            "intake",
            "intake_to_data_adapter",
            "data",
            "website",
        ]
        assert [s.payload_type for s in pipeline.STAGE_ORDER] == [
            "IntakeReport",
            "DataRequest",
            "DataReport",
            "RepoTarget",
        ]
        assert [s.target_agent for s in pipeline.STAGE_ORDER] == [
            "data",
            "data",
            "website",
            "website",
        ]
        assert [s.has_runner for s in pipeline.STAGE_ORDER] == [True, False, True, True]
        assert [s.halt_status for s in pipeline.STAGE_ORDER] == [
            "FAILED_AT_INTAKE",
            None,
            "FAILED_AT_DATA",
            "FAILED_AT_WEBSITE",
        ]
        assert [s.result_field for s in pipeline.STAGE_ORDER] == [
            "intake_report",
            "data_request",
            "data_report",
            "project_result",
        ]

    def test_stage_names_and_index_derive_from_order(self) -> None:
        assert tuple(s.name for s in pipeline.STAGE_ORDER) == pipeline.STAGE_NAMES
        assert pipeline._STAGE_INDEX == {
            "intake": 0,
            "intake_to_data_adapter": 1,
            "data": 2,
            "website": 3,
        }

    def test_adapter_stage_is_runnerless_and_haltless(self) -> None:
        # §1.3 shape 2: the adapter is pure code with no injected runner and no
        # halt predicate (DataRequest carries no ``.status``).
        adapter = pipeline.STAGE_ORDER[1]
        assert adapter.name == "intake_to_data_adapter"
        assert adapter.has_runner is False
        assert adapter.halt_status is None
        assert adapter.always_runs is False
        assert adapter.terminal_result is False

    def test_website_stage_is_terminal_always_runs_and_last(self) -> None:
        # §1.3 shape 3: website is terminal — it re-executes unconditionally and
        # double-saves; it MUST be the last stage.
        website = pipeline.STAGE_ORDER[3]
        assert pipeline.STAGE_ORDER[-1].name == "website"
        assert website.always_runs is True
        assert website.terminal_result is True
        # website is the ONLY always-runs / terminal stage.
        assert [s.name for s in pipeline.STAGE_ORDER if s.always_runs] == ["website"]
        assert [s.name for s in pipeline.STAGE_ORDER if s.terminal_result] == ["website"]

    def test_stage_record_is_frozen(self) -> None:
        with pytest.raises(FrozenInstanceError):
            pipeline.STAGE_ORDER[0].name = "tampered"  # type: ignore[misc]


# --- (b) ``_should_run`` reproduces the three current gates row-for-row ------


def _expected_intake_gate(resume: pipeline.ResumePoint | None) -> bool:
    # run_pipeline intake gate: ``if resume is None or resume == "intake":``
    return resume is None or resume == "intake"


def _expected_adapter_gate(resume: pipeline.ResumePoint | None) -> bool:
    # run_pipeline adapter gate: ``if resume in (None, "intake", "intake_to_data_adapter"):``
    return resume in (None, "intake", "intake_to_data_adapter")


def _expected_data_gate(resume: pipeline.ResumePoint | None) -> bool:
    # run_pipeline data gate: ``if resume in (None, "intake", "intake_to_data_adapter", "data"):``
    return resume in (None, "intake", "intake_to_data_adapter", "data")


class TestShouldRunReproducesCurrentGates:
    @pytest.mark.parametrize("resume", _GATE_RESUMES)
    def test_intake_gate(self, resume: pipeline.ResumePoint | None) -> None:
        assert pipeline._should_run(resume, pipeline.STAGE_ORDER[0]) == (
            _expected_intake_gate(resume)
        )

    @pytest.mark.parametrize("resume", _GATE_RESUMES)
    def test_adapter_gate(self, resume: pipeline.ResumePoint | None) -> None:
        assert pipeline._should_run(resume, pipeline.STAGE_ORDER[1]) == (
            _expected_adapter_gate(resume)
        )

    @pytest.mark.parametrize("resume", _GATE_RESUMES)
    def test_data_gate(self, resume: pipeline.ResumePoint | None) -> None:
        assert pipeline._should_run(resume, pipeline.STAGE_ORDER[2]) == (
            _expected_data_gate(resume)
        )

    @pytest.mark.parametrize("resume", _GATE_RESUMES)
    def test_website_always_runs(self, resume: pipeline.ResumePoint | None) -> None:
        # Website has no gate in run_pipeline today — it always re-executes when
        # reached. ``always_runs=True`` reproduces that unconditional behavior.
        assert pipeline._should_run(resume, pipeline.STAGE_ORDER[3]) is True


# --- (c) ``skipped_stages`` reproduces the CLI banner dict for every row -----

# Mirror of ``_SKIPPED_STAGES_BY_RESUME_POINT`` (scripts/run_pipeline.py:317) at
# HEAD. O1-1 pins ``skipped_stages`` to this contract — incl. the ``website`` and
# ``already_complete`` rows that have no existing CLI assertion — BEFORE O1-2
# deletes the dict and routes the banner through ``skipped_stages``.
_EXPECTED_SKIPPED: dict[pipeline.ResumePoint, list[str]] = {
    "intake": [],
    "intake_to_data_adapter": ["intake"],
    "data": ["intake", "intake_to_data_adapter"],
    "website": ["intake", "intake_to_data_adapter", "data"],
    "already_complete": ["intake", "intake_to_data_adapter", "data", "website"],
}


class TestSkippedStagesReproducesBannerDict:
    @pytest.mark.parametrize(("resume", "expected"), list(_EXPECTED_SKIPPED.items()))
    def test_each_row(
        self, resume: pipeline.ResumePoint, expected: list[str]
    ) -> None:
        assert pipeline.skipped_stages(resume) == expected

    def test_resume_none_skips_nothing(self) -> None:
        assert pipeline.skipped_stages(None) == []


# --- (d) The drift guards are non-vacuous (deliberate mismatch raises) -------

_R_HINT = "test-only reconcile hint"


class TestDriftGuardsAreNonVacuous:
    def test_live_resumepoint_parity_holds(self) -> None:
        # Guard 1 positive: STAGE_NAMES + the sentinel ARE the ResumePoint members.
        assert set(pipeline.STAGE_NAMES) | {"already_complete"} == set(
            get_args(pipeline.ResumePoint)
        )

    def test_guard1_raises_when_sentinel_omitted(self) -> None:
        # Passing ``set(STAGE_NAMES)`` WITHOUT the ``already_complete`` sentinel
        # must raise — proving the exact-match guard would catch a STAGE_ORDER
        # that fails to cover ResumePoint (the §6.3 sentinel gotcha).
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                set(pipeline.STAGE_NAMES),
                pipeline.ResumePoint,
                name="STAGE_ORDER",
                reconcile_hint=_R_HINT,
            )

    def test_guard1_raises_on_extra_member(self) -> None:
        drifted = set(get_args(pipeline.ResumePoint)) | {"bogus_stage"}
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                drifted, pipeline.ResumePoint, name="STAGE_ORDER", reconcile_hint=_R_HINT
            )

    def test_live_pipelinestatus_parity_holds(self) -> None:
        # Guard 2 positive: COMPLETE + the non-None halt_status values ARE the
        # PipelineStatus members.
        members = {"COMPLETE"} | {
            s.halt_status for s in pipeline.STAGE_ORDER if s.halt_status is not None
        }
        assert members == set(get_args(pipeline.PipelineStatus))

    def test_guard2_raises_when_a_halt_status_is_missing(self) -> None:
        # A halt_status set missing FAILED_AT_WEBSITE must raise — proving a
        # misspelled / dropped halt_status is caught (the §3.6 metrics gap).
        incomplete = {"COMPLETE", "FAILED_AT_INTAKE", "FAILED_AT_DATA"}
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                incomplete,
                pipeline.PipelineStatus,
                name="STAGE_ORDER.halt_status",
                reconcile_hint=_R_HINT,
            )

    def test_live_result_field_subset_holds(self) -> None:
        # Guard 3 positive: every result_field names a real PipelineResult attr.
        real = {f.name for f in fields(pipeline.PipelineResult)}
        assert {s.result_field for s in pipeline.STAGE_ORDER} <= real

    def test_guard3_subset_check_flags_a_bogus_result_field(self) -> None:
        # Replicate guard 3's set-difference against a synthetic stage whose
        # result_field is not a PipelineResult attribute — proving the subset
        # check would flag it (the §3.6 wrong-field gap).
        real = {f.name for f in fields(pipeline.PipelineResult)}
        bogus = pipeline.Stage(
            name=cast(pipeline.ResumePoint, "data"),
            payload_type="DataReport",
            target_agent="website",
            has_runner=True,
            halt_status="FAILED_AT_DATA",
            result_field="not_a_pipeline_result_field",
        )
        missing = {s.result_field for s in (*pipeline.STAGE_ORDER, bogus)} - real
        assert missing == {"not_a_pipeline_result_field"}


# --- (e) The single source SCALES (bounded extensibility proof) --------------


class TestStageOrderScales:
    def test_inserting_a_fifth_stage_partitions_load_vs_run(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Insert a synthetic mid-pipeline stage between ``data`` and ``website``
        # into a COPY of the order, repoint the module globals, and confirm the
        # gates / banner partition correctly with NO change to the gate logic.
        # (Proves the SoT scales — NOT zero-edit insertion; that is O1's later
        # value, and the loop-collapse is deferred — plan §11.)
        synthetic = pipeline.Stage(
            name=cast(pipeline.ResumePoint, "validation"),
            payload_type="ValidationReport",
            target_agent="website",
            has_runner=True,
            halt_status=None,
            result_field="data_report",
        )
        new_order = (
            pipeline.STAGE_ORDER[:3] + (synthetic,) + pipeline.STAGE_ORDER[3:]
        )
        new_index = {s.name: i for i, s in enumerate(new_order)}
        monkeypatch.setattr(pipeline, "STAGE_ORDER", new_order)
        monkeypatch.setattr(pipeline, "_STAGE_INDEX", new_index)

        # Resuming at the new stage loads everything before it; validation +
        # website re-run (website is always-runs).
        assert pipeline.skipped_stages(cast(pipeline.ResumePoint, "validation")) == [
            "intake",
            "intake_to_data_adapter",
            "data",
        ]
        # Resuming at ``data`` now also loads only intake + adapter; data,
        # validation, website all run.
        assert pipeline.skipped_stages("data") == ["intake", "intake_to_data_adapter"]
        # Resuming from website loads validation (index 3 > website? no — website
        # is index 4, so validation at 3 is before it and LOADS); website itself
        # always runs.
        assert pipeline._should_run(cast(pipeline.ResumePoint, "website"), synthetic) is False
        assert pipeline._should_run(cast(pipeline.ResumePoint, "website"), new_order[4]) is True
