"""Simulación con MATLAB (Antenna Toolbox, método de momentos) de la misma placa que se simula con openEMS.

Es un segundo motor, independiente y más aproximado: sirve para contrastar una simulación de openEMS (frecuencia de resonancia,
S11 y directividad), no para sustituirla. No ajusta la frecuencia, no tiene malla adaptada ni GPU, y solo entiende placas
sencillas: cobre en F.Cu y B.Cu, un FR4 de dos capas y la alimentación en el borde. No usa la licencia de nadie más que la del
usuario: se lanza `matlab -batch` con `herramientas/verdad_caso.m`.

`disponible()` dice si hay MATLAB con la Antenna Toolbox; `no_soporta(antena)` dice por qué una antena no se puede simular aquí;
`simular(...)` devuelve el mismo diccionario que `simulacion.simular` (lo que usan `simular_cli` y la interfaz).
Los resultados se guardan en `%TEMP%\\antenas_matlab\\<hash>` (misma entrada, mismo resultado).
"""
import glob
import hashlib
import json
import math
import os
import subprocess
import tempfile
import time

import numpy as np
from shapely.geometry import MultiPolygon

from .i18n import tr

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASO_M = os.path.join(RAIZ, 'herramientas')
CACHE = os.path.join(tempfile.gettempdir(), 'antenas_matlab')
BORDE_COBRE = 0.5
PASO_TETA, PASO_PHI = 3.0, 6.0             # la misma rejilla del diagrama que openEMS (`simulacion.simular`)


def ejecutable():
    """Ruta de matlab.exe: `MATLAB_EXE` o la versión más nueva de `Program Files\\MATLAB`."""
    e = os.environ.get('MATLAB_EXE')
    if e and os.path.exists(e):
        return e
    c = sorted(glob.glob(r'C:\Program Files\MATLAB\*\bin\matlab.exe'))
    return c[-1] if c else None


def disponible():
    """(bool, motivo). Comprueba los archivos de la Antenna Toolbox sin arrancar MATLAB (que tarda ~20 s)."""
    exe = ejecutable()
    if not exe:
        return False, tr('no se encuentra MATLAB (define MATLAB_EXE con la ruta de matlab.exe)')
    raiz = os.path.dirname(os.path.dirname(exe))
    if not os.path.exists(os.path.join(raiz, 'toolbox', 'antenna', 'antenna', 'dipole.m')):
        return False, tr('MATLAB no tiene la Antenna Toolbox instalada')
    return True, ''


def no_soporta(antena, sustrato=None):
    """None si la antena se puede simular con MATLAB; si no, el motivo."""
    if antena.modulos:
        return tr('es una antena modular (varias placas)')
    if antena.reflector:
        return tr('lleva un reflector separado por aire')
    if antena.entorno:
        return tr('lleva un entorno (carcasa, batería o mano)')
    if antena.vias:
        return tr('lleva vías entre las dos caras')
    if antena.puerto.get('tipo') in ('pasante', 'coaxial'):
        return tr('se alimenta por un coaxial vertical, no por el borde')
    if sustrato is not None and getattr(sustrato, 'capas', 2) != 2:
        return tr('el sustrato no es de dos capas')
    if not antena.cobre('F.Cu') or antena.cobre('F.Cu').is_empty:
        return tr('no tiene cobre en la cara superior')
    return None


def anillos(geom):
    """Anillos de una geometría de shapely como lista de {poli, hueco, x, y} (mm)."""
    if geom is None or geom.is_empty:
        return []
    polis = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for k, p in enumerate(polis, start=1):
        out.append({'poli': k, 'hueco': 0, 'x': [round(v, 5) for v in p.exterior.coords.xy[0][:-1]],
                    'y': [round(v, 5) for v in p.exterior.coords.xy[1][:-1]]})
        for h in p.interiors:
            out.append({'poli': k, 'hueco': 1, 'x': [round(v, 5) for v in h.coords.xy[0][:-1]],
                        'y': [round(v, 5) for v in h.coords.xy[1][:-1]]})
    return out


def entrada(antena, sustrato, malla_mm, f_ini_MHz, f_fin_MHz, puntos, f_diagrama_MHz=None):
    """Diccionario que lee `herramientas/verdad_caso.m`."""
    bx, by = antena.puerto['borde']
    dx, dy = antena.puerto['direccion']
    u = antena.puerto.get('inicio_mm', BORDE_COBRE) + 0.25         # un poco dentro de la línea, para que la sonda toque cobre
    cx, cy = antena.contorno.exterior.coords.xy
    d = {'cobre_superior': anillos(antena.cobre('F.Cu')), 'cobre_inferior': anillos(antena.cobre('B.Cu')),
         'contorno': {'x': list(cx[:-1]), 'y': list(cy[:-1])},
         'er': sustrato.er, 'tand': sustrato.tand, 'h_mm': sustrato.h,
         'alimentacion_mm': [bx + dx*u, by + dy*u],
         'f_ini_MHz': f_ini_MHz, 'f_fin_MHz': f_fin_MHz, 'puntos': int(puntos), 'malla_mm': malla_mm}
    if f_diagrama_MHz:
        d['f_diagrama_MHz'] = f_diagrama_MHz
        d['theta_deg'] = [float(t) for t in np.arange(0, 181, PASO_TETA)]
        d['phi_deg'] = [float(p) for p in np.arange(0, 361, PASO_PHI)]
    return d


def _malla_por_defecto(f_obj_Hz):
    """Paso del MoM: λ/50 en el aire, entre 1 y 4 mm."""
    return round(float(min(4.0, max(1.0, 299792458.0/f_obj_Hz*1e3/50))), 2)


def _lanzar(datos, progreso):
    """Ejecuta MATLAB (o usa la caché) y devuelve el JSON de salida."""
    texto = json.dumps(datos, sort_keys=True)
    clave = hashlib.sha1(texto.encode()).hexdigest()[:16]
    carpeta = os.path.join(CACHE, clave)
    sal = os.path.join(carpeta, 'salida.json')
    if os.path.exists(sal):
        progreso(tr('MATLAB: resultado ya calculado (caché).'))
    else:
        os.makedirs(carpeta, exist_ok=True)
        ent = os.path.join(carpeta, 'entrada.json')
        with open(ent, 'w', encoding='utf-8') as f:
            f.write(texto)
        progreso(tr('MATLAB: simulando {0} puntos con malla de {1:g} mm (puede tardar varios minutos)…', datos['puntos'], datos['malla_mm']))
        exe = ejecutable()
        r = subprocess.run([exe, '-batch', f"addpath('{CASO_M}'); verdad_caso('{ent}','{sal}')"],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=3*3600)
        if not os.path.exists(sal):
            raise RuntimeError(tr('MATLAB no dio resultado: {0}', (r.stdout + r.stderr).strip()[-500:]))
    with open(sal, encoding='utf-8') as f:
        return json.load(f)


def simular(antena, sustrato, f_obj, rango=(0.6, 1.4), puntos=None, malla_mm=None, progreso=print):
    """Simula `antena` con MATLAB. `f_obj` y `rango` como en `simulacion.simular` (Hz y factores). Mismo diccionario de salida."""
    from . import simulacion
    motivo = no_soporta(antena, sustrato)
    if motivo:
        raise ValueError(tr('MATLAB no puede simular esta antena: {0}.', motivo))
    ok, porque = disponible()
    if not ok:
        raise RuntimeError(tr('MATLAB no está disponible: {0}.', porque))
    t0 = time.time()
    malla_mm = malla_mm or _malla_por_defecto(f_obj)
    puntos = puntos or (45 if rango[1]/rango[0] > 3 else 25)
    datos = entrada(antena, sustrato, malla_mm, rango[0]*f_obj/1e6, rango[1]*f_obj/1e6, puntos, f_diagrama_MHz=f_obj/1e6)
    m = _lanzar(datos, progreso)
    f = np.asarray(m['f_MHz'], float)*1e6
    s11 = np.asarray(m['s11_re'], float) + 1j*np.asarray(m['s11_im'], float)
    zin = 50*(1 + s11)/(1 - s11)
    s11_db = 20*np.log10(np.abs(s11))
    fcen, flo, fhi, fmn, smn = simulacion.centro_banda(f, s11_db)
    avisos = [tr('Simulación de MATLAB (método de momentos): más aproximada que openEMS, sin ajuste automático ni eficiencia. '
                 'Úsala para contrastar la resonancia y la directividad.')]
    criterio = tr('centro de la banda a −10 dB')
    if flo is None:
        x = np.imag(zin)
        cruces = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
        if len(cruces):
            i = cruces[np.argmin(np.abs(f[cruces] - f_obj))]
            fcen = f[i] + (f[i + 1] - f[i])*(-x[i])/(x[i + 1] - x[i])
            criterio = tr('reactancia nula en los terminales (no llega a −10 dB cerca del objetivo)')
        else:
            fcen = fmn
            criterio = tr('mínimo de S11 (no llega a −10 dB)')
        avisos.append(tr('No llega a −10 dB cerca del objetivo (mínimo {0:.1f} dB): adaptación pobre; resonancia por {1}.', smn, criterio))
    ancho = simulacion.ancho_minimo(antena.cobre('F.Cu'))
    if ancho and ancho < malla_mm/2:           # una tira de 1,5 mm con malla de 2,5 mm sí se resuelve (dipolo: ±2 % al afinar a 1,2 mm)
        avisos.append(tr('Hay pistas de {0:.2f} mm, más finas que la malla de {1:g} mm: el resultado es solo orientativo.', ancho, malla_mm))
    if antena.ajuste and antena.ajuste.get('componentes'):
        avisos.append(tr('MATLAB no modela los componentes de ajuste (red en π, puentes): se simula la placa sin ellos.'))
    r = {'f_Hz': f, 's11': s11, 'zin': zin, 'f_resonancia_Hz': fcen, 'banda_Hz': (flo, fhi), 'f_min_s11_Hz': fmn,
         's11_min_dB': smn, 'celdas': 0, 'paso_malla_mm': malla_mm, 'criterio': criterio, 'rango_Hz': (rango[0]*f_obj, rango[1]*f_obj),
         'tiempo_s': round(time.time() - t0, 1), 'avisos': avisos, 'precision': 'MATLAB'}
    grid = m.get('D_grid')
    if grid:
        r['theta'] = np.arange(0, 181, PASO_TETA)
        r['phi'] = np.arange(0, 361, PASO_PHI)
        r['directividad_dBi_grid'] = np.asarray(grid, float)
        r['directividad_dBi'] = float(np.nanmax(r['directividad_dBi_grid']))
    return r


def resumen(r):
    """Resumen de un resultado de MATLAB para guardarlo junto al de openEMS (sin curvas)."""
    flo, fhi = r['banda_Hz']
    return {'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2), 'criterio': r.get('criterio'),
            'banda_MHz': None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)],
            's11_min_dB': round(r['s11_min_dB'], 1), 'f_min_s11_MHz': round(r['f_min_s11_Hz']/1e6, 2),
            'directividad_dBi': round(r['directividad_dBi'], 2) if 'directividad_dBi' in r and not math.isnan(r['directividad_dBi']) else None,
            'paso_malla_mm': r['paso_malla_mm'], 'tiempo_s': r['tiempo_s'], 'avisos': r['avisos']}
