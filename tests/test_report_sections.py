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

from __future__ import annotations

from core.artifacts.charts import build_relationship_graph_svg
from core.artifacts.html_report import (
    _build_fingerprint_section,
    _build_osint_hunt_section,
    _build_port_probe_section,
    _build_target_model_section,
)
from core.artifacts.reporting import ReportGenerator


def test_target_model_section_returns_html():
    html = _build_target_model_section(
        {
            "target_model": {
                "entity_class": "social_handle",
                "confidence": 0.84,
                "inferred_traits": ["public operator"],
                "risk_indicators": ["email exposure"],
                "simulation_notes": ["profile lane looks rich"],
                "scope_recommendation": "fusion",
            }
        }
    )
    assert html.startswith("<div")
    assert "social_handle" in html
    assert html.endswith("</div>")


def test_fingerprint_section_returns_html():
    html = _build_fingerprint_section(
        {
            "master_fingerprint": {
                "fingerprint_id": "abc123",
                "components": {
                    "social": {"platforms_found": ["GitHub"], "emails": ["a@example.com"], "phones": []},
                    "network": {"open_ports": [443], "services": ["https"], "host_state": "up"},
                    "domain": {"subdomain_count": 3, "registrar": "Example Registrar", "cert_issuer": "LE"},
                },
            }
        }
    )
    assert html.startswith("<div")
    assert html.endswith("</div>")


def test_port_probe_section_returns_html():
    html = _build_port_probe_section(
        {
            "port_surface": {
                "host_state": "up",
                "open_ports": [
                    {
                        "port": 443,
                        "protocol": "tcp",
                        "state": "open",
                        "service": "https",
                        "version": "1.2",
                        "product": "nginx",
                    }
                ],
                "os_matches": [{"name": "Linux", "accuracy": 98}],
            }
        }
    )
    assert html.startswith("<div")
    assert "<table" in html


def test_relationship_graph_svg_empty_input():
    svg = build_relationship_graph_svg({})
    assert svg.startswith("<svg")


def test_relationship_graph_svg_with_nodes():
    svg = build_relationship_graph_svg(
        {"relationship_map": {"entity-a": ["entity-b"], "entity-b": ["entity-c"]}}
    )
    assert "<circle" in svg
    assert "<line" in svg


def test_intelligence_brief_returns_box_format():
    brief = ReportGenerator().generate_intelligence_brief(
        {
            "target": "alice",
            "target_model": {
                "entity_class": "person",
                "confidence": 0.91,
                "risk_indicators": ["public email exposure"],
            },
            "risk_summary": {"level": "high"},
            "execution_guidance": {"actions": [{"title": "Pivot on email artifacts"}]},
        }
    )
    assert "SILICA-X INTELLIGENCE BRIEF" in brief


def test_osint_hunt_section_returns_html():
    html = _build_osint_hunt_section(
        {
            "osint_hunt": {
                "emails": ["alice@example.com"],
                "phones": ["+12025550123"],
                "credential_signals": {"api_keys": ["sk-example-token"]},
            },
            "contact_surface": {
                "findings": [
                    {"path": "/team", "signal_type": "email", "value": "alice@example.com"},
                ]
            },
        }
    )
    assert html.startswith("<div")
    assert html.endswith("</div>")
