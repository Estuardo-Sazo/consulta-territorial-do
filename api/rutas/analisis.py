"""Rutas de análisis entre municipios: catálogo, mapa, ranking, dispersión."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from api import analisis
from api.calculo import tabla
from api.db import RUTA_GEOJSON
from api.indicadores import POR_CLAVE, catalogo
from api.rutas.territorio import nombres_municipios

router = APIRouter(tags=["análisis"])


def _validar(clave: str) -> None:
    if clave not in POR_CLAVE:
        raise HTTPException(404, f"No existe el indicador {clave}")


@router.get("/indicadores")
def indicadores():
    """Catálogo de indicadores con sentido (1 mejor, -1 peor, 0 descriptivo), unidad y definición."""
    return catalogo()


@router.get("/mapa/municipios.geojson")
def geojson():
    """Polígonos de los 340 municipios con su código INE (geoBoundaries, CC BY 3.0 IGO)."""
    # Cache de un día: el archivo solo cambia al reconstruir los datos.
    return FileResponse(RUTA_GEOJSON, media_type="application/geo+json",
                        headers={"Cache-Control": "public, max-age=86400"})


@router.get("/mapa/{clave}")
def mapa(clave: str):
    """Valor de un indicador en los 340 municipios, para colorear el mapa."""
    _validar(clave)
    nombres = nombres_municipios()
    t = tabla()
    return {
        "indicador": next(i for i in catalogo() if i["clave"] == clave),
        "valores": [{"codigo": c, **nombres[c], **t[c][clave]} for c in sorted(t)],
    }


@router.get("/ranking/{clave}")
def ranking(clave: str, departamento: int | None = Query(None, description="Código de departamento")):
    """Municipios ordenados por un indicador (el puesto 1 es el valor más alto)."""
    _validar(clave)
    nombres = nombres_municipios()
    return [{**r, **nombres[r["codigo"]]} for r in analisis.ranking(clave, departamento)]


@router.get("/dispersion")
def dispersion(x: str = Query(..., description="Indicador del eje X"),
               y: str = Query(..., description="Indicador del eje Y")):
    """Puntos de los 340 municipios con r de Pearson y la advertencia de causalidad."""
    _validar(x)
    _validar(y)
    d = analisis.dispersion(x, y)
    nombres = nombres_municipios()
    d["puntos"] = [{**p, **nombres[p["codigo"]]} for p in d["puntos"]]
    return d


@router.get("/comparar")
def comparar(a: int = Query(..., description="Código del primer municipio"),
             b: int = Query(..., description="Código del segundo municipio")):
    """Dos municipios lado a lado: valor, puesto en el país y diferencia por indicador.

    `mejor` dice cuál está en mejor situación según el sentido del indicador
    (None si el indicador es descriptivo o la diferencia es menor a 1 punto)."""
    nombres = nombres_municipios()
    for cod in (a, b):
        if cod not in nombres:
            raise HTTPException(404, f"No existe el municipio {cod}")
    t = tabla()
    filas = []
    for ind in catalogo():
        k = ind["clave"]
        va, vb = t[a][k]["valor"], t[b][k]["valor"]
        mejor = None
        if ind["sentido"] and va is not None and vb is not None and abs(va - vb) >= 1:
            mejor = a if (va > vb) == (ind["sentido"] > 0) else b
        pa, pb = analisis.posicion(a, k), analisis.posicion(b, k)
        filas.append({
            **ind, "a": va, "b": vb,
            "diferencia": round(va - vb, 1) if va is not None and vb is not None else None,
            "puesto_a": pa and pa["pais"], "puesto_b": pb and pb["pais"],
            "pocos_casos": t[a][k]["pocos_casos"] or t[b][k]["pocos_casos"], "mejor": mejor,
        })
    return {"a": {"codigo": a, **nombres[a]}, "b": {"codigo": b, **nombres[b]}, "indicadores": filas}
