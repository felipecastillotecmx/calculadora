import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("operacion", "numeros", "esperado"),
    [
        ("suma", [1, 2], 3),
        ("resta", [8, 3], 5),
        ("multiplicacion", [2, 3], 6),
        ("division", [9, 2], 4.5),
        ("promedio", [8, 9, 10], 9),
        ("potencia", [2, 3], 8),
        ("mayor_menor", [5, -2, 10], {"mayor": 10, "menor": -2}),
    ],
)
def test_api_operaciones(operacion, numeros, esperado):
    response = client.post("/calcular", json={"operacion": operacion, "numeros": numeros})
    assert response.status_code == 200
    assert response.json() == {"resultado": esperado}


@pytest.mark.parametrize(
    ("datos", "status"),
    [
        ({"operacion": "division", "numeros": [1, 0]}, 400),
        ({"operacion": "potencia", "numeros": [-1, 0.5]}, 400),
        ({"operacion": "no", "numeros": [1]}, 400),
        ({"operacion": "suma", "numeros": []}, 422),
        ({"operacion": "suma", "numeros": [True]}, 422),
        ({"operacion": "suma", "numeros": ["1"]}, 422),
        ({"operacion": "suma", "numeros": [1], "extra": 4}, 422),
        ({"operacion": "suma", "numeros": [1] * 1001}, 422),
    ],
)
def test_api_validaciones(datos, status):
    assert client.post("/calcular", json=datos).status_code == status


def test_health_schema_seguridad():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "/calcular" in client.get("/openapi.json").json()["paths"]
    assert client.get("/docs").status_code == 404


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-Infinity", "1e9999"])
def test_api_rechaza_no_finitos_sin_error_interno(valor):
    response = client.post(
        "/calcular",
        content='{"operacion":"suma","numeros":[' + valor + "]}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_programa_completo_por_teclado():
    result = subprocess.run(
        [sys.executable, "calculadora.py"],
        input="5\n3\n8\n9\n10\nn\n",
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert "Resultado: 9.0" in result.stdout
