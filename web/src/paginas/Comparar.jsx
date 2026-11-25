// Página "Comparar": dos municipios lado a lado. Ruta: #/comparar/{a}/{b}
//
// Por indicador: valor de cada uno, diferencia y puesto en el país. La marca
// "mejor" la decide la API según el SENTIDO y solo si la diferencia es de al
// menos 1 punto; en los descriptivos no se marca ninguno.
import { useEffect, useState } from 'react'
import { comparar } from '../api.js'
import { irA } from '../ruta.js'
import Buscador from '../componentes/Buscador.jsx'
import { descargarCsv, valor as fmt } from '../formato.js'

export default function Comparar({ partes }) {
  const a = /^\d+$/.test(partes[0] ?? '') ? Number(partes[0]) : 1601
  const b = /^\d+$/.test(partes[1] ?? '') ? Number(partes[1]) : 901
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true
    comparar(a, b).then((d) => {
      if (!vigente) return
      setError(null)
      setDatos(d)
      document.title = `${d.a.nombre} vs ${d.b.nombre} · Fichas Territoriales`
    }).catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [a, b])

  const csv = () => descargarCsv(`comparacion-${a}-${b}.csv`,
    [{ clave: 'nombre', titulo: 'Indicador' }, { clave: 'unidad', titulo: 'Unidad' },
     { clave: 'a', titulo: datos.a.nombre }, { clave: 'b', titulo: datos.b.nombre },
     { clave: 'diferencia', titulo: 'Diferencia (A - B)' }, { clave: 'puesto_a', titulo: `Puesto ${datos.a.nombre}` },
     { clave: 'puesto_b', titulo: `Puesto ${datos.b.nombre}` }],
    datos.indicadores, 'INE, Censo 2018 y proyecciones 2015-2030')

  const marca = (ind, cod) => (ind.mejor === cod ? <span className="chip chip--bueno">mejor</span> : null)

  return (
    <>
      <section className="tarjeta">
        <h1>Comparar dos municipios</h1>
        <div className="rejilla no-imprimir">
          <Buscador id="comparar-a" soloNivel="municipio" etiqueta="Municipio A"
                    onSeleccionar={({ codigo }) => irA('comparar', codigo, b)} />
          <Buscador id="comparar-b" soloNivel="municipio" etiqueta="Municipio B"
                    onSeleccionar={({ codigo }) => irA('comparar', a, codigo)} />
        </div>
        {error && <p className="aviso">{error}</p>}
        {datos && (
          <p>
            <strong>A:</strong> <a href={`#/ficha/municipio/${a}`}>{datos.a.nombre}</a>, {datos.a.departamento} ·{' '}
            <strong>B:</strong> <a href={`#/ficha/municipio/${b}`}>{datos.b.nombre}</a>, {datos.b.departamento}{' '}
            <button type="button" className="boton no-imprimir" onClick={() => irA('comparar', b, a)}>Intercambiar</button>
          </p>
        )}
      </section>

      {datos && (
        <section className="tarjeta">
          <div className="tabla-desplazable">
            <table>
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th className="num">{datos.a.nombre}</th>
                  <th className="num">{datos.b.nombre}</th>
                  <th className="num">Diferencia (A − B)</th>
                  <th className="num">Puesto en el país (A / B)</th>
                </tr>
              </thead>
              <tbody>
                {datos.indicadores.map((i) => (
                  <tr key={i.clave}>
                    <td>
                      {i.nombre}
                      {i.sentido === 0 && <span className="nota"> · descriptivo</span>}
                      {i.pocos_casos && <span className="chip chip--aviso"> pocos casos</span>}
                    </td>
                    <td className="num">{fmt(i.a, i.unidad)} {marca(i, a)}</td>
                    <td className="num">{fmt(i.b, i.unidad)} {marca(i, b)}</td>
                    <td className="num">{i.diferencia == null ? '—' : `${i.diferencia > 0 ? '+' : ''}${fmt(i.diferencia, i.unidad)}`}</td>
                    <td className="num">{i.puesto_a ?? '—'} / {i.puesto_b ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="nota">
            "Mejor" según el sentido del indicador y solo si la diferencia es de 1 punto o más. Los indicadores
            descriptivos (p. ej. % de mujeres) no se juzgan. Puesto 1 = valor más alto de los 340 municipios.
          </p>
          <div className="no-imprimir" style={{ display: 'flex', gap: '.5rem' }}>
            <button type="button" className="boton" onClick={csv}>Descargar CSV</button>
            <button type="button" className="boton" onClick={() => window.print()}>Imprimir / PDF</button>
          </div>
        </section>
      )}
    </>
  )
}
