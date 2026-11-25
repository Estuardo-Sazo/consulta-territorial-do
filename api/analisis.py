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


def _estandarizados() -> tuple[list[str], dict[int, list[float]]]:
    """Valores z (media 0, desviación 1) de los indicadores en porcentaje o puntos.

    Se estandariza para que un indicador con mucha variación (urbana: 0-100 %)
    no pese más que uno con poca (65 años o más: 2-12 %).
    """
    claves = [i.clave for i in INDICADORES if i.unidad != "personas"]
    t = tabla()
    completos = {c: v for c, v in t.items() if all(v[k]["valor"] is not None for k in claves)}
    z = {c: [] for c in completos}
    for k in claves:
        xs = [v[k]["valor"] for v in completos.values()]
        media = sum(xs) / len(xs)
        desv = (sum((x - media) ** 2 for x in xs) / len(xs)) ** 0.5 or 1
        for c, v in completos.items():
            z[c].append((v[k]["valor"] - media) / desv)
    return claves, z


def parecidos(cod: int, n: int = 5) -> list[dict]:
    """Los n municipios con perfil más parecido (distancia euclidiana entre valores z)."""
    claves, z = _estandarizados()
    if cod not in z:
        return []
    propio = z[cod]
    dist = sorted(
        (sum((a - b) ** 2 for a, b in zip(propio, otro)) ** 0.5, c) for c, otro in z.items() if c != cod
    )
    return [{"codigo": c, "distancia": round(d, 2), "mismo_departamento": c // 100 == cod // 100}
            for d, c in dist[:n]]


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Coeficiente de correlación de Pearson (-1 a 1)."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(sxy / (sx * sy), 3) if sx and sy else None


def fuerza(r: float | None) -> str:
    """Lectura en palabras del valor absoluto de r (convención usual)."""
    if r is None:
        return "sin dato"
    a = abs(r)
    nivel = "muy débil" if a < 0.2 else "débil" if a < 0.4 else "moderada" if a < 0.6 else "fuerte"
    return f"{nivel} {'positiva' if r > 0 else 'negativa'}"


def dispersion(x: str, y: str) -> dict:
    """Puntos (municipio, x, y) de dos indicadores, con r y su lectura."""
    vx, vy = valores(x), valores(y)
    comunes = sorted(set(vx) & set(vy))
    r = pearson([vx[c] for c in comunes], [vy[c] for c in comunes])
    return {
        "x": POR_CLAVE[x].nombre, "y": POR_CLAVE[y].nombre,
        "puntos": [{"codigo": c, "x": vx[c], "y": vy[c]} for c in comunes],
        "r": r, "lectura": fuerza(r), "n": len(comunes),
        "advertencia": "Correlación no es causalidad: que dos indicadores se muevan juntos no "
                       "significa que uno cause al otro; ambos pueden depender de un tercero "
                       "(por ejemplo, la urbanización).",
    }
