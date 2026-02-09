# app/core/use_cases/export_table.py
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple, Protocol, Literal

from app.core.ports.exporter_registry import ExporterRegistry
from app.core.ports.table_exporter_port import ExportMeta, ExportResult

class TablePageLike(Protocol):
    rows: Sequence[Mapping[str, Any]]
    total_rows: int
    page: int
    page_size: int


class TableDataPortLike(Protocol):
    def fetch_page(self, query: Any) -> TablePageLike:
        ...


ProgressFn = Callable[[int, int], None]


@dataclass(frozen=True)
class ExportRequest:
    query: Any
    columns: Sequence[Tuple[str, str]]               # (key, title)
    mode: Literal["current_page", "all_results"]     # conforme UI
    fmt: str                                        # "xlsx" | "pdf"
    destination_path: str
    report_title: str = "Relatório"
    chunk_page_size: int = 1000


@dataclass(frozen=True)
class ExportTableUseCase:
    registry: ExporterRegistry

    def execute(
        self,
        req: ExportRequest,
        *,
        data_port: Optional[TableDataPortLike] = None,
        current_page_rows: Optional[Sequence[Mapping[str, Any]]] = None,
        progress: Optional[ProgressFn] = None,
    ) -> ExportResult:
        """
        Executa exportação de tabela:
        - current_page: usa current_page_rows (não consulta o data_port)
        - all_results: pagina via data_port.fetch_page(...) usando req.chunk_page_size
        """

        t0 = time.time()

        exporter = self.registry.get(req.fmt)

        generated_at_iso = datetime.now(timezone.utc).isoformat()
        query_summary = self._summarize_query(req.query)

        # ---------- Fonte de dados ----------
        if req.mode == "current_page":
            if current_page_rows is None:
                raise ValueError("Exportação 'current_page' requer current_page_rows.")
            total = len(current_page_rows)

            if progress:
                progress(0, total)

            rows_iter = self._iter_current_page(current_page_rows, progress=progress)
            meta = ExportMeta(
                title=req.report_title,
                generated_at_iso=generated_at_iso,
                total_rows=total,
                query_summary=query_summary,
            )
            return exporter.export(
                rows=rows_iter,
                columns=req.columns,
                meta=meta,
                destination_path=req.destination_path,
            )

        # all_results
        if data_port is None:
            raise ValueError("Exportação 'all_results' requer data_port para paginar os resultados.")

        # Primeira página para descobrir total (sem exportar duas vezes: a gente reutiliza)
        first_query = self._with_page(req.query, page=1, page_size=req.chunk_page_size)
        first_page = data_port.fetch_page(first_query)
        total = int(first_page.total_rows)

        if progress:
            progress(0, total)

        rows_iter = self._iter_all_results(
            data_port=data_port,
            req=req,
            first_page=first_page,
            total=total,
            progress=progress,
        )

        meta = ExportMeta(
            title=req.report_title,
            generated_at_iso=generated_at_iso,
            total_rows=total,
            query_summary=query_summary,
        )

        return exporter.export(
            rows=rows_iter,
            columns=req.columns,
            meta=meta,
            destination_path=req.destination_path,
        )

    def _iter_current_page(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        progress: Optional[ProgressFn],
    ) -> Iterable[Mapping[str, Any]]:
        done = 0
        total = len(rows)
        for r in rows:
            yield r
            done += 1
            if progress:
                progress(done, total)

    def _iter_all_results(
        self,
        *,
        data_port: TableDataPortLike,
        req: ExportRequest,
        first_page: TablePageLike,
        total: int,
        progress: Optional[ProgressFn],
    ) -> Iterable[Mapping[str, Any]]:
        done = 0

        # 1) exporta a primeira página já carregada
        for r in first_page.rows:
            yield r
            done += 1
            if progress:
                progress(done, total)

        # 2) exporta páginas seguintes
        page = 2
        while done < total:
            q = self._with_page(req.query, page=page, page_size=req.chunk_page_size)
            pg = data_port.fetch_page(q)

            if not pg.rows:
                break

            for r in pg.rows:
                yield r
                done += 1
                if progress:
                    progress(done, total)

            page += 1

    def _with_page(self, query: Any, *, page: int, page_size: int) -> Any:
        if hasattr(query, "__dict__"):
            d = dict(query.__dict__)
            d["page"] = page
            d["page_size"] = page_size
            return query.__class__(**d)
        # fallback: se query já é um dict
        if isinstance(query, dict):
            q = dict(query)
            q["page"] = page
            q["page_size"] = page_size
            return q
        raise TypeError("Não foi possível ajustar paginação da query (tipo não suportado).")

    def _summarize_query(self, query: Any) -> str:
        try:
            if hasattr(query, "__dict__"):
                d = query.__dict__
                parts = []
                s = (d.get("search_text") or "").strip()
                if s:
                    parts.append(f"busca='{s}' ({d.get('search_mode','')})")
                f = d.get("filters") or ()
                if f:
                    parts.append(f"filtros={len(f)}")
                so = d.get("sort") or ()
                if so:
                    parts.append(f"ordenação={len(so)}")
                return " | ".join(parts)
        except Exception:
            pass
        return ""
