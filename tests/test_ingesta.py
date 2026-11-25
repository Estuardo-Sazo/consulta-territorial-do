"""Pruebas unitarias de las funciones de ingesta (sin leer archivos grandes)."""

import pandas as pd
import pytest

from ingesta.comun import normalizar
from ingesta.cuadros import aplanar_encabezados, limpiar
from ingesta.municipalidades import cruzar
from ingesta.precios_ref import _numero, _vigente


def test_normalizar_quita_tildes_y_signos():
    assert normalizar("  Sololá, SOLOLÁ ") == "solola solola"


def test_limpiar_quita_llamada_de_nota_pero_no_rangos():
    assert limpiar("Personas que declararon haber utilizado: 1") == "Personas que declararon haber utilizado"
    assert limpiar("70  - 74") == "70 - 74"


def test_aplanar_encabezados_combinacion_horizontal_y_vertical():
    filas = [("Población total", "Sexo", None), (None, "Hombres", "Mujeres")]
    assert aplanar_encabezados(filas) == [["Población total"], ["Sexo", "Hombres"], ["Sexo", "Mujeres"]]


@pytest.mark.parametrize("texto,esperado", [("1,100.000", 1100.0), (23.3, 23.3), ("Sin Dato", None)])
def test_numero_de_precios_escritos_como_texto(texto, esperado):
    assert _numero(texto) == esperado


def test_precio_vigente_es_el_de_fecha_mas_reciente():
    # Caso real: la 2.ª actualización (07/02/2021) es anterior a la 1.ª (01/04/2021).
    fila = {
        "precio_original": 0.75, "fecha_original": pd.Timestamp("2020-07-14"),
        "precio_act1": 0.769, "fecha_act1": pd.Timestamp("2021-04-01"),
        "precio_act2": 0.988, "fecha_act2": pd.Timestamp("2021-02-07"),
    }
    assert _vigente(fila) == (0.769, pd.Timestamp("2021-04-01"))


def test_cruce_de_municipalidades_por_prefijo_y_alias():
    deptos = pd.DataFrame({"cod_depto": [16, 13], "nombre": ["Alta Verapaz", "Huehuetenango"]})
    munis = pd.DataFrame({"cod_mupio": [1611, 1305], "cod_depto": [16, 13],
                          "nombre": ["Santa María Cahabón", "San Ildefonso Ixtahuacán"]})
    procesos = pd.DataFrame({
        "nivel_entidad": ["Municipalidad"] * 2, "mes": ["2026-10"] * 2,
        "comprador_id": ["GT-NIT-1", "GT-NIT-2"],
        "comprador": ["MUNICIPALIDAD DE CAHABON, ALTA VERAPAZ",
                      "MUNICIPALIDAD DE SAN IDELFONSO IXTAHUACÁN, HUEHUETENANGO"],
        "region": ["ALTA VERAPAZ", "HUEHUETENANGO"],
    })
    r = cruzar(procesos, munis, deptos).set_index("comprador_id")
    assert r.loc["GT-NIT-1", "cod_mupio"] == 1611 and r.loc["GT-NIT-1", "metodo"] == "prefijo o sufijo"
    assert r.loc["GT-NIT-2", "cod_mupio"] == 1305
