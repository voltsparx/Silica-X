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

"""Signal Forge schema definitions for Silinosic-X."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


PluginContext = dict[str, Any]
PluginRunFn = Callable[[PluginContext], dict[str, Any]]


@dataclass(frozen=True)
class PluginSpec:
    module_name: str
    plugin_id: str
    title: str
    description: str
    scopes: tuple[str, ...]
    version: str = "1.0"
    author: str = "Silinosic-X"
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginExecutionResult:
    plugin_id: str
    title: str
    description: str
    scope: str
    summary: str
    severity: str
    highlights: tuple[str, ...]
    data: dict[str, Any]
