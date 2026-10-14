import pytest

from calculadora import Calculadora


def test_suma():
    assert Calculadora("suma", [1.5, 2, -1]).resultado() == 2.5


def test_resta():
    assert Calculadora("resta", [3, 8]).resultado() == -5


def test_multiplicacion():
    assert Calculadora("multiplicacion", [2, 3, 0.5]).resultado() == 3


def test_division():
    assert Calculadora("division", [9, 2]).resultado() == 4.5


def test_promedio():
    assert Calculadora("promedio", [8, 9, 10]).resultado() == 9


def test_promedio_con_decimales():
    assert Calculadora("promedio", [7.5, 8.5, 9.5]).resultado() == 8.5


def test_potencia():
    assert Calculadora("potencia", [2, 3]).resultado() == 8


def test_mayor_y_menor():
    assert Calculadora("mayor_menor", [4, -2, 8]).resultado() == {"mayor": 8, "menor": -2}


def test_division_entre_cero():
    with pytest.raises(ValueError, match="cero"):
        Calculadora("division", [5, 0]).resultado()


def test_datos_invalidos():
    casos = [
        ("otra", [1]),
        ("suma", []),
        ("suma", None),
        ("suma", ["hola"]),
        ("suma", [True]),
        ("suma", [float("inf")]),
        ("suma", [float("nan")]),
        ("resta", [1]),
        ("division", [1, 2, 3]),
    ]
    for operacion, numeros in casos:
        with pytest.raises(ValueError):
            Calculadora(operacion, numeros)


def test_resultados_no_validos():
    with pytest.raises(ValueError):
        Calculadora("potencia", [-2, 0.5]).resultado()
    with pytest.raises(ValueError):
        Calculadora("suma", [1e308, 1e308]).resultado()


def test_guarda_una_copia_de_los_numeros():
    numeros = [1, 2]
    calculadora = Calculadora("suma", numeros)
    numeros.append(100)
    assert calculadora.numeros == [1, 2]
