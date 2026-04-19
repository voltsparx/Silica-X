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

"""Compatibility shim for legacy imports."""

from __future__ import annotations

from typing import Any

from core.artifacts.html_report import generate_html as _generate_html
from core.artifacts.storage import sanitize_target
from core.reporting.report_generator import ReportGenerator as _BaseReportGenerator


def generate_html(*args: Any, **kwargs: Any) -> str:
    """Proxy to HTML generator (patchable in tests)."""

    return _generate_html(*args, **kwargs)


class ReportGenerator(_BaseReportGenerator):
    """Compat wrapper that routes HTML generation through this module."""

    def generate_html_dashboard(self, fused_data: dict[str, Any]) -> str:
        target_data = fused_data.get("target")
        if isinstance(target_data, dict):
            username = str(target_data.get("username") or "").strip()
            domain = str(target_data.get("domain") or "").strip()
            token = f"{username}_{domain}".strip("_")
            target = sanitize_target(token or "fused-target")
        else:
            target = sanitize_target(str(target_data or "fused-target"))

        output_stamp = fused_data.get("output_stamp") if isinstance(fused_data, dict) else None
        intelligence_bundle = (
            fused_data.get("intelligence_bundle")
            if isinstance(fused_data.get("intelligence_bundle"), dict)
            else (fused_data.get("fused_intel", {}) or {}).get("intelligence_bundle")
        )
        return generate_html(
            target=target,
            results=list(fused_data.get("results", []) or []),
            correlation=dict(fused_data.get("correlation", {}) or {}),
            issues=list(fused_data.get("issues", []) or []),
            issue_summary=dict(fused_data.get("issue_summary", {}) or {}),
            narrative=str(fused_data.get("narrative") or ""),
            domain_result=fused_data.get("domain_result") if isinstance(fused_data.get("domain_result"), dict) else None,
            mode=str(fused_data.get("mode") or "fusion"),
            plugin_results=list(fused_data.get("plugins", []) or []),
            plugin_errors=list(fused_data.get("plugin_errors", []) or []),
            filter_results=list(fused_data.get("filters", []) or []),
            filter_errors=list(fused_data.get("filter_errors", []) or []),
            intelligence_bundle=intelligence_bundle if isinstance(intelligence_bundle, dict) else {},
            ocr_scan=fused_data.get("ocr_scan") if isinstance(fused_data.get("ocr_scan"), dict) else None,
            fused_intel=fused_data.get("fused_intel") if isinstance(fused_data.get("fused_intel"), dict) else None,
            extra_payload=fused_data.get("extra_payload") if isinstance(fused_data.get("extra_payload"), dict) else None,
            output_stamp=output_stamp,
        )

    def generate_intelligence_brief(self, bundle: dict) -> str:
        """Generate a structured text intelligence brief from an intel bundle."""

        target_model = bundle.get("target_model", {}) if isinstance(bundle.get("target_model"), dict) else {}
        risk_summary = bundle.get("risk_summary", {}) if isinstance(bundle.get("risk_summary"), dict) else {}
        guidance = bundle.get("execution_guidance", {}) if isinstance(bundle.get("execution_guidance"), dict) else {}
        footprint_map = bundle.get("footprint_map", {}) if isinstance(bundle.get("footprint_map"), dict) else {}
        target = str(bundle.get("target") or bundle.get("target_key") or "unknown")
        entity_class = str(target_model.get("entity_class") or "unknown")
        confidence = int(round(float(target_model.get("confidence", 0.0) or 0.0) * 100))
        risk_level = str(risk_summary.get("level") or risk_summary.get("overall_level") or "INFO").upper()
        findings = []
        for key in ("names", "emails", "phones", "domains", "hosts"):
            values = footprint_map.get(key)
            if isinstance(values, list) and values:
                findings.append(f"{key}: {', '.join(str(item) for item in values[:3])}")
        if not findings:
            findings = ["No major finding clusters were summarized."]
        risks = [str(item) for item in list(target_model.get("risk_indicators", []) or [])]
        if not risks:
            risks = ["No explicit risk indicators were inferred."]
        actions_raw = guidance.get("actions", []) if isinstance(guidance.get("actions"), list) else []
        actions = [
            str(item.get("title") or "Review the collected telemetry.")
            for item in actions_raw
            if isinstance(item, dict)
        ] or ["Review the collected telemetry."]

        width = 70

        def _fit(text: str) -> str:
            value = str(text or "")
            return value if len(value) <= width - 4 else value[: width - 7] + "..."

        def _row(text: str) -> str:
            return f"│ {_fit(text).ljust(width - 4)} │"

        lines = [
            "┌─ SILICA-X INTELLIGENCE BRIEF " + "─" * (width - 31) + "┐",
            _row(f"Target: {target}"),
            _row(f"Entity: {entity_class} | Confidence: {confidence}%"),
            _row(f"Risk Level: {risk_level}"),
            "├─ KEY FINDINGS " + "─" * (width - 17) + "┤",
        ]
        lines.extend(_row(f"• {item}") for item in findings[:5])
        lines.append("├─ RISK INDICATORS " + "─" * (width - 21) + "┤")
        lines.extend(_row(f"• {item}") for item in risks[:5])
        lines.append("├─ RECOMMENDED NEXT STEPS " + "─" * (width - 28) + "┤")
        lines.extend(_row(f"• {item}") for item in actions[:5])
        lines.append("└" + "─" * (width - 2) + "┘")
        return "\n".join(lines)

__all__ = ["ReportGenerator", "generate_html"]
