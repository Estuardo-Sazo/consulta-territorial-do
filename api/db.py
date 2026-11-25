"""Acceso a la base DuckDB en modo solo lectura.

La API nunca modifica datos: todo se construye en la ingesta. FastAPI corre las
rutas `def` en varios hilos y una conexión de DuckDB no se comparte entre hilos,
así que cada consulta usa su propio cursor (una conexión ligera a la misma base).
"""

import os
import threading
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
# Docker cambia la ruta con la variable de entorno FICHAS_DB.
RUTA_BASE = Path(os.environ.get("FICHAS_DB", RAIZ / "datos" / "fichas.duckdb"))
RUTA_GEOJSON = Path(os.environ.get("FICHAS_GEOJSON", RAIZ / "datos" / "procesados" / "municipios.geojson"))

_conexion: duckdb.DuckDBPyConnection | None = None
_candado = threading.Lock()


def conexion() -> duckdb.DuckDBPyConnection:
    """Abre la base la primera vez que se necesita y reutiliza la conexión."""
    global _conexion
    with _candado:
        if _conexion is None:
            if not RUTA_BASE.exists():
                raise FileNotFoundError(f"No existe {RUTA_BASE}. Ejecuta: uv run python -m ingesta.cargar")
            _conexion = duckdb.connect(str(RUTA_BASE), read_only=True)
        return _conexion


def consultar(sql: str, parametros: list | None = None) -> list[dict]:
    """Ejecuta SQL y devuelve [{columna: valor}].

    Los valores del usuario van SIEMPRE como parámetros `?`, nunca pegados en el
    texto SQL: así no hay inyección de SQL.
    """
    cursor = conexion().cursor()
    try:
        resultado = cursor.execute(sql, parametros or [])
        columnas = [d[0] for d in resultado.description]
        return [dict(zip(columnas, fila)) for fila in resultado.fetchall()]
    finally:
        cursor.close()
