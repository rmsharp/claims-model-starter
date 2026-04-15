"""End-to-end tests for WebsiteAgent.run()."""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeGitLabClient
from model_project_constructor.schemas.v1.gitlab import GitLabTarget


class TestWebsiteAgentRun:
    def test_happy_path_produces_complete_result(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, data_report, gitlab_target)

        assert result.status == "COMPLETE"
        assert result.failure_reason is None
        assert result.project_url.endswith("/subrogation-recovery-model")
        assert result.project_id == 1000
        assert len(result.initial_commit_sha) == 40

    def test_all_section_11_base_files_scaffolded(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, data_report, gitlab_target)

        files = set(result.files_created)

        # Root files
        assert ".gitignore" in files
        assert "README.md" in files
        assert "pyproject.toml" in files

        # src/ module
        for name in ("__init__", "data_loading", "features", "models", "evaluation"):
            assert f"src/subrogation_recovery_model/{name}.py" in files

        # analysis qmd narratives — all seven from §11
        for qmd in (
            "01_business_understanding",
            "02_data",
            "03_eda",
            "04_feature_engineering",
            "05_initial_models",
            "06_implementation_plan",
            "99_extensions",
        ):
            assert f"analysis/{qmd}.qmd" in files

        # tests/ scaffolds
        assert "tests/__init__.py" in files
        for stub in ("data_loading", "features", "models", "evaluation"):
            assert f"tests/test_{stub}.py" in files

        # Reports
        assert "reports/intake_report.json" in files
        assert "reports/intake_report.md" in files
        assert "reports/data_report.json" in files
        assert "reports/data_report.md" in files

        # Queries from the data report
        assert "queries/primary/subrogation_training_set.sql" in files
        assert (
            "queries/quality/subrogation_training_set/row_count_sanity.sql" in files
        )

        # Data dictionary
        assert "data/README.md" in files

    def test_governance_artifacts_absent_in_4a(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, data_report, gitlab_target)
        files = set(result.files_created)

        assert not any(f.startswith("governance/") for f in files)
        assert "data/datasheet_subrogation_training_set.md" not in files
        assert ".gitlab-ci.yml" not in files
        assert ".pre-commit-config.yaml" not in files
        assert result.governance_manifest.artifacts_created == []

    def test_files_persisted_in_fake_client(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, data_report, gitlab_target)

        stored = fake_client.get_files(result.project_id)
        # README mentions the project and the business problem
        assert "subrogation-recovery-model" in stored["README.md"]
        assert "Subrogation recovery dropped" in stored["README.md"]
        # Primary SQL is committed verbatim from the data report
        assert "FROM claims_dw.public.claims" in stored[
            "queries/primary/subrogation_training_set.sql"
        ]

    def test_name_conflict_appends_suffix_end_to_end(
        self,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        client = FakeGitLabClient(
            existing_names={"data-science/model-drafts/subrogation-recovery-model"}
        )
        agent = WebsiteAgent(client)
        result = agent.run(intake_report, data_report, gitlab_target)

        assert result.status == "COMPLETE"
        assert result.project_url.endswith("subrogation-recovery-model-v2")

    def test_incomplete_intake_report_halts(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        incomplete = intake_report.model_copy(
            update={"status": "DRAFT_INCOMPLETE", "missing_fields": ["x"]}
        )
        agent = WebsiteAgent(fake_client)
        result = agent.run(incomplete, data_report, gitlab_target)

        assert result.status == "FAILED"
        assert "intake_status" in (result.failure_reason or "")
        # Nothing was created in GitLab
        assert fake_client.projects == {}

    def test_incomplete_data_report_halts(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        incomplete = data_report.model_copy(update={"status": "EXECUTION_FAILED"})
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, incomplete, gitlab_target)

        assert result.status == "FAILED"
        assert "data_status" in (result.failure_reason or "")
        assert fake_client.projects == {}

    def test_governance_manifest_reflects_intake_tier(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: GitLabTarget,
    ) -> None:
        agent = WebsiteAgent(fake_client)
        result = agent.run(intake_report, data_report, gitlab_target)

        # Manifest is empty in 4A but the tier/cycle time must mirror intake
        assert result.governance_manifest.risk_tier == "tier_3_moderate"
        assert result.governance_manifest.cycle_time == "tactical"
