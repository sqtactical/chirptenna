"""Entorno de la antena en la simulación: carcasa, batería, mano (F3.7).

Cada bloque es un dict {'nombre', 'tipo': 'dielectrico' o 'metal', 'caja': (x0, y0, z0, x1, y1, z1) en mm, 'er', 'tand'
y, opcional, 'sigma' en S/m}. `simulacion.simular` los pone con prioridad menor que el cobre y lleva sus caras a la malla.
Las cajas de los predefinidos se calculan a partir de la placa: y hacia arriba como en el modelo, z = 0 la cara inferior y
z = h la superior.
"""
from .i18n import tr

# nombre interno -> texto de la interfaz (castellano; la interfaz lo traduce al mostrarlo)
PREDEFINIDOS = {
    'carcasa': 'Carcasa de ABS (1,5 mm de pared, a 1 mm de la placa)',
    'bateria': 'Batería (bloque metálico de 40 × 60 × 8 mm detrás de la placa, a 1 mm)',
    'mano': 'Mano (80 × 40 × 20 mm, εr 30, 1 S/m, a 5 mm por debajo)',
}
ABS = {'er': 2.8, 'tand': 0.01}
MANO = {'er': 30.0, 'tand': 0.0, 'sigma': 1.0}


def neutro(bloque):
    """El mismo bloque convertido en aire (εr 1, sin pérdidas): sirve de control con la misma malla."""
    return {**bloque, 'tipo': 'dielectrico', 'er': 1.0, 'tand': 0.0, 'sigma': 0.0}


def bloques(antena, h, nombres):
    """Bloques de los predefinidos pedidos (lista de nombres de `PREDEFINIDOS`) para esta placa de grosor h [mm]."""
    x0, y0, x1, y1 = antena.contorno.bounds
    cx, cy = (x0 + x1)/2, (y0 + y1)/2
    out = []
    for n in nombres:
        if n == 'carcasa':
            m, pared, sep = 3.0, 1.5, 1.0               # la carcasa sobresale 3 mm de la placa
            for z0, z1 in ((h + sep, h + sep + pared), (-sep - pared, -sep)):
                out.append({'nombre': 'carcasa', 'tipo': 'dielectrico', 'caja': (x0 - m, y0 - m, z0, x1 + m, y1 + m, z1), **ABS})
        elif n == 'bateria':
            ancho = min(40.0, 0.8*(x1 - x0))
            largo = min(60.0, 0.5*(y1 - y0))
            # detrás de la placa (la masa apantalla la línea de alimentación), en su parte baja, lejos de la antena, a 1 mm
            out.append({'nombre': 'bateria', 'tipo': 'metal',
                        'caja': (cx - ancho/2, y0 + 2.0, -9.0, cx + ancho/2, y0 + 2.0 + largo, -1.0), 'er': 1.0, 'tand': 0.0})
        elif n == 'mano':
            out.append({'nombre': 'mano', 'tipo': 'dielectrico', 'caja': (cx - 20.0, cy - 40.0, -25.0, cx + 20.0, cy + 40.0, -5.0), **MANO})
        else:
            raise KeyError(tr('Entorno desconocido: {0}', n))
    return out
