// Paleta institucional del INE (tomada de sus publicaciones, p. ej. IPMC
// octubre 2026): azul oscuro, azul brillante, amarillo, naranja y verde.
// Las gráficas (Observable Plot) y los mapas (Leaflet) necesitan colores
// literales; el CSS usa las mismas cifras como variables en index.css.
//
// Reglas de uso para que se vea sobrio:
// - azul oscuro: identidad (encabezado, botones, series principales);
// - azul brillante y naranja: las dos series que se comparan (hombres/mujeres,
//   rural/urbana) y los acentos (mediana, Censo 2018, tendencia);
// - amarillo: solo acentos sobre azul (nunca texto sobre blanco: no se lee);
// - verde y naranja del logo son claros para texto: en texto se usan sus
//   versiones oscuras (--bueno, --malo en index.css).
export const INE = {
  azul: '#0b3a86',
  azulBrillante: '#1677e0',
  amarillo: '#ffd100',
  naranja: '#ff5a00',
  verde: '#7ac70c',
  gris: '#4a4a4a',
}

// Escalas de 5 tonos para el mapa coroplético, según el sentido del indicador.
// Azul (más alto = mejor) y naranja (más alto = peor) son de la paleta del INE;
// los descriptivos van en gris azulado para no sugerir que algo es bueno o malo.
export const ESCALAS = {
  1: ['#e4eefb', '#a8cbf2', '#5c9fe6', '#1a6bcc', INE.azul],
  '-1': ['#ffeadc', '#ffc097', '#ff8a4c', '#e2560c', '#9a3604'],
  0: ['#eef0f4', '#c9ced8', '#9aa3b4', '#6a7690', '#3e4a63'],
}
