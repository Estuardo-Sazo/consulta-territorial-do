"""Lector genérico de los cuadros del Censo 2018 publicados por el INE.

Todos los cuadros (A1, A5, B2, ...) siguen el mismo formato en Excel:

    fila 1   "Características generales de la población. Censo 2018"
    fila 2   "Cuadro A1.3 - Población total ... según lugar poblado"   <- título
    filas 5+ encabezados en 2 o 3 niveles, con celdas combinadas:
             | Código | Departamento | ... | Sexo            | Grupos de edad   |
             |        |              | ... | Hombres|Mujeres| 0 - 4 | 5 - 9 ...|
    datos    una fila por departamento, municipio o lugar poblado
    pie      "Fuente: INE, XII Censo ..." y notas "1 Se excluyen ..."

Cada libro trae 3 hojas: _1 por departamento, _2 por municipio, _3 por lugar
poblado. Este módulo lee cualquiera de ellas y la convierte a "formato largo":
una fila por (lugar, variable). Así un solo código sirve para todos los cuadros
y la API puede mostrar cualquier cuadro sin conocer sus columnas de antemano.

Ejemplo de salida (formato largo):

    nivel          codigo   grupo      categoria  orden  valor
    lugar_poblado  101001   Sexo       Hombres    1      22129
    lugar_poblado  101001   Sexo       Mujeres    2      24086
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import pandas as pd

# Encabezados que identifican columnas de identificación (no son datos).
ETIQUETAS_ID = {"Código", "Departamento", "Municipio", "Lugar Poblado", "Lugar poblado"}

# Según cuántas columnas de identificación tenga la hoja, sabemos su nivel:
# 2 = (Código, Departamento), 4 = + (Código, Municipio), 6 = + (Código, Lugar poblado).
NIVEL_POR_COLUMNAS_ID = {2: "departamento", 4: "municipio", 6: "lugar_poblado"}

# Columnas de coordenadas: se ignoran aquí porque las tomamos del listado de centroides.
ETIQUETAS_GEO = {"Longitud", "Latitud"}


@dataclass
class Cuadro:
    """Resultado de leer una hoja: metadatos + valores en formato largo."""

    titulo: str  # "Cuadro A1.3 - Población total ..."
    nivel: str  # "departamento" | "municipio" | "lugar_poblado"
    valores: pd.DataFrame  # columnas: nivel, codigo, grupo, categoria, orden, valor
    nombres: pd.DataFrame  # columnas de identificación (códigos y nombres)
    notas: list[str] = field(default_factory=list)  # notas al pie ("1 Se excluyen ...")


def limpiar(texto) -> str | None:
    """Normaliza una etiqueta de encabezado.

    - Colapsa espacios repetidos: "70  - 74" -> "70 - 74".
    - Quita llamadas a notas al pie: "Personas que declararon haber utilizado: 1"
      -> "Personas que declararon haber utilizado". Solo si hay dos puntos, para
      no romper etiquetas como "0 - 4".
    """
    if texto is None:
        return None
    t = re.sub(r"\s+", " ", str(texto)).strip()
    t = re.sub(r":\s*\d+$", "", t)
    return t or None


def aplanar_encabezados(filas: list[tuple]) -> list[list[str]]:
    """Convierte encabezados de varios niveles (celdas combinadas) en una lista
    de "partes" por columna, p. ej. ["Sexo", "Mujeres"].

    openpyxl solo entrega el valor en la PRIMERA celda de un rango combinado;
    las demás llegan vacías (None). Hay dos tipos de combinación:

    - Horizontal (p. ej. "Sexo" sobre Hombres y Mujeres): la celda vacía tiene
      algo DEBAJO en la misma columna -> se rellena con el valor de la izquierda.
    - Vertical (p. ej. "Población total" ocupando 2 filas): la celda vacía NO
      tiene nada debajo -> no se rellena; la columna termina en ese nivel.
    """
    n_cols = max(len(f) for f in filas)
    # Completa con None las filas más cortas para que todas tengan n_cols.
    crudo = [[limpiar(f[j]) if j < len(f) else None for j in range(n_cols)] for f in filas]

    # Para cada columna, el nivel más profundo que tiene texto.
    profundidad = []
    for j in range(n_cols):
        niveles = [i for i in range(len(crudo)) if crudo[i][j] is not None]
        profundidad.append(max(niveles) if niveles else -1)

    partes_por_columna = []
    ultimo_por_nivel = [None] * len(crudo)  # último texto visto en cada nivel (para rellenar)
    for j in range(n_cols):
        partes = []
        for i in range(len(crudo)):
            valor = crudo[i][j]
            if valor is not None:
                ultimo_por_nivel[i] = valor
                # Un texto nuevo en el nivel i "cierra" los rangos de los niveles inferiores.
                for k in range(i + 1, len(crudo)):
                    ultimo_por_nivel[k] = None
            elif i < profundidad[j]:
                valor = ultimo_por_nivel[i]  # combinación horizontal: hereda de la izquierda
            if valor is not None and i <= profundidad[j]:
                partes.append(valor)
        partes_por_columna.append(partes)
    return partes_por_columna


def _es_fila_de_datos(fila: tuple, n_id: int) -> bool:
    """Una fila es de datos si trae un código numérico, o si es el total nacional."""
    codigo = fila[n_id - 2] if len(fila) >= n_id else None
    return isinstance(codigo, (int, float)) or (len(fila) > 1 and fila[1] == "Total nacional")


def leer_hoja(ruta: Path, hoja: str) -> Cuadro:
    """Lee una hoja de un cuadro del censo y la devuelve en formato largo."""
    # read_only=True lee en modo streaming: mucho más rápido y con menos memoria.
    libro = openpyxl.load_workbook(ruta, read_only=True)
    filas = list(libro[hoja].iter_rows(values_only=True))
    libro.close()

    titulo = limpiar(filas[1][0])

    # 1) Ubicar encabezados: empiezan en la fila cuya primera celda dice "Código".
    inicio_enc = next(i for i, f in enumerate(filas) if f and f[0] == "Código")

    # 2) Número de columnas de identificación: las etiquetas iniciales conocidas.
    n_id = 0
    while limpiar(filas[inicio_enc][n_id]) in ETIQUETAS_ID:
        n_id += 1
    nivel = NIVEL_POR_COLUMNAS_ID[n_id]

    # 3) Los datos empiezan en la primera fila que cumpla _es_fila_de_datos.
    inicio_datos = next(i for i in range(inicio_enc + 1, len(filas)) if _es_fila_de_datos(filas[i], n_id))

    # Filas de encabezado sin las completamente vacías (A1.1 trae una en medio).
    encabezados = [f for f in filas[inicio_enc:inicio_datos] if any(c is not None for c in f)]
    partes = aplanar_encabezados(encabezados)

    # 4) Columnas de valores: después de las de identificación, sin coordenadas ni vacías.
    columnas = []
    for j in range(n_id, len(partes)):
        p = partes[j]
        if not p or p[-1] in ETIQUETAS_GEO:
            continue
        columnas.append(
            {
                "indice": j,
                "grupo": p[0],
                # "Celular · Usa" cuando hay 3 niveles; None si la columna es de un solo nivel.
                "categoria": " · ".join(p[1:]) or None,
                "orden": len(columnas),  # orden original, para mostrar igual que el INE
            }
        )

    # 5) Recorrer filas de datos hasta el pie ("Fuente: ...").
    registros, nombres, notas = [], [], []
    for f in filas[inicio_datos:]:
        if not any(c is not None for c in f):
            continue  # fila en blanco
        if _es_fila_de_datos(f, n_id):
            es_total = f[n_id - 2] is None  # "Total nacional" no tiene código
            nivel_fila = "pais" if es_total else nivel
            codigo = 0 if es_total else int(f[n_id - 2])
            nombres.append({"nivel": nivel_fila, "codigo": codigo, **{f"id{k}": f[k] for k in range(n_id)}})
            for c in columnas:
                valor = f[c["indice"]]
                registros.append(
                    {
                        "nivel": nivel_fila,
                        "codigo": codigo,
                        "grupo": c["grupo"],
                        "categoria": c["categoria"],
                        "orden": c["orden"],
                        # El INE escribe los ceros como "-" (hojas de municipio) o deja
                        # la celda vacía; ambos casos se toman como 0. Las validaciones
                        # de sumas en cargar.py confirman que esta lectura es correcta.
                        "valor": float(valor) if isinstance(valor, (int, float)) else 0.0,
                    }
                )
        else:
            texto = limpiar(f[0])
            # Las notas al pie empiezan con su número de llamada ("1 Se excluyen ...").
            if texto and re.match(r"^\d+\s", texto):
                notas.append(texto)

    return Cuadro(
        titulo=titulo,
        nivel=nivel,
        valores=pd.DataFrame(registros),
        nombres=pd.DataFrame(nombres),
        notas=notas,
    )
