// Ficha territorial: reúne las secciones de un territorio (se amplía en los
// siguientes commits).
import { useEffect, useState } from 'react'
import { ficha as pedirFicha } from '../api.js'
import { NOMBRE_NIVEL, entero } from '../formato.js'
import Hallazgos from './Hallazgos.jsx'
import Indicadores from './Indicadores.jsx'
import Parecidos from './Parecidos.jsx'
import Proyecciones from './Proyecciones.jsx'
import Subterritorios from './Subterritorios.jsx'
import TablaCuadro from './TablaCuadro.jsx'
import './Ficha.css'

export default function Ficha({ nivel, codigo, onSeleccionar }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true // evita guardar una respuesta que llegó después de cambiar de ficha
    pedirFicha(nivel, codigo)
      .then((d) => {
        if (!vigente) return
        setDatos(d)
        // El título de la pestaña es también el nombre sugerido del PDF.
        document.title = `${d.lugar.nombre} · Fichas Territoriales`
      })
      .catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [nivel, codigo])

  if (error) return <p className="aviso">{error}</p>
  if (!datos) return <p>Cargando ficha…</p>
  const { lugar, jerarquia } = datos
  // Las proyecciones no existen por lugar poblado: se muestran las de su municipio.
  const esLp = nivel === 'lugar_poblado'
  const proy = esLp
    ? { nivel: 'municipio', codigo: Math.floor(codigo / 1000), nombre: jerarquia[0].nombre }
    : { nivel, codigo, nombre: lugar.nombre }

  return (
    <article className="ficha">
      <nav className="ficha__ruta" aria-label="Ubicación">
        {[...jerarquia].reverse().map((j) => (
          <span key={j.nivel}><a href={`#/ficha/${j.nivel}/${j.codigo}`}>{j.nombre}</a> › </span>
        ))}
        <span aria-current="page">{lugar.nombre}</span>
      </nav>

      <header className="ficha__encabezado tarjeta">
        <div>
          <span className="chip">{NOMBRE_NIVEL[nivel]}</span>
          <h1>{lugar.nombre}</h1>
          <p className="nota">{lugar.contexto} · Código INE {codigo}</p>
        </div>
        <dl className="ficha__cifras">
          <div><dt>Población censada 2018</dt><dd>{entero(datos.poblacion_censada)}</dd></div>
          <div><dt>Hogares 2018</dt><dd>{entero(datos.hogares)}</dd></div>
        </dl>
        <button type="button" className="boton no-imprimir" onClick={() => window.print()}>
          Imprimir / guardar PDF
        </button>
      </header>

      {lugar.es_agrupado && (
        <p className="aviso">
          “Otros lugares poblados” es una agrupación del INE de lugares pequeños del municipio, no un lugar único.
        </p>
      )}

      <Hallazgos texto={datos.texto} destacaRetos={datos.destaca_retos} />

      <Indicadores indicadores={datos.indicadores} nombre={lugar.nombre} />

      <Parecidos codigo={codigo} parecidos={datos.parecidos} />

      <Subterritorios nivel={nivel} codigo={codigo} onSeleccionar={onSeleccionar} />

      <Proyecciones {...proy} esDeLugarPoblado={esLp} />

      <TablaCuadro nivel={nivel} codigo={codigo} />
    </article>
  )
}
