"""Análisis entre municipios: ranking, fortalezas y retos, parecidos, dispersión.

Todo se calcula sobre calculo.tabla("municipio"): los 340 municipios con los
indicadores del catálogo, de modo que los números coinciden con los de la ficha.
"""

from api.calculo import tabla
from api.indicadores import INDICADORES, POR_CLAVE


def valores(clave: str) -> dict[int, float]:
    """{cod_mupio: valor} de un indicador, sin los municipios sin dato."""
    return {c: v[clave]["valor"] for c, v in tabla().items() if v[clave]["valor"] is not None}


def posicion(cod: int, clave: str) -> dict | None:
    """Lugar del municipio en el país y en su departamento (1 = valor más alto).

    `percentil` es la proporción de municipios con valor MENOR o igual (0-100).
    """
    vals = valores(clave)
    if cod not in vals:
        return None
    propio = vals[cod]
    depto = {c: v for c, v in vals.items() if c // 100 == cod // 100}
    return {
        "pais": 1 + sum(v > propio for v in vals.values()),
        "de_pais": len(vals),
        "departamento": 1 + sum(v > propio for v in depto.values()),
        "de_departamento": len(depto),
        "percentil": round(100 * sum(v <= propio for v in vals.values()) / len(vals)),
    }


def ranking(clave: str, cod_depto: int | None = None) -> list[dict]:
    """Municipios ordenados por un indicador (opcionalmente de un departamento)."""
    vals = valores(clave)
    if cod_depto is not None:
        vals = {c: v for c, v in vals.items() if c // 100 == cod_depto}
    orden = sorted(vals.items(), key=lambda cv: cv[1], reverse=True)
    return [{"codigo": c, "valor": v, "puesto": i + 1} for i, (c, v) in enumerate(orden)]
