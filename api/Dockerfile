# Imagen de la API (FastAPI + DuckDB). Se construye desde la raíz del proyecto
# (docker-compose.yml usa context ".").
#
# La base NO se copia: se CONSTRUYE dentro de la imagen con la ingesta, a partir
# de datos/crudos/ (INE, geoBoundaries) y datos/procesados/ (Parquet de
# Guatecompras). Así la imagen es reproducible y, si una validación falla, el
# build falla. Los zips de Guatecompras no hacen falta.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR /app

# 1) Dependencias primero: esta capa queda en caché mientras no cambie uv.lock.
#    --frozen usa uv.lock tal cual; --no-dev deja fuera pytest y httpx2.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Código y datos.
COPY ingesta/ ingesta/
COPY api/ api/
COPY datos/crudos/ datos/crudos/
COPY datos/procesados/ datos/procesados/

# 3) Construye la base y corre las validaciones.
RUN uv run --no-sync python -m ingesta.cargar

ENV FICHAS_DB=/app/datos/fichas.duckdb \
    FICHAS_GEOJSON=/app/datos/procesados/municipios.geojson
EXPOSE 8000

# 0.0.0.0: escucha en todas las interfaces del contenedor para que nginx llegue.
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
