# Recon Source Integration

Sylica-X includes a native source-study layer for local recon architecture references under `temp/`.

Current command surface:

- `python sylica-x.py frameworks`
  - Shows which local source profiles were discovered under `temp/`
- `python sylica-x.py frameworks --framework recursive-modules --modules`
  - Lists modules parsed from the recursive-module source profile
- `python sylica-x.py frameworks --framework recursive-modules --presets`
  - Lists recipes parsed from the recursive-module source profile
- `python sylica-x.py frameworks --framework graph-registry --commands`
  - Shows command families and engine layout from the graph-registry source profile
- `python sylica-x.py surface-kit example.com --preset subdomain-enum --dry-run`
  - Builds a source-derived plan and shows the native Sylica-X command it maps to
- `python sylica-x.py surface-kit example.com --preset web-basic`
  - Executes the translated Sylica-X surface workflow

What this is:

- A local source-study and translation layer
- A way to understand what the studied recon architectures provide to operators
- A native Sylica-X execution bridge for the source recipes that overlap with Sylica-X surface capabilities

What this is not:

- A full embedded foreign engine
- One-to-one parity for intrusive modules such as fuzzers, repository miners, screenshots, service fingerprinting, or vulnerability runners

Current surface-kit translation focuses on:

- passive, active, and hybrid recon mode selection
- subdomain discovery intent
- web exposure and attack-surface inspection intent
- cloud-facing ownership and exposure enrichment
- analyst-readable execution planning before launch
