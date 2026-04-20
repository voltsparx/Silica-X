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

"""Framework about/description block."""

from __future__ import annotations

from core.foundation.colors import Colors, c
from core.foundation.metadata import AUTHOR, CONTACT_EMAIL, PROJECT_NAME, REPOSITORY_URL, TAGLINE, VERSION, VERSION_THEME


def build_about_text() -> str:
    lines = (
        f"{c(PROJECT_NAME, Colors.EMBER)} v{VERSION}",
        f"{c('Theme:', Colors.EMBER)} {VERSION_THEME}",
        f"{c('Author:', Colors.EMBER)} {AUTHOR}",
        f"{c('Contact:', Colors.EMBER)} {CONTACT_EMAIL}",
        f"{c('Repository:', Colors.EMBER)} {REPOSITORY_URL}",
        f"{c('Description:', Colors.EMBER)} {TAGLINE}",
        f"{c('Capabilities:', Colors.EMBER)} profile intelligence, domain-surface reconnaissance, fusion correlation,",
        "digital footprint mapping, plugin/filter extension pipeline, HTML/JSON/CLI reporting,",
        "Tor/proxy routing controls.",
    )
    return "\n".join(lines)
