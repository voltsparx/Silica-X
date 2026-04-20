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

from core.collect.platform_schema import load_platforms


def test_platform_count_above_threshold() -> None:
    assert len(load_platforms()) >= 50


def test_all_platforms_have_url() -> None:
    assert all(platform.url.strip() for platform in load_platforms())


def test_all_platforms_have_name() -> None:
    assert all(platform.name.strip() for platform in load_platforms())


def test_all_platforms_have_confidence() -> None:
    assert all(platform.confidence > 0 for platform in load_platforms())


def test_github_platform_present() -> None:
    assert any("GitHub" in platform.name for platform in load_platforms())


def test_reddit_platform_present() -> None:
    assert any("Reddit" in platform.name for platform in load_platforms())


def test_no_duplicate_names() -> None:
    names = [platform.name for platform in load_platforms()]
    assert len(names) == len(set(names))
