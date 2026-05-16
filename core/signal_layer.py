# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


NOISE_THRESHOLD = 0.20
LOW_THRESHOLD = 0.45
MEDIUM_THRESHOLD = 0.65
HIGH_THRESHOLD = 0.82


@dataclass
class Finding:
    source_module: str
    entity_id: str
    platform: str
    url: str
    raw: dict[str, Any]
    confidence: float = 0.0
    tier: str = "NOISE"
    why: list[str] = field(default_factory=list)
    fingerprint: str = ""

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(float(self.confidence or 0.0), 1.0))
        self.fingerprint = hashlib.sha256(
            f"{self.entity_id}:{self.platform}:{self.url}".encode("utf-8", errors="replace")
        ).hexdigest()[:16]
        self._assign_tier()

    def _assign_tier(self) -> None:
        if self.confidence >= HIGH_THRESHOLD:
            self.tier = "HIGH"
        elif self.confidence >= MEDIUM_THRESHOLD:
            self.tier = "MEDIUM"
        elif self.confidence >= LOW_THRESHOLD:
            self.tier = "LOW"
        else:
            self.tier = "NOISE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "platform": self.platform,
            "url": self.url,
            "confidence": round(self.confidence, 3),
            "tier": self.tier,
            "why": list(self.why),
            "fingerprint": self.fingerprint,
        }


class SignalLayer:
    """Single pass: normalize -> score -> gate -> emit."""

    def __init__(self, seen_fingerprints: set[str] | None = None) -> None:
        self._seen: set[str] = seen_fingerprints or set()

    def process(self, finding: Finding) -> Finding | None:
        if finding.fingerprint in self._seen:
            return None
        self._seen.add(finding.fingerprint)
        if finding.tier == "NOISE":
            return None
        return finding

    def process_batch(self, findings: list[Finding]) -> list[Finding]:
        results: list[Finding] = []
        for finding in findings:
            out = self.process(finding)
            if out is not None:
                results.append(out)
        results.sort(key=lambda item: item.confidence, reverse=True)
        return results
