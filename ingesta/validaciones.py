"""Validaciones de calidad: consultas SQL que cuentan "problemas".

Cada chequeo es (nombre, sql). 0 problemas = aprobado. Si alguno falla, cargar.py
no reemplaza la base: la API nunca sirve datos que no cuadran.
"""

import duckdb
import pandas as pd

# Rectángulo que contiene a Guatemala; detecta coordenadas erróneas.
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = -92.5, -88.0, 13.5, 18.0

CHEQUEOS_CENSO = [
    (
        "Suma de lugares poblados = total del municipio (todos los cuadros)",
        """WITH lp AS (SELECT cuadro, codigo // 1000 AS cod, orden, SUM(valor) AS v
                       FROM valores WHERE nivel = 'lugar_poblado' GROUP BY ALL)
           SELECT COUNT(*) FROM lp JOIN valores m ON m.nivel = 'municipio' AND m.cuadro = lp.cuadro
                AND m.codigo = lp.cod AND m.orden = lp.orden WHERE abs(m.valor - lp.v) > 0.5""",
    ),
    (
        "Suma de municipios = total del departamento (todos los cuadros)",
        """WITH mu AS (SELECT cuadro, codigo // 100 AS cod, orden, SUM(valor) AS v
                       FROM valores WHERE nivel = 'municipio' GROUP BY ALL)
           SELECT COUNT(*) FROM mu JOIN valores d ON d.nivel = 'departamento' AND d.cuadro = mu.cuadro
                AND d.codigo = mu.cod AND d.orden = mu.orden WHERE abs(d.valor - mu.v) > 0.5""",
    ),
    (
        "Hombres + mujeres = población total (A1, cada lugar poblado)",
        """SELECT COUNT(*) FROM (SELECT codigo, SUM(valor) FILTER (WHERE orden = 0) t,
                  SUM(valor) FILTER (WHERE grupo = 'Sexo') s
           FROM valores WHERE cuadro = 'A1' AND nivel = 'lugar_poblado' GROUP BY codigo) WHERE t <> s""",
    ),
    (
        "Total nacional del censo = 14,901,286 personas (cifra oficial publicada)",
        "SELECT COUNT(*) FROM valores WHERE cuadro='A1' AND nivel='pais' AND orden=0 AND valor <> 14901286",
    ),
    (
        "Todo lugar poblado de los cuadros existe en el listado de centroides",
        """SELECT COUNT(DISTINCT codigo) FROM valores WHERE nivel = 'lugar_poblado'
           AND codigo NOT IN (SELECT cod_lp FROM lugares_poblados)""",
    ),
    (
        "Coordenadas dentro del territorio de Guatemala",
        f"""SELECT COUNT(*) FROM lugares_poblados WHERE NOT es_agrupado AND NOT
            (longitud BETWEEN {LON_MIN} AND {LON_MAX} AND latitud BETWEEN {LAT_MIN} AND {LAT_MAX})""",
    ),
    (
        "Los 340 municipios cruzan con las proyecciones",
        "SELECT 340 - COUNT(DISTINCT cod_mupio) FROM proyecciones",
    ),
    (
        "Proyecciones: hombres + mujeres = ambos sexos",
        """SELECT COUNT(*) FROM (SELECT cod_mupio, anio, edad,
                  SUM(poblacion) FILTER (WHERE sexo = 'total') t,
                  SUM(poblacion) FILTER (WHERE sexo <> 'total') hm
           FROM proyecciones GROUP BY ALL) WHERE t <> hm""",
    ),
]


def ejecutar(con: duckdb.DuckDBPyConnection, chequeos: list[tuple[str, str]],
             informativos: list[str] = ()) -> pd.DataFrame:
    """Corre los chequeos y agrega notas informativas (siempre aprobadas)."""
    filas = []
    for nombre, sql in chequeos:
        # fetchall() consume el resultado completo antes de la siguiente consulta.
        problemas = int(con.execute(sql).fetchall()[0][0])
        filas.append({"chequeo": nombre, "problemas": problemas, "aprobado": problemas == 0})
    filas += [{"chequeo": t, "problemas": 0, "aprobado": True} for t in informativos]
    return pd.DataFrame(filas)

CHEQUEOS_PRECIOS = [
    (
        "Guatecompras: todo precio unitario es positivo",
        "SELECT COUNT(*) FROM precios_guatecompras WHERE NOT precio_unitario > 0",
    ),
    (
        "Guatecompras: las 340 municipalidades tienen código de municipio del INE",
        "SELECT 340 - COUNT(DISTINCT cod_mupio) FROM equivalencias_municipalidad WHERE cod_mupio IS NOT NULL",
    ),
    (
        "Guatecompras: todo proceso municipal apunta a un municipio existente",
        "SELECT COUNT(*) FROM compras_municipales WHERE cod_mupio NOT IN (SELECT cod_mupio FROM municipios)",
    ),
    (
        "Precios de referencia INE: todo precio es positivo y tiene fecha",
        "SELECT COUNT(*) FROM precios_referencia WHERE NOT precio > 0 OR fecha_precio IS NULL",
    ),
]
