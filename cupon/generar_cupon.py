"""Genera los cupones de calibración de εr (KiCad) para FR4 de JLC, en placas de 100 × 100 mm.

Placa A (cupon_A):
  - Anillo R868: modo n=1 a 868 MHz (también n=2 ≈1,74 GHz y n=3 ≈2,6 GHz).
  - Anillo R2G4: modo n=1 a 2,4 GHz.
Placa B (cupon_B):
  - Anillo R5G8: modo n=3 a 5,8 GHz (su n=1 ≈1,93 GHz se mide con el NanoVNA-H).
  - Líneas de un puerto abiertas S30 y S80 (30 y 80 mm).
  - Líneas de dos puertos en L, L64 y L17 (63,6 y 16,6 mm), con el mismo codo (método multilínea).
  - Línea coplanar con masa (CPWG) de 50 Ω de dos puertos, con valla de vías: para las pistas de RF
    de las placas de nodos.
  - Línea microstrip de 100 Ω de dos puertos (la de las redes de los arrays): de su rizado salen
    su εeff y su impedancia real.
Todo alimentado por SMA de canto (huella Samtec SMA-J-P-H-ST-EM1), con ≥ 11 mm entre conectores
de un mismo borde para que quepa la llave.

Las líneas y transiciones son zonas de cobre con la net de su SMA (bordes rectos y
extremos abiertos cuadrados); los anillos son dos pistas en arco.

Los radios de los anillos van ×CORRECCION_ANILLO: el de 2,4 GHz simulado (simular_anillo.py) resonaba
un 7 % bajo (2,236 GHz) por la carga del acoplo y la curvatura que no ve la fórmula de la línea recta.

Uso: python generar_cupon.py   ->  cupon_A/, cupon_B/ (placa, Gerber, zip para JLC, DRC, diseno.json)
"""
import os
import sys
import json
import math
import uuid

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, 'fase0'))
sys.path.insert(0, RAIZ)
from comun import ancho_microstrip, eps_eff_microstrip   # noqa: E402
from antenas import exportar   # noqa: E402

C0 = 299792458.0
ER, H = 4.5, 1.6          # FR4 de JLC (calculadora de impedancias), 1,6 mm
GAP = 0.25                # hueco de acoplo de los anillos [mm]
CORRECCION_ANILLO = 0.93  # radio: la simulación del de 2,4 GHz salió un 7 % baja
ANCHO_PLACA, ALTO_PLACA = 100.0, 100.0
W = round(ancho_microstrip(50, ER, H), 2)
W100 = round(ancho_microstrip(100, ER, H), 2)
EPS_EFF = eps_eff_microstrip(ER, H, W)
TAPER = 2.0               # transición del pad del SMA (1,27 mm) a la pista
W_PAD = 1.27
SMA_BORDE = 2.1           # distancia del origen de la huella al borde de la placa
SMA_PAD_FIN = 1.6         # extremo interior del pad central respecto al origen
CPWG_HUECO = 0.3          # hueco de la coplanar a la masa superior [mm]
CPWG_MASA = 4.0           # ancho de la masa superior a cada lado [mm]
VIA_PASO = 3.0            # paso de la valla de vías de la coplanar [mm]

objetos = []              # elementos S-expresión del cuerpo de la placa
piezas = {}               # net -> polígonos de cobre que se funden en una sola zona
diseno = {}
nets = []


def nueva_placa():
    objetos.clear()
    piezas.clear()
    nets[:] = ['', 'GND']
    diseno.clear()
    diseno.update({'material': {'er': ER, 'h_mm': H, 'w_50ohm_mm': W, 'w_100ohm_mm': W100,
                                'eps_eff_hammerstad': round(EPS_EFF, 4)},
                   'estructuras': {}})


def u():
    return str(uuid.uuid4())


def net(nombre):
    if nombre not in nets:
        nets.append(nombre)
    return nets.index(nombre)


def zona(pts, n, prioridad=1):
    """Zona de cobre en F.Cu ya rellena con el mismo contorno, con net n."""
    xy = ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in pts)
    objetos.append(f'  (zone (net {n}) (net_name "{nets[n]}") (layer "F.Cu") (uuid "{u()}") (hatch edge 0.5)\n'
                   f'    (priority {prioridad}) (connect_pads yes (clearance 0)) (min_thickness 0.1) (filled_areas_thickness no)\n'
                   f'    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 1))\n'
                   f'    (polygon (pts {xy}))\n'
                   f'    (filled_polygon (layer "F.Cu") (pts {xy})))')


def pieza(pts, n):
    """Añade un polígono de cobre a la net n; al final se funden en una zona por net."""
    piezas.setdefault(n, []).append(Polygon(pts))


def rect(x0, y0, x1, y1, n):
    pieza([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], n)


def emitir_zonas():
    for n, pols in piezas.items():
        union = unary_union(pols)
        if union.geom_type != 'Polygon':
            raise RuntimeError(f'El cobre de la net {nets[n]} no es una sola pieza')
        zona(list(union.exterior.coords)[:-1], n)


def texto(t, x, y, tam=1.5, rot=0, capa='F.SilkS'):
    """Texto de serigrafía; en la cara inferior va espejado para leerse dándole la vuelta a la placa."""
    espejo = ' (justify mirror)' if capa.startswith('B.') else ''
    objetos.append(f'  (gr_text "{t}" (at {x:.3f} {y:.3f} {rot}) (layer "{capa}") (uuid "{u()}")\n'
                   f'    (effects (font (size {tam} {tam}) (thickness {tam*0.15:.3f})){espejo}))')


def leyenda(titulo, lineas, x=ANCHO_PLACA/2, tam=1.15):
    """Leyenda de la placa en la serigrafía inferior (toda la cara es masa: hay sitio, salvo las vías)."""
    texto(titulo, x, 12.0, 1.6*tam/1.15, capa='B.SilkS')
    for i, t in enumerate(lineas):
        texto(t, x, 20.0 + 3.6*tam*i, tam, capa='B.SilkS')


def via(x, y):
    objetos.append(f'  (via (at {x:.4f} {y:.4f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) (uuid "{u()}"))')


def pista(x0, y0, x1, y1, ancho, n):
    objetos.append(f'  (segment (start {x0:.4f} {y0:.4f}) (end {x1:.4f} {y1:.4f}) (width {ancho}) '
                   f'(layer "F.Cu") (net {n}) (uuid "{u()}"))')


def arco(p0, pm, p1, ancho, n):
    objetos.append(f'  (arc (start {p0[0]:.4f} {p0[1]:.4f}) (mid {pm[0]:.4f} {pm[1]:.4f}) (end {p1[0]:.4f} {p1[1]:.4f}) '
                   f'(width {ancho}) (layer "F.Cu") (net {n}) (uuid "{u()}"))')


def sma(ref, borde, pos, señal, w_linea=None, vias_masa=True, rotulo=5.5):
    """SMA de canto en un borde ('arriba', 'abajo', 'dcha', 'izda') a la coordenada pos.

    Devuelve el punto donde acaba la transición (empieza la pista de ancho w_linea, por defecto la
    de 50 Ω), el vector unitario hacia el interior de la placa y la net de la señal.
    """
    w_linea = w_linea or W
    # rotación de la huella: su +x local (hacia fuera del conector) apunta al exterior
    rot, dentro = {'arriba': (90, (0, 1)), 'abajo': (270, (0, -1)),
                   'dcha': (0, (-1, 0)), 'izda': (180, (1, 0))}[borde]
    bx, by = {'arriba': (pos, 0.0), 'abajo': (pos, ALTO_PLACA),
              'dcha': (ANCHO_PLACA, pos), 'izda': (0.0, pos)}[borde]
    ox, oy = bx + dentro[0]*SMA_BORDE, by + dentro[1]*SMA_BORDE
    ns = net(señal)
    a = math.radians(rot)

    def loc(lx, ly):          # coordenadas locales de la huella -> placa (y hacia abajo)
        return ox + lx*math.cos(a) + ly*math.sin(a), oy - lx*math.sin(a) + ly*math.cos(a)

    pads = [f'    (pad "1" smd roundrect (at 0 0 {(90 + rot) % 360}) (size {W_PAD} 3.2) (layers "F.Cu" "F.Mask") '
            f'(roundrect_rratio 0.2) (net {ns} "{señal}") (uuid "{u()}"))']
    for ly in (-2.825, 2.825):
        for capa in ('F', 'B'):
            pads.append(f'    (pad "2" smd roundrect (at -0.25 {ly} {(90 + rot) % 360}) (size 1.35 3.7) '
                        f'(layers "{capa}.Cu" "{capa}.Mask") (roundrect_rratio 0.185) (net 1 "GND") (uuid "{u()}"))')
    objetos.append(f'  (footprint "Cupon:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount" (layer "F.Cu") (uuid "{u()}") '
                   f'(at {ox:.4f} {oy:.4f} {rot})\n'
                   f'    (property "Reference" "{ref}" (at -7 0 {rot}) (layer "F.Fab") (uuid "{u()}") '
                   f'(effects (font (size 1 1) (thickness 0.15))))\n'
                   f'    (property "Value" "SMA_edge" (at -9 0 {rot}) (layer "F.Fab") (uuid "{u()}") '
                   f'(effects (font (size 1 1) (thickness 0.15))))\n'
                   f'    (attr smd)\n' + '\n'.join(pads) + '\n  )')
    if vias_masa:
        # vías de masa detrás de los pads de masa, unidas con una pista corta en la cara superior
        for ly in (-2.825, 2.825):
            px, py = loc(-2.1, ly)
            vx, vy = loc(-3.0, ly)
            pista(px, py, vx, vy, 1.0, 1)
            via(vx, vy)
    # transición pad -> pista
    x0, y0 = loc(-SMA_PAD_FIN + 0.3, 0)       # solapa 0,3 mm con el pad
    x1, y1 = loc(-SMA_PAD_FIN - TAPER, 0)
    nx, ny = -dentro[1], dentro[0]
    pieza([(x0 + nx*W_PAD/2, y0 + ny*W_PAD/2), (x1 + nx*w_linea/2, y1 + ny*w_linea/2),
          (x1 - nx*w_linea/2, y1 - ny*w_linea/2), (x0 - nx*W_PAD/2, y0 - ny*W_PAD/2)], ns)
    # rótulo del puerto («R868 A») junto al conector, a un lado de la línea
    tx, ty = loc(-9.0, 0)
    if borde in ('arriba', 'abajo'):
        tx += rotulo if borde == 'arriba' else -rotulo
    else:
        ty -= 3.5
    texto(ref.removeprefix('J_').replace('_', ' '), tx, ty, 1.0)
    return (x1, y1), dentro, ns


def tramo(p0, p1, n, ancho=None):
    """Rectángulo de ancho W (o 'ancho') entre dos puntos alineados con un eje."""
    ancho = ancho or W
    (x0, y0), (x1, y1) = p0, p1
    if abs(x0 - x1) < 1e-9:
        rect(x0 - ancho/2, min(y0, y1), x0 + ancho/2, max(y0, y1), n)
    else:
        rect(min(x0, x1), y0 - ancho/2, max(x0, x1), y0 + ancho/2, n)


def anillo(nombre, cx, f_obj, modo):
    lam_g = C0/(f_obj*math.sqrt(EPS_EFF))*1e3
    r = CORRECCION_ANILLO*modo*lam_g/(2*math.pi)
    cy = ALTO_PLACA/2
    n_anillo = net(f'{nombre}_anillo')
    arco((cx, cy - r), (cx + r, cy), (cx, cy + r), W, n_anillo)
    arco((cx, cy + r), (cx - r, cy), (cx, cy - r), W, n_anillo)
    for borde, signo in (('arriba', -1), ('abajo', 1)):
        lado = 'A' if signo < 0 else 'B'
        p, d, ns = sma(f'J_{nombre}_{lado}', borde, cx, f'{nombre}_{lado}')
        y_fin = cy + signo*(r + W/2 + GAP)
        tramo(p, (cx, y_fin), ns)
    texto(nombre, cx, cy - 2.5, 2.0)
    texto(f'{f_obj/1e9:g} GHz (n={modo})', cx, cy + 0.8, 1.0)
    texto(f'r={r:.2f} g={GAP}', cx, cy + 2.6, 1.0)
    f1 = f_obj/modo
    diseno['estructuras'][nombre] = {
        'tipo': 'anillo', 'centro_mm': [round(cx, 3), round(cy, 3)], 'radio_medio_mm': round(r, 3),
        'ancho_mm': W, 'gap_mm': GAP, 'modo_diseno': modo, 'f_diseno_GHz': f_obj/1e9,
        'correccion_radio': CORRECCION_ANILLO,
        'modos_en_rango_GHz': [round(k*f1/1e9, 3) for k in range(1, 8) if k*f1 <= 2.7e9]}
    return r


def stub(nombre, x, largo):
    p, d, ns = sma(f'J_{nombre}', 'arriba', x, nombre)
    tramo(p, (x, p[1] + largo), ns)
    texto(f'{nombre} abierta {largo:g} mm', x + 4, p[1] + largo/2 + 6, 1.2, 90)
    diseno['estructuras'][nombre] = {'tipo': 'linea_1_puerto_abierta', 'x_mm': x,
                                     'longitud_desde_transicion_mm': largo}


def linea_L(nombre, x_abajo, y_codo):
    """Línea de dos puertos: del borde inferior sube hasta y_codo y gira hacia el borde derecho."""
    p_a, _, ns = sma(f'J_{nombre}_A', 'abajo', x_abajo, nombre)
    p_b, _, _ = sma(f'J_{nombre}_B', 'dcha', y_codo, nombre)
    c = W*0.9                                  # chaflán en la esquina exterior del codo
    xi, xd = x_abajo - W/2, x_abajo + W/2
    ys, yi = y_codo - W/2, y_codo + W/2
    pieza([(xi, p_a[1]), (xi, ys + c), (xi + c, ys), (p_b[0], ys), (p_b[0], yi), (xd, yi), (xd, p_a[1])], ns)
    largo = (p_a[1] - y_codo) + (p_b[0] - x_abajo)    # por el eje
    # descripción al otro lado del rótulo del puerto; en las cortas, abreviada para que quepa
    corta = p_a[1] - y_codo < 30
    texto(f'{nombre} {largo:.1f} mm' if corta else f'{nombre} 2 puertos {largo:.1f} mm',
          x_abajo + 4, (p_a[1] + y_codo)/2 + (1.5 if corta else 0), 1.0 if corta else 1.2, 90)
    diseno['estructuras'][nombre] = {'tipo': 'linea_2_puertos_L', 'x_tramo_vertical_mm': x_abajo,
                                     'y_codo_mm': y_codo, 'longitud_eje_entre_transiciones_mm': round(largo, 3)}


def linea_recta(nombre, x, ancho, z_ohm):
    """Microstrip de dos puertos de borde a borde (arriba-abajo) de ancho dado."""
    p_a, _, ns = sma(f'J_{nombre}_A', 'arriba', x, nombre, w_linea=ancho)
    p_b, _, _ = sma(f'J_{nombre}_B', 'abajo', x, nombre, w_linea=ancho)
    tramo(p_a, p_b, ns, ancho)
    texto(f'{nombre} microstrip {z_ohm} ohm W={ancho}', x + 3.0, ALTO_PLACA/2, 1.2, 90)
    diseno['estructuras'][nombre] = {'tipo': 'microstrip_2_puertos', 'x_mm': x, 'ancho_mm': ancho,
                                     'z_diseno_ohm': z_ohm, 'longitud_entre_transiciones_mm': round(p_b[1] - p_a[1], 3),
                                     'eps_eff_hammerstad': round(eps_eff_microstrip(ER, H, ancho), 4)}


# ------------------------------------------------------------------ coplanar con masa (CPWG)
def _k_eliptica(k):
    """Integral elíptica completa de primera especie K(k) por la media aritmético-geométrica."""
    a, b = 1.0, math.sqrt(1 - k*k)
    for _ in range(40):
        a, b = (a + b)/2, math.sqrt(a*b)
    return math.pi/(2*a)


def cpwg_z(w, s, er=ER, h=H):
    """Z0 y εeff de la coplanar con plano de masa inferior (masa superior ancha)."""
    k = w/(w + 2*s)
    k3 = math.tanh(math.pi*w/(4*h))/math.tanh(math.pi*(w + 2*s)/(4*h))
    r1 = _k_eliptica(math.sqrt(1 - k*k))/_k_eliptica(k)          # K(k')/K(k)
    r3 = _k_eliptica(k3)/_k_eliptica(math.sqrt(1 - k3*k3))        # K(k3)/K(k3')
    ee = (1 + er*r1*r3)/(1 + r1*r3)
    z = 60*math.pi/math.sqrt(ee)/(1/r1 + r3)
    return z, ee


def cpwg_ancho(z_obj, s):
    lo, hi = 0.1, 10.0
    for _ in range(60):
        m = (lo + hi)/2
        if cpwg_z(m, s)[0] > z_obj:
            lo = m
        else:
            hi = m
    return round((lo + hi)/2, 2)


def linea_cpwg(nombre, x):
    """Coplanar con masa de 50 Ω de dos puertos (arriba-abajo), masa superior a los lados unida a la
    inferior por una valla de vías a cada lado."""
    w = cpwg_ancho(50, CPWG_HUECO)
    z, ee = cpwg_z(w, CPWG_HUECO)
    lado = w/2 + CPWG_HUECO + CPWG_MASA
    # rótulos de los puertos fuera de la masa superior (sobre la valla de vías se recortarían)
    p_a, _, ns = sma(f'J_{nombre}_A', 'arriba', x, nombre, w_linea=w, vias_masa=False, rotulo=lado + 3.4)
    p_b, _, _ = sma(f'J_{nombre}_B', 'abajo', x, nombre, w_linea=w, vias_masa=False, rotulo=lado + 3.4)
    tramo(p_a, p_b, ns, w)
    # masa superior: banda a los lados de la señal (pad, transición y línea) con el hueco s
    senal = unary_union(piezas[ns]).union(box(x - W_PAD/2, 0, x + W_PAD/2, ALTO_PLACA))
    masa = box(x - lado, 0.5, x + lado, ALTO_PLACA - 0.5).difference(senal.buffer(CPWG_HUECO, join_style=2))
    for pol in getattr(masa, 'geoms', [masa]):
        zona(list(pol.exterior.coords)[:-1], 1, prioridad=0)
    # valla de vías a 1 mm del hueco, desde detrás del conector hasta el otro
    xv = w/2 + CPWG_HUECO + 1.0
    n_v = int((ALTO_PLACA - 2*5.0)//VIA_PASO)
    y0 = (ALTO_PLACA - n_v*VIA_PASO)/2
    for i in range(n_v + 1):
        for sx in (-1, 1):
            via(x + sx*xv, y0 + i*VIA_PASO)
    texto(f'{nombre} coplanar 50 ohm W={w} s={CPWG_HUECO}', x + lado + 2, ALTO_PLACA/2, 1.2, 90)
    diseno['estructuras'][nombre] = {'tipo': 'cpwg_2_puertos', 'x_mm': x, 'ancho_mm': w, 'hueco_mm': CPWG_HUECO,
                                     'masa_superior_mm': CPWG_MASA, 'paso_vias_mm': VIA_PASO,
                                     'z_diseno_ohm': round(z, 1), 'eps_eff_diseno': round(ee, 4),
                                     'longitud_entre_transiciones_mm': round(p_b[1] - p_a[1], 3)}


def plano_masa():
    m = 0.5
    pts = [(m, m), (ANCHO_PLACA - m, m), (ANCHO_PLACA - m, ALTO_PLACA - m), (m, ALTO_PLACA - m)]
    xy = ' '.join(f'(xy {x} {y})' for x, y in pts)
    objetos.append(f'  (zone (net 1) (net_name "GND") (layer "B.Cu") (uuid "{u()}") (hatch edge 0.5)\n'
                   f'    (connect_pads yes (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n'
                   f'    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
                   f'    (polygon (pts {xy}))\n'
                   f'    (filled_polygon (layer "B.Cu") (pts {xy})))')


def escribir(nombre):
    carpeta = os.path.join(AQUI, nombre)
    os.makedirs(carpeta, exist_ok=True)
    cabecera = ['(kicad_pcb (version 20240108) (generator "generar_cupon") (generator_version "8.0")',
                f'  (general (thickness {H}) (legacy_teardrops no))', '  (paper "A4")',
                '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") '
                '(33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user) '
                '(36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) '
                '(39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments") '
                '(42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2") (44 "Edge.Cuts" user) '
                '(45 "Margin" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") '
                '(48 "B.Fab" user) (49 "F.Fab" user))',
                '  (setup (pad_to_mask_clearance 0))']
    cabecera += [f'  (net {i} "{n}")' for i, n in enumerate(nets)]
    ruta = os.path.join(carpeta, f'{nombre}.kicad_pcb')
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(cabecera + objetos) + '\n)\n')
    diseno['placa_mm'] = [ANCHO_PLACA, ALTO_PLACA]
    diseno['transicion_sma'] = {'pad_mm': W_PAD, 'taper_mm': TAPER}
    exportar.gerber(ruta, os.path.join(carpeta, 'gerber'), os.path.join(carpeta, f'{nombre}_JLC.zip'))
    diseno['drc'] = [list(v) for v in exportar.drc(ruta)]
    with open(os.path.join(carpeta, 'diseno.json'), 'w', encoding='utf-8') as fh:
        json.dump(diseno, fh, indent=2, ensure_ascii=False)
    print(f'{nombre}:', ', '.join(f'{k} ({v["tipo"]})' for k, v in diseno['estructuras'].items()),
          f'| DRC: {len(diseno["drc"])} infracciones', diseno['drc'][:5])


def comun_placa():
    objetos.append(f'  (gr_rect (start 0 0) (end {ANCHO_PLACA} {ALTO_PLACA}) (stroke (width 0.1) (type default)) '
                   f'(fill none) (layer "Edge.Cuts") (uuid "{u()}"))')
    plano_masa()


def placa_A():
    nueva_placa()
    comun_placa()
    anillo('R868', 34.0, 868e6, 1)
    anillo('R2G4', 83.0, 2.4e9, 1)
    emitir_zonas()
    texto(f'CUPON A er FR4 {H} W50={W} g={GAP}', 62.0, 93.0, 1.2)
    texto('2026-11', 62.0, 96.0, 1.0)
    leyenda('CUPON A - medida de er del FR4', [
        f'FR4 JLC {H} mm, lineas de 50 ohm W={W} mm',
        'R868: anillo de 868 MHz; modos n=1,2,3 a',
        '  0,87 / 1,74 / 2,60 GHz. Medir S21 de R868 A a R868 B',
        'R2G4: anillo de 2,4 GHz. Medir S21 de R2G4 A a R2G4 B',
        f'Radios x{CORRECCION_ANILLO} (correccion por simulacion), hueco {GAP} mm',
        'Los picos de S21 dan er: ajustarla simulando el anillo',
        'Puertos sin usar: al aire o con carga de 50 ohm',
    ])
    escribir('cupon_A')


def placa_B():
    nueva_placa()
    comun_placa()
    anillo('R5G8', 18.0, 5.8e9, 3)
    linea_cpwg('CPWG50', 44.0)
    linea_recta('MS100', 57.0, W100, 100)
    # Separaciones ≥ 7 mm (>4h) entre estructuras para que no se acoplen
    stub('S80', 68.0, 80.0)
    stub('S30', 79.0, 30.0)
    linea_L('L64', 80.0, 45.0)
    linea_L('L17', 92.0, 80.0)
    emitir_zonas()
    texto('CUPON B', 26.0, 90.0, 1.2)
    texto(f'FR4 {H} 2026-11', 26.0, 93.0, 1.0)
    w_cpwg = diseno['estructuras']['CPWG50']['ancho_mm']
    # la valla de vías de la coplanar está en x ≈ 42–46: la leyenda va en la mitad de x > 48
    leyenda('CUPON B - er y lineas', [
        f'FR4 JLC {H} mm, 50 ohm W={W} mm',
        'R5G8: anillo 5,8 GHz (n=3);',
        '  su n=1 a 1,93 GHz. S21 A-B',
        'S80, S30: abiertas de 80 y 30 mm. S11',
        'L64, L17: en L de 2 puertos, mismo',
        '  codo: multilinea/TRL. S21 A-B',
        'CPWG50: coplanar con masa,',
        f'  W={w_cpwg} s={CPWG_HUECO}, vias c/{VIA_PASO:g} mm',
        f'MS100: microstrip 100 ohm W={W100}',
        '  (redes de arrays): eps_eff y Z0',
    ], x=74.0, tam=1.0)
    escribir('cupon_B')


def main():
    placa_A()
    placa_B()


if __name__ == '__main__':
    main()
