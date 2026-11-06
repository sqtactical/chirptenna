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
    'sin_ajuste': [],                      # tipos sin opciones de ajuste todavía (Yagi con boom)
}


def parametros_para(grupo):
    return [PARAMS_AJUSTE[n] for n in POR_FAMILIA[grupo]]


def activo(p):
    return int(p.get('ajuste', 0)) == 1


def vacio():
    return {'componentes': [], 'cortes': [], 'puentes_sim': [], 'islas_masa': [], 'vias_masa': [],
            'marcas': [], 'tramos': 0, 'notas': []}


def unir(a, b):
    for k in ('componentes', 'cortes', 'puentes_sim', 'islas_masa', 'vias_masa', 'marcas', 'notas'):
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
                txt = lambda c: '0 Ω' if c[0] == '0 Ω' else (f'{c[1]:g} nH' if c[0] == 'L' else f'{c[1]:g} pF')
                rec['acciones'].append(tr('Red en π: Z1 (serie) = {0}, {1} (a masa) = {2}, la otra derivación sin montar (|S11| calculado {3} dB con valores comerciales).', txt(s["serie"]), s["posicion"], txt(s["derivacion"]), s["s11_dB"]))
    return rec
