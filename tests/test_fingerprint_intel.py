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

"""Tests for FingerprintCollector."""

from core.collect.fingerprint_intel import FingerprintCollector


def _found(platform: str) -> dict:
    return {
        "status": "FOUND",
        "platform": platform,
        "confidence": 90,
        "contacts": {"emails": ["test@example.com"], "phones": [], "links": []},
    }


def test_social_fingerprint_counts_platforms():
    fc = FingerprintCollector()
    results = [_found("Twitter"), _found("GitHub"), _found("Reddit")]
    fp = fc.collect_social_fingerprint(results)
    assert fp["type"] == "social"
    assert fp["platform_count"] == 3
    assert "test@example.com" in fp["emails"]


def test_network_fingerprint_extracts_ports():
    fc = FingerprintCollector()
    port_data = {
        "open_ports": [
            {"port": 22, "protocol": "tcp", "state": "open", "service": "ssh"},
            {"port": 443, "protocol": "tcp", "state": "open", "service": "https"},
        ],
        "os_matches": [{"name": "Linux 5.x", "accuracy": 90}],
        "host_state": "up",
    }
    fp = fc.collect_network_fingerprint(port_data, {})
    assert fp["type"] == "network"
    assert 22 in fp["open_ports"]
    assert 443 in fp["open_ports"]


def test_domain_fingerprint_extracts_subdomains():
    fc = FingerprintCollector()
    domain_result = {
        "subdomains": ["mail.example.com", "api.example.com", "www.example.com"],
        "dns": {"a": ["1.2.3.4"], "mx": ["mail.example.com"], "txt": [], "ns": []},
        "rdap": {"registrar": "Namecheap", "creation_date": "2020-01-01"},
        "https": {"certificate": {"issuer": "Let's Encrypt", "san": []}},
    }
    fp = fc.collect_domain_fingerprint(domain_result)
    assert fp["type"] == "domain"
    assert fp["subdomain_count"] == 3
    assert fp["registrar"] == "Namecheap"


def test_master_fingerprint_has_fingerprint_id():
    fc = FingerprintCollector()
    fp = fc.build_master_fingerprint(
        target="testuser",
        profile_results=[_found("Twitter")],
    )
    assert "fingerprint_id" in fp
    assert len(fp["fingerprint_id"]) == 64
    assert fp["target"] == "testuser"


def test_master_fingerprint_is_deterministic():
    fc = FingerprintCollector()
    results = [_found("Twitter")]
    fp1 = fc.build_master_fingerprint("user", profile_results=results)
    fp2 = fc.build_master_fingerprint("user", profile_results=results)
    assert fp1["fingerprint_id"] == fp2["fingerprint_id"]


def test_master_fingerprint_changes_with_different_target():
    fc = FingerprintCollector()
    results = [_found("Twitter")]
    fp1 = fc.build_master_fingerprint("user_a", profile_results=results)
    fp2 = fc.build_master_fingerprint("user_b", profile_results=results)
    assert fp1["fingerprint_id"] != fp2["fingerprint_id"]
