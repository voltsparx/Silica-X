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

"""Tests for report artifact generation functions."""

from core.artifacts.charts import build_relationship_graph_svg
from core.artifacts.reporting import ReportGenerator


def test_svg_empty_input_returns_svg():
    result = build_relationship_graph_svg({})
    assert result.strip().startswith("<svg")
    assert "No relationship data" in result


def test_svg_with_nodes_returns_circles_and_lines():
    result = build_relationship_graph_svg(
        {
            "relationship_map": {
                "node_a": ["node_b"],
                "node_b": ["node_a"],
                "node_c": [],
            }
        }
    )
    assert result.strip().startswith("<svg")
    assert "<circle" in result
    assert "<line" in result


def test_svg_viewbox_is_correct():
    result = build_relationship_graph_svg({})
    assert "viewBox" in result or "viewbox" in result.lower()


def test_svg_background_color_present():
    result = build_relationship_graph_svg({})
    assert "#140d08" in result


def test_intelligence_brief_contains_header():
    rg = ReportGenerator()
    result = rg.generate_intelligence_brief(
        {
            "target_model": {
                "entity_class": "domain_asset",
                "confidence": 0.75,
                "risk_indicators": ["missing_hsts"],
                "inferred_traits": ["active_web"],
                "scope_recommendation": "surface",
                "simulation_notes": [],
            },
            "risk_summary": {"level": "MEDIUM"},
            "execution_guidance": {"actions": []},
        }
    )
    assert "SILICA-X INTELLIGENCE BRIEF" in result


def test_intelligence_brief_contains_entity_class():
    rg = ReportGenerator()
    result = rg.generate_intelligence_brief(
        {
            "target_model": {
                "entity_class": "social_handle",
                "confidence": 0.5,
                "risk_indicators": [],
                "inferred_traits": [],
                "scope_recommendation": "profile",
                "simulation_notes": [],
            },
        }
    )
    assert "social_handle" in result


def test_report_generator_instantiates():
    rg = ReportGenerator()
    assert rg is not None
