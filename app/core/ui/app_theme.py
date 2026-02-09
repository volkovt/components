# app/core/ui/app_theme.py
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .theme_manager import ThemeManager
from .theme_types import DensityMode, ThemeMode, ThemeSelection
from .icon_theme import IconTheme

if TYPE_CHECKING:
    from .application import AppApplication

class AppTheme:
    """
    Facade used by the rest of the app.
    Keeps old call sites stable: apply_app_theme() can just delegate here.
    """

    def __init__(
        self,
        project_root: Path,
        theme: ThemeMode = ThemeMode.DARK,
        density: DensityMode = DensityMode.REGULAR,
        dev_hot_reload: bool = False,
    ):
        self._manager = ThemeManager(
            project_root=project_root,
            selection=ThemeSelection.with_(theme, density),
            dev_hot_reload=dev_hot_reload,
        )

        self._manager.theme_changed.connect(self._on_theme_changed)

    @property
    def manager(self) -> ThemeManager:
        return self._manager

    def set_theme(self, theme: ThemeMode) -> None:
        sel = self._manager.selection
        self._manager.set_selection(ThemeSelection.with_(theme, sel.density))

    def set_density(self, density: DensityMode) -> None:
        sel = self._manager.selection
        self._manager.set_selection(ThemeSelection.with_(sel.theme, density))

    def apply(self, app: AppApplication) -> None:
        compiled = self._manager.apply(app)
        IconTheme.apply_tokens(compiled.tokens)

    def _on_theme_changed(self, _fingerprint: str) -> None:
        compiled = self._manager.last_compiled
        if compiled:
            IconTheme.apply_tokens(compiled.tokens)
