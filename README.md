# Calculadora con programación orientada a objetos

Solución de **Clase 7 - Actividad en Clase 2**. La clase `Calculadora` guarda la
operación y los números; `resultado()` llama al método correspondiente. Soporta
suma, resta, multiplicación, división, promedio, potencia y mayor/menor.
Valida decimales, listas vacías, división entre cero y resultados no finitos.
El menú permite repetir o salir. **El entregable `calculadora.py` funciona sin
instalar dependencias**, con Python 3.12 o posterior:

```sh
python calculadora.py
```

Ejemplo: opción `5`, cantidad `3`, números `8`, `9`, `10` → resultado `9.0`.
Para resta/división/potencia se piden dos números y se explica su orden.
Para las demás operaciones se solicita una cantidad positiva de números.

Elementos de POO: clase `Calculadora`; constructor `__init__`; atributos
`self.operacion` y `self.numeros`; objeto `objeto` en `main()`; métodos
`suma()`, `resta()`, etc., y `resultado()`. El menú y la captura están separados
respecto de los cálculos. Los comentarios explican las decisiones importantes.

## Desarrollo y pruebas

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov --cov-report=xml --cov-report=html
ruff check .
ruff format --check .
mypy calculadora.py api.py scripts
bandit -r calculadora.py api.py scripts
pip-audit -r requirements-dev.txt
uvicorn api:app --host 127.0.0.1 --port 8000 --no-server-header
```

La API reutiliza la clase. Endpoints: `GET /health`, `GET /openapi.json` y
`POST /calcular` con `{"operacion":"promedio","numeros":[8,9,10]}`.
Valida tipos estrictos, limita listas a 1000 números y devuelve errores 400/422.
La API sirve para integración y pruebas activas de OWASP ZAP exclusivamente en
el runner temporal; no se publica un servidor ni se escanean sitios externos.

## Pipeline de GitHub Actions

Se activa con push únicamente a `main`, pull request y ejecución manual.
Los pushes a ramas de trabajo se validan mediante su PR para evitar ejecuciones
duplicadas. Las acciones se fijan a
commits; Dependabot revisa actualizaciones. Se conservan artefactos de pruebas
y seguridad. No se guardan secretos, entornos, reportes ni temporales en Git.

| Job | Controles / dependencias |
|---|---|
| Formato y tipos | Ruff y mypy |
| Unitarias | Python 3.12, 3.13 y 3.14 |
| Integración | Menú como proceso, API y servidor HTTP real |
| Cobertura | Depende de pruebas; mínimo 90 % de líneas y ramas |
| Contraseñas y secretos | Gitleaks revisa todo el historial, con resultados censurados |
| Seguridad estática | Bandit revisa todo el código |
| Vulnerabilidades de dependencias | pip-audit; bloquea si detecta vulnerabilidades |
| Dependencias obsoletas | Reporte informativo con versiones disponibles |
| Distribución | Depende de formato/pruebas; construye e instala wheel limpio |
| OWASP ZAP | Depende de distribución/secretos/Bandit/auditoría; API local |
| SonarQube | Depende de cobertura/formato/secretos/Bandit/auditoría |
| Reporte SonarQube | Espera análisis, genera PDF/JSON/Markdown y verifica Quality Gate |
| Resumen final | Depende de todos; se ejecuta incluso si fallan y conserva el fallo |

## SonarQube y PDF de entrega

Servidor: <https://sonarqube.lynvera.ai>. Proyecto: `calculadora`.
Configura **Settings → Secrets and variables → Actions → SONAR_TOKEN** con un
**User Token** con permisos **Browse** y **Execute Analysis** sobre el proyecto.
Los tokens de análisis de proyecto no permiten consultar los resultados para
generar el PDF (HTTP 403). El proyecto debe existir antes de
analizarlo. Nunca guardes el token en el código.

La edición Community analiza `main`. En PRs/otras ramas se omiten explícitamente
los jobs de SonarQube y siguen ejecutándose los demás controles. La cobertura
XML se genera con toda la suite e incluye **calculadora.py, api.py y scripts de CI**.

Después de un run de `main`, abre **Actions → run → Artifacts** y descarga
**sonarqube-report-pdf-json-md**. El resumen al inicio del reporte distingue:

- Quality Gate, commit, identificador y fecha del análisis.
- Cobertura e issues abiertos de **todo el proyecto**.
- Cobertura e issues abiertos del **código nuevo**, según la línea base del servidor.

El PDF presenta un resumen ejecutivo con indicadores, una tabla comparativa
por alcance y una segunda sección con condiciones del Quality Gate, hallazgos
y trazabilidad. Incluye cabeceras, numeración y enlace al análisis; los hallazgos
extensos continúan en páginas adicionales.
`N/D` significa que no hay métricas/línea base de código nuevo, nunca un cero
inventado. Los security hotspots se informan por separado. El reporte se
publica incluso cuando falla el Quality Gate. Se verifica el análisis/commit
al inicio y final de la exportación para evitar mezclar ejecuciones.

**Entrega `calculadora.py` y el `sonarqube.pdf` descargado del pipeline.**
