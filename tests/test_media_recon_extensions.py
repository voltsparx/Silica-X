import unittest
from unittest.mock import patch

from core.collect.media_recon import (
    MediaReconAsset,
    MediaReconResult,
    MediaReconTargets,
    TextFragment,
    TextSignalSummary,
    VideoEndpointObservation,
    extract_media_targets,
)
from plugins.media_recon_engine import run as run_media_recon_plugin
from plugins.post_signal_intel import run as run_post_signal_plugin
from plugins.stego_signal_probe import run as run_stego_probe


def _fake_media_recon_result() -> MediaReconResult:
    return MediaReconResult(
        target="alice",
        targets=MediaReconTargets(
            image_urls=("https://cdn.example.com/post.png",),
            thumbnail_urls=("https://cdn.example.com/reel-thumb.jpg",),
            video_urls=("https://cdn.example.com/reel.mp4",),
            text_fragments=(
                TextFragment(source="instagram", field="bio", text="Alice Mercer shares OSINT notes."),
                TextFragment(source="instagram", field="post_texts", text="Reach me at alice@example.com #osint"),
            ),
        ),
        text_signals=TextSignalSummary(
            fragment_count=2,
            emails=("alice@example.com",),
            urls=(),
            phones=(),
            mentions=("alicemercer",),
            hashtags=("osint",),
            names=("Alice Mercer",),
            keywords=("osint", "notes"),
            target_hit_count=1,
        ),
        image_assets=(
            MediaReconAsset(
                url="https://cdn.example.com/post.png",
                asset_kind="image",
                content_type="image/png",
                size_bytes=4096,
                sha256="abc123",
                width=512,
                height=512,
                metadata={"format": "PNG", "mode": "RGBA", "info_keys": ["comment"]},
                ocr_text="alice@example.com",
                ocr_engine="easyocr",
                extracted_signals={"emails": ["alice@example.com"], "urls": []},
                entropy_score=7.92,
                stego_score=0.84,
                stego_flags=("high_entropy_payload", "png_container_entropy"),
            ),
        ),
        video_assets=(
            VideoEndpointObservation(
                url="https://cdn.example.com/reel.mp4",
                content_type="video/mp4",
                status_code=206,
                size_bytes=140000,
                final_url="https://cdn.example.com/reel.mp4",
                thumbnail_url="https://cdn.example.com/reel-thumb.jpg",
                extracted_signals={"emails": [], "urls": []},
                notes=("Video endpoint validated with a single-byte range request.",),
            ),
        ),
        notes=("Image lane collected public metadata, OCR, and stego-suspicion heuristics only from public assets.",),
    )


class TestMediaReconExtensions(unittest.TestCase):
    def test_extract_media_targets_collects_media_and_text(self):
        rows = [
            {
                "platform": "instagram",
                "bio": "Alice Mercer shares OSINT notes.",
                "post_texts": ["Reach me at alice@example.com #osint"],
                "post_image_urls": ["https://cdn.example.com/post.png"],
                "video_urls": ["https://cdn.example.com/reel.mp4"],
                "reel_thumbnail_urls": ["https://cdn.example.com/reel-thumb.jpg"],
            }
        ]

        targets = extract_media_targets(rows, target="alice")

        self.assertIn("https://cdn.example.com/post.png", targets.image_urls)
        self.assertIn("https://cdn.example.com/reel.mp4", targets.video_urls)
        self.assertEqual(targets.text_fragments[0].field, "bio")
        self.assertEqual(targets.text_fragments[1].field, "post_texts")

    def test_media_recon_plugin_reports_images_video_and_stego(self):
        with patch("plugins.media_recon_engine.resolve_media_recon_payload", return_value=_fake_media_recon_result()):
            payload = run_media_recon_plugin({"target": "alice"})

        self.assertEqual(payload["severity"], "HIGH")
        self.assertIn("video endpoint", payload["summary"])
        self.assertEqual(payload["data"]["image_assets"][0]["ocr_engine"], "easyocr")

    def test_post_signal_plugin_reports_public_text_intelligence(self):
        with patch("plugins.post_signal_intel.resolve_media_recon_payload", return_value=_fake_media_recon_result()):
            payload = run_post_signal_plugin({"target": "alice"})

        self.assertEqual(payload["severity"], "INFO")
        self.assertIn("public text fragment", payload["summary"])
        self.assertEqual(payload["data"]["text_signals"]["emails"], ["alice@example.com"])

    def test_stego_probe_reports_flagged_assets(self):
        with patch("plugins.stego_signal_probe.resolve_media_recon_payload", return_value=_fake_media_recon_result()):
            payload = run_stego_probe({"target": "alice"})

        self.assertEqual(payload["severity"], "HIGH")
        self.assertEqual(len(payload["data"]["flagged_assets"]), 1)
        self.assertIn("heuristic stego indicators", payload["summary"])


if __name__ == "__main__":
    unittest.main()
