// CP-CUP-01 a 04 · RN-CUP-01: N estudiantes intentan tomar el último cupo de la sección 1 al mismo tiempo.
// Uso: k6 run -e USUARIOS=50 tests/k6/concurrencia_ultimo_cupo.js
// Reiniciar los datos antes de cada corrida (data/reset.ps1).
// Genera evidencias/cup_<N>u_seccion<S>.json y .html
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';
import { reporteHtml } from './lib/reporte_html.js';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const USUARIOS = parseInt(__ENV.USUARIOS || '50');
const SECCION = parseInt(__ENV.SECCION || '1');
const CUPO = parseInt(__ENV.CUPO || '1');

const aceptadas = new Counter('inscripciones_aceptadas');
const rechazadas = new Counter('rechazadas_sin_cupo');

export const options = {
  scenarios: {
    ultimo_cupo: { executor: 'per-vu-iterations', vus: USUARIOS, iterations: 1, maxDuration: '60s' },
  },
  thresholds: { inscripciones_aceptadas: [`count<=${CUPO}`] },  // falla la corrida si hay sobrecupo
};

export default function () {
  const estudiante = 1000 + __VU;   // estudiantes 1001-1300 sin restricciones
  const r = http.post(`${BASE}/inscripciones`, JSON.stringify({ estudiante_id: estudiante, seccion_id: SECCION }),
    { headers: { 'Content-Type': 'application/json' } });
  if (r.status === 201) aceptadas.add(1);
  else if (r.status === 409) rechazadas.add(1);
  check(r, { 'respuesta 201 o 409': (x) => x.status === 201 || x.status === 409 });
}

export function handleSummary(data) {
  const n = (m) => (data.metrics[m] ? data.metrics[m].values.count : 0);
  const resumen = {
    caso: `CP-CUP · ${USUARIOS} solicitudes simultáneas sobre la sección ${SECCION} (cupo ${CUPO})`,
    aceptadas: n('inscripciones_aceptadas'),
    rechazadas: n('rechazadas_sin_cupo'),
    sobrecupo: Math.max(n('inscripciones_aceptadas') - CUPO, 0),
    resultado: n('inscripciones_aceptadas') <= CUPO ? 'APROBADO' : 'FALLIDO',
  };
  const base = `evidencias/cup_${USUARIOS}u_seccion${SECCION}`;
  return {
    stdout: `\n${JSON.stringify(resumen, null, 2)}\n`,
    [`${base}.json`]: JSON.stringify(resumen, null, 2),
    [`${base}.html`]: reporteHtml(data, {
      titulo: 'Concurrencia sobre el último cupo',
      caso: resumen.caso,
      version: __ENV.VERSION ? `v${__ENV.VERSION}` : '',
      extra: { 'Inscripciones aceptadas': resumen.aceptadas, 'Rechazadas sin cupo': resumen.rechazadas, 'Sobrecupo': resumen.sobrecupo },
    }),
  };
}
