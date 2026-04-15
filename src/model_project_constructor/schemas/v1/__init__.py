"""Version 1.0.0 payload schemas.

Every class in this package carries ``schema_version: Literal["1.0.0"] = "1.0.0"``
and is registered in :mod:`model_project_constructor.schemas.registry` under
the key ``(class_name, "1.0.0")``.
"""

from model_project_constructor.schemas.v1.common import (
    CycleTime,
    ModelType,
    RiskTier,
    SCHEMA_VERSION,
)
from model_project_constructor.schemas.v1.data import (
    DataGranularity,
    DataReport,
    DataRequest,
    Datasheet,
    PrimaryQuery,
    QualityCheck,
)
from model_project_constructor.schemas.v1.repo import (
    GovernanceManifest,
    RepoProjectResult,
    RepoTarget,
)
from model_project_constructor.schemas.v1.intake import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
)

__all__ = [
    "SCHEMA_VERSION",
    "CycleTime",
    "ModelType",
    "RiskTier",
    # intake
    "EstimatedValue",
    "GovernanceMetadata",
    "IntakeReport",
    "ModelSolution",
    # data
    "DataGranularity",
    "DataReport",
    "DataRequest",
    "Datasheet",
    "PrimaryQuery",
    "QualityCheck",
    # repo
    "GovernanceManifest",
    "RepoProjectResult",
    "RepoTarget",
]
