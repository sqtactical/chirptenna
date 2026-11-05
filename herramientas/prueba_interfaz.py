"""Prueba de humo de la interfaz: arranca gui/app.py, abre cada pestaña y comprueba que responde sin errores.

Usa una biblioteca de diseños temporal (no toca la del usuario) y un puerto libre. No necesita navegador:
NiceGUI construye la página en el servidor, así que un fallo al montar una pestaña da un error 500 o una
traza en la salida del servidor.

Uso (desde la raíz):  python herramientas/prueba_interfaz.py [--puerto 8097]
Sale con código 1 si algo falla.
"""
import os
import sys
import time
import socket
import argparse
import tempfile
import subprocess
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PESTANAS = ('galeria', 'diseno', 'simulacion', 'fabricar', 'medir', 'disenos')


def puerto_libre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def pedir(url, intentos=1, espera=1.0):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.status, r.read().decode('utf-8', 'replace')
        except Exception as ex:
            ultimo = ex
            time.sleep(espera)
    return None, str(ultimo)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--puerto', type=int, default=0)
    a = ap.parse_args()
    puerto = a.puerto or puerto_libre()
    base = f'http://127.0.0.1:{puerto}'
    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        entorno = dict(os.environ, PYTHONIOENCODING='utf-8', CHIRPTENNA_ABRIR='0')
        registro = open(os.path.join(tmp, 'servidor.log'), 'w+', encoding='utf-8')
        proc = subprocess.Popen([sys.executable, os.path.join(RAIZ, 'gui', 'app.py'), '--puerto', str(puerto),
                                 '--disenos', os.path.join(tmp, 'disenos')],
                                cwd=RAIZ, env=entorno, stdout=registro, stderr=subprocess.STDOUT)
        try:
            estado, _ = pedir(base + '/', intentos=90)
            if estado is None:
                fallos.append('el servidor no arranca en 90 s')
            else:
                for pestana in PESTANAS:
                    for tema in ('claro', 'oscuro'):
                        estado, html = pedir(f'{base}/?pestana={pestana}&tema={tema}', intentos=3)
                        ok = estado == 200 and 'Chirptenna' in html
                        print(f"  {'OK ' if ok else 'MAL'} {pestana:11s} {tema:6s} HTTP {estado}")
                        if not ok:
                            fallos.append(f'{pestana}/{tema}: HTTP {estado}')
            if proc.poll() is not None:
                fallos.append(f'el servidor se ha cerrado (código {proc.returncode})')
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
            registro.seek(0)
            salida = registro.read()
            registro.close()
        if 'Traceback' in salida:
            fallos.append('traza de error en la salida del servidor')
        if fallos:
            print('--- salida del servidor ---')
            print(salida[-6000:])
    print('Fallos: ' + '; '.join(fallos) if fallos else 'Interfaz bien')
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
