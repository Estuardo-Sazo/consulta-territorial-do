// "Lo que dicen los datos" (texto automático de la API) y, en municipios,
// "Dónde destaca" y "Sus retos" (10 % extremo del país según el sentido).
import { valor } from '../formato.js'
import './Hallazgos.css'

function Lista({ titulo, items, clase, vacio }) {
  return (
    <div className={`hallazgos__lista hallazgos__lista--${clase}`}>
      <h3>{titulo}</h3>
      {items.length === 0 ? (
        <p className="nota">{vacio}</p>
      ) : (
        <ul>
          {items.map((i) => (
            <li key={i.clave}>
              <strong>{i.nombre}</strong>: {valor(i.valor, i.unidad)}{' '}
              <span className="nota">(puesto {i.puesto} de {i.de})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function Hallazgos({ texto, destacaRetos }) {
  return (
    <section className="tarjeta hallazgos">
      <h2>Lo que dicen los datos</h2>
      {texto.map((frase) => <p key={frase}>{frase}</p>)}
      <p className="nota">
        Texto generado con reglas fijas a partir de las mismas cifras de la ficha; describe y compara, no atribuye causas.
      </p>
      {destacaRetos && (
        <div className="hallazgos__columnas">
          <Lista titulo="Dónde destaca" items={destacaRetos.destaca} clase="bueno"
                 vacio="No está en el 10 % con mejor resultado del país en ningún indicador." />
          <Lista titulo="Sus retos" items={destacaRetos.retos} clase="malo"
                 vacio="No está en el 10 % con peor resultado del país en ningún indicador." />
        </div>
      )}
      {destacaRetos && (
        <p className="nota">
          Criterio: {destacaRetos.criterio}, solo indicadores con sentido definido (los descriptivos no son logros ni
          problemas) y sin valores con pocos casos.
        </p>
      )}
    </section>
  )
}
