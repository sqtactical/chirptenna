"""Simula en openEMS una placa real importada de sus Gerber (EasyEDA) para ajustar εr.

Modelo: cobre de las dos caras como láminas PEC (inferior en z=0, superior en z=h),
vías y taladros metalizados como cilindros PEC, sustrato con el rectángulo que
envuelve el contorno, y un puerto concentrado de 50 Ω en la cara inferior entre el
punto de masa (malla del coaxial) y el borde del pad donde va el vivo.

Uso:
  python simular_placa.py <carpeta_placa> --er 4.4 [--res 0.5] [--h 1.6] [--solo-geometria]
       [--pad U19_4] [--fmin 200] [--fmax 1600]
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
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union, nearest_points, split

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'fase0'))
sys.path.insert(0, os.path.join(RAIZ, 'analisis'))
import comun   # noqa: E402  (antes que openEMS)
import analizar_placas as ap   # noqa: E402
from CSXCAD import ContinuousStructure   # noqa: E402
from openEMS import openEMS   # noqa: E402
from openEMS.physical_constants import C0, EPS0   # noqa: E402

DIR_RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
TAND = 0.02


def sin_agujeros(pol):
    """Parte un polígono con agujeros en trozos sin agujeros (CSXCAD no admite huecos)."""
    pendientes, listos = [pol], []
    while pendientes:
        p = pendientes.pop()
        if not p.interiors:
            listos.append(p)
            continue
        cx = p.interiors[0].centroid.x
        miny, maxy = p.bounds[1] - 1, p.bounds[3] + 1
        for trozo in split(p, LineString([(cx, miny), (cx, maxy)])).geoms:
            if trozo.area > 1e-4:
                pendientes.append(trozo)
    return listos


def preparar(carpeta, pad):
    nombre, gnd, capas, contorno, _ = ap.analizar_placa(carpeta)
    taladros = ap.leer_taladros(carpeta)
    contorno_pts = np.vstack([np.array(s) for s in contorno])
    xmin, ymin = contorno_pts.min(0)
    xmax, ymax = contorno_pts.max(0)

    # Puerto: del cobre de masa más cercano al pad hasta el borde del pad
    red = json.load(open(os.path.join(carpeta, 'FlyingProbeTesting.json'), encoding='utf-8'))
    campos = red['pins']['fields']
    pines = {r[1]: dict(zip(campos, r)) for r in red['pins']['rows']}
    p = pines[pad]
    lado = p['LAYER']
    cx, cy = p['PIN_X']*ap.MIL, p['PIN_Y']*ap.MIL
    geom_lado = capas[lado][0]
    isla_pad = next(i for i in ap.islas(geom_lado) if i.buffer(0.05).contains(Point(cx, cy)))
    pads_gnd = [q for q in pines.values() if q['NET_NAME'] == gnd and (q['LAYER'] == lado or q['HOLE_SIZE'] > 0)]
    masa = unary_union([i for i in ap.islas(geom_lado)
                        if any(i.buffer(0.05).contains(Point(q['PIN_X']*ap.MIL, q['PIN_Y']*ap.MIL))
                               for q in pads_gnd)])
    zona_pad = isla_pad.intersection(Point(cx, cy).buffer(3.0))   # solo el pad, no toda la pista
    a, b = nearest_points(masa, zona_pad)       # a en masa, b en el pad
    dx, dy = b.x - a.x, b.y - a.y
    if abs(dx) < 1e-3 and abs(dy) < 1e-3:
        raise RuntimeError('El pad toca el cobre de masa: revisar la detección de la masa')
    eje = 'x' if abs(dx) >= abs(dy) else 'y'
    signo = 1 if (dx if eje == 'x' else dy) > 0 else -1
    # El hueco real (~0,2 mm) es más fino que la malla y el puerto quedaría en
    # cortocircuito: se abre en la masa un hueco de HUECO mm frente al pad.
    HUECO, ANCHO = 1.0, 1.0
    if eje == 'x':
        xs = sorted([b.x, b.x - signo*HUECO])
        ini, fin = [xs[0], b.y - ANCHO/2], [xs[1], b.y + ANCHO/2]
        corte = box(xs[0], b.y - ANCHO, xs[1], b.y + ANCHO)
    else:
        ys = sorted([b.y, b.y - signo*HUECO])
        ini, fin = [b.x - ANCHO/2, ys[0]], [b.x + ANCHO/2, ys[1]]
        corte = box(b.x - ANCHO, ys[0], b.x + ANCHO, ys[1])
    capas[lado] = (capas[lado][0].difference(corte.difference(isla_pad)),) + tuple(capas[lado][1:])
    puerto = {'lado': lado, 'eje': eje, 'ini': ini, 'fin': fin, 'signo': signo,
              'masa': (a.x, a.y), 'pad': (b.x, b.y)}

    cobre = {}
    for l in ('T', 'B'):
        geom = capas[l][0].simplify(0.02)
        trozos = []
        for pol in ap.poligonos(geom):
            if pol.area > 0.01:
                trozos += sin_agujeros(pol)
        cobre[l] = (geom, trozos)
    return dict(nombre=nombre, cobre=cobre, taladros=taladros, contorno=contorno,
                bbox=(xmin, ymin, xmax, ymax), puerto=puerto)


def dibujar(g, ruta):
    fig, ax = plt.subplots(figsize=(8, 10), tight_layout=True)
    for lado, color in (('T', '#bbbbbb'), ('B', '#c9a86a')):
        for t in g['cobre'][lado][1]:
            ax.add_patch(MplPolygon(np.array(t.exterior.coords), fc=color, ec='k', lw=0.1, alpha=0.6))
    for x, y, d, _ in g['taladros']:
        ax.add_patch(plt.Circle((x, y), max(d, 0.3)/2, color='b'))
    pu = g['puerto']
    ax.add_patch(plt.Rectangle(pu['ini'], pu['fin'][0] - pu['ini'][0], pu['fin'][1] - pu['ini'][1], color='r'))
    ax.plot(*pu['masa'], 'ks'); ax.plot(*pu['pad'], 'r*', ms=12)
    ax.set_aspect('equal'); ax.autoscale()
    ax.set_title(f"{g['nombre']}: modelo (vista desde arriba). Rojo: puerto")
    fig.savefig(ruta, dpi=120)
    plt.close(fig)


def simular(g, er, h, res, fmin, fmax, solo_geometria=False):
    f0, fc = (fmin + fmax)/2, (fmax - fmin)/2
    sim_path = os.path.join(tempfile.gettempdir(), f"fase0_placa_{g['nombre']}_er{er:.3f}_h{h:.2f}_r{res:.2f}")
    FDTD = openEMS(NrTS=400000, EndCriteria=10**(-40/10))
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    xmin, ymin, xmax, ymax = g['bbox']
    kappa = 2*np.pi*f0*EPS0*er*TAND
    sus = CSX.AddMaterial('FR4', epsilon=er, kappa=kappa)
    sus.AddBox([xmin, ymin, 0], [xmax, ymax, h], priority=0)

    cobre = CSX.AddMetal('cobre')
    for lado, z in (('B', 0.0), ('T', h)):
        for t in g['cobre'][lado][1]:
            xs, ys = np.array(t.exterior.coords).T
            cobre.AddPolygon([xs, ys], norm_dir=2, elevation=z, priority=10)
    for x, y, d, _ in g['taladros']:
        cobre.AddCylinder([x, y, 0], [x, y, h], radius=max(d, 0.3)/2, priority=10)

    pu = g['puerto']
    z = 0.0 if pu['lado'] == 'B' else h
    ini, fin = [*pu['ini'], z], [*pu['fin'], z]
    if pu['signo'] < 0:
        ini, fin = fin, ini
    port = FDTD.AddLumpedPort(1, 50, ini, fin, pu['eje'], 1.0, priority=20)

    lam_min = C0/fmax*1e3
    margen = 80.0
    mesh.AddLine('x', np.arange(xmin, xmax + res/2, res))
    mesh.AddLine('y', np.arange(ymin, ymax + res/2, res))
    mesh.AddLine('x', [pu['ini'][0], pu['fin'][0], xmin - margen, xmax + margen])
    mesh.AddLine('y', [pu['ini'][1], pu['fin'][1], ymin - margen, ymax + margen])
    mesh.AddLine('z', np.linspace(0, h, 5))
    mesh.AddLine('z', [-margen, h + margen])
    mesh.SmoothMeshLines('all', lam_min/20, 1.3)
    celdas = [len(mesh.GetLines(d)) for d in 'xyz']
    print('Malla:', celdas, '=', np.prod(celdas)/1e6, 'M celdas')
    if solo_geometria:
        return None

    f = np.linspace(fmin, fmax, 1401)
    if not (os.path.exists(os.path.join(sim_path, 'port_ut_1')) and os.path.exists(os.path.join(sim_path, 'port_it_1'))):
        t0 = time.time()
        FDTD.Run(sim_path, cleanup=True, verbose=0)
        print(f'Tiempo: {time.time() - t0:.0f} s')
    port.CalcPort(sim_path, f)
    s11 = port.uf_ref/port.uf_inc
    return f, s11, celdas


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument('carpeta')
    ap_.add_argument('--er', type=float, default=4.4)
    ap_.add_argument('--h', type=float, default=1.6)
    ap_.add_argument('--res', type=float, default=0.5)
    ap_.add_argument('--pad', default='U19_4')
    ap_.add_argument('--fmin', type=float, default=200)
    ap_.add_argument('--fmax', type=float, default=1600)
    ap_.add_argument('--solo-geometria', action='store_true')
    a = ap_.parse_args()
    os.makedirs(DIR_RES, exist_ok=True)
    g = preparar(a.carpeta, a.pad)
    print('Trozos de cobre: inferior', len(g['cobre']['B'][1]), '| superior', len(g['cobre']['T'][1]),
          '| taladros', len(g['taladros']), '| puerto', g['puerto']['eje'], g['puerto']['ini'], g['puerto']['fin'])
    dibujar(g, os.path.join(DIR_RES, f"{g['nombre']}_modelo.png"))
    r = simular(g, a.er, a.h, a.res, a.fmin*1e6, a.fmax*1e6, a.solo_geometria)
    if r is None:
        return
    f, s11, celdas = r
    base = os.path.join(DIR_RES, f"{g['nombre']}_er{a.er:.3f}_h{a.h:.2f}_r{a.res:.2f}")
    sys.path.insert(0, os.path.join(RAIZ, 'vna'))
    from nanovna import guardar_s1p
    guardar_s1p(base + '.s1p', f, s11, f"Simulación {g['nombre']} er={a.er} h={a.h} res={a.res}")
    print('Guardado', base + '.s1p')


if __name__ == '__main__':
    main()
