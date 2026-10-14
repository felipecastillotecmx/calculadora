import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from pypdf import PdfReader

from herramientas import reporte_sonarqube as reporte
from herramientas.guia_pdf import crear_guia


def datos_de_ejemplo():
    return {
        "project": "calculadora",
        "analysis_id": "analisis",
        "revision": "commit",
        "date": "2026-10-14T16:00:00+0000",
        "metrics": {"coverage": "100"},
        "quality_gate": {
            "status": "OK",
            "conditions": [
                {
                    "metricKey": "new_coverage",
                    "actualValue": "100",
                    "errorThreshold": "80",
                    "comparator": "LT",
                    "status": "OK",
                }
            ],
        },
        "overall_issues": [],
        "new_issues": [],
        "dashboard": reporte.SERVIDOR,
    }


def test_crear_reportes(tmp_path):
    datos = datos_de_ejemplo()
    reporte.guardar_reportes(datos, tmp_path)
    assert (tmp_path / "sonarqube.pdf").read_bytes().startswith(b"%PDF")
    assert len(PdfReader(tmp_path / "sonarqube.pdf").pages) == 2
    assert json.loads((tmp_path / "sonarqube.json").read_text()) == datos
    assert "Issues abiertos nuevos: **0**" in (tmp_path / "sonarqube.md").read_text()


def test_guia_para_alumnos(tmp_path):
    destino = tmp_path / "guia.pdf"
    crear_guia(Path("GUIA_ALUMNOS.md"), destino)
    documento = PdfReader(destino)
    texto = "\n".join(pagina.extract_text() for pagina in documento.pages)
    for numero in range(1, 14):
        assert f"Paso {numero} " in texto
    assert "test_suma_con_negativos" in texto
    assert "Preguntas para explicar lo aprendido" in texto
    assert documento.outline
    assert any(pagina.get("/Annots") for pagina in documento.pages)


def test_reporte_sin_datos_y_con_hallazgos(tmp_path):
    datos = datos_de_ejemplo()
    datos["metrics"] = {"coverage": "N/D"}
    datos["date"] = "2026-10-14"
    datos["quality_gate"] = {"status": "NONE", "conditions": []}
    datos["overall_issues"] = [{"message": "A < B & C", "severity": "MAJOR"}]
    datos["new_issues"] = datos["overall_issues"]
    reporte.guardar_reportes(datos, tmp_path)
    assert (tmp_path / "sonarqube.pdf").exists()


def test_conexion(monkeypatch):
    monkeypatch.setenv("SONAR_TOKEN", "prueba")
    respuesta = Mock(status_code=200)
    respuesta.json.return_value = {"estado": "correcto"}
    monkeypatch.setattr(reporte.requests, "get", Mock(return_value=respuesta))
    assert reporte.consultar("system/status") == {"estado": "correcto"}
    respuesta.status_code = 403
    with pytest.raises(PermissionError):
        reporte.consultar("system/status")
    respuesta.status_code = 302
    with pytest.raises(RuntimeError):
        reporte.consultar("system/status")
    respuesta.raise_for_status.side_effect = requests.HTTPError()
    with pytest.raises(requests.HTTPError):
        reporte.consultar("system/status")


def test_espera_del_analisis(monkeypatch):
    monkeypatch.setattr(reporte.time, "sleep", lambda segundos: None)
    for estado, error in [("PENDING", TimeoutError), ("FAILED", RuntimeError)]:
        monkeypatch.setattr(reporte, "consultar", Mock(return_value={"task": {"status": estado}}))
        with pytest.raises(error):
            reporte.esperar_analisis("tarea")
    monkeypatch.setattr(
        reporte,
        "consultar",
        Mock(return_value={"task": {"status": "SUCCESS", "analysisId": "analisis"}}),
    )
    assert reporte.esperar_analisis("tarea") == "analisis"


def test_paginacion(monkeypatch):
    monkeypatch.setattr(
        reporte,
        "consultar",
        Mock(
            side_effect=[
                {"issues": [{}] * 500, "paging": {"total": 501}},
                {"issues": [{}], "paging": {"total": 501}},
            ]
        ),
    )
    assert len(reporte.obtener_problemas(nuevos=True)) == 501
    monkeypatch.setattr(
        reporte, "consultar", Mock(return_value={"issues": [], "paging": {"total": 10001}})
    )
    with pytest.raises(RuntimeError):
        reporte.obtener_problemas()


def test_datos_y_ejecucion_del_reporte(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_SHA", "commit")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "resumen.md"))
    respuestas = {
        "project_analyses/search": {
            "analyses": [{"key": "analisis", "revision": "commit", "date": "2026-10-14"}]
        },
        "measures/component": {
            "component": {
                "measures": [
                    {"metric": "coverage", "value": "100"},
                    {"metric": "new_coverage", "period": {"value": "90"}},
                ]
            }
        },
        "qualitygates/project_status": {"projectStatus": {"status": "OK", "conditions": []}},
        "issues/search": {"issues": [], "paging": {"total": 0}},
        "ce/task": {"task": {"status": "SUCCESS", "analysisId": "analisis"}},
    }
    monkeypatch.setattr(reporte, "consultar", lambda ruta, **parametros: respuestas[ruta])
    assert reporte.obtener_datos("analisis")["metrics"]["new_coverage"] == "90"
    with pytest.raises(RuntimeError):
        reporte.obtener_datos("otro")
    monkeypatch.chdir(tmp_path)
    Path(".scannerwork").mkdir()
    Path(".scannerwork/report-task.txt").write_text("ceTaskId=tarea\n")
    reporte.principal()
    assert Path("reports/sonarqube/sonarqube.pdf").exists()
    assert "Resumen de SonarQube" in Path("resumen.md").read_text()
    respuestas["qualitygates/project_status"]["projectStatus"]["status"] = "ERROR"
    monkeypatch.delenv("GITHUB_STEP_SUMMARY")
    with pytest.raises(SystemExit):
        reporte.principal()


def test_no_mezcla_analisis(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "commit")
    monkeypatch.setattr(reporte, "obtener_problemas", lambda nuevos=False: [])
    monkeypatch.setattr(
        reporte,
        "consultar",
        Mock(
            side_effect=[
                {"analyses": [{"key": "analisis", "revision": "commit", "date": "2026-10-14"}]},
                {"component": {"measures": []}},
                {"projectStatus": {"status": "OK"}},
                {"analyses": [{"key": "otro"}]},
            ]
        ),
    )
    with pytest.raises(RuntimeError, match="Otro análisis"):
        reporte.obtener_datos("analisis")
