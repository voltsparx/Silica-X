# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

"""Typed packet-crafting models for read-only, authorized reconnaissance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PacketCraftingRequest:
    """Describe a read-only packet crafting request for an authorized host or network."""

    investigation_target: str
    authorized_host: str
    service_inquiry_ports: tuple[int, ...] = ()
    authorized_network_range: str | None = None
    timeout_seconds: float = 2.0
    delay_seconds: float = 0.1
    source_port: int = 40000
    source_mac_address: str | None = None
    interface_name: str | None = None
    include_banner_inquiry: bool = False
    include_os_fingerprint: bool = False
    tcp_sequence_seed: int = 10_000
    tcp_acknowledgement_seed: int = 1

    def __post_init__(self) -> None:
        """Validate the request shape for read-only, research-grade packet crafting."""

        if not str(self.investigation_target).strip():
            raise ValueError("investigation_target is required.")
        if not str(self.authorized_host).strip():
            raise ValueError("authorized_host is required.")
        if float(self.timeout_seconds) <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if float(self.delay_seconds) < 0:
            raise ValueError("delay_seconds must be zero or greater.")
        if int(self.source_port) <= 0 or int(self.source_port) > 65535:
            raise ValueError("source_port must be between 1 and 65535.")
        for service_inquiry_port in self.service_inquiry_ports:
            if int(service_inquiry_port) <= 0 or int(service_inquiry_port) > 65535:
                raise ValueError("service_inquiry_ports must contain values between 1 and 65535.")


@dataclass(frozen=True)
class PacketCraftingEngineDescriptor:
    """Describe a packet-crafting engine exposed by the framework inventory."""

    engine_id: str
    scan_type: str
    title: str
    reads: str
    packet_purpose: str


@dataclass(frozen=True)
class CraftedPacketArtifact:
    """Wrap a crafted packet and its read-only interpretation metadata."""

    engine_id: str
    scan_type: str
    packet_label: str
    packet_summary: str
    layer_stack: tuple[str, ...]
    authorized_host: str
    service_inquiry_port: int | None
    timeout_seconds: float
    delay_seconds: float
    response_guidance: str
    response_dependent: bool
    scapy_packet: object


@dataclass(frozen=True)
class PacketCraftingBundle:
    """Group one or more crafted packets for a read-only scan intent or profile."""

    bundle_id: str
    title: str
    purpose: str
    scan_types: tuple[str, ...]
    artifacts: tuple[CraftedPacketArtifact, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PacketCraftingProfile:
    """Describe a curated combination of read-only packet-crafting engines."""

    profile_id: str
    title: str
    purpose: str
    scan_types: tuple[str, ...]
    notes: tuple[str, ...]
