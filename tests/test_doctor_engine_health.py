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

from __future__ import annotations

from core.runner import _build_doctor_snapshot, _build_engine_health_snapshot


def test_build_engine_health_snapshot_returns_dict():
    result = _build_engine_health_snapshot()
    assert isinstance(result, dict)
    assert "conductor_engine" in result


def test_engine_health_conductor_available():
    result = _build_engine_health_snapshot()
    assert result["conductor_engine"]["available"] is True


def test_engine_health_crypto_token_test():
    result = _build_engine_health_snapshot()
    assert result["crypto_engine"]["token_test"] is True


def test_engine_health_pipeline_available():
    result = _build_engine_health_snapshot()
    assert result["pipeline_engine"]["available"] is True


def test_doctor_snapshot_contains_engine_health():
    snapshot = _build_doctor_snapshot()
    assert "engine_health" in snapshot
    assert isinstance(snapshot["engine_health"], dict)
