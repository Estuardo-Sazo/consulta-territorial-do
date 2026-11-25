"""Catálogo de indicadores de la ficha.

Cada indicador declara de dónde sale (cuadro del censo o proyecciones), cómo se
calcula a partir de las "bases" (conteos publicados por el INE) y su SENTIDO:

     1  más alto es mejor   (p. ej. alfabetismo)
    -1  más alto es peor    (p. ej. hogares que cocinan con leña)
     0  descriptivo         (p. ej. % de mujeres: no se juzga)

El sentido decide qué aparece en "dónde destaca" y "sus retos" y el color del
mapa. Los indicadores descriptivos nunca se presentan como logros ni problemas.

Las bases son un diccionario plano con claves "cuadro|grupo|categoría" (más
"cuadro|u" para el universo del cuadro) y "proy|año" para las proyecciones.
"""

from collections.abc import Callable
from dataclasses import dataclass

ANIO_ACTUAL = 2026
# Por debajo de este universo un porcentaje es inestable: 1 caso lo mueve varios
# puntos. No se oculta (el INE ya lo publicó), pero se advierte.
UMBRAL_POCOS_CASOS = 30

FUENTE_CENSO = "INE, XII Censo Nacional de Población y VII de Vivienda 2018"
FUENTE_PROY = "INE, Estimaciones y proyecciones de población 2015-2030 (base Censo 2018)"

EDADES_0_14 = ("0 - 4", "5 - 9", "10 - 14")
EDADES_15_64 = ("15 - 19", "20 - 24", "25 - 29", "30 - 34", "35 - 39", "40 - 44", "45 - 49",
                "50 - 54", "55 - 59", "60 - 64")
EDADES_65 = ("65 - 69", "70 - 74", "75 - 79", "80 - 84", "85 - 89", "90 - 94", "95 - 99", "100 o más")


@dataclass(frozen=True)
class Indicador:
    clave: str
    nombre: str
    tema: str
    unidad: str  # "%", "personas", "puntos", "por cada 100"
    sentido: int  # 1 mejor, -1 peor, 0 descriptivo
    fuente: str
    definicion: str
    # Recibe las bases de un territorio y devuelve (valor, universo) o None.
    formula: Callable[[dict], tuple[float, float] | None]
    niveles: tuple[str, ...] = ("pais", "departamento", "municipio", "lugar_poblado")


def _suma(b: dict, cuadro: str, grupo: str, categorias) -> float:
    return sum(b.get(f"{cuadro}|{grupo}|{c}", 0) for c in categorias)


def porcentaje(cuadro: str, grupo: str, *categorias: str):
    """Fórmula "suma de categorías / universo del cuadro × 100"."""
    def f(b):
        u = b.get(f"{cuadro}|u")
        return (100 * _suma(b, cuadro, grupo, categorias) / u, u) if u else None
    return f


def _dependencia(b):
    """(0-14 + 65 y más) por cada 100 personas de 15-64 (definición demográfica usual)."""
    activa = _suma(b, "A1", "Grupos de edad", EDADES_15_64)
    if not activa:
        return None
    dependiente = _suma(b, "A1", "Grupos de edad", EDADES_0_14 + EDADES_65)
    return 100 * dependiente / activa, b.get("A1|u")


def _brecha_alfabetismo(b):
    """Puntos de diferencia entre el alfabetismo de hombres y el de mujeres."""
    h, m = b.get("A11|Hombres de 7 años o más|"), b.get("A11|Mujeres de 7 años o más|")
    if not h or not m:
        return None
    ah = 100 * b.get("A11|Alfabetismo|Hombres", 0) / h
    am = 100 * b.get("A11|Alfabetismo|Mujeres", 0) / m
    return ah - am, b.get("A11|u")


def _poblacion_actual(b):
    p = b.get(f"proy|{ANIO_ACTUAL}")
    return (p, p) if p else None


def _crecimiento(b):
    a, z = b.get("proy|2015"), b.get("proy|2030")
    return (100 * (z - a) / a, a) if a else None


_SOLO_PROY = ("pais", "departamento", "municipio")  # no hay proyecciones por lugar poblado

INDICADORES = [
    Indicador("poblacion_actual", f"Población estimada {ANIO_ACTUAL}", "Población", "personas", 0, FUENTE_PROY,
              f"Población total estimada para {ANIO_ACTUAL} (proyección, no conteo).", _poblacion_actual, _SOLO_PROY),
    Indicador("crecimiento", "Crecimiento 2015-2030", "Población", "%", 0, FUENTE_PROY,
              "Cambio porcentual de la población proyectada entre 2015 y 2030.", _crecimiento, _SOLO_PROY),
    Indicador("mujeres", "Mujeres", "Población", "%", 0, FUENTE_CENSO,
              "Mujeres / población total censada.", porcentaje("A1", "Sexo", "Mujeres")),
    Indicador("urbana", "Población urbana", "Población", "%", 0, FUENTE_CENSO,
              "Población en área urbana / población total censada, según la clasificación de área del Censo 2018 "
              "(por ella algunos municipios, como Cobán, aparecen casi 100 % urbanos).",
              porcentaje("A1", "Área", "Urbana")),
    Indicador("menores_15", "Menores de 15 años", "Población", "%", 0, FUENTE_CENSO,
              "Población de 0 a 14 años / población total censada.",
              porcentaje("A1", "Grupos de edad", *EDADES_0_14)),
    Indicador("mayores_65", "65 años o más", "Población", "%", 0, FUENTE_CENSO,
              "Población de 65 años o más / población total censada.",
              porcentaje("A1", "Grupos de edad", *EDADES_65)),
    Indicador("dependencia", "Razón de dependencia", "Población", "por cada 100", 0, FUENTE_CENSO,
              "Personas de 0-14 y de 65 años o más por cada 100 personas de 15 a 64 años.", _dependencia),
    Indicador("maya", "Pueblo maya", "Población", "%", 0, FUENTE_CENSO,
              "Personas que se autoidentifican como mayas / población total censada.",
              porcentaje("A5", "Pueblo de pertenencia", "Maya")),
    Indicador("alfabetismo", "Alfabetismo (7 años o más)", "Educación y tecnología", "%", 1, FUENTE_CENSO,
              "Personas de 7 años o más que saben leer y escribir / población de 7 años o más.",
              porcentaje("A11", "Alfabetismo", "Hombres", "Mujeres")),
    Indicador("brecha_alfabetismo", "Brecha de alfabetismo hombres-mujeres", "Educación y tecnología", "puntos",
              -1, FUENTE_CENSO,
              "Alfabetismo de hombres menos alfabetismo de mujeres (7 años o más), en puntos porcentuales.",
              _brecha_alfabetismo),
    Indicador("asistencia", "Asiste a un centro educativo (7 años o más)", "Educación y tecnología", "%", 0,
              FUENTE_CENSO, "Personas de 7 años o más que asisten a un centro educativo / población de 7 años o más. "
              "Descriptivo: depende mucho de la estructura de edades.",
              porcentaje("A11", "Asistencia escolar", "Asiste")),
    Indicador("internet", "Usa internet (7 años o más)", "Educación y tecnología", "%", 1, FUENTE_CENSO,
              "Personas de 7 años o más que declararon usar internet / población de 7 años o más.",
              porcentaje("A12", "Personas que declararon haber utilizado", "Internet · Usa")),
    Indicador("computadora", "Usa computadora (7 años o más)", "Educación y tecnología", "%", 1, FUENTE_CENSO,
              "Personas de 7 años o más que declararon usar computadora / población de 7 años o más.",
              porcentaje("A12", "Personas que declararon haber utilizado", "Computadora · Usa")),
    Indicador("agua_tuberia", "Agua por tubería en la vivienda", "Servicios del hogar", "%", 1, FUENTE_CENSO,
              "Hogares cuya fuente principal de agua es tubería en la vivienda / total de hogares.",
              porcentaje("B2", "Fuente principal de agua para consumo", "Tubería en la vivienda")),
    Indicador("drenaje", "Inodoro conectado a drenaje", "Servicios del hogar", "%", 1, FUENTE_CENSO,
              "Hogares con inodoro conectado a red de drenajes / total de hogares.",
              porcentaje("B3", "Tipo de servicio sanitario", "Inodoro conectado a red de drenajes")),
    Indicador("sin_sanitario", "Sin servicio sanitario", "Servicios del hogar", "%", -1, FUENTE_CENSO,
              "Hogares que no tienen servicio sanitario / total de hogares.",
              porcentaje("B3", "Tipo de servicio sanitario", "No tiene")),
    Indicador("electricidad", "Alumbrado con energía eléctrica", "Servicios del hogar", "%", 1, FUENTE_CENSO,
              "Hogares cuyo alumbrado es la red de energía eléctrica / total de hogares.",
              porcentaje("B4", "Tipo de alumbrado", "Red de energía eléctrica")),
    Indicador("lena", "Cocina con leña", "Servicios del hogar", "%", -1, FUENTE_CENSO,
              "Hogares cuya fuente principal para cocinar es leña / total de hogares.",
              porcentaje("B4", "Fuente principal para cocinar", "Leña")),
]

POR_CLAVE = {i.clave: i for i in INDICADORES}


def catalogo() -> list[dict]:
    """El catálogo en JSON (sin la fórmula), para la web y /docs."""
    return [
        {"clave": i.clave, "nombre": i.nombre, "tema": i.tema, "unidad": i.unidad, "sentido": i.sentido,
         "fuente": i.fuente, "definicion": i.definicion, "niveles": list(i.niveles)}
        for i in INDICADORES
    ]
