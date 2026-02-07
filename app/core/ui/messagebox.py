from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget


@dataclass(frozen=True)
class ConfirmResult:
    ok: bool
    clicked_text: str = ""


class AppMessageBox:
    @staticmethod
    def info(parent: QWidget, title: str, text: str) -> None:
        QMessageBox.information(parent, title, text)

    @staticmethod
    def information(parent: QWidget, title: str, text: str) -> None:
        AppMessageBox.info(parent, title, text)

    @staticmethod
    def warning(parent: QWidget, title: str, text: str) -> None:
        QMessageBox.warning(parent, title, text)

    @staticmethod
    def error(parent: QWidget, title: str, text: str) -> None:
        QMessageBox.critical(parent, title, text)

    @staticmethod
    def success(parent: QWidget, title: str, text: str) -> None:
        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle(title)
        box.setText(text)
        box.exec()

    @staticmethod
    def confirm(
        parent: QWidget,
        title: str,
        text: str,
        *,
        ok_text: str = "OK",
        cancel_text: str = "Cancelar",
        destructive: bool = False,
        default_ok: bool = False,
    ) -> ConfirmResult:
        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Warning if destructive else QMessageBox.Question)
        box.setWindowTitle(title)
        box.setText(text)

        btn_cancel = box.addButton(cancel_text, QMessageBox.RejectRole)
        btn_ok = box.addButton(ok_text, QMessageBox.DestructiveRole if destructive else QMessageBox.AcceptRole)

        box.setDefaultButton(btn_ok if default_ok else btn_cancel)
        box.exec()

        clicked = box.clickedButton()
        clicked_text = clicked.text() if clicked else ""
        return ConfirmResult(ok=clicked == btn_ok, clicked_text=clicked_text)

    @staticmethod
    def ask_destructive(
        parent: QWidget,
        title: str,
        text: str,
        *,
        confirm_label: str = "Excluir",
        cancel_label: str = "Cancelar",
    ) -> bool:
        r = AppMessageBox.confirm(
            parent,
            title=title,
            text=text,
            ok_text=confirm_label,
            cancel_text=cancel_label,
            destructive=True,
        )
        return r.ok
