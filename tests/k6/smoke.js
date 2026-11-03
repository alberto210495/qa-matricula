// Prueba de humo: confirma que MatriculaRef responde antes de cada sesión de pruebas.
// Uso: k6 run tests/k6/smoke.js            (desde la raíz del repositorio)
// Genera evidencias/smoke_v<versión>.json y evidencias/smoke_v<versión>.html
import http from 'k6/http';
import { check } from 'k6';
import { reporteHtml, resumenTexto } from './lib/reporte_html.js';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const TESORERIA = __ENV.TESORERIA_URL || 'http://localhost:8001';
const VERSION = __ENV.VERSION || '1.0.0';

export const options = { vus: 1, iterations: 1, thresholds: { checks: ['rate==1'] } };

export default function () {
  const salud = http.get(`${BASE}/salud`);
  check(salud, { 'API responde 200': (r) => r.status === 200, 'versión informada': (r) => !!r.json('version') });
  const oferta = http.get(`${BASE}/oferta?curso=INF101`);
  check(oferta, { 'oferta 200': (r) => r.status === 200, 'oferta con secciones': (r) => r.json().length > 0 });
  const teso = http.get(`${TESORERIA}/bloqueos/4001`);
  check(teso, { 'Tesorería responde': (r) => r.status === 200 });
}

export function handleSummary(data) {
  const base = `evidencias/smoke_v${VERSION}`;
  return {
    stdout: resumenTexto(data),
    [`${base}.json`]: JSON.stringify(data, null, 2),
    [`${base}.html`]: reporteHtml(data, {
      titulo: 'Prueba de humo · MatriculaRef',
      caso: 'Disponibilidad de API, oferta y Tesorería antes de cada sesión',
      version: `v${VERSION}`,
      extra: { 'API': BASE, 'Tesorería': TESORERIA },
    }),
  };
}
