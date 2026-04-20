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

"""Integration tests for PreIntelligenceSimulator with realistic data."""

from core.intelligence.pre_sim import PreIntelligenceSimulator, TargetModel


def _make_found_profile(platform: str, email: str = "") -> dict:
    return {
        "status": "FOUND",
        "platform": platform,
        "confidence": 85,
        "contacts": {"emails": [email] if email else [], "phones": []},
        "bio": f"Test bio for {platform}",
    }


def test_sim_with_rich_profile_data():
    sim = PreIntelligenceSimulator()
    results = [
        _make_found_profile(p)
        for p in [
            "Twitter",
            "GitHub",
            "Reddit",
            "LinkedIn",
            "Instagram",
            "Facebook",
            "TikTok",
            "YouTube",
            "Twitch",
            "Discord",
        ]
    ]
    model = sim.simulate("testuser", profile_results=results)
    assert isinstance(model, TargetModel)
    assert model.data_richness == "rich"
    assert model.entity_class in {"social_handle", "person"}
    assert "active_social_presence" in model.inferred_traits


def test_sim_with_domain_and_open_ssh():
    sim = PreIntelligenceSimulator()
    model = sim.simulate(
        "example.com",
        domain_result={
            "target": "example.com",
            "subdomains": ["mail.example.com", "api.example.com"],
            "https": {"available": True, "headers": {}},
        },
        port_data={
            "open_ports": [
                {"port": 22, "protocol": "tcp", "state": "open", "service": "ssh"},
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
            ],
            "os_matches": [],
            "host_state": "up",
        },
    )
    assert model.entity_class == "domain_asset"
    assert "open_ssh" in model.risk_indicators
    assert model.confidence > 0.3


def test_sim_empty_input_returns_unknown():
    sim = PreIntelligenceSimulator()
    model = sim.simulate("unknown-target")
    assert model.entity_class == "unknown"
    assert model.data_richness == "sparse"
    assert model.confidence < 0.5


def test_sim_as_dict_has_all_keys():
    sim = PreIntelligenceSimulator()
    model = sim.simulate("test")
    payload = model.as_dict()
    for key in [
        "entity_class",
        "confidence",
        "inferred_traits",
        "risk_indicators",
        "data_richness",
        "scope_recommendation",
        "simulation_notes",
    ]:
        assert key in payload, f"Missing key in as_dict: {key}"


def test_sim_email_target_classified_correctly():
    sim = PreIntelligenceSimulator()
    model = sim.simulate("user@example.com")
    assert model.entity_class == "email_address"


def test_sim_ip_target_classified_correctly():
    sim = PreIntelligenceSimulator()
    model = sim.simulate("192.168.1.1")
    assert model.entity_class == "ip_host"
