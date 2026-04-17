# OCR and Image Scan Infrastructure

## Status

Current state: partially shipped runtime lane plus deeper roadmap.  
Silica-X now ships public-media reconnaissance plugins for image OCR/metadata, public post-text intelligence, lightweight video endpoint handling, and heuristic stego triage.  
It is still not shipped as a dedicated default command or wizard phase in `silica-x.py`.
Remaining expansion target: `v9.5` or `v10.0` for deeper packaging/orchestration work.

Source planning note:

* `self-structuring/ocr-n-image/ocr-n-image-scan-infrastructure.txt`

## Goal

Provide an OCR-capable enrichment lane that can extract actionable OSINT signals from local or fetched images and feed those artifacts into existing Silica-X fusion/reporting flows.

Primary objectives:

* Extract raw text from images reliably
* Parse structured artifacts (emails, URLs, usernames, phone patterns)
* Support batch execution
* Integrate with wizard/extension controls
* Preserve output parity (JSON/CLI/CSV/HTML)

## Proposed Plugin Layout

Planned package:

* `plugins/ocr/__init__.py`
* `plugins/ocr/ocr_extractor.py`
* `plugins/ocr/regex_filters.py`
* `plugins/ocr/batch_processor.py`

## Dependency Profile

Runtime candidates:

* `Pillow`
* `pytesseract`
* optional: `langdetect`, `regex`

System dependency:

* Tesseract OCR binary installed on host/container

## Integration Model

Expected integration points:

* Plugin discovery via existing `Signal Forge` (`core/extensions/signal_forge.py`)
* Selector compatibility via existing extension control plane (`auto/manual/hybrid`)
* Wizard integration via current guided orchestration path (`wizard`)
* Artifact rendering via existing output stack (`core/output.py`, `core/artifacts/html_report.py`, CSV companions)

## Data Contract (Proposed)

Per-image result payload:

* `image_path`
* `raw_text`
* `emails`
* `urls`
* `usernames`
* `phones` (optional extension)
* `language` (optional extension)
* `confidence_hint` (optional extension)

Batch payload:

* `image_count`
* `processed_count`
* `failed_count`
* `items[]` (per-image records)
* `summary` (aggregated indicators)

## Performance Notes

Recommended controls:

* batch sizing and bounded concurrency
* optional preprocess pipeline (grayscale/threshold/resize)
* deterministic caching for repeated image targets
* timeout/guardrails per image decode + OCR call

## Security and Safety

Minimum safeguards:

* file type allowlist for local image inputs
* strict path validation/sandbox boundaries for local file ingestion
* size limits to prevent memory pressure
* sanitized rendering in CLI/HTML outputs

## Release Checklist (When Implementing)

1. Add OCR plugin package under `plugins/ocr/`.
2. Register plugin specs with scope metadata.
3. Wire wizard prompts/options for OCR phase selection.
4. Add tests for parser, compatibility rules, and plugin execution.
5. Add output rendering blocks for OCR-specific sections.
6. Update `requirements.txt` and `requirements-dev.txt` as needed.
7. Re-run full smoke suite and refresh documentation snapshots.

## Runtime Plugins Shipped Today

Current runtime plugins:

* `media_intel_core`
* `media_recon_engine`
* `post_signal_intel`
* `stego_signal_probe`

Current runtime scope:

* public image metadata extraction
* optional OCR on public images
* public post-text harvesting and signal extraction
* lightweight video endpoint + thumbnail reconnaissance
* heuristic stego-suspicion scoring

Still pending:

* local batch OCR package
* wizard/media phase controls
* dedicated local image path ingestion UX
* full frame extraction/video CV pipeline
