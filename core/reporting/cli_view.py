"""CLI view rendering for fused orchestration payloads."""

from __future__ import annotations

from typing import Any


def render_cli_summary(fused_data: dict[str, Any], advisory: dict[str, Any]) -> str:
    """Render a concise plain-text summary for terminal output."""

    entity_count = int(fused_data.get("entity_count", 0))
    confidence = float(fused_data.get("confidence_score", 0.0))
    anomaly_count = len(fused_data.get("anomalies", [])) if isinstance(fused_data.get("anomalies"), list) else 0
    intelligence_bundle = fused_data.get("intelligence_bundle", {})
    if not isinstance(intelligence_bundle, dict):
        intelligence_bundle = {}
    facets = intelligence_bundle.get("entity_facets", {}) if isinstance(intelligence_bundle.get("entity_facets"), dict) else {}
    risk_summary = intelligence_bundle.get("risk_summary", {}) if isinstance(intelligence_bundle.get("risk_summary"), dict) else {}
    confidence_distribution = (
        intelligence_bundle.get("confidence_distribution", {})
        if isinstance(intelligence_bundle.get("confidence_distribution"), dict)
        else {}
    )

    lines = [
        "[Silica-X Orchestrator Summary]",
        f"entities={entity_count}",
        f"confidence={confidence:.2f}",
        f"anomalies={anomaly_count}",
    ]
    if intelligence_bundle:
        lines.append(f"risk_summary={risk_summary}")
        lines.append(
            "confidence_distribution="
            f"high:{confidence_distribution.get('high', 0)} "
            f"medium:{confidence_distribution.get('medium', 0)} "
            f"low:{confidence_distribution.get('low', 0)}"
        )
        lines.append(f"emails={', '.join((facets.get('emails', []) or [])[:6]) or '-'}")
        lines.append(f"phones={', '.join((facets.get('phones', []) or [])[:6]) or '-'}")
        lines.append(f"names={', '.join((facets.get('names', []) or [])[:6]) or '-'}")

    next_steps = advisory.get("next_steps") if isinstance(advisory.get("next_steps"), list) else []
    for step in next_steps[:3]:
        lines.append(f"next: {step}")
    guidance = intelligence_bundle.get("execution_guidance", {}) if isinstance(intelligence_bundle.get("execution_guidance"), dict) else {}
    actions = guidance.get("actions") if isinstance(guidance.get("actions"), list) else []
    for action in actions[:3]:
        if not isinstance(action, dict):
            continue
        lines.append(f"guide: [{action.get('priority', 'P3')}] {action.get('title', 'Action')}")
    return "\n".join(lines)
