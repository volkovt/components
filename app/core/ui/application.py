from __future__ import annotations

import sys
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .theme_types import ThemeMode
from .base import apply_app_theme, set_theme_mode, set_density
from .theme_types import DensityMode

ExceptionHook = Callable[[type[BaseException], BaseException, object], None]


class AppApplication(QApplication):
    def __init__(
        self,
        argv: Optional[list[str]] = None,
        *,
        theme_mode: ThemeMode = ThemeMode.DARK,
        density: DensityMode = DensityMode.REGULAR,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        exception_hook: Optional[ExceptionHook] = None,
        quit_on_last_window_closed: bool = True,
    ):
        super().__init__(argv or sys.argv)

        self.setQuitOnLastWindowClosed(quit_on_last_window_closed)
        self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        if font_family or font_size:
            f = QFont()
            if font_family:
                f.setFamily(font_family)
            if font_size:
                f.setPointSize(font_size)
            self.setFont(f)

        set_theme_mode(theme_mode)
        set_density(density)
        apply_app_theme(self)

        if exception_hook is not None:
            sys.excepthook = exception_hook

    def set_theme(self, mode: ThemeMode) -> None:
        set_theme_mode(mode)
        apply_app_theme(self)

    def set_density_mode(self, density: DensityMode) -> None:
        set_density(density)
        apply_app_theme(self)
