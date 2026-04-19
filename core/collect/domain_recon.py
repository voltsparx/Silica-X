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
# ──────────────────────────────────────────────────────────────

"""Deep domain intelligence collection helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from functools import partial
import importlib.util
import os
import shutil
import socket
import subprocess
from typing import Any
from urllib.parse import quote

import aiohttp

from core.collect.domain_intel import scan_domain_surface


def _dedupe_sorted(values: list[str]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


async def collect_dns_records(
    domain: str,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """Collect DNS records for a domain using built-in socket support."""

    loop = asyncio.get_event_loop()
    result: dict[str, Any] = {
        "a_records": [],
        "aaaa_records": [],
        "ptr_records": [],
        "mx_records": [],
        "ns_records": [],
        "txt_records": [],
        "soa_record": [],
        "cname_records": [],
        "error": None,
    }

    try:
        a_infos = await asyncio.wait_for(
            loop.getaddrinfo(domain, None, family=socket.AF_INET),
            timeout=max(1, int(timeout_seconds)),
        )
        result["a_records"] = _dedupe_sorted([row[4][0] for row in a_infos if row and row[4]])
    except Exception as exc:
        result["error"] = str(exc)

    try:
        aaaa_infos = await asyncio.wait_for(
            loop.getaddrinfo(domain, None, family=socket.AF_INET6),
            timeout=max(1, int(timeout_seconds)),
        )
        result["aaaa_records"] = _dedupe_sorted([row[4][0] for row in aaaa_infos if row and row[4]])
    except Exception as exc:
        if result["error"] is None:
            result["error"] = str(exc)

    ptr_records: list[str] = []
    for ip_address in result["a_records"]:
        try:
            host, _service = await asyncio.wait_for(
                loop.getnameinfo((ip_address, 0), socket.NI_NAMEREQD),
                timeout=max(1, int(timeout_seconds)),
            )
            if host:
                ptr_records.append(str(host))
        except Exception:
            continue
    result["ptr_records"] = _dedupe_sorted(ptr_records)

    if importlib.util.find_spec("dns.resolver") is not None:
        try:
            import dns.resolver
        except Exception:
            dns = None
        else:
            dns = dns.resolver
        if dns is not None:
            def _resolve_text(record_type: str) -> list[str]:
                try:
                    answer = dns.resolve(domain, record_type)
                except Exception:
                    return []
                return [str(item).strip() for item in answer if str(item).strip()]

            result["mx_records"] = _dedupe_sorted(await loop.run_in_executor(None, partial(_resolve_text, "MX")))
            result["ns_records"] = _dedupe_sorted(await loop.run_in_executor(None, partial(_resolve_text, "NS")))
            result["txt_records"] = _dedupe_sorted(await loop.run_in_executor(None, partial(_resolve_text, "TXT")))
            result["soa_record"] = _dedupe_sorted(await loop.run_in_executor(None, partial(_resolve_text, "SOA")))
            result["cname_records"] = _dedupe_sorted(await loop.run_in_executor(None, partial(_resolve_text, "CNAME")))

    return result


async def collect_cert_transparency(
    domain: str,
    session: aiohttp.ClientSession,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    """Collect certificate-transparency entries from crt.sh."""

    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=max(1, int(timeout_seconds))),
        ) as response:
            payload = await response.json(content_type=None)
    except Exception as exc:
        return {
            "domain": domain,
            "ct_entries": [],
            "entry_count": 0,
            "error": str(exc),
        }

    entries: list[str] = []
    if isinstance(payload, list):
        for row in payload:
            if not isinstance(row, dict):
                continue
            name_value = str(row.get("name_value", "") or "")
            for token in name_value.splitlines():
                candidate = token.strip().lower()
                if not candidate or candidate.startswith("*."):
                    continue
                entries.append(candidate)
    ct_entries = sorted(set(entries))
    return {
        "domain": domain,
        "ct_entries": ct_entries,
        "entry_count": len(ct_entries),
        "error": None,
    }


def collect_whois_data(domain: str, timeout_seconds: int = 15) -> dict[str, Any]:
    """Collect WHOIS output using the system whois binary."""

    payload: dict[str, Any] = {
        "domain": domain,
        "registrar": "",
        "creation_date": "",
        "expiry_date": "",
        "updated_date": "",
        "name_servers": [],
        "registrant_org": "",
        "registrant_country": "",
        "status": [],
        "dnssec": "",
        "raw_output": "",
        "error": None,
    }

    binary = shutil.which("whois")
    if binary is None:
        payload["error"] = "whois binary not available"
        return payload

    try:
        result = subprocess.run(
            [binary, domain],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        payload["error"] = "whois lookup timed out"
        return payload

    payload["raw_output"] = result.stdout
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if "registrar:" in lowered and not payload["registrar"]:
            payload["registrar"] = line.split(":", 1)[1].strip()
        elif ("creation date:" in lowered or "created:" in lowered) and not payload["creation_date"]:
            payload["creation_date"] = line.split(":", 1)[1].strip()
        elif ("expiry date:" in lowered or "expires:" in lowered) and not payload["expiry_date"]:
            payload["expiry_date"] = line.split(":", 1)[1].strip()
        elif "updated date:" in lowered and not payload["updated_date"]:
            payload["updated_date"] = line.split(":", 1)[1].strip()
        elif "name server:" in lowered:
            payload["name_servers"].append(line.split(":", 1)[1].strip())
        elif "registrant organization:" in lowered and not payload["registrant_org"]:
            payload["registrant_org"] = line.split(":", 1)[1].strip()
        elif "registrant country:" in lowered and not payload["registrant_country"]:
            payload["registrant_country"] = line.split(":", 1)[1].strip()
        elif "domain status:" in lowered:
            payload["status"].append(line.split(":", 1)[1].strip())
        elif "dnssec:" in lowered and not payload["dnssec"]:
            payload["dnssec"] = line.split(":", 1)[1].strip()

    payload["name_servers"] = _dedupe_sorted(payload["name_servers"])
    payload["status"] = _dedupe_sorted(payload["status"])
    return payload


async def collect_whois_data_async(domain: str, timeout_seconds: int = 15) -> dict[str, Any]:
    """Async wrapper for collect_whois_data."""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(collect_whois_data, domain, timeout_seconds=timeout_seconds),
    )


async def collect_http_headers(
    domain: str,
    session: aiohttp.ClientSession,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """Collect HTTP and HTTPS headers plus a security posture summary."""

    async def _probe(url: str) -> tuple[dict[str, Any], str | None]:
        probe = {
            "final_url": url,
            "status_code": 0,
            "headers": {},
            "server": "",
            "x_powered_by": "",
            "content_security_policy": "",
            "strict_transport_security": "",
            "x_frame_options": "",
            "x_content_type_options": "",
            "referrer_policy": "",
            "permissions_policy": "",
            "set_cookie_flags": [],
        }
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=max(1, int(timeout_seconds))),
                allow_redirects=True,
                max_redirects=5,
            ) as response:
                headers = {key: value for key, value in response.headers.items()}
                probe.update(
                    {
                        "final_url": str(response.url),
                        "status_code": int(response.status),
                        "headers": headers,
                        "server": str(headers.get("server", "") or ""),
                        "x_powered_by": str(headers.get("x-powered-by", "") or ""),
                        "content_security_policy": str(headers.get("content-security-policy", "") or ""),
                        "strict_transport_security": str(headers.get("strict-transport-security", "") or ""),
                        "x_frame_options": str(headers.get("x-frame-options", "") or ""),
                        "x_content_type_options": str(headers.get("x-content-type-options", "") or ""),
                        "referrer_policy": str(headers.get("referrer-policy", "") or ""),
                        "permissions_policy": str(headers.get("permissions-policy", "") or ""),
                        "set_cookie_flags": list(response.headers.getall("Set-Cookie", [])),
                    }
                )
                return probe, None
        except Exception as exc:
            return probe, str(exc)

    http_probe, http_error = await _probe(f"http://{domain}")
    https_probe, https_error = await _probe(f"https://{domain}")
    posture_source = https_probe if https_probe.get("headers") else http_probe
    posture_keys = [
        "server",
        "x_powered_by",
        "content_security_policy",
        "strict_transport_security",
        "x_frame_options",
        "x_content_type_options",
        "referrer_policy",
        "permissions_policy",
    ]
    security_posture = {
        key: {
            "present": bool(str(posture_source.get(key, "") or "").strip()),
            "value": str(posture_source.get(key, "") or ""),
        }
        for key in posture_keys
    }
    headers_score = sum(1 for row in security_posture.values() if row["present"])

    error = None
    if http_error and https_error:
        error = f"http: {http_error}; https: {https_error}"
    elif http_error:
        error = f"http: {http_error}"
    elif https_error:
        error = f"https: {https_error}"

    return {
        "domain": domain,
        "http_probe": http_probe,
        "https_probe": https_probe,
        "redirects_to_https": bool(str(http_probe.get("final_url", "")).startswith("https://")),
        "security_posture": security_posture,
        "headers_score": headers_score,
        "error": error,
    }


async def run_domain_deep_recon(
    domain: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Run full deep domain reconnaissance."""

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        dns_result, ct_result, http_result = await asyncio.gather(
            collect_dns_records(domain, timeout_seconds=min(timeout_seconds, 15)),
            collect_cert_transparency(domain, session, timeout_seconds=min(timeout_seconds, 20)),
            collect_http_headers(domain, session, timeout_seconds=min(timeout_seconds, 15)),
        )
        whois_result = await collect_whois_data_async(domain, timeout_seconds=min(timeout_seconds, 15))

    known_dns_tokens = set(dns_result.get("ptr_records", []) or [])
    known_dns_tokens.update(dns_result.get("cname_records", []) or [])
    known_dns_tokens.update(dns_result.get("ns_records", []) or [])
    known_dns_tokens.update(dns_result.get("mx_records", []) or [])
    known_dns_tokens.update(dns_result.get("soa_record", []) or [])
    additional_ct_subdomains = sorted(
        {
            entry
            for entry in ct_result.get("ct_entries", []) or []
            if "." in entry and not entry.startswith("*.") and entry not in known_dns_tokens and entry != domain
        }
    )

    return {
        "domain": domain,
        "dns": dns_result,
        "whois": whois_result,
        "cert_transparency": ct_result,
        "http_headers": http_result,
        "additional_ct_subdomains": additional_ct_subdomains,
        "recon_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


async def run_domain_recon(domain: str, options: dict | None = None) -> dict:
    """Run comprehensive domain OSINT recon."""

    options = options or {}
    errors: list[str] = []
    result: dict[str, Any] = {
        "domain": domain,
        "dns": {
            "a": [],
            "aaaa": [],
            "mx": [],
            "ns": [],
            "txt": [],
            "cname": [],
            "soa": "",
            "spf": "",
            "dmarc": "",
            "ptr": [],
            "dkim": [],
        },
        "whois": {"registrar": "", "creation_date": "", "expiry_date": "", "name_servers": []},
        "ct_subdomains": [],
        "http_posture": {
            "status_code": 0,
            "https_available": False,
            "redirect_to_https": False,
            "headers": {},
            "tech_stack": [],
            "security_txt": "",
        },
        "robots_txt": "",
        "spf_valid": False,
        "dmarc_policy": "",
        "security_txt_present": False,
        "shodan_passive": {},
        "success": True,
        "errors": errors,
    }

    timeout_seconds = max(5, int(options.get("timeout_seconds", 25)))
    proxy_url = str(options.get("proxy_url") or "").strip() or None
    normalized = domain.strip().lower()

    async def _dns_lookup(name: str, record_type: str) -> list[str]:
        if importlib.util.find_spec("dns.resolver") is None:
            return []
        try:
            import dns.resolver

            answer = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: dns.resolver.resolve(name, record_type),
            )
            return [str(item).strip().strip('"') for item in answer if str(item).strip()]
        except Exception as exc:
            errors.append(f"dns {record_type} {name}: {exc}")
            return []

    def _parse_tech_stack(headers: dict[str, str]) -> list[str]:
        stack: list[str] = []
        mapping = {
            "server": headers.get("server", ""),
            "x-powered-by": headers.get("x-powered-by", ""),
            "x-generator": headers.get("x-generator", ""),
            "via": headers.get("via", ""),
        }
        for key, value in mapping.items():
            if value:
                stack.append(f"{key}:{value}")
        if headers.get("cf-ray"):
            stack.append("Cloudflare")
        if headers.get("x-vercel-id"):
            stack.append("Vercel")
        return sorted(set(stack))

    async def _fetch_text(session: aiohttp.ClientSession, url: str) -> tuple[int, str, dict[str, str]]:
        request_kwargs: dict[str, Any] = {
            "timeout": aiohttp.ClientTimeout(total=timeout_seconds),
            "allow_redirects": True,
        }
        if proxy_url:
            request_kwargs["proxy"] = proxy_url
        async with session.get(url, **request_kwargs) as response:
            text = await response.text(errors="replace")
            return int(response.status), text, {k: v for k, v in response.headers.items()}

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            base_surface = await scan_domain_surface(
                domain=normalized,
                timeout_seconds=timeout_seconds,
                include_ct=True,
                include_rdap=True,
                max_subdomains=int(options.get("max_subdomains", 100)),
                recon_mode=str(options.get("recon_mode", "hybrid") or "hybrid"),
            )
        except Exception as exc:
            errors.append(f"scan_domain_surface: {exc}")
            base_surface = {}

        try:
            a_records, aaaa_records, mx_records, ns_records, txt_records, cname_records, soa_records, ptr_records = await asyncio.gather(
                _dns_lookup(normalized, "A"),
                _dns_lookup(normalized, "AAAA"),
                _dns_lookup(normalized, "MX"),
                _dns_lookup(normalized, "NS"),
                _dns_lookup(normalized, "TXT"),
                _dns_lookup(normalized, "CNAME"),
                _dns_lookup(normalized, "SOA"),
                _dns_lookup(normalized, "PTR"),
            )
            result["dns"].update(
                {
                    "a": a_records,
                    "aaaa": aaaa_records,
                    "mx": mx_records,
                    "ns": ns_records,
                    "txt": txt_records,
                    "cname": cname_records,
                    "soa": soa_records[0] if soa_records else "",
                    "ptr": ptr_records,
                }
            )
        except Exception as exc:
            errors.append(f"dns gather: {exc}")

        result["whois"] = {
            "registrar": str((base_surface.get("rdap") or {}).get("registrar", "")),
            "creation_date": str((base_surface.get("rdap") or {}).get("creation_date", "")),
            "expiry_date": str((base_surface.get("rdap") or {}).get("expiration_date", "")),
            "name_servers": list((base_surface.get("rdap") or {}).get("name_servers", []) or []),
        }
        result["ct_subdomains"] = list(base_surface.get("subdomains", []) or [])

        try:
            status, body, headers = await _fetch_text(session, f"https://{normalized}")
            result["http_posture"].update(
                {
                    "status_code": status,
                    "https_available": status < 400,
                    "redirect_to_https": False,
                    "headers": headers,
                    "tech_stack": _parse_tech_stack(headers),
                }
            )
        except Exception as exc:
            errors.append(f"https probe: {exc}")
            try:
                status, body, headers = await _fetch_text(session, f"http://{normalized}")
                result["http_posture"].update(
                    {
                        "status_code": status,
                        "https_available": False,
                        "redirect_to_https": bool(str(headers.get("location", "")).startswith("https://")),
                        "headers": headers,
                        "tech_stack": _parse_tech_stack(headers),
                    }
                )
            except Exception as inner_exc:
                errors.append(f"http probe: {inner_exc}")

        preferred_scheme = "https" if result["http_posture"]["https_available"] else "http"
        try:
            _status, robots_text, _headers = await _fetch_text(session, f"{preferred_scheme}://{normalized}/robots.txt")
            result["robots_txt"] = robots_text[:4000]
        except Exception as exc:
            errors.append(f"robots.txt: {exc}")

        security_text = ""
        for path in ("/.well-known/security.txt", "/security.txt"):
            try:
                status, text, _headers = await _fetch_text(session, f"{preferred_scheme}://{normalized}{path}")
                if status < 400 and text.strip():
                    security_text = text[:4000]
                    result["security_txt_present"] = True
                    break
            except Exception as exc:
                errors.append(f"security.txt {path}: {exc}")
        result["http_posture"]["security_txt"] = security_text

        try:
            _status, _text, _headers = await _fetch_text(session, f"{preferred_scheme}://{normalized}/sitemap.xml")
        except Exception as exc:
            errors.append(f"sitemap.xml: {exc}")

        safe_url = f"https://transparencyreport.google.com/safe-browsing/search?url={quote(normalized)}"
        try:
            _status, safe_text, _headers = await _fetch_text(session, safe_url)
            result["safe_browsing"] = "Site is not listed" in safe_text
        except Exception as exc:
            errors.append(f"safe browsing: {exc}")

        shodan_key = str(os.getenv("SHODAN_API_KEY") or "").strip()
        if shodan_key:
            shodan_url = f"https://api.shodan.io/dns/resolve?hostnames={quote(normalized)}&key={quote(shodan_key)}"
            try:
                request_kwargs: dict[str, Any] = {"timeout": aiohttp.ClientTimeout(total=timeout_seconds)}
                if proxy_url:
                    request_kwargs["proxy"] = proxy_url
                async with session.get(shodan_url, **request_kwargs) as response:
                    payload = await response.json(content_type=None)
                    result["shodan_passive"] = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                errors.append(f"shodan: {exc}")

    txt_records = list(result["dns"].get("txt", []) or [])
    spf_record = next((row for row in txt_records if "v=spf1" in row.lower()), "")
    dmarc_records = await _dns_lookup(f"_dmarc.{normalized}", "TXT")
    dkim_records = await _dns_lookup(f"default._domainkey.{normalized}", "TXT")
    dmarc_record = dmarc_records[0] if dmarc_records else ""
    result["dns"]["spf"] = spf_record
    result["dns"]["dmarc"] = dmarc_record
    result["dns"]["dkim"] = dkim_records
    result["spf_valid"] = bool(spf_record and "all" in spf_record.lower())
    dmarc_policy = ""
    for token in dmarc_record.split(";"):
        token = token.strip()
        if token.lower().startswith("p="):
            dmarc_policy = token.split("=", 1)[1].strip()
            break
    result["dmarc_policy"] = dmarc_policy
    result["success"] = True
    return result
