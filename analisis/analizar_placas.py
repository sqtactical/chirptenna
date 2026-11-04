"""Busca en Gerber de EasyEDA pistas aptas para medir la εr del FR4 con el VNA.

En una placa sin montar, cada "isla" de cobre aislada (pistas + pads que se
tocan) es una línea de transmisión abierta. Sirve si:
  - es larga (>= 15 mm de pista) y sin ramas,
  - no tiene vías ni taladros (se quedaría en una sola capa),
  - tiene masa continua debajo, en la otra cara,
  - tiene un pad de masa cerca de uno de sus extremos para soldar la malla.

Uso: python analizar_placas.py <carpeta_placa> [<carpeta_placa> ...] --salida <carpeta>
"""
import os
import sys
import json
import math
import warnings
import collections

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, nearest_points
from shapely import affinity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

warnings.simplefilter('ignore')
from gerbonara import GerberFile, ExcellonFile
from gerbonara.utils import MM
import gerbonara.graphic_primitives as gp

MIL = 0.0254
L_MIN = 15.0          # longitud mínima de pista [mm]
H_SUSTRATO = 1.6      # para el margen de "masa debajo"
CAPAS = {'T': ('Gerber_TopLayer.GTL', 'Gerber_BottomLayer.GBL'),
         'B': ('Gerber_BottomLayer.GBL', 'Gerber_TopLayer.GTL')}


# ---------------------------------------------------------------- geometría
def puntos_arco(x1, y1, x2, y2, cx, cy, horario, paso=math.radians(5)):
    a1 = math.atan2(y1 - cy, x1 - cx)
    a2 = math.atan2(y2 - cy, x2 - cx)
    r = math.hypot(x1 - cx, y1 - cy)
    if horario:
        while a2 >= a1:
            a2 -= 2*math.pi
    else:
        while a2 <= a1:
            a2 += 2*math.pi
    n = max(2, int(abs(a2 - a1)/paso) + 1)
    return [(cx + r*math.cos(a), cy + r*math.sin(a)) for a in np.linspace(a1, a2, n)]


def primitiva_a_shapely(p):
    if isinstance(p, gp.Circle):
        return Point(p.x, p.y).buffer(p.r, 16)
    if isinstance(p, gp.Rectangle):
        r = box(p.x - p.w/2, p.y - p.h/2, p.x + p.w/2, p.y + p.h/2)
        return affinity.rotate(r, p.rotation, origin=(p.x, p.y), use_radians=True) if p.rotation else r
    if isinstance(p, gp.Line):
        return LineString([(p.x1, p.y1), (p.x2, p.y2)]).buffer(p.width/2, 8)
    if isinstance(p, gp.Arc):
        pts = puntos_arco(p.x1, p.y1, p.x2, p.y2, p.cx, p.cy, p.clockwise)
        return LineString(pts).buffer(p.width/2, 8)
    if isinstance(p, gp.ArcPoly):
        if len(p.outline) < 3:
            return None
        return Polygon(p.outline).buffer(0)
    return None


def leer_cobre(ruta):
    """Devuelve (cobre total, lista de pistas (LineString, ancho), polígonos de relleno)."""
    g = GerberFile.open(ruta)
    cobre = None
    lote = []
    pistas, rellenos = [], []
    for o in g.objects:
        nombre = type(o).__name__
        for p in o.to_primitives(MM):
            s = primitiva_a_shapely(p)
            if s is None or s.is_empty:
                continue
            if not p.polarity_dark:
                cobre = unary_union([cobre] + lote if cobre else lote).difference(s)
                lote = []
                continue
            lote.append(s)
            if nombre == 'Line' and isinstance(p, gp.Line):
                pistas.append((LineString([(p.x1, p.y1), (p.x2, p.y2)]), p.width))
            elif nombre == 'Arc' and isinstance(p, gp.Arc):
                pistas.append((LineString(puntos_arco(p.x1, p.y1, p.x2, p.y2, p.cx, p.cy, p.clockwise)), p.width))
            elif nombre == 'Region':
                rellenos.append(s)
    cobre = unary_union(([cobre] if cobre else []) + lote)
    return cobre, pistas, rellenos


def leer_taladros(carpeta):
    pts = []
    for n in os.listdir(carpeta):
        if n.upper().endswith('.DRL'):
            for d in ExcellonFile.open(os.path.join(carpeta, n)).drills():
                d = d.converted(MM) if hasattr(d, 'converted') else d
                pts.append((d.x, d.y, d.tool.diameter if hasattr(d, 'tool') else 0, 'VIA' in n.upper()))
    return pts


def leer_contorno(carpeta):
    ruta = os.path.join(carpeta, 'Gerber_BoardOutlineLayer.GKO')
    if not os.path.exists(ruta):
        return None
    segs = []
    for o in GerberFile.open(ruta).objects:
        for p in o.to_primitives(MM):
            if isinstance(p, gp.Line):
                segs.append([(p.x1, p.y1), (p.x2, p.y2)])
            elif isinstance(p, gp.Arc):
                segs.append(puntos_arco(p.x1, p.y1, p.x2, p.y2, p.cx, p.cy, p.clockwise))
    return segs


def poligonos(geom):
    return list(geom.geoms) if hasattr(geom, 'geoms') else [geom]


def islas(geom):
    return [g for g in poligonos(geom) if g.area > 0]


# ---------------------------------------------------------------- análisis
def grafo_pistas(segmentos):
    """Nodos de grado >= 3 (ramas) y longitud total de un conjunto de pistas."""
    grado = collections.Counter()
    for ls, _ in segmentos:
        a, b = ls.coords[0], ls.coords[-1]
        grado[(round(a[0], 2), round(a[1], 2))] += 1
        grado[(round(b[0], 2), round(b[1], 2))] += 1
    ramas = sum(1 for v in grado.values() if v >= 3)
    return ramas, sum(ls.length for ls, _ in segmentos)


def analizar_placa(carpeta):
    nombre = os.path.basename(os.path.normpath(carpeta))
    with open(os.path.join(carpeta, 'FlyingProbeTesting.json'), encoding='utf-8') as fh:
        red = json.load(fh)
    campos = red['pins']['fields']
    pines = [dict(zip(campos, r)) for r in red['pins']['rows']]
    for p in pines:
        p['x'], p['y'] = p['PIN_X']*MIL, p['PIN_Y']*MIL
    nets_por_cuenta = collections.Counter(p['NET_NAME'] for p in pines)
    gnd = next((n for n in nets_por_cuenta if n.upper() in ('GND', 'VSS', '0V')), nets_por_cuenta.most_common(1)[0][0])

    taladros = leer_taladros(carpeta)
    contorno = leer_contorno(carpeta)
    capas = {}
    for lado, (propia, _) in CAPAS.items():
        capas[lado] = leer_cobre(os.path.join(carpeta, propia))

    candidatas = []
    for lado, (propia, opuesta) in CAPAS.items():
        cobre, pistas, rellenos = capas[lado]
        cobre_op = capas['B' if lado == 'T' else 'T'][0]
        relleno = unary_union(rellenos) if rellenos else None
        pads_gnd = [p for p in pines if p['NET_NAME'] == gnd and (p['LAYER'] == lado or p['HOLE_SIZE'] > 0)]
        # Cobre de masa en esta cara: islas que contienen algún pad de masa
        cobre_gnd = unary_union([i for i in islas(cobre)
                                 if any(i.buffer(0.05).contains(Point(q['x'], q['y'])) for q in pads_gnd)])
        for isla in islas(cobre):
            if relleno is not None and isla.intersection(relleno).area > 5.0:
                continue   # es (o toca) un relleno de cobre
            segs = [(ls, w) for ls, w in pistas if isla.buffer(1e-3).contains(ls)]
            if not segs:
                continue
            ramas, longitud = grafo_pistas(segs)
            if longitud < L_MIN:
                continue
            agujeros = [t for t in taladros if isla.buffer(0.05).contains(Point(t[0], t[1]))]
            pins_isla = [p for p in pines if (p['LAYER'] == lado or p['HOLE_SIZE'] > 0)
                         and isla.buffer(0.05).contains(Point(p['x'], p['y']))]
            nets = sorted({p['NET_NAME'] for p in pins_isla})
            anchos = sorted({round(w, 3) for _, w in segs})
            huella = unary_union([ls.buffer(w/2 + H_SUSTRATO) for ls, w in segs])
            cobertura = huella.intersection(cobre_op).area/huella.area
            # masa coplanar: distancia mínima de la pista a otro cobre de la misma cara
            resto = cobre.difference(isla.buffer(0.01))
            linea = unary_union([ls for ls, _ in segs])
            gap = linea.distance(resto) - max(anchos)/2 if not resto.is_empty else float('inf')
            # extremo para soldar: pad de la isla más cercano a cobre de masa de la
            # misma cara (pad de masa o relleno, rascando la máscara)
            mejor = None
            if not cobre_gnd.is_empty:
                for p in pins_isla:
                    pt = Point(p['x'], p['y'])
                    d = pt.distance(cobre_gnd)
                    if mejor is None or d < mejor[0]:
                        cerca = nearest_points(pt, cobre_gnd)[1]
                        mejor = (d, p, {'PIN_NAME': 'relleno GND (rascar máscara)', 'x': cerca.x, 'y': cerca.y})
            gap_es_gnd = (not cobre_gnd.is_empty and math.isfinite(gap)
                          and abs(linea.distance(cobre_gnd) - max(anchos)/2 - gap) < 0.05)
            c = {
                'placa': nombre, 'cara': 'superior' if lado == 'T' else 'inferior', 'lado': lado,
                'longitud_mm': round(longitud, 2), 'anchos_mm': anchos, 'ramas': ramas,
                'segmentos': len(segs), 'vias_taladros': len(agujeros),
                'masa_debajo_%': round(100*cobertura, 1),
                'gap_coplanar_mm': round(gap, 2) if math.isfinite(gap) else None,
                'coplanar_es_masa': gap_es_gnd,
                'pads': [p['PIN_NAME'] for p in pins_isla], 'nets': nets,
                'soldar_vivo_en': None if mejor is None else mejor[1]['PIN_NAME'],
                'soldar_malla_en': None if mejor is None else mejor[2]['PIN_NAME'],
                'distancia_malla_mm': None if mejor is None else round(mejor[0], 2),
                '_isla': isla, '_segs': segs,
                '_pv': None if mejor is None else (mejor[1]['x'], mejor[1]['y']),
                '_pm': None if mejor is None else (mejor[2]['x'], mejor[2]['y']),
            }
            # La masa incompleta debajo no descarta: la geometría real se simula con
            # openEMS y se ajusta εr. Lo que sí descarta es lo que complica soldar o
            # medir: ramas, vías, anchos mezclados y no tener masa a mano.
            apta = (ramas == 0 and not agujeros and mejor is not None
                    and mejor[0] <= 3.0 and len(anchos) == 1 and longitud >= 30)
            c['apta'] = apta
            c['motivos'] = [m for m, cond in [
                ('tiene ramas', ramas > 0), ('tiene vías/taladros', bool(agujeros)),
                ('sin masa a <3 mm de un extremo', mejor is None or mejor[0] > 3.0),
                ('varios anchos', len(anchos) > 1), ('corta (<30 mm)', longitud < 30)] if cond]
            candidatas.append(c)
    candidatas.sort(key=lambda c: (not c['apta'], -c['longitud_mm']))
    return nombre, gnd, capas, contorno, candidatas


def dibujar(nombre, capas, contorno, candidatas, lado, ruta, giro180=False):
    """Vista de una cara tal como se ve al soldar (la inferior, espejada)."""
    sx, sy = (-1 if lado == 'B' else 1), 1
    if giro180:
        sx, sy = -sx, -1
    fig, ax = plt.subplots(figsize=(9, 9), tight_layout=True)
    otra = 'T' if lado == 'B' else 'B'
    for cara, color, alfa in ((otra, '#e4e4e4', 0.6), (lado, '#c9a86a', 0.55)):
        for pol in poligonos(capas[cara][0]):
            if pol.area > 0:
                xy = np.array(pol.exterior.coords)*[sx, sy]
                ax.add_patch(MplPolygon(xy, closed=True, fc=color, ec='none', alpha=alfa))
    if contorno:
        for s in contorno:
            xs, ys = zip(*s)
            ax.plot(np.array(xs)*sx, np.array(ys)*sy, 'k-', lw=1)
    colores = plt.cm.tab10.colors
    aptas = [c for c in candidatas if c['apta']]
    for i, c in enumerate(aptas):
        if c['lado'] != lado:
            continue
        col = colores[i % 10]
        for ls, w in c['_segs']:
            xs, ys = ls.xy
            ax.plot(np.array(xs)*sx, np.array(ys)*sy, '-', color=col, lw=3.5, solid_capstyle='round')
        if c['_pv']:
            pv = (c['_pv'][0]*sx, c['_pv'][1]*sy)
            pm = (c['_pm'][0]*sx, c['_pm'][1]*sy)
            ax.plot(*pv, marker='*', ms=18, color=col, mec='k')
            ax.plot(*pm, marker='s', ms=9, color='k')
            ax.annotate(f'{i+1}: {c["longitud_mm"]:.1f} mm, vivo en {c["soldar_vivo_en"]}', pv,
                        xytext=(-10 if sx < 0 else 10, 10), textcoords='offset points',
                        ha='right' if sx < 0 else 'left', fontsize=10, weight='bold', color=col,
                        bbox=dict(fc='white', ec=col, alpha=0.9))
    ax.set_aspect('equal'); ax.autoscale()
    vista = 'vista desde ABAJO (espejada, como la ves al darle la vuelta)' if lado == 'B' else 'vista desde ARRIBA'
    if giro180:
        vista += ', girada 180°'
    ax.set_title(f'{nombre} — {vista}\nmarrón: cobre de esta cara · gris: cobre de la otra · '
                 f'★ vivo del coaxial · ■ malla (rascar máscara)', fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    fig.savefig(ruta, dpi=110)
    plt.close(fig)


def main():
    args = sys.argv[1:]
    girar = set()
    if '--giro180' in args:   # placas cuya imagen se gira 180° (p. ej. para casar con una foto)
        k = args.index('--giro180')
        girar = set(args[k + 1].split(','))
        args = args[:k] + args[k + 2:]
    salida = args[args.index('--salida') + 1]
    carpetas = args[:args.index('--salida')]
    os.makedirs(salida, exist_ok=True)
    resumen = {}
    for carpeta in carpetas:
        nombre, gnd, capas, contorno, cands = analizar_placa(carpeta)
        for lado, cara in (('T', 'superior'), ('B', 'inferior')):
            if any(c['apta'] and c['lado'] == lado for c in cands):
                dibujar(nombre, capas, contorno, cands, lado, os.path.join(salida, f'{nombre}_{cara}.png'),
                        giro180=nombre in girar)
        limpio = [{k: v for k, v in c.items() if not k.startswith('_')} for c in cands]
        resumen[nombre] = {'net_masa': gnd, 'candidatas': limpio}
        aptas = [c for c in cands if c['apta']]
        print(f'\n=== {nombre}  (masa: {gnd})  islas >= {L_MIN:.0f} mm: {len(cands)}, aptas: {len(aptas)}')
        for i, c in enumerate(cands[:8]):
            marca = f'APTA {aptas.index(c) + 1}' if c['apta'] else 'no   '
            print(f'  [{marca}] {c["cara"]:8s} L={c["longitud_mm"]:6.1f} mm  w={c["anchos_mm"]}  '
                  f'masa={c["masa_debajo_%"]:5.1f}%  gap={c["gap_coplanar_mm"]}{"(GND)" if c["coplanar_es_masa"] else ""}  ramas={c["ramas"]}  '
                  f'vias={c["vias_taladros"]}  vivo={c["soldar_vivo_en"]} malla={c["soldar_malla_en"]} '
                  f'({c["distancia_malla_mm"]} mm)  nets={c["nets"]}'
                  + ('' if c['apta'] else f'  -> {", ".join(c["motivos"])}'))
    with open(os.path.join(salida, 'resumen.json'), 'w', encoding='utf-8') as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
