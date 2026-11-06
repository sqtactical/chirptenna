"""Antenas directivas: quasi-Yagi impresa (dipolo de Koch) y arrays de parches con red corporativa.

Quasi-Yagi (tipo Kaneda): microstrip de 50 Ω que se divide en dos ramas; una lleva
λg/2 de más (balun de 180°). Al pasar el borde del plano de masa (que hace de
reflector) las ramas siguen como línea de tiras paralelas (CPS) hasta el dipolo,
cuyos brazos pueden ser curvas de Koch. Uno o dos directores encima.

Array de parches: N×M parches alimentados por su borde inferior con una red en
árbol (H): cada parche lleva un transformador λ/4 de su resistencia de borde a
100 Ω; cada unión de dos ramas de 100 Ω da 50 Ω, y un λ/4 de 70,7 Ω lo vuelve a
pasar a 100 Ω para el nivel siguiente. Todas las ramas tienen la misma longitud
(alimentación en fase). Se estiman las pérdidas de la red en el sustrato.
"""
import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste
from .materiales import ancho_microstrip, eps_eff_microstrip, lambda0_mm, C0
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5


# ------------------------------------------------------------------ quasi-Yagi
def brazo_koch(iteracion, largo, angulo, hacia_izquierda, y):
    """Brazo de dipolo: curva de Koch horizontal desde x=0 (centro) hacia fuera."""
    signo = -1 if hacia_izquierda else 1
    pts = g.koch(iteracion, (0, 0), (signo*largo, 0), angulo)
    # que las indentaciones apunten hacia +y (lejos del reflector) en los dos brazos
    if hacia_izquierda:
        pts[:, 1] = -pts[:, 1]
    return pts + [0, y]


def generar_yagi(p, s, eps_eff_impreso):
    w50 = ancho_microstrip(50, s.er, s.h)
    wr = p['ancho_rama']
    w = p['ancho_pista']
    f_est = estimar_f_yagi(p, eps_eff_impreso)
    lam_g = lambda0_mm(f_est)/math.sqrt(eps_eff_microstrip(s.er, s.h, wr))
    gap = p['hueco_cps']
    xa, xb = -(gap/2 + wr/2), gap/2 + wr/2          # ejes de las dos ramas
    # Rama B: rodeo a la derecha. Con el trazado de abajo, B - A = 4d + 2·alto_u, y se
    # quiere λg/2 (balun de 180°).
    extra = lam_g/2
    d = max(p['ancho_rodeo'], wr + 0.6)              # escalado a 5,8 GHz no puede pisar las ramas
    alto_u = max((extra - 4*d)/2, 0.0)
    if alto_u == 0.0:
        d = extra/4
    auto = int(p.get('masa', 0)) == 1
    lg_min = p['largo_balun'] + alto_u + w50 + 3              # lo justo para el balun
    con_pi = ajuste.activo(p) and int(p.get('red_pi', 0)) == 1
    if con_pi:
        lg_min = max(lg_min, p['largo_balun'] + 14.0)         # sitio para la red en π bajo la T
    lg = lg_min if auto else max(p['largo_masa'], lg_min)
    y_t = lg - p['largo_balun']                     # unión en T
    piezas = [g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_t + wr/2)]
    # Rama A: recta desde la T hasta el borde de masa
    piezas.append(g.engordar([(0, y_t), (xa, y_t), (xa, lg)], wr))
    xr, arriba = xb + d, lg - 2*wr
    rodeo = [(0, y_t), (xr, y_t), (xr, y_t - alto_u), (xr + d, y_t - alto_u),
             (xr + d, arriba), (xb, arriba), (xb, lg)]
    piezas.append(g.engordar(rodeo, wr))
    # CPS por encima del borde de masa hasta el dipolo
    y_d = lg + p['alto_cps']
    piezas.append(g.engordar([(xa, lg), (xa, y_d)], wr))
    piezas.append(g.engordar([(xb, lg), (xb, y_d)], wr))
    # Dipolo de Koch
    n, la, ang = int(p['iteracion']), p['largo_brazo'], p['angulo']
    izq = brazo_koch(n, la, ang, True, y_d) + [xa + wr/2, 0]
    der = brazo_koch(n, la, ang, False, y_d) + [xb - wr/2, 0]
    piezas += [g.engordar(izq, w), g.engordar(der, w)]
    radiador_partes = [g.engordar(izq, w), g.engordar(der, w)]
    aj = ajuste.vacio()
    if ajuste.activo(p):
        # sobrelargo/marcas/tramos simétricos en las puntas de los dos brazos (f ∝ 1/largo de cada brazo)
        brazo_eq = (2*la*(1 + 0.35*((4/3)**n - 1)) + gap + 2*wr)/2
        for pts_brazo, pref in ((izq, 'I'), (der, 'D')):
            extra_b, a_b, _ = ajuste.alargar_polilinea(pts_brazo, w, brazo_eq, 1.0, f_est*p.get('k_sim', 1.0), p,
                                                       prefijo=pref)
            if extra_b is not None:
                piezas.append(extra_b)
                radiador_partes.append(extra_b)
            if pref == 'D':
                a_b['notas'] = []                  # las notas ya salen con el brazo izquierdo
            aj = ajuste.unir(aj, a_b)
    # Directores (rectos o de Koch, con la misma iteración), cada uno un poco más corto
    y_dir = y_d
    nd = int(p['directores'])
    ld = p['factor_director']*(2*la + gap + 2*wr)
    largos = []
    for k in range(nd):
        y_dir += p['separacion_director']
        dirc = _elemento(n, ld, ang, y_dir, w)          # misma forma que el dipolo (lección 42)
        piezas.append(dirc)
        radiador_partes.append(dirc)
        largos.append(round(ld, 2))
        ld *= 1 - p.get('reduccion_director', 0.0)
    cobre = unary_union(piezas)
    if con_pi:
        aj = ajuste.unir(aj, ajuste.red_pi(0.0, max(8.6, y_t - 5.1), w50, p, vertical=True, lado=-1))
        cobre = unary_union([cobre.difference(unary_union(aj['cortes']))] + aj['islas_masa'])
    minx, _, maxx, maxy = cobre.bounds
    margen = p.get('margen_borde', 2.0)
    ancho_min = 2*max(abs(minx), abs(maxx)) + 2*margen       # reflector tan ancho como el dipolo
    ancho = ancho_min if auto else max(p['ancho_placa'], ancho_min)
    masa_rect = g.rectangulo(-ancho/2, 0, ancho/2, lg)
    contorno = g.contorno_placa([masa_rect, cobre.buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(-1e4, 0, 1e4, 1e4))
    cx0, _, cx1, alto = contorno.bounds
    masa = masa_rect.intersection(contorno.buffer(-BORDE_COBRE, join_style='mitre'))
    radiador = unary_union(radiador_partes + [g.engordar([(xa, lg), (xa, y_d)], wr),
                                              g.engordar([(xb, lg), (xb, y_d)], wr)])
    # Ganancia orientativa de una Yagi impresa: ~4 dBi con reflector y +~2,2 dB por duplicar elementos
    ganancia = 4 + 2.2*math.log2(1 + nd)
    avisos = []
    if nd > 4 and p['separacion_director'] < 0.1*lambda0_mm(f_est):
        avisos.append(tr('Directores muy juntos para tantos elementos: separación típica 0,15–0,3 λ0.'))
    return Antena(tipo='yagi_koch', parametros=dict(p), capas={'F.Cu': cobre, 'B.Cu': masa}, ajuste=aj,
                  radiador=radiador, contorno=contorno,
                  zona_libre=g.rectangulo(cx0, lg, cx1, alto).intersection(contorno),
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_t), 'ancho_linea': w50},
                  info={'ancho_linea_50ohm_mm': round(w50, 3), 'retardo_balun_mm': round(extra, 2),
                        'placa_mm': [round(cx1 - cx0, 2), round(alto, 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'radiador_mm': [round(maxx - minx, 2), round(maxy - lg, 2)],
                        'largos_directores_mm': largos,
                        'hueco_minimo_mm': round(min(gap, d - wr), 3),
                        'pista_minima_mm': min(w, wr),
                        'ganancia_estimada_dBi': round(ganancia, 1), 'avisos': avisos,
                        'f_sin_cortar_MHz': (round(f_est*p.get('k_sim', 1.0)/(1 + p.get('sobrelargo', 0)/100)/1e6, 1)
                                             if ajuste.activo(p) and int(p.get('marcas', 0)) == 1 else None),
                        'ajuste': aj['notas'] or None})


def estimar_f_yagi(p, eps_eff_impreso):
    """Dipolo impreso: resuena cuando la longitud equivalente total ≈ λ/2 efectiva."""
    n = int(p['iteracion'])
    brazo_eq = p['largo_brazo']*(1 + 0.35*((4/3)**n - 1))
    total = 2*brazo_eq + p['hueco_cps'] + 2*p['ancho_rama']
    return C0/(2*total*1e-3*math.sqrt(eps_eff_impreso))


# ------------------------------------------------------------------ Yagi de doble cara con boom
def _elemento(n, largo, angulo, y, w):
    """Elemento parásito centrado en x=0: recto (n=0) o de Koch con LA MISMA FORMA que el dipolo excitado
    (dos brazos de largo/2 desde el centro, muescas hacia +y). Antes era una sola curva de Koch del largo
    entero, con muescas el doble de grandes: eléctricamente más corta, el reflector de 1,05× hacía de
    director y la Yagi de Koch radiaba hacia atrás (diagnóstico: herramientas/diag_yagi_boom.py)."""
    if n == 0:
        return g.engordar(g.koch(0, (-largo/2, y), (largo/2, y), angulo), w)
    return unary_union([g.engordar(brazo_koch(n, largo/2, angulo, True, y), w),
                        g.engordar(brazo_koch(n, largo/2, angulo, False, y), w)])


def largo_equivalente_brazo(p):
    n = int(p['iteracion'])
    return p['largo_brazo']*(1 + 0.35*((4/3)**n - 1))


# Calibrado con openEMS (tanda 3): con brazos de 23,7 mm resonó a 2063 MHz y hicieron falta 20,6 mm
# para 2436 MHz; el dipolo rodeado de parásitos y sobre la tira de masa resuena un 13 % más bajo
K_DIPOLO_BOOM = 0.87


def estimar_f_yagi_boom(p, eps_eff_impreso):
    """Dipolo de doble cara: resuena cuando los dos brazos (equivalentes) suman λ/2 efectiva."""
    return K_DIPOLO_BOOM*C0/(2*2*largo_equivalente_brazo(p)*1e-3*math.sqrt(eps_eff_impreso))


def generar_yagi_boom(p, s, eps_eff_impreso):
    """Yagi impresa de doble cara (tipo comercial): el boom lleva la microstrip de 50 Ω (pista arriba,
    tira de masa abajo). En su extremo, un brazo del dipolo sale de la pista (cara superior, hacia +x) y
    el otro de la tira de masa (cara inferior, hacia −x): la línea hace de balun. El reflector va en la
    cara inferior, unido a la tira de masa por su centro (punto de tensión nula); los directores, en la
    cara superior sueltos o, con unir_boom, en la inferior unidos por una tira central (antena entera a
    masa en continua). Elementos rectos (iteración 0) o de Koch. Radia hacia +y.

    Alimentación: 0 = directa (el dipolo rodeado de parásitos baja a ~10–15 Ω y solo adapta con el
    reflector lejos, ~0,35 λ); 1 = transformador λ/4 de z_transformador ohmios en el boom, justo antes
    del dipolo (50 → ~12 Ω), para poder llevar el reflector a 0,15–0,2 λ.
    """
    w50 = ancho_microstrip(50, s.er, s.h)
    w = p['ancho_pista']
    wb = max(p['ancho_boom'], w50 + 3*s.h, 8.0)       # masa para la microstrip y los pads del SMA
    n, ang, la = int(p['iteracion']), p['angulo'], p['largo_brazo']
    f_est = estimar_f_yagi_boom(p, eps_eff_impreso)
    lam0 = lambda0_mm(f_est)
    sep_r, sep_d = p['separacion_reflector']*lam0, p['separacion_director']*lam0   # en λ0 → mm
    y_r = BORDE_COBRE + p['largo_alimentacion']        # reflector
    y_d = y_r + sep_r                                  # dipolo
    sup, inf = [], []
    # Microstrip por el boom: pista arriba y tira de masa abajo, hasta el dipolo
    trafo = None
    if int(p.get('alimentacion', 0)) == 1:
        zt = p['z_transformador']
        wt = ancho_microstrip(zt, s.er, s.h)
        lt = lambda0_mm(f_est)/4/math.sqrt(eps_eff_microstrip(s.er, s.h, wt))
        y_t = max(y_d - lt, y_r + w)                    # no puede empezar antes del reflector
        sup.append(g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_t + 0.01))
        sup.append(g.rectangulo(-wt/2, y_t, wt/2, y_d + w/2))
        inf.append(g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_t + 0.01))
        inf.append(g.rectangulo(-(wt/2 + 1.5*s.h), y_t, wt/2 + 1.5*s.h, y_d + w/2))   # masa bajo el tramo ancho
        trafo = {'Z_ohm': zt, 'ancho_mm': round(wt, 2), 'largo_mm': round(y_d - y_t, 2),
                 'largo_lambda4_mm': round(lt, 2)}
    else:
        sup.append(g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_d + w/2))
        inf.append(g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_d + w/2))
    plegado = int(p.get('alimentacion', 0)) == 2
    vias, avisos = [], []
    if plegado:
        # Dipolo plegado: el brazo inferior va partido como el dipolo normal (mitad derecha desde la pista,
        # cara superior; mitad izquierda desde la masa del boom, cara inferior) y un conductor superior
        # entero, en la cara superior, une los dos extremos: por la derecha directamente y por la
        # izquierda con una vía al brazo de abajo. Con conductores iguales la impedancia es ~4 veces la del
        # dipolo simple: los 10–15 Ω con los parásitos cerca pasan a ~40–60 Ω sin adaptador. Solo recto.
        if n > 0:
            avisos.append(tr('El dipolo plegado se hace siempre recto: la iteración de Koch solo afecta a los parásitos.'))
        sp = p['separacion_plegado']
        y_s = y_d + sp
        sup.append(g.engordar([(0.0, y_d), (la, y_d), (la, y_s), (-la, y_s), (-la, y_d)], w))
        inf.append(g.engordar([(0.0, y_d), (-la, y_d)], w))
        vias.append((-la, y_d))
    else:
        # Dipolo: brazo derecho arriba (desde la pista) y brazo izquierdo abajo (desde la masa)
        der = brazo_koch(n, la, ang, False, y_d)
        izq = brazo_koch(n, la, ang, True, y_d)
        sup.append(g.engordar(der, w))
        inf.append(g.engordar(izq, w))
    l_dip = 2*la
    # Reflector (cara inferior, unido a la masa por el centro)
    l_ref = p['factor_reflector']*l_dip
    inf.append(_elemento(n, l_ref, ang, y_r, w))
    # Directores
    unidos = int(p.get('unir_boom', 0)) == 1
    nd = int(p['directores'])
    ld = p['factor_director']*l_dip
    y_dir = y_d
    largos = []
    y_tira = y_d
    for k in range(nd):
        y_dir += sep_d
        el = _elemento(n, ld, ang, y_dir, w)
        (inf if unidos else sup).append(el)
        largos.append(round(ld, 2))
        ld *= 1 - p.get('reduccion_director', 0.0)
        # en x = 0 el elemento de Koch está en el vértice de la muesca central, no en su base
        y_tira = max(y_tira, el.intersection(g.rectangulo(-w/2, y_dir - w, w/2, y_dir + ld)).bounds[3] - w/2)
    if unidos and nd:
        inf.append(g.rectangulo(-w/2, y_d, w/2, y_tira))
    cobre_sup, cobre_inf = unary_union(sup), unary_union(inf)
    margen = p.get('margen_borde', 2.0)
    contorno = g.contorno_placa([unary_union([cobre_sup, cobre_inf]).buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    cobre_sup, cobre_inf = cobre_sup.intersection(interior), cobre_inf.intersection(interior)
    cx0, _, cx1, alto = contorno.bounds
    sep_l = p['separacion_reflector'] + p['separacion_director']*nd
    ganancia = 4.5 + 2.2*math.log2(1 + nd)              # reflector + dipolo ≈ 4,5 dBi; +~2,2 dB por duplicar
    if not 0.1 <= p['separacion_reflector'] <= 0.3 and not plegado:
        avisos.append(tr('Reflector a {0:.2f} λ0 del dipolo: lo habitual es 0,15–0,25 λ0 (más cerca baja la impedancia y la eficiencia).', p["separacion_reflector"]))
    if p['factor_reflector'] <= 1.0:
        avisos.append(tr('Reflector más corto que el dipolo: actuará como director y el haz irá hacia atrás.'))
    return Antena(tipo='yagi_boom', parametros=dict(p), capas={'F.Cu': cobre_sup, 'B.Cu': cobre_inf},
                  ajuste=ajuste.vacio(), radiador=unary_union([cobre_sup, cobre_inf]), contorno=contorno,
                  zona_libre=None, vias=vias,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_d), 'ancho_linea': w50,
                          'largo_linea_mm': y_d - BORDE_COBRE},
                  info={'ancho_linea_50ohm_mm': round(w50, 3), 'ancho_boom_mm': round(wb, 2),
                        'placa_mm': [round(cx1 - cx0, 2), round(alto, 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'largo_dipolo_mm': round(l_dip, 2), 'largo_reflector_mm': round(l_ref, 2),
                        'largos_directores_mm': largos, 'largo_boom_lambda0': round(sep_l, 3),
                        'transformador': trafo, 'separaciones_mm': [round(sep_r, 2), round(sep_d, 2)],
                        'hueco_minimo_mm': round(p['separacion_plegado'] - w, 3) if plegado else None,
                        'pista_minima_mm': min(w, w50),
                        'ganancia_estimada_dBi': round(ganancia, 1), 'avisos': avisos,
                        'f_sin_cortar_MHz': None, 'ajuste': None})


# ------------------------------------------------------------------ panel de dipolos sobre reflector
# Sin calibrar: dipolo impreso ancho (acorta) sobre reflector a ~λ/4 (casi no mueve la resonancia)
K_DIPOLO_PANEL = 0.95
TALADRO_TORNILLO = 3.2          # M3, para los separadores de nailon
PAD_VIVO = 3.5                  # pad del vivo del coaxial (cara superior), cuadrado
PAD_MALLA = 6.0                 # pad de la malla (cara inferior), cuadrado
TALADRO_SMA_PANEL = 6.5         # SMA hembra de panel (rosca 1/4-36) en el reflector
HUECO_CRUCE = 3.0               # hueco entre las dos tiras de una misma cara en el cruce (≥ 2 celdas de malla)


K_BOWTIE_PANEL = 0.85           # sin calibrar: un brazo triangular ancho resuena con ~85 % del largo de uno recto


def estimar_f_panel(p, eps_eff_impreso):
    """Dipolo impreso con un brazo en cada cara: resuena cuando los brazos suman λ/2 efectiva.
    Con bowtie (elemento 1 o 2) el brazo triangular es eléctricamente más corto."""
    la = p['largo_brazo']/(K_BOWTIE_PANEL if int(p.get('elemento', 0)) else 1.0)
    return K_DIPOLO_PANEL*C0/(2*2*la*1e-3*math.sqrt(eps_eff_impreso))


def generar_panel_dipolos(p, s, eps_eff_impreso):
    """Panel: array 2×2 o 4×4 de dipolos impresos sobre un reflector (otra placa o una chapa) separado por aire.

    Cada dipolo lleva un brazo en cada cara (el de arriba hacia +x, el de abajo hacia −x) y se alimenta
    por su centro con una línea de tiras paralelas (PSL: la misma tira en las dos caras, equilibrada, así
    que no hace falta balun y la red apenas radia). Red en H con todas las ramas iguales (en fase):
    dipolo → 100 Ω; dos ramas de 100 Ω en paralelo dan 50 Ω y un λ/4 de 70,7 Ω lo vuelve a subir a 100 Ω
    para el nivel siguiente. En el centro quedan 50 Ω: el coaxial llega por detrás, atravesando el reflector
    (malla soldada al reflector y al pad de la cara inferior, vivo por un taladro al pad de la superior).
    Una PSL de impedancia Z equivale, por imagen, a una microstrip de Z/2 sobre la mitad del grosor.
    Polarización según x. Radia hacia +z (lado contrario al reflector, que queda en z < 0).
    Simétrico (por defecto): en cada bloque 2×2 la columna izquierda va espejada (brazo de arriba hacia
    −x) y su rama lleva un cruce (las tiras cambian de cara con dos vías) para volver a ir en fase. Con
    las dos columnas iguales, la izquierda ve a su vecina con el brazo de la otra cara y el acoplo
    distinto las desfasa ~45°: el haz se inclinaba 9° en el plano E (−1,1 dB de frente en el 2×2).
    """
    n = int(p['tamano'])
    if n not in (1, 2, 4):
        raise ValueError(tr('El panel admite un solo elemento, 2×2 o 4×4'))
    elemento = int(p.get('elemento', 0))             # 0 = dipolo recto, 1 = bowtie, 2 = bowtie de Sierpinski
    h2 = s.h/2
    w100 = float(ancho_microstrip(50, s.er, h2))
    w70 = float(ancho_microstrip(50/math.sqrt(2), s.er, h2))
    f_est = estimar_f_panel(p, eps_eff_impreso)
    lam0 = lambda0_mm(f_est)
    l70 = lam0/4/math.sqrt(eps_eff_microstrip(s.er, h2, w70))
    dx = dy = p['separacion']*lam0
    la, wd = p['largo_brazo'], p['ancho_dipolo']
    simetrico = int(p.get('simetrico', 1)) == 1
    sup, inf = [], []
    vias = []
    avisos = []

    def brazos(xc, yc, o):
        """Los dos brazos de un elemento centrado en (xc, yc): (cara superior, cara inferior). o = +1: el de
        arriba hacia +x (−1: espejado)."""
        if elemento == 0:
            return (g.rectangulo(xc - o*w100/2, yc - wd/2, xc + o*la, yc + wd/2),
                    g.rectangulo(xc - o*la, yc - wd/2, xc + o*w100/2, yc + wd/2))
        a = g.brazo_bowtie(la, p.get('apertura', 70), w100, int(p.get('iteracion_s', 2)) if elemento == 2 else 0,
                           p.get('cuello_s', 1.0))
        return tuple(affinity.translate(affinity.scale(a, xfact=sx, yfact=1, origin=(0, 0)), xc, yc)
                     for sx in (o, -o))

    def tira(a, b, w):
        """Tramo de PSL: la misma tira en las dos caras."""
        t = g.engordar([a, b], w)
        sup.append(t)
        inf.append(t)

    def cruce(a, b, w):
        """Tramo de PSL de a (lado de los dipolos) a b (lado del centro) en el que las tiras cambian de
        cara: en el medio cada una se aparta en diagonal hacia una vía (una a cada lado del eje)."""
        (x0, y0), (x1, y1) = a, b
        largo = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0)/largo, (y1 - y0)/largo
        nx, ny = -uy, ux
        d = (HUECO_CRUCE + w)/math.sqrt(2)          # así las diagonales paralelas quedan a HUECO_CRUCE
        if largo < 2*d + 2*w:
            avisos.append(tr('La rama es demasiado corta para el cruce de tiras: sube la separación.'))
        mx, my = (x0 + x1)/2, (y0 + y1)/2
        ca, cb = (mx - d*ux, my - d*uy), (mx + d*ux, my + d*uy)
        va, vb = (mx + d*nx, my + d*ny), (mx - d*nx, my - d*ny)
        pad = [Point(v).buffer(w/2, 16) for v in (va, vb)]
        sup.extend([g.engordar([b, cb, va], w), g.engordar([vb, ca, a], w)] + pad)
        inf.extend([g.engordar([b, cb, vb], w), g.engordar([va, ca, a], w)] + pad)
        vias.extend([va, vb])

    def rama(desde, hacia, cruzada=False):
        """De un nodo de 50 Ω hacia el nodo padre: λ/4 de 70,7 Ω y el resto a 100 Ω (con el cruce, si va)."""
        (x0, y0), (x1, y1) = desde, hacia
        largo = math.hypot(x1 - x0, y1 - y0)
        if largo < l70 + w100:
            avisos.append(tr('Las ramas de la red son más cortas que el λ/4 de 70,7 Ω: sube la separación.'))
        k = min(l70/largo, 1.0)
        medio = (x0 + k*(x1 - x0), y0 + k*(y1 - y0))
        tira(desde, medio, w70)
        (cruce if cruzada else tira)(medio, hacia, w100)

    def bloque(cx, cy):
        """2×2 centrado en (cx, cy): dipolos → 100 Ω en vertical; uniones en (cx ± dx/2, cy). Simétrico:
        el brazo de arriba de cada columna mira hacia fuera del bloque y la rama izquierda va cruzada."""
        for sx in (-1, 1):
            xc = cx + sx*dx/2
            o = sx if simetrico else 1                  # hacia dónde va el brazo de la cara superior
            for sy in (-1, 1):
                yc = cy + sy*dy/2
                arriba, abajo = brazos(xc, yc, o)
                sup.append(arriba)
                inf.append(abajo)
                tira((xc, cy), (xc, yc), w100)
            rama((xc, cy), (cx, cy), cruzada=simetrico and sx < 0)

    camino = {'100': dy/2 + dx/2 - l70, '70': l70}         # raíz -> dipolo (2×2)
    if n == 1:
        # un solo elemento sobre el reflector: el coaxial llega directo al centro (vivo al brazo de arriba,
        # malla al de abajo), sin red; la impedancia de un dipolo/bowtie sobre reflector se afina con la
        # separación del reflector
        arriba, abajo = brazos(0.0, 0.0, 1)
        sup.append(arriba)
        inf.append(abajo)
        camino = {'100': 0.0, '70': 0.0}
    elif n == 2:
        bloque(0.0, 0.0)
    else:
        for bx in (-dx, dx):
            for by in (-dy, dy):
                bloque(bx, by)
                rama((bx, by), (bx, 0.0))
            rama((bx, 0.0), (0.0, 0.0))
        camino['100'] += 2*(dx - l70)
        camino['70'] += 2*l70
    # Pads del coaxial en el centro: vivo arriba (pequeño, poca capacidad con la malla) y malla abajo
    pad_v = max(PAD_VIVO, p['taladro_coaxial'] + 1.8)        # deja ≥ 0,6 mm de anillo tras el taladro
    sup.append(g.rectangulo(-pad_v/2, -pad_v/2, pad_v/2, pad_v/2))
    inf.append(g.rectangulo(-PAD_MALLA/2, -PAD_MALLA/2, PAD_MALLA/2, PAD_MALLA/2))
    cobre_sup, cobre_inf = unary_union(sup), unary_union(inf)
    minx, miny, maxx, maxy = unary_union([cobre_sup, cobre_inf]).bounds
    m = p['margen_placa']
    contorno = g.rectangulo(minx - m, miny - m, maxx + m, maxy + m)
    x0, y0, x1, y1 = contorno.bounds
    e = TALADRO_TORNILLO/2 + 3.0
    tornillos = [(x0 + e, y0 + e), (x1 - e, y0 + e), (x0 + e, y1 - e), (x1 - e, y1 - e)]
    sep = p['separacion_reflector']*lam0
    mr = p['margen_reflector']*lam0
    reflector = g.rectangulo(x0 - mr, y0 - mr, x1 + mr, y1 + mr)
    rx0, ry0, rx1, ry1 = reflector.bounds
    # Pérdida de la red (PSL ≈ microstrip de Z/2 sobre h/2; conductor: el doble de tiras)
    from types import SimpleNamespace
    s2 = SimpleNamespace(er=s.er, h=h2, tand=s.tand)
    perdida = (perdida_linea_dB_mm(f_est, s2, w100, 50)*camino['100']
               + perdida_linea_dB_mm(f_est, s2, w70, 35.4)*camino['70'])
    d_elem = 7.5                                            # dipolo sobre reflector a ~λ/4
    d_ideal = d_elem + 10*math.log10(n*n) - (0.5 if n > 1 else 0.0)     # acoplo mutuo
    d_apertura = 10*math.log10(4*math.pi*(rx1 - rx0)*(ry1 - ry0)/lam0**2)
    d_est = min(d_ideal, d_apertura)
    if not 0.15 <= p['separacion_reflector'] <= 0.3:
        avisos.append(tr('Reflector a {0:.2f} λ0: lo habitual es 0,2–0,25 λ0 (más cerca baja la impedancia y la banda; más lejos el haz se deforma).', p["separacion_reflector"]))
    if n > 1 and p['separacion'] > 0.9:
        avisos.append(tr('Separación entre dipolos > 0,9 λ0: aparecen lóbulos de difracción.'))
    if n > 1 and elemento and 2*la*math.tan(math.radians(p.get('apertura', 70))/2) + 4 > dy:
        avisos.append(tr('Las bowtie casi se tocan en vertical: sube la separación o cierra la apertura.'))
    if n > 1 and 2*la + 4 > dx:
        avisos.append(tr('Los dipolos casi se tocan en la dirección de sus brazos: sube la separación.'))
    if max(rx1 - rx0, ry1 - ry0) > 400:
        avisos.append(tr('Reflector de más de 400 mm: mejor una chapa de aluminio que una PCB.'))
    return Antena(tipo='panel_dipolos', parametros=dict(p), capas={'F.Cu': cobre_sup, 'B.Cu': cobre_inf},
                  ajuste=ajuste.vacio(), radiador=cobre_sup, contorno=contorno, zona_libre=None,
                  puerto={'tipo': 'pasante', 'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 0.0),
                          'ancho_linea': w100, 'ancho_puerto': w100, 'taladro_mm': p['taladro_coaxial'],
                          'pad_vivo_mm': pad_v, 'pad_malla_mm': PAD_MALLA},
                  taladros=[(x, y, TALADRO_TORNILLO) for x, y in tornillos], vias=vias,
                  reflector={'contorno': reflector, 'separacion_mm': sep, 'hilos': [(0.0, 0.0)],
                             'taladros': [(x, y, TALADRO_TORNILLO) for x, y in tornillos]
                             + [(0.0, 0.0, TALADRO_SMA_PANEL)]},
                  info={'lineas_mm': {'100ohm': round(w100, 3), '70ohm': round(w70, 3)},
                        'largo_lambda4_mm': round(l70, 2), 'separacion_mm': round(dx, 2),
                        'largo_dipolo_mm': round(2*la, 2),
                        'separacion_reflector_mm': round(sep, 2),
                        'placa_mm': [round(x1 - x0, 2), round(y1 - y0, 2)],
                        'reflector_mm': [round(rx1 - rx0, 2), round(ry1 - ry0, 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'grosor_total_mm': round(sep + s.h, 1),
                        'perdida_red_estimada_dB': round(float(perdida), 2),
                        'directividad_ideal_dBi': round(d_est, 1),
                        'ganancia_estimada_dBi': round(float(d_est - perdida), 1),
                        'hueco_minimo_mm': HUECO_CRUCE if vias else None, 'pista_minima_mm': round(w100, 3),
                        'avisos': avisos, 'f_sin_cortar_MHz': None, 'ajuste': None})


# ------------------------------------------------------------------ arrays de parches
def perdida_linea_dB_mm(f, s, w, z0):
    """Pérdida aproximada de una microstrip: dieléctrico + conductor (cobre)."""
    ee = eps_eff_microstrip(s.er, s.h, w)
    lam0 = lambda0_mm(f)
    a_d = 27.3*s.er/(s.er - 1)*(ee - 1)/math.sqrt(ee)*s.tand/lam0
    rs = math.sqrt(math.pi*f*4e-7*math.pi/5.8e7)
    a_c = 8.686*rs/(z0*w*1e-3)*1e-3
    return a_d + a_c


def generar_array(p, s, parche_fn, f_parche, R_borde):
    """Array 2×2 o 4×4 de parches con red corporativa en el pasillo entre filas.

    Bloque 2×2: la fila de arriba se alimenta por su borde inferior y la de abajo va
    girada 180° y alimentada por su borde superior, así toda la red queda en el pasillo
    entre las dos filas. La rama de la fila girada lleva una U con λg/2 de más para
    volver a ponerla en fase. Impedancias: transformador λ/4 en cada parche a 100 Ω;
    100 Ω ∥ 100 Ω = 50 Ω en cada fila; 50 ∥ 50 = 25 Ω en la raíz del bloque y un λ/4 de
    35,4 Ω lo lleva a 50 Ω. El 4×4 junta cuatro bloques igual (50 ∥ 50 + λ/4 de 35,4 Ω).
    Salida por el borde izquierdo de la placa.
    """
    n = int(p['tamano'])
    if n not in (2, 4):
        raise ValueError(tr('El array admite 2×2 o 4×4'))
    lam0 = lambda0_mm(f_parche)
    dx = dy = p['separacion']*lam0
    w100, w50 = ancho_microstrip(100, s.er, s.h), ancho_microstrip(50, s.er, s.h)
    w35 = ancho_microstrip(50/math.sqrt(2), s.er, s.h)
    cuarto = lambda w: lam0/4/math.sqrt(eps_eff_microstrip(s.er, s.h, w))
    l35, lg50 = cuarto(w35), 4*cuarto(w50)
    baja = p['bajada']
    # Alimentación con inserción: la línea de 100 Ω entra hasta donde el parche presenta 100 Ω
    # (R(y) = R_borde·cos²(πy/L)). Evita transformadores de ~140 Ω, demasiado finos en FR4.
    L = p['largo']
    inset = L/math.pi*math.acos(math.sqrt(100/R_borde)) if R_borde > 100 else 0.0
    hueco_inset = max(w100/2, 0.5)
    parche0 = parche_fn()
    eje = LineString([(0, -L), (0, 0)]).intersection(parche0)
    y_ent = eje.bounds[1] if not eje.is_empty else parche0.bounds[1]   # borde inferior en el eje
    avisos_inset = []
    while True:
        muesca = g.rectangulo(-w100/2 - hueco_inset, y_ent - 1, w100/2 + hueco_inset, y_ent + inset)
        recortado = parche0.difference(muesca)
        if len(g.poligonos(recortado)) == 1 or inset == 0.0:
            break
        # Minkowski de iteración alta: el centro del parche es un cuello estrecho y la muesca lo
        # partiría en dos mitades sueltas. Se acorta la inserción hasta que el parche siga entero.
        inset = round(0.8*inset, 3) if inset > 0.5 else 0.0
        avisos_inset = [tr('Inserción acortada para no partir el parche (cuello central estrecho): la '
                        'adaptación saldrá peor; usa menos iteración o profundidad de Minkowski.')]
    parche0 = recortado
    y_borde = parche0.bounds[1]                    # lo más bajo del parche (la red va por debajo)
    y_ent = y_ent + inset                          # punto de alimentación dentro del parche
    girado = affinity.rotate(parche0, 180, origin=(0, 0))
    lt = 0.0
    piezas = []
    camino = {'100': 0.0, '50': 0.0, '35': 0.0}    # un camino raíz -> parche (fila sin U)
    avisos = []

    def bloque(cx, cy, salida):
        """Bloque 2×2 centrado en (cx, cy); devuelve el extremo de su salida de 50 Ω."""
        y_u = cy + dy/2 + y_borde - baja           # nodo de la fila de arriba (bajo sus parches)
        y_l = cy - dy/2 - y_borde + baja           # nodo de la fila girada (sobre sus parches)
        for sx in (-1, 1):
            x = cx + sx*dx/2
            yb = cy + dy/2 + y_ent                 # punto de inserción (fila de arriba)
            piezas.append(g.mover(parche0, x, cy + dy/2))
            piezas.append(g.rectangulo(x - w100/2, y_u, x + w100/2, yb + 0.05))
            yt = cy - dy/2 - y_ent                 # punto de inserción (fila girada)
            piezas.append(g.mover(girado, x, cy - dy/2))
            piezas.append(g.rectangulo(x - w100/2, yt - 0.05, x + w100/2, y_l))
        piezas.append(g.engordar([(cx - dx/2, y_u), (cx + dx/2, y_u)], w100))
        piezas.append(g.engordar([(cx - dx/2, y_l), (cx + dx/2, y_l)], w100))
        pasillo = y_u - y_l
        y_r = (y_u + y_l)/2
        # U de λg/2 en la rama de la fila girada, hacia el lado contrario a la salida
        a = lg50/4
        y1 = y_l + w100/2 + w50
        y2 = y1 + 2*w50
        if y2 + w50 > y_r - w50/2:
            avisos.append(tr('Pasillo entre filas de {0:.1f} mm: muy justo para la U de fase; sube la separación entre parches.', pasillo))
        piezas.append(g.engordar([(cx, y_l), (cx, y1), (cx - salida*a, y1), (cx - salida*a, y2),
                                  (cx, y2), (cx, y_r)], w50))
        piezas.append(g.engordar([(cx, y_u), (cx, y_r)], w50))
        # raíz del bloque: 25 Ω -> λ/4 de 35,4 Ω -> 50 Ω hacia la salida
        x_out = cx + salida*l35
        piezas.append(g.engordar([(cx, y_r), (x_out, y_r)], w35))
        return (x_out, y_r), pasillo

    if n == 2:
        salida, pasillo = bloque(0.0, 0.0, -1)
        camino['100'] += dx/2 + baja + inset
        camino['50'] += pasillo/2
        camino['35'] += l35
        raiz = salida
    else:
        filas_out = []
        for cy in (-dy, dy):
            izq, pasillo = bloque(-dx, cy, +1)
            der, _ = bloque(dx, cy, -1)
            piezas.append(g.engordar([izq, der], w50))           # se unen en x=0
            filas_out.append((0.0, cy))
        # cada unión de fila (25 Ω) -> λ/4 de 35,4 Ω hacia el centro -> 50 Ω hasta la raíz (0,0)
        for (x0, cy) in filas_out:
            sentido = 1 if cy < 0 else -1
            yq = cy + sentido*l35
            piezas.append(g.engordar([(0.0, cy), (0.0, yq)], w35))
            piezas.append(g.engordar([(0.0, yq), (0.0, 0.0)], w50))
        x_out = -l35
        piezas.append(g.engordar([(0.0, 0.0), (x_out, 0.0)], w35))
        raiz = (x_out, 0.0)
        camino['100'] += dx/2 + baja + inset
        camino['50'] += pasillo/2 + (dx - l35) + (dy - l35)
        camino['35'] += 3*l35
    todo = unary_union(piezas)
    minx, miny, maxx, maxy = todo.bounds
    margen = 6*s.h if int(p.get('masa', 0)) == 1 else max(6*s.h, p['margen_masa'])
    con_pi = ajuste.activo(p) and int(p.get('red_pi', 0)) == 1
    l_alim = max(p['largo_alimentacion'], 14.0) if con_pi else p['largo_alimentacion']
    x_borde = minx - l_alim
    piezas.append(g.rectangulo(x_borde + BORDE_COBRE, raiz[1] - w50/2, raiz[0] + 0.01, raiz[1] + w50/2))
    camino['50'] += raiz[0] - x_borde
    cobre = unary_union(piezas)
    aj = ajuste.vacio()
    if con_pi:
        # red en π en la línea de salida (horizontal), con las derivaciones por debajo
        aj = ajuste.red_pi(x_borde + 8.6, raiz[1], w50, p, vertical=False, lado=-1)
        cobre = unary_union([cobre.difference(unary_union(aj['cortes']))] + aj['islas_masa'])
    contorno = g.contorno_placa([cobre.buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(x_borde, -1e4, 1e4, 1e4))
    masa = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    desp = (-x_borde, -contorno.bounds[1])
    mv = lambda geo: g.mover(geo, *desp)
    perdida = (perdida_linea_dB_mm(f_parche, s, w100, 100)*camino['100']
               + perdida_linea_dB_mm(f_parche, s, w50, 50)*camino['50']
               + perdida_linea_dB_mm(f_parche, s, w35, 35.4)*camino['35'])
    elementos = n*n
    d_elem = 6.5 if s.er > 4 else 7.5
    aj = ajuste.mover(aj, *desp)
    return Antena(tipo='array_parches', parametros=dict(p), capas={'F.Cu': mv(cobre), 'B.Cu': mv(masa)}, ajuste=aj,
                  radiador=mv(todo), contorno=mv(contorno), zona_libre=None,
                  puerto={'borde': (0.0, raiz[1] + desp[1]), 'direccion': (1, 0),
                          'alimentacion': (raiz[0] + desp[0], raiz[1] + desp[1]), 'ancho_linea': w50},
                  info={'ancho_linea_50ohm_mm': round(w50, 3), 'separacion_mm': round(dx, 2),
                        'lineas_mm': {'50ohm': round(w50, 3), '35ohm': round(w35, 3), '100ohm': round(w100, 3)},
                        'insercion_mm': round(inset, 2), 'R_borde_estimada_ohm': round(R_borde, 1),
                        'hueco_minimo_mm': round(hueco_inset, 3), 'pista_minima_mm': round(w100, 3),
                        'perdida_red_estimada_dB': round(float(perdida), 2),
                        'directividad_ideal_dBi': round(d_elem + 10*math.log10(elementos), 1),
                        'ganancia_estimada_dBi': round(float(d_elem + 10*math.log10(elementos) - perdida), 1),
                        'avisos': avisos + avisos_inset,
                        'placa_mm': [round(contorno.bounds[2] - contorno.bounds[0], 2),
                                     round(contorno.bounds[3] - contorno.bounds[1], 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'radiador_mm': [round(maxx - minx, 2), round(maxy - miny, 2)],
                        'ajuste': aj['notas'] or None})

