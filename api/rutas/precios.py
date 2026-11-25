"""Rutas de precios (Guatecompras + referencias del INE) y compras municipales."""

from fastapi import APIRouter, Query

from api.db import consultar
from api.precios import UMBRAL_POCOS_CASOS, condicion_texto, estadisticas, referencias_ine, terminos
from api.territorio import lugar

router = APIRouter(tags=["precios y compras"])

FUENTE_GC = "Guatecompras OCDS (Ministerio de Finanzas Públicas), CC BY 4.0"
FUENTE_REF = "INE, Precios de referencia (al 02/10/2023), ODC-BY"

AVISOS = [
    "Son precios ADJUDICADOS en procesos de Guatecompras, no precios de mercado.",
    "El precio unitario se calcula como monto adjudicado ÷ cantidad, solo en procesos con un único "
    "renglón y una única adjudicación; procesos con varios renglones no se incluyen.",
    "Solo se comparan precios de la misma unidad de medida.",
    "El departamento es el de la entidad compradora, no el lugar de entrega.",
    "Los precios de referencia del INE tienen su propia fecha (2016 a 2023): no son precios actuales.",
]


@router.get("/precios")
def precios(q: str = Query(min_length=3, description="Producto, p. ej. 'papel bond'"),
            unidad: str | None = Query(None, description="Unidad de medida; por omisión, la más frecuente"),
            departamento: int | None = Query(None, description="Código de departamento del comprador")):
    """Precios unitarios adjudicados de un producto, por unidad de medida, con
    promedio, mediana y moda, distribución, y las referencias del INE al lado."""
    palabras = terminos(q)
    cond, p = condicion_texto("texto", palabras)
    unidades = consultar(
        f"""SELECT unidad, COUNT(*) AS n, median(precio_unitario) AS mediana
            FROM precios_guatecompras WHERE {cond} GROUP BY unidad ORDER BY n DESC LIMIT 15""", p)
    elegida = unidad or (unidades[0]["unidad"] if unidades else None)

    filtro, pf = f"{cond} AND unidad = ?", p + [elegida]
    if departamento is not None:
        filtro, pf = filtro + " AND cod_depto = ?", pf + [departamento]
    filas = consultar(
        f"""SELECT g.nog, g.fecha_adjudicacion, g.mes, g.descripcion, g.unspsc, g.cantidad, g.monto,
                   g.precio_unitario, g.comprador, g.nivel_entidad, g.modalidad, g.cod_depto, d.nombre AS departamento
            FROM precios_guatecompras g LEFT JOIN departamentos d USING (cod_depto)
            WHERE {filtro} ORDER BY g.fecha_adjudicacion DESC""", pf)
    stats = estadisticas([f["precio_unitario"] for f in filas])
    por_depto = consultar(
        f"""SELECT g.cod_depto, d.nombre AS departamento, COUNT(*) AS n,
                   round(median(precio_unitario), 2) AS mediana
            FROM precios_guatecompras g LEFT JOIN departamentos d USING (cod_depto)
            WHERE {cond} AND unidad = ? GROUP BY ALL ORDER BY n DESC""", p + [elegida])
    periodo = consultar("SELECT MIN(fecha_adjudicacion) AS desde, MAX(fecha_adjudicacion) AS hasta "
                        "FROM precios_guatecompras")[0]
    return {
        "consulta": q, "unidad": elegida, "unidades": unidades, "departamento": departamento,
        "estadisticas": stats,
        "precios": [round(f["precio_unitario"], 4) for f in filas],
        "renglones": filas[:40],
        "por_departamento": [{**d, "pocos_casos": d["n"] < UMBRAL_POCOS_CASOS} for d in por_depto],
        "referencias_ine": referencias_ine(palabras),
        "periodo": periodo,
        "avisos": AVISOS,
        "fuentes": [FUENTE_GC, FUENTE_REF],
    }


@router.get("/precios/sugerencias")
def sugerencias(q: str = Query(min_length=2)):
    """Descripciones más compradas que contienen el texto (para autocompletar)."""
    cond, p = condicion_texto("texto", terminos(q))
    return consultar(
        f"""SELECT descripcion, COUNT(*) AS n FROM precios_guatecompras WHERE {cond}
            GROUP BY descripcion ORDER BY n DESC LIMIT 10""", p)


@router.get("/compras/municipio/{codigo}")
def compras_municipio(codigo: int):
    """Compras públicas de la municipalidad: monto adjudicado, procesos y modalidades."""
    info = lugar("municipio", codigo)
    base = "FROM compras_municipales WHERE cod_mupio = ?"
    resumen = consultar(
        f"""SELECT COUNT(*) AS procesos,
                   COUNT(*) FILTER (WHERE estado = 'Adjudicado') AS adjudicados,
                   SUM(monto_adjudicado) AS monto, MIN(mes) AS desde, MAX(mes) AS hasta,
                   any_value(comprador) AS comprador {base}""", [codigo])[0]
    pob = consultar("SELECT SUM(poblacion) AS p FROM proyecciones WHERE cod_mupio = ? AND anio = 2026 "
                    "AND sexo = 'total'", [codigo])[0]["p"]
    return {
        "lugar": info,
        "resumen": {**resumen, "monto_por_habitante": round(resumen["monto"] / pob, 2)
                    if resumen["monto"] and pob else None, "poblacion_2026": pob},
        "modalidades": consultar(f"""SELECT modalidad, COUNT(*) AS procesos, SUM(monto_adjudicado) AS monto
                                     {base} GROUP BY modalidad ORDER BY monto DESC""", [codigo]),
        "categorias": consultar(f"""SELECT coalesce(categoria, 'Sin categoría') AS categoria, COUNT(*) AS procesos,
                                    SUM(monto_adjudicado) AS monto {base} GROUP BY ALL ORDER BY monto DESC""",
                                [codigo]),
        "por_mes": consultar(f"""SELECT mes, COUNT(*) AS procesos, SUM(monto_adjudicado) AS monto
                                 {base} GROUP BY mes ORDER BY mes""", [codigo]),
        "mayores": consultar(f"""SELECT nog, titulo, modalidad, monto_adjudicado, fecha_publicacion
                                 {base} AND monto_adjudicado > 0 ORDER BY monto_adjudicado DESC LIMIT 8""",
                             [codigo]),
        "avisos": [
            "Monto adjudicado según Guatecompras; no es el gasto ejecutado (eso está en SICOIN).",
            "Los meses corresponden a la publicación del proceso; procesos aún en evaluación suman 0.",
        ],
        "fuente": FUENTE_GC,
    }
