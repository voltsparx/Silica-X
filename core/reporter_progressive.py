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

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.signal_layer import Finding


ReportMode = Literal["brief", "analyst", "raw"]


@dataclass
class ReportSection:
    entity_id: str
    risk_score: float
    tier_summary: dict[str, int]
    top_findings: list[Finding]
    all_findings: list[Finding]

    def brief(self) -> str:
        lines = [
            f"  Entity : {self.entity_id}",
            f"  Risk   : {self.risk_score:.2f}",
            (
                f"  Signal : {self.tier_summary.get('HIGH', 0)} HIGH | "
                f"{self.tier_summary.get('MEDIUM', 0)} MEDIUM"
            ),
            "  Top findings:",
        ]
        for finding in self.top_findings[:3]:
            lines.append(f"    [{finding.platform}] {finding.url} - {', '.join(finding.why[:2])}")
        return "\n".join(lines)

    def analyst(self) -> str:
        lines = [self.brief(), "", "  All findings:"]
        for finding in self.all_findings:
            lines.append(
                f"    [{finding.tier:<6}] [{finding.platform}] conf={finding.confidence:.2f} | {finding.url}\n"
                f"             why: {'; '.join(finding.why)}"
            )
        return "\n".join(lines)


class ProgressiveReporter:
    def __init__(self, findings: list[Finding], entity_risk_scores: dict[str, float]) -> None:
        self._findings = findings
        self._risk = entity_risk_scores
        self._sections = self._build_sections()

    def _build_sections(self) -> list[ReportSection]:
        grouped: dict[str, list[Finding]] = {}
        for finding in self._findings:
            grouped.setdefault(finding.entity_id, []).append(finding)

        sections: list[ReportSection] = []
        for entity_id, findings in grouped.items():
            tier_summary: dict[str, int] = {}
            for finding in findings:
                tier_summary[finding.tier] = tier_summary.get(finding.tier, 0) + 1

            top = [finding for finding in findings if finding.tier == "HIGH"][:5]
            if not top:
                top = findings[:3]

            sections.append(
                ReportSection(
                    entity_id=entity_id,
                    risk_score=self._risk.get(entity_id, 0.0),
                    tier_summary=tier_summary,
                    top_findings=top,
                    all_findings=findings,
                )
            )

        sections.sort(key=lambda item: item.risk_score, reverse=True)
        return sections

    def render(self, mode: ReportMode = "analyst") -> str:
        header = f"{'=' * 72}\n  SILINOSIC-X REPORT  |  Mode: {mode.upper()}\n{'=' * 72}\n"
        body_parts: list[str] = []

        if mode == "brief":
            for section in self._sections:
                if section.tier_summary.get("HIGH", 0) > 0 or section.risk_score >= 0.65:
                    body_parts.append(section.brief())
        elif mode == "analyst":
            for section in self._sections:
                body_parts.append(section.analyst())
        else:
            for section in self._sections:
                body_parts.append(section.analyst())
                body_parts.append("  RAW ARTIFACTS:")
                for finding in section.all_findings:
                    body_parts.append(f"    {finding.raw}")

        if not body_parts:
            body_parts = ["  No HIGH-confidence findings. Use --analyst for full output."]

        footer = f"\n{'=' * 72}\n  END OF REPORT\n{'=' * 72}"
        return header + "\n\n".join(body_parts) + footer
