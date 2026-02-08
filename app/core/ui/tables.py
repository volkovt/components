# app/core/ui/tables.py
from __future__ import annotations

import math
import time
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, Sequence, List, Tuple

from qtpy.QtCore import (
    Qt, QObject, Signal, QRunnable, QThreadPool, QAbstractTableModel, QModelIndex,
    QEvent, QTimer, QPoint, QSize
)
from qtpy.QtGui import QAction, QGuiApplication, QIcon
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QSizePolicy, QHeaderView, QMenu,
    QInputDialog, QMessageBox
)

from app.core.ports.exporter_registry import ExporterRegistry
from app.core.ui import AppToolButton, AppSpinBox, AppComboBox, AppLineEdit, AppButton, AppDialog
from app.core.ui.icon_theme import IconTheme
from app.core.ui.typography import AppLabel
from app.core.use_cases.export_table import ExportRequest, ExportTableUseCase
from app.infra.export.excel.xlsx_exporter import XlsxTableExporter
from app.infra.export.pdf.pdf_exporter import PdfTableExporter

import qtawesome as qta

# -----------------------------
# DTOs / Contracts
# -----------------------------
@dataclass(frozen=True)
class SortSpec:
    key: str
    ascending: bool = True


@dataclass(frozen=True)
class FilterSpec:
    key: str
    op: str
    value: Any


@dataclass(frozen=True)
class TableQuery:
    page: int
    page_size: int

    search_text: str = ""
    search_mode: str = "contem"  # contem|comeca|igual|regex
    search_case_sensitive: bool = False
    search_accent_insensitive: bool = True

    filters: Tuple[FilterSpec, ...] = ()
    sort: Tuple[SortSpec, ...] = ()

    searchable_keys: Tuple[str, ...] = ()  # vazio => "todas as colunas visíveis"


@dataclass(frozen=True)
class TablePage:
    rows: Sequence[Mapping[str, Any]]
    total_rows: int
    page: int
    page_size: int


class TableDataPort(Protocol):
    def fetch_page(self, query: TableQuery) -> TablePage:
        ...


# -----------------------------
# Helpers
# -----------------------------

def _norm_text(s: str, accent_insensitive: bool) -> str:
    if not accent_insensitive:
        return s
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


# -----------------------------
# Worker
# -----------------------------

class _FetchSignals(QObject):
    ok = Signal(object, int)
    fail = Signal(object, int)


class _FetchTask(QRunnable):
    def __init__(self, port: TableDataPort, query: TableQuery, request_id: int):
        super().__init__()
        self._port = port
        self._query = query
        self._request_id = request_id
        self.signals = _FetchSignals()

    def run(self) -> None:
        try:
            page = self._port.fetch_page(self._query)
            self.signals.ok.emit(page, self._request_id)
        except Exception as e:
            self.signals.fail.emit(e, self._request_id)



# -----------------------------
# Export (Worker + UseCase wiring)
# -----------------------------

class _ExportSignals(QObject):
    progress = Signal(int, int)  # done, total
    ok = Signal(object)
    fail = Signal(object)


class _ExportTask(QRunnable):
    def __init__(self, use_case, req, current_rows, data_port):
        super().__init__()
        self._use_case = use_case
        self._req = req
        self._current_rows = current_rows
        self._data_port = data_port
        self.signals = _ExportSignals()

    def run(self) -> None:
        try:
            def _progress(done: int, total: int) -> None:
                self.signals.progress.emit(int(done), int(total))

            res = self._use_case.execute(
                self._req,
                data_port=self._data_port,
                current_page_rows=self._current_rows,
                progress=_progress,
            )
            self.signals.ok.emit(res)
        except Exception as e:
            self.signals.fail.emit(e)

class SmartTableModel(QAbstractTableModel):
    def __init__(self, columns: List[Tuple[str, str]]):
        super().__init__()
        self._columns: List[Tuple[str, str]] = list(columns)
        self._rows: List[dict] = []

    def columns(self) -> List[Tuple[str, str]]:
        return list(self._columns)

    def rows(self) -> List[Mapping[str, Any]]:
        return [dict(r) for r in self._rows]

    def set_columns(self, columns: List[Tuple[str, str]]) -> None:
        self.beginResetModel()
        self._columns = list(columns)
        self._rows = []
        self.endResetModel()

    def reset_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = [dict(r) for r in rows]
        self.endResetModel()

    def append_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        if not rows:
            return
        start = len(self._rows)
        end = start + len(rows) - 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._rows.extend([dict(r) for r in rows])
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        key = self._columns[index.column()][0]

        if role in (Qt.DisplayRole, Qt.EditRole):
            return _safe_str(row.get(key, ""))

        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | Qt.AlignLeft)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section][1]
            return ""

        return str(section + 1)

    def row_dict(self, row: int) -> Optional[Mapping[str, Any]]:
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]

# -----------------------------
# Controller
# -----------------------------

class SmartTableController(QObject):
    changed = Signal(object, int)          # TablePage, request_id
    loading_changed = Signal(bool)
    error = Signal(str)

    def __init__(self, port: TableDataPort):
        super().__init__()
        self._port = port
        self._pool = QThreadPool.globalInstance()

        self._page = 1
        self._page_size = 50
        self._total_rows = 0

        self._search_text = ""
        self._search_mode = "contem"
        self._case_sensitive = False
        self._accent_insensitive = True

        self._filters: List[FilterSpec] = []
        self._sort: List[SortSpec] = []
        self._searchable_keys: List[str] = []

        self._request_id = 0
        self._loading = False

        self._append_mode = False

    def data_port(self) -> TableDataPort:
        return self._port

    def set_searchable_keys(self, keys: List[str]) -> None:
        self._searchable_keys = list(keys)
        self.goto_page(1)

    def set_page_size(self, size: int) -> None:
        self._page_size = max(1, int(size))
        self.goto_page(1)

    def set_search(self, text: str, mode: str = "contem",
                   case_sensitive: bool = False, accent_insensitive: bool = True) -> None:
        self._search_text = text or ""
        self._search_mode = mode
        self._case_sensitive = case_sensitive
        self._accent_insensitive = accent_insensitive
        self.goto_page(1)

    def set_filters(self, filters: List[FilterSpec]) -> None:
        self._filters = list(filters)
        self.goto_page(1)

    def add_filter(self, spec: FilterSpec) -> None:
        self._filters.append(spec)
        self.goto_page(1)

    def clear_filters(self) -> None:
        self._filters = []
        self.goto_page(1)

    def set_sort(self, sort: List[SortSpec]) -> None:
        self._sort = list(sort)
        self.goto_page(1)

    def total_rows(self) -> int:
        return self._total_rows

    def page(self) -> int:
        return self._page

    def page_size(self) -> int:
        return self._page_size

    def total_pages(self) -> int:
        if self._page_size <= 0:
            return 1
        return max(1, math.ceil(self._total_rows / self._page_size))

    def is_loading(self) -> bool:
        return self._loading

    def _emit_loading(self, v: bool) -> None:
        if self._loading == v:
            return
        self._loading = v
        self.loading_changed.emit(v)

    def snapshot_query(self) -> TableQuery:
        return self._make_query()

    def _make_query(self) -> TableQuery:
        s = self._search_text
        if not self._case_sensitive:
            s = s.lower()
        if self._accent_insensitive:
            s = _norm_text(s, True)

        return TableQuery(
            page=self._page,
            page_size=self._page_size,
            search_text=s,
            search_mode=self._search_mode,
            search_case_sensitive=self._case_sensitive,
            search_accent_insensitive=self._accent_insensitive,
            filters=tuple(self._filters),
            sort=tuple(self._sort),
            searchable_keys=tuple(self._searchable_keys),
        )

    def refresh(self, append: bool = False) -> None:
        if self._loading:
            return

        self._append_mode = append
        self._request_id += 1
        rid = self._request_id

        self._emit_loading(True)

        task = _FetchTask(self._port, self._make_query(), rid)
        task.signals.ok.connect(self._on_ok)
        task.signals.fail.connect(self._on_fail)
        self._pool.start(task)

    def _on_ok(self, page: TablePage, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._total_rows = int(page.total_rows)
        self._emit_loading(False)
        self.changed.emit(page, request_id)

    def _on_fail(self, exc: Exception, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._emit_loading(False)
        self.error.emit(_safe_str(exc))

    def goto_page(self, page: int) -> None:
        self._page = max(1, int(page))
        self.refresh(append=False)

    def next_page(self) -> None:
        if self._page < self.total_pages():
            self._page += 1
            self.refresh(append=False)

    def prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self.refresh(append=False)

    def load_next_append(self) -> None:
        if self._page >= self.total_pages():
            return
        self._page += 1
        self.refresh(append=True)

    def append_mode(self) -> bool:
        return self._append_mode


# -----------------------------
# Widget
# -----------------------------

class AppTable(QWidget):
    row_activated = Signal(dict)
    selection_changed = Signal(object)  # dict | None

    def __init__(self, port: TableDataPort, columns: List[Tuple[str, str]]):
        super().__init__()

        self._controller = SmartTableController(port)
        self._model = SmartTableModel(columns)

        self._search = AppLineEdit()
        self._search.setPlaceholderText("Pesquisar (global) …")

        self._search_mode = AppComboBox()
        self._search_mode.addItems(["contem", "comeca", "igual", "regex"])

        self._page_size = AppSpinBox()
        self._page_size.setRange(10, 2000)
        self._page_size.setSingleStep(10)
        self._page_size.setValue(50)

        self._btn_first = AppButton()
        self._btn_prev = AppButton()
        self._btn_next = AppButton()
        self._btn_last = AppButton()

        IconTheme.bind(self._btn_first, "fa5s.angle-double-left")
        IconTheme.bind(self._btn_prev, "fa5s.angle-left")
        IconTheme.bind(self._btn_next, "fa5s.angle-right")
        IconTheme.bind(self._btn_last, "fa5s.angle-double-right")

        for b in (self._btn_first, self._btn_prev, self._btn_next, self._btn_last):
            b.setObjectName("PagerButton")
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(38, 38)

        self._page_jump = AppSpinBox()
        self._page_jump.setFixedHeight(38)
        self._page_jump.setRange(1, 1)
        self._page_jump.setValue(1)
        self._page_jump.setObjectName("PagerSpin")
        self._page_jump.setToolTip("Ir para página")

        self._btn_clear_filters = AppButton("Limpar filtros")
        self._btn_clear_filters.setToolTip("Remove todos os filtros ativos")

        self._btn_export = AppToolButton()
        self._btn_export.setObjectName("GearButton")
        self._btn_export.setToolTip("Ações")
        self._btn_export.setCursor(Qt.PointingHandCursor)
        IconTheme.bind(self._btn_export, "fa5s.cog")
        self._btn_export.setIconSize(QSize(18, 18))
        self._btn_export.setPopupMode(AppToolButton.InstantPopup)
        self._btn_export.setAutoRaise(False)
        self._btn_export.setFixedSize(38, 38)

        self._lbl_page = AppLabel("Página 1/1 — 0 itens")
        self._lbl_page.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSortingEnabled(False)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._table.setFocusPolicy(Qt.ClickFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self._search, 1)
        top.addWidget(self._search_mode, 0)
        top.addWidget(AppLabel("Page size:"), 0)
        top.addWidget(self._page_size, 0)
        top.addWidget(self._btn_export, 0)

        nav = QHBoxLayout()
        nav.setSpacing(10)
        nav.addWidget(self._btn_first)
        nav.addWidget(self._btn_prev)
        nav.addWidget(self._page_jump)
        nav.addWidget(self._btn_next)
        nav.addWidget(self._btn_last)
        nav.addStretch(1)
        nav.addWidget(self._lbl_page)

        root.addLayout(top)
        root.addWidget(self._table, 1)
        root.addLayout(nav)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)

        self._controller.changed.connect(self._apply_page_to_model)
        self._controller.loading_changed.connect(self._on_loading)
        self._controller.error.connect(self._on_error)

        self._search.textChanged.connect(self._debounced_search)
        self._search_mode.currentTextChanged.connect(self._debounced_search)
        self._search_timer.timeout.connect(self._do_search)

        self._page_size.valueChanged.connect(self._controller.set_page_size)

        self._btn_first.clicked.connect(lambda: self._controller.goto_page(1))
        self._btn_prev.clicked.connect(self._controller.prev_page)
        self._btn_next.clicked.connect(self._controller.next_page)
        self._btn_last.clicked.connect(lambda: self._controller.goto_page(self._controller.total_pages()))

        self._page_jump.valueChanged.connect(self._controller.goto_page)

        self._btn_clear_filters.clicked.connect(self._controller.clear_filters)

        self._pool = QThreadPool.globalInstance()

        self._ExportRequest = ExportRequest
        self._export_uc = ExportTableUseCase(ExporterRegistry({
            "xlsx": XlsxTableExporter(),
            "pdf": PdfTableExporter(),
        }))
        self._install_export_menu()

        self._table.installEventFilter(self)
        self._table.verticalScrollBar().valueChanged.connect(self._maybe_infinite_scroll)
        self._table.doubleClicked.connect(self._emit_row_activated)

        sel_model = self._table.selectionModel()
        sel_model.selectionChanged.connect(self._emit_selection)

        self._install_header_menu()
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self._sort_state: List[SortSpec] = []
        self._sort_col: Optional[int] = None
        self._sort_asc: bool = True

        self._controller.goto_page(1)

    # -------------------------
    # Public API
    # -------------------------

    def set_columns(self, columns: List[Tuple[str, str]]) -> None:
        self._model.set_columns(columns)
        self._controller.goto_page(1)

    def set_filters(self, filters: List[FilterSpec]) -> None:
        self._controller.set_filters(filters)

    def set_sort(self, sort: List[SortSpec]) -> None:
        self._controller.set_sort(sort)

    def set_searchable_keys(self, keys: List[str]) -> None:
        self._controller.set_searchable_keys(keys)

    def refresh(self) -> None:
        self._controller.refresh(append=False)

    # -------------------------
    # Internal
    # -------------------------

    def _install_header_menu(self) -> None:
        header = self._table.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_menu)

    def _on_header_menu(self, pos: QPoint) -> None:
        header = self._table.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return

        key = self._model._columns[col][0]
        title = self._model._columns[col][1]

        menu = QMenu(self)

        act_sort_asc = QAction("Ordenar A → Z", self)
        act_sort_desc = QAction("Ordenar Z → A", self)
        act_sort_clear = QAction("Limpar ordenação", self)
        act_filter = QAction(f"Filtrar por '{title}'…", self)
        act_clear = QAction("Limpar filtros", self)

        act_sort_asc.triggered.connect(lambda: self._set_sort_from_column(key, ascending=True, additive=False))
        act_sort_desc.triggered.connect(lambda: self._set_sort_from_column(key, ascending=False, additive=False))
        act_sort_clear.triggered.connect(self._clear_sort)

        act_filter.triggered.connect(lambda: self._prompt_column_filter(key, title))
        act_clear.triggered.connect(self._controller.clear_filters)

        menu.addAction(act_sort_asc)
        menu.addAction(act_sort_desc)
        menu.addAction(act_sort_clear)
        menu.addSeparator()
        menu.addAction(act_filter)
        menu.addSeparator()
        menu.addAction(act_clear)
        menu.exec(header.mapToGlobal(pos))

    def _on_header_clicked(self, logical_index: int) -> None:
        if logical_index < 0 or logical_index >= len(self._model._columns):
            return
        key = self._model._columns[logical_index][0]
        mods = QGuiApplication.keyboardModifiers()
        additive = bool(mods & Qt.ShiftModifier)

        if self._sort_col == logical_index:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = logical_index
            self._sort_asc = True

        self._set_sort_from_column(key, ascending=self._sort_asc, additive=additive)

    def _set_sort_from_column(self, key: str, ascending: bool, additive: bool) -> None:
        if not additive:
            self._sort_state = [SortSpec(key=key, ascending=ascending)]
        else:
            prev = [s for s in self._sort_state if s.key != key]
            prev.append(SortSpec(key=key, ascending=ascending))
            self._sort_state = prev
        self._controller.set_sort(self._sort_state)
        self._sync_header_sort_indicator()

    def _clear_sort(self) -> None:
        self._sort_state = []
        self._sort_col = None
        self._sort_asc = True
        self._controller.set_sort([])
        self._table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

    def _sync_header_sort_indicator(self) -> None:
        header = self._table.horizontalHeader()
        if not self._sort_state:
            header.setSortIndicator(-1, Qt.AscendingOrder)
            return
        primary = self._sort_state[-1]
        try:
            col = [k for k, _ in self._model._columns].index(primary.key)
        except ValueError:
            header.setSortIndicator(-1, Qt.AscendingOrder)
            return
        order = Qt.AscendingOrder if primary.ascending else Qt.DescendingOrder
        header.setSortIndicator(col, order)

    def _prompt_column_filter(self, key: str, title: str) -> None:
        value, ok = QInputDialog.getText(self, "Filtro", f"Contém em '{title}':")
        if not ok:
            return
        value = value.strip()
        if not value:
            return
        self._controller.add_filter(FilterSpec(key=key, op="contem", value=value))

    def set_qss(self, qss: str) -> None:
        self.setStyleSheet(qss)

    def _debounced_search(self) -> None:
        self._search_timer.start()

    def _do_search(self) -> None:
        text = self._search.text()
        mode = self._search_mode.currentText()
        self._controller.set_search(text=text, mode=mode, case_sensitive=False, accent_insensitive=True)

    def eventFilter(self, obj, event):
        if obj is self._table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Down, Qt.Key_PageDown):
                return self._maybe_cursor_down_paging()
        return super().eventFilter(obj, event)

    def _maybe_cursor_down_paging(self) -> bool:
        idx = self._table.currentIndex()
        if not idx.isValid():
            return False
        last_row = self._model.rowCount() - 1
        if last_row < 0:
            return False
        if idx.row() >= last_row:
            if not self._controller.is_loading():
                self._controller.load_next_append()
                return True
        return False

    def _maybe_infinite_scroll(self, value: int) -> None:
        sb = self._table.verticalScrollBar()
        if self._controller.is_loading():
            return
        if sb.maximum() <= 0:
            return
        if value >= int(sb.maximum() * 0.92):
            self._controller.load_next_append()

    def _apply_page_to_model(self, page: TablePage, request_id: int) -> None:
        if self._controller.append_mode():
            self._model.append_rows(page.rows)
        else:
            self._model.reset_rows(page.rows)

        self._update_footer()

        if self._model.rowCount() > 0 and not self._table.currentIndex().isValid():
            # Evita "roubar" o foco do campo de pesquisa enquanto o usuário digita.
            if not self._search.hasFocus():
                self._table.selectRow(0)

    def _update_footer(self) -> None:
        p = self._controller.page()
        tp = self._controller.total_pages()
        total = self._controller.total_rows()
        self._lbl_page.setText(f"Página {p}/{tp} — {total} itens")

        self._page_jump.blockSignals(True)
        self._page_jump.setRange(1, max(1, tp))
        self._page_jump.setValue(max(1, min(p, tp)))
        self._page_jump.blockSignals(False)

        loading = self._controller.is_loading()
        self._btn_first.setEnabled(p > 1 and not loading)
        self._btn_prev.setEnabled(p > 1 and not loading)
        self._btn_next.setEnabled(p < tp and not loading)
        self._btn_last.setEnabled(p < tp and not loading)

    def _on_loading(self, loading: bool) -> None:
        # Não desabilite o campo de pesquisa enquanto carrega, para evitar perda de foco a cada tecla.
        # Mantemos apenas controles que podem gerar navegação/paginação concorrente.
        self._page_size.setEnabled(not loading)
        self._btn_clear_filters.setEnabled(not loading)
        self._btn_first.setEnabled(self._controller.page() > 1 and not loading)
        self._btn_prev.setEnabled(self._controller.page() > 1 and not loading)
        self._btn_next.setEnabled(self._controller.page() < self._controller.total_pages() and not loading)
        self._btn_last.setEnabled(self._controller.page() < self._controller.total_pages() and not loading)
        self._page_jump.setEnabled(not loading)
        self._update_footer()

    def _on_error(self, msg: str) -> None:
        self._lbl_page.setText(f"Erro: {msg}")

    def _emit_row_activated(self, index: QModelIndex) -> None:
        row = index.row()
        d = self._model.row_dict(row)
        if d is not None:
            self.row_activated.emit(dict(d))

    def _emit_selection(self) -> None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            self.selection_changed.emit(None)
            return
        d = self._model.row_dict(idx.row())
        self.selection_changed.emit(dict(d) if d is not None else None)

    # -------------------------
    # Export UI
    # -------------------------
    def _install_export_menu(self) -> None:
        root_menu = QMenu(self)

        # Submenu: Exportar
        export_menu = QMenu("Exportar", self)

        # Ícones específicos por tipo
        ico_excel = QIcon("assets/icons/excel.svg")
        ico_pdf = QIcon("assets/icons/pdf.svg")

        act_xlsx_page = QAction(ico_excel, "Excel (XLSX) — Página atual", self)
        act_xlsx_all = QAction(ico_excel, "Excel (XLSX) — Todos os resultados", self)

        act_pdf_page = QAction(ico_pdf, "PDF — Página atual", self)
        act_pdf_all = QAction(ico_pdf, "PDF — Todos os resultados", self)

        act_xlsx_page.triggered.connect(lambda: self._export(fmt="xlsx", mode="current_page"))
        act_xlsx_all.triggered.connect(lambda: self._export(fmt="xlsx", mode="all_results"))
        act_pdf_page.triggered.connect(lambda: self._export(fmt="pdf", mode="current_page"))
        act_pdf_all.triggered.connect(lambda: self._export(fmt="pdf", mode="all_results"))

        export_menu.addAction(act_xlsx_page)
        export_menu.addAction(act_xlsx_all)
        export_menu.addSeparator()
        export_menu.addAction(act_pdf_page)
        export_menu.addAction(act_pdf_all)

        root_menu.addMenu(export_menu)

        self._btn_export.setMenu(root_menu)

    def _export(self, *, fmt: str, mode: str) -> None:
        if self._controller.is_loading():
            QMessageBox.information(self, "Aguarde", "A tabela ainda está carregando. Tente exportar novamente em alguns instantes.")
            return

        ext = "xlsx" if fmt == "xlsx" else "pdf"
        default_name = f"export_{int(time.time())}.{ext}"

        path, _ = AppDialog.getSaveFileName(
            self,
            "Salvar exportação",
            default_name,
            "Excel (*.xlsx)" if ext == "xlsx" else "PDF (*.pdf)",
        )
        if not path:
            return

        if not path.lower().endswith("." + ext):
            path = path + "." + ext

        columns = self._model.columns()
        query = self._controller.snapshot_query()
        current_rows = self._model.rows() if mode == "current_page" else None

        req = self._ExportRequest(
            query=query,
            columns=columns,
            mode=mode,
            fmt=fmt,
            destination_path=path,
            report_title="Relatório",
            chunk_page_size=1000,
        )

        self._btn_export.setEnabled(False)
        self._lbl_page.setText("Exportando…")

        data_port = self._controller._port
        task = _ExportTask(self._export_uc, req, current_rows, data_port)

        task.signals.progress.connect(self._on_export_progress)
        task.signals.ok.connect(self._on_export_ok)
        task.signals.fail.connect(self._on_export_fail)
        self._pool.start(task)

    def _on_export_progress(self, done: int, total: int) -> None:
        if total <= 0:
            self._lbl_page.setText(f"Exportando… {done} itens")
            return
        self._lbl_page.setText(f"Exportando… {done}/{total}")

    def _on_export_ok(self, res) -> None:
        self._btn_export.setEnabled(True)
        self._update_footer()
        QMessageBox.information(self, "Exportação concluída", f"Arquivo gerado com sucesso:\n{res.path}\n\nLinhas: {res.rows_exported}")

    def _on_export_fail(self, exc: Exception) -> None:
        self._btn_export.setEnabled(True)
        self._update_footer()
        QMessageBox.critical(self, "Falha ao exportar", _safe_str(exc))


# -----------------------------
# Optional: In-memory adapter (demo / tests)
# -----------------------------

class InMemoryTablePort:
    def __init__(self, rows: List[dict]):
        self._rows = list(rows)
        self._norm_cache: List[dict] = []
        for r in self._rows:
            self._norm_cache.append({k: _norm_text(_safe_str(v).lower(), True) for k, v in r.items()})

    def _norm_cell(self, row_index: int, key: str, *, case_sensitive: bool, accent_insensitive: bool) -> str:
        if row_index < 0 or row_index >= len(self._rows):
            return ""
        if (not case_sensitive) and accent_insensitive:
            return self._norm_cache[row_index].get(key, "")

        v = _safe_str(self._rows[row_index].get(key, ""))
        if not case_sensitive:
            v = v.lower()
        if accent_insensitive:
            v = _norm_text(v, True)
        return v

    def fetch_page(self, query: TableQuery) -> TablePage:
        idxs: List[int] = list(range(len(self._rows)))

        s = query.search_text or ""
        mode = query.search_mode
        searchable = list(query.searchable_keys)

        if s:
            rx: Optional[re.Pattern[str]] = None
            if mode == "regex":
                try:
                    flags = 0 if query.search_case_sensitive else re.IGNORECASE
                    rx = re.compile(query.search_text, flags=flags)
                except re.error:
                    rx = None

            keys_for_search: Optional[List[str]] = searchable if searchable else None

            def match_norm(base: str) -> bool:
                if mode == "igual":
                    return base == s
                if mode == "comeca":
                    return base.startswith(s)
                if mode == "contem":
                    return s in base
                return s in base

            kept_idxs: List[int] = []
            for i in idxs:
                r = self._rows[i]
                keys = keys_for_search if keys_for_search is not None else list(r.keys())
                if mode == "regex":
                    if rx is None:
                        continue
                    for k in keys:
                        if rx.search(_safe_str(r.get(k))):
                            kept_idxs.append(i)
                            break
                else:
                    for k in keys:
                        base = self._norm_cell(
                            i,
                            k,
                            case_sensitive=query.search_case_sensitive,
                            accent_insensitive=query.search_accent_insensitive,
                        )
                        if match_norm(base):
                            kept_idxs.append(i)
                            break
            idxs = kept_idxs

        for f in query.filters:
            if f.op == "igual":
                idxs = [i for i in idxs if self._rows[i].get(f.key) == f.value]
            elif f.op == "contem":
                needle = _norm_text(_safe_str(f.value).lower(), True)
                idxs = [
                    i for i in idxs
                    if needle in self._norm_cell(i, f.key, case_sensitive=False, accent_insensitive=True)
                ]
            elif f.op == "gt":
                idxs = [i for i in idxs if self._rows[i].get(f.key) is not None and self._rows[i].get(f.key) > f.value]
            elif f.op == "lt":
                idxs = [i for i in idxs if self._rows[i].get(f.key) is not None and self._rows[i].get(f.key) < f.value]

        def sort_key(v: Any) -> Any:
            if v is None:
                return (1, "")
            if isinstance(v, (int, float)):
                return (0, v)
            return (0, _norm_text(_safe_str(v).lower(), True))

        for srt in reversed(query.sort):
            idxs = sorted(
                idxs,
                key=lambda i: sort_key(self._rows[i].get(srt.key)),
                reverse=not srt.ascending,
            )

        total = len(idxs)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_idxs = idxs[start:end]
        page_rows = [self._rows[i] for i in page_idxs]

        return TablePage(rows=page_rows, total_rows=total, page=query.page, page_size=query.page_size)
