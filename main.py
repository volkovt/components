from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QWidget

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
    vbox, hbox, AppScrollArea, AppMainWindow, AppApplication, AppMessageBox, AppTabWidget,
)

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
        self.setWindowTitle("UI Components Demo (App*) — Theme + Density + CRUD Mock")
        self.resize(1200, 800)

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
        le3 = AppLineEdit(placeholder="Money", validator=money_validator(2))
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
        layout.addWidget(MutedLabel("Required/validator e state visual (error/success)."))
        layout.addWidget(Divider())

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
            msg = "\n".join([f"- {name}: {'OK' if r.ok else 'ERRO'} {('— ' + r.message) if r.message else ''}" for name, r in results])
            AppMessageBox.information(self, "Validação", msg)

        vr.addWidget(PrimaryButton("Validar agora", on_click=validate_all))
        vr.addWidget(GhostButton("Limpar estados", on_click=lambda: [w.clear_state() for w in (le_required, le_int, le_money)]))
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


def main() -> int:
    app = AppApplication(sys.argv)
    apply_app_theme(app)

    win = DemoWindow(app)
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
