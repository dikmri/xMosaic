from __future__ import annotations

import numpy as np

from xmosaic.detection import DummyDetector


def test_dummy_detector_returns_center_mask() -> None:
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    detector = DummyDetector(width_ratio=0.2, height_ratio=0.4)

    detections = detector.detect(frame)

    assert len(detections) == 1
    detection = detections[0]
    assert detection.confidence == 1.0
    assert detection.mask.shape == (100, 200)
    assert detection.mask.sum() > 0
    assert detection.bbox == (80, 30, 120, 70)

