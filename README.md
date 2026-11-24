# Consulta Territorial · Censos por municipio y lugar poblado

Proyecto del grupo **Data de Oriente** para el Datatón INE 2026 (propuesta 1 del DCR).

## Idea

Herramienta para las coordinaciones regionales y delegaciones departamentales del INE:

- **Importar** los archivos del censo (XLSX del INE) desde la web o por la API. Se procesan y se
  guardan en PostgreSQL, separados por **año de censo** (2018 hoy, el siguiente cuando exista).
- **Historial de importaciones:** cuándo se procesó cada archivo. Si se sube uno ya procesado, se
  avisa y no se reprocesa; si se sube otra versión del mismo dato, se pide confirmación antes de
  reemplazar los datos actuales.
- **Consultar** fichas de departamento, municipio y lugar poblado con indicadores, mapa,
  proyecciones y cuadros descargables.

## Tecnologías

NestJS + TypeORM (API), Angular (web), PostgreSQL 17 y Docker Compose.

## Estructura

```
api/            API en NestJS
web/            Web en Angular
datos/crudos/   Archivos del INE (XLSX) y su fuente
```

## Cómo empezar

```bash
cp .env.example .env          # cambiar contraseñas y secretos
docker compose up -d db       # PostgreSQL en localhost:5432
docker compose ps             # "db" debe aparecer como healthy
```

## Equipo

- _Roberto Rosales_ 
- _Miguel Sazo_ 
- _Jaime Sazo_ 

## Datos y uso de IA

- Fuente: Instituto Nacional de Estadística (INE) de Guatemala, XII Censo Nacional de Población y VII
  de Vivienda 2018, y estimaciones y proyecciones de población 2015-2030. Solo datos agregados
  publicados.
- En el desarrollo usamos asistencia de IA (Claude, de Anthropic), como permiten las bases del
  Datatón.

## Estado

En construcción.
