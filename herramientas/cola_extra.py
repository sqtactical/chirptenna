"""Cola de trabajos de simulación que se ejecuta cuando la campaña y los barridos de prueba han terminado.

Lee salidas/_cola/pendientes.txt (una orden por línea; las que empiezan por # se ignoran), espera a que no haya
`campana.py` ni barridos H_/F_ en marcha y va ejecutando las líneas por orden, releyendo el fichero entre una y otra
(así se pueden añadir órdenes al final mientras corre). Lo hecho se anota en salidas/_cola/hechas.txt.
Uso (desde la raíz):  python herramientas/cola_extra.py
"""
import os
import sys
import time
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, 'salidas', '_cola')
os.makedirs(CARPETA, exist_ok=True)
PEND, HECHAS = os.path.join(CARPETA, 'pendientes.txt'), os.path.join(CARPETA, 'hechas.txt')


def ocupado():
    """¿Siguen la campaña o los barridos de prueba (H_, F_)?"""
    r = subprocess.run(['powershell', '-NoProfile', '-Command',
                        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and ($_.CommandLine -match 'campana\\.py' "
                        "-or $_.CommandLine -match 'etiqueta (H|F)_') } | Measure-Object | ForEach-Object Count"],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip() or 0) > 0
    except ValueError:
        return True


def siguiente():
    hechas = set(open(HECHAS, encoding='utf-8').read().splitlines()) if os.path.exists(HECHAS) else set()
    for linea in open(PEND, encoding='utf-8').read().splitlines():
        if linea.strip() and not linea.lstrip().startswith('#') and linea not in hechas:
            return linea
    return None


def main():
    while ocupado():
        time.sleep(120)
    while True:
        linea = siguiente()
        if linea is None:
            print('Cola vacía', flush=True)
            return
        print(f'[{time.strftime("%H:%M")}] {linea}', flush=True)
        subprocess.run(linea.replace('python ', f'"{sys.executable}" -X utf8 ', 1), shell=True, cwd=RAIZ,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        open(HECHAS, 'a', encoding='utf-8').write(linea + '\n')


if __name__ == '__main__':
    main()