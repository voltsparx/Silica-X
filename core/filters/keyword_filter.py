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

"""Filter entities by keyword matching across values and metadata."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.domain import BaseEntity
from core.filters.base_filter import BaseFilter


class KeywordFilter(BaseFilter):
    """Retain entities matching configured keywords."""

    filter_id = "keyword"

    def apply(self, entities: Sequence[BaseEntity], context: Mapping[str, Any]) -> list[BaseEntity]:
        keywords = context.get("keywords", [])
        normalized = [
            str(item).strip().lower() for item in keywords if isinstance(item, str) and item.strip()
        ]
        if not normalized:
            return list(entities)

        output: list[BaseEntity] = []
        for entity in entities:
            haystack = entity.value.lower()
            metadata_text = " ".join(str(item).lower() for item in dict(entity.attributes).values())
            if any(keyword in haystack or keyword in metadata_text for keyword in normalized):
                output.append(entity)
        return output
