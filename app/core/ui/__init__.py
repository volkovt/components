from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List

# ---- Explicit theme exports (stable public surface) ----
from .app_theme import AppTheme
from .application import AppApplication
from .base import (
    apply_app_theme,
    repolish,
    set_theme_mode,
    set_density,
    get_theme_mode,
    get_density,
)
from .buttons import AppButton, PrimaryButton, GhostButton, DangerButton, AppToolButton
from .containers import Card, Section, Divider, Toolbar
from .dialogs import AppDialog, DialogSizePreset, FormDialog, confirm_destructive
from .feedback import AppProgressBar, InlineStatus
from .inputs import AppLineEdit, AppTextEdit, AppPlainTextEdit, AppComboBox, AppSpinBox, AppDoubleSpinBox, \
    AppDateTimeEdit, AppTimeEdit, AppDateEdit, int_validator, money_validator
from .layout import vbox, hbox
from .messagebox import AppMessageBox
from .scroll import AppScrollArea
from .tabs import AppTabWidget
from .theme_types import ThemeMode
from .theme_types import DensityMode as Density  # backwards-friendly alias
from .typography import TitleLabel, SubtitleLabel, MutedLabel, Badge
from .views import AppTableView, SimpleTableModel
from .window import AppMainWindow

# ---- Lazy export system for everything else under ui/ ----

_PKG_DIR = Path(__file__).resolve().parent
_PKG_NAME = __name__

# Cache: attribute -> value
_ATTR_CACHE: Dict[str, Any] = {}

# Cache: discovered module dotted paths
_MODULE_PATHS: List[str] | None = None


def _iter_module_paths() -> Iterable[str]:
    """Discover all python modules under this package (recursive).

    We avoid importing everything eagerly to keep startup fast.
    """
    global _MODULE_PATHS
    if _MODULE_PATHS is not None:
        yield from _MODULE_PATHS
        return

    paths: List[str] = []

    # Collect .py files (excluding __init__.py) and packages.
    for p in sorted(_PKG_DIR.rglob("*.py")):
        if p.name == "__init__.py":
            continue
        rel = p.relative_to(_PKG_DIR)
        # ui/foo/bar.py  ->  app.core.ui.foo.bar
        dotted = ".".join([_PKG_NAME] + list(rel.with_suffix("").parts))
        paths.append(dotted)

    _MODULE_PATHS = paths
    yield from paths


def _try_get_from_module(mod: ModuleType, name: str) -> Any:
    if hasattr(mod, name):
        return getattr(mod, name)
    return None


def __getattr__(name: str) -> Any:  # PEP 562
    if name in _ATTR_CACHE:
        return _ATTR_CACHE[name]

    # Avoid scanning for obvious dunder access
    if name.startswith("__"):
        raise AttributeError(name)

    for mod_path in _iter_module_paths():
        try:
            mod = import_module(mod_path)
        except Exception:
            # Keep UI resilient: a broken optional module shouldn't break imports.
            continue

        value = _try_get_from_module(mod, name)
        if value is not None:
            _ATTR_CACHE[name] = value
            return value

    raise AttributeError(f"module '{_PKG_NAME}' has no attribute '{name}'")


def __dir__() -> List[str]:
    # Provide a nice autocomplete surface.
    exported = set(globals().keys())
    for mod_path in _iter_module_paths():
        try:
            mod = import_module(mod_path)
        except Exception:
            continue
        exported.update([k for k in dir(mod) if not k.startswith("_")])
    return sorted(exported)


__all__ = [
    # Theme
    "AppTheme",
    "ThemeMode",
    "Density",
    "apply_app_theme",
    "repolish",
    "set_theme_mode",
    "set_density",
    "get_theme_mode",
    "get_density",

    # Typography
    "TitleLabel",
    "SubtitleLabel",
    "MutedLabel",
    "Badge",

    # Buttons
    "AppButton",
    "PrimaryButton",
    "GhostButton",
    "DangerButton",
    "AppToolButton",

    # Inputs
    "AppLineEdit",
    "AppTextEdit",
    "AppPlainTextEdit",
    "AppComboBox",
    "AppSpinBox",
    "AppDoubleSpinBox",
    "AppDateEdit",
    "AppTimeEdit",
    "AppDateTimeEdit",
    "int_validator",
    "money_validator",

    # Containers / Layout
    "Card",
    "Section",
    "Divider",
    "Toolbar",
    "vbox",
    "hbox",

    # Views / Models
    "AppTableView",
    "SimpleTableModel",

    # Dialogs
    "AppDialog",
    "DialogSizePreset",
    "FormDialog",
    "confirm_destructive",

    # Feedback
    "InlineStatus",
    "AppProgressBar",

    # Window / App
    "AppScrollArea",
    "AppMainWindow",
    "AppApplication",
    "AppMessageBox",
    "AppTabWidget",
]

