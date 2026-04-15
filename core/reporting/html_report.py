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

"""HTML report rendering for orchestrator outputs."""

from __future__ import annotations

import html
from typing import Any


def _safe_list(values: Any) -> list:
    return values if isinstance(values, list) else []


def render_html_report(target: str, mode: str, fused_data: dict[str, Any], advisory: dict[str, Any]) -> str:
    """Render HTML text from fused and advisory outputs."""

    anomalies = _safe_list(fused_data.get("anomalies"))
    recommendations = _safe_list(advisory.get("next_steps"))
    intelligence_bundle = fused_data.get("intelligence_bundle", {})
    if not isinstance(intelligence_bundle, dict):
        intelligence_bundle = {}
    facets = intelligence_bundle.get("entity_facets", {}) if isinstance(intelligence_bundle.get("entity_facets"), dict) else {}
    confidence_distribution = (
        intelligence_bundle.get("confidence_distribution", {})
        if isinstance(intelligence_bundle.get("confidence_distribution"), dict)
        else {}
    )
    risk_summary = intelligence_bundle.get("risk_summary", {}) if isinstance(intelligence_bundle.get("risk_summary"), dict) else {}
    scored_entities = _safe_list(intelligence_bundle.get("scored_entities"))
    guidance = intelligence_bundle.get("execution_guidance", {}) if isinstance(intelligence_bundle.get("execution_guidance"), dict) else {}
    actions = _safe_list(guidance.get("actions"))

    anomaly_items = "".join(
        (
            f"<li>{html.escape(str(item.get('entity_id', '-')))}: {html.escape(str(item.get('reason', '-')))}</li>"
            if isinstance(item, dict)
            else f"<li>{html.escape(str(item))}</li>"
        )
        for item in anomalies[:32]
    )
    recommendation_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in recommendations[:10])
    guidance_items = "".join(
        (
            "<li>"
            f"[{html.escape(str(item.get('priority', 'P3')))}] {html.escape(str(item.get('title', 'Action')))}"
            f"<br><span class='muted'>{html.escape(str(item.get('rationale', '-')))}</span>"
            f"<br><span class='muted'>Hint: {html.escape(str(item.get('command_hint', '-')))}</span>"
            "</li>"
        )
        for item in actions[:8]
        if isinstance(item, dict)
    )

    contact_rows = []
    for row in _safe_list(facets.get("scored_contacts"))[:20]:
        if not isinstance(row, dict):
            continue
        contact_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('kind', '-')))}</td>"
            f"<td>{html.escape(str(row.get('value', '-')))}</td>"
            f"<td>{html.escape(str(row.get('score_percent', 0)))}%</td>"
            f"<td>{html.escape(str(row.get('supporting_entities', 0)))}</td>"
            f"<td>{html.escape(str(row.get('risk_level', 'LOW')))}</td>"
            "</tr>"
        )
    if not contact_rows:
        contact_rows.append("<tr><td colspan='5'>No scored contacts/names.</td></tr>")

    entity_rows = []
    for row in scored_entities[:26]:
        if not isinstance(row, dict):
            continue
        entity_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('rank', '-')))}</td>"
            f"<td>{html.escape(str(row.get('entity_type', '-')))}</td>"
            f"<td>{html.escape(str(row.get('value', '-')))}</td>"
            f"<td>{html.escape(str(row.get('source', '-')))}</td>"
            f"<td>{html.escape(str(row.get('confidence_percent', 0)))}%</td>"
            f"<td>{html.escape(str(row.get('risk_level', 'LOW')))}</td>"
            "</tr>"
        )
    if not entity_rows:
        entity_rows.append("<tr><td colspan='6'>No scored entities.</td></tr>")

    emails = ", ".join(_safe_list(facets.get("emails"))[:8]) or "-"
    phones = ", ".join(_safe_list(facets.get("phones"))[:8]) or "-"
    names = ", ".join(_safe_list(facets.get("names"))[:8]) or "-"

    return f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Silica-X Orchestrator Report</title>
  <style>
    body {{ font-family: \"Segoe UI\", sans-serif; margin: 24px; background: #fff6ee; color: #2c1608; }}
    .card {{ border: 1px solid #f0bf97; background: #fffdfb; border-radius: 10px; padding: 14px; margin-bottom: 12px; box-shadow: 0 8px 24px rgba(168, 88, 21, 0.08); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #f1d6bf; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #fff0e0; color: #7a3f12; }}
    .muted {{ color: #8d6445; }}
  </style>
</head>
<body>
  <h1>Silica-X Orchestrator Report</h1>
  <div class=\"card\"><strong>Target:</strong> {html.escape(target)}</div>
  <div class=\"card\"><strong>Mode:</strong> {html.escape(mode)}</div>
  <div class=\"card\"><strong>Entity Count:</strong> {int(fused_data.get('entity_count', 0))}</div>
  <div class=\"card\"><strong>Confidence:</strong> {float(fused_data.get('confidence_score', 0.0)):.2f}</div>
  <div class=\"card\"><strong>Anomalies:</strong><ul>{anomaly_items or '<li>None</li>'}</ul></div>
  <div class=\"card\"><strong>Recommendations:</strong><ul>{recommendation_items or '<li>None</li>'}</ul></div>
  <div class=\"card\">
    <h3>Intelligence Summary</h3>
    <p><strong>Risk:</strong> {html.escape(str(risk_summary))}</p>
    <p><strong>Confidence Distribution:</strong>
      high={html.escape(str(confidence_distribution.get('high', 0)))}
      medium={html.escape(str(confidence_distribution.get('medium', 0)))}
      low={html.escape(str(confidence_distribution.get('low', 0)))}
    </p>
    <p><strong>Emails:</strong> {html.escape(emails)}</p>
    <p><strong>Phones:</strong> {html.escape(phones)}</p>
    <p><strong>Names:</strong> {html.escape(names)}</p>
  </div>
  <div class=\"card\">
    <h3>Top Contact / Name Signals</h3>
    <table>
      <tr><th>Kind</th><th>Value</th><th>Score</th><th>Support</th><th>Risk</th></tr>
      {''.join(contact_rows)}
    </table>
  </div>
  <div class=\"card\">
    <h3>Top Scored Entities</h3>
    <table>
      <tr><th>Rank</th><th>Type</th><th>Value</th><th>Source</th><th>Confidence</th><th>Risk</th></tr>
      {''.join(entity_rows)}
    </table>
  </div>
  <div class=\"card\"><h3>Execution Guidance</h3><ul>{guidance_items or '<li>None</li>'}</ul></div>
</body>
</html>
""".strip()
