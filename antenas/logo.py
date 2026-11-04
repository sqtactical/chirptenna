"""Logo de Chirptenna como geometría (shapely) para la serigrafía de las placas.

Es el grillo de `docs/logo/generar_logo.py` (antenas en curva de Koch, patas, cuerpo) en una sola tinta:
silueta rellena con los ojos, la separación cabeza/tórax/abdomen y el ala como huecos, más la palabra
«Chirptenna» como contorno de letra (DejaVu Sans Bold, la del logo). Todo en mm, construido ya a la
escala final para que ningún trazo baje del mínimo de serigrafía de JLC.
"""
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from . import geometria as g

TRAZO_MIN = 0.16          # mm: trazo y hueco mínimos de serigrafía (JLC: 0,153 mm)
ALTO_GRILLO = 7.9         # alto del dibujo original (unidades de generar_logo.py)
ALTO_MIN_MM = 7.0         # por debajo, las antenas de Koch y las patas ya no se distinguen


def _antena(lado):
    s = lado
    arco = [(s*0.12, 1.25), (s*0.75, 2.35), (s*1.55, 3.05), (s*2.55, 3.45)]
    pts = []
    for a, b in zip(arco, arco[1:]):
        tramo = g.koch(2, a, b, 60.0) if s > 0 else g.koch(2, b, a, 60.0)[::-1]
        pts.extend(tramo if not pts else tramo[1:])
    return pts


def _valida(geom):
    """Solo polígonos válidos (las uniones de curvas de Koch engordadas dejan a veces anillos que se cruzan)."""
    import shapely
    from shapely.geometry import MultiPolygon
    # rejilla de 1 µm: sin ella quedan segmentos casi coincidentes y GEOS falla ("non-noded intersection")
    geom = shapely.set_precision(shapely.make_valid(geom), 1e-3)
    if geom.geom_type == 'GeometryCollection':
        geom = MultiPolygon([p for p in g.poligonos(unary_union([x for x in geom.geoms
                                                                if x.geom_type in ('Polygon', 'MultiPolygon')]))])
    return geom


def _elipse(cx, cy, ancho, alto):
    return affinity.scale(Point(cx, cy).buffer(1.0, 64), ancho/2, alto/2)


def grillo(alto_mm):
    """Silueta del grillo de `alto_mm` de alto, centrada en el origen (y hacia arriba)."""
    k = alto_mm/ALTO_GRILLO

    def ancho(w):                     # ancho de trazo en unidades del dibujo, sin bajar del mínimo
        return max(w, TRAZO_MIN/k)

    def linea(pts, w):
        return LineString(pts).buffer(ancho(w)/2, cap_style='round', join_style='round')

    partes = []
    for s in (1, -1):
        partes.append(g.engordar(np.array(_antena(s)), ancho(0.10)))
        partes.append(linea([(s*0.42, 0.45), (s*1.05, 0.95), (s*1.25, 1.45)], 0.13))     # patas delanteras
        partes.append(linea([(s*0.5, 0.0), (s*1.25, -0.15), (s*1.6, 0.25)], 0.13))         # medias
        partes.append(linea([(s*0.55, -0.55), (s*1.35, -1.25), (s*1.2, -2.55)], 0.26))    # fémur
        partes.append(linea([(s*1.2, -2.55), (s*1.55, -3.35)], 0.11))                      # tibia
        partes.append(linea([(s*0.18, -2.95), (s*0.42, -3.6)], 0.09))                      # cercos
    abdomen = _elipse(0, -1.45, 1.35, 2.75)
    torax = _elipse(0, 0.35, 1.25, 0.95)
    cabeza = Point(0, 1.05).buffer(0.48, 64)
    cuerpo = unary_union([abdomen, torax, cabeza])
    silueta = unary_union(partes + [cuerpo])
    # Huecos: separación cabeza / tórax / abdomen, contorno y nervio del ala, ojos
    hueco = ancho(0.07)/2
    cortes = [cabeza.boundary.buffer(hueco).intersection(torax),
              torax.boundary.buffer(hueco).intersection(abdomen).difference(torax),
              Polygon([(0, -0.55), (0.55, -1.25), (0.33, -2.6), (0, -2.7), (-0.33, -2.6), (-0.55, -1.25)])
              .boundary.buffer(hueco),
              LineString([(0, -0.6), (0, -2.65)]).buffer(hueco)]
    for s in (1, -1):
        cortes.append(Point(s*0.25, 1.2).buffer(max(0.11, ancho(0.07)), 32))
    silueta = _valida(silueta).difference(_valida(unary_union(cortes)))
    silueta = _valida(affinity.scale(silueta, k, k, origin=(0, 0)))
    x0, y0, x1, y1 = silueta.bounds
    return affinity.translate(silueta, -(x0 + x1)/2, -(y0 + y1)/2)


def texto(cadena, alto_mm):
    """Texto como polígonos (DejaVu Sans Bold); `alto_mm` es la altura de las mayúsculas."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), cadena, size=1.0, prop=FontProperties(family='DejaVu Sans', weight='bold'))
    geom = Polygon()
    for anillo in tp.to_polygons():
        if len(anillo) >= 3:
            geom = geom.symmetric_difference(Polygon(anillo).buffer(0))     # par-impar: huecos de las letras
    alto_cap = TextPath((0, 0), 'H', size=1.0, prop=FontProperties(family='DejaVu Sans', weight='bold')) \
        .get_extents().height
    k = alto_mm/alto_cap
    geom = _valida(affinity.scale(geom, k, k, origin=(0, 0)))
    x0, y0, x1, y1 = geom.bounds
    return affinity.translate(geom, -(x0 + x1)/2, -(y0 + y1)/2)


def bloque(alto_mm, disposicion='horizontal'):
    """Logo completo (grillo + «Chirptenna») centrado en el origen.

    disposicion: 'horizontal' (grillo a la izquierda, nombre a la derecha), 'vertical' (nombre debajo) o
    'icono' (solo el grillo, para placas muy estrechas)."""
    gr = grillo(alto_mm)
    if disposicion == 'icono':
        return gr
    if disposicion == 'horizontal':
        tx = texto('Chirptenna', 0.26*alto_mm)
        gx0, _, gx1, _ = gr.bounds
        tx0, _, tx1, _ = tx.bounds
        sep = 0.12*alto_mm
        tx = affinity.translate(tx, gx1 + sep - tx0, 0.05*alto_mm)
    else:
        tx = texto('Chirptenna', max(0.15*alto_mm, 1.3))
        _, gy0, _, _ = gr.bounds
        _, ty0, _, ty1 = tx.bounds
        tx = affinity.translate(tx, 0, gy0 - 0.08*alto_mm - ty1)
    todo = _valida(unary_union([gr, tx]))
    x0, y0, x1, y1 = todo.bounds
    return affinity.translate(todo, -(x0 + x1)/2, -(y0 + y1)/2)
