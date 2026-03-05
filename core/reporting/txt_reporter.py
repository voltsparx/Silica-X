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

"""Text reporter for orchestrated intelligence payloads."""

from __future__ import annotations

from typing import Any

from core.reporting.cli_view import render_cli_summary


def render_txt_report(fused_data: dict[str, Any], advisory: dict[str, Any]) -> str:
    """Render human-readable text report."""

    return render_cli_summary(fused_data, advisory)
