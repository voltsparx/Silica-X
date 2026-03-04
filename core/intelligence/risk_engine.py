"""Risk classification from confidence, entity type, and anomaly context."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any, Mapping


RISK_BANDS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
_RISK_INDEX = {name: index for index, name in enumerate(RISK_BANDS)}


class RiskEngine:
    """Assign and summarize risk levels for intelligence output."""

    _BASE_RISK_BY_ENTITY = {
        "profile": "LOW",
        "domain": "MEDIUM",
        "email": "MEDIUM",
        "asset": "MEDIUM",
        "ip": "HIGH",
    }

    def assess(
        self,
        entity: Mapping[str, Any],
        *,
        confidence_score: float,
        anomaly_reasons: Sequence[str],
    ) -> str:
        """Assign risk level using deterministic policy."""

        reason_text = " ".join(str(item).lower() for item in anomaly_reasons if item)
        if any(token in reason_text for token in ("credential", "leak", "critical")):
            return "CRITICAL"

        entity_type = str(entity.get("entity_type", "profile")).strip().lower()
        base = self._BASE_RISK_BY_ENTITY.get(entity_type, "LOW")
        index = _RISK_INDEX[base]

        bounded_confidence = max(0.0, min(1.0, float(confidence_score)))
        if bounded_confidence >= 0.8:
            index += 1
        if bounded_confidence >= 0.93 and entity_type in {"domain", "asset", "ip"}:
            index += 1
        if anomaly_reasons:
            index += 1

        return RISK_BANDS[max(0, min(index, len(RISK_BANDS) - 1))]

    def summarize(self, levels: Sequence[str]) -> dict[str, int]:
        """Return normalized risk summary counts."""

        counter = Counter(str(item).upper() for item in levels if str(item).strip())
        summary = {level: int(counter.get(level, 0)) for level in RISK_BANDS}
        summary["total"] = sum(summary[level] for level in RISK_BANDS)
        return summary

