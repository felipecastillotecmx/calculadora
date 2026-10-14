"""Exporta el análisis real de SonarQube a JSON, Markdown y PDF."""

import json
import os
import time
from html import escape
from pathlib import Path
from typing import Any

import requests
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

METRICAS = (
    "coverage",
    "line_coverage",
    "branch_coverage",
    "lines_to_cover",
    "uncovered_lines",
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
    "ncloc",
    "duplicated_lines_density",
    "new_coverage",
    "new_lines_to_cover",
    "new_uncovered_lines",
    "new_bugs",
    "new_vulnerabilities",
    "new_code_smells",
    "new_security_hotspots",
)


class SonarClient:
    def __init__(self, host: str, token: str) -> None:
        if host != "https://sonarqube.lynvera.ai":
            raise ValueError("El destino autorizado es https://sonarqube.lynvera.ai.")
        self.host = host
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        response = self.session.get(
            f"{self.host}/api/{endpoint}", params=params, timeout=30, allow_redirects=False
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise RuntimeError("SonarQube no devolvió una respuesta HTTP 200.")
        return dict(response.json())

    def esperar(self, task_id: str, intentos: int = 90) -> str:
        for _ in range(intentos):
            task = self.get("ce/task", id=task_id)["task"]
            if task["status"] == "SUCCESS":
                return str(task["analysisId"])
            if task["status"] in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"El análisis terminó en {task['status']}.")
            time.sleep(5)
        raise TimeoutError("SonarQube no terminó el análisis en el tiempo previsto.")

    def issues(self, project: str, nuevos: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        pagina = 1
        while True:
            params: dict[str, Any] = {
                "componentKeys": project,
                "resolved": "false",
                "p": pagina,
                "ps": 500,
            }
            if nuevos:
                params["sinceLeakPeriod"] = "true"
            response = self.get("issues/search", **params)
            items.extend(response["issues"])
            total = response["paging"]["total"]
            if len(items) >= total:
                return items
            if pagina * 500 >= 10000:
                raise RuntimeError("El reporte excede el límite de paginación de SonarQube.")
            pagina += 1

    def recolectar(self, project: str, analysis_id: str, revision: str) -> dict[str, Any]:
        analisis = self.get("project_analyses/search", project=project, ps=1)["analyses"]
        if not analisis or analisis[0]["key"] != analysis_id:
            raise RuntimeError("El proyecto tiene otro análisis; evita mezclar ejecuciones.")
        if revision and analisis[0].get("revision") != revision:
            raise RuntimeError("La revisión analizada no coincide con el commit del pipeline.")
        measures = self.get("measures/component", component=project, metricKeys=",".join(METRICAS))[
            "component"
        ]["measures"]
        metrics = {}
        for measure in measures:
            metrics[measure["metric"]] = measure.get(
                "value", measure.get("period", {}).get("value", "N/D")
            )
        data = {
            "project": project,
            "analysis_id": analysis_id,
            "revision": revision,
            "date": analisis[0]["date"],
            "metrics": metrics,
            "quality_gate": self.get("qualitygates/project_status", analysisId=analysis_id)[
                "projectStatus"
            ],
            "overall_issues": self.issues(project),
            "new_issues": self.issues(project, True),
            "dashboard": f"{self.host}/dashboard?id={project}&codeScope=overall",
        }
        # Las métricas/issues son del último análisis: comprobar también al terminar.
        latest = self.get("project_analyses/search", project=project, ps=1)["analyses"]
        if latest[0]["key"] != analysis_id:
            raise RuntimeError("Otro análisis cambió el proyecto durante la exportación.")
        return data


def resumen(data: dict[str, Any]) -> str:
    metrics = data["metrics"]
    return (
        f"# Resumen de SonarQube: {data['project']}\n\n"
        f"- Quality Gate: **{data['quality_gate']['status']}**\n"
        f"- Cobertura de todo el proyecto: **{metrics.get('coverage', 'N/D')} %**\n"
        f"- Cobertura de código nuevo: **{metrics.get('new_coverage', 'N/D')}**"
        " (N/D significa que no existe una línea base o código nuevo medible).\n"
        f"- Issues abiertos totales: **{len(data['overall_issues'])}**\n"
        f"- Issues abiertos nuevos: **{len(data['new_issues'])}**\n"
        f"- Commit: `{data['revision']}`\n"
        f"- Análisis: `{data['analysis_id']}`\n"
        f"- Fecha del análisis: {data['date']}\n\n"
        f"[Ver todo el proyecto en SonarQube]({data['dashboard']})\n\n"
        "Los issues son hallazgos abiertos de SonarQube; los security hotspots son "
        "revisiones de seguridad separadas. La cobertura general incluye calculadora.py, "
        "api.py y los scripts de CI. La cobertura de código nuevo depende de la línea "
        "base configurada en el servidor.\n"
    )


def exportar(data: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "sonarqube.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (output / "sonarqube.md").write_text(resumen(data), encoding="utf-8")
    styles = getSampleStyleSheet()
    story: list[Any] = [Paragraph("Resumen del análisis SonarQube", styles["Title"])]
    for line in resumen(data).splitlines():
        if line:
            story.append(Paragraph(escape(line), styles["BodyText"]))
            story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Métricas: proyecto completo y código nuevo", styles["Heading2"]))
    rows = [["Métrica (new_ = código nuevo)", "Valor"]]
    rows += [[metric, str(data["metrics"].get(metric, "N/D"))] for metric in METRICAS]
    table = Table(rows, colWidths=[12 * cm, 4 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ]
        )
    )
    story.append(table)
    for scope, label in [
        ("overall_issues", "Issues abiertos de todo el proyecto"),
        ("new_issues", "Issues abiertos de código nuevo"),
    ]:
        story.append(Paragraph(label, styles["Heading2"]))
        if not data[scope]:
            story.append(Paragraph("Sin issues abiertos en este alcance.", styles["BodyText"]))
        for issue in data[scope]:
            line = (
                f"{issue.get('severity', 'N/D')} | {issue.get('type', 'N/D')} | "
                f"{issue.get('component', '')}:{issue.get('line', 'N/D')} | "
                f"{issue.get('message', '')}"
            )
            story.append(Paragraph(escape(line), styles["BodyText"]))
    story.append(Paragraph("Condiciones del Quality Gate", styles["Heading2"]))
    for condition in data["quality_gate"].get("conditions", []):
        story.append(Paragraph(escape(json.dumps(condition)), styles["BodyText"]))
    SimpleDocTemplate(str(output / "sonarqube.pdf"), title="Reporte SonarQube Calculadora").build(
        story
    )


def main() -> None:
    metadata = dict(
        line.split("=", 1)
        for line in Path(".scannerwork/report-task.txt").read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    client = SonarClient(os.environ["SONAR_HOST_URL"], os.environ["SONAR_TOKEN"])
    analysis_id = client.esperar(metadata["ceTaskId"])
    data = client.recolectar("calculadora", analysis_id, os.environ.get("GITHUB_SHA", ""))
    exportar(data, Path("reports/sonarqube"))
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write(resumen(data))
    if data["quality_gate"]["status"] != "OK":
        raise SystemExit("El Quality Gate de SonarQube no fue aprobado.")


if __name__ == "__main__":
    main()
