from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True, slots=True)
class Detection:
    mask: npt.NDArray[np.uint8]
    confidence: float
    label: str = "censor_region"
    bbox: tuple[int, int, int, int] | None = None


class Detector(Protocol):
    name: str

    def detect(self, frame: npt.NDArray[np.uint8], frame_index: int = 0) -> list[Detection]:
        """Return detections for one BGR frame."""

