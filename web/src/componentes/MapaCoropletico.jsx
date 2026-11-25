// Mapa coroplético de los 340 municipios con Leaflet (mismo patrón useRef que
// MapaLugares: Leaflet maneja su propio DOM dentro de un <div> de React).
//
// Color por quintiles: cada tono agrupa ~68 municipios, así un municipio
// extremo no aplasta la escala. La paleta depende del SENTIDO:
//   1  más alto es mejor  -> azul INE (oscuro = mejor)
//  -1  más alto es peor   -> naranja INE (oscuro = peor)
//   0  descriptivo        -> gris azulado (no se juzga)
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { valor as fmt } from '../formato.js'
import { ESCALAS, INE } from '../paleta.js'

const PALETAS = ESCALAS
const SIN_DATO = '#ffffff' // blanco: no se confunde con ningún tono de las escalas

/** Cortes de quintil de una lista de valores (4 límites). */
function cortes(valores) {
  const xs = valores.filter((v) => v != null).sort((a, b) => a - b)
  if (!xs.length) return []
  return [0.2, 0.4, 0.6, 0.8].map((q) => xs[Math.floor(q * (xs.length - 1))])
}

function colorDe(v, limites, paleta) {
  if (v == null) return SIN_DATO
  const i = limites.findIndex((c) => v <= c)
  return paleta[i === -1 ? paleta.length - 1 : i]
}

export default function MapaCoropletico({ geojson, datos, seleccionado, onSeleccionar }) {
  const contenedor = useRef(null)
  const mapa = useRef(null)
  const capa = useRef(null)
  const alSeleccionar = useRef(onSeleccionar)
  useEffect(() => {
    alSeleccionar.current = onSeleccionar
  })

  useEffect(() => {
    // Sin teselas de fondo: los polígonos bastan y así funciona sin internet.
    mapa.current = L.map(contenedor.current, { scrollWheelZoom: false, zoomSnap: 0.25, attributionControl: true })
    mapa.current.attributionControl.addAttribution('Límites: geoBoundaries (CC BY 3.0 IGO)')
    return () => {
      mapa.current.remove()
      mapa.current = null
    }
  }, [])

  useEffect(() => {
    if (!geojson || !datos) return
    const porCodigo = new Map(datos.valores.map((v) => [v.codigo, v]))
    const limites = cortes(datos.valores.map((v) => v.valor))
    const paleta = PALETAS[datos.indicador.sentido]
    const unidad = datos.indicador.unidad
    capa.current?.remove()
    capa.current = L.geoJSON(geojson, {
      style: (f) => {
        const d = porCodigo.get(f.properties.codigo)
        const elegido = f.properties.codigo === seleccionado
        return { fillColor: colorDe(d?.valor, limites, paleta), fillOpacity: 0.9,
                 // Contorno del elegido: amarillo sobre la escala azul, azul oscuro sobre las demás.
                 color: elegido ? (datos.indicador.sentido === 1 ? INE.amarillo : INE.azul) : '#fff', weight: elegido ? 3.5 : 0.5 }
      },
      onEachFeature: (f, capaPoligono) => {
        const d = porCodigo.get(f.properties.codigo)
        // textContent: los nombres no se interpretan como HTML.
        const div = document.createElement('div')
        const b = document.createElement('strong')
        b.textContent = d ? `${d.nombre}, ${d.departamento}` : f.properties.nombre
        div.append(b, document.createElement('br'), d ? fmt(d.valor, unidad) : 'Sin dato')
        if (d?.pocos_casos) div.append(' · pocos casos')
        capaPoligono.bindTooltip(div, { sticky: true })
        capaPoligono.on('click', () => alSeleccionar.current?.(f.properties.codigo))
      },
    }).addTo(mapa.current)
    if (!mapa.current._loaded) mapa.current.fitBounds(capa.current.getBounds())
  }, [geojson, datos, seleccionado])

  return <div ref={contenedor} style={{ height: 460, borderRadius: 'var(--radio)', background: 'var(--marca-suave)' }}
              role="img" aria-label="Mapa de municipios coloreado por el indicador elegido" />
}

/** Leyenda de quintiles para acompañar al mapa. */
export function LeyendaMapa({ datos }) {
  if (!datos) return null
  const limites = cortes(datos.valores.map((v) => v.valor))
  const paleta = PALETAS[datos.indicador.sentido]
  const u = datos.indicador.unidad
  const rangos = paleta.map((c, i) => [c, i === 0 ? `≤ ${fmt(limites[0], u)}` :
    i === paleta.length - 1 ? `> ${fmt(limites[i - 1], u)}` : `${fmt(limites[i - 1], u)} – ${fmt(limites[i], u)}`])
  const sentido = { 1: 'Más oscuro = mejor situación', '-1': 'Más oscuro = peor situación',
                    0: 'Indicador descriptivo: el color no juzga' }[datos.indicador.sentido]
  return (
    <div className="nota" style={{ display: 'flex', flexWrap: 'wrap', gap: '.4rem 1rem', alignItems: 'center' }}>
      {rangos.map(([c, t]) => (
        <span key={c} style={{ display: 'inline-flex', alignItems: 'center', gap: '.3rem' }}>
          <span style={{ width: 14, height: 14, background: c, borderRadius: 3, display: 'inline-block' }} />{t}
        </span>
      ))}
      <span><span style={{ width: 14, height: 14, background: SIN_DATO, border: '1px solid var(--borde)', borderRadius: 3, display: 'inline-block',
                           verticalAlign: 'middle' }} /> sin dato</span>
      <strong>{sentido}</strong> · quintiles (≈ 68 municipios por color)
    </div>
  )
}
