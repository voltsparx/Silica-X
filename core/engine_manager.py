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

"""Engine selection and runtime backend adapters for orchestration."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from time import perf_counter
from typing import Any, Literal, Protocol, cast

from core.execution_policy import ExecutionPolicy, load_execution_policy
from core.engines.async_engine import run_async_batch
from core.engines.engine_base import EngineBase
from core.engines.engine_result import EngineResult
from core.engines.parallel_engine import ParallelEngine
from core.engines.thread_engine import run_blocking
from core.utils.logging import get_logger


LOGGER = get_logger("engine_manager")
AsyncTaskFactory = Callable[[], Awaitable[Any]]


class ExecutionEngine(Protocol):
    """Execution backend contract."""

    async def run_detailed(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[EngineResult]:
        """Execute task factories and return standardized engine results."""

    async def run(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        """Execute async task factories and return ordered results."""

    def health_check(self) -> dict[str, Any]:
        """Return runtime health metrics for the engine."""


async def _run_with_timeout(task_factory: AsyncTaskFactory, timeout: float | None) -> Any:
    coroutine = task_factory()
    if timeout and timeout > 0:
        return await asyncio.wait_for(coroutine, timeout=float(timeout))
    return await coroutine


async def _await_awaitable(awaitable: Awaitable[Any]) -> Any:
    return await awaitable


def _resolve_timeout(runtime: Mapping[str, Any]) -> float | None:
    raw_timeout = runtime.get("timeout")
    if not isinstance(raw_timeout, (int, float)):
        return None
    timeout = float(raw_timeout)
    return timeout if timeout > 0 else None


def _extract_payloads(results: Sequence[EngineResult]) -> list[Any]:
    payloads: list[Any] = []
    for item in results:
        if item.status != "success":
            payloads.append(RuntimeError(item.error or f"{item.name} failed"))
            continue
        payloads.append(item.data.get("payload"))
    return payloads


class AsyncEngine(EngineBase):
    """Native async execution backend."""

    async def _run_one(self, task_factory: AsyncTaskFactory, *, timeout: float | None, index: int) -> EngineResult:
        name = self._task_name(task_factory, index=index)
        self._monitor.begin()
        started = perf_counter()
        try:
            outcome = await self.timeout_guard(task_factory(), timeout=timeout)
        except TimeoutError as exc:
            result = EngineResult(
                name=name,
                status="timeout",
                data={},
                error=str(exc),
                execution_time=perf_counter() - started,
            )
        except Exception as exc:  # pragma: no cover - isolation boundary
            result = EngineResult(
                name=name,
                status="failed",
                data={},
                error=str(exc),
                execution_time=perf_counter() - started,
            )
        else:
            result = EngineResult(
                name=name,
                status="success",
                data={"payload": outcome},
                error=None,
                execution_time=perf_counter() - started,
            )
        finally:
            self._monitor.end()
        self._monitor.record(result)
        return result

    async def run_detailed(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[EngineResult]:
        runtime = dict(context or {})
        max_workers = max(1, int(runtime.get("max_workers", 10)))
        timeout = _resolve_timeout(runtime)
        wrapped = [
            self._run_one(task_factory, timeout=timeout, index=index)
            for index, task_factory in enumerate(tasks, start=1)
        ]
        if not wrapped:
            return []
        return cast(
            list[EngineResult],
            await run_async_batch(
                wrapped,
                concurrency_limit=max_workers,
                return_exceptions=False,
            )
        )

    async def run(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        return _extract_payloads(await self.run_detailed(tasks=tasks, context=context))


class ThreadEngine(EngineBase):
    """Thread-backed execution backend for blocking environments."""

    async def _execute_one(self, task_factory: AsyncTaskFactory, *, timeout: float | None, index: int) -> EngineResult:
        def _runner() -> EngineResult:
            name = self._task_name(task_factory, index=index)
            started = perf_counter()
            coroutine = task_factory()
            try:
                if timeout and timeout > 0:
                    outcome = asyncio.run(asyncio.wait_for(coroutine, timeout=float(timeout)))
                else:
                    outcome = asyncio.run(_await_awaitable(coroutine))
            except TimeoutError as exc:
                return EngineResult(
                    name=name,
                    status="timeout",
                    data={},
                    error=str(exc),
                    execution_time=perf_counter() - started,
                )
            except Exception as exc:  # pragma: no cover - isolation boundary
                return EngineResult(
                    name=name,
                    status="failed",
                    data={},
                    error=str(exc),
                    execution_time=perf_counter() - started,
                )
            return EngineResult(
                name=name,
                status="success",
                data={"payload": outcome},
                error=None,
                execution_time=perf_counter() - started,
            )

        self._monitor.begin()
        try:
            result = await run_blocking(_runner)
        finally:
            self._monitor.end()
        self._monitor.record(result)
        return result

    async def run_detailed(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[EngineResult]:
        runtime = dict(context or {})
        max_workers = max(1, int(runtime.get("max_workers", 10)))
        timeout = _resolve_timeout(runtime)
        calls = [
            self._execute_one(task_factory, timeout=timeout, index=index)
            for index, task_factory in enumerate(tasks, start=1)
        ]
        if not calls:
            return []
        return cast(
            list[EngineResult],
            await run_async_batch(
                calls,
                concurrency_limit=max_workers,
                return_exceptions=False,
            )
        )

    async def run(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        return _extract_payloads(await self.run_detailed(tasks=tasks, context=context))


class ProcessEngine(EngineBase):
    """Process-backed interface with safe fallback for non-picklable callables."""

    _fallback_engine: AsyncEngine

    def __init__(self) -> None:
        super().__init__()
        self._fallback_engine = AsyncEngine(monitor=self._monitor)

    async def run_detailed(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[EngineResult]:
        LOGGER.warning("ProcessEngine is using async fallback for callable compatibility.")
        return await self._fallback_engine.run_detailed(tasks=tasks, context=context)

    async def run(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        return _extract_payloads(await self.run_detailed(tasks=tasks, context=context))


class HybridEngine(EngineBase):
    """Hybrid backend using the shared parallel engine."""

    def __init__(self) -> None:
        super().__init__()

    async def run_detailed(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[EngineResult]:
        runtime = dict(context or {})
        timeout = _resolve_timeout(runtime)
        worker_budget = max(1, int(runtime.get("max_workers", 10)))
        async_tasks = [_run_with_timeout(task_factory, timeout) for task_factory in tasks]
        if not async_tasks:
            return []
        for _ in async_tasks:
            self._monitor.begin()
        started = perf_counter()
        try:
            parallel = ParallelEngine(
                async_concurrency=worker_budget,
                thread_concurrency=worker_budget,
            )
            batch = await parallel.run_hybrid(async_tasks=async_tasks)
        finally:
            for _ in async_tasks:
                self._monitor.end()
        elapsed = perf_counter() - started
        results: list[EngineResult] = []
        for index, item in enumerate(batch.async_results, start=1):
            task_factory = tasks[index - 1]
            name = self._task_name(task_factory, index=index)
            if isinstance(item, Exception):
                status: Literal["timeout", "failed"] = "timeout" if isinstance(item, TimeoutError) else "failed"
                result = EngineResult(
                    name=name,
                    status=status,
                    data={},
                    error=str(item),
                    execution_time=elapsed / max(1, len(batch.async_results)),
                )
            else:
                result = EngineResult(
                    name=name,
                    status="success",
                    data={"payload": item},
                    error=None,
                    execution_time=elapsed / max(1, len(batch.async_results)),
                )
            self._monitor.record(result)
            results.append(result)
        return results

    async def run(
        self,
        tasks: Sequence[AsyncTaskFactory],
        context: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        return _extract_payloads(await self.run_detailed(tasks=tasks, context=context))


def get_engine(profile: ExecutionPolicy | str) -> ExecutionEngine:
    """Resolve execution engine from policy object or profile name."""

    policy = load_execution_policy(profile) if isinstance(profile, str) else profile
    engine_type = policy.engine_type.strip().lower()
    if engine_type == "async":
        return AsyncEngine()
    if engine_type == "thread":
        return ThreadEngine()
    if engine_type == "process":
        return ProcessEngine()
    return HybridEngine()
