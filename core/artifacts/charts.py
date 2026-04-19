# ──────────────────────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
# ──────────────────────────────────────────────────────────────────────────────

"""Shared chart generation helpers for portable report outputs."""

from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _status_counts(payload: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in payload.get("results", []) or []:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", "unknown")).strip().upper() or "UNKNOWN"
        counts[status] = counts.get(status, 0) + 1
    return counts or {"NO DATA": 1}


def _severity_counts(payload: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in payload.get("issues", []) or []:
        if not isinstance(row, dict):
            continue
        severity = str(row.get("severity", "INFO")).strip().upper() or "INFO"
        counts[severity] = counts.get(severity, 0) + 1
    return counts or {"INFO": 1}


def _confidence_values(payload: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for row in payload.get("results", []) or []:
        if not isinstance(row, dict):
            continue
        raw = _coerce_float(row.get("confidence"))
        if raw is not None:
            values.append(raw)
    return values or [0.0]


def _response_times(payload: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for row in payload.get("results", []) or []:
        if not isinstance(row, dict):
            continue
        raw = _coerce_float(row.get("response_time_ms"))
        if raw is not None:
            values.append(raw)
    return values or [0.0]


def build_chart_images(payload: dict[str, Any]) -> tuple[TemporaryDirectory[str] | None, dict[str, Path]]:
    """Create chart PNGs and return their paths.

    Returns `(temp_dir, paths)` so the caller can keep the temp directory alive
    until report generation is finished.
    """

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None, {}

    temp_dir = TemporaryDirectory()
    root = Path(temp_dir.name)
    charts: dict[str, Path] = {}

    status_counts = _status_counts(payload)
    severity_counts = _severity_counts(payload)
    confidence_values = _confidence_values(payload)
    response_times = _response_times(payload)

    def _save(name: str) -> Path:
        return root / f"{name}.png"

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.bar(list(status_counts.keys()), list(status_counts.values()), color="#f47c20")
    ax.set_title("Result Status Distribution")
    ax.set_ylabel("Count")
    fig.tight_layout()
    status_path = _save("status-bar")
    fig.savefig(status_path, dpi=160)
    plt.close(fig)
    charts["status_bar"] = status_path

    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.pie(
        list(severity_counts.values()),
        labels=list(severity_counts.keys()),
        autopct="%1.0f%%",
        colors=["#ff6b7d", "#ff8a3d", "#ffb454", "#70b9ff", "#87d6a6"][: len(severity_counts)],
    )
    ax.set_title("Issue Severity Mix")
    fig.tight_layout()
    severity_path = _save("severity-pie")
    fig.savefig(severity_path, dpi=160)
    plt.close(fig)
    charts["severity_pie"] = severity_path

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(range(1, len(response_times) + 1), response_times, color="#ff8a3d", linewidth=2.2)
    ax.set_title("Response Time Trend")
    ax.set_xlabel("Result Index")
    ax.set_ylabel("ms")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    line_path = _save("response-line")
    fig.savefig(line_path, dpi=160)
    plt.close(fig)
    charts["response_line"] = line_path

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.hist(confidence_values, bins=min(max(len(confidence_values), 4), 10), color="#d4651a", edgecolor="#fff4ea")
    ax.set_title("Confidence Histogram")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    hist_path = _save("confidence-hist")
    fig.savefig(hist_path, dpi=160)
    plt.close(fig)
    charts["confidence_hist"] = hist_path

    return temp_dir, charts


def build_relationship_graph_svg(fused_intel: dict) -> str:
    """Produce a simple relationship-map SVG using only stdlib layout math."""

    if not isinstance(fused_intel, dict):
        return ""
    relation_map = fused_intel.get("relationship_map", {})
    if not isinstance(relation_map, dict) or not relation_map:
        return ""

    node_ids: list[str] = []
    seen: set[str] = set()
    for source, targets in relation_map.items():
        source_id = str(source or "").strip()
        if source_id and source_id not in seen:
            seen.add(source_id)
            node_ids.append(source_id)
        if isinstance(targets, (list, tuple, set)):
            for target in targets:
                target_id = str(target or "").strip()
                if target_id and target_id not in seen:
                    seen.add(target_id)
                    node_ids.append(target_id)
    if not node_ids:
        return ""

    width, height = 800, 600
    center_x, center_y = width / 2, height / 2
    radius = min(width, height) * 0.34
    positions: dict[str, tuple[float, float]] = {}
    for index, node_id in enumerate(node_ids):
        angle = (2 * math.pi * index / max(1, len(node_ids))) - (math.pi / 2)
        positions[node_id] = (
            center_x + math.cos(angle) * radius,
            center_y + math.sin(angle) * radius,
        )

    edge_markup: list[str] = []
    seen_edges: set[tuple[str, str]] = set()
    for source, targets in relation_map.items():
        source_id = str(source or "").strip()
        if source_id not in positions or not isinstance(targets, (list, tuple, set)):
            continue
        x1, y1 = positions[source_id]
        for target in targets:
            target_id = str(target or "").strip()
            if target_id not in positions or target_id == source_id:
                continue
            edge_key = (source_id, target_id) if source_id <= target_id else (target_id, source_id)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            x2, y2 = positions[target_id]
            edge_markup.append(
                f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
                "stroke='#6a4327' stroke-width='2' opacity='0.84' />"
            )

    node_markup: list[str] = []
    for node_id in node_ids:
        x, y = positions[node_id]
        safe = (
            str(node_id)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        node_markup.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='18' fill='#c87941' stroke='#fff1e4' stroke-width='2' />"
        )
        node_markup.append(
            f"<text x='{x:.1f}' y='{(y + 34):.1f}' fill='#fff1e4' font-size='12' text-anchor='middle'>{safe}</text>"
        )

    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 600'>"
        "<rect width='800' height='600' fill='#140d08' rx='18' ry='18' />"
        + "".join(edge_markup)
        + "".join(node_markup)
        + "</svg>"
    )
