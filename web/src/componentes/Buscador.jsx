// Buscador de departamentos, municipios y lugares poblados.
// - Espera 250 ms después de la última tecla antes de consultar (debounce),
//   para no mandar una petición por cada letra.
// - Flechas ↑/↓ para moverse, Enter para elegir, Esc para cerrar.
import { useEffect, useRef, useState } from 'react'
import { buscar } from '../api.js'
import { NOMBRE_NIVEL, entero } from '../formato.js'
import './Buscador.css'

export default function Buscador({
  onSeleccionar,
  soloNivel = null, // p. ej. "municipio" en la comparación
  etiqueta = 'Buscar departamento, municipio o lugar poblado',
  id = 'busqueda',
}) {
  const [texto, setTexto] = useState('')
  const [resultados, setResultados] = useState([])
  const [activo, setActivo] = useState(0) // índice resaltado con el teclado
  const [abierto, setAbierto] = useState(false)
  const [error, setError] = useState(null)
  const ultimaConsulta = useRef(0) // para descartar respuestas viejas que lleguen tarde

  useEffect(() => {
    const q = texto.trim()
    // Con menos de 2 letras no se consulta; la lista ya se oculta en el render.
    if (q.length < 2) return
    const consulta = ++ultimaConsulta.current
    const temporizador = setTimeout(() => {
      buscar(q)
        .then((r) => {
          // Si el usuario siguió escribiendo, esta respuesta ya no sirve.
          if (consulta !== ultimaConsulta.current) return
          setResultados(soloNivel ? r.filter((x) => x.nivel === soloNivel) : r)
          setActivo(0)
          setAbierto(true)
          setError(null)
        })
        .catch((e) => setError(e.message))
    }, 250)
    // Limpieza: si `texto` cambia antes de 250 ms, se cancela el temporizador.
    return () => clearTimeout(temporizador)
  }, [texto, soloNivel])

  function elegir(r) {
    onSeleccionar({ nivel: r.nivel, codigo: r.codigo })
    setTexto('')
    setAbierto(false)
  }

  function alPresionarTecla(e) {
    if (!abierto || resultados.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActivo((i) => Math.min(i + 1, resultados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActivo((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      elegir(resultados[activo])
    } else if (e.key === 'Escape') {
      setAbierto(false)
    }
  }

  return (
    <div className="buscador">
      <label htmlFor={id} className="buscador__etiqueta">
        {etiqueta}
      </label>
      <input
        id={id}
        type="search"
        autoComplete="off"
        placeholder="Ej.: Cobán, Xela, Zona 1, San Juan…"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={alPresionarTecla}
        onFocus={() => resultados.length && setAbierto(true)}
        // onBlur con retraso: deja tiempo a que el clic en un resultado se registre.
        onBlur={() => setTimeout(() => setAbierto(false), 150)}
        // Atributos ARIA: los lectores de pantalla anuncian la lista desplegable.
        role="combobox"
        aria-expanded={abierto}
        aria-controls={`${id}-resultados`}
      />
      {error && <p className="buscador__error">{error}</p>}
      {abierto && texto.trim().length >= 2 && (
        <ul id={`${id}-resultados`} className="buscador__lista" role="listbox">
          {resultados.length === 0 && <li className="buscador__vacio">Sin resultados</li>}
          {resultados.map((r, i) => (
            <li
              key={`${r.nivel}-${r.codigo}`}
              role="option"
              aria-selected={i === activo}
              className={i === activo ? 'activo' : ''}
              onMouseEnter={() => setActivo(i)}
              onMouseDown={() => elegir(r)}
            >
              <span className={`insignia insignia--${r.nivel}`}>{NOMBRE_NIVEL[r.nivel]}</span>
              <span className="buscador__nombre">
                {r.nombre}
                <small>{r.contexto}</small>
              </span>
              <span className="buscador__pob">{entero(r.poblacion)} hab.</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
