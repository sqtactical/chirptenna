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


# ------------------------------------------------------------------ monopolo plano de banda ancha (UWB)
K_UWB = 1.0               # f baja = 72 GHz·mm / altura total (Ray, FR4): sin calibrar
K_PARCHE_CP = 1.0         # modelo de línea de transmisión de un parche cuadrado: sin calibrar
K_SERIE = 1.0
K_SIW = 1.0
RELACION_SIW = 1.35       # f de diseño = 1,35 × la frecuencia de corte de la guía


def estimar_f_uwb(p):
    """Borde bajo de la banda: f [GHz] ≈ 72 / altura total [mm] (disco de Ray para FR4); la banda sigue hasta ~3-4 veces más."""
    H = 2*p['radio']*p['relacion'] + p['hueco']
    return K_UWB*72e9/H


def generar_uwb(p, s, eps):
    """Monopolo plano (disco, elipse u octógono) alimentado por una microstrip, sobre una masa parcial en B.Cu que acaba a `hueco` del radiador."""
    from shapely import affinity
    from shapely.geometry import Polygon
    r, rel, gap, lm = p['radio'], p['relacion'], p['hueco'], p['largo_masa']
    W = max(p['ancho_placa'], 2*r + 4)
    w50 = ancho_microstrip(50, s.er, s.h)
    y_base = lm + gap
    yc = y_base + r*rel
    if int(p.get('forma', 0)) == 1:
        a, b = r, r*rel
        c = 0.3*min(a, b)
        radiador = Polygon([(-a + c, yc - b), (a - c, yc - b), (a, yc - b + c), (a, yc + b - c), (a - c, yc + b), (-a + c, yc + b),
                            (-a, yc + b - c), (-a, yc - b + c)])
    else:
        radiador = affinity.scale(Point(0, yc).buffer(r, 96), 1.0, rel, origin=(0, yc))
    sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_base + 0.5), radiador])
    inf = g.rectangulo(-W/2, BORDE_COBRE, W/2, lm)
    avisos = []
    if lm < 3*s.h:
        avisos.append(tr('La masa es muy corta frente al grosor del sustrato: sube el largo de la masa.'))
    contorno, sup, inf = _placa_por_linea(sup, inf, p)
    info = _info(contorno, {'hueco_minimo_mm': round(gap, 2), 'pista_minima_mm': round(w50, 3),
                            'radiador_mm': [round(2*r, 2), round(2*r*rel, 2)], 'avisos': avisos,
                            'banda_estimada_MHz': [round(estimar_f_uwb(p)/1e6), round(3.5*estimar_f_uwb(p)/1e6)]})
    return Antena(tipo='monopolo_uwb', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=radiador, contorno=contorno, zona_libre=contorno, puerto=_puerto_linea(w50), info=info)


# ------------------------------------------------------------------ parche circular de doble alimentación
def _dims_parche(L, W, er, h):
    ee = (er + 1)/2 + (er - 1)/2/math.sqrt(1 + 12*h/W)
    dL = 0.412*h*(ee + 0.3)*(W/h + 0.264)/((ee - 0.258)*(W/h + 0.8))
    return ee, dL


def estimar_f_parche_cp(p, er, h=1.6):
    ee, dL = _dims_parche(p['lado'], p['lado'], er, h)
    return K_PARCHE_CP*C0/(2*(p['lado'] + 2*dL)*1e-3*math.sqrt(ee))


def generar_parche_cp(p, s, eps):
    """Parche cuadrado alimentado por dos bordes contiguos (abajo y a la izquierda) con muesca, cada uno por una línea de `z_ramas` Ω. Las dos
    salen de una T de la línea de 50 Ω y la de la izquierda lleva un meandro de λg/4: 90° de desfase y polarización circular, sin acoplador."""
    from shapely import affinity
    from . import tipos
    L, z, hm = p['lado'], p['z_ramas'], p['hueco_muesca']
    w50 = ancho_microstrip(50, s.er, s.h)
    wz = ancho_microstrip(z, s.er, s.h)
    f_est = estimar_f_parche_cp(p, s.er, s.h)
    Rb = tipos._parche_rectangular_dims(f_est, s)[4]
    d = min(p.get('muesca', 0) or L/math.pi*math.acos(math.sqrt(min(z/Rb, 1.0))), 0.45*L)
    lam0 = C0/f_est*1e3
    lam_g = lam0/math.sqrt(eps_eff_microstrip(s.er, s.h, wz))
    wb = lam_g/8                                         # el meandro añade 2·wb = λg/4
    a = b = p['separacion_te']
    hb = max(4*wz, 2.5)
    xT, yT = -L/2 - b, -L/2 - a
    parche = g.rectangulo(-L/2, -L/2, L/2, L/2).difference(unary_union([
        g.rectangulo(-wz/2 - hm, -L/2 - 1, wz/2 + hm, -L/2 + d), g.rectangulo(-L/2 - 1, -wz/2 - hm, -L/2 + d, wz/2 + hm)]))
    ym = yT + (L/2 + a - hb)/2
    r1 = g.engordar([(xT, yT), (0, yT), (0, -L/2 + d)], wz)
    r2 = g.engordar([(xT, yT), (xT, ym), (xT - wb, ym), (xT - wb, ym + hb), (xT, ym + hb), (xT, 0), (-L/2 + d, 0)], wz)
    y0 = yT - p['largo_alimentacion']
    entrada = g.rectangulo(xT - w50/2, y0 + BORDE_COBRE, xT + w50/2, yT + w50/2)
    sup = unary_union([parche, r1, r2, entrada])
    margen = max(6*s.h, p['margen_masa'])
    contorno = g.contorno_placa([sup.buffer(margen)], int(p.get('contorno', 1)), recorte=(-1e4, y0, 1e4, 1e4))
    masa = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    radiador = unary_union([parche, r1, r2])
    xp = xT
    if int(p.get('sentido', 0)) == 1:
        esp = lambda geo: affinity.scale(geo, -1.0, 1.0, origin=(0, 0))
        sup, masa, contorno, radiador, xp = esp(sup), esp(masa), esp(contorno), esp(radiador), -xT
    mv = lambda geo: g.mover(geo, 0, -y0)
    contorno = mv(contorno)
    avisos = []
    if wb < 2*wz:
        avisos.append(tr('El meandro de desfase es muy corto: la polarización circular será mala.'))
    info = _info(contorno, {'ancho_linea_50ohm_mm': round(w50, 3), 'pista_minima_mm': round(min(w50, wz), 3), 'hueco_minimo_mm': round(min(hm, hb - wz), 3),
                            'muesca_mm': round(d, 2), 'radiador_mm': [round(L, 2), round(L, 2)], 'R_borde_estimada_ohm': round(Rb, 1),
                            'meandro_mm': round(2*wb, 2), 'polarizacion': 'circular', 'avisos': avisos})
    return Antena(tipo='parche_cp', parametros=dict(p), capas={'F.Cu': mv(sup), 'B.Cu': mv(masa)}, ajuste=ajuste.vacio(),
                  radiador=mv(radiador), contorno=contorno, zona_libre=None,
                  puerto={'borde': (xp, 0.0), 'direccion': (0, 1), 'alimentacion': (xp, 2.0), 'ancho_linea': w50}, info=info)


# ------------------------------------------------------------------ array de parches alimentado en serie
def estimar_f_array_serie(p, er, h=1.6):
    ee, dL = _dims_parche(p['largo'], p['ancho'], er, h)
    return K_SERIE*C0/(2*(p['largo'] + 2*dL)*1e-3*math.sqrt(ee))


def generar_array_serie(p, s, eps):
    """`elementos` parches en fila (eje y, la alimentación llega por abajo) unidos por líneas estrechas, con los centros a `paso` × λg: radian
    en fase hacia delante (perpendicular a la placa). Una sola línea, sin red de reparto; el último parche queda abierto."""
    from . import tipos
    N, L, W, wl, hm = int(p['elementos']), p['largo'], p['ancho'], p['ancho_enlace'], p['hueco_muesca']
    w50 = ancho_microstrip(50, s.er, s.h)
    f_est = estimar_f_array_serie(p, s.er, s.h)
    ee, _ = _dims_parche(L, W, s.er, s.h)
    lam_g = C0/f_est*1e3/math.sqrt(ee)
    paso = max(p['paso']*lam_g, L + 2.0)
    Rb = tipos._parche_rectangular_dims(f_est, s)[4]
    d = min(p.get('muesca', 0) or L/math.pi*math.acos(math.sqrt(min(50/Rb, 1.0))), 0.45*L)
    partes, huecos = [], [g.rectangulo(-w50/2 - hm, -L/2 - 1, w50/2 + hm, -L/2 + d)]
    for k in range(N):
        yk = k*paso
        partes.append(g.rectangulo(-W/2, yk - L/2, W/2, yk + L/2))
        if k < N - 1:
            partes.append(g.rectangulo(-wl/2, yk + L/2 - 0.01, wl/2, yk + paso - L/2 + 0.01))
    sup = unary_union(partes).difference(huecos[0])
    y0 = -L/2 - p['largo_alimentacion']
    linea = g.rectangulo(-w50/2, y0 + BORDE_COBRE, w50/2, -L/2 + d + 0.05)
    sup = unary_union([sup, linea])
    margen = max(6*s.h, p['margen_masa'])
    contorno = g.contorno_placa([sup.buffer(margen)], int(p.get('contorno', 1)), recorte=(-1e4, y0, 1e4, 1e4))
    masa = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    mv = lambda geo: g.mover(geo, 0, -y0)
    avisos = []
    if paso - L < 2.0 + 1e-6:
        avisos.append(tr('Los parches quedan casi pegados: sube la separación o baja el largo.'))
    contorno = mv(contorno)
    info = _info(contorno, {'ancho_linea_50ohm_mm': round(w50, 3), 'pista_minima_mm': round(min(w50, wl), 3), 'hueco_minimo_mm': round(min(hm, paso - L), 3),
                            'muesca_mm': round(d, 2), 'radiador_mm': [round(W, 2), round((N - 1)*paso + L, 2)], 'paso_mm': round(paso, 2),
                            'R_borde_estimada_ohm': round(Rb, 1), 'avisos': avisos})
    return Antena(tipo='array_serie', parametros=dict(p), capas={'F.Cu': mv(sup), 'B.Cu': mv(masa)}, ajuste=ajuste.vacio(),
                  radiador=mv(sup), contorno=contorno, zona_libre=None,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 2.0), 'ancho_linea': w50}, info=info)


# ------------------------------------------------------------------ guía de onda integrada en el sustrato (SIW) con ranuras
def estimar_f_siw(p, er):
    """f de diseño = 1,35 × la de corte de la guía (c / (2 a √εr))."""
    return K_SIW*RELACION_SIW*C0/(2*p['ancho_guia']*1e-3*math.sqrt(er))


def generar_siw(p, s, eps):
    """Guía SIW (dos filas de vías unidas por la cara superior y la masa) alimentada por una microstrip con un taper. En la cara superior, `elementos`
    ranuras longitudinales con el desplazamiento alternado, a λg/2: radian en fase hacia delante. Al fondo, una pared de vías a λg/4 de la última."""
    from . import tipos
    a, N, ls, ws, off = p['ancho_guia'], int(p['elementos']), p['largo_ranura'], p['ancho_ranura'], p['desplazamiento']
    paso_v = p['paso_via']
    w50 = ancho_microstrip(50, s.er, s.h)
    f_est = estimar_f_siw(p, s.er)
    lam0 = C0/f_est*1e3
    fc_term = (lam0/(2*a))**2
    lam_g = lam0/math.sqrt(max(s.er - fc_term, 0.05))
    sep = lam_g/2
    y_t0 = BORDE_COBRE + p['largo_alimentacion']
    lt, wt = p['largo_taper'], min(p['ancho_taper'], a - 4)
    y_s = y_t0 + lt
    ys = [y_s + 0.75*sep + k*sep for k in range(N)]
    y_fin = ys[-1] + sep/2
    dv = 1.0
    top = g.rectangulo(-a/2 - dv, y_s, a/2 + dv, y_fin + dv)
    ranuras = [g.rectangulo((off if k % 2 == 0 else -off) - ws/2, yk - ls/2, (off if k % 2 == 0 else -off) + ws/2, yk + ls/2) for k, yk in enumerate(ys)]
    top = top.difference(unary_union(ranuras))
    from shapely.geometry import Polygon
    taper = Polygon([(-w50/2, y_t0), (w50/2, y_t0), (wt/2, y_s + 0.01), (-wt/2, y_s + 0.01)])
    linea = g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_t0 + 0.01)
    sup = unary_union([top, taper, linea])
    nv = max(int((y_fin - y_s)/paso_v), 1)
    vias = []
    for i in range(nv + 1):
        y = y_s + i*(y_fin - y_s)/nv
        vias += [(-a/2, y), (a/2, y)]
    nx = max(int(a/paso_v), 1)
    vias += [(-a/2 + j*a/nx, y_fin) for j in range(1, nx)]
    margen = max(p['margen_masa'], 2.0)
    contorno = g.contorno_placa([sup.buffer(margen)], int(p.get('contorno', 1)), recorte=(-1e4, 0, 1e4, 1e4))
    interior = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    avisos = []
    if paso_v > 2.5:
        avisos.append(tr('Las vías quedan muy separadas (paso > 2 × el diámetro): la guía pierde energía por las paredes.'))
    if ls > 0.95*sep:
        avisos.append(tr('Las ranuras son casi tan largas como la separación entre ellas: acórtalas.'))
    info = _info(contorno, {'ancho_linea_50ohm_mm': round(w50, 3), 'pista_minima_mm': round(min(w50, ws), 3), 'hueco_minimo_mm': round(ws, 2),
                            'radiador_mm': [round(a + 2*dv, 2), round(y_fin - y_s, 2)], 'lambda_guia_mm': round(lam_g, 2),
                            'separacion_ranuras_mm': round(sep, 2), 'numero_vias': len(vias), 'avisos': avisos})
    return Antena(tipo='antena_siw', parametros=dict(p), capas={'F.Cu': sup.intersection(interior), 'B.Cu': interior}, ajuste=ajuste.vacio(),
                  radiador=top, contorno=contorno, zona_libre=None, puerto=_puerto_linea(w50), vias=vias, info=info)


TIPOS = {'dipolo_plegado': 'plegado', 'moxon': 'moxon', 'lpda': 'lpda', 'antena_ranura': 'ranura', 'espiral': 'espiral', 'torniquete': 'torniquete',
         'monopolo_uwb': 'uwb', 'parche_cp': 'parche_cp', 'array_serie': 'array_serie', 'antena_siw': 'siw'}


def estimar_f(clave, p, er, eps, h=1.6):
    """Frecuencia estimada (Hz) del tipo `clave`; `er` es la εr del sustrato y `eps` la εeff de una pista impresa."""
    if clave == 'monopolo_uwb':
        return estimar_f_uwb(p)
    if clave == 'parche_cp':
        return estimar_f_parche_cp(p, er, h)
    if clave == 'array_serie':
        return estimar_f_array_serie(p, er, h)
    if clave == 'antena_siw':
        return estimar_f_siw(p, er)
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