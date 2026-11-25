"""Descarga los archivos fuente a datos/crudos/ y registra su procedencia.

Uso:
    uv run python -m ingesta.descargar            # baja lo que falte
    uv run python -m ingesta.descargar --forzar   # vuelve a bajar todo
    uv run python -m ingesta.descargar --solo precios_ref_2023

Cada archivo queda registrado en datos/crudos/FUENTES.csv con URL, fecha de
descarga, tamaño y huella SHA-256. Las bases de la Datatón piden documentar
fuente y fecha de cada conjunto de datos; la huella permite comprobar después
que el archivo usado es el mismo que se descargó.

Solo usa la librería estándar (urllib), para que funcione antes de `uv sync`.
"""

import argparse
import csv
import hashlib
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS = RAIZ / "datos" / "crudos"
FUENTES = CRUDOS / "FUENTES.csv"

# Prefijos de los datasets del portal datos.ine.gob.gt (obtenidos de su API CKAN).
CENSO = "https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/resource"
PROY = "https://datos.ine.gob.gt/dataset/23bbe8f8-ec9b-49c9-bcca-de78bec4efc0/resource"
PRECIOS = "https://datos.ine.gob.gt/dataset/b247b9ac-e95f-4c32-acd3-fc4bdfb6185a/resource"
# geoBoundaries fijado a un commit: la URL no cambia aunque publiquen otra versión.
GEOB = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GTM/ADM2"
OCDS = "https://ocds.guatecompras.gt/file"

# Meses de Guatecompras que se usan (año, mes). Un mes da muy pocos casos por
# producto; con diez meses las medianas ya son estables para los más comprados.
MESES_GUATECOMPRAS = [(2026, m) for m in range(1, 11)]

# Firma inicial esperada por tipo: si el portal responde una página HTML de
# error (pasa con el INE cuando tarda), se detecta aquí y no se guarda.
FIRMAS = {"xlsx": b"PK", "zip": b"PK", "csv": None, "geojson": b"{"}

CATALOGO = [
    # --- Censo 2018 (INE) ---
    {"clave": "centroides", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Listado (centroides) de lugares poblados",
     "url": f"{CENSO}/053dfa99-b3f9-4b1f-a99f-fc933ef00da4/download/centroides-de-lugares-poblados-de-la-republica-de-guatemala.-censo-2018.xlsx"},
    {"clave": "a01_poblacion", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro A1 - Población total censada por sexo, grupos quinquenales de edad y área",
     "url": f"{CENSO}/4b9c7220-ca0c-41a9-a121-348f533b070e/download/cuadro-a1-poblacion-total-censada-por-sexo-grupos-quinquenales-de-edad-y-area.xlsx"},
    {"clave": "a05_pueblos", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro A5 - Población total censada por pueblos",
     "url": f"{CENSO}/7585a69c-7c15-4b6d-92e9-ecdd3223d221/download/cuadro-a5-poblacion-total-censada-por-pueblos.xlsx"},
    {"clave": "a11_alfabetismo", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro A11 - Población de 7 años o más por alfabetismo, asistencia escolar y lugar de estudio",
     "url": f"{CENSO}/320ff5da-f3dd-4e9c-a467-18bfcb5db63b/download/cuadro-a11-poblacion-censada-de-7-anos-o-mas-por-alfabetismo-asistencia-escolar-y-lugar-de-estu.xlsx"},
    {"clave": "a12_tic", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro A12 - Población de 7 años o más por uso de celular, computadora y/o internet",
     "url": f"{CENSO}/bf7a9212-365e-44ed-bffd-49b09fe5aa3b/download/cuadro-a12-poblacion-censada-de-7-anos-o-mas-por-uso-de-celular-computadora-y_o-internet.xlsx"},
    {"clave": "b02_agua", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro B2 - Hogares censados por fuente principal de agua para consumo",
     "url": f"{CENSO}/18e940c0-53f2-4e49-bc58-b9214947ab28/download/cuadro-b2-hogares-censados-por-fuente-principal-de-agua-para-consumo.xlsx"},
    {"clave": "b03_sanitario", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro B3 - Hogares censados por tipo y uso de servicio sanitario",
     "url": f"{CENSO}/5a5049e2-8147-4cae-9090-56aabb365f32/download/cuadro-b3-hogares-censados-por-tipo-y-uso-de-servicio-sanitario.xlsx"},
    {"clave": "b04_alumbrado", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Censo 2018 · Cuadro B4 - Hogares según tipo de alumbrado, energía para cocinar y cuarto exclusivo",
     "url": f"{CENSO}/966367be-d7f6-43f1-9313-90a240782695/download/cuadro-b4-hogares-censados-segun-tipo-de-alumbrado-fuente-principal-de-energia-para-cocinar-y-d.xlsx"},
    # --- Proyecciones de población 2015-2030 (INE) ---
    {"clave": "proyecciones", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Estimaciones y proyecciones de la población total por municipio, según sexo y edad. 2015-2030",
     "url": f"{PROY}/56b97bc0-5624-408d-a136-3931dd05610a/download/estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-segun-sexo-y-edad.-2015-2030.xlsx"},
    {"clave": "proyecciones_diccionario", "tipo": "xlsx", "licencia": "INE",
     "titulo": "Diccionario de datos de las proyecciones de población 2015-2030",
     "url": f"{PROY}/7b47c92a-9f87-4df2-baea-079dd08a40ec/download/diccionario-estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-segun-sexo-y-edad.-.xlsx"},
    # --- Precios de referencia (INE, ODC-BY) ---
    {"clave": "precios_ref_2022", "tipo": "csv", "licencia": "ODC-BY",
     "titulo": "INE · Precios de referencia actualizados hasta junio 2022 (CSV)",
     "url": f"{PRECIOS}/aec255ce-11f0-4d6c-90d2-af41b1a49870/download/base-de-datos-pr-actualizados-hasta-junio-2022.csv"},
    {"clave": "precios_ref_diccionario", "tipo": "xlsx", "licencia": "ODC-BY",
     "titulo": "INE · Diccionario de precios de referencia",
     "url": f"{PRECIOS}/024bd9b2-9fb0-45c8-9635-0056f81dd6b0/download/diccionario-pr.xlsx"},
    {"clave": "precios_ref_2023", "tipo": "xlsx", "licencia": "ODC-BY",
     "titulo": "INE · Precios de referencia al 02/10/2023",
     "url": f"{PRECIOS}/d2c5d27a-a4e1-4263-9f3a-10b344884d28/download/precios-de-referencia-al-02102023.xlsx"},
    # --- Límites municipales (geoBoundaries; fuente CONRED / OCHA) ---
    {"clave": "municipios_geoboundaries", "tipo": "geojson", "licencia": "CC BY 3.0 IGO",
     "titulo": "geoBoundaries · Guatemala ADM2 (municipios), geometría simplificada",
     "url": f"{GEOB}/geoBoundaries-GTM-ADM2_simplified.geojson"},
] + [
    # --- Guatecompras OCDS (Minfin, CC BY 4.0): un zip por mes ---
    {"clave": f"guatecompras/ocds_{a}_{m:02d}", "tipo": "zip", "licencia": "CC BY 4.0",
     "titulo": f"Guatecompras OCDS · procesos publicados en {a}-{m:02d} (CSV)",
     "url": f"{OCDS}/csv/{a}/{m}", "sha_url": f"{OCDS}/sha/{a}/{m}"}
    for a, m in MESES_GUATECOMPRAS
]

COLUMNAS = ["clave", "titulo", "licencia", "url", "fecha_descarga", "bytes", "sha256", "sha_portal"]


def bajar(url: str, intentos: int = 3) -> bytes:
    """GET con reintentos. El portal del INE a veces tarda 20-40 s o corta la
    conexión; HEAD no sirve porque responde HTML, así que siempre se usa GET."""
    for i in range(1, intentos + 1):
        try:
            peticion = urllib.request.Request(url, headers={"User-Agent": "fichas-territoriales/0.1"})
            with urllib.request.urlopen(peticion, timeout=180) as r:
                return r.read()
        except OSError as error:
            if i == intentos:
                raise
            print(f"    intento {i} falló ({error}); reintento en {5 * i} s", flush=True)
            time.sleep(5 * i)
    raise RuntimeError("inalcanzable")


def es_valido(contenido: bytes, tipo: str) -> bool:
    """Comprueba la firma del archivo y que no sea una página HTML."""
    firma = FIRMAS[tipo]
    if firma is not None:
        return contenido.startswith(firma)
    return not contenido.lstrip()[:15].lower().startswith((b"<!doctype", b"<html"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Descarga las fuentes a datos/crudos/")
    parser.add_argument("--forzar", action="store_true", help="vuelve a descargar aunque ya exista")
    parser.add_argument("--solo", help="descarga solo esta clave")
    args = parser.parse_args()

    CRUDOS.mkdir(parents=True, exist_ok=True)
    # Se conservan las filas previas: la fecha debe ser la de la descarga real.
    previas = {}
    if FUENTES.exists():
        with FUENTES.open(encoding="utf-8") as f:
            previas = {fila["clave"]: fila for fila in csv.DictReader(f)}

    filas = []
    for item in CATALOGO:
        destino = CRUDOS / f"{item['clave']}.{item['tipo']}"
        omitir = args.solo and item["clave"] != args.solo
        if omitir or (destino.exists() and not args.forzar and item["clave"] in previas):
            if item["clave"] in previas:
                filas.append(previas[item["clave"]])
            continue

        print(f"  bajando {destino.relative_to(CRUDOS)} ...", flush=True)
        contenido = bajar(item["url"])
        if not es_valido(contenido, item["tipo"]):
            print(f"  ERROR: {item['clave']} no es un {item['tipo']} válido", file=sys.stderr)
            return 1
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)

        # Guatecompras publica una suma propia; se registra tal cual para cotejarla.
        # (En la revisión del 2026-11-24 no coincidió con el SHA-256 del zip: el
        # portal parece calcularla sobre otro archivo. Por eso guardamos la nuestra.)
        sha_portal = bajar(item["sha_url"]).decode().strip()[:64] if "sha_url" in item else ""
        filas.append({
            "clave": item["clave"], "titulo": item["titulo"], "licencia": item["licencia"],
            "url": item["url"], "fecha_descarga": date.today().isoformat(),
            "bytes": len(contenido), "sha256": hashlib.sha256(contenido).hexdigest(),
            "sha_portal": sha_portal,
        })

    with FUENTES.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS, restval="")
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"Listo: {len(filas)} fuentes registradas en {FUENTES.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
