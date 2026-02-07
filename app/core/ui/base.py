from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Mapping, Any

from qtpy.QtWidgets import QApplication
from qtpy import QtCore, QtWidgets

from .app_theme import AppTheme
from .theme_types import DensityMode, ThemeMode


_THEME: Optional[AppTheme] = None
_THEME_MODE: ThemeMode = ThemeMode.DARK
_DENSITY: DensityMode = DensityMode.REGULAR


def _project_root_from_app(app: QApplication) -> Path:
    """Best-effort project root resolution.

    - In dev: uses current working directory.
    - In frozen builds: uses the executable folder.

    You can override by setting APP_PROJECT_ROOT env var.
    """
    override = os.getenv("APP_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    # Frozen builds (PyInstaller/Nuitka)
    if getattr(sys, "frozen", False):  # type: ignore[name-defined]
        return Path(getattr(sys, "executable", os.getcwd())).resolve().parent

    return Path(os.getcwd()).resolve()


def set_theme_mode(mode) -> None:
    global _THEME_MODE
    _THEME_MODE = ThemeMode(mode) if isinstance(mode, str) else mode

def get_theme_mode() -> ThemeMode:
    return _THEME_MODE

def set_density(density) -> None:
    global _DENSITY
    _DENSITY = DensityMode(density) if isinstance(density, str) else density

def get_density() -> DensityMode:
    return _DENSITY


def apply_app_theme(app: QApplication, *, project_root: Path | None = None, dev_hot_reload: bool | None = None) -> None:
    """Apply the current theme selection to the QApplication.

    This is the single entry-point the rest of the UI should call.

    Args:
        app: QApplication instance.
        project_root: optional root override; defaults to env/CWD/frozen path.
        dev_hot_reload: optional override. If None, enables hot reload when
                        APP_THEME_HOT_RELOAD=1.
    """
    global _THEME

    root = (project_root or _project_root_from_app(app)).resolve()
    hot = dev_hot_reload if dev_hot_reload is not None else os.getenv("APP_THEME_HOT_RELOAD", "0") == "1"

    if _THEME is None:
        _THEME = AppTheme(project_root=root, theme=_THEME_MODE, density=_DENSITY, dev_hot_reload=hot)
    else:
        _THEME.set_theme(_THEME_MODE)
        _THEME.set_density(_DENSITY)

    _THEME.apply(app)


def repolish(widget: QtWidgets.QWidget) -> None:
    """
    Força o Qt a reaplicar QSS no widget (e pode ser usado após mudar propriedades dinâmicas).
    """
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_default_focus_policy(
    widget: QtWidgets.QWidget,
    policy: QtCore.Qt.FocusPolicy = QtCore.Qt.StrongFocus,
) -> None:
    """
    Padroniza focus policy de componentes customizados.
    Default: StrongFocus (teclado + mouse), bom para apps de gestão.
    """
    widget.setFocusPolicy(policy)


class AppWidgetMixin:
    """
    Mixin base para widgets do projeto.

    Convenções de QSS via dynamic properties:
    - role: "title", "subtitle", "muted", "badge", "card", "dialog", ...
    - state: "success", "warning", "error", ""(limpo)
    - variant: "primary", "ghost", "danger", "default" (botões)
    - disabled: bool
    - busy: bool
    """

    # --------- role ----------
    def set_role(self, role: str, repolish_now: bool = True) -> None:
        self.set_style_prop("role", role, repolish_now=repolish_now)

    def role(self) -> str:
        return str(self.style_prop("role", ""))

    # --------- state ----------
    def set_state(self, state: str, repolish_now: bool = True) -> None:
        self.set_style_prop("state", state, repolish_now=repolish_now)

    def clear_state(self, repolish_now: bool = True) -> None:
        w = self._as_qwidget()
        # remove a property para voltar ao default do QSS
        w.setProperty("state", None)
        if repolish_now:
            repolish(w)

    def state(self) -> str:
        return str(self.style_prop("state", ""))

    # --------- generic props ----------
    def set_style_props(self, props: Mapping[str, Any], repolish_now: bool = True) -> None:
        w = self._as_qwidget()
        for k, v in props.items():
            w.setProperty(k, v)
        if repolish_now:
            repolish(w)

    def set_style_prop(self, key: str, value: Any, repolish_now: bool = True) -> None:
        w = self._as_qwidget()
        w.setProperty(key, value)
        if repolish_now:
            repolish(w)

    def style_prop(self, key: str, default: Any = None) -> Any:
        w = self._as_qwidget()
        v = w.property(key)
        return default if v is None else v

    # --------- convenience ----------
    def set_disabled_visual(self, disabled: bool, repolish_now: bool = True) -> None:
        w = self._as_qwidget()
        w.setDisabled(disabled)
        w.setProperty("disabled", bool(disabled))
        if repolish_now:
            repolish(w)

    def set_busy(self, busy: bool, repolish_now: bool = True) -> None:
        w = self._as_qwidget()
        w.setProperty("busy", bool(busy))
        if repolish_now:
            repolish(w)

    def _as_qwidget(self) -> QtWidgets.QWidget:
        if not isinstance(self, QtWidgets.QWidget):
            raise TypeError("AppWidgetMixin deve ser usado em classes que herdam QWidget.")
        return self
