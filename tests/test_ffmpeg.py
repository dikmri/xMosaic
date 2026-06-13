from __future__ import annotations

from pathlib import Path

from conftest import make_test_video

from xmosaic.ffmpeg import encode_frames, extract_frames, list_frame_files, probe_video


def test_probe_extract_and_encode_round_trip(tmp_path: Path) -> None:
    input_video = tmp_path / "input.mp4"
    output_video = tmp_path / "output.mp4"
    frames_dir = tmp_path / "frames"
    make_test_video(input_video)

    metadata = probe_video(input_video)
    frame_count = extract_frames(input_video, frames_dir)
    encode_frames(frames_dir, input_video, output_video, metadata.fps)
    output_metadata = probe_video(output_video)

    assert metadata.width == 64
    assert metadata.height == 48
    assert frame_count == 4
    assert len(list_frame_files(frames_dir)) == 4
    assert output_video.exists()
    assert output_metadata.width == 64
    assert output_metadata.height == 48
