// Tema "Compras públicas" de la ficha municipal: lo que adjudicó la
// municipalidad en Guatecompras (monto, procesos, modalidades, meses).
import { useCallback, useEffect, useState } from 'react'
import * as Plot from '@observablehq/plot'
import { comprasMunicipio } from '../api.js'
import { entero, fecha, quetzales, quetzalesCortos } from '../formato.js'
import Grafica from './Grafica.jsx'
import { INE } from '../paleta.js'

const enlaceNog = (nog) => `https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=${nog}`

export default function ComprasMunicipio({ codigo }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true
    comprasMunicipio(codigo).then((d) => vigente && setDatos(d)).catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [codigo])

  const opcionesMes = useCallback(
    (ancho) => ({
      width: ancho,
      height: 200,
      marginLeft: 70,
      y: { label: 'Monto adjudicado', grid: true, tickFormat: (d) => quetzalesCortos(d) },
      x: { label: 'Mes de publicación' },
      marks: [
        Plot.barY(datos?.por_mes ?? [], { x: 'mes', y: 'monto', fill: INE.azul, tip: true,
          title: (d) => `${d.mes}: ${quetzales(d.monto)} en ${d.procesos} procesos` }),
        Plot.ruleY([0]),
      ],
    }),
    [datos],
  )

  if (error) return <p className="aviso">{error}</p>
  if (!datos) return <p>Cargando compras públicas…</p>
  const r = datos.resumen
  const maxModalidad = Math.max(...datos.modalidades.map((m) => m.monto ?? 0), 1)

  return (
    <section className="tarjeta">
      <h2>Compras públicas de la municipalidad</h2>
      <p className="nota">{r.comprador} · procesos publicados de {r.desde} a {r.hasta}</p>
      <dl className="ficha__cifras" style={{ flexWrap: 'wrap', margin: '.5rem 0' }}>
        <div><dt>Procesos</dt><dd>{entero(r.procesos)}</dd></div>
        <div><dt>Adjudicados</dt><dd>{entero(r.adjudicados)}</dd></div>
        <div><dt>Monto adjudicado</dt><dd>{quetzalesCortos(r.monto)}</dd></div>
        <div><dt>Por habitante (pob. 2026)</dt><dd>{quetzales(r.monto_por_habitante)}</dd></div>
      </dl>
      {r.procesos < 30 && <p className="chip chip--aviso">Pocos procesos: interpretar con cuidado</p>}

      <h3>Por modalidad</h3>
      <div className="tabla-desplazable">
        <table>
          <thead><tr><th>Modalidad</th><th className="num">Procesos</th><th className="num">Monto</th><th style={{ width: '30%' }} /></tr></thead>
          <tbody>
            {datos.modalidades.map((m) => (
              <tr key={m.modalidad}>
                <td>{m.modalidad}</td>
                <td className="num">{entero(m.procesos)}</td>
                <td className="num">{quetzales(m.monto)}</td>
                <td><span style={{ display: 'block', height: '.5rem', background: INE.azulBrillante, borderRadius: 3,
                                   width: `${(100 * (m.monto ?? 0)) / maxModalidad}%` }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3>Por mes</h3>
      <Grafica opciones={opcionesMes} etiqueta="Monto adjudicado por mes" />

      <h3>Procesos de mayor monto</h3>
      <div className="tabla-desplazable">
        <table>
          <thead><tr><th>NOG</th><th>Proceso</th><th>Publicado</th><th className="num">Monto</th></tr></thead>
          <tbody>
            {datos.mayores.map((p) => (
              <tr key={p.nog}>
                <td><a href={enlaceNog(p.nog)} target="_blank" rel="noreferrer">{p.nog}</a></td>
                <td>{p.titulo}</td>
                <td>{fecha(p.fecha_publicacion)}</td>
                <td className="num">{quetzales(p.monto_adjudicado)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {datos.avisos.map((a) => <p key={a} className="aviso">{a}</p>)}
      <p className="nota">Fuente: {datos.fuente}. Municipalidad emparejada con el código INE del municipio por nombre y departamento.</p>
    </section>
  )
}
