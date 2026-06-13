from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cv2

from xmosaic.config import get_preset
from xmosaic.detection import Detection, Detector, DummyDetector
from xmosaic.ffmpeg import encode_frames, extract_frames, list_frame_files, probe_video
from xmosaic.mosaic.mask_ops import combine_masks, smooth_masks
from xmosaic.mosaic.renderer import apply_mosaic
from xmosaic.report import ProcessReport, write_qc_report
from xmosaic.report.qc_report import FrameIssue


@dataclass(frozen=True, slots=True)
class ProcessOptions:
    preset: str = "balanced"
    detector: str = "dummy"
    device: str = "auto"
    confidence_threshold: float = 0.25
    mask_dilation: int | None = None
    temporal_smoothing: int = 5
    keep_temp: bool = False


@dataclass(frozen=True, slots=True)
class ProcessResult:
    output_path: Path
    report: ProcessReport


def build_detector(name: str, device: str = "auto") -> Detector:
    del device
    normalized = name.strip().lower()
    if normalized == "dummy":
        return DummyDetector()
    raise ValueError(
        f"Unsupported detector '{name}'. The current MVP supports only 'dummy'."
    )


def _read_frame(path: Path):
    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"Could not read extracted frame: {path}")
    return frame


def _write_frame(path: Path, frame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise RuntimeError(f"Could not write rendered frame: {path}")


def _filter_detections(
    detections: list[Detection],
    threshold: float,
    frame_index: int,
    issues: list[FrameIssue],
) -> list[Detection]:
    if not detections:
        issues.append(FrameIssue(frame_index=frame_index, reason="no detections"))
        return []

    max_confidence = max(detection.confidence for detection in detections)
    if max_confidence < threshold:
        issues.append(
            FrameIssue(
                frame_index=frame_index,
                reason="confidence below threshold",
                confidence=max_confidence,
            )
        )
        return []

    return [detection for detection in detections if detection.confidence >= threshold]


def process_video(
    input_path: Path,
    output_path: Path,
    options: ProcessOptions,
    report_path: Path | None = None,
) -> ProcessResult:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if input_path == output_path:
        raise ValueError("Output path must be different from input path")
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    preset = get_preset(options.preset)
    metadata = probe_video(input_path)
    detector = build_detector(options.detector, options.device)

    temp_dir = Path(tempfile.mkdtemp(prefix="xmosaic-"))
    frames_dir = temp_dir / "frames"
    rendered_dir = temp_dir / "rendered"
    issues: list[FrameIssue] = []

    try:
        frame_count = extract_frames(input_path, frames_dir)
        frame_paths = list_frame_files(frames_dir)
        if frame_count == 0 or not frame_paths:
            raise RuntimeError(f"No frames were extracted from {input_path}")

        masks = []
        for frame_index, frame_path in enumerate(frame_paths):
            frame = _read_frame(frame_path)
            detections = detector.detect(frame, frame_index=frame_index)
            filtered = _filter_detections(
                detections,
                options.confidence_threshold,
                frame_index,
                issues,
            )
            masks.append(combine_masks([detection.mask for detection in filtered], frame.shape[:2]))

        smoothed_masks = smooth_masks(masks, options.temporal_smoothing)
        frame_mask_pairs = zip(frame_paths, smoothed_masks, strict=True)
        for frame_index, (frame_path, mask) in enumerate(frame_mask_pairs):
            frame = _read_frame(frame_path)
            rendered = apply_mosaic(
                frame,
                mask,
                preset=preset,
                dilation=options.mask_dilation,
            )
            _write_frame(rendered_dir / frame_path.name, rendered)
            if mask.max() == 0:
                issues.append(FrameIssue(frame_index=frame_index, reason="empty mask"))

        encode_frames(rendered_dir, input_path, output_path, metadata.fps)

        report = ProcessReport(
            input_path=str(input_path),
            output_path=str(output_path),
            detector=getattr(detector, "name", options.detector),
            preset=options.preset,
            frame_count=frame_count,
            low_confidence_frames=issues,
            temp_dir=str(temp_dir) if options.keep_temp else None,
        )
        if report_path is not None:
            write_qc_report(report_path, report)
        return ProcessResult(output_path=output_path, report=report)
    finally:
        if not options.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)
