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

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any

from core.engines.engine_base import EngineBase
from core.engines.engine_result import EngineResult
from core.engines.health_monitor import EngineHealthMonitor


class ReconScope(str, Enum):
    PORT_SURFACE = "port_surface"
    SUBDOMAIN = "subdomain"
    DOMAIN_INTEL = "domain_intel"
    SOURCE_FUSION = "source_fusion"
    OCR = "ocr"
    MEDIA = "media"
    OSINT_HUNT = "osint_hunt"


@dataclass
class ReconTask:
    scope: ReconScope
    target: str
    options: dict = field(default_factory=dict)


@dataclass
class ReconResult:
    scope: ReconScope
    target: str
    success: bool
    data: dict
    error: str = ""
    execution_time: float = 0.0


class ReconEngine(EngineBase):
    """Routes recon tasks to appropriate collect-layer modules."""

    async def run(self, tasks, context=None) -> list[Any]:
        import asyncio

        recon_tasks = [t() if callable(t) else t for t in tasks]
        coros = [self._dispatch(rt, context=context or {}) for rt in recon_tasks]
        return list(await asyncio.gather(*coros, return_exceptions=True))

    async def run_recon(
        self,
        recon_tasks: list[ReconTask],
        context: dict | None = None,
    ) -> list[ReconResult]:
        """Primary API: submit ReconTask list, get ReconResult list."""

        results = []
        for rt in recon_tasks:
            start = perf_counter()
            try:
                data = await self._dispatch(rt, context=context or {})
                results.append(
                    ReconResult(
                        scope=rt.scope,
                        target=rt.target,
                        success=True,
                        data=data,
                        execution_time=perf_counter() - start,
                    )
                )
            except Exception as exc:
                results.append(
                    ReconResult(
                        scope=rt.scope,
                        target=rt.target,
                        success=False,
                        data={},
                        error=str(exc),
                        execution_time=perf_counter() - start,
                    )
                )
        return results

    async def _dispatch(self, rt: ReconTask, context: dict) -> dict:
        import asyncio
        import importlib

        timeout = int(rt.options.get("timeout", context.get("timeout", 60)))
        if rt.scope == ReconScope.PORT_SURFACE:
            from core.collect.port_surface_probe import run_surface_port_probe

            profiles = rt.options.get("profiles", ["connect_sweep", "top_100_ports"])
            return await run_surface_port_probe(rt.target, profiles, timeout)
        if rt.scope == ReconScope.SUBDOMAIN:
            from core.collect.subdomain_harvest import harvest_subdomains

            mode = rt.options.get("mode", "passive")
            wordlist = rt.options.get("wordlist_path")
            return await harvest_subdomains(rt.target, mode=mode, timeout=timeout, wordlist_path=wordlist)
        if rt.scope == ReconScope.DOMAIN_INTEL:
            from core.collect.domain_intel import scan_domain_surface

            return await scan_domain_surface(
                domain=rt.target,
                timeout_seconds=timeout,
                include_ct=rt.options.get("include_ct", True),
                include_rdap=rt.options.get("include_rdap", True),
                max_subdomains=rt.options.get("max_subdomains", 50),
                recon_mode=rt.options.get("recon_mode", "hybrid"),
            )
        if rt.scope == ReconScope.SOURCE_FUSION:
            try:
                source_fusion = importlib.import_module("core.collect.source_fusion")
                run_source_fusion = getattr(source_fusion, "run_source_fusion")
                return await run_source_fusion(rt.target, options=rt.options)
            except (ImportError, AttributeError):
                return {"error": "source_fusion module unavailable", "success": False}
        if rt.scope == ReconScope.OCR:
            try:
                ocr_pipeline = importlib.import_module("core.collect.ocr_pipeline")
                run_ocr_pipeline = getattr(ocr_pipeline, "run_ocr_pipeline")
            except (ImportError, AttributeError):
                run_ocr_pipeline = None
            if callable(run_ocr_pipeline) and rt.options.get("image_bytes") is not None:
                return await asyncio.to_thread(
                    run_ocr_pipeline,
                    rt.options.get("image_bytes", b""),
                    preprocess_intensity=rt.options.get("preprocess_mode", "balanced"),
                )
            try:
                from core.collect.ocr_image_scan import collect_ocr_image_scan

                scan_result = await collect_ocr_image_scan(
                    paths=rt.options.get("paths", []),
                    urls=rt.options.get("urls", []),
                    preprocess_mode=rt.options.get("preprocess_mode", "balanced"),
                    timeout_seconds=timeout,
                    proxy_url=rt.options.get("proxy_url"),
                )
                return scan_result.as_dict()
            except Exception:
                return {"error": "ocr_pipeline module unavailable", "success": False}
        if rt.scope == ReconScope.MEDIA:
            try:
                from core.collect.public_media_recon import analyze_public_media

                return await analyze_public_media(rt.target, options=rt.options)
            except (ImportError, AttributeError):
                return {"error": "public_media_recon module unavailable", "success": False}
        if rt.scope == ReconScope.OSINT_HUNT:
            try:
                from core.collect.domain_recon import run_domain_recon

                return await run_domain_recon(rt.target, options=rt.options)
            except (ImportError, AttributeError):
                return {"error": "domain_recon module unavailable", "success": False}
        return {"error": f"Unknown scope: {rt.scope}", "success": False}


__all__ = [
    "EngineBase",
    "EngineResult",
    "EngineHealthMonitor",
    "ReconEngine",
    "ReconResult",
    "ReconScope",
    "ReconTask",
]
