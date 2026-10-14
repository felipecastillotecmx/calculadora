import json
import subprocess
import sys

from fastapi.testclient import TestClient

from api import aplicacion
from calculadora import principal

cliente = TestClient(aplicacion)


def test_programa_completo():
    respuesta = subprocess.run(
        [sys.executable, "calculadora.py"],
        input="5\n3\n8\n9\n10\nn\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert "Resultado: 9.0" in respuesta.stdout


def test_menu(monkeypatch, capsys):
    casos = [
        (["5", "3", "8", "9", "10", "n"], "Resultado: 9.0"),
        (["2", "8", "3", "s", "0"], "Resultado: 5.0"),
        (["4", "8", "2", "n"], "Resultado: 4.0"),
        (["6", "2", "3", "n"], "Resultado: 8.0"),
        (["9", "0"], "Elige una opción del 0 al 7"),
        (["1", "0", "0"], "La cantidad debe ser mayor"),
        (["1", "hola", "0"], "No se pudo calcular"),
        (["1", "1", "hola", "0"], "Escribe un número válido"),
        (["4", "2", "0", "0"], "cero"),
        (["1", "2", "1.5", "2.5", "n"], "Resultado: 4.0"),
    ]
    for entradas, esperado in casos:
        respuestas = iter(entradas)
        monkeypatch.setattr("builtins.input", lambda mensaje: next(respuestas))
        principal()
        assert esperado in capsys.readouterr().out


def test_fin_de_entrada(monkeypatch, capsys):
    def terminar(mensaje):
        raise EOFError

    monkeypatch.setattr("builtins.input", terminar)
    principal()
    assert "Hasta luego" in capsys.readouterr().out


def test_api():
    respuesta = cliente.post("/calcular", json={"operacion": "promedio", "numeros": [8, 9, 10]})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"resultado": 9}
    assert cliente.get("/estado").json() == {"estado": "correcto"}
    assert "/calcular" in cliente.get("/openapi.json").json()["paths"]
    assert respuesta.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert respuesta.headers["Cache-Control"] == "no-store"


def test_api_con_errores():
    casos = [
        {"operacion": "division", "numeros": [5, 0]},
        {"operacion": "suma", "numeros": [float("inf")]},
        {"operacion": "suma", "numeros": [1] * 1001},
        {"operacion": "suma", "numeros": [10**400]},
        {},
    ]
    for datos in casos:
        respuesta = cliente.post(
            "/calcular",
            content=json.dumps(datos),
            headers={"Content-Type": "application/json"},
        )
        assert respuesta.status_code == 400
        assert "detail" in respuesta.json()
    assert cliente.post("/calcular", json=[1, 2]).status_code == 422
