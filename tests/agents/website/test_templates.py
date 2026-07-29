"""Tests for the website agent's base-scaffolding templates."""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.website.templates import (
    build_base_files,
    derive_project_name,
    derive_project_slug,
    render_data_loading,
    render_evaluation,
    render_gitignore,
    render_license,
    render_models,
    render_pyproject,
    render_qmd_business_understanding,
    render_qmd_data,
    render_qmd_implementation_plan,
    render_qmd_initial_models,
    render_readme,
    render_reports_data_md,
    render_reports_intake_md,
)
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport


class TestProjectNameDerivation:
    def test_basic_lowercasing(self) -> None:
        assert derive_project_name("Subrogation Model") == "subrogation-model"

    def test_strips_punctuation(self) -> None:
        assert derive_project_name("  Claims -- Triage!  ") == "claims-triage"

    def test_collapses_runs(self) -> None:
        assert derive_project_name("foo___bar...baz") == "foo-bar-baz"

    def test_empty_input_fallback(self) -> None:
        assert derive_project_name("") == "model-project"
        assert derive_project_name("---") == "model-project"


class TestProjectSlugDerivation:
    def test_dashes_to_underscores(self) -> None:
        assert derive_project_slug("subrogation-model") == "subrogation_model"

    def test_strips_invalid_chars(self) -> None:
        assert derive_project_slug("foo-bar!@baz") == "foo_bar_baz"

    def test_leading_digit_prefixed(self) -> None:
        # A project name starting with a digit isn't a valid python identifier
        assert derive_project_slug("123-model").startswith("m_")

    def test_empty_fallback(self) -> None:
        assert derive_project_slug("") == "model_project"


class TestIndividualRenderers:
    def test_gitignore_has_python_and_quarto(self) -> None:
        out = render_gitignore()
        assert "__pycache__/" in out
        assert "_site/" in out
        assert "*.parquet" in out

    def test_readme_surfaces_business_problem(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        readme = render_readme(intake=intake, project_name="foo-bar")
        assert "# foo-bar" in readme
        assert "Subrogation recovery dropped" in readme
        assert "stakeholder_claims_001" in readme
        assert "## License" in readme
        assert "LICENSE" in readme

    def test_license_is_proprietary_placeholder_not_a_known_license(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_license(intake=intake, project_name="foo-bar")
        assert "PROPRIETARY AND CONFIDENTIAL" in out
        assert "stakeholder_claims_001" in out
        assert "Legal" in out
        # Must not resemble a real open-source grant (MIT, Apache, etc.) that
        # SPDX/license-detection tooling could mistake for a real license.
        assert "Permission is hereby granted" not in out
        assert "MIT" not in out

    def test_pyproject_uses_slug_for_wheel(self) -> None:
        out = render_pyproject(project_name="foo-bar", project_slug="foo_bar")
        assert 'name = "foo-bar"' in out
        assert 'packages = ["src/foo_bar"]' in out

    def test_data_loading_lists_primary_queries(self) -> None:
        out = render_data_loading(
            project_slug="foo_bar",
            primary_query_names=["alpha", "beta"],
        )
        assert '"alpha"' in out
        assert '"beta"' in out
        assert "NotImplementedError" in out
        assert "Wire up SQLAlchemy" in out

    def test_models_embeds_declared_model_type(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_models(intake=intake)
        assert "supervised_classification" in out
        assert "NotImplementedError" in out

    def test_evaluation_lists_requested_metrics(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_evaluation(intake=intake)
        assert '"AUC"' in out
        assert '"precision_at_top_decile"' in out

    def test_evaluation_handles_missing_metrics(self) -> None:
        out = render_evaluation(intake={"model_solution": {}})
        assert "REQUESTED_METRICS" in out

    def test_qmd_business_uses_narrative(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_qmd_business_understanding(intake=intake)
        assert "## Business Problem" in out
        assert "## Proposed Solution" in out
        assert "Subrogation recovery dropped" in out

    def test_qmd_business_renders_business_case(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_qmd_business_understanding(intake=intake)
        # All seven business-case sections are present...
        for heading in (
            "## Annual Impact Band",
            "## Cost of Inaction",
            "## Implementation Cost",
            "## Payback",
            "## Value Drivers",
            "## Assumptions",
            "## Decision Rights",
        ):
            assert heading in out
        # ...populated with the intake's figures.
        assert "$2,000,000 – $4,000,000 per year" in out
        assert "$250,000 – $500,000" in out
        assert "4 months" in out
        assert "improved_subrogation_recovery_rate" in out
        assert "Claims VP + Data Science lead" in out

    def test_qmd_business_missing_fields_render_placeholders(self) -> None:
        # A sparse intake (no estimated_value, no value_measurement_plan)
        # still yields a structurally complete business case.
        out = render_qmd_business_understanding(intake={})
        assert "## Cost of Inaction" in out
        assert "## Decision Rights" in out
        assert "(not estimated)" in out
        assert "- (none declared)" in out
        assert "(not specified)" in out

    def test_qmd_data_lists_queries(self, data_report: DataReport) -> None:
        data = data_report.model_dump(mode="json")
        out = render_qmd_data(data=data)
        assert "subrogation_training_set" in out
        assert "queries/primary/subrogation_training_set.sql" in out

    def test_qmd_initial_models_includes_metrics(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_qmd_initial_models(intake=intake)
        assert "AUC" in out
        assert "supervised_classification" in out

    def test_qmd_implementation_plan_formats_dollar_range(
        self, intake_report: IntakeReport, data_report: DataReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        data = data_report.model_dump(mode="json")
        out = render_qmd_implementation_plan(intake=intake, data=data)
        assert "$2,000,000" in out
        assert "$4,000,000" in out

    def test_qmd_implementation_plan_handles_missing_estimate(self) -> None:
        out = render_qmd_implementation_plan(
            intake={"estimated_value": {}}, data={}
        )
        assert "not estimated" in out
        assert "(none declared)" in out

    def test_qmd_implementation_plan_renders_production_measurement_plan(
        self, intake_report: IntakeReport, data_report: DataReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        data = data_report.model_dump(mode="json")
        out = render_qmd_implementation_plan(intake=intake, data=data)

        # Every Production Measurement Plan section is present.
        for heading in (
            "## Production Measurement Plan",
            "## Baseline",
            "## Counterfactual Design",
            "## Attribution Method",
            "## Evaluation Horizon",
            "## Logging Requirements",
            "## Review Cadence",
            "## Success Criteria",
            "## Decision Rights",
        ):
            assert heading in out

        # Baseline value is interpolated from DataReport.baseline_snapshot
        # with a citation footnote (operator-selected rendering).
        assert "subrogation_recovery_rate" in out
        assert "0.41 ratio" in out
        assert "[^baseline-src]: Baseline figures are sourced from" in out
        assert "`EXECUTED`" in out
        assert "2024-01-01 → 2024-12-31" in out
        # Methodology fields from the intake's ValueMeasurementPlan.
        assert "champion_challenger" in out
        assert "6 months" in out
        assert "claim_id" in out
        # The Phase-5 structured plan replaces the old TODO scaffold.
        assert "intentionally sparse" not in out

    def test_qmd_implementation_plan_missing_plan_renders_placeholders(
        self,
    ) -> None:
        out = render_qmd_implementation_plan(intake={}, data={})

        # Sections still render even with no value_measurement_plan / snapshot.
        assert "## Production Measurement Plan" in out
        assert "## Baseline" in out
        assert "## Decision Rights" in out
        assert "No baseline snapshot was collected by the Data Agent" in out
        assert "none_declared" in out
        assert "(not specified)" in out
        # No baseline value → no interpolated figure and no footnote.
        assert "[^baseline-src]" not in out
        assert "intentionally sparse" not in out

    def test_qmd_implementation_plan_baseline_collected_but_not_measured(
        self,
    ) -> None:
        # A baseline snapshot exists but the SQL did not yield a value
        # (Phase-3 FAILED / NOT_EXECUTED path) — the section still renders.
        data = {
            "baseline_snapshot": {
                "metric_name": "subrogation_recovery_rate",
                "value": None,
                "measurement_unit": "ratio",
                "query_execution_status": "FAILED",
                "caveats": [],
            }
        }
        out = render_qmd_implementation_plan(intake={}, data=data)
        assert "## Baseline" in out
        assert "(not measured) [^baseline-src]" in out
        assert "`FAILED`" in out
        # No measurement window recorded → placeholder, not a date range.
        assert "(not recorded)" in out
        # The provenance footnote is still emitted for a present snapshot.
        assert "[^baseline-src]: Baseline figures are sourced from" in out

    def test_intake_report_md_renders_governance(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_reports_intake_md(intake=intake)
        assert "tier_3_moderate" in out
        assert "tactical" in out
        assert "SR_26_2" in out

    def test_intake_report_md_renders_business_case(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_reports_intake_md(intake=intake)
        assert "## Cost of Inaction" in out
        assert "## Payback" in out
        assert "## Decision Rights" in out
        assert "$250,000 – $500,000" in out
        # The business case sits between Estimated Value and Governance.
        assert out.index("## Cost of Inaction") < out.index("## Governance")

    def test_intake_report_md_missing_fields_render_placeholders(self) -> None:
        out = render_reports_intake_md(intake={})
        assert "## Value Drivers" in out
        assert "- (none declared)" in out
        assert "(not specified)" in out
        # The Governance section still renders after the business case.
        assert "## Governance" in out

    def test_data_report_md_lists_expectations(
        self, data_report: DataReport
    ) -> None:
        data = data_report.model_dump(mode="json")
        out = render_reports_data_md(data=data)
        assert "Row count in the millions" in out
        assert "Information_completeness_score" in out


class TestBuildBaseFiles:
    def test_returns_expected_file_set(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
    ) -> None:
        files = build_base_files(
            intake=intake_report.model_dump(mode="json"),
            data=data_report.model_dump(mode="json"),
            project_name="subrogation-model",
            project_slug="subrogation_model",
        )

        expected = {
            ".gitignore",
            "README.md",
            "LICENSE",
            "pyproject.toml",
            "src/subrogation_model/__init__.py",
            "src/subrogation_model/data_loading.py",
            "src/subrogation_model/features.py",
            "src/subrogation_model/models.py",
            "src/subrogation_model/evaluation.py",
            "analysis/01_business_understanding.qmd",
            "analysis/02_data.qmd",
            "analysis/03_eda.qmd",
            "analysis/04_feature_engineering.qmd",
            "analysis/05_initial_models.qmd",
            "analysis/06_implementation_plan.qmd",
            "analysis/99_extensions.qmd",
            "tests/__init__.py",
            "tests/test_data_loading.py",
            "tests/test_features.py",
            "tests/test_models.py",
            "tests/test_evaluation.py",
            "data/README.md",
            "reports/intake_report.json",
            "reports/intake_report.md",
            "reports/data_report.json",
            "reports/data_report.md",
            "queries/primary/subrogation_training_set.sql",
            "queries/quality/subrogation_training_set/row_count_sanity.sql",
            "queries/quality/subrogation_training_set/target_nullability.sql",
        }
        assert expected <= set(files.keys())
        # Phase 4A MUST NOT emit governance artifacts yet
        for path in files:
            assert not path.startswith("governance/")
        assert "data/datasheet_subrogation_training_set.md" not in files
        assert ".gitlab-ci.yml" not in files
        assert ".pre-commit-config.yaml" not in files

    def test_primary_query_contents_match_sql(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
    ) -> None:
        files = build_base_files(
            intake=intake_report.model_dump(mode="json"),
            data=data_report.model_dump(mode="json"),
            project_name="subrogation-model",
            project_slug="subrogation_model",
        )
        sql = files["queries/primary/subrogation_training_set.sql"]
        assert "FROM claims_dw.public.claims" in sql
        assert sql.endswith("\n")

    def test_quality_check_contents_match(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
    ) -> None:
        files = build_base_files(
            intake=intake_report.model_dump(mode="json"),
            data=data_report.model_dump(mode="json"),
            project_name="subrogation-model",
            project_slug="subrogation_model",
        )
        row_count = files[
            "queries/quality/subrogation_training_set/row_count_sanity.sql"
        ]
        assert "SELECT COUNT(*)" in row_count

    def test_reports_json_round_trips_through_pydantic(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
    ) -> None:
        import json

        files = build_base_files(
            intake=intake_report.model_dump(mode="json"),
            data=data_report.model_dump(mode="json"),
            project_name="subrogation-model",
            project_slug="subrogation_model",
        )
        intake_json: Any = json.loads(files["reports/intake_report.json"])
        assert intake_json["status"] == "COMPLETE"
        data_json: Any = json.loads(files["reports/data_report.json"])
        assert data_json["status"] == "COMPLETE"

    def test_empty_data_report_yields_no_query_files(
        self, intake_report: IntakeReport
    ) -> None:
        empty_data = {
            "status": "COMPLETE",
            "summary": "",
            "primary_queries": [],
            "confirmed_expectations": [],
            "unconfirmed_expectations": [],
            "data_quality_concerns": [],
        }
        files = build_base_files(
            intake=intake_report.model_dump(mode="json"),
            data=empty_data,
            project_name="p",
            project_slug="p",
        )
        assert not any(path.startswith("queries/") for path in files)
