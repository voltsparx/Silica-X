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

"""Lightweight scheduler for delayed scan execution."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class _ScheduledJob:
    run_at: float
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class Scheduler:
    """Simple in-memory scheduler used by blueprint tests."""

    def __init__(self) -> None:
        self._jobs: list[_ScheduledJob] = []

    def schedule_scan(
        self,
        func: Callable[..., Any],
        target: Any,
        delay_seconds: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        run_at = time.time() + max(0.0, float(delay_seconds))
        self._jobs.append(_ScheduledJob(run_at=run_at, func=func, args=(target, *args), kwargs=kwargs))

    async def run_pending(self, *, now: float | None = None) -> list[dict[str, Any]]:
        """Run scheduled jobs that are due and return result envelopes."""

        current = time.time() if now is None else float(now)
        ready: list[_ScheduledJob] = [job for job in self._jobs if job.run_at <= current]
        self._jobs = [job for job in self._jobs if job.run_at > current]

        results: list[dict[str, Any]] = []
        for job in ready:
            try:
                payload = job.func(*job.args, **job.kwargs)
                results.append({"ok": True, "result": payload})
            except Exception as exc:  # pragma: no cover - defensive guard
                results.append({"ok": False, "error": str(exc), "result": None})
        return results

    def merge_results(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        """Deep-merge dictionaries, preferring values from `right`."""

        merged = dict(left)
        for key, value in right.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_results(merged[key], value)
            else:
                merged[key] = value
        return merged

    def send_alert(self, target: str, risk: dict[str, Any]) -> str:
        """Return a minimal alert string."""

        risk_score = risk.get("risk_score", "-")
        return f"alert target={target} risk_score={risk_score}"


__all__ = ["Scheduler"]
