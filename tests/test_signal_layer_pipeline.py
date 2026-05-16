# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

import asyncio
import unittest
from unittest.mock import patch

from core.entity import EntityResolver
from core.pipeline import PipelineConfig, run_full_pipeline
from core.reporter_progressive import ProgressiveReporter
from core.scorer import score_profile_finding
from core.signal_layer import Finding, SignalLayer


class _FakeKnowledgeBase:
    def upsert_entity(self, entity, *, risk_score=None):
        return None

    def insert_finding(self, finding):
        return None


class TestSignalLayerPipeline(unittest.TestCase):
    def test_signal_layer_filters_noise_and_duplicates(self):
        finding = Finding(
            source_module="profile",
            entity_id="ent_1",
            platform="github",
            url="https://github.com/alice",
            raw={},
            confidence=0.9,
            why=["exact username match"],
        )
        noise = Finding(
            source_module="profile",
            entity_id="ent_2",
            platform="example",
            url="https://example.com/alice",
            raw={},
            confidence=0.1,
            why=["weak signal"],
        )
        layer = SignalLayer()
        processed = layer.process_batch([finding, finding, noise])
        self.assertEqual(len(processed), 1)
        self.assertEqual(processed[0].tier, "HIGH")

    def test_score_profile_finding_reports_exact_match(self):
        result = score_profile_finding(
            {
                "status_code": 200,
                "username": "alice",
                "bio": "alice builder",
                "followers": 3,
                "cross_platform_link": True,
            },
            "alice",
        )
        self.assertGreater(result.score, 0.5)
        self.assertIn("exact username match", result.why)

    def test_entity_resolver_merges_by_email(self):
        resolver = EntityResolver()
        first = resolver.resolve("alice", email="alice@example.com")
        second = resolver.resolve("alice_dev", email="alice@example.com")
        self.assertEqual(first.canonical_id, second.canonical_id)
        self.assertIn("alice_dev", second.username_variants)

    def test_progressive_reporter_brief_mode(self):
        findings = [
            Finding(
                source_module="profile",
                entity_id="ent_1",
                platform="github",
                url="https://github.com/alice",
                raw={},
                confidence=0.9,
                why=["exact username match", "profile URL returned 200"],
            )
        ]
        reporter = ProgressiveReporter(findings, {"ent_1": 0.8})
        text = reporter.render(mode="brief")
        self.assertIn("SILINOSIC-X REPORT", text)
        self.assertIn("Entity : ent_1", text)

    def test_run_full_pipeline_returns_report(self):
        async def fake_scan_username(**kwargs):
            return [
                {
                    "platform": "GitHub",
                    "url": "https://github.com/alice",
                    "status": "FOUND",
                    "confidence": 85,
                    "context": "status_code=200",
                    "http_status": 200,
                    "contacts": {"emails": ["alice@example.com"], "phones": []},
                    "links": ["https://example.com"],
                    "mentions": [],
                    "bio": "alice security research",
                }
            ]

        async def fake_scan_domain_surface(**kwargs):
            return {
                "target": "example.com",
                "https": {"status": 200},
                "rdap": {"handle": "EXAMPLE"},
                "subdomains": ["api.example.com", "dev.example.com"],
                "prioritized_subdomains": ["dev.example.com"],
                "resolved_addresses": ["1.2.3.4"],
            }

        with (
            patch("core.pipeline.scan_username", new=fake_scan_username),
            patch("core.pipeline.scan_domain_surface", new=fake_scan_domain_surface),
            patch("core.pipeline.GraphKnowledgeBase", return_value=_FakeKnowledgeBase()),
        ):
            report = asyncio.run(
                run_full_pipeline(
                    PipelineConfig(
                        target_usernames=["alice"],
                        target_domains=["example.com"],
                        mode="analyst",
                        run_media_recon=False,
                    )
                )
            )

        self.assertIn("SILINOSIC-X REPORT", report)
        self.assertIn("github.com/alice", report.lower())
