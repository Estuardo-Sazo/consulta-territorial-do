"""Rutas de territorio: búsqueda, listas, ficha, cuadros, proyecciones y calidad."""

from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from api import analisis, texto
from api.calculo import bases_de, calcular
from api.db import consultar
from api.indicadores import FUENTE_CENSO, FUENTE_PROY, INDICADORES, UMBRAL_POCOS_CASOS
from api.territorio import ancestros, buscar, lugar

router = APIRouter(tags=["territorio"])

# FastAPI responde 422 si llega otro texto.
Nivel = Literal["pais", "departamento", "municipio", "lugar_poblado"]


@lru_cache
def nombres_municipios() -> dict[int, dict]:
    filas = consultar("""SELECT m.cod_mupio, m.nombre, d.nombre AS departamento
                         FROM municipios m JOIN departamentos d USING (cod_depto)""")
    return {f["cod_mupio"]: {"nombre": f["nombre"], "departamento": f["departamento"]} for f in filas}


@router.get("/salud")
def salud():
    """La API responde y la base está disponible (lo usa el healthcheck de Docker)."""
    consultar("SELECT 1")
    return {"estado": "ok"}


@router.get("/buscar")
def ruta_buscar(q: str = Query(min_length=2, description="Nombre o código"), limite: int = Query(20, le=100)):
    """Busca departamentos, municipios y lugares poblados (sin importar tildes; acepta 'xela')."""
    return buscar(q, limite)


@router.get("/departamentos")
def departamentos():
    """Los 22 departamentos con su población censada."""
    return consultar(
        """SELECT d.cod_depto AS codigo, d.nombre, CAST(v.valor AS INTEGER) AS poblacion
           FROM departamentos d JOIN valores v ON v.cuadro = 'A1' AND v.orden = 0
                AND v.nivel = 'departamento' AND v.codigo = d.cod_depto ORDER BY d.cod_depto""")


@router.get("/departamentos/{codigo}/municipios")
def municipios_de(codigo: int):
    """Municipios de un departamento con población y número de lugares poblados."""
    lugar("departamento", codigo)
    return consultar(
        """SELECT m.cod_mupio AS codigo, m.nombre, CAST(v.valor AS INTEGER) AS poblacion,
                  (SELECT COUNT(*) FROM lugares_poblados l
                   WHERE l.cod_mupio = m.cod_mupio AND NOT l.es_agrupado) AS lugares_poblados
           FROM municipios m JOIN valores v ON v.cuadro = 'A1' AND v.orden = 0
                AND v.nivel = 'municipio' AND v.codigo = m.cod_mupio
           WHERE m.cod_depto = ? ORDER BY m.cod_mupio""", [codigo])


@router.get("/municipios/{codigo}/lugares")
def lugares_de(codigo: int):
    """Lugares poblados de un municipio con población, hogares, área y coordenadas."""
    lugar("municipio", codigo)
    return consultar(
        """SELECT l.cod_lp AS codigo, l.nombre, l.longitud, l.latitud, l.es_agrupado,
                  CAST(SUM(v.valor) FILTER (WHERE v.cuadro = 'A1' AND v.orden = 0) AS INTEGER) AS poblacion,
                  CAST(SUM(v.valor) FILTER (WHERE v.cuadro = 'B2' AND v.orden = 0) AS INTEGER) AS hogares,
                  -- Área predominante: urbana si su población urbana supera a la rural.
                  CASE WHEN SUM(v.valor) FILTER (WHERE v.cuadro = 'A1' AND v.categoria = 'Urbana')
                          > SUM(v.valor) FILTER (WHERE v.cuadro = 'A1' AND v.categoria = 'Rural')
                       THEN 'urbana' ELSE 'rural' END AS area
           FROM lugares_poblados l
           LEFT JOIN valores v ON v.nivel = 'lugar_poblado' AND v.codigo = l.cod_lp AND v.cuadro IN ('A1', 'B2')
           WHERE l.cod_mupio = ? GROUP BY ALL ORDER BY poblacion DESC NULLS LAST""", [codigo])


@router.get("/ficha/{nivel}/{codigo}")
def ficha(nivel: Nivel, codigo: int):
    """Ficha completa: indicadores con comparación (municipio, departamento, país),
    posición, dónde destaca, retos, parecidos y el texto "Lo que dicen los datos"."""
    info = lugar(nivel, codigo)
    propio = calcular(bases_de(nivel, codigo), nivel)
    superiores = ancestros(nivel, codigo)
    comparacion = {n: calcular(bases_de(n, c), n) for n, c in superiores}
    pais = comparacion.get("pais") or propio
    es_muni = nivel == "municipio"

    indicadores = []
    for ind in INDICADORES:
        if nivel not in ind.niveles:
            continue
        indicadores.append({
            "clave": ind.clave, "nombre": ind.nombre, "tema": ind.tema, "unidad": ind.unidad,
            "sentido": ind.sentido, "fuente": ind.fuente, "definicion": ind.definicion,
            **propio[ind.clave],
            "comparacion": {n: comparacion[n][ind.clave]["valor"] for n, _ in superiores},
            "posicion": analisis.posicion(codigo, ind.clave) if es_muni else None,
        })
    totales = {f["cuadro"]: int(f["valor"]) for f in consultar(
        "SELECT cuadro, valor FROM valores WHERE nivel = ? AND codigo = ? AND orden = 0 AND cuadro IN ('A1', 'B2')",
        [nivel, codigo])}
    nombres = nombres_municipios()
    return {
        "lugar": info,
        "jerarquia": [lugar(n, c) for n, c in superiores],
        "poblacion_censada": totales.get("A1"),
        "hogares": totales.get("B2"),
        "indicadores": indicadores,
        "destaca_retos": analisis.destaca_y_retos(codigo) if es_muni else None,
        "parecidos": [{**p, **nombres[p["codigo"]]} for p in analisis.parecidos(codigo)] if es_muni else [],
        "texto": texto.generar(info["nombre"], nivel, codigo, propio, pais),
        "umbral_pocos_casos": UMBRAL_POCOS_CASOS,
        "fuentes": [FUENTE_CENSO, FUENTE_PROY],
    }


@router.get("/cuadros")
def cuadros():
    """Catálogo de los cuadros del censo cargados (título, tema, universo, notas)."""
    return consultar("SELECT * FROM cuadros ORDER BY cuadro")


@router.get("/cuadros/{cuadro}/{nivel}/{codigo}")
def cuadro_de(cuadro: str, nivel: Nivel, codigo: int):
    """Un cuadro completo para un territorio, con % sobre el universo y % nacional."""
    meta = consultar("SELECT * FROM cuadros WHERE cuadro = ?", [cuadro.upper()])
    if not meta:
        raise HTTPException(404, f"No existe el cuadro {cuadro}")
    filas = consultar(
        """WITH aqui AS (SELECT * FROM valores WHERE cuadro = ? AND nivel = ? AND codigo = ?),
                pais AS (SELECT * FROM valores WHERE cuadro = ? AND nivel = 'pais')
           SELECT a.grupo, a.categoria, a.orden, CAST(a.valor AS INTEGER) AS valor,
                  round(100 * a.valor / NULLIF((SELECT valor FROM aqui WHERE orden = 0), 0), 1) AS porcentaje,
                  round(100 * p.valor / NULLIF((SELECT valor FROM pais WHERE orden = 0), 0), 1) AS porcentaje_pais
           FROM aqui a LEFT JOIN pais p USING (orden) ORDER BY a.orden""",
        [meta[0]["cuadro"], nivel, codigo, meta[0]["cuadro"]])
    return {"cuadro": meta[0], "lugar": lugar(nivel, codigo), "filas": filas, "fuente": FUENTE_CENSO}


@router.get("/proyecciones/{nivel}/{codigo}")
def proyecciones(nivel: Literal["pais", "departamento", "municipio"], codigo: int,
                 anio: int = Query(2026, ge=2015, le=2030)):
    """Serie 2015-2030 y pirámide de edades de un año (no existen por lugar poblado)."""
    info = lugar(nivel, codigo)
    filtro = {"pais": "TRUE", "departamento": "cod_mupio // 100 = ?", "municipio": "cod_mupio = ?"}[nivel]
    p = [] if nivel == "pais" else [codigo]
    serie = consultar(
        f"""SELECT anio, SUM(poblacion) FILTER (WHERE sexo = 'total') AS total,
                   SUM(poblacion) FILTER (WHERE sexo = 'hombres') AS hombres,
                   SUM(poblacion) FILTER (WHERE sexo = 'mujeres') AS mujeres
            FROM proyecciones WHERE {filtro} GROUP BY anio ORDER BY anio""", p)
    piramide = consultar(
        f"""SELECT least(edad // 5 * 5, 70) AS edad_desde,   -- grupos de 5 años; 70 = "70 o más"
                   SUM(poblacion) FILTER (WHERE sexo = 'hombres') AS hombres,
                   SUM(poblacion) FILTER (WHERE sexo = 'mujeres') AS mujeres
            FROM proyecciones WHERE {filtro} AND anio = ? GROUP BY edad_desde ORDER BY edad_desde""", p + [anio])
    censada = consultar("SELECT CAST(valor AS INTEGER) v FROM valores WHERE cuadro = 'A1' AND nivel = ? "
                        "AND codigo = ? AND orden = 0", [nivel, codigo])
    return {
        "lugar": info, "serie": serie, "anio_piramide": anio, "piramide": piramide,
        "poblacion_censada_2018": censada[0]["v"] if censada else None,
        "nota": "Estimaciones y proyecciones del INE, no conteos. La estimación para 2018 es mayor que la "
                "población censada porque incorpora ajustes demográficos (como la omisión censal).",
        "fuente": FUENTE_PROY,
    }


@router.get("/calidad")
def calidad():
    """Validaciones de la ingesta y fuentes con URL, fecha de descarga y SHA-256."""
    return {
        "validaciones": consultar("SELECT chequeo, problemas, aprobado FROM validaciones"),
        "fuentes": consultar("SELECT clave, titulo, licencia, url, fecha_descarga, sha256 FROM fuentes"),
        "equivalencias": consultar(
            """SELECT e.cod_mupio, e.cod_proy, e.nombre FROM equivalencias_municipio e
               WHERE codigo_cambia ORDER BY cod_mupio"""),
    }
