import unittest

from core.domain import AssetEntity, DomainEntity, EmailEntity, IpEntity, ProfileEntity
from core.intelligence.entity_builder import build_fusion_entities, build_profile_entities, build_surface_entities


class TestIntelligenceEntityBuilder(unittest.TestCase):
    def test_build_profile_entities_extracts_contacts_and_names(self):
        rows = [
            {
                "platform": "GitHub",
                "url": "https://github.com/alice",
                "status": "FOUND",
                "confidence": 91,
                "bio": "Security researcher. Name: Alice Example",
                "contacts": {
                    "emails": ["alice@example.com"],
                    "phones": ["+1 (202) 555-0188"],
                },
                "links": ["https://example.com/about"],
                "mentions": ["alice", "@alice-sec"],
            }
        ]

        entities = build_profile_entities("alice", rows)
        profile_entities = [row for row in entities if isinstance(row, ProfileEntity)]
        email_entities = [row for row in entities if isinstance(row, EmailEntity)]
        phone_entities = [row for row in entities if isinstance(row, AssetEntity) and row.asset_kind == "contact_phone"]
        name_entities = [row for row in entities if isinstance(row, AssetEntity) and row.asset_kind == "identity_name"]

        self.assertEqual(1, len(profile_entities))
        self.assertEqual(1, len(email_entities))
        self.assertEqual(1, len(phone_entities))
        self.assertGreaterEqual(len(name_entities), 1)
        self.assertTrue(phone_entities[0].value.startswith("+1"))

    def test_build_surface_and_fusion_entities(self):
        domain_result = {
            "target": "example.com",
            "resolved_addresses": ["1.1.1.1"],
            "https": {"status": 200},
            "http": {"status": 301, "redirects_to_https": True},
            "subdomains": ["a.example.com", "b.example.com"],
            "rdap": {"name_servers": ["ns1.example.com"]},
            "robots_txt_present": True,
            "security_txt_present": True,
            "robots_preview": "User-agent: *",
            "security_preview": "Contact: security@example.com",
            "scan_notes": [],
        }
        profile_rows = [
            {
                "platform": "GitHub",
                "url": "https://github.com/alice",
                "status": "FOUND",
                "confidence": 80,
                "bio": "Alice Example",
                "contacts": {"emails": ["alice@example.com"], "phones": []},
            }
        ]

        surface_entities = build_surface_entities(domain_result)
        fusion_entities = build_fusion_entities("alice", profile_rows, domain_result)

        self.assertTrue(any(isinstance(row, DomainEntity) for row in surface_entities))
        self.assertTrue(any(isinstance(row, IpEntity) for row in surface_entities))
        self.assertTrue(any(isinstance(row, AssetEntity) and row.asset_kind == "subdomain" for row in surface_entities))
        self.assertTrue(any(isinstance(row, AssetEntity) and row.asset_kind == "nameserver" for row in surface_entities))
        self.assertGreater(len(fusion_entities), len(surface_entities))


if __name__ == "__main__":
    unittest.main()

