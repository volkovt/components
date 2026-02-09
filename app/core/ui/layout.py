from __future__ import annotations

from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout

def vbox(margins=(0, 0, 0, 0), spacing=10) -> QVBoxLayout:
    l = QVBoxLayout()
    l.setContentsMargins(*margins)
    l.setSpacing(spacing)
    return l

def hbox(margins=(0, 0, 0, 0), spacing=10) -> QHBoxLayout:
    l = QHBoxLayout()
    l.setContentsMargins(*margins)
    l.setSpacing(spacing)
    return l
