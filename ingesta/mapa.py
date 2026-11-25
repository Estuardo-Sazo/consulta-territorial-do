"""Límites municipales (geoBoundaries) con el código de municipio del INE.

geoBoundaries solo trae el nombre del municipio (y 2 lagos). En vez de cruzar
por nombre (con variantes de escritura y homónimos entre departamentos), se usa
el listado OFICIAL de centroides de lugares poblados del Censo 2018:

    1. se cuentan los lugares poblados de cada municipio dentro de cada polígono;
    2. si el nombre del polígono coincide con un municipio que tiene puntos
       dentro, se asigna ese (los puntos resuelven los homónimos entre
       departamentos, como los varios "San José");
    3. el resto se asigna uno a uno por cantidad de puntos, de mayor a menor.

El nombre solo se usa para verificar: se informa cuántos polígonos tienen un
nombre distinto al del municipio asignado. Los límites de 2021 (CONRED/OCHA)
pueden no coincidir exactamente con los del censo; por eso se usa la mayoría
y no la totalidad de los puntos.

Uso:
    uv run python -m ingesta.mapa     -> datos/procesados/municipios.geojson
"""

import json
import sys
from collections import Counter

from shapely import STRtree
from shapely.geometry import Point, mapping, shape

from ingesta.comun import CRUDOS, PROCESADOS, RAIZ, normalizar
from ingesta.territorio import leer_dimensiones


def construir() -> tuple[dict, dict]:
    """Devuelve (GeoJSON con propiedad 'codigo', métricas de calidad)."""
    _, municipios, lugares = leer_dimensiones()
    datos = json.loads((CRUDOS / "municipios_geoboundaries.geojson").read_text(encoding="utf-8"))
    poligonos = [(f["properties"]["shapeName"], shape(f["geometry"])) for f in datos["features"]]

    # STRtree: índice espacial; evita probar cada punto contra los 342 polígonos.
    arbol = STRtree([g for _, g in poligonos])
    votos = [Counter() for _ in poligonos]
    reales = lugares[~lugares.es_agrupado]
    for cod, lon, lat in zip(reales.cod_mupio, reales.longitud, reales.latitud):
        punto = Point(lon, lat)
        for i in arbol.query(punto, predicate="intersects"):
            votos[i][cod] += 1

    nombres = dict(zip(municipios.cod_mupio, municipios.nombre))
    # Pares (puntos, polígono, municipio) de mayor a menor, para el paso 3. Solo
    # con votos falla donde los límites de 2021 difieren del censo (el polígono
    # de Chinique contiene más puntos de Chiché); por eso el nombre va primero.
    pares = sorted(((n, i, cod) for i, v in enumerate(votos) for cod, n in v.items()), reverse=True)
    lagos = {i for i, (nombre, _) in enumerate(poligonos) if normalizar(nombre).startswith("lago ")}
    por_poligono, asignado = {}, {}
    for i, (nombre, _) in enumerate(poligonos):
        coinciden = [c for c in votos[i] if normalizar(nombres[c]) == normalizar(nombre)]
        if len(coinciden) == 1 and coinciden[0] not in asignado:
            por_poligono[i], asignado[coinciden[0]] = coinciden[0], nombre
    for _, i, cod in pares:
        if i in lagos or i in por_poligono or cod in asignado:
            continue
        por_poligono[i], asignado[cod] = cod, poligonos[i][0]

    salida, distinto_nombre = [], []
    for i, cod in sorted(por_poligono.items()):
        nombre, geo = poligonos[i]
        if normalizar(nombre) not in normalizar(nombres[cod]):
            distinto_nombre.append(f"{nombre} -> {nombres[cod]}")
        salida.append({
            "type": "Feature",
            "properties": {"codigo": int(cod), "nombre": nombres[cod]},
            # Simplificar ~200 m reduce el archivo sin cambiar la lectura del mapa.
            "geometry": mapping(geo.simplify(0.002, preserve_topology=True)),
        })
    calidad = {
        "poligonos": len(salida),
        "sin_poligono": sorted(nombres[c] for c in set(nombres) - set(asignado)),
        "nombre_distinto": distinto_nombre,
        "poligonos_sin_asignar": [poligonos[i][0] for i in range(len(poligonos))
                                  if i not in por_poligono and i not in lagos],
    }
    return {"type": "FeatureCollection", "features": salida}, calidad


def main() -> int:
    geo, calidad = construir()
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    ruta = PROCESADOS / "municipios.geojson"
    texto = json.dumps(geo, ensure_ascii=False, separators=(",", ":"))
    ruta.write_text(texto, encoding="utf-8")
    print(f"  {ruta.relative_to(RAIZ)}: {calidad['poligonos']} polígonos, {ruta.stat().st_size / 1e6:.1f} MB")
    print(f"  municipios sin polígono: {calidad['sin_poligono']}")
    print(f"  polígonos sin asignar: {calidad['poligonos_sin_asignar']}")
    print(f"  nombre distinto al municipio asignado: {calidad['nombre_distinto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
