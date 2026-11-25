"""Carga los 7 cuadros del Censo 2018 en sus 3 niveles (formato largo)."""

import re
import time

import pandas as pd

from ingesta.comun import CRUDOS
from ingesta.cuadros import leer_hoja

# Para agregar otro cuadro basta con descargarlo (ingesta/descargar.py) y
# añadir una línea aquí. `unidad` dice qué cuenta el cuadro.
CUADROS = [
    {"clave": "A1", "archivo": "a01_poblacion", "tema": "Población", "unidad": "personas"},
    {"clave": "A5", "archivo": "a05_pueblos", "tema": "Población", "unidad": "personas"},
    {"clave": "A11", "archivo": "a11_alfabetismo", "tema": "Educación", "unidad": "personas"},
    {"clave": "A12", "archivo": "a12_tic", "tema": "Tecnología", "unidad": "personas"},
    {"clave": "B2", "archivo": "b02_agua", "tema": "Servicios del hogar", "unidad": "hogares"},
    {"clave": "B3", "archivo": "b03_sanitario", "tema": "Servicios del hogar", "unidad": "hogares"},
    {"clave": "B4", "archivo": "b04_alumbrado", "tema": "Servicios del hogar", "unidad": "hogares"},
]


def leer_cuadros() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (cuadros, valores): metadatos de cada cuadro y todos sus valores."""
    metadatos, partes = [], []
    for c in CUADROS:
        ruta = CRUDOS / f"{c['archivo']}.xlsx"
        t0 = time.perf_counter()
        for sufijo in ("_1", "_2", "_3"):  # departamento, municipio, lugar poblado
            hoja = leer_hoja(ruta, f"{c['clave']}{sufijo}")
            df = hoja.valores.assign(cuadro=c["clave"])
            partes.append(df)
        # El título y las notas se toman de la hoja de lugar poblado (la más detallada).
        titulo = re.sub(r"^Cuadro [A-C]\d+\.\d+ - ", "", hoja.titulo)
        titulo = re.sub(r",? según lugar poblado$", "", titulo)
        metadatos.append(
            {
                "cuadro": c["clave"],
                "titulo": titulo,
                "tema": c["tema"],
                "unidad": c["unidad"],
                # El universo es la primera columna de valores (orden 0).
                "universo": df.loc[df.orden == 0, "grupo"].iloc[0],
                "notas": " ".join(hoja.notas) or None,
                "archivo": f"{c['archivo']}.xlsx",
            }
        )
        print(f"  {c['clave']:<4} {titulo[:70]:<70} {time.perf_counter() - t0:5.1f} s")
    return pd.DataFrame(metadatos), pd.concat(partes, ignore_index=True)
