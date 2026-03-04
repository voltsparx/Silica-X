import unittest

from core.domain import DomainEntity, ProfileEntity
from core.intelligence import IntelligenceEngine


class TestIntelligenceEngine(unittest.TestCase):
    def test_analyze_creates_analysis_ready_bundle(self):
        engine = IntelligenceEngine()
        entities = [
            ProfileEntity(
                id="profile-1",
                value="alice",
                source="username_lookup",
                confidence=0.72,
                attributes={"status": "FOUND", "platform_count": 3},
                platform="github",
                profile_url="https://github.com/alice",
                status="FOUND",
            ),
            DomainEntity(
                id="domain-1",
                value="example.com",
                source="domain_enumeration",
                confidence=0.64,
                attributes={"asn": "AS12345", "registrar": "Example Registrar"},
                domain="example.com",
            ),
        ]

        bundle = engine.analyze(
            entities,
            mode="deep",
            target="alice@example.com",
            anomalies=[{"entity_id": "domain-1", "reason": "credential_leak_reference"}],
            relation_map={"profile-1": ["domain-1"]},
        )

        self.assertTrue(bundle["analysis_ready"])
        self.assertEqual(bundle["metadata"]["scan_mode"], "deep")
        self.assertEqual(len(bundle["entities"]), 2)
        self.assertEqual(len(bundle["evidence"]), 2)
        self.assertTrue(bundle["relationships"])
        self.assertTrue(bundle["risk_summary"]["total"] >= 1)
        self.assertIn("confidence_distribution", bundle)
        self.assertIn("entity_facets", bundle)
        self.assertIn("execution_guidance", bundle)
        self.assertIn("correlation_summary", bundle)
        self.assertTrue(isinstance(bundle["scored_entities"], list))

    def test_analyze_entities_include_trace_fields(self):
        engine = IntelligenceEngine()
        entities = [
            ProfileEntity(
                id="profile-2",
                value="bob",
                source="username_lookup",
                confidence=0.5,
                attributes={"status": "FOUND"},
                platform="reddit",
                profile_url="https://reddit.com/u/bob",
                status="FOUND",
            )
        ]

        bundle = engine.analyze(entities, mode="max", target="bob")
        entity = bundle["entities"][0]

        self.assertTrue(entity["evidence_ids"])
        self.assertIn("confidence_breakdown", entity)
        self.assertIn("risk_level", entity)
        self.assertIn("expansion_depth", entity)
        self.assertIn("expansion_path", entity)
        self.assertIn(entity["risk_level"], {"LOW", "MEDIUM", "HIGH", "CRITICAL"})
        self.assertIn("actions", bundle["execution_guidance"])


if __name__ == "__main__":
    unittest.main()
