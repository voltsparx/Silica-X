# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Any


_NOISE_FIELDS = {
    "cdn_ip",
    "generic_description",
    "default_avatar",
    "suspended",
    "deactivated",
    "join_date_only",
    "cached_404",
    "rate_limited_guess",
}

_LOW_VALUE_PLATFORMS = {
    "placeholder_site",
    "parked_domain",
    "link_aggregator_generic",
}


def is_worth_storing(raw: dict[str, Any], platform_category: str = "") -> tuple[bool, str]:
    if raw.get("suspended") or raw.get("deactivated"):
        return False, "account is suspended or deactivated"

    if raw.get("status_code", 200) not in (200, 301, 302):
        if not raw.get("cached_content"):
            return False, f"non-200 status ({raw.get('status_code')}) with no cached content"

    if raw.get("avatar_is_default"):
        raw.pop("avatar_hash", None)

    if not raw.get("bio") and int(raw.get("followers", 0) or 0) == 0 and not raw.get("recent_activity"):
        return False, "ghost account: no bio, no followers, no activity"

    if platform_category in _LOW_VALUE_PLATFORMS:
        return False, f"low-value platform category: {platform_category}"

    return True, "passed relevance gate"
