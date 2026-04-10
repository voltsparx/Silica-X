# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Sylica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Sylica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root 
#
# This file is part of Sylica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

"""Mode-aware expansion metadata for entity intelligence trails."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


MODE_DEPTH_LIMIT = {
    "fast": 0,
    "balanced": 1,
    "deep": 2,
    "max": 4,
}


class ExpansionEngine:
    """Annotate entities with expansion origin, depth, and path."""

    _TYPE_DEPTH_HINT = {
        "profile": 1,
        "email": 2,
        "domain": 2,
        "asset": 3,
        "ip": 3,
    }

    def annotate(
        self,
        entities: Sequence[dict[str, Any]],
        *,
        target: str,
        mode: str,
    ) -> list[dict[str, Any]]:
        """Return expanded entity snapshots with deterministic path metadata."""

        depth_limit = MODE_DEPTH_LIMIT.get(str(mode).strip().lower(), MODE_DEPTH_LIMIT["balanced"])
        normalized_target = str(target).strip()
        rows: list[dict[str, Any]] = []

        for entity in entities:
            item = dict(entity)
            entity_type = str(item.get("entity_type", "")).strip().lower()
            value = str(item.get("value", "")).strip()
            hint_depth = self._TYPE_DEPTH_HINT.get(entity_type, 1)
            expansion_depth = min(depth_limit, hint_depth)

            path: list[str] = []
            if normalized_target:
                path.append(normalized_target)
            if value and value.lower() != normalized_target.lower():
                path.append(value)
            if depth_limit >= 3:
                source = str(item.get("source", "")).strip()
                if source:
                    path.append(source)

            item["expansion_origin"] = normalized_target or value
            item["expansion_depth"] = expansion_depth
            item["expansion_path"] = path
            rows.append(item)

        return rows

