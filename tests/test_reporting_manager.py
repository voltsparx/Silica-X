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

from core.reporting.report_manager import ReportManager


class TestReportingManager(unittest.TestCase):
    def test_report_manager_generates_all_formats(self):
        manager = ReportManager()
        payload = manager.generate(
            target="alice",
            mode="profile",
            fused_data={
                "entity_count": 2,
                "confidence_score": 84.2,
                "anomalies": [],
                "graph": {
                    "nodes": [{"id": "n1", "value": "alice", "source": "mock", "type": "profile"}],
                    "edges": [],
                },
            },
            advisory={"next_steps": ["review output"], "overall_confidence": 84.2, "priorities": []},
            lifecycle={"events": []},
        )

        self.assertIn("txt_report", payload)
        self.assertIn("html_report", payload)
        self.assertIn("json_report", payload)
        self.assertIn("graph_json", payload)
        self.assertIn("graph_graphml", payload)
        self.assertIn("<graphml", payload["graph_graphml"])


if __name__ == "__main__":
    unittest.main()
