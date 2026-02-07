from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union


class ThemeMode(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class DensityMode(str, Enum):
    COMPACT = "compact"
    REGULAR = "regular"
    COMFORTABLE = "comfortable"


ThemeModeLike = Union[ThemeMode, str]
DensityModeLike = Union[DensityMode, str]


def _as_mode_value(v: object) -> str:
    if isinstance(v, Enum):
        return str(v.value)
    if isinstance(v, str):
        return v
    return str(v)


@dataclass(frozen=True)
class ThemeSelection:
    theme: ThemeMode = ThemeMode.DARK
    density: DensityMode = DensityMode.REGULAR

    @staticmethod
    def with_(theme: ThemeModeLike, density: DensityModeLike) -> "ThemeSelection":
        t = ThemeMode(theme) if isinstance(theme, str) else theme
        d = DensityMode(density) if isinstance(density, str) else density
        return ThemeSelection(theme=t, density=d)


@dataclass(frozen=True)
class ThemePaths:
    root: Path

    @property
    def themes_dir(self) -> Path:
        return self.root / "assets" / "themes"

    @property
    def qss_dir(self) -> Path:
        return self.root / "assets" / "qss"

    def theme_tokens_path(self, mode: ThemeModeLike) -> Path:
        mode_val = _as_mode_value(mode)
        return self.themes_dir / f"{mode_val}.json"

    def density_tokens_path(self, mode: DensityModeLike) -> Path:
        mode_val = _as_mode_value(mode)
        return self.themes_dir / f"density_{mode_val}.json"

    def qss_manifest(self) -> Path:
        return self.qss_dir / "main.qss"
