"""Reduce los zips de Guatecompras a dos Parquet pequeños y versionados.

Uso:
    uv run python -m ingesta.compras      (después de ingesta.descargar)

Salidas en datos/procesados/:
    precios_guatecompras.parquet  renglones de BIENES con precio unitario
    compras_municipales.parquet   procesos de las 340 municipalidades

Así cargar.py y Docker no necesitan los 356 MB de zips: basta este paso una
vez por cada mes nuevo que se descargue.
"""

import sys

from ingesta.comun import PROCESADOS, RAIZ, normalizar
from ingesta.guatecompras import leer_todos
from ingesta.municipalidades import cruzar
from ingesta.territorio import leer_dimensiones


def main() -> int:
    departamentos, municipios, _ = leer_dimensiones()
    renglones, procesos = leer_todos()
    deptos = {normalizar(n): c for c, n in zip(departamentos.cod_depto, departamentos.nombre)}

    # Precios: solo bienes (en servicios y obras la "cantidad" casi nunca es una
    # unidad física comparable) y sin renglones genéricos.
    precios = renglones[(renglones.categoria == "Bienes") & ~renglones.descripcion_generica].copy()
    precios["cod_depto"] = precios.region.map(lambda r: deptos.get(normalizar(r or ""))).astype("Int64")
    precios = precios.drop(columns=["descripcion_generica", "region", "categoria"])

    equiv = cruzar(procesos, municipios, departamentos)
    muni = procesos.merge(equiv[["comprador_id", "cod_mupio", "metodo"]], on="comprador_id")
    muni = muni[["nog", "mes", "fecha_publicacion", "cod_mupio", "comprador", "titulo", "estado",
                 "modalidad", "categoria", "monto_adjudicado", "adjudicaciones"]]

    PROCESADOS.mkdir(parents=True, exist_ok=True)
    salidas = {
        "precios_guatecompras.parquet": precios,
        "compras_municipales.parquet": muni,
        "equivalencias_municipalidad.parquet": equiv,
    }
    for nombre, df in salidas.items():
        ruta = PROCESADOS / nombre
        df.to_parquet(ruta, index=False, compression="zstd")
        print(f"  {ruta.relative_to(RAIZ)}: {len(df):,} filas, {ruta.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
