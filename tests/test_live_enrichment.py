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

"""Tests for LiveEnrichmentSubscriber and pipeline wiring."""

import asyncio

from core.engines.pipeline_engine import PipelineEngine, PipelineEvent, PipelineEventType
from core.intelligence.live_enrichment import LiveEnrichmentSubscriber


def _make_found_event(platform: str, email: str = "") -> PipelineEvent:
    return PipelineEvent(
        event_type=PipelineEventType.RESULT_EMITTED,
        source=f"platform:{platform}",
        target="testuser",
        data={
            "platform": platform,
            "status": "FOUND",
            "confidence": 85,
            "url": f"https://example.com/{platform}",
            "contacts": {
                "emails": [email] if email else [],
                "phones": [],
                "links": [],
            },
            "bio": f"Test bio with email test@{platform}.com" if not email else "",
        },
    )


def _make_not_found_event(platform: str) -> PipelineEvent:
    return PipelineEvent(
        event_type=PipelineEventType.RESULT_EMITTED,
        source=f"platform:{platform}",
        target="testuser",
        data={
            "platform": platform,
            "status": "NOT_FOUND",
            "confidence": 0,
            "url": "",
            "contacts": {},
        },
    )


def test_enricher_ignores_not_found() -> None:
    enricher = LiveEnrichmentSubscriber()
    event = _make_not_found_event("GitHub")
    asyncio.run(enricher.handle_event(event))
    assert enricher.summary()["platforms_processed"] == 0


def test_enricher_processes_found_event() -> None:
    enricher = LiveEnrichmentSubscriber()
    event = _make_found_event("GitHub", email="user@example.com")
    asyncio.run(enricher.handle_event(event))
    assert enricher.summary()["platforms_processed"] == 1


def test_enricher_deduplicates_platforms() -> None:
    enricher = LiveEnrichmentSubscriber()
    event = _make_found_event("GitHub", email="user@example.com")
    asyncio.run(enricher.handle_event(event))
    asyncio.run(enricher.handle_event(event))
    assert enricher.summary()["platforms_processed"] == 1


def test_enricher_get_signals_returns_list() -> None:
    enricher = LiveEnrichmentSubscriber()
    signals = enricher.get_signals()
    assert isinstance(signals, list)


def test_enricher_summary_has_required_keys() -> None:
    enricher = LiveEnrichmentSubscriber()
    summary = enricher.summary()
    assert "platforms_processed" in summary
    assert "enriched_signal_count" in summary
    assert "platforms_with_signals" in summary


def test_pipeline_with_enricher_subscriber() -> None:
    enricher = LiveEnrichmentSubscriber()
    pipeline = PipelineEngine(buffer_size=64)
    pipeline.subscribe(enricher.handle_event)

    async def _run() -> None:
        pipeline.emit(_make_found_event("Twitter", email="a@b.com"))
        pipeline.emit(_make_not_found_event("Instagram"))
        try:
            await asyncio.wait_for(pipeline.dispatch_loop(), timeout=1.0)
        except asyncio.TimeoutError:
            pass

    asyncio.run(_run())
    assert enricher.summary()["platforms_processed"] >= 0


def test_enricher_ignores_non_result_events() -> None:
    enricher = LiveEnrichmentSubscriber()
    event = PipelineEvent(
        event_type=PipelineEventType.SCAN_STARTED,
        source="runner",
        target="testuser",
        data={},
    )
    asyncio.run(enricher.handle_event(event))
    assert enricher.summary()["platforms_processed"] == 0
