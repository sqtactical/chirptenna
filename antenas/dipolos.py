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

import numpy as np
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
    if forma == 3:
        # curva de punta de flecha de Sierpinski en cada brazo: longitud equivalente como la del monopolo de flecha
        total = 2*p['largo_brazo']*(1 + 0.35*(1.5**int(p.get('iteracion_s', 3)) - 1)) + (p['hueco'] if int(p['alimentacion']) == 1 else 0)
    elif forma:
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
    forma = int(p.get('forma', 0))        # 0 = recto o Koch, 1 = bowtie, 2 = bowtie de Sierpinski, 3 = flecha de Sierpinski
    wf = p.get('ancho_flecha', 0.5)

    def brazo(lado, y_d, desp):
        """Un brazo (lado = +1 derecho, −1 izquierdo), con el vértice de la bowtie o el inicio de la pista en
        (lado·desp, y_d). Devuelve (polilínea o None, polígono)."""
        if forma == 0:
            pol = brazo_koch(n, la, ang, lado < 0, y_d) + [lado*desp, 0]
            return pol, g.engordar(pol, w)
        if forma == 3:
            # una sola pista: base a lo largo del brazo (del centro hacia fuera) y el triángulo hacia +y, simétrico en x
            pts = g.flecha_sierpinski(int(p.get('iteracion_s', 3)), la)
            pol = np.column_stack([lado*(pts[:, 1] + desp), y_d + pts[:, 0]])
            return pol, g.engordar(pol, wf)
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
            y_d = max(y_d, la*math.tan(math.radians(p.get('apertura', 70))/2) if forma != 3 else 0.0)
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
        if forma in (1, 2):
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
                                              'hueco_minimo_mm': (min(hueco or 99, la/2**int(p.get('iteracion_s', 3))*math.sin(math.radians(60)) - wf)
                                                                  if forma == 3 else hueco),
                                              'pista_minima_mm': min(w, wf) if forma == 3 else w, 'avisos': avisos,
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
K_BOWTIE_COLINEAL = 0.9   # bowtie de la colineal (triángulo de ~41° de apertura, más estrecho que el del dipolo): sin calibrar; `--centrar` lo afina
K_SIERPINSKI_COLINEAL = 0.85   # Sierpinski (iteración 2): los huecos alargan el brazo; 0,9·0,75/0,79 como en el dipolo, sin calibrar


K_ALTERNADA = 0.85      # alternada: f = K·c/(4·L·√εr) (simulado el 16-11: FR4 con L 10,5–18,8 mm y PTFE con 16,7–21 mm, ±5 %; sin ella la del dipolo bowtie daba 3895 MHz para un brazo que resuena a 2432)


def f_alternada(largo_brazo, er):
    """Frecuencia de resonancia estimada del array alternado (bowtie o Sierpinski) con brazos de `largo_brazo` mm."""
    return K_ALTERNADA*C0/(4*largo_brazo*1e-3*math.sqrt(er))


def estimar_f_colineal_dipolos(p, eps_impreso):
    """Cada dipolo mide 2 brazos de `largo_brazo`: resuena donde esos dos brazos son λ/2 (efectiva). Con la bowtie (`forma` = 1) el
    brazo ancho resuena más bajo que la pata fina: como en el dipolo bowtie, f = K·f_recto."""
    if int(p.get('conexion', 0) or 0) == 1:
        # alternada: cada dipolo es un bowtie transversal a la línea, como el del `dipolo_bowtie` (sin balun)
        return f_alternada(p['largo_brazo'], 2*eps_impreso - 1)                # (eps_impreso = (εr + 1)/2)
    f = C0/(2*2*p['largo_brazo']*1e-3*math.sqrt(eps_impreso))
    forma = int(p.get('forma', 0) or 0)
    if forma == 3:                                                              # U de Koch: pata de cuerda La y largo equivalente _eq_koch (sin calibrar)
        return f*p['largo_brazo']/_eq_koch(p['largo_brazo'], p.get('iteracion', 1))
    return f*(K_BOWTIE_COLINEAL if forma == 1 else K_SIERPINSKI_COLINEAL if forma == 2 else 1.0)


def _brazo_colineal(p, yk, sentido):
    """Cobre de un brazo del dipolo colineal centrado en y = yk (sentido +1 hacia arriba, −1 hacia abajo): una «U» (barra y dos patas,
    `forma` = 0), un triángulo bowtie (`forma` = 1) o un triángulo de Sierpinski (`forma` = 2, con `iteracion_s` y `cuello_s`); los dos
    últimos ocupan el mismo ancho que la U y van de la punta (`ancho_brazo`) en la línea al extremo."""
    La, wa, xs = p['largo_brazo'], p['ancho_brazo'], p['separacion_patas']
    forma = int(p.get('forma', 0) or 0)
    if forma == 2:
        w = xs + wa/2
        tri = g.sierpinski(int(p.get('iteracion_s', 2)), 2*w, La, p.get('cuello_s', 1.0))        # vértice en el origen, base arriba
        tri = affinity.scale(tri, xfact=1, yfact=sentido, origin=(0, 0))
        return [affinity.translate(tri, 0, yk), g.rectangulo(-wa/2, min(yk, yk + sentido*wa), wa/2, max(yk, yk + sentido*wa))]
    if forma == 1:
        w = xs + wa/2
        return [Polygon([(-wa/2, yk), (wa/2, yk), (w, yk + sentido*La), (-w, yk + sentido*La)])]
    piezas = [g.rectangulo(-xs - wa/2, yk - wa/2, xs + wa/2, yk + wa/2)]          # barra en el eje
    if forma == 3:
        # U de Koch: cada pata es una curva de Koch de cuerda `largo_brazo` con las muescas hacia fuera (hacia dentro tocarían la línea)
        for x in (-xs, xs):
            pts = g.koch(int(p.get('iteracion', 1)), (0, 0), (0, sentido*La), 60.0)
            if pts[:, 0].mean()*x < 0:                                          # que las muescas apunten hacia fuera en las dos patas
                pts = pts*[-1, 1]
            piezas.append(g.engordar(pts + [x, yk], wa))
        return piezas
    for x in (-xs, xs):
        piezas.append(g.rectangulo(x - wa/2, min(yk, yk + sentido*La), x + wa/2, max(yk, yk + sentido*La)))
    return piezas


def _factor_inclinacion(p, s, w50):
    """Factor que alarga (o acorta) el tramo de línea entre dipolos para inclinar el haz `inclinacion` grados respecto a la perpendicular a la
    colineal (array alimentado en serie con inclinación fija). Con N elementos separados d y una línea de índice √εeff (sin las barras de los
    brazos), el máximo está donde k0·d·cos ψ = k·d·√εeff − 2π·m (serie, m = 1) o − π (alternada): con la separación d = λ0/(√εeff − sen τ)
    (λ0/2 en la alternada) el haz queda τ grados hacia el extremo lejano (τ > 0) o hacia el conector (τ < 0). Sin calibrar: la línea real
    no es una microstrip ideal y los dipolos se acoplan."""
    tau = float(p.get('inclinacion', 0) or 0)
    if not tau:
        return 1.0
    ee = math.sqrt(eps_eff_microstrip(s.er, s.h, w50))
    return ee/(ee - math.sin(math.radians(tau)))


def _hueco_colineal(p, w50, wb, Ls):
    """Hueco más pequeño del cobre (para la malla): patas–línea en la «U»; en la bowtie no hay patas, y queda el de un brazo al siguiente;
    en el Sierpinski, el del hueco triangular más pequeño (anchura = 4·área/perímetro)."""
    forma = int(p.get('forma', 0) or 0)
    if forma == 1:
        return round(max(Ls - p['largo_brazo'] - p['ancho_brazo'], 1.0), 2)
    if forma == 2:
        huecos = [h for pol in g.poligonos(unary_union(_brazo_colineal(p, 0.0, 1))) for h in pol.interiors]
        entre_brazos = max(Ls - p['largo_brazo'] - p['ancho_brazo'], 1.0)
        return round(min([4*Polygon(h).area/h.length for h in huecos] + [entre_brazos]), 2)
    h = p['separacion_patas'] - p['ancho_brazo']/2 - wb/2
    if forma == 3:                                                              # las muescas de Koch cierran el hueco más que la pata recta
        h = min(h, p['ancho_brazo'])
    return round(h, 2)


def _pista_colineal(p, w50):
    """Pista más fina del cobre: la línea, el ancho del brazo o, en el Sierpinski, el cuello entre triángulos."""
    m = min(w50, p['ancho_brazo'])
    return round(min(m, p.get('cuello_s', 1.0)) if int(p.get('forma', 0) or 0) == 2 else m, 3)


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
    Ls = p['factor_linea']*C0/f_est*1e3/math.sqrt(eps_eff_microstrip(s.er, s.h, w50))*_factor_inclinacion(p, s, w50)
    if int(p.get('conexion', 0) or 0) == 1:
        return _colineal_alternada(p, s, w50, wb, avisos)
    if Ls < 2*La + 2.0:
        avisos.append(tr('Los dipolos se tocan: el tramo de línea es más corto que los dos brazos. Alarga el tramo o acorta los brazos.'))
    if int(p.get('forma', 0) or 0) == 3:
        seg = La/3**int(p.get('iteracion', 1))
        if seg < wa + 0.6:
            avisos.append(tr('Las muescas de Koch ({0:.1f} mm) son casi tan finas como la pata ({1:.1f} mm) y se funden (DRC de distancia y bloque macizo): baja la iteración o estrecha las patas.', seg, wa))
    if int(p.get('modular', 0) or 0) == 1:
        return _colineal_modular(p, s, w50, wb, Ls, avisos)
    y_prim = BORDE_COBRE + p['largo_entrada'] + La
    ys = [y_prim + k*Ls for k in range(n)]
    F, B = [], []
    for k, yk in enumerate(ys):
        for cara, sentido in ((F, 1), (B, -1)):          # U (o bowtie) arriba (vivo) y su espejo abajo (malla)
            cara.extend(_brazo_colineal(p, yk, sentido))
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
    return Antena(tipo='colineal_dipolos', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_prim), 'ancho_linea': w50},
                  info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(y1_, 2)],
                                              'hueco_minimo_mm': _hueco_colineal(p, w50, wb, Ls),
                                              'pista_minima_mm': _pista_colineal(p, w50),
                                              'longitud_linea_mm': round(Ls, 1), 'avisos': avisos,
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


def _brazo_transversal(p, yk, lado):
    """Brazo de un dipolo bowtie (o de Sierpinski) a un lado de la línea (lado = +1 derecho, −1 izquierdo): el vértice en el eje, a la altura yk, y
    el triángulo abriéndose hacia el lado, como en `generar_dipolo` (`largo_brazo` de largo y `apertura` de ángulo total)."""
    forma = max(int(p.get('forma', 0) or 0), 1)
    a = g.brazo_bowtie(p['largo_brazo'], p.get('apertura', 50), p['ancho_brazo'],
                       int(p.get('iteracion_s', 2)) if forma == 2 else 0, p.get('cuello_s', 1.0))
    return affinity.translate(affinity.scale(a, xfact=lado, yfact=1, origin=(0, 0)), 0, yk)


def _colineal_alternada(p, s, w50, wb, avisos):
    """Array de dipolos bowtie con la polaridad alternada, alimentado por una sola línea microstrip (vivo en F.Cu, masa en B.Cu, tiras continuas).
    Cada dipolo es el del `dipolo_bowtie` antipodal: sus dos brazos salen a los lados de la línea (perpendiculares a ella), uno en cada cara. Los
    dipolos están separados Ls2 = λg/2 y cada uno lleva los brazos al revés que el anterior (el derecho en F.Cu y el izquierdo en B.Cu, y en el
    siguiente el derecho en B.Cu y el izquierdo en F.Cu): la inversión de polaridad compensa el retardo de media longitud de onda y todos radian en
    fase, sin vías. Es un array de dipolos en paralelo (haz perpendicular a la placa, polarización a lo largo de los brazos), no una colineal omni.
    La primera versión (brazos a lo largo de la línea) quedaba como una estrella: los brazos de dipolos vecinos se solapaban."""
    from . import tipos                    # (import local: `tipos` importa este módulo)
    La, n = p['largo_brazo'], int(p['elementos'])
    # media longitud de onda de la microstrip a la frecuencia que da el tamaño de los brazos (la estimación calibrada, no la fórmula cruda)
    Ls2 = p['factor_linea']*C0/tipos.estimar_f('colineal_dipolos', p, s.nombre)*1e3/math.sqrt(eps_eff_microstrip(s.er, s.h, w50))/2*_factor_inclinacion(p, s, w50)
    if int(p.get('forma', 0) or 0) == 0:
        avisos.append(tr('La conexión alternada usa brazos en triángulo (bowtie): la forma «U» no se puede alternar.'))
    if int(p.get('modular', 0) or 0) == 1:
        avisos.append(tr('La conexión alternada se hace de momento en una sola placa: sin módulos.'))
    medio = La*math.tan(math.radians(p.get('apertura', 50))/2)          # semialtura de la base de un brazo, a lo largo de la línea
    if 2*medio > Ls2 - 1.0:
        avisos.append(tr('Los brazos de dos dipolos vecinos se tocan o casi (altura {0:.1f} mm para {1:.1f} mm entre dipolos): reduce la apertura.', 2*medio, Ls2))
    y0 = BORDE_COBRE + p['largo_entrada'] + medio
    ys = [y0 + k*Ls2 for k in range(n)]
    F, B = [], []
    for k, yk in enumerate(ys):
        der, izq = (F, B) if k % 2 == 0 else (B, F)                      # cada dipolo, con los brazos cambiados de cara
        der.append(_brazo_transversal(p, yk, 1))
        izq.append(_brazo_transversal(p, yk, -1))
    y_fin = ys[-1] + p['ancho_brazo']/2
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
    huecos = [4*Polygon(h).area/h.length for pol in g.poligonos(unary_union(_brazo_transversal(p, 0.0, 1))) for h in pol.interiors]
    huecos.append(max(Ls2 - 2*medio, 0.5))                              # entre las bases de los brazos de dipolos vecinos (de caras distintas)
    return Antena(tipo='colineal_dipolos', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y0), 'ancho_linea': w50},
                  info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(y1_, 2)],
                                              'hueco_minimo_mm': round(min(huecos), 2),
                                              'pista_minima_mm': round(min(w50, p['ancho_brazo'], p.get('cuello_s', 1.0) if int(p.get('forma', 0) or 0) == 2 else 99), 3),
                                              'longitud_linea_mm': round(Ls2, 1), 'avisos': avisos,
                                              'f_sin_cortar_MHz': None, 'ajuste': None}))


VENTANA_UNION = 3.0      # colineal modular: largo de la apertura de máscara a cada lado de una unión [mm]
ENCAJE_ANCHO = 3.0       # ... ancho de cada lengüeta (la ranura es 0,3 mm más ancha por la tolerancia del fresado) [mm]
ENCAJE_LARGO = 3.0       # ... lo que sobresale la lengüeta del canto [mm]
ENCAJE_HOLGURA = 0.15    # ... holgura de la ranura a cada lado [mm]
COLA_CUELLO, COLA_PUNTA = 2.0, 3.6     # cola de milano: ancho de la lengüeta en el canto y en la punta [mm]


def _lengueta(encaje, xc, y0, sentido=1):
    """Lengüeta (rectangular o de cola de milano) centrada en x = xc que sale del canto y = y0 hacia `sentido`."""
    if encaje == 2:
        pts = [(xc - COLA_CUELLO/2, y0), (xc + COLA_CUELLO/2, y0),
               (xc + COLA_PUNTA/2, y0 + sentido*ENCAJE_LARGO), (xc - COLA_PUNTA/2, y0 + sentido*ENCAJE_LARGO)]
        return Polygon(pts)
    return g.rectangulo(xc - ENCAJE_ANCHO/2, min(y0, y0 + sentido*ENCAJE_LARGO), xc + ENCAJE_ANCHO/2, max(y0, y0 + sentido*ENCAJE_LARGO))


def _cobre_colineal_modular(p, w50, wb, ys, y_ini, y_fin):
    """Cobre de una colineal modular: dipolos centrados en `ys` y la línea (F.Cu) con su tira de masa (B.Cu) de y_ini a y_fin."""
    La, wa, xs = p['largo_brazo'], p['ancho_brazo'], p['separacion_patas']
    F, B = [g.rectangulo(-w50/2, y_ini, w50/2, y_fin)], [g.rectangulo(-wb/2, y_ini, wb/2, y_fin)]
    for yk in ys:
        for cara, sentido in ((F, 1), (B, -1)):
            cara.extend(_brazo_colineal(p, yk, sentido))
    return unary_union(F), unary_union(B)


def _colineal_modular(p, s, w50, wb, Lm, avisos):
    """Colineal de `elementos` dipolos sobre placas unidas por el canto. Cada módulo mide Lm (un tramo de λg) de largo y lleva
    su dipolo cerca del borde de abajo (a `y_d`) y la línea de 50 Ω de borde a borde con su tira de masa debajo: al juntarlos,
    los dipolos quedan separados Lm y en fase. Hay tres placas: la de **inicio** (con el conector), el **módulo** (igual en todos
    los intermedios) y el **final**, una tapa corta donde la línea acaba en la barra del último dipolo (un tramo abierto más
    largo cargaría y perdería). `modulos` = [inicio, módulo × (N−2), final]; la antena que se devuelve es la cadena entera
    (lo que se simula). El cobre llega a 0,5 mm del canto (mínimo de KiCad): la unión son ~1 mm que se rellenan con estaño
    sobre las aperturas de máscara (`mascara_abierta`)."""
    n = int(p['elementos'])
    La, wa, xs = p['largo_brazo'], p['ancho_brazo'], p['separacion_patas']
    margen = p.get('margen_borde', 2.0)
    ancho = max(2*(xs + wa/2 + margen), conector.ANCHO_MINIMO[conector.tipo(p)])
    encaje = int(p.get('encaje', 1) or 0)
    # el brazo de abajo (B.Cu) queda a 3 mm del canto de la unión (4,2 con encaje: la ranura entra 3,3 mm y el cobre va a ≥ 0,5 mm del borde)
    y_d = La + (4.2 if encaje else 3.0)
    x_enc = wb/2 + 1.0 + (COLA_PUNTA if encaje == 2 else ENCAJE_ANCHO)/2     # eje de las lengüetas: a 1 mm de la tira de masa
    if Lm < y_d + La + 2.0:
        avisos.append(tr('El módulo es más corto que el dipolo más la entrada: el dipolo de un módulo tocaría el de su vecino. Acorta los brazos o alarga el tramo.'))
    if n > 4:
        avisos.append(tr('Más de 4 módulos en FR4: la línea de λg pierde tanto que la ganancia ya no sube (6 módulos: 4,0 dBi, η 48 %; 4 módulos: 4,1 dBi, η 59 %). Usa RO4350B o PTFE, o menos módulos.'))

    def antena(largo, ys, y_fin_linea, inicio, abiertas, arriba=False, abajo=False):
        contorno = g.rectangulo(-ancho/2, 0.0, ancho/2, largo)
        if encaje and arriba:                    # lengüetas que entran en las ranuras del módulo siguiente
            contorno = unary_union([contorno] + [_lengueta(encaje, sg*x_enc, largo - 0.01) for sg in (-1, 1)])
        if encaje and abajo:                     # ranuras para las lengüetas del módulo anterior (con holgura y pasando del canto)
            contorno = contorno.difference(unary_union(
                [_lengueta(encaje, sg*x_enc, 0.0, -1).union(_lengueta(encaje, sg*x_enc, 0.0, 1)).buffer(ENCAJE_HOLGURA, join_style='mitre')
                 for sg in (-1, 1)]))
        sup, inf = _cobre_colineal_modular(p, w50, wb, ys, BORDE_COBRE, y_fin_linea)
        interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
        sup, inf = sup.intersection(interior), inf.intersection(interior)
        x0, _, x1, y1_ = unary_union([sup, inf]).bounds
        puerto = {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, ys[0]), 'ancho_linea': w50}
        if not inicio:
            puerto['conector'] = conector.SIN
        a = Antena(tipo='colineal_dipolos', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                   radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=puerto,
                   info=_info_placa(contorno, {'radiador_mm': [round(x1 - x0, 2), round(y1_, 2)],
                                               'hueco_minimo_mm': _hueco_colineal(p, w50, wb, Lm),
                                               'pista_minima_mm': _pista_colineal(p, w50),
                                               'longitud_linea_mm': round(Lm, 1), 'avisos': list(avisos),
                                               'f_sin_cortar_MHz': None, 'ajuste': None}))
        for y0 in abiertas:                 # y0 = el canto de la unión (0 o el largo); la apertura entra VENTANA_UNION en la placa
            sgn = 1 if y0 == 0 else -1
            for capa, a_cobre in (('F', w50), ('B', wb)):
                ya, yb = sorted((y0, y0 + sgn*VENTANA_UNION))
                a.mascara_abierta.append((capa, g.rectangulo(-a_cobre/2 - 0.25, ya, a_cobre/2 + 0.25, yb)))
        return a

    ys_cadena = [y_d + k*Lm for k in range(n)]
    largo_fin = y_d + La + margen                # tapa: hasta el extremo de la pata de arriba más el margen
    cadena = antena(ys_cadena[-1] + La + margen, ys_cadena, ys_cadena[-1] + wa/2, True, [])
    cadena.info.update({'modulos': n, 'largo_modulo_mm': round(Lm, 2), 'largo_final_mm': round(largo_fin, 1),
                        'largo_total_mm': round(ys_cadena[-1] + La + margen, 1)})
    cadena.modulos = [{'nombre': 'inicio', 'cantidad': 1,
                       'antena': antena(Lm, [y_d], Lm - BORDE_COBRE, True, [Lm], arriba=True)}]
    if n > 2:
        cadena.modulos.append({'nombre': 'modulo', 'cantidad': n - 2,
                               'antena': antena(Lm, [y_d], Lm - BORDE_COBRE, False, [0.0, Lm], arriba=True, abajo=True)})
    cadena.modulos.append({'nombre': 'final', 'cantidad': 1,
                           'antena': antena(largo_fin, [y_d], y_d + wa/2, False, [0.0], abajo=True)})
    return cadena


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
