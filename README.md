# Consulta Territorial · Censos por municipio y lugar poblado

Proyecto del grupo **Data de Oriente** para la Datatón INE 2026 (propuesta 1 del DCR).

Fichas del Censo 2018 por departamento, municipio y lugar poblado, con proyecciones de población
2015-2030 y compras públicas (Guatecompras), más los precios de referencia del INE.

## Tecnologías

Python 3.12 + uv (ingesta con pandas), DuckDB (base analítica en un archivo), FastAPI (API),
React + Vite con Leaflet y Observable Plot (web), Docker Compose + nginx (despliegue).

## Estructura

```
ingesta/            descarga, lectura y validación de las fuentes (Rol 1)
datos/crudos/       archivos del INE y FUENTES.csv (URL, fecha, SHA-256)
datos/procesados/   Parquet y GeoJSON derivados, pequeños y versionados
api/                API FastAPI (Rol 2)
web/                interfaz React (Rol 3)
tests/              pruebas con pytest
docs/               documentación y guía por rol
```

Las instrucciones completas de instalación y uso se agregan al final del desarrollo.

## Equipo

- Rol 1 · datos e ingesta: Estuardo Sazo
- Rol 2 · API y análisis: Miguel Sazo
- Rol 3 · interfaz web: Roberto Rosales
