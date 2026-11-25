"""Precios de referencia del INE (dataset precios-de-referencia, licencia ODC-BY).

El INE los armó "con la base de datos de Guatecompras": cada fila es un producto
de un evento (NOG) de contrato abierto o subasta electrónica inversa, con su
precio de referencia, la fecha y hasta dos actualizaciones.

Cómo se identifican los productos: por NOG + texto libre (Producto,
Características, Presentación). NO hay código de insumo ni UNSPSC, así que el
cruce con Guatecompras es por texto y unidad, nunca un emparejamiento exacto.

Archivos:
- precios_ref_2023.xlsx (al 02/10/2023): fuente principal, 4,995 filas, 2016-2023.
- precios_ref_2022.csv (hasta junio 2022): versión anterior; se usa solo para
  verificar que la nueva la contiene (55 de sus 56 NOG están en la de 2023) y
  para agregar las filas que la nueva ya no trae.

Problemas de calidad encontrados (se cuentan en las validaciones):
- 336 precios escritos como texto con separador de miles ("1,100.000") o "Sin Dato".
- En 38 filas la 2.ª actualización (07/02/2021) es ANTERIOR a la 1.ª (01/04/2021):
  el precio vigente es el de fecha más reciente, no el de la última columna.
"""

import pandas as pd

from ingesta.comun import CRUDOS, normalizar


def _numero(v) -> float | None:
    """'1,100.000' -> 1100.0; 'Sin Dato' -> None."""
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def _fecha(v) -> pd.Timestamp:
    # dayfirst: el INE escribe dd/mm/aaaa (hay fechas como 14/07/2020).
    return pd.to_datetime(v, dayfirst=True, errors="coerce")


def _estandarizar(df: pd.DataFrame, origen: str) -> pd.DataFrame:
    df = df.rename(columns=lambda c: normalizar(c).replace(" ", "_"))
    salida = pd.DataFrame({
        "nog": df.nog.astype(str).str.strip(),
        "evento": df.evento.str.strip(),
        "categoria": df.categoria.str.strip().str.upper(),
        "modalidad": df.modalidad.str.strip().str.upper(),
        "producto": df.producto.str.strip(),
        "caracteristicas": df.caracteristicas.str.strip(),
        "presentacion": df.presentacion.str.strip().str.upper(),
        "precio_original": df.precio_de_referencia_q.map(_numero),
        "fecha_original": _fecha(df.fecha_de_entrega),
        "precio_act1": df.precio_actualizado.map(_numero),
        "fecha_act1": _fecha(df.fecha_de_actualizacion_de_precio),
        "precio_act2": df.precio_actualizado_2.map(_numero),
        "fecha_act2": _fecha(df.fecha_de_actualizacion_de_precio_2),
        "origen": origen,
    })
    return salida


def _vigente(fila) -> tuple[float | None, pd.Timestamp]:
    """Precio con la fecha más reciente entre el original y sus actualizaciones."""
    opciones = [(fila[f"fecha_{k}"], fila[f"precio_{k}"]) for k in ("original", "act1", "act2")]
    opciones = [(f, p) for f, p in opciones if p is not None and pd.notna(p) and pd.notna(f)]
    if not opciones:
        return None, pd.NaT
    fecha, precio = max(opciones, key=lambda o: o[0])
    return precio, fecha


def leer_precios_ref() -> tuple[pd.DataFrame, dict]:
    """Devuelve (precios de referencia, métricas de calidad para las validaciones)."""
    nuevo = _estandarizar(pd.read_excel(CRUDOS / "precios_ref_2023.xlsx", dtype=str), "2023-10-02")
    viejo = _estandarizar(pd.read_csv(CRUDOS / "precios_ref_2022.csv", dtype=str, encoding="utf-8-sig"),
                          "2022-06")
    # Filas de 2022 cuyo NOG ya no aparece en 2023: se agregan.
    solo_viejo = viejo[~viejo.nog.isin(nuevo.nog)]
    df = pd.concat([nuevo, solo_viejo], ignore_index=True)

    df[["precio", "fecha_precio"]] = df.apply(lambda f: pd.Series(_vigente(f)), axis=1)
    df["texto"] = (df.producto + " " + df.caracteristicas.fillna("")).map(normalizar)
    calidad = {
        "sin_precio": int(df.precio.isna().sum()),
        "act2_anterior_a_act1": int((df.fecha_act2 < df.fecha_act1).sum()),
        "nog_2022_en_2023": f"{viejo.nog.isin(nuevo.nog).groupby(viejo.nog).first().sum()} de {viejo.nog.nunique()}",
        "filas_solo_2022": len(solo_viejo),
    }
    df = df[df.precio.notna()].reset_index(drop=True)
    df["fecha_precio"] = df.fecha_precio.dt.date
    return df.drop(columns=["fecha_original", "fecha_act1", "fecha_act2"]), calidad
