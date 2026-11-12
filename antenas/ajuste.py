"""Opciones para ajustar la antena una vez fabricada, y asistente a partir de una medida.

- Red en π en la línea de 50 Ω: serie (0 Ω de fábrica) + dos posiciones a masa (sin montar).
- Marcas de corte: el radiador se alarga un «sobrelargo» y la serigrafía marca dónde cortar;
  cortar SUBE la frecuencia.
- Tramos con puentes: trozos al final del radiador separados por huecos que se cierran con
  estaño o con un 0 Ω; vienen abiertos y cada puente cerrado BAJA la frecuencia un paso.

Todo en coordenadas del modelo (mm, y hacia arriba). Los generadores llaman a estas funciones
con la polilínea del radiador (o el parche) y la línea de 50 Ω, y guardan el resultado en
`Antena.ajuste`:
    componentes:  [{'ref', 'huella', 'x', 'y', 'rot', 'valor', 'montar', 'pads': [(dx, dy, w, h)]}]
    cortes:       polígonos que se quitan del cobre superior (hueco del componente en serie)
    puentes_sim:  polígonos que la simulación rellena (el 0 Ω en serie se da por montado)
    islas_masa:   polígonos de cobre superior que van a masa (con vía)
    vias_masa:    [(x, y)]
    marcas:       [{'linea': [(x, y), (x, y)], 'texto': str, 'pos': (x, y), 'rot': grados}]
    tramos:       número de tramos con puente
"""
import math
import re

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from . import geometria as g
from .tipos_base import Parametro
from .i18n import tr

# Huellas de componentes: (largo del pad, ancho del pad, distancia entre centros) [mm]
HUELLAS = {'0603': (0.9, 0.95, 1.6), '0402': (0.6, 0.6, 1.0)}
PUENTE_ESTANO = (0.6, 1.0, 0.9)      # dos medios pads separados 0,3 mm
TRAMO_MIN_ESTANO = 1.5               # largo mínimo de un tramo con puente de estaño [mm]
TRAMO_MIN_0OHM = 2.2                 # con resistencia 0603
SEP_MARCAS = 1.2                     # separación mínima entre marcas de corte [mm]

MODOS = {0: 'No ajustable', 1: 'Ajustable'}
PARAMS_AJUSTE = {
    'ajuste': Parametro('ajuste', 'Ajuste tras fabricar', 0, 0, 1, 1, True, opciones=MODOS),
    'red_pi': Parametro('red_pi', 'Red en π en la línea de 50 Ω', 1, 0, 1, 1, True, opciones={0: 'No', 1: 'Sí'}),
    'componentes': Parametro('componentes', 'Tamaño de los componentes', 0, 0, 1, 1, True,
                             opciones={0: '0603 (fácil de soldar)', 1: '0402'}),
    'sobrelargo': Parametro('sobrelargo', 'Sobrelargo para recortar [% de frecuencia]', 3, 0, 15, 0.5,
                            ayuda='La antena sale este % por debajo y las marcas indican dónde cortar'),
    'marcas': Parametro('marcas', 'Marcas de corte en la serigrafía', 1, 0, 1, 1, True, opciones={0: 'No', 1: 'Sí'}),
    'tramos': Parametro('tramos', 'Tramos con puente (cada uno baja la frecuencia)', 3, 0, 6, 1, True),
    'paso_tramo': Parametro('paso_tramo', 'Bajada por tramo [% de frecuencia]', 1.5, 0.3, 5, 0.1),
    'puente': Parametro('puente', 'Tipo de puente', 0, 0, 1, 1, True,
                        opciones={0: 'Puente de estaño', 1: 'Resistencia de 0 Ω'}),
}
PARAMS_SOLO_AJUSTABLE = set(PARAMS_AJUSTE) - {'ajuste'}

# Qué opciones tiene sentido en cada familia
POR_FAMILIA = {
    'monopolo_pista': ['ajuste', 'red_pi', 'componentes', 'sobrelargo', 'marcas', 'tramos', 'paso_tramo', 'puente'],
    'monopolo': ['ajuste', 'red_pi', 'componentes'],
    'jpole': ['ajuste', 'sobrelargo', 'marcas', 'tramos', 'paso_tramo', 'puente'],
    'yagi': ['ajuste', 'red_pi', 'componentes', 'sobrelargo', 'marcas', 'tramos', 'paso_tramo', 'puente'],
    'parche_rect': ['ajuste', 'red_pi', 'componentes', 'sobrelargo', 'marcas'],
    'parche': ['ajuste', 'red_pi', 'componentes'],
    'array': ['ajuste', 'red_pi', 'componentes'],
    'bucle': ['ajuste', 'red_pi', 'componentes'],
    'sin_ajuste': [],                      # tipos sin opciones de ajuste todavía (Yagi con boom)
}


def parametros_para(grupo):
    return [PARAMS_AJUSTE[n] for n in POR_FAMILIA[grupo]]


def activo(p):
    return int(p.get('ajuste', 0)) == 1


def vacio():
    return {'componentes': [], 'cortes': [], 'puentes_sim': [], 'islas_masa': [], 'vias_masa': [],
            'marcas': [], 'tramos': 0, 'notas': [], 'condensadores': []}


def unir(a, b):
    for k in ('componentes', 'cortes', 'puentes_sim', 'islas_masa', 'vias_masa', 'marcas', 'notas', 'condensadores'):
        a[k] = a[k] + b[k]
    a['tramos'] = a['tramos'] + b['tramos']
    return a


def mover(aj, dx, dy):
    """Desplaza todo el ajuste (para cuando el generador coloca el radiador)."""
    t = lambda geo: g.mover(geo, dx, dy)
    for c in aj['componentes']:
        c['x'] += dx
        c['y'] += dy
    aj['cortes'] = [t(x) for x in aj['cortes']]
    aj['puentes_sim'] = [t(x) for x in aj['puentes_sim']]
    aj['islas_masa'] = [t(x) for x in aj['islas_masa']]
    aj['vias_masa'] = [(x + dx, y + dy) for x, y in aj['vias_masa']]
    aj['condensadores'] = [dict(c, caja=(c['caja'][0] + dx, c['caja'][1] + dy, c['caja'][2] + dx, c['caja'][3] + dy))
                           for c in aj['condensadores']]
    for m in aj['marcas']:
        m['linea'] = [(x + dx, y + dy) for x, y in m['linea']]
        m['pos'] = (m['pos'][0] + dx, m['pos'][1] + dy)
    return aj


def _componente(ref, huella, x, y, rot, valor, montar):
    largo, ancho, paso = HUELLAS[huella] if huella in HUELLAS else PUENTE_ESTANO
    # pads a lo largo del eje local x; rot en grados (0: horizontal, 90: vertical)
    return {'ref': ref, 'huella': huella, 'x': x, 'y': y, 'rot': rot, 'valor': valor, 'montar': montar,
            'pads': [(-paso/2, 0.0, largo, ancho), (paso/2, 0.0, largo, ancho)]}


# ------------------------------------------------------------------ red en π
def red_pi(x_eje, y_centro, w_linea, p, vertical=True, lado=1):
    """Red en π sobre una línea de 50 Ω recta (vertical u horizontal) centrada en x_eje/y_centro.

    Serie: hueco en la línea con un componente (0 Ω de fábrica). Dos posiciones a masa a ±d del
    hueco, con su isla de cobre y vía a la masa inferior, en el lado 'lado' (+1/−1).
    """
    aj = vacio()
    huella = '0402' if int(p.get('componentes', 0)) == 1 else '0603'
    largo, ancho, paso = HUELLAS[huella]
    hueco = paso - largo + 0.1                       # separación entre los pads del serie
    d = paso + 1.6                                  # distancia de cada derivación al serie
    if vertical:
        corte = g.rectangulo(x_eje - w_linea/2 - 0.01, y_centro - hueco/2, x_eje + w_linea/2 + 0.01, y_centro + hueco/2)
        aj['componentes'].append(_componente('Z1', huella, x_eje, y_centro, 90, '0 Ω', True))
        for ref, dy in (('Z2', -d), ('Z3', d)):
            xc = x_eje + lado*(w_linea/2 + paso/2 - largo/2 + 0.05)
            aj['componentes'].append(_componente(ref, huella, xc, y_centro + dy, 0 if lado > 0 else 180, 'sin montar', False))
            xi = xc + lado*paso/2
            isla = g.rectangulo(xi - largo/2 - 0.1, y_centro + dy - 0.9, xi + lado*1.4, y_centro + dy + 0.9)
            aj['islas_masa'].append(isla)
            aj['vias_masa'].append((xi + lado*0.85, y_centro + dy))
    else:
        corte = g.rectangulo(x_eje - hueco/2, y_centro - w_linea/2 - 0.01, x_eje + hueco/2, y_centro + w_linea/2 + 0.01)
        aj['componentes'].append(_componente('Z1', huella, x_eje, y_centro, 0, '0 Ω', True))
        for ref, dx in (('Z2', -d), ('Z3', d)):
            yc = y_centro + lado*(w_linea/2 + paso/2 - largo/2 + 0.05)
            aj['componentes'].append(_componente(ref, huella, x_eje + dx, yc, 90 if lado > 0 else 270, 'sin montar', False))
            yi = yc + lado*paso/2
            isla = g.rectangulo(x_eje + dx - 0.9, yi - largo/2 - 0.1, x_eje + dx + 0.9, yi + lado*1.4)
            aj['islas_masa'].append(isla)
            aj['vias_masa'].append((x_eje + dx, yi + lado*0.85))
    aj['cortes'].append(corte)
    aj['puentes_sim'].append(corte)
    aj['notas'].append(tr('Red en π ({0}): Z1 en serie = 0 Ω de fábrica; Z2 (lado conector) y Z3 (lado antena) a masa, sin montar. Usa el asistente con tu medida para elegir valores.', huella))
    return aj


Q_CONDENSADOR_RED = 250.0           # C0G/NP0 0402/0603 a ~1 GHz (solo para las pérdidas simuladas)
Q_BOBINA_RED = 40.0                 # bobina cerámica o de hilo 0402/0603 a ~1 GHz
C0_RED = 299792458.0


def _trasladar(z, beta_d, z0=50.0):
    """Impedancia vista una distancia `d` más cerca del generador (línea sin pérdidas de z0; beta_d = β·d en rad)."""
    t = np.tan(beta_d)
    return z0*(z + 1j*z0*t)/(z0 + 1j*z*t)


def _z_componente_q(tipo, valor, f, q_l, q_c):
    """Impedancia de una L (nH) o C (pF) con su resistencia serie por la Q; ('0 Ω') = 0."""
    w = 2*np.pi*f
    if tipo == 'L':
        x = w*valor*1e-9
        return x/q_l + 1j*x
    if tipo == 'C':
        x = 1/(w*valor*1e-12)
        return x/q_c - 1j*x
    return 0j*w


def zin_red_l(freq, z_ref, topologia, cs, cp, d_z1_mm, d_comp_mm, eps_eff, q_l=Q_BOBINA_RED, q_c=Q_CONDENSADOR_RED, z0=50.0):
    """Impedancia vista desde el conector con la red en L montada. z_ref: la del anillo en `freq` (array o escalar);
    topologia 'Z2' (serie Z1 junto al anillo y derivación Z2 hacia el conector) o 'Z3' (derivación Z3 junto al anillo y
    serie Z1 hacia el conector); cs, cp: (tipo, valor) del serie y la derivación."""
    def beta(mm):
        return 2*np.pi*freq*np.sqrt(eps_eff)/C0_RED*mm*1e-3
    zs = _z_componente_q(cs[0], cs[1], freq, q_l, q_c)
    zp = _z_componente_q(cp[0], cp[1], freq, q_l, q_c)
    if topologia == 'Z2':       # anillo → línea → Z1 serie → línea → Z2 derivación → conector
        z1 = _trasladar(z_ref, beta(d_z1_mm), z0) + zs
        z2 = _trasladar(z1, beta(d_comp_mm), z0)
        return 1/(1/z2 + 1/zp)
    z3 = _trasladar(z_ref, beta(d_z1_mm - d_comp_mm), z0)                    # anillo → línea → Z3 derivación
    z3 = 1/(1/z3 + 1/zp)
    return _trasladar(z3, beta(d_comp_mm), z0) + zs                         # → línea → Z1 serie → conector


def eficiencia_red_l(freq, z_ref, topologia, cs, cp, d_z1_mm, d_comp_mm, eps_eff, q_l=Q_BOBINA_RED, q_c=Q_CONDENSADOR_RED, z0=50.0):
    """Fracción de la potencia aceptada que llega al anillo (el resto se pierde en la resistencia de los componentes), a `freq`
    (escalar). Mismos argumentos que `zin_red_l`; z_ref: la impedancia del anillo en esa frecuencia."""
    def beta(mm):
        return 2*np.pi*freq*np.sqrt(eps_eff)/C0_RED*mm*1e-3

    def linea(v, i, mm):
        th = beta(mm)
        return v*np.cos(th) + 1j*z0*i*np.sin(th), i*np.cos(th) + 1j*v/z0*np.sin(th)
    zs = _z_componente_q(cs[0], cs[1], freq, q_l, q_c)
    zp = _z_componente_q(cp[0], cp[1], freq, q_l, q_c)
    v, i = z_ref*1.0, 1.0 + 0j                              # corriente 1 A en el anillo
    p_anillo = (abs(i)**2)*z_ref.real
    if topologia == 'Z2':
        v, i = linea(v, i, d_z1_mm)
        v = v + zs*i
        v, i = linea(v, i, d_comp_mm)
        i = i + v/zp
    else:
        v, i = linea(v, i, d_z1_mm - d_comp_mm)
        i = i + v/zp
        v, i = linea(v, i, d_comp_mm)
        v = v + zs*i
    p_entrada = (v*np.conj(i)).real
    return float(p_anillo/p_entrada) if p_entrada > 0 else 0.0


def mejor_red_l(z_anillo, f, f_obj, d_z1_mm, d_comp_mm, eps_eff, q_l=Q_BOBINA_RED, q_c=Q_CONDENSADOR_RED, z0=50.0):
    """Red en L (serie Z1 + derivación Z2 o Z3) con valores E24 que adapta a z0 la impedancia `z_anillo(f)` de una antena
    pequeña de resistencia baja, teniendo en cuenta las pérdidas de los componentes (Q) y la línea de 50 Ω entre ellos.

    z_anillo: impedancia en el punto de alimentación del anillo (sin la línea de 50 Ω hasta el conector), array sobre `f` [Hz].
    d_z1_mm: línea de 50 Ω entre ese punto y Z1; d_comp_mm: entre Z1 y cada derivación (Z2 al lado del conector, Z3 al de la
    antena); eps_eff: de la línea. Prueba las dos topologías con todos los valores E24 (L de 0,5 a 100 nH, C de 0,3 a 100 pF).
    Devuelve {'posicion', 'serie', 'derivacion', 's11_dB' (en f_obj), 's11_f_dB' (array sobre f)} o None."""
    f = np.asarray(f, float)
    z_anillo = np.asarray(z_anillo, complex)
    k = int(np.argmin(np.abs(f - f_obj)))
    cand_l = [v for v in np.concatenate([E24*10**e for e in range(-1, 3)]) if 0.5 <= v <= 100]
    cand_c = [v for v in np.concatenate([E24*10**e for e in range(-1, 3)]) if 0.3 <= v <= 100]
    lista_s = [('0 Ω', 0.0)] + [('L', float(f'{v:.3g}')) for v in cand_l] + [('C', float(f'{v:.3g}')) for v in cand_c]
    lista_p = [('L', float(f'{v:.3g}')) for v in cand_l] + [('C', float(f'{v:.3g}')) for v in cand_c]

    def zin(freq, z_ref, topologia, cs, cp):
        return zin_red_l(freq, z_ref, topologia, cs, cp, d_z1_mm, d_comp_mm, eps_eff, q_l, q_c, z0)

    mejor = None
    for topologia in ('Z2', 'Z3'):
        for cs in lista_s:
            for cp in lista_p:
                z = zin(f[k], z_anillo[k], topologia, cs, cp)
                g = abs((z - z0)/(z + z0))
                n = (cs[0] != '0 Ω') + 1
                clave = (round(g, 4), n)
                if mejor is None or clave < mejor[0]:
                    mejor = (clave, topologia, cs, cp)
    if mejor is None:
        return None
    _, topologia, cs, cp = mejor
    z = zin(f, z_anillo, topologia, cs, cp)
    s11 = 20*np.log10(np.abs((z - z0)/(z + z0)) + 1e-12)
    return {'posicion': topologia, 'serie': cs, 'derivacion': cp, 's11_dB': float(s11[k]), 's11_f_dB': s11}


def texto_componente(tipo, valor):
    """('L', 3.9) → '3,9 nH' (con punto, como el resto de valores del ajuste); ('C', 1.2) → '1.2 pF'."""
    if tipo == 'L':
        return f'{valor:g} nH'
    if tipo == 'C':
        return f'{valor:g} pF'
    return '0 Ω'


def montar_red(aj, red, w_linea, p, elementos=False):
    """Da valores a la red en π `aj` (la de `red_pi`, con la línea vertical u horizontal): los pone en la lista de
    componentes (valor y «montar») y, con `elementos`, también como elementos concentrados de la simulación
    (`aj['condensadores']`: C o L con su Q). **Con `elementos` la FDTD no es fiable con C ≥ ~2 pF o L pequeñas** (la
    derivación sale en cortocircuito o inestable con el paso de malla normal): por defecto la red se aplica por
    circuito sobre la impedancia simulada del anillo (`simulacion.aplicar_red_bucle`).

    red: {'posicion': 'Z2' o 'Z3', 'serie': (tipo, valor), 'derivacion': (tipo, valor)} como da `redes_l`;
    tipo 'L' (nH), 'C' (pF) o '0 Ω' (serie sin componente). El serie va en Z1 y la derivación en Z2 (lado del
    conector) o Z3 (lado de la antena). Devuelve las vías de masa de la isla que se usa (para `Antena.vias`; vacío si
    no hay `elementos`)."""
    huella = '0402' if int(p.get('componentes', 0)) == 1 else '0603'
    largo, ancho, paso = HUELLAS[huella]
    hueco = paso - largo + 0.1
    comp = {c['ref']: c for c in aj['componentes']}
    z1 = comp['Z1']
    vertical = z1['rot'] == 90

    def elemento(tipo, valor, caja, direccion):
        d = {'caja': tuple(caja), 'dir': direccion, 'caps': False}
        if tipo == 'L':
            d.update({'L_nH': valor, 'Q': Q_BOBINA_RED})
        else:
            d.update({'C_pF': valor, 'Q': Q_CONDENSADOR_RED})
        return d

    ts, vs = red['serie']
    if ts in ('L', 'C') and vs:
        z1['valor'], z1['montar'] = texto_componente(ts, vs), True
        if vertical:
            caja = (z1['x'] - w_linea/2, z1['y'] - hueco/2, z1['x'] + w_linea/2, z1['y'] + hueco/2)
        else:
            caja = (z1['x'] - hueco/2, z1['y'] - w_linea/2, z1['x'] + hueco/2, z1['y'] + w_linea/2)
        if elementos:
            aj['condensadores'].append(elemento(ts, vs, caja, 'y' if vertical else 'x'))
            aj['puentes_sim'] = []                  # el hueco del serie queda abierto: lo llena el elemento concentrado
    td, vd = red['derivacion']
    c = comp[red['posicion']]
    c['valor'], c['montar'] = texto_componente(td, vd), True
    if vertical:
        lado = 1.0 if c['rot'] == 0 else -1.0
        x_linea = z1['x'] + lado*w_linea/2
        x_isla = c['x'] + lado*(paso/2 - largo/2 - 0.1)
        caja = (min(x_linea, x_isla), c['y'] - ancho/2, max(x_linea, x_isla), c['y'] + ancho/2)
        via = (c['x'] + lado*(paso/2 + 0.85), c['y'])
        direccion = 'x'
    else:
        lado = 1.0 if c['rot'] == 90 else -1.0
        y_linea = z1['y'] + lado*w_linea/2
        y_isla = c['y'] + lado*(paso/2 - largo/2 - 0.1)
        caja = (c['x'] - ancho/2, min(y_linea, y_isla), c['x'] + ancho/2, max(y_linea, y_isla))
        via = (c['x'], c['y'] + lado*(paso/2 + 0.85))
        direccion = 'y'
    if elementos:
        aj['condensadores'].append(elemento(td, vd, caja, direccion))
    aj['notas'].append(tr('Red de adaptación: Z1 (serie) = {0}; {1} (a masa) = {2}.',
                          texto_componente(ts, vs), red['posicion'], texto_componente(td, vd)))
    return [via] if elementos else []


# Componentes reales en la simulación (F4.1). Valores TÍPICOS de 0402/0603 de gama media, sin hoja de datos concreta (los de Murata
# GJM/LQW no los he consultado): hay que sustituirlos por los de la pieza que se compre.
ESL_C_NH = {'0402': 0.4, '0603': 0.6}      # inductancia serie parásita de un condensador [nH]
ESL_C_DEFECTO_NH = 0.5


def parse_componente(texto):
    """'C 1,2 pF' → ('C', 1.2); 'L 3,9 nH' → ('L', 3.9); '0R' o '0 Ω' → ('0 Ω', 0.0); vacío, None o «sin montar» → None.
    Lanza ValueError si no se entiende."""
    if texto is None:
        return None
    t = str(texto).strip()
    if t == '' or t.lower() in ('sin montar', 'vacio', 'vacío', '-', '—'):
        return None
    if t.lower() in ('0r', '0 r', '0', '0 ω', '0ω', '0 ohm', '0ohm'):
        return ('0 Ω', 0.0)
    m = re.fullmatch(r'([CcLl])\s*([0-9]+(?:[.,][0-9]+)?)\s*(pF|nH|pf|nh)?', t)
    if not m:
        raise ValueError(tr('Componente no válido: «{0}». Usa «C 1,2 pF», «L 3,9 nH», «0R» o déjalo vacío.', texto))
    tipo = m.group(1).upper()
    unidad = (m.group(3) or '').lower()
    if unidad and unidad != ('pf' if tipo == 'C' else 'nh'):
        raise ValueError(tr('Componente no válido: «{0}»: un condensador va en pF y una bobina en nH.', texto))
    return (tipo, float(m.group(2).replace(',', '.')))


def montar_componentes(aj, z1, z2, z3, w_linea, p):
    """Monta como elementos concentrados de la simulación los componentes de la red en π `aj`: z1 en serie y z2, z3 a masa, cada uno
    (tipo, valor) como da `parse_componente` o None. Un condensador lleva su ESR (Q) y su ESL en serie; una bobina, su ESR por la Q
    (la capacidad paralela de la bobina —su SRF— no se modela). Pone también el valor en la lista de componentes. Devuelve las vías
    de masa de las islas usadas (para `Antena.vias`). Z1 (serie) y las bobinas a masa van a la FDTD (validadas a 2,4 GHz: S11 a ±0,5 dB
    del circuito); **un condensador a masa NO**: la FDTD lo deja casi abierto aunque sean 100 pF (lección 77), así que se guarda en
    `aj['derivaciones_circuito']` y `simulacion.aplicar_derivaciones` lo aplica por circuito sobre la Z simulada (hacia el conector)."""
    huella = '0402' if int(p.get('componentes', 0)) == 1 else '0603'
    largo, ancho, paso = HUELLAS[huella]
    hueco = paso - largo + 0.1
    comp = {c['ref']: c for c in aj['componentes']}
    zc = comp['Z1']
    vertical = zc['rot'] == 90

    def elemento(tipo, valor, caja, direccion):
        d = {'caja': tuple(caja), 'dir': direccion, 'caps': False}
        if tipo == 'L':
            d.update({'L_nH': valor, 'Q': Q_BOBINA_RED})
        else:
            d.update({'C_pF': valor, 'Q': Q_CONDENSADOR_RED, 'esl_nH': ESL_C_NH.get(huella, ESL_C_DEFECTO_NH)})
        return d

    vias = []
    if z1 and z1[0] in ('L', 'C'):
        zc['valor'], zc['montar'] = texto_componente(*z1), True
        if vertical:
            caja = (zc['x'] - w_linea/2, zc['y'] - hueco/2, zc['x'] + w_linea/2, zc['y'] + hueco/2)
        else:
            caja = (zc['x'] - hueco/2, zc['y'] - w_linea/2, zc['x'] + hueco/2, zc['y'] + w_linea/2)
        aj['condensadores'].append(elemento(*z1, caja, 'y' if vertical else 'x'))
        aj['puentes_sim'] = []                      # el hueco del serie queda abierto: lo llena el elemento concentrado
    for ref, z in (('Z2', z2), ('Z3', z3)):
        if not z or z[0] not in ('L', 'C'):
            continue
        c = comp[ref]
        c['valor'], c['montar'] = texto_componente(*z), True
        if not vertical:
            raise ValueError(tr('Los componentes simulados solo están preparados para la red en π sobre una línea vertical.'))
        lado = 1.0 if c['rot'] == 0 else -1.0
        x_linea, x_isla = zc['x'] + lado*w_linea/2, c['x'] + lado*(paso/2 - largo/2 - 0.1)
        caja = (min(x_linea, x_isla), c['y'] - ancho/2, max(x_linea, x_isla), c['y'] + ancho/2)
        vias.append((c['x'] + lado*(paso/2 + 0.85), c['y']))
        if z[0] == 'C':
            # el condensador a masa NO va a la FDTD (no hace corto ni con 100 pF: ver docstring): se aplica por circuito sobre la Z simulada
            if ref == 'Z3' and z1 and z1[0] in ('L', 'C'):
                raise ValueError(tr('Un condensador en Z3 con un componente en Z1 no se puede simular: el orden de la red lo impide. '
                                    'Ponlo en Z2 (lado del conector) o deja Z1 en 0 Ω.'))
            aj.setdefault('derivaciones_circuito', []).append(
                {'ref': ref, 'tipo': 'C', 'valor': z[1], 'y': c['y'], 'esl_nH': ESL_C_NH.get(huella, ESL_C_DEFECTO_NH)})
        else:
            aj['condensadores'].append(elemento(*z, caja, 'x'))
    aj['notas'].append(tr('Componentes simulados: Z1 = {0}; Z2 = {1}; Z3 = {2}.', texto_componente(*z1) if z1 else '—',
                          texto_componente(*z2) if z2 else '—', texto_componente(*z3) if z3 else '—'))
    return vias


# ------------------------------------------------------------------ marcas y tramos
def alargar_polilinea(pts, w, le, k_eq, f_nom, p, prefijo='T'):
    """Sobrelargo + marcas + tramos al final de una polilínea de radiador.

    le: longitud equivalente del radiador; k_eq: cuánto de cada mm físico de pista recta añadida
    en la punta cuenta como longitud equivalente. f ∝ 1/le.
    Devuelve (cobre_extra, ajuste, le_total).
    """
    aj = vacio()
    pts = np.asarray(pts, float)
    fin = pts[-1]
    d = pts[-1] - pts[-2]
    d = d/np.linalg.norm(d)
    piezas = []
    if d[1] < -0.3:
        # la punta baja hacia la masa (p. ej. el Hilbert): se prolonga en horizontal, hacia fuera
        lado = np.sign(fin[0] - pts[:, 0].mean()) or 1.0
        d = np.array([lado, 0.0])
        piezas.append(g.rectangulo(fin[0] - w/2, fin[1] - w/2, fin[0] + w/2, fin[1] + w/2))   # codo
    n_perp = np.array([-d[1], d[0]])
    s = p.get('sobrelargo', 0)/100 if int(p.get('marcas', 0)) == 1 else 0.0   # sobrelargo solo para cortar
    ext = s*le/k_eq                                   # mm de pista recta añadidos
    if ext > 0:
        piezas.append(g.engordar([fin, fin + d*ext], w))
    punta = fin + d*ext
    le_tot = le + ext*k_eq
    f_sin_cortar = f_nom*le/le_tot
    if int(p.get('marcas', 0)) == 1 and ext > 0:
        # una marca por cada ~1 % de frecuencia (máx. 8), contando desde la punta, pero separadas
        # al menos SEP_MARCAS mm para que se puedan cortar y leer
        pasos = max(1, min(8, int(round(p.get('sobrelargo', 3))), int(ext//SEP_MARCAS)))
        for k in range(1, pasos + 1):
            corte_mm = ext*k/pasos
            punto = punta - d*corte_mm
            f_k = f_nom*le/(le_tot - corte_mm*k_eq)
            a = punto + n_perp*(w/2 + 0.4)
            b = punto - n_perp*(w/2 + 0.4)
            aj['marcas'].append({'linea': [tuple(a), tuple(b)], 'texto': f'{f_k/1e6:.0f}',
                                 'pos': tuple(punto + n_perp*(w/2 + 1.6)),
                                 'rot': math.degrees(math.atan2(d[1], d[0]))})
        aj['notas'].append(tr('Sin cortar resuena ~{0:.0f} MHz; cada marca indica en MHz la frecuencia que queda si cortas por ella.', f_sin_cortar/1e6))
    n_tr = int(p.get('tramos', 0))
    if n_tr > 0:
        estano = int(p.get('puente', 0)) == 0
        hueco = 0.3 if estano else HUELLAS['0603'][2] - HUELLAS['0603'][0] + 0.1
        # cada tramo debe alojar medio pad en cada extremo: si el paso pedido es más corto, se alarga
        largo_tr = max(p.get('paso_tramo', 1.5)/100*le/k_eq, TRAMO_MIN_ESTANO if estano else TRAMO_MIN_0OHM)
        paso_f = largo_tr*k_eq/le
        x = punta
        for i in range(n_tr):
            ini = x + d*hueco
            fin_tr = ini + d*largo_tr
            piezas.append(g.engordar([ini, fin_tr], w))
            centro = x + d*hueco/2
            rot = math.degrees(math.atan2(d[1], d[0]))
            if estano:
                c = {'ref': f'JP{prefijo}{i + 1}', 'huella': 'puente', 'x': centro[0], 'y': centro[1], 'rot': rot,
                     'valor': 'abierto', 'montar': False,
                     'pads': [(-(hueco/2 + 0.3), 0.0, 0.6, max(w, 1.0)), (hueco/2 + 0.3, 0.0, 0.6, max(w, 1.0))]}
            else:
                c = _componente(f'R{prefijo}{i + 1}', '0603', centro[0], centro[1], rot, tr('0 Ω (no montada)'), False)
            aj['componentes'].append(c)
            x = fin_tr
        aj['tramos'] = n_tr
        aj['notas'].append(f'{n_tr} tramos con {"puente de estaño" if estano else "0 Ω"}: vienen abiertos; cerrando '
                           f'puentes en orden desde el radiador, cada uno baja ~{100*paso_f:.1f} % la frecuencia.')
    return unary_union(piezas) if piezas else None, aj, le_tot


def marcas_parche(x0, x1, y_borde, L, f_nom, p):
    """Sobrelargo del parche por su borde radiante superior y marcas de corte paralelas a él."""
    aj = vacio()
    s = p.get('sobrelargo', 0)/100
    ext = s*L
    if int(p.get('marcas', 0)) == 1 and ext > 0:
        pasos = max(1, min(8, int(round(p.get('sobrelargo', 3)))))
        for k in range(1, pasos + 1):
            c = ext*k/pasos
            y = y_borde + ext - c
            f_k = f_nom*L/(L + ext - c)
            aj['marcas'].append({'linea': [(x0 - 0.5, y), (x1 + 0.5, y)], 'texto': f'{f_k/1e6:.0f}',
                                 'pos': (x1 + 3.0, y), 'rot': 0})
        aj['notas'].append(tr('Parche alargado {0:.1f} %: corta en paralelo al borde superior por la marca de la frecuencia deseada.', 100*s))
    return ext, aj


# ------------------------------------------------------------------ asistente
def leer_s1p(texto):
    """Touchstone de 1 puerto (formatos RI, MA o DB; unidades Hz/kHz/MHz/GHz). Devuelve (f, s11)."""
    escala, formato = 1e9, 'MA'
    f, s = [], []
    for linea in texto.splitlines():
        linea = linea.split('!')[0].strip()
        if not linea:
            continue
        if linea.startswith('#'):
            t = linea[1:].upper().split()
            escala = {'HZ': 1, 'KHZ': 1e3, 'MHZ': 1e6, 'GHZ': 1e9}.get(t[0], 1e9) if t else 1e9
            for fm in ('RI', 'MA', 'DB'):
                if fm in t:
                    formato = fm
            continue
        v = [float(x) for x in linea.split()[:3]]
        if len(v) < 3:
            continue
        f.append(v[0]*escala)
        if formato == 'RI':
            s.append(complex(v[1], v[2]))
        else:
            mag = 10**(v[1]/20) if formato == 'DB' else v[1]
            s.append(mag*complex(math.cos(math.radians(v[2])), math.sin(math.radians(v[2]))))
    return np.array(f), np.array(s)


def distancia_conector_a_red(antena):
    """mm de línea de 50 Ω entre el borde del conector y el componente en serie Z1 (o None)."""
    aj = antena.ajuste or {}
    z1 = next((c for c in aj.get('componentes', []) if c['ref'] == 'Z1'), None)
    if z1 is None or antena.puerto.get('tipo') == 'coaxial':
        return None
    bx, by = antena.puerto['borde']
    return math.hypot(z1['x'] - bx, z1['y'] - by) - antena.puerto.get('inicio_mm', 0.0)
E24 = np.array([1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6,
                6.2, 6.8, 7.5, 8.2, 9.1])


def normalizado(valor, minimo, maximo):
    """Valor comercial E24 más cercano dentro de [minimo, maximo]."""
    serie = np.concatenate([E24*10**k for k in range(-2, 4)])
    serie = serie[(serie >= minimo) & (serie <= maximo)]
    v = float(serie[np.argmin(np.abs(np.log(serie/valor)))]) if len(serie) else valor
    return float(f'{v:.3g}')


def _x_a_componente(x, f):
    """Reactancia -> ('L', nH) o ('C', pF) normalizados."""
    w = 2*math.pi*f
    if x > 0:
        return 'L', normalizado(x/w*1e9, 0.5, 220)
    return 'C', normalizado(-1/(w*x)*1e12, 0.3, 220)


def _z_componente(tipo, valor, f):
    w = 2*math.pi*f
    return 1j*w*valor*1e-9 if tipo == 'L' else 1/(1j*w*valor*1e-12)


def redes_l(zl, f, z0=50.0):
    """Redes L (serie + derivación) que adaptan zl a z0, con valores normalizados y su |S11|.

    Devuelve una lista de soluciones: {'serie': (tipo, valor), 'derivacion': (tipo, valor),
    'posicion': 'Z2' o 'Z3', 's11_dB'}. Z3 = derivación en el lado de la antena (cuando R > z0),
    Z2 = derivación en el lado del conector (cuando R < z0).
    """
    r, x = zl.real, zl.imag
    sols = []
    if r > z0:
        # derivación junto a la carga (Z3) y luego serie (Z1)
        for sg in (1, -1):
            b = (x + sg*math.sqrt(r/z0)*math.sqrt(r*r + x*x - z0*r))/(r*r + x*x)
            xs = 1/b + x*z0/r - z0/(b*r)
            sols.append(('Z3', -1/b if b != 0 else math.inf, xs))
    else:
        # serie junto a la carga (Z1) y derivación en el lado del conector (Z2)
        for sg in (1, -1):
            xs = sg*math.sqrt(r*(z0 - r)) - x
            bp = sg*math.sqrt((z0 - r)/r)/z0
            sols.append(('Z2', -1/bp if bp != 0 else math.inf, xs))
    out = []
    for pos, x_der, x_ser in sols:
        if not math.isfinite(x_der):
            continue
        der = _x_a_componente(x_der, f)
        ser = _x_a_componente(x_ser, f) if abs(x_ser) > 0.5 else ('0 Ω', 0.0)
        zs = 0 if ser[0] == '0 Ω' else _z_componente(*ser, f)
        zp = _z_componente(*der, f)
        if pos == 'Z3':
            z1 = 1/(1/zl + 1/zp)
            zin = z1 + zs
        else:
            z1 = zl + zs
            zin = 1/(1/z1 + 1/zp)
        g_ = (zin - z0)/(zin + z0)
        out.append({'posicion': pos, 'serie': ser, 'derivacion': der, 's11_dB': round(20*math.log10(abs(g_) + 1e-12), 1)})
    out.sort(key=lambda s: s['s11_dB'])
    return out


def descripcion_pieza(tipo):
    """Qué comprar para un componente de la red (sin números de pieza: solo la descripción, 0402 o 0603 según la huella elegida)."""
    return {'C': tr('condensador C0G/NP0 0402 o 0603'), 'L': tr('bobina 0402 o 0603 (Q ≥ 40)')}.get(tipo, tr('resistencia de 0 Ω 0402 o 0603'))


def _banda_menos10(f, db, f_obj):
    """(f_inf, f_sup) de la zona a −10 dB que contiene f_obj (o la más cercana), o None."""
    f = np.asarray(f, float)
    debajo = np.asarray(db) < -10
    if not debajo.any():
        return None
    idx = np.where(debajo)[0]
    i = int(idx[np.argmin(np.abs(f[idx] - f_obj))])
    lo = hi = i
    while lo > 0 and debajo[lo - 1]:
        lo -= 1
    while hi < len(f) - 1 and debajo[hi + 1]:
        hi += 1
    return float(f[lo]), float(f[hi])


def _efecto_red(f, s11, f_obj, sol, distancia_red_mm, eps_eff, tolerancia=0.05):
    """Con la medida (s11 en el plano del conector) y la red `sol` (de `redes_l`): lista de piezas, S11 por circuito en la
    frecuencia objetivo, banda a −10 dB que quedaría y peor caso con los componentes a ±`tolerancia` (cuatro esquinas).
    La Z medida se lleva a la posición de la red quitando la línea (`distancia_red_mm`, `eps_eff`) y se calcula en toda la
    banda medida con la Q de los componentes. Es un cálculo por circuito, no una medida."""
    f = np.asarray(f, float)
    ee = eps_eff or 3.2
    z = 50*(1 + np.asarray(s11))/(1 - np.asarray(s11))
    if distancia_red_mm:
        z = _trasladar(z, -2*np.pi*f*math.sqrt(ee)/C0_RED*distancia_red_mm*1e-3)
    top, cs, cp = sol['posicion'], tuple(sol['serie']), tuple(sol['derivacion'])
    k = int(np.argmin(np.abs(f - f_obj)))

    def s11_db(cs_, cp_):
        zr = zin_red_l(f, z, top, cs_, cp_, 0.0, 0.0, ee)
        return 20*np.log10(np.abs((zr - 50)/(zr + 50)) + 1e-12)
    nominal = s11_db(cs, cp)
    peor, bandas = -1e9, []
    for fs in (1 - tolerancia, 1 + tolerancia):
        for fp in (1 - tolerancia, 1 + tolerancia):
            db = s11_db(cs if cs[0] == '0 Ω' else (cs[0], cs[1]*fs), (cp[0], cp[1]*fp))
            peor = max(peor, float(db[k]))
            bandas.append(_banda_menos10(f, db, f_obj))
    b = _banda_menos10(f, nominal, f_obj)
    comunes = None if any(x is None for x in bandas) else (max(x[0] for x in bandas), min(x[1] for x in bandas))
    return {'piezas': [{'ref': 'Z1', 'valor': texto_componente(*cs), 'descripcion': descripcion_pieza(cs[0]), 'montaje': tr('en serie')},
                       {'ref': top, 'valor': texto_componente(*cp), 'descripcion': descripcion_pieza(cp[0]), 'montaje': tr('a masa')}],
            's11_red_dB': round(float(nominal[k]), 1), 's11_peor_dB': round(peor, 1),
            'banda_esperada_MHz': [round(b[0]/1e6, 1), round(b[1]/1e6, 1)] if b else None,
            'banda_peor_MHz': [round(comunes[0]/1e6, 1), round(comunes[1]/1e6, 1)] if comunes and comunes[1] > comunes[0] else None}


def asistente(antena, f, s11, f_obj, distancia_red_mm=None, eps_eff=None):
    """Recomendaciones a partir de una medida (f en Hz, s11 complejo en el plano del conector)."""
    aj = antena.ajuste or vacio()
    db = 20*np.log10(np.abs(s11))
    i = int(np.argmin(db))
    debajo = db < -10
    if debajo[i]:
        lo = i
        while lo > 0 and debajo[lo - 1]:
            lo -= 1
        hi = i
        while hi < len(f) - 1 and debajo[hi + 1]:
            hi += 1
        f_res = math.sqrt(f[lo]*f[hi])
    else:
        f_res = f[i]
    rec = {'f_medida_MHz': round(f_res/1e6, 2), 's11_min_dB': round(float(db[i]), 1),
           'desvio_%': round(100*(f_res - f_obj)/f_obj, 2), 'acciones': []}
    desvio = (f_res - f_obj)/f_obj
    # 1) frecuencia: marcas (subir) o tramos (bajar)
    marcas = aj.get('marcas', [])
    if desvio < -0.003 and marcas:
        # las marcas se calcularon con la frecuencia de diseño: se corrigen por el desvío medido
        f_dis = antena.info.get('f_sin_cortar_MHz', None)
        escala = f_res/(f_dis*1e6) if f_dis else 1.0
        mejor = min(marcas, key=lambda m: abs(float(m['texto'])*1e6*escala - f_obj))
        rec['acciones'].append(tr('Corta por la marca «{0}» (con tu medida quedará ≈ {1:.0f} MHz).', mejor["texto"], float(mejor["texto"])*escala))
    elif desvio > 0.003 and aj.get('tramos', 0):
        paso = antena.parametros.get('paso_tramo', 1.5)/100
        n = min(aj['tramos'], max(1, round(desvio/paso)))
        rec['acciones'].append(tr('Cierra {0} puente(s) de tramo, empezando por el más cercano al radiador (baja ≈ {1:.1f} %).', n, 100*n*paso))
    elif abs(desvio) > 0.003:
        rec['acciones'].append(tr('La resonancia está un {0:+.1f} % desviada y esta antena no tiene margen de corte/tramos: corrígela con la red en π o rediseña.', 100*desvio))
    else:
        rec['acciones'].append(tr('La resonancia ya está en la frecuencia objetivo.'))
    # 2) adaptación: red L con la impedancia medida en f_obj (trasladada a la posición de la red)
    k = int(np.argmin(np.abs(f - f_obj)))
    zl = 50*(1 + s11[k])/(1 - s11[k])
    if distancia_red_mm and eps_eff:
        # quitar la línea entre el conector y la red (sin pérdidas)
        t = math.tan(2*math.pi*f_obj*math.sqrt(eps_eff)/299792458.0*distancia_red_mm*1e-3)
        zl = 50*(zl - 1j*50*t)/(50 - 1j*zl*t)
    rec['Z_en_f_obj_ohm'] = [round(float(zl.real), 1), round(float(zl.imag), 1)]
    rec['f_Hz'], rec['s11'] = f, s11
    rec['s11_en_f_obj_dB'] = round(float(db[k]), 1)
    if aj.get('componentes') and any(c['ref'] == 'Z1' for c in aj['componentes']):
        if db[k] < -15:
            rec['acciones'].append(tr('Adaptación ya buena en la frecuencia objetivo: deja Z1 = 0 Ω y Z2/Z3 sin montar.'))
        else:
            sols = redes_l(zl, f_obj)
            rec['redes'] = sols
            if sols:
                s = sols[0]
                rec.update(_efecto_red(f, s11, f_obj, s, distancia_red_mm, eps_eff))
                txt = lambda c: '0 Ω' if c[0] == '0 Ω' else (f'{c[1]:g} nH' if c[0] == 'L' else f'{c[1]:g} pF')
                rec['acciones'].append(tr('Red en π: Z1 (serie) = {0}, {1} (a masa) = {2}, la otra derivación sin montar (|S11| calculado {3} dB con valores comerciales).', txt(s["serie"]), s["posicion"], txt(s["derivacion"]), s["s11_dB"]))
    return rec
