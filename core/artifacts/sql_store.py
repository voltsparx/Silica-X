# ──────────────────────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
# ──────────────────────────────────────────────────────────────────────────────

"""SQLite artifact storage for full scan payloads."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def write_sqlite_report(path: Path, payload: dict[str, Any]) -> str:
    """Persist the full run payload to a SQLite database file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                mode TEXT NOT NULL,
                generated_at_utc TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS findings (
                run_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                identifier TEXT NOT NULL,
                severity TEXT,
                summary TEXT,
                data_json TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                run_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                details_json TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_items (
                run_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                source_kind TEXT,
                ocr_engine TEXT,
                confidence_hint TEXT,
                text_excerpt TEXT,
                signals_json TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        generated_at = str((payload.get("metadata") or {}).get("generated_at_utc") or "")
        summary_json = json.dumps(payload.get("summary", {}), indent=2, default=str)
        payload_json = json.dumps(payload, indent=2, default=str)
        cursor = conn.execute(
            """
            INSERT INTO runs(target, mode, generated_at_utc, summary_json, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(payload.get("target", "")),
                str((payload.get("metadata") or {}).get("mode", "profile")),
                generated_at,
                summary_json,
                payload_json,
            ),
        )
        run_id = int(cursor.lastrowid or 0)

        def _insert_rows(kind: str, rows: list[dict[str, Any]], identifier_key: str, summary_key: str) -> None:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                conn.execute(
                    """
                    INSERT INTO findings(run_id, kind, identifier, severity, summary, data_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        kind,
                        str(row.get(identifier_key, row.get("id", kind))),
                        str(row.get("severity", "")),
                        str(row.get(summary_key, row.get("title", ""))),
                        json.dumps(row, indent=2, default=str),
                    ),
                )

        _insert_rows("result", list(payload.get("results", []) or []), "platform", "context")
        _insert_rows("issue", list(payload.get("issues", []) or []), "title", "recommendation")
        _insert_rows("plugin", list(payload.get("plugins", []) or []), "id", "summary")
        _insert_rows("filter", list(payload.get("filters", []) or []), "id", "summary")
        for kind, key in (("plugin", "selected_plugins"), ("filter", "selected_filters"), ("module", "attached_modules")):
            raw_value = payload.get(key)
            if kind == "module":
                rows = raw_value if isinstance(raw_value, list) else []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    conn.execute(
                        """
                        INSERT INTO attachments(run_id, kind, name, details_json)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            kind,
                            str(row.get("id", "module")),
                            json.dumps(row, indent=2, default=str),
                        ),
                    )
                continue
            names = raw_value if isinstance(raw_value, list) else []
            for name in names:
                conn.execute(
                    """
                    INSERT INTO attachments(run_id, kind, name, details_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        kind,
                        str(name),
                        json.dumps({"name": str(name)}, indent=2, default=str),
                    ),
                )
        ocr_scan = payload.get("ocr_scan", {}) if isinstance(payload.get("ocr_scan"), dict) else {}
        ocr_items = ocr_scan.get("items", []) if isinstance(ocr_scan.get("items"), list) else []
        for item in ocr_items:
            if not isinstance(item, dict):
                continue
            conn.execute(
                """
                INSERT INTO ocr_items(run_id, source, source_kind, ocr_engine, confidence_hint, text_excerpt, signals_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(item.get("source", "image")),
                    str(item.get("source_kind", "")),
                    str(item.get("ocr_engine", "")),
                    str(item.get("confidence_hint", "")),
                    str(item.get("normalized_text", "") or item.get("raw_text", ""))[:4000],
                    json.dumps(item.get("signals", {}), indent=2, default=str),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    return str(path)


class KnowledgeBase:
    """Cross-session persistent knowledge base for Silica-X.

    Stores findings from every scan so future scans of the same or related
    targets can be enriched with historical context.

    All methods are synchronous and safe to call from async context via
    asyncio.run_in_executor. All SQL operations use parameterized queries.
    The database is created automatically on first use.
    """

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            try:
                from core.foundation.output_config import get_output_settings

                settings = get_output_settings()
                root = settings.output_root or Path("output")
                db_path = str(Path(root) / "silica_x_kb.db")
            except Exception:
                db_path = "output/silica_x_kb.db"
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create all tables if they do not exist."""
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scan_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    scan_count INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS found_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    profile_url TEXT,
                    confidence INTEGER,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS contact_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source_platform TEXT,
                    first_seen TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS domain_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    finding_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    first_seen TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    fingerprint_id TEXT NOT NULL,
                    component_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS risk_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    risk_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    detail TEXT,
                    first_seen TEXT NOT NULL
                );
                """
            )
        finally:
            conn.close()

    def record_scan_target(self, target: str, target_type: str) -> None:
        """Record or update a scan target."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT id, scan_count FROM scan_targets WHERE target = ?",
                (target,),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE scan_targets SET last_seen = ?, scan_count = ? WHERE id = ?",
                    (now, existing["scan_count"] + 1, existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO scan_targets (target, target_type, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                    (target, target_type, now, now),
                )
            conn.commit()
        finally:
            conn.close()

    def record_found_profiles(self, target: str, results: list[dict[str, Any]]) -> None:
        """Store FOUND profile results."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        found = [row for row in results if str(row.get("status")) == "FOUND"]
        conn = self._connect()
        try:
            for row in found:
                platform = str(row.get("platform", "")).strip()
                url = str(row.get("url", "")).strip()
                confidence = int(row.get("confidence", 0) or 0)
                if not platform:
                    continue
                existing = conn.execute(
                    "SELECT id FROM found_profiles WHERE target = ? AND platform = ?",
                    (target, platform),
                ).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE found_profiles SET last_seen = ?, confidence = ?, profile_url = ? WHERE id = ?",
                        (now, confidence, url, existing["id"]),
                    )
                else:
                    conn.execute(
                        "INSERT INTO found_profiles (target, platform, profile_url, confidence, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
                        (target, platform, url, confidence, now, now),
                    )
            conn.commit()
        finally:
            conn.close()

    def record_contact_signals(
        self,
        target: str,
        signals: dict[str, Any],
        source_platform: str = "",
    ) -> None:
        """Store contact signals (emails, phones, links)."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            for signal_type, values in signals.items():
                if not isinstance(values, list):
                    continue
                for value in values:
                    clean_value = str(value).strip()
                    if not clean_value:
                        continue
                    existing = conn.execute(
                        "SELECT id FROM contact_signals WHERE target = ? AND signal_type = ? AND value = ?",
                        (target, signal_type, clean_value),
                    ).fetchone()
                    if not existing:
                        conn.execute(
                            "INSERT INTO contact_signals (target, signal_type, value, source_platform, first_seen) VALUES (?, ?, ?, ?, ?)",
                            (target, signal_type, clean_value, source_platform, now),
                        )
            conn.commit()
        finally:
            conn.close()

    def record_fingerprint(self, target: str, fingerprint: dict[str, Any]) -> None:
        """Store a master fingerprint."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        fingerprint_id = str(fingerprint.get("fingerprint_id", "")).strip()
        if not fingerprint_id:
            return
        components = fingerprint.get("components", {})
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT id FROM fingerprints WHERE target = ? AND fingerprint_id = ?",
                (target, fingerprint_id),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO fingerprints (target, fingerprint_id, component_json, created_at) VALUES (?, ?, ?, ?)",
                    (target, fingerprint_id, json.dumps(components, default=str), now),
                )
            conn.commit()
        finally:
            conn.close()

    def record_risk_signals(self, target: str, issues: list[dict[str, Any]]) -> None:
        """Store risk/exposure signals from issue list."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            for issue in issues:
                risk_type = str(issue.get("title", "")).strip().lower().replace(" ", "_")
                severity = str(issue.get("severity", "LOW")).upper()
                detail = str(issue.get("evidence", "")).strip()
                if not risk_type:
                    continue
                existing = conn.execute(
                    "SELECT id FROM risk_signals WHERE target = ? AND risk_type = ?",
                    (target, risk_type),
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO risk_signals (target, risk_type, severity, detail, first_seen) VALUES (?, ?, ?, ?, ?)",
                        (target, risk_type, severity, detail, now),
                    )
            conn.commit()
        finally:
            conn.close()

    def get_target_history(self, target: str) -> dict[str, Any]:
        """Retrieve full history for a target from the knowledge base."""
        conn = self._connect()
        try:
            scan_row = conn.execute(
                "SELECT * FROM scan_targets WHERE target = ?",
                (target,),
            ).fetchone()
            profiles = conn.execute(
                "SELECT * FROM found_profiles WHERE target = ? ORDER BY confidence DESC",
                (target,),
            ).fetchall()
            contacts = conn.execute(
                "SELECT * FROM contact_signals WHERE target = ?",
                (target,),
            ).fetchall()
            risks = conn.execute(
                "SELECT * FROM risk_signals WHERE target = ? ORDER BY severity DESC",
                (target,),
            ).fetchall()
            fingerprint = conn.execute(
                "SELECT * FROM fingerprints WHERE target = ? ORDER BY id DESC LIMIT 1",
                (target,),
            ).fetchone()
        finally:
            conn.close()

        return {
            "target": target,
            "scan_count": scan_row["scan_count"] if scan_row else 0,
            "first_seen": scan_row["first_seen"] if scan_row else None,
            "last_seen": scan_row["last_seen"] if scan_row else None,
            "found_profiles": [dict(row) for row in profiles],
            "contact_signals": [dict(row) for row in contacts],
            "risk_signals": [dict(row) for row in risks],
            "fingerprint_id": fingerprint["fingerprint_id"] if fingerprint else None,
            "has_history": scan_row is not None,
        }

    def get_all_targets(self) -> list[dict[str, Any]]:
        """Return all known targets ordered by last seen."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM scan_targets ORDER BY last_seen DESC"
            ).fetchall()
        finally:
            conn.close()
        return [dict(row) for row in rows]

    def search_contact_value(self, value: str) -> list[dict[str, Any]]:
        """Find all targets associated with a contact value (email, phone, etc.)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM contact_signals WHERE value LIKE ?",
                (f"%{value}%",),
            ).fetchall()
        finally:
            conn.close()
        return [dict(row) for row in rows]
