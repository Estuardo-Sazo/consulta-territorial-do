"""Pruebas sobre la base construida (requiere `uv run python -m ingesta.cargar`)."""

import json

import duckdb
import pytest

from ingesta.comun import BASE, PROCESADOS

pytestmark = pytest.mark.skipif(not BASE.exists(), reason="falta construir la base")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(str(BASE), read_only=True)
    yield c
    c.close()


def uno(con, sql):
    return con.execute(sql).fetchall()[0][0]


def test_todas_las_validaciones_aprobadas(con):
    assert uno(con, "SELECT COUNT(*) FROM validaciones WHERE NOT aprobado") == 0


def test_dimensiones(con):
    assert uno(con, "SELECT COUNT(*) FROM departamentos") == 22
    assert uno(con, "SELECT COUNT(*) FROM municipios") == 340


def test_equivalencia_mixco(con):
    # El censo usa 0108 y las proyecciones 0129 para Mixco.
    assert uno(con, "SELECT cod_proy FROM equivalencias_municipio WHERE cod_mupio = 108") == "0129"


def test_poligonos_cubren_los_340_municipios_sin_repetir():
    geo = json.loads((PROCESADOS / "municipios.geojson").read_text(encoding="utf-8"))
    codigos = [f["properties"]["codigo"] for f in geo["features"]]
    assert len(codigos) == len(set(codigos)) == 340


def test_precios_tienen_fecha(con):
    assert uno(con, "SELECT COUNT(*) FROM precios_guatecompras WHERE fecha_adjudicacion IS NULL") == 0
    assert uno(con, "SELECT MAX(fecha_precio) FROM precios_referencia").year == 2023
