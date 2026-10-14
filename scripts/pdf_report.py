"""Presentación editorial del reporte, separada de la consulta a SonarQube."""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#14283F")
TEAL = colors.HexColor("#087F78")
MUTED = colors.HexColor("#536579")
LIGHT = colors.HexColor("#F1F5F8")
LINE = colors.HexColor("#DDE5EC")
RED = colors.HexColor("#AB3542")
WIDTH = A4[0] - 88
LABELS = {
    "new_coverage": "Cobertura de código nuevo",
    "new_duplicated_lines_density": "Duplicación en código nuevo",
    "new_violations": "Issues nuevos",
    "coverage": "Cobertura general",
    "bugs": "Bugs",
    "vulnerabilities": "Vulnerabilidades",
    "code_smells": "Problemas de mantenibilidad",
    "security_hotspots": "Puntos de revisión de seguridad",
}
STYLES = {
    "eyebrow": ParagraphStyle(
        "Eyebrow", fontSize=8, leading=12, textColor=TEAL, fontName="Helvetica-Bold", spaceAfter=10
    ),
    "title": ParagraphStyle(
        "ReportTitle",
        fontSize=31,
        leading=35,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        spaceAfter=12,
    ),
    "heading": ParagraphStyle(
        "Section",
        fontSize=14,
        leading=19,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        spaceBefore=17,
        spaceAfter=10,
        keepWithNext=True,
    ),
    "body": ParagraphStyle("Body", fontSize=9.5, leading=14, textColor=MUTED),
    "small": ParagraphStyle("Small", fontSize=8, leading=12, textColor=MUTED),
    "label": ParagraphStyle("Label", fontSize=8, leading=11, textColor=MUTED),
    "value": ParagraphStyle(
        "Value", fontSize=28, leading=34, textColor=NAVY, fontName="Helvetica-Bold"
    ),
    "cell": ParagraphStyle("Cell", fontSize=8.7, leading=13, textColor=NAVY),
    "column": ParagraphStyle(
        "Column", fontSize=8, leading=11, textColor=colors.white, fontName="Helvetica-Bold"
    ),
    "mono": ParagraphStyle(
        "Mono", fontSize=7.5, leading=12, textColor=MUTED, fontName="Courier", splitLongWords=True
    ),
    "status": ParagraphStyle(
        "Status",
        fontSize=12,
        leading=16,
        textColor=TEAL,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    ),
}


def texto(value: Any, style: str = "body") -> Paragraph:
    return Paragraph(escape(str(value)), STYLES[style])


def valor(value: Any, porcentaje: bool = False) -> str:
    if value is None or value == "N/D":
        return "N/D"
    number = float(value)
    formatted = f"{number:,.1f}".removesuffix(".0")
    return f"{formatted} %" if porcentaje else formatted


def fecha(value: str) -> str:
    date = datetime.fromisoformat(value)
    if date.tzinfo is None:
        return value
    return date.astimezone(ZoneInfo("America/Monterrey")).strftime("%d/%m/%Y · %H:%M (Monterrey)")


def estado(status: str) -> tuple[str, colors.Color, colors.Color]:
    return {
        "OK": ("APROBADO", TEAL, colors.HexColor("#EAF6F2")),
        "ERROR": ("NO APROBADO", RED, colors.HexColor("#FCEFF0")),
    }.get(status, ("SIN EVALUAR", MUTED, LIGHT))


def tabla(rows: list[list[Any]], widths: list[float]) -> Table:
    content = [
        [texto(cell, "column" if i == 0 else "cell") for cell in row] for i, row in enumerate(rows)
    ]
    table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("LINEBELOW", (0, 0), (-1, 0), 2, TEAL),
            ]
        )
    )
    return table


def indicadores(data: dict[str, Any]) -> Table:
    metrics = data["metrics"]
    values = [
        ("COBERTURA GENERAL", valor(metrics.get("coverage"), True)),
        ("COBERTURA NUEVA", valor(metrics.get("new_coverage"), True)),
        ("ISSUES TOTALES", str(len(data["overall_issues"]))),
        ("ISSUES NUEVOS", str(len(data["new_issues"]))),
    ]
    cards = [
        [texto(label, "label"), Spacer(1, 8), texto(value, "value")] for label, value in values
    ]
    table = Table([cards], colWidths=[WIDTH / 4] * 4)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("LINEAFTER", (0, 0), (-2, 0), 3, colors.white),
            ]
        )
    )
    return table


def comparativa(metrics: dict[str, Any]) -> Table:
    rows = [["MÉTRICA", "TODO EL PROYECTO", "CÓDIGO NUEVO"]]
    for label, key, percent in [
        ("Cobertura", "coverage", True),
        ("Líneas evaluables", "lines_to_cover", False),
        ("Líneas sin cubrir", "uncovered_lines", False),
        ("Bugs", "bugs", False),
        ("Vulnerabilidades", "vulnerabilities", False),
        ("Problemas de mantenibilidad", "code_smells", False),
        ("Puntos de revisión de seguridad", "security_hotspots", False),
    ]:
        rows.append(
            [label, valor(metrics.get(key), percent), valor(metrics.get(f"new_{key}"), percent)]
        )
    return tabla(rows, [WIDTH * 0.46, WIDTH * 0.28, WIDTH * 0.26])


def condiciones(data: dict[str, Any]) -> list[Flowable]:
    conditions = data["quality_gate"].get("conditions", [])
    if not conditions:
        return [texto("El servidor no devolvió condiciones para este análisis.")]
    rows = [["CONDICIÓN", "MEDIDO", "FALLA SI", "ESTADO"]]
    for condition in conditions:
        key = condition.get("metricKey", condition.get("metric", "N/D"))
        percent = "coverage" in key or "density" in key
        comparator = {"LT": "<", "GT": ">"}.get(condition.get("comparator"), "")
        rows.append(
            [
                LABELS.get(key, key.replace("_", " ")),
                valor(condition.get("actualValue"), percent),
                f"{comparator} {valor(condition.get('errorThreshold'), percent)}".strip(),
                estado(condition.get("status", "NONE"))[0],
            ]
        )
    return [tabla(rows, [WIDTH * 0.39, WIDTH * 0.16, WIDTH * 0.18, WIDTH * 0.27])]


def hallazgos(data: dict[str, Any]) -> list[Flowable]:
    story: list[Flowable] = []
    for key, title in [("overall_issues", "Todo el proyecto"), ("new_issues", "Código nuevo")]:
        issues = data[key]
        story.append(texto(f"{title} · {len(issues)} issues abiertos", "eyebrow"))
        if not issues:
            story.extend([texto("Sin issues abiertos en este alcance."), Spacer(1, 12)])
        for issue in issues:
            story.append(
                KeepTogether(
                    [
                        texto(
                            f"{issue.get('severity', 'N/D')} / {issue.get('type', 'N/D')}", "small"
                        ),
                        texto(issue.get("message", "Sin descripción"), "cell"),
                        texto(
                            f"{issue.get('component', 'N/D')} · línea {issue.get('line', 'N/D')}",
                            "mono",
                        ),
                        Spacer(1, 12),
                    ]
                )
            )
    return story


def trazabilidad(data: dict[str, Any]) -> Table:
    rows = []
    for label, value in [
        ("Proyecto", data["project"]),
        ("Fecha del análisis", fecha(data["date"])),
        ("Commit analizado", data["revision"]),
        ("ID del análisis", data["analysis_id"]),
    ]:
        rows.append([texto(label, "small"), texto(value, "mono")])
    table = Table(rows, colWidths=[125, WIDTH - 125], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def marco(canvas: Canvas, doc: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 8, A4[0], 8, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(44, A4[1] - 40, "SONARQUBE  /  CALIDAD DE SOFTWARE")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(A4[0] - 44, A4[1] - 40, "CALCULADORA · PYTHON")
    canvas.setStrokeColor(LINE)
    canvas.line(44, 43, A4[0] - 44, 43)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(44, 29, "Fuente: sonarqube.lynvera.ai  ·  Reporte del análisis automatizado")
    canvas.drawRightString(A4[0] - 44, 29, f"{doc.page:02d}")
    canvas.restoreState()


def crear_pdf(data: dict[str, Any], path: Path) -> None:
    label, color, background = estado(data["quality_gate"]["status"])
    status_style = ParagraphStyle("GateStatus", parent=STYLES["status"], textColor=color)
    badge = Table(
        [
            [
                Paragraph(escape(label), status_style),
                [
                    texto("QUALITY GATE", "eyebrow"),
                    texto("Evaluación según las condiciones configuradas en SonarQube.", "small"),
                ],
            ]
        ],
        colWidths=[145, WIDTH - 145],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("LINEBEFORE", (0, 0), (0, 0), 3, color),
            ]
        )
    )
    story: list[Flowable] = [
        texto("01 / RESUMEN EJECUTIVO", "eyebrow"),
        texto("Calidad y seguridad del código", "title"),
        texto(f"Proyecto {data['project']} · {fecha(data['date'])}"),
        Spacer(1, 20),
        badge,
        Spacer(1, 20),
        indicadores(data),
        texto("Proyecto completo y código nuevo", "heading"),
        comparativa(data["metrics"]),
        Spacer(1, 12),
        texto(
            "GENERAL: todos los archivos analizados del proyecto. NUEVO: cambios incluidos "
            "en la línea base de código nuevo de SonarQube. N/D indica que la métrica "
            "no está disponible; no equivale a cero.",
            "small",
        ),
        texto("Alcance del análisis", "heading"),
        texto(
            "La cobertura incluye calculadora.py, api.py y los scripts de CI. Los issues "
            "son hallazgos abiertos; los puntos de revisión de seguridad (hotspots) "
            "se contabilizan por separado.",
            "small",
        ),
        PageBreak(),
        texto("02 / CONTROLES Y EVIDENCIA", "eyebrow"),
        texto("Detalle del análisis", "title"),
        texto("Condiciones de calidad, hallazgos y referencia exacta del código evaluado."),
        texto("Condiciones del Quality Gate", "heading"),
        *condiciones(data),
        texto("Métricas complementarias del proyecto", "heading"),
        texto(
            f"Cobertura de líneas: {valor(data['metrics'].get('line_coverage'), True)}"
            f" · Cobertura de ramas: {valor(data['metrics'].get('branch_coverage'), True)}"
        ),
        texto(
            f"Duplicación: {valor(data['metrics'].get('duplicated_lines_density'), True)}"
            f" · Líneas de código: {valor(data['metrics'].get('ncloc'))}"
        ),
        texto("Hallazgos por alcance", "heading"),
        *hallazgos(data),
        texto("Trazabilidad", "heading"),
        trazabilidad(data),
        Spacer(1, 12),
        Paragraph(
            '<link href="'
            + escape(data["dashboard"], quote=True)
            + '" color="#087F78"><b>Abrir el análisis en SonarQube</b></link>',
            STYLES["body"],
        ),
        Spacer(1, 10),
        texto(
            "Los datos de este documento corresponden al análisis y al commit indicados. "
            "El JSON adjunto conserva todas las métricas originales y el Markdown "
            "ofrece un resumen para su consulta en GitHub Actions.",
            "small",
        ),
    ]
    SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=77,
        bottomMargin=62,
        title=f"Calidad y seguridad del código | {data['project']}",
        author="Calculadora · Integración continua",
        subject="Reporte de calidad SonarQube",
    ).build(story, onFirstPage=marco, onLaterPages=marco)
