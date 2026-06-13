from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from xmosaic import SAFETY_NOTICE, __version__
from xmosaic.config import PRESETS
from xmosaic.ffmpeg import FFmpegError, probe_video
from xmosaic.utils.system import collect_doctor_report

console = Console()

app = typer.Typer(
    name="xmosaic",
    add_completion=False,
    no_args_is_help=True,
    help=(
        "Local video mosaic CLI. Intended only for adult, consensual, "
        "rights-cleared material. No de-censorship or cloud upload."
    ),
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"xMosaic {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the xMosaic version and exit.",
        ),
    ] = False,
) -> None:
    del version


@app.command()
def doctor() -> None:
    """Check local dependencies and execution environment."""
    report = collect_doctor_report()
    table = Table(title="xMosaic doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in report.checks:
        style = {"ok": "green", "warn": "yellow", "fail": "red"}.get(check.status, "")
        status = f"[{style}]{check.status}[/{style}]" if style else check.status
        table.add_row(check.name, status, check.detail)
    console.print(table)
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def inspect(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Input video path.",
        ),
    ],
) -> None:
    """Print video metadata from ffprobe."""
    try:
        metadata = probe_video(input_path)
    except FFmpegError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"file: {metadata.path}")
    console.print(f"duration: {metadata.duration_label}")
    console.print(f"fps: {metadata.fps_label}")
    console.print(f"resolution: {metadata.resolution}")
    console.print(f"audio: {metadata.audio_codec or 'none'}")
    console.print(f"video: {metadata.video_codec or 'unknown'}")


@app.command()
def process(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Input video path.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", dir_okay=False, help="Output video path."),
    ],
    preset: Annotated[
        str,
        typer.Option(help=f"Mosaic preset: {', '.join(sorted(PRESETS))}."),
    ] = "balanced",
    detector: Annotated[
        str,
        typer.Option(help="Detector backend. The current MVP supports only 'dummy'."),
    ] = "dummy",
    device: Annotated[
        str,
        typer.Option(help="Execution device hint: auto, cpu, cuda, or mps."),
    ] = "auto",
    confidence_threshold: Annotated[
        float,
        typer.Option("--confidence-threshold", min=0.0, max=1.0, help="Detection threshold."),
    ] = 0.25,
    mask_dilation: Annotated[
        int | None,
        typer.Option("--mask-dilation", min=0, help="Override preset mask dilation in pixels."),
    ] = None,
    temporal_smoothing: Annotated[
        int,
        typer.Option("--temporal-smoothing", min=1, help="Temporal smoothing window."),
    ] = 5,
    report: Annotated[
        Path | None,
        typer.Option("--report", dir_okay=False, help="Optional QC report path (.html or .json)."),
    ] = None,
    keep_temp: Annotated[
        bool,
        typer.Option("--keep-temp/--cleanup-temp", help="Keep temporary extracted frames."),
    ] = False,
) -> None:
    """Apply mosaic processing to a video."""
    from xmosaic.pipeline import ProcessOptions, process_video

    console.print(f"[yellow]Safety:[/yellow] {SAFETY_NOTICE}")
    try:
        result = process_video(
            input_path=input_path,
            output_path=output_path,
            options=ProcessOptions(
                preset=preset,
                detector=detector,
                device=device,
                confidence_threshold=confidence_threshold,
                mask_dilation=mask_dilation,
                temporal_smoothing=temporal_smoothing,
                keep_temp=keep_temp,
            ),
            report_path=report,
        )
    except (FFmpegError, OSError, RuntimeError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"Wrote: {result.output_path}")
    console.print(f"Frames: {result.report.frame_count}")
    console.print(f"QC issues: {result.report.low_confidence_count}")
    if report is not None:
        console.print(f"Report: {report}")


def _not_implemented(command: str) -> None:
    console.print(f"{command} is planned for a later phase.")
    raise typer.Exit(code=2)


@app.command("download-models")
def download_models() -> None:
    """Placeholder for future model download support."""
    _not_implemented("download-models")


@app.command()
def benchmark() -> None:
    """Placeholder for future benchmark support."""
    _not_implemented("benchmark")


@app.command("synth-dataset")
def synth_dataset() -> None:
    """Placeholder for future synthetic dataset conversion support."""
    _not_implemented("synth-dataset")


@app.command()
def train() -> None:
    """Placeholder for future training support."""
    _not_implemented("train")


@app.command("export-onnx")
def export_onnx() -> None:
    """Placeholder for future ONNX export support."""
    _not_implemented("export-onnx")


def main() -> None:
    app()
