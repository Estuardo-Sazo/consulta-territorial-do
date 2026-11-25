"""Equivalencias: municipalidad compradora en Guatecompras -> municipio del censo.

Guatecompras no trae el código INE del municipio. La municipalidad se
identifica por su NIT y por un nombre escrito a mano, con variantes:
    "MUNICIPALIDAD DE SANTA CATARINA PALOPÓ, SOLOLÁ"
    "MUNICIPALIDAD DE RAXRUHA ALTA VERAPAZ"          (sin coma)
    "MUNICIPALIDAD DE CAHABON, ALTA VERAPAZ"         (oficial: Santa María Cahabón)

Se cruza por pasadas, de la más estricta a la más laxa, siempre dentro del
departamento de la dirección de la entidad y aceptando solo resultados únicos:
    1. nombre exacto
    2. el nombre oficial termina o empieza con el de Guatecompras
    3. coincidencia aproximada (difflib, >= 0.8)
    4. alias revisados a mano
Lo que no cruza queda sin código y se informa en las validaciones.
"""

import difflib
import re

import pandas as pd

from ingesta.comun import normalizar

# Nombres de Guatecompras que ninguna regla resuelve. Revisados a mano.
ALIAS = {
    "san idelfonso ixtahuacan": "san ildefonso ixtahuacan",
    "ostuncalco": "san juan ostuncalco",
    "comalapa": "san juan comalapa",
    "quezada": "quesada",
}


def _nombre(comprador: str, depto_norm: str) -> str:
    """'MUNICIPALIDAD DE PASACO, JUTIAPA' -> 'pasaco'."""
    n = normalizar(re.sub(r"^\s*MUNICIPALIDAD\s+DE\s+", "", comprador, flags=re.I))
    return re.sub(rf"\s+{re.escape(depto_norm)}$", "", n).strip() if depto_norm else n


def cruzar(procesos: pd.DataFrame, municipios: pd.DataFrame, departamentos: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por municipalidad: comprador_id, comprador, cod_mupio, metodo."""
    deptos = {normalizar(n): c for c, n in zip(departamentos.cod_depto, departamentos.nombre)}
    muni = (procesos[procesos.nivel_entidad == "Municipalidad"]
            .sort_values("mes").drop_duplicates("comprador_id", keep="last"))
    oficiales: dict[int, dict[str, int]] = {}
    for cod, dep, nom in zip(municipios.cod_mupio, municipios.cod_depto, municipios.nombre):
        oficiales.setdefault(dep, {})[normalizar(nom)] = cod

    filas = []
    for _, m in muni.iterrows():
        region = normalizar(m.region or "")
        cod_depto = deptos.get(region)
        nombre = _nombre(m.comprador, region)
        nombre = ALIAS.get(nombre, nombre)
        candidatos = oficiales.get(cod_depto, {})
        cod, metodo = None, None
        pasadas = [
            ("exacto", lambda: [n for n in candidatos if n == nombre]),
            ("prefijo o sufijo", lambda: [n for n in candidatos
                                         if n.endswith(" " + nombre) or n.startswith(nombre + " ")]),
            ("aproximado", lambda: difflib.get_close_matches(nombre, list(candidatos), n=1, cutoff=0.8)),
        ]
        for etiqueta, buscar in pasadas:
            hallados = buscar()
            if len(hallados) == 1:
                cod, metodo = candidatos[hallados[0]], etiqueta
                break
        filas.append({"comprador_id": m.comprador_id, "comprador": m.comprador,
                      "cod_depto": cod_depto, "cod_mupio": cod, "metodo": metodo})
    return pd.DataFrame(filas).astype({"cod_mupio": "Int64", "cod_depto": "Int64"})
