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


class SyncEngine(EngineBase):
    """Runs synchronous blocking tasks in a dedicated thread pool."""

    DEFAULT_MAX_WORKERS = 4

    def __init__(self, *, max_workers: int = DEFAULT_MAX_WORKERS, monitor=None) -> None:
        super().__init__(monitor=monitor)
        self._max_workers = max(1, int(max_workers))

    async def run(self, tasks, context=None) -> list[Any]:
        """Execute sync callables in thread pool, return results list."""

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_event_loop()
        results = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futs = [loop.run_in_executor(pool, task) for task in tasks]
            gathered = await asyncio.gather(*futs, return_exceptions=True)
            results = list(gathered)
        return results


__all__ = ["EngineBase", "EngineResult", "EngineHealthMonitor", "SyncEngine"]
