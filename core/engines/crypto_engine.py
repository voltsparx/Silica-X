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

import base64
import hashlib
import os
import secrets
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.engines.engine_base import EngineBase
from core.engines.engine_result import EngineResult
from core.engines.health_monitor import EngineHealthMonitor


class CryptoEngine(EngineBase):
    """Cryptographic operation engine for Silica-X."""

    def __init__(self, *, monitor=None) -> None:
        super().__init__(monitor=monitor)

    async def run(self, tasks, context=None) -> list[Any]:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [loop.run_in_executor(pool, task) for task in tasks]
            return list(await asyncio.gather(*futs, return_exceptions=True))

    def hash_data(self, data: str) -> str:
        """Return SHA-256 hex digest of data string."""

        return hashlib.sha256(data.encode("utf-8", errors="replace")).hexdigest()

    def hmac_sign(self, data: str, key: bytes) -> str:
        """Return HMAC-SHA256 signature as base64."""

        import hmac as hmac_lib

        sig = hmac_lib.new(key, data.encode("utf-8", errors="replace"), hashlib.sha256).digest()
        return base64.b64encode(sig).decode()

    def encrypt(self, plaintext: str, key: bytes) -> str:
        """AES-256-GCM encrypt. Returns base64(iv + tag + ciphertext)."""

        if len(key) < 32:
            key = hashlib.sha256(key).digest()
        else:
            key = key[:32]
        iv = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend(),
        ).encryptor()
        ct = encryptor.update(plaintext.encode("utf-8", errors="replace")) + encryptor.finalize()
        payload = iv + encryptor.tag + ct
        return base64.b64encode(payload).decode()

    def decrypt(self, ciphertext_b64: str, key: bytes) -> str:
        """AES-256-GCM decrypt. Returns plaintext string."""

        if len(key) < 32:
            key = hashlib.sha256(key).digest()
        else:
            key = key[:32]
        payload = base64.b64decode(ciphertext_b64)
        iv, tag, ct = payload[:12], payload[12:28], payload[28:]
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend(),
        ).decryptor()
        return (decryptor.update(ct) + decryptor.finalize()).decode("utf-8", errors="replace")

    def derive_key(self, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """PBKDF2-HMAC-SHA256 key derivation. Returns (key_bytes, salt_bytes)."""

        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(password.encode("utf-8", errors="replace"))
        return key, salt

    def fingerprint(self, obj: Any) -> str:
        """SHA-256 fingerprint of any JSON-serializable object."""

        import json

        try:
            raw = json.dumps(obj, sort_keys=True, default=str)
        except Exception:
            raw = str(obj)
        return self.hash_data(raw)

    def random_token(self) -> str:
        """Cryptographically secure 64-character hex token."""

        return secrets.token_hex(32)


__all__ = ["EngineBase", "EngineResult", "EngineHealthMonitor", "CryptoEngine", "serialization", "hmac"]
