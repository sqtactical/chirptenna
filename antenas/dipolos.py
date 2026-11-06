"""Dipolo impreso y antenas colineales (omnidireccionales).

  - Dipolo: brazos rectos o de Koch. Alimentación 0 = SMA con balun impreso (como el excitado de la
    Yagi con boom: microstrip por un boom con tira de masa debajo; un brazo sale de la pista, cara
    superior, y el otro de la tira, cara inferior); 1 = coaxial soldado al centro (una cara, sin masa,
    como la J-pole).
  - Colineal coaxial impresa (COCO): tramos de λg/2 de dos tiras superpuestas, una en cada cara, que en
    cada unión se cruzan con dos vías (la de arriba pasa abajo y viceversa). Dentro de cada tramo la onda
    viaja como en una línea; al cruzarse, las corrientes exteriores de todos los tramos quedan en fase y
    radian juntas. SMA en un extremo (vivo a la tira superior, masa a la inferior).
  - Colineal Franklin: monopolo sobre plano de masa (λ/4) seguido de elementos de λ/2 unidos por
    horquillas de λ/4 (tiras paralelas, no radian) que invierten la fase; las horquillas alternan de lado.

Estimaciones orientativas (y calibradas con simulaciones cuando las haya: tipos.factor_calibracion).
"""
import math

from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste
from . import conector
from .materiales import C0, ancho_microstrip, eps_eff_microstrip
from .modelo import Antena
from .directivas import brazo_koch
from .jpole import eps_eff_cps
from .i18n import tr

BORDE_COBRE = 0.5
Y_COAXIAL = 6.0           # dipolo con coaxial: los brazos van a esta altura; debajo, la zona de soldadura


def _eq_koch(largo, n):
    """Longitud equivalente de una curva de Koch de cuerda 'largo' (la misma regla que la Yagi)."""
    return largo*(1 + 0.35*((4/3)**int(n) - 1))


def _info_placa(contorno, extra):
    x0, y0, x1, y1 = contorno.bounds
    extra.update({'placa_mm': [round(x1 - x0, 2), round(y1 - y0, 2)], 'area_placa_cm2': round(contorno.area/100, 2)})
    return extra


# ------------------------------------------------------------------ dipolo
# Calibrados con simulaciones en GPU (06-11): un brazo triangular ancho resuena con menos largo que uno recto
K_BOWTIE = 0.79
K_SIERPINSKI = 0.75   # bowtie de Sierpinski (iteración 2): los huecos lo alargan eléctricamente


def estimar_f_dipolo(p, eps_impreso):
    forma = int(p.get('forma', 0))
    if forma:
        # bowtie / bowtie de Sierpinski: sin Koch, y el brazo ancho es eléctricamente más corto
        total = 2*p['largo_brazo']/(K_BOWTIE if forma == 1 else K_SIERPINSKI) + (p['hueco'] if int(p['alimentacion']) == 1 else 0)
    else:
        total = 2*_eq_koch(p['largo_brazo'], p.get('iteracion', 0)) + (p['hueco'] if int(p['alimentacion']) == 1 else 0)
    return C0/(2*total*1e-3*math.sqrt(eps_impreso))


def generar_dipolo(p, s, eps_impreso):
    w = p['ancho_pista']
    n, ang, la = int(p.get('iteracion', 0)), p.get('angulo', 60), p['largo_brazo']
    margen = p.get('margen_borde', 2.0)
    vias, avisos = [], []
    forma = int(p.get('forma', 0))        # 0 = recto o Koch, 1 = bowtie, 2 = bowtie de Sierpinski

    def brazo(lado, y_d, desp):
        """Un brazo (lado = +1 derecho, −1 izquierdo), con el vértice de la bowtie o el inicio de la pista en
        (lado·desp, y_d). Devuelve (polilínea o None, polígono)."""
        if forma == 0:
            pol = brazo_koch(n, la, ang, lado < 0, y_d) + [lado*desp, 0]
            return pol, g.engordar(pol, w)
        a = g.brazo_bowtie(la, p.get('apertura', 70), w, int(p.get('iteracion_s', 2)) if forma == 2 else 0,
                           p.get('cuello_s', 1.0))
        a = affinity.translate(affinity.scale(a, xfact=lado, yfact=1, origin=(0, 0)), lado*desp, y_d)
        return None, a

    if int(p['alimentacion']) == 1:
        # Coaxial al centro: una cara; vivo al brazo derecho, malla al izquierdo
        hc = p['hueco']
        y_d = Y_COAXIAL
        if forma:
            # la bowtie es simétrica respecto al centro: sube el centro para que quepa entera, y la placa
            # la rodea con el mismo margen y las mismas esquinas redondeadas arriba y abajo (sin recorte)
            y_d = max(y_d, la*math.tan(math.radians(p.get('apertura', 70))/2))
        der, g_der = brazo(1, y_d, hc/2)
        izq, g_izq = brazo(-1, y_d, hc/2)
        pads = [g.rectangulo(hc/2, y_d - 1.0, hc/2 + 2.0, y_d + 1.0), g.rectangulo(-hc/2 - 2.0, y_d - 1.0, -hc/2, y_d + 1.0)]
        sup = unary_union([g_der, g_izq] + pads)
        inf = Polygon()
        soporte = g.rectangulo(-4.0, 0, 4.0, y_d)          # sitio para el coaxial y su sujeción
        contorno = g.contorno_placa([sup.buffer(margen), soporte], int(p.get('contorno', 1)),
                                    recorte=None if forma else (-1e4, 0, 1e4, 1e4))
        puerto = {'tipo': 'coaxial', 'borde': (0.0, y_d), 'direccion': (1, 0), 'alimentacion': (hc/2, y_d),
                  'ancho_linea': 2.0, 'puntos': ((-hc/2, y_d), (hc/2, y_d)),
                  'pads': ((-hc/2 - 1.0, y_d), (hc/2 + 1.0, y_d))}
        hueco = hc
    else:
        # SMA con balun impreso: microstrip por el boom y un brazo en cada cara
        w50 = ancho_microstrip(50, s.er, s.h)
        wb = max(p['ancho_boom'], w50 + 3*s.h)
        y_d = BORDE_COBRE + p['largo_alimentacion']
        if forma:
            y_d = max(y_d, la*math.tan(math.radians(p.get('apertura', 70))/2) + BORDE_COBRE + 0.2)
        der, g_der = brazo(1, y_d, 0.0)
        izq, g_izq = brazo(-1, y_d, 0.0)
        sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_d + w/2), g_der])
        inf = unary_union([g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_d + w/2), g_izq])
        a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
        contorno = g.contorno_placa([unary_union([sup, inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                    int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
        puerto = {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_d), 'ancho_linea': w50}
        hueco = None
        if p['largo_alimentacion'] < 0.15*C0/estimar_f_dipolo(p, eps_impreso)*1e3/math.sqrt(eps_impreso):
            avisos.append(tr('Boom corto: el balun funciona mejor con la tira de masa de ~λg/4 bajo la línea.'))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    sup, inf = sup.intersection(interior), inf.intersection(interior)
    x0, _, x1, _ = unary_union([g_der, g_izq]).bounds
    return Antena(tipo='dipolo_bowtie' if forma else 'dipolo', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=puerto, vias=vias,
                  info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(w, 2)],
                                              'hueco_minimo_mm': hueco, 'pista_minima_mm': w, 'avisos': avisos,
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


# ------------------------------------------------------------------ Vivaldi antipodal
def estimar_f_vivaldi(p, eps_impreso):
    """Frecuencia de corte inferior aproximada: la boca mide ~λ/2 (efectiva)."""
    return C0/(2*p['ancho_apertura']*1e-3*math.sqrt(eps_impreso))


def _aleta(p, w50, lado):
    """Aleta exponencial hacia el lado `lado` (+1 cara superior, −1 inferior), con la línea en x = 0.
    Arranca con el ancho de la línea en y = 0 (local) y acaba en la boca, a Lf de altura."""
    Wv, Lf, r = p['ancho_apertura'], p['largo_aleta'], p['tasa']
    xi_fin = p['abertura_interior']*Wv/2
    n = 60
    ts = [i/n for i in range(n + 1)]
    s = [(math.exp(r*t) - 1)/(math.exp(r) - 1) for t in ts]
    ext = [(w50/2 + (Wv/2 - w50/2)*si, Lf*t) for si, t in zip(s, ts)]
    inte = [(-w50/2 + (xi_fin + w50/2)*si, Lf*t) for si, t in zip(s, ts)]
    pol = Polygon(ext + inte[::-1])
    return affinity.scale(pol, xfact=lado, yfact=1, origin=(0, 0))


def generar_vivaldi(p, s, eps_impreso):
    w50 = ancho_microstrip(50, s.er, s.h)
    wb = max(p['ancho_boom'], w50 + 3*s.h)
    y_f = BORDE_COBRE + p['largo_alimentacion']          # donde empiezan las aletas
    margen = p.get('margen_borde', 2.0)
    sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_f + 0.01),
                       affinity.translate(_aleta(p, w50, 1), 0, y_f)])
    inf = unary_union([g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_f + 0.01),
                       affinity.translate(_aleta(p, w50, -1), 0, y_f)])
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    contorno = g.contorno_placa([unary_union([sup, inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    sup, inf = sup.intersection(interior), inf.intersection(interior)
    x0, y0_, x1, y1_ = unary_union([sup, inf]).bounds
    return Antena(tipo='vivaldi', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_f), 'ancho_linea': w50},
                  info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(y1_ - y_f, 2)],
                                              'hueco_minimo_mm': round(p['abertura_interior']*p['ancho_apertura'], 2),
                                              'pista_minima_mm': round(w50, 3), 'avisos': [],
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


# ------------------------------------------------------------------ colineal de dipolos en serie (microstrip)
def estimar_f_colineal_dipolos(p, eps_impreso):
    """Cada dipolo mide 2 brazos de `largo_brazo`: resuena donde esos dos brazos son λ/2 (efectiva)."""
    return C0/(2*2*p['largo_brazo']*1e-3*math.sqrt(eps_impreso))


def generar_colineal_dipolos(p, s, eps_impreso):
    """N dipolos en serie sobre una línea central (vivo en F.Cu, malla en B.Cu), unidos por tramos de microstrip
    de λg (así quedan en fase). Cada dipolo es una «U» en F.Cu (vivo, brazo superior, patas hacia arriba) y una
    «U» invertida en B.Cu (malla, brazo inferior, patas hacia abajo), con la barra en el eje y las patas a los
    lados de la línea.
    El coaxial se suelda en el arranque de la línea (vivo a la línea, malla a la tira de masa)."""
    w50 = ancho_microstrip(50, s.er, s.h)
    wa, xs = p['ancho_brazo'], p['separacion_patas']
    wb = max(min(p['ancho_boom'], 2*(xs - wa/2) - 1.5), w50 + 3*s.h)
    La, n = p['largo_brazo'], int(p['elementos'])
    avisos = []
    f_est = estimar_f_colineal_dipolos(p, eps_impreso)
    Ls = p['factor_linea']*C0/f_est*1e3/math.sqrt(eps_eff_microstrip(s.er, s.h, w50))
    if Ls < 2*La + 2.0:
        avisos.append(tr('Los dipolos se tocan: el tramo de línea es más corto que los dos brazos. Alarga el tramo o acorta los brazos.'))
    y_prim = BORDE_COBRE + p['largo_entrada'] + La
    ys = [y_prim + k*Ls for k in range(n)]
    F, B = [], []
    for k, yk in enumerate(ys):
        for cara, sentido in ((F, 1), (B, -1)):          # U arriba (vivo) y U invertida abajo (malla)
            cara.append(g.rectangulo(-xs - wa/2, yk - wa/2, xs + wa/2, yk + wa/2))          # barra en el eje
            for x in (-xs, xs):
                cara.append(g.rectangulo(x - wa/2, min(yk, yk + sentido*La), x + wa/2, max(yk, yk + sentido*La)))
    y_fin = ys[-1] + wa/2
    F.append(g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_fin))
    B.append(g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_fin))
    sup, inf = unary_union(F), unary_union(B)
    margen = p.get('margen_borde', 2.0)
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    contorno = g.contorno_placa([unary_union([sup, inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    sup, inf = sup.intersection(interior), inf.intersection(interior)
    x0, _, x1, y1_ = unary_union([sup, inf]).bounds
    if y1_ > 290:
        avisos.append(tr('La placa mide {0:.0f} mm: no cabe en un tubo de PVC de 30 cm. Quita dipolos o acorta los tramos.', y1_))
    return Antena(tipo='colineal_dipolos', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_prim), 'ancho_linea': w50},
                  info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(y1_, 2)],
                                              'hueco_minimo_mm': round(xs - wa/2 - wb/2, 2),
                                              'pista_minima_mm': round(min(w50, wa), 3),
                                              'longitud_linea_mm': round(Ls, 1), 'avisos': avisos,
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


# ------------------------------------------------------------------ colineal coaxial impresa (COCO)
def eps_eff_coco(s, w):
    """Cada tramo es una microstrip: tira estrecha (el vivo) arriba sobre la ancha (la malla) abajo."""
    return eps_eff_microstrip(s.er, s.h, w)


def estimar_f_coco(p, s):
    return C0/(2*p['largo_seccion']*1e-3*math.sqrt(eps_eff_coco(s, p['ancho_pista'])))


def generar_colineal_coco(p, s):
    """Como la colineal de trozos de coaxial: en cada tramo, vivo estrecho arriba y malla ancha abajo (con dos
    tiras iguales la línea queda equilibrada, las corrientes se cancelan y no radia: la primera versión dio
    η 8 %). En cada cruce, el vivo de un tramo pasa a ser la malla del siguiente y viceversa; lo que radia es
    la corriente por la cara exterior de las mallas, en fase en todos los tramos."""
    w, we = p['ancho_pista'], max(p['ancho_exterior'], p['ancho_pista'] + 1.0)
    ls, nsec, gap = p['largo_seccion'], int(p['secciones']), p['hueco']
    tw = 1.0                                  # ancho de las lengüetas que llevan a las vías (pad 0,8 mm)
    sep = 0.8                                 # hueco entre una lengüeta y la tira del tramo siguiente
    dx = max(w, we)/2 + tw/2 + sep            # las vías del cruce, a ±dx del eje
    margen = p.get('margen_borde', 2.0)
    sup, inf, vias = [], [], []
    a = BORDE_COBRE
    for k in range(nsec):
        b = a + ls
        sup.append(g.rectangulo(-w/2, a, w/2, b))          # vivo
        inf.append(g.rectangulo(-we/2, a, we/2, b))        # malla
        if k < nsec - 1:
            yj = b + gap/2                    # cruce entre el tramo k y el k+1
            # tramo k: arriba sale hacia +x hasta la vía (+dx); abajo, hacia −x (−dx)
            for capa, sx in ((sup, 1), (inf, -1)):
                capa.append(g.rectangulo(min(0, sx*(dx + tw/2)), b - tw, max(0, sx*(dx + tw/2)), b))
                capa.append(g.rectangulo(sx*dx - tw/2, b - tw, sx*dx + tw/2, yj + tw/2))
            # tramo k+1: arriba llega desde la vía de −dx; abajo, desde la de +dx
            a2 = b + gap
            for capa, sx in ((sup, -1), (inf, 1)):
                capa.append(g.rectangulo(min(0, sx*(dx + tw/2)), a2, max(0, sx*(dx + tw/2)), a2 + tw))
                capa.append(g.rectangulo(sx*dx - tw/2, yj - tw/2, sx*dx + tw/2, a2 + tw))
            vias += [(dx, yj), (-dx, yj)]
        a = b + gap
    # Pie de la tira inferior bajo el SMA (sus pads de masa)
    a_min = conector.ANCHO_MINIMO[conector.SMA]
    inf.append(g.rectangulo(-a_min/2 + 1.0, BORDE_COBRE, a_min/2 - 1.0, 6.0))
    cobre_sup, cobre_inf = unary_union(sup), unary_union(inf)
    contorno = g.contorno_placa([unary_union([cobre_sup, cobre_inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    cobre_sup, cobre_inf = cobre_sup.intersection(interior), cobre_inf.intersection(interior)
    ganancia = 2.15 + 10*math.log10(nsec)*0.8          # dipolo + ~80 % de la ganancia ideal del array
    avisos = []
    if nsec > 6:
        avisos.append(tr('Con muchos tramos, la corriente decae hacia la punta y la ganancia crece poco.'))
    return Antena(tipo='colineal_coco', parametros=dict(p), capas={'F.Cu': cobre_sup, 'B.Cu': cobre_inf},
                  ajuste=ajuste.vacio(), radiador=unary_union([cobre_sup, cobre_inf]), contorno=contorno,
                  zona_libre=contorno, vias=vias,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, BORDE_COBRE), 'ancho_linea': w},
                  info=_info_placa(contorno, {'radiador_mm': [round(2*dx + tw, 2), round(a - gap - BORDE_COBRE, 2)],
                                              'hueco_minimo_mm': min(gap, sep), 'pista_minima_mm': min(w, tw),
                                              'eps_eff_tramo': round(eps_eff_coco(s, w), 3),
                                              'ganancia_estimada_dBi': round(ganancia, 1), 'avisos': avisos,
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


# ------------------------------------------------------------------ colineal Franklin
def estimar_f_franklin(p, eps_impreso):
    return C0/(2*p['largo_elemento']*1e-3*math.sqrt(eps_impreso))


def largo_horquilla(p, eps_impreso, s):
    """Cada rama de la horquilla: λ/4 en la línea de tiras paralelas a la frecuencia de los elementos."""
    return p['factor_horquilla']*p['largo_elemento']/2*math.sqrt(eps_impreso/eps_eff_cps(s.er))


def generar_colineal_franklin(p, s, eps_impreso, lg):
    """lg: largo del plano de masa (lo calcula tipos con el mismo criterio que los monopolos)."""
    w, le, ne = p['ancho_pista'], p['largo_elemento'], int(p['elementos'])
    sh = p['hueco_horquilla'] + w             # separación entre ejes de las dos ramas
    lh = largo_horquilla(p, eps_impreso, s)
    pts = [(0.0, 0.0), (0.0, le/2)]           # base de λ/4 sobre la masa
    y = le/2
    for i in range(ne):
        lado = 1 if i % 2 == 0 else -1        # las horquillas alternan de lado
        pts += [(lado*lh, y), (lado*lh, y + sh), (0.0, y + sh), (0.0, y + sh + le)]
        y += sh + le
    rad = g.mover(g.engordar(pts, w), 0, lg)
    w50 = ancho_microstrip(50, s.er, s.h)
    margen = p.get('margen_borde', 2.0)
    minx, _, maxx, maxy = rad.bounds
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    if int(p.get('masa', 0)) == 0:
        # manual: masa centrada con el ancho pedido (o más, si las horquillas no caben)
        semi = max(p['ancho_placa']/2, max(abs(minx), abs(maxx)) + margen)
        gx0, gx1 = -semi, semi
    else:
        gx0, gx1 = min(minx - margen, -a_min/2), max(maxx + margen, a_min/2)
    contorno = g.contorno_placa([g.rectangulo(gx0, 0, gx1, lg), rad.buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(gx0 - 1e3, 0, gx1 + 1e3, 1e4))
    masa = g.rectangulo(gx0, 0, gx1, lg).intersection(contorno.buffer(-BORDE_COBRE, join_style='mitre'))
    alim = g.rectangulo(-w50/2, BORDE_COBRE, w50/2, lg + 0.01)
    cx0, _, cx1, alto = contorno.bounds
    avisos = []
    if lg < 0.95*le/2:
        avisos.append(tr('Masa de {0:.0f} mm, menos de λ/4: el cable pasa a formar parte de la antena (ferrita al medir).', lg))
    return Antena(tipo='colineal_franklin', parametros=dict(p), capas={'F.Cu': unary_union([alim, rad]), 'B.Cu': masa},
                  ajuste=ajuste.vacio(), radiador=rad, contorno=contorno,
                  zona_libre=g.rectangulo(cx0, lg, cx1, alto).intersection(contorno),
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, lg), 'ancho_linea': w50,
                          'largo_linea_mm': lg - BORDE_COBRE},
                  info=_info_placa(contorno, {'ancho_linea_50ohm_mm': round(w50, 3), 'largo_horquilla_mm': round(lh, 2),
                                              'masa_mm': [round(gx1 - gx0 - 2*BORDE_COBRE, 2), round(lg - BORDE_COBRE, 2)],
                                              'radiador_mm': [round(maxx - minx, 2), round(maxy - lg, 2)],
                                              'hueco_minimo_mm': p['hueco_horquilla'], 'pista_minima_mm': w,
                                              'ganancia_estimada_dBi': round(2.15 + 10*math.log10(1 + ne)*0.7, 1),
                                              'avisos': avisos, 'f_sin_cortar_MHz': None, 'ajuste': None}))
