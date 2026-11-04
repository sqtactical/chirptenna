"""Utilidades comunes de la Fase 0.

Importar este módulo ANTES que openEMS/CSXCAD: fija CSXCAD_INSTALL_PATH para
que Python encuentre las DLL sin tocar las variables de entorno del sistema.
"""
import os
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OPENEMS_DIR = os.environ.get(
    'CSXCAD_INSTALL_PATH',
    os.path.join(os.environ['LOCALAPPDATA'], 'Programs', 'openEMS', 'openEMS'))
os.environ['CSXCAD_INSTALL_PATH'] = OPENEMS_DIR

DIR_RESULTADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
os.makedirs(DIR_RESULTADOS, exist_ok=True)


def ancho_microstrip(z0, er, h):
    """Ancho de pista microstrip para impedancia z0 (síntesis de Wheeler/Hammerstad).

    Devuelve el ancho en las mismas unidades que h (espesor del sustrato).
    """
    a = z0/60*np.sqrt((er + 1)/2) + (er - 1)/(er + 1)*(0.23 + 0.11/er)
    wh = 8*np.exp(a)/(np.exp(2*a) - 2)
    if wh > 2:
        b = 377*np.pi/(2*z0*np.sqrt(er))
        wh = 2/np.pi*(b - 1 - np.log(2*b - 1)
                      + (er - 1)/(2*er)*(np.log(b - 1) + 0.39 - 0.61/er))
    return wh*h


def eps_eff_microstrip(er, h, w):
    """Permitividad efectiva de una microstrip (Hammerstad, w/h >= 1)."""
    return (er + 1)/2 + (er - 1)/2/np.sqrt(1 + 12*h/w)


def quitar_linea(f, zin, z0, eps_eff, longitud_m):
    """Traslada Zin a través de una línea sin pérdidas (de-embedding).

    Devuelve la impedancia vista al final de la línea, es decir, en los
    terminales de la antena.
    """
    t = np.tan(2*np.pi*f*np.sqrt(eps_eff)/299792458.0*longitud_m)
    return z0*(zin - 1j*z0*t)/(z0 - 1j*zin*t)


def centro_banda(f, s11_db, umbral=-10.0):
    """Centro geométrico de la banda a -10 dB (None si no llega)."""
    bw = ancho_banda(f, s11_db, umbral)
    return None if bw is None else float(np.sqrt(bw[0]*bw[1]))


def minimo_s11(f, s11_db):
    """Frecuencia y valor del mínimo de |S11|, con interpolación parabólica."""
    i = int(np.argmin(s11_db))
    if 0 < i < len(f) - 1:
        y0, y1, y2 = s11_db[i-1:i+2]
        den = y0 - 2*y1 + y2
        d = 0.5*(y0 - y2)/den if den != 0 else 0.0
        return f[i] + d*(f[1] - f[0]), y1 - 0.25*(y0 - y2)*d
    return f[i], s11_db[i]


def ancho_banda(f, s11_db, umbral=-10.0):
    """Banda contigua alrededor del mínimo con |S11| < umbral. None si no llega."""
    i = int(np.argmin(s11_db))
    if s11_db[i] >= umbral:
        return None
    lo = i
    while lo > 0 and s11_db[lo - 1] < umbral:
        lo -= 1
    hi = i
    while hi < len(f) - 1 and s11_db[hi + 1] < umbral:
        hi += 1
    return f[lo], f[hi]


def cruce_reactancia(f, zin):
    """Primera frecuencia donde Im{Zin} pasa de negativo a positivo (resonancia serie)."""
    x = np.imag(zin)
    idx = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
    if not len(idx):
        return None, None
    i = idx[0]
    t = -x[i]/(x[i+1] - x[i])
    fr = f[i] + t*(f[i+1] - f[i])
    r = np.real(zin[i]) + t*(np.real(zin[i+1]) - np.real(zin[i]))
    return fr, r


def guardar_json(nombre, datos):
    ruta = os.path.join(DIR_RESULTADOS, nombre)
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, indent=2, ensure_ascii=False)
    return ruta


def guardar_figura(fig, nombre):
    ruta = os.path.join(DIR_RESULTADOS, nombre)
    fig.savefig(ruta, dpi=130)
    plt.close(fig)
    return ruta
