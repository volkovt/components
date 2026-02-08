
from __future__ import annotations

import time
from typing import Any, Iterable, Mapping, Sequence, Tuple

from app.core.ports.table_exporter_port import ExportMeta, ExportResult, TableExporterPort


class PdfTableExporter(TableExporterPort):
    def export(
        self,
        rows: Iterable[Mapping[str, Any]],
        columns: Sequence[Tuple[str, str]],
        meta: ExportMeta,
        destination_path: str,
    ) -> ExportResult:
        t0 = time.time()
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except Exception as e:
            raise RuntimeError("Dependência 'reportlab' não disponível para exportar PDF.") from e

        doc = SimpleDocTemplate(
            destination_path,
            pagesize=landscape(A4),
            leftMargin=28,
            rightMargin=28,
            topMargin=28,
            bottomMargin=28,
        )

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(meta.title, styles["Title"]))
        story.append(Paragraph(f"Gerado em: {meta.generated_at_iso}", styles["Normal"]))
        story.append(Paragraph(f"Total de itens: {meta.total_rows}", styles["Normal"]))
        if meta.query_summary:
            story.append(Paragraph(f"Consulta: {meta.query_summary}", styles["Normal"]))
        story.append(Spacer(1, 12))

        header = [title for _, title in columns]
        data = [header]

        exported = 0
        for r in rows:
            data.append([_safe_str(r.get(k, "")) for k, _ in columns])
            exported += 1

        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        story.append(tbl)
        doc.build(story)
        return ExportResult(path=destination_path, rows_exported=exported, duration_ms=int((time.time()-t0)*1000))


def _safe_str(v: Any) -> str:
    return "" if v is None else str(v)
