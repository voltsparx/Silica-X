# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.collect.domain_intel import normalize_domain, scan_domain_surface
from core.collect.scanner import scan_username
from core.entity import EntityResolver
from core.kb import GraphKnowledgeBase
from core.reporter_progressive import ProgressiveReporter, ReportMode
from core.risk_ranker import rank_entities
from core.scorer import score_profile_finding
from core.signal_layer import Finding, SignalLayer
from filters.relevance_gate import is_worth_storing


@dataclass
class PipelineConfig:
    target_usernames: list[str]
    target_domains: list[str]
    mode: ReportMode = "analyst"
    run_media_recon: bool = True
    run_ocr: bool = True
    use_tor: bool = False
    proxy_url: str | None = None
    timeout_seconds: int = 20
    max_concurrency: int = 25


async def _run_profile_scan(
    usernames: list[str],
    resolver: EntityResolver,
    *,
    proxy_url: str | None = None,
    timeout_seconds: int = 20,
    max_concurrency: int = 25,
) -> list[Finding]:
    findings: list[Finding] = []
    for username in usernames:
        rows = await scan_username(
            username=username,
            proxy_url=proxy_url,
            timeout_seconds=timeout_seconds,
            max_concurrency=max_concurrency,
        )
        for row in rows:
            status = str(row.get("status", "") or "")
            if status != "FOUND":
                continue

            contacts = row.get("contacts", {}) if isinstance(row.get("contacts"), dict) else {}
            emails = [str(item).strip() for item in list(contacts.get("emails", []) or []) if str(item).strip()]
            email = emails[0] if emails else None
            entity = resolver.resolve(username, email=email)
            platform_name = str(row.get("platform", "") or "unknown")
            url = str(row.get("url", "") or "")
            if url:
                entity.platforms[platform_name] = url
                entity.exposure_breadth = len(entity.platforms)

            score_input = {
                "status_code": row.get("http_status"),
                "username": username,
                "bio": row.get("bio", ""),
                "avatar_hash_match": bool(row.get("avatar_hash_match")),
                "recent_activity": bool(row.get("recent_activity")),
                "join_date_consistent": bool(row.get("join_date_consistent")),
                "followers": 1 if status == "FOUND" else 0,
                "cross_platform_link": bool(list(row.get("links", []) or [])),
            }
            should_store, _reason = is_worth_storing(
                {
                    "status_code": row.get("http_status") or 200,
                    "bio": row.get("bio", ""),
                    "followers": 1 if status == "FOUND" else 0,
                    "recent_activity": bool(row.get("recent_activity")),
                },
                platform_category="profile",
            )
            if not should_store:
                continue

            score_result = score_profile_finding(score_input, username)
            native_confidence = max(0.0, min(float(row.get("confidence", 0) or 0) / 100.0, 1.0))
            why = list(score_result.why)
            context = str(row.get("context", "") or "").strip()
            if context:
                why.append(context)
            findings.append(
                Finding(
                    source_module="profile",
                    entity_id=entity.canonical_id,
                    platform=platform_name,
                    url=url,
                    raw={
                        **row,
                        "status_code": row.get("http_status"),
                        "username": username,
                        "leak_indicator": bool(emails),
                    },
                    confidence=max(native_confidence, score_result.score),
                    why=why,
                )
            )
    return findings


def _domain_summary_confidence(payload: dict[str, Any]) -> tuple[float, list[str]]:
    confidence = 0.25
    why: list[str] = []
    https_payload = payload.get("https", {}) if isinstance(payload.get("https"), dict) else {}
    rdap_payload = payload.get("rdap", {}) if isinstance(payload.get("rdap"), dict) else {}
    subdomains = list(payload.get("subdomains", []) or [])
    resolved_addresses = list(payload.get("resolved_addresses", []) or [])

    https_status = https_payload.get("status")
    if isinstance(https_status, int) and https_status < 400:
        confidence += 0.20
        why.append("https endpoint responded")
    if rdap_payload:
        confidence += 0.15
        why.append("rdap ownership data available")
    if subdomains:
        confidence += min(len(subdomains) / 50.0, 0.30)
        why.append(f"{len(subdomains)} subdomains discovered")
    if resolved_addresses:
        confidence += min(len(resolved_addresses) / 10.0, 0.10)
        why.append(f"{len(resolved_addresses)} resolved addresses")
    return min(confidence, 1.0), why


async def _run_surface_scan(
    domains: list[str],
    resolver: EntityResolver,
    *,
    timeout_seconds: int = 20,
) -> list[Finding]:
    findings: list[Finding] = []
    for domain in domains:
        normalized_domain = normalize_domain(domain)
        if not normalized_domain:
            continue
        payload = await scan_domain_surface(
            domain=normalized_domain,
            timeout_seconds=timeout_seconds,
            include_ct=True,
            include_rdap=True,
            recon_mode="hybrid",
        )
        entity = resolver.resolve(normalized_domain)
        main_url = f"https://{normalized_domain}"
        entity.platforms["domain_surface"] = main_url

        subdomains = [str(item).strip().lower() for item in list(payload.get("subdomains", []) or []) if str(item).strip()]
        for subdomain in subdomains[:20]:
            entity.platforms.setdefault(f"subdomain:{subdomain}", f"https://{subdomain}")
        entity.exposure_breadth = len(entity.platforms)

        confidence, why = _domain_summary_confidence(payload)
        findings.append(
            Finding(
                source_module="surface",
                entity_id=entity.canonical_id,
                platform="domain_surface",
                url=main_url,
                raw=payload,
                confidence=confidence,
                why=why or ["domain surface collected"],
            )
        )

        prioritized = set(str(item).strip().lower() for item in list(payload.get("prioritized_subdomains", []) or []) if str(item).strip())
        for subdomain in subdomains[:50]:
            subdomain_why = ["certificate transparency subdomain discovered"]
            if subdomain in prioritized:
                subdomain_why.append("prioritized by surface guidance")
            findings.append(
                Finding(
                    source_module="surface",
                    entity_id=entity.canonical_id,
                    platform="subdomain",
                    url=f"https://{subdomain}",
                    raw={"subdomain": subdomain, "anomaly_flag": subdomain.startswith(("dev.", "staging.", "admin."))},
                    confidence=0.62 if subdomain in prioritized else 0.48,
                    why=subdomain_why,
                )
            )
    return findings


async def run_full_pipeline(cfg: PipelineConfig) -> str:
    """
    Single entry point that replaces running profile + surface + fusion manually.
    Returns rendered report string.
    """

    resolver = EntityResolver()
    sig_layer = SignalLayer()
    all_findings: list[Finding] = []

    profile_findings = await _run_profile_scan(
        cfg.target_usernames,
        resolver,
        proxy_url=cfg.proxy_url,
        timeout_seconds=cfg.timeout_seconds,
        max_concurrency=cfg.max_concurrency,
    )
    all_findings.extend(sig_layer.process_batch(profile_findings))

    surface_findings = await _run_surface_scan(
        cfg.target_domains,
        resolver,
        timeout_seconds=cfg.timeout_seconds,
    )
    all_findings.extend(sig_layer.process_batch(surface_findings))

    if cfg.run_media_recon:
        from modules.media_recon import MediaRecon

        media = MediaRecon()
        for finding in [item for item in all_findings if item.tier == "HIGH"]:
            avatar_url = str(finding.raw.get("avatar_url", "") or "")
            if not avatar_url:
                continue
            media_finding = await media.analyse_avatar(avatar_url)
            if media_finding.phash:
                resolver.resolve(finding.entity_id, avatar_hash=media_finding.phash)

    entities = resolver.all_entities()
    for entity in entities:
        entity.exposure_breadth = len(entity.platforms)
    ranked = rank_entities(entities, all_findings)
    risk_scores = {entity.canonical_id: score for entity, score in ranked}

    kb = GraphKnowledgeBase()
    for entity, score in ranked:
        entity.risk_score = score
        kb.upsert_entity(entity, risk_score=score)
    for finding in all_findings:
        kb.insert_finding(finding)

    reporter = ProgressiveReporter(all_findings, risk_scores)
    return reporter.render(mode=cfg.mode)
