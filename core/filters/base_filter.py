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

"""Base filter contract for post-capability refinement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from core.domain import BaseEntity


class BaseFilter(ABC):
    """Stateless filter interface operating on entity collections."""

    filter_id: str = "base"

    @abstractmethod
    def apply(self, entities: Sequence[BaseEntity], context: Mapping[str, Any]) -> list[BaseEntity]:
        """Apply filter and return a new entity list."""
