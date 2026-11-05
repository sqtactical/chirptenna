// Chirptenna web lite: interfaz. El cálculo lo hace Python (antenas.web_api) dentro de motor.js.
// Chirptenna · Copyright (C) 2026 sqtactical · AGPL-3.0
'use strict';

const $ = (id) => document.getElementById(id);
const CLAVE_LOCAL = 'chirptenna-web-diseno';
const ICONOS = { grave: '⛔', error: '⛔', aviso: '⚠️', info: 'ℹ️', ok: '✅' };
const ICONOS_CONSEJO = { banda: '📡', 'diseño': '💡', montaje: '🔧', medida: '📏' };

// ------------------------------------------------------------------ motor (Web Worker con Pyodide)
const motor = new Worker('motor.js');
const pendientes = new Map();
let siguienteId = 1;
motor.onmessage = (ev) => {
  const m = ev.data;
  if (m.progreso) { $('carga-texto').textContent = m.progreso; $('carga-barra').style.width = `${100 * m.fraccion}%`; return; }
  if (m.fallo) { $('carga-texto').textContent = 'No se ha podido cargar el motor: ' + m.fallo; return; }
  if (m.listo) return;
  const p = pendientes.get(m.id);
  if (!p) return;
  pendientes.delete(m.id);
  m.ok ? p.resolver(m.resultado) : p.rechazar(new Error(m.error));
};
function llamar(fn, arg) {
  return new Promise((resolver, rechazar) => {
    const id = siguienteId++;
    pendientes.set(id, { resolver, rechazar });
    motor.postMessage({ id, fn, arg: arg === undefined ? undefined : JSON.stringify(arg) });
  });
}

// ------------------------------------------------------------------ estado
let cat = null;              // catálogo (tipos, sustratos, reglas, bandas, textos)
let ultimo = null;           // último resultado de generar
const estado = {
  nombre: 'antena', clave: 'monopolo_koch', f_MHz: 2441.75, bw_MHz: 83.5, sustrato: null, reglas: null,
  parametros: null, serigrafia: null,
};

function tipoActual() { return cat.tipos.find((t) => t.clave === estado.clave); }
function defectos(clave) {
  const t = cat.tipos.find((x) => x.clave === clave);
  return Object.fromEntries(t.parametros.map((p) => [p.nombre, p.defecto]));
}
function entrada(extra = {}) {
  return { clave: estado.clave, f_MHz: estado.f_MHz, bw_MHz: estado.bw_MHz, sustrato: estado.sustrato,
    reglas: estado.reglas, parametros: estado.parametros, serigrafia: estado.serigrafia, nombre: estado.nombre, ...extra };
}
function guardarLocal() {
  try { localStorage.setItem(CLAVE_LOCAL, JSON.stringify(estado)); } catch (e) { /* sin almacenamiento */ }
}

// ------------------------------------------------------------------ avisos
let temporizadorAviso = null;
function avisar(texto, error = false, ms = 4500) {
  const t = $('aviso');
  t.textContent = texto;
  t.className = 'toast' + (error ? ' error' : '');
  t.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => { t.hidden = true; }, ms);
}
function lista(el, filas) {
  el.replaceChildren(...filas.map(([nivel, texto, icono]) => {
    const li = document.createElement('li');
    li.className = 'n-' + nivel;
    li.dataset.icono = icono || ICONOS[nivel] || '•';
    li.textContent = texto;
    return li;
  }));
}

// ------------------------------------------------------------------ tema
function aplicarTema(t) {
  if (t === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.dataset.theme = t;
  try { localStorage.setItem('chirptenna-tema', t); } catch (e) { /* nada */ }
}
$('btn-tema').onclick = () => {
  const oscuro = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === 'dark'
    : matchMedia('(prefers-color-scheme: dark)').matches;
  aplicarTema(oscuro ? 'light' : 'dark');
};
try { const t = localStorage.getItem('chirptenna-tema'); if (t) aplicarTema(t); } catch (e) { /* nada */ }

// ------------------------------------------------------------------ vista (SVG)
let caja = null;             // viewBox actual {x, y, w, h}
let cajaInicial = null;
function svgEsc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function ruta(anillos) {      // anillos con y hacia arriba -> path SVG (y invertida)
  return anillos.map((a) => 'M' + a.map(([x, y]) => `${x},${-y}`).join('L') + 'Z').join('');
}
function dibujar(v, encajar) {
  const pts = v.contorno.flat().concat(v.reflector || []);
  const xs = pts.map((p) => p[0]); const ys = pts.map((p) => -p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const m = 0.06 * Math.max(x1 - x0, y1 - y0) + 2;
  const nueva = { x: x0 - m, y: y0 - m, w: x1 - x0 + 2 * m, h: y1 - y0 + 2 * m };
  if (encajar || !caja) caja = { ...nueva };
  cajaInicial = nueva;
  const g = Math.max(nueva.w, nueva.h) / 400;       // grosor de línea base (mm)
  let s = '';
  if (v.reflector) s += `<path d="${ruta([v.reflector])}" fill="none" stroke="var(--sec)" stroke-dasharray="${4 * g} ${3 * g}" stroke-width="${1.5 * g}"/>`;
  s += `<path d="${ruta(v.contorno)}" fill="var(--tarjeta)" fill-rule="evenodd" stroke="var(--linea)" stroke-width="${1.5 * g}"/>`;
  for (const p of v.cobre_inf) s += `<path d="${ruta(p)}" fill="var(--masa)" fill-opacity=".45" fill-rule="evenodd"/>`;
  for (const p of v.cobre_sup) s += `<path d="${ruta(p)}" fill="var(--cobre)" fill-opacity=".95" fill-rule="evenodd"/>`;
  for (const [x, y, d] of v.taladros) s += `<circle cx="${x}" cy="${-y}" r="${d / 2}" fill="var(--fondo)" stroke="var(--linea)" stroke-width="${g}"/>`;
  for (const [x, y, w, h] of v.pads) s += `<rect x="${x}" y="${-(y + h)}" width="${w}" height="${h}" fill="none" stroke="var(--pads)" stroke-width="${1.2 * g}"/>`;
  for (const [x, y, w, h] of v.ipex) s += `<rect x="${x}" y="${-(y + h)}" width="${w}" height="${h}" fill="rgba(255,0,0,.25)" stroke="red" stroke-width="${g}"/>`;
  for (const c of v.componentes) s += `<circle cx="${c.x}" cy="${-c.y}" r="${2 * g}" fill="var(--pads)"><title>${svgEsc(c.ref + ': ' + c.valor)}</title></circle>`;
  const letra = Math.max(1.2, Math.max(nueva.w, nueva.h) / 55);
  for (const mk of v.marcas) {
    const [[ax, ay], [bx, by]] = mk.linea;
    s += `<line x1="${ax}" y1="${-ay}" x2="${bx}" y2="${-by}" stroke="var(--texto)" stroke-width="${2 * g}"/>`;
    s += `<text x="${mk.pos[0]}" y="${-mk.pos[1]}" font-size="${letra}" fill="var(--texto)" text-anchor="middle" dominant-baseline="middle">${svgEsc(mk.texto)}</text>`;
  }
  const [px, py] = v.puerto; const t = 3 * g + letra / 3;
  s += `<path d="M${px - t},${-py - t}L${px + t},${-py}L${px - t},${-py + t}Z" fill="red"><title>${svgEsc(v.tipo_puerto === 'coaxial' || v.tipo_puerto === 'pasante' ? 'Toma del coaxial' : 'Conector ' + v.conector)}</title></path>`;
  $('vista').innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${caja.x} ${caja.y} ${caja.w} ${caja.h}" preserveAspectRatio="xMidYMid meet">${s}</svg>`;
  const ley = [['var(--cobre)', 'Cobre (cara superior)'], ['var(--masa)', 'Masa (cara inferior)']];
  if (v.pads.length) ley.push(['var(--pads)', 'Componentes de ajuste']);
  if (v.marcas.length) ley.push(['var(--texto)', 'Marcas de corte (MHz)']);
  if (v.reflector) ley.push(['var(--sec)', `Reflector (a ${v.separacion_reflector_mm.toFixed(1)} mm por detrás)`]);
  ley.push(['red', v.tipo_puerto === 'coaxial' || v.tipo_puerto === 'pasante' ? 'Toma del coaxial' : `Conector (${v.conector})`]);
  $('leyenda').innerHTML = ley.map(([c, t2]) => `<span><i style="background:${c}"></i>${svgEsc(t2)}</span>`).join('');
}
function ponerCaja() { const svg = $('vista').querySelector('svg'); if (svg) svg.setAttribute('viewBox', `${caja.x} ${caja.y} ${caja.w} ${caja.h}`); }
(function zoomYArrastre() {
  const el = $('vista');
  el.addEventListener('wheel', (e) => {
    if (!caja) return;
    e.preventDefault();
    const r = el.getBoundingClientRect();
    const k = Math.exp(e.deltaY * 0.0015);
    const esc = Math.max(caja.w / r.width, caja.h / r.height);
    const ox = caja.x + (caja.w - r.width * esc) / 2, oy = caja.y + (caja.h - r.height * esc) / 2;
    const mx = ox + (e.clientX - r.left) * esc, my = oy + (e.clientY - r.top) * esc;
    caja = { x: mx - (mx - caja.x) * k, y: my - (my - caja.y) * k, w: caja.w * k, h: caja.h * k };
    ponerCaja();
  }, { passive: false });
  let ini = null;
  el.addEventListener('pointerdown', (e) => { if (caja) { ini = { x: e.clientX, y: e.clientY, c: { ...caja } }; el.setPointerCapture(e.pointerId); } });
  el.addEventListener('pointermove', (e) => {
    if (!ini) return;
    const r = el.getBoundingClientRect();
    const esc = Math.max(ini.c.w / r.width, ini.c.h / r.height);
    caja = { ...ini.c, x: ini.c.x - (e.clientX - ini.x) * esc, y: ini.c.y - (e.clientY - ini.y) * esc };
    ponerCaja();
  });
  el.addEventListener('pointerup', () => { ini = null; });
  el.addEventListener('dblclick', () => { if (cajaInicial) { caja = { ...cajaInicial }; ponerCaja(); } });
})();

// ------------------------------------------------------------------ parámetros
let visiblesActuales = '';
function construirParametros(visibles) {
  const cont = $('parametros');
  const t = tipoActual();
  visiblesActuales = visibles.join(',');
  cont.replaceChildren();
  for (const p of t.parametros) {
    if (!visibles.includes(p.nombre)) continue;
    const valor = estado.parametros[p.nombre] ?? p.defecto;
    const lab = document.createElement('label');
    lab.textContent = p.etiqueta;
    if (p.ayuda) lab.title = p.ayuda;
    let campo;
    if (p.opciones) {
      campo = document.createElement('select');
      for (const [k, txt] of Object.entries(p.opciones)) campo.add(new Option(txt, k, false, Number(k) === Number(valor)));
      campo.onchange = () => cambiarParametro(p, Number(campo.value));
    } else {
      campo = document.createElement('input');
      Object.assign(campo, { type: 'number', min: p.minimo, max: p.maximo, step: p.paso, value: valor });
      campo.onchange = () => {
        let v = Number(campo.value);
        if (!Number.isFinite(v)) return;
        v = Math.min(p.maximo, Math.max(p.minimo, v));
        cambiarParametro(p, p.entero ? Math.round(v) : v);
      };
    }
    campo.dataset.nombre = p.nombre;
    lab.append(campo);
    cont.append(lab);
  }
}
function ponerValores() {
  for (const campo of $('parametros').querySelectorAll('[data-nombre]')) {
    const v = estado.parametros[campo.dataset.nombre];
    if (v !== undefined) campo.value = campo.tagName === 'SELECT' ? String(Math.round(v)) : v;
  }
}
function cambiarParametro(p, valor) {
  estado.parametros[p.nombre] = valor;
  const t = tipoActual();
  if (t.escalables.includes(p.nombre) && Number(estado.parametros.escalado ?? 0) === 1) {
    // medida fijada a mano: si siguiera en «proporcionales», el próximo ajuste la pisaría
    estado.parametros.escalado = 0;
    avisar('Medidas secundarias pasadas a «Manuales» para respetar el valor que has puesto.');
  }
  if ((p.nombre === 'escalado' && valor === 1) || p.nombre === 'masa' || (p.nombre === 'conector' && t.familia === 'monopolo')) {
    dimensionar();
    return;
  }
  regenerar();
}

// ------------------------------------------------------------------ generar y mostrar
let generando = Promise.resolve();
function regenerar(encajar = false) {
  guardarLocal();
  const e = entrada();
  generando = generando.then(() => llamar('generar', e)).then((r) => mostrar(r, encajar)).catch((err) => avisar(err.message, true));
  return generando;
}
async function dimensionar(ampliar = false) {
  try {
    const r = await llamar('dimensionar', entrada({ ampliar_banda: ampliar }));
    estado.parametros = r.parametros;
    $('aviso-ajuste').textContent = r.aviso || '';
    if (ampliar && r.aviso) avisar(r.aviso);
    await regenerar(true);
    ponerValores();
  } catch (err) { avisar(err.message, true); }
}
function mostrar(r, encajar) {
  if (r.visibles.join(',') !== visiblesActuales) construirParametros(r.visibles);
  if (r.error) { avisar(r.error, true); return; }
  ultimo = r;
  dibujar(r.vista, encajar);
  $('descripcion').textContent = r.descripcion;
  lista($('problemas'), r.problemas.map(([n, t]) => [n, t]));
  const b = $('banda-estado');
  if (r.banda) {
    b.textContent = (r.banda.estado === 'holgado' ? '✅ ' : r.banda.estado === 'justo' ? '⚠️ ' : '⛔ ') + r.banda.texto;
    b.className = 'pequeno n-' + (r.banda.estado === 'holgado' ? 'ok' : r.banda.estado === 'justo' ? 'aviso' : 'error');
  } else b.textContent = '';
  $('info').replaceChildren(...r.info.map(([k, v]) => {
    const tr = document.createElement('tr');
    const a = document.createElement('td'); a.textContent = k;
    const c = document.createElement('td'); c.textContent = v;
    tr.append(a, c);
    return tr;
  }));
  lista($('consejos'), r.consejos.map(([cat_, t]) => ['info', t, ICONOS_CONSEJO[cat_] || '•']));
  const graves = r.problemas.filter(([n]) => n === 'grave' || n === 'aviso').map(([, t]) => ['error', 'Problema conocido: ' + t]);
  lista($('comprobaciones'), graves.concat(r.comprobaciones));
  $('seri-vista').textContent = (estado.serigrafia.logo !== 'ninguno' ? '[logo de Chirptenna]\n' : '') + r.serigrafia.join('\n');
}

// ------------------------------------------------------------------ barra del diseño
function mostrarRango() {
  const lo = estado.f_MHz - estado.bw_MHz / 2, hi = estado.f_MHz + estado.bw_MHz / 2;
  $('rango').textContent = `${+lo.toFixed(3)}–${+hi.toFixed(3)} MHz`;
}
function bandaDe() {
  for (const [n, b] of Object.entries(cat.bandas)) {
    if (b && Math.abs((b[0] + b[1]) / 2 - estado.f_MHz) < 0.01 && Math.abs(b[1] - b[0] - estado.bw_MHz) < 0.01) return n;
  }
  return 'Otra';
}
function marcarBanda() {
  const actual = bandaDe();
  for (const b of $('bandas').children) b.classList.toggle('activa', b.dataset.banda === actual);
}
function ponerBarra() {
  $('nombre').value = estado.nombre;
  $('tipo').value = estado.clave;
  $('f').value = estado.f_MHz;
  $('bw').value = estado.bw_MHz;
  $('sustrato').value = estado.sustrato;
  $('reglas').value = estado.reglas;
  mostrarRango();
  marcarBanda();
  ponerSerigrafia();
}

// ------------------------------------------------------------------ serigrafía
function ponerSerigrafia() {
  const s = estado.serigrafia;
  $('logo').value = s.logo || 'grande';
  $('aviso-logo').hidden = s.logo !== 'ninguno';
  for (const c of $('seri-opciones').querySelectorAll('input')) c.checked = !!s[c.dataset.clave];
  $('seri-libre').value = s.libre || '';
}

// ------------------------------------------------------------------ compartir, abrir y exportar
function aBase64Url(texto) {
  const bytes = new TextEncoder().encode(texto);
  let bin = '';
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function deBase64Url(t) {
  const bin = atob(t.replace(/-/g, '+').replace(/_/g, '/'));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}
function cargarDiseno(d) {
  // acepta el estado de la web o un diseno.json de la aplicación de escritorio
  const clave = d.clave || d.tipo;
  if (!cat.tipos.some((t) => t.clave === clave)) throw new Error(`Tipo desconocido: ${clave}`);
  estado.clave = clave;
  estado.nombre = d.nombre || 'antena';
  estado.f_MHz = Number(d.f_MHz ?? d.f_objetivo_MHz ?? estado.f_MHz);
  estado.bw_MHz = Number(d.bw_MHz ?? d.ancho_banda_MHz ?? estado.bw_MHz);
  estado.sustrato = cat.sustratos.includes(d.sustrato) ? d.sustrato : cat.sustrato_defecto;
  estado.reglas = cat.reglas.includes(d.reglas) ? d.reglas : cat.reglas_defecto;
  estado.parametros = { ...defectos(clave), ...(d.parametros || {}) };
  const s = { ...cat.serigrafia_defecto, ...(d.serigrafia || {}) };
  if (typeof s.logo === 'boolean') s.logo = s.logo ? 'grande' : 'ninguno';     // diseños antiguos
  estado.serigrafia = s;
}
$('btn-enlace').onclick = async () => {
  const url = location.href.split('#')[0] + '#d=' + aBase64Url(JSON.stringify(estado));
  history.replaceState(null, '', url);
  try { await navigator.clipboard.writeText(url); avisar('Enlace copiado: quien lo abra verá este mismo diseño.'); }
  catch (e) { avisar('Enlace listo en la barra de direcciones: cópialo desde ahí.'); }
};
$('abrir').onchange = async (ev) => {
  const f = ev.target.files[0];
  ev.target.value = '';
  if (!f) return;
  try {
    cargarDiseno(JSON.parse(await f.text()));
    visiblesActuales = '';
    ponerBarra();
    await regenerar(true);
    avisar(`Abierto «${estado.nombre}».`);
  } catch (err) { avisar('No se puede abrir: ' + err.message, true); }
};
$('btn-exportar').onclick = async () => {
  const b = $('btn-exportar');
  b.disabled = true;
  $('estado-exportar').textContent = 'Generando la placa…';
  try {
    const { zip, info } = await llamar('exportar', entrada());
    const url = URL.createObjectURL(new Blob([zip], { type: 'application/zip' }));
    const a = document.createElement('a');
    a.href = url; a.download = `${info.nombre}_chirptenna.zip`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    const s = info.serigrafia || {};
    let txt = `Descargado ${info.nombre}_chirptenna.zip. Ábrelo en KiCad y pasa el DRC antes de sacar los Gerber.`;
    if (s.logo_forma === 'texto') txt += ' Serigrafía: no cabe el grillo; va la palabra «Chirptenna».';
    else if (s.logo_mm) txt += ` Serigrafía: logo de ${s.logo_mm} mm.`;
    if (s.quitadas && s.quitadas.length) txt += ' No caben: ' + s.quitadas.join(' · ') + '.';
    $('estado-exportar').textContent = txt;
  } catch (err) {
    $('estado-exportar').textContent = '';
    avisar('Error al exportar: ' + err.message, true, 8000);
  } finally { b.disabled = false; }
};

// ------------------------------------------------------------------ arranque
async function iniciar() {
  cat = await llamar('catalogo');
  $('version').textContent = 'v' + cat.version;
  $('pie-version').textContent = 'Chirptenna v' + cat.version;
  $('aviso-general').textContent = cat.aviso_general;
  for (const t of cat.tipos) $('tipo').add(new Option(t.nombre, t.clave));
  for (const s of cat.sustratos) $('sustrato').add(new Option(s, s));
  for (const r of cat.reglas) $('reglas').add(new Option(r, r));
  for (const [k, txt] of Object.entries(cat.logo_opciones)) $('logo').add(new Option(txt, k));
  $('aviso-logo').textContent = cat.aviso_sin_logo;
  for (const [k, txt] of cat.serigrafia_opciones) {
    const lab = document.createElement('label');
    lab.className = 'casilla';
    const c = document.createElement('input');
    c.type = 'checkbox'; c.dataset.clave = k;
    c.onchange = () => { estado.serigrafia[k] = c.checked; regenerar(); };
    lab.append(c, txt);
    $('seri-opciones').append(lab);
  }
  for (const n of Object.keys(cat.bandas)) {
    const b = document.createElement('button');
    b.className = 'opcion'; b.textContent = n; b.dataset.banda = n;
    b.onclick = () => {
      const rango = cat.bandas[n];
      if (rango) { estado.f_MHz = (rango[0] + rango[1]) / 2; estado.bw_MHz = rango[1] - rango[0]; }
      ponerBarra();
      if (rango) dimensionar(); else $('f').focus();
    };
    $('bandas').append(b);
  }

  // estado inicial: enlace compartido > último diseño de este navegador > valores por defecto
  estado.sustrato = cat.sustrato_defecto;
  estado.reglas = cat.reglas_defecto;
  estado.serigrafia = { ...cat.serigrafia_defecto };
  estado.parametros = defectos(estado.clave);
  let origen = null;
  try {
    if (location.hash.startsWith('#d=')) origen = JSON.parse(deBase64Url(location.hash.slice(3)));
    else origen = JSON.parse(localStorage.getItem(CLAVE_LOCAL) || 'null');
  } catch (e) { origen = null; }
  let nuevo = true;
  if (origen) { try { cargarDiseno(origen); nuevo = false; } catch (e) { avisar('No se ha podido abrir el diseño del enlace.', true); } }
  ponerBarra();

  $('nombre').onchange = () => { estado.nombre = $('nombre').value.trim() || 'antena'; regenerar(); };
  $('tipo').onchange = () => {
    estado.clave = $('tipo').value;
    estado.parametros = defectos(estado.clave);
    $('aviso-ajuste').textContent = '';
    visiblesActuales = '';
    dimensionar();
  };
  $('f').onchange = () => {
    const v = Number($('f').value);
    if (v > 0) { estado.f_MHz = v; mostrarRango(); marcarBanda(); regenerar(); $('aviso-ajuste').textContent = 'Frecuencia cambiada: pulsa «Ajustar tamaño a la frecuencia».'; }
  };
  $('bw').onchange = () => { const v = Number($('bw').value); if (v > 0) { estado.bw_MHz = v; mostrarRango(); marcarBanda(); regenerar(); } };
  $('sustrato').onchange = () => { estado.sustrato = $('sustrato').value; regenerar(); };
  $('reglas').onchange = () => { estado.reglas = $('reglas').value; regenerar(); };
  $('btn-ajustar').onclick = () => dimensionar();
  $('btn-banda').onclick = () => dimensionar(true);
  $('logo').onchange = () => {
    estado.serigrafia.logo = $('logo').value;
    $('aviso-logo').hidden = estado.serigrafia.logo !== 'ninguno';
    if (estado.serigrafia.logo === 'ninguno') avisar(cat.aviso_sin_logo, false, 9000);
    regenerar();
  };
  $('seri-libre').onchange = () => { estado.serigrafia.libre = $('seri-libre').value; regenerar(); };

  $('carga').hidden = true;
  $('app').hidden = false;
  if (nuevo) await dimensionar(); else await regenerar(true);
}
iniciar().catch((e) => { $('carga-texto').textContent = 'Error al arrancar: ' + e.message; });
