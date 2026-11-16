"""Antenas de varias placas no coplanares y hélices de flex (sin validar).

  - Dipolo en V (`diedro`): el dipolo bowtie antipodal con los dos brazos doblados hacia arriba un ángulo β respecto a la placa central (que lleva
    el SMA, la línea y el balun). Tres placas: la central y un ala por brazo, que se sueldan en la bisagra. Cambia el diagrama del dipolo: más ancho
    en el plano de la V y algo de directividad hacia el lado en que se cierra.
  - Reflector de esquina (`reflector_esquina`): un dipolo bowtie delante de dos placas reflectoras unidas por el vértice (ángulo `apertura_diedro`),
    con el dipolo en el plano bisector. Ganancia de ~9–11 dBi sin red de alimentación. El vértice va truncado: las placas empiezan a `h + 1 mm`
    del plano de la placa del dipolo para que pase su línea de alimentación. Las placas reflectoras son FR4 con cobre en las dos caras.
  - Hélice de modo normal (`helice_normal`): monopolo helicoidal de λ/4 de hilo sobre una placa de masa con SMA; el hilo se imprime como
    una tira de flex de π·D de ancho (rayas diagonales) que se enrolla en un cilindro.
  - Hélice cuadrifilar (`helice_cuadrifilar`): cuatro brazos de λ/4 en una tira de flex enrollada (GPS L1, polarización circular). Solo geometría,
    vista 3D y tira para fabricar: la alimentación en cuadratura necesita dos puertos (`herramientas/helice_flex.py` la simula así) y no entra en
    el simulador de la interfaz.

Las placas fuera del plano de la principal van en `Antena.placas3d` (con su pose, ver `pose.py`) y las placas a fabricar en `Antena.modulos`.
Todo está sin simular ni medir.
"""
import math

import numpy as np
from dataclasses import replace
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import geometria as g
from . import ajuste, conector
from .materiales import C0, ancho_microstrip
from .modelo import Antena
from .i18n import tr

BORDE_COBRE = 0.5
INSET_UNION = 0.5          # el cobre se queda a esta distancia de un canto de unión al fabricar (mínimo de KiCad)
K_HELICE_NORMAL = 1.0      # f = K·c/(4·L hilo): sin calibrar
K_QHA = 1.0                # f = K·c/(4·L brazo): sin calibrar


# ------------------------------------------------------------------ utilidades
def _info(contorno, extra):
    x0, y0, x1, y1 = contorno.bounds
    extra.update({'placa_mm': [round(x1 - x0, 2), round(y1 - y0, 2)], 'area_placa_cm2': round(contorno.area/100, 2)})
    return extra


def _placa_plana(tipo, p, contorno, f_cu, b_cu, nombre_borde=(0.0, 0.0), conector_sin=True, info=None):
    """Una placa plana a fabricar (sin conector si `conector_sin`): contorno y cobre de cada cara."""
    x0, y0, x1, y1 = contorno.bounds
    puerto = {'borde': nombre_borde, 'direccion': (0, 1), 'alimentacion': ((x0 + x1)/2, (y0 + y1)/2), 'ancho_linea': 1.0}
    if conector_sin:
        puerto['conector'] = conector.SIN
    return Antena(tipo=tipo, parametros=dict(p), capas={'F.Cu': f_cu, 'B.Cu': b_cu}, ajuste=ajuste.vacio(), radiador=f_cu,
                  contorno=contorno, zona_libre=contorno, puerto=puerto, info=_info(contorno, dict(info or {}, avisos=[], f_sin_cortar_MHz=None, ajuste=None)))


def _dipolo_base(p, s, eps):
    """El dipolo bowtie antipodal de `dipolos.generar_dipolo` con los parámetros que comparten estos tipos."""
    from . import tipos, dipolos
    q = tipos.CATALOGO['dipolo_bowtie'].defectos()
    for k in ('largo_brazo', 'apertura', 'ancho_pista', 'largo_alimentacion', 'ancho_boom', 'conector', 'contorno', 'margen_borde',
              'iteracion_s', 'forma'):
        if k in p:
            q[k] = p[k]
    q['forma'] = 2 if int(p.get('forma', 1)) == 2 else 1
    q['alimentacion'] = 0
    return dipolos.generar_dipolo(q, s, eps), q


def _tramo(base, x0, x1, desp, inset=(0.0, 0.0)):
    """Parte de una placa plana entre x0 y x1 (en su sistema), desplazada `desp` en x. `inset` = separación del cobre a cada corte (fabricar)."""
    caja = g.rectangulo(x0, -1e4, x1, 1e4)
    interior = g.rectangulo(x0 + inset[0], -1e4, x1 - inset[1], 1e4)
    mover = lambda geom: affinity.translate(geom, desp, 0)
    cont = mover(base.contorno.intersection(caja))
    capas = {c: mover(base.cobre(c).intersection(interior)) for c in ('F.Cu', 'B.Cu')}
    return cont, capas


def _antena_tramo(base, cont, capas, tipo, sin_conector):
    x0, y0, x1, y1 = cont.bounds
    puerto = dict(base.puerto, borde=((x0 + x1)/2, y0))
    if sin_conector:
        puerto['conector'] = conector.SIN
        puerto['alimentacion'] = ((x0 + x1)/2, y0 + y1)        # el pad GND de una placa sin conector va en (x, y/2): el centro de la placa
    return replace(base, tipo=tipo, capas=capas, radiador=unary_union([capas['F.Cu'], capas['B.Cu']]), contorno=cont, zona_libre=cont, puerto=puerto, vias=[],
                   modulos=[], placas3d=[], hilos3d=[], cobre_sim=None, mascara_abierta=[],
                   info=_info(cont, {'avisos': [], 'f_sin_cortar_MHz': None, 'ajuste': None}))


# ------------------------------------------------------------------ dipolo en V
def estimar_f_diedro(p, eps):
    """El dipolo bowtie con los brazos doblados: la V acorta un poco la extensión horizontal pero el brazo es el mismo (sin calibrar)."""
    from . import dipolos
    return dipolos.estimar_f_dipolo({'forma': 1, 'largo_brazo': p['largo_brazo'], 'alimentacion': 0, 'hueco': 0.0,
                                     'iteracion_s': p.get('iteracion_s', 2)}, eps)


def generar_diedro(p, s, eps):
    base, q = _dipolo_base(p, s, eps)
    w50 = ancho_microstrip(50, s.er, s.h)
    wb = max(q['ancho_boom'], w50 + 3*s.h)
    xh = float(p['bisagra']) if p.get('bisagra') else wb/2 + 2.0
    beta = float(p['angulo_v'])
    # lo que se simula: el cobre continuo hasta la bisagra; lo que se fabrica: a 0,5 mm del canto de cada unión
    cont_c, capas_c = _tramo(base, -xh, xh, 0.0)
    cont_d, capas_d = _tramo(base, xh, 1e4, -xh)
    cont_i, capas_i = _tramo(base, -1e4, -xh, xh)
    fab_c = _tramo(base, -xh, xh, 0.0, (INSET_UNION, INSET_UNION))
    fab_d = _tramo(base, xh, 1e4, -xh, (INSET_UNION, 0.0))
    fab_i = _tramo(base, -1e4, -xh, xh, (0.0, INSET_UNION))
    centro = _antena_tramo(base, fab_c[0], fab_c[1], 'diedro', False)
    ala_d = _antena_tramo(base, fab_d[0], fab_d[1], 'diedro', True)
    ala_i = _antena_tramo(base, fab_i[0], fab_i[1], 'diedro', True)
    a = replace(base, tipo='diedro', parametros=dict(p), capas=centro.capas, radiador=centro.radiador, contorno=cont_c, zona_libre=cont_c,
                cobre_sim=capas_c)
    a.placas3d = [{'nombre': 'ala_derecha', 'antena': _antena_tramo(base, cont_d, capas_d, 'diedro', True), 'origen': (xh, 0.0, 0.0),
                   'giros': [(1, -beta)], 'fina': True},
                  {'nombre': 'ala_izquierda', 'antena': _antena_tramo(base, cont_i, capas_i, 'diedro', True), 'origen': (-xh, 0.0, 0.0),
                   'giros': [(1, beta)], 'fina': True}]
    a.modulos = [{'nombre': 'centro', 'cantidad': 1, 'antena': centro}, {'nombre': 'ala_derecha', 'cantidad': 1, 'antena': ala_d},
                 {'nombre': 'ala_izquierda', 'cantidad': 1, 'antena': ala_i}]
    a.info = dict(base.info, placa_mm=[round(cont_c.bounds[2] - cont_c.bounds[0], 2), round(cont_c.bounds[3], 2)],
                  bisagra_mm=round(xh, 2), angulo_v=beta, placas=3)
    a.info['avisos'] = list(base.info.get('avisos', [])) + [tr('Dipolo en V: tres placas que se sueldan en las bisagras (una unión por brazo); el ángulo lo fija una escuadra o una pieza impresa.')]
    return a


# ------------------------------------------------------------------ reflector de esquina
def estimar_f_reflector(p, eps):
    """El dipolo bowtie manda; las placas lo desplazan poco (sin calibrar)."""
    from . import dipolos
    return dipolos.estimar_f_dipolo({'forma': 1, 'largo_brazo': p['largo_brazo'], 'alimentacion': 0, 'hueco': 0.0,
                                     'iteracion_s': p.get('iteracion_s', 2)}, eps)


def generar_reflector_esquina(p, s, eps):
    base, q = _dipolo_base(p, s, eps)
    h = s.h
    y_d = base.puerto['alimentacion'][1]
    alfa = float(p['apertura_diedro'])
    m = math.radians(alfa/2)
    zmin = h + 1.0                                     # separación de la placa del dipolo a la cara interior de cada reflector en el arranque
    v0 = zmin/math.sin(m)                              # distancia del vértice al arranque de cada placa (vértice truncado)
    y_vertice = y_d - float(p['separacion'])
    W, L = float(p['ancho_reflector']), float(p['largo_reflector'])
    x0, x1 = -W/2, W/2
    cont = g.rectangulo(x0, 0, x1, L)
    cu = g.rectangulo(x0 + BORDE_COBRE, BORDE_COBRE, x1 - BORDE_COBRE, L - BORDE_COBRE)
    placa = _placa_plana('reflector_esquina', p, cont, cu, cu, (0.0, 0.0), True)
    zc = h/2                                           # el plano bisector es el centro de la placa del dipolo
    y_s = y_vertice + v0*math.cos(m)
    a = replace(base, tipo='reflector_esquina', parametros=dict(p))
    a.placas3d = [{'nombre': 'reflector_a', 'antena': placa, 'origen': (0.0, y_s, zc + v0*math.sin(m)), 'giros': [(0, alfa/2)], 'fina': False},
                  # la placa de abajo, girada al revés, tendría su grosor hacia dentro de la esquina: se baja `h` por su normal interior
                  {'nombre': 'reflector_b', 'antena': placa, 'origen': (0.0, y_s - h*math.sin(m), zc - v0*math.sin(m) - h*math.cos(m)),
                   'giros': [(0, -alfa/2)], 'fina': False}]
    a.modulos = [{'nombre': 'dipolo', 'cantidad': 1, 'antena': replace(base, tipo='reflector_esquina', modulos=[], placas3d=[], hilos3d=[]) },
                 {'nombre': 'reflector', 'cantidad': 2, 'antena': placa}]
    a.info = dict(base.info, vertice_y_mm=round(y_vertice, 1), placas=3, ancho_reflector_mm=W, largo_reflector_mm=L)
    a.info['avisos'] = list(base.info.get('avisos', [])) + [
        tr('Reflector de esquina: dos placas de cobre unidas por el vértice (o sujetas con una escuadra) a {0:.0f}°; el dipolo va en el plano bisector, a {1:.0f} mm del vértice.', alfa, float(p['separacion']))]
    if y_vertice < base.puerto['borde'][1] - 1:
        a.info['avisos'].append(tr('El vértice queda por detrás del borde de la placa del dipolo: acorta la separación o alarga el boom.'))
    return a


# ------------------------------------------------------------------ hélices
def _hilo_helice(r, centro, z0, altura, vueltas, sentido, fase0=0.0, paso_mm=1.0):
    """Puntos (n, 3) de una hélice de radio r, con el pie en z0 y a `centro` + r·(cos fase0, sin fase0)."""
    giro = 2*math.pi*vueltas
    arco = math.hypot(altura, giro*r)
    n = max(int(math.ceil(arco/paso_mm)), 12)
    t = np.linspace(0.0, 1.0, n + 1)
    fi = fase0 + sentido*giro*t
    return np.column_stack([centro[0] + r*np.cos(fi), centro[1] + r*np.sin(fi), z0 + altura*t])


def _placa_base_helice(tipo, p, s, y_pad):
    """Placa de masa con SMA en el borde y una línea de 50 Ω hasta (0, y_pad), de donde sale el hilo."""
    w50 = ancho_microstrip(50, s.er, s.h)
    W, L = float(p['ancho_placa']), float(p['largo_placa'])
    a_min = conector.ANCHO_MINIMO[conector.tipo(p)]
    W = max(W, a_min + 2.0)
    cont = g.rectangulo(-W/2, 0, W/2, L)
    sup = unary_union([g.rectangulo(-w50/2, BORDE_COBRE, w50/2, y_pad), g.rectangulo(-1.0, y_pad - 1.0, 1.0, y_pad + 1.0)])
    inf = g.rectangulo(-W/2 + BORDE_COBRE, BORDE_COBRE, W/2 - BORDE_COBRE, L - BORDE_COBRE)
    puerto = {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_pad), 'ancho_linea': w50}
    return Antena(tipo=tipo, parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(), radiador=sup, contorno=cont,
                  zona_libre=cont, puerto=puerto, info=_info(cont, {'pista_minima_mm': min(w50, p['ancho_pista']), 'hueco_minimo_mm': 5.0,
                                                                     'avisos': [], 'f_sin_cortar_MHz': None, 'ajuste': None}))


def _tira(tipo, p, trazas, ancho_tira, alto):
    """Tira de flex a fabricar: `trazas` = polilíneas en (x, y) con x en [0, ancho_tira]; el cobre queda a 0,5 mm de los cantos
    (la unión de los bordes al enrollar se suelda con estaño)."""
    cont = g.rectangulo(0, 0, ancho_tira, alto)
    interior = g.rectangulo(BORDE_COBRE, BORDE_COBRE, ancho_tira - BORDE_COBRE, alto - BORDE_COBRE)
    cu = unary_union([g.engordar(t, p['ancho_pista']) for t in trazas]).intersection(interior)
    return _placa_plana(tipo, p, cont, cu, Polygon(), (ancho_tira/2, 0.0), True)


def longitud_hilo_normal(p):
    """Largo del hilo de la hélice de modo normal."""
    giro = math.pi*p['diametro']*p['vueltas']
    return math.hypot(giro, p['altura'])


def estimar_f_helice_normal(p):
    return K_HELICE_NORMAL*C0/(4*longitud_hilo_normal(p)*1e-3)


def generar_helice_normal(p, s, eps):
    r = p['diametro']/2
    N = float(p['vueltas'])
    sentido = 1.0 if int(p.get('sentido', 1)) >= 0 else -1.0
    y_pad = max(float(p['largo_placa'])/2, BORDE_COBRE + 4.0)
    a = _placa_base_helice('helice_normal', p, s, y_pad)
    a.hilos3d = [{'puntos': _hilo_helice(r, (-r, y_pad), s.h, p['altura'], N, sentido), 'ancho': p['ancho_pista']}]
    W, H = math.pi*p['diametro'], p['altura']
    paso = H/N
    n_traz = int(math.ceil(N))
    trazas = []
    for i in range(n_traz):
        f = min(1.0, N - i)                                       # el último tramo puede ser fracción de vuelta
        trazas.append([(0.0, 1.0 + i*paso), (W*f, 1.0 + i*paso + f*paso)])
    tira = _tira('helice_normal', p, trazas, W, H + 2.0)
    a.modulos = [{'nombre': 'tira_flex', 'cantidad': 1, 'antena': tira}]
    a.info.update(placas=2, largo_hilo_mm=round(longitud_hilo_normal(p), 1), altura_mm=p['altura'], tira_mm=[round(W, 1), round(H + 2, 1)])
    a.info['avisos'] = [tr('Hélice en flex: se imprime plana (tira de {0:.1f} × {1:.1f} mm) y se enrolla en un tubo de {2:.1f} mm; el pie de la raya baja se suelda al pad de la línea y los bordes se unen con estaño.',
                           W, H + 2, p['diametro'])]
    return a


def longitud_brazo_qha(p):
    return math.hypot(p['altura'], p['vueltas']*math.pi*p['diametro'])


def estimar_f_helice_cuadrifilar(p):
    return K_QHA*C0/(4*longitud_brazo_qha(p)*1e-3)


def generar_helice_cuadrifilar(p, s, eps):
    r = p['diametro']/2
    N = float(p['vueltas'])
    sentido = 1.0 if int(p.get('sentido', 1)) >= 0 else -1.0
    y_pad = max(float(p['largo_placa'])/2, BORDE_COBRE + 4.0)
    a = _placa_base_helice('helice_cuadrifilar', p, s, y_pad)
    centro = (0.0, y_pad)
    a.hilos3d = [{'puntos': _hilo_helice(r, centro, s.h, p['altura'], N, sentido, fase0=math.radians(90*k)), 'ancho': p['ancho_pista']}
                 for k in range(4)]
    W, H = math.pi*p['diametro'], p['altura']
    trazas = []
    for k in range(4):
        x = (W*(k/4 + sentido*N*np.linspace(0, 1, 120))) % W
        z = 1.0 + H*np.linspace(0, 1, 120)
        tramo = [(x[0], z[0])]
        for i in range(1, len(z)):
            if abs(x[i] - x[i - 1]) > W/2:
                if len(tramo) > 1:
                    trazas.append(tramo)
                tramo = []
            tramo.append((x[i], z[i]))
        if len(tramo) > 1:
            trazas.append(tramo)
    tira = _tira('helice_cuadrifilar', p, trazas, W, H + 2.0)
    a.modulos = [{'nombre': 'tira_flex', 'cantidad': 1, 'antena': tira}]
    a.info.update(placas=2, largo_brazo_mm=round(longitud_brazo_qha(p), 1), altura_mm=p['altura'], tira_mm=[round(W, 1), round(H + 2, 1)],
                  sin_simulacion=tr('la alimentación en cuadratura necesita dos puertos: usa herramientas/helice_flex.py'))
    a.info['avisos'] = [tr('Hélice cuadrifilar: solo geometría, vista 3D y tira de flex. No se simula desde la interfaz (la alimentación en cuadratura es de dos puertos) y '
                           'falta la red de 90° o el balun.')]
    return a
