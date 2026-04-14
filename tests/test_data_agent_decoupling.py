"""Enforce §7 of architecture-plan.md: the Data Agent knows nothing about IntakeReport.

AST-walks every module under the standalone package
``packages/data-agent/src/model_project_constructor_data_agent/`` and fails
the build if any ``import`` or ``from ... import ...`` statement references
the intake schema. This is the structural guarantee that lets the Data Agent
be reused standalone (constraint C4) and that lets its standalone wheel be
distributed without pulling in the orchestrator.

The main ``model_project_constructor.agents.data.*`` modules are thin
re-export shims and are also walked here as defense in depth — a shim that
accidentally started importing ``IntakeReport`` would defeat the guarantee.
"""

from __future__ import annotations

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STANDALONE_DIR = (
    REPO_ROOT / "packages" / "data-agent" / "src" / "model_project_constructor_data_agent"
)
SHIM_DIR = REPO_ROOT / "src" / "model_project_constructor" / "agents" / "data"

FORBIDDEN_SUBSTRINGS = (
    "IntakeReport",
    "schemas.v1.intake",
    "intake_report",
)


def _walk_imports(root: pathlib.Path) -> list[str]:
    files = sorted(root.rglob("*.py"))
    assert files, f"expected python files under {root}"

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
    return offenders


def test_standalone_package_does_not_import_intake_report() -> None:
    offenders = _walk_imports(STANDALONE_DIR)
    assert not offenders, (
        "Standalone Data Agent decoupling violation — the following imports "
        "reference the intake schema, breaking §7 of architecture-plan.md:\n  - "
        + "\n  - ".join(offenders)
    )


def test_main_package_data_agent_shim_does_not_import_intake_report() -> None:
    offenders = _walk_imports(SHIM_DIR)
    assert not offenders, (
        "Main-package Data Agent shim decoupling violation — the following "
        "imports reference the intake schema, breaking §7 of architecture-plan.md:\n  - "
        + "\n  - ".join(offenders)
    )
