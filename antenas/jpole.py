"""J-pole impresa (y su versión fractal con radiador de Koch).

Geometría (cara superior, sin plano de masa; y hacia arriba):
  - adaptador de λ/4: dos tiras paralelas (brazo corto a la izquierda, largo a la derecha)
    unidas abajo por una barra (cortocircuito);
  - radiador de λ/2: continúa el brazo largo hacia arriba (recto o curva de Koch);
  - alimentación con coaxial en el punto de toma, a una fracción de la altura del adaptador:
    vivo al brazo largo, malla al corto. Más arriba = más impedancia.

El adaptador se calcula solo para la frecuencia a la que resuena el radiador (con un
factor de corrección opcional). Estimaciones orientativas: el ajuste fino se hace simulando.
"""
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

import numpy as np

from . import geometria as g
from . import ajuste
from .materiales import C0, lambda0_mm
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5


def eps_eff_cps(er):
    """Línea de tiras paralelas impresa (una cara al aire): εeff ≈ 0,85·(εr+1)/2 (orientativo)."""
    return 0.85*(er + 1)/2


def largo_equivalente_radiador(p):
    n = int(p.get('iteracion', 0))
    return p['largo_radiador']*(1 + 0.35*((4/3)**n - 1))


def estimar_f(p, eps_radiador):
    """Resonancia del radiador de λ/2 (el adaptador se dimensiona a esta misma frecuencia)."""
    return C0/(2*largo_equivalente_radiador(p)*1e-3*math.sqrt(eps_radiador))


def generar(p, s, eps_radiador):
    f = estimar_f(p, eps_radiador)
    w, gap = p['ancho_pista'], p['hueco']
    ls = p['factor_adaptador']*C0/(4*f*math.sqrt(eps_eff_cps(s.er)))*1e3
    xl, xr = -(gap/2 + w/2), gap/2 + w/2               # ejes de los brazos corto y largo
    piezas = [g.engordar([(xl, ls), (xl, 0), (xr, 0), (xr, ls)], w)]   # U: brazos + cortocircuito
    n = int(p.get('iteracion', 0))
    if n == 0:
        rad = g.engordar([(xr, ls), (xr, ls + p['largo_radiador'])], w)
        l_traza = p['largo_radiador']
    else:
        pts = g.koch(n, (0, 0), (0, p['largo_radiador']), p.get('angulo', 60))
        pts[:, 0] = -pts[:, 0]               # muescas hacia fuera, lejos del brazo corto
        pts = pts + [xr, ls]
        rad = g.engordar(pts, w)
        l_traza = g.longitud(pts)
    piezas.append(rad)
    # tapón para que la unión brazo largo–radiador quede maciza
    piezas.append(g.rectangulo(xr - w/2, ls - w/2, xr + w/2, ls + w/2))
    aj = ajuste.vacio()
    if ajuste.activo(p):
        pts_rad = pts if n else np.array([(xr, ls), (xr, ls + p['largo_radiador'])])
        extra, aj, _ = ajuste.alargar_polilinea(pts_rad, w, largo_equivalente_radiador(p), 1.0,
                                                f*p.get('k_sim', 1.0), p)
        if extra is not None:
            piezas.append(extra)
    cobre = unary_union(piezas)
    y_t = p['toma']*ls
    margen = p.get('margen_borde', 2.0)
    contorno = g.contorno_placa([cobre.buffer(margen)], int(p.get('contorno', 1)))
    minx, miny, maxx, maxy = cobre.bounds
    vacio = Polygon()
    avisos = []
    if p['toma'] < 0.08 or p['toma'] > 0.6:
        avisos.append(tr('La toma suele estar entre el 10 y el 40 % del adaptador para 50 Ω.'))
    return Antena(tipo=p['_clave'], parametros={k: v for k, v in p.items() if k != '_clave'}, ajuste=aj,
                  capas={'F.Cu': cobre, 'B.Cu': vacio}, radiador=cobre, contorno=contorno,
                  zona_libre=contorno,
                  puerto={'tipo': 'coaxial', 'borde': (0.0, y_t), 'direccion': (1, 0),
                          'alimentacion': (xr, y_t), 'ancho_linea': w,
                          'puntos': ((xl + w/2, y_t), (xr - w/2, y_t)),
                          'pads': ((xl, y_t), (xr, y_t))},
                  info={'largo_adaptador_mm': round(ls, 2), 'altura_toma_mm': round(y_t, 2),
                        'longitud_traza_mm': round(l_traza, 2),
                        'placa_mm': [round(contorno.bounds[2] - contorno.bounds[0], 2),
                                     round(contorno.bounds[3] - contorno.bounds[1], 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'radiador_mm': [round(maxx - minx, 2), round(maxy - miny, 2)],
                        'hueco_minimo_mm': gap, 'pista_minima_mm': w, 'avisos': avisos,
                        'f_sin_cortar_MHz': (round(f*p.get('k_sim', 1.0)/(1 + p.get('sobrelargo', 0)/100)/1e6, 1)
                                             if ajuste.activo(p) and int(p.get('marcas', 0)) == 1 else None),
                        'ajuste': aj['notas'] or None})
