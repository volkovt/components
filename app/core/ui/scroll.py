from __future__ import annotations

from qtpy.QtWidgets import QScrollArea, QWidget

class AppScrollArea(QScrollArea):
    def __init__(self, parent=None, *, widget_resizable: bool = True, frame: bool = False):
        super().__init__(parent)
        self.setWidgetResizable(widget_resizable)
        if not frame:
            self.setFrameShape(QScrollArea.NoFrame)

    def set_content(self, content: QWidget) -> None:
        self.setWidget(content)

    @classmethod
    def wrap(cls, content: QWidget) -> "AppScrollArea":
        s = cls()
        s.set_content(content)
        return s
