"""Seis tipos planares nuevos (23-11, sin validar hasta que se simulen y se midan): dipolo plegado, Moxon, log-periódica, antena de ranura, espiral
y torniquete. Todos de una o dos caras de cobre sobre una sola placa plana.

Las tres primeras se alimentan por una línea de 50 Ω desde el borde inferior (F.Cu) sobre una tira de masa (B.Cu), como el resto de dipolos
antipodales del proyecto: cada mitad de un elemento cuelga de una cara. La ranura va en la masa, alimentada por una microstrip que la cruza. La
espiral y el torniquete se alimentan con un puerto vertical en el centro («pasante», cable soldado por detrás), igual que el panel de dipolos.

Las fórmulas de tamaño (`estimar_f_*`) no están calibradas: hay que centrar simulando (herramientas/barrido.py --centrar).
"""
import math

from shapely.geometry import Point
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste, conector
from .materiales import C0, ancho_microstrip, eps_eff_microstrip
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5
K_PLEGADO = 1.0           # f simulada / f de un dipolo recto de la misma longitud: sin calibrar
K_MOXON = 1.0             # A = 0,477 λ efectiva (Moxon de hilo en el aire): sin calibrar
K_LPDA = 1.0              # centro de la banda: λg/4 = media geométrica de los brazos extremos: sin calibrar
K_RANURA = 1.2            # la ranura de λ0/(2√((εr+1)/2)) resuena un ~20 % alta (herramientas/topologias.py, 08-11)
K_ESPIRAL = 1.25          # centro de banda / frecuencia con circunferencia exterior = λ efectiva: sin calibrar
K_TORNIQUETE = 55200.0    # f [MHz] = K / largo del brazo [mm] (GPS L1: 35 mm; herramientas/topologias.py)
PAD_VIVO = 3.0
TALADRO_COAX = 1.2


def _info(contorno, extra):
    x0, y0, x1, y1 = contorno.bounds
    extra.update({'placa_mm': [round(x1 - x0, 2), round(y1 - y0, 2)], 'area_placa_cm2': round(contorno.area/100, 2),
                  'f_sin_cortar_MHz': None, 'ajuste': None})
    extra.setdefault('avisos', [])
    return extra


def _placa_por_linea(sup, inf, p):
    """Contorno que envuelve el cobre con el margen, sin salir por debajo del borde del conector, y el cobre recortado a 0,5 mm del borde."""
    margen = p.get('margen_borde', 2.0)
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    contorno = g.contorno_placa([unary_union([sup, inf]).buffer(margen), g.rectangulo(-a_min/2, 0, a_min/2, 6.0)],
                                int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    return contorno, sup.intersection(interior), inf.intersection(interior)


def _puerto_linea(w50):
    return {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 2.0), 'ancho_linea': w50}


# ------------------------------------------------------------------ dipolo plegado
def estimar_f_plegado(p, eps):
    """Dipolo plegado de largo `largo`: media onda efectiva (el lazo no cambia mucho la resonancia respecto a un dipolo recto)."""
    return K_PLEGADO*C0/(2*p['largo']*1e-3*math.sqrt(eps))


def generar_plegado(p, s, eps):
    """Dipolo plegado antipodal: el conductor inferior (alimentado) lleva su mitad derecha en F.Cu y la izquierda en B.Cu; el superior, entero en
    B.Cu, se cierra con el extremo izquierdo en B.Cu y el derecho por una vía a la mitad de F.Cu. Impedancia ≈ 4 × la del dipolo (~290 Ω):
    un transformador λg/4 de `z_transformador` Ω la lleva a 50 Ω. Queda un cortocircuito en continua entre el vivo y la masa."""
    from . import tipos
    L, sep, wp = p['largo'], p['separacion'], max(p['ancho_pista'], 1.2)         # la vía pide ≥ 1,2 mm de pista
    w50 = ancho_microstrip(50, s.er, s.h)
    zt = max(p['z_transformador'], 55.0)
    wT = ancho_microstrip(zt, s.er, s.h)
    wb = max(p['ancho_boom'], w50 + 3*s.h)
    avisos = []
    if p['ancho_pista'] < 1.2:
        avisos.append(tr('La pista se sube a 1,2 mm: la vía de cierre del lazo necesita ese ancho.'))
    f_est = tipos.estimar_f('dipolo_plegado', p, s.nombre)
    lam0 = C0/f_est*1e3
    l_t = lam0/math.sqrt(eps_eff_microstrip(s.er, s.h, wT))/4
    y_a = BORDE_COBRE + p['largo_alimentacion']
    y_d = y_a + l_t                                                    # el conductor alimentado
    sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_a), g.rectangulo(-wT/2, y_a, wT/2, y_d + wp/2),
                       g.rectangulo(0.0, y_d - wp/2, L/2, y_d + wp/2)])
    inf = unary_union([g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_d + wp/2),
                       g.rectangulo(-L/2, y_d - wp/2, 0.0, y_d + wp/2),
                       g.rectangulo(-L/2, y_d - wp/2, -L/2 + wp, y_d + sep + wp/2),
                       g.rectangulo(-L/2, y_d + sep - wp/2, L/2, y_d + sep + wp/2),
                       g.rectangulo(L/2 - wp, y_d - wp/2, L/2, y_d + sep + wp/2)])
    contorno, sup, inf = _placa_por_linea(sup, inf, p)
    info = _info(contorno, {'hueco_minimo_mm': round(max(sep - wp, 0.2), 2), 'pista_minima_mm': round(min(w50, wT, wp), 3),
                            'radiador_mm': [round(L, 2), round(sep + wp, 2)], 'transformador_mm': round(l_t, 2), 'avisos': avisos})
    return Antena(tipo='dipolo_plegado', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=_puerto_linea(w50),
                  vias=[(L/2 - wp/2, y_d)], info=info)


# ------------------------------------------------------------------ Moxon
def estimar_f_moxon(p, eps):
    """El ancho A de un Moxon es ~0,477 λ efectiva (la forma de las colas ajusta el resto)."""
    return K_MOXON*0.477*C0/(p['ancho']*1e-3*math.sqrt(eps))


def generar_moxon(p, s, eps):
    """Rectángulo de Moxon: el elemento excitado (delante, hacia +y) y el reflector (detrás) tienen colas dobladas una hacia la otra, separadas
    `hueco`. El excitado es un dipolo antipodal (derecha en F.Cu, izquierda en B.Cu); el reflector, entero en B.Cu y unido a la tira de masa por
    donde la cruza la línea. Haz hacia +y, unos 6 dBi en el aire."""
    A, B, C, D, wp = p['ancho'], p['cola_excitado'], p['hueco'], p['cola_reflector'], p['ancho_pista']
    w50 = ancho_microstrip(50, s.er, s.h)
    wb = max(p['ancho_boom'], w50 + 3*s.h)
    y_r = BORDE_COBRE + p['largo_alimentacion']
    y_d = y_r + D + C + B
    sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_d + wp/2),
                       g.engordar([(0.0, y_d), (A/2, y_d), (A/2, y_d - B)], wp)])
    inf = unary_union([g.rectangulo(-wb/2, BORDE_COBRE, wb/2, y_d + wp/2),
                       g.engordar([(-A/2, y_r + D), (-A/2, y_r), (A/2, y_r), (A/2, y_r + D)], wp),
                       g.engordar([(0.0, y_d), (-A/2, y_d), (-A/2, y_d - B)], wp)])
    contorno, sup, inf = _placa_por_linea(sup, inf, p)
    info = _info(contorno, {'hueco_minimo_mm': round(C, 2), 'pista_minima_mm': round(min(w50, wp), 3),
                            'radiador_mm': [round(A + wp, 2), round(y_d - y_r + wp, 2)]})
    return Antena(tipo='moxon', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=_puerto_linea(w50), info=info)


# ------------------------------------------------------------------ log-periódica
def _brazos_lpda(p):
    """Largos de los brazos de menor a mayor (el menor, junto al conector) y posición y de cada elemento."""
    n, tau, sigma = int(p['elementos']), p['tau'], p['sigma']
    largos = [p['largo_brazo']*tau**(n - 1 - k) for k in range(n)]
    ys = [BORDE_COBRE + p['largo_alimentacion']]
    for k in range(n - 1):
        ys.append(ys[-1] + 4*sigma*largos[k])           # separación d = 2σ · (largo total del elemento)
    return largos, ys


def estimar_f_lpda(p, eps):
    """Centro geométrico de la banda: λg/4 = media geométrica del brazo mayor y el menor."""
    largos, _ = _brazos_lpda(p)
    return K_LPDA*C0/(4*math.sqrt(largos[0]*largos[-1])*1e-3*math.sqrt(eps))


def generar_lpda(p, s, eps):
    """Matriz log-periódica de dipolos antipodales: dos tiras (F.Cu y B.Cu, la línea de 50 Ω) y un dipolo por elemento, cada mitad en su cara, con
    el lado cambiado de un elemento al siguiente (inversión de fase). El elemento menor queda junto al conector; el haz sale hacia él (−y)."""
    w50 = ancho_microstrip(50, s.er, s.h)
    wb = max(p['ancho_boom'], w50 + 3*s.h)
    wp = p['ancho_pista']
    largos, ys = _brazos_lpda(p)
    avisos = []
    sup, inf = [g.rectangulo(-w50/2, BORDE_COBRE, w50/2, ys[-1] + wp/2)], [g.rectangulo(-wb/2, BORDE_COBRE, wb/2, ys[-1] + wp/2)]
    for k, (La, y) in enumerate(zip(largos, ys)):
        lado = 1 if k % 2 == 0 else -1
        sup.append(g.rectangulo(0.0, y - wp/2, lado*La, y + wp/2))
        inf.append(g.rectangulo(0.0, y - wp/2, -lado*La, y + wp/2))
    for k in range(len(ys) - 1):
        if ys[k + 1] - ys[k] - wp < 1.0:
            avisos.append(tr('Los elementos {0} y {1} quedan a menos de 1 mm: baja σ o sube el largo.', k + 1, k + 2))
    contorno, sup, inf = _placa_por_linea(unary_union(sup), unary_union(inf), p)
    f_bajo, f_alto = (K_LPDA*C0/(4*La*1e-3*math.sqrt(eps))/1e6 for La in (largos[-1], largos[0]))
    info = _info(contorno, {'hueco_minimo_mm': round(max(min(b - a - wp for a, b in zip(ys[:-1], ys[1:])), 0.3), 2),
                            'pista_minima_mm': round(min(w50, wp), 3), 'radiador_mm': [round(2*largos[-1], 2), round(ys[-1] - ys[0] + wp, 2)],
                            'banda_estimada_MHz': [round(f_bajo), round(f_alto)], 'avisos': avisos})
    return Antena(tipo='lpda', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=unary_union([sup, inf]), contorno=contorno, zona_libre=contorno, puerto=_puerto_linea(w50), info=info)


# ------------------------------------------------------------------ ranura
def estimar_f_ranura(p, er):
    return K_RANURA*C0/(2*p['largo_ranura']*1e-3*math.sqrt((er + 1)/2))


def generar_ranura(p, s, eps):
    """Ranura de λ/2 en la masa (B.Cu) y una microstrip (F.Cu) que la cruza y acaba en un stub abierto. Radia por las dos caras (bidireccional)."""
    ls, ws, stub, xoff = p['largo_ranura'], p['ancho_ranura'], p['largo_stub'], p['desplazamiento']
    gx = gy = ls*p['lado_masa']
    w50 = ancho_microstrip(50, s.er, s.h)
    masa = g.rectangulo(-gx/2, -gy/2, gx/2, gy/2).buffer(-BORDE_COBRE, join_style='mitre').difference(g.rectangulo(-ls/2, -ws/2, ls/2, ws/2))
    linea = g.rectangulo(xoff - w50/2, -gy/2 + BORDE_COBRE, xoff + w50/2, ws/2 + stub)
    contorno = g.rectangulo(-gx/2, -gy/2, gx/2, gy/2)
    puerto = {'borde': (xoff, -gy/2), 'direccion': (0, 1), 'alimentacion': (xoff, -gy/2 + BORDE_COBRE), 'ancho_linea': w50,
              'largo_linea_mm': gy/2 - ws/2}
    avisos = [] if gx > 1.2*ls else [tr('La masa es pequeña frente a la ranura: sube el lado de la masa.')]
    return Antena(tipo='antena_ranura', parametros=dict(p), capas={'F.Cu': linea, 'B.Cu': masa}, ajuste=ajuste.vacio(),
                  radiador=linea, contorno=contorno, zona_libre=contorno, puerto=puerto,
                  info=_info(contorno, {'hueco_minimo_mm': ws, 'pista_minima_mm': round(w50, 3), 'radiador_mm': [round(ls, 2), ws],
                                        'avisos': avisos}))


# ------------------------------------------------------------------ espiral y torniquete (alimentación vertical en el centro)
def _puerto_central(w_puerto):
    return {'tipo': 'pasante', 'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 0.0), 'ancho_linea': w_puerto,
            'ancho_puerto': w_puerto, 'taladro_mm': TALADRO_COAX, 'pad_vivo_mm': PAD_VIVO, 'pad_malla_mm': PAD_VIVO + 1.0}


def estimar_f_espiral(p, er):
    """Centro de banda ≈ 1,25 × la frecuencia a la que la circunferencia exterior mide una λ efectiva (medio aire, medio FR4)."""
    return K_ESPIRAL*C0/(2*math.pi*p['radio']*1e-3*math.sqrt((er + 1)/2))


def generar_espiral(p, s, eps):
    """Espiral de Arquímedes de dos brazos: uno en F.Cu y el mismo girado 180° en B.Cu, alimentados en el centro por un coaxial por detrás. Cada
    brazo mide `ancho_pista` y entre brazos queda `hueco`. Bidireccional con polarización circular (cada cara, un sentido); `sentido` la invierte."""
    R, w, gap = p['radio'], p['ancho_pista'], p['hueco']
    r0 = PAD_VIVO/2 + 0.6
    paso = 2*(w + gap)                           # avance radial por vuelta de cada brazo
    n_vueltas = max((R - r0 - w/2)/paso, 0.25)
    n_pts = max(int(60*n_vueltas), 24)
    esp = -1 if int(p.get('sentido', 0)) else 1
    pts = []
    for i in range(n_pts + 1):
        phi = 2*math.pi*n_vueltas*i/n_pts
        r = r0 + paso*phi/(2*math.pi)
        pts.append((r*math.cos(phi), esp*r*math.sin(phi)))
    brazo = g.engordar(pts, w)
    centro = Point(0, 0).buffer(r0 + w/2, 32)
    sup = unary_union([brazo, centro])
    from shapely import affinity
    inf = unary_union([affinity.rotate(brazo, 180, origin=(0, 0)), centro])
    contorno = Point(0, 0).buffer(R + p.get('margen_borde', 2.0), 96)
    return Antena(tipo='espiral', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=sup, contorno=contorno, zona_libre=contorno, puerto=_puerto_central(PAD_VIVO),
                  info=_info(contorno, {'hueco_minimo_mm': gap, 'pista_minima_mm': w, 'radiador_mm': [round(2*R, 2), round(2*R, 2)],
                                        'vueltas': round(n_vueltas, 2),
                                        'avisos': [tr('Alimentación con un coaxial soldado por detrás, en el centro: el cable perturba la cara trasera.')]}))


def estimar_f_torniquete(p, er=None):
    return K_TORNIQUETE/p['largo']*1e6


def generar_torniquete(p, s, eps):
    """Dos dipolos cruzados (X e Y), uno por cada cara en cada brazo, alimentados a la vez por un coaxial por detrás en el centro. Con largos distintos
    (X = L(1 + d), Y = L(1 − d)) uno es inductivo y otro capacitivo y salen a ~90°: polarización circular sin red de fase. El signo de `asimetria`
    elige el sentido de giro. Bidireccional (cada cara, un sentido)."""
    L, d, w, c = p['largo'], p['asimetria'], p['ancho_pista'], max(p['lado_centro'], PAD_VIVO + 1.2)
    lx, ly = L*(1 + d), L*(1 - d)
    cuadro = g.rectangulo(-c/2, -c/2, c/2, c/2)
    sup = unary_union([g.engordar([(0, 0), (-lx, 0)], w), g.engordar([(0, 0), (0, ly)], w), cuadro])
    inf = unary_union([g.engordar([(0, 0), (lx, 0)], w), g.engordar([(0, 0), (0, -ly)], w), cuadro])
    m = p.get('margen_borde', 3.0)
    contorno = g.rectangulo(-lx - m, -ly - m, lx + m, ly + m)
    return Antena(tipo='torniquete', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=sup, contorno=contorno, zona_libre=contorno, puerto=_puerto_central(c),
                  info=_info(contorno, {'pista_minima_mm': w, 'hueco_minimo_mm': 1.0, 'radiador_mm': [round(2*lx, 2), round(2*ly, 2)],
                                        'largo_x_mm': round(lx, 2), 'largo_y_mm': round(ly, 2),
                                        'avisos': [tr('Alimentación con un coaxial soldado por detrás, en el centro: el cable perturba la cara trasera.')]}))


TIPOS = {'dipolo_plegado': 'plegado', 'moxon': 'moxon', 'lpda': 'lpda', 'antena_ranura': 'ranura', 'espiral': 'espiral', 'torniquete': 'torniquete'}


def estimar_f(clave, p, er, eps):
    """Frecuencia estimada (Hz) del tipo `clave`; `er` es la εr del sustrato y `eps` la εeff de una pista impresa."""
    if clave == 'dipolo_plegado':
        return estimar_f_plegado(p, eps)
    if clave == 'moxon':
        return estimar_f_moxon(p, eps)
    if clave == 'lpda':
        return estimar_f_lpda(p, eps)
    if clave == 'antena_ranura':
        return estimar_f_ranura(p, er)
    if clave == 'espiral':
        return estimar_f_espiral(p, er)
    return estimar_f_torniquete(p)