"""Simula en openEMS 3D una microstrip recta de dos puertos del cupón B (como L17/L64 sin el codo, o la MS100) con el pad del SMA y la
transición cónica de cada extremo (igual que `simular_stub.py`), y da el retardo de S21 y los mínimos de |S11|.

Sirve para contrastar con la medida (`vna/medir_s21_pc.py`) la εr que sale de la fase de S21 (cuasi-estático) con la del simulador 3D.

Los puertos MSL tienen que ser largos (20 mm) con el plano de medida (12 mm) y la fuente (3 mm) dentro y alejados del inicio, como en el tutorial MSL de
openEMS: con puertos de 6 mm y el plano fuera del puerto la simulación salía sin sentido (|S11| −0,5 dB en una línea continua, |S21| > 0 dB). El plano de
medida queda 8 mm antes del borde de la placa (da igual para |S11| y para diferencias de retardo entre líneas con la misma alimentación).
`--directa` es la comprobación: una línea de 50 Ω continua debe dar |S11| < −30 dB.
(Ojo: `simular_stub.py` y `simular_anillo.py` usan puertos de 6 mm con el plano fuera del puerto; en un puerto único eso no se nota en S11 de un abierto,
pero conviene revisarlo.)

Uso: python simular_linea.py <ancho_mm> <largo_placa_mm> [--er 4.5] [--tand 0.02] [--fmin 100] [--fmax 2200] [--fin 1e-6]
  ancho_mm        ancho de la línea (3,01 = 50 Ω; 0,69 = 100 Ω); la alimentación del puerto siempre es de 50 Ω
  largo_placa_mm  distancia entre los dos bordes con SMA (la línea mide esto − 11,4 mm de pads y transiciones)
"""
import os
import sys
import json
import time
import argparse
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'fase0'))
sys.path.insert(0, os.path.dirname(AQUI))
import comun   # noqa: E402  (antes que openEMS)
from CSXCAD import ContinuousStructure   # noqa: E402
from openEMS import openEMS   # noqa: E402
from openEMS.physical_constants import C0, EPS0   # noqa: E402

H, W50 = 1.6, 3.01
L_ALIM = 20.0       # largo de la alimentación de 50 Ω antes del borde = largo del puerto MSL (con puertos cortos la simulación sale sin sentido)
W_PAD, Y_PAD, Y_TAPER = 1.27, 3.4, 5.7


def minimos(f, db, lo, hi):
    m = (f >= lo) & (f <= hi)
    i = np.where(m)[0]
    j = i[np.argmin(db[m])]
    return float(f[j])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ancho', type=float)
    ap.add_argument('largo_placa', type=float)
    ap.add_argument('--er', type=float, default=4.5)
    ap.add_argument('--tand', type=float, default=0.02)
    ap.add_argument('--h', type=float, default=1.6, help='grosor del FR4 [mm]')
    ap.add_argument('--fmin', type=float, default=100.0)
    ap.add_argument('--fmax', type=float, default=2200.0)
    ap.add_argument('--fin', type=float, default=1e-6)
    ap.add_argument('--pasos', type=int, default=3000000)
    ap.add_argument('--directa', action='store_true', help='validación: línea de 50 Ω continua sin pads')
    ap.add_argument('--largo-puerto', type=float, default=L_ALIM, help='largo de cada puerto MSL [mm]: debe ser largo (como en el tutorial de openEMS)')
    ap.add_argument('--plano', type=float, default=12.0, help='plano de medida desde el inicio del puerto [mm], dentro del puerto y lejos de la fuente')
    ap.add_argument('--excite', type=float, default=-1.0)
    ap.add_argument('--feed', type=float, default=3.0, help='FeedShift [mm]')
    ap.add_argument('--paso', type=float, default=1.28, help='celda máxima de la malla [mm] (con 2 mm la pérdida sale ×2,5; 1,28 y 0,8 dan lo mismo)')
    ap.add_argument('--bordes', action='store_true', help='líneas de malla a 1/3–2/3 de celda de los bordes del cobre, como el tutorial de openEMS')
    ap.add_argument('--extender', action='store_true', help='sustrato y masa hasta el borde de la malla')
    ap.add_argument('--etiq', default='', help='sufijo para distinguir variantes en la caché')
    a = ap.parse_args()
    global H
    H = a.h
    w, B = a.ancho, a.largo_placa
    f0, fc = (a.fmin + a.fmax)/2*1e6, (a.fmax - a.fmin)/2*1e6
    etiqueta = f'linea_w{w:g}_B{B:g}_er{a.er:.3f}_tan{a.tand:g}' + ('_directa' if a.directa else '') + ('' if a.h == 1.6 else f'_h{a.h:g}') + a.etiq
    sim_path = os.path.join(tempfile.gettempdir(), 'fase0_' + etiqueta)

    FDTD = openEMS(NrTS=a.pasos, EndCriteria=a.fin)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
    X = 14.0
    y_a, y_b = -L_ALIM, B + L_ALIM
    kappa = 2*np.pi*f0*EPS0*a.er*a.tand
    # sustrato y masa hasta el borde de la malla (dentro de la capa absorbente), como el tutorial MSL de openEMS: si terminan en el puerto, hay reflexión
    ext = 20.0 if a.extender else 0.0
    CSX.AddMaterial('FR4', epsilon=a.er, kappa=kappa).AddBox([-X - ext, y_a - ext, 0], [X + ext, y_b + ext, H], priority=0)
    CSX.AddMetal('masa').AddBox([-X - ext, y_a - ext, 0], [X + ext, y_b + ext, 0], priority=10)
    cobre = CSX.AddMetal('cobre')
    if a.directa:        # prueba de validación: línea de 50 Ω continua de puerto a puerto, sin pads ni transiciones
        cobre.AddBox([-W50/2, y_a, H], [W50/2, y_b, H], priority=10)
    else:
        # extremo 1 (y = 0): alimentación de 50 Ω hasta el borde, pad del SMA, transición cónica y línea
        cobre.AddBox([-W50/2, y_a, H], [W50/2, 0.0, H], priority=10)
        cobre.AddBox([-W_PAD/2, 0.0, H], [W_PAD/2, Y_PAD, H], priority=10)
        cobre.AddPolygon([[-W_PAD/2, W_PAD/2, w/2, -w/2], [Y_PAD, Y_PAD, Y_TAPER, Y_TAPER]], norm_dir=2, elevation=H, priority=10)
        cobre.AddBox([-w/2, Y_TAPER, H], [w/2, B - Y_TAPER, H], priority=10)
        # extremo 2 (y = B), simétrico
        cobre.AddPolygon([[-W_PAD/2, W_PAD/2, w/2, -w/2], [B - Y_PAD, B - Y_PAD, B - Y_TAPER, B - Y_TAPER]], norm_dir=2, elevation=H, priority=10)
        cobre.AddBox([-W_PAD/2, B - Y_PAD, H], [W_PAD/2, B, H], priority=10)
        cobre.AddBox([-W50/2, B, H], [W50/2, y_b, H], priority=10)
    lam_min = C0/(a.fmax*1e6)*1e3
    # bordes de las pistas como en el tutorial MSL de openEMS: líneas a +2/3 y −1/3 de celda del borde (singularidad del campo en el borde del cobre)
    res = lam_min/np.sqrt(a.er)/50
    tercio = np.array([2*res/3, -res/3])/4
    bordes = np.concatenate([[s*(ancho/2 + t) for t in tercio for s in (1, -1)] for ancho in (W50, w, W_PAD)]) if a.bordes else \
        np.concatenate([np.linspace(-W50/2, W50/2, 5), np.linspace(-w/2, w/2, 5), [-W_PAD/2, W_PAD/2]])
    mesh.AddLine('x', np.concatenate([[-X - 20, X + 20, -X, X], bordes, np.arange(-X, X + 0.01, 2.0)]))
    # sin aire entre el final de los puertos y la capa absorbente (como el tutorial: con 20 mm de aire la simulación no converge y sale sin sentido)
    mesh.AddLine('y', np.concatenate([[y_a, y_b, 0.0, B], np.arange(y_a, y_b + 0.01, 2.0),
                                      [Y_PAD, Y_TAPER, B - Y_PAD, B - Y_TAPER]]))
    mesh.AddLine('z', np.concatenate([np.linspace(0, H, 5), [-15, H + 20]]))
    mesh.SmoothMeshLines('all', a.paso if a.paso else lam_min/20, 1.3)
    print('Malla:', [len(mesh.GetLines(d)) for d in 'xyz'])
    lp, desp = a.largo_puerto, a.plano
    p1 = FDTD.AddMSLPort(1, cobre, [-W50/2, y_a, H], [W50/2, y_a + lp, 0], 'y', 'z', excite=a.excite, FeedShift=a.feed, MeasPlaneShift=desp, priority=20)
    p2 = FDTD.AddMSLPort(2, cobre, [-W50/2, y_b, H], [W50/2, y_b - lp, 0], 'y', 'z', MeasPlaneShift=desp, priority=20)

    if not os.path.exists(os.path.join(sim_path, 'port_ut_2')):
        t0 = time.time()
        from antenas import gpu
        if not (gpu.activa() and gpu.ejecutar(FDTD, sim_path)):
            FDTD.Run(sim_path, cleanup=True, verbose=0)
        print(f'Tiempo: {time.time() - t0:.0f} s')
    f = np.linspace(a.fmin*1e6, a.fmax*1e6, 1101)
    p1.CalcPort(sim_path, f, ref_impedance=50)
    p2.CalcPort(sim_path, f, ref_impedance=50)
    s11 = p1.uf_ref/p1.uf_inc
    s21 = p2.uf_ref/p1.uf_inc
    m = (f > 150e6) & (f < 1000e6)       # por debajo de ~150 MHz la excitación gaussiana apenas tiene energía
    ph = np.unwrap(np.angle(s21[m]))
    tau = -np.polyfit(f[m], ph, 1)[0]/(2*np.pi)
    db11 = 20*np.log10(np.abs(s11))
    res = {'ancho_mm': w, 'largo_placa_mm': B, 'er': a.er, 'tand': a.tand, 'retardo_ns': round(tau*1e9, 4),
           's21_min_dB_hasta_1GHz': round(float(20*np.log10(np.abs(s21[m])).min()), 2),
           's11_max_dB_hasta_1GHz': round(float(db11[m].max()), 1),
           'min_s11_MHz_700_1100': round(minimos(f/1e6, db11, 700, 1100), 1),
           'min_s11_MHz_1500_2100': round(minimos(f/1e6, db11, 1500, 2100), 1)}
    os.makedirs(os.path.join(AQUI, 'simulaciones'), exist_ok=True)
    base = os.path.join(AQUI, 'simulaciones', etiqueta)
    json.dump(res, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    with open(base + '.s2p', 'w', encoding='utf-8') as fh:
        fh.write('! Chirptenna · simulación 3D de una microstrip de dos puertos (S12 = S21, S22 = S11 por simetría)\n# HZ S RI R 50\n')
        fh.write('\n'.join(f'{fi:.0f} {x.real:.6e} {x.imag:.6e} {y.real:.6e} {y.imag:.6e} {y.real:.6e} {y.imag:.6e} {x.real:.6e} {x.imag:.6e}'
                           for fi, x, y in zip(f, s11, s21)) + '\n')
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
