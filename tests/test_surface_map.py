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

        next_steps = build_surface_next_steps(domain_result, issue_summary={"risk_score": 70})
        self.assertTrue(next_steps)
        self.assertTrue(any("security.txt" in row["title"] or "Escalate" in row["title"] for row in next_steps))


if __name__ == "__main__":
    unittest.main()
