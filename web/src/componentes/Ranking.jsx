// Ranking de municipios por un indicador, con filtro por departamento y CSV.
import { useEffect, useState } from 'react'
import { departamentos, ranking } from '../api.js'
import { descargarCsv, valor as fmt } from '../formato.js'

export default function Ranking({ indicador, resaltado }) {
  const [depto, setDepto] = useState('')
  const [deptos, setDeptos] = useState([])
  const [filas, setFilas] = useState(null)
  const [todo, setTodo] = useState(false)

  useEffect(() => {
    departamentos().then(setDeptos)
  }, [])

  useEffect(() => {
    let vigente = true
    ranking(indicador.clave, depto).then((r) => vigente && setFilas(r))
    return () => {
      vigente = false
    }
  }, [indicador.clave, depto])

  if (!filas) return null
  const visibles = todo ? filas : filas.slice(0, 15)
  const explicacion = { 1: 'El puesto 1 es la mejor situación.', '-1': 'El puesto 1 es la peor situación (valor más alto).',
                        0: 'Indicador descriptivo: el puesto 1 es solo el valor más alto.' }[indicador.sentido]

  const csv = () => descargarCsv(`ranking-${indicador.clave}.csv`,
    [{ clave: 'puesto', titulo: 'Puesto' }, { clave: 'codigo', titulo: 'Código INE' }, { clave: 'nombre', titulo: 'Municipio' },
     { clave: 'departamento', titulo: 'Departamento' }, { clave: 'valor', titulo: `${indicador.nombre} (${indicador.unidad})` }],
    filas, indicador.fuente)

  return (
    <section className="tarjeta">
      <h2>Ranking: {indicador.nombre}</h2>
      <p className="nota">{explicacion} Puesto = posición por valor más alto.</p>
      <div className="no-imprimir" style={{ display: 'flex', flexWrap: 'wrap', gap: '.5rem 1rem', marginBottom: '.5rem' }}>
        <label>
          Departamento{' '}
          <select value={depto} onChange={(e) => setDepto(e.target.value)}>
            <option value="">Todo el país</option>
            {deptos.map((d) => <option key={d.codigo} value={d.codigo}>{d.nombre}</option>)}
          </select>
        </label>
        <button type="button" className="boton" onClick={csv}>Descargar CSV</button>
      </div>
      <div className="tabla-desplazable">
        <table>
          <thead><tr><th className="num">Puesto</th><th>Municipio</th><th>Departamento</th><th className="num">Valor</th></tr></thead>
          <tbody>
            {visibles.map((f) => (
              <tr key={f.codigo} style={f.codigo === resaltado ? { background: 'var(--marca-suave)' } : undefined}>
                <td className="num">{f.puesto}</td>
                <td><a href={`#/ficha/municipio/${f.codigo}`}>{f.nombre}</a></td>
                <td>{f.departamento}</td>
                <td className="num">{fmt(f.valor, indicador.unidad)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filas.length > 15 && (
        <button type="button" className="boton no-imprimir" onClick={() => setTodo(!todo)}>
          {todo ? 'Ver solo los primeros 15' : `Ver los ${filas.length}`}
        </button>
      )}
    </section>
  )
}
