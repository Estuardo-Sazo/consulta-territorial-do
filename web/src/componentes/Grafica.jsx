// Envoltorio para dibujar una gráfica de Observable Plot dentro de React.
//
// Plot.plot(opciones) devuelve un elemento SVG ya construido. Este componente:
// - mide el ancho disponible (ResizeObserver) para que la gráfica se adapte
//   a la pantalla, también en celular;
// - inserta el SVG en su <div> y lo reemplaza cuando cambian las opciones.
//
// Uso:  <Grafica opciones={(ancho) => ({ width: ancho, marks: [...] })} />
// `opciones` es una función del ancho; envuélvela en useCallback en el padre.
import { useEffect, useRef, useState } from 'react'
import * as Plot from '@observablehq/plot'

export default function Grafica({ opciones, etiqueta }) {
  const contenedor = useRef(null)
  const [ancho, setAncho] = useState(0)

  // Observa cambios de tamaño del contenedor (girar el celular, redimensionar).
  useEffect(() => {
    const observador = new ResizeObserver(([entrada]) => setAncho(Math.floor(entrada.contentRect.width)))
    observador.observe(contenedor.current)
    return () => observador.disconnect()
  }, [])

  useEffect(() => {
    if (!ancho) return
    const svg = Plot.plot(opciones(ancho))
    contenedor.current.replaceChildren(svg)
    return () => svg.remove()
  }, [opciones, ancho])

  // role="img" + aria-label: describe la gráfica para lectores de pantalla.
  return <div ref={contenedor} role="img" aria-label={etiqueta} />
}
