from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from xmosaic.ffmpeg import probe_video
from xmosaic.pipeline import ProcessOptions, process_video


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def inspect_video(input_path: Path) -> int:
    metadata = probe_video(input_path)
    emit(
        {
            "type": "result",
            "metadata": {
                "path": str(metadata.path),
                "durationSeconds": metadata.duration_seconds,
                "durationLabel": metadata.duration_label,
                "fps": metadata.fps,
                "fpsLabel": metadata.fps_label,
                "width": metadata.width,
                "height": metadata.height,
                "resolution": metadata.resolution,
                "videoCodec": metadata.video_codec,
                "audioCodec": metadata.audio_codec,
                "formatName": metadata.format_name,
            },
        }
    )
    return 0


def run_process(args: argparse.Namespace) -> int:
    def progress(stage: str, completed: int | None, total: int | None, message: str) -> None:
        emit(
            {
                "type": "progress",
                "stage": stage,
                "completed": completed,
                "total": total,
                "message": message,
            }
        )

    report_path = Path(args.report) if args.report else None
    result = process_video(
        input_path=Path(args.input),
        output_path=Path(args.output),
        options=ProcessOptions(
            preset=args.preset,
            detector=args.detector,
            device=args.device,
            confidence_threshold=args.confidence_threshold,
            mask_dilation=args.mask_dilation,
            temporal_smoothing=args.temporal_smoothing,
            keep_temp=args.keep_temp,
        ),
        report_path=report_path,
        progress_callback=progress,
    )
    emit(
        {
            "type": "result",
            "outputPath": str(result.output_path),
            "report": asdict(result.report),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xmosaic-electrobun-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("input")

    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("--input", required=True)
    process_parser.add_argument("--output", required=True)
    process_parser.add_argument("--preset", default="balanced")
    process_parser.add_argument("--detector", default="dummy")
    process_parser.add_argument("--device", default="auto")
    process_parser.add_argument("--confidence-threshold", type=float, default=0.25)
    process_parser.add_argument("--mask-dilation", type=int, default=20)
    process_parser.add_argument("--temporal-smoothing", type=int, default=5)
    process_parser.add_argument("--report")
    process_parser.add_argument("--keep-temp", action="store_true")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            return inspect_video(Path(args.input))
        if args.command == "process":
            return run_process(args)
    except Exception as exc:  # noqa: BLE001
        emit({"type": "error", "message": str(exc)})
        return 1
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

