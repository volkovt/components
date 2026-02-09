from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QTabWidget, QWidget


@dataclass(frozen=True)
class TabSpec:
    title: str
    widget: QWidget
    icon: Optional[QIcon] = None
    tooltip: str = ""


class AppTabWidget(QTabWidget):
    current_tab_changed = Signal(int)

    def __init__(self, parent=None, *, document_mode: bool = True, movable: bool = False, elide: bool = True):
        super().__init__(parent)
        self.setDocumentMode(document_mode)
        self.setMovable(movable)
        self.setTabsClosable(False)
        if elide:
            self.tabBar().setElideMode(Qt.ElideRight)
        self.currentChanged.connect(self.current_tab_changed.emit)

    def add_app_tab(self, widget: QWidget, title: str, *, icon: Optional[QIcon] = None, tooltip: str = "") -> int:
        if icon is None:
            idx = self.addTab(widget, title)
        else:
            idx = self.addTab(widget, icon, title)
        if tooltip:
            self.setTabToolTip(idx, tooltip)
        return idx

    def add_tabs(self, tabs: list[TabSpec]) -> None:
        for t in tabs:
            self.add_app_tab(t.widget, t.title, icon=t.icon, tooltip=t.tooltip)
