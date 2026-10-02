"""Execute the real C++ decoder and lifecycle coordinator, with generated fixtures."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import random
import shlex
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native-artwork"


class NativeArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.driver = Path(cls.tmp.name) / "artwork-test"
        compiler = os.environ.get("CXX", "c++")
        if not shutil.which(compiler):
            raise RuntimeError("A C++17 compiler is required; native tests must not silently skip")
        command = [compiler, *shlex.split(os.environ.get("CXXFLAGS", "")), "-std=c++17", "-O1", "-g", "-pthread", "-Wall", "-Wextra", "-I", str(NATIVE), str(NATIVE / "Artwork.cpp"), str(NATIVE / "tests/driver.cpp"), "-o", str(cls.driver)]
        subprocess.run(command, check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_image(self, data, width=16, height=16):
        path = Path(self.tmp.name) / "input.image"
        path.write_bytes(data)
        result = subprocess.run([str(self.driver), str(path), str(width), str(height)], check=True, capture_output=True, text=True, timeout=10)
        self.assertLessEqual(len(result.stdout), 16000)
        return json.loads(result.stdout)

    @staticmethod
    def encoded(image, fmt="PNG", **opts):
        stream = io.BytesIO()
        image.save(stream, format=fmt, **opts)
        return stream.getvalue()

    def test_lifecycle_and_http_stream_boundaries(self):
        result = subprocess.run([str(self.driver), "--self-test"], check=True, capture_output=True, text=True)
        self.assertIn("passed", result.stdout)

    def test_solid_color_and_both_requested_sizes(self):
        image = self.encoded(Image.new("RGB", (640, 640), (35, 180, 90)))
        for size in (10, 16):
            with self.subTest(size=size):
                result = self.run_image(image, size, size)
                self.assertEqual(result["error"], "ok")
                self.assertEqual(result["pixels"], [0x23B45A] * (size * size))
                self.assertLessEqual(result["decoder_peak_bytes"], 6 * 1024 * 1024)

    def test_progressive_and_baseline_jpeg(self):
        for progressive in (False, True):
            result = self.run_image(self.encoded(Image.new("RGB", (640, 640), (140, 80, 200)), "JPEG", progressive=progressive))
            self.assertEqual(result["error"], "ok")
            for channel, target in zip(((result["pixels"][0] >> s) & 255 for s in (16, 8, 0)), (140, 80, 200)):
                self.assertLessEqual(abs(channel - target), 3)

    def test_center_crop_does_not_stretch_or_keep_side_borders(self):
        image = Image.new("RGB", (48, 16), (255, 0, 0))
        image.paste((0, 255, 0), (16, 0, 32, 16))
        result = self.run_image(self.encoded(image))
        self.assertEqual(result["pixels"], [0x00FF00] * 256)

    def test_area_resampling_avoids_checkerboard_aliasing(self):
        image = Image.new("RGB", (64, 64))
        image.putdata([(255, 255, 255) if (x+y) % 2 else (0, 0, 0) for y in range(64) for x in range(64)])
        result = self.run_image(self.encoded(image))
        self.assertEqual(result["pixels"], [0x808080] * 256)

    def test_alpha_is_composited_over_black(self):
        result = self.run_image(self.encoded(Image.new("RGBA", (16, 16), (200, 100, 50, 128))))
        self.assertEqual(result["pixels"], [0x643219] * 256)

    def test_palette_grayscale_small_and_non_square_output(self):
        for image in (Image.new("P", (32, 32)), Image.new("L", (8, 8), 77), Image.new("RGB", (1, 1), (3, 4, 5))):
            result = self.run_image(self.encoded(image), 10, 16)
            self.assertEqual(result["error"], "ok")
            self.assertEqual(len(result["pixels"]), 160)
            self.assertTrue(all(0 <= value <= 0xFFFFFF for value in result["pixels"]))

    def test_reject_invalid_sizes_and_bounded_source_dimensions(self):
        image = self.encoded(Image.new("RGB", (16, 16)))
        for width, height in ((0, 16), (16, 0), (33, 16), (16, 33), (65535, 65535)):
            self.assertEqual(self.run_image(image, width, height)["error"], "bad_size")
        for dims in ((1025, 1025), (2048, 1024)):
            self.assertEqual(self.run_image(self.encoded(Image.new("RGB", dims)))["error"], "too_large")

    def test_reject_huge_png_header_without_allocating_pixels(self):
        image = bytearray(self.encoded(Image.new("RGB", (16, 16))))
        image[16:24] = struct.pack(">II", 200000, 200000)
        image[29:33] = struct.pack(">I", zlib.crc32(image[12:29]))
        result = self.run_image(image)
        self.assertNotEqual(result["error"], "ok")
        self.assertNotIn("pixels", result)

    def test_allocation_budget_failure_is_clean_and_identified(self):
        # Valid RGB PNG, small encoded body but decoder temporaries exceed the
        # resident budget. Never allocate first and reject afterward.
        image = self.encoded(Image.new("RGB", (1024, 1024), (20, 60, 90)))
        result = self.run_image(image)
        self.assertEqual(result["error"], "no_memory")
        self.assertNotIn("pixels", result)
        self.assertLessEqual(result["decoder_peak_bytes"], 6 * 1024 * 1024)

    def test_reject_oversized_unsupported_and_truncated_input(self):
        self.assertEqual(self.run_image(b"x" * (1024 * 1024 + 1))["error"], "too_large")
        self.assertEqual(self.run_image(b"GIF89a00")["error"], "unsupported")
        image = self.encoded(Image.new("RGB", (64, 64), (10, 20, 30)))
        for data in (b"", image[:7], image[:33], image[:50]):
            self.assertNotEqual(self.run_image(data)["error"], "ok")

    def test_malformed_fuzz_inputs_do_not_crash_or_exceed_decoder_budget(self):
        rng = random.Random(22046)
        valid = self.encoded(Image.new("RGB", (32, 32), (10, 20, 30)))
        for i in range(40):
            data = bytearray(valid if i % 2 else b"\xff\xd8" + rng.randbytes(150))
            for _ in range(3):
                data[rng.randrange(len(data))] ^= rng.randrange(1, 256)
            result = self.run_image(data)
            self.assertLessEqual(result["decoder_peak_bytes"], 6 * 1024 * 1024)
            if result["error"] == "ok":
                self.assertEqual(len(result["pixels"]), 256)

    def test_decoder_provenance(self):
        provenance = json.loads((NATIVE / "vendor/provenance.json").read_text())
        self.assertEqual(provenance["commit"], "2c980bb59875b0d32144a71867fbdebb2f77cd20")
        for name, expected in provenance["files"].items():
            path = NATIVE / "vendor" / ("LICENSE-stb.txt" if name == "LICENSE" else name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
