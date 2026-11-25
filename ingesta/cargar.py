"""Construye datos/fichas.duckdb a partir de datos/crudos/.

Uso:
    uv run python -m ingesta.cargar

La base se escribe en un archivo temporal y al final se renombra: la API nunca
ve una base a medio construir, y si una validación falla la base vieja queda.
"""

import csv
import sys
import time

import duckdb
import pandas as pd

from ingesta import validaciones
from ingesta.censo import leer_cuadros
from ingesta.comun import BASE, CRUDOS, RAIZ
from ingesta.equivalencias import leer_equivalencias
from ingesta.proyecciones import leer_proyecciones
from ingesta.territorio import leer_dimensiones


def escribir(con: duckdb.DuckDBPyConnection, tablas: dict[str, pd.DataFrame]) -> None:
    """Copia cada DataFrame a una tabla de DuckDB."""
    for nombre, df in tablas.items():
        con.register("df_temporal", df)
        con.execute(f"CREATE TABLE {nombre} AS SELECT * FROM df_temporal")
        con.unregister("df_temporal")


def main() -> int:
    t0 = time.perf_counter()
    print("1. Territorio")
    departamentos, municipios, lugares = leer_dimensiones()
    print(f"  {len(departamentos)} departamentos, {len(municipios)} municipios, {len(lugares)} lugares poblados")

    print("2. Cuadros del censo")
    cuadros, valores = leer_cuadros()

    print("3. Proyecciones")
    equiv = leer_equivalencias(municipios)
    proyecciones, reparadas = leer_proyecciones(equiv)

    with (CRUDOS / "FUENTES.csv").open(encoding="utf-8") as f:
        fuentes = pd.DataFrame(list(csv.DictReader(f)))

    tablas = {
        "departamentos": departamentos,
        "municipios": municipios,
        "lugares_poblados": lugares,
        "cuadros": cuadros,
        "valores": valores,
        "equivalencias_municipio": equiv,
        "proyecciones": proyecciones,
        "fuentes": fuentes,
    }
    chequeos = list(validaciones.CHEQUEOS_CENSO)
    informativos = [f"Proyecciones: filas con EDAD vacía, deducida por posición ({reparadas})"]

    print("4. Escribiendo DuckDB y validando")
    temporal = BASE.with_suffix(".duckdb.tmp")
    temporal.unlink(missing_ok=True)
    con = duckdb.connect(str(temporal))
    escribir(con, tablas)
    con.execute("CREATE INDEX idx_valores ON valores (nivel, codigo, cuadro)")
    resultado = validaciones.ejecutar(con, chequeos, informativos)
    escribir(con, {"validaciones": resultado})
    con.close()

    for _, v in resultado.iterrows():
        print(f"  [{'OK ' if v.aprobado else 'ERR'}] {v.chequeo}" + ("" if v.aprobado else f" -> {v.problemas}"))
    if not resultado.aprobado.all():
        print("Hay validaciones fallidas: NO se reemplaza la base.", file=sys.stderr)
        return 1
    temporal.replace(BASE)
    print(f"Listo: {BASE.relative_to(RAIZ)} ({BASE.stat().st_size / 1e6:.0f} MB) en {time.perf_counter() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
