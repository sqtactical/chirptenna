"""Antena de bucle impresa (pequeña) con condensador de sintonía y red en π.

Un anillo cuadrado o redondo de cobre alimentado por una línea microstrip: la línea llega a un extremo del anillo y el otro extremo
vuelve a masa por una vía. Un condensador en serie en el lado opuesto lo sintoniza (L del anillo con C → resonancia). Un bucle pequeño
(perímetro < ~λ/3) radia con una resistencia de entrada de 0,1–5 Ω: sin red de adaptación la S11 sale casi 0 dB. Por eso lleva la
red en π en la línea de 50 Ω (los mismos Z1, Z2 y Z3 que los monopolos) y el asistente calcula sus componentes.

Modelo de la simulación: el condensador es un elemento concentrado de openEMS (`Antena.ajuste['condensadores']`) con una resistencia
serie por su Q; la red en π no se simula (Z1 = 0 Ω de fábrica). Coordenadas: x transversal, y hacia el anillo; el conector en y = 0.
"""
import math

from shapely.geometry import Point
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste
from .materiales import ancho_microstrip
from .modelo import Antena
from .i18n import tr

MU0 = 4e-7*math.pi
C_PARASITA_PF_MM = 0.016        # capacidad parásita (hueco, pads, masa) por mm de lado: 0,38 pF con 25 mm y 0,14 pF con 9 mm (simulado)
SEP_ANILLO = 1.5               # distancia del borde de la masa al lado inferior del anillo [mm]
HUECO_ALIM = 0.6               # hueco entre el punto de la línea y el extremo que va a masa [mm]
C_MINIMA_MONTADO_PF = 0.1       # por debajo no hay condensador: basta la capacidad del hueco
MASA_MINIMA_PI = 14.0          # la red en π necesita sitio entre el conector y el anillo [mm]


def inductancia_nH(p):
    """Inductancia del anillo (fórmulas de Grover para un hilo de radio w/4 equivalente a una tira de ancho w)."""
    w = p['ancho_pista']*1e-3
    r = w/4
    a = max(p['lado'] - p['ancho_pista'], 0.5)*1e-3            # lado de la línea media
    if int(p.get('forma', 0)) == 1:
        R = a/2
        L = MU0*R*(math.log(8*R/r) - 2)
    else:
        L = 2*MU0*a/math.pi*(math.log(a/r) - 0.774)
    return L*1e9


# f simulada / f de la fórmula (GPU, FR4 de 1,6 mm, resonancia serie con la línea de 50 Ω quitada). Cinco simulaciones: lado 25,4 mm con 0,47 y
# 0,34 pF (758 y 824 MHz), lado 9 mm con 0,07 pF (2406 MHz) y sin condensador (2937 MHz) y lado 11,5 mm sin condensador (2367 MHz). La fórmula
# sale 4 % baja a 868 MHz y dentro de ±5 % a 2,4 GHz. Interpolado en log f.
CALIBRACION = ((780e6, 1.04), (2400e6, 1.0))


def _factor(f):
    (f0, k0), (f1, k1) = CALIBRACION
    if f <= f0:
        return k0
    if f >= f1:
        return k1
    t = (math.log(f) - math.log(f0))/(math.log(f1) - math.log(f0))
    return k0 + t*(k1 - k0)


def estimar_f(p):
    """Resonancia serie del anillo con su condensador: f = 1/(2π√(L·C)), con C = condensador + capacidad parásita.

    Ojo al medirla en una simulación: la impedancia en el conector incluye la línea de 50 Ω hasta el anillo (~λ/4 a 2,4 GHz), que
    invierte la impedancia y hace pasar por cero la reactancia en otra frecuencia. Hay que quitar la línea antes (ver `puerto['largo_linea_mm']`).
    """
    L = inductancia_nH(p)*1e-9
    C = (p['capacidad_pF'] + C_PARASITA_PF_MM*p['lado'])*1e-12
    f = 1/(2*math.pi*math.sqrt(L*C))
    return f*_factor(f)


def resistencia_radiacion(p, f):
    """R de radiación de un bucle pequeño, 20π²(C/λ)⁴ Ω (válida para perímetros < ~λ/3)."""
    lam = 299792458.0/f*1e3
    per = 4*p['lado'] if int(p.get('forma', 0)) == 0 else math.pi*p['lado']
    return 20*math.pi**2*(per/lam)**4


def generar(p, s, tipo='bucle'):
    w, a = p['ancho_pista'], p['lado']
    redonda = int(p.get('forma', 0)) == 1
    w50 = ancho_microstrip(50, s.er, s.h)
    huella = '0402' if int(p.get('componentes', 0)) == 1 else '0603'
    largo, ancho_c, paso = ajuste.HUELLAS[huella]
    hc = paso - largo + 0.1                                          # hueco del condensador
    con_pi = ajuste.activo(p) and int(p.get('red_pi', 0)) == 1
    lg = max(p['largo_masa'], MASA_MINIMA_PI) if con_pi else p['largo_masa']
    yb = lg + SEP_ANILLO
    x_g0 = w50/2 + 0.2
    x_g1 = x_g0 + HUECO_ALIM
    xv = x_g1 + 0.9
    if a < 2*(xv + 1.0) or a < 2*w + 3*hc:
        raise ValueError(f'el lado del anillo ({a} mm) es demasiado pequeño para la línea, el hueco de alimentación y la vía')
    # --- anillo con sus dos huecos
    if redonda:
        ext = Point(0, yb + a/2).buffer(a/2, 64)
        ring = ext.difference(Point(0, yb + a/2).buffer(a/2 - w, 64))
    else:
        ring = g.rectangulo(-a/2, yb, a/2, yb + a).difference(g.rectangulo(-a/2 + w, yb + w, a/2 - w, yb + a - w))
    y_c = yb + a - w/2                                               # centro del lado superior (condensador)
    corte_c = g.rectangulo(-hc/2, y_c - w/2 - 0.2, hc/2, y_c + w/2 + 0.2)
    corte_a = g.rectangulo(x_g0, yb - 0.2, x_g1, yb + w + 0.2)
    ring = ring.difference(unary_union([corte_c, corte_a]))
    linea = g.rectangulo(-w50/2, 0.5, w50/2, yb + w)
    sup = unary_union([linea, ring])
    # --- masa y pad de la vía bajo el extremo que vuelve a masa
    W = max(p['ancho_placa'], a + 2*p.get('margen_borde', 2.0))
    masa = unary_union([g.rectangulo(-W/2, 0, W/2, lg), g.rectangulo(xv - 1.0, lg - 0.5, xv + 1.0, yb + w + 0.4)])
    # --- condensador (elemento concentrado en la simulación, componente en la placa) y red en π
    C_pF = p['capacidad_pF']
    montado = C_pF >= C_MINIMA_MONTADO_PF
    aj = ajuste.vacio()
    aj['componentes'].append(ajuste._componente('C1', huella, 0.0, y_c, 0, f'{C_pF:g} pF' if montado else 'sin montar', montado))
    aj['cortes'].append(corte_c)
    if montado:
        aj['condensadores'].append({'ref': 'C1', 'caja': (-hc/2, y_c - w/2, hc/2, y_c + w/2), 'dir': 'x', 'C_pF': C_pF,
                                    'Q': p.get('q_condensador', 250.0)})
        aj['notas'].append(tr('C1 = {0:g} pF (C0G/NP0, {1}): sintoniza el anillo. Su Q fija la eficiencia: usa un condensador de Q alta.', C_pF, huella))
    else:
        aj['notas'].append(tr('C1 sin montar: con un anillo así de pequeño basta la capacidad del hueco (menos de {0:g} pF). Dejar el hueco abierto.', C_MINIMA_MONTADO_PF))
    if con_pi:
        y_pi = max(8.6, lg - 4.6)
        aj = ajuste.unir(aj, ajuste.red_pi(0.0, y_pi, w50, p, vertical=True, lado=1))
    cortes_pi = [c for c in aj['cortes'] if c is not corte_c]
    if cortes_pi:
        sup = sup.difference(unary_union(cortes_pi))
    if aj['islas_masa']:
        sup = unary_union([sup] + aj['islas_masa'])
    margen = p.get('margen_borde', 2.0)
    contorno = g.contorno_placa([g.rectangulo(-W/2, 0, W/2, lg), ring.buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(-W/2 - 1e3, 0, W/2 + 1e3, 1e4))
    cx0, _, cx1, alto = contorno.bounds
    masa = masa.intersection(contorno.buffer(-0.5, join_style='mitre'))
    zona_libre = g.rectangulo(cx0, lg, cx1, alto).intersection(contorno)
    per = 4*(a - w) if not redonda else math.pi*(a - w)
    avisos = []
    f_est = estimar_f(p)
    if resistencia_radiacion(p, f_est) < 0.3:
        avisos.append(tr('Bucle muy pequeño: la resistencia de radiación es de {0:.2f} Ω, menos que la de pérdida del cobre y del '
                         'condensador. Casi no radia: agranda el anillo.', resistencia_radiacion(p, f_est)))
    return Antena(tipo=tipo, parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': masa}, ajuste=aj, radiador=ring,
                  contorno=contorno, zona_libre=zona_libre, vias=[(xv, yb + w/2)],
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, yb), 'ancho_linea': w50,
                          'largo_linea_mm': yb + w/2 - 0.5},
                  info={'longitud_traza_mm': round(per, 2), 'ancho_linea_50ohm_mm': round(w50, 3),
                        'inductancia_nH': round(inductancia_nH(p), 2), 'capacidad_total_pF': round(C_pF + C_PARASITA_PF_MM*a, 2),
                        'R_radiacion_ohm': round(resistencia_radiacion(p, f_est), 3),
                        'hueco_minimo_mm': round(min(HUECO_ALIM, 99), 3), 'pista_minima_mm': min(w, w50),
                        'placa_mm': [round(cx1 - cx0, 2), round(alto, 2)], 'avisos': avisos, 'ajuste': aj['notas'] or None,
                        'area_placa_cm2': round(contorno.area/100, 2)})
