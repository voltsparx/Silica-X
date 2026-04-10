import unittest
from unittest.mock import patch

import plugins.darkweb_tor_intel as darkweb_plugin
import plugins.entity_link_intel as link_plugin
import plugins.media_intel_core as media_plugin
from core.collect.darkweb_intel import DarkwebSignalResult
from core.collect.link_intel import LinkExplorationResult, LinkObservation
from core.collect.media_intel import MediaAssetObservation, MediaIntelligenceResult


class TestInvestigationPlugins(unittest.TestCase):
    def test_entity_link_plugin_returns_controlled_follow_up_summary(self):
        fake_result = LinkExplorationResult(
            target="alice",
            seed_links=("https://example.com/about",),
            observations=(
                LinkObservation(
                    url="https://example.com/about",
                    final_url="https://example.com/about",
                    classification="web",
                    depth=0,
                    status_code=200,
                    title="About",
                    description="Example",
                    related_links=("https://example.com/team",),
                    contacts={"emails": ["alice@example.com"], "phones": []},
                    bio_excerpt="Example profile",
                ),
            ),
            notes=("Controlled same-host link expansion stayed within one public recursion lane.",),
        )
        with patch("plugins.entity_link_intel.collect_link_exploration_blocking", return_value=fake_result):
            payload = link_plugin.run({"target": "alice", "results": [{"links": ["https://example.com/about"]}]})

        self.assertEqual(payload["severity"], "MEDIUM")
        self.assertIn("public link target", payload["summary"])
        self.assertEqual(payload["data"]["seed_links"], ["https://example.com/about"])

    def test_media_plugin_reports_ocr_and_metadata_counts(self):
        fake_result = MediaIntelligenceResult(
            target="alice",
            media_urls=("https://cdn.example.com/avatar.png",),
            assets=(
                MediaAssetObservation(
                    url="https://cdn.example.com/avatar.png",
                    content_type="image/png",
                    size_bytes=1024,
                    sha256="abc",
                    width=200,
                    height=200,
                    metadata={"format": "PNG"},
                    ocr_text="alice@example.com",
                    ocr_engine="easyocr",
                    extracted_signals={"emails": ["alice@example.com"], "urls": []},
                ),
            ),
            notes=(),
        )
        with patch("plugins.media_intel_core.collect_profile_media_intelligence_blocking", return_value=fake_result):
            payload = media_plugin.run({"target": "alice", "results": [{"media_urls": ["https://cdn.example.com/avatar.png"]}]})

        self.assertEqual(payload["severity"], "MEDIUM")
        self.assertIn("OCR text on 1 asset", payload["summary"])
        self.assertEqual(payload["data"]["assets"][0]["ocr_engine"], "easyocr")

    def test_darkweb_plugin_reports_onion_and_ahmia_hits(self):
        fake_result = DarkwebSignalResult(
            target="alice",
            search_terms=("alice@example.com",),
            onion_references=("abcdefghijklmnop.onion",),
            ahmia_results=(
                {
                    "search_term": "alice@example.com",
                    "onion": "abcdefghijklmnop.onion",
                    "source": "ahmia",
                    "search_url": "https://ahmia.fi/search/?q=alice%40example.com",
                },
            ),
            notes=("Dark-web collection stayed passive.",),
        )
        with patch("plugins.darkweb_tor_intel.collect_darkweb_signals_blocking", return_value=fake_result):
            payload = darkweb_plugin.run({"target": "alice"})

        self.assertEqual(payload["severity"], "MEDIUM")
        self.assertIn("onion reference", payload["summary"])
        self.assertEqual(payload["data"]["onion_references"], ["abcdefghijklmnop.onion"])


if __name__ == "__main__":
    unittest.main()
