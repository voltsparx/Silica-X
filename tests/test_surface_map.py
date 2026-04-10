import unittest

from core.analyze.surface_map import build_surface_map, build_surface_next_steps


class TestSurfaceMap(unittest.TestCase):
    def test_surface_map_prioritizes_high_risk_hosts(self):
        domain_result = {
            "target": "example.com",
            "recon_mode": "hybrid",
            "resolved_addresses": ["1.1.1.1"],
            "subdomains": ["admin.example.com", "api.example.com", "dev.example.com", "www.example.com"],
            "rdap": {"handle": "HANDLE-1", "name_servers": ["ns1.example.com"]},
            "https": {"status": 200, "final_url": "https://example.com", "redirects_to_https": True},
            "http": {"status": 301, "final_url": "https://example.com", "redirects_to_https": True},
            "robots_txt_present": True,
            "security_txt_present": False,
            "collector_status": {
                "ct": {"lane": "passive", "status": "ok", "detail": "subdomains=4"},
                "dns": {"lane": "active", "status": "ok", "detail": "addresses=1"},
            },
        }

        surface_map = build_surface_map(domain_result)
        self.assertEqual(surface_map["recon_mode"], "hybrid")
        self.assertGreaterEqual(surface_map["attack_surface_score"], 1)
        self.assertIn("admin.example.com", surface_map["priority_summary"]["prioritized_hosts"])
        self.assertIn("admin", surface_map["priority_summary"]["matched_priority_labels"])
        self.assertIn("recommended_ports", surface_map["probe_plan"])
        self.assertIn("common_paths", surface_map["probe_plan"])

        next_steps = build_surface_next_steps(domain_result, issue_summary={"risk_score": 70})
        self.assertTrue(next_steps)
        self.assertTrue(
            any(
                "security.txt" in row["title"]
                or "Escalate" in row["title"]
                or "surface recon plan" in row["title"]
                for row in next_steps
            )
        )

    def test_surface_map_uses_embedded_wordlist_guidance(self):
        domain_result = {
            "target": "example.com",
            "recon_mode": "hybrid",
            "resolved_addresses": [],
            "subdomains": ["api.example.com", "portal.example.com", "misc.example.com"],
            "prioritized_subdomains": ["api.example.com", "portal.example.com", "misc.example.com"],
            "surface_wordlists": {
                "matched_priority_labels": ["api", "portal"],
                "common_paths": ["robots.txt", "api-docs"],
                "top_ports": [80, 443, 8080],
            },
            "rdap": {},
            "https": {"status": 200, "final_url": "https://example.com", "redirects_to_https": True},
            "http": {"status": 301, "final_url": "https://example.com", "redirects_to_https": True},
            "robots_txt_present": True,
            "security_txt_present": True,
            "collector_status": {},
        }

        surface_map = build_surface_map(domain_result)
        self.assertEqual(surface_map["priority_summary"]["prioritized_hosts"][:2], ["api.example.com", "portal.example.com"])
        self.assertEqual(surface_map["probe_plan"]["recommended_ports"][:3], [80, 443, 8080])
        self.assertEqual(surface_map["probe_plan"]["common_paths"][:2], ["robots.txt", "api-docs"])


if __name__ == "__main__":
    unittest.main()
