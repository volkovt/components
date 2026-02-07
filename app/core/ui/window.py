from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget

from .base import repolish


class AppMainWindow(QMainWindow):
    closed = Signal()

    def __init__(
        self,
        *,
        title: str = "",
        icon: Optional[QIcon] = None,
        min_size: tuple[int, int] = (960, 640),
        start_size: tuple[int, int] = (1200, 800),
        parent=None,
    ):
        super().__init__(parent)

        if title:
            self.setWindowTitle(title)
        if icon is not None:
            self.setWindowIcon(icon)

        self.setMinimumSize(*min_size)
        self.resize(*start_size)

        self._content: Optional[QWidget] = None

    def set_content(self, widget: QWidget) -> None:
        self._content = widget
        self.setCentralWidget(widget)

    def repolish_tree(self, root: Optional[QWidget] = None) -> None:
        w = root or self
        repolish(w)
        for child in w.findChildren(QWidget):
            repolish(child)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closed.emit()
        super().closeEvent(event)
