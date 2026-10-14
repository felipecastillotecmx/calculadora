from unittest.mock import Mock

import pytest
import requests

from scripts import sonar_report as report


@pytest.fixture
def data():
    return {
        "project": "calculadora",
        "analysis_id": "a1",
        "revision": "abc",
        "date": "2026-10-14",
        "dashboard": "https://sonarqube.lynvera.ai",
        "metrics": {"coverage": "100", "new_coverage": "90"},
        "quality_gate": {"status": "OK", "conditions": [{"metric": "coverage"}]},
        "overall_issues": [{"severity": "MAJOR", "message": "A < B"}],
        "new_issues": [],
    }


def test_exportacion_real(tmp_path, data):
    report.exportar(data, tmp_path)
    assert (tmp_path / "sonarqube.pdf").read_bytes().startswith(b"%PDF")
    assert '"coverage": "100"' in (tmp_path / "sonarqube.json").read_text()
    assert "Issues abiertos nuevos: **0**" in (tmp_path / "sonarqube.md").read_text()


def test_destino_autorizado():
    with pytest.raises(ValueError):
        report.SonarClient("http://example.com", "test")


def test_http(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    response = Mock(status_code=200)
    response.json.return_value = {"ok": True}
    getter = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", getter)
    assert client.get("system/status") == {"ok": True}
    assert getter.call_args.kwargs["timeout"] == 30
    response.status_code = 302
    with pytest.raises(RuntimeError):
        client.get("system/status")
    response.raise_for_status.side_effect = requests.HTTPError()
    with pytest.raises(requests.HTTPError):
        client.get("system/status")


@pytest.mark.parametrize("status", ["FAILED", "CANCELED"])
def test_analisis_fallido(monkeypatch, status):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    monkeypatch.setattr(client, "get", Mock(return_value={"task": {"status": status}}))
    with pytest.raises(RuntimeError):
        client.esperar("task")


def test_espera_y_timeout(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    monkeypatch.setattr(report.time, "sleep", Mock())
    monkeypatch.setattr(
        client,
        "get",
        Mock(
            side_effect=[
                {"task": {"status": "PENDING"}},
                {"task": {"status": "SUCCESS", "analysisId": "a1"}},
            ]
        ),
    )
    assert client.esperar("task") == "a1"
    with pytest.raises(TimeoutError):
        client.esperar("task", intentos=0)


def test_issues_paginados(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    getter = Mock(
        side_effect=[
            {"issues": [{}] * 500, "paging": {"total": 501}},
            {"issues": [{}], "paging": {"total": 501}},
        ]
    )
    monkeypatch.setattr(client, "get", getter)
    assert len(client.issues("calculadora", True)) == 501
    assert getter.call_args.kwargs["sinceLeakPeriod"] == "true"


def test_issues_limite(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    monkeypatch.setattr(
        client, "get", Mock(return_value={"issues": [{}] * 500, "paging": {"total": 10001}})
    )
    with pytest.raises(RuntimeError):
        client.issues("calculadora")


def test_recolectar(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    analisis = {"analyses": [{"key": "a1", "revision": "abc", "date": "hoy"}]}
    getter = Mock(
        side_effect=[
            analisis,
            {
                "component": {
                    "measures": [
                        {"metric": "coverage", "value": "100"},
                        {"metric": "new_coverage", "period": {"value": "90"}},
                    ]
                }
            },
            {"projectStatus": {"status": "OK"}},
            analisis,
        ]
    )
    monkeypatch.setattr(client, "get", getter)
    monkeypatch.setattr(client, "issues", Mock(return_value=[]))
    assert client.recolectar("calculadora", "a1", "abc")["metrics"]["new_coverage"] == "90"


@pytest.mark.parametrize(
    ("analyses", "revision"),
    [
        ([], "abc"),
        ([{"key": "otro"}], "abc"),
        ([{"key": "a1", "revision": "otro"}], "abc"),
    ],
)
def test_no_mezcla_analisis(monkeypatch, analyses, revision):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    monkeypatch.setattr(client, "get", Mock(return_value={"analyses": analyses}))
    with pytest.raises(RuntimeError):
        client.recolectar("calculadora", "a1", revision)


def test_detecta_cambio_durante_exportacion(monkeypatch):
    client = report.SonarClient("https://sonarqube.lynvera.ai", "test")
    monkeypatch.setattr(
        client,
        "get",
        Mock(
            side_effect=[
                {"analyses": [{"key": "a1", "date": "hoy"}]},
                {"component": {"measures": []}},
                {"projectStatus": {"status": "OK"}},
                {"analyses": [{"key": "otro"}]},
            ]
        ),
    )
    monkeypatch.setattr(client, "issues", Mock(return_value=[]))
    with pytest.raises(RuntimeError):
        client.recolectar("calculadora", "a1", "")


@pytest.mark.parametrize("estado", ["OK", "ERROR"])
@pytest.mark.parametrize("con_resumen", [True, False])
def test_main(monkeypatch, tmp_path, data, estado, con_resumen):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".scannerwork").mkdir()
    (tmp_path / ".scannerwork/report-task.txt").write_text("ceTaskId=task\n")
    monkeypatch.setenv("SONAR_HOST_URL", "https://sonarqube.lynvera.ai")
    monkeypatch.setenv("SONAR_TOKEN", "test")
    if con_resumen:
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    else:
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(report.SonarClient, "esperar", Mock(return_value="a1"))
    data["quality_gate"]["status"] = estado
    monkeypatch.setattr(report.SonarClient, "recolectar", Mock(return_value=data))
    if estado == "ERROR":
        with pytest.raises(SystemExit):
            report.main()
    else:
        report.main()
    assert (tmp_path / "reports/sonarqube/sonarqube.pdf").exists()
    if con_resumen:
        assert "Resumen" in (tmp_path / "summary.md").read_text()
