# Changelog

All notable changes to Silica-X are documented in this file.

## Unreleased

## v11.2.0

### Changed

- Aligned the Python package version and runtime metadata with the current Silica-X release state.
- Updated root README package/install guidance and cleaned the top section layout for better rendering.
- Replaced stale hardcoded runtime version strings in user-facing report and HTTP user-agent paths.

### Added

- First-class Docker runtime integration via `--docker` and `--docker-rebuild`.
- Docker runtime manager in `core/setup/docker_runtime.py` for OS detection, install flow, daemon checks, image build checks, and container launch.
- Tor runtime manager in `core/setup/tor_runtime.py` for torrc deployment, readiness checks, and higher-level startup orchestration.
- Docker-aware doctor snapshot output with runtime visibility for Docker binary presence, daemon state, and local image status.
- Docker-aware prompt banner messaging when running inside a container.
- Root Docker guide in `docs/docker.md`.
- Runtime tests for Docker and Tor setup helpers.

### Changed

- `docker/Dockerfile` now builds a full Silica-X runtime image with Tesseract, Tor, nmap, and package installation through the project entrypoint.
- `docker/docker-compose.yml` now exposes `silica-x`, `silica-x-tor`, and `silica-x-full` services for prompt-mode container workflows.

## v11.1-stable

### Added

- Full CLI smoke-tested audit marker for the stable runtime state.
- Expanded platform manifest coverage with `91` validated platform definitions.
- Live pipeline-driven enrichment for profile scans through `PipelineEngine`.
- `LiveEnrichmentSubscriber` for real-time contact and credential signal enrichment during profile scans.
- Persistent cross-session knowledge base in `output/silica_x_kb.db`.
- Doctor snapshot visibility for engine health and knowledge-base status.
- New platform manifest, live enrichment, Docker, and Tor runtime tests.

### Changed

- HTML reporting now includes live enrichment sections when available.
- Profile scanning emits per-platform `RESULT_EMITTED` events for downstream pipeline consumers.
- Profile and surface runs now persist richer operational intelligence into the local knowledge base.
- `doctor --json` remains machine-parseable in non-interactive contexts.

### Verification

- Stable audit baseline completed with `323` passing tests at the time of the `v11.1-stable` marker.
