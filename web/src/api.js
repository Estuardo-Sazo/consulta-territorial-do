// Cliente de la API: una función por ruta de FastAPI (ver api/rutas/).
// Rutas relativas "/api/...": Vite (desarrollo) o nginx (Docker) las reenvían.

// Las respuestas se guardan en memoria: los datos no cambian mientras la app
// está abierta, así volver a una ficha o cambiar de pestaña es instantáneo.
const cache = new Map()

async function pedir(ruta) {
  if (cache.has(ruta)) return cache.get(ruta)
  const promesa = fetch(`/api${ruta}`).then(async (r) => {
    if (!r.ok) {
      let detalle = r.statusText
      try {
        detalle = (await r.json()).detail ?? detalle
      } catch {
        // la respuesta no era JSON
      }
      throw new Error(`Error ${r.status}: ${detalle}`)
    }
    return r.json()
  })
  cache.set(ruta, promesa)
  promesa.catch(() => cache.delete(ruta)) // un error no se queda guardado
  return promesa
}

const q = encodeURIComponent // protege tildes, espacios y "&"

export const buscar = (texto) => pedir(`/buscar?q=${q(texto)}&limite=15`)
export const departamentos = () => pedir('/departamentos')
export const municipiosDe = (depto) => pedir(`/departamentos/${depto}/municipios`)
export const lugaresDe = (mupio) => pedir(`/municipios/${mupio}/lugares`)
export const ficha = (nivel, codigo) => pedir(`/ficha/${nivel}/${codigo}`)
export const catalogoCuadros = () => pedir('/cuadros')
export const cuadro = (clave, nivel, codigo) => pedir(`/cuadros/${clave}/${nivel}/${codigo}`)
export const proyecciones = (nivel, codigo, anio) => pedir(`/proyecciones/${nivel}/${codigo}?anio=${anio}`)
export const calidad = () => pedir('/calidad')
export const indicadores = () => pedir('/indicadores')
export const geojson = () => pedir('/mapa/municipios.geojson')
export const mapa = (clave) => pedir(`/mapa/${clave}`)
export const ranking = (clave, depto) => pedir(`/ranking/${clave}${depto ? `?departamento=${depto}` : ''}`)
export const dispersion = (x, y) => pedir(`/dispersion?x=${x}&y=${y}`)
export const comparar = (a, b) => pedir(`/comparar?a=${a}&b=${b}`)
export const precios = (texto, unidad, depto) =>
  pedir(`/precios?q=${q(texto)}${unidad ? `&unidad=${q(unidad)}` : ''}${depto ? `&departamento=${depto}` : ''}`)
export const sugerenciasPrecios = (texto) => pedir(`/precios/sugerencias?q=${q(texto)}`)
export const comprasMunicipio = (mupio) => pedir(`/compras/municipio/${mupio}`)
