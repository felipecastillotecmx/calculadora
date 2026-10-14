"""Adaptador HTTP de la calculadora para integración y análisis OWASP ZAP."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

from calculadora import Calculadora

app = FastAPI(title="Calculadora", docs_url=None, redoc_url=None)


class Calculo(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    operacion: str = Field(max_length=30, examples=["promedio"])
    numeros: list[StrictFloat | StrictInt] = Field(
        min_length=1, max_length=1000, examples=[[8, 9, 10]]
    )


@app.middleware("http")
async def seguridad(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers.update(
        {
            "Content-Security-Policy": (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Referrer-Policy": "no-referrer",
        }
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/calcular")
def calcular(datos: Calculo) -> dict[str, float | dict[str, float]]:
    try:
        return {"resultado": Calculadora(datos.operacion, datos.numeros).resultado()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
