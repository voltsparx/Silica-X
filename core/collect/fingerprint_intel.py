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


class FingerprintCollector:
    """Collects and aggregates OSINT fingerprints from collected data."""

    def collect_social_fingerprint(self, profile_results: list[dict]) -> dict:
        """Extract social fingerprint from profile scan results."""

        found = [r for r in profile_results if str(r.get("status")) == "FOUND"]
        platforms = [r.get("platform", "") for r in found]
        bios = [str(r.get("bio") or "") for r in found if r.get("bio")]
        emails = set()
        phones = set()
        links = set()
        for r in found:
            contacts = r.get("contacts") or {}
            for e in contacts.get("emails", []):
                emails.add(str(e))
            for p in contacts.get("phones", []):
                phones.add(str(p))
            for l in contacts.get("links", []):
                links.add(str(l))
        return {
            "type": "social",
            "platforms_found": platforms,
            "platform_count": len(platforms),
            "emails": sorted(emails),
            "phones": sorted(phones),
            "external_links": sorted(links),
            "bio_count": len(bios),
            "bio_text_length": sum(len(b) for b in bios),
        }

    def collect_network_fingerprint(self, port_data: dict, domain_result: dict) -> dict:
        """Extract network fingerprint from port and domain data."""

        open_ports = [p["port"] for p in port_data.get("open_ports", [])]
        services = [p.get("service", "") for p in port_data.get("open_ports", [])]
        os_matches = [m.get("name", "") for m in port_data.get("os_matches", [])]
        rdap = domain_result.get("rdap") or {}
        return {
            "type": "network",
            "open_ports": open_ports,
            "services": list(set(services)),
            "os_fingerprints": os_matches[:3],
            "registrar": rdap.get("registrar", ""),
            "nameservers": domain_result.get("dns", {}).get("ns", []),
            "host_state": port_data.get("host_state", "unknown"),
        }

    def collect_domain_fingerprint(self, domain_result: dict) -> dict:
        """Extract domain fingerprint from surface scan result."""

        ct_subdomains = domain_result.get("subdomains", [])
        dns = domain_result.get("dns") or {}
        rdap = domain_result.get("rdap") or {}
        https = domain_result.get("https") or {}
        cert = https.get("certificate") or {}
        return {
            "type": "domain",
            "subdomain_count": len(ct_subdomains),
            "subdomains_sample": ct_subdomains[:10],
            "a_records": dns.get("a", []),
            "mx_records": dns.get("mx", []),
            "txt_records": dns.get("txt", []),
            "cert_issuer": cert.get("issuer", ""),
            "cert_san": cert.get("san", []),
            "registrar": rdap.get("registrar", ""),
            "creation_date": rdap.get("creation_date", ""),
        }

    def build_master_fingerprint(
        self,
        target: str,
        profile_results: list[dict] | None = None,
        domain_result: dict | None = None,
        port_data: dict | None = None,
    ) -> dict:
        """Build the combined master fingerprint for a target."""

        from core.engines.crypto_engine import CryptoEngine

        crypto = CryptoEngine()
        components = {}
        if profile_results:
            components["social"] = self.collect_social_fingerprint(profile_results)
        if domain_result:
            port = port_data or {}
            components["network"] = self.collect_network_fingerprint(port, domain_result)
            components["domain"] = self.collect_domain_fingerprint(domain_result)
        fingerprint_id = crypto.fingerprint({"target": target, **components})
        return {
            "target": target,
            "fingerprint_id": fingerprint_id,
            "components": components,
            "component_count": len(components),
        }


__all__ = ["FingerprintCollector"]
