"""Exportación: placa de prueba y huella de KiCad, Gerber + taladros (kicad-cli), DXF y JSON.

Coordenadas: el modelo usa mm con y hacia arriba; KiCad usa y hacia abajo. La placa
se coloca con su esquina en (ORIGEN_X, ORIGEN_Y) de la hoja de KiCad.
"""
import os
import json
import math
import uuid
import shutil
import zipfile
import subprocess

from shapely import affinity
from shapely.geometry import Point, Polygon, box

from . import conector
from .i18n import tr
from .geometria import poligonos, sin_agujeros

def _buscar_kicad_cli():
    """kicad-cli: variable KICAD_CLI, la versión más nueva en Program Files\\KiCad\\<versión>\\bin o el PATH.

    Las placas se escriben en el formato de KiCad 8, así que vale KiCad 8 o posterior.
    """
    if os.environ.get('KICAD_CLI') and os.path.exists(os.environ['KICAD_CLI']):
        return os.environ['KICAD_CLI']
    candidatos = []
    for base in {os.environ.get('ProgramFiles', r'C:\Program Files'), r'C:\Program Files'}:
        dir_kicad = os.path.join(base, 'KiCad')
        if os.path.isdir(dir_kicad):
            for v in os.listdir(dir_kicad):
                exe = os.path.join(dir_kicad, v, 'bin', 'kicad-cli.exe')
                if os.path.exists(exe):
                    try:
                        clave = tuple(int(x) for x in v.split('.'))
                    except ValueError:
                        clave = (0,)
                    candidatos.append((clave, exe))
    if candidatos:
        return max(candidatos)[1]
    return shutil.which('kicad-cli') or r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'


KICAD_CLI = _buscar_kicad_cli()
ORIGEN_X, ORIGEN_Y = 100.0, 150.0
SMA_BORDE = 2.1           # huella Samtec SMA-J-P-H-ST-EM1: del origen al borde de la placa
W_PAD_SMA = 1.27
HOLGURA_TALADRO = 0.3     # cobre retirado alrededor de un taladro sin metalizar (KiCad pide ≥ 0,25 mm)


def _u():
    return str(uuid.uuid4())


def _xy(pts):
    return ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in pts)


class _Conversor:
    """Pasa del sistema del modelo (y arriba) al de KiCad (y abajo)."""

    def __init__(self, antena):
        minx, miny, maxx, maxy = antena.contorno.bounds
        self.minx, self.maxy = minx, maxy

    def p(self, x, y):
        return ORIGEN_X + (x - self.minx), ORIGEN_Y + (self.maxy - y)

    def anillo(self, coords):
        return [self.p(x, y) for x, y in list(coords)[:-1]]


def _pad_personalizado(numero, piezas, conv, ancla, n_net, nombre_net, origen_fp):
    """Pad SMD de forma libre (piezas sin agujeros). ancla: posición absoluta del pad en KiCad;
    en el fichero se escribe relativa a la huella (origen_fp), y las primitivas relativas al pad."""
    ax, ay = ancla
    prims = []
    for pol in piezas:
        pts = [(x - ax, y - ay) for x, y in conv.anillo(pol.exterior.coords)]
        prims.append(f'        (gr_poly (pts {_xy(pts)}) (width 0) (fill yes))')
    net = f' (net {n_net} "{nombre_net}")' if n_net else ''
    rx, ry = ax - origen_fp[0], ay - origen_fp[1]
    return (f'    (pad "{numero}" smd custom (at {rx:.4f} {ry:.4f}) (size 0.3 0.3) (layers "F.Cu")\n'
            f'      (options (clearance outline) (anchor rect))\n'
            f'      (primitives\n' + '\n'.join(prims) + '\n      )' + net + f' (uuid "{_u()}"))')


def _sma(conv, borde_modelo, direccion, n_net):
    """Huella de SMA de canto + vías de masa. Devuelve las líneas S-expresión."""
    dx, dy = direccion                       # hacia dentro, en el modelo (y arriba)
    kx, ky = dx, -dy                         # en KiCad
    rot = {(0, -1): 270, (0, 1): 90, (1, 0): 180, (-1, 0): 0}[(round(kx), round(ky))]
    # en KiCad la +x local de la huella apunta hacia fuera de la placa
    bx, by = conv.p(*borde_modelo)
    ox, oy = bx + kx*SMA_BORDE, by + ky*SMA_BORDE
    a = math.radians(rot)

    def loc(lx, ly):
        return ox + lx*math.cos(a) + ly*math.sin(a), oy - lx*math.sin(a) + ly*math.cos(a)

    # Posición de los pads relativa a la huella (en su sistema sin girar); el ángulo es absoluto
    pads = [f'    (pad "1" smd roundrect (at 0 0 {(90 + rot) % 360}) (size {W_PAD_SMA} 3.2) '
            f'(layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {n_net} "{"GND" if n_net == 1 else "ANT"}") '
            f'(uuid "{_u()}"))']
    for ly in (-2.825, 2.825):
        for capa in ('F', 'B'):
            pads.append(f'    (pad "2" smd roundrect (at -0.25 {ly} {(90 + rot) % 360}) (size 1.35 3.7) '
                        f'(layers "{capa}.Cu" "{capa}.Mask") (roundrect_rratio 0.185) (net 1 "GND") (uuid "{_u()}"))')
    lineas = [f'  (footprint "Antenas:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount" (layer "F.Cu") (uuid "{_u()}") '
              f'(at {ox:.4f} {oy:.4f} {rot})\n'
              f'    (property "Reference" "J1" (at -7 0 {rot}) (layer "F.Fab") '
              f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (property "Value" "SMA_edge" (at -9 0 {rot}) (layer "F.Fab") '
              f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (attr smd)\n' + '\n'.join(pads) + '\n  )']
    for ly in (-2.825, 2.825):
        px, py = loc(-2.1, ly)
        vx, vy = loc(-3.0, ly)
        lineas.append(f'  (segment (start {px:.4f} {py:.4f}) (end {vx:.4f} {vy:.4f}) (width 1.0) (layer "F.Cu") '
                      f'(net 1) (uuid "{_u()}"))')
        lineas.append(f'  (via (at {vx:.4f} {vy:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) '
                      f'(uuid "{_u()}"))')
    return lineas


def _coax_soldado(conv, puerto, n_net):
    """Coaxial soldado en la línea (sin conector): pad del vivo sobre la línea y pad de la malla al lado, unido
    por dos vías a la masa de la cara inferior. Ambos con la máscara abierta."""
    loc = conector._local(puerto)
    dx, dy = puerto['direccion']
    w = puerto['ancho_linea']
    lado = conector.PAD_COAX
    girar = abs(dy) > 0.5

    def tam(a, b):                                   # (u, v) → (x, y)
        return (b, a) if girar else (a, b)
    vm = w/2 + 1.0 + lado/2
    ox, oy = conv.p(*loc(conector.U_COAX, 0.0))
    pads = []
    for nombre, v, (su, sv), net in (('V', 0.0, (lado, w), f'(net {n_net} "{"GND" if n_net == 1 else "ANT"}")'),
                                     ('M', vm, (lado, lado), '(net 1 "GND")')):
        kx, ky = conv.p(*loc(conector.U_COAX, v))
        sx, sy = tam(su, sv)
        pads.append(f'    (pad "{nombre}" smd rect (at {kx - ox:.4f} {ky - oy:.4f}) (size {sx:.3f} {sy:.3f}) '
                    f'(layers "F.Cu" "F.Mask") {net} (uuid "{_u()}"))')
    lineas = [f'  (footprint "Antenas:coax_soldado" (layer "F.Cu") (uuid "{_u()}") (at {ox:.4f} {oy:.4f})\n'
              f'    (property "Reference" "J1" (at 0 -3 0) (layer "F.Fab") '
              f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (property "Value" "coax" (at 0 3 0) (layer "F.Fab") '
              f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (attr smd)\n' + '\n'.join(pads) + '\n  )']
    for du in (-0.8, 0.8):
        vx, vy = conv.p(*loc(conector.U_COAX + du, vm))
        lineas.append(f'  (via (at {vx:.4f} {vy:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) '
                      f'(uuid "{_u()}"))')
    for texto, v in ((tr('vivo'), -(w/2 + 3.2)), (tr('malla'), vm + 0.8)):
        tx, ty = conv.p(*loc(conector.U_COAX + 3.2, v))
        lineas.append(f'  (gr_text "{texto}" (at {tx:.3f} {ty:.3f} 0) (layer "F.SilkS") (uuid "{_u()}")\n'
                      f'    (effects (font (size 0.8 0.8) (thickness 0.12))))')
    return lineas


def _pad_rf(conv, puerto, n_net):
    """Pad de RF (sin conector): un pad sobre el extremo de la línea de 50 Ω, con la máscara abierta, y dos vías de masa a su lado.
    En un producto, la línea que viene del chip llega a este pad (o la huella se sustituye por la línea)."""
    loc = conector._local(puerto)
    dx, dy = puerto['direccion']
    w = puerto['ancho_linea']
    girar = abs(dy) > 0.5
    ox, oy = conv.p(*loc(conector.U_PAD_RF, 0.0))
    su, sv = conector.PAD_RF_LARGO, w
    sx, sy = (sv, su) if girar else (su, sv)
    net = f'(net {n_net} "{"GND" if n_net == 1 else "ANT"}")'
    lineas = [f'  (footprint "Antenas:pad_RF" (layer "F.Cu") (uuid "{_u()}") (at {ox:.4f} {oy:.4f})\n'
              f'    (property "Reference" "J1" (at 0 -3 0) (layer "F.Fab") (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (property "Value" "RF" (at 0 3 0) (layer "F.Fab") (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
              f'    (attr smd)\n    (pad "1" smd rect (at 0 0) (size {sx:.3f} {sy:.3f}) (layers "F.Cu" "F.Mask") {net} (uuid "{_u()}"))\n'
              + '\n'.join(f'    (pad "2" thru_hole circle (at {conv.p(*loc(conector.U_PAD_RF, s*(w/2 + conector.V_VIA_RF)))[0] - ox:.4f} '
                          f'{conv.p(*loc(conector.U_PAD_RF, s*(w/2 + conector.V_VIA_RF)))[1] - oy:.4f}) (size 1.2 1.2) (drill 0.5) '
                          f'(layers "*.Cu" "F.Mask") (net 1 "GND") (uuid "{_u()}"))' for s in (-1, 1)) + '\n  )']
    tx, ty = conv.p(*loc(conector.U_PAD_RF + 2.8, 0.0))
    lineas.append(f'  (gr_text "RF" (at {tx:.3f} {ty:.3f} 0) (layer "F.SilkS") (uuid "{_u()}")\n'
                  f'    (effects (font (size 0.8 0.8) (thickness 0.12))))')
    return lineas


def _ipex(conv, puerto, n_net):
    """Huella de IPEX / U.FL encima de la placa + vías de los pads de masa."""
    pads, vias, centro = conector.pads_ipex(puerto)
    ox, oy = conv.p(*centro)
    lineas_pad = []
    for nombre, (x, y), (sx, sy) in pads:
        kx, ky = conv.p(x, y)
        net = f'(net {n_net} "{"GND" if n_net == 1 else "ANT"}")' if nombre == '1' else '(net 1 "GND")'
        lineas_pad.append(f'    (pad "{nombre}" smd rect (at {kx - ox:.4f} {ky - oy:.4f}) (size {sx:.3f} {sy:.3f}) '
                          f'(layers "F.Cu" "F.Mask" "F.Paste") {net} (uuid "{_u()}"))')
    lineas = [f'  (footprint "Antenas:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (layer "F.Cu") (uuid "{_u()}") '
              f'(at {ox:.4f} {oy:.4f})\n'
              f'    (property "Reference" "J1" (at 0 -3 0) (layer "F.SilkS") '
              f'(uuid "{_u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
              f'    (property "Value" "U.FL" (at 0 3 0) (layer "F.Fab") '
              f'(uuid "{_u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
              f'    (attr smd)\n' + '\n'.join(lineas_pad) + '\n  )']
    for (_, (px, py), _), (vx, vy) in zip(pads[1:], vias):
        a, b = conv.p(px, py), conv.p(vx, vy)
        lineas.append(f'  (segment (start {a[0]:.4f} {a[1]:.4f}) (end {b[0]:.4f} {b[1]:.4f}) (width 1.0) '
                      f'(layer "F.Cu") (net 1) (uuid "{_u()}"))')
        lineas.append(f'  (via (at {b[0]:.4f} {b[1]:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) '
                      f'(uuid "{_u()}"))')
    return lineas


def placa_kicad(antena, ruta, titulo='', etiqueta=None, logo=True):
    """Placa de prueba completa: antena + alimentación + masa + conector (SMA de canto o IPEX).

    Serigrafía inferior: las líneas de `etiqueta` y el logo de Chirptenna (`logo`: 'grande' por defecto,
    'pequeno' o None/False para no ponerlo). Devuelve qué se ha podido colocar
    ({'logo_mm', 'logo_forma', 'lineas', 'quitadas'})."""
    from shapely.geometry import Point
    conv = _Conversor(antena)
    nets = ['', 'GND', 'ANT']
    cuerpo = []
    # borde exterior y, si la placa va aligerada, cada ventana como contorno interior (se fresa)
    for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):
        cuerpo.append(f'  (gr_poly (pts {_xy(conv.anillo(anillo.coords))}) '
                      f'(stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{_u()}"))')
    cobre_sup, cobre_inf = antena.cobre('F.Cu'), antena.cobre('B.Cu')
    pasante = antena.puerto.get('tipo') == 'pasante'
    taladros = list(antena.taladros)
    if pasante:
        # Coaxial por detrás (panel): taladro sin metalizar en el centro, con el cobre de las dos caras
        # retirado alrededor (vivo arriba, malla abajo; no pueden quedar unidos por el taladro)
        xa, ya = antena.puerto['alimentacion']
        d = antena.puerto['taladro_mm']
        taladros.append((xa, ya, d))
        hueco = Point(xa, ya).buffer(d/2 + HOLGURA_TALADRO, 32)
        cobre_sup, cobre_inf = cobre_sup.difference(hueco), cobre_inf.difference(hueco)
    aj = antena.ajuste or {}
    piezas, piezas_inf = poligonos(cobre_sup), poligonos(cobre_inf)
    coaxial = antena.puerto.get('tipo') == 'coaxial'
    if pasante:
        # ancla en el anillo del pad del vivo (el centro queda en el taladro)
        xa, ya = antena.puerto['alimentacion']
        p_con = Point(xa + (antena.puerto['pad_vivo_mm']/2 + antena.puerto['taladro_mm']/2 + HOLGURA_TALADRO)/2, ya)
        ancla = conv.p(p_con.x, p_con.y)
    elif coaxial:
        p_con = Point(*antena.puerto['alimentacion'])
        ancla = conv.p(*antena.puerto['alimentacion'])
    else:
        bx, by = antena.puerto['borde']
        d = antena.puerto['direccion']
        u = antena.puerto.get('inicio_mm', 0.5) + 0.5             # sobre la línea (IPEX: en su pad)
        p_con = Point(bx + d[0]*u, by + d[1]*u)
        ancla = conv.p(p_con.x, p_con.y)
    # Vías de la antena (cruce de tiras del panel): cada una une una pieza de cada cara. Por grupos
    # conectados: el de la pieza superior del conector es ANT; los demás con cobre inferior, GND
    grupo = {('F', i): ('F', i) for i in range(len(piezas))}
    grupo.update({('B', j): ('B', j) for j in range(len(piezas_inf))})

    def raiz(n):
        while grupo[n] != n:
            n = grupo[n]
        return n

    def pieza_en(lista, x, y):
        pt = Point(x, y)
        k = min(range(len(lista)), key=lambda j: lista[j].distance(pt))
        return k if lista[k].distance(pt) < 1e-3 else None

    vias = []
    for vx, vy in antena.vias:
        i, j = pieza_en(piezas, vx, vy), pieza_en(piezas_inf, vx, vy)
        if i is not None and j is not None:
            grupo[raiz(('F', i))] = raiz(('B', j))
            vias.append((vx, vy, ('F', i)))
    i_con = pieza_en(piezas, p_con.x, p_con.y)
    g_ant = raiz(('F', i_con)) if i_con is not None else None
    con_inf = {raiz(('B', j)) for j in range(len(piezas_inf))}
    # Antena en cortocircuito en continua (dipolo plegado: el vivo llega a la masa por una vía): todo es
    # una sola net, GND, también el pad central del conector; si no, el DRC lo vería como un corto
    corto = g_ant is not None and g_ant in con_inf
    # Masa (cara inferior) como zona rellena
    for j, pol in enumerate(piezas_inf):
        n_inf = 'ANT' if raiz(('B', j)) == g_ant and not corto else 'GND'
        # una pieza con huecos se parte en trozos que se solapan: prioridades distintas para que
        # el DRC no dé zones_intersect (mismas net y prioridad)
        for k, trozo in enumerate(sin_agujeros(pol)):
            pts = _xy(conv.anillo(trozo.exterior.coords))
            cuerpo.append(f'  (zone (net {nets.index(n_inf)}) (net_name "{n_inf}") (layer "B.Cu") (uuid "{_u()}") (hatch edge 0.5) (priority {k})\n'
                          f'    (connect_pads yes (clearance 0)) (min_thickness 0.2) (filled_areas_thickness no)\n'
                          f'    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 1))\n'
                          f'    (polygon (pts {pts}))\n    (filled_polygon (layer "B.Cu") (pts {pts})))')
    # Cobre superior: cada pieza es un pad de forma libre con su net. La que toca el conector es
    # ANT; las islas de la red en π van a GND; el resto (lado antena tras el componente en serie,
    # tramos con puente, directores) llevan nets propias para que el DRC no vea cortocircuitos.
    # Con vías, la pieza unida al conector es ANT y la unida al cobre inferior (malla), GND.
    islas = aj.get('islas_masa', [])
    net_de = []
    for i, pz in enumerate(piezas):
        if any(pz.intersects(isla) for isla in islas):
            net_de.append('GND')
        elif pz.distance(p_con) < 1e-3 or raiz(('F', i)) == g_ant:
            net_de.append('GND' if corto else 'ANT')
        elif raiz(('F', i)) in con_inf:
            net_de.append('GND')
        else:
            net_de.append(f'ANT_{i}')
    for n in net_de:
        if n not in nets:
            nets.append(n)
    for vx, vy, pieza in vias:
        kx, ky = conv.p(vx, vy)
        n = net_de[pieza[1]]
        cuerpo.append(f'  (via (at {kx:.4f} {ky:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") '
                      f'(net {nets.index(n)}) (uuid "{_u()}"))')

    def net_en(x, y):
        """Net de la pieza que hay bajo un punto (o la más cercana a menos de 0,6 mm)."""
        pt = Point(x, y)
        k = min(range(len(piezas)), key=lambda j: piezas[j].distance(pt))
        return net_de[k] if piezas[k].distance(pt) < 0.6 else ''

    pads = []
    for i, pz in enumerate(piezas):
        en_con = pz.distance(p_con) < 1e-3
        c = p_con if en_con else pz.representative_point()
        anc = ancla if en_con else conv.p(c.x, c.y)
        pads.append(_pad_personalizado(str(i + 1), sin_agujeros(pz), conv, anc, nets.index(net_de[i]),
                                       net_de[i], ancla))
    for x, y, d in taladros:
        kx, ky = conv.p(x, y)
        pads.append(f'    (pad "" np_thru_hole circle (at {kx - ancla[0]:.4f} {ky - ancla[1]:.4f}) (size {d:.3f} {d:.3f}) '
                    f'(drill {d:.3f}) (layers "*.Cu" "*.Mask") (uuid "{_u()}"))')
    if coaxial:
        # Pads con máscara abierta para soldar el coaxial: vivo (brazo largo) y malla (brazo corto).
        w = antena.puerto['ancho_linea']
        for num, (x, y) in zip(('V', 'M'), (antena.puerto['pads'][1], antena.puerto['pads'][0])):
            kx, ky = conv.p(x, y)
            n = net_en(x, y) or 'ANT'
            pads.append(f'    (pad "{num}" smd rect (at {kx - ancla[0]:.4f} {ky - ancla[1]:.4f}) '
                        f'(size {w:.3f} {max(w, 1.5):.3f}) (layers "F.Cu" "F.Mask") (net {nets.index(n)} "{n}") '
                        f'(uuid "{_u()}"))')
    if pasante:
        # Sin máscara sobre los pads del coaxial para soldar (vivo arriba, malla abajo), como parte de la
        # huella (permite aperturas con varias piezas). Un pad GND pequeño en la cara inferior conecta la
        # zona de masa (si no, el DRC la da por cobre aislado).
        xa, ya = antena.puerto['alimentacion']
        for capa, lado in (('F', antena.puerto['pad_vivo_mm']), ('B', antena.puerto['pad_malla_mm'])):
            pts = _xy([(kx - ancla[0], ky - ancla[1]) for kx, ky in
                       (conv.p(xa + sx*lado/2, ya + sy*lado/2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)))])
            pads.append(f'    (fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill solid) (layer "{capa}.Mask") '
                        f'(uuid "{_u()}"))')
        kx, ky = conv.p(xa + antena.puerto['pad_malla_mm']/2 - 0.75, ya)
        pads.append(f'    (pad "M" smd rect (at {kx - ancla[0]:.4f} {ky - ancla[1]:.4f}) (size 1 1) (layers "B.Cu" "B.Mask") '
                    f'(net 1 "GND") (uuid "{_u()}"))')
    cuerpo.append(f'  (footprint "Antenas:{antena.tipo}" (layer "F.Cu") (uuid "{_u()}") (at {ancla[0]:.4f} {ancla[1]:.4f})\n'
                  f'    (property "Reference" "AE1" (at 0 -3 0) (layer "F.Fab") '
                  f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
                  f'    (property "Value" "{antena.tipo}" (at 0 3 0) (layer "F.Fab") '
                  f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))\n'
                  f'    (attr smd{" allow_soldermask_bridges" if pasante else ""})\n' + '\n'.join(pads) + '\n  )')
    if coaxial:
        (xm, ym), (xv, yv) = antena.puerto['pads']
        dentro = antena.contorno.buffer(-0.6)
        for texto, (x, y), opciones in ((tr('vivo'), (xv, yv), ((4.0, 0), (0, 3.0), (0, 5.5))),
                                        (tr('malla'), (xm, ym), ((-4.5, 0), (0, -3.0), (0, -5.5)))):
            # al lado del pad si cabe; si no (placas estrechas), encima o debajo: es lo que guía al soldar
            ancho = 0.8*len(texto) + 0.4
            dx, dy = next((o for o in opciones if dentro.contains(box(x + o[0] - ancho/2, y + o[1] - 0.6,
                                                                     x + o[0] + ancho/2, y + o[1] + 0.6))),
                          opciones[-1])
            tx, ty = conv.p(x + dx, y + dy)
            cuerpo.append(f'  (gr_text "{texto}" (at {tx:.3f} {ty:.3f} 0) (layer "F.SilkS") (uuid "{_u()}")\n'
                          f'    (effects (font (size 1 1) (thickness 0.15))))')
    elif pasante:
        xa, ya = antena.puerto['alimentacion']
        for capa, lado, texto, espejo in (('F', antena.puerto['pad_vivo_mm'], tr('vivo'), ''),
                                          ('B', antena.puerto['pad_malla_mm'], tr('malla'), ' (justify mirror)')):
            tx, ty = conv.p(xa, ya - lado/2 - 1.8)
            cuerpo.append(f'  (gr_text "{texto}" (at {tx:.3f} {ty:.3f} 0) (layer "{capa}.SilkS") (uuid "{_u()}")\n'
                          f'    (effects (font (size 1 1) (thickness 0.15)){espejo}))')
    elif antena.puerto.get('conector') == conector.IPEX:
        cuerpo += _ipex(conv, antena.puerto, 1 if corto else 2)
    elif antena.puerto.get('conector') == conector.COAX:
        cuerpo += _coax_soldado(conv, antena.puerto, 1 if corto else 2)
    elif antena.puerto.get('conector') == conector.PAD_RF:
        cuerpo += _pad_rf(conv, antena.puerto, 1 if corto else 2)
    else:
        cuerpo += _sma(conv, antena.puerto['borde'], antena.puerto['direccion'], 1 if corto else 2)
    cuerpo += _componentes_ajuste(aj, conv, nets, net_en, antena.contorno.buffer(-0.6))
    # etiqueta None = el título; [] = sin texto (el usuario ha quitado todas las inscripciones)
    lineas = etiqueta if etiqueta is not None else ([titulo] if titulo else [])
    kicad, info = _serigrafia(antena, conv, lineas, con_logo=logo)
    cuerpo += kicad
    _escribir_pcb(ruta, nets, cuerpo, antena)
    return info


def _zona_rotulo(antena):
    """Zona de la cara inferior donde la serigrafía no afecta: sobre el plano de masa (lejos del borde y
    de los pads del conector) o, sin masa (J-pole), en la placa lejos del cobre de la cara superior."""
    placa = antena.contorno.buffer(-1.2)
    masa = antena.cobre('B.Cu')
    if not masa.is_empty and masa.area > 0.15*antena.contorno.area:
        zona = masa.buffer(-1.5).intersection(placa)
    else:
        zona = placa.difference(antena.cobre('F.Cu').buffer(3.0))
    # los pads del conector (y su soldadura) en el borde de alimentación
    bx, by = antena.puerto['borde']
    return zona.difference(Point(bx, by).buffer(7.5))    # pads y vías de masa del SMA (a ~6 mm)


def _hueco_texto(zona, n_lineas, n_car):
    """Busca en una rejilla de 1 mm dónde cabe un bloque de texto, de la letra más grande a la más
    pequeña (1,2 → 0,8 mm), en horizontal o girado 90°. Devuelve (cx, cy, tam, girado) o None."""
    from shapely.prepared import prep
    z = prep(zona)
    x0, y0, x1, y1 = zona.bounds
    xs = [x0 + i for i in range(int(x1 - x0) + 1)]
    ys = [y0 + j for j in range(int(y1 - y0) + 1)]
    for tam in (1.2, 1.1, 1.0, 0.9, 0.8):
        largo, ancho = 0.8*tam*n_car + 0.6, 1.6*tam*n_lineas
        for girado in (False, True):
            hx, hy = (ancho/2, largo/2) if girado else (largo/2, ancho/2)
            for cy in ys:
                for cx in xs:
                    if z.contains(box(cx - hx, cy - hy, cx + hx, cy + hy)):
                        return cx, cy, tam, girado
    return None


ALTOS_LOGO = (14.0, 12.0, 10.0, 9.0, 8.0, 7.0)    # mm, del más grande al más pequeño que se prueba
ALTOS_ICONO = (8.0, 7.0, 6.0, 5.0)                 # solo el grillo, si no cabe el logo con el nombre
# Logo pequeño, el que va siempre aunque no se pida el grande (alto, disposición)
LOGO_PEQUENO = ((6.0, 'horizontal'), (5.0, 'horizontal'), (6.0, 'vertical'), (5.0, 'vertical'),
                (5.0, 'icono'), (4.0, 'icono'))


def _hueco_rect(zona, w, h, girar=True):
    """Centro donde cabe un rectángulo w × h (horizontal o, con `girar`, girado 90°) dentro de la zona, lo
    más cerca posible de su centro. Devuelve (cx, cy, girado) o None."""
    from shapely.prepared import prep
    if zona.is_empty:
        return None
    z = prep(zona)
    for girado in ((False, True) if girar else (False,)):
        ww, hh = (h, w) if girado else (w, h)
        # los centros posibles quedan dentro de la zona encogida medio lado corto (condición necesaria)
        nucleo = zona.buffer(-min(ww, hh)/2, join_style='mitre')
        if nucleo.is_empty:
            continue
        paso = max(0.5, min(ww, hh)/4)
        x0, y0, x1, y1 = nucleo.bounds
        c = zona.representative_point() if zona.geom_type != 'Polygon' else zona.centroid
        nz = prep(nucleo)
        cand = [(x0 + i*paso, y0 + j*paso) for i in range(int((x1 - x0)/paso) + 1)
                for j in range(int((y1 - y0)/paso) + 1)]
        cand = [p for p in cand if nz.contains(Point(p))]
        cand.sort(key=lambda p: (p[0] - c.x)**2 + (p[1] - c.y)**2)
        for cx, cy in cand:
            if z.contains(box(cx - ww/2, cy - hh/2, cx + ww/2, cy + hh/2)):
                return cx, cy, girado
    return None


def _caja_texto(hueco, lineas):
    cx, cy, tam, girado = hueco
    largo, ancho = 0.8*tam*max(len(t) for t in lineas) + 0.6, 1.6*tam*len(lineas)
    hx, hy = (ancho/2, largo/2) if girado else (largo/2, ancho/2)
    return box(cx - hx, cy - hy, cx + hx, cy + hy)


def _modo_logo(logo):
    """'grande', 'pequeno' o None (sin logo). Admite también True (grande) y False (sin logo)."""
    if logo is True:
        return 'grande'
    if logo in ('grande', 'pequeno'):
        return logo
    return None


def _serigrafia(antena, conv, lineas, con_logo='grande'):
    """Serigrafía inferior: logo de Chirptenna y líneas de texto, sin solaparse.

    con_logo: 'grande' (14 → 7 mm, y si no cabe, el pequeño), 'pequeno' (6 → 4 mm) o None (sin logo; es
    opcional, la interfaz pide amablemente que se mencione el proyecto). Con logo, si no cabe ni el grillo,
    va la palabra «Chirptenna» en letra mínima. Prueba a poner primero el logo y luego el texto, y al revés;
    prioridad: que haya logo (si se pidió), la primera línea, el resto de líneas y el tamaño del logo. Zonas:
    sobre la masa o lejos del cobre superior y, si no cabe, la cara inferior entera salvo junto al conector
    (la tinta por detrás del FR4 no afecta a la antena)."""
    from . import logo as lg
    modo = _modo_logo(con_logo)
    zona = _zona_rotulo(antena)
    bx, by = antena.puerto['borde']
    alternativa = antena.contorno.buffer(-1.0).difference(Point(bx, by).buffer(4.0))
    lineas = [t for t in lineas if t and t.strip()]

    def poner_texto(zonas):
        ls = list(lineas)
        while ls:
            for z in zonas:
                if not z.is_empty:
                    h = _hueco_texto(z, len(ls), max(len(t) for t in ls))
                    if h:
                        return ls, h
            ls.pop()
        return [], None

    def poner_logo(zonas):
        lado = min(antena.contorno.bounds[2] - antena.contorno.bounds[0],
                   antena.contorno.bounds[3] - antena.contorno.bounds[1])
        pruebas = []
        if modo == 'grande':
            # primero sin girar y de 9 mm para arriba (se lee mejor); luego cualquier tamaño, girado si hace falta
            pruebas += [(a, d, False) for a in ALTOS_LOGO if a >= 9.0 for d in ('horizontal', 'vertical')] + \
                       [(a, d, True) for a in ALTOS_LOGO for d in ('horizontal', 'vertical')] + \
                       [(a, 'icono', True) for a in ALTOS_ICONO]
        pruebas += [(a, d, True) for a, d in LOGO_PEQUENO]     # el pequeño (y último recurso del grande)
        for alto, disp, girar in pruebas:
            if alto > 0.45*lado and alto > lg.ALTO_MIN_MM:
                continue                     # que el logo no domine la placa
            geom = lg.bloque(alto, disp)
            x0, y0, x1, y1 = geom.bounds
            for z in zonas:
                r = _hueco_rect(z, x1 - x0, y1 - y0, girar)
                if r:
                    return geom, r, (alto, disp)
        return None, None, None

    opciones = []
    for orden in (('logo', 'texto'), ('texto', 'logo')):
        zonas = [zona, alternativa]
        res = {'lineas': [], 'hueco': None, 'logo': None, 'alto': None}
        for cosa in orden:
            if cosa == 'texto' and lineas:
                res['lineas'], res['hueco'] = poner_texto(zonas)
                if res['hueco']:
                    ocupado = _caja_texto(res['hueco'], res['lineas']).buffer(1.0)
                    zonas = [z.difference(ocupado) for z in zonas]
            elif cosa == 'logo' and modo:
                geom, sitio, alto = poner_logo(zonas)
                if geom is not None:
                    res['logo'], res['alto'] = (geom, sitio), alto
                    cx, cy, girado = sitio
                    x0, y0, x1, y1 = geom.bounds
                    hx, hy = ((y1 - y0)/2, (x1 - x0)/2) if girado else ((x1 - x0)/2, (y1 - y0)/2)
                    ocupado = box(cx - hx, cy - hy, cx + hx, cy + hy).buffer(1.0)
                    zonas = [z.difference(ocupado) for z in zonas]
        opciones.append(res)
    # prioridad: que haya logo (si se pidió), la primera línea (qué antena es), logo con nombre mejor que solo
    # el grillo, el resto de líneas y, por último, el logo más grande
    puntos_logo = {'horizontal': 2, 'vertical': 2, 'icono': 1}
    mejor = max(opciones, key=lambda r: (r['logo'] is not None, min(len(r['lineas']), 1),
                                         puntos_logo[r['alto'][1]] if r['alto'] else 0,
                                         len(r['lineas']), r['alto'][0] if r['alto'] else 0))

    salida = []
    if modo and not mejor['logo']:
        # Ni el grillo pequeño cabe: la palabra «Chirptenna» en letra mínima, donde sea (sin pisar el texto)
        libre = antena.contorno.buffer(-0.6).difference(Point(bx, by).buffer(2.5))
        if mejor['hueco']:
            libre = libre.difference(_caja_texto(mejor['hueco'], mejor['lineas']).buffer(0.5))
        h = _hueco_texto(libre, 1, len('Chirptenna')) if not libre.is_empty else None
        if h is None:
            c = antena.contorno.representative_point()
            x0, y0, x1, y1 = antena.contorno.bounds
            h = (c.x, c.y, 0.8, (y1 - y0) > (x1 - x0))
        cx, cy, tam, girado = h
        tx, ty = conv.p(cx, cy)
        salida.append(f'  (gr_text "Chirptenna" (at {tx:.3f} {ty:.3f} {90 if girado else 0}) (layer "B.SilkS") '
                      f'(uuid "{_u()}")\n    (effects (font (size {tam:.2f} {tam:.2f}) (thickness 0.15) bold) '
                      f'(justify mirror)))')
        mejor['alto'] = (tam, 'texto')
    if mejor['logo']:
        geom, (cx, cy, girado) = mejor['logo']
        if girado:
            # -90°: se lee de arriba abajo, en el mismo sentido que el texto girado de KiCad
            geom = affinity.rotate(geom, -90, origin=(0, 0))
        # cara inferior: se dibuja espejado en x para que se lea al dar la vuelta a la placa
        geom = affinity.translate(affinity.scale(geom, -1, 1, origin=(0, 0)), cx, cy)
        for pol in poligonos(geom):
            for trozo in sin_agujeros(pol):
                salida.append(f'  (gr_poly (pts {_xy(conv.anillo(trozo.exterior.coords))}) '
                              f'(stroke (width 0) (type solid)) (fill solid) (layer "B.SilkS") (uuid "{_u()}"))')
    if mejor['hueco']:
        cx, cy, tam, girado = mejor['hueco']
        for i, t in enumerate(mejor['lineas']):
            d = (i - (len(mejor['lineas']) - 1)/2)*1.6*tam
            # cara inferior espejada: con el texto girado, las líneas se apilan en x
            px, py = (cx - d, cy) if girado else (cx, cy - d)
            tx, ty = conv.p(px, py)
            t = t.replace('"', "'")
            salida.append(f'  (gr_text "{t}" (at {tx:.3f} {ty:.3f} {90 if girado else 0}) (layer "B.SilkS") (uuid "{_u()}")\n'
                          f'    (effects (font (size {tam:.2f} {tam:.2f}) (thickness {max(0.15, 0.15*tam):.3f})) '
                          f'(justify mirror)))')     # 0,15 mm: trazo mínimo de serigrafía de JLC
    info = {'logo_mm': mejor['alto'][0] if mejor['alto'] else None,
            'logo_forma': mejor['alto'][1] if mejor['alto'] else None, 'lineas': mejor['lineas'],
            'quitadas': lineas[len(mejor['lineas']):]}
    return salida, info


def placa_reflector(antena, ruta, titulo=''):
    """Placa del reflector del panel: cobre macizo (GND) en las dos caras con los taladros de los
    separadores (alineados con los de la placa de dipolos) y el del SMA de panel en el centro."""
    from types import SimpleNamespace
    from shapely.geometry import Point
    refl = antena.reflector
    hoja = SimpleNamespace(contorno=refl['contorno'], info=antena.info)
    conv = _Conversor(hoja)
    cuerpo = [f'  (gr_poly (pts {_xy(conv.anillo(refl["contorno"].exterior.coords))}) '
              f'(stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{_u()}"))']
    cobre = refl['contorno'].buffer(-0.5, join_style='mitre')
    for x, y, d in refl['taladros']:
        cobre = cobre.difference(Point(x, y).buffer(d/2 + HOLGURA_TALADRO, 32))
    for capa in ('F', 'B'):
        for pol in poligonos(cobre):
            for k, trozo in enumerate(sin_agujeros(pol)):
                pts = _xy(conv.anillo(trozo.exterior.coords))
                cuerpo.append(f'  (zone (net 1) (net_name "GND") (layer "{capa}.Cu") (uuid "{_u()}") (hatch edge 0.5) '
                              f'(priority {k})\n'
                              f'    (connect_pads yes (clearance 0)) (min_thickness 0.2) (filled_areas_thickness no)\n'
                              f'    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 1))\n'
                              f'    (polygon (pts {pts}))\n    (filled_polygon (layer "{capa}.Cu") (pts {pts})))')
    ox, oy = conv.p(0.0, 0.0)
    pads = []
    for x, y, d in refl['taladros']:
        kx, ky = conv.p(x, y)
        pads.append(f'    (pad "" np_thru_hole circle (at {kx - ox:.4f} {ky - oy:.4f}) (size {d:.3f} {d:.3f}) '
                    f'(drill {d:.3f}) (layers "*.Cu" "*.Mask") (uuid "{_u()}"))')
    # Pads de masa junto al SMA (soldar la tuerca o un cable de masa); además conectan las zonas
    for capa in ('F', 'B'):
        pads.append(f'    (pad "1" smd rect (at 6.5 0) (size 2 2) (layers "{capa}.Cu" "{capa}.Mask") (net 1 "GND") '
                    f'(uuid "{_u()}"))')
    cuerpo.append(f'  (footprint "Antenas:taladros_reflector" (layer "F.Cu") (uuid "{_u()}") (at {ox:.4f} {oy:.4f})\n'
                  f'    (property "Reference" "H1" (at 0 -6 0) (layer "F.Fab") (uuid "{_u()}") '
                  f'(effects (font (size 1 1) (thickness 0.15))))\n'
                  f'    (property "Value" "reflector" (at 0 6 0) (layer "F.Fab") (uuid "{_u()}") '
                  f'(effects (font (size 1 1) (thickness 0.15))))\n'
                  f'    (attr exclude_from_pos_files exclude_from_bom)\n' + '\n'.join(pads) + '\n  )')
    minx, miny, maxx, maxy = refl['contorno'].bounds
    tx, ty = conv.p((minx + maxx)/2, maxy - 4)
    texto = (tr('{0} - reflector a {1:.1f} mm de la placa', titulo, refl['separacion_mm']) if titulo
             else tr('Reflector a {0:.1f} mm de la placa', refl['separacion_mm']))
    cuerpo.append(f'  (gr_text "{texto}" (at {tx:.3f} {ty:.3f} 0) (layer "F.SilkS") (uuid "{_u()}")\n'
                  f'    (effects (font (size 1.5 1.5) (thickness 0.2))))')
    _escribir_pcb(ruta, ['', 'GND'], cuerpo, hoja)


def _girar(dx, dy, rot):
    r = int(round(rot/90.0)) % 4
    return [(dx, dy), (-dy, dx), (-dx, -dy), (dy, -dx)][r], r % 2 == 1


def _componentes_ajuste(aj, conv, nets, net_en, dentro=None):
    """Huellas de la red en π y de los puentes, vías de las islas de masa y marcas de corte.
    dentro: zona de la placa (modelo) donde caben los rótulos de las referencias."""
    lineas = []
    for c in aj.get('componentes', []):
        cx, cy = conv.p(c['x'], c['y'])
        pads = []
        for k, (dx, dy, w, h) in enumerate(c['pads']):
            (rx, ry), girado = _girar(dx, dy, c['rot'])
            mx, my = c['x'] + rx, c['y'] + ry                       # centro del pad en el modelo
            kx, ky = conv.p(mx, my)
            sw, sh = (h, w) if girado else (w, h)
            n = net_en(mx, my)
            net = f' (net {nets.index(n)} "{n}")' if n else ''
            pads.append(f'    (pad "{k + 1}" smd rect (at {kx - cx:.4f} {ky - cy:.4f}) (size {sw:.3f} {sh:.3f}) '
                        f'(layers "F.Cu" "F.Mask" "F.Paste"){net} (uuid "{_u()}"))')
        valor = c['valor'] + ('' if c['montar'] else ' (no montar)' if 'no montada' not in c['valor'] else '')
        # referencia al lado de la huella, en perpendicular a sus pads: con los puentes en fila sobre una
        # pista vertical, «encima» caía sobre el pad del siguiente y JLC la recortaría
        _, girado = _girar(1, 0, c['rot'])
        ancho_pads = max(max(w, h) for _, _, w, h in c['pads'])
        rotulo, (rx, ry), oculta = c['ref'], (0.0, -1.6), ''
        if girado:
            # a la derecha o a la izquierda; en una punta estrecha, solo el número (el orden de cierre)
            numero = ''.join(ch for ch in c['ref'] if ch.isdigit())
            for texto in (c['ref'], numero):
                d = ancho_pads/2 + 0.6 + 0.4*len(texto)
                lado = next((s for s in (1, -1) if dentro is None or dentro.contains(
                    box(c['x'] + s*d - 0.4*len(texto), c['y'] - 0.5, c['x'] + s*d + 0.4*len(texto), c['y'] + 0.5))), None)
                if lado:
                    rotulo, (rx, ry) = texto, (lado*d, 0.0)
                    break
            else:
                oculta = ' hide'
        texto_ref = f'(effects (font (size 0.8 0.8) (thickness 0.15)){oculta})'
        if rotulo != c['ref']:
            # la referencia (única) se oculta y el número va como texto de la huella
            texto_ref = '(effects (font (size 0.8 0.8) (thickness 0.15)) hide)'
            lineas_num = (f'    (fp_text user "{rotulo}" (at {rx:.3f} {ry:.3f} 0) (layer "F.SilkS") (uuid "{_u()}") '
                          f'(effects (font (size 0.8 0.8) (thickness 0.15))))\n')
        else:
            lineas_num = ''
        lineas.append(f'  (footprint "Antenas:{c["huella"]}" (layer "F.Cu") (uuid "{_u()}") (at {cx:.4f} {cy:.4f})\n'
                      f'    (property "Reference" "{c["ref"]}" (at {rx:.3f} {ry:.3f} 0) (layer "F.SilkS") (uuid "{_u()}") '
                      f'{texto_ref})\n' + lineas_num +
                      f'    (property "Value" "{valor}" (at 0 1.6 0) (layer "F.Fab") (uuid "{_u()}") '
                      f'(effects (font (size 0.8 0.8) (thickness 0.12))))\n'
                      f'    (attr smd)\n' + '\n'.join(pads) + '\n  )')
    for x, y in aj.get('vias_masa', []):
        kx, ky = conv.p(x, y)
        lineas.append(f'  (via (at {kx:.4f} {ky:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") '
                      f'(net {nets.index("GND")}) (uuid "{_u()}"))')
    for m in aj.get('marcas', []):
        (ax, ay), (bx, by) = [conv.p(*q) for q in m['linea']]
        lineas.append(f'  (gr_line (start {ax:.4f} {ay:.4f}) (end {bx:.4f} {by:.4f}) (stroke (width 0.15) '
                      f'(type default)) (layer "F.SilkS") (uuid "{_u()}"))')
        tx, ty = conv.p(*m['pos'])
        ang = m['rot'] % 180
        ang = ang - 180 if ang > 90 else ang                       # texto siempre legible
        lineas.append(f'  (gr_text "{m["texto"]}" (at {tx:.3f} {ty:.3f} {ang:.0f}) (layer "F.SilkS") (uuid "{_u()}")\n'
                      f'    (effects (font (size 0.8 0.8) (thickness 0.12))))')
    return lineas


def _escribir_pcb(ruta, nets, cuerpo, antena):
    h = antena.info.get('h_mm', 1.6)
    cab = ['(kicad_pcb (version 20240108) (generator "generador_antenas") (generator_version "8.0")',
           f'  (general (thickness {h}) (legacy_teardrops no))', '  (paper "A4")',
           '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") '
           '(33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user) '
           '(36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) '
           '(39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments") '
           '(42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2") (44 "Edge.Cuts" user) '
           '(45 "Margin" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") '
           '(48 "B.Fab" user) (49 "F.Fab" user))',
           '  (setup (pad_to_mask_clearance 0))']
    cab += [f'  (net {i} "{n}")' for i, n in enumerate(nets)]
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(cab + cuerpo) + '\n)\n')


def huella_kicad(antena, ruta, nombre, integrar=False):
    """Huella (.kicad_mod) solo con el radiador, para colocarla en una placa propia.

    El pad 1 (la alimentación) está en el origen de la huella. El patio (courtyard) marca
    la zona que debe quedar sin cobre en ambas caras (monopolos y Yagi).
    integrar (antena integrada en una placa, F3.3): añade una zona de exclusión que cubre la zona de antena en todas las
    capas de cobre, un pad pasante «2» en la vía a masa (IFA) y, en Dwgs.User, el lado que debe coincidir con Edge.Cuts.
    """
    texto = _texto_huella(antena, nombre, integrar)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write(texto)


def _texto_huella(antena, nombre, integrar=False, nets=None, en=None):
    """Texto del .kicad_mod. nets: {número de pad: (índice de net, nombre)} y en: (x, y) en KiCad, para incrustarla en
    una placa (`placa_ejemplo_integrada`); sin ellos, es el fichero de la biblioteca."""
    nets = nets or {}
    conv = _Conversor(antena)
    ancla = conv.p(*antena.puerto['alimentacion'])
    piezas = poligonos(antena.radiador)
    from shapely.geometry import Point
    alim = Point(*antena.puerto['alimentacion'])
    principal = min(piezas, key=lambda p: p.distance(alim))
    lineas = []

    def pad_rel(numero, trozos, ancla_pad, con_net):
        ax, ay = ancla_pad
        prims = []
        for pol in trozos:
            pts = [(x - ax, y - ay) for x, y in conv.anillo(pol.exterior.coords)]
            prims.append(f'      (gr_poly (pts {_xy(pts)}) (width 0) (fill yes))')
        net = f' (net {nets[numero][0]} "{nets[numero][1]}")' if numero in nets else ''
        return (f'  (pad "{numero}" smd custom (at {ax - ancla[0]:.4f} {ay - ancla[1]:.4f}) (size 0.3 0.3) '
                f'(layers "F.Cu")\n    (options (clearance outline) (anchor rect))\n    (primitives\n'
                + '\n'.join(prims) + f'\n    ){net} (uuid "{_u()}"))')

    lineas.append(pad_rel('1', sin_agujeros(principal), ancla, True))
    for i, otra in enumerate(p for p in piezas if p is not principal):
        c = otra.representative_point()
        lineas.append(pad_rel(str(i + 2), sin_agujeros(otra), conv.p(c.x, c.y), False))
    for m in (antena.ajuste or {}).get('marcas', []):
        (ax, ay), (bx, by) = [conv.p(*q) for q in m['linea']]
        lineas.append(f'  (fp_line (start {ax - ancla[0]:.4f} {ay - ancla[1]:.4f}) (end {bx - ancla[0]:.4f} '
                      f'{by - ancla[1]:.4f}) (stroke (width 0.15) (type solid)) (layer "F.SilkS") (uuid "{_u()}"))')
        tx, ty = conv.p(*m['pos'])
        ang = m['rot'] % 180
        ang = ang - 180 if ang > 90 else ang
        lineas.append(f'  (fp_text user "{m["texto"]}" (at {tx - ancla[0]:.3f} {ty - ancla[1]:.3f} {ang:.0f}) '
                      f'(layer "F.SilkS") (uuid "{_u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    if antena.zona_libre is not None:
        zl = antena.zona_libre
        if not isinstance(zl, Polygon):        # el GEOS de Pyodide puede dar polígono + línea suelta
            zl = max(poligonos(zl), key=lambda q: q.area)
        pts = [(x - ancla[0], y - ancla[1]) for x, y in conv.anillo(zl.exterior.coords)]
        lineas.append(f'  (fp_poly (pts {_xy(pts)}) (stroke (width 0.05) (type solid)) (fill none) '
                      f'(layer "F.CrtYd") (uuid "{_u()}"))')
        sin_cobre = tr('Sin cobre en ambas caras')
        lineas.append(f'  (fp_text user "{sin_cobre}" (at {pts[0][0] + 2:.3f} {pts[0][1] - 1:.3f} 0) '
                      f'(layer "Cmts.User") (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15)) (justify left)))')
    if integrar and antena.zona_libre is not None:
        zl = antena.zona_libre
        if not isinstance(zl, Polygon):
            zl = max(poligonos(zl), key=lambda q: q.area)
        pts = [(x - ancla[0], y - ancla[1]) for x, y in conv.anillo(zl.exterior.coords)]
        # zona de exclusión: ni pistas, ni vías, ni relleno de masa en ninguna capa de cobre. Los pads de la propia antena y su
        # huella quedan permitidos (si no, el DRC marcaría el radiador contra su propia zona)
        lineas.append(f'  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{_u()}") (name "{tr("zona de antena")}") '
                      f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n'
                      f'    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) '
                      f'(footprints allowed))\n    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
                      f'    (polygon (pts {_xy(pts)})))')
        # vía a masa de la antena (IFA): pad pasante, unido a la masa de la placa por el relleno de B.Cu
        for k, (vx, vy) in enumerate(antena.vias):
            kx, ky = conv.p(vx, vy)
            numero = str(len(piezas) + 1 + k)
            net = f' (net {nets[numero][0]} "{nets[numero][1]}")' if numero in nets else ''
            lineas.append(f'  (pad "{numero}" thru_hole circle (at {kx - ancla[0]:.4f} {ky - ancla[1]:.4f}) (size 0.8 0.8) '
                          f'(drill 0.4) (layers "*.Cu" "*.Mask"){net} (uuid "{_u()}"))')
        # el lado de la zona que coincide con el borde de la placa (Edge.Cuts): hay que alinearlo al colocar la huella
        x0, y0, x1, y1 = antena.contorno.bounds
        zx0, zy0, zx1, zy1 = zl.bounds
        lados = [(zx0, zy1, zx1, zy1)] if abs(zy1 - y1) < 1e-6 else []
        if abs(zx0 - x0) < 1e-6:
            lados.append((zx0, zy0, zx0, zy1))
        if abs(zx1 - x1) < 1e-6:
            lados.append((zx1, zy0, zx1, zy1))
        for ax, ay, bx, by in lados:
            (pax, pay), (pbx, pby) = conv.p(ax, ay), conv.p(bx, by)
            lineas.append(f'  (fp_line (start {pax - ancla[0]:.4f} {pay - ancla[1]:.4f}) (end {pbx - ancla[0]:.4f} {pby - ancla[1]:.4f}) '
                          f'(stroke (width 0.25) (type dash)) (layer "Dwgs.User") (uuid "{_u()}"))')
        if lados:
            ax, ay, bx, by = lados[0]
            (pax, pay), (pbx, pby) = conv.p(ax, ay), conv.p(bx, by)
            lineas.append(f'  (fp_text user "{tr("borde de la placa aquí")}" (at {(pax + pbx)/2 - ancla[0]:.3f} {(pay + pby)/2 - ancla[1] + 1.2:.3f} 0) '
                          f'(layer "Dwgs.User") (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))')
    en_pcb = f'(uuid "{_u()}") (at {en[0]:.4f} {en[1]:.4f}) ' if en else ''
    texto = (f'(footprint "{nombre}" (version 20240108) (generator "generador_antenas") (generator_version "8.0")\n'
             f'  (layer "F.Cu") {en_pcb}\n  (descr "{antena.tipo} generado; f estimada {antena.info.get("f_estimada_MHz")} MHz; '
             f'alimentar en el pad 1 con línea de 50 Ohm")\n  (attr smd)\n'
             f'  (property "Reference" "AE**" (at 0 -2 0) (layer "F.SilkS") (uuid "{_u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))\n'
             f'  (property "Value" "{nombre}" (at 0 2 0) (layer "F.Fab") (uuid "{_u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))\n' + '\n'.join(lineas) + '\n)\n')
    return texto


def placa_ejemplo_integrada(antena, ruta, nombre):
    """Placa de ejemplo de una antena integrada: la placa anfitriona vacía (masa GND en las dos caras) con la huella colocada
    en su esquina. Sirve para comprobar que el relleno de masa respeta la zona de antena sin tocar nada a mano (el DRC se
    ejecuta con `--refill-zones`: es KiCad quien rellena)."""
    conv = _Conversor(antena)
    nets = ['', 'GND', 'ANT']
    ancla = conv.p(*antena.puerto['alimentacion'])
    corto = bool(antena.vias)            # IFA: el cobre de la antena y la vía son el mismo, unido a masa
    n1 = (1, 'GND') if corto else (2, 'ANT')
    pads = {'1': n1}
    for k in range(len(antena.vias)):
        pads[str(len(poligonos(antena.radiador)) + 1 + k)] = (1, 'GND')
    cuerpo = []
    for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):
        cuerpo.append(f'  (gr_poly (pts {_xy(conv.anillo(anillo.coords))}) '
                      f'(stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{_u()}"))')
    dentro = antena.contorno.buffer(-0.5, join_style='mitre')       # el mismo retranqueo que `tipos.BORDE_COBRE`
    for capa in ('F.Cu', 'B.Cu'):
        for pol in poligonos(dentro):
            pts = _xy(conv.anillo(pol.exterior.coords))
            cuerpo.append(f'  (zone (net 1) (net_name "GND") (layer "{capa}") (uuid "{_u()}") (hatch edge 0.5)\n'
                          f'    (connect_pads yes (clearance 0)) (min_thickness 0.2) (filled_areas_thickness no)\n'
                          f'    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 1))\n'
                          f'    (polygon (pts {pts})))')
    zl = antena.zona_libre
    if not isinstance(zl, Polygon):
        zl = max(poligonos(zl), key=lambda q: q.area)
    # KiCad no aplica (al menos con `kicad-cli --refill-zones`) la zona de exclusión que va dentro de la huella: la misma zona, a nivel
    # de placa, hace que el ejemplo se vea y se compruebe igual. En KiCad con la interfaz, la de la huella es la que vale.
    pts = _xy(conv.anillo(zl.exterior.coords))
    cuerpo.append(f'  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{_u()}") (name "{tr("zona de antena")}") (hatch edge 0.5) '
                  f'(connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n'
                  f'    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))\n'
                  f'    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n    (polygon (pts {pts})))')
    prohibido = zl.buffer(0.8)
    # (la línea de 50 Ω hasta el pad 1 la traza cada usuario con su placa: aquí queda el pad sin conectar)
    x0, y0 = antena.puerto['alimentacion']
    w50 = antena.puerto.get('ancho_linea', 3.0)
    prohibido = prohibido.union(box(x0 - w50/2 - 0.8, antena.contorno.bounds[1], x0 + w50/2 + 0.8, y0))
    # vías de cosido entre las masas de las dos caras (sin ellas el DRC da cobre aislado en los trozos que deja la línea)
    paso = 8.0
    libre = dentro.buffer(-0.8).difference(prohibido)
    minx, miny, maxx, maxy = antena.contorno.bounds
    for k, pol in enumerate(sorted(poligonos(libre), key=lambda q: -q.area)):
        if pol.area < 1:
            continue
        cx, cy = pol.representative_point().x, pol.representative_point().y
        if k == 0:
            # un pad de masa (punto de prueba): sin ningún pad de su net, el DRC da la zona por cobre aislado
            kx, ky = conv.p(cx, cy)
            cuerpo.append(f'  (footprint "Antenas:GND" (layer "F.Cu") (uuid "{_u()}") (at {kx:.4f} {ky:.4f})\n'
                          f'    (property "Reference" "TP1" (at 0 -2 0) (layer "F.Fab") (uuid "{_u()}") '
                          f'(effects (font (size 1 1) (thickness 0.15))))\n    (attr smd)\n'
                          f'    (pad "1" thru_hole circle (at 0 0) (size 1.4 1.4) (drill 0.7) (layers "*.Cu" "*.Mask") '
                          f'(net 1 "GND") (uuid "{_u()}")))')
            continue
        puestos = [(cx, cy)]
        nx, ny = int((maxx - minx)/paso), int((maxy - miny)/paso)
        for i in range(nx + 1):
            for j in range(ny + 1):
                q = Point(minx + paso/2 + i*paso, miny + paso/2 + j*paso)
                if pol.contains(q) and q.distance(Point(cx, cy)) > 0.5:
                    puestos.append((q.x, q.y))
        for vx, vy in puestos:
            kx, ky = conv.p(vx, vy)
            cuerpo.append(f'  (via (at {kx:.4f} {ky:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) (uuid "{_u()}"))')
    texto = _texto_huella(antena, nombre, True, nets=pads, en=ancla)
    cuerpo.append('  ' + texto.replace('\n', '\n  ').rstrip())
    _escribir_pcb(ruta, nets, cuerpo, antena)


def gerber(ruta_pcb, carpeta, ruta_zip):
    """Gerber + taladros con kicad-cli, empaquetados en un .zip para JLC."""
    if not os.path.exists(KICAD_CLI):
        raise FileNotFoundError(tr('No se encuentra kicad-cli en {0}', KICAD_CLI))
    os.makedirs(carpeta, exist_ok=True)
    for n in os.listdir(carpeta):
        os.remove(os.path.join(carpeta, n))
    capas = 'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts'
    for args in (['pcb', 'export', 'gerbers', '--layers', capas, '-o', carpeta, ruta_pcb],
                 ['pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o',
                  carpeta + os.sep, ruta_pcb]):
        r = subprocess.run([KICAD_CLI] + args, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(tr('kicad-cli falló: {0}', r.stderr or r.stdout))
    with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(carpeta)):
            z.write(os.path.join(carpeta, n), n)


def drc(ruta_pcb, rellenar=False):
    """Ejecuta el DRC de KiCad y devuelve las infracciones relevantes (sin avisos esperados).
    rellenar: KiCad rellena las zonas antes (y guarda la placa rellena), para placas con zonas sin relleno."""
    salida = ruta_pcb + '.drc.json'
    extra = ['--refill-zones', '--save-board'] if rellenar else []
    subprocess.run([KICAD_CLI, 'pcb', 'drc', '--format', 'json', '-o', salida] + extra + [ruta_pcb], capture_output=True)
    d = json.load(open(salida, encoding='utf-8'))
    ignorar = {'lib_footprint_issues', 'lib_footprint_mismatch', 'silk_overlap', 'silk_over_copper',
               'silk_edge_clearance', 'track_dangling'}
    return [(v['type'], v['severity'], v['items'][0]['description'] if v['items'] else '')
            for v in d.get('violations', []) if v['type'] not in ignorar]


def dxf(antena, ruta):
    """DXF con capas COBRE_SUP, COBRE_INF y CONTORNO (polilíneas cerradas, huecos incluidos)."""
    import ezdxf
    doc = ezdxf.new('R2010', setup=False)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for nombre, color in (('COBRE_SUP', 1), ('COBRE_INF', 5), ('CONTORNO', 7)):
        doc.layers.add(nombre, color=color)

    def pol(geom, capa):
        for p in poligonos(geom):
            msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={'layer': capa})
            for h in p.interiors:
                msp.add_lwpolyline(list(h.coords), close=True, dxfattribs={'layer': capa})

    pol(antena.cobre('F.Cu'), 'COBRE_SUP')
    pol(antena.cobre('B.Cu'), 'COBRE_INF')
    pol(antena.contorno, 'CONTORNO')
    taladros = list(antena.taladros)
    if antena.puerto.get('tipo') == 'pasante':
        taladros.append((*antena.puerto['alimentacion'], antena.puerto['taladro_mm']))
    if taladros:
        doc.layers.add('TALADROS', color=3)
        for x, y, d in taladros:
            msp.add_circle((x, y), d/2, dxfattribs={'layer': 'TALADROS'})
    doc.saveas(ruta)


def dxf_reflector(antena, ruta):
    """DXF del reflector del panel (contorno y taladros), para cortarlo en chapa o pedirlo como placa."""
    import ezdxf
    doc = ezdxf.new('R2010', setup=False)
    doc.units = ezdxf.units.MM
    doc.layers.add('CONTORNO', color=7)
    doc.layers.add('TALADROS', color=1)
    msp = doc.modelspace()
    msp.add_lwpolyline(list(antena.reflector['contorno'].exterior.coords), close=True,
                       dxfattribs={'layer': 'CONTORNO'})
    for x, y, d in antena.reflector['taladros']:
        msp.add_circle((x, y), d/2, dxfattribs={'layer': 'TALADROS'})
    doc.saveas(ruta)


def exportar_todo(antena, carpeta, nombre, titulo='', etiqueta=None, logo=True):
    """Genera en la carpeta: placa .kicad_pcb, huella .kicad_mod, Gerber .zip, DXF y .json.

    etiqueta: líneas de texto para la serigrafía inferior (None = el título; [] = ninguna).
    logo: logo de Chirptenna en la serigrafía inferior: 'grande' (o True, por defecto), 'pequeno' o None/False
    (sin logo). Si no cabe ni el grillo, la palabra «Chirptenna». rutas['serigrafia'] dice qué se puso."""
    os.makedirs(carpeta, exist_ok=True)
    rutas = {}
    rutas['placa'] = os.path.join(carpeta, f'{nombre}.kicad_pcb')
    rutas['serigrafia'] = placa_kicad(antena, rutas['placa'], titulo or nombre, etiqueta, logo)
    rutas['huella'] = os.path.join(carpeta, 'Antenas.pretty', f'{nombre}.kicad_mod')
    huella_kicad(antena, rutas['huella'], nombre)
    rutas['dxf'] = os.path.join(carpeta, f'{nombre}.dxf')
    dxf(antena, rutas['dxf'])
    rutas['gerber_zip'] = os.path.join(carpeta, f'{nombre}_gerber_JLC.zip')
    gerber(rutas['placa'], os.path.join(carpeta, 'gerber'), rutas['gerber_zip'])
    rutas['json'] = os.path.join(carpeta, f'{nombre}.json')
    with open(rutas['json'], 'w', encoding='utf-8') as fh:
        json.dump({'tipo': antena.tipo, 'parametros': {k: v for k, v in antena.parametros.items()
                                                        if not k.startswith('_')},
                   'info': antena.info}, fh, indent=2, ensure_ascii=False, default=float)
    rutas['drc'] = drc(rutas['placa'])
    if antena.info.get('integrada'):
        # F3.3: huella con la zona de exclusión y una placa de ejemplo que la usa (KiCad rellena la masa y respeta la zona)
        rutas['huella_integrar'] = os.path.join(carpeta, 'Antenas.pretty', f'{nombre}_integrar.kicad_mod')
        huella_kicad(antena, rutas['huella_integrar'], f'{nombre}_integrar', integrar=True)
        rutas['placa_ejemplo'] = os.path.join(carpeta, f'{nombre}_ejemplo_integrada.kicad_pcb')
        placa_ejemplo_integrada(antena, rutas['placa_ejemplo'], f'{nombre}_integrar')
        rutas['drc'] = rutas['drc'] + [(t, sev, 'ejemplo: ' + d) for t, sev, d in drc(rutas['placa_ejemplo'], rellenar=True)]
    if antena.reflector:
        # Panel: segunda placa (reflector), con sus Gerber y su DXF
        rutas['placa_reflector'] = os.path.join(carpeta, f'{nombre}_reflector.kicad_pcb')
        placa_reflector(antena, rutas['placa_reflector'], titulo or nombre)
        rutas['gerber_zip_reflector'] = os.path.join(carpeta, f'{nombre}_reflector_gerber_JLC.zip')
        gerber(rutas['placa_reflector'], os.path.join(carpeta, 'gerber_reflector'), rutas['gerber_zip_reflector'])
        rutas['dxf_reflector'] = os.path.join(carpeta, f'{nombre}_reflector.dxf')
        dxf_reflector(antena, rutas['dxf_reflector'])
        rutas['drc'] = rutas['drc'] + [(t, sev, 'reflector: ' + d) for t, sev, d in drc(rutas['placa_reflector'])]
    return rutas
