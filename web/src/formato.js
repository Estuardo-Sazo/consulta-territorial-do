// Utilidades de formato compartidas.
const enteros = new Intl.NumberFormat('es-GT')
const unDecimal = new Intl.NumberFormat('es-GT', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const quetzal = new Intl.NumberFormat('es-GT', { style: 'currency', currency: 'GTQ', maximumFractionDigits: 2 })
const quetzalCorto = new Intl.NumberFormat('es-GT', { style: 'currency', currency: 'GTQ', notation: 'compact' })

export const entero = (n) => (n == null ? '—' : enteros.format(n))
export const decimal = (n) => (n == null ? '—' : unDecimal.format(n))
export const porcentaje = (n) => (n == null ? '—' : `${unDecimal.format(n)} %`)
export const quetzales = (n) => (n == null ? '—' : quetzal.format(n))
export const quetzalesCortos = (n) => (n == null ? '—' : quetzalCorto.format(n))

// Valor con su unidad, según el catálogo de indicadores.
export function valor(v, unidad) {
  if (v == null) return '—'
  if (unidad === '%') return porcentaje(v)
  if (unidad === 'personas') return entero(v)
  return `${decimal(v)} ${unidad}`
}

// '2021-04-01' -> '01/04/2021' (sin pasar por Date para no correr un día por zona horaria).
export function fecha(iso) {
  if (!iso) return '—'
  const [a, m, d] = String(iso).slice(0, 10).split('-')
  return `${d}/${m}/${a}`
}

export const NOMBRE_NIVEL = {
  pais: 'País',
  departamento: 'Departamento',
  municipio: 'Municipio',
  lugar_poblado: 'Lugar poblado',
}

// Color según el sentido del indicador (variables de index.css).
export const COLOR_SENTIDO = { 1: 'var(--bueno)', '-1': 'var(--malo)', 0: 'var(--neutro)' }

// Descarga un CSV con la fuente en las primeras líneas (las bases piden citar al INE).
// El BOM (carácter invisible U+FEFF al inicio) hace que Excel abra bien las tildes.
export function descargarCsv(nombreArchivo, columnas, filas, fuente) {
  const celda = (v) => {
    const t = v == null ? '' : String(v)
    return /[",\n;]/.test(t) ? `"${t.replaceAll('"', '""')}"` : t
  }
  const lineas = [
    `# Fuente: ${fuente}`,
    `# Descargado de Fichas Territoriales el ${new Date().toISOString().slice(0, 10)}`,
    columnas.map((c) => celda(c.titulo)).join(','),
    ...filas.map((f) => columnas.map((c) => celda(f[c.clave])).join(',')),
  ]
  const blob = new Blob(['\uFEFF' + lineas.join('\n')], { type: 'text/csv;charset=utf-8' })
  const enlace = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: nombreArchivo,
  })
  enlace.click()
  URL.revokeObjectURL(enlace.href)
}
