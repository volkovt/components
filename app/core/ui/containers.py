from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt

from .base import AppWidgetMixin
from .typography import SubtitleLabel, MutedLabel

class Card(QFrame, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setFrameShape(QFrame.NoFrame)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

    @property
    def body(self) -> QVBoxLayout:
        return self._layout

class Section(QWidget, AppWidgetMixin):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2)

        self.lbl_title = SubtitleLabel(title)
        header.addWidget(self.lbl_title)

        self.lbl_subtitle = MutedLabel(subtitle) if subtitle else None
        if self.lbl_subtitle:
            header.addWidget(self.lbl_subtitle)

        root.addLayout(header)

        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(10)
        root.addLayout(self.content)

class Divider(QFrame, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedHeight(1)
        # keep minimal local style to remove default frame artifacts
        self.setStyleSheet("background: transparent; border: 0px;")

class Toolbar(QWidget, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self._layout.setAlignment(Qt.AlignLeft)

    @property
    def layout_row(self) -> QHBoxLayout:
        return self._layout
