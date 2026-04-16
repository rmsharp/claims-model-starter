"""In-memory metrics registry for the orchestrator pipeline.

Phase 6 scope (architecture-plan §14): counts of runs, status
distribution, per-agent latency. A Prometheus exporter is a post-pilot
concern — the registry is deliberately plain Python so tests and small
deployments can introspect state directly, and a future drop-in can
wrap or replace it without touching the call sites.

The public surface:

- :class:`MetricsRegistry` — thread-safe in-memory state.
- :class:`MetricsSnapshot` + :class:`LatencySamples` — immutable view of
  the registry for assertions and dashboards.
- :func:`make_measured_runner` — wraps a pipeline runner callable so
  each invocation records its latency against ``registry`` under
  ``agent_name``. The wrapper preserves the runner's signature and
  records latency even if the runner raises.

Like :mod:`.logging`, this module is NOT imported by ``pipeline.py`` —
the caller composes instrumented runners before handing them to
:func:`run_pipeline`, and calls :meth:`MetricsRegistry.record_run` on
the resulting :class:`PipelineResult`.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class LatencySamples:
    """Running aggregates for one agent's latency (milliseconds)."""

    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def record(self, ms: float) -> None:
        self.count += 1
        self.total_ms += ms
        if ms > self.max_ms:
            self.max_ms = ms

    @property
    def mean_ms(self) -> float:
        return self.total_ms / self.count if self.count else 0.0


@dataclass(frozen=True)
class MetricsSnapshot:
    """Immutable view of a :class:`MetricsRegistry` at one point in time."""

    run_count: int
    status_counts: dict[str, int]
    agent_latency: dict[str, LatencySamples]


class MetricsRegistry:
    """Thread-safe in-memory metrics for a single process.

    All mutations are guarded by a single lock because Phase 6 volumes
    are small (one run ≈ minutes of agent work, latency recorded thrice
    per run) and correctness matters more than throughput. A future
    Prometheus-backed implementation can replace this class wholesale.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._run_count = 0
        self._status_counts: dict[str, int] = defaultdict(int)
        self._agent_latency: dict[str, LatencySamples] = defaultdict(LatencySamples)

    def record_run(self, status: str) -> None:
        """Record one completed pipeline run with its terminal status."""

        with self._lock:
            self._run_count += 1
            self._status_counts[status] += 1

    def record_agent_latency(self, agent: str, duration_ms: float) -> None:
        """Record one agent-call latency sample in milliseconds."""

        with self._lock:
            self._agent_latency[agent].record(duration_ms)

    def snapshot(self) -> MetricsSnapshot:
        """Return an immutable snapshot decoupled from live mutation."""

        with self._lock:
            return MetricsSnapshot(
                run_count=self._run_count,
                status_counts=dict(self._status_counts),
                agent_latency={
                    name: LatencySamples(
                        count=samples.count,
                        total_ms=samples.total_ms,
                        max_ms=samples.max_ms,
                    )
                    for name, samples in self._agent_latency.items()
                },
            )

    def reset(self) -> None:
        """Clear all state. Intended for test isolation."""

        with self._lock:
            self._run_count = 0
            self._status_counts.clear()
            self._agent_latency.clear()


def make_measured_runner(
    runner: Callable[..., T],
    *,
    agent_name: str,
    registry: MetricsRegistry,
) -> Callable[..., T]:
    """Wrap ``runner`` so its latency is recorded against ``registry``.

    Latency is measured with ``time.perf_counter`` and recorded via the
    ``finally`` clause, so exceptions still produce a sample. The
    original exception propagates unchanged.
    """

    def wrapped(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        try:
            return runner(*args, **kwargs)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            registry.record_agent_latency(agent_name, duration_ms)

    return wrapped


__all__ = [
    "LatencySamples",
    "MetricsRegistry",
    "MetricsSnapshot",
    "make_measured_runner",
]
