# Calculadora en Python

Para recorrer el proyecto en clase, descarga la
[guía para alumnos en PDF](material/GUIA_ALUMNOS.pdf), con ejemplos de ejecución,
pruebas y una explicación de cada job del workflow. Su
[versión editable](GUIA_ALUMNOS.md) permite adaptar los ejemplos para cada grupo.

La actividad está en **calculadora.py**. No necesita instalar ninguna biblioteca:

```sh
python calculadora.py
```

Elige una operación, escribe los números y decide si quieres continuar.
Para el promedio de 8, 9 y 10, el resultado es 9.

La clase `Calculadora` guarda `operacion` y `numeros` en su constructor.
Tiene un método para cada operación y `resultado()` elige cuál llamar.
`principal()` se ocupa del menú, los `input()` y la presentación del resultado.

## Archivos del proyecto

| Archivo o carpeta | Para qué sirve |
|---|---|
| `calculadora.py` | Programa que pide la actividad: clase, operaciones y menú. |
| `pruebas/` | Ejemplos que comprueban que el programa funciona. |
| `api.py` | Expone la calculadora por HTTP para poder probarla con ZAP. |
| `herramientas/reporte_sonarqube.py` | Descarga los resultados del análisis. |
| `herramientas/reporte_pdf.py` | Da formato al PDF. |
| `herramientas/guia_pdf.py` | Convierte la guía editable en un PDF con índice y marcadores. |
| `material/GUIA_ALUMNOS.pdf` | Guía lista para compartir en clase. |
| `requirements.txt` | Bibliotecas de las pruebas, los análisis y el reporte. |
| `pyproject.toml` | Configuración de las pruebas, la cobertura y el formato. |
| `sonar-project.properties` | Indica qué archivos analiza SonarQube. |
| `.github/workflows/ci.yml` | Instrucciones que GitHub ejecuta automáticamente. |

## Probar el código

Con Python 3.12 o posterior, crea un entorno e instala las bibliotecas:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

En Windows, activa el entorno con `.venv\Scripts\activate`.

Una **prueba unitaria** comprueba una operación por separado. Por ejemplo:

```python
assert Calculadora("suma", [2, 3]).resultado() == 5
```

Una **prueba de integración** comprueba varias partes juntas: el menú con la
clase, o una petición HTTP con el cálculo. Los ejemplos están separados en
`pruebas/test_calculadora.py` y `pruebas/test_integracion.py`.
`pruebas/test_reporte.py` comprueba los reportes y el contenido y navegación del PDF de clase.

Después de editar la guía, regenera su PDF con las bibliotecas instaladas:

```sh
python -m herramientas.guia_pdf
```

El archivo se guarda en `material/GUIA_ALUMNOS.pdf`. Revisa su presentación antes
de compartirlo; el índice se actualiza automáticamente.

La **cobertura** indica qué partes del código ejecutaron las pruebas:

```sh
pytest --cov --cov-report=xml
```

Se mide todo el código Python del proyecto y se exige al menos 90 % de cobertura
de líneas y ramas. El archivo `coverage.xml` se envía a SonarQube.

## Qué hace GitHub Actions

Un **workflow** es la receta completa. Cada **job** hace una revisión concreta.
`needs` indica que un job debe esperar a otro. Los tres primeros pasos se repiten
porque cada job empieza en una máquina limpia: descargar el código, preparar
Python e instalar las bibliotecas.

| Job | Qué comprueba |
|---|---|
| Revisión del código | Errores de escritura y formato con Ruff. |
| Pruebas unitarias | Operaciones de la calculadora y reporte. |
| Pruebas de integración | Menú, clase y API trabajando juntos. |
| Cobertura | Ejecuta todas las pruebas y genera el XML. |
| Contraseñas y secretos | Busca credenciales en el historial con Gitleaks. |
| Seguridad estática | Busca problemas en Python con Bandit. |
| Vulnerabilidades de dependencias | Busca bibliotecas vulnerables con pip-audit. |
| Dependencias obsoletas | Informa si existen versiones más recientes. |
| OWASP ZAP | Prueba la API temporal dentro del runner. |
| SonarQube | Analiza el código e importa la cobertura. |
| Reporte | Comprueba el Quality Gate y publica el reporte y la guía en PDF. |
| Resumen | Muestra el resultado de todos los jobs. |

Se ejecuta con **push solo en main**, con **pull request** y de forma manual.
SonarQube Community analiza main; los PR ejecutan los demás controles.
Los hallazgos de seguridad bloquean el pipeline. Tener versiones más recientes
es informativo: no significa por sí mismo que haya una vulnerabilidad.

## SonarQube y entrega

El proyecto `calculadora` usa <https://sonarqube.lynvera.ai>.
El secreto de GitHub `SONAR_TOKEN` debe ser un **User Token** con permisos
**Browse** y **Execute Analysis**. No se escribe en el código.

En **Actions → ejecución → Artifacts**, descarga
**sonarqube-report-pdf-json-md**. El PDF conserva el resumen ejecutivo, distingue
cobertura e issues del proyecto completo y del código nuevo, y muestra el commit
analizado. `N/D` significa que no hay datos; no significa cero.

La guía también se regenera y se publica como **guia-para-alumnos-pdf** en esa
ejecución cuando aprueba el Quality Gate.

Entrega **calculadora.py** y **sonarqube.pdf**. Los reportes del análisis y los
archivos locales de desarrollo no se incluyen en los commits. La guía de clase
en `material/` sí se guarda en el repositorio para descargarla directamente.
