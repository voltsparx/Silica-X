# Recon Framework Intel

Silica-X now includes a native reverse-engineering layer for local framework source trees under `temp/`.

Current command surface:

- `python silica-x.py frameworks`
  - Shows which local framework trees were discovered under `temp/`
  - Includes reverse-engineered summaries for `bbot`, `amass`, and the local Metasploit console UI reference tree
- `python silica-x.py frameworks --framework bbot --modules`
  - Lists BBOT modules parsed from the local markdown inventory
- `python silica-x.py frameworks --framework bbot --presets`
  - Lists BBOT presets parsed from `temp/bbot/bbot/presets`
- `python silica-x.py frameworks --framework amass --commands`
  - Shows local Amass command binaries and engine layout
- `python silica-x.py bbot example.com --preset subdomain-enum --dry-run`
  - Builds a BBOT-style translation plan and shows the native Silica-X command it maps to
- `python silica-x.py bbot example.com --preset web-basic`
  - Executes the translated Silica-X surface workflow

What this is:

- A local source-study and translation layer
- A way to understand what BBOT and Amass provide to operators
- A native Silica-X execution bridge for the BBOT presets that overlap with Silica-X surface capabilities

What this is not:

- A full embedded BBOT engine
- A full embedded Amass engine
- One-to-one parity for intrusive modules such as fuzzers, repository miners, screenshots, service fingerprinting, or vulnerability runners

Current BBOT-to-Silica translation focuses on:

- passive, active, and hybrid recon mode selection
- subdomain discovery intent
- web exposure and attack-surface inspection intent
- cloud-facing ownership and exposure enrichment
- analyst-readable execution planning before launch
