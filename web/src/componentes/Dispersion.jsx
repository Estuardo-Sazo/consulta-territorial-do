// Diagrama de dispersión entre dos indicadores municipales, con r de Pearson
// y la advertencia de que correlación no es causalidad.
import { useCallback, useEffect, useState } from 'react'
import * as Plot from '@observablehq/plot'
import { dispersion } from '../api.js'
import Grafica from './Grafica.jsx'
import { INE } from '../paleta.js'

export default function Dispersion({ catalogo, x, y, onCambiar, resaltado }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true
    dispersion(x, y).then((d) => vigente && setDatos(d)).catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [x, y])

  const opciones = useCallback(
    (ancho) => {
      const puntos = datos?.puntos ?? []
      const marca = puntos.filter((p) => p.codigo === resaltado)
      return {
        width: ancho,
        height: Math.min(420, Math.max(300, ancho * 0.6)),
        grid: true,
        x: { label: datos?.x },
        y: { label: datos?.y },
        marks: [
          Plot.dot(puntos, { x: 'x', y: 'y', r: 3.5, fill: INE.azulBrillante, fillOpacity: 0.45, tip: true,
                             channels: { Municipio: 'nombre', Departamento: 'departamento' } }),
          // Recta de tendencia (mínimos cuadrados): solo ilustra la dirección de r.
          Plot.linearRegressionY(puntos, { x: 'x', y: 'y', stroke: INE.naranja }),
          Plot.dot(marca, { x: 'x', y: 'y', r: 7, stroke: INE.azul, strokeWidth: 2 }),
          Plot.text(marca, { x: 'x', y: 'y', text: 'nombre', dy: -12, fontWeight: 'bold' }),
        ],
      }
    },
    [datos, resaltado],
  )

  const selector = (eje, valor) => (
    <label>
      Eje {eje}{' '}
      <select value={valor} onChange={(e) => onCambiar(eje === 'X' ? e.target.value : x, eje === 'Y' ? e.target.value : y)}>
        {catalogo.map((i) => <option key={i.clave} value={i.clave}>{i.nombre}</option>)}
      </select>
    </label>
  )

  return (
    <section className="tarjeta">
      <h2>¿Se mueven juntos? Dispersión entre indicadores</h2>
      <div className="no-imprimir" style={{ display: 'flex', flexWrap: 'wrap', gap: '.5rem 1rem', marginBottom: '.5rem' }}>
        {selector('X', x)}
        {selector('Y', y)}
      </div>
      {error && <p className="aviso">{error}</p>}
      {datos && (
        <>
          <p>
            <strong>r = {datos.r?.toFixed(2) ?? '—'}</strong> ({datos.lectura}) · {datos.n} municipios.
            Cada punto es un municipio; la línea naranja es la tendencia.
          </p>
          <Grafica opciones={opciones} etiqueta={`Dispersión de ${datos.x} contra ${datos.y}`} />
          <p className="aviso">{datos.advertencia}</p>
        </>
      )}
    </section>
  )
}
