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

"""Entity deduplication utilities for fusion phase."""

from __future__ import annotations

from collections.abc import Sequence

from core.domain import BaseEntity


def deduplicate_entities(entities: Sequence[BaseEntity]) -> list[BaseEntity]:
    """Remove duplicate entities by identifier then semantic key."""

    unique: list[BaseEntity] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()

    for entity in entities:
        semantic_key = (entity.entity_type, entity.source.strip().lower(), entity.value.strip().lower())
        if entity.id in seen_ids or semantic_key in seen_keys:
            continue
        seen_ids.add(entity.id)
        seen_keys.add(semantic_key)
        unique.append(entity)

    return unique
