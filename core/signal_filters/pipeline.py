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

"""Composable filter pipeline for entity refinement."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.domain import BaseEntity
from core.signal_filters.base_filter import BaseFilter


class FilterPipeline:
    """Run a deterministic sequence of stateless filters."""

    def __init__(self, filters: Sequence[BaseFilter]) -> None:
        self._filters = list(filters)

    def run(self, entities: Sequence[BaseEntity], context: Mapping[str, Any]) -> list[BaseEntity]:
        """Apply all configured filters in-order."""

        output = list(entities)
        for item in self._filters:
            output = item.apply(output, context)
        return output
