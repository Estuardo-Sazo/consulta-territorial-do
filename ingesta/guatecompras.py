"""Guatecompras OCDS (Minfin): renglones con precio unitario y procesos municipales.

Cada zip mensual trae 16 CSV con el estándar OCDS "aplanado". Se usan 4:
    records.csv        un proceso (NOG) por fila: comprador, modalidad, estado
    com_ten_items.csv  renglones: descripción, código UNSPSC, cantidad, unidad
    com_awards.csv     adjudicaciones: monto total y fecha
    com_parties.csv    entidades: nivel (Municipalidad, Ministerio...) y departamento

Lo que NO trae: el precio unitario por renglón, ni a qué renglón corresponde
cada adjudicación. Por eso el precio unitario solo se calcula cuando no hay
ambigüedad: un proceso adjudicado con UN renglón y UNA adjudicación activa:
    precio_unitario = monto adjudicado / cantidad

Rigor: es un precio ADJUDICADO (lo que pagó el Estado en ese proceso), no un
precio de mercado. No se guardan nombres de proveedores: no hacen falta para el
análisis y así no se expone a empresas concretas.

Los CSV vienen en cp1252 (Windows), no en UTF-8, con algunos bytes inválidos;
se reemplazan en vez de abortar la lectura.
"""

import re
import zipfile
from pathlib import Path

import pandas as pd

from ingesta.comun import CRUDOS, normalizar

CARPETA = CRUDOS / "guatecompras"

COLUMNAS = {
    "records.csv": {
        "ocid": "ocid",
        "compiledRelease/tender/id": "nog",
        "compiledRelease/tender/title": "titulo",
        "compiledRelease/tender/statusDetails": "estado",
        "compiledRelease/tender/procurementMethodDetails": "modalidad",
        "compiledRelease/tender/mainProcurementCategory": "categoria",
        "compiledRelease/tender/datePublished": "fecha_publicacion",
        "compiledRelease/buyer/id": "comprador_id",
        "compiledRelease/buyer/name": "comprador",
    },
    "com_ten_items.csv": {
        "ocid": "ocid",
        "compiledRelease/tender/items/0/description": "descripcion",
        "compiledRelease/tender/items/0/classification/id": "unspsc",
        "compiledRelease/tender/items/0/quantity": "cantidad",
        "compiledRelease/tender/items/0/unit/name": "unidad",
    },
    "com_awards.csv": {
        "ocid": "ocid",
        "compiledRelease/awards/0/status": "estado_adj",
        "compiledRelease/awards/0/date": "fecha_adjudicacion",
        "compiledRelease/awards/0/value/amount": "monto",
        "compiledRelease/awards/0/value/currency": "moneda",
    },
    "com_parties.csv": {
        "ocid": "ocid",
        "compiledRelease/parties/0/id": "entidad_id",
        "compiledRelease/parties/0/roles": "roles",
        "compiledRelease/parties/0/details/level/description": "nivel_entidad",
        "compiledRelease/parties/0/address/region": "region",
        "compiledRelease/parties/0/address/locality": "localidad",
    },
}

# Categorías OCDS -> español, para mostrar.
CATEGORIAS = {"goods": "Bienes", "services": "Servicios", "works": "Obras"}


def leer_csv(zf: zipfile.ZipFile, nombre: str) -> pd.DataFrame:
    """Lee un CSV del zip con solo las columnas útiles, ya renombradas."""
    mapa = COLUMNAS[nombre]
    with zf.open(nombre) as f:
        df = pd.read_csv(f, dtype=str, encoding="cp1252", encoding_errors="replace",
                         usecols=lambda c: c in mapa, low_memory=False)
    # records.csv repite la columna "ocid"; usecols la toma una sola vez.
    return df.rename(columns=mapa)


def leer_mes(ruta: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (renglones con precio unitario, procesos) de un zip mensual."""
    with zipfile.ZipFile(ruta) as zf:
        rec = leer_csv(zf, "records.csv")
        items = leer_csv(zf, "com_ten_items.csv")
        adj = leer_csv(zf, "com_awards.csv")
        partes = leer_csv(zf, "com_parties.csv")

    rec["nog"] = rec.nog.str.replace("GT-NOG-", "", regex=False)
    rec["categoria"] = rec.categoria.map(CATEGORIAS)
    adj = adj[adj.estado_adj == "active"].copy()  # adjudicaciones vigentes
    adj["monto"] = pd.to_numeric(adj.monto, errors="coerce")

    # Datos del comprador: nivel de entidad y departamento de su dirección.
    # Ojo: records identifica al comprador por NIT (GT-NIT-...) y parties por su
    # código de entidad (GT-CISP-...); se unen por proceso (ocid), no por id.
    comp = (partes[partes.roles.str.contains("buyer", na=False)]
            .drop_duplicates("ocid")[["ocid", "entidad_id", "nivel_entidad", "region", "localidad"]])

    # --- Procesos: monto adjudicado total por NOG ---
    monto = adj.groupby("ocid").agg(monto_adjudicado=("monto", "sum"), adjudicaciones=("monto", "size"))
    procesos = (rec.merge(monto, on="ocid", how="left")
                   .merge(comp, on="ocid", how="left"))
    procesos["monto_adjudicado"] = procesos.monto_adjudicado.fillna(0)
    procesos["adjudicaciones"] = procesos.adjudicaciones.fillna(0).astype(int)

    # --- Renglones con precio unitario sin ambigüedad ---
    n_items = items.groupby("ocid").size()
    n_adj = adj.groupby("ocid").size()
    unicos = n_items[n_items == 1].index.intersection(n_adj[n_adj == 1].index)
    r = (rec[rec.ocid.isin(unicos) & (rec.estado == "Adjudicado")]
         .merge(items, on="ocid").merge(adj, on="ocid").merge(comp, on="ocid", how="left"))
    r["cantidad"] = pd.to_numeric(r.cantidad, errors="coerce")
    r = r[(r.cantidad > 0) & (r.monto > 0) & (r.moneda == "GTQ")].copy()
    r["precio_unitario"] = r.monto / r.cantidad
    # Si la "descripción" del renglón es el título del proceso, no es un producto
    # del catálogo sino la compra entera: su precio "unitario" no es comparable.
    r["descripcion_generica"] = r.descripcion.map(normalizar) == r.titulo.map(normalizar)
    renglones = r[["nog", "fecha_adjudicacion", "comprador_id", "comprador", "nivel_entidad", "region",
                   "modalidad", "categoria", "descripcion", "unspsc", "unidad", "cantidad", "monto",
                   "precio_unitario", "descripcion_generica"]]
    return renglones, procesos.drop(columns=["ocid"])


def leer_todos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee todos los zips de datos/crudos/guatecompras/ y los une."""
    rutas = sorted(CARPETA.glob("ocds_*.zip"))
    if not rutas:
        raise FileNotFoundError("Faltan los zips de Guatecompras: uv run python -m ingesta.descargar")
    partes_r, partes_p = [], []
    for ruta in rutas:
        renglones, procesos = leer_mes(ruta)
        mes = re.search(r"(\d{4})_(\d{2})", ruta.name).group(0).replace("_", "-")
        partes_r.append(renglones.assign(mes=mes))
        partes_p.append(procesos.assign(mes=mes))
        print(f"  {ruta.name}: {len(procesos):,} procesos, {len(renglones):,} renglones con precio unitario")
    renglones = pd.concat(partes_r, ignore_index=True)
    procesos = pd.concat(partes_p, ignore_index=True)
    # Un NOG puede reaparecer en otro mes si cambió; se queda la versión más reciente.
    procesos = procesos.sort_values("mes").drop_duplicates("nog", keep="last")
    renglones = renglones.sort_values("mes").drop_duplicates("nog", keep="last")
    for df, col in ((renglones, "fecha_adjudicacion"), (procesos, "fecha_publicacion")):
        # Fechas con zona horaria (-06:00) -> fecha local sin hora.
        df[col] = pd.to_datetime(df[col].str[:10], errors="coerce").dt.date
    return renglones, procesos
