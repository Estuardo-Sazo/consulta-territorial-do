# Manual de uso · Fichas Territoriales

Guía para el personal de coordinaciones regionales, delegaciones departamentales y cualquier
persona que consulte la herramienta. No se necesita saber de programación.

> Para instalarla, ver la sección **Instalación y uso** del [README](../README.md). Una vez en
> marcha se abre en el navegador: `http://localhost:8090` con Docker o `http://localhost:5180`
> en desarrollo.

## 1. Pantalla principal

La barra superior tiene:

| Elemento | Para qué |
|---|---|
| **Fichas Territoriales** (logo) | Vuelve a la ficha de Guatemala (país) |
| **Fichas** | Ficha del territorio elegido |
| **Explorar** | Mapa, ranking y dispersión de los 340 municipios |
| **Comparar** | Dos municipios lado a lado |
| **Precios** | Precios de compras públicas |
| **Buscador** | Busca departamentos, municipios y lugares poblados |

Al pie de cada página están la fuente de los datos y el panel **Rigor y fuentes**.

## 2. Buscar un territorio

1. Escriba en el buscador al menos parte del nombre: `coban`, `San Juan`, `Zona 1`.
   - No importan las tildes ni las mayúsculas.
   - Se aceptan nombres populares: `Xela` (Quetzaltenango), `Nebaj`, `Cahabón`.
   - También se puede escribir el código del INE: `1601` (Cobán) o `16` (Alta Verapaz).
2. Elija un resultado con el ratón o con las flechas ↑ ↓ y Enter. Cada resultado indica si es
   departamento, municipio o lugar poblado y a qué territorio pertenece.

## 3. Leer la ficha

La ficha tiene las mismas secciones para el país, un departamento, un municipio o un lugar
poblado. Las secciones que no aplican a un nivel se omiten.

| Sección | Qué muestra | Cómo leerla |
|---|---|---|
| **Encabezado** | Nombre, territorios superiores, población y hogares del Censo 2018 | Es el resumen para citar en una reunión |
| **Lo que dicen los datos** | Frases automáticas: población, crecimiento, comparación con el país, dónde destaca y sus retos | Cada cifra sale del mismo cálculo de la ficha. Describe y compara, pero no atribuye causas |
| **Indicadores** | 18 indicadores en tres temas: Población, Educación y tecnología, Servicios del hogar | Las barras comparan con el departamento y el país. **¿Cómo se calcula?** muestra la definición y la fuente |
| **Municipios con perfil parecido** | Los 5 municipios más parecidos en el conjunto de indicadores | "Parecido" se refiere al perfil, no a la distancia en el mapa |
| **Departamentos / Municipios / Lugares poblados** | Territorios del nivel inferior, con filtro por nombre | Haga clic en uno para bajar de nivel. En un municipio incluye el mapa de sus lugares poblados |
| **Proyección de población 2015-2030** | Línea de población por año y pirámide por sexo y edad | Es una **proyección** del INE, no un conteo. El deslizador cambia el año de la pirámide |
| **Compras públicas de la municipalidad** | Solo en municipios: monto adjudicado, monto por habitante, modalidades, meses y procesos de mayor monto | Datos de Guatecompras, de enero a octubre de 2026 |
| **Cuadros detallados del censo** | Cualquiera de los 7 cuadros del Censo 2018, con % local y % nacional | **Descargar CSV** guarda el cuadro con la fuente en la primera línea |

### Avisos que pueden aparecer

| Aviso | Significado |
|---|---|
| **pocos casos** | El porcentaje se calculó sobre menos de 30 personas u hogares. Un solo caso lo mueve varios puntos, así que conviene usarlo con cautela |
| **"Otros lugares poblados"** | Es una agrupación del INE de lugares pequeños del municipio, no un lugar único |
| **No hay proyección por lugar poblado** | Las proyecciones del INE existen solo por municipio |

### Colores y "mejor / peor"

Cada indicador tiene un **sentido**:

- **Más alto es mejor:** alfabetismo, uso de internet, agua por tubería, electricidad.
- **Más alto es peor:** cocina con leña, hogares sin sanitario, brecha de alfabetismo.
- **Descriptivo:** % de mujeres, población urbana, pueblo maya, edades. Estos no se califican
  como logro ni como problema.

## 4. Imprimir o guardar en PDF

1. En la ficha, pulse **Imprimir / guardar PDF**.
2. En el diálogo del navegador elija **Guardar como PDF**. El nombre sugerido es el del
   territorio.

La impresión oculta la barra y los botones, conserva el encabezado de la ficha y evita cortar
las tarjetas entre páginas.

## 5. Explorar los 340 municipios

1. Elija un **indicador** en la lista. El mapa colorea cada municipio en 5 grupos (quintiles) de
   unos 68 municipios cada uno.
   - Con indicadores "mejor/peor", el color más oscuro indica la peor situación (lo dice la
     leyenda).
   - Con indicadores descriptivos, el color no califica.
2. Haga clic en un municipio para seleccionarlo y luego en **Abrir su ficha**.
3. El **Ranking** ordena los municipios de mayor a menor. Se puede filtrar por departamento y
   descargar en CSV.
4. **¿Se mueven juntos?** compara dos indicadores en una dispersión y muestra el coeficiente de
   correlación *r*, con su lectura en palabras (débil, moderada, fuerte).
   **Correlación no es causalidad:** que dos indicadores se muevan juntos no significa que uno
   cause el otro.

La dirección de la página guarda el indicador elegido, así que se puede copiar y compartir.

## 6. Comparar dos municipios

1. Escriba el **Municipio A** y el **Municipio B** en sus buscadores.
2. La tabla muestra cada indicador lado a lado, la diferencia y el puesto en el país.
3. La marca de **mejor** aparece solo en indicadores con sentido y cuando la diferencia es de al
   menos 1 punto.
4. **Intercambiar** invierte el orden.

También se llega a esta página desde **Municipios con perfil parecido** en la ficha.

## 7. Consultar precios de compras públicas

1. Escriba un producto en **Producto** (por ejemplo `papel bond`, `cemento` o `guantes`). Al
   escribir aparecen las descripciones más compradas.
2. Elija la **Unidad de medida**. Los precios solo se comparan dentro de la misma unidad (no se
   mezclan "resma" y "unidad").
3. Si quiere, filtre por **Departamento del comprador**.

Qué se obtiene:

| Bloque | Contenido |
|---|---|
| Cifras | **Mediana** (cifra principal), promedio, moda, mínimo y máximo |
| Distribución | Histograma de precios **sin atípicos**, con la mediana marcada |
| Precio de referencia del INE | Precio vigente publicado por el INE para el producto, si existe |
| Por departamento del comprador | Mediana y número de renglones por departamento |
| Adjudicaciones más recientes | Renglones con comprador, fecha y precio. Los atípicos van marcados. Se pueden descargar en CSV |

**Cómo leer estos precios:**

- Son precios **adjudicados** en Guatecompras, no precios de mercado.
- Se usa la **mediana** porque un renglón mal capturado puede disparar el promedio pero no la
  mediana.
- Un precio es **atípico** cuando cae fuera del rango de Tukey (Q1 − 1.5·RIC, Q3 + 1.5·RIC).
- Con menos de 30 renglones se muestra un aviso de cifras poco estables.
- Si un departamento concentra más del 80 % de los renglones (por ejemplo, compras centralizadas
  en la capital), la página lo advierte.
- Si no aparecen resultados, pruebe con menos palabras.

## 8. Rigor y fuentes

Al pie de cada página, el panel **Rigor y fuentes** muestra:

- **Validaciones de la ingesta:** los 17 chequeos que se ejecutaron al construir la base y su
  resultado.
- **Archivos fuente:** cada archivo con licencia, fecha de descarga y huella SHA-256.
- **Equivalencias de códigos municipales:** cómo se relacionan los códigos del censo con los de
  las proyecciones.

## 9. Preguntas frecuentes

**¿De qué año son los datos?** Los indicadores son del Censo 2018. La población 2026 y el
crecimiento son proyecciones del INE. Los precios de Guatecompras van de enero a octubre de 2026
y los de referencia del INE son del 2 de octubre de 2023.

**¿Puedo compartir una ficha?** Sí. Copie la dirección del navegador: cada ficha, comparación y
búsqueda de precios tiene su propio enlace.

**¿Funciona en el celular?** Sí. Las gráficas y tablas se acomodan al ancho de la pantalla.

**¿Necesita internet?** Solo para el fondo de calles del mapa de lugares poblados
(OpenStreetMap). Todo lo demás funciona sin conexión.

**¿Cómo cito los datos?** "Fuente: Instituto Nacional de Estadística (INE), XII Censo Nacional
de Población y VII de Vivienda 2018". Cada indicador y cada CSV indica su fuente exacta.
