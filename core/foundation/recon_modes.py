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

"""Shared recon mode normalization for surface workflows."""

from __future__ import annotations


RECON_MODE_ALIASES: dict[str, str] = {
    "passive": "passive",
    "stealth": "passive",
    "active": "active",
    "aggressive": "active",
    "hybrid": "hybrid",
    "mixed": "hybrid",
}

RECON_MODES: tuple[str, ...] = ("passive", "active", "hybrid")


def normalize_recon_mode(mode: str | None) -> str:
    """Normalize operator aliases into passive, active, or hybrid."""

    key = str(mode or "").strip().lower()
    return RECON_MODE_ALIASES.get(key, "hybrid")
