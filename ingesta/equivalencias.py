"""Tabla de equivalencias de códigos municipales: censo <-> proyecciones.

El censo numera los municipios del departamento de Guatemala 0101-0117, pero las
proyecciones usan 0101 y 0123-0138 (los códigos cambiaron entre publicaciones).
En vez de suponer una regla fija ("sumar 21"), se cruzan por NOMBRE dentro del
mismo departamento usando el diccionario oficial de las proyecciones, y se exige
que cuadren los 340. Si un día no cuadran, la ingesta falla en vez de inventar.
"""

import re

import openpyxl
import pandas as pd

from ingesta.comun import CRUDOS, normalizar


def leer_equivalencias(municipios: pd.DataFrame) -> pd.DataFrame:
    """Devuelve cod_mupio (censo), cod_proy (proyecciones) y ambos nombres."""
    libro = openpyxl.load_workbook(CRUDOS / "proyecciones_diccionario.xlsx", read_only=True)
    pares = []
    for fila in libro.worksheets[0].iter_rows(values_only=True):
        valores = [v for v in fila if v is not None]
        if valores and valores[0] == "MUPIO":
            valores = valores[1:]  # la primera fila de la lista trae la etiqueta
        # Fila de la lista de municipios: un código de 4 dígitos y el nombre.
        if len(valores) >= 2 and re.fullmatch(r"\d{4}", str(valores[0])):
            pares.append({"cod_proy": str(valores[0]), "nombre_proy": str(valores[1])})
    libro.close()

    proy = pd.DataFrame(pares)
    proy["cod_depto"] = proy.cod_proy.str[:2].astype(int)
    proy["clave"] = proy.nombre_proy.map(normalizar)
    cen = municipios.assign(clave=municipios.nombre.map(normalizar))
    equiv = cen.merge(proy, on=["cod_depto", "clave"], how="inner")
    if len(equiv) != len(municipios):
        faltan = sorted(set(cen.nombre) - set(equiv.nombre))
        raise ValueError(f"No se pudieron emparejar {len(faltan)} municipios: {faltan[:10]}")
    equiv["codigo_cambia"] = equiv.cod_mupio != equiv.cod_proy.astype(int)
    return equiv[["cod_mupio", "cod_proy", "nombre", "nombre_proy", "codigo_cambia"]]
