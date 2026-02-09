from __future__ import annotations

from typing import Optional

from qtpy.QtCore import Signal, QTimer
from qtpy.QtGui import QCloseEvent, QIcon, QCursor, QGuiApplication, QShowEvent
from qtpy.QtWidgets import QMainWindow, QWidget

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

        self._min_size = min_size
        self.setMinimumSize(*min_size)

        self._fallback_start_size = start_size
        self.resize(*start_size)

        self._content: Optional[QWidget] = None
        self._did_place_on_cursor_screen = False

    def set_content(self, widget: QWidget) -> None:
        self._content = widget
        self.setCentralWidget(widget)

    def repolish_tree(self, root: Optional[QWidget] = None) -> None:
        w = root or self
        repolish(w)
        for child in w.findChildren(QWidget):
            repolish(child)

    def _apply_half_screen_geometry_at_cursor(self) -> None:
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        if screen is None:
            return

        avail = screen.availableGeometry()
        if avail.width() <= 0 or avail.height() <= 0:
            return

        min_w, min_h = self._min_size

        target_w = max(min_w, avail.width() // 2)
        target_h = max(min_h, avail.height() // 2)

        # Não deixa maior que a área útil da tela (evita “vazar”)
        target_w = min(target_w, avail.width())
        target_h = min(target_h, avail.height())

        self.resize(target_w, target_h)

        frame = self.frameGeometry()
        frame.moveCenter(avail.center())
        self.move(frame.topLeft())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if self._did_place_on_cursor_screen:
            return

        self._did_place_on_cursor_screen = True
        QTimer.singleShot(0, self._apply_half_screen_geometry_at_cursor)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closed.emit()
        super().closeEvent(event)
