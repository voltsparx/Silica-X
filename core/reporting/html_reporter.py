# ──────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────

"""HTML reporter for orchestrated intelligence payloads."""

from __future__ import annotations

from typing import Any

from core.reporting.html_report import render_html_report


def render_html_reporter(target: str, mode: str, fused_data: dict[str, Any], advisory: dict[str, Any]) -> str:
    """Render HTML report string."""

    return render_html_report(target=target, mode=mode, fused_data=fused_data, advisory=advisory)
