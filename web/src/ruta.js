// Navegación con el hash de la URL: #/pagina/parte1/parte2...

// "#/ficha/municipio/1601" -> { pagina: 'ficha', partes: ['municipio', '1601'] }
export function leerRuta() {
  const [, pagina = 'ficha', ...partes] = window.location.hash.split('/')
  return { pagina: pagina || 'ficha', partes: partes.map(decodeURIComponent) }
}

// irA('ficha', 'municipio', 1601) -> #/ficha/municipio/1601
export const irA = (...partes) => {
  window.location.hash = '/' + partes.map((p) => encodeURIComponent(p)).join('/')
}
