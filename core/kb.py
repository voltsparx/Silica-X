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

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from core.entity import Entity
from core.signal_layer import Finding


SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    canonical_id TEXT PRIMARY KEY,
    username_variants TEXT,
    emails TEXT,
    avatar_hashes TEXT,
    risk_score REAL DEFAULT 0,
    exposure_breadth INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    fingerprint TEXT PRIMARY KEY,
    entity_id TEXT REFERENCES entities(canonical_id),
    source_module TEXT,
    platform TEXT,
    url TEXT,
    confidence REAL,
    tier TEXT,
    why TEXT,
    raw TEXT,
    discovered_at TEXT
);

CREATE TABLE IF NOT EXISTS media_findings (
    id TEXT PRIMARY KEY,
    entity_id TEXT REFERENCES entities(canonical_id),
    url TEXT,
    media_type TEXT,
    phash TEXT,
    ocr_text TEXT,
    gps_lat REAL,
    gps_lon REAL,
    exif_json TEXT,
    anomaly_flags TEXT,
    discovered_at TEXT
);

CREATE TABLE IF NOT EXISTS edges (
    from_entity TEXT REFERENCES entities(canonical_id),
    to_entity TEXT REFERENCES entities(canonical_id),
    edge_type TEXT,
    confidence REAL,
    evidence TEXT,
    created_at TEXT,
    PRIMARY KEY (from_entity, to_entity, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_findings_entity ON findings(entity_id);
CREATE INDEX IF NOT EXISTS idx_findings_tier ON findings(tier);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_entity);
"""

MIGRATION = """
ALTER TABLE profiles RENAME TO findings_old;
"""


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


class GraphKnowledgeBase:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or "output/silinosic_x_kb.db"
        self.ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(path)

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def upsert_entity(self, entity: Entity, *, risk_score: float | None = None) -> None:
        now = _now_utc()
        effective_risk = float(entity.risk_score if risk_score is None else risk_score)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO entities (
                    canonical_id, username_variants, emails, avatar_hashes,
                    risk_score, exposure_breadth, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_id) DO UPDATE SET
                    username_variants=excluded.username_variants,
                    emails=excluded.emails,
                    avatar_hashes=excluded.avatar_hashes,
                    risk_score=excluded.risk_score,
                    exposure_breadth=excluded.exposure_breadth,
                    updated_at=excluded.updated_at
                """,
                (
                    entity.canonical_id,
                    _json_dumps(entity.username_variants),
                    _json_dumps(entity.emails),
                    _json_dumps(entity.avatar_hashes),
                    effective_risk,
                    int(entity.exposure_breadth),
                    now,
                    now,
                ),
            )
            connection.commit()

    def insert_finding(self, finding: Finding) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO findings (
                    fingerprint, entity_id, source_module, platform, url,
                    confidence, tier, why, raw, discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    confidence=excluded.confidence,
                    tier=excluded.tier,
                    why=excluded.why,
                    raw=excluded.raw,
                    discovered_at=excluded.discovered_at
                """,
                (
                    finding.fingerprint,
                    finding.entity_id,
                    finding.source_module,
                    finding.platform,
                    finding.url,
                    float(finding.confidence),
                    finding.tier,
                    _json_dumps(finding.why),
                    _json_dumps(finding.raw),
                    _now_utc(),
                ),
            )
            connection.commit()

    def insert_media_finding(self, entity_id: str, media_finding: Any) -> None:
        payload = asdict(media_finding) if is_dataclass(media_finding) else dict(media_finding or {})
        gps = payload.get("gps_coords") if isinstance(payload.get("gps_coords"), tuple) else None
        media_id = str(payload.get("phash") or payload.get("url") or f"{entity_id}:{payload.get('media_type', '')}")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO media_findings (
                    id, entity_id, url, media_type, phash, ocr_text, gps_lat, gps_lon,
                    exif_json, anomaly_flags, discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    ocr_text=excluded.ocr_text,
                    gps_lat=excluded.gps_lat,
                    gps_lon=excluded.gps_lon,
                    exif_json=excluded.exif_json,
                    anomaly_flags=excluded.anomaly_flags,
                    discovered_at=excluded.discovered_at
                """,
                (
                    media_id,
                    entity_id,
                    str(payload.get("url", "")),
                    str(payload.get("media_type", "")),
                    str(payload.get("phash", "")),
                    str(payload.get("ocr_text", "") or ""),
                    float(gps[0]) if gps else None,
                    float(gps[1]) if gps else None,
                    _json_dumps(payload.get("exif", {})),
                    _json_dumps(payload.get("anomaly_flags", [])),
                    _now_utc(),
                ),
            )
            connection.commit()

    def upsert_edge(
        self,
        from_entity: str,
        to_entity: str,
        edge_type: str,
        *,
        confidence: float = 0.0,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO edges (from_entity, to_entity, edge_type, confidence, evidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_entity, to_entity, edge_type) DO UPDATE SET
                    confidence=excluded.confidence,
                    evidence=excluded.evidence,
                    created_at=excluded.created_at
                """,
                (
                    from_entity,
                    to_entity,
                    edge_type,
                    float(confidence),
                    _json_dumps(evidence or {}),
                    _now_utc(),
                ),
            )
            connection.commit()

    def count_entities(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM entities").fetchone()
        return int(row[0]) if row else 0
