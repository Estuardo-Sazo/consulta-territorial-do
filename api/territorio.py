"""Búsqueda de territorios y datos de identificación (nombre y jerarquía)."""

import re
import unicodedata

from fastapi import HTTPException

from api.db import consultar

# Nombres populares que no coinciden con el nombre oficial.
ALIAS = {
    "xela": "quetzaltenango",
    "xelaju": "quetzaltenango",
    "guate": "guatemala",
    "la capital": "guatemala",
    "antigua": "antigua guatemala",
    "la antigua": "antigua guatemala",
    "cahabon": "santa maria cahabon",
    "barillas": "santa cruz barillas",
    "nebaj": "santa maria nebaj",
}


def sin_tildes(texto: str) -> str:
    """'Cobán' -> 'coban'. Equivale a strip_accents(lower()) de DuckDB."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower().strip()


def expandir(q: str) -> str:
    """Aplica alias y atajos: 'zona 1' -> 'zona municipal 1' (nombre oficial)."""
    t = re.sub(r"\s+", " ", sin_tildes(q))
    t = ALIAS.get(t, t)
    return re.sub(r"^zona (\d+)$", r"zona municipal \1", t)


def buscar(q: str, limite: int = 20) -> list[dict]:
    """Departamentos, municipios y lugares poblados por nombre o código."""
    termino = expandir(q)
    return consultar(
        """
        WITH t AS (
            SELECT 'departamento' AS nivel, cod_depto AS codigo, nombre, 'Departamento' AS contexto
            FROM departamentos
            UNION ALL
            SELECT 'municipio', m.cod_mupio, m.nombre, 'Municipio de ' || d.nombre
            FROM municipios m JOIN departamentos d USING (cod_depto)
            UNION ALL
            SELECT 'lugar_poblado', l.cod_lp, l.nombre, m.nombre || ', ' || d.nombre
            FROM lugares_poblados l JOIN municipios m USING (cod_mupio)
            JOIN departamentos d ON d.cod_depto = l.cod_depto
            WHERE NOT l.es_agrupado
        )
        SELECT t.*, CAST(v.valor AS INTEGER) AS poblacion
        FROM t LEFT JOIN valores v ON v.cuadro = 'A1' AND v.orden = 0 AND v.nivel = t.nivel AND v.codigo = t.codigo
        WHERE CASE WHEN regexp_full_match(?, '\\d+') THEN CAST(t.codigo AS VARCHAR) = ?
                   ELSE strip_accents(lower(t.nombre)) LIKE '%' || ? || '%' END
        ORDER BY strip_accents(lower(t.nombre)) = ? DESC,       -- coincidencia exacta primero
                 CASE t.nivel WHEN 'departamento' THEN 0 WHEN 'municipio' THEN 1 ELSE 2 END,
                 poblacion DESC NULLS LAST
        LIMIT ?
        """,
        [termino, termino, termino, termino, limite],
    )


def ancestros(nivel: str, codigo: int) -> list[tuple[str, int]]:
    """Niveles superiores, del más cercano al país (los códigos son jerárquicos)."""
    if nivel == "lugar_poblado":
        return [("municipio", codigo // 1000), ("departamento", codigo // 100_000), ("pais", 0)]
    if nivel == "municipio":
        return [("departamento", codigo // 100), ("pais", 0)]
    if nivel == "departamento":
        return [("pais", 0)]
    return []


def lugar(nivel: str, codigo: int) -> dict:
    """Nombre y contexto de un territorio. Lanza 404 si no existe."""
    if nivel == "pais":
        return {"nivel": "pais", "codigo": 0, "nombre": "Guatemala", "contexto": "República"}
    if nivel == "departamento":
        filas = consultar("SELECT nombre, 'Departamento' AS contexto FROM departamentos WHERE cod_depto = ?",
                          [codigo])
    elif nivel == "municipio":
        filas = consultar(
            """SELECT m.nombre, 'Municipio de ' || d.nombre AS contexto, d.cod_depto
               FROM municipios m JOIN departamentos d USING (cod_depto) WHERE cod_mupio = ?""", [codigo])
    else:
        filas = consultar(
            """SELECT l.nombre, m.nombre || ', ' || d.nombre AS contexto, l.cod_mupio, l.cod_depto,
                      l.longitud, l.latitud, l.es_agrupado
               FROM lugares_poblados l JOIN municipios m USING (cod_mupio)
               JOIN departamentos d ON d.cod_depto = l.cod_depto WHERE l.cod_lp = ?""", [codigo])
    if not filas:
        raise HTTPException(404, f"No existe {nivel} con código {codigo}")
    return {"nivel": nivel, "codigo": codigo, **filas[0]}
