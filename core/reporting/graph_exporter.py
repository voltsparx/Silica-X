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

"""Graph export helpers for fused entity relationship graphs."""

from __future__ import annotations

import json
from typing import Any


def export_graph_json(graph: dict[str, Any]) -> str:
    """Export graph payload as JSON text."""

    return json.dumps(graph, indent=2)


def export_graphml(graph: dict[str, Any]) -> str:
    """Export graph payload as GraphML string."""

    nodes = graph.get("nodes", []) if isinstance(graph.get("nodes"), list) else []
    edges = graph.get("edges", []) if isinstance(graph.get("edges"), list) else []

    node_xml = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", ""))
        node_label = str(node.get("value", ""))
        node_xml.append(f"<node id=\"{node_id}\"><data key=\"label\">{node_label}</data></node>")

    edge_xml = []
    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        edge_xml.append(f"<edge id=\"e{idx}\" source=\"{source}\" target=\"{target}\"/>")

    return "\n".join(
        [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
            "<graph edgedefault=\"undirected\">",
            *node_xml,
            *edge_xml,
            "</graph>",
            "</graphml>",
        ]
    )
