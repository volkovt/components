
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .table_exporter_port import TableExporterPort


@dataclass
class ExporterRegistry:
    _exporters: Dict[str, TableExporterPort]

    def get(self, fmt: str) -> TableExporterPort:
        k = (fmt or "").strip().lower()
        if k not in self._exporters:
            raise ValueError(f"Formato de exportação não suportado: {fmt}")
        return self._exporters[k]

    def register(self, fmt: str, exporter: TableExporterPort) -> None:
        k = (fmt or "").strip().lower()
        self._exporters[k] = exporter
