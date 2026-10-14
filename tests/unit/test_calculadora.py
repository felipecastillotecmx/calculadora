import math

import pytest

from calculadora import Calculadora, capturar_numeros, main


@pytest.mark.parametrize(
    ("operacion", "numeros", "esperado"),
    [
        ("suma", [1.5, -2, 3], 2.5),
        ("resta", [2, 8], -6),
        ("multiplicacion", [2, -3, 0.5], -3),
        ("division", [9, 2], 4.5),
        ("promedio", [8, 9, 10], 9),
        ("potencia", [2, -2], 0.25),
        ("mayor_menor", [3, -8, 4], {"mayor": 4, "menor": -8}),
        ("1", [1], 1),
        ("promedio", [1e308, 1e308], 1e308),
        ("mayor_menor", [3], {"mayor": 3, "menor": 3}),
    ],
)
def test_operaciones(operacion, numeros, esperado):
    assert Calculadora(operacion, numeros).resultado() == esperado


@pytest.mark.parametrize(
    ("operacion", "numeros"),
    [
        ("desconocida", [1]),
        ("suma", []),
        ("promedio", []),
        ("suma", [True]),
        ("suma", ["2"]),
        ("suma", [math.nan]),
        ("suma", [math.inf]),
        ("suma", [10**400]),
        ("resta", [1]),
        ("division", [1, 2, 3]),
        ("division", [1, 0]),
        ("potencia", [-2, 0.5]),
        ("potencia", [0, -1]),
        ("potencia", [1e308, 2]),
        ("suma", [1e308, 1e308]),
        ("multiplicacion", [1e308, 1e308]),
        ("division", [1e308, 1e-308]),
    ],
)
def test_rechaza_datos_invalidos(operacion, numeros):
    with pytest.raises(ValueError):
        Calculadora(operacion, numeros).resultado()


def test_constructor_copia_atributos():
    numeros = [1, 2]
    objeto = Calculadora("suma", numeros)
    numeros.append(99)
    assert objeto.operacion == "suma"
    assert objeto.numeros == [1, 2]


@pytest.mark.parametrize(
    ("entradas", "texto"),
    [
        (["5", "3", "8", "9", "10", "n"], "Resultado: 9.0"),
        (["2", "8", "3", "s", "0"], "Resultado: 5.0"),
        (["4", "8", "2", "n"], "Resultado: 4.0"),
        (["6", "2", "3", "n"], "Resultado: 8.0"),
        (["9", "0"], "Opción inválida"),
        (["1", "0", "0"], "al menos un número"),
        (["1", "texto", "0"], "Datos inválidos"),
        (["1", "1", "no", "0"], "Datos inválidos"),
        (["4", "2", "0", "0"], "dividir entre cero"),
    ],
)
def test_menu(monkeypatch, capsys, entradas, texto):
    iterator = iter(entradas)
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))
    main()
    assert texto in capsys.readouterr().out


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_salida_interrumpida(monkeypatch, capsys, error):
    def interrumpir(_):
        raise error

    monkeypatch.setattr("builtins.input", interrumpir)
    main()
    assert "Hasta luego" in capsys.readouterr().out


def test_captura_decimales(monkeypatch):
    iterator = iter(["2", "1.5", "-2.75"])
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))
    assert capturar_numeros("suma") == [1.5, -2.75]
