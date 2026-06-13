from __future__ import annotations


class YOLOSegDetector:
    """Placeholder for the optional YOLO segmentation backend."""

    name = "yolo-seg"

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError(
            "YOLOSegDetector is planned for a later phase. Install xMosaic with "
            "'xmosaic[ai]' once the backend is implemented."
        )

