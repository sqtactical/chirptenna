"""Aceleración por GPU de openEMS (experimental, rama gpu-pruebas).

El openEMS oficial 0.37 no trae motor GPU: está en `master` de thliebig/openEMS (`--engine=gpu`). Hay que
compilarlo aparte (ver RETOMAR.md). Este módulo busca ese `openEMS.exe`, comprueba que ve una GPU y lanza la
simulación con él: la API de Python del 0.37 no sabe elegir motor, así que se escribe el XML con
`FDTD.Write2XML` y se ejecuta el binario con GPU.

En esta rama se usa por defecto si está disponible; `ANTENAS_GPU=0` fuerza la CPU (ajustes finales). `OPENEMS_GPU_DIR` apunta a la carpeta con el `openEMS.exe` con
GPU (por defecto `%LOCALAPPDATA%\\Programs\\gpu-build\\opt\\bin`). Si algo falla se avisa y se usa la CPU.
"""
import os
import subprocess
import sys

_DIR_DEFECTO = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'gpu-build', 'opt', 'bin')
_cache = {}


def carpeta():
    return os.environ.get('OPENEMS_GPU_DIR') or _DIR_DEFECTO


def ejecutable():
    """Ruta del openEMS con GPU, o None si no está instalado."""
    exe = os.path.join(carpeta(), 'openEMS.exe' if sys.platform == 'win32' else 'openEMS')
    return exe if os.path.exists(exe) else None


def _entorno():
    env = dict(os.environ)
    # las DLL de este openEMS (y CUDA) tienen que encontrarse antes que las del 0.37
    extra = [carpeta(), os.path.join(os.path.dirname(carpeta()), 'cuda', 'bin')]
    env['PATH'] = os.pathsep.join(extra + [env.get('PATH', '')])
    return env


def disponible():
    """(True, descripción) si el openEMS con GPU existe y encuentra una GPU; si no, (False, motivo)."""
    if 'r' in _cache:
        return _cache['r']
    exe = ejecutable()
    if exe is None:
        r = (False, f'no se encuentra openEMS con GPU en {carpeta()}')
    else:
        try:
            p = subprocess.run([exe, '--engine=gpu', '--help'], capture_output=True, text=True, timeout=60,
                               env=_entorno(), encoding='utf-8', errors='replace')
            salida = (p.stdout or '') + (p.stderr or '')
            r = (True, exe) if 'engine' in salida.lower() else (False, 'este openEMS no tiene la opción --engine')
        except (OSError, subprocess.SubprocessError) as e:
            r = (False, str(e))
    _cache['r'] = r
    return r


def activa():
    """¿Hay que usar la GPU? Sí si el openEMS con GPU está disponible, salvo que ANTENAS_GPU=0 (en esta rama es
    el comportamiento por defecto: se itera en GPU y los ajustes finales se hacen en CPU con ANTENAS_GPU=0)."""
    return os.environ.get('ANTENAS_GPU', '') != '0' and disponible()[0]


def ejecutar(fdtd, sim_path, progreso=print):
    """Simula `sim_path` con la GPU. Devuelve True si lo ha hecho; False si hay que usar la CPU."""
    exe = ejecutable()
    try:
        os.makedirs(sim_path, exist_ok=True)
        xml = os.path.join(sim_path, 'openEMS.xml')
        fdtd.Write2XML(xml)
        p = subprocess.run([exe, xml, '--engine=gpu', '-v', '1'], cwd=sim_path, env=_entorno(),
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
    except (OSError, subprocess.SubprocessError) as e:
        progreso(f'GPU no disponible ({e}): se usa la CPU')
        return False
    registro = (p.stdout or '') + (p.stderr or '')
    with open(os.path.join(sim_path, 'registro_gpu.txt'), 'w', encoding='utf-8') as fh:
        fh.write(registro)
    if p.returncode != 0:
        ultimas = ' | '.join(l.strip() for l in registro.splitlines()[-3:] if l.strip())
        progreso(f'La GPU ha fallado ({ultimas}): se usa la CPU')
        return False
    for linea in registro.splitlines():
        if 'GPU' in linea and ('backend' in linea or 'device' in linea):
            progreso(linea.strip())
            break
    return True
