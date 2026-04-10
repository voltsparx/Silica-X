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

"""Heuristic scoring rules for intelligence enrichment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


RuleEvaluator = Callable[[Mapping[str, Any], Mapping[str, Any]], float]


@dataclass(frozen=True)
class HeuristicRule:
    """Declarative heuristic rule with weighted score contribution."""

    name: str
    description: str
    weight: float
    evaluator: RuleEvaluator

    def apply(self, entity: Mapping[str, Any], context: Mapping[str, Any]) -> float:
        """Return bounded score adjustment for one entity."""

        raw = float(self.evaluator(entity, context))
        bounded = max(0.0, min(1.0, raw))
        return bounded * max(0.0, float(self.weight))


def _cross_platform_presence(entity: Mapping[str, Any], _context: Mapping[str, Any]) -> float:
    if str(entity.get("entity_type", "")).lower() != "profile":
        return 0.0
    attributes = entity.get("attributes", {})
    if not isinstance(attributes, Mapping):
        return 0.0
    platform_count = int(attributes.get("platform_count", 0) or 0)
    if platform_count >= 3:
        return 1.0
    status = str(attributes.get("status", "")).upper()
    return 0.7 if status == "FOUND" else 0.0


def _domain_email_match(entity: Mapping[str, Any], context: Mapping[str, Any]) -> float:
    if str(entity.get("entity_type", "")).lower() != "email":
        return 0.0
    value = str(entity.get("value", "")).strip().lower()
    if "@" not in value:
        return 0.0
    email_domain = value.split("@", maxsplit=1)[1]
    target_domains = context.get("target_domains", ())
    if not isinstance(target_domains, (list, tuple, set)):
        return 0.0
    return 1.0 if email_domain in {str(item).lower() for item in target_domains} else 0.0


def _infrastructure_overlap(entity: Mapping[str, Any], _context: Mapping[str, Any]) -> float:
    entity_type = str(entity.get("entity_type", "")).lower()
    if entity_type not in {"domain", "asset"}:
        return 0.0
    attributes = entity.get("attributes", {})
    if not isinstance(attributes, Mapping):
        return 0.0
    has_asn = bool(attributes.get("asn"))
    has_registrar = bool(attributes.get("registrar"))
    if has_asn and has_registrar:
        return 1.0
    return 0.4 if has_asn or has_registrar else 0.0


def _evidence_density(entity: Mapping[str, Any], context: Mapping[str, Any]) -> float:
    evidence_count = int(context.get("evidence_count", 1) or 1)
    if evidence_count >= 3:
        return 1.0
    if evidence_count == 2:
        return 0.5
    return 0.0


DEFAULT_HEURISTIC_RULES: tuple[HeuristicRule, ...] = (
    HeuristicRule(
        name="cross_platform_presence",
        description="Increase confidence when user appears across multiple platforms.",
        weight=0.15,
        evaluator=_cross_platform_presence,
    ),
    HeuristicRule(
        name="domain_email_match",
        description="Increase confidence when email domain matches scanned target domain.",
        weight=0.1,
        evaluator=_domain_email_match,
    ),
    HeuristicRule(
        name="infrastructure_overlap",
        description="Increase confidence when domain/asset shares infrastructure clues.",
        weight=0.12,
        evaluator=_infrastructure_overlap,
    ),
    HeuristicRule(
        name="evidence_density",
        description="Increase confidence when multiple evidence records support an entity.",
        weight=0.08,
        evaluator=_evidence_density,
    ),
)


class HeuristicEngine:
    """Evaluate all configured heuristic rules against an entity."""

    def __init__(self, rules: tuple[HeuristicRule, ...] = DEFAULT_HEURISTIC_RULES) -> None:
        self.rules = rules

    def evaluate(
        self,
        entity: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> tuple[float, list[dict[str, Any]]]:
        """Return total heuristic bonus and rule-level evidence."""

        applied: list[dict[str, Any]] = []
        total = 0.0
        for rule in self.rules:
            adjustment = rule.apply(entity, context)
            if adjustment <= 0.0:
                continue
            total += adjustment
            applied.append(
                {
                    "rule": rule.name,
                    "description": rule.description,
                    "weight": rule.weight,
                    "adjustment": round(adjustment, 4),
                }
            )
        return min(total, 0.4), applied

