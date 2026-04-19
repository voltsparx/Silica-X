# ──────────────────────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silica-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silica-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silica-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────────────────────

# Silica-X Setup

## Requirements

1. Python `>= 3.11` is required.
2. Create and activate a virtual environment before installing dependencies.

## Install

For the full feature set:

```bash
pip install -e ".[full]"
```

For the base framework:

```bash
pip install -e .
```

## Tesseract OCR Binary

Install the native `tesseract` binary so OCR features can run end to end.

Ubuntu / Debian:

```bash
sudo apt-get install -y tesseract-ocr
```

Fedora:

```bash
sudo dnf install -y tesseract
```

Arch:

```bash
sudo pacman -S --noconfirm tesseract
```

macOS:

```bash
brew install tesseract
```

Windows:

Install the Mannheim build:

`https://digi.bib.uni-mannheim.de/tesseract/`

## Amass

Silica-X uses Amass for subdomain harvest workflows.

Go install:

```bash
go install github.com/owasp-amass/amass/v4/...@master
```

Homebrew:

```bash
brew install amass
```

Snap:

```bash
sudo snap install amass
```

Ubuntu / Debian (universe when available):

```bash
sudo apt-get install -y amass
```

## Tor

Ubuntu / Debian:

```bash
sudo apt-get install -y tor
```

macOS:

```bash
brew install tor
```

Windows:

Install the Tor Expert Bundle from the official Tor Project distribution page.

## Optional High-Speed Surface Scanning

For faster active port surface probing, install `masscan` if your environment allows it.

## Verify Installation

Run:

```bash
silica-x doctor --json
```

This reports OCR backends, Tor availability, and related runtime dependencies.

## First Scans

Profile mode:

```bash
silica-x profile johndoe --out-type json,html
```

Surface mode:

```bash
silica-x surface example.com --out-type json,html
```

Fusion mode:

```bash
silica-x fusion johndoe example.com --out-type json,html
```

OCR mode:

```bash
silica-x ocr ./capture.png --out-type json,html
```

Quicktest:

```bash
silica-x quicktest --out-type json
```
