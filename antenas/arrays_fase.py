"""Array de dos dipolos bowtie alimentados por separado desde un solo conector, con una línea de retardo en una rama (sin validar).

Idea (16-11): la colineal alimentada en serie desadapta en cuanto se cambia la separación (los dipolos se acoplan por la línea común), así que
no sirve para inclinar el haz. Aquí cada dipolo cuelga de su propia línea de 50 Ω y el desfase lo fija solo la diferencia de largo entre las dos:

  conector (borde inferior) → línea de 50 Ω → transformador λ/4 de ~35 Ω → T → dos ramas de 50 Ω de igual largo → dipolo 1 (abajo) y dipolo 2 (arriba)

La rama con retardo lleva un meandro de largo extra ΔL = |desfase|/360 · λg. Los dos dipolos están en el mismo eje (colineales, el eje es Y) y con la
misma orientación (brazo de arriba en F.Cu, de abajo en B.Cu): con ramas iguales radian en fase y el haz sale perpendicular al eje (como la colineal);
con el retardo en la rama del dipolo de arriba el haz se inclina hacia +y (desfase > 0) o hacia −y (< 0): sen τ = Δφ·λ0/(2π·d), con d la separación.

Cada dipolo es el bowtie antipodal de `dipolos.generar_dipolo` girado 90°: la línea entra por la izquierda con su tira de masa (B.Cu) debajo, a modo de
boom/balun, y los brazos salen hacia ±Y. Solo dos elementos por ahora.
"""
import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste, conector
from .materiales import C0, ancho_microstrip, eps_eff_microstrip
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5
K_ARRAY_FASE = 0.75             # f simulada / f del dipolo_bowtie suelto: FR4, brazo 14 mm, apertura 50°, boom 20 mm → ~2440 MHz (CPU, 17-11; boom 17 mm: 2521, 22 mm: 2359 MHz); sin calibrar en otros sustratos
Z_TRANSFORMADOR = 35.4         # √(50 Ω · 25 Ω): de la línea de 50 Ω a dos ramas de 50 Ω en paralelo


def estimar_f_array_fase(p, nombre_sustrato=None):
    """Cada dipolo es un bowtie sin balun impreso largo: la estimación (calibrada) del `dipolo_bowtie`. El acoplo entre los dos elementos la mueve."""
    from . import tipos
    return K_ARRAY_FASE*tipos.estimar_f('dipolo_bowtie', {'largo_brazo': p['largo_brazo'], 'forma': max(int(p.get('forma', 1) or 1), 1),
                                             'iteracion_s': p.get('iteracion_s', 2), 'alimentacion': 0, 'apertura': p.get('apertura', 50)}, nombre_sustrato)


def _brazo(p, sentido, x, y):
    """Brazo bowtie (o de Sierpinski) con el vértice en (x, y) y apuntando a +Y (sentido +1) o −Y (−1)."""
    forma = int(p.get('forma', 1) or 1)
    a = g.brazo_bowtie(p['largo_brazo'], p.get('apertura', 50), p['ancho_pista'], int(p.get('iteracion_s', 2)) if forma == 2 else 0,
                       p.get('cuello_s', 1.0))                      # el brazo sale hacia +X con el vértice en el origen
    a = affinity.rotate(a, 90*sentido, origin=(0, 0))
    return affinity.translate(a, x, y)


def generar_array_fase(p, s, eps):
    from . import tipos
    w50 = ancho_microstrip(50, s.er, s.h)
    wT = ancho_microstrip(Z_TRANSFORMADOR, s.er, s.h)
    wb = max(p['ancho_boom'], w50 + 3*s.h, wT + 3*s.h)
    La = p['largo_brazo']
    d = float(p['separacion'])
    avisos = []
    f_est = tipos.estimar_f('array_fase', p, s.nombre)
    lam0 = C0/f_est*1e3
    lam_g = lam0/math.sqrt(eps_eff_microstrip(s.er, s.h, w50))
    lam_gT = lam0/math.sqrt(eps_eff_microstrip(s.er, s.h, wT))
    desfase = float(p.get('desfase', 0) or 0)
    dL = abs(desfase)/360*lam_g                                      # largo extra de la rama retardada
    semi = La*math.tan(math.radians(p.get('apertura', 50))/2)        # semiancho de la base de un brazo (en X)
    if d < 2*La + 4:
        avisos.append(tr('Los brazos de los dos dipolos se tocan o casi ({0:.1f} mm entre centros para {1:.1f} mm de dipolo): aumenta la separación.', d, 2*La))
    # trazado (X a la derecha, Y hacia arriba): tronco en x = 0, T en y_m, ramas con tramo vertical en x_v y horizontal hasta el centro del dipolo en x_d
    x_v = wb + 4.0
    x_d = x_v + float(p['largo_alimentacion'])
    y_m = max(d/2 + La + BORDE_COBRE + 0.2, BORDE_COBRE + lam_gT/4 + 4.0)
    ys = (y_m - d/2, y_m + d/2)                                      # centros de los dipolos 1 y 2
    retardada = 1 if desfase > 0 else 0 if desfase < 0 else None     # rama con el meandro (índice del dipolo): desfase > 0 retarda al de arriba
    u = dL/2                                                         # el meandro sube (o baja) u, avanza wm y vuelve: añade 2u
    wm = w50 + 3.0                                                   # separación entre las patas del meandro: 3 mm
    xb = x_v + 3.0
    if retardada is not None and xb + wm > x_d - semi - 2.0:
        avisos.append(tr('El meandro del retardo no cabe delante de los brazos: alarga el tramo hasta el dipolo.'))
    lineas = []                                                      # polilíneas de las ramas (línea de 50 Ω)
    for k, yk in enumerate(ys):
        sgn = 1 if k == 1 else -1
        pts = [(0.0, y_m), (x_v, y_m), (x_v, yk)]
        if k == retardada:
            pts += [(xb, yk), (xb, yk + sgn*u), (xb + wm, yk + sgn*u), (xb + wm, yk)]
        pts.append((x_d, yk))
        lineas.append(pts)
    y_T0 = y_m - lam_gT/4
    tronco = [(0.0, BORDE_COBRE), (0.0, y_T0)]
    sup = [g.engordar(tronco, w50), g.rectangulo(-wT/2, y_T0, wT/2, y_m + wT/2)]
    inf = [g.engordar(tronco, wb), g.rectangulo(-wb/2, y_T0, wb/2, y_m + wb/2)]
    for pts in lineas:
        sup.append(g.engordar(pts, w50))
        inf.append(LineString(pts).buffer(wb/2, cap_style='flat', join_style='mitre', mitre_limit=2.0))
    for k, yk in enumerate(ys):
        sup.append(_brazo(p, 1, x_d, yk))                            # brazo de arriba, en F.Cu, unido a la línea
        inf.append(_brazo(p, -1, x_d, yk))                           # brazo de abajo, en B.Cu, unido a la tira de masa
    sup, inf = unary_union(sup), unary_union(inf)
    margen = p.get('margen_borde', 2.0)
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    contorno = g.contorno_placa([unary_union([sup, inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    sup, inf = sup.intersection(interior), inf.intersection(interior)
    puerto = {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 2.0), 'ancho_linea': w50}
    tau = None
    if abs(desfase) > 0 and d > 0:
        tau = math.degrees(math.asin(max(-1.0, min(1.0, desfase*math.pi/180*lam0/(2*math.pi*d)))))
    x0, y0, x1, y1 = contorno.bounds
    huecos = [wm - w50, d - 2*La, 2.0]
    info = {'placa_mm': [round(x1 - x0, 2), round(y1 - y0, 2)], 'area_placa_cm2': round(contorno.area/100, 2),
            'radiador_mm': [round(2*semi, 2), round(d + 2*La, 2)],
            'hueco_minimo_mm': round(max(min(h for h in huecos if h > 0), 0.3), 2), 'pista_minima_mm': round(min(w50, p['ancho_pista']), 3),
            'separacion_mm': d, 'largo_extra_retardo_mm': round(dL, 2), 'avisos': avisos, 'f_sin_cortar_MHz': None, 'ajuste': None}
    if tau is not None:
        info['inclinacion_estimada_grados'] = round(tau, 1)
    return Antena(tipo='array_fase', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=puerto, info=info)
