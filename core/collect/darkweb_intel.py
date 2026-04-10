# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Proprietary
#
# Sylica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Sylica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Sylica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ------------------------------------------------------------------------------

"""Passive dark-web reference collection using public onion references and Tor-aware search."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import quote_plus

import aiohttp

from core.collect.http_resilience import request_text_with_retries


_ONION_RE = re.compile(r"\b[a-z2-7]{16,56}\.onion\b", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}")
_DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[A-Za-z]{2,}\b")


@dataclass(frozen=True)
class DarkwebSignalResult:
    """Summarize passive dark-web references and Tor-aware search results."""

    target: str
    search_terms: tuple[str, ...]
    onion_references: tuple[str, ...]
    ahmia_results: tuple[dict[str, str], ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Render a JSON-safe dark-web signal summary for plugin output and reporting."""

        return {
            "target": self.target,
            "search_terms": list(self.search_terms),
            "onion_references": list(self.onion_references),
            "ahmia_results": list(self.ahmia_results),
            "notes": list(self.notes),
        }


def _search_terms_from_context(context: dict[str, Any]) -> tuple[str, ...]:
    candidates: list[str] = []
    candidates.append(str(context.get("target") or "").strip())
    domain_result = context.get("domain_result")
    if isinstance(domain_result, dict):
        candidates.append(str(domain_result.get("target") or "").strip())
    for row in context.get("results", []) or []:
        if not isinstance(row, dict):
            continue
        candidates.append(str(row.get("platform") or "").strip())
        candidates.append(str(row.get("bio") or "").strip())
        for email in ((row.get("contacts") or {}) if isinstance(row.get("contacts"), dict) else {}).get("emails", []):
            candidates.append(str(email).strip())
        for link_url in row.get("links", []) or []:
            candidates.append(str(link_url).strip())

    previous_plugin_data = context.get("previous_plugin_data")
    if isinstance(previous_plugin_data, dict):
        for payload in previous_plugin_data.values():
            if not isinstance(payload, dict):
                continue
            for onion in payload.get("onion_references", []) or []:
                candidates.append(str(onion).strip())
            for asset in payload.get("assets", []) or []:
                if isinstance(asset, dict):
                    candidates.append(str(asset.get("ocr_text") or "").strip())

    tokens: list[str] = []
    for candidate in candidates:
        for onion in _ONION_RE.findall(candidate):
            tokens.append(onion.lower())
        for email in _EMAIL_RE.findall(candidate):
            tokens.append(email.lower())
        for domain in _DOMAIN_RE.findall(candidate):
            if ".onion" not in domain.lower():
                tokens.append(domain.lower())
    ordered: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
        if len(ordered) >= 8:
            break
    return tuple(ordered)


async def _fetch_ahmia_results(
    session: aiohttp.ClientSession,
    search_term: str,
    *,
    timeout_seconds: int,
    proxy_url: str | None,
) -> list[dict[str, str]]:
    search_url = f"https://ahmia.fi/search/?q={quote_plus(search_term)}"
    response = await request_text_with_retries(
        session,
        method="GET",
        url=search_url,
        timeout_seconds=timeout_seconds,
        proxy_url=proxy_url,
    )
    body = response.body or ""
    matches = []
    for onion in _ONION_RE.findall(body):
        matches.append(
            {
                "search_term": search_term,
                "onion": onion.lower(),
                "source": "ahmia",
                "search_url": search_url,
            }
        )
        if len(matches) >= 6:
            break
    return matches


async def collect_darkweb_signals(
    context: dict[str, Any],
    *,
    timeout_seconds: int = 12,
) -> DarkwebSignalResult:
    """Collect passive onion references and Ahmia search hints in a read-only manner."""

    target = str(context.get("target") or "").strip() or "target"
    proxy_url = str(context.get("proxy_url") or "").strip() or None
    use_tor = bool(context.get("use_tor", False))
    search_terms = _search_terms_from_context(context)
    onion_references = tuple(term for term in search_terms if term.endswith(".onion"))
    notes: list[str] = []

    if not search_terms:
        return DarkwebSignalResult(
            target=target,
            search_terms=(),
            onion_references=(),
            ahmia_results=(),
            notes=("No dark-web search terms or onion references were available in the current investigation context.",),
        )

    connector: aiohttp.BaseConnector | None = None
    if proxy_url and proxy_url.lower().startswith("socks"):
        try:
            from aiohttp_socks import ProxyConnector  # type: ignore
        except Exception:
            notes.append("Tor SOCKS routing was requested, but aiohttp_socks is not installed, so live Ahmia fetches were skipped.")
        else:
            connector = ProxyConnector.from_url(proxy_url)
    else:
        connector = aiohttp.TCPConnector(limit=4, ttl_dns_cache=300)

    ahmia_results: list[dict[str, str]] = []
    if connector is None:
        notes.append("Dark-web collection stayed in passive reference mode because no compatible Tor-aware HTTP connector was available.")
        return DarkwebSignalResult(
            target=target,
            search_terms=search_terms,
            onion_references=onion_references,
            ahmia_results=(),
            notes=tuple(notes),
        )

    async with aiohttp.ClientSession(connector=connector) as session:
        for search_term in search_terms[:4]:
            try:
                ahmia_results.extend(
                    await _fetch_ahmia_results(
                        session,
                        search_term,
                        timeout_seconds=timeout_seconds,
                        proxy_url=None if connector is not None and proxy_url and proxy_url.lower().startswith("socks") else proxy_url,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive network guard
                notes.append(f"Ahmia lookup skipped for {search_term}: {exc}")

    if use_tor and not notes:
        notes.append("Dark-web collection used Tor-aware routing only for public index queries and never attempted exploitation or private-service access.")
    elif not use_tor:
        notes.append("Dark-web collection stayed passive and only queried public Ahmia indexing endpoints.")

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in ahmia_results:
        key = (str(row.get("search_term", "")).lower(), str(row.get("onion", "")).lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    return DarkwebSignalResult(
        target=target,
        search_terms=search_terms,
        onion_references=onion_references,
        ahmia_results=tuple(deduped[:20]),
        notes=tuple(notes),
    )


def collect_darkweb_signals_blocking(
    context: dict[str, Any],
    *,
    timeout_seconds: int = 12,
) -> DarkwebSignalResult:
    """Run passive dark-web reference collection from blocking plugin code."""

    return asyncio.run(collect_darkweb_signals(context, timeout_seconds=timeout_seconds))
