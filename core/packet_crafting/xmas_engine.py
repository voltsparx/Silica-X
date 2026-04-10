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

"""XMAS packet crafting engine for read-only firewall and port-state research."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class XmasPacketCraftingEngine(PacketCraftingEngine):
    """Craft TCP XMAS inquiry packets for read-only firewall and OS behavior research."""

    engine_id = "packet_crafter_xmas"
    scan_type = "xmas"
    title = "XMAS Packet Crafter"
    reads = "RST or silence from authorized services to infer closed versus open|filtered TCP states."
    packet_purpose = "Read-only XMAS inquiry for firewall and operating-system behavior research."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft TCP XMAS packets without payload delivery or state-changing traffic."""

        scapy_catalog = self._scapy()
        artifacts = []
        for service_inquiry_port in self._validated_ports(service_inquiry):
            scapy_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="FPU",
                seq=self._sequence_number(service_inquiry, service_inquiry_port),
            )
            artifacts.append(
                self._artifact(
                    service_inquiry=service_inquiry,
                    packet_label=f"xmas_inquiry_{service_inquiry_port}",
                    packet_summary=f"TCP XMAS inquiry to {service_inquiry.authorized_host}:{service_inquiry_port}",
                    response_guidance="RST suggests closed, while silence suggests open|filtered behavior.",
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
                "XMAS inquiry is commonly paired with FIN and NULL for comparative firewall research.",
                "This engine crafts templates only and intentionally excludes spoofing and fragmentation.",
            ),
        )
