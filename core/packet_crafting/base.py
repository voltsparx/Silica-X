# ------------------------------------------------------------------------------
# SPDX-License-Identifier: Proprietary
#
# Sylica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Sylica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Sylica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ------------------------------------------------------------------------------

"""Base packet-crafting engine contract for read-only, authorized research."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.packet_crafting.models import (
    CraftedPacketArtifact,
    PacketCraftingBundle,
    PacketCraftingEngineDescriptor,
    PacketCraftingRequest,
)
from core.packet_crafting.scapy_support import load_scapy_layer_catalog, summarize_packet_layers


class PacketCraftingEngine(ABC):
    """Craft read-only packet templates for one authorized reconnaissance scan type."""

    engine_id: str = ""
    scan_type: str = ""
    title: str = ""
    reads: str = ""
    packet_purpose: str = ""

    def descriptor(self) -> PacketCraftingEngineDescriptor:
        """Describe what the engine reads or observes in a read-only workflow."""

        return PacketCraftingEngineDescriptor(
            engine_id=self.engine_id,
            scan_type=self.scan_type,
            title=self.title,
            reads=self.reads,
            packet_purpose=self.packet_purpose,
        )

    @abstractmethod
    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft read-only packet templates for an authorized host or network."""

    def _scapy(self) -> object:
        """Load Scapy lazily so packet crafting stays explicit and optional."""

        return load_scapy_layer_catalog()

    def _validated_ports(self, service_inquiry: PacketCraftingRequest) -> tuple[int, ...]:
        """Return validated inquiry ports for read-only, port-oriented packet crafting."""

        normalized_ports = tuple(
            sorted({int(service_inquiry_port) for service_inquiry_port in service_inquiry.service_inquiry_ports})
        )
        if not normalized_ports:
            raise ValueError(f"{self.engine_id} requires at least one service_inquiry_port.")
        return normalized_ports

    def _artifact(
        self,
        *,
        service_inquiry: PacketCraftingRequest,
        packet_label: str,
        packet_summary: str,
        response_guidance: str,
        scapy_packet: object,
        service_inquiry_port: int | None = None,
        response_dependent: bool = False,
    ) -> CraftedPacketArtifact:
        """Wrap one crafted packet in typed, read-only artifact metadata."""

        return CraftedPacketArtifact(
            engine_id=self.engine_id,
            scan_type=self.scan_type,
            packet_label=packet_label,
            packet_summary=packet_summary,
            layer_stack=summarize_packet_layers(scapy_packet),
            authorized_host=service_inquiry.authorized_host,
            service_inquiry_port=service_inquiry_port,
            timeout_seconds=float(service_inquiry.timeout_seconds),
            delay_seconds=float(service_inquiry.delay_seconds),
            response_guidance=response_guidance,
            response_dependent=response_dependent,
            scapy_packet=scapy_packet,
        )

    def _sequence_number(self, service_inquiry: PacketCraftingRequest, service_inquiry_port: int, *, offset: int = 0) -> int:
        """Build a deterministic TCP sequence seed for read-only packet templates."""

        return int(service_inquiry.tcp_sequence_seed) + int(service_inquiry_port) + int(offset)
