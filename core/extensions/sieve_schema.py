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

"""Signal Sieve schema definitions for Sylica-X."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FilterContext = dict[str, Any]


@dataclass(frozen=True)
class FilterSpec:
    module_name: str
    filter_id: str
    title: str
    description: str
    scopes: tuple[str, ...]
    version: str = "1.0"
    author: str = "Sylica-X"
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class FilterExecutionResult:
    filter_id: str
    title: str
    description: str
    scope: str
    summary: str
    severity: str
    highlights: tuple[str, ...]
    data: dict[str, Any]
