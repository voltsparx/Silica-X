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

"""Smoke tests for CLI command handlers without network calls."""

from core.runner import (
    RunnerState,
    _build_doctor_snapshot,
    _build_engine_health_snapshot,
    build_prompt_parser,
    build_root_parser,
)


def test_doctor_snapshot_has_required_keys():
    snapshot = _build_doctor_snapshot()
    for key in [
        "silica_x",
        "runtime_inventory",
        "ocr_tooling",
        "tor",
        "engine_health",
        "warnings",
        "errors",
        "summary",
    ]:
        assert key in snapshot, f"Missing key: {key}"


def test_doctor_snapshot_engine_health_has_conductor():
    snapshot = _build_doctor_snapshot()
    assert "conductor_engine" in snapshot["engine_health"]
    assert snapshot["engine_health"]["conductor_engine"]["available"] is True


def test_doctor_snapshot_engine_health_has_pipeline():
    snapshot = _build_doctor_snapshot()
    assert "pipeline_engine" in snapshot["engine_health"]
    assert snapshot["engine_health"]["pipeline_engine"]["available"] is True


def test_doctor_snapshot_engine_health_has_crypto():
    snapshot = _build_doctor_snapshot()
    assert "crypto_engine" in snapshot["engine_health"]
    assert snapshot["engine_health"]["crypto_engine"]["available"] is True


def test_root_parser_builds_without_error():
    parser = build_root_parser()
    assert parser is not None


def test_prompt_parser_builds_without_error():
    parser = build_prompt_parser()
    assert parser is not None


def test_runner_state_defaults():
    state = RunnerState()
    assert state.use_tor is False
    assert state.use_proxy is False


def test_engine_health_snapshot_keys():
    health = _build_engine_health_snapshot()
    for key in [
        "conductor_engine",
        "crypto_engine",
        "recon_engine",
        "pipeline_engine",
        "pre_sim",
        "fingerprint_collector",
    ]:
        assert key in health, f"Missing engine health key: {key}"
