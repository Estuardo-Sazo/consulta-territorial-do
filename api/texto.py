"""Texto automático "Lo que dicen los datos".

Frases armadas con reglas fijas (no con un modelo de lenguaje): cada número del
texto sale del mismo cálculo que la ficha, se puede rastrear y no se inventa
nada. Solo describe y compara; nunca atribuye causas.
"""

from api.analisis import destaca_y_retos
from api.indicadores import ANIO_ACTUAL, POR_CLAVE


def _num(v: float, unidad: str) -> str:
    if unidad == "personas":
        return f"{v:,.0f}".replace(",", " ")
    return f"{v:.1f}".rstrip("0").rstrip(".") + (" %" if unidad == "%" else f" {unidad}")


def _comparar(propio: float, ref: float) -> str:
    """Compara con el valor del país; diferencias menores a 2 puntos se leen como similares."""
    if abs(propio - ref) < 2:
        return "similar al"
    return "por encima del" if propio > ref else "por debajo del"


# Indicadores que se narran siempre, en este orden.
CLAVE_NARRADOS = ["alfabetismo", "internet", "agua_tuberia", "electricidad", "lena"]


def generar(nombre: str, nivel: str, codigo: int, ind: dict, pais: dict) -> list[str]:
    """Devuelve una lista de frases. `ind` y `pais` son salidas de calculo.calcular()."""
    frases = []
    p = ind.get("poblacion_actual", {}).get("valor")
    c = ind.get("crecimiento", {}).get("valor")
    if p:
        frase = f"{nombre} tiene una población estimada de {_num(p, 'personas')} personas en {ANIO_ACTUAL}"
        if c is not None:
            frase += f" y, según las proyecciones del INE, crecerá {_num(c, '%')} entre 2015 y 2030"
        frases.append(frase + " (son proyecciones, no conteos).")

    comparaciones = []
    for k in CLAVE_NARRADOS:
        v, ref, meta = ind[k]["valor"], pais[k]["valor"], POR_CLAVE[k]
        if v is None or ref is None or nivel == "pais":
            continue
        comparaciones.append(f"{meta.nombre.lower()}: {_num(v, meta.unidad)} ({_comparar(v, ref)} "
                             f"valor nacional, {_num(ref, meta.unidad)})")
    if comparaciones:
        frases.append("En el Censo 2018: " + "; ".join(comparaciones) + ".")

    if nivel == "municipio":
        dr = destaca_y_retos(codigo)
        if dr["destaca"]:
            frases.append("Está entre el 10 % de municipios con mejor resultado del país en "
                          + ", ".join(i["nombre"].lower() for i in dr["destaca"]) + ".")
        if dr["retos"]:
            frases.append("Sus principales retos, donde está entre el 10 % con peor resultado, son "
                          + ", ".join(f"{i['nombre'].lower()} (puesto {i['puesto']} de {i['de']})"
                                      for i in dr["retos"]) + ".")
        if not dr["destaca"] and not dr["retos"]:
            frases.append("No está en los extremos del país en ningún indicador con sentido definido.")

    if any(v["pocos_casos"] for v in ind.values()):
        frases.append("Atención: algunos porcentajes se calculan sobre menos de 30 personas u hogares; "
                      "un solo caso los cambia varios puntos.")
    return frases
