// Tarjetas de indicadores agrupadas por tema. Cada tarjeta muestra:
// - el valor del territorio, con su universo (de cuántas personas u hogares sale);
// - barras de comparación con los niveles superiores (municipio, departamento, país);
// - el puesto entre los 340 municipios (solo fichas de municipio);
// - el sentido (más alto es mejor / peor / descriptivo) y el aviso de pocos casos.
import { useState } from 'react'
import { NOMBRE_NIVEL, entero, valor } from '../formato.js'
import './Indicadores.css'

const SENTIDO = {
  1: { texto: 'Más alto es mejor', clase: 'chip--bueno' },
  '-1': { texto: 'Más alto es peor', clase: 'chip--malo' },
  0: { texto: 'Descriptivo', clase: '' },
}

function Barra({ etiqueta, v, max, unidad, propio }) {
  const ancho = v == null || !max ? 0 : Math.max(2, (100 * v) / max)
  return (
    <div className={`ind__barra ${propio ? 'ind__barra--propio' : ''}`}>
      <span className="ind__barra-etiqueta">{etiqueta}</span>
      <span className="ind__barra-pista"><span style={{ width: `${ancho}%` }} /></span>
      <span className="ind__barra-valor">{valor(v, unidad)}</span>
    </div>
  )
}

function Tarjeta({ ind, nombre }) {
  const [verDefinicion, setVerDefinicion] = useState(false)
  const comparaciones = Object.entries(ind.comparacion ?? {})
  const porcentual = ind.unidad !== 'personas'
  const max = Math.max(ind.valor ?? 0, ...comparaciones.map(([, v]) => v ?? 0), ind.unidad === '%' ? 100 : 0)
  const s = SENTIDO[ind.sentido]
  return (
    <div className="ind tarjeta">
      <div className="ind__cabeza">
        <h3>{ind.nombre}</h3>
        <span className={`chip ${s.clase}`} title={s.texto}>{s.texto}</span>
      </div>
      <p className="ind__valor">{valor(ind.valor, ind.unidad)}</p>
      {ind.universo != null && porcentual && (
        <p className="nota">sobre {entero(ind.universo)} {ind.tema === 'Servicios del hogar' ? 'hogares' : 'personas'}</p>
      )}
      {ind.pocos_casos && (
        <p className="chip chip--aviso">Pocos casos: universo menor de 30, el porcentaje es inestable</p>
      )}
      {porcentual && comparaciones.length > 0 && (
        <div className="ind__comparacion">
          <Barra etiqueta={nombre} v={ind.valor} max={max} unidad={ind.unidad} propio />
          {comparaciones.map(([nivel, v]) => (
            <Barra key={nivel} etiqueta={NOMBRE_NIVEL[nivel]} v={v} max={max} unidad={ind.unidad} />
          ))}
        </div>
      )}
      {ind.posicion && (
        <p className="nota">
          Puesto {ind.posicion.pais} de {ind.posicion.de_pais} en el país · {ind.posicion.departamento} de{' '}
          {ind.posicion.de_departamento} en el departamento (1 = valor más alto)
        </p>
      )}
      <button type="button" className="ind__def no-imprimir" onClick={() => setVerDefinicion((x) => !x)}>
        {verDefinicion ? 'Ocultar definición' : '¿Cómo se calcula?'}
      </button>
      {verDefinicion && <p className="nota">{ind.definicion} Fuente: {ind.fuente}.</p>}
    </div>
  )
}

export default function Indicadores({ indicadores, nombre }) {
  // Agrupa por tema respetando el orden del catálogo.
  const temas = []
  for (const ind of indicadores) {
    let t = temas.find((x) => x.tema === ind.tema)
    if (!t) temas.push((t = { tema: ind.tema, lista: [] }))
    t.lista.push(ind)
  }
  return (
    <section className="ficha__seccion">
      {temas.map((t) => (
        <div key={t.tema}>
          <h2>{t.tema}</h2>
          <div className="rejilla">
            {t.lista.map((ind) => <Tarjeta key={ind.clave} ind={ind} nombre={nombre} />)}
          </div>
        </div>
      ))}
    </section>
  )
}
