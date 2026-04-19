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

from __future__ import annotations


class TargetModel:
    """Inferred understanding of the scan target before deep processing."""

    def __init__(self) -> None:
        self.entity_class: str = "unknown"
        self.confidence: float = 0.0
        self.inferred_traits: list[str] = []
        self.risk_indicators: list[str] = []
        self.data_richness: str = "sparse"
        self.scope_recommendation: str = "profile"
        self.simulation_notes: list[str] = []

    def as_dict(self) -> dict:
        return {
            "entity_class": self.entity_class,
            "confidence": round(self.confidence, 3),
            "inferred_traits": self.inferred_traits,
            "risk_indicators": self.risk_indicators,
            "data_richness": self.data_richness,
            "scope_recommendation": self.scope_recommendation,
            "simulation_notes": self.simulation_notes,
        }


class PreIntelligenceSimulator:
    """Simulate target understanding before deep analysis."""

    def simulate(
        self,
        target: str,
        profile_results: list[dict] | None = None,
        domain_result: dict | None = None,
        ocr_payload: dict | None = None,
        port_data: dict | None = None,
        subdomain_data: dict | None = None,
    ) -> TargetModel:
        model = TargetModel()
        profile_results = profile_results or []
        domain_result = domain_result or {}
        ocr_payload = ocr_payload or {}
        port_data = port_data or {}
        subdomain_data = subdomain_data or {}

        has_profile = bool(profile_results)
        has_domain = bool(domain_result.get("target") or domain_result.get("subdomains"))
        has_port = bool(port_data.get("open_ports"))
        has_ocr = bool(ocr_payload.get("ocr_hits", 0))
        has_subdomain = bool(subdomain_data.get("subdomains"))

        domain_pattern = any(c in target for c in [".", "://"])
        email_pattern = "@" in target
        ip_pattern = all(part.isdigit() for part in target.split(".")) and target.count(".") == 3

        if email_pattern:
            model.entity_class = "email_address"
        elif ip_pattern:
            model.entity_class = "ip_host"
        elif domain_pattern:
            model.entity_class = "domain_asset"
        elif has_profile and not has_domain:
            model.entity_class = "social_handle"
        elif has_domain and not has_profile:
            model.entity_class = "domain_asset"
        elif has_profile and has_domain:
            model.entity_class = "person" if len(profile_results) > 3 else "mixed"
        else:
            model.entity_class = "unknown"

        signal_count = (
            len(profile_results)
            + len(domain_result.get("subdomains", []))
            + len(port_data.get("open_ports", []))
            + int(ocr_payload.get("ocr_hits", 0))
            + int(subdomain_data.get("count", 0))
        )
        if signal_count > 20:
            model.data_richness = "rich"
        elif signal_count > 5:
            model.data_richness = "moderate"
        else:
            model.data_richness = "sparse"

        found_profiles = [r for r in profile_results if str(r.get("status")) == "FOUND"]
        if found_profiles:
            model.inferred_traits.append("active_social_presence")
        emails = set()
        for r in found_profiles:
            for e in (r.get("contacts", {}) or {}).get("emails", []):
                emails.add(e)
        if emails:
            model.inferred_traits.append("has_email")
        if domain_result.get("https", {}).get("available"):
            model.inferred_traits.append("active_web")
        if domain_result.get("subdomains"):
            model.inferred_traits.append("multi_subdomain")
        if port_data.get("open_ports"):
            model.inferred_traits.append("network_exposed")
        if ocr_payload.get("ocr_hits", 0):
            model.inferred_traits.append("media_intel_available")

        open_ports = port_data.get("open_ports", [])
        sensitive_ports = {
            22: "open_ssh",
            23: "open_telnet",
            3306: "open_mysql",
            5432: "open_postgres",
            6379: "open_redis",
            27017: "open_mongodb",
            9200: "open_elasticsearch",
            3389: "open_rdp",
            5900: "open_vnc",
        }
        for port_info in open_ports:
            port_num = int(port_info.get("port", 0))
            if port_num in sensitive_ports:
                model.risk_indicators.append(sensitive_ports[port_num])

        https_headers = (domain_result.get("https") or {}).get("headers") or {}
        if not https_headers.get("Strict-Transport-Security"):
            if has_domain:
                model.risk_indicators.append("missing_hsts")
        if not https_headers.get("Content-Security-Policy"):
            if has_domain:
                model.risk_indicators.append("missing_csp")

        ct_count = len(domain_result.get("subdomains", []))
        if ct_count > 30:
            model.risk_indicators.append("large_attack_surface")

        has_signals = [has_profile, has_domain, has_port, has_ocr, has_subdomain]
        model.confidence = min(1.0, sum(1 for s in has_signals if s) * 0.2 + 0.1)

        if has_profile and has_domain:
            model.scope_recommendation = "fusion"
        elif has_domain and (has_port or has_subdomain):
            model.scope_recommendation = "surface"
        elif has_profile:
            model.scope_recommendation = "profile"
        elif has_ocr:
            model.scope_recommendation = "media_only"
        else:
            model.scope_recommendation = "osint_deep"

        if model.data_richness == "sparse":
            model.simulation_notes.append("Low data volume - consider running additional recon phases.")
        if model.entity_class == "unknown":
            model.simulation_notes.append(
                "Entity class could not be determined - try profile + surface fusion."
            )
        if model.risk_indicators:
            model.simulation_notes.append(
                f"Risk signals detected: {', '.join(model.risk_indicators[:5])}"
            )
        if model.confidence < 0.3:
            model.simulation_notes.append("Low confidence model - results may be incomplete.")

        return model


__all__ = ["PreIntelligenceSimulator", "TargetModel"]
