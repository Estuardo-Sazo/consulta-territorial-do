"""Aplicación FastAPI. Documentación interactiva en /api/docs.

Todas las rutas cuelgan de /api: en producción nginx sirve la web en "/" y
reenvía "/api/..." a este servidor desde el mismo dominio.
"""

import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.rutas import analisis, precios, territorio

app = FastAPI(
    title="Fichas Territoriales · INE Guatemala",
    description="Censo 2018, proyecciones 2015-2030, precios de referencia del INE y compras públicas "
                "(Guatecompras OCDS) por departamento, municipio y lugar poblado. "
                "Fuente de los datos: Instituto Nacional de Estadística (INE), Guatemala.",
    version="0.1.0",
    # Bajo /api para que también se vea a través de nginx (que solo reenvía /api/).
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# CORS: en desarrollo la web corre en otro puerto (Vite, 5180). En Docker no hace
# falta (nginx sirve todo desde el mismo origen), pero no estorba.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGENES", "http://localhost:5180").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")
api.include_router(territorio.router)
api.include_router(analisis.router)
api.include_router(precios.router)
app.include_router(api)
