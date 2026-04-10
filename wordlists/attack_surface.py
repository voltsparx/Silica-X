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

"""Attack-surface wordlist accessors backed by the framework wordlist inventory."""

from __future__ import annotations

from wordlists.inventory import WordlistAsset, build_wordlist_inventory, load_wordlist_entries, load_wordlist_ports


ATTACK_SURFACE_COLLECTION = "attack_surface"


def attack_surface_inventory() -> tuple[WordlistAsset, ...]:
    """Return the framework-owned attack-surface wordlist inventory."""

    return build_wordlist_inventory().by_collection(ATTACK_SURFACE_COLLECTION)


def load_attack_surface_text_wordlist(filename: str, fallback: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Load one text-based attack-surface wordlist for read-only runtime guidance."""

    return load_wordlist_entries(ATTACK_SURFACE_COLLECTION, filename, fallback)


def load_attack_surface_port_wordlist(filename: str, fallback: tuple[int, ...] = ()) -> tuple[int, ...]:
    """Load one port-based attack-surface wordlist for read-only runtime guidance."""

    return load_wordlist_ports(ATTACK_SURFACE_COLLECTION, filename, fallback)
