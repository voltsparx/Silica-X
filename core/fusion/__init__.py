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

"""Fusion layer exports."""

from core.fusion.confidence_engine import aggregate_confidence_score, score_entity_confidence
from core.fusion.correlator import correlate_entities
from core.fusion.deduplicator import deduplicate_entities
from core.fusion.fusion_engine import FusionEngine
from core.fusion.graph_builder import build_relationship_graph

__all__ = [
    "FusionEngine",
    "aggregate_confidence_score",
    "build_relationship_graph",
    "correlate_entities",
    "deduplicate_entities",
    "score_entity_confidence",
]
