from __future__ import annotations

import cv2
import numpy as np
import numpy.typing as npt

from xmosaic.config import MosaicPreset, get_preset
from xmosaic.mosaic.mask_ops import dilate_mask, feather_mask


def pixelate_frame(
    frame: npt.NDArray[np.uint8],
    block_size: int,
) -> npt.NDArray[np.uint8]:
    if block_size <= 1:
        return frame.copy()

    height, width = frame.shape[:2]
    small_width = max(1, width // block_size)
    small_height = max(1, height // block_size)
    small = cv2.resize(frame, (small_width, small_height), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)


def apply_mosaic(
    frame: npt.NDArray[np.uint8],
    mask: npt.ArrayLike,
    preset: str | MosaicPreset = "balanced",
    *,
    dilation: int | None = None,
    feather: int | None = None,
    block_size: int | None = None,
) -> npt.NDArray[np.uint8]:
    preset_obj = get_preset(preset) if isinstance(preset, str) else preset
    dilation_value = preset_obj.dilation if dilation is None else dilation
    feather_value = preset_obj.feather if feather is None else feather
    block_value = preset_obj.block_size if block_size is None else block_size

    dilated = dilate_mask(mask, dilation_value)
    alpha = feather_mask(dilated, feather_value)
    alpha_3d = alpha[..., np.newaxis]

    if preset_obj.mode == "solid":
        overlay = np.zeros_like(frame)
        overlay[:, :] = preset_obj.color
    else:
        overlay = pixelate_frame(frame, block_value)

    blended = frame.astype(np.float32) * (1.0 - alpha_3d) + overlay.astype(np.float32) * alpha_3d
    return np.clip(blended, 0, 255).astype(np.uint8)

