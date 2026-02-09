from __future__ import annotations

from qtpy.QtWidgets import QTableView, QTreeView, QListView
from qtpy.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from .base import AppWidgetMixin, set_default_focus_policy

class AppTableView(QTableView, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.horizontalHeader().setStretchLastSection(True)
        set_default_focus_policy(self)

        self._proxy: QSortFilterProxyModel | None = None

    def setModel(self, model):  # type: ignore[override]
        if model is None:
            super().setModel(model)
            self._proxy = None
            return

        if isinstance(model, QSortFilterProxyModel):
            self._proxy = model
            self._proxy.setSortRole(Qt.UserRole)
            super().setModel(model)
            return

        proxy = QSortFilterProxyModel(self)
        proxy.setSourceModel(model)
        proxy.setSortRole(Qt.UserRole)
        proxy.setDynamicSortFilter(True)
        self._proxy = proxy
        super().setModel(proxy)


class AppTreeView(QTreeView, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(False)
        self.setUniformRowHeights(True)
        self.setAnimated(False)
        self.setIndentation(18)
        self.setSelectionMode(QTreeView.SingleSelection)
        set_default_focus_policy(self)


class AppListView(QListView, AppWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListView.SingleSelection)
        set_default_focus_policy(self)


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, headers: list[str], columns, rows=None, parent=None):
        super().__init__(parent)
        self._headers = headers
        self._columns = columns
        self._rows = rows or []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        value = self._columns[index.column()](row)

        if role == Qt.UserRole:
            return value

        if role == Qt.DisplayRole:
            return "" if value is None else str(value)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section]
        return str(section + 1)

    def set_rows(self, rows: list):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int):
        return self._rows[row]
