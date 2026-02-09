from __future__ import annotations

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from qtpy.QtCore import QTimer, QLocale, QObject, Signal, QRunnable, QThreadPool
from qtpy.QtCore import QUrl
from qtpy.QtWidgets import QSizePolicy, QWidget, QLabel, QFileDialog
from qtpy.QtGui import QDesktopServices, QIcon

from app.core.ui import (
    apply_app_theme, repolish,
    ThemeMode, Density, set_theme_mode, set_density,

    TitleLabel, SubtitleLabel, MutedLabel, Badge,
    AppButton, PrimaryButton, GhostButton, DangerButton, AppToolButton,
    AppLineEdit, AppTextEdit, AppPlainTextEdit, AppComboBox,
    AppSpinBox, AppDoubleSpinBox, AppDateEdit, AppTimeEdit, AppDateTimeEdit,
    int_validator, money_validator,

    Card, Section, Divider, Toolbar,
    AppTableView, SimpleTableModel,
    AppDialog, DialogSizePreset,
    FormDialog, confirm_destructive,
    InlineStatus, AppProgressBar,
    vbox, hbox, AppScrollArea, AppMainWindow, AppApplication, AppMessageBox, AppTabWidget, AppMoneyLineEdit,
    AppTable, InMemoryTablePort, FilterSpec, SortSpec
)
from app.core.ui.icon_theme import IconTheme
from app.core.ui.theme_manager import ThemeManager
from app.core.ui.theme_types import ThemeSelection, ThemePaths
from app.core.ui.tables import TableQuery as UiTableQuery
from app.core.use_cases.export_table import ExportRequest as UseCaseExportRequest, ExportTableUseCase
from app.core.ports.exporter_registry import ExporterRegistry
from app.core.ports.table_exporter_port import ExportResult
from app.core.dto.export_dto import ExportRequest as DtoExportRequest
from app.core.ports.table_ports import TableQuery as PortTableQuery, FilterSpec as PortFilterSpec, SortSpec as PortSortSpec
from app.infra.export.excel.xlsx_exporter import XlsxTableExporter
from app.infra.export.pdf.pdf_exporter import PdfTableExporter
import time



class _WorkerSignals(QObject):
    progress = Signal(int, int)  # done, total
    finished = Signal(object)
    error = Signal(str)

class _Worker(QRunnable):
    def __init__(self, fn: Callable[[_WorkerSignals], object]):
        super().__init__()
        self._fn = fn
        self.signals = _WorkerSignals()

    def run(self) -> None:
        try:
            res = self._fn(self.signals)
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))


def _scrollable(content: QWidget) -> AppScrollArea:
    scroll = AppScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(AppScrollArea.NoFrame)
    scroll.setWidget(content)
    return scroll

@dataclass
class Product:
    id: int
    name: str
    cat: str
    price: float
    active: bool

class DemoWindow(AppMainWindow):
    def __init__(self, app: AppApplication):
        super().__init__()
        self._app = app
        self._thread_pool = QThreadPool.globalInstance()
        self._project_root = self._resolve_project_root()
        self.setWindowTitle("UI Components Demo (App*) — Theme • Density • Tables • Export • Ports")

        self._products = [
            Product(1, "Produto A", "A", 10.50, True),
            Product(2, "Produto B", "B", 25.00, True),
            Product(3, "Produto C", "C", 7.99, False),
            Product(4, "Produto D", "A", 99.90, True),
        ]

        root = QWidget()
        root_layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(root_layout)

        # Top control bar (theme + density)
        controls = self._build_controls()
        root_layout.addWidget(controls)
        root_layout.addWidget(Divider())

        tabs = AppTabWidget()
        tabs.addTab(_scrollable(self._tab_gallery()), "Gallery (All)")
        tabs.addTab(_scrollable(self._tab_typography()), "Typography")
        tabs.addTab(_scrollable(self._tab_buttons()), "Buttons")
        tabs.addTab(_scrollable(self._tab_inputs()), "Inputs")
        tabs.addTab(_scrollable(self._tab_containers()), "Containers")
        tabs.addTab(_scrollable(self._tab_views()), "Views")
        tabs.addTab(_scrollable(self._tab_feedback_dialogs()), "Feedback & Dialogs")
        tabs.addTab(_scrollable(self._tab_nextgen_tables()), "Next-Gen Tables")
        tabs.addTab(_scrollable(self._tab_theme_assets()), "Theme & Assets")
        tabs.addTab(_scrollable(self._tab_icon_theme()), "Icons")
        tabs.addTab(_scrollable(self._tab_export_showcase()), "Export (PDF/XLSX)")
        tabs.addTab(_scrollable(self._tab_ports_dtos()), "Ports & DTOs")
        tabs.addTab(_scrollable(self._tab_manifesto()), "Manifesto / About")
        tabs.addTab(self._tab_crud_mock(), "CRUD Mock")
        root_layout.addWidget(tabs, 1)

        self.setCentralWidget(root)

    def _build_controls(self) -> QWidget:
        bar = QWidget()
        l = hbox(spacing=10)
        bar.setLayout(l)

        l.addWidget(TitleLabel("UI Kit Demo"))
        l.addStretch(1)

        self.cmb_theme = AppComboBox(required=True)
        self.cmb_theme.set_items([("Dark", ThemeMode.DARK), ("Light", ThemeMode.LIGHT)])
        self.cmb_theme.setCurrentIndex(0)

        self.cmb_density = AppComboBox(required=True)
        self.cmb_density.set_items([("Compact", Density.COMPACT), ("Regular", Density.REGULAR), ("Comfortable", Density.COMFORTABLE)])
        self.cmb_density.setCurrentIndex(1)

        def apply_changes():
            mode = self.cmb_theme.currentData()
            dens = self.cmb_density.currentData()
            set_theme_mode(mode)
            set_density(dens)
            apply_app_theme(self._app)
            # repolish this window tree
            self._repolish_tree(self)
            self._on_theme_applied()

        l.addWidget(MutedLabel("Theme:"))
        l.addWidget(self.cmb_theme)
        l.addWidget(MutedLabel("Density:"))
        l.addWidget(self.cmb_density)
        l.addWidget(PrimaryButton("Apply", on_click=apply_changes))
        return bar

    def _repolish_tree(self, w: QWidget) -> None:
        repolish(w)
        for child in w.findChildren(QWidget):
            repolish(child)

    # -------------------------
    # Gallery tab (all quick)
    # -------------------------
    def _tab_gallery(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Gallery"))
        layout.addWidget(MutedLabel("Visão rápida de vários componentes lado a lado. Use Theme/Density no topo."))
        layout.addWidget(Divider())

        grid = QWidget()
        gl = hbox(spacing=14)
        grid.setLayout(gl)

        # Left: inputs
        left = Card()
        left.body.addWidget(SubtitleLabel("Inputs"))
        left.body.addWidget(MutedLabel("Required / Validator / State"))
        le1 = AppLineEdit(placeholder="Obrigatório...", required=True)
        le2 = AppLineEdit(placeholder="Inteiro 0..9999", validator=int_validator(0, 9999))
        le3 = AppMoneyLineEdit(prefix="R$", locale=QLocale(QLocale.Portuguese, QLocale.Brazil))
        left.body.addWidget(le1)
        left.body.addWidget(le2)
        left.body.addWidget(le3)
        btns = QWidget()
        bl = hbox(spacing=10)
        btns.setLayout(bl)
        bl.addWidget(PrimaryButton("Validate", on_click=lambda: [le1.validate_now(), le2.validate_now(), le3.validate_now()]))
        bl.addWidget(GhostButton("Clear state", on_click=lambda: [le1.clear_state(), le2.clear_state(), le3.clear_state()]))
        bl.addStretch(1)
        left.body.addWidget(btns)

        # Middle: buttons/status
        mid = Card()
        mid.body.addWidget(SubtitleLabel("Buttons & Status"))
        status = InlineStatus()
        mid.body.addWidget(status)
        r = QWidget()
        rl = hbox(spacing=10)
        r.setLayout(rl)
        rl.addWidget(AppButton("Info", on_click=lambda: status.show_info("Mensagem informativa.")))
        rl.addWidget(AppButton("Success", on_click=lambda: status.show_success("Operação OK.")))
        rl.addWidget(AppButton("Warning", on_click=lambda: status.show_warning("Atenção.")))
        rl.addWidget(AppButton("Error", on_click=lambda: status.show_error("Falhou.")))
        rl.addStretch(1)
        mid.body.addWidget(r)

        r2 = QWidget()
        r2l = hbox(spacing=10)
        r2.setLayout(r2l)
        r2l.addWidget(PrimaryButton("Primary"))
        r2l.addWidget(GhostButton("Ghost"))
        r2l.addWidget(DangerButton("Danger"))
        r2l.addStretch(1)
        mid.body.addWidget(r2)

        pb = AppProgressBar()
        pb.setValue(55)
        mid.body.addWidget(pb)

        # Right: table
        right = Card()
        right.body.addWidget(SubtitleLabel("Table"))
        table = AppTableView()
        table.setMinimumHeight(240)
        headers = ["ID", "Nome", "Categoria", "Preço", "Ativo"]
        columns = [
            lambda p: p.id,
            lambda p: p.name,
            lambda p: p.cat,
            lambda p: f"{p.price:.2f}",
            lambda p: "Sim" if p.active else "Não",
        ]
        model = SimpleTableModel(headers=headers, columns=columns, rows=self._products)
        table.setModel(model)
        right.body.addWidget(table)

        gl.addWidget(left, 1)
        gl.addWidget(mid, 1)
        gl.addWidget(right, 1)

        layout.addWidget(grid)
        layout.addStretch(1)
        return root

    # -------------------------
    # Tabs (detailed)
    # -------------------------
    def _tab_typography(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Typography"))
        layout.addWidget(SubtitleLabel("SubtitleLabel — Títulos de seção / cards"))
        layout.addWidget(MutedLabel("MutedLabel — Texto de apoio, descrição, hints, metadados."))
        layout.addWidget(Divider())

        row = QWidget()
        row_l = hbox(spacing=10)
        row.setLayout(row_l)

        b1 = Badge("Badge default")
        b2 = Badge("Badge success"); b2.set_state("success")
        b3 = Badge("Badge warning"); b3.set_state("warning")
        b4 = Badge("Badge error"); b4.set_state("error")

        row_l.addWidget(b1)
        row_l.addWidget(b2)
        row_l.addWidget(b3)
        row_l.addWidget(b4)
        row_l.addStretch(1)

        layout.addWidget(SubtitleLabel("Badges (com estados)"))
        layout.addWidget(row)
        layout.addStretch(1)
        return root

    def _tab_buttons(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Buttons"))
        layout.addWidget(MutedLabel("Botões com variantes e estados via properties."))
        layout.addWidget(Divider())

        toolbar = Toolbar()
        tb = toolbar.layout_row

        def on_click(name: str):
            AppMessageBox.information(self, "Click", f"Você clicou: {name}")

        tb.addWidget(AppToolButton("Tool", on_click=lambda: on_click("ToolButton")))
        tb.addWidget(AppToolButton("Outra ação", on_click=lambda: on_click("Outra ação")))
        tb.addStretch(1)
        layout.addWidget(SubtitleLabel("Toolbar (AppToolButton)"))
        layout.addWidget(toolbar)

        layout.addWidget(Divider())

        row = QWidget()
        row_l = hbox(spacing=10)
        row.setLayout(row_l)

        row_l.addWidget(AppButton("Default", on_click=lambda: on_click("Default")))
        row_l.addWidget(PrimaryButton("Primary", on_click=lambda: on_click("Primary")))
        row_l.addWidget(GhostButton("Ghost", on_click=lambda: on_click("Ghost")))
        row_l.addWidget(DangerButton("Danger", on_click=lambda: on_click("Danger")))
        row_l.addStretch(1)

        disabled = PrimaryButton("Disabled")
        disabled.setEnabled(False)
        row_l.addWidget(disabled)

        layout.addWidget(SubtitleLabel("Variantes"))
        layout.addWidget(row)

        layout.addWidget(Divider())

        states = QWidget()
        st_l = hbox(spacing=10)
        states.setLayout(st_l)

        btn_ok = AppButton("State: success"); btn_ok.set_state("success")
        btn_warn = AppButton("State: warning"); btn_warn.set_state("warning")
        btn_err = AppButton("State: error"); btn_err.set_state("error")

        st_l.addWidget(btn_ok)
        st_l.addWidget(btn_warn)
        st_l.addWidget(btn_err)
        st_l.addStretch(1)

        layout.addWidget(SubtitleLabel("Estados (via dynamicProperty state)"))
        layout.addWidget(states)

        layout.addStretch(1)
        return root

    def _tab_inputs(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Inputs"))
        layout.addWidget(MutedLabel(
            "Required/validator e state visual (error/success). Agora com uma vitrine avançada de Money Inputs."))
        layout.addWidget(Divider())

        # -------------------------
        # LineEdits básicos (já existia)
        # -------------------------
        card = Card()
        card.body.addWidget(SubtitleLabel("LineEdits"))
        card.body.addWidget(MutedLabel("Exemplos: obrigatório, int validator, money validator."))

        le_required = AppLineEdit(placeholder="Obrigatório...", required=True)
        le_int = AppLineEdit(placeholder="Apenas inteiros (0..9999)", validator=int_validator(0, 9999))
        le_money = AppLineEdit(placeholder="Dinheiro (0.00+)", validator=money_validator(2))

        validate_row = QWidget()
        vr = hbox(spacing=10)
        validate_row.setLayout(vr)

        def validate_all():
            results = [
                ("Obrigatório", le_required.validate_now()),
                ("Int", le_int.validate_now()),
                ("Money", le_money.validate_now()),
            ]
            msg = "\n".join(
                [f"- {name}: {'OK' if r.ok else 'ERRO'} {('— ' + r.message) if r.message else ''}" for name, r in
                 results])
            AppMessageBox.information(self, "Validação", msg)

        vr.addWidget(PrimaryButton("Validar agora", on_click=validate_all))
        vr.addWidget(
            GhostButton("Limpar estados", on_click=lambda: [w.clear_state() for w in (le_required, le_int, le_money)]))
        vr.addStretch(1)

        card.body.addWidget(MutedLabel("Obrigatório:"))
        card.body.addWidget(le_required)
        card.body.addWidget(MutedLabel("Inteiro:"))
        card.body.addWidget(le_int)
        card.body.addWidget(MutedLabel("Dinheiro:"))
        card.body.addWidget(le_money)
        card.body.addWidget(validate_row)

        layout.addWidget(card)
        layout.addWidget(Divider())

        # -------------------------
        # VITRINE: AppMoneyLineEdit (Nível mercado)
        # -------------------------
        money_card = Card()
        money_card.body.addWidget(SubtitleLabel("Money Inputs — AppMoneyLineEdit (nível mercado)"))
        money_card.body.addWidget(MutedLabel(
            "Teste tudo: locale, prefix/suffix, agrupamento, soft-format, cents-mode (PDV/banco), negativos, decimais variados e paste-friendly."
        ))

        # Helpers
        def _section_title(text: str) -> QWidget:
            w = QWidget()
            l = hbox(spacing=10)
            w.setLayout(l)
            b = Badge(text)
            b.set_state("success")
            l.addWidget(b)
            l.addStretch(1)
            return w

        def _row2(a: QWidget, b: QWidget) -> QWidget:
            r = QWidget()
            rl = hbox(spacing=12)
            r.setLayout(rl)
            rl.addWidget(a, 1)
            rl.addWidget(b, 1)
            return r

        def _row3(a: QWidget, b: QWidget, c: QWidget) -> QWidget:
            r = QWidget()
            rl = hbox(spacing=12)
            r.setLayout(rl)
            rl.addWidget(a, 1)
            rl.addWidget(b, 1)
            rl.addWidget(c, 1)
            return r

        # (A) BRL / Locale pt-BR
        money_card.body.addWidget(_section_title("BRL • pt-BR • formatos essenciais"))

        m_brl_basic = AppMoneyLineEdit(
            prefix="R$",
            locale=QLocale(QLocale.Portuguese, QLocale.Brazil),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            placeholder="Ex.: 1.234,56",
        )

        m_brl_cents = AppMoneyLineEdit(
            prefix="R$",
            locale=QLocale(QLocale.Portuguese, QLocale.Brazil),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=True,  # <- comportamento tipo banco/PDV
            allow_negative=False,
            placeholder="Cents mode: digite 1 2 3… → 0,01 0,12 1,23",
        )

        m_brl_cents_neg = AppMoneyLineEdit(
            prefix="BRL",
            locale=QLocale(QLocale.Portuguese, QLocale.Brazil),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=True,
            allow_negative=True,  # <- toggle com "-"
            placeholder="Cents + negativo: '-' alterna sinal",
        )

        money_card.body.addWidget(MutedLabel("BRL básico (soft-format + agrupamento):"))
        money_card.body.addWidget(m_brl_basic)
        money_card.body.addWidget(MutedLabel("BRL cents-mode (mercado: digite só números):"))
        money_card.body.addWidget(m_brl_cents)
        money_card.body.addWidget(MutedLabel("BRL cents-mode + negativo (toggle '-'):"))
        money_card.body.addWidget(m_brl_cents_neg)

        money_card.body.addWidget(Divider())

        # (B) USD / Locale en-US
        money_card.body.addWidget(_section_title("USD • en-US • separadores e agrupamento"))

        m_usd_basic = AppMoneyLineEdit(
            prefix="USD",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            placeholder="Ex.: 1,234.56",
        )

        m_usd_cents = AppMoneyLineEdit(
            prefix="USD",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=True,
            allow_negative=False,
            placeholder="Cents mode: 1 2 3 → 0.01 0.12 1.23",
        )

        money_card.body.addWidget(_row2(m_usd_basic, m_usd_cents))

        money_card.body.addWidget(Divider())

        # (C) EUR • 4 decimais / sem auto-format
        money_card.body.addWidget(_section_title("EUR • 4 decimais • modo precisão"))

        m_eur_prec = AppMoneyLineEdit(
            prefix="EUR",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),  # intencional: mostrar separador '.' com 4 dec
            decimals=4,
            grouping_enabled=True,
            auto_format_on_change=False,
            cents_mode=False,
            allow_negative=False,
            placeholder="Ex.: 12,345.6789 (ou 12345.6789 dependendo do locale)",
        )

        m_eur_prec_soft = AppMoneyLineEdit(
            prefix="EUR",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),
            decimals=4,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            placeholder="4 dec + soft-format (agrupa enquanto digita)",
        )

        m_eur_cents4 = AppMoneyLineEdit(
            prefix="EUR",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),
            decimals=4,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=True,  # 4 “casas”: digitar vira base 10^4 (ótimo p/ cripto / taxas / juros)
            allow_negative=False,
            placeholder="Cents mode com 4 casas (taxas/cripto): 1 → 0.0001",
        )

        money_card.body.addWidget(_row3(m_eur_prec_soft, m_eur_prec, m_eur_cents4))

        money_card.body.addWidget(Divider())

        money_card.body.addWidget(_section_title("Separadores forçados • padronização global"))

        m_forced_pt = AppMoneyLineEdit(
            prefix="R$",
            locale=QLocale(QLocale.English, QLocale.UnitedStates),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            decimal_sep=",",
            group_sep=".",
            placeholder="Forçado pt-BR: 1.234,56 (mesmo em en-US)",
        )

        m_forced_us = AppMoneyLineEdit(
            prefix="USD",
            locale=QLocale(QLocale.Portuguese, QLocale.Brazil),
            decimals=2,
            grouping_enabled=True,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            decimal_sep=".",
            group_sep=",",
            placeholder="Forçado en-US: 1,234.56 (mesmo em pt-BR)",
        )

        m_no_group = AppMoneyLineEdit(
            prefix="R$",
            locale=QLocale(QLocale.Portuguese, QLocale.Brazil),
            decimals=2,
            grouping_enabled=False,
            auto_format_on_change=True,
            cents_mode=False,
            allow_negative=False,
            placeholder="Sem agrupamento: 1234567,89",
        )

        money_card.body.addWidget(_row3(m_forced_pt, m_forced_us, m_no_group))

        money_card.body.addWidget(Divider())

        money_card.body.addWidget(_section_title("Ações rápidas • set_value • paste-friendly"))

        hint = MutedLabel(
            "Cole textos como: 'R$ 1.234,56', 'USD -1,234.56', '  9999999  ' — o input sanitiza e normaliza."
        )
        money_card.body.addWidget(hint)

        actions = QWidget()
        al = hbox(spacing=10)
        actions.setLayout(al)

        money_inputs = [
            m_brl_basic, m_brl_cents, m_brl_cents_neg,
            m_usd_basic, m_usd_cents,
            m_eur_prec_soft, m_eur_prec, m_eur_cents4,
            m_forced_pt, m_forced_us, m_no_group,
        ]

        def clear_all_money():
            for w in money_inputs:
                w.setText("")
                w.clear_state()

        def set_examples():
            # exemplos grandes e variados
            m_brl_basic.set_value("1234567.89")
            m_brl_cents.setText("")  # cents mode: deixa usuário digitar
            m_brl_cents_neg.set_value("-98765.43")

            m_usd_basic.set_value("1234567.89")
            m_usd_cents.setText("")

            m_eur_prec_soft.set_value("12345.6789")
            m_eur_prec.set_value("999999.0001")
            m_eur_cents4.setText("")

            m_forced_pt.set_value("1234567.89")
            m_forced_us.set_value("1234567.89")
            m_no_group.set_value("1234567.89")

        def validate_money():
            results = []
            for w in money_inputs:
                r = w.validate_now()
                label = (w.placeholderText() or w.__class__.__name__)
                results.append((label, r))
            msg = "\n".join(
                [f"- {name}: {'OK' if r.ok else 'ERRO'} {('— ' + r.message) if r.message else ''}" for name, r in
                 results])
            AppMessageBox.information(self, "Validação Money", msg)

        def show_values():
            lines = []
            for w in money_inputs:
                v = w.value()
                lines.append(
                    f"- {w.prefixText() if hasattr(w, 'prefixText') else (w.text()[:12] + '…' if len(w.text()) > 12 else w.text())}: {v}")
            AppMessageBox.information(self, "Valores (Decimal)", "\n".join(lines))

        al.addWidget(PrimaryButton("Preencher exemplos", on_click=set_examples))
        al.addWidget(AppButton("Validar todos", on_click=validate_money))
        al.addWidget(GhostButton("Limpar tudo", on_click=clear_all_money))
        al.addStretch(1)

        money_card.body.addWidget(actions)

        layout.addWidget(money_card)
        layout.addWidget(Divider())

        # -------------------------
        # Text areas (já existia)
        # -------------------------
        card2 = Card()
        card2.body.addWidget(SubtitleLabel("Text Areas"))
        te = AppTextEdit(placeholder="QTextEdit (descrições longas)...", required=False)
        pte = AppPlainTextEdit(placeholder="QPlainTextEdit (logs / texto puro)...", required=False)

        card2.body.addWidget(MutedLabel("AppTextEdit:"))
        card2.body.addWidget(te)
        card2.body.addWidget(MutedLabel("AppPlainTextEdit:"))
        card2.body.addWidget(pte)

        layout.addWidget(card2)
        layout.addWidget(Divider())

        # -------------------------
        # Combo/Spin/Date-Time (já existia)
        # -------------------------
        card3 = Card()
        card3.body.addWidget(SubtitleLabel("Combo / Spin / Date-Time"))

        cb = AppComboBox(required=True)
        cb.set_items(
            [("Categoria A", "A"), ("Categoria B", "B"), ("Categoria C", "C")],
            include_empty=True,
            empty_label="Selecione uma categoria..."
        )

        sp = AppSpinBox(minimum=0, maximum=999)
        dsp = AppDoubleSpinBox(minimum=0.0, maximum=999999.0, decimals=2)

        de = AppDateEdit()
        te2 = AppTimeEdit()
        dte = AppDateTimeEdit()

        validate_row2 = QWidget()
        vr2 = hbox(spacing=10)
        validate_row2.setLayout(vr2)

        def validate_combo():
            r = cb.validate_now()
            AppMessageBox.information(self, "Combo validation", "OK" if r.ok else f"ERRO: {r.message}")

        vr2.addWidget(PrimaryButton("Validar Combo", on_click=validate_combo))
        vr2.addWidget(GhostButton("Reset state", on_click=lambda: cb.clear_state()))
        vr2.addStretch(1)

        card3.body.addWidget(MutedLabel("Combo (required):"))
        card3.body.addWidget(cb)
        card3.body.addWidget(validate_row2)

        row = QWidget()
        row_l = hbox(spacing=10)
        row.setLayout(row_l)
        row_l.addWidget(sp)
        row_l.addWidget(dsp)
        row_l.addWidget(de)
        row_l.addWidget(te2)
        row_l.addWidget(dte)
        row_l.addStretch(1)

        card3.body.addWidget(MutedLabel("Spin / DoubleSpin / Date / Time / DateTime:"))
        card3.body.addWidget(row)

        layout.addWidget(card3)
        layout.addStretch(1)
        return root

    def _tab_containers(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Containers"))
        layout.addWidget(MutedLabel("Card, Section, Divider e Toolbar para estruturar telas de CRUD."))
        layout.addWidget(Divider())

        section = Section("Section exemplo", "Subtítulo opcional para orientar o usuário.")
        section.content.addWidget(MutedLabel("Dentro de section.content você adiciona layouts/widgets da tela."))
        section.content.addWidget(PrimaryButton("Ação de exemplo"))
        layout.addWidget(section)

        layout.addWidget(Divider())

        card = Card()
        card.body.addWidget(SubtitleLabel("Card"))
        card.body.addWidget(MutedLabel("Cards são ótimos para agrupar formulários, filtros e blocos de informação."))
        card.body.addWidget(AppLineEdit(placeholder="Exemplo de campo dentro do card"))
        layout.addWidget(card)

        layout.addStretch(1)
        return root

    def _tab_views(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Views"))
        layout.addWidget(MutedLabel("Tabela padrão com SimpleTableModel (ideal para listagem CRUD)."))
        layout.addWidget(Divider())

        table = AppTableView()
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        headers = ["ID", "Nome", "Categoria", "Preço", "Ativo"]
        rows = self._products
        columns = [
            lambda p: p.id,
            lambda p: p.name,
            lambda p: p.cat,
            lambda p: f"{p.price:.2f}",
            lambda p: "Sim" if p.active else "Não",
        ]
        model = SimpleTableModel(headers=headers, columns=columns, rows=rows)
        table.setModel(model)

        toolbar = Toolbar()
        tb = toolbar.layout_row

        search = AppLineEdit(placeholder="Buscar por nome...")
        search.setMaximumWidth(320)

        def do_filter():
            q = search.text().strip().lower()
            if not q:
                model.set_rows(rows)
                return
            model.set_rows([p for p in rows if q in p.name.lower()])

        tb.addWidget(search)
        tb.addWidget(PrimaryButton("Buscar", on_click=do_filter))
        tb.addWidget(GhostButton("Limpar", on_click=lambda: (search.setText(""), model.set_rows(rows))))
        tb.addStretch(1)

        def selected_info():
            idx = table.selectionModel().currentIndex()
            if not idx.isValid():
                AppMessageBox.information(self, "Seleção", "Nenhuma linha selecionada.")
                return
            p = model.row_at(idx.row())
            AppMessageBox.information(self, "Seleção", f"Selecionado: {p}")

        tb.addWidget(AppButton("Ver selecionado", on_click=selected_info))

        layout.addWidget(toolbar)
        layout.addWidget(table, 1)

        layout.addStretch(1)
        return root

    def _tab_feedback_dialogs(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Feedback & Dialogs"))
        layout.addWidget(MutedLabel("InlineStatus, ProgressBar, FormDialog e confirmação destrutiva."))
        layout.addWidget(Divider())

        card = Card()
        card.body.addWidget(SubtitleLabel("InlineStatus"))
        status = InlineStatus()
        card.body.addWidget(status)

        row = QWidget()
        row_l = hbox(spacing=10)
        row.setLayout(row_l)

        row_l.addWidget(AppButton("Info", on_click=lambda: status.show_info("Mensagem informativa.")))
        row_l.addWidget(AppButton("Success", on_click=lambda: status.show_success("Operação concluída com sucesso.")))
        row_l.addWidget(AppButton("Warning", on_click=lambda: status.show_warning("Atenção: verifique os dados.")))
        row_l.addWidget(AppButton("Error", on_click=lambda: status.show_error("Falha ao executar a operação.")))
        row_l.addWidget(GhostButton("Ocultar", on_click=status.hide))
        row_l.addStretch(1)

        card.body.addWidget(row)
        layout.addWidget(card)

        layout.addWidget(Divider())

        card2 = Card()
        card2.body.addWidget(SubtitleLabel("ProgressBar"))

        pb = AppProgressBar()
        pb.setValue(35)

        row2 = QWidget()
        row2_l = hbox(spacing=10)
        row2.setLayout(row2_l)

        def set_pb(v: int):
            pb.setValue(v)

        row2_l.addWidget(AppButton("0%", on_click=lambda: set_pb(0)))
        row2_l.addWidget(AppButton("35%", on_click=lambda: set_pb(35)))
        row2_l.addWidget(AppButton("70%", on_click=lambda: set_pb(70)))
        row2_l.addWidget(AppButton("100%", on_click=lambda: set_pb(100)))
        row2_l.addStretch(1)

        card2.body.addWidget(pb)
        card2.body.addWidget(row2)
        layout.addWidget(card2)

        layout.addWidget(Divider())

        card3 = Card()
        card3.body.addWidget(SubtitleLabel("Dialogs"))
        card3.body.addWidget(MutedLabel("Demonstração: FormDialog (simples) e AppDialog (super-wrapper: header actions + presets + loading)."))

        def open_super_dialog():
            dlg = AppDialog(
                title="AppDialog (Super) — exemplo",
                subtitle="Header actions • Presets • Loading overlay • Resize grip",
                parent=self,
                size=DialogSizePreset.LG,
                resizable=True,
                show_size_grip=True,
                allow_close_on_escape=True,
            )

            # Header actions (top-right)
            dlg.add_header_action("Ajuda", tooltip="Mostra dicas rápidas", on_click=lambda: AppMessageBox.information(dlg, "Ajuda", "Exemplo de header action."))
            dlg.add_header_action("Recarregar", tooltip="Simula uma operação", on_click=lambda: start_loading())

            # Body content
            dlg.body.addWidget(SubtitleLabel("Conteúdo"))
            dlg.body.addWidget(MutedLabel("Use os botões abaixo para simular uma operação em background com overlay bloqueante."))

            btn_row = QWidget()
            br = hbox(spacing=10)
            btn_row.setLayout(br)

            def stop_loading():
                dlg.set_loading(False)

            def start_loading():
                # loading com cancelamento + bloqueio de fechamento enquanto carrega
                dlg.set_loading(
                    True,
                    title="Processando…",
                    subtitle="Simulando tarefa pesada (2s).",
                    cancellable=True,
                    on_cancel=stop_loading,
                    block_close=True,
                )
                QTimer.singleShot(2000, stop_loading)

            br.addWidget(PrimaryButton("Iniciar loading (2s)", on_click=start_loading))
            br.addWidget(GhostButton("Parar loading", on_click=stop_loading))
            br.addStretch(1)

            dlg.body.addWidget(btn_row)

            # Footer (override padrão)
            dlg.set_footer_buttons(
                primary_text="OK",
                primary_cb=dlg.accept,
                secondary_text="Fechar",
                secondary_cb=dlg.reject,
            )

            dlg.exec()

        def open_form_dialog():
            dlg = FormDialog("FormDialog (exemplo)", "Base para telas Adicionar/Editar.")

            name = AppLineEdit(placeholder="Nome (obrigatório)", required=True)
            desc = AppTextEdit(placeholder="Descrição")

            dlg.body.addWidget(MutedLabel("Nome:"))
            dlg.body.addWidget(name)
            dlg.body.addWidget(MutedLabel("Descrição:"))
            dlg.body.addWidget(desc)

            def validate():
                r = name.validate_now()
                if not r.ok:
                    return False, r.message
                return True, ""

            dlg.validate = validate  # override

            if dlg.exec() == FormDialog.Accepted:
                AppMessageBox.information(self, "Salvo", f"Nome: {name.text().strip()}\nDescrição: {desc.text_value().strip()}")

        def open_confirm():
            ok = confirm_destructive(
                self,
                title="Confirmar exclusão",
                text="Essa ação não pode ser desfeita. Deseja excluir mesmo?",
                confirm_label="Excluir",
            )
            AppMessageBox.information(self, "Resultado", "Confirmado" if ok else "Cancelado")

        row3 = QWidget()
        row3_l = hbox(spacing=10)
        row3.setLayout(row3_l)

        row3_l.addWidget(PrimaryButton("Abrir FormDialog", on_click=open_form_dialog))
        row3_l.addWidget(AppButton("Abrir AppDialog (Super)", on_click=open_super_dialog))
        row3_l.addWidget(DangerButton("Confirmar exclusão", on_click=open_confirm))
        row3_l.addStretch(1)

        card3.body.addWidget(row3)
        layout.addWidget(card3)

        layout.addStretch(1)
        return root


    # -------------------------
    # Next-Gen Tables (SmartTableWidget)
    # -------------------------
    def _tab_nextgen_tables(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Next-Gen Tables — SmartTableWidget"))
        layout.addWidget(MutedLabel(
            "Demonstração avançada do novo componente de tabela: paginação híbrida, cursor-down paging, infinite scroll, "
            "busca global (contains/starts_with/equals/regex), filtros por coluna (menu no header) e exportação PDF/XLSX."
        ))
        layout.addWidget(Divider())

        def make_card(title: str, subtitle: str) -> Card:
            c = Card()
            c.body.addWidget(SubtitleLabel(title))
            c.body.addWidget(MutedLabel(subtitle))
            return c

        class SlowPort:
            def __init__(self, base: InMemoryTablePort, delay_ms: int = 220):
                self._base = base
                self._delay = max(0, int(delay_ms))

            def fetch_page(self, query):
                if self._delay:
                    time.sleep(self._delay / 1000.0)
                return self._base.fetch_page(query)

        def bind_signals(table: AppTable, title: str) -> None:
            table.row_activated.connect(lambda row: AppMessageBox.information(self, "Row activated", f"[{title}]\n{row}"))
            table.selection_changed.connect(lambda row: self._on_table_selection(title, row))

        # -------------------------
        # Dataset 1: Produtos (CRUD-like)
        # -------------------------
        products_rows: List[dict] = []
        cats = ["A", "B", "C", "D"]
        for i in range(1, 601):
            products_rows.append({
                "id": i,
                "name": f"Produto {i:04d}",
                "cat": cats[i % len(cats)],
                "price": round((i * 1.37) % 250 + 9.9, 2),
                "active": (i % 7) != 0,
                "min_stock": (i % 5) * 3,
                "stock": (i * 11) % 120,
            })

        p_columns = [
            ("id", "ID"),
            ("name", "Nome"),
            ("cat", "Categoria"),
            ("price", "Preço"),
            ("stock", "Estoque"),
            ("min_stock", "Min"),
            ("active", "Ativo"),
        ]

        card1 = make_card(
            "Exemplo 1 — Produtos (600 linhas)",
            "Use a busca global. Clique com o botão direito no header para criar filtro por coluna. "
            "Role até o final ou use a seta ↓ no último item para carregar mais páginas (append)."
        )

        port1 = SlowPort(InMemoryTablePort(products_rows), delay_ms=180)
        t1 = AppTable(port=port1, columns=p_columns)
        t1.set_searchable_keys(["id", "name", "cat", "price", "stock", "active"])
        bind_signals(t1, "Produtos")
        t1.set_sort([SortSpec("name", True)])

        card1.body.addWidget(t1, 1)
        layout.addWidget(card1)

        layout.addWidget(Divider())

        # -------------------------
        # Dataset 2: Clientes (muito texto + regex)
        # -------------------------
        customers_rows: List[dict] = []
        cities = ["Uberlândia", "Araguari", "Patos de Minas", "São Paulo", "Campinas", "Curitiba", "Brasília"]
        tags = ["vip", "novo", "inadimplente", "regular", "lead", "parceiro"]
        for i in range(1, 1501):
            customers_rows.append({
                "id": i,
                "name": f"Cliente {i:05d}",
                "email": f"cliente{i:05d}@exemplo.com",
                "phone": f"+55 (34) 9{i%10}{(i*7)%10}{(i*3)%10}{(i*9)%10}-{(i*13)%10000:04d}",
                "city": cities[i % len(cities)],
                "tag": tags[i % len(tags)],
                "active": (i % 11) != 0,
                "notes": f"Observação {i} — contrato {(i%4)+1} — prioridade {(i%3)+1}",
            })

        c_columns = [
            ("id", "ID"),
            ("name", "Nome"),
            ("email", "Email"),
            ("phone", "Telefone"),
            ("city", "Cidade"),
            ("tag", "Tag"),
            ("active", "Ativo"),
        ]

        card2 = make_card(
            "Exemplo 2 — Clientes (1500 linhas)",
            "Teste o modo REGEX na busca (ex.: '^Cliente 00[1-9]' ou 'cliente0(12|34)'). "
            "Aqui a tabela fica ótima para cadastros extensos e buscas rápidas."
        )

        port2 = SlowPort(InMemoryTablePort(customers_rows), delay_ms=250)
        t2 = AppTable(port=port2, columns=c_columns)
        t2.set_searchable_keys(["id", "name", "email", "phone", "city", "tag"])
        bind_signals(t2, "Clientes")
        t2.set_filters([FilterSpec("active", "equals", True)])
        t2.set_sort([SortSpec("city", True), SortSpec("name", True)])

        card2.body.addWidget(t2, 1)
        layout.addWidget(card2)

        layout.addWidget(Divider())

        # -------------------------
        # Dataset 3: Tarefas (prioridade/status/prazo)
        # -------------------------
        tasks_rows: List[dict] = []
        statuses = ["Backlog", "Em andamento", "Bloqueada", "Concluída"]
        prios = ["Baixa", "Média", "Alta", "Crítica"]
        owners = ["Diego", "Ana", "Bruno", "Carla", "Equipe"]

        for i in range(1, 901):
            tasks_rows.append({
                "id": i,
                "title": f"Tarefa {i:04d} — Ajuste no módulo {(i%3)+1}",
                "status": statuses[i % len(statuses)],
                "priority": prios[(i * 3) % len(prios)],
                "owner": owners[i % len(owners)],
                "due_days": (i % 45),
                "customer_id": (i % 200) if (i % 4) == 0 else None,
            })

        t_columns = [
            ("id", "ID"),
            ("title", "Título"),
            ("status", "Status"),
            ("priority", "Prioridade"),
            ("owner", "Responsável"),
            ("due_days", "Prazo (dias)"),
            ("customer_id", "Cliente"),
        ]

        card3 = make_card(
            "Exemplo 3 — Tarefas (900 linhas)",
            "Exemplo com campos típicos de workflow: status, prioridade, responsável e prazo. "
            "Use filtros no header para encontrar rapidamente 'Crítica' ou 'Bloqueada'."
        )

        port3 = SlowPort(InMemoryTablePort(tasks_rows), delay_ms=200)
        t3 = AppTable(port=port3, columns=t_columns)
        t3.set_searchable_keys(["id", "title", "status", "priority", "owner", "customer_id"])
        bind_signals(t3, "Tarefas")
        t3.set_sort([SortSpec("priority", False), SortSpec("due_days", True)])

        card3.body.addWidget(t3, 1)
        layout.addWidget(card3)

        layout.addStretch(1)
        return root

    def _on_table_selection(self, title: str, row: Optional[dict]) -> None:
        if row is None:
            return
        self.statusBar().showMessage(f"[{title}] Selecionado: {row.get('id')}", 1200)

    # -------------------------
    # CRUD Mock tab
    # -------------------------
    def _tab_crud_mock(self) -> QWidget:
        page = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        page.setLayout(layout)

        layout.addWidget(TitleLabel("CRUD Mock — Produtos"))
        layout.addWidget(MutedLabel("Mock completo: filtros + tabela + ações + dialog Add/Edit. Sem BD ainda (in-memory)."))
        layout.addWidget(Divider())

        # Filters card
        filters = Card()
        filters.body.addWidget(SubtitleLabel("Filtros"))

        row = QWidget()
        rl = hbox(spacing=10)
        row.setLayout(rl)

        self.f_search = AppLineEdit(placeholder="Buscar por nome...")
        self.f_search.setMaximumWidth(320)

        self.f_cat = AppComboBox(required=False)
        self.f_cat.set_items([("Todas", None), ("Categoria A", "A"), ("Categoria B", "B"), ("Categoria C", "C")])
        self.f_cat.setCurrentIndex(0)

        self.f_active = AppComboBox(required=False)
        self.f_active.set_items([("Todos", None), ("Ativos", True), ("Inativos", False)])
        self.f_active.setCurrentIndex(0)

        rl.addWidget(self.f_search)
        rl.addWidget(self.f_cat)
        rl.addWidget(self.f_active)
        rl.addStretch(1)

        btn_apply = PrimaryButton("Aplicar", on_click=self._apply_filters)
        btn_clear = GhostButton("Limpar", on_click=self._clear_filters)
        rl.addWidget(btn_apply)
        rl.addWidget(btn_clear)

        filters.body.addWidget(row)
        layout.addWidget(filters)

        # Actions toolbar
        actions = Toolbar()
        al = actions.layout_row

        al.addWidget(PrimaryButton("Adicionar", on_click=self._add_product))
        al.addWidget(AppButton("Editar", on_click=self._edit_selected))
        al.addWidget(DangerButton("Excluir", on_click=self._delete_selected))
        al.addStretch(1)

        self.status = InlineStatus()
        al.addWidget(self.status)

        layout.addWidget(actions)

        # Table
        self.table = AppTableView()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._model = SimpleTableModel(
            headers=["ID", "Nome", "Categoria", "Preço", "Ativo"],
            columns=[
                lambda p: p.id,
                lambda p: p.name,
                lambda p: p.cat,
                lambda p: f"{p.price:.2f}",
                lambda p: "Sim" if p.active else "Não",
            ],
            rows=list(self._products),
        )
        self.table.setModel(self._model)
        layout.addWidget(self.table, 1)

        self._apply_filters()
        return page

    def _apply_filters(self):
        q = self.f_search.text().strip().lower()
        cat = self.f_cat.currentData()
        active = self.f_active.currentData()

        rows = list(self._products)
        if q:
            rows = [p for p in rows if q in p.name.lower()]
        if cat is not None:
            rows = [p for p in rows if p.cat == cat]
        if active is not None:
            rows = [p for p in rows if p.active == active]

        self._model.set_rows(rows)
        self.status.show_info(f"{len(rows)} item(ns)")

    def _clear_filters(self):
        self.f_search.setText("")
        self.f_cat.setCurrentIndex(0)
        self.f_active.setCurrentIndex(0)
        self._apply_filters()

    def _selected_product(self) -> Product | None:
        idx = self.table.selectionModel().currentIndex()
        if not idx.isValid():
            return None
        return self._model.row_at(idx.row())

    def _add_product(self):
        dlg = self._product_dialog("Adicionar produto")
        if dlg.exec() == FormDialog.Accepted:
            p = dlg._result
            self._products.append(p)
            self._apply_filters()
            self.status.show_success("Adicionado.")

    def _edit_selected(self):
        p = self._selected_product()
        if not p:
            self.status.show_warning("Selecione um item.")
            return

        dlg = self._product_dialog("Editar produto", initial=p)
        if dlg.exec() == FormDialog.Accepted:
            newp = dlg._result
            for i, it in enumerate(self._products):
                if it.id == p.id:
                    self._products[i] = newp
                    break
            self._apply_filters()
            self.status.show_success("Atualizado.")

    def _delete_selected(self):
        p = self._selected_product()
        if not p:
            self.status.show_warning("Selecione um item.")
            return

        ok = confirm_destructive(self, "Excluir produto", f"Excluir '{p.name}'?")
        if not ok:
            self.status.show_info("Cancelado.")
            return

        self._products = [it for it in self._products if it.id != p.id]
        self._apply_filters()
        self.status.show_success("Excluído.")

    def _product_dialog(self, title: str, initial: Product | None = None) -> FormDialog:
        dlg = FormDialog(title, "Preencha os campos e clique em salvar.")

        name = AppLineEdit(placeholder="Nome (obrigatório)", required=True)
        price = AppLineEdit(placeholder="Preço (ex: 10.50)", validator=money_validator(2), required=True)
        cat = AppComboBox(required=True)
        cat.set_items([("Categoria A", "A"), ("Categoria B", "B"), ("Categoria C", "C")], include_empty=True, empty_label="Selecione...")
        active = AppComboBox(required=True)
        active.set_items([("Ativo", True), ("Inativo", False)])

        if initial:
            name.setText(initial.name)
            price.setText(f"{initial.price:.2f}")
            # set category index
            for i in range(cat.count()):
                if cat.itemData(i) == initial.cat:
                    cat.setCurrentIndex(i)
                    break
            for i in range(active.count()):
                if active.itemData(i) == initial.active:
                    active.setCurrentIndex(i)
                    break

        dlg.body.addWidget(MutedLabel("Nome:"))
        dlg.body.addWidget(name)
        dlg.body.addWidget(MutedLabel("Categoria:"))
        dlg.body.addWidget(cat)
        dlg.body.addWidget(MutedLabel("Preço:"))
        dlg.body.addWidget(price)
        dlg.body.addWidget(MutedLabel("Status:"))
        dlg.body.addWidget(active)

        def validate():
            r1 = name.validate_now()
            r2 = cat.validate_now()
            r3 = price.validate_now()
            r4 = active.validate_now()
            ok = all([r1.ok, r2.ok, r3.ok, r4.ok])
            if not ok:
                return False, "Revise os campos marcados."
            return True, ""

        def on_accept():
            # id
            pid = initial.id if initial else (max([p.id for p in self._products], default=0) + 1)
            dlg._result = Product(
                id=pid,
                name=name.text().strip(),
                cat=cat.currentData(),
                price=float(price.text().replace(",", ".").strip()),
                active=bool(active.currentData()),
            )

        dlg.validate = validate
        dlg.accepted.connect(on_accept)
        return dlg

    def _resolve_project_root(self) -> Path:
        override = os.getenv("APP_PROJECT_ROOT", "").strip()
        if override:
            return Path(override).expanduser().resolve()
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "executable", os.getcwd())).resolve().parent
        return Path.cwd().resolve()
        if env and (env / "assets").exists():
            return env
        return p

    def _current_selection(self) -> ThemeSelection:
        mode = self.cmb_theme.currentData()
        dens = self.cmb_density.currentData()
        return ThemeSelection.with_(mode, dens)

    def _on_theme_applied(self) -> None:
        for fn in getattr(self, "_theme_refresh_hooks", []):
            try:
                fn()
            except Exception:
                pass

    def _tab_theme_assets(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Theme Engine & Assets"))
        layout.addWidget(MutedLabel(
            "Mostra a infraestrutura de tema: tokens (JSON), QSS com template tokens, manifest de includes e integração com IconTheme."
        ))
        layout.addWidget(Divider())

        card = Card()
        card.body.addWidget(SubtitleLabel("Tema compilado (ThemeManager)"))
        info = AppPlainTextEdit()
        info.setReadOnly(True)
        info.setMinimumHeight(220)
        card.body.addWidget(info)

        icons_row = QWidget()
        icons_row.setLayout(hbox(spacing=14))
        lbl1 = QLabel()
        lbl2 = QLabel()
        icons_row.layout().addWidget(lbl1)
        icons_row.layout().addWidget(lbl2)
        icons_row.layout().addStretch(1)
        card.body.addWidget(icons_row)

        layout.addWidget(card)

        files = Card()
        files.body.addWidget(SubtitleLabel("Arquivos do tema (assets/)"))
        files.body.addWidget(MutedLabel(str(self._project_root)))
        listing = AppPlainTextEdit()
        listing.setReadOnly(True)
        listing.setMinimumHeight(240)
        files.body.addWidget(listing)
        layout.addWidget(files)

        def refresh():
            sel = self._current_selection()
            paths = ThemePaths(self._project_root)
            tm = ThemeManager(self._project_root, selection=sel, dev_hot_reload=False)
            compiled = tm.compile(sel)
            tokens = compiled.tokens
            pick = {
                "fingerprint": compiled.fingerprint,
                "theme": str(sel.theme),
                "density": str(sel.density),
                "colors.primary": tokens.get("colors", {}).get("primary"),
                "colors.bg": tokens.get("colors", {}).get("bg"),
                "colors.text_primary": tokens.get("colors", {}).get("text_primary"),
                "metrics.pad_sm": tokens.get("metrics", {}).get("pad_sm") if isinstance(tokens.get("metrics"), dict) else None,
                "typography.font_family": tokens.get("typography", {}).get("font_family") if isinstance(tokens.get("typography"), dict) else None,
                "effects.shadow_sm": tokens.get("effects", {}).get("shadow_sm") if isinstance(tokens.get("effects"), dict) else None,
            }
            qss_manifest = paths.qss_manifest()
            qss_size = len(compiled.qss)
            info.setPlainText(
                "\n".join([
                    f"selection: theme={pick['theme']} density={pick['density']}",
                    f"fingerprint: {pick['fingerprint']}",
                    f"compiled_qss_size: {qss_size} chars",
                    "",
                    "token snapshot:",
                    *[f"- {k}: {v}" for k, v in pick.items() if k not in ("fingerprint", "theme", "density")],
                    "",
                    f"qss_manifest: {qss_manifest}",
                ])
            )

            parts = []
            if paths.qss_dir.exists():
                parts.append("QSS:")
                for p in sorted(paths.qss_dir.glob("*.qss")):
                    parts.append(f"  - {p.name}")
            if paths.themes_dir.exists():
                parts.append("")
                parts.append("THEMES:")
                for p in sorted(paths.themes_dir.glob("*.json")):
                    parts.append(f"  - {p.name}")
            icons_dir = self._project_root / "assets" / "icons"
            if icons_dir.exists():
                parts.append("")
                parts.append("ICONS:")
                for p in sorted(icons_dir.glob("*.*")):
                    parts.append(f"  - {p.name}")
            listing.setPlainText("\n".join(parts).strip())

            excel_svg = (self._project_root / "assets" / "icons" / "excel.svg")
            pdf_svg = (self._project_root / "assets" / "icons" / "pdf.svg")
            if excel_svg.exists():
                ico = QIcon(str(excel_svg))
                lbl1.setPixmap(ico.pixmap(32, 32))
                lbl1.setToolTip(str(excel_svg))
            else:
                lbl1.setText("excel.svg não encontrado")
            if pdf_svg.exists():
                ico = QIcon(str(pdf_svg))
                lbl2.setPixmap(ico.pixmap(32, 32))
                lbl2.setToolTip(str(pdf_svg))
            else:
                lbl2.setText("pdf.svg não encontrado")

        self._theme_refresh_hooks = getattr(self, "_theme_refresh_hooks", [])
        self._theme_refresh_hooks.append(refresh)
        refresh()

        layout.addStretch(1)
        return root

    def _tab_icon_theme(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("IconTheme (qtawesome)"))
        layout.addWidget(MutedLabel(
            "Demonstração do sistema de ícones: bind em botões e recoloração automática via tokens do tema."
        ))
        layout.addWidget(Divider())

        card = Card()
        card.body.addWidget(SubtitleLabel("Botões com ícones vinculados"))
        row = QWidget()
        row.setLayout(hbox(spacing=10))

        b1 = AppToolButton()
        b2 = AppToolButton()
        b3 = AppToolButton()
        b4 = AppToolButton()

        IconTheme.bind(b1, "fa5s.home")
        IconTheme.bind(b2, "fa5s.search")
        IconTheme.bind(b3, "fa5s.file-export")
        IconTheme.bind(b4, "fa5s.cog")

        row.layout().addWidget(b1)
        row.layout().addWidget(b2)
        row.layout().addWidget(b3)
        row.layout().addWidget(b4)
        row.layout().addStretch(1)
        card.body.addWidget(row)

        card.body.addWidget(MutedLabel(
            "Troque Theme/Density no topo e clique em Apply: os ícones mudam as cores automaticamente (IconTheme.apply_tokens)."
        ))

        layout.addWidget(card)

        diag = Card()
        diag.body.addWidget(SubtitleLabel("Ícone avulso (IconTheme.icon)"))
        lbl = QLabel()
        lbl.setMinimumHeight(48)
        diag.body.addWidget(lbl)

        def refresh():
            ic = IconTheme.icon("fa5s.star")
            lbl.setPixmap(ic.pixmap(40, 40))

        self._theme_refresh_hooks = getattr(self, "_theme_refresh_hooks", [])
        self._theme_refresh_hooks.append(refresh)
        refresh()

        layout.addStretch(1)
        return root

    def _tab_export_showcase(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Export Showcase (Use Case + Infra Exporters)"))
        layout.addWidget(MutedLabel(
            "Exportação real para PDF/XLSX usando ExportTableUseCase + ExporterRegistry + implementações PdfTableExporter/XlsxTableExporter."
        ))
        layout.addWidget(Divider())

        rows: List[dict] = []
        for i in range(1, 2501):
            rows.append({
                "id": i,
                "name": f"Produto {i:05d}",
                "cat": ["A", "B", "C", "D"][i % 4],
                "price": round((i * 2.17) % 350 + 7.5, 2),
                "active": (i % 9) != 0,
                "stock": (i * 11) % 200,
            })

        columns = [
            ("id", "ID"),
            ("name", "Nome"),
            ("cat", "Categoria"),
            ("price", "Preço"),
            ("stock", "Estoque"),
            ("active", "Ativo"),
        ]

        port = InMemoryTablePort(rows)

        card_table = Card()
        card_table.body.addWidget(SubtitleLabel("AppTable (UI) — busca, filtros, paginação, export embutido"))
        t = AppTable(port=port, columns=columns)
        t.set_searchable_keys(["id", "name", "cat"])
        t.set_sort([SortSpec("name", True)])
        card_table.body.addWidget(t, 1)
        card_table.body.addWidget(MutedLabel("Dica: o AppTable já traz o botão Export (PDF/XLSX) no header."))
        layout.addWidget(card_table)

        layout.addWidget(Divider())

        card_uc = Card()
        card_uc.body.addWidget(SubtitleLabel("ExportTableUseCase (Headless) — sem depender do widget"))
        status = InlineStatus()
        card_uc.body.addWidget(status)

        form = QWidget()
        form.setLayout(vbox(spacing=10))

        cmb_mode = AppComboBox(required=True)
        cmb_mode.set_items([("All results (paginado)", "all_results"), ("Current page (snapshot)", "current_page")], include_empty=False)

        cmb_fmt = AppComboBox(required=True)
        cmb_fmt.set_items([("XLSX", "xlsx"), ("PDF", "pdf")], include_empty=False)

        title = AppLineEdit(placeholder="Título do relatório", required=True)
        title.setText("Relatório de Produtos")

        pick_path = AppLineEdit(placeholder="Destino do arquivo (use Browse)", required=True)
        btn_browse = GhostButton("Browse...")

        row_path = QWidget()
        row_path.setLayout(hbox(spacing=10))
        row_path.layout().addWidget(pick_path, 1)
        row_path.layout().addWidget(btn_browse)
        form.layout().addWidget(MutedLabel("Mode:"))
        form.layout().addWidget(cmb_mode)
        form.layout().addWidget(MutedLabel("Format:"))
        form.layout().addWidget(cmb_fmt)
        form.layout().addWidget(MutedLabel("Title:"))
        form.layout().addWidget(title)
        form.layout().addWidget(MutedLabel("Destination path:"))
        form.layout().addWidget(row_path)

        prog = AppProgressBar()
        prog.setRange(0, 100)
        prog.setValue(0)

        row_btns = QWidget()
        row_btns.setLayout(hbox(spacing=10))
        btn_run = PrimaryButton("Run export")
        btn_open = AppButton("Open file", on_click=lambda: self._open_path(pick_path.text().strip()))
        row_btns.layout().addWidget(btn_run)
        row_btns.layout().addWidget(btn_open)
        row_btns.layout().addStretch(1)

        card_uc.body.addWidget(form)
        card_uc.body.addWidget(prog)
        card_uc.body.addWidget(row_btns)

        layout.addWidget(card_uc)

        registry = ExporterRegistry(_exporters={
            "xlsx": XlsxTableExporter(),
            "pdf": PdfTableExporter(),
        })
        uc = ExportTableUseCase(registry=registry)

        def browse():
            fmt = str(cmb_fmt.currentData())
            ext = "xlsx" if fmt == "xlsx" else "pdf"
            p0 = str((Path.cwd() / f"export_demo.{ext}").resolve())
            fn, _ = QFileDialog.getSaveFileName(self, "Salvar exportação", p0, f"*.{ext}")
            if fn:
                if not fn.lower().endswith(f".{ext}"):
                    fn = f"{fn}.{ext}"
                pick_path.setText(fn)

        btn_browse.clicked.connect(browse)

        def set_busy(busy: bool):
            btn_run.setDisabled(busy)
            btn_browse.setDisabled(busy)
            cmb_mode.setDisabled(busy)
            cmb_fmt.setDisabled(busy)
            title.setDisabled(busy)
            pick_path.setDisabled(busy)

        def run_export():
            ok1 = title.validate_now().ok
            ok2 = pick_path.validate_now().ok
            if not (ok1 and ok2):
                status.show_warning("Preencha os campos obrigatórios.")
                return

            mode = str(cmb_mode.currentData())
            fmt = str(cmb_fmt.currentData())
            dest = pick_path.text().strip()
            report_title = title.text().strip()

            status.show_info("Exportando...")
            prog.setValue(0)
            set_busy(True)

            def job(sig: _WorkerSignals):
                query = UiTableQuery(page=1, page_size=200, search_text="", filters=(), sort=(), searchable_keys=())
                if mode == "current_page":
                    pg = port.fetch_page(query)
                    req = UseCaseExportRequest(
                        query=query,
                        columns=columns,
                        mode="current_page",
                        fmt=fmt,
                        destination_path=dest,
                        report_title=report_title,
                    )
                    def progress(done: int, total: int):
                        sig.progress.emit(done, total)
                    return uc.execute(req, current_page_rows=pg.rows, progress=progress)
                req = UseCaseExportRequest(
                    query=query,
                    columns=columns,
                    mode="all_results",
                    fmt=fmt,
                    destination_path=dest,
                    report_title=report_title,
                )
                def progress(done: int, total: int):
                    sig.progress.emit(done, total)
                return uc.execute(req, data_port=port, progress=progress)

            w = _Worker(job)
            w.signals.progress.connect(lambda done, total: prog.setValue(int((done / max(1, total)) * 100)))
            w.signals.finished.connect(lambda res: self._on_export_done(res, status, prog, set_busy))
            w.signals.error.connect(lambda msg: self._on_export_error(msg, status, prog, set_busy))
            self._thread_pool.start(w)

        btn_run.clicked.connect(run_export)

        layout.addStretch(1)
        return root

    def _open_path(self, path: str) -> None:
        p = path.strip()
        if not p:
            return
        q = QUrl.fromLocalFile(p)
        if q.isValid():
            QDesktopServices.openUrl(q)

    def _on_export_done(self, res: object, status: InlineStatus, prog: AppProgressBar, set_busy: Callable[[bool], None]) -> None:
        set_busy(False)
        prog.setValue(100)
        if isinstance(res, ExportResult):
            status.show_success(f"Export OK: {res.rows_exported} linhas em {res.duration_ms}ms.")
        else:
            status.show_success("Export OK.")

    def _on_export_error(self, msg: str, status: InlineStatus, prog: AppProgressBar, set_busy: Callable[[bool], None]) -> None:
        set_busy(False)
        prog.setValue(0)
        status.show_error(f"Falha ao exportar: {msg}")

    def _tab_ports_dtos(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Ports & DTOs (Core Contracts)"))
        layout.addWidget(MutedLabel(
            "Contrato de dados/exportação desacoplado da UI e da infraestrutura. Aqui exibimos as dataclasses/ports principais."
        ))
        layout.addWidget(Divider())

        txt = AppPlainTextEdit()
        txt.setReadOnly(True)
        txt.setMinimumHeight(520)

        dto = DtoExportRequest(fmt="xlsx", destination_path="relatorio.xlsx", report_title="Relatório", query="cat=A", mode="all_results")
        port_query = PortTableQuery(
            text="busca",
            filters=(PortFilterSpec(field="cat", op="eq", value="A"),),
            sort=PortSortSpec(field="id", direction="asc"),
            limit=100,
            offset=0,
        )

        content = "\n".join([
            "app/core/dto/export_dto.py",
            f"  - ExportRequest: {dto}",
            "",
            "app/core/ports/exporter_registry.py",
            "  - ExporterRegistry: registry(fmt)->TableExporterPort",
            "",
            "app/core/ports/table_exporter_port.py",
            "  - ExportMeta / ExportResult / TableExporterPort.export(...)",
            "",
            "app/core/ports/table_ports.py",
            f"  - TableQuery (exemplo): {port_query}",
            f"  - FilterSpec / SortSpec (core): {port_query.filters[0]} | {port_query.sort}",
            "",
            "app/core/use_cases/export_table.py",
            "  - ExportTableUseCase.execute(req, data_port=..., progress=...)",
            "",
            "Observação:",
            "  - A UI (AppTable) usa um TableQuery próprio (app/core/ui/tables.py) com paginação + search modes avançados.",
            "  - O use-case export_table é compatível com ambos via Protocol + __dict__/dict fallback.",
        ])
        txt.setPlainText(content)
        layout.addWidget(txt)

        layout.addStretch(1)
        return root

    def _tab_manifesto(self) -> QWidget:
        root = QWidget()
        layout = vbox(margins=(18, 18, 18, 18), spacing=14)
        root.setLayout(layout)

        layout.addWidget(TitleLabel("Manifesto / About"))
        layout.addWidget(MutedLabel("Mapa do que foi construído (UI + Theme + Tables + Export + Ports)."))
        layout.addWidget(Divider())

        text = AppPlainTextEdit()
        text.setReadOnly(True)
        text.setMinimumHeight(650)

        summary = "\n".join([
            "Arquivos e componentes (alto nível):",
            "",
            "- app/core/ui/*  => UI kit (tipografia, botões, inputs, containers, dialogs, feedback, scroll, tabs, window/app)",
            "- app/core/ui/theme_manager.py + theme_types.py + app_theme.py => engine de tema (tokens JSON + QSS + hot reload opcional)",
            "- app/core/ui/icon_theme.py => integração com qtawesome e recoloração por tokens",
            "- app/core/ui/tables.py => AppTable (smart table) com busca, filtros, ordenação, paginação híbrida e export embutido",
            "- app/core/use_cases/export_table.py => caso de uso de exportação desacoplado da UI",
            "- app/core/ports/* => contratos (registry, exporter port, table ports)",
            "- app/infra/export/* => exporters concretos (XLSX via openpyxl, PDF via reportlab)",
            "- assets/qss + assets/themes + assets/icons => identidade visual e recursos",
            "",
            "O objetivo deste main.py é funcionar como vitrine: cada aba demonstra uma fatia do sistema.",
        ])
        text.setPlainText(summary)
        layout.addWidget(text)

        layout.addStretch(1)
        return root


def main() -> int:
    app = AppApplication(sys.argv)
    apply_app_theme(app)

    win = DemoWindow(app)
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
