from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit
)
from PySide6.QtGui import QValidator, QIntValidator, QDoubleValidator
from PySide6.QtCore import QDate, QTime, QDateTime

from .base import AppWidgetMixin, set_default_focus_policy

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str = ""

class AppLineEdit(QLineEdit, AppWidgetMixin):
    def __init__(
        self,
        parent=None,
        placeholder: str = "",
        validator: Optional[QValidator] = None,
        required: bool = False,
        validate_fn: Optional[Callable[[str], ValidationResult]] = None,
        clear_button: bool = True,
    ):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._required = required
        self._validate_fn = validate_fn

        if validator is not None:
            self.setValidator(validator)

        if clear_button:
            self.setClearButtonEnabled(True)

        set_default_focus_policy(self)

    def validate_now(self) -> ValidationResult:
        text = self.text().strip()

        if self._required and not text:
            self.set_state("error")
            return ValidationResult(False, "Campo obrigatório.")

        if self.validator() is not None:
            state, _, _ = self.validator().validate(text, 0)
            if state != QValidator.Acceptable and text:
                self.set_state("error")
                return ValidationResult(False, "Valor inválido.")

        if self._validate_fn is not None:
            result = self._validate_fn(text)
            self.set_state("success" if result.ok else "error")
            return result

        self.set_state("success" if (text or not self._required) else "error")
        return ValidationResult(True, "")

class AppTextEdit(QTextEdit, AppWidgetMixin):
    def __init__(self, parent=None, placeholder: str = "", required: bool = False):
        super().__init__(parent)
        self._required = required
        if placeholder:
            self.setPlaceholderText(placeholder)
        set_default_focus_policy(self)

    def text_value(self) -> str:
        return self.toPlainText()

    def validate_now(self) -> ValidationResult:
        value = self.text_value().strip()
        if self._required and not value:
            self.set_state("error")
            return ValidationResult(False, "Campo obrigatório.")
        self.set_state("success")
        return ValidationResult(True, "")

class AppPlainTextEdit(QPlainTextEdit, AppWidgetMixin):
    def __init__(self, parent=None, placeholder: str = "", required: bool = False):
        super().__init__(parent)
        self._required = required
        if placeholder:
            self.setPlaceholderText(placeholder)
        set_default_focus_policy(self)

    def text_value(self) -> str:
        return self.toPlainText()

    def validate_now(self) -> ValidationResult:
        value = self.text_value().strip()
        if self._required and not value:
            self.set_state("error")
            return ValidationResult(False, "Campo obrigatório.")
        self.set_state("success")
        return ValidationResult(True, "")

class AppComboBox(QComboBox, AppWidgetMixin):
    def __init__(self, parent=None, required: bool = False):
        super().__init__(parent)
        self._required = required
        self.setEditable(False)
        set_default_focus_policy(self)

    def set_items(self, items: list[tuple[str, object]] | list[str], include_empty: bool = False, empty_label: str = "Selecione..."):
        self.clear()
        if include_empty:
            self.addItem(empty_label, None)

        if items and isinstance(items[0], tuple):
            for label, data in items:
                self.addItem(label, data)
        else:
            for label in items:
                self.addItem(label, label)

    def current_data_value(self):
        return self.currentData()

    def validate_now(self) -> ValidationResult:
        if not self._required:
            self.clear_state()
            return ValidationResult(True, "")

        data = self.currentData()
        label = self.currentText().strip()

        ok = (data is not None) and (label != "")
        self.set_state("success" if ok else "error")
        return ValidationResult(ok, "" if ok else "Selecione um item.")

class AppSpinBox(QSpinBox, AppWidgetMixin):
    def __init__(self, parent=None, minimum: int = 0, maximum: int = 10**9):
        super().__init__(parent)
        self.setRange(minimum, maximum)
        set_default_focus_policy(self)

class AppDoubleSpinBox(QDoubleSpinBox, AppWidgetMixin):
    def __init__(self, parent=None, minimum: float = 0.0, maximum: float = 10**12, decimals: int = 2):
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        set_default_focus_policy(self)

class AppDateEdit(QDateEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QDate] = None, calendar_popup: bool = True):
        super().__init__(parent)
        self.setCalendarPopup(calendar_popup)
        self.setDate(default or QDate.currentDate())
        set_default_focus_policy(self)

class AppTimeEdit(QTimeEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QTime] = None):
        super().__init__(parent)
        self.setTime(default or QTime.currentTime())
        set_default_focus_policy(self)

class AppDateTimeEdit(QDateTimeEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QDateTime] = None, calendar_popup: bool = True):
        super().__init__(parent)
        self.setCalendarPopup(calendar_popup)
        self.setDateTime(default or QDateTime.currentDateTime())
        set_default_focus_policy(self)

def int_validator(min_value: int = 0, max_value: int = 10**9) -> QIntValidator:
    return QIntValidator(min_value, max_value)

def money_validator(decimals: int = 2) -> QDoubleValidator:
    v = QDoubleValidator()
    v.setDecimals(decimals)
    v.setBottom(0.0)
    v.setNotation(QDoubleValidator.StandardNotation)
    return v
