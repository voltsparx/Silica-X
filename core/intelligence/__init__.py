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

"""Intelligence-layer exports."""

from core.intelligence.advisor import StrategicAdvisor
from core.intelligence.entity_builder import build_fusion_entities, build_profile_entities, build_surface_entities
from core.intelligence.intelligence_engine import IntelligenceEngine

__all__ = [
    "StrategicAdvisor",
    "IntelligenceEngine",
    "build_profile_entities",
    "build_surface_entities",
    "build_fusion_entities",
]
