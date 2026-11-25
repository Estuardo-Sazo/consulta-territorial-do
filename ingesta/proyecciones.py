"""Estimaciones y proyecciones de población 2015-2030 en formato largo."""

import pandas as pd

from ingesta.comun import CRUDOS


def leer_proyecciones(equiv: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Devuelve (proyecciones, edades_reparadas), con códigos del CENSO.

    Formato original: DEPTO, MUPIO, SEXO, EDAD, 2015, ..., 2030.
    SEXO: 0 = ambos, 1 = hombres, 2 = mujeres. EDAD 70 = "70 años o más".
    """
    # dtype=str conserva el cero inicial ("0101").
    df = pd.read_excel(CRUDOS / "proyecciones.xlsx", dtype={"DEPTO": str, "MUPIO": str})
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    df = df.dropna(subset=["MUPIO"])

    # Problema de calidad conocido: filas con EDAD vacía. El archivo está ordenado
    # por municipio, sexo y edad (0..70), así que la faltante es la anterior + 1.
    faltantes = df.EDAD.isna()
    reparadas = int(faltantes.sum())
    if reparadas:
        anterior = df.groupby(["MUPIO", "SEXO"]).EDAD.shift(1)
        df.loc[faltantes, "EDAD"] = anterior[faltantes] + 1
    df["EDAD"] = df.EDAD.astype(int)

    anios = [c for c in df.columns if str(c).isdigit()]
    largo = df.melt(id_vars=["MUPIO", "SEXO", "EDAD"], value_vars=anios, var_name="anio", value_name="poblacion")
    # Aquí se aplica la tabla de equivalencias: todo queda con el código del censo.
    largo = largo.merge(equiv[["cod_mupio", "cod_proy"]], left_on="MUPIO", right_on="cod_proy")
    return (
        pd.DataFrame(
            {
                "cod_mupio": largo.cod_mupio.astype(int),
                "anio": largo.anio.astype(int),
                "sexo": largo.SEXO.map({0: "total", 1: "hombres", 2: "mujeres"}),
                "edad": largo.EDAD,
                "poblacion": largo.poblacion.astype(int),
            }
        ),
        reparadas,
    )
