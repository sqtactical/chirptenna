"""Importar la placa de un producto desde un `.kicad_pcb` (F3.6).

Lee el contorno (`Edge.Cuts`), el cobre de cada capa, los taladros y el grosor, y lo deja en milímetros con el eje y
hacia arriba y la esquina inferior izquierda del contorno en (0, 0), que es el sistema del modelo. Sin dependencias
más allá de shapely, para que funcione también en la versión web.

Lo que entiende (formato de KiCad 7–10): `gr_line`, `gr_arc` (inicio, punto medio y fin), `gr_rect`, `gr_circle`, `gr_poly`
en `Edge.Cuts`, también dentro de huellas (`fp_*`); cobre de zonas rellenas (`filled_polygon`), pistas (`segment`, `arc`),
vías, pads (círculo, rectángulo, óvalo, rectángulo redondeado como rectángulo, y los de forma libre con sus primitivas)
y `gr_poly` en capas de cobre. Lo demás se ignora y se anota en `avisos`.
"""
import math

from shapely import affinity
from shapely import wkt as _wkt
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import polygonize, unary_union

from . import sexp
from .i18n import tr

FLECHA_MAX = 0.1             # flecha máxima al discretizar un arco [mm]
CERRAR_HUECOS = 1.0          # huecos de cobre más finos que esto se cierran al usarlo como masa [mm]


# --- geometría básica ---------------------------------------------------------------------------------------------

def _xy(nodo, nombre):
    n = sexp.hijo(nodo, nombre)
    return (float(n[1]), float(n[2])) if n and len(n) >= 3 else None


def _arco(a, m, b):
    """Puntos de un arco que pasa por a, m, b (tres puntos), con flecha ≤ FLECHA_MAX."""
    ax, ay = a
    mx, my = m
    bx, by = b
    d = 2*(ax*(my - by) + mx*(by - ay) + bx*(ay - my))
    if abs(d) < 1e-12:
        return [a, b]
    ux = ((ax**2 + ay**2)*(my - by) + (mx**2 + my**2)*(by - ay) + (bx**2 + by**2)*(ay - my))/d
    uy = ((ax**2 + ay**2)*(bx - mx) + (mx**2 + my**2)*(ax - bx) + (bx**2 + by**2)*(mx - ax))/d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(y - uy, x - ux) for x, y in (a, m, b))
    # sentido: el que pasa por el punto medio
    s = (a1 - a0) % (2*math.pi)
    if (am - a0) % (2*math.pi) > s:
        s -= 2*math.pi
    paso = 2*math.acos(max(0.0, 1 - FLECHA_MAX/r)) if r > FLECHA_MAX else math.pi/4
    n = max(2, int(math.ceil(abs(s)/max(paso, 1e-3))))
    return [(ux + r*math.cos(a0 + s*i/n), uy + r*math.sin(a0 + s*i/n)) for i in range(n + 1)]


def _circulo(centro, radio):
    return Point(centro).buffer(radio, quad_segs=max(8, int(math.pi/max(2*math.acos(max(0.0, 1 - FLECHA_MAX/max(radio, 0.2))), 1e-3))))


def _gira(x, y, grados):
    """Rotación de KiCad (y hacia abajo, positivo = antihorario en pantalla)."""
    a = math.radians(grados)
    return x*math.cos(a) + y*math.sin(a), -x*math.sin(a) + y*math.cos(a)


def _capa(nodo):
    c = sexp.hijo(nodo, 'layer')
    return str(c[1]) if c and len(c) > 1 else ''


def _capas_de(nodo):
    c = sexp.hijo(nodo, 'layers')
    return [str(x) for x in c[1:]] if c else []


# --- elementos ---------------------------------------------------------------------------------------------------

def _linea_borde(nodo, tipo, mover):
    """Línea (LineString) o polígono cerrado de una primitiva de Edge.Cuts. mover: (x, y) → (x, y) absoluto."""
    if tipo in ('gr_line', 'fp_line'):
        return LineString([mover(*_xy(nodo, 'start')), mover(*_xy(nodo, 'end'))])
    if tipo in ('gr_arc', 'fp_arc'):
        if sexp.hijo(nodo, 'mid') is None:
            raise ValueError('arco con el formato antiguo (sin punto medio)')
        pts = _arco(_xy(nodo, 'start'), _xy(nodo, 'mid'), _xy(nodo, 'end'))
        return LineString([mover(*q) for q in pts])
    if tipo in ('gr_rect', 'fp_rect'):
        (x0, y0), (x1, y1) = _xy(nodo, 'start'), _xy(nodo, 'end')
        return LineString([mover(x0, y0), mover(x1, y0), mover(x1, y1), mover(x0, y1), mover(x0, y0)])
    if tipo in ('gr_circle', 'fp_circle'):
        cx, cy = _xy(nodo, 'center')
        ex, ey = _xy(nodo, 'end')
        r = math.hypot(ex - cx, ey - cy)
        c = _circulo((cx, cy), r)
        return LineString([mover(x, y) for x, y in c.exterior.coords])
    if tipo in ('gr_poly', 'fp_poly'):
        pts = [mover(float(q[1]), float(q[2])) for q in sexp.hijo(nodo, 'pts') if isinstance(q, list) and q[0] == 'xy']
        return LineString(pts + [pts[0]])
    return None


PRIMITIVAS_BORDE = ('gr_line', 'gr_arc', 'gr_rect', 'gr_circle', 'gr_poly')
PRIMITIVAS_FP = ('fp_line', 'fp_arc', 'fp_rect', 'fp_circle', 'fp_poly')


def _contorno(lineas):
    """Polígono de la placa a partir de las líneas de Edge.Cuts: el mayor, menos los recortes que contiene."""
    if not lineas:
        return None
    cerradas = [Polygon(l) for l in lineas if l.is_ring and len(l.coords) >= 4]
    abiertas = [l for l in lineas if not (l.is_ring and len(l.coords) >= 4)]
    piezas = list(cerradas)
    if abiertas:
        piezas += [pol for pol in polygonize(unary_union([_redondea(l) for l in abiertas]))]
    piezas = [pol.buffer(0) for pol in piezas if pol.area > 1e-6]
    if not piezas:
        return None
    piezas.sort(key=lambda pol: -pol.area)
    ext = piezas[0]
    for otra in piezas[1:]:
        if ext.contains(otra.representative_point()):
            ext = ext.difference(otra)
        else:
            ext = ext.union(otra)            # dos placas en el mismo fichero: se queda con todo
    return ext


def _redondea(linea):
    """Coordenadas al micrómetro: los extremos que casi se tocan se unen al polygonizar."""
    return LineString([(round(x, 3), round(y, 3)) for x, y in linea.coords])


def _forma_pad(pad, ox, oy, angulo):
    """Polígono del pad en absoluto: forma, tamaño y giro propios (`angulo` absoluto)."""
    tipo = str(pad[3]) if len(pad) > 3 else 'rect'
    sz = _xy(pad, 'size') or (0.0, 0.0)
    w, h = sz
    if tipo == 'circle':
        base = Point(0, 0).buffer(w/2, quad_segs=16)
    elif tipo == 'oval':
        corto, largo = min(w, h), max(w, h)
        seg = LineString([(-(largo - corto)/2, 0), ((largo - corto)/2, 0)]) if w >= h else \
            LineString([(0, -(largo - corto)/2), (0, (largo - corto)/2)])
        base = seg.buffer(corto/2, quad_segs=8)
    elif tipo == 'custom':
        anc = sexp.hijo(sexp.hijo(pad, 'options') or [], 'anchor')
        base = Point(0, 0).buffer(w/2, quad_segs=8) if anc and len(anc) > 1 and anc[1] == 'circle' else box(-w/2, -h/2, w/2, h/2)
        prims = [base]
        for pr in sexp.hijo(pad, 'primitives') or []:
            if not isinstance(pr, list):
                continue
            if pr[0] == 'gr_poly':
                pts = [(float(q[1]), float(q[2])) for q in sexp.hijo(pr, 'pts') if isinstance(q, list) and q[0] == 'xy']
                if len(pts) >= 3:
                    prims.append(Polygon(pts).buffer(0))
            elif pr[0] == 'gr_rect':
                (x0, y0), (x1, y1) = _xy(pr, 'start'), _xy(pr, 'end')
                prims.append(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
            elif pr[0] == 'gr_circle':
                cx, cy = _xy(pr, 'center')
                ex, ey = _xy(pr, 'end')
                prims.append(_circulo((cx, cy), math.hypot(ex - cx, ey - cy)))
            elif pr[0] == 'gr_line':
                an = sexp.hijo(pr, 'width')
                prims.append(LineString([_xy(pr, 'start'), _xy(pr, 'end')]).buffer(max(float(an[1]) if an else 0.1, 0.01)/2))
        base = unary_union(prims)
    else:                                   # rect, roundrect, trapezoid: se toma el rectángulo
        base = box(-w/2, -h/2, w/2, h/2)
    # Giro de KiCad (y abajo): el ángulo positivo gira en sentido antihorario en pantalla = horario en y-abajo con
    # la matriz normal, así que se aplica con signo negativo de shapely.
    base = affinity.rotate(base, -angulo, origin=(0, 0))
    return affinity.translate(base, ox, oy)


def _pad(pad, fp_at, fp_rot, capas_cobre):
    """(geometría, capas de cobre, taladro | None) de un pad de una huella."""
    lx, ly = _xy(pad, 'at')
    at = sexp.hijo(pad, 'at')
    angulo = float(at[3]) if len(at) > 3 else fp_rot
    dx, dy = _gira(lx, ly, fp_rot)
    ox, oy = fp_at[0] + dx, fp_at[1] + dy
    geo = _forma_pad(pad, ox, oy, angulo)
    capas = []
    for c in _capas_de(pad):
        if c == '*.Cu':
            capas = list(capas_cobre)
            break
        if c.endswith('.Cu'):
            capas.append(c)
    taladro = None
    d = sexp.hijo(pad, 'drill')
    if d and len(d) > 1:
        if d[1] == 'oval':
            dd = float(d[2]) if len(d) > 2 else 0.0
        else:
            dd = float(d[1])
        if dd > 0:
            taladro = (ox, oy, dd)
    return geo, capas, taladro


# --- lectura de la placa --------------------------------------------------------------------------------------------

def leer_texto(texto):
    """Ver `placa`. Recibe el texto del `.kicad_pcb`."""
    raiz = sexp.leer(texto)
    if not raiz or raiz[0] != 'kicad_pcb':
        raise ValueError(tr('No es un fichero de placa de KiCad (.kicad_pcb).'))
    avisos = []
    capas_cobre = []
    for c in sexp.hijo(raiz, 'layers') or []:
        if isinstance(c, list) and len(c) > 1 and str(c[1]).endswith('.Cu'):
            capas_cobre.append(str(c[1]))
    capas_cobre = capas_cobre or ['F.Cu', 'B.Cu']
    g = sexp.hijo(raiz, 'general')
    gr = sexp.hijo(g, 'thickness') if g else None
    grosor = float(gr[1]) if gr else 1.6

    borde, cobre, taladros = [], {c: [] for c in capas_cobre}, []
    noent = set()

    def ident(x, y):
        return x, y

    def lineas_borde(nodo, mover):
        for h in nodo:
            if not isinstance(h, list) or not h:
                continue
            t = str(h[0])
            if t in PRIMITIVAS_BORDE + PRIMITIVAS_FP and _capa(h) == 'Edge.Cuts':
                try:
                    l = _linea_borde(h, t, mover)
                    if l is not None:
                        borde.append(l)
                except (ValueError, TypeError) as e:
                    noent.add(f'{t}: {e}')
            elif t in ('gr_curve', 'fp_curve') and _capa(h) == 'Edge.Cuts':
                noent.add(t)

    lineas_borde(raiz, ident)
    for fp in sexp.hijos(raiz, 'footprint'):
        at = sexp.hijo(fp, 'at')
        if not at:
            continue
        pos = (float(at[1]), float(at[2]))
        rot = float(at[3]) if len(at) > 3 else 0.0
        lineas_borde(fp, lambda x, y, pos=pos, rot=rot: tuple(p + q for p, q in zip(pos, _gira(x, y, rot))))
        for pad in sexp.hijos(fp, 'pad'):
            try:
                geo, capas, tal = _pad(pad, pos, rot, capas_cobre)
            except (TypeError, ValueError, IndexError):
                noent.add('pad')
                continue
            for c in capas:
                cobre.setdefault(c, []).append(geo)
            if tal:
                taladros.append(tal)
        for h in sexp.hijos(fp, 'fp_poly'):           # cobre dibujado dentro de una huella
            c = _capa(h)
            if c.endswith('.Cu'):
                l = _linea_borde(h, 'fp_poly', lambda x, y, pos=pos, rot=rot: tuple(p + q for p, q in zip(pos, _gira(x, y, rot))))
                cobre.setdefault(c, []).append(Polygon(l).buffer(0))

    for z in sexp.hijos(raiz, 'zone'):
        rellenos = sexp.hijos(z, 'filled_polygon')
        for fpol in rellenos:
            pts = [(float(q[1]), float(q[2])) for q in sexp.hijo(fpol, 'pts') if isinstance(q, list) and q[0] == 'xy']
            if len(pts) >= 3:
                cobre.setdefault(_capa(fpol), []).append(Polygon(pts).buffer(0))
        if not rellenos:
            avisos.append(tr('Hay zonas de cobre sin rellenar: abre la placa en KiCad y pulsa B (rellenar zonas) antes de importarla.'))
    for s in sexp.hijos(raiz, 'segment') + sexp.hijos(raiz, 'arc'):
        c = _capa(s)
        if not c.endswith('.Cu'):
            continue
        an = sexp.hijo(s, 'width')
        ancho = float(an[1]) if an else 0.2
        if s[0] == 'segment':
            linea = LineString([_xy(s, 'start'), _xy(s, 'end')])
        else:
            linea = LineString(_arco(_xy(s, 'start'), _xy(s, 'mid'), _xy(s, 'end')))
        cobre.setdefault(c, []).append(linea.buffer(ancho/2, quad_segs=8))
    for v in sexp.hijos(raiz, 'via'):
        x, y = _xy(v, 'at')
        sz = sexp.hijo(v, 'size')
        dr = sexp.hijo(v, 'drill')
        d = float(sz[1]) if sz else 0.6
        for c in capas_cobre:
            cobre[c].append(Point(x, y).buffer(d/2, quad_segs=8))
        if dr and len(dr) > 1:
            taladros.append((x, y, float(dr[1])))
    for h in sexp.hijos(raiz, 'gr_poly'):
        c = _capa(h)
        if c.endswith('.Cu'):
            l = _linea_borde(h, 'gr_poly', ident)
            cobre.setdefault(c, []).append(Polygon(l).buffer(0))

    contorno = _contorno(borde)
    if contorno is None:
        raise ValueError(tr('La placa no tiene un contorno cerrado en la capa Edge.Cuts.'))
    if noent:
        avisos.append(tr('Elementos ignorados (no se entienden): {0}.', ', '.join(sorted(noent))))
    cobre = {c: unary_union(l) for c, l in cobre.items() if l}
    return _a_modelo({'contorno': contorno, 'cobre': cobre, 'taladros': taladros, 'grosor_mm': grosor,
                      'capas_cobre': capas_cobre, 'avisos': avisos})


def _a_modelo(d):
    """Pasa de KiCad (y abajo) al modelo (y arriba, esquina inferior izquierda del contorno en el origen)."""
    minx, _, _, maxy = d['contorno'].bounds
    m = [1, 0, 0, -1, -minx, maxy]
    out = dict(d)
    out['contorno'] = affinity.affine_transform(d['contorno'], m)
    out['cobre'] = {c: affinity.affine_transform(g, m) for c, g in d['cobre'].items()}
    out['taladros'] = [(x - minx, maxy - y, dd) for x, y, dd in d['taladros']]
    x0, y0, x1, y1 = out['contorno'].bounds
    out['ancho_mm'], out['alto_mm'] = round(x1 - x0, 3), round(y1 - y0, 3)
    return out


def placa(ruta):
    """Lee un `.kicad_pcb`. Devuelve un dict con `contorno` (Polygon), `cobre` ({capa: geometría}), `taladros`
    ([(x, y, d)]), `grosor_mm`, `capas_cobre`, `ancho_mm`, `alto_mm` y `avisos`, todo en el sistema del modelo."""
    with open(ruta, encoding='utf-8-sig') as f:
        return leer_texto(f.read())


# --- para guardar en el diseño -----------------------------------------------------------------------------------

def a_dato(pl, nombre=''):
    """Resumen serializable (WKT) de la placa importada, para guardarlo en los parámetros del diseño."""
    cobre = unary_union(list(pl['cobre'].values())) if pl['cobre'] else Polygon()
    return {'nombre': nombre, 'contorno': _wkt.dumps(pl['contorno'], rounding_precision=3),
            'cobre': _wkt.dumps(cobre, rounding_precision=3), 'ancho': pl['ancho_mm'], 'alto': pl['alto_mm'],
            'grosor_mm': pl.get('grosor_mm', 1.6), 'giro': 0}


def desde_dato(dato):
    """(contorno, cobre) como geometrías de shapely a partir de `a_dato`."""
    return _wkt.loads(dato['contorno']), _wkt.loads(dato['cobre'])


def girar_dato(dato, grados):
    """La misma placa girada `grados` (múltiplo de 90) en sentido antihorario, otra vez con la esquina en (0, 0)."""
    contorno, cobre = desde_dato(dato)
    c = affinity.rotate(contorno, grados, origin=(0, 0))
    k = affinity.rotate(cobre, grados, origin=(0, 0))
    minx, miny, maxx, maxy = c.bounds
    c, k = affinity.translate(c, -minx, -miny), affinity.translate(k, -minx, -miny)
    out = dict(dato)
    out.update({'contorno': _wkt.dumps(c, rounding_precision=3), 'cobre': _wkt.dumps(k, rounding_precision=3),
                'ancho': round(maxx - minx, 3), 'alto': round(maxy - miny, 3), 'giro': (int(dato.get('giro', 0)) + int(grados)) % 360})
    return out


def masa_desde_cobre(cobre, contorno):
    """Cobre importado usable como masa: huecos < CERRAR_HUECOS cerrados y dentro del contorno."""
    if cobre.is_empty:
        return contorno
    r = CERRAR_HUECOS/2
    cerrado = cobre.buffer(r, join_style='mitre').buffer(-r, join_style='mitre')
    return cerrado.intersection(contorno)
