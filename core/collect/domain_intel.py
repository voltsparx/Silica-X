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

"""Domain surface intelligence collection helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import socket
from typing import Any
from urllib.parse import quote, urlsplit

import aiohttp

from core.collect.extractor import filter_valid_hostnames
from core.foundation.recon_modes import normalize_recon_mode
from core.foundation.surface_wordlists import build_surface_wordlist_guidance


DEFAULT_TIMEOUT_SECONDS = 20
_MAX_BODY_BYTES = 140_000


@dataclass(frozen=True)
class HttpArtifact:
    status: int | None
    final_url: str
    headers: dict[str, str]
    body: str
    error: str | None
    redirects_to_https: bool = False


def normalize_domain(raw: str | None) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""

    lowered = value.lower()
    if "//" not in lowered:
        lowered = f"http://{lowered}"

    parsed = urlsplit(lowered)
    host = parsed.hostname or ""
    return host.strip(".")


async def _resolve_addresses(domain: str, timeout_seconds: int) -> list[str]:
    if not domain:
        return []
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.getaddrinfo(domain, None, type=socket.SOCK_STREAM),
            timeout=max(1, int(timeout_seconds)),
        )
    except Exception:
        return []

    addresses = {info[4][0] for info in infos if info and info[4]}
    return sorted(addresses)


async def _http_probe(
    session: aiohttp.ClientSession,
    url: str,
    timeout_seconds: int,
) -> HttpArtifact:
    timeout = aiohttp.ClientTimeout(total=max(1, int(timeout_seconds)))

    async def _request(method: str, *, max_bytes: int) -> HttpArtifact:
        async with session.request(method, url, timeout=timeout, allow_redirects=True) as response:
            if method.upper() == "HEAD":
                body = ""
            else:
                raw = await response.content.read(max_bytes)
                body = raw.decode("utf-8", errors="ignore")
            return HttpArtifact(
                status=response.status,
                final_url=str(response.url),
                headers={key: value for key, value in response.headers.items()},
                body=body,
                error=None,
                redirects_to_https=str(response.url).startswith("https://"),
            )

    try:
        head_result = await _request("HEAD", max_bytes=0)
        if head_result.status in {405, 501}:
            return await _request("GET", max_bytes=min(8000, _MAX_BODY_BYTES))
        return head_result
    except asyncio.TimeoutError:
        return HttpArtifact(status=None, final_url=url, headers={}, body="", error="Timeout")
    except aiohttp.ClientError as exc:
        return HttpArtifact(status=None, final_url=url, headers={}, body="", error=f"Network error: {exc}")
    except Exception as exc:  # pragma: no cover
        return HttpArtifact(status=None, final_url=url, headers={}, body="", error=str(exc))


async def _load_ct_subdomains(
    session: aiohttp.ClientSession,
    domain: str,
    timeout_seconds: int,
    max_subdomains: int,
) -> tuple[list[str], str | None]:
    if not domain:
        return [], "missing domain"

    url = f"https://crt.sh/?q=%25.{quote(domain)}&output=json"
    timeout = aiohttp.ClientTimeout(total=max(1, int(timeout_seconds)))
    try:
        async with session.get(url, timeout=timeout) as response:
            raw = await response.content.read(2_000_000)
            payload = json.loads(raw.decode("utf-8", errors="ignore"))
    except asyncio.TimeoutError:
        return [], "ct timeout"
    except Exception as exc:
        return [], f"ct error: {exc}"

    names: set[str] = set()
    if isinstance(payload, list):
        for row in payload:
            name_value = row.get("name_value") if isinstance(row, dict) else None
            if not name_value:
                continue
            for entry in str(name_value).split("\n"):
                entry = entry.strip().lower()
                if entry and entry.endswith(f".{domain}"):
                    names.add(entry)
                if len(names) >= max_subdomains:
                    break
            if len(names) >= max_subdomains:
                break

    return filter_valid_hostnames(sorted(names), base_domain=domain)[:max_subdomains], None


async def _load_rdap(
    session: aiohttp.ClientSession,
    domain: str,
    timeout_seconds: int,
) -> tuple[dict[str, Any], str | None]:
    if not domain:
        return {}, "missing domain"

    url = f"https://rdap.org/domain/{quote(domain)}"
    timeout = aiohttp.ClientTimeout(total=max(1, int(timeout_seconds)))
    try:
        async with session.get(url, timeout=timeout) as response:
            raw = await response.content.read(500_000)
            payload = json.loads(raw.decode("utf-8", errors="ignore"))
    except asyncio.TimeoutError:
        return {}, "rdap timeout"
    except Exception as exc:
        return {}, f"rdap error: {exc}"

    return payload if isinstance(payload, dict) else {}, None


async def _fetch_small_text(
    session: aiohttp.ClientSession,
    url: str,
    timeout_seconds: int,
) -> tuple[bool, str]:
    timeout = aiohttp.ClientTimeout(total=max(1, int(timeout_seconds)))
    try:
        async with session.get(url, timeout=timeout, allow_redirects=True) as response:
            raw = await response.content.read(4000)
            body = raw.decode("utf-8", errors="ignore").strip()
            if response.status and response.status < 400:
                return True, body
            return False, body
    except Exception:
        return False, ""


def _http_artifact_payload(artifact: HttpArtifact) -> dict[str, Any]:
    return {
        "status": artifact.status,
        "final_url": artifact.final_url,
        "headers": artifact.headers,
        "error": artifact.error,
        "redirects_to_https": artifact.redirects_to_https,
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _note_if_error(notes: list[str], label: str, error: str | None) -> None:
    if error:
        notes.append(f"{label}: {error}")


def _string_list(value: object) -> list[str]:
    """Normalize a loose JSON-like collection into a list of strings."""

    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return []


def _collector_row(*, lane: str, enabled: bool, status: str, detail: str = "") -> dict[str, str]:
    return {
        "lane": lane,
        "status": status if enabled else "skipped",
        "detail": detail if enabled else "disabled by recon mode",
    }


def _normalize_rdap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    normalized = dict(payload)
    if "name_servers" not in normalized:
        raw_nameservers = payload.get("nameservers", [])
        values: list[str] = []
        if isinstance(raw_nameservers, list):
            for row in raw_nameservers:
                if isinstance(row, dict):
                    token = str(row.get("ldhName", "")).strip().lower()
                else:
                    token = str(row).strip().lower()
                if token:
                    values.append(token)
        normalized["name_servers"] = sorted(set(values))

    if "statuses" not in normalized:
        raw_status = payload.get("status", [])
        if isinstance(raw_status, list):
            normalized["statuses"] = [str(item).strip().lower() for item in raw_status if str(item).strip()]
        else:
            normalized["statuses"] = []

    return normalized


async def scan_domain_surface(
    *,
    domain: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    include_ct: bool = False,
    include_rdap: bool = False,
    max_subdomains: int = 250,
    recon_mode: str = "hybrid",
) -> dict[str, Any]:
    normalized_domain = normalize_domain(domain)
    if not normalized_domain:
        return {}

    timeout_seconds = max(5, int(timeout_seconds))
    max_subdomains = max(0, int(max_subdomains))
    normalized_recon_mode = normalize_recon_mode(recon_mode)
    passive_enabled = normalized_recon_mode in {"passive", "hybrid"}
    active_enabled = normalized_recon_mode in {"active", "hybrid"}
    collector_status: dict[str, dict[str, str]] = {}

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        resolve_task = (
            asyncio.create_task(_resolve_addresses(normalized_domain, timeout_seconds))
            if active_enabled
            else None
        )
        https_task = (
            asyncio.create_task(_http_probe(session, f"https://{normalized_domain}", timeout_seconds))
            if active_enabled
            else None
        )
        http_task = (
            asyncio.create_task(_http_probe(session, f"http://{normalized_domain}", timeout_seconds))
            if active_enabled
            else None
        )

        ct_task = (
            asyncio.create_task(_load_ct_subdomains(session, normalized_domain, timeout_seconds, max_subdomains))
            if include_ct and passive_enabled
            else None
        )
        rdap_task = (
            asyncio.create_task(_load_rdap(session, normalized_domain, timeout_seconds))
            if include_rdap and passive_enabled
            else None
        )

        resolved_addresses = await resolve_task if resolve_task is not None else []
        if https_task is not None and http_task is not None:
            https_artifact, http_artifact = await asyncio.gather(https_task, http_task)
        else:
            https_artifact = HttpArtifact(
                status=None,
                final_url=f"https://{normalized_domain}",
                headers={},
                body="",
                error="skipped (passive recon mode)",
            )
            http_artifact = HttpArtifact(
                status=None,
                final_url=f"http://{normalized_domain}",
                headers={},
                body="",
                error="skipped (passive recon mode)",
            )

        subdomains: list[str] = []
        rdap_payload: dict[str, Any] = {}
        scan_notes: list[str] = []

        if ct_task:
            ct_payload, ct_error = await ct_task
            subdomains = ct_payload
            _note_if_error(scan_notes, "ct", ct_error)
            collector_status["ct"] = _collector_row(
                lane="passive",
                enabled=True,
                status="error" if ct_error else "ok",
                detail=ct_error or f"subdomains={len(ct_payload)}",
            )
        elif include_ct:
            collector_status["ct"] = _collector_row(lane="passive", enabled=False, status="skipped")
        else:
            collector_status["ct"] = _collector_row(
                lane="passive",
                enabled=True,
                status="disabled",
                detail="ct lookup disabled",
            )
        if rdap_task:
            rdap_payload, rdap_error = await rdap_task
            _note_if_error(scan_notes, "rdap", rdap_error)
            rdap_payload = _normalize_rdap_payload(rdap_payload)
            collector_status["rdap"] = _collector_row(
                lane="passive",
                enabled=True,
                status="error" if rdap_error else "ok",
                detail=rdap_error or f"nameservers={len(rdap_payload.get('name_servers', []))}",
            )
        elif include_rdap:
            collector_status["rdap"] = _collector_row(lane="passive", enabled=False, status="skipped")
        else:
            collector_status["rdap"] = _collector_row(
                lane="passive",
                enabled=True,
                status="disabled",
                detail="rdap lookup disabled",
            )
        wordlist_guidance = build_surface_wordlist_guidance(subdomains)
        matched_priority_labels = _string_list(wordlist_guidance.get("matched_priority_labels", []))
        if matched_priority_labels:
            scan_notes.append(
                "surface priority labels observed: " + ", ".join(matched_priority_labels[:12])
            )

        robots_present = False
        security_present = False
        robots_preview = ""
        security_preview = ""

        if active_enabled:
            preferred_scheme = "https" if https_artifact.status and https_artifact.status < 400 else "http"
            robots_url = f"{preferred_scheme}://{normalized_domain}/robots.txt"
            security_url = f"{preferred_scheme}://{normalized_domain}/.well-known/security.txt"

            robots_task = asyncio.create_task(
                _fetch_small_text(session, robots_url, min(8, timeout_seconds))
            )
            security_task = asyncio.create_task(
                _fetch_small_text(session, security_url, min(8, timeout_seconds))
            )
            (robots_present, robots_preview), (security_present, security_preview) = await asyncio.gather(
                robots_task,
                security_task,
            )

        collector_status["dns"] = _collector_row(
            lane="active",
            enabled=active_enabled,
            status="ok" if active_enabled else "skipped",
            detail=f"addresses={len(resolved_addresses)}" if active_enabled else "",
        )
        collector_status["https"] = _collector_row(
            lane="active",
            enabled=active_enabled,
            status="ok" if active_enabled and not https_artifact.error else "error" if active_enabled else "skipped",
            detail=https_artifact.error or f"status={https_artifact.status}",
        )
        collector_status["http"] = _collector_row(
            lane="active",
            enabled=active_enabled,
            status="ok" if active_enabled and not http_artifact.error else "error" if active_enabled else "skipped",
            detail=http_artifact.error or f"status={http_artifact.status}",
        )
        collector_status["robots"] = _collector_row(
            lane="active",
            enabled=active_enabled,
            status="ok" if robots_present else "missing" if active_enabled else "skipped",
            detail="robots.txt present" if robots_present else "robots.txt not observed" if active_enabled else "",
        )
        collector_status["security_txt"] = _collector_row(
            lane="active",
            enabled=active_enabled,
            status="ok" if security_present else "missing" if active_enabled else "skipped",
            detail="security.txt present" if security_present else "security.txt not observed" if active_enabled else "",
        )

    return {
        "target": normalized_domain,
        "recon_mode": normalized_recon_mode,
        "resolved_addresses": resolved_addresses,
        "https": _http_artifact_payload(https_artifact),
        "http": _http_artifact_payload(http_artifact),
        "subdomains": subdomains,
        "prioritized_subdomains": _string_list(wordlist_guidance.get("prioritized_subdomains", [])),
        "surface_wordlists": wordlist_guidance,
        "rdap": rdap_payload,
        "collector_status": collector_status,
        "scan_notes": scan_notes,
        "robots_txt_present": robots_present,
        "security_txt_present": security_present,
        "robots_preview": robots_preview[:400],
        "security_preview": security_preview[:400],
    }
