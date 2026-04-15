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

"""Framework-owned wordlists and inventory helpers."""

from wordlists.attack_surface import (
    attack_surface_inventory,
    load_attack_surface_port_wordlist,
    load_attack_surface_text_wordlist,
)
from wordlists.inventory import WordlistAsset, WordlistInventory, build_wordlist_inventory

__all__ = [
    "WordlistAsset",
    "WordlistInventory",
    "attack_surface_inventory",
    "build_wordlist_inventory",
    "load_attack_surface_port_wordlist",
    "load_attack_surface_text_wordlist",
]
