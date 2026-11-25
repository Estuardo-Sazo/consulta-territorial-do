// Mapa de los lugares poblados de un municipio, con Leaflet usado directamente
// (adaptado de consulta-territorial).
//
// React y Leaflet manejan el DOM cada uno a su manera. El patrón es:
// 1) React crea un <div> vacío y nos da una referencia (useRef).
// 2) Un useEffect crea el mapa de Leaflet UNA vez dentro de ese div.
// 3) Otro useEffect redibuja los puntos cada vez que cambian los datos.
// 4) Al desmontar el componente, la función de limpieza destruye el mapa.
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css' // estilos propios de Leaflet (controles, capas)
import { entero } from '../formato.js'
import './MapaLugares.css'

const COLOR = { urbana: '#c2571a', rural: '#1f7a8c' }

// Contenido del tooltip creado con textContent (no innerHTML): si un nombre
// trajera caracteres como "<", se muestran como texto y no se ejecutan.
function contenidoTooltip(lugar) {
  const div = document.createElement('div')
  const nombre = document.createElement('strong')
  nombre.textContent = lugar.nombre
  div.append(nombre, document.createElement('br'), `${entero(lugar.poblacion)} hab. · ${lugar.area}`)
  return div
}

export default function MapaLugares({ lugares, seleccionado, onSeleccionar }) {
  const contenedor = useRef(null) // el <div> donde vive el mapa
  const mapa = useRef(null) // instancia de L.Map
  const capaPuntos = useRef(null) // grupo de círculos, para borrarlos y redibujar
  // Guardamos la última función onSeleccionar en una ref: así el efecto de
  // dibujo no se repite solo porque el componente padre se volvió a renderizar.
  const alSeleccionar = useRef(onSeleccionar)
  // Las refs no se tocan durante el render; se actualizan en un efecto.
  useEffect(() => {
    alSeleccionar.current = onSeleccionar
  })

  // (2) Crear el mapa una sola vez.
  useEffect(() => {
    mapa.current = L.map(contenedor.current, { scrollWheelZoom: false, zoomSnap: 0.5 })
    // Teselas de OpenStreetMap (requieren internet; sin conexión los puntos se ven igual).
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; colaboradores de OpenStreetMap',
    }).addTo(mapa.current)
    capaPuntos.current = L.layerGroup().addTo(mapa.current)
    // (4) Limpieza al desmontar.
    return () => {
      mapa.current.remove()
      mapa.current = null
    }
  }, [])

  // (3) Dibujar los lugares poblados.
  useEffect(() => {
    const capa = capaPuntos.current
    capa.clearLayers()
    // "Otros lugares poblados" (código ...999) no es un lugar real: no se dibuja.
    const puntos = lugares.filter((l) => !l.es_agrupado && l.latitud != null && l.poblacion > 0)
    if (puntos.length === 0) return

    const maximo = Math.max(...puntos.map((l) => l.poblacion))
    // Se dibujan de mayor a menor para que los círculos chicos queden encima.
    for (const l of [...puntos].sort((a, b) => b.poblacion - a.poblacion)) {
      const elegido = l.codigo === seleccionado
      L.circleMarker([l.latitud, l.longitud], {
        // Radio proporcional a la raíz de la población: el ÁREA del círculo
        // queda proporcional a la población (lectura honesta del tamaño).
        radius: 3 + 14 * Math.sqrt(l.poblacion / maximo),
        color: elegido ? '#000' : COLOR[l.area],
        weight: elegido ? 3 : 1,
        fillColor: COLOR[l.area],
        fillOpacity: elegido ? 0.9 : 0.55,
      })
        .bindTooltip(contenidoTooltip(l))
        .on('click', () => alSeleccionar.current(l.codigo))
        .addTo(capa)
    }

    const elegido = puntos.find((l) => l.codigo === seleccionado)
    if (elegido) {
      mapa.current.setView([elegido.latitud, elegido.longitud], 13)
    } else {
      // Encuadra todos los puntos con un margen de 20 px.
      mapa.current.fitBounds(L.latLngBounds(puntos.map((l) => [l.latitud, l.longitud])), { padding: [20, 20] })
    }
  }, [lugares, seleccionado])

  return (
    <figure className="mapa">
      <div ref={contenedor} className="mapa__lienzo" />
      <figcaption>
        <span><i style={{ background: COLOR.urbana }} /> Urbana</span>
        <span><i style={{ background: COLOR.rural }} /> Rural</span>
        <span>Tamaño del círculo = población · Ubicación: centroide oficial del lugar poblado (INE, Censo 2018)</span>
      </figcaption>
    </figure>
  )
}
