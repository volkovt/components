
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, Sequence, Tuple


@dataclass(frozen=True)
class ExportMeta:
    title: str
    generated_at_iso: str
    total_rows: int
    query_summary: str = ""


@dataclass(frozen=True)
class ExportResult:
    path: str
    rows_exported: int
    duration_ms: int


class TableExporterPort(Protocol):
    def export(
        self,
        rows: Iterable[Mapping[str, Any]],
        columns: Sequence[Tuple[str, str]],
        meta: ExportMeta,
        destination_path: str,
    ) -> ExportResult:
        ...
