# Silica-X v9.3.0 "Ember" Update Notes

## Engine Architecture Upgrade

- Added standardized engine result schema:
  - `name`
  - `status` (`success`, `failed`, `timeout`)
  - `data`
  - `error`
  - `execution_time`
- Added shared engine base contract with:
  - hard timeout guard
  - exception isolation boundary
  - health-check surface
- Added runtime engine health monitor:
  - active task tracking
  - average response time
  - engine failure counters

## Orchestration Improvements

- Orchestrator now consumes structured engine results (`run_detailed`) when available.
- Capability stage now records:
  - succeeded count
  - failed count
  - timeout count
- Engine health snapshot is attached into orchestration payload and lifecycle events.

## Mode Alias Support

- Added execution-mode aliases:
  - `safe` -> `fast`
  - `aggressive` -> `max`
  - `standard` -> `balanced`

## Version Marking

- Core metadata version updated to `9.3.0`.
- Top-level docs updated to reflect `v9.3.0`.
