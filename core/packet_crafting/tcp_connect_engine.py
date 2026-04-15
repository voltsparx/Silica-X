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

"""TCP connect packet crafting engine for read-only handshake templates."""

from __future__ import annotations

from core.packet_crafting.base import PacketCraftingEngine
from core.packet_crafting.models import PacketCraftingBundle, PacketCraftingRequest


class TcpConnectPacketCraftingEngine(PacketCraftingEngine):
    """Craft TCP connect packet templates for read-only service reachability validation."""

    engine_id = "packet_crafter_tcp_connect"
    scan_type = "tcp-connect"
    title = "TCP Connect Packet Crafter"
    reads = "Full-handshake reachability signals from authorized services before a clean connection teardown."
    packet_purpose = "Definitive TCP connect validation using read-only handshake templates."

    def craft_packets(self, service_inquiry: PacketCraftingRequest) -> PacketCraftingBundle:
        """Craft SYN, ACK, and RST handshake templates for read-only validation planning."""

        scapy_catalog = self._scapy()
        artifacts = []
        for service_inquiry_port in self._validated_ports(service_inquiry):
            sequence_number = self._sequence_number(service_inquiry, service_inquiry_port)
            syn_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="S",
                seq=sequence_number,
            )
            ack_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="A",
                seq=sequence_number + 1,
                ack=int(service_inquiry.tcp_acknowledgement_seed),
            )
            rst_packet = scapy_catalog.IP(dst=service_inquiry.authorized_host) / scapy_catalog.TCP(
                sport=int(service_inquiry.source_port),
                dport=service_inquiry_port,
                flags="R",
                seq=sequence_number + 1,
                ack=int(service_inquiry.tcp_acknowledgement_seed),
            )
            artifacts.extend(
                (
                    self._artifact(
                        service_inquiry=service_inquiry,
                        packet_label=f"tcp_connect_syn_{service_inquiry_port}",
                        packet_summary=f"TCP connect SYN stage for {service_inquiry.authorized_host}:{service_inquiry_port}",
                        response_guidance="Use the next ACK template only after a SYN-ACK is observed from the authorized service.",
                        scapy_packet=syn_packet,
                        service_inquiry_port=service_inquiry_port,
                    ),
                    self._artifact(
                        service_inquiry=service_inquiry,
                        packet_label=f"tcp_connect_ack_{service_inquiry_port}",
                        packet_summary=f"TCP connect ACK stage for {service_inquiry.authorized_host}:{service_inquiry_port}",
                        response_guidance="This ACK is response-dependent and should only be populated with observed SYN-ACK values.",
                        scapy_packet=ack_packet,
                        service_inquiry_port=service_inquiry_port,
                        response_dependent=True,
                    ),
                    self._artifact(
                        service_inquiry=service_inquiry,
                        packet_label=f"tcp_connect_rst_{service_inquiry_port}",
                        packet_summary=f"TCP connect cleanup RST for {service_inquiry.authorized_host}:{service_inquiry_port}",
                        response_guidance="This cleanup packet closes the connection after a read-only validation handshake.",
                        scapy_packet=rst_packet,
                        service_inquiry_port=service_inquiry_port,
                        response_dependent=True,
                    ),
                )
            )
        return PacketCraftingBundle(
            bundle_id=self.engine_id,
            title=self.title,
            purpose=self.packet_purpose,
            scan_types=(self.scan_type,),
            artifacts=tuple(artifacts),
            notes=(
                "TCP connect crafting uses response-dependent ACK/RST templates rather than sending fixed sequence values.",
                "The packet crafter stays read-only and leaves live handshake execution to a separate, scope-gated layer.",
            ),
        )
