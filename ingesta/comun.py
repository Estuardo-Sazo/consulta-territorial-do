"""Rutas y utilidades compartidas por los módulos de ingesta."""

import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS = RAIZ / "datos" / "crudos"
PROCESADOS = RAIZ / "datos" / "procesados"
BASE = RAIZ / "datos" / "fichas.duckdb"


def normalizar(texto) -> str:
    """'Sololá ' -> 'solola'. Quita tildes y signos, pasa a minúsculas y colapsa
    espacios. Sirve para cruzar nombres escritos distinto entre bases."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sin_tildes.lower())).strip()
