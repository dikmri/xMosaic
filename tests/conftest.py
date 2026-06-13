from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for this test")
    return ffmpeg


def make_test_video(path: Path) -> None:
    ffmpeg = require_ffmpeg()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x48:rate=5",
            "-frames:v",
            "4",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
    )

