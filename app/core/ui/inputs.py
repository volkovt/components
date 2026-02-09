from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional, Callable

from PySide6.QtCore import QSize
from qtpy.QtWidgets import (
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit,
    QAbstractSpinBox,
)
from qtpy.QtGui import QValidator, QIntValidator, QDoubleValidator
from qtpy.QtCore import Qt, QDate, QTime, QDateTime, QLocale, QSignalBlocker

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

    def set_items(self, items: list[tuple[str, object]] | list[str], include_empty: bool = False,
                  empty_label: str = "Selecione..."):
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


class _ElegantSpinBehavior:
    def _configure_spin_common(self) -> None:
        self.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.setAccelerated(True)
        self.setKeyboardTracking(False)
        self.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)

        try:
            self.setGroupSeparatorShown(True)
        except Exception:
            pass

        try:
            self.lineEdit().setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        except Exception:
            pass

        set_default_focus_policy(self)

        self._default_value = self.value()

    def set_default_value(self, value) -> None:
        self._default_value = value

    def reset_to_default(self) -> None:
        self.setValue(self._default_value)

    def wheelEvent(self, event) -> None:
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)

    def stepBy(self, steps: int) -> None:
        mods = Qt.KeyboardModifier(self.keyboardModifiers())
        mult = 1
        if mods & Qt.ShiftModifier:
            mult *= 10
        if mods & Qt.ControlModifier:
            mult *= 100
        super().stepBy(steps * mult)

class AppSpinBox(QSpinBox, AppWidgetMixin, _ElegantSpinBehavior):
    def __init__(self, parent=None, minimum: int = 0, maximum: int = 10 ** 9):
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self._configure_spin_common()

class AppDoubleSpinBox(QDoubleSpinBox, AppWidgetMixin, _ElegantSpinBehavior):
    def __init__(self, parent=None, minimum: float = 0.0, maximum: float = 10 ** 12, decimals: int = 2):
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        self._configure_spin_common()

class AppDateEdit(QDateEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QDate] = None, calendar_popup: bool = True):
        super().__init__(parent)
        self.setCalendarPopup(calendar_popup)
        self.setDate(default or QDate.currentDate())
        self.setFixedSize(QSize(120, self.sizeHint().height()))
        set_default_focus_policy(self)

class AppTimeEdit(QTimeEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QTime] = None):
        super().__init__(parent)
        self.setTime(default or QTime.currentTime())

        self.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.setAccelerated(True)
        self.setKeyboardTracking(False)
        self.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)

        try:
            self.lineEdit().setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        except Exception:
            pass

        set_default_focus_policy(self)


class AppDateTimeEdit(QDateTimeEdit, AppWidgetMixin):
    def __init__(self, parent=None, default: Optional[QDateTime] = None, calendar_popup: bool = True):
        super().__init__(parent)
        self.setCalendarPopup(calendar_popup)

        self.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.setFixedSize(QSize(150, self.sizeHint().height()))

        self.setDateTime(default or QDateTime.currentDateTime())
        set_default_focus_policy(self)

class AppMoneyLineEdit(AppLineEdit):
    def __init__(
        self,
        parent=None,
        placeholder: str = "0,00",
        required: bool = False,
        locale: Optional[QLocale] = None,
        decimals: int = 2,
        allow_empty: bool = True,
        allow_negative: bool = False,
        prefix: str = "",
        suffix: str = "",
        affix_separator: str = " ",
        decimal_sep: Optional[str] = None,
        group_sep: Optional[str] = None,
        grouping_enabled: bool = True,
        auto_format_on_change: bool = False,
        cents_mode: bool = False,
    ):
        super().__init__(
            parent=parent,
            placeholder=placeholder,
            validator=None,
            required=required,
        )

        self._locale = locale or QLocale(QLocale.Portuguese, QLocale.Brazil)
        self._decimals = max(0, int(decimals))
        self._allow_empty = bool(allow_empty)
        self._allow_negative = bool(allow_negative)

        self._prefix = prefix or ""
        self._suffix = suffix or ""
        self._affix_sep = affix_separator

        self._forced_decimal_sep = decimal_sep if decimal_sep in (",", ".") else None
        self._forced_group_sep = group_sep if group_sep in (",", ".", "") else None

        self._grouping_enabled = bool(grouping_enabled)
        self._auto_format_on_change = bool(auto_format_on_change)

        self._cents_mode = bool(cents_mode)

        self._value: Optional[Decimal] = None
        self._internal_change = False
        self._editing_numeric_mode = False

        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)

        if not self.text():
            self.setText("")

    # -------- Public API --------

    def set_cents_mode(self, enabled: bool) -> None:
        self._cents_mode = bool(enabled)
        if self._editing_numeric_mode:
            self._apply_cents_mode_format(force=True)
        else:
            self._format_final_if_possible()

    def cents_mode_enabled(self) -> bool:
        return self._cents_mode

    def set_locale(self, locale: QLocale) -> None:
        self._locale = locale
        self._format_final_if_possible()

    def set_separators(self, decimal_sep: Optional[str], group_sep: Optional[str]) -> None:
        self._forced_decimal_sep = decimal_sep if decimal_sep in (",", ".") else None
        self._forced_group_sep = group_sep if group_sep in (",", ".", "") else None
        self._format_final_if_possible()

    def set_affixes(self, prefix: str = "", suffix: str = "", separator: str = " ") -> None:
        self._prefix = prefix or ""
        self._suffix = suffix or ""
        self._affix_sep = separator
        self._format_final_if_possible()

    def set_grouping_enabled(self, enabled: bool) -> None:
        self._grouping_enabled = bool(enabled)
        self._format_final_if_possible()

    def grouping_enabled(self) -> bool:
        return self._grouping_enabled

    def value(self) -> Optional[Decimal]:
        self._value = self._parse_decimal(self.text())
        return self._value

    def set_value(self, value: Optional[Decimal | float | int | str]) -> None:
        if value is None:
            self._value = None
            with QSignalBlocker(self):
                self.setText("" if self._allow_empty else self._format_full(Decimal("0")))
            self.clear_state()
            return

        d = self._coerce_decimal(value)
        if not self._allow_negative and d < 0:
            d = abs(d)

        self._value = d
        with QSignalBlocker(self):
            self.setText(self._format_full(d))
        self.clear_state()

    def validate_now(self) -> ValidationResult:
        raw = self.text().strip()

        if self._required and not raw:
            self.set_state("error")
            return ValidationResult(False, "Campo obrigatório.")

        if not raw:
            if self._allow_empty:
                self.clear_state()
                return ValidationResult(True, "")
            self.set_state("error")
            return ValidationResult(False, "Valor inválido.")

        d = self._parse_decimal(raw)
        if d is None:
            self.set_state("error")
            return ValidationResult(False, "Valor inválido.")

        if not self._allow_negative and d < 0:
            self.set_state("error")
            return ValidationResult(False, "Não pode ser negativo.")

        self.set_state("success")
        return ValidationResult(True, "")

    # -------- Events --------

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._editing_numeric_mode = True

        numeric = self._strip_affixes(self.text())

        if self._cents_mode:
            with QSignalBlocker(self):
                self.setText(self._cents_format_from_any(numeric, keep_empty=self._allow_empty))
            self.setCursorPosition(len(self.text()))
            return

        numeric = self._sanitize_numeric(numeric, keep_intermediate=True)
        with QSignalBlocker(self):
            self.setText(numeric)
        self.setCursorPosition(len(self.text()))

    def focusOutEvent(self, event):
        self._editing_numeric_mode = False
        self._format_final_if_possible()
        super().focusOutEvent(event)

    def _on_editing_finished(self) -> None:
        self._editing_numeric_mode = False
        self._format_final_if_possible()

    def keyPressEvent(self, event):
        t = event.text()
        if self._allow_negative and t == "-":
            self._toggle_negative()
            return
        super().keyPressEvent(event)

    # -------- Core behavior --------

    def _toggle_negative(self) -> None:
        t = self.text()
        cur = self.cursorPosition()

        if t.startswith("-"):
            new_t = t[1:]
            new_cur = max(0, cur - 1)
        else:
            new_t = "-" + t if t else "-"
            new_cur = cur + 1

        self._internal_change = True
        with QSignalBlocker(self):
            self.setText(new_t)
        self._internal_change = False

        self.setCursorPosition(max(0, min(new_cur, len(new_t))))

    def _on_text_changed(self, text: str) -> None:
        if self._internal_change:
            return

        if self._editing_numeric_mode and self._cents_mode:
            self._apply_cents_mode_format()
            self.clear_state(repolish_now=False)
            return

        cur = self.cursorPosition()
        sanitized = self._sanitize_numeric(text, keep_intermediate=True)
        if sanitized != text:
            self._internal_change = True
            with QSignalBlocker(self):
                self.setText(sanitized)
            self._internal_change = False
            self.setCursorPosition(min(cur, len(sanitized)))
            return

        self.clear_state(repolish_now=False)

        if self._auto_format_on_change and self._editing_numeric_mode:
            self._apply_soft_format()

    # -------- Cents mode --------

    def _apply_cents_mode_format(self, force: bool = False) -> None:
        t = self.text()
        if not t and not force:
            return

        new_text = self._cents_format_from_any(t, keep_empty=self._allow_empty)
        if not force and new_text == t:
            return

        self._internal_change = True
        with QSignalBlocker(self):
            self.setText(new_text)
        self._internal_change = False

        self.setCursorPosition(len(self.text()))

    def _cents_format_from_any(self, text: str, *, keep_empty: bool) -> str:
        s = (text or "").replace("\u00A0", " ").strip()
        s = self._strip_affixes(s)

        neg = False
        if self._allow_negative and s.startswith("-"):
            neg = True
        s = s.replace("-", "")

        digits = "".join(ch for ch in s if ch.isdigit())

        if digits == "":
            return "" if keep_empty else self._format_cents_digits("0", neg=False)

        digits = digits.lstrip("0") or "0"

        formatted = self._format_cents_digits(digits, neg=neg)
        return formatted

    def _format_cents_digits(self, digits: str, *, neg: bool) -> str:
        digits = digits or "0"
        scale = 10 ** self._decimals if self._decimals > 0 else 1

        try:
            as_int = int(digits)
        except ValueError:
            as_int = 0

        d = Decimal(as_int) / Decimal(scale)

        if neg:
            d = -abs(d)
        else:
            d = abs(d)

        txt = self._format_number(d)

        if txt == "-0" or txt == "-0,0" or txt == "-0.0":
            txt = txt.lstrip("-")

        return ("-" + txt) if (neg and self._allow_negative) else txt

    # -------- Soft format (non-cents) --------

    def _apply_soft_format(self) -> None:
        t = self.text()
        if not t:
            return

        old_cursor = self.cursorPosition()
        digits_left = self._count_digits_left_of_cursor(t, old_cursor)

        new_text = self._soft_format_numeric(t)
        if new_text == t:
            return

        self._internal_change = True
        with QSignalBlocker(self):
            self.setText(new_text)
        self._internal_change = False

        new_cursor = self._cursor_pos_for_digits_left(new_text, digits_left)
        self.setCursorPosition(max(0, min(new_cursor, len(new_text))))

    def _soft_format_numeric(self, text: str) -> str:
        s = self._sanitize_numeric(text, keep_intermediate=True)
        if s in ("", "-", "-.", "-,"):
            return s

        dec_char = self._active_decimal_char()
        grp_char = self._active_group_char(dec_char)

        sign = ""
        if s.startswith("-"):
            sign = "-"
            s = s[1:]

        trailing_decimal = False
        if s.endswith(dec_char):
            trailing_decimal = True
            s = s[:-1]

        if dec_char in s:
            left, right = s.split(dec_char, 1)
        else:
            left, right = s, ""

        left_digits = "".join(ch for ch in left if ch.isdigit())
        right_digits = "".join(ch for ch in right if ch.isdigit())
        right_digits = right_digits[: self._decimals] if self._decimals >= 0 else right_digits

        grouped_left = self._group_digits(left_digits, grp_char) if (self._grouping_enabled and left_digits) else left_digits

        if dec_char in text or trailing_decimal:
            if self._decimals == 0:
                out = grouped_left
            else:
                if trailing_decimal and right == "" and right_digits == "":
                    out = grouped_left + dec_char
                else:
                    out = grouped_left + (dec_char + right_digits if (right_digits != "" or trailing_decimal) else "")
        else:
            out = grouped_left

        if sign:
            return "-" + out if (out != "" or trailing_decimal) else "-"
        return out

    def _group_digits(self, digits: str, grp_char: str) -> str:
        if not digits:
            return ""
        parts = []
        i = len(digits)
        while i > 0:
            start = max(0, i - 3)
            parts.append(digits[start:i])
            i = start
        parts.reverse()
        return grp_char.join(parts)

    def _sanitize_numeric(self, text: str, *, keep_intermediate: bool) -> str:
        s = (text or "").replace("\u00A0", " ").strip()
        s = self._strip_affixes(s)
        s = s.replace(" ", "")

        allowed = set("0123456789.,-")
        s = "".join(ch for ch in s if ch in allowed)

        dec_char = self._active_decimal_char()
        grp_char = self._active_group_char(dec_char)

        neg = False
        if self._allow_negative and s.startswith("-"):
            neg = True
        s = s.replace("-", "")

        if neg and s == "" and keep_intermediate:
            return "-"

        out = []
        seen_decimal = False

        for ch in s:
            if ch.isdigit():
                out.append(ch)
                continue

            if ch == dec_char:
                if seen_decimal:
                    continue
                if not out:
                    if keep_intermediate:
                        out.append(dec_char)
                        seen_decimal = True
                    continue
                out.append(dec_char)
                seen_decimal = True
                continue

            if ch == grp_char:
                if seen_decimal:
                    continue
                if not out:
                    continue
                if out and out[-1] == grp_char:
                    continue
                out.append(grp_char)
                continue

        cleaned = "".join(out)

        if keep_intermediate and cleaned.endswith(grp_char):
            cleaned = cleaned[:-1]

        while cleaned and cleaned[-1] == grp_char:
            cleaned = cleaned[:-1]

        if neg:
            return "-" + cleaned if (cleaned != "" or keep_intermediate) else ""
        return cleaned

    # -------- Parsing / Final formatting --------

    def _parse_decimal(self, text: str) -> Optional[Decimal]:
        s = (text or "").strip()
        if not s:
            return None

        s = s.replace("\u00A0", " ")
        s = self._strip_affixes(s).replace(" ", "")

        if s in ("-", "-.", "-,"):
            return None

        if self._forced_decimal_sep in (",", "."):
            dec = self._forced_decimal_sep
            grp = self._forced_group_sep if self._forced_group_sep in (",", ".", "") else None
            if grp:
                s = s.replace(grp, "")
            if dec == ",":
                s = s.replace(".", "")
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        else:
            if "," in s and "." in s:
                last_comma = s.rfind(",")
                last_dot = s.rfind(".")
                if last_comma > last_dot:
                    s = s.replace(".", "")
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s and "." not in s:
                s = s.replace(".", "")
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")

        if s in ("", ".", "-", "-."):
            return None

        try:
            d = Decimal(s)
        except (InvalidOperation, ValueError):
            return None

        q = Decimal("1").scaleb(-self._decimals)
        return d.quantize(q)

    def _coerce_decimal(self, value: Decimal | float | int | str) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        s = str(value).strip()
        d = self._parse_decimal(s)
        return d if d is not None else Decimal("0")

    def _format_final_if_possible(self) -> None:
        t = self.text().strip()
        if not t:
            with QSignalBlocker(self):
                self.setText("" if self._allow_empty else self._format_full(Decimal("0")))
            return

        d = self._parse_decimal(t)
        if d is None:
            return
        if not self._allow_negative and d < 0:
            return

        self._value = d
        with QSignalBlocker(self):
            self.setText(self._format_full(d))

    def _strip_affixes(self, text: str) -> str:
        s = (text or "").strip()

        if self._prefix:
            p = self._prefix.strip()
            if s.startswith(p):
                s = s[len(p):].lstrip()
            sep = (self._affix_sep or "").strip()
            if sep and s.startswith(sep):
                s = s[len(sep):].lstrip()

        if self._suffix:
            suf = self._suffix.strip()
            if s.endswith(suf):
                s = s[: -len(suf)].rstrip()
            sep = (self._affix_sep or "").strip()
            if sep and s.endswith(sep):
                s = s[: -len(sep)].rstrip()

        return s

    def _format_full(self, value: Decimal) -> str:
        numeric = self._format_number(value)
        if self._prefix:
            numeric = f"{self._prefix}{self._affix_sep}{numeric}".strip()
        if self._suffix:
            numeric = f"{numeric}{self._affix_sep}{self._suffix}".strip()
        return numeric

    def _format_number(self, value: Decimal) -> str:
        f = float(value)
        base = self._locale.toString(f, "f", self._decimals)

        if not self._grouping_enabled:
            loc_grp = self._locale.groupSeparator()
            if loc_grp:
                base = base.replace(loc_grp, "")

        if self._forced_decimal_sep in (",", ".") or self._forced_group_sep in (",", ".", ""):
            base = self._apply_forced_separators(base)

        return base

    def _apply_forced_separators(self, formatted: str) -> str:
        s = formatted
        loc_dec = self._locale.decimalPoint()
        loc_grp = self._locale.groupSeparator()

        forced_dec = self._forced_decimal_sep if self._forced_decimal_sep in (",", ".") else None
        forced_grp = self._forced_group_sep if self._forced_group_sep in (",", ".", "") else None

        placeholder = "\u241F"
        if loc_grp:
            s = s.replace(loc_grp, placeholder)

        if forced_dec and loc_dec:
            s = s.replace(loc_dec, forced_dec)

        if forced_grp is not None:
            if forced_grp == "":
                s = s.replace(placeholder, "")
            else:
                s = s.replace(placeholder, forced_grp)
        else:
            if self._grouping_enabled and loc_grp:
                s = s.replace(placeholder, loc_grp)
            else:
                s = s.replace(placeholder, "")

        return s

    def _active_decimal_char(self) -> str:
        if self._forced_decimal_sep in (",", "."):
            return self._forced_decimal_sep
        loc_dec = self._locale.decimalPoint()
        if loc_dec in (",", "."):
            return loc_dec
        return ","

    def _active_group_char(self, dec_char: str) -> str:
        if self._forced_group_sep in (",", ".", ""):
            if self._forced_group_sep == "":
                return "," if dec_char == "." else "."
            return self._forced_group_sep
        return "," if dec_char == "." else "."

    def _count_digits_left_of_cursor(self, text: str, cursor_pos: int) -> int:
        cursor_pos = max(0, min(cursor_pos, len(text)))
        left = text[:cursor_pos]
        return sum(1 for ch in left if ch.isdigit())

    def _cursor_pos_for_digits_left(self, text: str, digits_left: int) -> int:
        if digits_left <= 0:
            return 1 if text.startswith("-") else 0
        count = 0
        for i, ch in enumerate(text):
            if ch.isdigit():
                count += 1
                if count >= digits_left:
                    return i + 1
        return len(text)

def int_validator(min_value: int = 0, max_value: int = 10 ** 9) -> QIntValidator:
    return QIntValidator(min_value, max_value)


def money_validator(decimals: int = 2) -> QDoubleValidator:
    v = QDoubleValidator()
    v.setDecimals(decimals)
    v.setBottom(0.0)
    v.setNotation(QDoubleValidator.StandardNotation)
    return v
