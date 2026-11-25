// Panel "Rigor y fuentes": validaciones de la ingesta, fuentes con URL, fecha,
// licencia y huella SHA-256, tabla de equivalencias de códigos y criterios.
// Va plegado (<details>) para no estorbar, pero siempre al alcance.
import { useEffect, useState } from 'react'
import { calidad } from '../api.js'

export default function Rigor() {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    calidad().then(setDatos).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="aviso">{error}</p>
  if (!datos) return null
  const aprobadas = datos.validaciones.filter((v) => v.aprobado).length

  return (
    <details className="tarjeta">
      <summary>
        <strong>Rigor y fuentes</strong> · {aprobadas} de {datos.validaciones.length} validaciones aprobadas ·{' '}
        {datos.fuentes.length} archivos fuente
      </summary>

      <h3>Criterios</h3>
      <ul>
        <li>Indicadores calculados con los conteos publicados por el INE; misma fórmula en todos los niveles.</li>
        <li>“Pocos casos”: universo menor de 30 personas u hogares; el dato se muestra con aviso.</li>
        <li>Población 2026 y crecimiento son proyecciones del INE, no conteos.</li>
        <li>Precios de Guatecompras: adjudicados (no de mercado), solo procesos de un renglón y una adjudicación,
          comparados dentro de la misma unidad; cada precio lleva su fecha.</li>
        <li>Solo datos agregados: no se identifica a personas, hogares ni proveedores.</li>
      </ul>

      <h3>Validaciones de la ingesta</h3>
      <ul>
        {datos.validaciones.map((v) => (
          <li key={v.chequeo}>{v.aprobado ? '✔' : '✘'} {v.chequeo}{v.problemas ? ` (${v.problemas} problemas)` : ''}</li>
        ))}
      </ul>

      <h3>Archivos fuente</h3>
      <div className="tabla-desplazable">
        <table>
          <thead><tr><th>Archivo</th><th>Licencia</th><th>Descarga</th><th>SHA-256</th></tr></thead>
          <tbody>
            {datos.fuentes.map((f) => (
              <tr key={f.clave}>
                <td><a href={f.url} target="_blank" rel="noreferrer">{f.titulo}</a></td>
                <td>{f.licencia}</td>
                <td>{f.fecha_descarga}</td>
                <td><code title={f.sha256}>{f.sha256.slice(0, 12)}…</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3>Equivalencias de códigos municipales</h3>
      <p className="nota">
        El censo numera los municipios del departamento de Guatemala 0101-0117 y las proyecciones usan 0101 y
        0123-0138. Se cruzaron por nombre con el diccionario oficial; estos son los que cambian:
      </p>
      <div className="tabla-desplazable">
        <table>
          <thead><tr><th>Municipio</th><th className="num">Código censo</th><th className="num">Código proyecciones</th></tr></thead>
          <tbody>
            {datos.equivalencias.map((e) => (
              <tr key={e.cod_mupio}>
                <td>{e.nombre}</td>
                <td className="num">{String(e.cod_mupio).padStart(4, '0')}</td>
                <td className="num">{e.cod_proy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}
