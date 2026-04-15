"""Envelope-based checkpoint store (architecture-plan §6, §12).

Each inter-agent handoff is wrapped in a :class:`HandoffEnvelope` and
written to disk under ``<base_dir>/<run_id>/<payload_type>.json``. The
store is intentionally flat:

- No database, no migrations, no locking. A pipeline run is sequential
  and single-writer per §4, so the filesystem is sufficient.
- The key is ``payload_type``, not ``source_agent``. The registry already
  maps payload types to their canonical source (only the Website Agent
  produces ``RepoProjectResult``, only Intake produces ``IntakeReport``),
  so prefixing the filename with the source would be redundant.
- Re-running a pipeline with the same ``run_id`` overwrites the previous
  checkpoint. Resumption support (reading back an envelope and skipping
  an earlier stage) is deferred to Phase 6, but the on-disk format is
  ready for it.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from model_project_constructor.schemas.envelope import HandoffEnvelope
from model_project_constructor.schemas.registry import load_payload


class CheckpointStore:
    """Persist and retrieve pipeline handoff artifacts on disk.

    Two kinds of artifacts are stored under ``<base_dir>/<run_id>/``:

    - **Envelopes**: inter-agent handoffs wrapped in a
      :class:`HandoffEnvelope` and written as ``<payload_type>.json``.
      These are what resumption replays.
    - **Terminal results**: the orchestrator's own outputs (most
      importantly the final ``RepoProjectResult``), written via
      :meth:`save_result` as ``<name>.json`` with a plain Pydantic
      model_dump. They are NOT wrapped in an envelope because the
      Phase 1 envelope invariant is that the orchestrator never
      *receives* an envelope — it only sends them between agents.
    """

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)

    def _run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def _envelope_path(self, run_id: str, payload_type: str) -> Path:
        return self._run_dir(run_id) / f"{payload_type}.json"

    def _result_path(self, run_id: str, name: str) -> Path:
        return self._run_dir(run_id) / f"{name}.result.json"

    def save(self, envelope: HandoffEnvelope) -> Path:
        """Write ``envelope`` to ``<base_dir>/<run_id>/<payload_type>.json``.

        Creates the run directory on first write. Returns the path the
        envelope was written to so callers can log / assert on it.
        """

        run_dir = self._run_dir(envelope.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        path = self._envelope_path(envelope.run_id, envelope.payload_type)
        path.write_text(envelope.model_dump_json(indent=2))
        return path

    def save_result(self, run_id: str, name: str, model: BaseModel) -> Path:
        """Persist the orchestrator's terminal artifact (non-envelope).

        Written alongside the envelopes in the same run directory, with
        a ``.result.json`` suffix so it does not collide with the
        envelope filename namespace even if ``name`` happens to match a
        registered payload type.
        """

        run_dir = self._run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        path = self._result_path(run_id, name)
        path.write_text(model.model_dump_json(indent=2))
        return path

    def load(self, run_id: str, payload_type: str) -> HandoffEnvelope:
        """Read a previously-saved envelope. Raises ``FileNotFoundError``."""

        path = self._envelope_path(run_id, payload_type)
        return HandoffEnvelope.model_validate_json(path.read_text())

    def load_payload(self, run_id: str, payload_type: str) -> BaseModel:
        """Load an envelope and resolve its payload via the schema registry."""

        envelope = self.load(run_id, payload_type)
        return load_payload(envelope)

    def has(self, run_id: str, payload_type: str) -> bool:
        """Return True iff an envelope for ``(run_id, payload_type)`` exists."""

        return self._envelope_path(run_id, payload_type).exists()

    def has_result(self, run_id: str, name: str) -> bool:
        """Return True iff a terminal result artifact exists."""

        return self._result_path(run_id, name).exists()

    def list_payload_types(self, run_id: str) -> list[str]:
        """Return the sorted list of payload types checkpointed for ``run_id``.

        Excludes terminal ``.result.json`` artifacts — those are not
        envelopes and are listed separately via
        :meth:`list_result_names`.
        """

        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            return []
        return sorted(
            p.stem for p in run_dir.glob("*.json") if not p.name.endswith(".result.json")
        )

    def list_result_names(self, run_id: str) -> list[str]:
        """Return the sorted list of terminal result artifacts for ``run_id``."""

        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            return []
        return sorted(p.name[: -len(".result.json")] for p in run_dir.glob("*.result.json"))


__all__ = ["CheckpointStore"]
