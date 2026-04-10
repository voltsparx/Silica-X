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

"""Controlled link-intelligence collection for read-only public URL analysis."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp

from core.collect.extractor import extract_bio, extract_contacts, extract_links
from core.collect.http_resilience import request_text_with_retries


_URL_TEXT_RE = re.compile(r"https?://[^\s<>'\"]+")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_DESCRIPTION_RE = re.compile(
    r"<meta[^>]+(?:name|property)=['\"](?:description|og:description)['\"][^>]+content=['\"](.*?)['\"]",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class LinkObservation:
    """Describe what a read-only follow-up fetch observed about one public URL."""

    url: str
    final_url: str
    classification: str
    depth: int
    status_code: int | None
    title: str
    description: str
    related_links: tuple[str, ...]
    contacts: dict[str, list[str]]
    bio_excerpt: str

    def as_dict(self) -> dict[str, Any]:
        """Render a JSON-safe observation for plugin and report payloads."""

        return {
            "url": self.url,
            "final_url": self.final_url,
            "classification": self.classification,
            "depth": self.depth,
            "status_code": self.status_code,
            "title": self.title,
            "description": self.description,
            "related_links": list(self.related_links),
            "contacts": {
                "emails": list(self.contacts.get("emails", [])),
                "phones": list(self.contacts.get("phones", [])),
            },
            "bio_excerpt": self.bio_excerpt,
        }


@dataclass(frozen=True)
class LinkExplorationResult:
    """Summarize controlled recursive link exploration from public profile/entity URLs."""

    target: str
    seed_links: tuple[str, ...]
    observations: tuple[LinkObservation, ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Render a JSON-safe result payload for plugin output and reporting."""

        return {
            "target": self.target,
            "seed_links": list(self.seed_links),
            "observations": [item.as_dict() for item in self.observations],
            "notes": list(self.notes),
        }


def _clean_text(value: str, *, limit: int = 240) -> str:
    token = re.sub(r"\s+", " ", str(value or "")).strip()
    return token[:limit]


def _classify_link(link_url: str) -> str:
    parsed = urlparse(link_url)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()
    if host.endswith(".onion"):
        return "darkweb_onion"
    if any(marker in host for marker in ("github.com", "gitlab.com", "bitbucket.org")):
        return "repository"
    if any(path.endswith(suffix) for suffix in (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")):
        return "document"
    if any(marker in host for marker in ("x.com", "twitter.com", "linkedin.com", "instagram.com", "facebook.com")):
        return "social"
    return "web"


def _extract_seed_links(profile_results: list[dict[str, Any]], *, target: str) -> tuple[str, ...]:
    candidate_links: list[str] = []
    for row in profile_results:
        if not isinstance(row, dict):
            continue
        for link_url in row.get("links", []) or []:
            token = str(link_url).strip()
            if token.startswith(("http://", "https://")):
                candidate_links.append(token)
        profile_url = str(row.get("url") or "").strip()
        if profile_url.startswith(("http://", "https://")):
            candidate_links.append(profile_url)
        bio = str(row.get("bio") or "")
        candidate_links.extend(_URL_TEXT_RE.findall(bio))

    ordered: list[str] = []
    seen: set[str] = set()
    for link_url in candidate_links:
        normalized = str(link_url).strip()
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(normalized)
        if len(ordered) >= 16:
            break
    if not ordered and str(target).startswith(("http://", "https://")):
        return (str(target),)
    return tuple(ordered)


async def _fetch_link_observation(
    session: aiohttp.ClientSession,
    link_url: str,
    *,
    timeout_seconds: int,
    proxy_url: str | None,
    depth: int,
) -> LinkObservation:
    response = await request_text_with_retries(
        session,
        method="GET",
        url=link_url,
        timeout_seconds=timeout_seconds,
        proxy_url=proxy_url,
        allow_redirects=True,
    )
    body = response.body or ""
    title_match = _TITLE_RE.search(body)
    description_match = _DESCRIPTION_RE.search(body)
    title = _clean_text(title_match.group(1) if title_match else "")
    description = _clean_text(description_match.group(1) if description_match else "")
    related_links = tuple(extract_links(body)[:8])
    contacts = extract_contacts(body)
    bio_excerpt = _clean_text(extract_bio(body) or "", limit=180)
    return LinkObservation(
        url=link_url,
        final_url=response.response_url or link_url,
        classification=_classify_link(link_url),
        depth=depth,
        status_code=response.status_code,
        title=title,
        description=description,
        related_links=related_links,
        contacts={
            "emails": list(contacts.get("emails", [])),
            "phones": list(contacts.get("phones", [])),
        },
        bio_excerpt=bio_excerpt,
    )


async def collect_link_exploration(
    profile_results: list[dict[str, Any]],
    *,
    target: str,
    timeout_seconds: int = 10,
    proxy_url: str | None = None,
    max_depth: int = 1,
    max_seed_links: int = 8,
) -> LinkExplorationResult:
    """Collect read-only intelligence from public links found in profile/entity bios."""

    seed_links = _extract_seed_links(profile_results, target=target)[: max(1, int(max_seed_links))]
    if not seed_links:
        return LinkExplorationResult(
            target=str(target),
            seed_links=(),
            observations=(),
            notes=("No public bio/entity links were available for controlled follow-up.",),
        )

    connector = aiohttp.TCPConnector(limit=6, ttl_dns_cache=300)
    observations: list[LinkObservation] = []
    notes: list[str] = []
    visited: set[str] = set()
    frontier: list[tuple[str, int]] = [(link_url, 0) for link_url in seed_links]

    async with aiohttp.ClientSession(connector=connector) as session:
        while frontier:
            link_url, depth = frontier.pop(0)
            lowered = link_url.lower()
            if lowered in visited:
                continue
            visited.add(lowered)
            try:
                observation = await _fetch_link_observation(
                    session,
                    link_url,
                    timeout_seconds=timeout_seconds,
                    proxy_url=proxy_url,
                    depth=depth,
                )
                observations.append(observation)
                if depth >= max_depth:
                    continue
                base_host = urlparse(observation.final_url or observation.url).netloc.lower()
                follow_ups = []
                for related in observation.related_links:
                    resolved = urljoin(observation.final_url or observation.url, related)
                    related_host = urlparse(resolved).netloc.lower()
                    if not related_host or related_host != base_host:
                        continue
                    follow_ups.append(resolved)
                for resolved in follow_ups[:3]:
                    if resolved.lower() not in visited:
                        frontier.append((resolved, depth + 1))
            except Exception as exc:  # pragma: no cover - defensive collection guard
                notes.append(f"Link follow-up skipped for {link_url}: {exc}")

    if observations and max_depth > 0:
        notes.append("Controlled same-host link expansion stayed within one public recursion lane.")

    return LinkExplorationResult(
        target=str(target),
        seed_links=tuple(seed_links),
        observations=tuple(observations[:24]),
        notes=tuple(notes),
    )


def collect_link_exploration_blocking(
    profile_results: list[dict[str, Any]],
    *,
    target: str,
    timeout_seconds: int = 10,
    proxy_url: str | None = None,
    max_depth: int = 1,
    max_seed_links: int = 8,
) -> LinkExplorationResult:
    """Run controlled link exploration from blocking plugin code in a read-only manner."""

    return asyncio.run(
        collect_link_exploration(
            profile_results,
            target=target,
            timeout_seconds=timeout_seconds,
            proxy_url=proxy_url,
            max_depth=max_depth,
            max_seed_links=max_seed_links,
        )
    )
