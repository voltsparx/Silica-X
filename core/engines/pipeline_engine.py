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

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any


class PipelineEventType(str, Enum):
    SCAN_STARTED = "scan_started"
    MODULE_STARTED = "module_started"
    RESULT_EMITTED = "result_emitted"
    SIGNAL_FOUND = "signal_found"
    MODULE_DONE = "module_done"
    SCAN_DONE = "scan_done"
    ERROR = "error"


@dataclass
class PipelineEvent:
    event_type: PipelineEventType
    source: str
    target: str
    data: dict
    timestamp: float = field(default_factory=perf_counter)
    sequence: int = 0


class PipelineEngine:
    def __init__(self, *, buffer_size: int = 512, timeout_per_module: float = 120.0) -> None:
        self.buffer_size = max(1, int(buffer_size))
        self.timeout_per_module = float(timeout_per_module)
        self._queue: asyncio.Queue[PipelineEvent] = asyncio.Queue(maxsize=self.buffer_size)
        self._sequence = 0
        self._dropped_count = 0
        self._subscribers: list[Callable[[PipelineEvent], Awaitable[None]]] = []
        self._stream_queues: list[asyncio.Queue[PipelineEvent]] = []
        self._history: list[PipelineEvent] = []

    def subscribe(self, handler: Callable[[PipelineEvent], Awaitable[None]]) -> None:
        self._subscribers.append(handler)

    def emit(self, event: PipelineEvent) -> None:
        self._sequence += 1
        event.sequence = self._sequence
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._dropped_count += 1
            return
        self._history.append(event)

    async def dispatch_loop(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                stale_streams: list[asyncio.Queue[PipelineEvent]] = []
                for stream_queue in self._stream_queues:
                    try:
                        stream_queue.put_nowait(event)
                    except asyncio.QueueFull:
                        self._dropped_count += 1
                        stale_streams.append(stream_queue)
                for stale_stream in stale_streams:
                    if stale_stream in self._stream_queues:
                        self._stream_queues.remove(stale_stream)

                if self._subscribers:
                    results = await asyncio.gather(
                        *(handler(event) for handler in list(self._subscribers)),
                        return_exceptions=True,
                    )
                    _ = results
            finally:
                self._queue.task_done()

    async def run_pipeline(
        self,
        target: str,
        stages: list[Callable[[str, PipelineEngine], Awaitable[dict]]],
    ) -> dict[str, Any]:
        started_at = perf_counter()
        dispatcher_task = asyncio.create_task(self.dispatch_loop())
        stage_results: dict[str, Any] = {}

        self.emit(
            PipelineEvent(
                event_type=PipelineEventType.SCAN_STARTED,
                source="pipeline",
                target=target,
                data={"stage_count": len(stages)},
            )
        )

        try:
            for stage in stages:
                stage_name = getattr(stage, "__name__", "stage")
                self.emit(
                    PipelineEvent(
                        event_type=PipelineEventType.MODULE_STARTED,
                        source=stage_name,
                        target=target,
                        data={"stage": stage_name},
                    )
                )
                try:
                    stage_result = await asyncio.wait_for(
                        stage(target, self),
                        timeout=self.timeout_per_module,
                    )
                    stage_results[stage_name] = stage_result
                    self.emit(
                        PipelineEvent(
                            event_type=PipelineEventType.MODULE_DONE,
                            source=stage_name,
                            target=target,
                            data={"stage": stage_name, "result": stage_result},
                        )
                    )
                except Exception as exc:
                    self.emit(
                        PipelineEvent(
                            event_type=PipelineEventType.ERROR,
                            source=stage_name,
                            target=target,
                            data={"stage": stage_name, "error": str(exc)},
                        )
                    )
        finally:
            self.emit(
                PipelineEvent(
                    event_type=PipelineEventType.SCAN_DONE,
                    source="pipeline",
                    target=target,
                    data={"stages_run": len(stages), "stage_results": list(stage_results)},
                )
            )
            await self._queue.join()
            dispatcher_task.cancel()
            with suppress(asyncio.CancelledError):
                await dispatcher_task

        return {
            "target": target,
            "stages_run": len(stages),
            "stage_results": stage_results,
            "events_emitted": self._sequence,
            "dropped_events": self._dropped_count,
            "duration": perf_counter() - started_at,
        }

    async def stream_events(self) -> AsyncIterator[PipelineEvent]:
        history_index = 0
        stream_queue: asyncio.Queue[PipelineEvent] = asyncio.Queue(maxsize=self.buffer_size)
        self._stream_queues.append(stream_queue)
        try:
            while True:
                while history_index < len(self._history):
                    event = self._history[history_index]
                    history_index += 1
                    yield event
                    if (
                        event.event_type == PipelineEventType.SCAN_DONE
                        and history_index >= len(self._history)
                        and stream_queue.empty()
                    ):
                        return
                event = await stream_queue.get()
                yield event
                if event.event_type == PipelineEventType.SCAN_DONE and stream_queue.empty():
                    return
        finally:
            if stream_queue in self._stream_queues:
                self._stream_queues.remove(stream_queue)

    def event_summary(self) -> dict:
        return {
            "events_emitted": self._sequence,
            "dropped_events": self._dropped_count,
            "subscriber_count": len(self._subscribers),
        }


__all__ = ["PipelineEngine", "PipelineEvent", "PipelineEventType"]
