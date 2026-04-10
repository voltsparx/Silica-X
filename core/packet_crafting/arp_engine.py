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

"""ARP packet crafting engine for local read-only host discovery."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class ArpPacketCraftingEngine(PacketCraftingEngine):
    """Craft broadcast ARP discovery packets for an authorized local network range."""

    engine_id = "packet_crafter_arp"
    scan_type = "arp"
    title = "ARP Discovery Packet Crafter"
    reads = "Broadcast ARP replies that reveal which authorized local hosts respond with MAC addresses."
    packet_purpose = "Layer-2 host discovery for read-only, authorized local-network research."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft a broadcast ARP request packet without transmitting or modifying any host."""

        if not str(service_inquiry.authorized_network_range or "").strip():
            raise ValueError("authorized_network_range is required for arp packet crafting.")

        scapy_catalog = self._scapy()
        scapy_packet = scapy_catalog.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy_catalog.ARP(
            pdst=str(service_inquiry.authorized_network_range).strip()
        )
        artifact = self._artifact(
            service_inquiry=service_inquiry,
            packet_label="arp_broadcast_request",
            packet_summary=f"ARP who-has inquiry for {service_inquiry.authorized_network_range}",
            response_guidance="ARP reply with sender MAC address indicates a live authorized host on the local segment.",
            scapy_packet=scapy_packet,
        )
        return PacketCraftingBundle(
            bundle_id=self.engine_id,
            title=self.title,
            purpose=self.packet_purpose,
            scan_types=(self.scan_type,),
            artifacts=(artifact,),
            notes=(
                "ARP discovery is local-network only and does not cross routers.",
                "This engine only crafts the packet template; transmission remains a separate, scope-gated step.",
            ),
        )
