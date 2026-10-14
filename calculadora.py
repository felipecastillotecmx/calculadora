"""Calculadora orientada a objetos y menú interactivo de la actividad."""

import math
from collections.abc import Callable, Iterable

OPERACIONES = {
    "1": "suma",
    "2": "resta",
    "3": "multiplicacion",
    "4": "division",
    "5": "promedio",
    "6": "potencia",
    "7": "mayor_menor",
}
BINARIAS = {"resta", "division", "potencia"}


class Calculadora:
    """El constructor guarda la operación y una copia de los números."""

    def __init__(self, operacion: str, numeros: Iterable[float]) -> None:
        self.operacion = OPERACIONES.get(operacion, operacion)
        if self.operacion not in OPERACIONES.values():
            raise ValueError("Operación inválida. Elige una opción del menú.")
        self.numeros = list(numeros)
        if not self.numeros:
            raise ValueError("Debes ingresar al menos un número.")
        if any(isinstance(n, bool) or not isinstance(n, (int, float)) for n in self.numeros):
            raise ValueError("Los valores deben ser números reales.")
        try:
            self.numeros = [float(n) for n in self.numeros]
        except OverflowError as exc:
            raise ValueError("Los números son demasiado grandes.") from exc
        if not all(math.isfinite(n) for n in self.numeros):
            raise ValueError("Los números deben ser finitos.")
        if self.operacion in BINARIAS and len(self.numeros) != 2:
            raise ValueError("Esta operación requiere exactamente dos números.")

    def suma(self) -> float:
        return sum(self.numeros)

    def resta(self) -> float:
        return self.numeros[0] - self.numeros[1]

    def multiplicacion(self) -> float:
        return math.prod(self.numeros)

    def division(self) -> float:
        if self.numeros[1] == 0:
            raise ValueError("No se puede dividir entre cero.")
        return self.numeros[0] / self.numeros[1]

    def promedio(self) -> float:
        # Dividir antes de sumar evita desbordar promedios de valores grandes.
        return math.fsum(n / len(self.numeros) for n in self.numeros)

    def potencia(self) -> float:
        try:
            return math.pow(self.numeros[0], self.numeros[1])
        except (ValueError, OverflowError) as exc:
            raise ValueError("La potencia no produce un número real finito.") from exc

    def mayor_menor(self) -> dict[str, float]:
        return {"mayor": max(self.numeros), "menor": min(self.numeros)}

    def resultado(self) -> float | dict[str, float]:
        """Despacha la operación a su método y valida el resultado."""
        metodos: dict[str, Callable[[], float | dict[str, float]]] = {
            "suma": self.suma,
            "resta": self.resta,
            "multiplicacion": self.multiplicacion,
            "division": self.division,
            "promedio": self.promedio,
            "potencia": self.potencia,
            "mayor_menor": self.mayor_menor,
        }
        respuesta = metodos[self.operacion]()
        if isinstance(respuesta, float) and not math.isfinite(respuesta):
            raise ValueError("El resultado es demasiado grande.")
        return respuesta


def capturar_numeros(operacion: str) -> list[float]:
    if operacion in BINARIAS:
        instrucciones = {
            "resta": "primero menos segundo",
            "division": "primero entre segundo",
            "potencia": "primero elevado al segundo",
        }
        print(f"Orden: {instrucciones[operacion]}.")
        cantidad = 2
    else:
        cantidad = int(input("Cantidad de números: "))
        if cantidad < 1:
            raise ValueError("Debes ingresar al menos un número.")
    return [float(input(f"Número {i + 1}: ")) for i in range(cantidad)]


def main() -> None:
    """La captura y presentación quedan fuera de la clase de cálculos."""
    try:
        while True:
            print(
                "\n1. Suma\n2. Resta\n3. Multiplicación\n4. División\n"
                "5. Promedio\n6. Potencia\n7. Mayor y menor\n0. Salir"
            )
            opcion = input("Operación: ").strip()
            if opcion == "0":
                break
            try:
                if opcion not in OPERACIONES:
                    raise ValueError("Opción inválida. Elige un número del 0 al 7.")
                numeros = capturar_numeros(OPERACIONES[opcion])
                objeto = Calculadora(opcion, numeros)
                respuesta = objeto.resultado()
                print(f"Resultado: {respuesta}")
            except ValueError as exc:
                print(f"Datos inválidos: {exc}")
                continue
            if input("¿Otra operación? (s/n): ").strip().lower() not in {"s", "si", "sí"}:
                break
    except (EOFError, KeyboardInterrupt):
        print("\nHasta luego.")


if __name__ == "__main__":
    main()
