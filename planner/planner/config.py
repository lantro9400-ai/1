"""채널 프로필 / 코너 템플릿 로드."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"
CORNERS_DIR = ROOT / "corners"
ARCHIVE_DIR = ROOT / "archive"
REFERENCES_DIR = ROOT / "references"


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_profile(name: str) -> dict[str, Any]:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in PROFILES_DIR.glob("*.yaml"))
        raise SystemExit(f"채널 프로필 '{name}' 이 없습니다. 사용 가능: {available}")
    return _load(path)


def load_corner(name: str) -> dict[str, Any]:
    path = CORNERS_DIR / f"{name}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in CORNERS_DIR.glob("*.yaml"))
        raise SystemExit(f"코너 템플릿 '{name}' 이 없습니다. 사용 가능: {available}")
    return _load(path)
