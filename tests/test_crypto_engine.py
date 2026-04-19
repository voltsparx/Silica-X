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

from core.engines.crypto_engine import CryptoEngine


def test_hash_data_returns_64char_hex():
    digest = CryptoEngine().hash_data("alice")
    assert len(digest) == 64
    int(digest, 16)


def test_encrypt_decrypt_roundtrip():
    engine = CryptoEngine()
    key = b"secret"
    ciphertext = engine.encrypt("hello", key)
    assert engine.decrypt(ciphertext, key) == "hello"


def test_hmac_sign_returns_base64():
    signature = CryptoEngine().hmac_sign("hello", b"secret")
    assert isinstance(signature, str)
    assert len(signature) > 10


def test_derive_key_returns_32bytes():
    key, salt = CryptoEngine().derive_key("password")
    assert len(key) == 32
    assert len(salt) == 16


def test_fingerprint_is_deterministic():
    engine = CryptoEngine()
    assert engine.fingerprint({"a": 1}) == engine.fingerprint({"a": 1})


def test_random_token_is_64chars():
    token = CryptoEngine().random_token()
    assert len(token) == 64
