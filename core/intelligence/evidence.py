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

"""Evidence records for traceable intelligence analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any

from core.domain import BaseEntity


def build_evidence_id(*, source_adapter: str, entity_id: str, trace_id: str) -> str:
    """Build a stable evidence identifier."""

    material = f"{source_adapter.strip().lower()}::{entity_id.strip().lower()}::{trace_id.strip().lower()}"
    digest = hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]
    return f"evidence-{digest}"


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence object preserving raw and normalized artifacts."""

    id: str
    source_adapter: str
    timestamp: datetime
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    reliability_score: float
    collection_method: str
    trace_id: str

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-friendly evidence payload."""

        return {
            "id": self.id,
            "source_adapter": self.source_adapter,
            "timestamp": self.timestamp.isoformat(),
            "raw_data": dict(self.raw_data),
            "normalized_data": dict(self.normalized_data),
            "reliability_score": max(0.0, min(1.0, float(self.reliability_score))),
            "collection_method": self.collection_method,
            "trace_id": self.trace_id,
        }


def evidence_from_entity(
    entity: BaseEntity,
    *,
    trace_prefix: str,
    collection_method: str = "capability",
) -> Evidence:
    """Create evidence record from a normalized entity."""

    raw_payload = entity.as_dict()
    normalized_payload = {
        "entity_id": entity.id,
        "entity_type": entity.entity_type,
        "value": entity.value,
        "source": entity.source,
        "metadata": dict(entity.attributes),
    }
    trace_id = f"{trace_prefix}:{entity.id}"
    evidence_id = build_evidence_id(
        source_adapter=entity.source,
        entity_id=entity.id,
        trace_id=trace_id,
    )
    return Evidence(
        id=evidence_id,
        source_adapter=entity.source,
        timestamp=entity.timestamp if entity.timestamp.tzinfo else entity.timestamp.replace(tzinfo=timezone.utc),
        raw_data=raw_payload,
        normalized_data=normalized_payload,
        reliability_score=max(0.0, min(1.0, float(entity.confidence))),
        collection_method=collection_method,
        trace_id=trace_id,
    )

