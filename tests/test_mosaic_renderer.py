from __future__ import annotations

import numpy as np

from xmosaic.config import MosaicPreset
from xmosaic.mosaic.renderer import apply_mosaic, pixelate_frame


def _gradient_frame(height: int = 48, width: int = 64) -> np.ndarray:
    x = np.tile(np.arange(width, dtype=np.uint8), (height, 1))
    y = np.tile(np.arange(height, dtype=np.uint8)[:, None], (1, width))
    return np.dstack([x, y, (x + y).astype(np.uint8)])


def test_pixelate_frame_preserves_shape() -> None:
    frame = _gradient_frame()

    pixelated = pixelate_frame(frame, block_size=8)

    assert pixelated.shape == frame.shape
    assert pixelated.dtype == frame.dtype


def test_apply_mosaic_changes_masked_region_only_when_no_dilation() -> None:
    frame = _gradient_frame()
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mask[16:32, 20:44] = 255
    preset = MosaicPreset(name="test", block_size=8, dilation=0, feather=0)

    rendered = apply_mosaic(frame, mask, preset=preset)

    assert rendered.shape == frame.shape
    assert np.array_equal(rendered[0:8, 0:8], frame[0:8, 0:8])
    assert not np.array_equal(rendered[16:32, 20:44], frame[16:32, 20:44])


def test_apply_mosaic_supports_solid_mode() -> None:
    frame = _gradient_frame()
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mask[10:20, 10:20] = 255
    preset = MosaicPreset(name="solid", mode="solid", dilation=0, feather=0, color=(0, 0, 0))

    rendered = apply_mosaic(frame, mask, preset=preset)

    assert rendered[15, 15].tolist() == [0, 0, 0]

