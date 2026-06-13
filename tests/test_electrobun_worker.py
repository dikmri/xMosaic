from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import make_test_video


def test_electrobun_worker_inspect_outputs_json(tmp_path: Path) -> None:
    input_video = tmp_path / "input.mp4"
    make_test_video(input_video)

    completed = subprocess.run(
        [sys.executable, "-m", "xmosaic.electrobun_worker", "inspect", str(input_video)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["type"] == "result"
    assert payload["metadata"]["resolution"] == "64x48"

