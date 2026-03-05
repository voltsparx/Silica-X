# ──────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────

"""Centralized logger for orchestration-layer components."""

from __future__ import annotations

import logging
from typing import Final


LOGGER_NAMESPACE: Final[str] = "silica_x"


def _configure_root_logger() -> logging.Logger:
    root_logger = logging.getLogger(LOGGER_NAMESPACE)
    if root_logger.handlers:
        return root_logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    root_logger.propagate = False
    return root_logger


def get_logger(component: str) -> logging.Logger:
    """Return a namespaced logger configured for framework internals."""

    _configure_root_logger()
    suffix = component.strip().replace(" ", "_")
    if not suffix:
        return logging.getLogger(LOGGER_NAMESPACE)
    return logging.getLogger(f"{LOGGER_NAMESPACE}.{suffix}")
