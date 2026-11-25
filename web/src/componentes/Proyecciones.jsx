// Proyecciones de población 2015-2030 (país, departamento o municipio):
// - línea de la población total por año, con el conteo del Censo 2018 como referencia;
// - pirámide de edades (hombres a la izquierda, mujeres a la derecha) del año elegido.
// Las proyecciones solo existen por municipio; en la ficha de un lugar poblado
// se muestran las de su municipio y se aclara.
import { useCallback, useEffect, useState } from 'react'
import * as Plot from '@observablehq/plot'
import { proyecciones } from '../api.js'
import { entero } from '../formato.js'
import Grafica from './Grafica.jsx'
import './Proyecciones.css'
import { INE } from '../paleta.js'

const ANIO_ACTUAL = 2026

export default function Proyecciones({ nivel, codigo, nombre, esDeLugarPoblado }) {
  const [anio, setAnio] = useState(ANIO_ACTUAL)
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true // evita guardar una respuesta si el componente ya cambió
    proyecciones(nivel, codigo, anio)
      .then((d) => vigente && setDatos(d))
      .catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [nivel, codigo, anio])

  // useCallback: la función solo cambia si cambian los datos (ver Grafica.jsx).
  const opcionesSerie = useCallback(
    (ancho) => ({
      width: ancho,
      height: 240,
      marginLeft: 60,
      // zero: true -> el eje empieza en 0. Sin esto Plot recorta el eje y un
      // crecimiento de 10 % parece enorme (gráfica que induce a error).
      y: { label: 'Población', grid: true, zero: true, tickFormat: (d) => entero(d) },
      x: { label: null, tickFormat: (d) => String(d) },
      marks: [
        Plot.lineY(datos?.serie ?? [], { x: 'anio', y: 'total', stroke: INE.azul, strokeWidth: 2 }),
        Plot.dot(datos?.serie ?? [], { x: 'anio', y: 'total', fill: INE.azul, r: 2.5,
          tip: true, title: (d) => `${d.anio}: ${entero(d.total)} (proyección)` }),
        // El año elegido para la pirámide, resaltado.
        Plot.ruleX([anio], { stroke: INE.naranja, strokeDasharray: '4,3' }),
        // Conteo del censo 2018 como punto aparte (no es parte de la serie proyectada).
        Plot.dot(datos ? [{ anio: 2018, v: datos.poblacion_censada_2018 }] : [],
          { x: 'anio', y: 'v', symbol: 'diamond', r: 5, fill: INE.naranja }),
        Plot.text(datos ? [{ anio: 2018, v: datos.poblacion_censada_2018 }] : [],
          { x: 'anio', y: 'v', text: () => 'Censo 2018', dy: 14, fill: '#c2410c', fontSize: 11 }),
      ],
    }),
    [datos, anio],
  )

  const opcionesPiramide = useCallback(
    (ancho) => {
      // Formato largo: una fila por (grupo de edad, sexo); hombres en negativo.
      const filas = (datos?.piramide ?? []).flatMap((g) => {
        const etiqueta = g.edad_desde === 70 ? '70+' : `${g.edad_desde}-${g.edad_desde + 4}`
        return [
          { edad: etiqueta, orden: g.edad_desde, sexo: 'Hombres', valor: -g.hombres },
          { edad: etiqueta, orden: g.edad_desde, sexo: 'Mujeres', valor: g.mujeres },
        ]
      })
      return {
        width: ancho,
        height: 300,
        marginLeft: 50,
        x: { label: '← Hombres · Mujeres →', tickFormat: (d) => entero(Math.abs(d)) },
        // Eje Y ordenado de menor a mayor edad (de abajo hacia arriba).
        y: { label: 'Edad', domain: [...new Set(filas.sort((a, b) => b.orden - a.orden).map((f) => f.edad))] },
        color: { domain: ['Hombres', 'Mujeres'], range: [INE.azulBrillante, INE.naranja], legend: true },
        marks: [
          Plot.barX(filas, { x: 'valor', y: 'edad', fill: 'sexo', tip: true,
            title: (d) => `${d.sexo} ${d.edad}: ${entero(Math.abs(d.valor))}` }),
          Plot.ruleX([0]),
        ],
      }
    },
    [datos],
  )

  if (error) return <p className="aviso">{error}</p>
  if (!datos) return <p>Cargando proyecciones…</p>

  return (
    <section className="tarjeta proyecciones">
      <h2>Proyección de población 2015-2030 · {nombre}</h2>
      {esDeLugarPoblado && (
        <p className="aviso">Las proyecciones del INE existen solo por municipio; no hay proyección por lugar poblado.</p>
      )}
      <div className="proyecciones__rejilla">
        <Grafica opciones={opcionesSerie} etiqueta={`Población proyectada 2015-2030 de ${nombre}`} />
        <div>
          <label className="proyecciones__anio">
            Pirámide del año <strong>{anio}</strong>
            <input type="range" min="2015" max="2030" value={anio}
                   onChange={(e) => setAnio(Number(e.target.value))} />
          </label>
          <Grafica opciones={opcionesPiramide} etiqueta={`Pirámide de edades ${anio} de ${nombre}`} />
        </div>
      </div>
      <p className="nota">{datos.nota}</p>
      <p className="nota">Fuente: {datos.fuente}.</p>
    </section>
  )
}
