// Municipios con perfil parecido (distancia entre indicadores estandarizados)
// con enlace a su ficha y a la comparación lado a lado.

export default function Parecidos({ codigo, parecidos }) {
  if (!parecidos.length) return null
  return (
    <section className="tarjeta">
      <h2>Municipios con perfil parecido</h2>
      <p className="nota">
        Los 5 más cercanos al comparar los 16 indicadores del censo y proyecciones en porcentaje, puestos en la misma
        escala (valores z) para que ninguno pese más que otro. Sirve para buscar experiencias en contextos similares.
      </p>
      <div className="tabla-desplazable">
        <table>
          <thead>
            <tr><th>Municipio</th><th>Departamento</th><th className="num">Distancia</th><th className="no-imprimir" /></tr>
          </thead>
          <tbody>
            {parecidos.map((p) => (
              <tr key={p.codigo}>
                <td><a href={`#/ficha/municipio/${p.codigo}`}>{p.nombre}</a></td>
                <td>{p.departamento}{p.mismo_departamento && <span className="chip"> mismo departamento</span>}</td>
                <td className="num">{p.distancia.toFixed(2)}</td>
                <td className="no-imprimir"><a href={`#/comparar/${codigo}/${p.codigo}`}>Comparar</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="nota">Distancia menor = perfil más parecido.</p>
    </section>
  )
}
