"""Cola FIFO de simulaciones: cada trabajo es un fichero numerado en una carpeta y cada proceso
«trabajar» coge el siguiente (renombrarlo es atómico: dos procesos no cogen el mismo). Con dos
procesos «trabajar» hay dos simulaciones a la vez, el máximo para este portátil.

La carpeta está fuera de OneDrive (%LOCALAPPDATA%\\antenas\\cola): pendientes/, en_curso/, hechos/ y
registros/ (salida de cada trabajo). Los comandos se ejecutan desde la raíz del proyecto.

Uso:
  python herramientas/cola.py añadir <nombre> <comando> [args...]   -> al final de la cola
  python herramientas/cola.py ver                                   -> pendientes, en curso y hechos
  python herramientas/cola.py trabajar [--hilos 6]                  -> procesa hasta vaciar la cola
                                                                       (espera 10 min a trabajos nuevos)
Para cambiar el orden basta con renombrar los ficheros de pendientes/ (se cogen por orden de nombre).
"""
import os
import sys
import json
import time
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLA = os.path.join(os.environ.get('LOCALAPPDATA', RAIZ), 'antenas', 'cola')
CARPETAS = {n: os.path.join(COLA, n) for n in ('pendientes', 'en_curso', 'hechos', 'registros')}
ESPERA_MAX_S = 600


def _preparar():
    for c in CARPETAS.values():
        os.makedirs(c, exist_ok=True)


def añadir(nombre, comando):
    _preparar()
    existentes = [f for c in ('pendientes', 'en_curso', 'hechos') for f in os.listdir(CARPETAS[c])]
    n = max([int(f[:4]) for f in existentes if f[:4].isdigit()] + [0]) + 1
    fichero = f'{n:04d}_{nombre}.json'
    with open(os.path.join(CARPETAS['pendientes'], fichero), 'w', encoding='utf-8') as fh:
        json.dump({'nombre': nombre, 'comando': comando, 'añadido': time.strftime('%Y-%m-%d %H:%M:%S')}, fh,
                  ensure_ascii=False, indent=2)
    print('Añadido', fichero)


def ver():
    _preparar()
    for c in ('en_curso', 'pendientes', 'hechos'):
        print(f'--- {c}')
        for f in sorted(os.listdir(CARPETAS[c])):
            t = json.load(open(os.path.join(CARPETAS[c], f), encoding='utf-8'))
            extra = ''
            if c == 'hechos':
                extra = f"  (código {t.get('codigo')}, {t.get('duracion_min')} min)"
            elif c == 'en_curso':
                extra = f"  (desde {t.get('inicio')}, proceso {t.get('trabajador')})"
            print(f'  {f}{extra}')


def _coger():
    """Mueve el primer pendiente a en_curso; None si no hay o si otro proceso se lo llevó antes."""
    for f in sorted(os.listdir(CARPETAS['pendientes'])):
        try:
            os.rename(os.path.join(CARPETAS['pendientes'], f), os.path.join(CARPETAS['en_curso'], f))
            return f
        except OSError:
            continue                      # lo cogió otro proceso
    return None


def trabajar(hilos):
    _preparar()
    yo = os.getpid()
    sin_trabajo = time.time()
    while True:
        f = _coger()
        if f is None:
            if time.time() - sin_trabajo > ESPERA_MAX_S:
                print('Cola vacía: fin', flush=True)
                return
            time.sleep(30)
            continue
        ruta = os.path.join(CARPETAS['en_curso'], f)
        t = json.load(open(ruta, encoding='utf-8'))
        t.update(inicio=time.strftime('%Y-%m-%d %H:%M:%S'), trabajador=yo)
        json.dump(t, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'=== {f} ({t["inicio"]})', flush=True)
        entorno = dict(os.environ, ANTENAS_HILOS=str(hilos), PYTHONIOENCODING='utf-8')
        t0 = time.time()
        with open(os.path.join(CARPETAS['registros'], f.replace('.json', '.log')), 'w', encoding='utf-8') as reg:
            cod = subprocess.run(t['comando'], cwd=RAIZ, env=entorno, stdout=reg, stderr=subprocess.STDOUT).returncode
        t.update(codigo=cod, fin=time.strftime('%Y-%m-%d %H:%M:%S'), duracion_min=round((time.time() - t0)/60, 1))
        json.dump(t, open(os.path.join(CARPETAS['hechos'], f), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        os.remove(ruta)
        print(f'--- {f}: código {cod}, {t["duracion_min"]} min', flush=True)
        sin_trabajo = time.time()


if __name__ == '__main__':
    orden = sys.argv[1] if len(sys.argv) > 1 else 'ver'
    if orden == 'añadir':
        añadir(sys.argv[2], [sys.executable if a == 'python' else a for a in sys.argv[3:]])
    elif orden == 'trabajar':
        trabajar(int(sys.argv[sys.argv.index('--hilos') + 1]) if '--hilos' in sys.argv else 6)
    else:
        ver()
