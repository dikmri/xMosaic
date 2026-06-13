from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


class FFmpegError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    path: Path
    duration_seconds: float | None
    fps: float | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    format_name: str | None

    @property
    def resolution(self) -> str:
        if self.width is None or self.height is None:
            return "unknown"
        return f"{self.width}x{self.height}"

    @property
    def duration_label(self) -> str:
        if self.duration_seconds is None:
            return "unknown"
        seconds = int(round(self.duration_seconds))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def fps_label(self) -> str:
        if self.fps is None:
            return "unknown"
        return f"{self.fps:.3f}".rstrip("0").rstrip(".")


def which_ffmpeg(binary: str) -> str | None:
    return shutil.which(binary)


def require_binary(binary: str) -> str:
    path = which_ffmpeg(binary)
    if path is None:
        raise FFmpegError(f"Required executable not found on PATH: {binary}")
    return path


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        command = " ".join(args)
        message = completed.stderr.strip() or completed.stdout.strip()
        raise FFmpegError(f"Command failed ({completed.returncode}): {command}\n{message}")
    return completed


def _parse_fps(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def _parse_float(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def probe_json(path: Path) -> dict[str, Any]:
    ffprobe = require_binary("ffprobe")
    completed = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FFmpegError(f"ffprobe did not return valid JSON for {path}") from exc
    if not isinstance(data, dict):
        raise FFmpegError(f"ffprobe returned unexpected data for {path}")
    return data


def probe_video(path: Path) -> VideoMetadata:
    data = probe_json(path)
    streams = data.get("streams", [])
    if not isinstance(streams, list):
        streams = []
    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        {},
    )
    audio_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        {},
    )
    format_info = data.get("format", {})
    if not isinstance(format_info, dict):
        format_info = {}

    fps = _parse_fps(video_stream.get("avg_frame_rate")) or _parse_fps(
        video_stream.get("r_frame_rate")
    )
    duration = _parse_float(format_info.get("duration")) or _parse_float(
        video_stream.get("duration")
    )

    return VideoMetadata(
        path=path,
        duration_seconds=duration,
        fps=fps,
        width=video_stream.get("width"),
        height=video_stream.get("height"),
        video_codec=video_stream.get("codec_name"),
        audio_codec=audio_stream.get("codec_name"),
        format_name=format_info.get("format_name"),
    )


def extract_frames(input_path: Path, frames_dir: Path) -> int:
    ffmpeg = require_binary("ffmpeg")
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "%08d.png"
    run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            str(pattern),
        ]
    )
    return len(list_frame_files(frames_dir))


def list_frame_files(frames_dir: Path) -> list[Path]:
    return sorted(frames_dir.glob("*.png"))


def encode_frames(
    frames_dir: Path,
    source_video: Path,
    output_path: Path,
    fps: float | None,
) -> None:
    ffmpeg = require_binary("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_rate = fps if fps and fps > 0 else 30.0
    pattern = frames_dir / "%08d.png"

    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        f"{frame_rate:.6f}",
        "-i",
        str(pattern),
        "-i",
        str(source_video),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
    ]

    if output_path.suffix.lower() == ".webm":
        command.extend(["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-c:a", "libopus"])
    else:
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy"])

    command.extend(["-shortest", str(output_path)])
    run_command(command)


def executable_version(binary: str) -> str | None:
    path = which_ffmpeg(binary)
    if path is None:
        return None
    try:
        completed = run_command([path, "-version"])
    except FFmpegError:
        return None
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    return first_line or None

