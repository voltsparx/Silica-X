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

"""SYN packet crafting engine for read-only service exposure inquiries."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class SynPacketCraftingEngine(PacketCraftingEngine):
    """Craft TCP SYN packets for read-only, authorized half-open service inquiries."""

    engine_id = "packet_crafter_syn"
    scan_type = "syn"
    title = "SYN Packet Crafter"
    reads = "TCP SYN-ACK, RST, or silence from authorized services to classify open, closed, or filtered states."
    packet_purpose = "Half-open TCP service inquiry for read-only attack-surface mapping."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft TCP SYN packets without sending payloads or completing a handshake."""

        scapy_catalog = self._scapy()
        artifacts = []
        for service_inquiry_port in self._validated_ports(service_inquiry):
            scapy_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="S",
                seq=self._sequence_number(service_inquiry, service_inquiry_port),
            )
            artifacts.append(
                self._artifact(
                    service_inquiry=service_inquiry,
                    packet_label=f"syn_inquiry_{service_inquiry_port}",
                    packet_summary=f"TCP SYN inquiry to {service_inquiry.authorized_host}:{service_inquiry_port}",
                    response_guidance="SYN-ACK suggests open, RST suggests closed, and silence suggests filtered.",
                    scapy_packet=scapy_packet,
                    service_inquiry_port=service_inquiry_port,
                )
            )
        return PacketCraftingBundle(
            bundle_id=self.engine_id,
            title=self.title,
            purpose=self.packet_purpose,
            scan_types=(self.scan_type,),
            artifacts=tuple(artifacts),
            notes=(
                "SYN inquiry is read-only and does not carry an application payload.",
                "A separate, scope-gated transmission layer must send a cleanup RST after SYN-ACK if execution is enabled.",
            ),
        )
