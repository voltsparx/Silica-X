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

import re
from typing import Any
from urllib.parse import urlparse

import aiohttp

from core.collect.extractor import (
    filter_valid_emails,
    filter_valid_hostnames,
    filter_valid_phones,
)
from core.collect.scanner import scan_username

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s().]{6,}\d)")
_URL_RE = re.compile(r"https?://[^\s<>'\"]+")
_MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9_.\-]{2,32})")
_SOCIAL_RE = re.compile(r"https?://(?:www\.)?(?:x\.com|twitter\.com|facebook\.com|instagram\.com|linkedin\.com|github\.com)/[^\s<>'\"]+")
_API_KEY_RE = re.compile(
    r"(?:\bsk-[A-Za-z0-9]{16,}\b|\bpk-[A-Za-z0-9]{16,}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|"
    r"\btoken=[A-Za-z0-9._\-]{12,}\b|\bapi_key=[A-Za-z0-9._\-]{12,}\b)",
    re.IGNORECASE,
)
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\b")
_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/]{64,}={0,2}\b")
_SSH_RE = re.compile(r"\bssh-(?:rsa|ed25519|dss)\s+[A-Za-z0-9+/=]+\b")
_PGP_RE = re.compile(r"-----BEGIN PGP (?:PUBLIC KEY BLOCK|PRIVATE KEY BLOCK|MESSAGE)-----")


def _dedupe(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = str(value or "").strip()
        if not token:
            continue
        lowered = token.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(token)
    return ordered


def hunt_credential_signals(text_blob: str) -> dict[str, Any]:
    """Pure text analysis function."""

    body = str(text_blob or "")
    api_keys = _dedupe(_API_KEY_RE.findall(body))
    base64_blobs = _dedupe(_BASE64_RE.findall(body))
    return {
        "emails": filter_valid_emails(_EMAIL_RE.findall(body)),
        "phones": filter_valid_phones(_PHONE_RE.findall(body)),
        "api_keys": api_keys,
        "pgp_blocks": _dedupe(_PGP_RE.findall(body)),
        "ssh_public_keys": _dedupe(_SSH_RE.findall(body)),
        "jwts": _dedupe(_JWT_RE.findall(body)),
        "base64_blobs": base64_blobs,
        "success": True,
        "error": "",
    }


async def hunt_contact_surface(
    domain: str,
    proxy_url: str | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    """Scrape common contact-exposing paths on a domain."""

    paths = [
        "/contact",
        "/about",
        "/team",
        "/humans.txt",
        "/security.txt",
        "/.well-known/security.txt",
        "/robots.txt",
        "/sitemap.xml",
    ]
    findings: list[dict[str, str]] = []
    names: list[str] = []
    social_links: list[str] = []
    try:
        request_kwargs: dict[str, Any] = {
            "timeout": aiohttp.ClientTimeout(total=max(1, int(timeout))),
            "allow_redirects": True,
        }
        if proxy_url:
            request_kwargs["proxy"] = proxy_url
        async with aiohttp.ClientSession() as session:
            for path in paths:
                try:
                    async with session.get(f"https://{domain}{path}", **request_kwargs) as response:
                        text = await response.text(errors="replace")
                except Exception:
                    try:
                        async with session.get(f"http://{domain}{path}", **request_kwargs) as response:
                            text = await response.text(errors="replace")
                    except Exception:
                        continue
                signals = hunt_credential_signals(text)
                for email in signals.get("emails", []):
                    findings.append({"path": path, "signal_type": "email", "value": email})
                for phone in signals.get("phones", []):
                    findings.append({"path": path, "signal_type": "phone", "value": phone})
                for api_key in signals.get("api_keys", []):
                    findings.append({"path": path, "signal_type": "api_key", "value": api_key})
                for link in _SOCIAL_RE.findall(text):
                    social_links.append(link)
                    findings.append({"path": path, "signal_type": "social_link", "value": link})
                names.extend(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", text))
        return {
            "domain": domain,
            "findings": findings,
            "emails": filter_valid_emails([row["value"] for row in findings if row["signal_type"] == "email"]),
            "phones": filter_valid_phones([row["value"] for row in findings if row["signal_type"] == "phone"]),
            "names": _dedupe(names),
            "social_links": _dedupe(social_links),
            "success": True,
            "error": "",
        }
    except Exception as exc:
        return {
            "domain": domain,
            "findings": [],
            "emails": [],
            "phones": [],
            "names": [],
            "social_links": [],
            "success": False,
            "error": str(exc),
        }


async def hunt_username_signals(
    username: str,
    proxy_url: str | None = None,
    timeout: int = 20,
    max_concurrency: int = 15,
) -> dict[str, Any]:
    """Runs scan_username and surfaces contact + credential-adjacent signals."""

    try:
        results = await scan_username(
            username=username,
            proxy_url=proxy_url,
            timeout_seconds=timeout,
            max_concurrency=max_concurrency,
        )
        found = [row for row in results if str(row.get("status")) == "FOUND"]
        bios = [str(row.get("bio") or "") for row in found]
        links: list[str] = []
        mentions: list[str] = []
        profile_images: list[str] = []
        credential_hits: list[dict[str, Any]] = []
        external_links: list[str] = []
        emails: list[str] = []
        phones: list[str] = []
        for row in found:
            for link in (row.get("links") or []):
                links.append(str(link))
            for mention in (row.get("mentions") or []):
                mentions.append(str(mention))
            avatar = str(row.get("avatar_url") or row.get("image_url") or "").strip()
            if avatar:
                profile_images.append(avatar)
            contacts = row.get("contacts") or {}
            emails.extend(str(item) for item in contacts.get("emails", []))
            phones.extend(str(item) for item in contacts.get("phones", []))
            external_links.extend(str(item) for item in contacts.get("links", []))
            blob_parts = [
                str(row.get("bio") or ""),
                str(row.get("context") or ""),
                " ".join(str(item) for item in (row.get("links") or [])),
            ]
            credential_hits.append(hunt_credential_signals("\n".join(blob_parts)))

        merged_credentials = {
            "emails": filter_valid_emails(emails + [item for hit in credential_hits for item in hit.get("emails", [])]),
            "phones": filter_valid_phones(phones + [item for hit in credential_hits for item in hit.get("phones", [])]),
            "api_keys": _dedupe([item for hit in credential_hits for item in hit.get("api_keys", [])]),
            "pgp_blocks": _dedupe([item for hit in credential_hits for item in hit.get("pgp_blocks", [])]),
            "ssh_public_keys": _dedupe([item for hit in credential_hits for item in hit.get("ssh_public_keys", [])]),
            "jwts": _dedupe([item for hit in credential_hits for item in hit.get("jwts", [])]),
            "base64_blobs": _dedupe([item for hit in credential_hits for item in hit.get("base64_blobs", [])]),
        }
        domains = filter_valid_hostnames(
            [
                urlparse(link).hostname or ""
                for link in external_links + links
            ]
        )
        return {
            "username": username,
            "profiles_found": len(found),
            "bios": bios,
            "emails": merged_credentials["emails"],
            "phones": merged_credentials["phones"],
            "external_links": _dedupe(external_links + links),
            "external_domains": domains,
            "mentions": _dedupe(mentions + _MENTION_RE.findall("\n".join(bios))),
            "profile_images": _dedupe(profile_images),
            "credential_signals": merged_credentials,
            "success": True,
            "error": "",
        }
    except Exception as exc:
        return {
            "username": username,
            "profiles_found": 0,
            "bios": [],
            "emails": [],
            "phones": [],
            "external_links": [],
            "external_domains": [],
            "mentions": [],
            "profile_images": [],
            "credential_signals": hunt_credential_signals(""),
            "success": False,
            "error": str(exc),
        }


__all__ = ["hunt_contact_surface", "hunt_credential_signals", "hunt_username_signals"]
