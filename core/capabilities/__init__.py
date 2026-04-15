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

"""Capability registry exports for orchestration layer."""

from core.capabilities.base import Capability
from core.capabilities.correlation_capability import CorrelationCapability
from core.capabilities.domain_enumeration import DomainEnumerationCapability
from core.capabilities.username_lookup import UsernameLookupCapability


def build_capability_registry() -> dict[str, Capability]:
    """Build default capability registry used by the orchestrator."""

    capabilities: list[Capability] = [
        UsernameLookupCapability(),
        DomainEnumerationCapability(),
        CorrelationCapability(),
    ]
    return {capability.capability_id: capability for capability in capabilities}


__all__ = [
    "Capability",
    "CorrelationCapability",
    "DomainEnumerationCapability",
    "UsernameLookupCapability",
    "build_capability_registry",
]
