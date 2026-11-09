"""Optional integration boundary for the PyBibX bibliometric library."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from ..review.importers import load_records


class PyBibXUnavailable(RuntimeError):
    """Raised when the optional pybibx dependency is missing."""


def is_installed() -> bool:
    return importlib.util.find_spec("pybibx") is not None


def prepare_inputs(paths: list[str | Path]) -> dict[str, Any]:
    """Normalise supported SāhityaLab bibliography files into a run manifest."""
    records = []
    for path in paths:
        records.extend(load_records(path))
    return {
        "files": [str(Path(p).resolve()) for p in paths],
        "records_imported_by_sahityalab": len(records),
        "records": [item.model_dump(mode="json") for item in records],
        "pybibx_documentation": "https://github.com/valdecy/pybibx",
    }


def launch_pybibx_webapp() -> None:
    """Launch the documented PyBibX interactive web application."""
    if not is_installed():
        raise PyBibXUnavailable("Install PyBibX with: pip install 'sahityalab[bibliometrics]'")
    import pybibx  # type: ignore[import-not-found]
    launcher = getattr(pybibx, "web_app", None)
    if launcher is None:
        raise RuntimeError("The installed PyBibX version does not expose pybibx.web_app().")
    launcher()


def stop_pybibx_webapp() -> None:
    """Stop PyBibX's local web application when supported by the installed version."""
    if not is_installed():
        raise PyBibXUnavailable("Install PyBibX with: pip install 'sahityalab[bibliometrics]'")
    import pybibx  # type: ignore[import-not-found]
    stopper = getattr(pybibx, "web_stop", None)
    if stopper is None:
        raise RuntimeError("The installed PyBibX version does not expose pybibx.web_stop().")
    stopper()


def run_analysis(
    paths: list[str | Path],
    output_dir: str | Path,
    analysis_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a reproducible manifest; analysis itself runs in PyBibX.

    PyBibX exposes a rich interactive workbench and an evolving Python API.
    This adapter does not claim that creating the manifest performs analysis.
    It preserves provenance and gives the researcher a stable hand-off point.
    """
    if not is_installed():
        raise PyBibXUnavailable("Install PyBibX with: pip install 'sahityalab[bibliometrics]'")
    from ..io import write_json
    manifest = prepare_inputs(paths)
    manifest["analysis_config"] = analysis_config or {}
    manifest["engine"] = "pybibx"
    manifest["engine_note"] = "Run the requested analysis using the PyBibX workbench; archive its outputs with this manifest."
    write_json(manifest, Path(output_dir) / "pybibx_run_manifest.json")
    return manifest
