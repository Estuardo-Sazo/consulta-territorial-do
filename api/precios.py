"""Estadísticas de precios unitarios adjudicados (Guatecompras) y referencias del INE.

Se reportan promedio, mediana y moda, como lo hace la Dirección de Precios e
Índices de Referencia (DPIR) del INE, más cuartiles y valores atípicos:

- Mediana: el valor del medio; no la mueven los extremos. Es la cifra principal.
- Promedio: sensible a extremos (un renglón mal capturado lo dispara), por eso
  también se da sin atípicos.
- Moda: el precio que más se repite, redondeado al quetzal (con centavos casi
  nunca hay dos iguales). Si ninguno se repite, no hay moda.
- Atípico: fuera de [Q1 - 1.5·RIC, Q3 + 1.5·RIC] (regla de Tukey).

Rigor: son precios ADJUDICADOS en procesos concretos, no precios de mercado.
Solo se comparan precios de la MISMA unidad de medida.
"""

import re
import statistics
from collections import Counter

from api.db import consultar
from api.territorio import sin_tildes

UMBRAL_POCOS_CASOS = 30


def cuartil(xs: list[float], q: float) -> float:
    """Cuartil por interpolación lineal sobre la lista ordenada."""
    pos = (len(xs) - 1) * q
    i = int(pos)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (pos - i)


def estadisticas(precios: list[float]) -> dict | None:
    """Resumen de una lista de precios unitarios."""
    if not precios:
        return None
    xs = sorted(precios)
    q1, q3 = cuartil(xs, 0.25), cuartil(xs, 0.75)
    ric = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * ric, q3 + 1.5 * ric
    normales = [x for x in xs if lim_inf <= x <= lim_sup]
    redondeados = Counter(round(x) for x in xs)
    valor_moda, veces = redondeados.most_common(1)[0]
    return {
        "n": len(xs),
        "promedio": round(statistics.fmean(xs), 2),
        "mediana": round(statistics.median(xs), 2),
        "moda": valor_moda if veces > 1 else None,
        "moda_veces": veces if veces > 1 else 0,
        "minimo": round(xs[0], 2),
        "maximo": round(xs[-1], 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "atipicos": len(xs) - len(normales),
        "promedio_sin_atipicos": round(statistics.fmean(normales), 2) if normales else None,
        "limite_atipico_superior": round(lim_sup, 2),
        "pocos_casos": len(xs) < UMBRAL_POCOS_CASOS,
    }


def terminos(q: str) -> list[str]:
    """'Papel Bond carta' -> ['papel', 'bond', 'carta'] (sin tildes, palabras de 2+ letras)."""
    return [t for t in re.split(r"[^a-z0-9]+", sin_tildes(q)) if len(t) >= 2]


def condicion_texto(columna: str, palabras: list[str]) -> tuple[str, list]:
    """Todas las palabras deben aparecer (AND). Devuelve (sql, parámetros)."""
    sql = " AND ".join(f"{columna} LIKE '%' || ? || '%'" for _ in palabras) or "FALSE"
    return sql, palabras


def referencias_ine(palabras: list[str], limite: int = 25) -> list[dict]:
    """Precios de referencia del INE cuyo producto o características contienen las palabras."""
    cond, p = condicion_texto("texto", palabras)
    return consultar(
        f"""SELECT nog, evento, producto, caracteristicas, presentacion, precio, fecha_precio, origen
            FROM precios_referencia WHERE {cond}
            ORDER BY fecha_precio DESC LIMIT ?""", p + [limite])
