"""Reverse-engineering knowledge map helpers for Silica-X."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


DEFAULT_MAP_PATH = Path("reverse-engineering-temp/reverse-engineering-tools-map.txt")


@dataclass(frozen=True)
class ToolInsight:
    """Structured metadata extracted from reverse-engineering study notes."""

    name: str
    bullets: tuple[str, ...]
    github_url: str | None = None


@dataclass(frozen=True)
class ReverseEngineeringMap:
    """Container for parsed tool insights."""

    tools: tuple[ToolInsight, ...]
    source_path: Path


_TOOL_HEADING_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
_URL_RE = re.compile(r"https?://[^\s)]+")


def _extract_url(text: str) -> str | None:
    match = _URL_RE.search(text)
    if not match:
        return None
    return match.group(0).strip()


def load_reverse_engineering_map(path: str | Path = DEFAULT_MAP_PATH) -> ReverseEngineeringMap:
    """Parse the reverse-engineering map text file into structured entries."""

    source_path = Path(path)
    if not source_path.exists():
        return ReverseEngineeringMap(tools=(), source_path=source_path)

    tools: list[ToolInsight] = []
    current_name: str | None = None
    current_bullets: list[str] = []
    current_url: str | None = None

    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_match = _TOOL_HEADING_RE.match(line)
        if heading_match:
            if current_name:
                tools.append(
                    ToolInsight(
                        name=current_name,
                        bullets=tuple(current_bullets),
                        github_url=current_url,
                    )
                )
            current_name = heading_match.group(2).strip()
            current_bullets = []
            current_url = None
            continue

        if current_name is None:
            continue

        if line.startswith("*"):
            bullet = line.lstrip("*").strip()
            url = _extract_url(bullet)
            if url:
                current_url = url
            current_bullets.append(bullet)
            continue

        # Keep plain continuation lines if present under a tool entry.
        url = _extract_url(line)
        if url:
            current_url = url
        current_bullets.append(line)

    if current_name:
        tools.append(
            ToolInsight(
                name=current_name,
                bullets=tuple(current_bullets),
                github_url=current_url,
            )
        )

    return ReverseEngineeringMap(tools=tuple(tools), source_path=source_path)


def map_tools_to_silica_modules(
    mapping: ReverseEngineeringMap,
) -> dict[str, list[str]]:
    """Map external framework strengths to Silica-X module focus areas."""

    module_map: dict[str, list[str]] = {
        "core/scanner.py": [],
        "core/domain_intel.py": [],
        "core/signal_forge.py": [],
        "core/signal_sieve.py": [],
        "core/output.py": [],
        "core/html_report.py": [],
    }

    for tool in mapping.tools:
        lowered = " ".join((tool.name, *tool.bullets)).lower()
        if any(token in lowered for token in ("username", "profile", "account", "sherlock", "maigret")):
            module_map["core/scanner.py"].append(tool.name)
        if any(token in lowered for token in ("domain", "subdomain", "network", "amass", "harvester")):
            module_map["core/domain_intel.py"].append(tool.name)
        if any(token in lowered for token in ("modular", "module", "plugin", "recon-ng", "spiderfoot")):
            module_map["core/signal_forge.py"].append(tool.name)
        if any(token in lowered for token in ("correlation", "workspace", "normalization", "datasploit")):
            module_map["core/signal_sieve.py"].append(tool.name)
        if any(token in lowered for token in ("output", "json", "html", "report", "cli")):
            module_map["core/output.py"].append(tool.name)
            module_map["core/html_report.py"].append(tool.name)

    # De-duplicate while preserving insertion order.
    deduped: dict[str, list[str]] = {}
    for module_name, names in module_map.items():
        seen: set[str] = set()
        ordered: list[str] = []
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        deduped[module_name] = ordered
    return deduped


def recommend_research_focus(workflow: str, mapping: ReverseEngineeringMap) -> list[str]:
    """Return human-readable research recommendations for a workflow area."""

    module_map = map_tools_to_silica_modules(mapping)
    key = workflow.strip().lower()
    if key == "profile":
        targets = module_map.get("core/scanner.py", [])
    elif key == "surface":
        targets = module_map.get("core/domain_intel.py", [])
    elif key == "fusion":
        targets = module_map.get("core/signal_sieve.py", []) + module_map.get("core/output.py", [])
    else:
        targets = []

    if not targets:
        return ["No mapped research target yet."]
    return [f"Study patterns from: {', '.join(targets)}"]
