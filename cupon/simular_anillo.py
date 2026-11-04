"""Simula en openEMS un anillo del cupón (aislado, con alimentaciones cortas) y da S21.

Sirve para comprobar que el modo de diseño cae donde se espera y que el pico de
S21 es medible con el NanoVNA (> ~-35 dB). Más adelante, con varias εr, da la
tabla εr -> f_resonancia para interpretar las medidas.

Uso: python simular_anillo.py <R868|R2G4|R5G8> [--er 4.5] [--fmin MHz] [--fmax MHz]
"""
import os
import sys
import json
import time
import argparse
import tempfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'fase0'))
import comun   # noqa: E402  (antes que openEMS)
from CSXCAD import ContinuousStructure   # noqa: E402
from openEMS import openEMS   # noqa: E402
from openEMS.physical_constants import C0, EPS0   # noqa: E402

TAND = 0.02
L_ALIM = 12.0     # alimentación simulada [mm] (en la placa es más larga; no afecta a f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('anillo')
    ap.add_argument('--er', type=float, default=4.5)
    ap.add_argument('--fmin', type=float, default=None)
    ap.add_argument('--fmax', type=float, default=None)
    a = ap.parse_args()
    # el anillo puede estar en cualquiera de las placas (cupon_A, cupon_B)
    for placa in ('cupon_A', 'cupon_B'):
        dis = json.load(open(os.path.join(AQUI, placa, 'diseno.json'), encoding='utf-8'))
        if a.anillo in dis['estructuras']:
            break
    e = dis['estructuras'][a.anillo]
    h, W, g, r = dis['material']['h_mm'], e['ancho_mm'], e['gap_mm'], e['radio_medio_mm']
    f1 = e['f_diseno_GHz']*1e9/e['modo_diseno']
    fmin = a.fmin*1e6 if a.fmin else 0.6*f1
    fmax = a.fmax*1e6 if a.fmax else min(1.4*e['f_diseno_GHz']*1e9, 3.0e9)
    f0, fc = (fmin + fmax)/2, (fmax - fmin)/2

    # el radio va en la clave: el anillo cambió de radio con la corrección ×0,93 de los cupones de 100 mm
    sim_path = os.path.join(tempfile.gettempdir(), f'fase0_anillo_{a.anillo}_r{r:.3f}_er{a.er:.3f}')
    FDTD = openEMS(NrTS=600000, EndCriteria=1e-5)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)

    R_ext = r + W/2
    y_a = -(R_ext + g)            # extremo de la alimentación superior
    y_b = +(R_ext + g)
    yp_a, yp_b = y_a - L_ALIM, y_b + L_ALIM
    marg = 6.0
    X = R_ext + marg
    kappa = 2*np.pi*f0*EPS0*a.er*TAND
    CSX.AddMaterial('FR4', epsilon=a.er, kappa=kappa).AddBox([-X, yp_a, 0], [X, yp_b, h], priority=0)
    masa = CSX.AddMetal('masa'); masa.AddBox([-X, yp_a, 0], [X, yp_b, 0], priority=10)
    cobre = CSX.AddMetal('cobre')
    # anillo como polígono (corona) aproximado por un polígono de muchos lados en dos mitades
    t = np.linspace(0, np.pi, 181)
    for s in (1, -1):
        xs = np.concatenate([(r + W/2)*np.cos(t), (r - W/2)*np.cos(t[::-1])])
        ys = s*np.concatenate([(r + W/2)*np.sin(t), (r - W/2)*np.sin(t[::-1])])
        cobre.AddPolygon([xs, ys], norm_dir=2, elevation=h, priority=10)
    cobre.AddBox([-W/2, yp_a, h], [W/2, y_a, h], priority=10)
    cobre.AddBox([-W/2, y_b, h], [W/2, yp_b, h], priority=10)
    fino = min(0.25, g/2)
    lam_min = C0/fmax*1e3
    mesh.AddLine('x', np.concatenate([[-X - 20, X + 20], np.linspace(-W/2, W/2, 5),
                                      np.arange(-R_ext, R_ext + 0.01, 0.5)]))
    mesh.AddLine('y', np.concatenate([[yp_a, yp_b, -R_ext - 20 + yp_a, yp_b + 20],
                                      np.arange(y_a - 1, y_a + 1.01, fino), np.arange(y_b - 1, y_b + 1.01, fino),
                                      np.arange(-R_ext, R_ext + 0.01, 0.5), np.linspace(yp_a, yp_a + 6, 7),
                                      np.linspace(yp_b - 6, yp_b, 7)]))
    mesh.AddLine('z', np.concatenate([np.linspace(0, h, 5), [-15, h + 20]]))
    mesh.SmoothMeshLines('all', lam_min/20, 1.3)
    print('Malla:', [len(mesh.GetLines(d)) for d in 'xyz'])
    # puertos MSL (necesitan la malla ya hecha), con de-embedding hasta el hueco
    p1 = FDTD.AddMSLPort(1, cobre, [-W/2, yp_a, h], [W/2, yp_a + 6, 0], 'y', 'z',
                         excite=1, FeedShift=1.0, MeasPlaneShift=L_ALIM, priority=20)
    p2 = FDTD.AddMSLPort(2, cobre, [-W/2, yp_b, h], [W/2, yp_b - 6, 0], 'y', 'z',
                         MeasPlaneShift=L_ALIM, priority=20)

    if not os.path.exists(os.path.join(sim_path, 'port_ut_2')):
        t0 = time.time()
        FDTD.Run(sim_path, cleanup=True, verbose=0)
        print(f'Tiempo: {time.time() - t0:.0f} s')
    f = np.linspace(fmin, fmax, 2001)
    for p in (p1, p2):
        p.CalcPort(sim_path, f, ref_impedance=50)
    s11 = p1.uf_ref/p1.uf_inc
    s21 = p2.uf_ref/p1.uf_inc
    s21_db = 20*np.log10(np.abs(s21))
    # picos de S21
    picos = [i for i in range(1, len(f) - 1) if s21_db[i] > s21_db[i - 1] and s21_db[i] >= s21_db[i + 1]
             and s21_db[i] > s21_db.max() - 10]
    res = {'anillo': a.anillo, 'er': a.er, 'picos': [{'f_GHz': round(f[i]/1e9, 4), 'S21_dB': round(float(s21_db[i]), 1)}
                                                     for i in picos],
           'f_diseno_modos_GHz': e['modos_en_rango_GHz']}
    os.makedirs(os.path.join(AQUI, 'simulaciones'), exist_ok=True)
    base = os.path.join(AQUI, 'simulaciones', f'{a.anillo}_r{r:.2f}_er{a.er:.3f}')
    json.dump(res, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    fig, ax = plt.subplots(figsize=(9, 4.5), tight_layout=True)
    ax.plot(f/1e9, s21_db, 'b-', label='S21'); ax.plot(f/1e9, 20*np.log10(np.abs(s11)), 'k--', lw=0.8, label='S11')
    for m in e['modos_en_rango_GHz']:
        ax.axvline(m, color='r', ls=':', lw=1)
    ax.set_xlabel('GHz'); ax.set_ylabel('dB'); ax.grid(); ax.legend()
    ax.set_title(f'{a.anillo}, εr={a.er}: picos ' + ', '.join(f"{p['f_GHz']} GHz ({p['S21_dB']} dB)" for p in res['picos']))
    fig.savefig(base + '.png', dpi=120)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
