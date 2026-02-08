from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt

from .typography import Badge, MutedLabel
from .base import AppWidgetMixin


class InlineStatus(QWidget, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "inline_status")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.badge = Badge("Info")
        self.badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.badge.setAlignment(Qt.AlignCenter)

        self.text = MutedLabel("")
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.badge, 0, Qt.AlignTop)
        layout.addWidget(self.text, 1)  # não usar alignment aqui (evita corte em multi-linha)

        self.hide()

    def show_info(self, message: str, label: str = "Info"):
        self.badge.setText(label)
        self.badge.set_state("info")
        self.text.setText(message)
        self.show()

    def show_success(self, message: str, label: str = "OK"):
        self.badge.setText(label)
        self.badge.set_state("success")
        self.text.setText(message)
        self.show()

    def show_warning(self, message: str, label: str = "Atenção"):
        self.badge.setText(label)
        self.badge.set_state("warning")
        self.text.setText(message)
        self.show()

    def show_error(self, message: str, label: str = "Erro"):
        self.badge.setText(label)
        self.badge.set_state("error")
        self.text.setText(message)
        self.show()


class AppProgressBar(QProgressBar, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setRange(0, 100)
