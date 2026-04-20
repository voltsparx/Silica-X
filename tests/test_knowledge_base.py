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

"""Tests for KnowledgeBase persistent storage."""

import os
import tempfile

from core.artifacts.sql_store import KnowledgeBase


def _make_kb() -> tuple[KnowledgeBase, str]:
    tmp = tempfile.mktemp(suffix=".db")
    kb = KnowledgeBase(db_path=tmp)
    return kb, tmp


def test_kb_creates_database_file() -> None:
    kb, path = _make_kb()
    assert isinstance(kb, KnowledgeBase)
    assert os.path.exists(path)
    os.unlink(path)


def test_kb_record_and_retrieve_target() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("testuser", "social_handle")
        history = kb.get_target_history("testuser")
        assert history["has_history"] is True
        assert history["scan_count"] == 1
        assert history["target"] == "testuser"
    finally:
        os.unlink(path)


def test_kb_scan_count_increments() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("testuser", "social_handle")
        kb.record_scan_target("testuser", "social_handle")
        kb.record_scan_target("testuser", "social_handle")
        history = kb.get_target_history("testuser")
        assert history["scan_count"] == 3
    finally:
        os.unlink(path)


def test_kb_record_found_profiles() -> None:
    kb, path = _make_kb()
    try:
        results = [
            {
                "status": "FOUND",
                "platform": "GitHub",
                "url": "https://github.com/u",
                "confidence": 90,
            },
            {
                "status": "NOT_FOUND",
                "platform": "Twitter",
                "url": "",
                "confidence": 0,
            },
        ]
        kb.record_scan_target("testuser", "social_handle")
        kb.record_found_profiles("testuser", results)
        history = kb.get_target_history("testuser")
        assert len(history["found_profiles"]) == 1
        assert history["found_profiles"][0]["platform"] == "GitHub"
    finally:
        os.unlink(path)


def test_kb_record_contact_signals() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("testuser", "social_handle")
        kb.record_contact_signals(
            "testuser",
            {"emails": ["a@b.com", "c@d.com"], "phones": ["+1234567890"]},
        )
        history = kb.get_target_history("testuser")
        assert len(history["contact_signals"]) == 3
    finally:
        os.unlink(path)


def test_kb_no_duplicate_contact_signals() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("testuser", "social_handle")
        kb.record_contact_signals("testuser", {"emails": ["a@b.com"]})
        kb.record_contact_signals("testuser", {"emails": ["a@b.com"]})
        history = kb.get_target_history("testuser")
        assert len(history["contact_signals"]) == 1
    finally:
        os.unlink(path)


def test_kb_record_fingerprint() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("testuser", "social_handle")
        kb.record_fingerprint(
            "testuser",
            {
                "fingerprint_id": "a" * 64,
                "components": {"social": {"platform_count": 3}},
            },
        )
        history = kb.get_target_history("testuser")
        assert history["fingerprint_id"] == "a" * 64
    finally:
        os.unlink(path)


def test_kb_search_contact_value() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("userA", "social_handle")
        kb.record_contact_signals("userA", {"emails": ["shared@example.com"]})
        kb.record_scan_target("userB", "social_handle")
        kb.record_contact_signals("userB", {"emails": ["shared@example.com"]})
        results = kb.search_contact_value("shared@example.com")
        targets = [row["target"] for row in results]
        assert "userA" in targets
        assert "userB" in targets
    finally:
        os.unlink(path)


def test_kb_get_all_targets() -> None:
    kb, path = _make_kb()
    try:
        kb.record_scan_target("target1", "social_handle")
        kb.record_scan_target("target2", "domain")
        all_targets = kb.get_all_targets()
        names = [target["target"] for target in all_targets]
        assert "target1" in names
        assert "target2" in names
    finally:
        os.unlink(path)


def test_kb_unknown_target_returns_no_history() -> None:
    kb, path = _make_kb()
    try:
        history = kb.get_target_history("nobody_was_here_xyz")
        assert history["has_history"] is False
        assert history["scan_count"] == 0
    finally:
        os.unlink(path)
