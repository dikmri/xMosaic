from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from xmosaic.detection.onnx_backend import available_execution_providers
from xmosaic.ffmpeg import executable_version, which_ffmpeg


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class DoctorReport:
    checks: list[Check]

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)


def _torch_device_checks() -> tuple[Check, Check]:
    try:
        import torch
    except ImportError:
        return (
            Check("CUDA", "warn", "torch not installed"),
            Check("MPS", "warn", "torch not installed"),
        )

    cuda_status = "ok" if torch.cuda.is_available() else "warn"
    cuda_detail = "available" if torch.cuda.is_available() else "not available"

    mps_backend = getattr(torch.backends, "mps", None)
    mps_available = bool(mps_backend and mps_backend.is_available())
    mps_status = "ok" if mps_available else "warn"
    mps_detail = "available" if mps_available else "not available"
    return Check("CUDA", cuda_status, cuda_detail), Check("MPS", mps_status, mps_detail)


def collect_doctor_report(cwd: Path | None = None) -> DoctorReport:
    cwd = Path.cwd() if cwd is None else cwd
    checks: list[Check] = []

    python_ok = sys.version_info >= (3, 11)
    checks.append(
        Check(
            "Python",
            "ok" if python_ok else "fail",
            f"{platform.python_version()} at {sys.executable}",
        )
    )

    for binary in ("ffmpeg", "ffprobe"):
        path = which_ffmpeg(binary)
        if path is None:
            checks.append(Check(binary, "fail", "not found on PATH"))
        else:
            checks.append(Check(binary, "ok", executable_version(binary) or path))

    checks.extend(_torch_device_checks())

    providers = available_execution_providers()
    checks.append(
        Check(
            "ONNX Runtime",
            "ok" if providers else "warn",
            ", ".join(providers) if providers else "onnxruntime not installed",
        )
    )

    disk = shutil.disk_usage(cwd)
    free_gb = disk.free / (1024**3)
    checks.append(Check("Disk", "ok" if free_gb >= 1 else "warn", f"{free_gb:.1f} GiB free"))

    try:
        test_path = cwd / ".xmosaic-write-test"
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink()
        checks.append(Check("Write permission", "ok", str(cwd)))
    except OSError as exc:
        checks.append(Check("Write permission", "fail", str(exc)))

    checks.append(Check("Model files", "warn", "not configured; DummyDetector is available"))
    return DoctorReport(checks=checks)

