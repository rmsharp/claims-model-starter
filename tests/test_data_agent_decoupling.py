"""Enforce §7 of architecture-plan.md: the Data Agent knows nothing about IntakeReport.

AST-walks every module under ``src/model_project_constructor/agents/data/``
and fails the build if any ``import`` or ``from ... import ...`` statement
references the intake schema. This is the structural guarantee that lets the
Data Agent be reused standalone (constraint C4) and that lets its standalone
package be distributed without pulling in the orchestrator.
"""

from __future__ import annotations

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_AGENT_DIR = REPO_ROOT / "src" / "model_project_constructor" / "agents" / "data"

FORBIDDEN_SUBSTRINGS = (
    "IntakeReport",
    "schemas.v1.intake",
    "intake_report",
)


def test_data_agent_does_not_import_intake_report() -> None:
    files = sorted(DATA_AGENT_DIR.rglob("*.py"))
    assert files, f"expected python files under {DATA_AGENT_DIR}"

    offenders: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported = ast.unparse(node)
                for forbidden in FORBIDDEN_SUBSTRINGS:
                    if forbidden in imported:
                        offenders.append(
                            f"{path.relative_to(REPO_ROOT)}: {imported!r} "
                            f"contains forbidden token {forbidden!r}"
                        )

    assert not offenders, (
        "Data Agent decoupling violation — the following imports reference "
        "the intake schema, breaking §7 of architecture-plan.md:\n  - "
        + "\n  - ".join(offenders)
    )
