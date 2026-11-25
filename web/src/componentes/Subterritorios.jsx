// Territorios "hijos" del elegido, para bajar de nivel:
//   país -> departamentos -> municipios -> lugares poblados (con mapa).
// En un lugar poblado se muestran sus vecinos del mismo municipio, resaltándolo.
import { useEffect, useMemo, useState } from 'react'
import { departamentos, lugaresDe, municipiosDe } from '../api.js'
import { entero } from '../formato.js'
import MapaLugares from './MapaLugares.jsx'

function fuenteDeHijos(nivel, codigo) {
  if (nivel === 'pais') return { pedir: departamentos, hijo: 'departamento', titulo: 'Departamentos' }
  if (nivel === 'departamento') return { pedir: () => municipiosDe(codigo), hijo: 'municipio', titulo: 'Municipios' }
  if (nivel === 'municipio') return { pedir: () => lugaresDe(codigo), hijo: 'lugar_poblado', titulo: 'Lugares poblados' }
  return { pedir: () => lugaresDe(Math.floor(codigo / 1000)), hijo: 'lugar_poblado', titulo: 'Lugares poblados del municipio' }
}

const MOSTRAR = 25
const sinTildes = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export default function Subterritorios({ nivel, codigo, onSeleccionar }) {
  const [filas, setFilas] = useState([])
  const [filtro, setFiltro] = useState('')
  const [todos, setTodos] = useState(false)
  const fuente = fuenteDeHijos(nivel, codigo)

  useEffect(() => {
    let vigente = true
    fuenteDeHijos(nivel, codigo).pedir().then((r) => vigente && setFilas(r))
    return () => {
      vigente = false
    }
  }, [nivel, codigo])

  const visibles = useMemo(() => {
    const f = sinTildes(filtro.trim())
    return f ? filas.filter((r) => sinTildes(r.nombre).includes(f)) : filas
  }, [filas, filtro])

  const total = filas.reduce((s, x) => s + (x.poblacion ?? 0), 0)
  const conMapa = fuente.hijo === 'lugar_poblado'
  const seleccionado = nivel === 'lugar_poblado' ? codigo : null

  return (
    <section className="tarjeta">
      <h2>{fuente.titulo} <span className="nota">({entero(filas.length)})</span></h2>
      {conMapa && filas.length > 0 && (
        <MapaLugares lugares={filas} seleccionado={seleccionado}
                     onSeleccionar={(c) => onSeleccionar({ nivel: 'lugar_poblado', codigo: c })} />
      )}
      {filas.length > MOSTRAR && (
        <input type="search" className="no-imprimir" placeholder="Filtrar por nombre…" value={filtro}
               onChange={(e) => setFiltro(e.target.value)} aria-label="Filtrar por nombre" />
      )}
      <div className="tabla-desplazable">
        <table>
          <thead>
            <tr><th>Nombre</th><th className="num">Población 2018</th><th className="num">{conMapa ? 'Área' : '% del total'}</th></tr>
          </thead>
          <tbody>
            {(todos ? visibles : visibles.slice(0, MOSTRAR)).map((r) => (
              <tr key={r.codigo} style={r.codigo === seleccionado ? { background: 'var(--marca-suave)' } : undefined}>
                <td>
                  {r.es_agrupado ? (
                    <span title="Agrupación del INE de lugares poblados pequeños">{r.nombre}</span>
                  ) : (
                    <a href={`#/ficha/${fuente.hijo}/${r.codigo}`}>{r.nombre}</a>
                  )}
                </td>
                <td className="num">{entero(r.poblacion)}</td>
                <td className="num">{conMapa ? r.area : total ? `${((100 * r.poblacion) / total).toFixed(1)} %` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!todos && visibles.length > MOSTRAR && (
        <button type="button" className="boton no-imprimir" onClick={() => setTodos(true)}>
          Ver los {entero(visibles.length)}
        </button>
      )}
    </section>
  )
}
