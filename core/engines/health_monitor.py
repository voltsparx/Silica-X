# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root 
#
# This file is part of Silica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

"""Runtime health metrics for execution engines."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from core.engines.engine_result import EngineResult


@dataclass(frozen=True)
class EngineHealthSnapshot:
    """Immutable health snapshot used by orchestrator/reporting surfaces."""

    active_tasks: int
    failed_engines: int
    average_response_time: float
    memory_usage_mb: float | None
    engine_failure_counts: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "active_tasks": self.active_tasks,
            "failed_engines": self.failed_engines,
            "average_response_time": round(self.average_response_time, 4),
            "memory_usage_mb": self.memory_usage_mb,
            "engine_failure_counts": dict(self.engine_failure_counts),
        }


class EngineHealthMonitor:
    """Thread-safe monitor for core engine runtime metrics."""

    def __init__(self, *, latency_window: int = 500) -> None:
        self._latencies: deque[float] = deque(maxlen=max(10, int(latency_window)))
        self._failure_counts: dict[str, int] = {}
        self._active_tasks = 0
        self._lock = Lock()

    def begin(self) -> None:
        with self._lock:
            self._active_tasks += 1

    def end(self) -> None:
        with self._lock:
            self._active_tasks = max(0, self._active_tasks - 1)

    def record(self, result: EngineResult) -> None:
        with self._lock:
            self._latencies.append(max(0.0, float(result.execution_time)))
            if result.status != "success":
                key = str(result.name or "unknown").strip().lower() or "unknown"
                self._failure_counts[key] = self._failure_counts.get(key, 0) + 1

    def snapshot(self, *, memory_usage_mb: float | None = None) -> EngineHealthSnapshot:
        with self._lock:
            avg = (sum(self._latencies) / len(self._latencies)) if self._latencies else 0.0
            failures = dict(self._failure_counts)
            return EngineHealthSnapshot(
                active_tasks=self._active_tasks,
                failed_engines=sum(failures.values()),
                average_response_time=avg,
                memory_usage_mb=memory_usage_mb,
                engine_failure_counts=failures,
            )

    def merge_failures(self, counts: Mapping[str, int]) -> None:
        with self._lock:
            for key, value in counts.items():
                normalized = str(key).strip().lower()
                amount = int(value)
                if not normalized or amount <= 0:
                    continue
                self._failure_counts[normalized] = self._failure_counts.get(normalized, 0) + amount

