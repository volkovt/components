# app/core/ports/table_ports.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence, Mapping, Optional, Literal


@dataclass(frozen=True)
class FilterSpec:
    field: str
    op: Literal["eq", "neq", "contains", "startswith", "endswith", "lt", "lte", "gt", "gte", "in"]
    value: Any


@dataclass(frozen=True)
class SortSpec:
    field: str
    direction: Literal["asc", "desc"] = "asc"


@dataclass(frozen=True)
class TableQuery:
    text: Optional[str] = None
    filters: tuple[FilterSpec, ...] = ()
    sort: Optional[SortSpec] = None
    limit: Optional[int] = None
    offset: int = 0


class TableDataPort(Protocol):
    """
    Porta para fornecer dados tabulares para listagem/exportação.
    Implementações podem ser in-memory, SQLAlchemy, API, etc.
    """

    def columns(self) -> Sequence[str]:
        ...

    def rows(self, query: TableQuery) -> Sequence[Mapping[str, Any]]:
        ...

    def total_count(self, query: TableQuery) -> int:
        ...
