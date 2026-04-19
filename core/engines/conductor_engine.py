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

from __future__ import annotations

from typing import Any


class ConductorEngine:
    """Master engine conductor for Silica-X."""

    def __init__(self) -> None:
        from core.engines.async_engine import AsyncEngine
        from core.engines.sync_engine import SyncEngine
        from core.engines.stabilizer_engine import StabilizerEngine
        from core.engines.crypto_engine import CryptoEngine
        from core.engines.recon_engine import ReconEngine

        self.async_engine = AsyncEngine()
        self.sync_engine = SyncEngine()
        self.stabilizer = StabilizerEngine(inner=self.async_engine)
        self.crypto_engine = CryptoEngine()
        self.recon_engine = ReconEngine()

    async def run(self, tasks, context=None) -> list:
        """Route tasks to the correct sub-engine based on _silica_x_engine tag."""

        task_list = list(tasks)
        buckets: dict[str, list[tuple[int, Any]]] = {
            "crypto": [],
            "recon": [],
            "sync": [],
            "stable": [],
            "async": [],
        }
        for i, task in enumerate(task_list):
            tag = str(getattr(task, "_silica_x_engine", "async")).lower()
            bucket = tag if tag in buckets else "async"
            buckets[bucket].append((i, task))

        results_map: dict[int, Any] = {}
        engine_map = {
            "crypto": self.crypto_engine,
            "recon": self.recon_engine,
            "sync": self.sync_engine,
            "stable": self.stabilizer,
            "async": self.async_engine,
        }
        for bucket_name, bucket_tasks in buckets.items():
            if not bucket_tasks:
                continue
            indices, raw_tasks = zip(*bucket_tasks)
            engine = engine_map[bucket_name]
            bucket_results = await engine.run(list(raw_tasks), context=context)
            for original_index, result in zip(indices, bucket_results):
                results_map[original_index] = result

        return [results_map[i] for i in range(len(task_list))]

    async def run_recon(self, recon_tasks, context=None):
        """Direct access to recon engine's run_recon."""

        return await self.recon_engine.run_recon(recon_tasks, context=context)

    def fingerprint(self, obj) -> str:
        """Direct access to crypto engine's fingerprint."""

        return self.crypto_engine.fingerprint(obj)

    def hash_data(self, data: str) -> str:
        return self.crypto_engine.hash_data(data)


__all__ = ["ConductorEngine"]
