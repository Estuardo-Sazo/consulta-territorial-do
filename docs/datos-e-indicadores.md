# Datos, indicadores y métodos

Este documento explica **qué datos usa la herramienta, cómo se calcula cada cifra y cómo se
comprueba que es correcta**. Corresponde al criterio de rigor en el uso de los datos.

Fuente principal: **Instituto Nacional de Estadística (INE) de Guatemala**.

## 1. Fuentes

Todas se descargaron el **24 de noviembre de 2026**. El registro, con URL, bytes y SHA-256 de
cada archivo, está en [`datos/crudos/FUENTES.csv`](../datos/crudos/FUENTES.csv).

| Clave | Conjunto | Nivel | Universo |
|---|---|---|---|
| `a01_poblacion` | Censo 2018 · Cuadro A1: población por sexo, grupos quinquenales de edad y área | depto, municipio y lugar poblado | Personas |
| `a05_pueblos` | Censo 2018 · Cuadro A5: población por pueblo de pertenencia | ídem | Personas |
| `a11_alfabetismo` | Censo 2018 · Cuadro A11: población de 7 años o más por alfabetismo, asistencia y lugar de estudio | ídem | Personas de 7 años o más |
| `a12_tic` | Censo 2018 · Cuadro A12: población de 7 años o más por uso de celular, computadora e internet | ídem | Personas de 7 años o más |
| `b02_agua` | Censo 2018 · Cuadro B2: hogares por fuente principal de agua para consumo | ídem | Hogares |
| `b03_sanitario` | Censo 2018 · Cuadro B3: hogares por tipo y uso de servicio sanitario | ídem | Hogares |
| `b04_alumbrado` | Censo 2018 · Cuadro B4: hogares por alumbrado, energía para cocinar y cuarto para cocinar | ídem | Hogares |
| `centroides` | Censo 2018 · Listado (centroides) de lugares poblados | lugar poblado | 20,036 lugares |
| `proyecciones` + diccionario | Estimaciones y proyecciones de población por municipio, sexo y edad, 2015-2030 | municipio | Personas |
| `precios_ref_2022`, `precios_ref_2023` + diccionario | Precios de referencia del INE (junio 2022 y 2 de octubre de 2023) | producto | Precios |
| `guatecompras/ocds_2026_01` a `_10` | Guatecompras OCDS, procesos publicados de enero a octubre de 2026 | proceso | Renglones de compra |
| `municipios_geoboundaries` | geoBoundaries GTM ADM2 (límites municipales simplificados) | municipio | Polígonos |

## 2. Códigos territoriales

- Los códigos del INE son **jerárquicos**: el lugar poblado `1601045` pertenece al municipio
  `1601`, que pertenece al departamento `16`. La herramienta usa esta regla para subir de nivel.
- **Censo y proyecciones numeran distinto algunos municipios.** En el departamento de Guatemala,
  Mixco es `0108` en el censo y `0129` en las proyecciones. Por eso no se supone ninguna regla
  aritmética: la tabla `equivalencias_municipio` cruza por nombre normalizado dentro de cada
  departamento, y la ingesta falla si no cruzan los 340.
- Los códigos que terminan en `999` ("Otros lugares poblados") son una agrupación del INE, no un
  lugar real. Se marcan como agrupados, se excluyen del mapa de puntos y la ficha lo advierte.

## 3. Indicadores

Los 18 indicadores están definidos en [`api/indicadores.py`](../api/indicadores.py). Todos se
calculan con **la misma función para los cuatro niveles** (país, departamento, municipio y lugar
poblado), a partir de los **conteos** publicados por el INE, no de porcentajes ya redondeados.

**Sentido:** `+` más alto es mejor · `−` más alto es peor · `0` descriptivo (no se califica).

### Población

| Indicador | Definición | Cuadro | Sentido |
|---|---|---|---|
| Población estimada 2026 | Población total estimada para 2026 (proyección, no conteo). Solo hasta municipio | Proyecciones | 0 |
| Crecimiento 2015-2030 | (Población 2030 − población 2015) / población 2015 × 100. Solo hasta municipio | Proyecciones | 0 |
| Mujeres | Mujeres / población total censada × 100 | A1 | 0 |
| Población urbana | Población en área urbana / población total censada × 100, según la clasificación de área del Censo 2018 | A1 | 0 |
| Menores de 15 años | Población de 0 a 14 años / población total × 100 | A1 | 0 |
| 65 años o más | Población de 65 años o más / población total × 100 | A1 | 0 |
| Razón de dependencia | (Población de 0-14 + 65 y más) / población de 15-64 × 100 | A1 | 0 |
| Pueblo maya | Personas que se autoidentifican como mayas / población total × 100 | A5 | 0 |

### Educación y tecnología (población de 7 años o más)

| Indicador | Definición | Cuadro | Sentido |
|---|---|---|---|
| Alfabetismo | Personas que saben leer y escribir / población de 7 años o más × 100 | A11 | + |
| Brecha de alfabetismo hombres-mujeres | Alfabetismo de hombres − alfabetismo de mujeres, en puntos porcentuales | A11 | − |
| Asiste a un centro educativo | Personas que asisten / población de 7 años o más × 100. Es descriptivo porque depende mucho de la estructura de edades | A11 | 0 |
| Usa internet | Personas que declararon usar internet / población de 7 años o más × 100 | A12 | + |
| Usa computadora | Personas que declararon usar computadora / población de 7 años o más × 100 | A12 | + |

### Servicios del hogar (hogares)

| Indicador | Definición | Cuadro | Sentido |
|---|---|---|---|
| Agua por tubería en la vivienda | Hogares cuya fuente principal es tubería en la vivienda / total de hogares × 100 | B2 | + |
| Inodoro conectado a drenaje | Hogares con inodoro conectado a red de drenajes / total de hogares × 100 | B3 | + |
| Sin servicio sanitario | Hogares que no tienen servicio sanitario / total de hogares × 100 | B3 | − |
| Alumbrado con energía eléctrica | Hogares cuyo alumbrado es la red eléctrica / total de hogares × 100 | B4 | + |
| Cocina con leña | Hogares cuya fuente principal para cocinar es leña / total de hogares × 100 | B4 | − |

### Comprobación contra la publicación oficial

La validación 4 de la ingesta y las pruebas de `tests/test_api.py` verifican que los valores
nacionales calculados coinciden con los publicados por el INE para el Censo 2018:

| Cifra | Valor |
|---|---|
| Población total censada | 14,901,286 |
| Alfabetismo (7 años o más) | 81.5 % |
| Población urbana | 53.9 % |
| Alumbrado con energía eléctrica | 88.1 % |

### Pocos casos

Si el universo de un indicador (personas u hogares) es **menor de 30**, el porcentaje se marca
como *pocos casos*. No se oculta, porque el INE ya publicó esa cifra, pero se advierte que un
solo caso la mueve varios puntos. Estos indicadores no entran en "dónde destaca" ni en "sus
retos".

## 4. Métodos de análisis

Están en [`api/analisis.py`](../api/analisis.py) y [`api/precios.py`](../api/precios.py). Se
escribieron en Python puro, sin numpy ni scipy, para que cada fórmula se pueda leer y auditar.

| Método | Dónde se ve | Cómo se calcula |
|---|---|---|
| **Puesto y percentil** | Ficha, Comparar | Puesto entre los 340 municipios y dentro del departamento (1 = valor más alto). Percentil = % de municipios con valor menor o igual |
| **Dónde destaca / sus retos** | Ficha | Indicadores con sentido en los que el municipio está en el **10 % extremo** del país (34 de 340), según el percentil a favor. Se excluyen los descriptivos y los de pocos casos |
| **Municipios parecidos** | Ficha | Los indicadores se estandarizan en valores z, (x − media) / desviación, para que todos pesen igual. Luego se eligen los 5 municipios con menor **distancia euclidiana** |
| **Correlación** | Explorar | Coeficiente de Pearson *r*, con su lectura: muy débil < 0.2 ≤ débil < 0.4 ≤ moderada < 0.6 ≤ fuerte. Siempre se acompaña de "correlación no es causalidad" |
| **Mapa** | Explorar | **Quintiles**: 5 grupos de ≈ 68 municipios, para que un valor extremo no aplaste la escala |
| **"Mejor" al comparar** | Comparar | Solo en indicadores con sentido y si la diferencia es de 1 punto o más |
| **Texto "Lo que dicen los datos"** | Ficha | Reglas fijas. Una diferencia menor de 2 puntos se describe como "similar al" país |

## 5. Precios

### Precios de referencia del INE

- Se usa la versión del 2 de octubre de 2023 como principal y se agregan las 3 filas de 2022
  que ya no aparecen en ella.
- El **precio vigente** es el de la fecha más reciente entre el precio original y sus
  actualizaciones. En 38 filas la segunda actualización es anterior a la primera, así que tomar
  "la última columna" habría sido un error.
- Se excluyen 5 filas con "Sin Dato".

### Precios de Guatecompras

- Solo **bienes**. En servicios y obras, la cantidad no es una unidad comparable.
- **Precio unitario = monto adjudicado / cantidad**, calculado solo en procesos adjudicados con
  un renglón y una adjudicación activa. OCDS no indica a qué renglón corresponde cada
  adjudicación, así que no se reparte el monto entre renglones.
- Si un proceso (NOG) aparece en varios meses, se conserva su versión más reciente.
- Los precios solo se comparan **dentro de la misma unidad de medida**.

| Cifra | Cálculo |
|---|---|
| **Mediana** (principal) | Valor central. Un renglón mal capturado no la mueve |
| Promedio y moda | Como los reporta la DPIR. La moda se redondea al quetzal |
| Q1, Q3 | Cuartiles por interpolación lineal |
| **Atípicos** | Regla de Tukey: fuera de [Q1 − 1.5·RIC, Q3 + 1.5·RIC] |
| Pocos casos | Aviso con menos de 30 renglones |

### Compras municipales

Cada municipalidad compradora se asigna a su municipio por nombre, dentro del departamento.
Resultado: **323 por nombre exacto, 14 por prefijo o sufijo y 3 aproximados**, con 4 alias
revisados a mano. Las 340 quedan emparejadas.

## 6. Validaciones

`ingesta/cargar.py` ejecuta 17 consultas SQL al construir la base. Cada una cuenta problemas, y
0 significa aprobada. **Si alguna falla, la base anterior no se reemplaza.**

| # | Chequeo |
|---|---|
| 1 | Suma de lugares poblados = total del municipio (todos los cuadros) |
| 2 | Suma de municipios = total del departamento (todos los cuadros) |
| 3 | Hombres + mujeres = población total (A1, cada lugar poblado) |
| 4 | Total nacional del censo = 14,901,286 personas |
| 5 | Todo lugar poblado de los cuadros existe en el listado de centroides |
| 6 | Coordenadas dentro del territorio de Guatemala |
| 7 | Los 340 municipios cruzan con las proyecciones |
| 8 | Proyecciones: hombres + mujeres = ambos sexos |
| 9 | Guatecompras: todo precio unitario es positivo |
| 10 | Guatecompras: las 340 municipalidades tienen código de municipio del INE |
| 11 | Guatecompras: todo proceso municipal apunta a un municipio existente |
| 12 | Precios de referencia: todo precio es positivo y tiene fecha |
| 13-17 | Informativos: edades reparadas en proyecciones, fechas invertidas, filas sin precio, filas de 2022 agregadas y método de emparejamiento de municipalidades |

Los resultados se ven en la aplicación (panel **Rigor y fuentes**) y en `GET /api/calidad`.

## 7. Secreto estadístico

- Solo se usan **cuadros agregados publicados** por el INE. No se usan microdatos.
- La herramienta no intenta identificar personas, hogares ni empresas, y no cruza fuentes con
  ese fin.
- De Guatecompras no se guardan nombres de proveedores. Solo se muestran la entidad compradora
  (pública), el producto, la fecha y el precio.
