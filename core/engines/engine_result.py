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

"""Standardized engine execution result schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


EngineStatus = Literal["success", "failed", "timeout"]


@dataclass(frozen=True)
class EngineResult:
    """Normalized result returned by every engine execution lane."""

    name: str
    status: EngineStatus
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == "success"

