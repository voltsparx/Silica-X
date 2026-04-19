# ──────────────────────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Any

from core.engines.engine_base import EngineBase
from core.engines.engine_result import EngineResult
from core.engines.health_monitor import EngineHealthMonitor


class StabilizerEngine(EngineBase):
    """Resilience wrapper that adds retry, circuit breaking, and fallback."""

    def __init__(
        self,
        inner: EngineBase,
        *,
        max_retries: int = 2,
        base_delay: float = 0.5,
        circuit_threshold: int = 5,
        reset_after_seconds: float = 60.0,
        fallback_value: Any = None,
        monitor=None,
    ) -> None:
        super().__init__(monitor=monitor)
        self._inner = inner
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._circuit_threshold = circuit_threshold
        self._reset_after = reset_after_seconds
        self._fallback = fallback_value
        self._consecutive_failures = 0
        self._circuit_opened_at: float | None = None
        self.failure_log: list[str] = []

    def _circuit_is_open(self) -> bool:
        import time

        if self._consecutive_failures < self._circuit_threshold:
            return False
        if self._circuit_opened_at is None:
            return True
        if time.monotonic() - self._circuit_opened_at >= self._reset_after:
            self.reset()
            return False
        return True

    def reset(self) -> None:
        self._consecutive_failures = 0
        self._circuit_opened_at = None

    async def run(self, tasks, context=None) -> list[Any]:
        import asyncio
        import time

        task_list = list(tasks)
        if self._circuit_is_open():
            return [self._fallback] * len(task_list)
        results = []
        for task in task_list:
            result = self._fallback
            for attempt in range(self._max_retries + 1):
                try:
                    inner_results = await self._inner.run([task], context=context)
                    result = inner_results[0] if inner_results else self._fallback
                    if isinstance(result, BaseException):
                        raise result
                    self._consecutive_failures = 0
                    break
                except Exception as exc:
                    reason = f"attempt={attempt} task={getattr(task, '__name__', '?')} err={exc}"
                    self.failure_log.append(reason)
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= self._circuit_threshold:
                        self._circuit_opened_at = time.monotonic()
                    if attempt < self._max_retries:
                        delay = self._base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        result = self._fallback
            results.append(result)
        return results


__all__ = ["EngineBase", "EngineResult", "EngineHealthMonitor", "StabilizerEngine"]
