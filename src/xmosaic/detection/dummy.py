from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from xmosaic.detection.base import Detection


@dataclass(slots=True)
class DummyDetector:
    """Safe detector used for pipeline testing without model weights or adult samples."""

    width_ratio: float = 0.28
    height_ratio: float = 0.28
    confidence: float = 1.0
    name: str = "dummy"

    def detect(self, frame: npt.NDArray[np.uint8], frame_index: int = 0) -> list[Detection]:
        del frame_index
        height, width = frame.shape[:2]
        box_width = max(1, int(width * self.width_ratio))
        box_height = max(1, int(height * self.height_ratio))
        x1 = max(0, (width - box_width) // 2)
        y1 = max(0, (height - box_height) // 2)
        x2 = min(width, x1 + box_width)
        y2 = min(height, y1 + box_height)

        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        return [
            Detection(
                mask=mask,
                confidence=self.confidence,
                label="censor_region",
                bbox=(x1, y1, x2, y2),
            )
        ]

