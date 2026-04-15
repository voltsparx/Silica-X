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

"""Wordlist discovery and loading helpers for framework-owned inventories."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class WordlistAsset:
    """Describe one framework-owned wordlist file available to the runtime."""

    collection: str
    filename: str
    path: Path
    entry_count: int
    value_kind: str


@dataclass(frozen=True)
class WordlistInventory:
    """Summarize all framework-owned wordlists discovered under the runtime package."""

    root: Path
    assets: tuple[WordlistAsset, ...]

    def by_collection(self, collection: str) -> tuple[WordlistAsset, ...]:
        """Return wordlist assets for one logical collection directory."""

        normalized_collection = str(collection or "").strip().lower()
        return tuple(asset for asset in self.assets if asset.collection == normalized_collection)


def wordlist_root() -> Path:
    """Return the framework-owned wordlist root directory used at runtime."""

    return Path(__file__).resolve().parent


def _read_active_lines(path: Path) -> tuple[str, ...]:
    """Read non-comment lines from a framework-owned wordlist file."""

    if not path.exists():
        return ()
    values: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        values.append(line)
    return tuple(values)


@lru_cache(maxsize=1)
def build_wordlist_inventory() -> WordlistInventory:
    """Build a cached inventory of framework-owned wordlist assets."""

    root = wordlist_root()
    assets: list[WordlistAsset] = []
    for path in sorted(root.rglob("*.txt")):
        collection = path.parent.name.lower()
        value_kind = "ports" if "port" in path.name.lower() else "text"
        assets.append(
            WordlistAsset(
                collection=collection,
                filename=path.name,
                path=path,
                entry_count=len(_read_active_lines(path)),
                value_kind=value_kind,
            )
        )
    return WordlistInventory(root=root, assets=tuple(assets))


def load_wordlist_entries(collection: str, filename: str, fallback: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Load text entries from a framework-owned wordlist file for read-only runtime use."""

    path = wordlist_root() / str(collection).strip() / str(filename).strip()
    values = _read_active_lines(path)
    return values or fallback


def load_wordlist_ports(collection: str, filename: str, fallback: tuple[int, ...] = ()) -> tuple[int, ...]:
    """Load integer port entries from a framework-owned wordlist file for read-only runtime use."""

    values = load_wordlist_entries(collection, filename, ())
    parsed_ports: list[int] = []
    for value in values:
        try:
            parsed_ports.append(int(value))
        except ValueError:
            continue
    return tuple(parsed_ports) or fallback
