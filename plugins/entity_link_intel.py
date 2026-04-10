# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Proprietary
#
# Sylica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Sylica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Sylica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ------------------------------------------------------------------------------

"""Plugin: controlled recursive intelligence from public bio and entity links."""

from __future__ import annotations

from core.collect.link_intel import collect_link_exploration_blocking


PLUGIN_SPEC = {
    "id": "entity_link_intel",
    "title": "Entity Link Intelligence",
    "description": "Follows public bio/entity links in a controlled depth-limited way for deeper public-context gathering.",
    "scopes": ["profile", "fusion"],
    "aliases": ["link_intel", "bio_links", "deep_links"],
    "version": "1.0",
}


def run(context: dict) -> dict:
    profile_results = [
        row for row in (context.get("results", []) or [])
        if isinstance(row, dict)
    ]
    exploration = collect_link_exploration_blocking(
        profile_results,
        target=str(context.get("target") or ""),
        timeout_seconds=10,
        proxy_url=str(context.get("proxy_url") or "").strip() or None,
        max_depth=1,
        max_seed_links=8,
    )
    observations = list(exploration.observations)
    contact_hits = sum(
        len(item.contacts.get("emails", [])) + len(item.contacts.get("phones", []))
        for item in observations
    )

    if observations:
        severity = "MEDIUM" if contact_hits or any(item.classification == "repository" for item in observations) else "INFO"
        summary = (
            f"Controlled link intelligence reviewed {len(observations)} public link target(s) "
            f"from bios/entities and extracted {contact_hits} contact signal(s)."
        )
    else:
        severity = "INFO"
        summary = "No public bio/entity links were available for controlled follow-up."

    return {
        "severity": severity,
        "summary": summary,
        "highlights": [
            f"seed_links={len(exploration.seed_links)}",
            f"observations={len(observations)}",
            f"contact_hits={contact_hits}",
        ],
        "data": exploration.as_dict(),
    }
