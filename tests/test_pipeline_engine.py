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

from core.engines.pipeline_engine import PipelineEngine, PipelineEvent, PipelineEventType


def test_pipeline_engine_emits_scan_started_and_done():
    async def dummy_stage(target: str, pipeline: PipelineEngine) -> dict:
        pipeline.emit(
            PipelineEvent(
                event_type=PipelineEventType.RESULT_EMITTED,
                source="dummy_stage",
                target=target,
                data={"ok": True},
            )
        )
        return {"ok": True}

    result = asyncio.run(PipelineEngine().run_pipeline("example.com", [dummy_stage]))
    assert result["stages_run"] == 1
    assert "dummy_stage" in result["stage_results"]
    assert result["stage_results"]["dummy_stage"] == {"ok": True}


def test_pipeline_engine_subscriber_receives_events():
    received: list[int] = []

    async def handler(event: PipelineEvent) -> None:
        received.append(event.sequence)

    async def dummy_stage(target: str, pipeline: PipelineEngine) -> dict:
        pipeline.emit(
            PipelineEvent(
                event_type=PipelineEventType.SIGNAL_FOUND,
                source="dummy_stage",
                target=target,
                data={"value": "signal"},
            )
        )
        return {"ok": True}

    engine = PipelineEngine()
    engine.subscribe(handler)
    asyncio.run(engine.run_pipeline("example.com", [dummy_stage]))
    assert received


def test_pipeline_engine_handles_stage_exception_without_crashing():
    async def failing_stage(target: str, pipeline: PipelineEngine) -> dict:
        raise RuntimeError(f"boom:{target}:{pipeline.event_summary()['subscriber_count']}")

    result = asyncio.run(PipelineEngine().run_pipeline("example.com", [failing_stage]))
    assert result["stages_run"] == 1
    assert result["stage_results"] == {}
    assert result["events_emitted"] >= 3


def test_pipeline_engine_emit_respects_buffer_size():
    engine = PipelineEngine(buffer_size=2)
    for index in range(10):
        engine.emit(
            PipelineEvent(
                event_type=PipelineEventType.SIGNAL_FOUND,
                source="buffer_test",
                target="example.com",
                data={"index": index},
            )
        )
    assert engine.event_summary()["dropped_events"] > 0


def test_pipeline_event_sequence_is_monotonic():
    engine = PipelineEngine(buffer_size=10)
    events = [
        PipelineEvent(
            event_type=PipelineEventType.SIGNAL_FOUND,
            source="seq_test",
            target="example.com",
            data={"index": index},
        )
        for index in range(5)
    ]
    for event in events:
        engine.emit(event)
    assert [event.sequence for event in events] == [1, 2, 3, 4, 5]
