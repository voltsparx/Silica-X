# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

"""Plugin: passive dark-web reference collection with Tor-aware public indexing."""

from __future__ import annotations

from core.collect.darkweb_intel import collect_darkweb_signals_blocking


PLUGIN_SPEC = {
    "id": "darkweb_tor_intel",
    "title": "Darkweb Tor Intelligence",
    "description": "Collects passive onion references and Tor-aware Ahmia search hints from public investigation context.",
    "scopes": ["profile", "surface", "fusion"],
    "aliases": ["darkweb", "darknet", "tor_intel", "onion_intel"],
    "version": "1.0",
}


def run(context: dict) -> dict:
    darkweb_result = collect_darkweb_signals_blocking(context, timeout_seconds=12)
    results = list(darkweb_result.ahmia_results)
    onion_refs = list(darkweb_result.onion_references)

    if results or onion_refs:
        severity = "MEDIUM" if onion_refs else "INFO"
        summary = (
            f"Dark-web intelligence identified {len(onion_refs)} onion reference(s) "
            f"and {len(results)} public Ahmia search result hint(s)."
        )
    else:
        severity = "INFO"
        summary = "No passive dark-web references were found in the current public investigation context."

    return {
        "severity": severity,
        "summary": summary,
        "highlights": [
            f"search_terms={len(darkweb_result.search_terms)}",
            f"onion_refs={len(onion_refs)}",
            f"ahmia_results={len(results)}",
        ],
        "data": darkweb_result.as_dict(),
    }
