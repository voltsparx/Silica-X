"""Structured intelligence pipeline with evidence traceability."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from core.domain import BaseEntity
from core.intelligence.clustering_engine import ClusteringEngine
from core.intelligence.confidence_model import ConfidenceModel
from core.intelligence.correlation_engine import CorrelationEngine, CorrelationLink
from core.intelligence.evidence import Evidence, evidence_from_entity
from core.intelligence.expansion_engine import ExpansionEngine
from core.intelligence.heuristic_rules import HeuristicEngine
from core.intelligence.risk_engine import RiskEngine


def _confidence_bucket(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _normalize_anomaly_map(anomalies: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    mapped: dict[str, list[str]] = {}
    for anomaly in anomalies:
        entity_id = str(anomaly.get("entity_id", "")).strip()
        if not entity_id:
            continue
        reason = str(anomaly.get("reason", "anomaly")).strip().lower()
        mapped.setdefault(entity_id, []).append(reason)
    return mapped


class IntelligenceEngine:
    """Run evidence, heuristics, correlation, confidence, risk, and clustering stages."""

    def __init__(self) -> None:
        self._heuristics = HeuristicEngine()
        self._correlation = CorrelationEngine()
        self._confidence_model = ConfidenceModel()
        self._risk_engine = RiskEngine()
        self._clustering = ClusteringEngine()
        self._expansion = ExpansionEngine()

    def analyze(
        self,
        entities: Sequence[BaseEntity],
        *,
        mode: str,
        target: str,
        anomalies: Sequence[Mapping[str, Any]] | None = None,
        relation_map: Mapping[str, Sequence[str]] | None = None,
    ) -> dict[str, Any]:
        """Run full intelligence pipeline and return analysis-ready bundle."""

        started_at = datetime.now(tz=timezone.utc)
        mode_name = str(mode or "balanced").strip().lower()
        target_name = str(target or "").strip()

        snapshots: list[dict[str, Any]] = []
        evidence_rows: list[Evidence] = []
        entities_by_id: dict[str, dict[str, Any]] = {}

        trace_prefix = f"{mode_name}:{target_name or 'target'}"
        for entity in entities:
            evidence = evidence_from_entity(entity, trace_prefix=trace_prefix)
            evidence_rows.append(evidence)

            row = entity.as_dict()
            row["attributes"] = dict(entity.attributes)
            row["evidence_ids"] = [evidence.id]
            row["first_seen"] = entity.timestamp.isoformat()
            row["last_updated"] = entity.timestamp.isoformat()
            row["risk_level"] = "LOW"
            row["confidence_breakdown"] = {}
            row["heuristics"] = []
            snapshots.append(row)
            entities_by_id[row["id"]] = row

        links = self._correlation.correlate(snapshots)
        if relation_map:
            links.extend(self._correlation.from_relation_map(relation_map, entities_by_id))
        links = self._dedupe_links(links)

        links_by_source: dict[str, list[CorrelationLink]] = defaultdict(list)
        for link in links:
            links_by_source[link.source_entity_id].append(link)
            links_by_source[link.target_entity_id].append(link)

        anomaly_map = _normalize_anomaly_map(list(anomalies or []))
        target_domains = self._target_domains(target_name)

        confidence_by_entity: dict[str, float] = {}
        risk_levels: list[str] = []
        bucket_counts = {"low": 0, "medium": 0, "high": 0}

        evidence_by_id = {row.id: row for row in evidence_rows}
        for row in snapshots:
            entity_id = str(row.get("id", "")).strip()
            attached_links = links_by_source.get(entity_id, [])
            strengths = [float(link.strength_score) for link in attached_links]

            evidence_ids = row.get("evidence_ids", [])
            evidence_reliability = 0.5
            if isinstance(evidence_ids, Sequence) and evidence_ids:
                evidence = evidence_by_id.get(str(evidence_ids[0]))
                if evidence is not None:
                    evidence_reliability = float(evidence.reliability_score)

            heuristic_bonus, applied_heuristics = self._heuristics.evaluate(
                row,
                {
                    "mode": mode_name,
                    "target_domains": target_domains,
                    "evidence_count": len(evidence_ids) if isinstance(evidence_ids, Sequence) else 1,
                },
            )
            anomaly_reasons = anomaly_map.get(entity_id, [])
            contradiction_penalty = 0.1 if anomaly_reasons else 0.0

            score, breakdown = self._confidence_model.score(
                heuristic_bonus=heuristic_bonus,
                correlation_strengths=strengths,
                evidence_reliability=evidence_reliability,
                contradiction_penalty=contradiction_penalty,
                base_score=float(row.get("confidence", 0.3) or 0.3),
            )

            risk_level = self._risk_engine.assess(
                row,
                confidence_score=score,
                anomaly_reasons=anomaly_reasons,
            )

            row["confidence"] = round(score, 4)
            row["confidence_score"] = round(score, 4)
            row["confidence_breakdown"] = breakdown
            row["heuristics"] = applied_heuristics
            row["risk_level"] = risk_level
            row["relationships"] = [link.target_entity_id for link in attached_links if link.source_entity_id == entity_id]
            confidence_by_entity[entity_id] = score
            risk_levels.append(risk_level)
            bucket_counts[_confidence_bucket(score)] += 1

        snapshots = self._expansion.annotate(
            snapshots,
            target=target_name,
            mode=mode_name,
        )
        clusters = self._clustering.build_clusters(snapshots, links, confidence_by_entity)
        risk_summary = self._risk_engine.summarize(risk_levels)
        finished_at = datetime.now(tz=timezone.utc)

        return {
            "metadata": {
                "scan_mode": mode_name,
                "start_time": started_at.isoformat(),
                "end_time": finished_at.isoformat(),
                "entity_count": len(snapshots),
                "evidence_count": len(evidence_rows),
            },
            "entities": snapshots,
            "evidence": [row.as_dict() for row in evidence_rows],
            "relationships": [link.as_dict() for link in links],
            "clusters": clusters,
            "risk_summary": risk_summary,
            "confidence_distribution": bucket_counts,
            "analysis_ready": True,
        }

    def _target_domains(self, target: str) -> set[str]:
        values: set[str] = set()
        normalized = str(target or "").strip().lower()
        if not normalized:
            return values
        if "@" in normalized:
            values.add(normalized.split("@", maxsplit=1)[1])
        if "." in normalized:
            values.add(normalized)
        return values

    def _dedupe_links(self, links: Sequence[CorrelationLink]) -> list[CorrelationLink]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[CorrelationLink] = []
        for link in links:
            key = (link.source_entity_id, link.target_entity_id, link.reason)
            if key in seen:
                continue
            seen.add(key)
            unique.append(link)
        return unique

