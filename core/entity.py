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

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Entity:
    canonical_id: str
    username_variants: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    avatar_hashes: list[str] = field(default_factory=list)
    platforms: dict[str, str] = field(default_factory=dict)
    risk_score: float = 0.0
    exposure_breadth: int = 0

    def merge(self, other: Entity) -> None:
        for value in other.username_variants:
            if value not in self.username_variants:
                self.username_variants.append(value)
        for value in other.emails:
            if value not in self.emails:
                self.emails.append(value)
        for value in other.avatar_hashes:
            if value not in self.avatar_hashes:
                self.avatar_hashes.append(value)
        self.platforms.update(other.platforms)
        self.exposure_breadth = len(self.platforms)


class EntityResolver:
    """
    Resolves raw usernames/emails into canonical entity IDs.
    Uses fuzzy matching on usernames and exact match on email/avatar hash.
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._email_index: dict[str, str] = {}
        self._username_index: dict[str, str] = {}
        self._avatar_index: dict[str, str] = {}

    def resolve(
        self,
        username: str,
        email: Optional[str] = None,
        avatar_hash: Optional[str] = None,
    ) -> Entity:
        canonical_id = self._find_existing(username, email, avatar_hash)
        if canonical_id:
            entity = self._entities[canonical_id]
            if username and username not in entity.username_variants:
                entity.username_variants.append(username)
        else:
            canonical_id = self._make_id(username)
            entity = Entity(
                canonical_id=canonical_id,
                username_variants=[username] if username else [],
            )
            self._entities[canonical_id] = entity
            if username:
                self._username_index[_normalize(username)] = canonical_id

        if email and email not in self._email_index:
            self._email_index[email] = canonical_id
            if email not in entity.emails:
                entity.emails.append(email)
        if avatar_hash and avatar_hash not in self._avatar_index:
            self._avatar_index[avatar_hash] = canonical_id
            if avatar_hash not in entity.avatar_hashes:
                entity.avatar_hashes.append(avatar_hash)
        return entity

    def _find_existing(self, username: str, email: Optional[str], avatar_hash: Optional[str]) -> Optional[str]:
        if email and email in self._email_index:
            return self._email_index[email]
        if avatar_hash and avatar_hash in self._avatar_index:
            return self._avatar_index[avatar_hash]
        norm = _normalize(username)
        if norm in self._username_index:
            return self._username_index[norm]
        return None

    def _make_id(self, username: str) -> str:
        return "ent_" + hashlib.sha256(str(username or "").encode("utf-8", errors="replace")).hexdigest()[:12]

    def all_entities(self) -> list[Entity]:
        return list(self._entities.values())


def _normalize(username: str) -> str:
    u = str(username or "").lower()
    u = re.sub(r"[_.\-]", "", u)
    u = re.sub(r"(official|real|the|0|_|dev|irl)$", "", u)
    return u.strip()
