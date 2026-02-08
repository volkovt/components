from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence

ExportFmt = Literal["xlsx", "pdf"]
ExportMode = Literal["all_results", "current_page", "selected_rows"]

@dataclass(frozen=True)
class ExportRequest:
    fmt: ExportFmt
    destination_path: str
    report_title: Optional[str] = None
    query: Optional[str] = None
    mode: ExportMode = "all_results"
    columns: Optional[Sequence[str]] = None
    chunk_page_size: int = 1000