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


# "Extremo" = el 10 % del país en ese lado (34 de 340 municipios).
EXTREMO = 10


def destaca_y_retos(cod: int) -> dict[str, list[dict]]:
    """Indicadores en que el municipio está en el 10 % MEJOR (destaca) o PEOR (retos)
    del país, según el sentido de cada indicador. Los descriptivos no participan."""
    destaca, retos = [], []
    for ind in INDICADORES:
        if ind.sentido == 0:
            continue
        p = posicion(cod, ind.clave)
        if p is None or tabla()[cod][ind.clave]["pocos_casos"]:
            continue
        # Percentil "a favor": 100 = el mejor del país según el sentido.
        a_favor = p["percentil"] if ind.sentido > 0 else 100 - p["percentil"]
        item = {"clave": ind.clave, "nombre": ind.nombre, "unidad": ind.unidad,
                "valor": tabla()[cod][ind.clave]["valor"], "puesto": p["pais"], "de": p["de_pais"],
                "percentil_a_favor": a_favor}
        if a_favor >= 100 - EXTREMO:
            destaca.append(item)
        elif a_favor <= EXTREMO:
            retos.append(item)
    destaca.sort(key=lambda i: -i["percentil_a_favor"])
    retos.sort(key=lambda i: i["percentil_a_favor"])
    return {"destaca": destaca, "retos": retos, "criterio": f"{EXTREMO} % extremo del país"}
