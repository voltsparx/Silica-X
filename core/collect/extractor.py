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

import re
from html import unescape
from typing import Iterable

EMAIL_REGEX = r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
PHONE_REGEX = r"(?:\+?\d[\d\s().-]{6,}\d)"
HOSTNAME_REGEX = r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}\b"
SCRIPT_STYLE_REGEX = r"<(script|style)\b[^>]*>.*?</\1>"
TAG_REGEX = r"<[^>]+>"
META_DESCRIPTION_PATTERNS = (
    r"<meta[^>]*name=['\"]description['\"][^>]*content=['\"](.*?)['\"][^>]*>",
    r"<meta[^>]*content=['\"](.*?)['\"][^>]*name=['\"]description['\"][^>]*>",
    r"<meta[^>]*property=['\"]og:description['\"][^>]*content=['\"](.*?)['\"][^>]*>",
    r"<meta[^>]*content=['\"](.*?)['\"][^>]*property=['\"]og:description['\"][^>]*>",
    r"<meta[^>]*name=['\"]twitter:description['\"][^>]*content=['\"](.*?)['\"][^>]*>",
    r"<meta[^>]*content=['\"](.*?)['\"][^>]*name=['\"]twitter:description['\"][^>]*>",
)


def _strip_scripts_and_styles(text):
    return re.sub(SCRIPT_STYLE_REGEX, " ", text or "", flags=re.I | re.S)


def _strip_tags(text):
    return re.sub(TAG_REGEX, " ", text or "")


def clean(text):
    if not text:
        return None
    normalized = unescape(text)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip()
    return normalized or None


def normalize_email(value):
    token = clean(value)
    if not token:
        return None
    return token.strip(".,;:!?)('\"<>[]{}").lower()


def is_valid_email(value):
    token = normalize_email(value)
    if not token or "@" not in token or token.count("@") != 1:
        return False
    local_part, domain_part = token.split("@", 1)
    if not local_part or not domain_part:
        return False
    if len(token) > 254 or len(local_part) > 64:
        return False
    if local_part.startswith(".") or local_part.endswith("."):
        return False
    if domain_part.startswith(".") or domain_part.endswith("."):
        return False
    if ".." in local_part or ".." in domain_part:
        return False
    if not re.fullmatch(r"[a-z0-9!#$%&'*+/=?^_`{|}~.-]+", local_part):
        return False
    return is_valid_hostname(domain_part)


def normalize_phone(value):
    token = clean(value)
    if not token:
        return None
    digits = re.sub(r"\D", "", token)
    if token.startswith("+"):
        return f"+{digits}"
    return digits


def is_valid_phone(value):
    token = clean(value)
    if not token:
        return False
    digits = re.sub(r"\D", "", token)
    if len(digits) < 8 or len(digits) > 15:
        return False
    if len(set(digits)) < 2:
        return False
    return True


def normalize_hostname(value):
    token = clean(value)
    if not token:
        return None
    lowered = token.strip(".,;:!?)('\"<>[]{}").lower().rstrip(".")
    if lowered.startswith("*."):
        lowered = lowered[2:]
    return lowered or None


def is_valid_hostname(value):
    hostname = normalize_hostname(value)
    if not hostname or len(hostname) > 253:
        return False
    if "." not in hostname:
        return False
    if not re.fullmatch(r"[a-z0-9.-]+", hostname):
        return False
    labels = hostname.split(".")
    if any(not label or len(label) > 63 for label in labels):
        return False
    if any(label.startswith("-") or label.endswith("-") for label in labels):
        return False
    if all(label.isdigit() for label in labels):
        return False
    tld = labels[-1]
    if not tld.isalpha() or len(tld) < 2 or len(tld) > 24:
        return False
    return True


def filter_valid_emails(values: Iterable[str]):
    emails = []
    seen = set()
    for raw in values:
        normalized = normalize_email(raw)
        if not normalized or not is_valid_email(normalized):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        emails.append(normalized)
    return emails


def filter_valid_phones(values: Iterable[str]):
    phones = []
    seen = set()
    for raw in values:
        display = clean(raw)
        normalized = normalize_phone(raw)
        if not normalized or not is_valid_phone(raw):
            continue
        key = normalized.lstrip("+")
        if key in seen:
            continue
        seen.add(key)
        phones.append(display or normalized)
    return phones


def filter_valid_hostnames(values: Iterable[str], *, base_domain=None):
    hosts = []
    seen = set()
    base = normalize_hostname(base_domain) if base_domain else None
    for raw in values:
        normalized = normalize_hostname(raw)
        if not normalized or not is_valid_hostname(normalized):
            continue
        if base and normalized != base and not normalized.endswith(f".{base}"):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        hosts.append(normalized)
    return hosts


def _html_to_text(payload):
    without_scripts = _strip_scripts_and_styles(payload)
    return clean(_strip_tags(without_scripts)) or ""


def extract_bio(html):
    for pattern in META_DESCRIPTION_PATTERNS:
        match = re.search(pattern, html, re.I | re.S)
        if match:
            return clean(match.group(1))

    paragraph = re.search(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
    if paragraph:
        return clean(re.sub("<.*?>", "", paragraph.group(1)))

    return None


def extract_links(html):
    links = re.findall(r"href\s*=\s*['\"](https?://[^'\"#]+)['\"]", html, re.I)
    deduped = []
    seen = set()
    for link in links:
        normalized = clean(link)
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def extract_contacts(html):
    text = _html_to_text(html)
    emails = filter_valid_emails(re.findall(EMAIL_REGEX, text))
    phones = filter_valid_phones(re.findall(PHONE_REGEX, text))

    return {
        "emails": emails,
        "phones": phones,
    }


def extract_username_mentions(html, username):
    mentions = set()
    text = _html_to_text(html)
    patterns = [
        rf"\b{re.escape(username)}\b",
        rf"@{re.escape(username)}",
        rf"/{re.escape(username)}",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text, re.I):
            mentions.add(match)

    return sorted(mentions)
