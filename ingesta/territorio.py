"""Dimensiones territoriales: departamentos, municipios y lugares poblados.

Los códigos del INE son jerárquicos: lugar poblado 1601045 -> municipio 1601
-> departamento 16. Departamentos y municipios salen del cuadro A1; los lugares
poblados y sus coordenadas, del listado oficial de centroides.
"""

import openpyxl
import pandas as pd

from ingesta.comun import CRUDOS
from ingesta.cuadros import leer_hoja


def leer_dimensiones() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve (departamentos, municipios, lugares_poblados)."""
    a1 = CRUDOS / "a01_poblacion.xlsx"
    dep = leer_hoja(a1, "A1_1").nombres
    dep = dep[dep.nivel == "departamento"]
    departamentos = pd.DataFrame({"cod_depto": dep.id0.astype(int), "nombre": dep.id1})

    mun = leer_hoja(a1, "A1_2").nombres
    municipios = pd.DataFrame(
        {"cod_mupio": mun.id2.astype(int), "cod_depto": mun.id0.astype(int), "nombre": mun.id3}
    )

    libro = openpyxl.load_workbook(CRUDOS / "centroides.xlsx", read_only=True)
    filas = list(libro.worksheets[0].iter_rows(values_only=True))
    libro.close()
    # Filas de datos: las que traen el código de lugar poblado (columna 5) numérico.
    datos = [f for f in filas if len(f) > 7 and isinstance(f[4], (int, float))]
    lugares = pd.DataFrame(
        {
            "cod_lp": [int(f[4]) for f in datos],
            "cod_mupio": [int(f[2]) for f in datos],
            "cod_depto": [int(f[0]) for f in datos],
            "nombre": [str(f[5]).strip() for f in datos],
            "longitud": [f[6] for f in datos],
            "latitud": [f[7] for f in datos],
        }
    )
    # "Otros lugares poblados" (código ...999) agrupa caseríos pequeños: no es un
    # lugar real, así que no se ubica en el mapa.
    lugares["es_agrupado"] = lugares.cod_lp % 1000 == 999
    return departamentos, municipios, lugares
