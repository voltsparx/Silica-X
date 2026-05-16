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

from core.entity import Entity
from core.signal_layer import Finding


W_EXPOSURE_BREADTH = 0.25
W_HIGH_CONFIDENCE = 0.30
W_CREDENTIAL_SIGNAL = 0.25
W_ANOMALY = 0.20

MAX_PLATFORMS_NORM = 20


def compute_risk(entity: Entity, findings: list[Finding]) -> float:
    """Returns a risk score 0.0-1.0 for this entity."""

    entity_findings = [item for item in findings if item.entity_id == entity.canonical_id]
    breadth_score = min(entity.exposure_breadth / MAX_PLATFORMS_NORM, 1.0)
    high_count = sum(1 for item in entity_findings if item.tier == "HIGH")
    high_score = min(high_count / 5, 1.0)
    cred_score = (
        1.0
        if any(item.raw.get("credential_signal") or item.raw.get("leak_indicator") for item in entity_findings)
        else 0.0
    )
    anomaly_count = sum(1 for item in entity_findings if item.raw.get("anomaly_flag"))
    anomaly_score = min(anomaly_count / 3, 1.0)
    composite = (
        W_EXPOSURE_BREADTH * breadth_score
        + W_HIGH_CONFIDENCE * high_score
        + W_CREDENTIAL_SIGNAL * cred_score
        + W_ANOMALY * anomaly_score
    )
    return round(min(composite, 1.0), 3)


def rank_entities(entities: list[Entity], findings: list[Finding]) -> list[tuple[Entity, float]]:
    """Returns list of (entity, risk_score) sorted high-to-low."""

    scored = [(entity, compute_risk(entity, findings)) for entity in entities]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored
