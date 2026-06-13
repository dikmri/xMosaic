from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np
import numpy.typing as npt


def as_uint8_mask(mask: npt.ArrayLike) -> npt.NDArray[np.uint8]:
    array = np.asarray(mask)
    if array.ndim != 2:
        raise ValueError(f"Mask must be 2D, got shape {array.shape}")
    if array.dtype == np.bool_:
        return (array.astype(np.uint8) * 255).copy()
    if np.issubdtype(array.dtype, np.floating):
        if array.size and float(np.nanmax(array)) <= 1.0:
            array = array * 255.0
        return np.clip(array, 0, 255).astype(np.uint8)
    return np.clip(array, 0, 255).astype(np.uint8)


def dilate_mask(mask: npt.ArrayLike, pixels: int) -> npt.NDArray[np.uint8]:
    mask_u8 = as_uint8_mask(mask)
    if pixels <= 0:
        return mask_u8
    kernel_size = pixels * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.dilate(mask_u8, kernel)


def feather_mask(mask: npt.ArrayLike, pixels: int) -> npt.NDArray[np.float32]:
    mask_u8 = as_uint8_mask(mask)
    if pixels <= 0:
        return (mask_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)
    kernel_size = pixels * 2 + 1
    if kernel_size % 2 == 0:
        kernel_size += 1
    blurred = cv2.GaussianBlur(mask_u8, (kernel_size, kernel_size), sigmaX=0)
    return (blurred.astype(np.float32) / 255.0).clip(0.0, 1.0)


def combine_masks(
    masks: Sequence[npt.ArrayLike],
    shape: tuple[int, int],
) -> npt.NDArray[np.uint8]:
    combined = np.zeros(shape, dtype=np.uint8)
    for mask in masks:
        mask_u8 = as_uint8_mask(mask)
        if mask_u8.shape != shape:
            mask_u8 = cv2.resize(mask_u8, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
        combined = np.maximum(combined, mask_u8)
    return combined


def smooth_masks(
    masks: Sequence[npt.ArrayLike],
    window: int,
    threshold: float = 0.5,
) -> list[npt.NDArray[np.uint8]]:
    if window <= 1 or len(masks) <= 1:
        return [as_uint8_mask(mask) for mask in masks]

    mask_stack = np.stack([as_uint8_mask(mask).astype(np.float32) / 255.0 for mask in masks])
    radius = max(0, window // 2)
    smoothed: list[npt.NDArray[np.uint8]] = []
    for index in range(len(mask_stack)):
        start = max(0, index - radius)
        end = min(len(mask_stack), index + radius + 1)
        averaged = mask_stack[start:end].mean(axis=0)
        smoothed.append((averaged >= threshold).astype(np.uint8) * 255)
    return smoothed

