from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FrameIssue:
    frame_index: int
    reason: str
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ProcessReport:
    input_path: str
    output_path: str
    detector: str
    preset: str
    frame_count: int
    low_confidence_frames: list[FrameIssue] = field(default_factory=list)
    temp_dir: str | None = None

    @property
    def low_confidence_count(self) -> int:
        return len(self.low_confidence_frames)


def write_qc_report(path: Path, report: ProcessReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(
            json.dumps(asdict(report), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        return

    rows = "\n".join(
        "<tr>"
        f"<td>{issue.frame_index}</td>"
        f"<td>{html.escape(issue.reason)}</td>"
        f"<td>{'' if issue.confidence is None else f'{issue.confidence:.3f}'}</td>"
        "</tr>"
        for issue in report.low_confidence_frames
    )
    if not rows:
        rows = '<tr><td colspan="3">No low-confidence frames recorded.</td></tr>'

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>xMosaic QC Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.45rem; text-align: left; }}
    th {{ background: #f3f3f3; }}
  </style>
</head>
<body>
  <h1>xMosaic QC Report</h1>
  <p><strong>Input:</strong> {html.escape(report.input_path)}</p>
  <p><strong>Output:</strong> {html.escape(report.output_path)}</p>
  <p><strong>Detector:</strong> {html.escape(report.detector)}</p>
  <p><strong>Preset:</strong> {html.escape(report.preset)}</p>
  <p><strong>Frames:</strong> {report.frame_count}</p>
  <p><strong>Low-confidence frames:</strong> {report.low_confidence_count}</p>
  <table>
    <thead><tr><th>Frame</th><th>Reason</th><th>Confidence</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")

