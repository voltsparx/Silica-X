"""Relationship correlation with explainable evidence traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CorrelationLink:
    """Directed correlation link between two entities."""

    source_entity_id: str
    target_entity_id: str
    reason: str
    evidence_reference: str
    strength_score: float

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-friendly link payload."""

        return {
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "reason": self.reason,
            "evidence_reference": self.evidence_reference,
            "strength_score": round(max(0.0, min(1.0, float(self.strength_score))), 4),
        }


def _first_evidence_id(entity: Mapping[str, Any]) -> str:
    evidence_ids = entity.get("evidence_ids", [])
    if isinstance(evidence_ids, Sequence) and evidence_ids:
        return str(evidence_ids[0])
    return ""


def _extract_domains(entity: Mapping[str, Any]) -> set[str]:
    domains: set[str] = set()
    value = str(entity.get("value", "")).strip().lower()
    entity_type = str(entity.get("entity_type", "")).strip().lower()
    if entity_type == "email" and "@" in value:
        domains.add(value.split("@", maxsplit=1)[1])
    if entity_type in {"domain", "asset"} and "." in value:
        domains.add(value)

    attributes = entity.get("attributes", {})
    if isinstance(attributes, Mapping):
        for key in ("domain", "root_domain", "email_domain", "registrar_domain"):
            raw = str(attributes.get(key, "")).strip().lower()
            if raw:
                domains.add(raw)
    return domains


def _extract_emails(entity: Mapping[str, Any]) -> set[str]:
    emails: set[str] = set()
    value = str(entity.get("value", "")).strip().lower()
    if "@" in value:
        emails.add(value)
    attributes = entity.get("attributes", {})
    if isinstance(attributes, Mapping):
        contacts = attributes.get("contacts", {})
        if isinstance(contacts, Mapping):
            raw_emails = contacts.get("emails", [])
            if isinstance(raw_emails, Sequence):
                for item in raw_emails:
                    token = str(item).strip().lower()
                    if "@" in token:
                        emails.add(token)
    return emails


class CorrelationEngine:
    """Build explainable entity relationships from normalized snapshots."""

    def correlate(self, entities: Sequence[Mapping[str, Any]]) -> list[CorrelationLink]:
        """Generate pairwise links with reasons and strength."""

        links: list[CorrelationLink] = []
        items = list(entities)
        for index, left in enumerate(items):
            left_id = str(left.get("id", "")).strip()
            if not left_id:
                continue
            for right in items[index + 1 :]:
                right_id = str(right.get("id", "")).strip()
                if not right_id or right_id == left_id:
                    continue
                reason, strength = self._link_reason(left, right)
                if strength <= 0.0:
                    continue
                evidence_reference = _first_evidence_id(left) or _first_evidence_id(right)
                links.append(
                    CorrelationLink(
                        source_entity_id=left_id,
                        target_entity_id=right_id,
                        reason=reason,
                        evidence_reference=evidence_reference,
                        strength_score=strength,
                    )
                )
        return links

    def from_relation_map(
        self,
        relation_map: Mapping[str, Sequence[str]],
        entities_by_id: Mapping[str, Mapping[str, Any]],
    ) -> list[CorrelationLink]:
        """Convert relationship-map payloads into structured links."""

        links: list[CorrelationLink] = []
        for source_id, targets in relation_map.items():
            if not isinstance(targets, Sequence):
                continue
            source_entity = entities_by_id.get(source_id, {})
            evidence_reference = _first_evidence_id(source_entity)
            for target_id in targets:
                target_key = str(target_id).strip()
                if not target_key or target_key == source_id:
                    continue
                links.append(
                    CorrelationLink(
                        source_entity_id=str(source_id),
                        target_entity_id=target_key,
                        reason="existing_relationship_map",
                        evidence_reference=evidence_reference,
                        strength_score=0.5,
                    )
                )
        return links

    def _link_reason(self, left: Mapping[str, Any], right: Mapping[str, Any]) -> tuple[str, float]:
        left_value = str(left.get("value", "")).strip().lower()
        right_value = str(right.get("value", "")).strip().lower()
        left_source = str(left.get("source", "")).strip().lower()
        right_source = str(right.get("source", "")).strip().lower()

        if left_value and left_value == right_value:
            return "exact_value_match", 0.9

        left_domains = _extract_domains(left)
        right_domains = _extract_domains(right)
        if left_domains and right_domains and left_domains.intersection(right_domains):
            return "shared_domain", 0.7

        left_emails = _extract_emails(left)
        right_emails = _extract_emails(right)
        if left_emails and right_emails and left_emails.intersection(right_emails):
            return "shared_email", 0.8

        if left_source and left_source == right_source:
            return "shared_source", 0.35

        return "", 0.0

