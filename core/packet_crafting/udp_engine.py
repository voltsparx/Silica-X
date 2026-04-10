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

"""UDP packet crafting engine for read-only service exposure inquiries."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class UdpPacketCraftingEngine(PacketCraftingEngine):
    """Craft UDP service inquiry packets for read-only, authorized reconnaissance."""

    engine_id = "packet_crafter_udp"
    scan_type = "udp"
    title = "UDP Packet Crafter"
    reads = "UDP responses or ICMP unreachable signals from authorized services to classify exposure."
    packet_purpose = "Read-only UDP service inquiry with timeout-aware interpretation guidance."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft UDP inquiry packets without sending application payloads or state-changing traffic."""

        scapy_catalog = self._scapy()
        artifacts = []
        for service_inquiry_port in self._validated_ports(service_inquiry):
            scapy_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.UDP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
            )
            artifacts.append(
                self._artifact(
                    service_inquiry=service_inquiry,
                    packet_label=f"udp_inquiry_{service_inquiry_port}",
                    packet_summary=f"UDP inquiry to {service_inquiry.authorized_host}:{service_inquiry_port}",
                    response_guidance=(
                        "UDP response suggests open, ICMP type 3 code 3 suggests closed, and silence suggests open|filtered."
                    ),
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
                "UDP inquiries generally require longer timeouts than TCP service inquiries.",
                "This engine only crafts packet templates and does not transmit them.",
            ),
        )
