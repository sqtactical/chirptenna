"""Curvas fractales y utilidades geométricas. Unidades: mm, eje y hacia arriba."""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity


# ------------------------------------------------------------------ sistemas L
def sistema_l(axioma, reglas, iteraciones):
    s = axioma
    for _ in range(iteraciones):
        s = ''.join(reglas.get(c, c) for c in s)
    return s


def tortuga(cadena, angulo_grados, paso=1.0, rumbo_inicial=0.0):
    """Recorre la cadena: F/G avanzan dibujando, + gira a la izquierda, - a la derecha."""
    x, y, a = 0.0, 0.0, math.radians(rumbo_inicial)
    da = math.radians(angulo_grados)
    pts = [(x, y)]
    for c in cadena:
        if c in 'FG':
            x += paso*math.cos(a)
            y += paso*math.sin(a)
            pts.append((round(x, 9), round(y, 9)))
        elif c == '+':
            a += da
        elif c == '-':
            a -= da
    return np.array(pts)


def ajustar_extremos(pts, p0, p1):
    """Escala y gira una polilínea para que vaya exactamente de p0 a p1."""
    a, b = pts[0], pts[-1]
    v, w = b - a, np.array(p1) - np.array(p0)
    escala = np.linalg.norm(w)/np.linalg.norm(v)
    giro = math.atan2(w[1], w[0]) - math.atan2(v[1], v[0])
    c, s = math.cos(giro), math.sin(giro)
    rot = np.array([[c, -s], [s, c]])
    return (pts - a) @ rot.T*escala + np.array(p0)


# ------------------------------------------------------------------ curvas
def koch(iteraciones, p0=(0, 0), p1=(1, 0), angulo=60.0):
    """Curva de Koch (con ángulo de indentación configurable; 60° es la clásica)."""
    cadena = sistema_l('F', {'F': 'F+F--F+F'}, iteraciones)
    pts = tortuga(cadena, angulo)
    return ajustar_extremos(pts, p0, p1)


def isla_minkowski(esquinas, iteraciones, profundidad=0.5):
    """Polígono con bordes de Minkowski: cada tramo se parte en tercios y el central se
    sustituye por una muesca rectangular hacia DENTRO de profundidad = profundidad·(tramo/3).

    esquinas en sentido antihorario (así la normal izquierda apunta hacia dentro).
    """
    pts = [np.array(e, float) for e in esquinas]
    for _ in range(iteraciones):
        nuevos = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            d = b - a
            n = np.array([-d[1], d[0]])/np.linalg.norm(d)      # normal izquierda = hacia dentro
            t1, t2 = a + d/3, a + 2*d/3
            prof = profundidad*np.linalg.norm(d)/3
            nuevos += [a, t1, t1 + n*prof, t2 + n*prof, t2]
        pts = nuevos
    return Polygon(pts).buffer(0)


def hilbert(orden):
    """Curva de Hilbert de orden n en el cuadrado unidad; empieza en (0,0) y acaba en (1,0)."""
    cadena = sistema_l('A', {'A': '+BF-AFA-FB+', 'B': '-AF+BFB+FA-'}, orden)
    pts = tortuga(cadena, 90.0)
    pts = pts - pts.min(0)
    return pts/max(pts.max(), 1e-12)


def meandro(n_vueltas, ancho, alto):
    """Meandro vertical: sube 'alto' haciendo n_vueltas idas y vueltas de 'ancho'."""
    paso = alto/(2*n_vueltas)
    pts = [(0.0, 0.0)]
    y = 0.0
    for i in range(n_vueltas):
        y += paso
        pts += [(0.0, y), (ancho, y)]
        y += paso
        pts += [(ancho, y), (0.0, y)]
    return np.array(pts)


def sierpinski(iteraciones, base, alto, cuello=0.0):
    """Triángulo de Sierpinski (vértice abajo, en el origen) como polígono.

    cuello: ancho aproximado de las uniones entre triángulos [mm]. Sin él se tocan en un punto
    (ancho cero): no se puede fabricar y en la simulación la conexión depende de la malla.
    Se engorda cada triángulo cuello/3,2 (el cuello sale ≈ 3,2 × el engorde) y se recorta al
    triángulo exterior, así que solo encogen los huecos.
    """
    v = [np.array([0.0, 0.0]), np.array([-base/2, alto]), np.array([base/2, alto])]
    tri = [v]
    for _ in range(iteraciones):
        nuevos = []
        for a, b, c in tri:
            ab, bc, ca = (a + b)/2, (b + c)/2, (c + a)/2
            nuevos += [[a, ab, ca], [ab, b, bc], [ca, bc, c]]
        tri = nuevos
    pols = [Polygon(t) for t in tri]
    if cuello <= 0:
        # se engorda un pelo para fundir los que se tocan en un vértice
        return unary_union([p.buffer(1e-6) for p in pols])
    return unary_union([p.buffer(cuello/3.2, join_style='mitre') for p in pols]).intersection(Polygon(v))


# ------------------------------------------------------------------ polígonos
def engordar(polilinea, ancho):
    """Convierte una polilínea en una pista de ancho dado (esquinas a inglete, extremos planos)."""
    return LineString(polilinea).buffer(ancho/2, cap_style='flat', join_style='mitre', mitre_limit=2.0)


def rectangulo(x0, y0, x1, y1):
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def longitud(polilinea):
    d = np.diff(np.asarray(polilinea), axis=0)
    return float(np.sum(np.hypot(d[:, 0], d[:, 1])))


def poligonos(geom):
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, 'geoms', []) if isinstance(g, Polygon)]


def mover(geom, dx, dy):
    return affinity.translate(geom, dx, dy)


def contorno_placa(partes, modo, recorte=None, redondeo=1.5):
    """Contorno de la placa que envuelve las partes (ya engordadas con el margen).

    modo 0: rectángulo envolvente. modo 1: envolvente convexa con las esquinas redondeadas
    (sigue la forma de la antena y recorta la placa sobrante).
    recorte: (x0, y0, x1, y1) opcional; la placa no sale de esa caja (p. ej. el borde del SMA).
    """
    u = unary_union(partes)
    if modo == 0:
        c = box(*u.bounds)
    else:
        c = u.convex_hull
        if redondeo > 0:
            c = c.buffer(-redondeo, join_style='round').buffer(redondeo, join_style='round')
    if recorte is not None:
        c = c.intersection(box(*recorte))
    return c


def sin_agujeros(pol):
    """Parte un polígono con agujeros en trozos sin agujeros (KiCad y CSXCAD no admiten huecos)."""
    from shapely.ops import split
    pendientes, listos = [pol], []
    while pendientes:
        p = pendientes.pop()
        if not p.interiors:
            listos.append(p)
            continue
        cx = p.interiors[0].centroid.x
        corte = LineString([(cx, p.bounds[1] - 1), (cx, p.bounds[3] + 1)])
        for trozo in split(p, corte).geoms:
            if trozo.area > 1e-6:
                pendientes.append(trozo)
    return listos
