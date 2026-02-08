# app/core/ui/icon_theme.py
from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import qtawesome as qta
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon


def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    s = hex_color.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 3:
        s = "".join([c * 2 for c in s])
    if len(s) != 6:
        return (0.0, 0.0, 0.0)
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b)


def _luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb01(hex_color)
    # luminância simples (boa o bastante pra decidir “claro vs escuro”)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@dataclass(frozen=True)
class IconColors:
    normal: str
    active: str
    disabled: str
    selected: str


class IconTheme:
    _bound: "weakref.WeakKeyDictionary[object, Tuple[str, Optional[int]]]" = weakref.WeakKeyDictionary()
    _colors: Optional[IconColors] = None

    @classmethod
    def apply_tokens(cls, tokens: Dict[str, Any]) -> None:
        colors = tokens.get("colors") or {}

        normal = str(colors.get("icon") or colors.get("text_primary") or "#D0D0D0")
        active = str(colors.get("icon_active") or colors.get("primary") or normal)
        disabled = str(colors.get("icon_disabled") or colors.get("text_muted") or "#808080")
        selected = str(colors.get("icon_selected") or colors.get("primary") or normal)

        # --- blindagem: se fundo for claro e ícone vier claro demais, escurece ---
        bg = str(colors.get("bg") or colors.get("surface") or colors.get("panel") or "")
        if bg:
            bg_l = _luminance(bg)
            n_l = _luminance(normal)
            # “claro em fundo claro” => baixa legibilidade
            if bg_l >= 0.80 and n_l >= 0.70:
                normal = "#1F2328"
                # mantém active/selected no primary se existir; disabled também dá pra ajustar se quiser
                if not colors.get("icon_active"):
                    active = str(colors.get("primary") or "#0B5FFF")
                if not colors.get("icon_selected"):
                    selected = str(colors.get("primary") or active)

        cls._colors = IconColors(normal=normal, active=active, disabled=disabled, selected=selected)

        qta.set_defaults(
            color=cls._colors.normal,
            color_active=cls._colors.active,
            color_disabled=cls._colors.disabled,
            color_selected=cls._colors.selected,
        )

        cls.refresh_all()

    @classmethod
    def icon(cls, name: str) -> QIcon:
        c = cls._colors or IconColors(normal="#D0D0D0", active="#FFFFFF", disabled="#808080", selected="#FFFFFF")
        return qta.icon(
            name,
            color=c.normal,
            color_active=c.active,
            color_disabled=c.disabled,
            color_selected=c.selected,
        )

    @classmethod
    def bind(cls, target: object, icon_name: str) -> None:
        cls._bound[target] = (icon_name, None)
        cls._apply_one(target, icon_name)

    @classmethod
    def refresh_all(cls) -> None:
        dead: list[object] = []
        for target, (icon_name, _size) in cls._bound.items():
            try:
                cls._apply_one(target, icon_name)
            except RuntimeError:
                dead.append(target)
            except Exception:
                pass

        for d in dead:
            try:
                del cls._bound[d]
            except Exception:
                pass

    @classmethod
    def _apply_one(cls, target: object, icon_name: str) -> None:
        ic = cls.icon(icon_name)

        if isinstance(target, QWidget) and hasattr(target, "setIcon"):
            target.setIcon(ic)
            return

        if hasattr(target, "setIcon"):
            target.setIcon(ic)
            return
