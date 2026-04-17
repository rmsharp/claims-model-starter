#!/usr/bin/env python3
"""First end-to-end pipeline run.

Drives the full Intake -> Data -> Website sequence using:
  - Pre-built fixture data for the Intake and Data stages (no LLM needed)
  - A FakeRepoClient that captures files in memory (no live host needed)

This is the recommended smoke test before graduating to live LLM calls
and a real GitLab/GitHub host.  See docs/tutorial.md for the full
walkthrough.

Usage
-----
    uv run python scripts/run_pipeline.py [OPTIONS]

Options:
    --run-id ID        Unique run identifier (default: auto-generated)
    --host HOST        "gitlab" or "github" (default: gitlab)
    --checkpoint-dir   Where to write checkpoint envelopes
                       (default: .orchestrator/checkpoints)
    --live             Use a real repo host instead of FakeRepoClient.
                       Requires GITLAB_TOKEN or GITHUB_TOKEN in the
                       environment (see .env.example).
    --llm {none,data}  Which stages use real Anthropic LLM calls.
                       "none" (default): fixture data for intake AND data
                                         (fastest, no API cost).
                       "data": intake fixture + real Anthropic data agent
                               (requires ANTHROPIC_API_KEY; ~$0.10-0.50/run
                               depending on --model).
    --model ID         Claude model for the real data agent (default:
                       claude-opus-4-7). Ignored when --llm=none.
    --db-url URL       SQLAlchemy URL for the data agent's read-only DB.
                       When omitted, data quality checks are generated but
                       not executed. Ignored when --llm=none.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so this script works whether
# invoked via `uv run python scripts/run_pipeline.py` or directly.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "data-agent" / "src"))

from model_project_constructor.agents.website.agent import WebsiteAgent  # noqa: E402
from model_project_constructor.agents.website.fake_client import FakeRepoClient  # noqa: E402
from model_project_constructor.orchestrator import (  # noqa: E402
    MetricsRegistry,
    OrchestratorSettings,
    PipelineConfig,
    make_logged_runner,
    make_measured_runner,
    run_pipeline,
)
from model_project_constructor.schemas.v1.data import DataReport  # noqa: E402
from model_project_constructor.schemas.v1.intake import IntakeReport  # noqa: E402
from model_project_constructor.schemas.v1.repo import RepoTarget  # noqa: E402

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_intake_fixture() -> IntakeReport:
    """Load the subrogation intake report fixture."""
    path = FIXTURE_DIR / "subrogation_intake.json"
    return IntakeReport.model_validate_json(path.read_text())


def load_data_fixture() -> DataReport:
    """Load the sample data report fixture."""
    path = FIXTURE_DIR / "sample_datareport.json"
    return DataReport.model_validate_json(path.read_text())


def build_repo_target(host: str) -> RepoTarget:
    """Build a RepoTarget appropriate for the selected host."""
    if host == "github":
        host_url = os.environ.get("MPC_HOST_URL", "https://api.github.com")
        namespace = os.environ.get("MPC_NAMESPACE", "my-org")
    else:
        host_url = os.environ.get("MPC_HOST_URL", "https://gitlab.com")
        namespace = os.environ.get("MPC_NAMESPACE", "data-science/model-drafts")

    return RepoTarget(
        host_url=host_url,
        namespace=namespace,
        project_name_hint="subrogation_pilot",
        visibility="private",
    )


def build_data_runner(*, llm_mode: str, db_url: str | None, model: str):
    """Return a DataRunner callable.

    In "none" mode, returns a closure that serves the fixture DataReport
    regardless of the request — preserves Scope A behavior.
    In "data" mode, binds a real ``DataAgent(AnthropicLLMClient(...), db)``
    to its ``.run`` method, which already matches the ``DataRunner`` shape.
    """
    if llm_mode == "none":
        data = load_data_fixture()
        return lambda _req: data

    from model_project_constructor_data_agent.agent import DataAgent
    from model_project_constructor_data_agent.anthropic_client import (
        AnthropicLLMClient,
    )
    from model_project_constructor_data_agent.db import ReadOnlyDB

    llm = AnthropicLLMClient(model=model)
    db = ReadOnlyDB(db_url) if db_url else None
    return DataAgent(llm=llm, db=db).run


def build_website_runner(*, host: str, live: bool):
    """Return a WebsiteRunner callable.

    In fake mode, uses FakeRepoClient (in-memory, no credentials).
    In live mode, constructs the real adapter for the chosen host.
    """
    ci_platform = host

    if not live:
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform=ci_platform)
        return agent.run, client  # return client so we can inspect files

    # Live mode: build the real adapter
    settings = OrchestratorSettings.from_env()
    token = settings.require_host_token()

    if host == "github":
        from model_project_constructor.agents.website.github_adapter import (
            PyGithubAdapter,
        )
        client = PyGithubAdapter(token=token)
    else:
        from model_project_constructor.agents.website.gitlab_adapter import (
            PythonGitLabAdapter,
        )
        host_url = os.environ.get("MPC_HOST_URL", "https://gitlab.com")
        client = PythonGitLabAdapter(host_url=host_url, private_token=token)

    agent = WebsiteAgent(client, ci_platform=ci_platform)
    return agent.run, None  # no fake client to inspect


def instrument(runner, *, name: str, config: PipelineConfig, metrics: MetricsRegistry):
    """Wrap a runner with logging + metrics."""
    return make_logged_runner(
        make_measured_runner(runner, agent_name=name, registry=metrics),
        agent_name=name,
        run_id=config.run_id,
        correlation_id=config.correlation_id,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Model Project Constructor pipeline end-to-end.",
    )
    parser.add_argument(
        "--run-id",
        default=f"run_{uuid.uuid4().hex[:8]}",
        help="Unique run identifier (default: auto-generated)",
    )
    parser.add_argument(
        "--host",
        choices=["gitlab", "github"],
        default="gitlab",
        help="Target repo host (default: gitlab)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path(".orchestrator/checkpoints"),
        help="Checkpoint directory (default: .orchestrator/checkpoints)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use a real repo host (requires host token in env)",
    )
    parser.add_argument(
        "--llm",
        choices=["none", "data"],
        default="none",
        help=(
            "Which stages use real Anthropic LLM calls "
            "(default: none = fixture data)"
        ),
    )
    parser.add_argument(
        "--model",
        default="claude-opus-4-7",
        help=(
            "Claude model for the real data agent "
            "(default: claude-opus-4-7; ignored when --llm=none)"
        ),
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help=(
            "SQLAlchemy URL for the data agent's read-only DB "
            "(default: None = quality checks generated but not executed; "
            "ignored when --llm=none)"
        ),
    )
    args = parser.parse_args()

    # --- Banner ---
    mode = "LIVE" if args.live else "FAKE (dry run)"
    llm_label = "fixture" if args.llm == "none" else f"data={args.model}"
    print(f"\n{'=' * 60}")
    print("  Model Project Constructor — End-to-End Pipeline Run")
    print(f"  Mode: {mode}  |  Host: {args.host}  |  LLM: {llm_label}")
    print(f"  Run ID: {args.run_id}")
    print(f"{'=' * 60}\n")

    # --- Load fixture data ---
    print("[1/5] Loading fixture data...")
    intake = load_intake_fixture()
    print(f"      Intake: {intake.model_solution.target_variable} "
          f"({intake.model_solution.model_type})")
    if args.llm == "none":
        data_preview = load_data_fixture()
        print(f"      Data:   {len(data_preview.primary_queries)} queries "
              f"(fixture), "
              f"{len(data_preview.confirmed_expectations)} confirmed expectations")
    else:
        print(f"      Data:   real Anthropic "
              f"(model={args.model}, "
              f"db={'connected' if args.db_url else 'disconnected'})")

    # --- Build config ---
    print("[2/5] Building pipeline config...")
    repo_target = build_repo_target(args.host)
    config = PipelineConfig(
        run_id=args.run_id,
        repo_target=repo_target,
        checkpoint_dir=args.checkpoint_dir,
    )
    print(f"      Target: {repo_target.namespace} on {repo_target.host_url}")
    print(f"      Checkpoints: {config.checkpoint_dir}")

    # --- Build runners ---
    print("[3/5] Wiring runners...")
    website_runner, fake_client = build_website_runner(
        host=args.host, live=args.live,
    )
    metrics = MetricsRegistry()

    intake_runner = instrument(
        lambda: intake, name="intake", config=config, metrics=metrics,
    )
    data_runner = instrument(
        build_data_runner(
            llm_mode=args.llm, db_url=args.db_url, model=args.model,
        ),
        name="data", config=config, metrics=metrics,
    )
    website_runner_instrumented = instrument(
        website_runner, name="website", config=config, metrics=metrics,
    )
    print("      Runners ready.")

    # --- Run pipeline ---
    print("[4/5] Running pipeline...")
    result = run_pipeline(
        config,
        intake_runner=intake_runner,
        data_runner=data_runner,
        website_runner=website_runner_instrumented,
    )
    metrics.record_run(result.status)

    # --- Report ---
    print("\n[5/5] Pipeline complete.")
    print(f"\n{'=' * 60}")
    print("  RESULT")
    print(f"{'=' * 60}")
    print(f"  Status:  {result.status}")
    if result.project_url:
        print(f"  Project: {result.project_url}")
    if result.failure_reason:
        print(f"  Failure: {result.failure_reason}")

    # Show metrics
    snap = metrics.snapshot()
    print("\n  Metrics:")
    print(f"    Total runs:  {snap.run_count}")
    print(f"    Status dist: {snap.status_counts}")
    for agent_name, latency in snap.agent_latency.items():
        print(f"    {agent_name}: {latency.mean_ms:.0f}ms avg "
              f"({latency.count} call(s))")

    # Show checkpoint files
    checkpoint_dir = config.checkpoint_dir / args.run_id
    if checkpoint_dir.exists():
        files = sorted(checkpoint_dir.iterdir())
        print(f"\n  Checkpoints ({checkpoint_dir}):")
        for f in files:
            size = f.stat().st_size
            print(f"    {f.name} ({size:,} bytes)")

    # Show generated files (fake mode only)
    if fake_client and fake_client.projects:
        project = next(iter(fake_client.projects.values()))
        print(f"\n  Generated project: {project.url}")
        print(f"  Files ({len(project.files)}):")
        for path in sorted(project.files):
            print(f"    {path}")

    print(f"\n{'=' * 60}\n")

    # Exit with appropriate code
    sys.exit(0 if result.status == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
