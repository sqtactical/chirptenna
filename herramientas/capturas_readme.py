"""Regenera las capturas de docs/capturas/ (README y manuales).

    python herramientas/capturas_readme.py [--tema oscuro|claro] [--salida docs/capturas] [--lanzador script.py]

Qué hace: crea una biblioteca temporal con dos diseños simulados (un monopolo de Sierpinski y una Yagi con boom de
2,4 GHz, a partir de simulaciones ya hechas en `salidas/_validacion3` y `salidas/_validacion4`), arranca la interfaz
contra ella en el puerto 8091 y la fotografía con Edge sin ventana por CDP (espera real, para que Plotly dibuje).
`placa_yagi.png` no sale de aquí (es una vista de la placa y no depende de la interfaz).

`--lanzador`: script que arranque `gui/app.py` con los mismos argumentos; solo hace falta en el entorno virtualizado de la
sesión de Claude (lección 49 de CLAUDE.md), donde NiceGUI da 403 a Plotly.
Requisitos: Edge (o `EDGE` con otra ruta), el paquete `websockets` (lo trae NiceGUI) y las simulaciones citadas.
"""
import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 8091
CDP = 9333
EDGE = os.environ.get('EDGE', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')

DISENOS = [('monopolo_sierpinski_demo', 'salidas/_validacion3/monopolo_sierpinski_2441.75MHz'),
           ('yagi_2450_demo', 'salidas/_validacion4/yagi_boom_2441.75MHz_iteracion0_directores3')]


def crear_biblioteca(destino):
    """Guarda los dos diseños de demo (banda de 2,4 GHz) con su simulación."""
    os.environ['CHIRPTENNA_DISENOS'] = str(destino)
    sys.path.insert(0, str(RAIZ))
    from antenas import biblioteca, fabricacion, materiales
    sustrato = list(materiales.SUSTRATOS)[0]
    reglas = list(fabricacion.REGLAS)[0]
    for nombre, rel in DISENOS:
        ruta = RAIZ / rel
        r = json.loads((ruta / 'resultado.json').read_text(encoding='utf-8-sig'))
        biblioteca.guardar(nombre, r['clave'], r['parametros'], sustrato, reglas, 2441.75, 83.5)
        biblioteca.guardar_simulacion(nombre, str(ruta))


def casos(tema):
    # nombre, consulta, alto máximo del recorte, espera en s
    return [('galeria', f'?pestana=galeria&tema={tema}', 1460, 4),
            ('diseno', f'?diseno=monopolo_sierpinski_demo&pestana=diseno&tema={tema}', 1700, 8),
            ('simulacion', f'?diseno=yagi_2450_demo&pestana=simulacion&tema={tema}', 2700, 9),
            ('fabricar', f'?diseno=yagi_2450_demo&pestana=fabricar&tema={tema}', 2000, 6),
            ('medir', f'?diseno=yagi_2450_demo&pestana=medir&tema={tema}', 1300, 5)]


async def fotografiar(tema, salida, perfil):
    import websockets
    edge = subprocess.Popen([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                             f'--user-data-dir={perfil}', f'--remote-debugging-port={CDP}',
                             '--window-size=1280,1000', 'about:blank'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        pagina = None
        for _ in range(40):
            try:
                alvos = json.load(urllib.request.urlopen(f'http://127.0.0.1:{CDP}/json'))
                pagina = [a for a in alvos if a['type'] == 'page'][0]
                break
            except Exception:
                time.sleep(0.5)
        if pagina is None:
            raise RuntimeError('Edge no arrancó')
        async with websockets.connect(pagina['webSocketDebuggerUrl'], max_size=None) as ws:
            n = 0

            async def cmd(metodo, **params):
                nonlocal n
                n += 1
                await ws.send(json.dumps({'id': n, 'method': metodo, 'params': params}))
                while True:
                    r = json.loads(await ws.recv())
                    if r.get('id') == n:
                        return r.get('result', {})

            await cmd('Page.enable')
            await cmd('Emulation.setDeviceMetricsOverride', width=1280, height=1000, deviceScaleFactor=1, mobile=False)
            for nombre, consulta, alto, espera in casos(tema):
                await cmd('Page.navigate', url=f'http://127.0.0.1:{PUERTO}/{consulta}')
                await asyncio.sleep(espera)
                alto_pagina = (await cmd('Runtime.evaluate', expression='document.documentElement.scrollHeight',
                                         returnByValue=True))['result']['value']
                h = min(alto, alto_pagina)
                r = await cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
                              clip={'x': 0, 'y': 0, 'width': 1280, 'height': h, 'scale': 1})
                (salida / f'{nombre}.png').write_bytes(base64.b64decode(r['data']))
                print(f'{nombre}.png  1280 x {h}')
    finally:
        edge.terminate()
        try:
            edge.wait(10)
        except subprocess.TimeoutExpired:
            edge.kill()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tema', default='oscuro', choices=['oscuro', 'claro'])
    ap.add_argument('--salida', default=str(RAIZ / 'docs' / 'capturas'))
    ap.add_argument('--lanzador', default='')
    args = ap.parse_args()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        biblioteca = Path(tmp) / 'disenos'
        crear_biblioteca(biblioteca)
        guion = args.lanzador or str(RAIZ / 'gui' / 'app.py')
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        srv = subprocess.Popen([sys.executable, guion, '--puerto', str(PUERTO), '--disenos', str(biblioteca)],
                               cwd=str(RAIZ), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{PUERTO}/', timeout=2)
                    break
                except Exception:
                    time.sleep(1)
            asyncio.run(fotografiar(args.tema, salida, str(Path(tmp) / 'edge')))
        finally:
            srv.terminate()


if __name__ == '__main__':
    main()
