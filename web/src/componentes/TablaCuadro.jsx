// Cuadro completo del censo para el territorio, con % local y % nacional, y
// descarga en CSV con la fuente (útil para responder solicitudes de información).
import { useEffect, useState } from 'react'
import { catalogoCuadros, cuadro as pedirCuadro } from '../api.js'
import { descargarCsv, entero, porcentaje } from '../formato.js'

const FUENTE = 'INE, XII Censo Nacional de Población y VII de Vivienda 2018'

function descargar(d) {
  const filas = d.filas.map((f) => ({ ...f, categoria: f.categoria ?? '' }))
  descargarCsv(
    `${d.cuadro.cuadro}_${d.lugar.nivel}_${d.lugar.codigo}.csv`,
    [
      { clave: 'grupo', titulo: 'Grupo' },
      { clave: 'categoria', titulo: 'Categoría' },
      { clave: 'valor', titulo: d.cuadro.unidad === 'hogares' ? 'Hogares' : 'Personas' },
      { clave: 'porcentaje', titulo: `% en ${d.lugar.nombre}` },
      { clave: 'porcentaje_pais', titulo: '% nacional' },
    ],
    filas,
    `${FUENTE}. Cuadro ${d.cuadro.cuadro} - ${d.cuadro.titulo}. ${d.lugar.nombre} (código ${d.lugar.codigo}).` +
      (d.cuadro.notas ? ` Notas: ${d.cuadro.notas}` : ''),
  )
}

export default function TablaCuadro({ nivel, codigo }) {
  const [catalogo, setCatalogo] = useState([])
  const [elegido, setElegido] = useState('A1')
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    catalogoCuadros().then(setCatalogo).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    let vigente = true
    pedirCuadro(elegido, nivel, codigo)
      .then((d) => vigente && setDatos(d))
      .catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [elegido, nivel, codigo])

  // Estado derivado: los datos sirven si corresponden al cuadro elegido.
  const listo = datos?.cuadro.cuadro === elegido

  return (
    <section className="tarjeta">
      <h2>Cuadros detallados del censo</h2>
      <div className="no-imprimir" style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={elegido} onChange={(e) => setElegido(e.target.value)} aria-label="Cuadro del censo">
          {catalogo.map((c) => <option key={c.cuadro} value={c.cuadro}>{c.cuadro} · {c.titulo}</option>)}
        </select>
        <button type="button" className="boton" disabled={!listo} onClick={() => descargar(datos)}>
          Descargar CSV
        </button>
      </div>
      {error && <p className="aviso">{error}</p>}
      {!listo && !error && <p>Cargando cuadro…</p>}
      {listo && (
        <>
          <h3 style={{ marginTop: '.75rem' }}>{datos.cuadro.cuadro} · {datos.cuadro.titulo}</h3>
          <div className="tabla-desplazable">
            <table>
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th className="num">{datos.cuadro.unidad === 'hogares' ? 'Hogares' : 'Personas'}</th>
                  <th className="num">%</th>
                  <th className="num">% nacional</th>
                </tr>
              </thead>
              <tbody>
                {datos.filas.map((f, i) => {
                  const nuevoGrupo = f.categoria && f.grupo !== datos.filas[i - 1]?.grupo
                  return [
                    nuevoGrupo && <tr key={`g${f.orden}`}><th colSpan={4}>{f.grupo}</th></tr>,
                    <tr key={f.orden} style={f.orden === 0 ? { fontWeight: 700 } : undefined}>
                      <td>{f.categoria ?? f.grupo}</td>
                      <td className="num">{entero(f.valor)}</td>
                      <td className="num">{porcentaje(f.porcentaje)}</td>
                      <td className="num">{porcentaje(f.porcentaje_pais)}</td>
                    </tr>,
                  ]
                })}
              </tbody>
            </table>
          </div>
          {datos.cuadro.notas && <p className="nota">Nota del INE: {datos.cuadro.notas}</p>}
          <p className="nota">Fuente: {FUENTE}, cuadro {datos.cuadro.cuadro}.</p>
        </>
      )}
    </section>
  )
}
