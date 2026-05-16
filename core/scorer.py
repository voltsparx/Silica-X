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

from dataclasses import dataclass
from typing import Any


WEIGHTS = {
    "http_200": 0.20,
    "username_exact": 0.20,
    "bio_keyword_hit": 0.15,
    "avatar_hash_match": 0.15,
    "activity_recent": 0.10,
    "join_date_consistent": 0.08,
    "follower_nonzero": 0.05,
    "cross_link": 0.07,
}


@dataclass
class ScoreResult:
    score: float
    why: list[str]


def score_profile_finding(raw: dict[str, Any], target_username: str) -> ScoreResult:
    score = 0.0
    why: list[str] = []

    if raw.get("status_code") == 200:
        score += WEIGHTS["http_200"]
        why.append("profile URL returned 200")

    found_name = str(raw.get("username", "") or "")
    if found_name.lower() == str(target_username or "").lower():
        score += WEIGHTS["username_exact"]
        why.append("exact username match")

    bio = str(raw.get("bio", "") or "")
    if _bio_has_keyword(bio, target_username):
        score += WEIGHTS["bio_keyword_hit"]
        why.append("bio contains username fragment")

    if raw.get("avatar_hash_match"):
        score += WEIGHTS["avatar_hash_match"]
        why.append("avatar hash matches known reference")

    if raw.get("recent_activity"):
        score += WEIGHTS["activity_recent"]
        why.append("account has recent activity")

    if raw.get("join_date_consistent"):
        score += WEIGHTS["join_date_consistent"]
        why.append("join date consistent with other platforms")

    if int(raw.get("followers", 0) or 0) > 0:
        score += WEIGHTS["follower_nonzero"]
        why.append(f"has {raw['followers']} followers")

    if raw.get("cross_platform_link"):
        score += WEIGHTS["cross_link"]
        why.append("profile links to confirmed platform")

    return ScoreResult(score=min(score, 1.0), why=why)


def _bio_has_keyword(bio: str, username: str) -> bool:
    lowered_username = str(username or "").lower()
    fragments = [lowered_username, lowered_username[:4]]
    lowered_bio = str(bio or "").lower()
    return any(fragment in lowered_bio for fragment in fragments if len(fragment) >= 3)
