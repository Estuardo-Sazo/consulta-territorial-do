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
from ingesta.comun import BASE, CRUDOS, PROCESADOS, RAIZ, normalizar
from ingesta.equivalencias import leer_equivalencias
from ingesta.precios_ref import leer_precios_ref
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

    print("4. Precios y compras públicas")
    precios_ref, calidad_ref = leer_precios_ref()
    # Los datos de Guatecompras vienen ya filtrados en Parquet (ingesta.compras).
    precios_gc = pd.read_parquet(PROCESADOS / "precios_guatecompras.parquet")
    precios_gc["texto"] = precios_gc.descripcion.map(normalizar)  # para buscar sin tildes
    compras = pd.read_parquet(PROCESADOS / "compras_municipales.parquet")
    equiv_muni = pd.read_parquet(PROCESADOS / "equivalencias_municipalidad.parquet")
    print(f"  {len(precios_ref):,} precios de referencia, {len(precios_gc):,} renglones de Guatecompras, "
          f"{len(compras):,} procesos municipales")

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
        "precios_referencia": precios_ref,
        "precios_guatecompras": precios_gc,
        "compras_municipales": compras,
        "equivalencias_municipalidad": equiv_muni,
    }
    chequeos = validaciones.CHEQUEOS_CENSO + validaciones.CHEQUEOS_PRECIOS
    metodos = equiv_muni.metodo.value_counts().to_dict()
    informativos = [
        f"Proyecciones: filas con EDAD vacía, deducida por posición ({reparadas})",
        f"Precios de referencia: {calidad_ref['act2_anterior_a_act1']} filas con la 2.ª actualización anterior "
        "a la 1.ª; se usa el precio de fecha más reciente",
        f"Precios de referencia: {calidad_ref['sin_precio']} filas sin precio (\"Sin Dato\"), excluidas",
        f"Precios de referencia: {calidad_ref['nog_2022_en_2023']} NOG del archivo 2022 están en el de 2023; "
        f"{calidad_ref['filas_solo_2022']} filas solo en 2022, agregadas",
        f"Municipalidades emparejadas: {metodos.get('exacto', 0)} por nombre exacto, "
        f"{metodos.get('prefijo o sufijo', 0)} por prefijo/sufijo, {metodos.get('aproximado', 0)} aproximadas",
    ]

    print("5. Escribiendo DuckDB y validando")
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
