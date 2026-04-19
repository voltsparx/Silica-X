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

from core.engines.engine_base import EngineBase
from core.engines.stabilizer_engine import StabilizerEngine


class _InnerEngine(EngineBase):
    def __init__(self, outcomes):
        super().__init__()
        self.outcomes = list(outcomes)

    async def run(self, tasks, context=None):
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return [outcome]


def _task():
    async def inner():
        return "unused"

    return inner()


def test_stabilizer_retries_on_failure():
    engine = StabilizerEngine(_InnerEngine([RuntimeError("boom"), "ok"]), max_retries=1, base_delay=0)
    result = asyncio.run(engine.run([_task]))
    assert result == ["ok"]


def test_stabilizer_opens_circuit_after_threshold():
    engine = StabilizerEngine(
        _InnerEngine([RuntimeError("boom"), RuntimeError("again")]),
        max_retries=0,
        circuit_threshold=1,
        fallback_value="fallback",
    )
    asyncio.run(engine.run([_task]))
    assert engine._circuit_is_open() is True


def test_stabilizer_reset_closes_circuit():
    engine = StabilizerEngine(
        _InnerEngine([RuntimeError("boom")]),
        max_retries=0,
        circuit_threshold=1,
        fallback_value="fallback",
    )
    asyncio.run(engine.run([_task]))
    engine.reset()
    assert engine._circuit_is_open() is False


def test_stabilizer_returns_fallback_when_circuit_open():
    engine = StabilizerEngine(
        _InnerEngine([RuntimeError("boom")]),
        max_retries=0,
        circuit_threshold=1,
        fallback_value="fallback",
    )
    asyncio.run(engine.run([_task]))
    result = asyncio.run(engine.run([_task, _task]))
    assert result == ["fallback", "fallback"]
