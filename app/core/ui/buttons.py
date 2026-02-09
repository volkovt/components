from __future__ import annotations

from typing import Callable, Optional

from qtpy.QtWidgets import QPushButton, QToolButton
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt, QSize

from .base import AppWidgetMixin, set_default_focus_policy, repolish

class AppButton(QPushButton, AppWidgetMixin):
    def __init__(
        self,
        text: str = "",
        parent=None,
        on_click: Optional[Callable[[], None]] = None,
        variant: str = "default",
        icon: Optional[QIcon] = None,
        icon_size: int = 18,
    ):
        super().__init__(text, parent)
        self.setProperty("variant", variant)
        if icon is not None:
            self.setIcon(icon)
            self.setIconSize(QSize(icon_size, icon_size))
        if on_click:
            self.clicked.connect(on_click)
        set_default_focus_policy(self)

    def set_variant(self, variant: str) -> None:
        self.setProperty("variant", variant)
        repolish(self)

class PrimaryButton(AppButton):
    def __init__(self, text: str = "Salvar", parent=None, on_click=None, icon: Optional[QIcon] = None):
        super().__init__(text=text, parent=parent, on_click=on_click, variant="primary", icon=icon)

class GhostButton(AppButton):
    def __init__(self, text: str = "Cancelar", parent=None, on_click=None, icon: Optional[QIcon] = None):
        super().__init__(text=text, parent=parent, on_click=on_click, variant="ghost", icon=icon)

class DangerButton(AppButton):
    def __init__(self, text: str = "Excluir", parent=None, on_click=None, icon: Optional[QIcon] = None):
        super().__init__(text=text, parent=parent, on_click=on_click, variant="danger", icon=icon)

class AppToolButton(QToolButton, AppWidgetMixin):
    def __init__(
        self,
        text: str = "",
        parent=None,
        icon: Optional[QIcon] = None,
        on_click: Optional[Callable[[], None]] = None,
        *,
        icon_size: int = 18,
        square: bool = False,
        size: int = 32,
    ):
        super().__init__(parent)
        self.setProperty("variant", "tool")
        self.setText(text)
        if text.strip():
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        if icon is not None:
            self.setIcon(icon)
            self.setIconSize(QSize(icon_size, icon_size))
        if square:
            self.setFixedSize(size, size)
        self.setContentsMargins(0, 0, 0, 0)

        if on_click:
            self.clicked.connect(on_click)

        set_default_focus_policy(self)
