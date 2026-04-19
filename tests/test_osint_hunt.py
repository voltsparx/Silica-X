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
from unittest.mock import patch

from core.collect.osint_hunt import (
    hunt_contact_surface,
    hunt_credential_signals,
    hunt_username_signals,
)


def test_hunt_credential_signals_finds_email():
    result = hunt_credential_signals("reach me at alice@example.com")
    assert "alice@example.com" in result["emails"]


def test_hunt_credential_signals_finds_api_key_pattern():
    result = hunt_credential_signals("token=abcdef1234567890")
    assert result["api_keys"]


def test_hunt_credential_signals_finds_phone():
    result = hunt_credential_signals("Call me on +1 555 123 4567")
    assert result["phones"]


def test_hunt_username_signals_returns_dict():
    async def fake_scan_username(*args, **kwargs):
        return [
            {
                "status": "FOUND",
                "bio": "Contact alice@example.com",
                "links": ["https://example.com"],
                "mentions": ["alice"],
                "contacts": {"emails": ["alice@example.com"], "phones": [], "links": ["https://example.com"]},
            }
        ]

    with patch("core.collect.osint_hunt.scan_username", side_effect=fake_scan_username):
        result = asyncio.run(hunt_username_signals("alice"))
    assert isinstance(result, dict)
    assert result["success"] is True


def test_hunt_contact_surface_returns_dict():
    class _Response:
        def __init__(self, text: str):
            self.status = 200
            self._text = text

        async def text(self, errors="replace"):
            return self._text

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Session:
        def get(self, url, **kwargs):
            return _Response("Contact alice@example.com and token=abcdef1234567890")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("core.collect.osint_hunt.aiohttp.ClientSession", return_value=_Session()):
        result = asyncio.run(hunt_contact_surface("example.com"))
    assert isinstance(result, dict)
    assert result["success"] is True
