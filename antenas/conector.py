"""Conector de la placa de prueba: SMA de canto (por defecto) o IPEX / U.FL (MHF1).

Con SMA el cobre del modelo no cambia: la línea de 50 Ω llega al borde y la huella se añade al
exportar. Con IPEX el conector va encima de la placa, a unos milímetros del borde: la línea
empieza en su pad central (estrechándose hasta él) y los pads de masa de la cara superior se unen
a la masa inferior con vías (solo en KiCad; en la simulación el puerto va en el pad central).
Huella según el patrón recomendado por Hirose para U.FL-R-SMT-1.

Ejes locales: u hacia dentro de la placa (a lo largo de la línea, desde el borde), v transversal.
"""
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union
from .i18n import tr

BORDE_COBRE = 0.5                  # donde empieza la línea con SMA (retranqueo del cobre) [mm]
SMA, IPEX = 0, 1
NOMBRES = {SMA: 'SMA de canto', IPEX: 'IPEX / U.FL (MHF1)'}
MASA_MINIMA = {SMA: 12.0, IPEX: 7.0}       # largo mínimo de la masa de los monopolos [mm]
ANCHO_MINIMO = {SMA: 16.0, IPEX: 8.0}      # ancho mínimo de la placa de los monopolos [mm]

IPEX_CENTRO = 3.0                  # del borde de la placa al centro del conector [mm]
U_SENAL, PAD_SENAL = 1.5, (1.05, 1.0)          # pad central: centro en u y tamaño (u, v)
U_MASA, V_MASA, PAD_MASA = -0.975, 1.475, (2.2, 1.05)
V_VIA = 2.7                        # vías de masa al lado de cada pad de masa
TRANSICION = 1.0                   # estrechamiento del pad central a la línea de 50 Ω [mm]


def tipo(p):
    return int(p.get('conector', SMA))


def largo_ocupado():
    """mm desde el borde que ocupa el IPEX hasta donde la línea ya tiene su ancho."""
    return IPEX_CENTRO + U_SENAL + PAD_SENAL[0]/2 + TRANSICION


def _local(puerto):
    bx, by = puerto['borde']
    dx, dy = puerto['direccion']
    return lambda u, v: (bx + dx*u - dy*v, by + dy*u + dx*v)


def _caja(loc, u0, u1, v0, v1):
    return Polygon([loc(u0, v0), loc(u1, v0), loc(u1, v1), loc(u0, v1)])


def aplicar_ipex(antena, w50):
    """Cambia el arranque de la línea de 50 Ω por el pad central del IPEX (en el sitio)."""
    loc = _local(antena.puerto)
    u_pad = IPEX_CENTRO + U_SENAL
    u_fin = largo_ocupado()
    a_pad = PAD_SENAL[1]/2
    sup = antena.cobre('F.Cu')
    corte = _caja(loc, -1.0, u_fin, -w50/2 - 0.05, w50/2 + 0.05)
    quitado = sup.intersection(corte).area
    nuevo = unary_union([
        _caja(loc, u_pad - PAD_SENAL[0]/2, u_pad + PAD_SENAL[0]/2, -a_pad, a_pad),
        Polygon([loc(u_pad + PAD_SENAL[0]/2 - 0.01, -a_pad), loc(u_fin, -w50/2),
                 loc(u_fin, w50/2), loc(u_pad + PAD_SENAL[0]/2 - 0.01, a_pad)]),
        _caja(loc, u_fin - 0.01, u_fin + 0.05, -w50/2, w50/2)])
    antena.capas['F.Cu'] = unary_union([sup.difference(corte), nuevo])
    antena.puerto['conector'] = IPEX
    if antena.puerto.get('largo_linea_mm'):
        antena.puerto['largo_linea_mm'] -= u_pad - antena.puerto.get('inicio_mm', BORDE_COBRE)
    antena.puerto['inicio_mm'] = u_pad
    antena.puerto['ancho_puerto'] = PAD_SENAL[1]
    avisos = antena.info.setdefault('avisos', [])
    if quitado > 1.05*w50*(u_fin + 1.0):
        avisos.append(tr('El IPEX ocupa {0:.1f} mm desde el borde y pisa cobre que no es la línea de 50 Ω: alarga la línea de alimentación.', u_fin))
    return antena


def pads_ipex(puerto):
    """Pads del IPEX en coordenadas del modelo: [(nombre, (x, y), (tam_x, tam_y))] y vías [(x, y)]."""
    loc = _local(puerto)
    dx, dy = puerto['direccion']
    girar = abs(dy) > 0.5                    # u va por y: el tamaño (u, v) pasa a (v, u) en (x, y)
    tam = lambda t: (t[1], t[0]) if girar else t
    pads = [('1', loc(IPEX_CENTRO + U_SENAL, 0.0), tam(PAD_SENAL))]
    vias = []
    for s in (-1, 1):
        pads.append(('2', loc(IPEX_CENTRO + U_MASA, s*V_MASA), tam(PAD_MASA)))
        vias.append(loc(IPEX_CENTRO + U_MASA, s*V_VIA))
    return pads, vias, loc(IPEX_CENTRO, 0.0)
