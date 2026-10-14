import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from herramientas.reporte_pdf import AZUL, BORDE, FONDO, GRIS, VERDE

ANCHO = A4[0] - 96
ESTILOS = {
    "texto": ParagraphStyle("TextoGuia", fontSize=10, leading=15, textColor=AZUL, spaceAfter=10),
    "paso": ParagraphStyle(
        "Paso",
        fontSize=19,
        leading=24,
        textColor=AZUL,
        fontName="Helvetica-Bold",
        spaceBefore=18,
        spaceAfter=13,
        keepWithNext=True,
    ),
    "job": ParagraphStyle(
        "Job",
        fontSize=12,
        leading=17,
        textColor=VERDE,
        fontName="Helvetica-Bold",
        spaceBefore=13,
        spaceAfter=8,
        keepWithNext=True,
    ),
    "indice": ParagraphStyle(
        "IndiceGuia",
        fontSize=28,
        leading=34,
        textColor=AZUL,
        fontName="Helvetica-Bold",
        spaceAfter=20,
    ),
    "codigo": ParagraphStyle(
        "CodigoGuia", fontName="Courier", fontSize=8.5, leading=12, textColor=AZUL
    ),
    "etiqueta": ParagraphStyle(
        "EtiquetaGuia", fontSize=7.5, leading=10, textColor=VERDE, fontName="Helvetica-Bold"
    ),
    "celda": ParagraphStyle("CeldaGuia", fontSize=8.5, leading=12, textColor=AZUL),
    "cabecera": ParagraphStyle(
        "CabeceraGuia", fontSize=8, leading=11, textColor=colors.white, fontName="Helvetica-Bold"
    ),
    "lista": ParagraphStyle(
        "ListaGuia",
        fontSize=10,
        leading=15,
        textColor=AZUL,
        leftIndent=13,
        bulletIndent=0,
        spaceAfter=8,
    ),
}


def dar_formato(texto):
    texto = escape(texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#087F78">\1</link>', texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    return re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.5">\1</font>', texto)


class DocumentoGuia(BaseDocTemplate):
    def afterFlowable(self, elemento):
        if not isinstance(elemento, Paragraph):
            return
        if elemento.style.name not in ("Paso", "Job"):
            return
        titulo = elemento.getPlainText()
        clave = re.sub(r"\W+", "-", titulo.lower())
        nivel = 0 if elemento.style.name == "Paso" else 1
        self.canv.bookmarkPage(clave)
        self.canv.addOutlineEntry(titulo, clave, nivel, closed=False)
        self.canv.showOutline()
        if nivel == 0:
            self.notify("TOCEntry", (0, titulo, self.page, clave))


def portada(lienzo):
    lienzo.setFillColor(AZUL)
    lienzo.rect(0, 300, A4[0], A4[1] - 300, fill=1, stroke=0)
    lienzo.setFillColor(VERDE)
    lienzo.rect(48, 705, 45, 4, fill=1, stroke=0)
    lienzo.setFillColor(colors.white)
    lienzo.setFont("Helvetica-Bold", 10)
    lienzo.drawString(48, 730, "GUÍA PARA ALUMNOS")
    lienzo.setFont("Helvetica-Bold", 44)
    lienzo.drawString(48, 620, "Calculadora")
    lienzo.drawString(48, 565, "en Python")
    lienzo.setFont("Helvetica", 15)
    lienzo.drawString(48, 515, "Del programa a las pruebas automáticas")
    lienzo.setFont("Helvetica", 11)
    lienzo.drawString(48, 435, "Programación orientada a objetos")
    lienzo.drawString(48, 412, "Pruebas unitarias e integración")
    lienzo.drawString(48, 389, "Primeros pasos con GitHub Actions y SonarQube")
    lienzo.setFillColor(VERDE)
    lienzo.setFont("Helvetica-Bold", 10)
    lienzo.drawString(48, 247, "13 PASOS  /  12 JOBS  /  EJEMPLOS REPRODUCIBLES")
    lienzo.setFillColor(AZUL)
    lienzo.setFont("Helvetica-Bold", 17)
    lienzo.drawString(48, 207, "Lee, ejecuta, prueba y explica.")
    lienzo.setFillColor(GRIS)
    lienzo.setFont("Helvetica", 11)
    lienzo.drawString(48, 173, "Material de apoyo para trabajar en clase y por tu cuenta.")
    lienzo.drawString(48, 151, "Requisito: Python 3.12 o posterior.")
    lienzo.setFont("Helvetica", 8)
    lienzo.drawString(48, 64, "PROYECTO CALCULADORA  ·  MATERIAL DE CLASE")


def marco(lienzo, documento):
    lienzo.saveState()
    if documento.page == 1:
        portada(lienzo)
    else:
        lienzo.setFillColor(AZUL)
        lienzo.setFont("Helvetica-Bold", 8)
        lienzo.drawString(48, A4[1] - 36, "CALCULADORA EN PYTHON")
        lienzo.setFillColor(GRIS)
        lienzo.setFont("Helvetica", 8)
        lienzo.drawRightString(A4[0] - 48, A4[1] - 36, "GUÍA PARA ALUMNOS")
        lienzo.setStrokeColor(BORDE)
        lienzo.line(48, 43, A4[0] - 48, 43)
        lienzo.setFont("Helvetica", 7.5)
        lienzo.drawString(48, 28, "Python · Pruebas automáticas · DevOps")
        lienzo.drawRightString(A4[0] - 48, 28, f"{documento.page:02d}")
    lienzo.restoreState()


def bloque_codigo(fragmento):
    lineas = fragmento.splitlines()
    lenguaje = lineas[0].removeprefix("```")
    etiqueta = {
        "sh": "TERMINAL",
        "bat": "WINDOWS CMD",
        "python": "PYTHON",
        "text": "EJEMPLO DE EJECUCIÓN",
    }.get(lenguaje, "EJEMPLO")
    bloque = Table(
        [
            [Paragraph(etiqueta, ESTILOS["etiqueta"])],
            [Preformatted("\n".join(lineas[1:-1]), ESTILOS["codigo"])],
        ],
        colWidths=[ANCHO],
    )
    bloque.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FONDO),
                ("LINEBEFORE", (0, 0), (0, -1), 2, VERDE),
                ("LEFTPADDING", (0, 0), (-1, -1), 13),
                ("RIGHTPADDING", (0, 0), (-1, -1), 13),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return [KeepTogether([bloque, Spacer(1, 12)])]


def bloque_tabla(fragmento):
    filas = []
    for linea in fragmento.splitlines():
        if re.fullmatch(r"[|:\- ]+", linea):
            continue
        estilo = ESTILOS["cabecera"] if not filas else ESTILOS["celda"]
        filas.append(
            [
                Paragraph(dar_formato(celda.strip()), estilo)
                for celda in linea.strip().strip("|").split("|")
            ]
        )
    anchos = {2: [125, ANCHO - 125], 3: [89, 141, ANCHO - 230], 4: [38, 90, 164, ANCHO - 292]}[
        len(filas[0])
    ]
    tabla = Table(filas, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FONDO]),
                ("LINEBELOW", (0, 0), (-1, 0), 2, VERDE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return [KeepTogether([tabla, Spacer(1, 12)])]


def bloque_texto(fragmento):
    if fragmento.startswith("# "):
        return []
    if fragmento.startswith("## "):
        return [CondPageBreak(340), Paragraph(dar_formato(fragmento[3:]), ESTILOS["paso"])]
    if fragmento.startswith("### "):
        return [CondPageBreak(100), Paragraph(dar_formato(fragmento[4:]), ESTILOS["job"])]
    if fragmento.startswith("|"):
        return bloque_tabla(fragmento)
    parrafos = []
    for elemento in re.split(r"\n(?=- |\d+\. )", fragmento):
        elemento = " ".join(elemento.splitlines())
        if elemento.startswith("- "):
            parrafos.append(Paragraph(dar_formato(elemento[2:]), ESTILOS["lista"], bulletText="•"))
        else:
            parrafos.append(Paragraph(dar_formato(elemento), ESTILOS["texto"]))
    return parrafos


def crear_guia(origen=Path("GUIA_ALUMNOS.md"), destino=Path("material/GUIA_ALUMNOS.pdf")):
    destino.parent.mkdir(parents=True, exist_ok=True)
    indice = TableOfContents()
    indice.levelStyles = [
        ParagraphStyle("EntradaIndice", fontSize=10, leading=15, textColor=AZUL, spaceBefore=10)
    ]
    contenido = [
        Spacer(1, 600),
        PageBreak(),
        Paragraph("Tu ruta de trabajo", ESTILOS["indice"]),
        Paragraph(
            "Consulta cada paso y regresa a los ejemplos cuando lo necesites. "
            "El índice y los marcadores del PDF permiten navegar por la guía.",
            ESTILOS["texto"],
        ),
        Spacer(1, 12),
        indice,
        PageBreak(),
        Paragraph("Antes de empezar", ESTILOS["indice"]),
    ]
    texto = origen.read_text(encoding="utf-8")
    for fragmento in re.split(r"(```[^\n]*\n.*?```)", texto, flags=re.S):
        if fragmento.startswith("```"):
            contenido.extend(bloque_codigo(fragmento))
        else:
            for bloque in fragmento.split("\n\n"):
                if bloque.strip():
                    contenido.extend(bloque_texto(bloque.strip()))
    documento = DocumentoGuia(
        str(destino),
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=65,
        bottomMargin=62,
        invariant=1,
        lang="es-MX",
        title="Guía para alumnos · Calculadora en Python",
        author="Proyecto Calculadora",
        subject="Programación, pruebas y primeros pasos en DevOps",
    )
    documento.addPageTemplates(
        PageTemplate(
            id="Guia",
            frames=[
                Frame(
                    48,
                    62,
                    ANCHO,
                    A4[1] - 127,
                    leftPadding=0,
                    rightPadding=0,
                    topPadding=0,
                    bottomPadding=0,
                )
            ],
            onPage=marco,
        )
    )
    documento.multiBuild(contenido)


if __name__ == "__main__":
    crear_guia()
