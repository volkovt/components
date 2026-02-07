from __future__ import annotations

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from .base import AppWidgetMixin


class AppLabel(QLabel, AppWidgetMixin):
    def __init__(self, text: str = "", parent=None, role: str | None = None, selectable: bool = False):
        super().__init__(text, parent)
        if role:
            self.set_role(role)
        if selectable:
            self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWordWrap(True)


class TitleLabel(AppLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent, role="title")


class SubtitleLabel(AppLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent, role="subtitle")


class MutedLabel(AppLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent, role="muted")


class Badge(AppLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent, role="badge", selectable=False)
        self.setAlignment(Qt.AlignCenter)
        self.setFocusPolicy(Qt.NoFocus)
