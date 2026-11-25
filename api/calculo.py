"""Patrón bases() -> calcular(): una sola fórmula para todos los niveles.

1. bases(nivel) trae los CONTEOS publicados por el INE (no porcentajes) de cada
   territorio del nivel: numeradores, universos y población proyectada.
2. calcular(b) aplica las fórmulas del catálogo a esos conteos.

Como las bases son conteos, el país, un departamento, un municipio o un lugar
poblado pasan por exactamente la misma función: no hay una fórmula "nacional"
distinta que pueda contradecir a la municipal.
"""

from functools import lru_cache

from api.db import consultar
from api.indicadores import ANIO_ACTUAL, INDICADORES, UMBRAL_POCOS_CASOS

# Agrupación de las proyecciones (que son municipales) para cada nivel.
_AGRUPAR_PROY = {"pais": "0", "departamento": "cod_mupio // 100", "municipio": "cod_mupio"}


def _bases_sql(nivel: str, codigos: list[int] | None) -> dict[int, dict]:
    filtro, parametros = "", [nivel]
    if codigos is not None:
        filtro = f" AND codigo IN ({', '.join('?' * len(codigos))})"
        parametros += codigos
    filas = consultar(
        f"""SELECT codigo, cuadro, grupo, coalesce(categoria, '') AS categoria, orden, valor
            FROM valores WHERE nivel = ?{filtro}""",
        parametros,
    )
    bases: dict[int, dict] = {}
    for f in filas:
        b = bases.setdefault(f["codigo"], {})
        b[f"{f['cuadro']}|{f['grupo']}|{f['categoria']}"] = f["valor"]
        if f["orden"] == 0:
            b[f"{f['cuadro']}|u"] = f["valor"]

    if nivel in _AGRUPAR_PROY:
        grupo = _AGRUPAR_PROY[nivel]
        proy = consultar(
            f"""SELECT {grupo} AS codigo, anio, SUM(poblacion) AS p FROM proyecciones
                WHERE sexo = 'total' AND anio IN (2015, ?, 2030) GROUP BY ALL""",
            [ANIO_ACTUAL],
        )
        for f in proy:
            if f["codigo"] in bases:
                bases[f["codigo"]][f"proy|{f['anio']}"] = f["p"]
    return bases


@lru_cache(maxsize=8)
def bases(nivel: str) -> dict[int, dict]:
    """Bases de TODOS los territorios de un nivel. Se guardan en memoria porque la
    base es de solo lectura (340 municipios ≈ 30 mil valores)."""
    return _bases_sql(nivel, None)


def bases_de(nivel: str, codigo: int) -> dict:
    """Bases de un territorio. Para lugares poblados (≈ 20 mil) se consulta solo
    el pedido en vez de cargarlos todos."""
    if nivel == "lugar_poblado":
        return _bases_sql(nivel, [codigo]).get(codigo, {})
    return bases(nivel).get(codigo, {})


def calcular(b: dict, nivel: str | None = None) -> dict[str, dict]:
    """Aplica el catálogo a unas bases. Devuelve {clave: {valor, universo, pocos_casos}}."""
    salida = {}
    for ind in INDICADORES:
        r = ind.formula(b) if b and (nivel is None or nivel in ind.niveles) else None
        if r is None:
            salida[ind.clave] = {"valor": None, "universo": None, "pocos_casos": False}
            continue
        valor, universo = r
        salida[ind.clave] = {
            "valor": round(valor, 1) if ind.unidad != "personas" else int(valor),
            "universo": int(universo) if universo else None,
            "pocos_casos": bool(universo is not None and universo < UMBRAL_POCOS_CASOS),
        }
    return salida


@lru_cache(maxsize=4)
def tabla(nivel: str = "municipio") -> dict[int, dict[str, dict]]:
    """Indicadores de todos los territorios de un nivel (para mapa, ranking, parecidos)."""
    return {cod: calcular(b, nivel) for cod, b in bases(nivel).items() if cod != 0}
