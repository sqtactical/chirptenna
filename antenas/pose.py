"""Posición y giro de una placa en el espacio (antenas de varias placas no coplanares: diedro, reflector de esquina).

Una pieza de `Antena.placas3d` lleva sus coordenadas locales (la placa plana en XY con z = 0 en la cara inferior y z = h en la superior, como
el resto del proyecto) y una pose: primero los `giros` [(eje, grados), …] alrededor del origen local, en orden (0 = X, 1 = Y, 2 = Z; regla de la
mano derecha, la misma de `CSXCAD`: `AddTransform('RotateAxis', eje, grados)`), y después el desplazamiento `origen`.
"""
import numpy as np


def matriz(eje, grados):
    """Matriz de giro de `grados` alrededor del eje 0 (X), 1 (Y) o 2 (Z)."""
    a = np.radians(grados)
    c, s = np.cos(a), np.sin(a)
    if eje == 0:
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if eje == 1:
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def aplicar(puntos, pieza):
    """Puntos (n, 3) locales de la pieza → coordenadas del modelo."""
    p = np.asarray(puntos, float).reshape(-1, 3)
    for eje, grados in pieza.get('giros', []):
        p = p @ matriz(int(eje), float(grados)).T
    return p + np.asarray(pieza.get('origen', (0.0, 0.0, 0.0)), float)


def caja(pieza, h):
    """((x0, y0, z0), (x1, y1, z1)): caja que envuelve la placa de la pieza, de grosor `h`, ya colocada."""
    x0, y0, x1, y1 = pieza['antena'].contorno.bounds
    esq = np.array([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (0.0, h)])
    q = aplicar(esq, pieza)
    return q.min(axis=0), q.max(axis=0)


def caja_conjunto(antena, h):
    """Caja que envuelve las placas y los hilos 3D de una antena (None si no tiene)."""
    cajas = [caja(pl, h) for pl in (antena.placas3d or [])]
    for hl in antena.hilos3d or []:
        pts = np.asarray(hl['puntos'], float).reshape(-1, 3)
        cajas.append((pts.min(axis=0), pts.max(axis=0)))
    if not cajas:
        return None
    return np.min([c[0] for c in cajas], axis=0), np.max([c[1] for c in cajas], axis=0)
