from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import Qt, QEvent, QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from .buttons import AppToolButton, GhostButton, PrimaryButton
from .containers import Card, Divider
from .typography import MutedLabel, TitleLabel


class DialogSizePreset(str, Enum):
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass(frozen=True)
class DialogSizing:
    min_width: int
    min_height: int
    default_width: int
    default_height: int


_PRESETS: dict[DialogSizePreset, DialogSizing] = {
    DialogSizePreset.SM: DialogSizing(min_width=420, min_height=220, default_width=480, default_height=320),
    DialogSizePreset.MD: DialogSizing(min_width=520, min_height=280, default_width=560, default_height=420),
    DialogSizePreset.LG: DialogSizing(min_width=680, min_height=360, default_width=760, default_height=560),
    DialogSizePreset.XL: DialogSizing(min_width=860, min_height=480, default_width=960, default_height=680),
}


class _LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("role", "overlay")
        self.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        center = QWidget(self)
        center_l = QVBoxLayout(center)
        center_l.setContentsMargins(0, 0, 0, 0)
        center_l.setSpacing(0)
        center_l.setAlignment(Qt.AlignCenter)

        self._card = Card()
        self._card.setMaximumWidth(520)
        self._card.body.setContentsMargins(18, 16, 18, 16)
        self._card.body.setSpacing(10)

        self._title = TitleLabel("Processando…")
        self._title.setProperty("role", "subtitle")
        self._subtitle = MutedLabel("Aguarde um momento.")
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)

        self._cancel_row = QWidget()
        cr = QHBoxLayout(self._cancel_row)
        cr.setContentsMargins(0, 6, 0, 0)
        cr.setSpacing(10)
        cr.setAlignment(Qt.AlignRight)
        self._btn_cancel = GhostButton("Cancelar", on_click=self._on_cancel_clicked)
        cr.addWidget(self._btn_cancel)
        self._cancel_row.hide()

        self._card.body.addWidget(self._title)
        self._card.body.addWidget(self._subtitle)
        self._card.body.addWidget(Divider())
        self._card.body.addWidget(self._bar)
        self._card.body.addWidget(self._cancel_row)

        center_l.addWidget(self._card)
        root.addWidget(center)

        self._cancel_cb: Optional[Callable[[], None]] = None

    def set_message(self, title: str, subtitle: str = "") -> None:
        self._title.setText(title)
        self._subtitle.setText(subtitle or "")

    def set_cancellable(self, cancellable: bool, on_cancel: Optional[Callable[[], None]] = None) -> None:
        self._cancel_cb = on_cancel
        self._cancel_row.setVisible(bool(cancellable))
        self._btn_cancel.setEnabled(bool(cancellable))

    def _on_cancel_clicked(self) -> None:
        if self._cancel_cb:
            self._cancel_cb()


class AppDialog(QDialog):
    """Super-wrapper para QDialog com header actions, presets de tamanho e loading overlay."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: Optional[QWidget] = None,
        modal: bool = True,
        size: DialogSizePreset = DialogSizePreset.MD,
        resizable: bool = True,
        show_size_grip: bool = True,
        allow_close_on_escape: bool = True,
    ):
        super().__init__(parent)
        self.setModal(modal)
        self.setWindowTitle(title)
        self.setProperty("role", "dialog")
        self._allow_close_on_escape = allow_close_on_escape

        sizing = _PRESETS[size]
        self.setMinimumSize(QSize(sizing.min_width, sizing.min_height))
        self.resize(QSize(sizing.default_width, sizing.default_height))

        if not resizable:
            self.setFixedSize(QSize(sizing.default_width, sizing.default_height))

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self._header = QWidget(self)
        header_l = QHBoxLayout(self._header)
        header_l.setContentsMargins(0, 0, 0, 0)
        header_l.setSpacing(10)

        titles = QWidget(self._header)
        titles_l = QVBoxLayout(titles)
        titles_l.setContentsMargins(0, 0, 0, 0)
        titles_l.setSpacing(2)

        self.lbl_title = TitleLabel(title)
        titles_l.addWidget(self.lbl_title)

        self.lbl_subtitle: Optional[QLabel] = MutedLabel(subtitle) if subtitle else None
        if self.lbl_subtitle:
            titles_l.addWidget(self.lbl_subtitle)

        self._header_actions = QWidget(self._header)
        self._header_actions.setProperty("role", "header_actions")
        ha = QHBoxLayout(self._header_actions)
        ha.setContentsMargins(0, 0, 0, 0)
        ha.setSpacing(8)
        ha.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_l.addWidget(titles, 1)
        header_l.addWidget(self._header_actions, 0)

        root.addWidget(self._header)
        root.addWidget(Divider())

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(12)
        root.addLayout(self.body, 1)

        root.addWidget(Divider())
        self._footer = QWidget(self)
        self._footer.setProperty("role", "dialog_footer")
        footer_l = QHBoxLayout(self._footer)
        footer_l.setContentsMargins(0, 0, 0, 0)
        footer_l.setSpacing(10)
        footer_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.footer = footer_l
        root.addWidget(self._footer)

        self._size_grip: Optional[QSizeGrip] = None
        if resizable and show_size_grip:
            self._size_grip = QSizeGrip(self)
            self._size_grip.setProperty("role", "size_grip")
            self._size_grip.setFixedSize(16, 16)

        self._overlay = _LoadingOverlay(self)
        self._is_loading = False

        self.installEventFilter(self)
        QTimer.singleShot(0, self._sync_overlay_geometry)

    def add_header_action(
        self,
        text: str = "",
        icon: Optional[QIcon] = None,
        tooltip: str = "",
        on_click: Optional[Callable[[], None]] = None,
        enabled: bool = True,
    ) -> AppToolButton:
        btn = AppToolButton(text=text, icon=icon, on_click=on_click)
        btn.setEnabled(enabled)
        if tooltip:
            btn.setToolTip(tooltip)
        self._header_actions.layout().addWidget(btn)  # type: ignore[arg-type]
        return btn

    def clear_header_actions(self) -> None:
        layout = self._header_actions.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def set_subtitle(self, subtitle: str) -> None:
        if subtitle and self.lbl_subtitle is None:
            self.lbl_subtitle = MutedLabel(subtitle)
            titles_layout = self.lbl_title.parentWidget().layout()
            if titles_layout:
                titles_layout.addWidget(self.lbl_subtitle)  # type: ignore[arg-type]
        if self.lbl_subtitle is not None:
            self.lbl_subtitle.setText(subtitle)
            self.lbl_subtitle.setVisible(bool(subtitle))

    def add_footer_widget(self, widget: QWidget) -> None:
        self.footer.addWidget(widget)

    def set_footer_buttons(
        self,
        primary_text: str = "Salvar",
        primary_cb: Optional[Callable[[], None]] = None,
        secondary_text: str = "Cancelar",
        secondary_cb: Optional[Callable[[], None]] = None,
        danger: bool = False,
    ):
        while self.footer.count():
            item = self.footer.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        btn_secondary = GhostButton(secondary_text, on_click=secondary_cb or self.reject)
        btn_primary = PrimaryButton(primary_text, on_click=primary_cb or self.accept)
        if danger:
            btn_primary.setProperty("state", "error")

        self.footer.addWidget(btn_secondary)
        self.footer.addWidget(btn_primary)
        return btn_secondary, btn_primary

    def set_loading(
        self,
        loading: bool,
        title: str = "Processando…",
        subtitle: str = "Aguarde um momento.",
        cancellable: bool = False,
        on_cancel: Optional[Callable[[], None]] = None,
        block_close: bool = True,
    ) -> None:
        self._is_loading = bool(loading)
        self._allow_close_on_escape = not (block_close and loading)

        self._overlay.set_message(title, subtitle)
        self._overlay.set_cancellable(cancellable, on_cancel)

        self._overlay.setVisible(self._is_loading)
        self._set_content_enabled(not self._is_loading)
        self._sync_overlay_geometry()

    def _set_content_enabled(self, enabled: bool) -> None:
        self._header.setEnabled(enabled)
        self._footer.setEnabled(enabled)
        for w in self.findChildren(QWidget):
            if w is self._overlay or self._overlay.isAncestorOf(w):
                continue
            if w is self._header or self._header.isAncestorOf(w):
                continue
            if w is self._footer or self._footer.isAncestorOf(w):
                continue
            if w.parent() and (w.parent() == self or self.isAncestorOf(w)):
                w.setEnabled(enabled)

    def _sync_overlay_geometry(self) -> None:
        self._overlay.setGeometry(self.rect())
        if self._size_grip is not None:
            m = 10
            self._size_grip.move(self.width() - self._size_grip.width() - m, self.height() - self._size_grip.height() - m)
            self._size_grip.setVisible(not self._is_loading)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_overlay_geometry()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_overlay_geometry()

    def closeEvent(self, event) -> None:
        if self._is_loading and not self._allow_close_on_escape:
            event.ignore()
            return
        super().closeEvent(event)

    def eventFilter(self, obj, event) -> bool:
        if obj is self and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape and not self._allow_close_on_escape:
                return True
        return super().eventFilter(obj, event)


class FormDialog(AppDialog):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(title=title, subtitle=subtitle, parent=parent, size=DialogSizePreset.MD, resizable=True)
        self.btn_cancel = GhostButton("Cancelar", on_click=self.reject)
        self.btn_save = PrimaryButton("Salvar", on_click=self._on_save)
        self.footer.addWidget(self.btn_cancel)
        self.footer.addWidget(self.btn_save)

    def validate(self) -> tuple[bool, str]:
        return True, ""

    def _on_save(self):
        ok, msg = self.validate()
        if not ok:
            QMessageBox.warning(self, "Validação", msg)
            return
        self.accept()


def confirm_destructive(parent: QWidget, title: str, text: str, confirm_label: str = "Excluir") -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    box.addButton("Cancelar", QMessageBox.RejectRole)
    btn_ok = box.addButton(confirm_label, QMessageBox.DestructiveRole)
    box.exec()
    return box.clickedButton() == btn_ok
