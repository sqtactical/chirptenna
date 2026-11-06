"""Prueba de la versión web lite en un navegador de verdad (Playwright + Chromium sin ventana).

1. Construye la web (herramientas/construir_web.py) y la sirve en local.
2. Abre la página y espera a que la interfaz arranque (Pyodide + núcleo de Chirptenna).
3. En un Web Worker aparte, genera y exporta los 18 tipos a 868 y 2441,75 MHz con el mismo Pyodide que usa la web.
4. Pasa el DRC de KiCad a cada .kicad_pcb generado en el navegador (si hay kicad-cli).

Uso (desde la raíz):  python herramientas/prueba_web.py [--sin-drc]
Necesita:  pip install playwright  y  python -m playwright install chromium
           (o PRUEBA_WEB_CANAL=msedge para usar el Edge de Windows sin descargar Chromium)
Sale con código 1 si algo falla.
"""
import os
import sys
import json
import time
import base64
import tempfile
import threading
import subprocess
import http.server
import functools

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# Código del Worker de prueba: mismo Pyodide que motor.js (se lee de ahí para no duplicar la versión)
PRUEBA = r"""
const PYODIDE = '%PYODIDE%';
importScripts(PYODIDE + 'pyodide.js');
(async () => {
  const py = await loadPyodide({ indexURL: PYODIDE });
  await py.loadPackage(['numpy', 'shapely', 'micropip']);
  py.unpackArchive(await (await fetch('%ORIGEN%/py/antenas.zip')).arrayBuffer(), 'zip', { extractDir: '/home/pyodide' });
  await py.runPythonAsync("import micropip\nawait micropip.install('ezdxf')");
  const codigo = `
import io, json, time, zipfile, base64, traceback
from antenas import web_api as w
c = json.loads(w.catalogo())
out = {}
for t in c['tipos']:
    for f in (866.5, 2441.75):
        k = f"{t['clave']}_{f:g}MHz"
        t0 = time.time()
        try:
            e = {'clave': t['clave'], 'f_MHz': f, 'bw_MHz': 5}
            e['parametros'] = json.loads(w.dimensionar(json.dumps(e)))['parametros']
            g = json.loads(w.generar(json.dumps(e)))
            if 'error' in g:
                raise RuntimeError(g['error'])
            e['nombre'] = k
            z, info = w.exportar(json.dumps(e))
            out[k] = {'zip': base64.b64encode(z).decode(), 's': round(time.time() - t0, 2)}
        except Exception as ex:
            out[k] = {'error': f'{type(ex).__name__}: {ex}', 'traza': traceback.format_exc()[-800:]}
json.dumps(out)
`;
  postMessage(JSON.parse(await py.runPythonAsync(codigo)));
})().catch((e) => postMessage({ fallo: String(e) }));
"""


def servir(carpeta):
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta)
    manejador.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}'


def main():
    sin_drc = '--sin-drc' in sys.argv
    from playwright.sync_api import sync_playwright
    salida = tempfile.mkdtemp(prefix='chirptenna_web_')
    web = os.path.join(salida, 'web')
    subprocess.run([sys.executable, os.path.join(RAIZ, 'herramientas', 'construir_web.py'), web], check=True)
    with open(os.path.join(web, 'motor.js'), encoding='utf-8') as fh:
        pyodide = next(l.split("'")[1] for l in fh if l.startswith('const PYODIDE'))
    srv, origen = servir(web)
    fallos = []
    with sync_playwright() as pw:
        # PRUEBA_WEB_CANAL=msedge usa el Edge instalado (sin descargar Chromium)
        nav = pw.chromium.launch(channel=os.environ.get('PRUEBA_WEB_CANAL') or None)
        pag = nav.new_page()
        errores_consola = []
        pag.on('console', lambda m: errores_consola.append(m.text) if m.type == 'error' else None)
        t0 = time.time()
        pag.goto(origen + '/')
        # Se entra por la galería de tipos; al elegir uno se abre el diseño
        pag.wait_for_function("!document.getElementById('galeria').hidden"
                              " && document.querySelectorAll('#galeria .ficha').length >= 18", timeout=60_000)
        pag.click('#galeria .ficha')
        pag.wait_for_function("!document.getElementById('app').hidden && document.querySelector('#vista svg')",
                              timeout=180_000)
        print(f'Interfaz lista en {time.time() - t0:.0f} s')
        # Idiomas: cada uno cambia el botón de descargar y la banda estimada (esta última la traduce Python)
        for idioma, boton in (('de', 'Für KiCad herunterladen (.zip)'), ('fr', 'Télécharger pour KiCad (.zip)'),
                              ('en', 'Download for KiCad (.zip)'), ('es', 'Descargar para KiCad (.zip)')):
            pag.select_option('#idioma', idioma)
            try:
                pag.wait_for_function("(t) => document.getElementById('btn-exportar').textContent === t", arg=boton,
                                      timeout=20_000)
                pag.wait_for_function("() => /\\d/.test(document.getElementById('banda-estado').textContent)",
                                      timeout=60_000)
                print(f'  OK  idioma {idioma}')
            except Exception as ex:
                fallos.append(f'idioma {idioma}: {type(ex).__name__}')
                print(f'  MAL idioma {idioma}')
        codigo =PRUEBA.replace('%PYODIDE%', pyodide).replace('%ORIGEN%', origen)
        res = pag.evaluate("""(codigo) => new Promise((ok) => {
            const w = new Worker(URL.createObjectURL(new Blob([codigo], {type: 'text/javascript'})));
            w.onmessage = (e) => ok(e.data);
        })""", codigo)
        if errores_consola:
            fallos.append('errores en la consola: ' + ' | '.join(errores_consola[:5]))
        nav.close()
    srv.shutdown()
    if 'fallo' in res:
        print('El Worker de prueba no arranca:', res['fallo'])
        sys.exit(1)
    from antenas import exportar
    import zipfile
    tiempos = []
    for k, v in res.items():
        if 'error' in v:
            fallos.append(f"{k}: {v['error']}")
            print(f"  MAL {k}: {v['error']}\n{v['traza']}")
            continue
        tiempos.append(v['s'])
        carpeta = os.path.join(salida, 'zips', k)
        with zipfile.ZipFile(__import__('io').BytesIO(base64.b64decode(v['zip']))) as z:
            z.extractall(carpeta)
        drc = []
        if not sin_drc:
            for r, _, fs in os.walk(carpeta):
                for f in fs:
                    if f.endswith('.kicad_pcb'):
                        drc += exportar.drc(os.path.join(r, f))
        if drc:
            fallos.append(f'{k}: DRC ' + '; '.join(f'{t}: {d}' for t, _, d in drc[:3]))
        print(f"  {'MAL' if drc else 'OK '} {k:32s} {v['s']:5.2f} s  {'DRC sin errores' if not sin_drc and not drc else ''}")
    print(f'{len(res) - len(fallos)}/{len(res)} bien · media {sum(tiempos)/max(1, len(tiempos)):.2f} s, '
          f'máx. {max(tiempos, default=0):.2f} s por antena')
    if fallos:
        print('Fallos:\n  ' + '\n  '.join(fallos))
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
