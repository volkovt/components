from typing import TYPE_CHECKING

from qtpy.QtWidgets import QMenu
from app.core.ui.base import AppWidgetMixin

class AppMenu(QMenu, AppWidgetMixin):
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)