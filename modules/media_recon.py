# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import aiohttp

    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

try:
    from PIL import Image
    import imagehash

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import piexif

    HAS_EXIF = True
except ImportError:
    HAS_EXIF = False

try:
    import pytesseract

    HAS_OCR = True
except ImportError:
    HAS_OCR = False


@dataclass
class MediaFinding:
    url: str
    media_type: str
    phash: Optional[str] = None
    exif: dict[str, Any] = field(default_factory=dict)
    ocr_text: Optional[str] = None
    gps_coords: Optional[tuple[float, float]] = None
    anomaly_flags: list[str] = field(default_factory=list)
    raw_headers: dict[str, str] = field(default_factory=dict)

    def has_intelligence(self) -> bool:
        return bool(self.exif or self.ocr_text or self.gps_coords or self.phash)


class MediaRecon:
    """
    Fetches and analyses publicly accessible media from confirmed profile URLs.
    Designed to be called after profile scan confirms a profile exists.
    """

    def __init__(self, session: Any = None) -> None:
        self._session = session

    async def analyse_avatar(self, avatar_url: str) -> MediaFinding:
        finding = MediaFinding(url=avatar_url, media_type="avatar")
        if not avatar_url:
            finding.anomaly_flags.append("missing avatar url")
            return finding
        if not HAS_HTTP or not HAS_PIL:
            finding.anomaly_flags.append("missing dependencies: aiohttp or Pillow")
            return finding

        try:
            image_bytes = await self._fetch_bytes(avatar_url)
            img = Image.open(io.BytesIO(image_bytes))
            finding.phash = str(imagehash.phash(img))
            if _is_likely_default_avatar(img):
                finding.anomaly_flags.append("probable default avatar")
        except Exception as exc:
            finding.anomaly_flags.append(f"fetch failed: {exc}")
        return finding

    async def analyse_image(self, image_url: str, run_ocr: bool = True) -> MediaFinding:
        finding = MediaFinding(url=image_url, media_type="image")
        if not image_url:
            finding.anomaly_flags.append("missing image url")
            return finding
        if not HAS_HTTP:
            return finding

        try:
            image_bytes = await self._fetch_bytes(image_url)
            if HAS_PIL:
                img = Image.open(io.BytesIO(image_bytes))
                finding.phash = str(imagehash.phash(img))
            if HAS_EXIF:
                exif_data = _extract_exif(image_bytes)
                finding.exif = exif_data
                if "GPS" in exif_data:
                    finding.gps_coords = _parse_gps(exif_data["GPS"])
                    if finding.gps_coords is not None:
                        finding.anomaly_flags.append("GPS coordinates present in EXIF")
            if run_ocr and HAS_OCR and HAS_PIL:
                img = Image.open(io.BytesIO(image_bytes))
                text = pytesseract.image_to_string(img).strip()
                if len(text) > 10:
                    finding.ocr_text = text
        except Exception as exc:
            finding.anomaly_flags.append(f"analysis error: {exc}")
        return finding

    async def analyse_video_thumb(self, video_url: str) -> MediaFinding:
        finding = MediaFinding(url=video_url, media_type="video_thumb")
        thumb_url = _resolve_thumbnail_url(video_url)
        if not thumb_url:
            finding.anomaly_flags.append("could not resolve thumbnail URL")
            return finding
        return await self.analyse_image(thumb_url, run_ocr=False)

    async def scan_profile_media(
        self,
        profile_url: str,
        avatar_url: Optional[str] = None,
        image_urls: list[str] | None = None,
        video_urls: list[str] | None = None,
    ) -> list[MediaFinding]:
        tasks: list[asyncio.Future[Any] | asyncio.Task[Any] | Any] = []
        if avatar_url:
            tasks.append(self.analyse_avatar(avatar_url))
        for url in image_urls or []:
            tasks.append(self.analyse_image(url))
        for url in video_urls or []:
            tasks.append(self.analyse_video_thumb(url))
        if not tasks:
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [item for item in results if isinstance(item, MediaFinding) and item.has_intelligence()]

    async def _fetch_bytes(self, url: str) -> bytes:
        if self._session:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                return await response.read()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                return await response.read()


def _is_likely_default_avatar(img: Any) -> bool:
    try:
        img_small = img.convert("RGB").resize((16, 16))
        pixels = list(img_small.getdata())
        red_values = [pixel[0] for pixel in pixels]
        spread = max(red_values) - min(red_values)
        return spread < 30
    except Exception:
        return False


def _extract_exif(image_bytes: bytes) -> dict[str, Any]:
    if not HAS_EXIF:
        return {}
    try:
        exif_dict = piexif.load(image_bytes)
        readable: dict[str, Any] = {}
        for ifd in exif_dict:
            if isinstance(exif_dict[ifd], dict):
                for tag, value in exif_dict[ifd].items():
                    tag_name = piexif.TAGS[ifd].get(tag, {}).get("name", str(tag))
                    readable[tag_name] = value
        return readable
    except Exception:
        return {}


def _parse_gps(gps_data: dict) -> Optional[tuple[float, float]]:
    try:
        def to_deg(values: list[tuple[int, int]]) -> float:
            degrees, minutes, seconds = [value[0] / value[1] for value in values]
            return degrees + minutes / 60 + seconds / 3600

        lat = to_deg(gps_data.get("GPSLatitude", [(0, 1), (0, 1), (0, 1)]))
        lon = to_deg(gps_data.get("GPSLongitude", [(0, 1), (0, 1), (0, 1)]))
        if gps_data.get("GPSLatitudeRef") == b"S":
            lat = -lat
        if gps_data.get("GPSLongitudeRef") == b"W":
            lon = -lon
        return (lat, lon)
    except Exception:
        return None


def _resolve_thumbnail_url(video_url: str) -> Optional[str]:
    import re

    yt_match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})", str(video_url or ""))
    if yt_match:
        return f"https://img.youtube.com/vi/{yt_match.group(1)}/maxresdefault.jpg"
    if "tiktok.com" in str(video_url or ""):
        return f"https://www.tiktok.com/oembed?url={video_url}"
    return None
