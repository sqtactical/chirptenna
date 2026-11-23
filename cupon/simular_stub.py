"""Simula en openEMS 3D un stub abierto del cupón C (una línea de 50 Ω que acaba en circuito abierto) medido en S11 en el borde de la placa, con y sin una muestra de
plástico encima. Sirve para validar el modelo de `antenas/plastico.py` y calibrar su corrección.

Un stub abierto de largo L resuena (X = 0 con pendiente positiva, R mínima) cuando L = λg/4, 3λg/4, 5λg/4…: f_n = (2n − 1)·c/(4·L·√εeff). La muestra sube el εeff y baja f_n; su
pérdida sube R en la resonancia. Se mide con un solo puerto (S11), como el NanoVNA y Chirptenna VNA.

Uso: python simular_stub.py <S43|S59|S86|largo_mm> [--er 4.5] [--tand 0.02] [--muestra εr,tanδ,grosor,ancho[,y_ini,y_fin]] [--fmin MHz] [--fmax MHz] [--fin 1e-6]
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
sys.path.insert(0, os.path.dirname(AQUI))
import comun   # noqa: E402  (antes que openEMS)
from CSXCAD import ContinuousStructure   # noqa: E402
from openEMS import openEMS   # noqa: E402
from openEMS.physical_constants import C0, EPS0   # noqa: E402

LARGOS = {'S43': 43.0, 'S59': 59.0, 'S86': 86.0}     # distancia del borde de la placa al extremo abierto [mm]
H, W = 1.6, 3.01
L_ALIM = 10.0                                         # alimentación simulada antes del borde [mm]
W_PAD, Y_PAD, Y_TAPER = 1.27, 3.4, 5.7                      # pad del SMA, fin del pad y fin de la transición cónica (como cupon/generar_cupon.py) [mm]


def cruces_x(f, z):
    """Resonancias serie: cruces de X por cero con pendiente positiva. Devuelve [(f, R, dX/df)]."""
    x, r = z.imag, z.real
    out = []
    for i in range(len(f) - 1):
        if x[i] < 0 <= x[i + 1]:
            t = -x[i]/(x[i + 1] - x[i])
            out.append((float(f[i] + t*(f[i + 1] - f[i])), float(r[i] + t*(r[i + 1] - r[i])), float((x[i + 1] - x[i])/(f[i + 1] - f[i]))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stub')
    ap.add_argument('--er', type=float, default=4.5)
    ap.add_argument('--tand', type=float, default=0.02)
    ap.add_argument('--muestra', default=None)
    ap.add_argument('--mesa', default=None, help='εr,tanδ,grosor[mm]: bloque (madera, etc.) pegado bajo la masa, que llena todo el dominio en x e y')
    ap.add_argument('--fmin', type=float, default=300.0)
    ap.add_argument('--fmax', type=float, default=3000.0)
    ap.add_argument('--fin', type=float, default=1e-6)
    ap.add_argument('--pasos', type=int, default=2000000)
    a = ap.parse_args()
    largo = LARGOS.get(a.stub) or float(a.stub)
    mu = [float(v) for v in a.muestra.split(',')] if a.muestra else None
    if mu:
        er_m, tand_m, t_m, ancho_m = mu[:4]
        y0_m = mu[4] if len(mu) > 4 else 4.0              # la muestra empieza a 4 mm del borde (hay un conector)
        y1_m = mu[5] if len(mu) > 5 else largo + 3.0
    me = [float(v) for v in a.mesa.split(',')] if a.mesa else None
    f0, fc = (a.fmin + a.fmax)/2*1e6, (a.fmax - a.fmin)/2*1e6
    sufijo = ('' if not mu else '_mu' + '_'.join(f'{v:g}' for v in mu)) + ('' if not me else '_mesa' + '_'.join(f'{v:g}' for v in me))
    sim_path = os.path.join(tempfile.gettempdir(), f'fase0_stub_{largo:g}_er{a.er:.3f}_tan{a.tand:g}{sufijo}')

    FDTD = openEMS(NrTS=a.pasos, EndCriteria=a.fin)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
    X = 14.0
    y_a, y_b = -L_ALIM, largo + 10.0
    kappa = 2*np.pi*f0*EPS0*a.er*a.tand
    CSX.AddMaterial('FR4', epsilon=a.er, kappa=kappa).AddBox([-X, y_a, 0], [X, y_b, H], priority=0)
    if mu:
        CSX.AddMaterial('muestra', epsilon=er_m, kappa=2*np.pi*f0*EPS0*er_m*tand_m).AddBox(
            [-ancho_m/2, y0_m, H], [ancho_m/2, y1_m, H + t_m], priority=1)
    if me:
        er_t, tand_t, t_t = me
        CSX.AddMaterial('mesa', epsilon=er_t, kappa=2*np.pi*f0*EPS0*er_t*tand_t).AddBox(
            [-X - 20, y_a - 20, -t_t], [X + 20, y_b + 20, 0], priority=1)
    CSX.AddMetal('masa').AddBox([-X, y_a, 0], [X, y_b, 0], priority=10)
    cobre = CSX.AddMetal('cobre')
    # línea de alimentación de 50 Ω hasta el borde (el plano de medida) y, como en la placa, el pad del SMA (1,27 mm), la transición cónica y la línea
    cobre.AddBox([-W/2, y_a, H], [W/2, 0.0, H], priority=10)
    cobre.AddBox([-W_PAD/2, 0.0, H], [W_PAD/2, Y_PAD, H], priority=10)
    cobre.AddPolygon([[-W_PAD/2, W_PAD/2, W/2, -W/2], [Y_PAD, Y_PAD, Y_TAPER, Y_TAPER]], norm_dir=2, elevation=H, priority=10)
    cobre.AddBox([-W/2, Y_TAPER, H], [W/2, largo, H], priority=10)
    lam_min = C0/(a.fmax*1e6)*1e3
    mesh.AddLine('x', np.concatenate([[-X - 20, X + 20, -X, X], np.linspace(-W/2, W/2, 5), [-W_PAD/2, W_PAD/2], np.arange(-X, X + 0.01, 2.0)]
                                     + ([[-ancho_m/2, ancho_m/2]] if mu else [])))
    mesh.AddLine('y', np.concatenate([[y_a - 20, y_b + 20, y_a, y_b, 0.0, largo], np.arange(y_a, y_b + 0.01, 2.0),
                                      np.linspace(largo - 2, largo + 2, 9), [Y_PAD, Y_TAPER]] + ([[y0_m, y1_m]] if mu else [])))
    z_bajo = -15 - (me[2] if me else 0.0)
    mesh.AddLine('z', np.concatenate([np.linspace(0, H, 5), [z_bajo, H + 20]] + ([[-me[2]]] if me else []) + ([list(np.linspace(H, H + t_m, int(np.ceil(t_m/0.75)) + 1))] if mu else [])))
    mesh.SmoothMeshLines('all', lam_min/20, 1.3)
    print('Malla:', [len(mesh.GetLines(d)) for d in 'xyz'])
    port = FDTD.AddMSLPort(1, cobre, [-W/2, y_a, H], [W/2, y_a + 6, 0], 'y', 'z', excite=1, FeedShift=1.0, MeasPlaneShift=L_ALIM, priority=20)

    if not os.path.exists(os.path.join(sim_path, 'port_ut_1')):
        t0 = time.time()
        from antenas import gpu
        if not (gpu.activa() and gpu.ejecutar(FDTD, sim_path)):
            FDTD.Run(sim_path, cleanup=True, verbose=0)
        print(f'Tiempo: {time.time() - t0:.0f} s')
    f = np.linspace(a.fmin*1e6, a.fmax*1e6, 2001)
    port.CalcPort(sim_path, f, ref_impedance=50)
    s11 = port.uf_ref/port.uf_inc
    z = 50*(1 + s11)/(1 - s11)
    cr = cruces_x(f, z)
    res = {'stub': a.stub, 'largo_mm': largo, 'er': a.er, 'tand': a.tand, 'muestra': mu,
           'resonancias': [{'f_MHz': round(fr/1e6, 3), 'R_ohm': round(r, 3), 'dXdf_ohm_MHz': round(d*1e6, 4)} for fr, r, d in cr]}
    os.makedirs(os.path.join(AQUI, 'simulaciones'), exist_ok=True)
    base = os.path.join(AQUI, 'simulaciones', f'stub_{largo:g}_er{a.er:.3f}_tan{a.tand:g}{sufijo}')
    json.dump(res, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    with open(base + '.s1p', 'w', encoding='utf-8') as fh:
        fh.write('! Chirptenna · simulación 3D de un stub abierto\n# HZ S RI R 50\n')
        fh.write('\n'.join(f'{fi:.0f} {s.real:.6e} {s.imag:.6e}' for fi, s in zip(f, s11)) + '\n')
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), tight_layout=True, sharex=True)
    ax[0].plot(f/1e6, 20*np.log10(np.abs(s11)), 'b-'); ax[0].set_ylabel('|S11| dB'); ax[0].grid()
    ax[1].plot(f/1e6, np.clip(z.imag, -300, 300), 'r-', label='X'); ax[1].plot(f/1e6, np.clip(z.real, -300, 300), 'k--', lw=.8, label='R')
    for fr, r, d in cr:
        ax[1].axvline(fr/1e6, color='g', ls=':')
    ax[1].set_xlabel('MHz'); ax[1].set_ylabel('Ω'); ax[1].grid(); ax[1].legend()
    ax[0].set_title(f'stub {largo:g} mm: ' + ', '.join(f"{r['f_MHz']} MHz (R {r['R_ohm']} Ω)" for r in res['resonancias']))
    fig.savefig(base + '.png', dpi=110)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
