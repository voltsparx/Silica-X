# ──────────────────────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────────────────────

import asyncio
from unittest.mock import AsyncMock

from core.engines.conductor_engine import ConductorEngine
from core.engines.recon_engine import ReconResult, ReconScope, ReconTask


def test_conductor_routes_to_async_by_default():
    async def task():
        return "async"

    result = asyncio.run(ConductorEngine().run([task]))
    assert result == ["async"]


def test_conductor_routes_tagged_sync_task():
    def task():
        return "sync"

    task._silica_x_engine = "sync"
    result = asyncio.run(ConductorEngine().run([task]))
    assert result == ["sync"]


def test_conductor_routes_tagged_crypto_task():
    def task():
        return "crypto"

    task._silica_x_engine = "crypto"
    result = asyncio.run(ConductorEngine().run([task]))
    assert result == ["crypto"]


def test_conductor_fingerprint_returns_hex_string():
    fingerprint = ConductorEngine().fingerprint({"target": "alice"})
    assert isinstance(fingerprint, str)
    assert len(fingerprint) == 64
    int(fingerprint, 16)


def test_conductor_run_recon_returns_recon_results():
    conductor = ConductorEngine()
    conductor.recon_engine.run_recon = AsyncMock(
        return_value=[
            ReconResult(
                scope=ReconScope.PORT_SURFACE,
                target="example.com",
                success=True,
                data={"success": True},
            )
        ]
    )
    rows = asyncio.run(
        conductor.run_recon([ReconTask(scope=ReconScope.PORT_SURFACE, target="example.com")])
    )
    assert rows[0].scope == ReconScope.PORT_SURFACE
    assert rows[0].success is True
