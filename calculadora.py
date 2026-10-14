import math

OPCIONES = {
    "1": "suma",
    "2": "resta",
    "3": "multiplicacion",
    "4": "division",
    "5": "promedio",
    "6": "potencia",
    "7": "mayor_menor",
}


class Calculadora:
    def __init__(self, operacion, numeros):
        if operacion not in OPCIONES.values():
            raise ValueError("La operación no es válida.")
        if not isinstance(numeros, list) or not numeros:
            raise ValueError("Ingresa al menos un número.")
        for numero in numeros:
            if type(numero) not in (int, float) or not math.isfinite(numero):
                raise ValueError("Ingresa números reales y finitos.")
        if operacion in ("resta", "division", "potencia") and len(numeros) != 2:
            raise ValueError("Esta operación necesita dos números.")

        self.operacion = operacion
        self.numeros = numeros.copy()

    def suma(self):
        return sum(self.numeros)

    def resta(self):
        return self.numeros[0] - self.numeros[1]

    def multiplicacion(self):
        total = 1
        for numero in self.numeros:
            total *= numero
        return total

    def division(self):
        if self.numeros[1] == 0:
            raise ValueError("No se puede dividir entre cero.")
        return self.numeros[0] / self.numeros[1]

    def promedio(self):
        return self.suma() / len(self.numeros)

    def potencia(self):
        try:
            return math.pow(self.numeros[0], self.numeros[1])
        except (ValueError, OverflowError) as error:
            raise ValueError("Esa potencia no produce un número real finito.") from error

    def mayor_menor(self):
        return {"mayor": max(self.numeros), "menor": min(self.numeros)}

    def resultado(self):
        if self.operacion == "suma":
            respuesta = self.suma()
        elif self.operacion == "resta":
            respuesta = self.resta()
        elif self.operacion == "multiplicacion":
            respuesta = self.multiplicacion()
        elif self.operacion == "division":
            respuesta = self.division()
        elif self.operacion == "promedio":
            respuesta = self.promedio()
        elif self.operacion == "potencia":
            respuesta = self.potencia()
        else:
            respuesta = self.mayor_menor()
        if isinstance(respuesta, float) and not math.isfinite(respuesta):
            raise ValueError("El resultado es demasiado grande.")
        return respuesta


def pedir_numeros(operacion):
    orden = {
        "resta": "primero menos segundo",
        "division": "primero entre segundo",
        "potencia": "primero elevado al segundo",
    }
    if operacion in orden:
        print(f"Orden: {orden[operacion]}.")
        cantidad = 2
    else:
        try:
            cantidad = int(input("¿Cuántos números vas a usar? "))
        except ValueError as error:
            raise ValueError("Escribe una cantidad entera de números.") from error
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero.")
    numeros = []
    for posicion in range(cantidad):
        try:
            numeros.append(float(input(f"Número {posicion + 1}: ")))
        except ValueError as error:
            raise ValueError("Escribe un número válido; puedes usar decimales.") from error
    return numeros


def principal():
    # Aquí pedimos los datos; la clase se encarga de hacer las cuentas.
    while True:
        try:
            print("\n1. Suma\n2. Resta\n3. Multiplicación\n4. División")
            print("5. Promedio\n6. Potencia\n7. Mayor y menor\n0. Salir")
            opcion = input("Elige una opción: ").strip()
            if opcion == "0":
                break
            if opcion not in OPCIONES:
                print("Elige una opción del 0 al 7.")
                continue
            operacion = OPCIONES[opcion]
            numeros = pedir_numeros(operacion)
            calculadora = Calculadora(operacion, numeros)
            resultado = calculadora.resultado()
            print(f"Resultado: {resultado}")
            if input("¿Quieres hacer otra operación? (s/n): ").strip().lower() not in (
                "s",
                "si",
                "sí",
            ):
                break
        except (ValueError, OverflowError) as error:
            print(f"No se pudo calcular: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    principal()
