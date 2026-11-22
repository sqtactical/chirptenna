"""Carcasa impresa en 3D para meter la antena: STL de la base y de la tapa, y los mismos bloques para simularla.

Geometría (mm, como el modelo: x a la derecha, y hacia arriba, z = 0 la cara inferior de la placa y z = h la superior):
- **Base**: bandeja con suelo, paredes hasta `z_div` y un reborde de apoyo de 2 mm bajo los cantos de la placa.
- **Tapa**: placa superior con falda y un labio que entra en la base (holgura de 0,2 mm), listo para imprimir boca abajo.
- Opcionales: cuatro orejetas para tornillos autorroscantes (agujero ciego de 1,8 mm en la base, pasante de 2,4 mm en la tapa)
  y una abertura en la pared por donde sale el conector.
La carcasa envuelve el rectángulo que contiene la placa. Se simula como bloques dieléctricos de caras rectas
(`bloques`: suelo, tapa y cuatro paredes; sin esquinas redondeadas, labio, reborde ni orejetas, que pesan poco).
Los materiales de impresión son valores típicos de FDM al 100 % de relleno: un relleno menor baja la εr efectiva.
"""
import math
import struct

import numpy as np
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from .i18n import tr

# nombre -> (εr, tanδ) del material macizo a ~2,4 GHz. Valores TÍPICOS de hojas técnicas y literatura, sin medir: varían con la marca, el color (los
# pigmentos y los retardantes de llama los suben), el secado y el contenido de fibra. Para el tuyo, mídelo con el cupón C (`antenas/plastico.py`).
# Los rellenos de fibra de carbono (CF), los de grafito y los filamentos conductores o ESD NO valen: son conductores y apantallan la antena.
MATERIALES = {
    'PLA': (2.7, 0.008), 'PETG': (2.8, 0.010), 'ABS': (2.8, 0.010), 'ASA': (2.8, 0.012), 'PC': (2.9, 0.010),
    'PA12': (3.0, 0.020), 'PA6': (3.4, 0.030),
    'PLA-GF': (3.0, 0.010), 'PETG-GF': (3.3, 0.012), 'ABS-GF': (3.1, 0.012), 'PA-GF': (3.8, 0.020),
}
# texto de cada material en la interfaz (castellano; la interfaz lo traduce)
DESCRIPCIONES = {
    'PLA': 'PLA', 'PETG': 'PETG', 'ABS': 'ABS', 'ASA': 'ASA', 'PC': 'PC (policarbonato)',
    'PA12': 'PA12 (nailon 12, seco)', 'PA6': 'PA6 (nailon 6, seco: húmedo sube la εr y las pérdidas)',
    'PLA-GF': 'PLA con fibra de vidrio (GF)', 'PETG-GF': 'PETG con fibra de vidrio (GF)', 'ABS-GF': 'ABS con fibra de vidrio (GF)',
    'PA-GF': 'Nailon con fibra de vidrio (PA-GF)',
}
DEFECTO = {'material': 'PLA', 'relleno': 100.0, 'er': 2.8, 'tand': 0.010, 'pared': 1.6, 'holgura': 0.5, 'espacio_abajo': 3.0, 'espacio_arriba': 4.0,
           'radio': 2.0, 'fijacion': 'rosca', 'tornillo': 'M2', 'abertura': 1}
LIMITES = {'relleno': (20.0, 100.0), 'er': (1.0, 12.0), 'tand': (0.0, 0.1), 'pared': (0.8, 4.0), 'holgura': (0.2, 3.0), 'espacio_abajo': (1.0, 15.0), 'espacio_arriba': (2.5, 20.0),
           'radio': (0.5, 10.0)}
# Cómo se cierra la carcasa (clave -> texto de la interfaz, en castellano; la interfaz lo traduce)
FIJACIONES = {'rosca': 'Tornillo autorroscante (agujero ciego en el plástico)',
              'tuerca': 'Tornillo y tuerca (la tuerca entra por debajo)',
              'inserto': 'Tornillo e inserto roscado de latón (a soldador)',
              'adhesivo': 'Sin tornillos: pegada (cianoacrilato o epoxi)'}
# mm. paso = diámetro del tornillo; pasante = agujero de paso; cabeza/cabeza_h = cabeza cilíndrica y su altura; rosca = agujero
# para autorroscante; inserto/inserto_h = agujero y profundidad del inserto; tuerca_ac/tuerca_h = tuerca entre caras y su grosor
TORNILLOS = {
    'M2': {'paso': 2.0, 'pasante': 2.4, 'cabeza': 4.0, 'cabeza_h': 1.6, 'rosca': 1.7, 'inserto': 3.2, 'inserto_h': 3.5, 'tuerca_ac': 4.0, 'tuerca_h': 1.6},
    'M2.5': {'paso': 2.5, 'pasante': 2.9, 'cabeza': 5.0, 'cabeza_h': 2.0, 'rosca': 2.1, 'inserto': 3.8, 'inserto_h': 4.0, 'tuerca_ac': 5.0, 'tuerca_h': 2.0},
    'M3': {'paso': 3.0, 'pasante': 3.4, 'cabeza': 6.0, 'cabeza_h': 2.4, 'rosca': 2.5, 'inserto': 4.6, 'inserto_h': 5.0, 'tuerca_ac': 5.5, 'tuerca_h': 2.4},
}
ANCHO_ABERTURA = 9.0       # ancho y alto del hueco del conector
BORDE_APOYO = 2.0          # lo que el reborde se mete bajo la placa
HOLGURA_LABIO = 0.2


PERSONALIZADO = 'Personalizado'     # εr y tanδ los pone el usuario (p. ej. medidos con el cupón C: `antenas/plastico.py`)


# Los valores de MATERIALES son a F_REF. Para otra frecuencia se aplica una tendencia GENÉRICA de los polímeros de impresión (suposición, no medida de cada
# material): la εr casi no cambia con la frecuencia (sube ~3 % por década hacia abajo) y la tanδ baja al bajar la frecuencia (∝ f^0,3). No hay medidas de estos
# filamentos a 868 MHz que yo haya encontrado; a 868 MHz esto da +1,2 % de εr y −27 % de tanδ respecto a 2,4 GHz. Mide el tuyo (cupón C) y úsalo como «Personalizado».
F_REF = 2.4e9
K_ER_DECADA = 0.03
N_TAND = 0.3
F_MIN, F_MAX = 0.3e9, 6.0e9


def escalar_frecuencia(er, tand, f_Hz):
    """(εr, tanδ) de un material de la lista a la frecuencia f_Hz, con la tendencia genérica de arriba (acotada a 0,3–6 GHz)."""
    if not f_Hz:
        return er, tand
    f = min(max(float(f_Hz), F_MIN), F_MAX)
    return er*(1 + K_ER_DECADA*math.log10(F_REF/f)), tand*(f/F_REF)**N_TAND


def propiedades(c, f_Hz=None):
    """(εr, tanδ) del material de la carcasa a la frecuencia f_Hz (por defecto, la de referencia de la tabla, 2,4 GHz).

    Un material de la lista se da macizo: con `relleno` < 100 % se mezcla con aire (fórmula de índices de refracción, εr_ef = (f·√εr + 1 − f)²) y la
    tanδ se reparte por energía (f·εr·tanδ/εr_ef). El «Personalizado» se toma tal cual: se supone medido ya con el relleno, la orientación y la
    frecuencia que interesan (no se escala)."""
    c = completar(c)
    if c['material'] == PERSONALIZADO:
        return c['er'], c['tand']
    er, tand = escalar_frecuencia(*MATERIALES[c['material']], f_Hz)
    f = c['relleno']/100.0
    if f >= 1.0:
        return er, tand
    er_ef = (f*math.sqrt(er) + 1 - f)**2
    return er_ef, tand*f*er/er_ef

def completar(c):
    """Parámetros con los valores por defecto y dentro de sus límites."""
    c = dict(c or {})
    if 'fijacion' not in c and 'tornillos' in c:          # diseños guardados antes de elegir la fijación
        c['fijacion'] = 'rosca' if c['tornillos'] else 'adhesivo'
    c.pop('tornillos', None)
    c = {**DEFECTO, **c}
    if c['material'] not in MATERIALES and c['material'] != PERSONALIZADO:
        c['material'] = DEFECTO['material']
    if c['fijacion'] not in FIJACIONES:
        c['fijacion'] = DEFECTO['fijacion']
    if c['tornillo'] not in TORNILLOS:
        c['tornillo'] = DEFECTO['tornillo']
    for k, (lo, hi) in LIMITES.items():
        c[k] = min(max(float(c[k]), lo), hi)
    c['abertura'] = int(bool(c['abertura']))
    return c


def _orejeta(c):
    """Radio de las orejetas (mm): que quepan la cabeza y el hueco de la tuerca con 1,2 mm de plástico alrededor."""
    t = TORNILLOS[c['tornillo']]
    esquina_tuerca = t['tuerca_ac']/math.sqrt(3) + 0.15
    return max(4.0, t['cabeza']/2 + 1.6, esquina_tuerca + 1.2)


def _esquinas(d):
    return [(d['xo0'], d['yo0']), (d['xo1'], d['yo0']), (d['xo0'], d['yo1']), (d['xo1'], d['yo1'])]


def no_soporta(antena):
    """Motivo por el que no se puede hacer la carcasa de esta antena, o None."""
    if antena.modulos or antena.placas3d or antena.reflector or antena.hilos3d:
        return tr('La carcasa solo vale para antenas de una sola placa plana (sin módulos, reflector ni placas en 3D).')
    return None


def _redondeado(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0)/2 - 0.01, (y1 - y0)/2 - 0.01)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=8)


def _dims(antena, h, c):
    x0, y0, x1, y1 = antena.contorno.bounds
    hol, par, ea, eb = c['holgura'], c['pared'], c['espacio_abajo'], c['espacio_arriba']
    d = {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
         'xi0': x0 - hol, 'yi0': y0 - hol, 'xi1': x1 + hol, 'yi1': y1 + hol}
    d.update(xo0=d['xi0'] - par, yo0=d['yi0'] - par, xo1=d['xi1'] + par, yo1=d['yi1'] + par)
    d.update(z_fondo=-ea - par, z_fondo_in=-ea, z_arriba_in=h + eb, z_arriba=h + eb + par, z_div=h + eb/2)
    return d


def _abertura(antena, h, c, d):
    """Caja (x0, y0, z0, x1, y1, z1) del hueco del conector en la pared, o None."""
    p = antena.puerto or {}
    if not c['abertura'] or not p.get('borde') or not p.get('direccion'):
        return None
    bx, by = p['borde']
    dx, dy = p['direccion']
    a = ANCHO_ABERTURA
    z0, z1 = max(h/2 - a/2, d['z_fondo_in']), h/2 + a/2        # no baja del suelo de la base
    if abs(dy) >= abs(dx):          # el conector sale por arriba o por abajo
        x0, x1 = bx - a/2, bx + a/2
        if dy > 0:                  # la línea entra hacia +y: el conector está en el borde de abajo
            return (x0, d['yo0'] - 1.0, z0, x1, d['yi0'] + BORDE_APOYO + 0.5, z1)
        return (x0, d['yi1'] - BORDE_APOYO - 0.5, z0, x1, d['yo1'] + 1.0, z1)
    y0, y1 = by - a/2, by + a/2
    if dx > 0:
        return (d['xo0'] - 1.0, y0, z0, d['xi0'] + BORDE_APOYO + 0.5, y1, z1)
    return (d['xi1'] - BORDE_APOYO - 0.5, y0, z0, d['xo1'] + 1.0, y1, z1)


def _prismas(antena, h, c):
    """{'base': [...], 'tapa': [...]} con prismas (z0, z1, polígono, '+' suma o '-' resta)."""
    d = _dims(antena, h, c)
    dentro = _redondeado(d['xi0'], d['yi0'], d['xi1'], d['yi1'], c['radio'])
    fuera = dentro.buffer(c['pared'], quad_segs=8)
    pared = fuera.difference(dentro)
    apoyo = dentro.difference(dentro.buffer(-BORDE_APOYO))
    lab_h = max(0.8, min(2.0, c['espacio_arriba']/2 - 0.2))
    labio_ext = dentro.buffer(-HOLGURA_LABIO)
    labio = labio_ext.difference(labio_ext.buffer(-1.0))
    base = [(d['z_fondo'], d['z_fondo_in'], fuera, '+'), (d['z_fondo_in'], d['z_div'], pared, '+'),
            (d['z_fondo_in'], 0.0, apoyo, '+')]
    tapa = [(d['z_arriba_in'], d['z_arriba'], fuera, '+'), (d['z_div'], d['z_arriba_in'], pared, '+'),
            (d['z_div'] - lab_h, d['z_div'], labio, '+')]
    if c['fijacion'] != 'adhesivo':
        t = TORNILLOS[c['tornillo']]
        radio_o = _orejeta(c)
        e = 0.01
        for ex, ey in _esquinas(d):
            oreja = Point(ex, ey).buffer(radio_o, quad_segs=8)
            pasante = Point(ex, ey).buffer(t['pasante']/2, quad_segs=8)
            base.append((d['z_fondo'], d['z_div'], oreja, '+'))
            tapa.append((d['z_div'], d['z_arriba'], oreja, '+'))
            # tapa: agujero de paso y asiento de la cabeza, desde arriba (la cabeza queda a ras)
            tapa += [(d['z_div'] - e, d['z_arriba'] + e, pasante, '-'),
                     (d['z_arriba'] - t['cabeza_h'] - 0.2, d['z_arriba'] + e, Point(ex, ey).buffer(t['cabeza']/2 + 0.2, quad_segs=8), '-')]
            if c['fijacion'] == 'rosca':
                base.append((d['z_fondo'] + 1.0, d['z_div'] + e, Point(ex, ey).buffer(t['rosca']/2, quad_segs=8), '-'))
            elif c['fijacion'] == 'inserto':
                base.append((d['z_div'] - t['inserto_h'], d['z_div'] + e, Point(ex, ey).buffer(t['inserto']/2, quad_segs=8), '-'))
            else:   # tuerca: agujero de paso entero y el hueco hexagonal abierto por debajo
                base.append((d['z_fondo'] - e, d['z_div'] + e, pasante, '-'))
                rc = t['tuerca_ac']/math.sqrt(3) + 0.15       # radio hasta las esquinas del hexágono, con holgura
                hexa = Polygon([(ex + rc*math.cos(math.radians(60*i + 30)), ey + rc*math.sin(math.radians(60*i + 30))) for i in range(6)])
                base.append((d['z_fondo'] - e, d['z_fondo'] + t['tuerca_h'] + 0.2, hexa, '-'))
    ab = _abertura(antena, h, c, d)
    if ab:
        hueco = box(ab[0], ab[1], ab[3], ab[4])
        for pieza in (base, tapa):
            pieza.append((ab[2], ab[5], hueco, '-'))
    return {'base': base, 'tapa': tapa}, d


def _losas(prismas):
    """Capas horizontales [(za, zb, polígono)] de una pieza: suma de los prismas '+' menos los '-'."""
    cortes = sorted({round(z, 6) for p in prismas for z in (p[0], p[1])})
    out = []
    for za, zb in zip(cortes[:-1], cortes[1:]):
        zm = (za + zb)/2
        mas = [p[2] for p in prismas if p[3] == '+' and p[0] <= zm <= p[1]]
        if not mas:
            continue
        poli = unary_union(mas)
        menos = [p[2] for p in prismas if p[3] == '-' and p[0] <= zm <= p[1]]
        if menos:
            poli = poli.difference(unary_union(menos))
        poli = set_precision(poli.buffer(0), 1e-4)
        if not poli.is_empty and poli.area > 1e-6:
            out.append((za, zb, poli))
    return out


def _partes(g):
    return [] if g.is_empty else (list(g.geoms) if hasattr(g, 'geoms') else [g])


def _tapas(poli, z, arriba, tris):
    """Triángulos de una cara horizontal (normal hacia +z si `arriba`)."""
    for pg in _partes(poli):
        if pg.geom_type != 'Polygon' or pg.area < 1e-6:
            continue
        for t in constrained_delaunay_triangles(pg).geoms:
            xy = list(orient(t, 1.0).exterior.coords)[:3]
            v = [(x, y, z) for x, y in xy]
            tris.append(v if arriba else [v[0], v[2], v[1]])


def malla(prismas):
    """Triángulos [[(x,y,z)×3], …] de la pieza, con las normales hacia fuera."""
    losas = _losas(prismas)
    tris = []
    for k, (za, zb, poli) in enumerate(losas):
        sobre = losas[k + 1][2] if k + 1 < len(losas) and abs(losas[k + 1][0] - zb) < 1e-6 else None
        bajo = losas[k - 1][2] if k > 0 and abs(losas[k - 1][1] - za) < 1e-6 else None
        _tapas(poli if sobre is None else poli.difference(sobre), zb, True, tris)
        _tapas(poli if bajo is None else poli.difference(bajo), za, False, tris)
        for pg in _partes(poli):
            if pg.geom_type != 'Polygon':
                continue
            pg = orient(pg, 1.0)
            for anillo in (pg.exterior, *pg.interiors):
                pts = list(anillo.coords)
                for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
                    if (ax, ay) == (bx, by):
                        continue
                    tris.append([(ax, ay, za), (bx, by, za), (bx, by, zb)])
                    tris.append([(ax, ay, za), (bx, by, zb), (ax, ay, zb)])
    return tris


def volumen_mm3(tris):
    """Volumen con signo de la malla (positivo si las normales miran hacia fuera)."""
    t = np.asarray(tris, float)
    return float(np.einsum('ij,ij->', t[:, 0], np.cross(t[:, 1], t[:, 2]))/6.0)


def escribir_stl(ruta, tris, nombre='Chirptenna'):
    """STL binario."""
    t = np.asarray(tris, np.float32)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ln = np.linalg.norm(n, axis=1)
    n = np.where(ln[:, None] > 0, n/np.maximum(ln, 1e-20)[:, None], 0).astype(np.float32)
    with open(ruta, 'wb') as fh:
        fh.write(f'{nombre} · carcasa'.encode('utf-8')[:80].ljust(80, b' '))
        fh.write(struct.pack('<I', len(t)))
        for ni, ti in zip(n, t):
            fh.write(struct.pack('<12fH', *ni, *ti.reshape(-1), 0))


def _para_imprimir(tris, z_max):
    """La tapa boca abajo (giro de 180° alrededor de x): la placa superior queda sobre la cama."""
    return [[(x, -y, z_max - z) for x, y, z in t] for t in tris]


def generar(antena, h, c=None):
    """Mallas de las dos piezas (la tapa ya boca abajo) y sus datos: {'base': tris, 'tapa': tris, 'dims': {...}}."""
    motivo = no_soporta(antena)
    if motivo:
        raise ValueError(motivo)
    c = completar(c)
    piezas, d = _prismas(antena, h, c)
    base, tapa = malla(piezas['base']), malla(piezas['tapa'])
    return {'base': base, 'tapa': _para_imprimir(tapa, d['z_arriba']), 'dims': d, 'parametros': c}


def exportar_stl(antena, h, carpeta, nombre, c=None):
    """Escribe `<nombre>_carcasa_base.stl` y `<nombre>_carcasa_tapa.stl` y devuelve las rutas y las medidas exteriores."""
    import os
    r = generar(antena, h, c)
    os.makedirs(carpeta, exist_ok=True)
    rutas = {}
    for pieza in ('base', 'tapa'):
        rutas[pieza] = os.path.join(carpeta, f'{nombre}_carcasa_{pieza}.stl')
        escribir_stl(rutas[pieza], r[pieza], nombre)
    d = r['dims']
    rutas['exterior_mm'] = [round(d['xo1'] - d['xo0'], 1), round(d['yo1'] - d['yo0'], 1), round(d['z_arriba'] - d['z_fondo'], 1)]
    return rutas


def _restar(c, q):
    """Cajas que quedan de la caja c al quitarle la q."""
    x0, y0, z0, x1, y1, z1 = c
    a0, b0, c0, a1, b1, c1 = q
    if a1 <= x0 or a0 >= x1 or b1 <= y0 or b0 >= y1 or c1 <= z0 or c0 >= z1:
        return [c]
    out = []
    if a0 > x0:
        out.append((x0, y0, z0, a0, y1, z1)); x0 = a0
    if a1 < x1:
        out.append((a1, y0, z0, x1, y1, z1)); x1 = a1
    if b0 > y0:
        out.append((x0, y0, z0, x1, b0, z1)); y0 = b0
    if b1 < y1:
        out.append((x0, b1, z0, x1, y1, z1)); y1 = b1
    if c0 > z0:
        out.append((x0, y0, z0, x1, y1, c0)); z0 = c0
    if c1 < z1:
        out.append((x0, y0, c1, x1, y1, z1))
    return out


def bloques(antena, h, c=None, f_Hz=None):
    """Bloques dieléctricos para la simulación (formato de `entorno.py`): suelo, tapa y cuatro paredes con el hueco del conector."""
    c = completar(c)
    d = _dims(antena, h, c)
    er, tand = propiedades(c, f_Hz)
    xo0, yo0, xo1, yo1 = d['xo0'], d['yo0'], d['xo1'], d['yo1']
    xi0, yi0, xi1, yi1 = d['xi0'], d['yi0'], d['xi1'], d['yi1']
    za, zb = d['z_fondo_in'], d['z_arriba_in']
    cajas = [(xo0, yo0, d['z_fondo'], xo1, yo1, za), (xo0, yo0, zb, xo1, yo1, d['z_arriba'])]
    paredes = [(xo0, yo0, za, xi0, yo1, zb), (xi1, yo0, za, xo1, yo1, zb),
               (xi0, yo0, za, xi1, yi0, zb), (xi0, yi1, za, xi1, yo1, zb)]
    ab = _abertura(antena, h, c, d)
    for p in paredes:
        cajas += _restar(p, ab) if ab else [p]
    out = [{'nombre': 'carcasa', 'tipo': 'dielectrico', 'caja': tuple(round(float(v), 4) for v in cj), 'er': er, 'tand': tand}
           for cj in cajas]
    if c['fijacion'] != 'adhesivo':
        t = TORNILLOS[c['tornillo']]
        r_o = _orejeta(c)
        for ex, ey in _esquinas(d):
            # orejeta de plástico (caja cuadrada del lado de su diámetro)
            out.append({'nombre': 'carcasa', 'tipo': 'dielectrico', 'er': er, 'tand': tand,
                        'caja': (ex - r_o, ey - r_o, d['z_fondo'], ex + r_o, ey + r_o, d['z_arriba'])})
            # metal (PEC, de sección cuadrada del mismo lado que el diámetro): cabeza, caña y tuerca o inserto
            z_cab = d['z_arriba'] - 0.2
            z_base = z_cab - t['cabeza_h']
            if c['fijacion'] == 'rosca':
                z_fin = d['z_fondo'] + 1.5
            elif c['fijacion'] == 'inserto':
                z_fin = d['z_div'] - 0.9*t['inserto_h']
            else:
                z_fin = d['z_fondo'] + 0.2
            piezas = [('tornillo', t['cabeza'], z_base, z_cab), ('tornillo', t['paso'], z_fin, z_base)]
            if c['fijacion'] == 'inserto':
                piezas.append(('inserto', t['inserto'], d['z_div'] - t['inserto_h'], d['z_div']))
            elif c['fijacion'] == 'tuerca':
                piezas.append(('tuerca', t['tuerca_ac']*1.07, d['z_fondo'], d['z_fondo'] + t['tuerca_h']))
            for nombre, lado, z0, z1 in piezas:
                out.append({'nombre': nombre, 'tipo': 'metal', 'er': 1.0, 'tand': 0.0,
                            'caja': tuple(round(float(v), 4) for v in (ex - lado/2, ey - lado/2, z0, ex + lado/2, ey + lado/2, z1))})
    return out


def sin_metal(bloques_):
    """Los mismos bloques con el metal (tornillos, tuercas, insertos) convertido en aire: sirve de control con la misma malla."""
    from . import entorno as ent
    return [ent.neutro(b) if b['tipo'] == 'metal' else b for b in bloques_]
