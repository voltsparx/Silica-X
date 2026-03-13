"""Console entrypoint for Silica-X."""

from __future__ import annotations

import asyncio
from typing import Sequence

from core.runner import run


def main(argv: Sequence[str] | None = None) -> None:
    """Run the Silica-X CLI."""
    try:
        raise SystemExit(asyncio.run(run(argv)))
    except KeyboardInterrupt:
        raise SystemExit(130)
