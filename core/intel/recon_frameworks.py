"""Reverse-engineered framework intelligence from local temp/ source trees."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
import re
import shlex

from core.collect.domain_intel import normalize_domain
from core.foundation.recon_modes import normalize_recon_mode

DEFAULT_TEMP_ROOT = Path("temp")
DEFAULT_BBOT_ROOT = DEFAULT_TEMP_ROOT / "bbot"
DEFAULT_AMASS_ROOT = DEFAULT_TEMP_ROOT / "amass"
DEFAULT_METASPLOIT_ROOT = (
    DEFAULT_TEMP_ROOT / "only-ui-architecture" / "metasploit-framework-master" / "metasploit-framework-master"
)

_PIPE_SPLIT_RE = re.compile(r"\s*\|\s*")
_OPTION_RE = re.compile(r"options\.([a-z_]+)")

_BBOT_OPTION_LABELS: dict[str, str] = {
    "allow_deadly": "Allow highly intrusive modules",
    "current_preset": "Show the merged preset before execution",
    "current_preset_full": "Show the full resolved preset/config",
    "dry_run": "Build module plan without executing the scan",
    "install_all_deps": "Install dependencies for all modules",
    "list_flags": "List available module flags",
    "list_module_options": "List module-specific options",
    "list_modules": "List scan and internal modules",
    "list_output_modules": "List output modules",
    "list_presets": "List built-in presets",
    "module_help": "Show help for a specific module",
    "version": "Show BBOT version",
    "yes": "Skip interactive scan confirmation",
}

_BBOT_PRESET_TO_SILICA: dict[str, dict[str, Any]] = {
    "subdomain-enum": {
        "surface_preset": "deep",
        "recon_mode": "passive",
        "include_ct": True,
        "include_rdap": True,
        "coverage": "Passive subdomain expansion and ownership enrichment",
    },
    "fast": {
        "surface_preset": "quick",
        "recon_mode": "passive",
        "include_ct": True,
        "include_rdap": False,
        "coverage": "Fast low-noise discovery against the exact target",
    },
    "cloud-enum": {
        "surface_preset": "balanced",
        "recon_mode": "hybrid",
        "include_ct": True,
        "include_rdap": True,
        "coverage": "Cloud-facing surface discovery with ownership context",
    },
    "tech-detect": {
        "surface_preset": "balanced",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "HTTP-led technology and exposure profiling",
    },
    "web-basic": {
        "surface_preset": "balanced",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "Light web surface inspection",
    },
    "web-thorough": {
        "surface_preset": "deep",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "Deeper active web reconnaissance",
    },
    "web-screenshots": {
        "surface_preset": "balanced",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "Web target validation before analyst follow-up",
    },
    "spider": {
        "surface_preset": "balanced",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "Active HTTP collection with recursive-follow ideas",
    },
    "spider-intense": {
        "surface_preset": "deep",
        "recon_mode": "active",
        "include_ct": False,
        "include_rdap": False,
        "coverage": "Deeper recursive web exploration pattern",
    },
    "baddns-intense": {
        "surface_preset": "deep",
        "recon_mode": "active",
        "include_ct": True,
        "include_rdap": True,
        "coverage": "Higher-effort DNS and exposure verification",
    },
    "kitchen-sink": {
        "surface_preset": "max",
        "recon_mode": "hybrid",
        "include_ct": True,
        "include_rdap": True,
        "coverage": "Maximum mixed-lane attack-surface collection",
    },
}

_BBOT_NATIVE_CAPABILITIES: dict[str, str] = {
    "subdomain-enum": "Subdomain discovery and prioritization",
    "passive": "Passive ownership and discovery mode",
    "active": "Active HTTP and DNS verification mode",
    "cloud-enum": "Cloud-facing asset visibility enrichment",
    "web-basic": "HTTP exposure, redirect, and header profiling",
    "web-thorough": "Deeper active web coverage pattern",
}

_BBOT_PARTIAL_CAPABILITIES: dict[str, str] = {
    "tech-detect": "Technology hints are inferred through HTTP behavior and headers, not full fingerprint stacks",
    "spider": "Recursive web discovery is represented as follow-up guidance, not full crawler parity",
    "web-screenshots": "Silica-X can validate web targets but does not capture screenshots natively",
    "baddns": "DNS takeover-style review is represented as prioritization hints, not dedicated takeover modules",
}

_BBOT_UNSUPPORTED_CAPABILITIES: dict[str, str] = {
    "code-enum": "Repository mining and code-search modules are not native in the surface engine",
    "email-enum": "Dedicated email enumeration is outside the current surface lane",
    "web-paramminer": "Parameter mining/fuzzing is not implemented",
    "portscan": "Port scan and service fingerprint parity is not implemented",
    "service-enum": "Protocol fingerprint modules are not implemented",
    "deadly": "Intrusive vulnerability modules are intentionally not mirrored",
    "aggressive": "High-noise brute-force/fuzz lanes are intentionally not mirrored",
    "download": "File and repository download workflows are not mirrored",
    "iis-shortnames": "Dedicated IIS shortname exploitation checks are not implemented",
}


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _clean_value(value: str) -> str:
    return value.strip().strip("`").strip()


def _parse_markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        parts = [_clean_value(part) for part in _PIPE_SPLIT_RE.split(line.strip("|"))]
        if len(parts) < 2 or parts[0].lower() == "module":
            continue
        rows.append(parts)
    return rows


def _parse_simple_preset(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": path.stem,
        "description": "",
        "include": [],
        "flags": [],
        "modules": [],
        "exclude_modules": [],
        "output_modules": [],
        "config_hints": [],
    }
    section: str | None = None
    list_sections = {"include", "flags", "modules", "exclude_modules", "output_modules"}

    for raw_line in _safe_read(path).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            item = stripped[2:].split("#", maxsplit=1)[0].strip().strip("'\"")
            if item and section in list_sections:
                cast_list = data[section]
                if isinstance(cast_list, list):
                    cast_list.append(item)
            elif item and section == "config":
                hints = data["config_hints"]
                if isinstance(hints, list):
                    hints.append(item)
            continue

        if ":" not in stripped:
            if section == "config":
                hints = data["config_hints"]
                if isinstance(hints, list):
                    hints.append(stripped)
            continue

        key, _, remainder = stripped.partition(":")
        key = key.strip()
        value = remainder.strip().strip("'\"")
        if key == "description":
            data["description"] = value
            section = None
            continue
        if key in list_sections:
            section = key
            if value:
                cast_list = data[key]
                if isinstance(cast_list, list):
                    cast_list.append(value)
            continue
        if key == "config":
            section = "config"
            continue
        if section == "config":
            hints = data["config_hints"]
            if isinstance(hints, list):
                hints.append(stripped)

    return data


def _match_search(text: str, search: str) -> bool:
    query = str(search or "").strip().lower()
    if not query:
        return True
    return query in text.lower()


@lru_cache(maxsize=1)
def load_bbot_reference(root: str | Path = DEFAULT_BBOT_ROOT) -> dict[str, Any]:
    base = Path(root)
    modules_path = base / "docs" / "modules" / "list_of_modules.md"
    presets_dir = base / "bbot" / "presets"
    cli_path = base / "bbot" / "cli.py"

    module_rows: list[dict[str, Any]] = []
    flag_to_modules: dict[str, list[str]] = {}
    for row in _parse_markdown_rows(_safe_read(modules_path)):
        if len(row) < 8:
            continue
        module_flags = [item.strip() for item in row[4].split(",") if item.strip()]
        consumes = [item.strip() for item in row[5].split(",") if item.strip()]
        produces = [item.strip() for item in row[6].split(",") if item.strip()]
        module = {
            "name": row[0],
            "type": row[1],
            "needs_api_key": row[2].lower() == "yes",
            "description": row[3],
            "flags": module_flags,
            "consumes": consumes,
            "produces": produces,
            "author": row[7],
        }
        module_rows.append(module)
        for flag in module_flags:
            flag_to_modules.setdefault(flag, []).append(str(module["name"]))

    presets: list[dict[str, Any]] = []
    if presets_dir.exists():
        for preset_path in sorted(presets_dir.glob("*.yml")):
            presets.append(_parse_simple_preset(preset_path))

    raw_cli = _safe_read(cli_path)
    commands: list[dict[str, str]] = []
    for option in sorted(set(_OPTION_RE.findall(raw_cli))):
        label = _BBOT_OPTION_LABELS.get(option)
        if not label:
            continue
        commands.append({"id": option, "title": label})

    flags: list[dict[str, Any]] = [
        {
            "name": name,
            "count": len(modules),
            "modules": sorted(modules),
        }
        for name, modules in sorted(flag_to_modules.items(), key=lambda item: (-len(item[1]), item[0]))
    ]

    return {
        "framework": "bbot",
        "path": str(base),
        "module_count": len(module_rows),
        "preset_count": len(presets),
        "flag_count": len(flags),
        "architecture": [
            "Event-driven and recursive scan model",
            "Preset-driven scan composition",
            "Module flags for passive/active/safe/aggressive selection",
            "Parallel module execution with queue-based event flow",
        ],
        "commands": commands,
        "modules": module_rows,
        "presets": presets,
        "flags": flags,
    }


@lru_cache(maxsize=1)
def load_amass_reference(root: str | Path = DEFAULT_AMASS_ROOT) -> dict[str, Any]:
    base = Path(root)
    cmd_dir = base / "cmd"
    engine_dir = base / "engine"
    plugin_dir = engine_dir / "plugins"

    commands = []
    if cmd_dir.exists():
        for path in sorted(item for item in cmd_dir.iterdir() if item.is_dir()):
            commands.append(path.name)

    plugin_families = []
    if plugin_dir.exists():
        for path in sorted(item for item in plugin_dir.iterdir() if item.is_dir()):
            plugin_families.append(path.name)

    engine_components = []
    if engine_dir.exists():
        for name in ("api", "dispatcher", "plugins", "pubsub", "registry", "sessions", "types"):
            component = engine_dir / name
            if component.exists():
                engine_components.append(name)

    return {
        "framework": "amass",
        "path": str(base),
        "command_count": len(commands),
        "commands": commands,
        "engine_components": engine_components,
        "plugin_families": plugin_families,
        "architecture": [
            "Attack-surface mapping with open-source and active reconnaissance",
            "Dedicated engine registry, dispatcher, and session subsystems",
            "Separate command binaries for enum, viz, track, assoc, and engine tasks",
            "Plugin families for brute force, scrape, DNS, enrich, and service discovery",
        ],
    }


@lru_cache(maxsize=1)
def load_metasploit_ui_reference(root: str | Path = DEFAULT_METASPLOIT_ROOT) -> dict[str, Any]:
    base = Path(root)
    return {
        "framework": "metasploit-ui",
        "path": str(base),
        "architecture": [
            "Console-first driver and dispatcher shell pattern",
            "Banner, inventory, and prompt-centered operator workflow",
            "Interactive command routing with shell-like session UX",
        ],
    }


def load_temp_framework_inventory(temp_root: str | Path = DEFAULT_TEMP_ROOT) -> dict[str, Any]:
    base = Path(temp_root)
    frameworks: list[dict[str, Any]] = []
    if DEFAULT_BBOT_ROOT.exists():
        bbot = load_bbot_reference()
        frameworks.append(
            {
                "name": "bbot",
                "path": bbot["path"],
                "summary": "Recursive event-driven recon with presets, flags, and large module inventory",
                "module_count": bbot["module_count"],
                "preset_count": bbot["preset_count"],
                "command_count": len(bbot["commands"]),
            }
        )
    if DEFAULT_AMASS_ROOT.exists():
        amass = load_amass_reference()
        frameworks.append(
            {
                "name": "amass",
                "path": amass["path"],
                "summary": "Attack-surface mapping engine with dedicated binaries, registry, and plugin families",
                "command_count": amass["command_count"],
                "engine_component_count": len(amass["engine_components"]),
                "plugin_family_count": len(amass["plugin_families"]),
            }
        )
    if DEFAULT_METASPLOIT_ROOT.exists():
        metasploit = load_metasploit_ui_reference()
        frameworks.append(
            {
                "name": "metasploit-ui",
                "path": metasploit["path"],
                "summary": "Console UX reference for prompt, inventory, and dispatcher-shell interactions",
            }
        )

    generic_dirs: list[dict[str, Any]] = []
    if base.exists():
        known = {"bbot", "amass", "only-ui-architecture"}
        for path in sorted(item for item in base.iterdir() if item.is_dir() and item.name not in known):
            generic_dirs.append({"name": path.name, "path": str(path)})

    return {
        "temp_root": str(base),
        "frameworks": frameworks,
        "other_dirs": generic_dirs,
    }


def _bbot_modules_for_preset(reference: dict[str, Any], preset_name: str) -> list[dict[str, Any]]:
    preset = next((row for row in reference.get("presets", []) if row.get("name") == preset_name), None)
    if not isinstance(preset, dict):
        return []

    requested_names = {str(name) for name in preset.get("modules", []) if str(name).strip()}
    requested_flags = {str(flag) for flag in preset.get("flags", []) if str(flag).strip()}
    modules: list[dict[str, Any]] = []
    for row in reference.get("modules", []):
        if not isinstance(row, dict):
            continue
        row_name = str(row.get("name", "")).strip()
        row_flags = {str(flag) for flag in row.get("flags", []) if str(flag).strip()}
        if row_name in requested_names or requested_flags.intersection(row_flags):
            modules.append(row)
    return modules


def build_bbot_scan_plan(
    *,
    domain: str,
    preset_name: str = "subdomain-enum",
    modules: list[str] | None = None,
    require_flags: list[str] | None = None,
    exclude_flags: list[str] | None = None,
    recon_mode: str | None = None,
) -> dict[str, Any]:
    normalized_domain = normalize_domain(domain)
    if not normalized_domain:
        raise ValueError("Invalid domain for BBOT-style plan.")

    reference = load_bbot_reference()
    preset = next((row for row in reference.get("presets", []) if row.get("name") == preset_name), None)
    if not isinstance(preset, dict):
        raise ValueError(f"Unknown BBOT preset: {preset_name}")

    selected_modules = _bbot_modules_for_preset(reference, preset_name)
    requested_module_names = {str(name).strip() for name in (modules or []) if str(name).strip()}
    required_flag_names = {str(name).strip() for name in (require_flags or []) if str(name).strip()}
    excluded_flag_names = {str(name).strip() for name in (exclude_flags or []) if str(name).strip()}

    if requested_module_names:
        selected_modules = [row for row in selected_modules if str(row.get("name", "")) in requested_module_names]
    if required_flag_names:
        selected_modules = [
            row
            for row in selected_modules
            if required_flag_names.issubset({str(flag) for flag in row.get("flags", [])})
        ]
    if excluded_flag_names:
        selected_modules = [
            row
            for row in selected_modules
            if not excluded_flag_names.intersection({str(flag) for flag in row.get("flags", [])})
        ]

    selected_flags = sorted(
        {
            str(flag)
            for row in selected_modules
            if isinstance(row, dict)
            for flag in row.get("flags", [])
            if str(flag).strip()
        }
    )

    preset_defaults = dict(_BBOT_PRESET_TO_SILICA.get(preset_name, {}))
    resolved_recon_mode = normalize_recon_mode(recon_mode or str(preset_defaults.get("recon_mode", "hybrid")))
    surface_preset = str(preset_defaults.get("surface_preset", "balanced"))
    include_ct = bool(preset_defaults.get("include_ct", True))
    include_rdap = bool(preset_defaults.get("include_rdap", True))

    native_capabilities = [text for flag, text in _BBOT_NATIVE_CAPABILITIES.items() if flag in selected_flags]
    partial_capabilities = [text for flag, text in _BBOT_PARTIAL_CAPABILITIES.items() if flag in selected_flags]
    unsupported_capabilities = [text for flag, text in _BBOT_UNSUPPORTED_CAPABILITIES.items() if flag in selected_flags]
    unsupported_modules = sorted(
        str(row.get("name", ""))
        for row in selected_modules
        if {"deadly", "aggressive", "code-enum", "service-enum", "download", "email-enum"}.intersection(
            {str(flag) for flag in row.get("flags", [])}
        )
    )

    command_parts = [
        "python",
        "silica-x.py",
        "surface",
        normalized_domain,
        "--preset",
        surface_preset,
        "--recon-mode",
        resolved_recon_mode,
    ]
    command_parts.append("--ct" if include_ct else "--no-ct")
    command_parts.append("--rdap" if include_rdap else "--no-rdap")

    command_preview = shlex.join(command_parts)

    return {
        "framework": "bbot",
        "target": normalized_domain,
        "preset": {
            "name": preset_name,
            "description": str(preset.get("description", "")),
            "flags": list(preset.get("flags", [])),
            "includes": list(preset.get("include", [])),
        },
        "selected_module_count": len(selected_modules),
        "selected_flags": selected_flags,
        "selected_modules_preview": [str(row.get("name", "")) for row in selected_modules[:20]],
        "native_capabilities": native_capabilities,
        "partial_capabilities": partial_capabilities,
        "unsupported_capabilities": unsupported_capabilities,
        "unsupported_modules_preview": unsupported_modules[:20],
        "silica_mapping": {
            "surface_preset": surface_preset,
            "recon_mode": resolved_recon_mode,
            "include_ct": include_ct,
            "include_rdap": include_rdap,
            "coverage": str(preset_defaults.get("coverage", "General BBOT-style surface translation")),
        },
        "execution_preview": command_preview,
        "notes": [
            "This is a native Silica-X translation of BBOT preset intent, not a full BBOT engine port.",
            "Supported coverage maps into Silica-X passive/active/hybrid surface collection lanes.",
            "Unsupported BBOT module families remain analyst follow-up areas until dedicated Silica-X engines are added.",
        ],
    }


def filter_bbot_modules(
    *,
    search: str = "",
    limit: int = 25,
) -> list[dict[str, Any]]:
    reference = load_bbot_reference()
    rows: list[dict[str, Any]] = []
    for row in reference.get("modules", []):
        if not isinstance(row, dict):
            continue
        haystack = " ".join(
            [
                str(row.get("name", "")),
                str(row.get("description", "")),
                " ".join(str(item) for item in row.get("flags", [])),
                " ".join(str(item) for item in row.get("produces", [])),
            ]
        )
        if _match_search(haystack, search):
            rows.append(row)
    return rows[: max(1, int(limit))]


def filter_bbot_presets(
    *,
    search: str = "",
    limit: int = 25,
) -> list[dict[str, Any]]:
    reference = load_bbot_reference()
    rows = [
        row
        for row in reference.get("presets", [])
        if isinstance(row, dict)
        and _match_search(
            " ".join(
                [
                    str(row.get("name", "")),
                    str(row.get("description", "")),
                    " ".join(str(item) for item in row.get("flags", [])),
                ]
            ),
            search,
        )
    ]
    return rows[: max(1, int(limit))]


def filter_bbot_flags(
    *,
    search: str = "",
    limit: int = 25,
) -> list[dict[str, Any]]:
    reference = load_bbot_reference()
    rows = [
        row
        for row in reference.get("flags", [])
        if isinstance(row, dict) and _match_search(str(row.get("name", "")), search)
    ]
    return rows[: max(1, int(limit))]
