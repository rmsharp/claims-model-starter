"""Version 1.0.0 payload schemas.

Every class in this package carries ``schema_version: Literal["1.0.0"] = "1.0.0"``
and is registered in :mod:`model_project_constructor.schemas.registry` under
the key ``(class_name, "1.0.0")``.
"""

from model_project_constructor.schemas.v1.common import (
    SCHEMA_VERSION,
    CycleTime,
    ModelType,
    RiskTier,
)
from model_project_constructor.schemas.v1.data import (
    ColumnMetadata,
    DataGranularity,
    DataReport,
    DataRequest,
    Datasheet,
    DataSourceEntry,
    DataSourceInventory,
    PrimaryQuery,
    ProducerMetadata,
    QualityCheck,
)
from model_project_constructor.schemas.v1.intake import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
)
from model_project_constructor.schemas.v1.repo import (
    GovernanceManifest,
    RepoProjectResult,
    RepoTarget,
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
    "ColumnMetadata",
    "DataGranularity",
    "DataReport",
    "DataRequest",
    "DataSourceEntry",
    "DataSourceInventory",
    "Datasheet",
    "PrimaryQuery",
    "ProducerMetadata",
    "QualityCheck",
    # repo
    "GovernanceManifest",
    "RepoProjectResult",
    "RepoTarget",
]
