import asyncio
import unittest
from unittest.mock import patch

from core.collect.media_recon import MediaFrameObservation, MediaReconAsset, VideoEndpointObservation
from core.engines.media_recon_engine import MediaReconEngine


class TestMediaReconEngineRuntime(unittest.TestCase):
    def test_media_recon_engine_returns_coverage_and_frames(self):
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

        async def fake_image_asset(*args, **kwargs):
            return MediaReconAsset(
                url="https://cdn.example.com/post.png",
                asset_kind="image",
                content_type="image/png",
                size_bytes=4096,
                sha256="abc123",
                width=512,
                height=512,
                metadata={"format": "PNG"},
                ocr_text="alice@example.com",
                ocr_engine="easyocr",
                extracted_signals={"emails": ["alice@example.com"], "urls": []},
                entropy_score=7.88,
                stego_score=0.82,
                stego_flags=("high_entropy_payload",),
            )

        async def fake_video_asset(*args, **kwargs):
            return VideoEndpointObservation(
                url="https://cdn.example.com/reel.mp4",
                content_type="video/mp4",
                status_code=206,
                size_bytes=2048,
                final_url="https://cdn.example.com/reel.mp4",
                thumbnail_url="https://cdn.example.com/reel-thumb.jpg",
                extracted_signals={"emails": [], "urls": []},
                notes=("Thumbnail URL was linked for visual follow-up.",),
            )

        async def fake_frame(*args, **kwargs):
            return MediaFrameObservation(
                source_url="https://cdn.example.com/reel-thumb.jpg",
                origin_kind="video_thumbnail",
                frame_label="preview",
                width=1280,
                height=720,
                brightness_mean=122.0,
                contrast_score=48.0,
                ocr_excerpt="alice@example.com",
                tags=("landscape", "ocr_present"),
            )

        with (
            patch("core.engines.media_recon_engine._fetch_image_asset", side_effect=fake_image_asset),
            patch("core.engines.media_recon_engine._fetch_video_endpoint", side_effect=fake_video_asset),
            patch("core.engines.media_recon_engine._fetch_frame_source", side_effect=fake_frame),
            patch("core.engines.media_recon_engine._fetch_video_frames", return_value=([], None)),
        ):
            result = asyncio.run(MediaReconEngine().run_media_recon(rows, target="alice"))

        self.assertEqual(result.coverage.image_assets, 2)
        self.assertEqual(result.coverage.video_assets, 1)
        self.assertGreaterEqual(result.coverage.frame_observations, 1)
        self.assertIn("cross_media_email_overlap", result.fusion_summary.notable_patterns)
        self.assertTrue(result.engine_results)


if __name__ == "__main__":
    unittest.main()
