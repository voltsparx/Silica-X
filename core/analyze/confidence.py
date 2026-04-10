# ──────────────────────────────────────────────────────────────
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
# ──────────────────────────────────────────────────────────────

# core/analyze/confidence.py
def explain_confidence(r):
    reasons = []
    if r["status"] == "FOUND":
        reasons.append("Profile page exists")
    if r.get("bio"):
        reasons.append("Public bio detected")
    if r.get("links"):
        reasons.append("External links found")
    if r.get("contacts", {}):
        reasons.append("Contacts information found")
    if r["confidence"] >= 90:
        reasons.append("High reliability platform")
    return reasons

