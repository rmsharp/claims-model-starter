"""Tests for the website agent's base-scaffolding templates."""

from __future__ import annotations

from typing import Any

import pytest

from model_project_constructor.agents.website.templates import (
    build_base_files,
    derive_project_name,
    derive_project_slug,
    render_data_loading,
    render_evaluation,
    render_gitignore,
    render_models,
    render_pyproject,
    render_qmd_business_understanding,
    render_qmd_data,
    render_qmd_implementation_plan,
    render_qmd_initial_models,
    render_readme,
    render_reports_intake_md,
    render_reports_data_md,
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
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_qmd_implementation_plan(intake=intake)
        assert "$2,000,000" in out
        assert "$4,000,000" in out

    def test_qmd_implementation_plan_handles_missing_estimate(self) -> None:
        out = render_qmd_implementation_plan(intake={"estimated_value": {}})
        assert "not estimated" in out
        assert "(none declared)" in out

    def test_intake_report_md_renders_governance(
        self, intake_report: IntakeReport
    ) -> None:
        intake = intake_report.model_dump(mode="json")
        out = render_reports_intake_md(intake=intake)
        assert "tier_3_moderate" in out
        assert "tactical" in out
        assert "SR_11_7" in out

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
