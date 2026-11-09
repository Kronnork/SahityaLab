"""Safe, small helpers for reading and writing project artefacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def read_text(path: str | Path) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8-sig")


def write_json(data: Any, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return p


def write_yaml(data: Any, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p


def load_yaml(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)
