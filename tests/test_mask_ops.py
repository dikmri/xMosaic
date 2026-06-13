from __future__ import annotations

import numpy as np

from xmosaic.mosaic.mask_ops import as_uint8_mask, dilate_mask, feather_mask, smooth_masks


def test_as_uint8_mask_converts_bool_mask() -> None:
    mask = np.array([[False, True]], dtype=bool)

    converted = as_uint8_mask(mask)

    assert converted.dtype == np.uint8
    assert converted.tolist() == [[0, 255]]


def test_dilate_mask_grows_region() -> None:
    mask = np.zeros((9, 9), dtype=np.uint8)
    mask[4, 4] = 255

    dilated = dilate_mask(mask, pixels=2)

    assert dilated.sum() > mask.sum()
    assert dilated[4, 4] == 255


def test_feather_mask_returns_alpha() -> None:
    mask = np.zeros((15, 15), dtype=np.uint8)
    mask[5:10, 5:10] = 255

    alpha = feather_mask(mask, pixels=2)

    assert alpha.dtype == np.float32
    assert alpha.min() >= 0.0
    assert alpha.max() <= 1.0


def test_smooth_masks_fills_short_gap() -> None:
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[2, 2] = 255
    empty = np.zeros_like(mask)

    smoothed = smooth_masks([mask, empty, mask], window=3)

    assert smoothed[1][2, 2] == 255

