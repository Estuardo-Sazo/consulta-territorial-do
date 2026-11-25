// Componente raíz: encabezado con navegación y buscador, y la página activa.
//
// Navegación con el hash de la URL, p. ej. #/ficha/municipio/1601:
// - cada ficha tiene su propio enlace (se puede guardar o compartir);
// - Atrás/Adelante funcionan;
// - nginx no necesita configuración extra (el hash no llega al servidor).
import { useEffect, useState } from 'react'
import Buscador from './componentes/Buscador.jsx'
import Ficha from './componentes/Ficha.jsx'
import { irA, leerRuta } from './ruta.js'
import './App.css'

const NIVELES = ['pais', 'departamento', 'municipio', 'lugar_poblado']

function fichaDesdeRuta(partes) {
  const [nivel, codigo] = partes
  if (NIVELES.includes(nivel) && /^\d+$/.test(codigo ?? '')) return { nivel, codigo: Number(codigo) }
  return { nivel: 'pais', codigo: 0 }
}

const PAGINAS = [
  { clave: 'ficha', titulo: 'Fichas', ruta: '#/ficha/pais/0' },
]

export default function App() {
  const [ruta, setRuta] = useState(leerRuta)

  useEffect(() => {
    const alCambiar = () => {
      setRuta(leerRuta())
      window.scrollTo({ top: 0 })
    }
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])

  const seleccionar = ({ nivel, codigo }) => irA('ficha', nivel, codigo)
  const ficha = fichaDesdeRuta(ruta.partes)

  return (
    <>
      <header className="app__encabezado">
        <div className="contenedor app__barra">
          <a href="#/ficha/pais/0" className="app__marca">
            <strong>Fichas Territoriales</strong>
            <span>Censo 2018 · proyecciones · compras públicas</span>
          </a>
          <nav className="app__nav" aria-label="Secciones">
            {PAGINAS.map((p) => (
              <a key={p.clave} href={p.ruta} aria-current={ruta.pagina === p.clave ? 'page' : undefined}>
                {p.titulo}
              </a>
            ))}
          </nav>
          <div className="app__buscador">
            <Buscador onSeleccionar={seleccionar} />
          </div>
        </div>
      </header>

      <main className="contenedor">
        {/* key: al cambiar de territorio React monta una Ficha nueva con estado limpio. */}
        <Ficha key={`${ficha.nivel}-${ficha.codigo}`} {...ficha} onSeleccionar={seleccionar} />
      </main>

      <footer className="contenedor app__pie">
        <p className="nota">
          Fuente de los datos: Instituto Nacional de Estadística (INE) de Guatemala, datos.ine.gob.gt ·
          Guatecompras OCDS (Minfin) · Límites municipales: geoBoundaries (CONRED/OCHA). Prototipo del
          equipo Data de Oriente para la Datatón INE 2026.
        </p>
      </footer>
    </>
  )
}
