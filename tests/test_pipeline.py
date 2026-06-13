from __future__ import annotations

from pathlib import Path

from conftest import make_test_video

from xmosaic.ffmpeg import probe_video
from xmosaic.pipeline import ProcessOptions, process_video


def test_process_video_with_dummy_detector(tmp_path: Path) -> None:
    input_video = tmp_path / "input.mp4"
    output_video = tmp_path / "output.mp4"
    report_path = tmp_path / "report.json"
    make_test_video(input_video)

    result = process_video(
        input_path=input_video,
        output_path=output_video,
        options=ProcessOptions(detector="dummy", preset="balanced", temporal_smoothing=1),
        report_path=report_path,
    )
    metadata = probe_video(output_video)

    assert result.output_path == output_video.resolve()
    assert output_video.exists()
    assert report_path.exists()
    assert metadata.width == 64
    assert metadata.height == 48
    assert result.report.frame_count == 4
