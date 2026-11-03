// Prueba de humo: confirma que MatriculaRef responde antes de cada sesión de pruebas.
// Uso: k6 run tests/k6/smoke.js
import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const TESORERIA = __ENV.TESORERIA_URL || 'http://localhost:8001';

export const options = { vus: 1, iterations: 1, thresholds: { checks: ['rate==1'] } };

export default function () {
  const salud = http.get(`${BASE}/salud`);
  check(salud, { 'API responde 200': (r) => r.status === 200, 'versión informada': (r) => !!r.json('version') });
  const oferta = http.get(`${BASE}/oferta?curso=INF101`);
  check(oferta, { 'oferta 200': (r) => r.status === 200, 'oferta con secciones': (r) => r.json().length > 0 });
  const teso = http.get(`${TESORERIA}/bloqueos/4001`);
  check(teso, { 'Tesorería responde': (r) => r.status === 200 });
}
