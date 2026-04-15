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

"""NULL packet crafting engine for read-only firewall and port-state research."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class NullPacketCraftingEngine(PacketCraftingEngine):
    """Craft TCP NULL inquiry packets for read-only firewall and OS behavior research."""

    engine_id = "packet_crafter_null"
    scan_type = "null"
    title = "NULL Packet Crafter"
    reads = "RST or silence from authorized services to infer closed versus open|filtered TCP states."
    packet_purpose = "Read-only NULL inquiry for firewall and operating-system behavior research."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft TCP NULL packets without payload delivery or state-changing traffic."""

        scapy_catalog = self._scapy()
        artifacts = []
        for service_inquiry_port in self._validated_ports(service_inquiry):
            scapy_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="",
                seq=self._sequence_number(service_inquiry, service_inquiry_port),
            )
            artifacts.append(
                self._artifact(
                    service_inquiry=service_inquiry,
                    packet_label=f"null_inquiry_{service_inquiry_port}",
                    packet_summary=f"TCP NULL inquiry to {service_inquiry.authorized_host}:{service_inquiry_port}",
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
                "NULL inquiry is useful when paired with FIN and XMAS in comparative firewall research.",
                "This engine crafts templates only and intentionally excludes spoofing and fragmentation.",
            ),
        )
