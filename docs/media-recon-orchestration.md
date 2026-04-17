# Media Recon Orchestration

## Current Runtime Coverage

Silica-X now ships a dedicated public-media reconnaissance lane through runtime plugins:

* `media_recon_engine`
* `post_signal_intel`
* `stego_signal_probe`
* `media_intel_core` (legacy OCR/metadata-focused image lane)

These plugins run through the existing extension system and can be attached to `profile` and `fusion` workflows.
The core staged runtime now lives in `core/engines/media_recon_engine.py`.

## What The Runtime Lane Does Today

Current public-media coverage includes:

* image URL harvesting from discovered profile rows
* thumbnail harvesting linked to public video/reel endpoints
* video endpoint reconnaissance using headers/range validation
* visual frame profiling from thumbnails/images
* optional small-video frame sampling when local decode support is available
* OCR on public images when optional OCR dependencies are installed
* post/profile text harvesting from public fields such as bios, captions, descriptions, and post-like text arrays
* structured text intelligence extraction for emails, URLs, phone hints, mentions, hashtags, and repeated keywords
* lightweight stego-suspicion heuristics for public image assets
* cross-media fusion summaries with host distribution, signal totals, and stage health

## What It Does Not Yet Do

The current lane does not yet provide:

* deep computer-vision tagging pipelines
* local batch image ingestion commands
* dedicated wizard phases for media-specific orchestration
* strong steganography detection guarantees

Stego scoring is heuristic-only and should be treated as triage guidance, not proof of hidden payloads.
Video frame sampling is best-effort and depends on local decoder availability.

## Suggested Usage

```bash
silica-x profile alice \
  --plugin media_recon_engine \
  --plugin post_signal_intel \
  --plugin stego_signal_probe \
  --html
```

```bash
silica-x fusion alice example.com \
  --plugin media_recon_engine \
  --plugin post_signal_intel \
  --plugin stego_signal_probe \
  --filter signal_lane_fusion \
  --html
```

## Design Direction

The broader roadmap described in `self-assessment/Silica-X-media-intel.txt` still applies.
The current runtime implementation is the first production lane:

* public image + thumbnail reconnaissance
* public post-text intelligence
* lightweight video endpoint handling
* heuristic stego triage

Future expansion can build on this lane for frame extraction, visual tagging, and deeper media orchestration.
