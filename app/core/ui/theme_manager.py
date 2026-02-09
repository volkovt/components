from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable

from qtpy.QtCore import QFileSystemWatcher, QObject, Signal
from qtpy.QtWidgets import QApplication

from .theme_types import DensityMode, ThemeMode, ThemePaths, ThemeSelection

_TOKEN_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")

@dataclass(frozen=True)
class CompiledTheme:
    selection: ThemeSelection
    qss: str
    fingerprint: str
    tokens: Dict[str, Any]

class ThemeError(RuntimeError):
    pass


class ThemeManager(QObject):
    theme_changed = Signal(str)  # fingerprint

    def __init__(self, project_root: Path, selection: ThemeSelection | None = None, dev_hot_reload: bool = False):
        super().__init__()
        self._paths = ThemePaths(project_root)
        self._selection = selection or ThemeSelection()
        self._dev_hot_reload = dev_hot_reload
        self._cache: Dict[str, CompiledTheme] = {}
        self._watcher: QFileSystemWatcher | None = None
        self._last_compiled: CompiledTheme | None = None  # <-- NOVO

        if self._dev_hot_reload:
            self._setup_watcher()

    @property
    def selection(self) -> ThemeSelection:
        return self._selection

    def set_selection(self, selection: ThemeSelection) -> None:
        self._selection = selection

    @property
    def last_compiled(self) -> CompiledTheme | None:
        return self._last_compiled

    def apply(self, app: QApplication) -> CompiledTheme:
        compiled = self.compile(self._selection)
        app.setStyleSheet(compiled.qss)
        self._last_compiled = compiled  # <-- NOVO
        self.theme_changed.emit(compiled.fingerprint)
        return compiled

    def compile(self, selection: ThemeSelection) -> CompiledTheme:
        fingerprint = self._fingerprint(selection)
        cached = self._cache.get(fingerprint)
        if cached:
            return cached

        tokens = self._load_tokens(selection)
        qss = self._compile_qss(tokens)
        compiled = CompiledTheme(selection=selection, qss=qss, fingerprint=fingerprint, tokens=tokens)  # <-- NOVO
        self._cache[fingerprint] = compiled
        return compiled

    def _load_tokens(self, selection: ThemeSelection) -> Dict[str, Any]:
        theme_path = self._paths.theme_tokens_path(selection.theme)
        density_path = self._paths.density_tokens_path(selection.density)

        theme = self._read_json(theme_path)
        density = self._read_json(density_path)

        # merge: theme tokens at root, plus density.metrics under "metrics"
        merged: Dict[str, Any] = {}
        merged.update(theme)
        merged.update(density)

        # Ensure keys exist for templating
        if "metrics" not in merged:
            raise ThemeError("Missing 'metrics' in density tokens.")
        if "colors" not in merged or "typography" not in merged:
            raise ThemeError("Missing 'colors' or 'typography' in theme tokens.")
        if "effects" not in merged:
            merged["effects"] = {}

        return merged

    def _compile_qss(self, tokens: Dict[str, Any]) -> str:
        manifest = self._paths.qss_manifest()
        if not manifest.exists():
            raise ThemeError(f"QSS manifest not found: {manifest}")

        # Support simple '@include file.qss' directives
        raw = manifest.read_text(encoding="utf-8")
        parts: list[str] = []
        for line in raw.splitlines():
            line_strip = line.strip()
            if line_strip.startswith("@include"):
                _, name = line_strip.split(maxsplit=1)
                inc = (self._paths.qss_dir / name).resolve()
                if not inc.exists():
                    raise ThemeError(f"Included QSS not found: {inc}")
                parts.append(inc.read_text(encoding="utf-8"))
            else:
                parts.append(line)

        joined = "\n".join(parts)
        return self._render(joined, tokens)

    def _render(self, template: str, tokens: Dict[str, Any]) -> str:
        def resolve(path: str) -> str:
            cur: Any = tokens
            for key in path.split("."):
                if isinstance(cur, dict) and key in cur:
                    cur = cur[key]
                else:
                    raise ThemeError(f"Missing token: '{path}'")
            return str(cur)

        # Replace both {{a.b}} and {{ a.b }}
        def replace(match: re.Match) -> str:
            return resolve(match.group(1))

        rendered = _TOKEN_PATTERN.sub(replace, template)

        # Also allow {{metrics.pad_sm}} in numeric contexts; user may want raw ints. That's fine (stringified).
        # Validate no unresolved tokens remain
        if "{{" in rendered or "}}" in rendered:
            # Try to find first unresolved token
            m = _TOKEN_PATTERN.search(rendered)
            if m:
                raise ThemeError(f"Unresolved token: {m.group(1)}")
            raise ThemeError("Unresolved tokens remain in QSS.")

        return rendered

    def _read_json(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ThemeError(f"Failed to read tokens: {path}") from e

    def _fingerprint(self, selection: ThemeSelection) -> str:
        h = hashlib.sha256()

        theme_val = selection.theme.value if hasattr(selection.theme, "value") else str(selection.theme)
        dens_val = selection.density.value if hasattr(selection.density, "value") else str(selection.density)

        h.update(theme_val.encode("utf-8"))
        h.update(dens_val.encode("utf-8"))

        for p in self._list_theme_files():
            stat = p.stat()
            h.update(str(p).encode("utf-8"))
            h.update(str(stat.st_mtime_ns).encode("utf-8"))
            h.update(str(stat.st_size).encode("utf-8"))

        return h.hexdigest()[:16]

    def _list_theme_files(self) -> Iterable[Path]:
        yield self._paths.theme_tokens_path(self._selection.theme)
        yield self._paths.density_tokens_path(self._selection.density)
        yield self._paths.qss_manifest()
        for p in sorted(self._paths.qss_dir.glob("*.qss")):
            yield p

    def _setup_watcher(self) -> None:
        files = [str(p) for p in self._paths.qss_dir.glob("*.qss")]
        files += [
            str(self._paths.qss_manifest()),
            str(self._paths.theme_tokens_path(ThemeMode.DARK)),
            str(self._paths.theme_tokens_path(ThemeMode.LIGHT)),
            str(self._paths.density_tokens_path(DensityMode.COMPACT)),
            str(self._paths.density_tokens_path(DensityMode.REGULAR)),
            str(self._paths.density_tokens_path(DensityMode.COMFORTABLE)),
        ]

        self._watcher = QFileSystemWatcher(files)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def _on_file_changed(self, _path: str) -> None:
        # clear cache and re-emit on next apply/compile
        self._cache.clear()
        # In dev, we can automatically reapply to the running app if desired.
        app = QApplication.instance()
        if app:
            try:
                self.apply(app)  # will emit theme_changed
            except Exception:
                # Don't crash UI on theme errors
                pass
