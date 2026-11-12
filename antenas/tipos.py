"""Catálogo de antenas y dimensionado orientativo.

Cada tipo define sus parámetros (con valores por defecto y límites), un parámetro de
escala que se ajusta para llevar la resonancia a la frecuencia objetivo, una
estimación analítica de la frecuencia y la función que genera la geometría.

Las estimaciones de los monopolos están calibradas con el monopolo recto simulado en
la Fase 0 (FR4 εr 4,4, 1,6 mm, masa 40×40 mm: tira de 23,63 mm → 2,463 GHz) y
modelan cada forma con una "longitud eléctrica equivalente". Son orientativas
(±20 %): el ajuste fino se hace simulando (Fase 2). El parche rectangular usa el
modelo de línea de transmisión (±3–5 %).

Encima de las fórmulas va una calibración con las simulaciones (calibracion_estimaciones.json, que
genera herramientas/calibrar_estimaciones.py): un factor f_simulada/f_fórmula por tipo, interpolado
en frecuencia entre las bandas con datos. Sirve para que el ajuste por simulación empiece cerca.
"""
import os
import json
import math
from dataclasses import dataclass, field, replace

import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

from . import geometria as g
from . import directivas
from . import ancho_banda
from . import jpole
from . import bibanda
from . import bucle
from . import dipolos
from . import ajuste
from . import conector
from . import integracion
from .tipos_base import Parametro
from .materiales import SUSTRATOS, SUSTRATO_POR_DEFECTO, ancho_microstrip, eps_eff_microstrip, lambda0_mm, C0
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5            # retranqueo del cobre respecto al borde de la placa [mm]

# Calibración de la Fase 0: sqrt(εeff) efectiva de un monopolo impreso = 1,2876 con εr 4,4
_Q_MONOPOLO = (1.2876**2 - 1)/(4.4 - 1)


def eps_eff_monopolo(er):
    return 1 + _Q_MONOPOLO*(er - 1)


@dataclass
class TipoAntena:
    clave: str
    nombre: str
    descripcion: str
    familia: str                      # 'monopolo' o 'parche'
    parametros: list
    escala: str                       # parámetro que se ajusta a la frecuencia
    bandas: list = field(default_factory=lambda: [868e6, 2.4e9])
    escala_conjunta: tuple = ()       # otros parámetros que se escalan en proporción
    precision: str = '±20 % (orientativa; ajustar simulando)'

    def defectos(self):
        return {p.nombre: p.defecto for p in self.parametros}


# ------------------------------------------------------------------ monopolos
# Plano de masa de los monopolos. La masa es la otra mitad de la antena: si es más corta que
# λ/4 efectivo la resonancia sube y el radiador tiene que alargarse (modelo de dipolo
# asimétrico: radiador + masa ≈ λ/2 efectivo).
MODOS_MASA = {0: 'Manual', 1: 'Automática λ/4 (recomendada)', 2: 'Automática compacta (λ/8)',
              3: 'Automática mínima (solo cabe el conector)'}
FRACCION_MASA = {1: 1.0, 2: 0.5}
PARAMS_MASA = [
    Parametro('masa', 'Plano de masa', 1, 0, 3, 1, True, opciones=MODOS_MASA,
              ayuda='Automática: largo según λ/4 (o fracción) y ancho ajustado al radiador'),
    Parametro('ancho_placa', 'Ancho de la placa / plano de masa [mm]', 40, 10, 400, 1),
    Parametro('largo_masa', 'Largo del plano de masa [mm]', 40, 10, 400, 1),
]
PARAMS_SOLO_MANUAL = {'ancho_placa', 'largo_masa', 'margen_masa'}
# Alimentación de los parches: por el borde con transformador λ/4 o por muesca hasta el punto de 50 Ω
PARAMS_MUESCA = [
    Parametro('alimentacion', 'Alimentación', 0, 0, 1, 1, True,
              opciones={0: 'Por el borde, con transformador λ/4', 1: 'Por ranura (inset) hasta el punto de 50 Ω'},
              ayuda='La ranura ahorra la cola del transformador (~λg/4 bajo el parche)'),
    Parametro('muesca', 'Profundidad de la ranura desde el borde del parche [mm] (0 = estimada)', 0, 0, 100, 0.1),
    Parametro('hueco_muesca', 'Hueco a cada lado de la línea en la ranura [mm]', 1.0, 0.3, 5, 0.1),
]

# Recortes para aligerar (Yagi y panel): ventanas sin FR4 donde no hay cobre
PARAMS_ALIGERADO = [
    Parametro('aligerado', 'Recortes para aligerar', 0, 0, 1, 1, True,
              opciones={0: 'No', 1: 'Sí: ventanas sin FR4 entre el borde y el centro'},
              ayuda='Menos peso y algo menos de pérdidas; quitar FR4 sube un poco la frecuencia: vuelve a simular'),
    Parametro('margen_aligerado', 'Distancia de las ventanas al cobre [mm]', 2.0, 1.0, 20, 0.5),
    Parametro('nervio', 'Ancho del marco y de los nervios [mm]', 3.0, 1.5, 20, 0.5,
              ayuda='Marco del borde, nervio central y nervios que parten las ventanas largas'),
]
PARAMS_SOLO_ALIGERADO = {'margen_aligerado', 'nervio'}

# Comunes a todos los tipos: forma de la placa de prueba
PARAMS_CONTORNO = [
    Parametro('contorno', 'Contorno de la placa', 1, 0, 1, 1, True,
              opciones={0: 'Rectangular', 1: 'Ajustado a la antena'},
              ayuda='Ajustado: sigue la forma de la antena (envolvente con esquinas redondeadas)'),
    Parametro('margen_borde', 'Margen del cobre al borde [mm]', 2.0, 1.0, 20, 0.5),
]
PARAM_CONECTOR = Parametro('conector', 'Conector', conector.SMA, 0, 3, 1, True, opciones=conector.NOMBRES,
                           ayuda='IPEX: encima de la placa a 3 mm del borde; la masa mínima de los monopolos '
                                 'baja de 12 a 7 mm y el ancho mínimo de 16 a 8 mm. Coaxial soldado: sin conector, '
                                 'con un pad para el vivo en la línea y otro para la malla, unido a la masa. Pad de RF: sin conector, '
                                 'un pad en el extremo de la línea de 50 Ω con dos vías de masa al lado, para llegar a él con la línea de tu producto')


def largo_masa_monopolo(p, le, clave=None):
    """Largo del plano de masa [mm] según el modo. le: longitud equivalente del radiador.

    Con masa = fracción·λeff/4 y radiador + masa = λeff/2  ->  masa = fracción·le/(2 − fracción).
    Con la antena integrada en una placa (`clave` en `integracion.TIPOS`) es lo que queda de placa bajo la zona de antena.
    """
    if clave is not None and integracion.activa(p, clave):
        arriba = _radiador_monopolo(clave, p)[0].bounds[3]
        return max(integracion.largo_masa(p, arriba), 1.0)
    modo = int(p.get('masa', 0))
    # con red en π la línea de 50 Ω necesita sitio para los tres componentes además del SMA
    minimo = (MASA_RED_PI if ajuste.activo(p) and int(p.get('red_pi', 0)) == 1
              else conector.MASA_MINIMA[conector.tipo(p)])
    if modo == 0:
        return max(p['largo_masa'], minimo) if minimo == MASA_RED_PI else p['largo_masa']
    if modo == 3:
        return minimo
    k = FRACCION_MASA[modo]
    return max(minimo, k*le/(2 - k))


MASA_RED_PI = 14.0
K_EQ_PUNTA = {'monopolo_flecha': 0.5, 'monopolo_recto': 1.0, 'monopolo_koch': 1.0, 'monopolo_meandro': 0.6, 'monopolo_hilbert': 0.5}


def _radiador_monopolo(clave, p):
    """Radiador con la alimentación en (0,0), creciendo hacia +y.

    Devuelve (geometría, longitud de la pista, polilínea o None si no es una pista).
    """
    w = p.get('ancho_pista', 1.0)
    if clave in ('ifa', 'pifa'):
        # F invertida: toma de alimentación en (0,0), brazo horizontal a la altura h y cortocircuito a masa
        L, h, d, wf = p['largo_brazo'], p['altura'], p['separacion_toma'], min(p['ancho_pista'], 2.0)
        wc, sd = p['ancho_corto'], PROFUNDIDAD_CORTO
        geo = unary_union([g.rectangulo(-d - wc/2, h - w/2, L - d, h + w/2),
                           g.rectangulo(-wf/2, 0, wf/2, h + w/2),
                           g.rectangulo(-d - wc/2, -sd, -d + wc/2, h + w/2)])
        return geo, geo.area/w, None
    if clave in ('monopolo_recto', 'dipolo_sleeve'):
        pts = np.array([(0, 0), (0, p['alto'])], float)
        return g.engordar(pts, w), p['alto'], pts
    if clave == 'monopolo_meandro':
        n, a, h, t = int(p['vueltas']), p['ancho_meandro'], p['alto'], p['tramo_inicial']
        # sube el tramo inicial desde la alimentación, va al lado izquierdo y hace el meandro centrado
        pts = [(0.0, 0.0), (0.0, t)] + [tuple(q) for q in g.meandro(n, a, h - t) + [-a/2, t]]
        limpio = [pts[0]]
        for q in pts[1:]:
            if np.hypot(q[0] - limpio[-1][0], q[1] - limpio[-1][1]) > 1e-9:
                limpio.append(q)
        return g.engordar(limpio, w), g.longitud(limpio), np.array(limpio)
    if clave == 'monopolo_koch':
        pts = g.koch(int(p['iteracion']), (0, 0), (0, p['alto']), p['angulo'])
        return g.engordar(pts, w), g.longitud(pts), pts
    if clave == 'monopolo_flecha':
        pts = g.flecha_sierpinski(int(p['iteracion']), p['alto'])
        return g.engordar(pts, w), g.longitud(pts), pts
    if clave == 'monopolo_hilbert':
        s, d = p['lado'], p['separacion']
        pts = g.hilbert(int(p['orden']))*s + [0, d]
        pts = np.vstack([[0, 0], pts])
        return g.engordar(pts, w), g.longitud(pts), pts
    if clave == 'monopolo_sierpinski':
        h = p['alto']
        base = 2*h*math.tan(math.radians(p['apertura'])/2)
        tri = g.sierpinski(int(p['iteracion']), base, h, p.get('cuello', 1.0))
        return tri, h, None
    raise KeyError(clave)


PROFUNDIDAD_CORTO = 2.0      # el cortocircuito de la F invertida entra tanto en la zona de masa [mm]


def _longitud_equivalente(clave, p):
    if clave in ('ifa', 'pifa'):
        return p['largo_brazo'] + p['altura']
    if clave in ('monopolo_recto', 'dipolo_sleeve'):
        return p['alto']
    if clave == 'monopolo_meandro':
        _, l_total, _ = _radiador_monopolo(clave, p)
        return p['alto'] + 0.5*(l_total - p['alto'])
    if clave == 'monopolo_koch':
        return p['alto']*(1 + 0.35*((4/3)**int(p['iteracion']) - 1))
    if clave == 'monopolo_flecha':
        return p['alto']*(1 + 0.35*(1.5**int(p['iteracion']) - 1))
    if clave == 'monopolo_hilbert':
        n = int(p['orden'])
        return p['separacion'] + 0.45*p['lado']*(2**n + 1)
    if clave == 'monopolo_sierpinski':
        return 1.25*p['alto']
    raise KeyError(clave)


def _generar_monopolo(tipo, p, sustrato):
    rad, l_traza, pts = _radiador_monopolo(tipo.clave, p)
    w50 = ancho_microstrip(50, sustrato.er, sustrato.h)
    le = _longitud_equivalente(tipo.clave, p)
    lg = largo_masa_monopolo(p, le, tipo.clave)
    integrada = integracion.activa(p, tipo.clave)
    if integrada and integracion.largo_masa(p, _radiador_monopolo(tipo.clave, p)[0].bounds[3]) < conector.MASA_MINIMA[conector.tipo(p)]:
        zona = p['placa_y'] - integracion.largo_masa(p, _radiador_monopolo(tipo.clave, p)[0].bounds[3])
        raise ValueError(tr('La zona de antena mide {0:.1f} mm de alto y bajo ella el conector necesita {1:.0f} mm de masa: '
                            'la placa tiene que medir al menos {2:.1f} mm de alto.',
                            zona, conector.MASA_MINIMA[conector.tipo(p)], zona + conector.MASA_MINIMA[conector.tipo(p)]))
    aj = ajuste.vacio()
    f_nom = _f_monopolo(tipo, p, sustrato)*k_sim(p)
    if ajuste.activo(p) and pts is not None:
        # sobrelargo/marcas/tramos en la punta del radiador (coordenadas locales)
        extra, a1, _ = ajuste.alargar_polilinea(pts, p.get('ancho_pista', 1.0), le, K_EQ_PUNTA[tipo.clave],
                                                 f_nom, p)
        if extra is not None:
            rad = unary_union([rad, extra])
        aj = ajuste.unir(aj, ajuste.mover(a1, 0, lg))
    minx, _, maxx, maxy = rad.bounds
    margen = p.get('margen_borde', 2.0)
    if integrada:
        pass                   # contorno, masa y zona libre salen de `integracion.geometria` (abajo)
    elif int(p.get('masa', 0)) == 0:
        # manual: masa centrada con el ancho pedido (o más, si el radiador no cabe)
        semi = max(p['ancho_placa']/2, max(abs(minx), abs(maxx)) + margen)
        gx0, gx1 = -semi, semi
    else:
        # automática: la masa cubre el radiador (aunque no esté centrado) y el conector
        a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
        gx0 = min(minx - margen, -a_min/2)
        gx1 = max(maxx + margen, a_min/2)
    radiador = g.mover(rad, 0, lg)
    if integrada:
        # el conector solo necesita su propio ancho (la mitad del ancho mínimo de una placa de prueba, que lleva masa de sobra)
        semi = (w50/2 + conector.V_VIA_RF + 0.6 if conector.tipo(p) == conector.PAD_RF       # las vías de masa junto al pad
                else conector.ANCHO_MINIMO[conector.tipo(p)]/4)
        geo = integracion.geometria(p, radiador, lg, semi)
        contorno, masa, gx0, gx1, alto_placa = geo['contorno'], geo['masa'], geo['gx0'], geo['gx1'], geo['alto_placa']
        cx0, ancho = gx0, gx1 - gx0
    else:
        contorno = g.contorno_placa([g.rectangulo(gx0, 0, gx1, lg), radiador.buffer(margen)],
                                    int(p.get('contorno', 1)), recorte=(gx0 - 1e3, 0, gx1 + 1e3, 1e4))
        cx0, _, cx1, alto_placa = contorno.bounds
        ancho = cx1 - cx0
        masa = g.rectangulo(gx0, 0, gx1, lg).intersection(contorno.buffer(-BORDE_COBRE, join_style='mitre'))
    entra = 0.01
    if tipo.clave == 'monopolo_sierpinski':
        # el vértice inferior es un punto: la línea entra hasta donde el triángulo es tan ancho como ella
        entra = w50/2/math.tan(math.radians(p['apertura'])/2)
    alim = g.rectangulo(-w50/2, BORDE_COBRE, w50/2, lg + entra)
    zona_libre = geo['zona'] if integrada else g.rectangulo(cx0, lg, cx0 + ancho, alto_placa).intersection(contorno)
    # Si las vueltas de la pista se pisan, el área real queda por debajo de largo × ancho
    solape = None
    if tipo.clave != 'monopolo_sierpinski':
        esperada = l_traza*p.get('ancho_pista', 1.0)
        solape = max(0.0, 1 - rad.area/esperada) if esperada > 0 else 0.0
    # Huecos conocidos por construcción (para la malla de la simulación)
    huecos = {'monopolo_flecha': lambda: p['alto']/2**int(p['iteracion'])*math.sin(math.radians(60)) - p['ancho_pista'],
              'monopolo_hilbert': lambda: p['lado']/(2**int(p['orden']) - 1) - p['ancho_pista'],
              'monopolo_meandro': lambda: (p['alto'] - p['tramo_inicial'])/(2*int(p['vueltas'])) - p['ancho_pista']}
    hueco = huecos[tipo.clave]() if tipo.clave in huecos else None
    avisos = []
    if lg < 0.95*le:
        avisos.append(tr('Masa de {0:.0f} mm, el {1:.0f} % de λ/4: menos eficiencia y ancho de banda, y el cable pasa a formar parte de la antena (usar ferrita al medir).', lg, 100*lg/((le + lg)/2)))
    sup = unary_union([alim, radiador])
    if ajuste.activo(p) and int(p.get('red_pi', 0)) == 1:
        # red en π en la línea de 50 Ω, lo más cerca posible de la antena pero por encima del SMA
        y_c = 7.0 if conector.tipo(p) == conector.PAD_RF else max(8.6, lg - 4.6)      # con pad de RF, la red va junto al pad (sin SMA)
        aj = ajuste.unir(aj, ajuste.red_pi(0.0, y_c, w50, p, vertical=True, lado=1))
    if aj['cortes']:
        sup = sup.difference(unary_union(aj['cortes']))
    if aj['islas_masa']:
        sup = unary_union([sup] + aj['islas_masa'])
    return Antena(tipo=tipo.clave, parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': masa}, ajuste=aj,
                  radiador=radiador, contorno=contorno, zona_libre=zona_libre,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, lg), 'ancho_linea': w50,
                          'largo_linea_mm': lg - BORDE_COBRE},
                  info={'longitud_traza_mm': round(l_traza, 2), 'ancho_linea_50ohm_mm': round(w50, 3),
                        'solape_pistas': None if solape is None else round(solape, 3),
                        'hueco_minimo_mm': None if hueco is None else round(max(hueco, 0.0), 3),
                        'pista_minima_mm': p.get('ancho_pista', p.get('cuello')),
                        'placa_mm': [round(ancho, 2), round(alto_placa, 2)],
                        'masa_mm': [round(gx1 - gx0 - 2*BORDE_COBRE, 2), round(lg - BORDE_COBRE, 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'radiador_mm': [round(maxx - minx, 2), round(maxy, 2)], 'avisos': avisos,
                        'f_sin_cortar_MHz': (round(f_nom/(1 + p.get('sobrelargo', 0)/100)/1e6, 1)
                                             if ajuste.activo(p) and int(p.get('marcas', 0)) == 1 else None),
                        'ajuste': aj['notas'] or None})


def k_sim(p):
    """Corrección de la estimación analítica que deja `simulacion.ajustar` (f simulada / estimada).
    Solo rotula las marcas de corte y la frecuencia sin cortar: la geometría no la usa."""
    return float(p.get('k_sim', 1.0))


def _f_monopolo(tipo, p, sustrato):
    """Radiador + masa como dipolo asimétrico: si la masa es ≥ λ/4 no influye; si no, la
    resonancia es la de un dipolo de largo radiador + masa."""
    le = _longitud_equivalente(tipo.clave, p)
    lg = largo_masa_monopolo(p, le, tipo.clave)
    cuarto = le if lg >= le else (le + lg)/2
    return C0/(4*cuarto*1e-3*math.sqrt(eps_eff_monopolo(sustrato.er)))


# ------------------------------------------------------------------ parches
def _parche_rectangular_dims(f, s):
    """Modelo de línea de transmisión (Balanis): ancho, largo, εeff y resistencia de borde."""
    lam = lambda0_mm(f)
    W = lam/2*math.sqrt(2/(s.er + 1))
    ee = (s.er + 1)/2 + (s.er - 1)/2/math.sqrt(1 + 12*s.h/W)
    dL = 0.412*s.h*(ee + 0.3)*(W/s.h + 0.264)/((ee - 0.258)*(W/s.h + 0.8))
    L = lam/(2*math.sqrt(ee)) - 2*dL
    k0 = 2*math.pi/lam
    G1 = W/(120*lam)*(1 - (k0*s.h)**2/24) if W < lam else W/(120*lam)
    R_borde = 1/(2*G1)
    return W, L, ee, dL, R_borde


def poligono_parche(minkowski, p):
    """Parche centrado en el origen (rectangular o con bordes de Minkowski)."""
    L, W = p['largo'], p['ancho']
    if minkowski and int(p.get('iteracion', 0)) > 0:
        esquinas = [(-W/2, -L/2), (W/2, -L/2), (W/2, L/2), (-W/2, L/2)]
        return g.isla_minkowski(esquinas, int(p['iteracion']), p['profundidad'])
    parche = g.rectangulo(-W/2, -L/2, W/2, L/2)
    if p.get('ranura_largo', 0) > 0:
        # ranura en U (más banda): base horizontal y dos brazos que suben hacia el borde radiante superior
        a, hs = p['ranura_ancho']*W, p.get('ranura_hueco', 1.0)
        y_b = L/2 - p['ranura_largo']*L
        y_t = L/2 - 0.1*L
        u = unary_union([g.rectangulo(-a/2 - hs/2, y_b - hs/2, a/2 + hs/2, y_b + hs/2),
                         g.rectangulo(-a/2 - hs/2, y_b, -a/2 + hs/2, y_t),
                         g.rectangulo(a/2 - hs/2, y_b, a/2 + hs/2, y_t)])
        parche = parche.difference(u)
    if p.get('parasito_hueco', 0) > 0:
        # parche parásito acoplado por el borde radiante superior (alternativa plana al apilado)
        Lp = p['parasito_factor']*L
        y0 = L/2 + p['parasito_hueco']
        parche = unary_union([parche, g.rectangulo(-W/2, y0, W/2, y0 + Lp)])
    if p.get('corte', 0) > 0:
        # polarización circular: dos esquinas opuestas cortadas (el modo se desdobla en dos a 90°)
        c = p['corte']*min(L, W)
        s = -1 if int(p.get('diagonal', 0)) == 1 else 1
        for sx, sy in ((s, 1), (-s, -1)):
            parche = parche.difference(Polygon([(sx*W/2, sy*L/2), (sx*(W/2 - c), sy*L/2), (sx*W/2, sy*(L/2 - c))]))
    return parche


def _generar_parche(tipo, p, sustrato):
    s = sustrato
    w50 = ancho_microstrip(50, s.er, s.h)
    L, W = p['largo'], p['ancho']
    # Contorno del parche (centrado en el origen), y alimentación por el centro del borde inferior
    parche = poligono_parche(tipo.clave == 'parche_minkowski', p)
    # Transformador λ/4 desde 50 Ω hasta la resistencia de borde estimada
    f_est = _f_parche(tipo, p, s)
    _, _, _, _, R_borde = _parche_rectangular_dims(f_est, s)
    if tipo.clave == 'parche_minkowski':
        R_borde *= p.get('factor_r_borde', 1.0)
    y_borde = parche.bounds[1]
    # en el Minkowski el borde inferior tiene entrantes; se alimenta en el punto más bajo del eje
    eje = LineString([(0, -L), (0, 0)]).intersection(parche)
    y_entrada = eje.bounds[1] if not eje.is_empty else y_borde
    con_muesca = int(p.get('alimentacion', 0)) == 1
    if con_muesca:
        # Muesca (inset): R(d) = R_borde·cos²(π·d/L) desde el borde; la línea de 50 Ω entra hasta R = 50 Ω.
        # En el Minkowski la estimación es orientativa: `simulacion.ajustar` afina la profundidad.
        d_est = L/math.pi*math.acos(math.sqrt(min(50/R_borde, 1.0)))
        d_m = p.get('muesca', 0) or d_est
        d_m = min(d_m, 0.45*L)
        hm = p.get('hueco_muesca', 1.0)
        zt, wt, lt = 50.0, w50, 0.0
    else:
        zt = math.sqrt(50*R_borde)
        wt = ancho_microstrip(zt, s.er, s.h)
        lt = lambda0_mm(f_est)/4/math.sqrt(eps_eff_microstrip(s.er, s.h, wt))
    margen = 6*s.h if int(p.get('masa', 0)) == 1 else max(6*s.h, p['margen_masa'])
    # con ranura la línea solo cruza el margen de masa hasta el SMA (lo que se quería ahorrar)
    l50 = (y_entrada - y_borde) + margen if con_muesca else p['largo_alimentacion']
    con_pi = ajuste.activo(p) and int(p.get('red_pi', 0)) == 1
    if con_pi:
        l50 = max(l50, MASA_RED_PI)                 # sitio para la red en π junto al SMA
    if conector.tipo(p) == conector.IPEX:
        l50 = max(l50, conector.largo_ocupado() + 1.0)   # el IPEX ocupa el arranque de la línea
    y0 = y_entrada - lt - l50
    if con_muesca:
        # la línea sube por la muesca hasta el fondo (punto de 50 Ω), donde se une al parche. La
        # profundidad se mide desde el borde radiante (el más bajo del parche), no desde la entrada: en
        # el Minkowski de iteración 3 la entrante central ya mete la entrada ~L/6 y, sumándola, la línea
        # llegaba casi al centro (R ≈ 0: la simulación dio 1,7 Ω y −15 dBi)
        y_alim = max(y_borde + d_m, y_entrada + 1.0)
        trafo = g.rectangulo(-w50/2, y_entrada - 0.01, w50/2, y_alim + 0.05)
    else:
        y_alim = y_entrada - lt
        trafo = g.rectangulo(-wt/2, y_entrada - lt, wt/2, y_entrada + 0.05)
    linea = g.rectangulo(-w50/2, y0 + BORDE_COBRE, w50/2, y_entrada - lt + 0.01)
    aj = ajuste.vacio()
    if ajuste.activo(p) and tipo.clave == 'parche_rectangular':
        # sobrelargo por el borde radiante superior + marcas de corte paralelas a él
        ext, a1 = ajuste.marcas_parche(-W/2, W/2, parche.bounds[3], L, f_est*k_sim(p), p)
        if ext > 0:
            parche = g.rectangulo(-W/2, -L/2, W/2, L/2 + ext)
        aj = ajuste.unir(aj, a1)
    if con_muesca:
        parche = parche.difference(g.rectangulo(-w50/2 - hm, y_entrada - 1.0, w50/2 + hm, y_alim))
    if con_pi:
        aj = ajuste.unir(aj, ajuste.red_pi(0.0, y0 + max(8.6, l50 - 4.6), w50, p, vertical=True, lado=1))
    minx, miny, maxx, maxy = parche.bounds
    # la masa (toda la placa) sobresale 'margen' alrededor del parche y de la alimentación
    contorno = g.contorno_placa([unary_union([parche, trafo, linea]).buffer(margen)], int(p.get('contorno', 1)),
                                recorte=(-1e4, y0, 1e4, 1e4))
    masa = contorno.buffer(-BORDE_COBRE, join_style='mitre')
    desp = -y0                                      # placa empezando en y=0
    mv = lambda geo: g.mover(geo, 0, desp)
    sup = unary_union([parche, trafo, linea])
    if aj['cortes']:
        sup = sup.difference(unary_union(aj['cortes']))
    if aj['islas_masa']:
        sup = unary_union([sup] + aj['islas_masa'])
    aj = ajuste.mover(aj, 0, desp)
    return Antena(tipo=tipo.clave, parametros=dict(p), ajuste=aj,
                  capas={'F.Cu': mv(sup), 'B.Cu': mv(masa)},
                  radiador=mv(unary_union([parche, trafo])), contorno=mv(contorno), zona_libre=None,
                  puerto={'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_entrada - lt + desp),
                          'ancho_linea': w50},
                  info={'ancho_linea_50ohm_mm': round(w50, 3), 'R_borde_estimada_ohm': round(R_borde, 1),
                        'pista_minima_mm': round(min(wt, w50), 3),   # el transformador (la malla debe verlo)
                        'transformador': (None if con_muesca else
                                          {'Z_ohm': round(zt, 1), 'ancho_mm': round(wt, 3), 'largo_mm': round(lt, 2)}),
                        'muesca_mm': round(d_m, 2) if con_muesca else None,
                        'hueco_minimo_mm': round(hm, 3) if con_muesca else None,
                        'placa_mm': [round(contorno.bounds[2] - contorno.bounds[0], 2),
                                     round(contorno.bounds[3] - contorno.bounds[1], 2)],
                        'area_placa_cm2': round(contorno.area/100, 2),
                        'radiador_mm': [round(maxx - minx, 2), round(maxy - miny, 2)],
                        'f_sin_cortar_MHz': (round(f_est*k_sim(p)*L/(L + L*p.get('sobrelargo', 0)/100)/1e6, 1)
                                             if ajuste.activo(p) and int(p.get('marcas', 0)) == 1
                                             and tipo.clave == 'parche_rectangular' else None),
                        'ajuste': aj['notas'] or None})


def _f_parche(tipo, p, s):
    """Frecuencia del modo TM010 por el largo L (modelo de línea de transmisión)."""
    L, W = p['largo'], p['ancho']
    ee = (s.er + 1)/2 + (s.er - 1)/2/math.sqrt(1 + 12*s.h/W)
    dL = 0.412*s.h*(ee + 0.3)*(W/s.h + 0.264)/((ee - 0.258)*(W/s.h + 0.8))
    f = C0/(2*(L + 2*dL)*1e-3*math.sqrt(ee))
    if tipo.clave == 'parche_minkowski' or (tipo.clave == 'array_parches' and int(p['elemento']) == 1):
        # Las muescas alargan el camino de la corriente y bajan la frecuencia: del orden de
        # un 20 %·profundidad por iteración (orientativo, a calibrar simulando).
        f /= (1 + 0.2*p['profundidad']*int(p['iteracion']))
    return f


# ------------------------------------------------------------------ catálogo
PISTA = Parametro('ancho_pista', 'Ancho de la pista del radiador [mm]', 1.0, 0.15, 15, 0.05)

CATALOGO = {t.clave: t for t in [
    TipoAntena('monopolo_recto', 'Monopolo recto (referencia)',
               'Tira recta sobre la zona sin masa. Referencia para comparar.', 'monopolo',
               [Parametro('alto', 'Largo de la tira [mm]', 23.6, 3, 200, 0.1), PISTA] + PARAMS_MASA, 'alto'),
    TipoAntena('monopolo_meandro', 'Monopolo en meandro (referencia compacta)',
               'Tira en zigzag: reduce la altura a costa de ancho de banda.', 'monopolo',
               [Parametro('alto', 'Altura total [mm]', 20, 3, 200, 0.1),
                Parametro('ancho_meandro', 'Ancho del meandro [mm]', 8, 1, 100, 0.1),
                Parametro('vueltas', 'Vueltas', 3, 1, 20, 1, True),
                Parametro('tramo_inicial', 'Tramo recto inicial [mm]', 0, 0, 50, 0.1), PISTA] + PARAMS_MASA, 'alto',
               escala_conjunta=('ancho_meandro',)),
    TipoAntena('monopolo_koch', 'Monopolo de Koch',
               'Curva de Koch: la iteración alarga la pista sin aumentar la altura.', 'monopolo',
               [Parametro('alto', 'Altura (distancia entre extremos) [mm]', 20, 3, 200, 0.1),
                Parametro('iteracion', 'Iteración', 2, 0, 4, 1, True),
                Parametro('angulo', 'Ángulo de la indentación [°]', 60, 20, 85, 1), PISTA] + PARAMS_MASA, 'alto'),
    TipoAntena('monopolo_flecha', 'Monopolo de punta de flecha de Sierpinski',
               'Curva de punta de flecha de Sierpinski: una sola pista que rellena un triángulo, de esquina a esquina '
               'de su base. Muy compacta; por curiosidad, sin validar.', 'monopolo',
               [Parametro('alto', 'Base del triángulo (entre extremos) [mm]', 13, 3, 200, 0.1),
                Parametro('iteracion', 'Iteración', 3, 1, 6, 1, True),
                Parametro('ancho_pista', 'Ancho de la pista [mm]', 0.4, 0.15, 5, 0.05)] + PARAMS_MASA,
               'alto', escala_conjunta=('ancho_pista',), precision='±25 % (sin calibrar)'),
    TipoAntena('monopolo_hilbert', 'Monopolo de Hilbert',
               'Curva de Hilbert: muy compacta; el orden alto exige pistas y huecos finos.', 'monopolo',
               [Parametro('lado', 'Lado del cuadrado [mm]', 15, 3, 100, 0.1),
                Parametro('orden', 'Orden', 3, 1, 5, 1, True),
                Parametro('separacion', 'Separación sobre la masa [mm]', 2, 0, 20, 0.1),
                Parametro('ancho_pista', 'Ancho de la pista del radiador [mm]', 0.6, 0.15, 5, 0.05)] + PARAMS_MASA,
               # la pista debe seguir al paso de la curva (lado/(2^orden − 1)) o las vueltas se pisan
               'lado', escala_conjunta=('ancho_pista', 'separacion')),
    TipoAntena('monopolo_sierpinski', 'Monopolo de Sierpinski',
               'Triángulo de Sierpinski: multibanda, con bandas a razón ~2.', 'monopolo',
               [Parametro('alto', 'Altura [mm]', 25, 3, 200, 0.1),
                Parametro('apertura', 'Ángulo de apertura [°]', 60, 20, 120, 1),
                Parametro('iteracion', 'Iteración', 2, 0, 5, 1, True),
                Parametro('cuello', 'Ancho de las uniones entre triángulos [mm]', 1.0, 0.3, 15, 0.1),
                Parametro('multibanda', 'Bandas', 0, 0, 1, 1, True,
                          opciones={0: 'Una banda', 1: 'Dos bandas (la segunda, a ~3 veces la primera)'},
                          ayuda='Dos bandas: el diseño se ajusta a la banda baja y, con apertura 85° e iteración 2, la segunda '
                                'resonancia cae cerca de 3 veces su frecuencia (868/915 MHz y 2,4 GHz en simulación)')] + PARAMS_MASA,
               'alto'),
    TipoAntena('ifa', 'Antena F invertida (J-pole en F)',
               'Monopolo λ/4 plegado en «F»: brazo horizontal paralelo a la masa, alimentado por una toma y '
               'cortocircuitado a masa con una vía. Compacta y baja.', 'monopolo',
               [Parametro('largo_brazo', 'Largo del brazo horizontal [mm]', 20, 3, 200, 0.1),
                Parametro('altura', 'Altura del brazo sobre la masa [mm]', 7, 1, 50, 0.1),
                Parametro('separacion_toma', 'Distancia entre el cortocircuito y la toma [mm]', 3.5, 1, 30, 0.1,
                          ayuda='Fija la impedancia: más separada, más impedancia'),
                Parametro('ancho_pista', 'Ancho del brazo [mm]', 1.0, 0.3, 10, 0.05),
                Parametro('ancho_corto', 'Ancho del cortocircuito [mm]', 1.0, 0.5, 10, 0.05),
                Parametro('multibanda', 'Bandas', 0, 0, 1, 1, True,
                          opciones={0: 'Una banda', 1: 'Dos bandas (la baja del diseño y 2,4 GHz)'},
                          ayuda='Dos bandas: añade el brazo de 2,4 GHz. Simulada con la baja en 868 MHz (J-pole: dos J-pole unidas; IFA: segunda rama); '
                                'la banda alta es siempre 2,4 GHz')] + PARAMS_MASA, 'largo_brazo',
               precision='±15 % (sin calibrar)'),
    TipoAntena('pifa', 'Antena PIFA (F invertida plana)',
               'Como la F invertida pero con el brazo y el cortocircuito anchos (placas): más banda y menos '
               'sensible a la masa.', 'monopolo',
               [Parametro('largo_brazo', 'Largo del brazo horizontal [mm]', 18, 3, 200, 0.1),
                Parametro('altura', 'Altura del brazo sobre la masa [mm]', 6, 1, 50, 0.1),
                Parametro('separacion_toma', 'Distancia entre el cortocircuito y la toma [mm]', 7, 1, 40, 0.1),
                Parametro('ancho_pista', 'Ancho del brazo [mm]', 7, 0.3, 20, 0.05),
                Parametro('ancho_corto', 'Ancho del cortocircuito [mm]', 4, 0.5, 20, 0.05)] + PARAMS_MASA, 'largo_brazo',
               precision='±20 % (sin calibrar)'),
    TipoAntena('dipolo_sleeve', 'Dipolo con manga (sleeve)',
               'Tira λ/4 arriba y manga λ/4 de masa debajo: un dipolo alimentado con la línea por dentro de la manga.', 'monopolo',
               [Parametro('alto', 'Largo de la tira [mm]', 23.6, 3, 200, 0.1),
                PISTA] + [
                Parametro('masa', 'Plano de masa', 0, 0, 3, 1, True, opciones=MODOS_MASA,
                          ayuda='Manual: la manga es la masa, de ancho y largo fijos; automática: λ/4'),
                Parametro('ancho_placa', 'Ancho de la manga [mm]', 16, 10, 400, 1),
                Parametro('largo_masa', 'Largo de la manga [mm]', 24, 10, 400, 1)], 'alto',
               precision='±15 % (sin calibrar)'),
    TipoAntena('parche_rectangular', 'Parche rectangular (referencia)',
               'Parche microstrip con transformador λ/4. Directivo (~6 dBi).', 'parche',
               [Parametro('largo', 'Largo L (resonante) [mm]', 29, 3, 200, 0.1),
                Parametro('ancho', 'Ancho W [mm]', 38, 3, 250, 0.1),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el transformador [mm]', 10, 2, 100, 0.5)]
               + PARAMS_MUESCA +
               [Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 15, 3, 100, 1)], 'largo',
               bandas=[2.4e9, 868e6], precision='±3–5 % (modelo de línea de transmisión)'),
    TipoAntena('parche_minkowski', 'Parche de Minkowski',
               'Parche cuadrado con bordes de Minkowski: más pequeño que el rectangular.', 'parche',
               [Parametro('largo', 'Lado (antes de las indentaciones) [mm]', 28, 3, 200, 0.1),
                Parametro('ancho', 'Ancho [mm] (igual al lado = cuadrado)', 28, 3, 250, 0.1),
                Parametro('iteracion', 'Iteración', 1, 0, 3, 1, True),
                Parametro('profundidad', 'Profundidad de la muesca (fracción del tercio)', 0.5, 0.1, 0.9, 0.05),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el transformador [mm]', 10, 2, 100, 0.5)]
               + PARAMS_MUESCA +
               [Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 15, 3, 100, 1)], 'largo',
               bandas=[2.4e9, 868e6]),
    TipoAntena('parche_circular', 'Parche de polarización circular (esquinas cortadas)',
               'Parche casi cuadrado con dos esquinas opuestas cortadas y una sola entrada: la polarización sale '
               'circular (GPS, Iridium) en teoría; en simulación no adapta ni da polarización circular.', 'parche',
               [Parametro('largo', 'Lado (largo resonante) [mm]', 28, 3, 200, 0.1),
                Parametro('ancho', 'Ancho [mm] (igual al lado = cuadrado)', 28, 3, 250, 0.1),
                Parametro('corte', 'Corte de las esquinas (fracción del lado)', 0.15, 0.03, 0.4, 0.01,
                          ayuda='Cateto del triángulo que se quita en dos esquinas opuestas; más corte, más separación de los dos modos'),
                Parametro('diagonal', 'Diagonal cortada', 0, 0, 1, 1, True,
                          opciones={0: 'Esquinas superior derecha e inferior izquierda', 1: 'Esquinas superior izquierda e inferior derecha'},
                          ayuda='Cambia el sentido de giro (derecho o izquierdo): hay que comprobarlo simulando'),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el transformador [mm]', 10, 2, 100, 0.5)]
               + PARAMS_MUESCA +
               [Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 15, 3, 100, 1)], 'largo',
               bandas=[1.575e9, 2.4e9], precision='±5–10 % (sin calibrar)'),
    TipoAntena('parche_ranura', 'Parche con ranura en U',
               'Parche rectangular con una ranura en U: más ancho de banda que el normal (hasta ~3 veces). '
               'Sin validar.', 'parche',
               [Parametro('largo', 'Largo L (resonante) [mm]', 29, 3, 200, 0.1),
                Parametro('ancho', 'Ancho W [mm]', 38, 3, 250, 0.1),
                Parametro('ranura_ancho', 'Ancho de la ranura (fracción del ancho)', 0.5, 0.2, 0.8, 0.01),
                Parametro('ranura_largo', 'Profundidad de la ranura (fracción del largo)', 0.4, 0.1, 0.7, 0.01),
                Parametro('ranura_hueco', 'Ancho de las rendijas de la ranura [mm]', 1.0, 0.3, 5, 0.1),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el transformador [mm]', 10, 2, 100, 0.5)]
               + PARAMS_MUESCA +
               [Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 15, 3, 100, 1)], 'largo',
               bandas=[2.4e9, 868e6], precision='±8 % (sin calibrar)'),
    TipoAntena('parche_apilado', 'Parche con parásito acoplado (alternativa plana al apilado)',
               'Parche con un segundo parche acoplado por el borde radiante, en la misma cara: más ancho de banda '
               'que el simple. Un apilado de verdad necesita una segunda placa. En simulación no adapta.', 'parche',
               [Parametro('largo', 'Largo L (resonante) [mm]', 29, 3, 200, 0.1),
                Parametro('ancho', 'Ancho W [mm]', 38, 3, 250, 0.1),
                Parametro('parasito_hueco', 'Hueco entre el parche y el parásito [mm]', 1.0, 0.3, 10, 0.1,
                          ayuda='Más hueco: acoplo más débil; menos: más acoplo y más banda'),
                Parametro('parasito_factor', 'Largo del parásito (fracción del largo)', 0.96, 0.8, 1.1, 0.01,
                          ayuda='Algo menor que 1: resuena un poco más arriba y ensancha la banda'),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el transformador [mm]', 10, 2, 100, 0.5)]
               + PARAMS_MUESCA +
               [Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 15, 3, 100, 1)], 'largo',
               bandas=[2.4e9, 868e6], precision='±8 % (sin calibrar)'),
    TipoAntena('yagi_koch', 'Quasi-Yagi impresa con dipolo de Koch (directiva)',
               'Dipolo (Koch o recto) alimentado por balun microstrip→CPS; la masa hace de reflector '
               'y 0–8 directores, cada uno algo más corto que el anterior. Ganancia ~4–11 dBi.', 'yagi',
               [Parametro('largo_brazo', 'Largo de cada brazo (entre extremos) [mm]', 16, 3, 200, 0.1),
                Parametro('iteracion', 'Iteración de Koch (0 = dipolo recto)', 2, 0, 3, 1, True),
                Parametro('angulo', 'Ángulo de la indentación [°]', 60, 20, 85, 1),
                Parametro('directores', 'Directores', 1, 0, 8, 1, True),
                Parametro('separacion_director', 'Separación entre dipolo/directores [mm]', 22, 3, 200, 0.5),
                Parametro('factor_director', 'Largo del 1.er director (fracción del dipolo)', 0.8, 0.4, 1.0, 0.01),
                Parametro('reduccion_director', 'Acortamiento de cada director siguiente', 0.03, 0.0, 0.15, 0.005,
                          ayuda='Cada director mide (1 − este valor) veces el anterior'),
                Parametro('ancho_pista', 'Ancho de pista de dipolo y directores [mm]', 1.0, 0.15, 15, 0.05),
                Parametro('ancho_rama', 'Ancho de las ramas del balun/CPS [mm]', 1.5, 0.3, 5, 0.05),
                Parametro('hueco_cps', 'Hueco de la línea de tiras (CPS) [mm]', 1.0, 0.15, 5, 0.05),
                Parametro('alto_cps', 'Largo de la CPS sobre la masa [mm]', 8, 1, 60, 0.5),
                Parametro('largo_balun', 'Distancia de la T al borde de masa [mm]', 10, 3, 60, 0.5),
                Parametro('ancho_rodeo', 'Ancho de los tramos del rodeo λ/2 [mm]', 5, 2, 30, 0.5),
                Parametro('masa', 'Plano de masa (reflector)', 1, 0, 1, 1, True,
                          opciones={0: 'Manual', 1: 'Automática (la mínima que cabe)'},
                          ayuda='Automática: reflector del ancho del dipolo y largo justo para el balun'),
                Parametro('ancho_placa', 'Ancho mínimo de la placa / reflector [mm]', 60, 20, 600, 1),
                Parametro('largo_masa', 'Largo del plano de masa [mm]', 25, 10, 400, 1)],
               'largo_brazo', escala_conjunta=('separacion_director',)),
    TipoAntena('yagi_boom', 'Yagi impresa de doble cara con boom (directiva)',
               'Microstrip por el boom; medio dipolo en cada cara (la línea hace de balun), reflector en la '
               'cara inferior unido a la masa y 0–8 directores, sueltos o unidos al boom. Elementos rectos o '
               'de Koch. Placa estrecha y larga; ganancia ~4,5–11 dBi.', 'yagi',
               [Parametro('largo_brazo', 'Largo de cada brazo del dipolo (entre extremos) [mm]', 24, 3, 300, 0.1),
                Parametro('iteracion', 'Iteración de Koch de los elementos (0 = rectos)', 0, 0, 3, 1, True),
                Parametro('angulo', 'Ángulo de la indentación [°]', 60, 20, 85, 1),
                Parametro('ancho_pista', 'Ancho de los elementos [mm]', 1.5, 0.15, 15, 0.05),
                Parametro('ancho_boom', 'Ancho de la tira de masa del boom [mm]', 8, 4, 30, 0.5),
                Parametro('largo_alimentacion', 'Del conector al reflector [mm]', 8, 4, 60, 0.5),
                Parametro('alimentacion', 'Alimentación del dipolo', 0, 0, 2, 1, True,
                          opciones={0: 'Directa (reflector lejos para adaptar)',
                                    1: 'Transformador λ/4 en el boom (en revisión: radiaba hacia atrás)',
                                    2: 'Dipolo plegado (×4 la impedancia, sin adaptador)'},
                          ayuda='Con parásitos cerca, el dipolo baja a ~10–15 Ω: el transformador o el plegado lo llevan a 50 Ω'),
                Parametro('z_transformador', 'Impedancia del transformador λ/4 [Ω]', 25, 12, 45, 0.5),
                Parametro('separacion_plegado', 'Separación entre los conductores del plegado [mm]', 3.0, 1.0, 30, 0.1,
                          ayuda='Distancia entre ejes del conductor partido y el entero'),
                Parametro('factor_reflector', 'Largo del reflector (fracción del dipolo)', 1.05, 0.9, 1.3, 0.01),
                Parametro('separacion_reflector', 'Separación reflector–dipolo [λ0]', 0.17, 0.05, 0.5, 0.005,
                          ayuda='Lo habitual es 0,15–0,25 λ0; en λ0 para que no encoja con los elementos de Koch'),
                Parametro('directores', 'Directores', 1, 0, 8, 1, True),
                Parametro('separacion_director', 'Separación entre dipolo/directores [λ0]', 0.15, 0.05, 0.5, 0.005),
                Parametro('factor_director', 'Largo del 1.er director (fracción del dipolo)', 0.9, 0.6, 1.0, 0.01),
                Parametro('reduccion_director', 'Acortamiento de cada director siguiente', 0.03, 0.0, 0.15, 0.005,
                          ayuda='Cada director mide (1 − este valor) veces el anterior'),
                Parametro('unir_boom', 'Directores unidos al boom', 0, 0, 1, 1, True,
                          opciones={0: 'Sueltos (cara superior)', 1: 'Unidos por una tira central (cara inferior)'},
                          ayuda='Unidos: toda la antena queda a masa en continua (protege de la estática)')],
               'largo_brazo'),
    TipoAntena('array_parches', 'Array de parches 2×2 / 4×4 (directivo)',
               'Parches rectangulares o de Minkowski con red corporativa en fase. '
               '2×2 ≈ 10–11 dBi y 4×4 ≈ 15–17 dBi ideales, menos las pérdidas de la red (se estiman).',
               'array',
               [Parametro('tamano', 'Tamaño (2 = 2×2, 4 = 4×4)', 2, 2, 4, 2, True),
                Parametro('elemento', 'Elemento (0 = rectangular, 1 = Minkowski)', 0, 0, 1, 1, True),
                Parametro('largo', 'Largo L de cada parche [mm]', 29, 3, 200, 0.1),
                Parametro('ancho', 'Ancho W de cada parche [mm]', 38, 3, 250, 0.1),
                Parametro('iteracion', 'Iteración de Minkowski', 1, 0, 3, 1, True),
                Parametro('profundidad', 'Profundidad de la muesca (fracción del tercio)', 0.5, 0.1, 0.9, 0.05),
                Parametro('separacion', 'Separación entre parches [λ0]', 0.75, 0.5, 1.0, 0.01),
                Parametro('bajada', 'Separación de la red al borde de los parches [mm]', 6.0, 1.0, 30, 0.5),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta el borde [mm]', 10, 2, 100, 0.5),
                Parametro('masa', 'Plano de masa', 1, 0, 1, 1, True, opciones={0: 'Manual (margen)', 1: 'Automática compacta (margen 6h)'}),
                Parametro('margen_masa', 'Margen de masa alrededor [mm]', 10, 3, 100, 1)], 'largo',
               bandas=[2.4e9, 868e6], precision='±3–5 % (rect.) / ±20 % (Minkowski)'),
    TipoAntena('panel_dipolos', 'Panel de dipolos 2×2 / 4×4 sobre reflector (directivo)',
               'Dipolos impresos (un brazo en cada cara) con red en H de tiras paralelas, sobre un reflector '
               'separado por aire (segunda placa o chapa). Coaxial por detrás, al centro. Haz hacia el lado '
               'contrario al reflector; 2×2 ≈ 12–13 dBi y 4×4 ≈ 16–17 dBi, menos las pérdidas de la red.',
               'panel',
               [Parametro('tamano', 'Tamaño (1 = un elemento, 2 = 2×2, 4 = 4×4)', 2, 1, 4, 1, True,
                          ayuda='1 = un solo elemento sobre el reflector (sin red); 3 no existe'),
                Parametro('elemento', 'Elemento', 0, 0, 2, 1, True,
                          opciones={0: 'Dipolo recto', 1: 'Bowtie (pajarita)', 2: 'Bowtie de Sierpinski'},
                          ayuda='Bowtie: más ancho de banda (tolera mejor los desajustes de εr y máscara). '
                                'Sin simular todavía'),
                Parametro('apertura', 'Apertura de la bowtie [°]', 70, 30, 120, 1,
                          ayuda='Ángulo total de cada triángulo (solo con bowtie)'),
                Parametro('iteracion_s', 'Iteración de Sierpinski', 2, 1, 4, 1, True,
                          ayuda='Solo con «Bowtie de Sierpinski»: huecos triangulares en el brazo'),
                Parametro('simetrico', 'Disposición de los dipolos', 1, 0, 1, 1, True,
                          opciones={0: 'Todos iguales (sin vías)', 1: 'Simétrica con cruce (2 vías por bloque)'},
                          ayuda='Todos iguales: el haz sale inclinado ~9° en el plano de los dipolos (2×2)'),
                Parametro('largo_brazo', 'Largo de cada brazo del dipolo [mm]', 23, 3, 300, 0.1),
                Parametro('ancho_dipolo', 'Ancho de los brazos [mm]', 3.0, 0.5, 30, 0.1,
                          ayuda='Más ancho: más ancho de banda (y dipolo algo más corto)'),
                Parametro('separacion', 'Separación entre dipolos [λ0]', 0.75, 0.55, 1.0, 0.01),
                Parametro('separacion_reflector', 'Separación placa–reflector [λ0]', 0.25, 0.1, 0.4, 0.005,
                          ayuda='Aire entre la cara inferior y el reflector; ajusta la impedancia'),
                Parametro('margen_reflector', 'Reflector más grande que la placa, por lado [λ0]', 0.2, 0.0, 1.0, 0.01),
                Parametro('reflector', 'Reflector', 1, 0, 1, 1, True,
                          opciones={0: 'Sin reflector (radia por las dos caras)', 1: 'Con reflector (directivo)'},
                          ayuda='Sin reflector el panel es bidireccional y no anula una segunda banda baja; sin validar'),
                Parametro('margen_placa', 'Margen de la placa alrededor del cobre [mm]', 8, 4, 50, 0.5,
                          ayuda='Deja sitio a los taladros M3 de las esquinas'),
                Parametro('taladro_coaxial', 'Taladro del coaxial en el centro [mm]', 1.7, 0.8, 4, 0.1,
                          ayuda='Pasa el dieléctrico; 1,7 mm para RG-316 / RG-174')],
               'largo_brazo'),
]}

_PARAMS_JPOLE = [
    Parametro('ancho_pista', 'Ancho de las pistas [mm]', 1.0, 0.2, 15, 0.05),
    Parametro('hueco', 'Hueco entre los brazos del adaptador [mm]', 1.0, 0.2, 40, 0.05),
    Parametro('toma', 'Altura de la toma (fracción del adaptador)', 0.2, 0.03, 0.9, 0.01,
              ayuda='Punto donde se suelda el coaxial; más arriba = más impedancia'),
    Parametro('factor_adaptador', 'Corrección del largo del adaptador', 1.0, 0.7, 1.3, 0.01,
              ayuda='El adaptador λ/4 se calcula solo; esto lo alarga o acorta'),
]
for _td in [
    TipoAntena('dipolo', 'Dipolo impreso (recto o de Koch)',
               'Dipolo de media onda, omnidireccional en el plano perpendicular a los brazos (~2 dBi). Con SMA y '
               'balun impreso (un brazo en cada cara) o con coaxial soldado al centro.', 'dipolo',
               [Parametro('largo_brazo', 'Largo de cada brazo (entre extremos) [mm]', 25, 3, 300, 0.1),
                Parametro('iteracion', 'Iteración de Koch (0 = recto)', 0, 0, 3, 1, True),

                Parametro('angulo', 'Ángulo de la indentación [°]', 60, 20, 85, 1),
                Parametro('ancho_pista', 'Ancho de los brazos [mm]', 1.5, 0.15, 15, 0.05),
                Parametro('alimentacion', 'Alimentación', 0, 0, 1, 1, True,
                          opciones={0: 'SMA con balun impreso (un brazo en cada cara)',
                                    1: 'Coaxial soldado al centro (una cara)'},
                          ayuda='Coaxial: vivo al brazo derecho, malla al izquierdo; con ferrita en el cable'),
                Parametro('hueco', 'Hueco central entre brazos (coaxial) [mm]', 1.0, 0.3, 10, 0.05),
                Parametro('largo_alimentacion', 'Largo del boom (balun) [mm]', 20, 4, 200, 0.5,
                          ayuda='Tira de masa bajo la línea: ~λg/4 hace de balun'),
                Parametro('ancho_boom', 'Ancho de la tira de masa del boom [mm]', 8, 4, 30, 0.5)],
               'largo_brazo'),
    TipoAntena('dipolo_bowtie', 'Dipolo bowtie (pajarita)',
               'Dipolo de media onda con brazos triangulares (o triángulos de Sierpinski): más ancho de banda que el '
               'recto y tolera mejor los desajustes de εr. Omnidireccional (~2 dBi). Con SMA y balun impreso o coaxial '
               'al centro.', 'dipolo',
               [Parametro('largo_brazo', 'Largo de cada brazo (entre extremos) [mm]', 25, 3, 300, 0.1),
                Parametro('forma', 'Forma de los brazos', 1, 1, 3, 1, True,
                          opciones={1: 'Bowtie (pajarita)', 2: 'Bowtie de Sierpinski', 3: 'Flecha de Sierpinski (curva)'},
                          ayuda='Bowtie: brazos triangulares; Sierpinski: triángulos con huecos fractales; Flecha: una sola pista fractal por brazo (curiosidad, sin validar)'),
                Parametro('ancho_flecha', 'Ancho de la pista de la flecha [mm]', 0.5, 0.15, 5, 0.05,
                          ayuda='Solo con «Flecha de Sierpinski»'),
                Parametro('apertura', 'Apertura de la bowtie [°]', 70, 30, 120, 1,
                          ayuda='Ángulo total de cada triángulo'),
                Parametro('iteracion_s', 'Iteración de Sierpinski', 2, 1, 5, 1, True,
                          ayuda='Con «Bowtie de Sierpinski»: huecos triangulares en el brazo; con «Flecha»: iteración de la curva (3 es un buen punto de partida)'),
                Parametro('ancho_pista', 'Ancho de la línea de alimentación [mm]', 1.5, 0.15, 15, 0.05),
                Parametro('alimentacion', 'Alimentación', 0, 0, 1, 1, True,
                          opciones={0: 'SMA con balun impreso (un brazo en cada cara)',
                                    1: 'Coaxial soldado al centro (una cara)'},
                          ayuda='Coaxial: vivo al brazo derecho, malla al izquierdo; con ferrita en el cable'),
                Parametro('hueco', 'Hueco central entre brazos (coaxial) [mm]', 1.0, 0.3, 10, 0.05),
                Parametro('largo_alimentacion', 'Largo del boom (balun) [mm]', 20, 4, 200, 0.5,
                          ayuda='Tira de masa bajo la línea: ~λg/4 hace de balun'),
                Parametro('ancho_boom', 'Ancho de la tira de masa del boom [mm]', 8, 4, 30, 0.5)],
               'largo_brazo'),
    TipoAntena('vivaldi', 'Vivaldi antipodal',
               'Dos aletas exponenciales, una en cada cara: banda ancha y directiva hacia la boca (~5–7 dBi). '
               'Grande a 868 MHz.', 'vivaldi',
               [Parametro('ancho_apertura', 'Ancho de la boca [mm]', 48, 8, 400, 0.5),
                Parametro('largo_aleta', 'Largo de las aletas [mm]', 55, 8, 500, 0.5),
                Parametro('tasa', 'Tasa de apertura exponencial', 3.0, 1.0, 8.0, 0.1,
                          ayuda='Más tasa: la aleta se abre más tarde y de golpe'),
                Parametro('abertura_interior', 'Separación entre aletas en la boca (fracción del ancho)', 0.15, 0.05, 0.5, 0.01),
                Parametro('largo_alimentacion', 'Línea de 50 Ω hasta las aletas [mm]', 10, 4, 100, 0.5),
                Parametro('ancho_boom', 'Ancho de la tira de masa bajo la línea [mm]', 8, 4, 30, 0.5)],
               'ancho_apertura', escala_conjunta=('largo_aleta',), precision='±25 % (sin calibrar)'),
    TipoAntena('colineal_dipolos', 'Colineal de dipolos en serie (línea microstrip)',
               'Varios dipolos en serie sobre una línea central: cada uno es una «U» en la cara de arriba (vivo) y una '
               '«U» invertida en la de abajo (malla), unidos por tramos de microstrip de λg que los ponen en fase. '
               'Más ganancia omnidireccional que un dipolo; placa larga. El coaxial se suelda en el arranque de la '
               'línea.', 'colineal',
               [Parametro('largo_brazo', 'Largo de cada pata de la U [mm]', 22, 3, 300, 0.1),
                Parametro('elementos', 'Número de dipolos', 4, 2, 10, 1, True),
                Parametro('separacion_patas', 'Distancia de las patas de la U al eje [mm]', 7, 2, 40, 0.1),
                Parametro('ancho_brazo', 'Ancho de las patas de la U [mm]', 2.5, 0.5, 15, 0.1),
                Parametro('factor_linea', 'Corrección del largo de los tramos de línea', 1.0, 0.7, 1.3, 0.01,
                          ayuda='Cada tramo mide λg (microstrip); esto lo alarga o acorta'),
                Parametro('largo_entrada', 'Línea de 50 Ω desde el conector al primer dipolo [mm]', 8, 4, 100, 0.5),
                Parametro('ancho_boom', 'Ancho de la tira de masa bajo la línea [mm]', 8, 4, 30, 0.5)],
               'largo_brazo', precision='±15 % (sin calibrar)'),
    TipoAntena('colineal_coco', 'Colineal coaxial impresa (COCO)',
               'Tramos de λg/2 de dos tiras superpuestas (una en cada cara) que se cruzan con vías en cada '
               'unión: todos radian en fase. Omnidireccional, ~5–8 dBi según los tramos; placa larga y estrecha. '
               'SMA en un extremo.', 'colineal',
               [Parametro('largo_seccion', 'Largo de cada tramo [mm]', 33, 5, 400, 0.1),
                Parametro('secciones', 'Número de tramos', 4, 2, 10, 1, True),
                Parametro('ancho_pista', 'Ancho de la tira estrecha (el «vivo») [mm]', 1.5, 0.3, 10, 0.05),
                Parametro('ancho_exterior', 'Ancho de la tira ancha (la «malla») [mm]', 6.0, 2, 30, 0.1,
                          ayuda='Debe ser bastante más ancha que la estrecha: con las dos iguales no radia'),
                Parametro('hueco', 'Hueco en cada cruce [mm]', 1.5, 0.5, 5, 0.1)],
               'largo_seccion'),
    TipoAntena('colineal_franklin', 'Colineal Franklin (horquillas)',
               'Monopolo λ/4 sobre masa seguido de elementos λ/2 unidos por horquillas de λ/4 que invierten '
               'la fase. Una sola cara; omnidireccional, ~4–6 dBi. Las horquillas ensanchan la placa.', 'colineal',
               [Parametro('largo_elemento', 'Largo de cada elemento λ/2 [mm]', 50, 5, 500, 0.1),
                Parametro('elementos', 'Elementos λ/2 sobre la base λ/4', 2, 1, 6, 1, True),
                Parametro('factor_horquilla', 'Corrección del largo de las horquillas', 1.0, 0.6, 1.4, 0.01,
                          ayuda='Cada rama mide λ/4 en tiras paralelas; esto la alarga o acorta'),
                Parametro('hueco_horquilla', 'Hueco entre las ramas de la horquilla [mm]', 1.0, 0.3, 10, 0.05),
                Parametro('ancho_pista', 'Ancho de la pista [mm]', 1.0, 0.2, 10, 0.05)] + PARAMS_MASA,
               'largo_elemento'),
]:
    CATALOGO[_td.clave] = _td

CATALOGO['bucle'] = TipoAntena(
    'bucle', 'Bucle impreso (pequeño, con condensador y red en π)',
    'Anillo de cobre alimentado por una línea microstrip, con un condensador de sintonía en el lado opuesto y el otro extremo '
    'a masa. Pequeño y poco sensible a lo que hay cerca, pero de banda estrecha y con una resistencia de entrada de pocos ohmios: '
    'necesita la red en π para adaptarse.', 'bucle',
    [Parametro('lado', 'Lado (o diámetro) del anillo [mm]', 9.0, 3, 80, 0.1,
               ayuda='Perímetro pequeño frente a λ (~λ/4): más pequeño, menos eficiencia y más estrecho'),
     Parametro('capacidad_pF', 'Condensador de sintonía [pF]', 0.2, 0.0, 100, 0.05,
               ayuda='En serie en el anillo (C0G/NP0 de Q alta). Con más capacidad el anillo resuena a menos frecuencia; la capacidad '
                     'parásita del hueco y los pads suma ~0,15 pF. «Ajustar tamaño a la frecuencia» elige este valor'),
     Parametro('forma', 'Forma del anillo', 0, 0, 1, 1, True, opciones={0: 'Cuadrada', 1: 'Redonda'},
               ayuda='El anillo redondo (diámetro = lado) tiene menos perímetro que el cuadrado: resuena más alto. Sin calibrar'),
     Parametro('ancho_pista', 'Ancho de la pista del anillo [mm]', 0.8, 0.2, 10, 0.05,
               ayuda='Más ancha: menos pérdida del cobre y menos inductancia'),
     Parametro('q_condensador', 'Q del condensador (pérdidas)', 250, 20, 2000, 10,
               ayuda='C0G/NP0 de 0402 a 1 GHz: 150–400. Solo afecta a la eficiencia de la simulación'),
     Parametro('ancho_placa', 'Ancho de la placa / plano de masa [mm]', 25, 10, 400, 1),
     Parametro('largo_masa', 'Largo del plano de masa [mm]', 16, 8, 400, 1)],
    'capacidad_pF', precision='±25 % (sin calibrar)')

for _tj in [
    TipoAntena('jpole', 'J-pole impresa',
               'Radiador λ/2 con adaptador λ/4 de tiras paralelas; sin plano de masa. Se alimenta con '
               'coaxial soldado en el punto de toma.', 'jpole',
               [Parametro('largo_radiador', 'Largo del radiador [mm]', 40, 5, 400, 0.1)] + _PARAMS_JPOLE +
               [Parametro('multibanda', 'Bandas', 0, 0, 1, 1, True,
                          opciones={0: 'Una banda', 1: 'Dos bandas (la baja del diseño y 2,4 GHz)'},
                          ayuda='Dos bandas: añade el brazo de 2,4 GHz. Simulada con la baja en 868 MHz (J-pole: dos J-pole unidas; IFA: segunda rama); '
                                'la banda alta es siempre 2,4 GHz')],
               'largo_radiador'),
    TipoAntena('jpole_koch', 'J-pole de Koch (fractal)',
               'J-pole con el radiador en curva de Koch: más corta para la misma frecuencia.', 'jpole',
               [Parametro('largo_radiador', 'Altura del radiador (entre extremos) [mm]', 30, 5, 400, 0.1),
                Parametro('iteracion', 'Iteración de Koch', 2, 1, 4, 1, True),
                Parametro('angulo', 'Ángulo de la indentación [°]', 60, 20, 85, 1)] + _PARAMS_JPOLE,
               'largo_radiador'),
]:
    CATALOGO[_tj.clave] = _tj


GRUPO_AJUSTE = {'monopolo_recto': 'monopolo_pista', 'monopolo_meandro': 'monopolo_pista',
                'monopolo_koch': 'monopolo_pista', 'monopolo_hilbert': 'monopolo_pista', 'monopolo_flecha': 'sin_ajuste',
                'monopolo_sierpinski': 'monopolo', 'jpole': 'jpole', 'jpole_koch': 'jpole', 'yagi_koch': 'yagi',
                'yagi_boom': 'sin_ajuste',
                'parche_rectangular': 'parche_rect', 'parche_minkowski': 'parche', 'parche_circular': 'sin_ajuste', 'parche_ranura': 'sin_ajuste', 'parche_apilado': 'sin_ajuste', 'ifa': 'sin_ajuste', 'pifa': 'sin_ajuste', 'dipolo_sleeve': 'sin_ajuste', 'vivaldi': 'sin_ajuste', 'colineal_dipolos': 'sin_ajuste', 'array_parches': 'array',
                'panel_dipolos': 'sin_ajuste', 'dipolo': 'sin_ajuste', 'dipolo_bowtie': 'sin_ajuste', 'colineal_coco': 'sin_ajuste',
                'colineal_franklin': 'sin_ajuste', 'bucle': 'bucle'}

# Medidas secundarias que escalan con λ0. Sus valores por defecto están pensados para F_REFERENCIA;
# con 'escalado' = 1, dimensionar las pone a defecto·λ0(f)/λ0(F_REFERENCIA). No se escalan: los
# parámetros fractales (iteración, ángulo, profundidad, orden, vueltas), los fijados por la
# impedancia con el grosor del FR4 (líneas de 50 Ω, transformadores, ramas del balun de la
# quasi-Yagi), los de fabricación o del conector (margen al borde, largo hasta el SMA) ni los
# ligados al grosor del sustrato (margen de masa de los parches, bajada de la red del array).
# Escalar las pistas también acelera la simulación a baja frecuencia: la malla la fija la pista
# más estrecha y el paso de tiempo, la celda más pequeña.
F_REFERENCIA = 2441.75e6
_MASA = ('ancho_placa', 'largo_masa')
ESCALABLES = {
    'monopolo_recto': ('ancho_pista',) + _MASA,
    'monopolo_meandro': ('ancho_pista', 'tramo_inicial') + _MASA,
    'monopolo_koch': ('ancho_pista',) + _MASA,
    'monopolo_flecha': _MASA,           # la pista va con la base (escala_conjunta)
    'monopolo_hilbert': _MASA,          # pista y separación van con el lado (escala_conjunta), no con λ
    'monopolo_sierpinski': ('cuello',) + _MASA,
    'parche_rectangular': ('largo_alimentacion',),
    'parche_minkowski': ('largo_alimentacion',),
    'parche_circular': ('largo_alimentacion',),
    'parche_ranura': ('largo_alimentacion', 'ranura_hueco'),
    'parche_apilado': ('largo_alimentacion', 'parasito_hueco'),
    'ifa': ('ancho_pista', 'ancho_corto', 'altura', 'separacion_toma') + _MASA,
    'pifa': ('ancho_pista', 'ancho_corto', 'altura', 'separacion_toma') + _MASA,
    'dipolo_sleeve': ('ancho_pista',) + _MASA,
    'vivaldi': ('largo_alimentacion',),
    'colineal_dipolos': ('ancho_brazo', 'largo_entrada', 'separacion_patas'),
    'yagi_koch': ('ancho_pista', 'alto_cps', 'largo_balun', 'ancho_rodeo') + _MASA,
    'yagi_boom': ('ancho_pista', 'separacion_plegado'),
    'array_parches': ('largo_alimentacion',),
    'panel_dipolos': ('ancho_dipolo',),
    'jpole':('ancho_pista', 'hueco'),
    'jpole_koch': ('ancho_pista', 'hueco'),
    # el boom del dipolo es su balun (~λg/4); su ancho y las tiras del COCO van con el grosor del FR4
    'dipolo': ('ancho_pista', 'hueco', 'largo_alimentacion'),
    'dipolo_bowtie': ('ancho_pista', 'hueco', 'largo_alimentacion', 'ancho_flecha'),
    'colineal_franklin': ('ancho_pista', 'hueco_horquilla') + _MASA,
    'bucle': ('lado', 'ancho_pista') + _MASA,
}
PARAM_ESCALADO = Parametro('escalado', 'Medidas secundarias (pistas, huecos, masa…)', 1, 0, 1, 1, True,
                           opciones={0: 'Manuales', 1: 'Proporcionales a λ (referencia 2,4 GHz)'},
                           ayuda='Al ajustar a otra frecuencia, las pistas, huecos y demás medidas se escalan '
                                 'con la longitud de onda: el diseño se mantiene y la simulación es más rápida')


def escalar_secundarios(clave, p, f_obj):
    """Pone las medidas de ESCALABLES[clave] a su valor por defecto escalado con λ0 (en el sitio)."""
    k = F_REFERENCIA/f_obj
    for par in CATALOGO[clave].parametros:
        if par.nombre in ESCALABLES.get(clave, ()):
            p[par.nombre] = round(min(max(par.defecto*k, par.minimo), par.maximo), 2)
    return p


for _t in CATALOGO.values():
    # Forma de la placa: los monopolos y la Yagi usan además el margen al borde; en parches y
    # arrays el borde lo fija el margen de masa
    _t.parametros = _t.parametros + (PARAMS_CONTORNO if _t.familia in ('monopolo', 'yagi', 'jpole', 'dipolo', 'colineal', 'vivaldi', 'bucle')
                                     else [] if _t.familia == 'panel'      # rectangular, con los taladros
                                     else PARAMS_CONTORNO[:1]) + [PARAM_ESCALADO]
    # J-pole y panel van con coaxial soldado; la COCO, con SMA (el IPEX no encaja con sus dos tiras)
    if _t.familia not in ('jpole', 'panel') and _t.clave != 'colineal_coco':
        _t.parametros = _t.parametros + [PARAM_CONECTOR]
    _t.parametros = _t.parametros + ajuste.parametros_para(GRUPO_AJUSTE[_t.clave])
    if _t.familia in ('yagi', 'panel'):
        _t.parametros = _t.parametros + PARAMS_ALIGERADO
    if _t.clave in integracion.TIPOS:
        _t.parametros = _t.parametros + integracion.PARAMETROS
# el bucle sin red en π casi no adapta (R de entrada de pocos ohmios): sale con el ajuste y la red activados
CATALOGO['bucle'].parametros = [replace(q, defecto=1) if q.nombre == 'ajuste' else q for q in CATALOGO['bucle'].parametros]


def _marcar_integrada(a, p):
    """Datos de la placa anfitriona en `info` y avisos de una antena integrada."""
    x0, y0, x1, y1 = a.zona_libre.bounds
    a.info['integrada'] = True
    a.info['zona_antena_mm'] = [round(x1 - x0, 2), round(y1 - y0, 2)]
    a.info['posicion_antena'] = integracion.POSICIONES[int(p.get('posicion', 0))]


def _aligerar(a, p):
    """Abre en el contorno las ventanas de `geometria.ventanas_aligerado` (lejos del cobre de las dos caras,
    de los taladros y del conector). La simulación pone aire en ellas y la exportación las fresa."""
    evitar = list(a.taladros)
    if a.puerto.get('tipo') == 'pasante':
        evitar.append((*a.puerto['alimentacion'], a.puerto.get('taladro_mm', 2.0)))
    bx, by = a.puerto['borde']
    evitar.append((bx, by, 16.0))                       # el SMA y su soldadura
    cobre = unary_union([a.cobre('F.Cu'), a.cobre('B.Cu')])
    ventanas = g.ventanas_aligerado(a.contorno, cobre, p['margen_aligerado'], p['nervio'], evitar)
    if ventanas:
        antes = a.contorno.area
        a.contorno = a.contorno.difference(unary_union(ventanas))
        a.info['ventanas_aligerado'] = len(ventanas)
        a.info['fr4_quitado_%'] = round(100*(1 - a.contorno.area/antes), 1)
    else:
        a.info.setdefault('avisos', []).append(tr('Recortes: no cabe ninguna ventana con ese margen y ese nervio.'))


def sustrato(nombre=None):
    return SUSTRATOS[nombre or SUSTRATO_POR_DEFECTO]


def generar(clave, parametros=None, nombre_sustrato=None):
    tipo = CATALOGO[clave]
    p = tipo.defectos()
    p.update(parametros or {})
    s = sustrato(nombre_sustrato)
    if tipo.familia == 'monopolo':
        a = _generar_monopolo(tipo, p, s)
        if clave in ('ifa', 'pifa'):
            lg = largo_masa_monopolo(p, _longitud_equivalente(clave, p), clave)
            a.vias = [(-p['separacion_toma'], lg - PROFUNDIDAD_CORTO/2)]
            if clave == 'ifa' and int(p.get('multibanda', 0) or 0) == 1:
                bibanda.ifa_dos_ramas(a, p, a.puerto['alimentacion'][1])
        if integracion.activa(p, clave):
            _marcar_integrada(a, p)
    elif clave == 'yagi_boom':
        a = directivas.generar_yagi_boom(p, s, eps_eff_monopolo(s.er))
    elif clave == 'panel_dipolos':
        a = directivas.generar_panel_dipolos(p, s, eps_eff_monopolo(s.er))
    elif tipo.familia == 'yagi':
        a = directivas.generar_yagi(p, s, eps_eff_monopolo(s.er))
    elif tipo.familia == 'bucle':
        a = bucle.generar(p, s, clave)
    elif tipo.familia == 'jpole':
        a = jpole.generar(dict(p, _clave=clave), s, eps_eff_monopolo(s.er))
        if clave == 'jpole' and int(p.get('multibanda', 0) or 0) == 1:
            bibanda.jpole_unida(a, p)
    elif clave in ('dipolo', 'dipolo_bowtie'):
        a = dipolos.generar_dipolo(p, s, eps_eff_monopolo(s.er))
    elif clave == 'vivaldi':
        a = dipolos.generar_vivaldi(p, s, eps_eff_monopolo(s.er))
    elif clave == 'colineal_dipolos':
        a = dipolos.generar_colineal_dipolos(p, s, eps_eff_monopolo(s.er))
    elif clave == 'colineal_coco':
        a = dipolos.generar_colineal_coco(p, s)
    elif clave == 'colineal_franklin':
        a = dipolos.generar_colineal_franklin(p, s, eps_eff_monopolo(s.er),
                                              largo_masa_monopolo(p, p['largo_elemento']/2))
    elif tipo.familia == 'array':
        mink = int(p['elemento']) == 1
        f_el = _f_parche(tipo, p, s)
        R = _parche_rectangular_dims(f_el, s)[4]
        a = directivas.generar_array(p, s, lambda: poligono_parche(mink, p), f_el, R)
    else:
        a = _generar_parche(tipo, p, s)
    if int(p.get('aligerado', 0)) == 1:
        _aligerar(a, p)
    if conector.tipo(p) == conector.IPEX and a.puerto.get('tipo') not in ('coaxial', 'pasante'):
        conector.aplicar_ipex(a, ancho_microstrip(50, s.er, s.h))
    elif conector.tipo(p) == conector.COAX and a.puerto.get('tipo') not in ('coaxial', 'pasante'):
        a.puerto['conector'] = conector.COAX
    elif conector.tipo(p) == conector.PAD_RF and a.puerto.get('tipo') not in ('coaxial', 'pasante'):
        a.puerto['conector'] = conector.PAD_RF       # el cobre es el de la línea de 50 Ω hasta el borde; el pad y las vías se añaden al exportar
    f_est = estimar_f(clave, p, nombre_sustrato)
    a.info['f_estimada_MHz'] = round(f_est/1e6, 1)
    a.info['precision_estimacion'] = precision_estimacion(clave, p)
    bw = ancho_banda.estimar(a, f_est, s)
    a.info['ancho_banda_estimado'] = {'f_inf_MHz': round(bw['f_lo']/1e6, 1), 'f_sup_MHz': round(bw['f_hi']/1e6, 1),
                                      'MHz': round((bw['f_hi'] - bw['f_lo'])/1e6, 1),
                                      'porcentaje': round(100*bw['fbw'], 1)}
    a.info['sustrato'] = s.nombre
    return a


MARGEN_BW = 1.5      # el ancho de banda estimado debe superar en este factor al necesario
                     # (tolerancias de εr, grosor y la propia estimación)


def _largo_parche_para(f_obj, p, clave, nombre_sustrato):
    """Largo L que da f_obj manteniendo el ancho W (bisección sobre el modelo)."""
    lo, hi = 3.0, 300.0
    for _ in range(60):
        mid = (lo + hi)/2
        if estimar_f(clave, dict(p, largo=mid), nombre_sustrato) > f_obj:
            lo = mid
        else:
            hi = mid
    return round((lo + hi)/2, 2)


def ajustar_ancho_banda(clave, f_obj, bw_necesario, parametros=None, nombre_sustrato=None):
    """Intenta que el ancho de banda estimado cubra bw_necesario (Hz) con margen MARGEN_BW.

    Monopolos/Yagi: ensancha la pista. Parches/arrays rectangulares: ensancha el parche
    (hasta 1,5 × el ancho óptimo). Siempre manteniendo la resonancia en f_obj.
    Devuelve (parámetros, mensaje).
    """
    tipo = CATALOGO[clave]
    p = dimensionar(clave, f_obj, parametros, nombre_sustrato)
    p.pop('_aviso', None)
    s = sustrato(nombre_sustrato)
    objetivo = MARGEN_BW*bw_necesario/f_obj

    def bw_de(q):
        a = generar(clave, q, nombre_sustrato)
        return ancho_banda.estimar(a, estimar_f(clave, q, nombre_sustrato), s)['fbw'], a

    fbw, a = bw_de(p)
    if fbw >= objetivo:
        return p, tr('Ya cubre la banda: {0:.1f} % estimado frente a {1:.1f} % necesario (con margen).', 100*fbw, 100*objetivo)
    candidatos = []
    if 'ancho_pista' in p:
        w0 = p['ancho_pista']
        candidatos = [('ancho_pista', round(w, 2)) for w in [w0*1.25**k for k in range(1, 12)] if w <= 5.0]
    elif clave == 'panel_dipolos':
        w0 = p['ancho_dipolo']
        candidatos = [('ancho_dipolo', round(w, 2)) for w in [w0*1.25**k for k in range(1, 10)] if w <= 15.0]
    elif clave == 'parche_rectangular' or (clave == 'array_parches' and int(p['elemento']) == 0):
        w0 = p['ancho']
        candidatos = [('ancho', round(w0*(1 + 0.05*k), 2)) for k in range(1, 11)]
    mejor = (fbw, p)
    for nombre, valor in candidatos:
        q = dict(p, **{nombre: valor})
        if nombre == 'ancho':
            q['largo'] = _largo_parche_para(f_obj, q, clave, nombre_sustrato)
        else:
            q = dimensionar(clave, f_obj, q, nombre_sustrato)
            q.pop('_aviso', None)
        fq, aq = bw_de(q)
        if (aq.info.get('solape_pistas') or 0) > 0.08:
            break                      # la pista ya no cabe sin pisarse
        if fq > mejor[0]:
            mejor = (fq, q)
        if fq >= objetivo:
            return q, (tr('Ancho de banda ampliado a {0:.1f} % ({1} = {2} mm), necesario {3:.1f} % con margen.', 100*fq, nombre.replace("_", " "), valor, 100*objetivo))
    fbw, q = mejor
    consejo = {'monopolo': tr('baja la iteración/orden, usa la masa λ/4 o un radiador más ancho (Sierpinski)'),
               'yagi': tr('usa dipolo recto (iteración 0) o menos directores'),
               'panel': tr('ensancha los brazos de los dipolos o separa más el reflector'),
               'parche': tr('usa un sustrato más grueso (o con menos εr, como RO4350B)'),
               'array': tr('usa un sustrato más grueso (o con menos εr, como RO4350B)'),
               'dipolo': tr('usa brazos rectos (iteración 0) o más anchos'),
               'vivaldi': tr('abre más la boca o alarga las aletas'),
               'colineal': tr('usa menos tramos o elementos (la banda se estrecha al añadirlos)')}[tipo.familia]
    if clave == 'parche_minkowski' or (clave == 'array_parches' and int(p['elemento']) == 1):
        consejo += ', o parches rectangulares (las muescas estrechan la banda)'
    return q, (tr('No llega: {0:.1f} % estimado frente a {1:.1f} % necesario (con margen). Para ganar ancho de banda: {2}.', 100*fbw, 100*objetivo, consejo))


RUTA_CALIBRACION = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calibracion_estimaciones.json')


def _cargar_calibracion():
    try:
        with open(RUTA_CALIBRACION, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


CALIBRACION = _cargar_calibracion()


def clave_calibracion(clave, p):
    """En los tipos con iteración fractal se calibra cada iteración aparte: la geometría cambia mucho
    (el Minkowski de iteración 1 sale un 5 % bajo y el de iteración 3, un 38 % alto)."""
    if p is not None and 'iteracion' in p:
        return f"{clave}@it{int(p['iteracion'])}"
    return clave


def factor_calibracion(clave, f_hz, p=None):
    """f_simulada/f_fórmula del tipo a la frecuencia f (interpolado en log f entre las bandas con
    datos; fuera de ellas, el de la banda más cercana). 1 si no hay simulaciones de ese tipo (e
    iteración)."""
    c = CALIBRACION.get(clave_calibracion(clave, p))
    if not c:
        return 1.0
    puntos = sorted(c['puntos'])                       # [[f_MHz, factor], ...]
    x = math.log(f_hz/1e6)
    if x <= math.log(puntos[0][0]):
        return puntos[0][1]
    for (f0, k0), (f1, k1) in zip(puntos, puntos[1:]):
        if x <= math.log(f1):
            t = (x - math.log(f0))/(math.log(f1) - math.log(f0))
            return k0 + t*(k1 - k0)
    return puntos[-1][1]


def precision_estimacion(clave, p=None):
    c = CALIBRACION.get(clave_calibracion(clave, p))
    if not c:
        return CATALOGO[clave].precision
    if c.get('dispersion_%') is None:
        return tr('calibrada con {0} simulación{1} (sin datos de dispersión)', c['n'], 'es' if c['n'] > 1 else '')
    return tr('±{0:.0f} % (calibrada con {1} simulaciones)', max(c['dispersion_%'], 1.0), c['n'])


def estimar_f(clave, parametros, nombre_sustrato=None, calibrada=True):
    """Frecuencia de resonancia estimada; calibrada=False da la de la fórmula sola."""
    tipo = CATALOGO[clave]
    p = tipo.defectos()
    p.update(parametros or {})
    s = sustrato(nombre_sustrato)
    if clave in ('jpole', 'ifa') and int(p.get('multibanda', 0) or 0) == 1:
        # dos bandas: la banda baja sale de las simulaciones de antenas/bibanda.py (con la calibración de una banda saldría
        # un 10 % alta en la J-pole y un 11 % baja en la IFA, que lleva el brazo alargado)
        if clave == 'jpole':
            return bibanda.F_BAJA_REF*1e6*bibanda.JPOLE_RADIADOR_REF/p['largo_radiador']
        return estimar_f(clave, dict(p, multibanda=0, largo_brazo=p['largo_brazo']/bibanda.IFA_X_BRAZO), nombre_sustrato, calibrada)
    if tipo.familia == 'monopolo':
        f = _f_monopolo(tipo, p, s)
    elif clave == 'yagi_boom':
        f = directivas.estimar_f_yagi_boom(p, eps_eff_monopolo(s.er))
    elif clave == 'panel_dipolos':
        f = directivas.estimar_f_panel(p, eps_eff_monopolo(s.er))
    elif tipo.familia == 'yagi':
        f = directivas.estimar_f_yagi(p, eps_eff_monopolo(s.er))
    elif tipo.familia == 'bucle':
        f = bucle.estimar_f(p)
    elif tipo.familia == 'jpole':
        f = jpole.estimar_f(p, eps_eff_monopolo(s.er))
    elif clave in ('dipolo', 'dipolo_bowtie'):
        f = dipolos.estimar_f_dipolo(p, eps_eff_monopolo(s.er))
    elif clave == 'vivaldi':
        f = dipolos.estimar_f_vivaldi(p, eps_eff_monopolo(s.er))
    elif clave == 'colineal_dipolos':
        f = dipolos.estimar_f_colineal_dipolos(p, eps_eff_monopolo(s.er))
    elif clave == 'colineal_coco':
        f = dipolos.estimar_f_coco(p, s)
    elif clave == 'colineal_franklin':
        f = dipolos.estimar_f_franklin(p, eps_eff_monopolo(s.er))
    else:
        f = _f_parche(tipo, p, s)
    return f*factor_calibracion(clave, f, p) if calibrada else f


def dimensionar(clave, f_obj, parametros=None, nombre_sustrato=None, fijos=()):
    """Ajusta el parámetro de escala del tipo para que la estimación dé f_obj.

    En los parches cuadrados (Minkowski con ancho = largo) se escalan los dos.
    fijos: parámetros que el escalado con λ no toca (los que el usuario ya fijó: `simulacion.ajustar`
    pasa todos los recibidos, para no deshacer una masa manual de la interfaz o de un lote).
    """
    tipo = CATALOGO[clave]
    p = tipo.defectos()
    p.update(parametros or {})
    s = sustrato(nombre_sustrato)
    if int(p.get('escalado', 0)) == 1:
        guardados = {k: p[k] for k in fijos if k in p}
        escalar_secundarios(clave, p, f_obj)
        p.update(guardados)
    if clave in ('parche_rectangular', 'parche_ranura', 'parche_apilado') or (clave == 'array_parches' and int(p['elemento']) == 0):
        # si la simulación da f = k·f_fórmula, se diseña para f_obj/k
        W, L, *_ = _parche_rectangular_dims(f_obj/factor_calibracion(clave, f_obj, p), s)
        p['ancho'], p['largo'] = round(W, 2), round(L, 2)
        return p
    cuadrado = clave in ('parche_minkowski', 'parche_circular', 'array_parches') and abs(p['ancho'] - p['largo']) < 1e-6
    par = next(q for q in tipo.parametros if q.nombre == tipo.escala)
    proporciones = {k: p[k]/p[tipo.escala] for k in tipo.escala_conjunta}

    def con_escala(x):
        q = dict(p, **{tipo.escala: x})
        for k, r in proporciones.items():
            q[k] = r*x
        if cuadrado:
            q['ancho'] = x
        return q

    lo, hi = par.minimo, par.maximo
    for _ in range(60):                    # la frecuencia baja al crecer la escala
        mid = (lo + hi)/2
        if estimar_f(clave, con_escala(mid), nombre_sustrato) > f_obj:
            lo = mid
        else:
            hi = mid
    p = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in con_escala((lo + hi)/2).items()}
    f_conseguida = estimar_f(clave, p, nombre_sustrato)
    if abs(f_conseguida - f_obj)/f_obj > 0.01:
        p['_aviso'] = (tr('No se alcanza {0:.0f} MHz dentro de los límites de "{1}" (queda en {2:.0f} MHz): cambia otros parámetros.', f_obj/1e6, par.etiqueta, f_conseguida/1e6))
    return p


# Sierpinski de dos bandas: con apertura 85° e iteración 2 la segunda resonancia cae a ~3× la primera. Simulado (06-11,
# FR4 1,6 mm, sin centrar) con la banda alta en 2400–2483,5 MHz y la baja en:
#   868–870 MHz: altura 50,17 mm -> S11 −13,0 y −11,6 dB (malla de 0,7 mm)
#   902–928 MHz y 863–928 MHz: altura 49,7 mm -> S11 −10,0 y −9,7 dB
# Fuera de esas bandas se escala el tamaño de una banda con k_alto (sin simular).
MULTIBANDA_SIERPINSKI = {'apertura': 85, 'iteracion': 2, 'k_alto': 0.98}
MULTIBANDA_ALTURAS = ((860e6, 880e6, 50.17), (880e6, 930e6, 49.7))        # (f_min, f_max, altura [mm]) simuladas
_dimensionar_una_banda = dimensionar

# J-pole recta (08-11, GPU): con el hueco pequeño de antes (1 mm a 2,4 GHz) adapta mal (−7 dB); con un hueco mayor y la toma al 26 %
# del adaptador sí. Multiplicador del hueco que sale de ESCALABLES (1 mm a 2,4 GHz, escalado con λ), simulado y centrado:
#   868 MHz: ×5 (14,1 mm) -> S11 −12,9 dB, η 92 %, banda 841–879 MHz;  2,4 GHz: ×6 (6,0 mm) -> −10,9 dB, η 85 %, 2375–2491 MHz.
# Entre las dos se interpola en log f; fuera de ellas se usa el de la banda más cercana (1,2 GHz da −9,8 dB como mucho y
# 5,8 GHz no adapta). El largo del radiador sale de la calibración de `calibracion_estimaciones.json` con estos huecos.
JPOLE_HUECO = ((868e6, 5.0), (2441.75e6, 6.0))
JPOLE_TOMA = 0.26


def _multiplicador_hueco_jpole(f_obj):
    (f0, k0), (f1, k1) = JPOLE_HUECO
    if f_obj <= f0:
        return k0
    if f_obj >= f1:
        return k1
    t = (math.log(f_obj) - math.log(f0))/(math.log(f1) - math.log(f0))
    return k0 + t*(k1 - k0)


def dimensionar(clave, f_obj, parametros=None, nombre_sustrato=None, fijos=()):
    """Ver `_dimensionar_una_banda`. El Sierpinski de dos bandas se ajusta a la banda baja con la apertura y la
    iteración fijas de MULTIBANDA_SIERPINSKI."""
    if clave == 'monopolo_sierpinski' and int((parametros or {}).get('multibanda', 0) or 0) == 1:
        q = dict(parametros, apertura=MULTIBANDA_SIERPINSKI['apertura'], iteracion=MULTIBANDA_SIERPINSKI['iteracion'])
        p = _dimensionar_una_banda(clave, f_obj, q, nombre_sustrato, fijos=tuple(fijos) + ('apertura', 'iteracion'))
        aviso = p.pop('_aviso', None)
        p['alto'] = round(MULTIBANDA_SIERPINSKI['k_alto']*p['alto'], 2)
        for f_min, f_max, alto in MULTIBANDA_ALTURAS:
            if f_min <= f_obj < f_max:
                p['alto'] = alto
        if aviso is not None:
            p['_aviso'] = aviso
        return p
    dos = clave in ('jpole', 'ifa') and int((parametros or {}).get('multibanda', 0) or 0) == 1
    # el tamaño de partida, el de una banda (la estimación de dos bandas ya incluye el alargado de la IFA)
    p = _dimensionar_una_banda(clave, f_obj, dict(parametros, multibanda=0) if dos else parametros, nombre_sustrato, fijos=fijos)
    if clave == 'bucle' and 'capacidad_pF' not in fijos and p['capacidad_pF'] < bucle.C_MINIMA_MONTADO_PF:
        # un anillo tan pequeño no lleva condensador (menos de 0,1 pF no existe): basta el hueco y se afina con el lado
        p['capacidad_pF'] = 0.0
        par_lado = next(q for q in CATALOGO['bucle'].parametros if q.nombre == 'lado')
        lo, hi = par_lado.minimo, par_lado.maximo
        for _ in range(60):                                 # la frecuencia baja al crecer el lado
            mid = (lo + hi)/2
            if estimar_f('bucle', dict(p, lado=mid), nombre_sustrato) > f_obj:
                lo = mid
            else:
                hi = mid
        p['lado'] = round((lo + hi)/2, 2)
    if dos:
        p['multibanda'] = 1
    if dos and int(p.get('escalado', 0)) == 1:
        # dos bandas: medidas de las pruebas bibanda (antenas/bibanda.py), escaladas con λ desde 868 MHz
        if clave == 'jpole':
            esc = p['ancho_pista']/bibanda.ANCHO_REF
            for k, v in (('largo_radiador', round(bibanda.JPOLE_RADIADOR_REF*esc, 2)), ('hueco', p['ancho_pista']),
                         ('toma', bibanda.JPOLE_TOMA), ('factor_adaptador', bibanda.JPOLE_FACTOR_ADAPTADOR)):
                if k not in fijos:
                    p[k] = v
        elif 'largo_brazo' not in fijos:
            p['largo_brazo'] = round(p['largo_brazo']*bibanda.IFA_X_BRAZO, 2)
        return p
    if clave == 'jpole' and int(p.get('escalado', 0)) == 1:
        # hueco y toma de la J-pole recta calibrados por simulación; lo que el usuario fija (`fijos`) no se toca
        par = next(q for q in CATALOGO['jpole'].parametros if q.nombre == 'hueco')
        if 'hueco' not in fijos:
            p['hueco'] = round(min(max(p['hueco']*_multiplicador_hueco_jpole(f_obj), par.minimo), par.maximo), 2)
        if 'toma' not in fijos:
            p['toma'] = JPOLE_TOMA
    return p
