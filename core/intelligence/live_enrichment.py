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

from typing import Any


class LiveEnrichmentSubscriber:
    """Subscribes to pipeline events and enriches FOUND results in real time.

    When a RESULT_EMITTED event arrives with status=FOUND, this subscriber
    immediately extracts contact signals and credential patterns from the
    available data and stores them in self.enriched_signals for later
    collection by the runner.
    """

    def __init__(self) -> None:
        self.enriched_signals: list[dict[str, Any]] = []
        self._processed_platforms: set[str] = set()

    async def handle_event(self, event: Any) -> None:
        """Handle a single pipeline event. Safe to call from dispatch_loop."""
        from core.engines.pipeline_engine import PipelineEventType

        if event.event_type != PipelineEventType.RESULT_EMITTED:
            return
        data = event.data or {}
        if str(data.get("status", "")).upper() != "FOUND":
            return
        platform = str(data.get("platform", "")).strip()
        if not platform or platform in self._processed_platforms:
            return
        self._processed_platforms.add(platform)
        try:
            from core.collect.osint_hunt import hunt_credential_signals

            contacts = data.get("contacts") or {}
            bio_text = str(data.get("bio") or "")
            contact_text = " ".join(
                [
                    " ".join(contacts.get("emails", [])),
                    " ".join(contacts.get("phones", [])),
                    " ".join(contacts.get("links", [])),
                    bio_text,
                ]
            )
            if contact_text.strip():
                signals = hunt_credential_signals(contact_text)
                if any(
                    signals.get(key)
                    for key in [
                        "emails",
                        "phones",
                        "api_key_patterns",
                        "jwt_patterns",
                        "pgp_blocks",
                    ]
                ):
                    self.enriched_signals.append(
                        {
                            "platform": platform,
                            "target": event.target,
                            "signals": signals,
                            "url": data.get("url", ""),
                        }
                    )
        except Exception:
            pass

    def get_signals(self) -> list[dict[str, Any]]:
        """Return all enriched signals collected so far."""
        return list(self.enriched_signals)

    def summary(self) -> dict[str, Any]:
        """Return a summary of enrichment activity."""
        return {
            "platforms_processed": len(self._processed_platforms),
            "enriched_signal_count": len(self.enriched_signals),
            "platforms_with_signals": [signal["platform"] for signal in self.enriched_signals],
        }
