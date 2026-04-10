# Recon Intelligence Tranche

This tranche implements the highest-signal items from the self-assessment notes as native Silica-X surface workflow features.

## What Changed

- Added explicit surface recon lanes:
  - `passive`
  - `active`
  - `hybrid`
- Surface presets now carry a default recon lane:
  - `quick` -> `passive`
  - `balanced` -> `hybrid`
  - `deep` -> `hybrid`
  - `max` -> `hybrid`
- Surface and fusion CLI flows now accept recon-mode control for the surface phase.
- Domain scans now emit:
  - `collector_status`
  - `surface_map`
  - `next_steps`
  - `recon_mode`

## Why

The self-assessment notes emphasized:

- reducing cognitive load
- guiding decisions instead of only collecting data
- supporting passive and active reconnaissance deliberately
- improving attack-surface mapping and prioritization

This tranche addresses that by making the surface pipeline explain:

- which collectors ran
- which lane they belong to
- which hosts look most interesting
- what the operator should do next

## Local Framework Inspiration

The implementation was informed by the local study trees under `temp/`:

- `temp/bbot`
  Inspired the lane-oriented, event-style surface mapping mindset.
- `temp/amass`
  Inspired the emphasis on fast attack-surface enumeration and active/passive separation.

No foreign framework code was copied into the runtime path. The result is modeled and implemented as part of Silica-X itself.
