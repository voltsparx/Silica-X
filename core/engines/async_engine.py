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

"""Silica-X native async engine task map.

Network-bound OSINT work should run through the async layer.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from typing import Final

from core.engines.engine_base import EngineBase


ASYNC_TASKS: Final[dict[str, str]] = {
    # Username intelligence
    "platform_existence_checks": "async HTTP status checks",
    "profile_page_fetch": "aiohttp page retrieval",
    "bio/link extraction": "async fetch + parse",
    # Domain intelligence
    "crt_sh_queries": "certificate transparency lookups",
    "rdap_api_calls": "async RDAP queries",
    "http_probe": "security headers & tech detection",
    # Enrichment
    "avatar_download": "async media fetch",
    "public API enrichment": "GitHub, Reddit, etc.",
}


WORKFLOW_ASYNC_PHASES: Final[dict[str, list[str]]] = {
    "profile": [
        "platform_existence_checks",
        "profile_page_fetch",
        "avatar_download",
    ],
    "surface": [
        "crt_sh_queries",
        "rdap_api_calls",
        "http_probe",
    ],
    "fusion": [
        "public API enrichment",
    ],
}


ENGINE_RULES: Final[tuple[str, ...]] = (
    "Network wait -> ASYNC",
    "Blocks interpreter -> THREAD",
    "Needs full dataset -> SYNC",
)

DEFAULT_ASYNC_CONCURRENCY: Final[int] = 25
MAX_ASYNC_CONCURRENCY: Final[int] = 120


def async_tasks_for_workflow(workflow: str) -> list[str]:
    """Return async task keys for a workflow name."""

    return list(WORKFLOW_ASYNC_PHASES.get(workflow.strip().lower(), []))


def recommend_async_concurrency(task_count: int, requested_limit: int = DEFAULT_ASYNC_CONCURRENCY) -> int:
    """Pick an efficient async batch size for current workload."""

    bounded_request = max(1, int(requested_limit))
    if task_count <= 0:
        return 1
    return min(MAX_ASYNC_CONCURRENCY, bounded_request, task_count)


async def run_async_batch(
    coroutines: Sequence[Awaitable[object]],
    *,
    concurrency_limit: int = DEFAULT_ASYNC_CONCURRENCY,
    return_exceptions: bool = False,
) -> list[object]:
    """Run async tasks with bounded concurrency.

    This keeps large workflow batches from over-saturating sockets while still
    maximizing network throughput.
    """

    if not coroutines:
        return []

    effective_limit = recommend_async_concurrency(len(coroutines), concurrency_limit)
    if effective_limit >= len(coroutines):
        return list(await asyncio.gather(*coroutines, return_exceptions=return_exceptions))

    semaphore = asyncio.Semaphore(effective_limit)

    async def _guarded(coro: Awaitable[object]) -> object:
        async with semaphore:
            return await coro

    tasks = [asyncio.create_task(_guarded(coro)) for coro in coroutines]
    return list(await asyncio.gather(*tasks, return_exceptions=return_exceptions))


class AsyncEngine(EngineBase):
    """Async-native engine using asyncio.gather with bounded concurrency."""

    def __init__(self, *, concurrency_limit: int = DEFAULT_ASYNC_CONCURRENCY, monitor=None) -> None:
        super().__init__(monitor=monitor)
        self._concurrency_limit = max(1, int(concurrency_limit))

    async def run(self, tasks, context=None):
        coros = [task() for task in tasks]
        return list(
            await run_async_batch(
                coros,
                concurrency_limit=self._concurrency_limit,
                return_exceptions=True,
            )
        )
