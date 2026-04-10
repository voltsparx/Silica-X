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

"""Lazy Scapy loading helpers for read-only packet crafting."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


@dataclass(frozen=True)
class ScapyLayerCatalog:
    """Expose the Scapy packet layers required by the packet-crafting engines."""

    Ether: type[object]
    ARP: type[object]
    IP: type[object]
    TCP: type[object]
    UDP: type[object]
    ICMP: type[object]
    Raw: type[object] | None


def load_scapy_layer_catalog() -> ScapyLayerCatalog:
    """Load Scapy packet layers for read-only packet crafting without side effects."""

    try:
        scapy_all = import_module("scapy.all")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Scapy is required for packet crafting. Install the framework dependencies first."
        ) from exc

    return ScapyLayerCatalog(
        Ether=getattr(scapy_all, "Ether"),
        ARP=getattr(scapy_all, "ARP"),
        IP=getattr(scapy_all, "IP"),
        TCP=getattr(scapy_all, "TCP"),
        UDP=getattr(scapy_all, "UDP"),
        ICMP=getattr(scapy_all, "ICMP"),
        Raw=getattr(scapy_all, "Raw", None),
    )


def summarize_packet_layers(scapy_packet: object) -> tuple[str, ...]:
    """Return packet layer names without transmitting packets or mutating them."""

    layer_names: list[str] = []
    current_layer = scapy_packet
    visited_layers = 0
    while current_layer is not None and visited_layers < 12:
        layer_name = type(current_layer).__name__
        if layer_name == "NoPayload":
            break
        layer_names.append(layer_name)
        next_layer = getattr(current_layer, "payload", None)
        if next_layer is None or next_layer is current_layer:
            break
        current_layer = next_layer
        visited_layers += 1
    return tuple(layer_names)
