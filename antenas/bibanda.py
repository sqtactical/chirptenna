"""Variantes de dos bandas (868/915 MHz + 2,4 GHz) de la J-pole recta y de la IFA.

Salen de las pruebas de `herramientas/jpole_dual.py` (modo union) y `herramientas/rama_dual.py`; las medidas fijas de la banda
alta son las de esas pruebas. La banda alta es siempre la de 2,4 GHz (2441,75 MHz); la baja es la del diseño, y las medidas de
la baja se escalan con λ a partir de 868 MHz (referencia: `ancho_pista` = 2,81 mm a 868 MHz, que `dimensionar` escala con λ).

* J-pole recta, «dos J-pole unidas»: comparten el brazo corto (masa) y la barra de cortocircuito. A la izquierda se añade el brazo
  largo de la segunda, con un adaptador de ~18,5 mm y un radiador de ~51 mm que se desvía 3 mm hacia fuera. Los dos brazos largos
  (el «vivo») se unen con una tira en B.Cu y una vía en cada extremo. Simulada: −11,2 dB (868 MHz) y −10,6 dB (2,4 GHz).
* IFA con segunda rama: un segundo brazo horizontal más corto, desde el pie de la F, a 0,6 × la altura. Simulada: −11,7 dB
  (868 MHz) y −10,8 dB (2,4 GHz).
"""
from shapely.ops import unary_union

from . import geometria as g

F_BAJA_REF = 868.0               # MHz: frecuencia a la que están medidas las constantes
F_ALTA = 2441.75                 # MHz: centro de la banda alta
ANCHO_REF = 2.81                 # mm: ancho de pista de la J-pole/IFA a 868 MHz
# J-pole unida (valores a 868 MHz y 2,4 GHz; la banda alta no cambia con la baja, así que sus medidas son fijas)
JPOLE_RADIADOR_REF = 143.94      # mm: largo del radiador de la banda baja a 868 MHz (con la calibración anterior al hueco ampliado)
JPOLE_FACTOR_ADAPTADOR = 0.95
JPOLE_TOMA = 0.2
JPOLE_ADAPTADOR2 = 18.53         # mm: 0,9 × λ/4 de 2,4 GHz sobre el adaptador de 868 MHz (57,92 mm × 868/2441,75 × 0,9)
JPOLE_RADIADOR2 = 51.17          # mm: λ/2 de 2,4 GHz según el radiador de 868 MHz (143,94 × 868/2441,75)
JPOLE_SEP2 = 3.0                 # mm: desvío del radiador 2 hacia fuera
JPOLE_TOMA2 = 0.25               # fracción del adaptador 2
# IFA con segunda rama
IFA_X_BRAZO = 1.17               # el brazo principal se alarga ×1,17 para centrar la banda baja
IFA_H2 = 0.6                     # altura de la rama 2 (fracción de la del brazo principal)
IFA_RAMA_REF = 27.26             # mm: largo equivalente de la rama 2 a 868 MHz (k2 = 1: (48,71 × 1,17 + 19,69) × 868/2441,75)


def escala(p):
    """Factor de escala de las medidas de la banda baja respecto a 868 MHz (λ_diseño / λ_868)."""
    return float(p.get('ancho_pista', ANCHO_REF))/ANCHO_REF


def jpole_unida(a, p):
    """Añade a la J-pole recta `a` (ya generada con los parámetros `p`) el brazo de la segunda banda."""
    w = p['ancho_pista']
    gap = p['hueco']
    xl, xr = -(gap/2 + w/2), gap/2 + w/2
    x2 = xl - (gap + w)
    x3 = x2 - JPOLE_SEP2
    ls2, l2 = JPOLE_ADAPTADOR2, JPOLE_RADIADOR2
    piezas = [a.capas['F.Cu'],
              g.engordar([(x2, ls2), (x2, 0), (xl, 0)], w),               # brazo largo 2 y barra hasta el brazo corto
              g.engordar([(x2, ls2), (x3, ls2)], w),                      # desvío hacia fuera
              g.engordar([(x3, ls2), (x3, ls2 + l2)], w)]                 # radiador 2
    cobre = unary_union(piezas)
    y_t1 = a.puerto['alimentacion'][1]
    y_t2 = JPOLE_TOMA2*ls2
    a.capas['F.Cu'] = cobre
    a.capas['B.Cu'] = g.engordar([(xr, y_t1), (x2, y_t2)], w)             # tira que une los dos «vivos»
    a.vias = [(xr, y_t1), (x2, y_t2)]
    a.radiador = cobre
    margen = p.get('margen_borde', 2.0)
    a.contorno = g.contorno_placa([unary_union([cobre, a.capas['B.Cu']]).buffer(margen)], int(p.get('contorno', 1)))
    a.zona_libre = a.contorno
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, gap)
    a.info['pista_minima_mm'] = min(a.info.get('pista_minima_mm') or 99, w)
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_radiador2_mm'] = round(l2, 2)
    a.info['largo_adaptador2_mm'] = round(ls2, 2)
    return a


def ifa_dos_ramas(a, p, lg):
    """Añade a la IFA `a` la rama de la segunda banda. `lg`: y a la que arranca el radiador (alto de la masa)."""
    w = p.get('ancho_pista', 1.0)
    h = p['altura']
    y2 = lg + IFA_H2*h
    l2 = IFA_RAMA_REF*escala(p)
    rama = g.engordar([(0.0, y2), (l2 - IFA_H2*h, y2)], w)
    a.capas['F.Cu'] = unary_union([a.capas['F.Cu'], rama])
    margen = p.get('margen_borde', 2.0)
    a.radiador = unary_union([a.radiador, rama])
    a.contorno = unary_union([a.contorno, rama.buffer(margen)])
    a.zona_libre = unary_union([a.zona_libre, rama.buffer(margen)])
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, (1 - IFA_H2)*h - w)
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_rama2_mm'] = round(l2 - IFA_H2*h, 2)
    return a
