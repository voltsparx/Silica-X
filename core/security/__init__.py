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

"""Security layer exports for orchestrator architecture."""

from core.security.credential_manager import CredentialVault
from core.security.encryption import derive_secret_key
from core.security.proxy_manager import ProxySettings, build_proxy_settings

__all__ = ["CredentialVault", "ProxySettings", "build_proxy_settings", "derive_secret_key"]
