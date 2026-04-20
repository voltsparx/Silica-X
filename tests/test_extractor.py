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

import unittest

from core.collect.extractor import (
    extract_bio,
    extract_contacts,
    extract_links,
    extract_username_mentions,
    filter_valid_hostnames,
)


class TestExtractor(unittest.TestCase):
    def test_extract_bio_supports_single_quote_meta(self):
        html = "<meta name='description' content='Hello &amp; welcome'>"
        self.assertEqual(extract_bio(html), "Hello & welcome")

    def test_extract_links_handles_quote_variants_and_dedupes(self):
        html = (
            '<a href="https://alpha.example">A</a>'
            "<a href='https://beta.example/path'>B</a>"
            '<a href="https://alpha.example#fragment">A2</a>'
        )
        self.assertEqual(extract_links(html), ["https://alpha.example", "https://beta.example/path"])

    def test_extract_contacts_ignores_short_phone_noise(self):
        html = (
            "<script>var hidden='bot@spam.example';</script>"
            "<p>Mail me at User@Test.com and call +1 (202) 555-0188 or 123-45.</p>"
        )
        contacts = extract_contacts(html)
        self.assertEqual(contacts["emails"], ["user@test.com"])
        self.assertEqual(contacts["phones"], ["+1 (202) 555-0188"])

    def test_extract_username_mentions_from_text(self):
        html = "<p>Alice account @alice has alias alice and mirror /alice</p>"
        mentions = extract_username_mentions(html, "alice")
        self.assertIn("alice", [value.lower() for value in mentions])
        self.assertIn("@alice", [value.lower() for value in mentions])
        self.assertIn("/alice", [value.lower() for value in mentions])

    def test_extract_contacts_filters_invalid_email_and_phone_noise(self):
        html = (
            "<p>Noise admin..ops@example..com and 00000000 and 1111111111.</p>"
            "<p>Valid: analyst@example.com and +1 (202) 555-0188</p>"
        )
        contacts = extract_contacts(html)
        self.assertEqual(contacts["emails"], ["analyst@example.com"])
        self.assertEqual(contacts["phones"], ["+1 (202) 555-0188"])

    def test_filter_valid_hostnames_restricts_to_base_domain(self):
        values = [
            "api.example.com",
            "*.dev.example.com",
            "mailto:test@example.com",
            "evil-example.net",
            "bad_host",
        ]
        self.assertEqual(
            filter_valid_hostnames(values, base_domain="example.com"),
            ["api.example.com", "dev.example.com"],
        )


if __name__ == "__main__":
    unittest.main()
