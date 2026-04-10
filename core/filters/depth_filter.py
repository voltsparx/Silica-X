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

"""Depth-oriented filter to constrain entity volume by scan depth."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.domain import BaseEntity
from core.filters.base_filter import BaseFilter


class DepthFilter(BaseFilter):
    """Apply depth-aware cap to output volume."""

    filter_id = "depth"

    def apply(self, entities: Sequence[BaseEntity], context: Mapping[str, Any]) -> list[BaseEntity]:
        depth = max(1, int(context.get("depth", 2)))
        explicit_limit = context.get("entity_limit")
        if isinstance(explicit_limit, int) and explicit_limit > 0:
            limit = explicit_limit
        else:
            limit = depth * 30

        if len(entities) <= limit:
            return list(entities)

        ranked = sorted(entities, key=lambda item: (-item.confidence, item.entity_type, item.value))
        return ranked[:limit]
