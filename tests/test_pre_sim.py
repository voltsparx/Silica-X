# ──────────────────────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────────────────────

from core.intelligence.pre_sim import PreIntelligenceSimulator


def test_simulate_returns_target_model():
    model = PreIntelligenceSimulator().simulate("alice")
    assert hasattr(model, "as_dict")


def test_simulate_infers_social_handle():
    model = PreIntelligenceSimulator().simulate("alice", profile_results=[{"status": "FOUND"}])
    assert model.entity_class == "social_handle"


def test_simulate_infers_domain_asset():
    model = PreIntelligenceSimulator().simulate("example.com")
    assert model.entity_class == "domain_asset"


def test_simulate_detects_open_ssh_risk():
    model = PreIntelligenceSimulator().simulate(
        "example.com",
        domain_result={"target": "example.com", "https": {"headers": {}}},
        port_data={"open_ports": [{"port": 22}]},
    )
    assert "open_ssh" in model.risk_indicators


def test_simulate_sparse_richness_with_no_data():
    model = PreIntelligenceSimulator().simulate("alice")
    assert model.data_richness == "sparse"


def test_simulate_rich_richness_with_many_signals():
    profile_results = [{"status": "FOUND"} for _ in range(10)]
    domain_result = {"subdomains": [f"s{i}.example.com" for i in range(10)], "https": {"available": True, "headers": {}}}
    port_data = {"open_ports": [{"port": 80} for _ in range(3)]}
    model = PreIntelligenceSimulator().simulate(
        "example.com",
        profile_results=profile_results,
        domain_result=domain_result,
        port_data=port_data,
    )
    assert model.data_richness == "rich"


def test_simulate_recommends_fusion_with_both():
    model = PreIntelligenceSimulator().simulate(
        "alice",
        profile_results=[{"status": "FOUND"}],
        domain_result={"target": "example.com"},
    )
    assert model.scope_recommendation == "fusion"
