"""Pruebas de la API con TestClient (sin levantar el servidor)."""

import pytest
from fastapi.testclient import TestClient

from api.db import RUTA_BASE
from api.main import app
from api.precios import estadisticas

pytestmark = pytest.mark.skipif(not RUTA_BASE.exists(), reason="falta construir la base")
cliente = TestClient(app)


def get(ruta: str):
    r = cliente.get(ruta)
    assert r.status_code == 200, r.text
    return r.json()


def test_salud():
    assert get("/api/salud") == {"estado": "ok"}


@pytest.mark.parametrize("q,esperado", [("xela", "Quetzaltenango"), ("coban", "Cobán"), ("1601", "Cobán")])
def test_buscar_sin_tildes_alias_y_codigo(q, esperado):
    assert get(f"/api/buscar?q={q}")[0]["nombre"] == esperado


def test_indicadores_nacionales_coinciden_con_la_publicacion_del_censo():
    ind = {i["clave"]: i["valor"] for i in get("/api/ficha/pais/0")["indicadores"]}
    assert ind["alfabetismo"] == 81.5
    assert ind["urbana"] == 53.9
    assert ind["electricidad"] == 88.1


def test_ficha_municipio_trae_analisis():
    f = get("/api/ficha/municipio/1601")
    assert f["lugar"]["nombre"] == "Cobán"
    assert len(f["parecidos"]) == 5 and f["texto"]
    assert {"destaca", "retos"} <= f["destaca_retos"].keys()
    alf = next(i for i in f["indicadores"] if i["clave"] == "alfabetismo")
    assert set(alf["comparacion"]) == {"departamento", "pais"} and alf["posicion"]["de_pais"] == 340


def test_ficha_lugar_poblado_sin_proyecciones():
    f = get("/api/ficha/lugar_poblado/1601045")
    claves = {i["clave"] for i in f["indicadores"]}
    assert "alfabetismo" in claves and "poblacion_actual" not in claves


def test_errores_404_y_422():
    assert cliente.get("/api/ficha/municipio/9999").status_code == 404
    assert cliente.get("/api/ficha/aldea/1").status_code == 422
    assert cliente.get("/api/mapa/no_existe").status_code == 404


def test_mapa_y_geojson_cubren_340():
    assert len(get("/api/mapa/lena")["valores"]) == 340
    assert len(get("/api/mapa/municipios.geojson")["features"]) == 340


def test_dispersion_lleva_r_y_advertencia():
    d = get("/api/dispersion?x=lena&y=alfabetismo")
    assert -1 <= d["r"] < 0 and "causalidad" in d["advertencia"] and d["n"] == 340


def test_comparar_respeta_el_sentido():
    c = get("/api/comparar?a=1601&b=901")
    lena = next(i for i in c["indicadores"] if i["clave"] == "lena")
    assert lena["mejor"] == 901  # Cobán cocina más con leña: más alto es peor
    mujeres = next(i for i in c["indicadores"] if i["clave"] == "mujeres")
    assert mujeres["mejor"] is None  # descriptivo


def test_proyecciones_por_departamento():
    p = get("/api/proyecciones/departamento/16")
    assert [s["anio"] for s in p["serie"]] == list(range(2015, 2031))


def test_precios_por_unidad_con_referencia_ine():
    p = get("/api/precios?q=papel%20bond")
    assert p["unidad"] and p["estadisticas"]["n"] > 0
    assert all(r["fecha_precio"] for r in p["referencias_ine"])
    assert any("ADJUDICADOS" in a for a in p["avisos"])
    # Las referencias salen del NOMBRE del producto, no de características que
    # solo mencionan el papel (impresoras, chocolates en empaque de papel...).
    assert p["referencias_ine"] and all("papel bond" in r["producto"].lower() for r in p["referencias_ine"])


def test_compras_municipales():
    c = get("/api/compras/municipio/1601")
    assert c["resumen"]["procesos"] > 0 and c["modalidades"]


def test_estadisticas_marca_atipicos_y_pocos_casos():
    s = estadisticas([20, 21, 22, 22.4, 23, 25, 80])
    assert s["mediana"] == 22.4 and s["atipicos"] == 1 and s["pocos_casos"]
    assert s["moda"] == 22


def test_calidad_trae_validaciones_y_fuentes_con_sha():
    c = get("/api/calidad")
    assert all(v["aprobado"] for v in c["validaciones"])
    assert all(len(f["sha256"]) == 64 for f in c["fuentes"])
