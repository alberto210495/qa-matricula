// Genera un informe HTML autocontenido a partir del resumen de k6 (handleSummary).
// No depende de librerías externas: funciona sin conexión a internet.
// Uso en un script:
//   import { reporteHtml, resumenTexto } from './lib/reporte_html.js';
//   export function handleSummary(data) {
//     return { stdout: resumenTexto(data), 'evidencias/x.html': reporteHtml(data, { titulo: '...' }) };
//   }

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ms = (v) => (v === undefined || v === null ? '—' : `${v.toFixed(v < 10 ? 2 : 0)} ms`);
const num = (v) => (v === undefined || v === null ? '—' : Number.isInteger(v) ? String(v) : v.toFixed(2));

// Fecha en hora de Costa Rica (UTC-6, sin horario de verano), formato dd/mm/aaaa hh:mm:ss
function fechaCR(d) {
  const cr = new Date(d.getTime() - 6 * 3600 * 1000);
  const z = (n) => String(n).padStart(2, '0');
  return `${z(cr.getUTCDate())}/${z(cr.getUTCMonth() + 1)}/${cr.getUTCFullYear()} ${z(cr.getUTCHours())}:${z(cr.getUTCMinutes())}:${z(cr.getUTCSeconds())} (hora de Costa Rica)`;
}

function verificaciones(grupo, ruta = []) {
  const filas = Object.values(grupo.checks || {}).map((c) => ({ grupo: ruta.join(' › '), nombre: c.name, ok: c.passes, fallas: c.fails }));
  for (const g of Object.values(grupo.groups || {})) filas.push(...verificaciones(g, [...ruta, g.name]));
  return filas;
}

function umbrales(data) {
  const filas = [];
  for (const [metrica, m] of Object.entries(data.metrics)) {
    for (const [expr, t] of Object.entries(m.thresholds || {})) filas.push({ metrica, expr, ok: t.ok });
  }
  return filas;
}

function valorMetrica(m) {
  const v = m.values;
  if (m.type === 'trend') return `prom ${ms(v.avg)} · mediana ${ms(v.med)} · p90 ${ms(v['p(90)'])} · p95 ${ms(v['p(95)'])} · máx ${ms(v.max)}`;
  if (m.type === 'rate') return `${(v.rate * 100).toFixed(2)} % (${v.passes ?? 0} de ${(v.passes ?? 0) + (v.fails ?? 0)})`;
  if (m.type === 'counter') return `${num(v.count)} (${num(v.rate)}/s)`;
  return `${num(v.value)} (mín ${num(v.min)}, máx ${num(v.max)})`;
}

export function resultadoGeneral(data) {
  const ver = verificaciones(data.root_group);
  const umb = umbrales(data);
  return ver.every((c) => c.fallas === 0) && umb.every((t) => t.ok);
}

export function resumenTexto(data) {
  const ver = verificaciones(data.root_group);
  const umb = umbrales(data);
  const lineas = ['', resultadoGeneral(data) ? 'RESULTADO: APROBADO' : 'RESULTADO: FALLIDO', ''];
  for (const c of ver) lineas.push(`  ${c.fallas === 0 ? '✓' : '✗'} ${c.nombre} (${c.ok}/${c.ok + c.fallas})`);
  for (const t of umb) lineas.push(`  ${t.ok ? '✓' : '✗'} umbral ${t.metrica}: ${t.expr}`);
  const d = data.metrics.http_req_duration;
  if (d) lineas.push('', `  http_req_duration: ${valorMetrica(d)}`);
  return lineas.join('\n') + '\n\n';
}

export function reporteHtml(data, { titulo = 'Informe de prueba k6', caso = '', version = '', extra = {} } = {}) {
  const ver = verificaciones(data.root_group);
  const umb = umbrales(data);
  const ok = resultadoGeneral(data);
  const fecha = fechaCR(new Date());
  const st = data.state || {};
  const t = st.testRunDurationMs;
  const duracion = t === undefined ? '—' : t < 1000 ? `${Math.round(t)} ms` : `${(t / 1000).toFixed(1)} s`;
  const metricas = Object.entries(data.metrics).sort(([a], [b]) => a.localeCompare(b));
  const estado = (b) => `<span class="${b ? 'ok' : 'ko'}">${b ? 'Aprobado' : 'Fallido'}</span>`;

  const datos = [
    ['Caso', caso || '—'],
    ['Versión del sistema', version || '—'],
    ['Fecha de ejecución', fecha],
    ['Duración', duracion],
    ...Object.entries(extra),
  ];

  return `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(titulo)}</title>
<style>
  :root { --tinta:#1f1a24; --suave:#6b6b6b; --linea:#ddd3e6; --marca:#4b2569; --ok:#1b7f3b; --ko:#b3261e; --fondo:#faf8fc; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:Calibri, "Segoe UI", system-ui, sans-serif; color:var(--tinta); background:var(--fondo); }
  main { max-width:960px; margin:0 auto; padding:32px 16px 48px; }
  h1 { color:var(--marca); margin:0 0 4px; font-size:26px; }
  h2 { color:var(--marca); font-size:18px; margin:28px 0 8px; }
  .sub { color:var(--suave); margin:0 0 20px; }
  .banda { display:inline-block; padding:6px 14px; border-radius:6px; font-weight:700; color:#fff; background:${ok ? 'var(--ok)' : 'var(--ko)'}; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:14px; }
  th, td { text-align:left; padding:7px 10px; border:1px solid var(--linea); vertical-align:top; }
  th { background:var(--marca); color:#fff; font-weight:600; }
  td.k { width:30%; font-weight:600; }
  .ok { color:var(--ok); font-weight:700; } .ko { color:var(--ko); font-weight:700; }
  code { font-family:Consolas, monospace; font-size:13px; }
  footer { margin-top:32px; color:var(--suave); font-size:12px; }
  @media (max-width:600px) { td.k { width:40%; } th, td { padding:6px; } }
</style></head>
<body><main>
  <h1>${esc(titulo)}</h1>
  <p class="sub">QA Matrícula Universitaria · Grupo 7 · ULACIT</p>
  <p><span class="banda">${ok ? 'APROBADO' : 'FALLIDO'}</span></p>

  <h2>Datos de la ejecución</h2>
  <table>${datos.map(([k, v]) => `<tr><td class="k">${esc(k)}</td><td>${esc(v)}</td></tr>`).join('')}</table>

  <h2>Verificaciones</h2>
  <table><tr><th>Verificación</th><th>Aprobadas</th><th>Fallidas</th><th>Estado</th></tr>
  ${ver.length ? ver.map((c) => `<tr><td>${esc(c.grupo ? `${c.grupo} › ${c.nombre}` : c.nombre)}</td><td>${c.ok}</td><td>${c.fallas}</td><td>${estado(c.fallas === 0)}</td></tr>`).join('') : '<tr><td colspan="4">Sin verificaciones</td></tr>'}
  </table>

  <h2>Umbrales</h2>
  <table><tr><th>Métrica</th><th>Condición</th><th>Estado</th></tr>
  ${umb.length ? umb.map((t) => `<tr><td><code>${esc(t.metrica)}</code></td><td><code>${esc(t.expr)}</code></td><td>${estado(t.ok)}</td></tr>`).join('') : '<tr><td colspan="3">Sin umbrales</td></tr>'}
  </table>

  <h2>Métricas</h2>
  <table><tr><th>Métrica</th><th>Valor</th></tr>
  ${metricas.map(([n, m]) => `<tr><td><code>${esc(n)}</code></td><td>${esc(valorMetrica(m))}</td></tr>`).join('')}
  </table>

  <footer>Generado por k6 con tests/k6/lib/reporte_html.js · El JSON completo de esta corrida está junto a este archivo en evidencias/.</footer>
</main></body></html>`;
}
