from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MosaicMode = Literal["pixel", "solid"]


@dataclass(frozen=True, slots=True)
class MosaicPreset:
    name: str
    mode: MosaicMode = "pixel"
    block_size: int = 24
    dilation: int = 20
    feather: int = 3
    color: tuple[int, int, int] = (0, 0, 0)


PRESETS: dict[str, MosaicPreset] = {
    "light": MosaicPreset(name="light", block_size=12, dilation=12, feather=2),
    "balanced": MosaicPreset(name="balanced", block_size=24, dilation=20, feather=3),
    "fanza-strong": MosaicPreset(name="fanza-strong", block_size=36, dilation=32, feather=4),
    "black-box": MosaicPreset(
        name="black-box",
        mode="solid",
        block_size=1,
        dilation=24,
        feather=0,
        color=(0, 0, 0),
    ),
}


def get_preset(name: str) -> MosaicPreset:
    try:
        return PRESETS[name]
    except KeyError as exc:
        choices = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {choices}") from exc

