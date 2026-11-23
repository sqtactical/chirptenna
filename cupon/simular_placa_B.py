"""Simula en openEMS 3D un stub del cupón B con TODA la placa (las otras líneas, el anillo, la CPWG, las vías y los pads de los SMA sin soldar), leída del
`cupon_B.kicad_pcb`. Sirve para ver si los vecinos mueven las resonancias del stub frente a `simular_stub.py` (stub aislado en una franja de 28 mm).

Uso: python simular_placa_B.py <S80|S30> [--er 4.5] [--tand 0.02] [--fmin 300] [--fmax 3000] [--fin 1e-6] [--sin-vecinas]

El puerto es el de `simular_stub.py` (una línea de 50 Ω de 10 mm que se alarga fuera del borde de arriba); el borde de arriba pasa a ser y = 0 (la placa va de
y = 0 abajo a y = 100) para usar las mismas coordenadas. `--sin-vecinas` deja solo el stub y su SMA (cobre de la placa menos todo lo demás) para comprobar el modelo.
"""
import os
import sys
import json
import time
import argparse
import tempfile

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, box
from shapely.ops import unary_union, split

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from simular_stub import cruces_x, L_ALIM, H, W   # noqa: E402  (importa comun y openEMS antes)
from CSXCAD import ContinuousStructure   # noqa: E402
from openEMS import openEMS   # noqa: E402
from openEMS.physical_constants import C0, EPS0   # noqa: E402
from antenas import importar_kicad   # noqa: E402

X_STUB = {'S80': 68.0, 'S30': 79.0}
LARGO = {'S80': 85.7, 'S30': 35.7}      # como en `er_fr4_stubs`: del borde de la placa al extremo abierto


def sin_agujeros(pol):
    """Parte un polígono con agujeros en trozos sin agujeros (CSXCAD no admite huecos)."""
    pendientes, listos = [pol], []
    while pendientes:
        p = pendientes.pop()
        if not p.interiors:
            listos.append(p)
            continue
        cx = p.interiors[0].centroid.x
        for trozo in split(p, LineString([(cx, p.bounds[1] - 1), (cx, p.bounds[3] + 1)])).geoms:
            if trozo.area > 1e-4:
                pendientes.append(trozo)
    return listos


def fundir(valores, minimo=0.2):
    """Líneas de malla ordenadas, sin dos a menos de `minimo` mm (lección 37: una celda de micras hunde el paso de tiempo): de cada grupo se queda la media."""
    v = np.sort(np.unique(np.round(np.asarray(valores, float), 3)))
    grupos = [[v[0]]]
    for x in v[1:]:
        if x - grupos[-1][-1] < minimo:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    return np.array([np.mean(g) for g in grupos])


def poligonos(geo):
    if geo.is_empty:
        return []
    return [p for p in getattr(geo, 'geoms', [geo]) if p.geom_type == 'Polygon' and p.area > 1e-3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stub', choices=list(X_STUB))
    ap.add_argument('--er', type=float, default=4.5)
    ap.add_argument('--tand', type=float, default=0.02)
    ap.add_argument('--fmin', type=float, default=300.0)
    ap.add_argument('--fmax', type=float, default=3000.0)
    ap.add_argument('--fin', type=float, default=1e-6)
    ap.add_argument('--pasos', type=int, default=3000000)
    ap.add_argument('--sin-vecinas', action='store_true')
    a = ap.parse_args()
    x_s = X_STUB[a.stub]
    pl = importar_kicad.placa(os.path.join(os.path.dirname(AQUI), 'cupon', 'cupon_B', 'cupon_B.kicad_pcb'))
    alto = pl['alto_mm']
    # el modelo del importador tiene y hacia arriba; aquí el borde de arriba es y = 0 (como en simular_stub.py)
    inv = lambda g: affinity.scale(g, 1.0, -1.0, origin=(0, alto/2))
    f_cu, b_cu = inv(pl['cobre']['F.Cu']), inv(pl['cobre']['B.Cu'])
    vias = [(x, alto - y, d) for x, y, d in pl['taladros']]
    ancho = pl['ancho_mm']
    if a.sin_vecinas:
        # solo la franja del stub: el pad del SMA y la línea
        franja = box(x_s - 14, -1, x_s + 14, alto + 1)
        f_cu, b_cu = f_cu.intersection(franja), b_cu.intersection(franja)
        vias = [v for v in vias if abs(v[0] - x_s) <= 14]
    print(f'Placa {ancho} x {alto} mm, F.Cu {len(poligonos(f_cu))} piezas, B.Cu {len(poligonos(b_cu))}, vías/taladros {len(vias)}')

    f0, fc = (a.fmin + a.fmax)/2*1e6, (a.fmax - a.fmin)/2*1e6
    sim_path = os.path.join(tempfile.gettempdir(), f'fase0_placaB_{a.stub}_er{a.er:.3f}_tan{a.tand:g}' + ('_sola' if a.sin_vecinas else ''))
    FDTD = openEMS(NrTS=a.pasos, EndCriteria=a.fin)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    y_a = -L_ALIM
    kappa = 2*np.pi*f0*EPS0*a.er*a.tand
    CSX.AddMaterial('FR4', epsilon=a.er, kappa=kappa).AddBox([0, y_a, 0], [ancho, alto, H], priority=0)
    cobre = CSX.AddMetal('cobre')
    masa = CSX.AddMetal('masa')
    pol_f, pol_b = [], []
    for g_, lista in ((f_cu, pol_f), (b_cu, pol_b)):
        for p in poligonos(g_):
            lista += sin_agujeros(p)
    for p in pol_f:
        cobre.AddPolygon([np.array(p.exterior.coords).T[0], np.array(p.exterior.coords).T[1]], norm_dir=2, elevation=H, priority=10)
    for p in pol_b:
        masa.AddPolygon([np.array(p.exterior.coords).T[0], np.array(p.exterior.coords).T[1]], norm_dir=2, elevation=0.0, priority=10)
    masa.AddBox([0, y_a, 0], [ancho, 0.0, 0], priority=10)                 # masa de la línea de alimentación simulada
    cobre.AddBox([x_s - W/2, y_a, H], [x_s + W/2, 0.0, H], priority=10)    # línea de 50 Ω hasta el borde
    for x, y, d in vias:
        masa.AddCylinder([x, y, 0], [x, y, H], radius=max(d, 0.3)/2, priority=10)

    # malla: rejilla de 2 mm, bordes de las piezas rectas y de las cajas de las curvas, y las del stub
    xs, ys = [-20.0, ancho + 20.0, 0.0, ancho], [y_a - 20.0, alto + 20.0, y_a, alto, 0.0, LARGO[a.stub]]
    for p in pol_f + pol_b:
        c = np.array(p.exterior.coords)
        if len(c) <= 17:
            xs += list(np.round(c[:, 0], 2))
            ys += list(np.round(c[:, 1], 2))
        else:
            xs += [round(p.bounds[0], 2), round(p.bounds[2], 2)]
            ys += [round(p.bounds[1], 2), round(p.bounds[3], 2)]
    xs += list(np.linspace(x_s - W/2, x_s + W/2, 5)) + list(np.arange(0, ancho + 0.01, 2.0))
    ys += list(np.arange(y_a, alto + 0.01, 2.0)) + list(np.linspace(LARGO[a.stub] - 2, LARGO[a.stub] + 2, 9))
    mesh.AddLine('x', fundir(xs))
    mesh.AddLine('y', fundir(ys))
    mesh.AddLine('z', np.concatenate([np.linspace(0, H, 5), [-15, H + 20]]))
    mesh.SmoothMeshLines('all', 2.5, 1.3)
    celdas = [len(mesh.GetLines(d)) for d in 'xyz']
    print('Malla:', celdas, '=', round(np.prod(celdas)/1e6, 2), 'M celdas')
    port = FDTD.AddMSLPort(1, cobre, [x_s - W/2, y_a, H], [x_s + W/2, y_a + 6, 0], 'y', 'z', excite=1, FeedShift=1.0,
                           MeasPlaneShift=L_ALIM, priority=20)

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
    res = {'stub': a.stub, 'er': a.er, 'tand': a.tand, 'solo_el_stub': a.sin_vecinas, 'celdas_M': round(float(np.prod(celdas))/1e6, 2),
           'resonancias': [{'f_MHz': round(fr/1e6, 3), 'R_ohm': round(r, 3)} for fr, r, d in cruces_x(f, z)]}
    os.makedirs(os.path.join(AQUI, 'simulaciones'), exist_ok=True)
    base = os.path.join(AQUI, 'simulaciones', f'placaB_{a.stub}_er{a.er:.3f}' + ('_sola' if a.sin_vecinas else ''))
    json.dump(res, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    with open(base + '.s1p', 'w', encoding='utf-8') as fh:
        fh.write('! Chirptenna · simulación 3D de un stub con toda la placa\n# HZ S RI R 50\n')
        fh.write('\n'.join(f'{fi:.0f} {s.real:.6e} {s.imag:.6e}' for fi, s in zip(f, s11)) + '\n')
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
