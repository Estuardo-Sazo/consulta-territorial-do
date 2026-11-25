// Página "Precios": cuánto pagó el Estado por un producto (Guatecompras) y el
// precio de referencia del INE al lado. Ruta: #/precios/{texto}/{unidad}/{depto}
//
// La cifra principal es la MEDIANA: un solo renglón mal capturado (p. ej. un
// monto total puesto como unitario) dispara el promedio pero no la mediana.
import { useCallback, useEffect, useState } from 'react'
import * as Plot from '@observablehq/plot'
import { departamentos, precios, sugerenciasPrecios } from '../api.js'
import { irA } from '../ruta.js'
import Grafica from '../componentes/Grafica.jsx'
import { descargarCsv, entero, fecha, quetzales } from '../formato.js'

const EJEMPLOS = ['papel bond', 'cemento', 'guantes', 'tóner', 'gasolina', 'arroz']

function Cifra({ titulo, valor, nota }) {
  return (
    <div className="tarjeta" style={{ padding: '.75rem 1rem', margin: 0 }}>
      <div className="nota">{titulo}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{valor}</div>
      {nota && <div className="nota">{nota}</div>}
    </div>
  )
}

export default function Precios({ partes }) {
  const [texto, unidad, depto] = [partes[0] ?? '', partes[1] ?? '', partes[2] ?? '']
  const [borrador, setBorrador] = useState(texto)
  const [sugerencias, setSugerencias] = useState([])
  const [deptos, setDeptos] = useState([])
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.title = 'Precios · Fichas Territoriales'
    departamentos().then(setDeptos)
  }, [])

  // Autocompletar con las descripciones más compradas (espera 300 ms).
  useEffect(() => {
    if (borrador.trim().length < 3) return
    const t = setTimeout(() => sugerenciasPrecios(borrador.trim()).then(setSugerencias).catch(() => {}), 300)
    return () => clearTimeout(t)
  }, [borrador])

  useEffect(() => {
    if (texto.length < 3) return
    let vigente = true
    precios(texto, unidad, depto).then((d) => {
      if (!vigente) return
      setError(null)
      setDatos(d)
    }).catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [texto, unidad, depto])

  const e = datos?.estadisticas
  // Histograma sin atípicos: con ellos la escala se estira y no se ve nada.
  const opciones = useCallback(
    (ancho) => {
      const lim = e?.limite_atipico_superior ?? Infinity
      const xs = (datos?.precios ?? []).filter((p) => p <= lim)
      return {
        width: ancho,
        height: 220,
        x: { label: `Precio unitario (Q por ${datos?.unidad ?? ''})` },
        y: { label: 'Renglones', grid: true },
        marks: [
          Plot.rectY(xs, Plot.binX({ y: 'count' }, { x: (d) => d, fill: '#1d4e89', fillOpacity: 0.7, thresholds: 25 })),
          Plot.ruleX(e ? [e.mediana] : [], { stroke: '#c2571a', strokeWidth: 2 }),
          Plot.text(e ? [e.mediana] : [], { x: (d) => d, frameAnchor: 'top', dy: 4, dx: 6, textAnchor: 'start',
                                            text: (d) => `mediana ${quetzales(d)}`, fill: '#c2571a' }),
          Plot.ruleY([0]),
        ],
      }
    },
    [datos, e],
  )

  const buscarAhora = (ev) => {
    ev.preventDefault()
    if (borrador.trim().length >= 3) irA('precios', borrador.trim())
  }

  // El departamento del comprador es su sede: IGSS y Salud compran casi todo
  // desde la capital. Si un departamento domina, se avisa.
  const totalDeptos = datos?.por_departamento.reduce((s, d) => s + d.n, 0) ?? 0
  const dominante = datos?.por_departamento.find((d) => totalDeptos && d.n / totalDeptos > 0.8)

  const csv = () => descargarCsv(`precios-${texto}.csv`,
    [{ clave: 'nog', titulo: 'NOG' }, { clave: 'fecha_adjudicacion', titulo: 'Fecha de adjudicación' },
     { clave: 'descripcion', titulo: 'Descripción' }, { clave: 'cantidad', titulo: 'Cantidad' },
     { clave: 'monto', titulo: 'Monto adjudicado (Q)' }, { clave: 'precio_unitario', titulo: `Precio unitario (Q por ${datos.unidad})` },
     { clave: 'comprador', titulo: 'Comprador' }, { clave: 'departamento', titulo: 'Departamento del comprador' },
     { clave: 'modalidad', titulo: 'Modalidad' }],
    datos.renglones, datos.fuentes[0])

  return (
    <>
      <section className="tarjeta">
        <h1>Precios de compras públicas</h1>
        <p className="nota">
          Cuánto pagó el Estado por unidad en Guatecompras y, al lado, el precio de referencia publicado por el INE.
        </p>
        <form onSubmit={buscarAhora} className="no-imprimir" style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          <label htmlFor="producto" className="nota" style={{ width: '100%' }}>Producto</label>
          <input id="producto" list="sugerencias-precios" value={borrador} minLength={3} required
                 onChange={(ev) => setBorrador(ev.target.value)} placeholder="Ej.: papel bond, cemento, guantes"
                 style={{ flex: '1 1 220px', padding: '.5rem .7rem', borderRadius: 6, border: '1px solid var(--borde)' }} />
          <datalist id="sugerencias-precios">
            {sugerencias.map((s) => <option key={s.descripcion} value={s.descripcion}>{s.n} renglones</option>)}
          </datalist>
          <button type="submit" className="boton boton--lleno">Buscar</button>
        </form>
        <p className="nota no-imprimir">
          Ejemplos:{' '}
          {EJEMPLOS.map((x, i) => <span key={x}>{i > 0 && ' · '}<a href={`#/precios/${encodeURIComponent(x)}`}>{x}</a></span>)}
        </p>
      </section>

      {error && <p className="aviso">{error}</p>}
      {texto && datos && !e && <p className="aviso">No hay precios unitarios para “{texto}”. Prueba con menos palabras.</p>}

      {datos && e && (
        <>
          <section className="tarjeta">
            <h2>“{datos.consulta}” · {datos.unidad}</h2>
            <div className="no-imprimir" style={{ display: 'flex', flexWrap: 'wrap', gap: '.5rem 1rem', marginBottom: '.75rem' }}>
              <label>
                Unidad de medida{' '}
                <select value={datos.unidad} onChange={(ev) => irA('precios', texto, ev.target.value, depto)}>
                  {datos.unidades.map((u) => <option key={u.unidad} value={u.unidad}>{u.unidad} ({u.n})</option>)}
                </select>
              </label>
              <label>
                Departamento del comprador{' '}
                <select value={depto} onChange={(ev) => irA('precios', texto, datos.unidad, ev.target.value)}>
                  <option value="">Todos</option>
                  {deptos.map((d) => <option key={d.codigo} value={d.codigo}>{d.nombre}</option>)}
                </select>
              </label>
            </div>
            {e.pocos_casos && (
              <p className="aviso">Solo {e.n} renglones (menos de 30): las cifras son poco estables.</p>
            )}
            <div className="rejilla">
              <Cifra titulo="Mediana (cifra principal)" valor={quetzales(e.mediana)} nota={`${entero(e.n)} renglones`} />
              <Cifra titulo="Promedio" valor={quetzales(e.promedio)}
                     nota={`sin ${e.atipicos} atípicos: ${quetzales(e.promedio_sin_atipicos)}`} />
              <Cifra titulo="Moda (al quetzal)" valor={e.moda == null ? 'Sin moda' : quetzales(e.moda)}
                     nota={e.moda_veces ? `se repite ${e.moda_veces} veces` : 'ningún precio se repite'} />
              <Cifra titulo="Rango central (50 %)" valor={`${quetzales(e.q1)} – ${quetzales(e.q3)}`}
                     nota={`mín. ${quetzales(e.minimo)} · máx. ${quetzales(e.maximo)}`} />
            </div>
            <h3>Distribución</h3>
            <Grafica opciones={opciones} etiqueta={`Distribución de precios unitarios de ${datos.consulta}`} />
            <p className="nota">
              Sin los {e.atipicos} valores atípicos (más de {quetzales(e.limite_atipico_superior)} o muy por debajo del
              rango central, regla de Tukey). Adjudicaciones del {fecha(datos.periodo.desde)} al {fecha(datos.periodo.hasta)}.
            </p>
          </section>

          <section className="tarjeta">
            <h2>Precio de referencia del INE</h2>
            {datos.referencias_ine.length ? (
              <>
                <p className="nota">
                  Publicados por la Dirección de Precios e Índices de Referencia. Cada uno tiene su fecha y su
                  presentación: compárelos solo si la presentación coincide con la unidad de arriba.
                </p>
                {datos.referencias_ine[0].coincidencia === 'caracteristicas' && (
                  <p className="aviso">
                    Ningún producto del INE se llama así; se muestran los que lo mencionan en sus características
                    (pueden ser productos distintos).
                  </p>
                )}
                <div className="tabla-desplazable">
                  <table>
                    <thead><tr><th>Producto</th><th>Presentación</th><th className="num">Precio</th><th>Fecha del precio</th><th>NOG</th></tr></thead>
                    <tbody>
                      {datos.referencias_ine.slice(0, 10).map((r, i) => (
                        <tr key={`${r.nog}-${i}`}>
                          <td title={r.caracteristicas}>{r.producto}</td>
                          <td>{r.presentacion}</td>
                          <td className="num">{quetzales(r.precio)}</td>
                          <td>{fecha(r.fecha_precio)}</td>
                          <td>{r.nog}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : <p className="nota">El INE no publica precio de referencia para este producto.</p>}
          </section>

          <section className="tarjeta">
            <h2>Por departamento del comprador</h2>
            {dominante && (
              <p className="aviso">
                {Math.round((100 * dominante.n) / totalDeptos)} % de los renglones son de entidades con sede en{' '}
                {dominante.departamento}: instituciones como el IGSS o Salud Pública compran desde la capital aunque
                entreguen en otros departamentos.
              </p>
            )}
            <div className="tabla-desplazable">
              <table>
                <thead><tr><th>Departamento</th><th className="num">Renglones</th><th className="num">Mediana</th></tr></thead>
                <tbody>
                  {datos.por_departamento.map((d) => (
                    <tr key={d.cod_depto ?? 'sd'}>
                      <td>{d.departamento ?? 'Sin dato'}</td>
                      <td className="num">{entero(d.n)}{d.pocos_casos && <span className="chip chip--aviso"> pocos casos</span>}</td>
                      <td className="num">{quetzales(d.mediana)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="tarjeta">
            <h2>Adjudicaciones más recientes</h2>
            <div className="tabla-desplazable">
              <table>
                <thead><tr><th>Fecha</th><th>Descripción</th><th className="num">Cantidad</th><th className="num">Precio unitario</th><th>Comprador</th><th>NOG</th></tr></thead>
                <tbody>
                  {datos.renglones.map((r) => (
                    <tr key={r.nog}>
                      <td>{fecha(r.fecha_adjudicacion)}</td>
                      <td>{r.descripcion}</td>
                      <td className="num">{entero(r.cantidad)}</td>
                      <td className="num">
                        {quetzales(r.precio_unitario)}
                        {r.precio_unitario > e.limite_atipico_superior && <span className="chip chip--aviso"> atípico</span>}
                      </td>
                      <td>{r.comprador}</td>
                      <td>
                        <a href={`https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=${r.nog}`}
                           target="_blank" rel="noreferrer">{r.nog}</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" className="boton no-imprimir" onClick={csv}>Descargar CSV (40 más recientes)</button>
          </section>

          <section className="tarjeta">
            <h2>Cómo leer estos precios</h2>
            <ul>{datos.avisos.map((a) => <li key={a}>{a}</li>)}</ul>
            <p className="nota">Fuentes: {datos.fuentes.join(' · ')}.</p>
          </section>
        </>
      )}
    </>
  )
}
