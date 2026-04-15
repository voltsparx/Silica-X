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

"""Explainable confidence scoring model for intelligence entities."""

from __future__ import annotations

from collections.abc import Sequence


class ConfidenceModel:
    """Compute confidence with transparent score breakdown."""

    def score(
        self,
        *,
        heuristic_bonus: float,
        correlation_strengths: Sequence[float],
        evidence_reliability: float,
        contradiction_penalty: float = 0.0,
        base_score: float = 0.3,
    ) -> tuple[float, dict[str, float]]:
        """Return bounded confidence and calculation breakdown."""

        normalized_base = max(0.0, min(1.0, float(base_score)))
        normalized_heuristic = max(0.0, min(0.5, float(heuristic_bonus)))
        normalized_evidence = max(0.0, min(1.0, float(evidence_reliability)))
        normalized_penalty = max(0.0, min(0.5, float(contradiction_penalty)))

        if correlation_strengths:
            avg_strength = sum(float(item) for item in correlation_strengths) / float(len(correlation_strengths))
            normalized_correlation = max(0.0, min(1.0, avg_strength))
        else:
            normalized_correlation = 0.0

        correlation_bonus = normalized_correlation * 0.35
        multi_source_bonus = max(0.0, (normalized_evidence - 0.5) * 0.4)

        raw_total = normalized_base + normalized_heuristic + correlation_bonus + multi_source_bonus - normalized_penalty
        bounded_total = max(0.0, min(1.0, raw_total))

        breakdown = {
            "base": round(normalized_base, 4),
            "heuristic_bonus": round(normalized_heuristic, 4),
            "correlation_bonus": round(correlation_bonus, 4),
            "multi_source_bonus": round(multi_source_bonus, 4),
            "contradiction_penalty": round(-normalized_penalty, 4),
            "total": round(bounded_total, 4),
        }
        return bounded_total, breakdown

