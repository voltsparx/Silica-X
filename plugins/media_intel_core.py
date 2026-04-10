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

"""Plugin: public media OCR and metadata extraction for profile intelligence."""

from __future__ import annotations

from core.collect.media_intel import collect_profile_media_intelligence_blocking


PLUGIN_SPEC = {
    "id": "media_intel_core",
    "title": "Media Intelligence Core",
    "description": "Extracts public image metadata and optional OCR text from profile-linked media.",
    "scopes": ["profile", "fusion"],
    "aliases": ["media_intel", "ocr_media", "image_intel"],
    "version": "1.0",
}


def run(context: dict) -> dict:
    profile_results = [
        row for row in (context.get("results", []) or [])
        if isinstance(row, dict)
    ]
    media_result = collect_profile_media_intelligence_blocking(
        profile_results,
        target=str(context.get("target") or ""),
        timeout_seconds=12,
        proxy_url=str(context.get("proxy_url") or "").strip() or None,
    )
    assets = list(media_result.assets)
    ocr_hits = sum(1 for item in assets if item.ocr_text.strip())
    metadata_hits = sum(1 for item in assets if item.metadata)

    if assets:
        severity = "MEDIUM" if ocr_hits else "INFO"
        summary = (
            f"Media intelligence reviewed {len(assets)} public media asset(s), "
            f"with OCR text on {ocr_hits} asset(s) and metadata on {metadata_hits} asset(s)."
        )
    else:
        severity = "INFO"
        summary = "No public media URLs were available for OCR or metadata extraction."

    return {
        "severity": severity,
        "summary": summary,
        "highlights": [
            f"media_urls={len(media_result.media_urls)}",
            f"assets={len(assets)}",
            f"ocr_hits={ocr_hits}",
        ],
        "data": media_result.as_dict(),
    }
