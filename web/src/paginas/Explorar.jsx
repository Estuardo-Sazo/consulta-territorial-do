// Página "Explorar": compara los 340 municipios a la vez.
// Ruta: #/explorar/{indicador}/{indicadorY}/{municipio resaltado}
import { useEffect, useState } from 'react'
import { geojson as pedirGeojson, indicadores, mapa } from '../api.js'
import { irA } from '../ruta.js'
import Dispersion from '../componentes/Dispersion.jsx'
import MapaCoropletico, { LeyendaMapa } from '../componentes/MapaCoropletico.jsx'
import Ranking from '../componentes/Ranking.jsx'

export default function Explorar({ partes }) {
  const [catalogo, setCatalogo] = useState(null)
  const [geo, setGeo] = useState(null)
  const [datos, setDatos] = useState(null)
  const clave = partes[0] || 'alfabetismo'
  const claveY = partes[1] || 'internet'
  const resaltado = partes[2] ? Number(partes[2]) : null

  useEffect(() => {
    document.title = 'Explorar municipios · Fichas Territoriales'
    indicadores().then(setCatalogo)
    pedirGeojson().then(setGeo)
  }, [])

  useEffect(() => {
    let vigente = true
    mapa(clave).then((d) => vigente && setDatos(d))
    return () => {
      vigente = false
    }
  }, [clave])

  if (!catalogo) return <p>Cargando indicadores…</p>
  // Solo indicadores que existen a nivel municipal (todos los del catálogo).
  const municipales = catalogo.filter((i) => i.niveles.includes('municipio'))
  const indicador = municipales.find((i) => i.clave === clave) ?? municipales[0]
  const ir = (k = clave, ky = claveY, cod = resaltado) => irA('explorar', k, ky, ...(cod ? [cod] : []))
  const elegido = datos?.valores.find((v) => v.codigo === resaltado)

  return (
    <>
      <section className="tarjeta">
        <h1>Explorar los 340 municipios</h1>
        <label className="no-imprimir">
          Indicador{' '}
          <select value={indicador.clave} onChange={(e) => ir(e.target.value)}>
            {municipales.map((i) => <option key={i.clave} value={i.clave}>{i.tema} · {i.nombre}</option>)}
          </select>
        </label>
        <p className="nota">{indicador.definicion} Fuente: {indicador.fuente}.</p>
        <MapaCoropletico geojson={geo} datos={datos} seleccionado={resaltado}
                         onSeleccionar={(cod) => ir(clave, claveY, cod)} />
        <LeyendaMapa datos={datos} />
        {elegido ? (
          <p>
            <strong>{elegido.nombre}, {elegido.departamento}</strong> ·{' '}
            <a href={`#/ficha/municipio/${elegido.codigo}`}>Abrir su ficha</a>
          </p>
        ) : <p className="nota no-imprimir">Haz clic en un municipio para resaltarlo en el ranking y la dispersión.</p>}
      </section>
        <Ranking indicador={indicador} resaltado={resaltado} />
        <Dispersion catalogo={municipales} x={indicador.clave} y={claveY} resaltado={resaltado}
                    onCambiar={(x, y) => ir(x, y)} />
    </>
  )
}
