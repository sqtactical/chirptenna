"""Simulación de cualquier antena del catálogo con openEMS y ajuste a la frecuencia.

Modelo: sustrato extruido con la forma de la placa, cobre de las dos caras como láminas PEC
(cara inferior en z=0, superior en z=h), pérdidas del dieléctrico con kappa = 2π f0 ε0 εr tanδ
y un puerto concentrado de 50 Ω vertical (masa → pista) en el borde donde va el SMA.

Malla: fina y uniforme sobre la placa, con paso ≤ mitad de la pista más estrecha y del hueco
más estrecho (si un hueco no queda resuelto, el cobre de los dos lados se une y la antena sale
en cortocircuito), y gradual en el aire hasta λ/20.

Criterio de resonancia (lección de la Fase 0): centro geométrico de la banda a −10 dB; si no
llega a −10 dB, el mínimo de S11.
"""
import os
import shutil
import sys
import json
import math
import time
import hashlib
import tempfile

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from . import gpu
from .geometria import poligonos, sin_agujeros
from .materiales import C0, eps_eff_microstrip
from .i18n import tr, N_

DIR_OPENEMS = os.environ.get('CSXCAD_INSTALL_PATH',
                             os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'openEMS', 'openEMS'))
os.environ['CSXCAD_INSTALL_PATH'] = DIR_OPENEMS
EPS0 = 8.854187817e-12
BORDE_COBRE = 0.5
FUSION_LINEAS = 0.25    # líneas de malla más cerca que esta fracción del paso se funden en una

PRECISIONES = {
    'rápida': {'lam_div': 15, 'factor_detalle': 1.0},
    'normal': {'lam_div': 20, 'factor_detalle': 0.8},
    'fina': {'lam_div': 30, 'factor_detalle': 0.5},
}


# ------------------------------------------------------------------ utilidades
def hueco_minimo(cobre, maximo=5.0):
    """Hueco más estrecho entre tramos de cobre (aprox.).

    Se busca el mayor s cuyo 'cierre' (engordar y encoger s/2) no rellena una franja
    apreciable: los huecos entre pistas paralelas rellenan ~s·longitud, mientras que las
    esquinas cóncavas (muescas en V de Koch) solo rellenan ~s² cada una. Por eso el umbral
    es una fracción de s × perímetro.
    """
    lo, hi = 0.0, maximo
    area, perim = cobre.area, cobre.length
    for _ in range(14):
        s = (lo + hi)/2
        relleno = cobre.buffer(s/2, join_style='round').buffer(-s/2, join_style='round').area - area
        if relleno > 0.15*s*perim:
            hi = s
        else:
            lo = s
    return hi


def ancho_minimo(cobre, maximo=5.0):
    """Parte de cobre más estrecha (aprox.): el mayor w cuya 'apertura' no elimina una franja apreciable."""
    lo, hi = 0.0, maximo
    area, perim = cobre.area, cobre.length
    for _ in range(14):
        w = (lo + hi)/2
        perdido = area - cobre.buffer(-w/2, join_style='round').buffer(w/2, join_style='round').area
        if perdido > 0.15*w*perim:
            hi = w
        else:
            lo = w
    return hi


def lineas_adaptadas(geoms, eje, fino, grueso, lo, hi):
    """Líneas de malla de un eje sobre la placa: paso 'fino' alrededor de cada borde de cobre
    (2 celdas a cada lado) y gradual (×1,3) hasta 'grueso' en las zonas sin bordes.

    Los bordes a menos de 4 celdas se agrupan, así que las pistas y huecos estrechos quedan
    enteros con paso fino; en las curvas densas (Hilbert, Koch) sale prácticamente uniforme.
    Las líneas finas caen en la misma rejilla que la malla uniforme (lo + k·fino): cerca del cobre
    la malla es idéntica a la validada y no aparecen celdas diminutas (bajarían el paso de tiempo;
    la primera versión, con rejillas sueltas por grupo, tardaba más y rompió el meandro).
    """
    from CSXCAD.SmoothMeshLines import SmoothMeshLines
    c = []
    for geom in geoms:
        for pol in poligonos(geom):
            for anillo in [pol.exterior] + list(pol.interiors):
                c.extend(np.asarray(anillo.coords)[:, eje])
    c = np.unique(np.round(c, 4))
    lineas = [lo, hi]
    if len(c):
        grupos = np.split(c, np.where(np.diff(c) > 4*fino)[0] + 1)
        for gr in grupos:
            k0 = math.floor((gr[0] - lo)/fino) - 2
            k1 = math.ceil((gr[-1] - lo)/fino) + 2
            lineas.extend(lo + np.arange(k0, k1 + 1)*fino)
    lineas = np.unique(np.round(np.clip(lineas, lo, hi), 6))
    # el último de la rejilla puede quedar pegado a hi: se quita para no dejar una celda diminuta
    if len(lineas) > 2 and lineas[-1] - lineas[-2] < 0.5*fino:
        lineas = np.delete(lineas, -2)
    return SmoothMeshLines(lineas, grueso, 1.3)


def centro_banda(f, s11_db, umbral=-10.0, ventana=None):
    """(f_centro, f_inf, f_sup, f_min, s11_min): banda contigua bajo el umbral alrededor del mínimo."""
    m = np.ones_like(f, bool) if ventana is None else (f >= ventana[0]) & (f <= ventana[1])
    idx = np.where(m)[0]
    i = idx[int(np.argmin(s11_db[m]))]
    f_min, s_min = f[i], float(s11_db[i])
    if s_min >= umbral:
        return f_min, None, None, f_min, s_min
    lo = i
    while lo > 0 and s11_db[lo - 1] < umbral:
        lo -= 1
    hi = i
    while hi < len(f) - 1 and s11_db[hi + 1] < umbral:
        hi += 1
    return math.sqrt(f[lo]*f[hi]), f[lo], f[hi], f_min, s_min


def _clave_cache(antena, sustrato, fmin, fmax, precision):
    h = hashlib.sha1()
    h.update(antena.cobre('F.Cu').wkb)
    h.update(antena.cobre('B.Cu').wkb)
    h.update(antena.contorno.wkb)
    # 'en_malla': las cachés de antes de llevar los hilos a la malla los tenían desconectados
    if antena.vias:
        h.update(json.dumps(['en_malla', [[round(x, 4), round(y, 4)] for x, y in antena.vias]]).encode())
    if antena.reflector:
        r = antena.reflector
        h.update(r['contorno'].wkb)
        h.update(json.dumps([round(r['separacion_mm'], 4), r.get('hilos', []), 'en_malla']).encode())
    if antena.ajuste and (antena.ajuste.get('condensadores') or antena.ajuste.get('puentes_sim')):
        # elementos concentrados (C o L con su Q) y relleno del serie: el cobre es el mismo con valores distintos
        h.update(json.dumps(['elementos', antena.ajuste.get('condensadores', []),
                             [p.wkb.hex() for p in antena.ajuste.get('puentes_sim', [])]], default=str).encode())
    if antena.entorno:
        h.update(json.dumps(['entorno', antena.entorno], default=str).encode())
    if sustrato.capas > 2:
        h.update(json.dumps(['capas', sustrato.capas, sustrato.h_ref]).encode())     # la caché de 2 capas no cambia
    h.update(json.dumps([sustrato.er, sustrato.tand, sustrato.h, fmin, fmax, precision,
                         antena.puerto['borde'], antena.puerto['direccion']]).encode())
    return h.hexdigest()[:16]


def _terminada(sim_path):
    """Si la simulación de la caché acabó bien: la tensión del puerto tiene que haberse apagado al final.
    Una cortada a medias (proceso parado) o que agotó los pasos sin converger sigue oscilando, y antes
    contaba como hecha solo por existir port_ut_1 (la J-pole de Koch falló así: un fichero de una muestra)."""
    try:
        u = np.loadtxt(os.path.join(sim_path, 'port_ut_1'), comments='%')
    except (OSError, ValueError):
        return False
    if u.ndim != 2 or len(u) < 20:
        return False
    v = np.abs(u[:, 1])
    return v[-max(5, len(v)//20):].max() < 0.1*v.max()


# ------------------------------------------------------------------ simulación
def simular(antena, sustrato, f_centro, precision='normal', nf2ff=True, progreso=print, rango=(0.6, 1.4),
            paso=None, malla='uniforme', f_radiacion=None):
    """Simula la antena y devuelve un diccionario con S11, banda, impedancia y radiación.

    f_radiacion: frecuencia del diagrama de radiación (por defecto, la de resonancia).

    paso: paso de malla en la placa fijado desde fuera (el ajuste lo mantiene constante entre
    iteraciones: si cambia, la frecuencia simulada salta varios % y la secante oscila).
    malla: 'uniforme' (paso fino en toda la placa) o 'adaptada' (fino solo junto a los bordes del
    cobre y de la placa, ver lineas_adaptadas). La adaptada está pendiente de validar.
    """
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS

    cfg = PRECISIONES[precision]
    fmin, fmax = rango[0]*f_centro, rango[1]*f_centro
    f0, fc = (fmin + fmax)/2, (fmax - fmin)/2
    h, er = sustrato.h, sustrato.er
    zm = sustrato.z_masa           # cota de la masa: 0 con 2 capas, la de In1.Cu con 4 (el FR4 llega hasta z = 0 igualmente)
    clave = _clave_cache(antena, sustrato, fmin, fmax, f'{precision}{paso}' + ('' if malla == 'uniforme' else malla + '2'))
    sim_path = os.path.join(tempfile.gettempdir(), 'antenas_sim', clave)
    os.makedirs(sim_path, exist_ok=True)

    sup, inf = antena.cobre('F.Cu'), antena.cobre('B.Cu')
    if antena.ajuste and antena.ajuste.get('puentes_sim'):
        # el componente en serie de la red en π se da por montado (0 Ω): se rellena su hueco
        sup = unary_union([sup] + antena.ajuste['puentes_sim'])
    # condensadores concentrados (bucle): su hueco no cuenta para la malla, un elemento de openEMS lo llena en una celda
    caps = list(antena.ajuste.get('condensadores', [])) if antena.ajuste else []
    sup_malla = unary_union([sup] + [box(*c['caja']) for c in caps]) if caps else sup
    # Paso de malla en la placa: λ en el sustrato y detalles más finos del cobre
    lam_min = C0/fmax*1e3
    res_lam = lam_min/math.sqrt(er)/cfg['lam_div']
    w_min = min(ancho_minimo(sup_malla, 3.0), antena.info.get('pista_minima_mm') or 99)
    s_min = min(hueco_minimo(sup_malla, 3.0), antena.info.get('hueco_minimo_mm') or 99)
    res = min(res_lam, cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2)
    res = max(res, 0.08)
    if paso is not None:
        res = paso
    res_aire = lam_min/cfg['lam_div']
    avisos = []
    if s_min/res < 2:
        avisos.append(tr('El hueco más estrecho ({0:.2f} mm) queda con menos de 2 celdas: el resultado puede salir en cortocircuito; usa la precisión «fina».', s_min))

    FDTD = openEMS(NrTS=400000, EndCriteria=1e-4)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    kappa = 2*math.pi*f0*EPS0*er*sustrato.tand
    fr4 = CSX.AddMaterial('sustrato', epsilon=er, kappa=kappa)
    cx, cy = antena.contorno.exterior.xy
    fr4.AddLinPoly(points=[np.array(cx[:-1]), np.array(cy[:-1])], norm_dir='z', elevation=0, length=h, priority=0)
    if antena.contorno.interiors:
        # recortes para aligerar: aire dentro de cada hueco del contorno (por encima del FR4, por debajo del cobre)
        aire = CSX.AddMaterial('recortes', epsilon=1.0)
        for hueco in antena.contorno.interiors:
            hx, hy = hueco.xy
            aire.AddLinPoly(points=[np.array(hx[:-1]), np.array(hy[:-1])], norm_dir='z', elevation=0, length=h,
                            priority=1)
    cobre = CSX.AddMetal('cobre')
    for geom, z in ((inf, zm), (sup, h)):
        for pol in poligonos(geom):
            for t in sin_agujeros(pol):
                xs, ys = np.array(t.exterior.coords[:-1]).T
                cobre.AddPolygon([xs, ys], norm_dir='z', elevation=z, priority=10)
    for k, c in enumerate(caps):
        # condensador o bobina en serie: con su resistencia serie por la Q (a la frecuencia central de la simulación)
        ny = 0 if c.get('dir', 'x') == 'x' else 1
        if 'L_nH' in c:
            l_h = c['L_nH']*1e-9
            r_esr = 2*math.pi*f0*l_h/c.get('Q', 40.0)
            el = CSX.AddLumpedElement(f'bobina{k + 1}', ny=ny, caps=c.get('caps', True), R=r_esr, L=l_h, LEtype=1)
        else:
            c_f = c['C_pF']*1e-12
            r_esr = 1/(2*math.pi*f0*c_f*c.get('Q', 250.0))
            el = CSX.AddLumpedElement(f'condensador{k + 1}', ny=ny, caps=c.get('caps', True), R=r_esr, C=c_f, LEtype=1)
        x0c, y0c, x1c, y1c = c['caja']
        el.AddBox([x0c, y0c, h], [x1c, y1c, h], priority=20)
    # Reflector (panel): lámina PEC bajo la cara inferior, separada por aire
    refl = antena.reflector
    z_ref = -refl['separacion_mm'] if refl else 0.0
    if refl:
        xs, ys = np.array(refl['contorno'].exterior.coords[:-1]).T
        cobre.AddPolygon([xs, ys], norm_dir='z', elevation=z_ref, priority=10)

    # Entorno (carcasa, batería, mano): bloques por debajo del cobre en prioridad; los metálicos son PEC
    for k, b in enumerate(antena.entorno or []):
        bx0, by0, bz0, bx1, by1, bz1 = b['caja']
        if b['tipo'] == 'metal':
            cobre.AddBox([bx0, by0, bz0], [bx1, by1, bz1], priority=10)
        else:
            kap = b['sigma'] if b.get('sigma') is not None else 2*math.pi*f0*EPS0*b['er']*b.get('tand', 0.0)
            mat = CSX.AddMaterial(f'entorno{k + 1}', epsilon=b['er'], kappa=kap)
            mat.AddBox([bx0, by0, bz0], [bx1, by1, bz1], priority=5)

    # Puerto: vertical en el arranque de la línea de 50 Ω (borde del SMA)
    w = antena.puerto['ancho_linea']
    if antena.puerto.get('tipo') == 'pasante':
        # Coaxial que atraviesa la placa (panel): puerto vertical de la cara inferior a la superior
        px, py = antena.puerto['alimentacion']
        wp = antena.puerto.get('ancho_puerto', w)
        ini, fin = [px - wp/2, py, 0], [px + wp/2, py, h]
        port = FDTD.AddLumpedPort(1, 50, ini, fin, 'z', 1.0, priority=20)
    elif antena.puerto.get('tipo') == 'coaxial':
        # Coaxial soldado entre dos tiras de la cara superior (J-pole): puerto horizontal en el hueco
        (xa, ya), (xb, yb) = antena.puerto['puntos']
        ini, fin = [xa, ya - w/2, h], [xb, yb + w/2, h]
        port = FDTD.AddLumpedPort(1, 50, ini, fin, 'x', 1.0, priority=20)
    else:
        bx, by = antena.puerto['borde']
        dx, dy = antena.puerto['direccion']
        u = antena.puerto.get('inicio_mm', BORDE_COBRE)       # IPEX: en su pad central
        px, py = bx + dx*u, by + dy*u
        wp = antena.puerto.get('ancho_puerto', w)
        if dy:
            ini, fin = [px - wp/2, py, zm], [px + wp/2, py, h]
        else:
            ini, fin = [px, py - wp/2, zm], [px, py + wp/2, h]
        port = FDTD.AddLumpedPort(1, 50, ini, fin, 'z', 1.0, priority=20)

    # Malla
    x0, y0, x1, y1 = antena.contorno.bounds
    margen = max(C0/fmin*1e3/4, 20.0)
    if malla == 'adaptada':
        bordes = [sup, inf, antena.contorno]
        rejilla = {'x': lineas_adaptadas(bordes, 0, res, max(res, res_lam), x0, x1),
                   'y': lineas_adaptadas(bordes, 1, res, max(res, res_lam), y0, y1)}
    else:
        rejilla = {'x': np.arange(x0, x1 + res/2, res), 'y': np.arange(y0, y1 + res/2, res)}
    mesh.AddLine('x', rejilla['x'])
    mesh.AddLine('y', rejilla['y'])
    # el dominio abarca también el reflector (más grande que la placa); sus bordes, con líneas propias
    ex0, ey0, ex1, ey1 = refl['contorno'].bounds if refl else (x0, y0, x1, y1)
    ex0, ey0, ex1, ey1 = min(ex0, x0), min(ey0, y0), max(ex1, x1), max(ey1, y1)
    # el dominio abarca también el entorno, con líneas de malla en las caras de cada bloque
    ent = [b['caja'] for b in (antena.entorno or [])]
    xs_ent = [v for c in ent for v in (c[0], c[3])]
    ys_ent = [v for c in ent for v in (c[1], c[4])]
    zs_ent = [v for c in ent for v in (c[2], c[5])]
    if ent:
        ex0, ey0 = min([ex0] + xs_ent), min([ey0] + ys_ent)
        ex1, ey1 = max([ex1] + xs_ent), max([ey1] + ys_ent)
    xs_caps = [v for c in caps for v in (c['caja'][0], c['caja'][2])]
    ys_caps = [v for c in caps for v in (c['caja'][1], c['caja'][3])]
    mesh.AddLine('x', [ex0 - margen, ex1 + margen, ini[0], fin[0], ex0, ex1] + xs_caps + xs_ent)
    mesh.AddLine('y', [ey0 - margen, ey1 + margen, ini[1], fin[1], ey0, ey1] + ys_caps + ys_ent)
    # sustratos muy finos (flex de 25–50 µm): 2 celdas en z; con 4, el paso de tiempo se hundiría (la celda más pequeña lo fija)
    if zm > 0:
        # 4 capas: el prepreg entre F.Cu y la masa de In1.Cu (~0,2 mm) lleva 2 celdas (con más, la celda fina hundiría el paso de tiempo)
        mesh.AddLine('z', np.r_[np.linspace(0, zm, 4), np.linspace(zm, h, 3)])
    else:
        mesh.AddLine('z', np.linspace(0, h, 5 if h >= 0.4 else 3))
    mesh.AddLine('z', [min([z_ref] + zs_ent) - margen, max([h] + zs_ent) + margen, z_ref] + zs_ent)
    mesh.SmoothMeshLines('all', res_aire, 1.3)
    # Las líneas del puerto y de los bordes no caen en la rejilla: si quedan a micras de otra, la celda
    # diminuta hunde el paso de tiempo (1e-19 s: la simulación no acaba y el resultado es basura).
    # De dos líneas pegadas se queda la de la rejilla de la placa o la de una cara (el puerto se ajusta
    # solo a la malla). Las cachés de esas mallas tienen resultados sin terminar: van a otra carpeta.
    fijas = {'x': set(np.round(np.r_[rejilla['x'], ex0, ex1, xs_caps, xs_ent], 6)), 'y': set(np.round(np.r_[rejilla['y'], ey0, ey1, ys_caps, ys_ent], 6)),
             'z': set(np.round([0.0, zm, h, z_ref] + zs_ent, 6))}
    # Las del puerto van por encima de todo: un puerto (caja plana) que no cae en una línea de malla
    # desaparece sin avisar y la simulación corre sin excitación (le pasó al Hilbert de 2,4 GHz).
    puerto = {d: set(np.round([ini[i], fin[i]], 6)) for i, d in enumerate('xyz')}

    def rango(d, v):
        v = round(v, 6)
        return 2 if v in puerto[d] else 1 if v in fijas[d] else 0

    fundidas = False
    for d in 'xyz':
        ls = np.sort(np.asarray(mesh.GetLines(d)))
        tol = (sustrato.h_linea/4 if d == 'z' else res)*FUSION_LINEAS
        quedan = [ls[0]]
        for v in ls[1:]:
            if v - quedan[-1] >= tol:
                quedan.append(v)
            elif rango(d, v) > rango(d, quedan[-1]):
                quedan[-1] = v
        if len(quedan) < len(ls):
            mesh.SetLines(d, quedan)
            fundidas = True
    if fundidas:
        sim_path += '_f'
        os.makedirs(sim_path, exist_ok=True)
    for i, d in enumerate('xyz'):
        lineas = np.asarray(mesh.GetLines(d))
        for v in (ini[i], fin[i]):
            if np.min(np.abs(lineas - v)) > 1e-6:
                raise RuntimeError(tr('El puerto no cae en la malla ({0} = {1:.4f} mm): openEMS lo descartaría y la simulación correría sin excitación', d, v))
    # Hilos PEC verticales: vías de cara a cara y malla del coaxial del panel (del reflector a la cara
    # inferior). Una caja degenerada solo existe si cae exactamente en una línea de malla (si no,
    # openEMS la descarta sin avisar): se lleva a la línea más cercana, dentro del pad de la vía.
    lx, ly = np.asarray(mesh.GetLines('x')), np.asarray(mesh.GetLines('y'))

    def en_malla(vx, vy):
        return float(lx[np.argmin(abs(lx - vx))]), float(ly[np.argmin(abs(ly - vy))])

    for vx, vy in antena.vias:
        mx, my = en_malla(vx, vy)
        cobre.AddBox([mx, my, zm], [mx, my, h], priority=10)
    for vx, vy in (refl.get('hilos', []) if refl else []):
        mx, my = en_malla(vx, vy)
        cobre.AddBox([mx, my, z_ref], [mx, my, 0.0], priority=10)
    celdas = [len(mesh.GetLines(d)) for d in 'xyz']
    n_celdas = int(np.prod(celdas))
    progreso(tr('Malla {0}×{1}×{2} = {3:.2f} M celdas (paso en la placa {4:.2f} mm; pista mín. {5:.2f} mm, hueco mín. {6:.2f} mm)', celdas[0], celdas[1], celdas[2], n_celdas/1e6, res, w_min, s_min))
    if n_celdas > 15e6:
        avisos.append(tr('Malla muy grande ({0:.0f} M celdas): la simulación tardará mucho.', n_celdas/1e6))

    caja = FDTD.CreateNF2FFBox() if nf2ff else None
    hecho = _terminada(sim_path) and os.path.exists(os.path.join(sim_path, 'port_it_1'))
    if nf2ff:
        hecho = hecho and os.path.exists(os.path.join(sim_path, 'nf2ff_E_0.h5'))
    t0 = time.time()
    if hecho:
        progreso(tr('Resultado en caché: no se vuelve a simular'))
    else:
        usar_gpu = gpu.activa()
        progreso(tr('Simulando con openEMS (GPU)…') if usar_gpu else tr('Simulando con openEMS…'))
        if not (usar_gpu and gpu.ejecutar(FDTD, sim_path, progreso)):
            # hilos: 0 = todos. ANTENAS_HILOS permite repartir la CPU entre dos simulaciones a la vez
            FDTD.Run(sim_path, cleanup=True, verbose=0, numThreads=int(os.environ.get('ANTENAS_HILOS', '0')))
    t_sim = time.time() - t0

    f = np.linspace(fmin, fmax, 1201)
    port.CalcPort(sim_path, f)
    s11 = port.uf_ref/port.uf_inc
    zin = port.uf_tot/port.if_tot
    s11_db = 20*np.log10(np.abs(s11))
    fcen, flo, fhi, fmn, smn = centro_banda(f, s11_db)
    criterio = tr('centro de la banda a −10 dB')
    en_borde = False
    if flo is not None and abs(fcen - f_centro)/f_centro > 0.25:
        # la banda a −10 dB es de otra resonancia lejos del objetivo: se busca la más cercana
        flo_banda, fhi_banda = flo, fhi
        flo = None
    else:
        flo_banda = fhi_banda = None
    if flo is None:
        # Sin banda a −10 dB: resonancia de la antena = paso por cero (− → +) de la reactancia en sus
        # terminales, quitando la línea de 50 Ω si se conoce su largo. Si no, mínimo de S11 lejos de
        # los bordes del rango (en el borde no significa nada: la resonancia está fuera).
        z_ant = zin
        l_lin = antena.puerto.get('largo_linea_mm')
        if l_lin:
            ee = eps_eff_microstrip(er, sustrato.h_linea, w)
            t = np.tan(2*np.pi*f*math.sqrt(ee)/C0*l_lin*1e-3)
            z_ant = 50*(zin - 1j*50*t)/(50 - 1j*zin*t)
        x = np.imag(z_ant)
        cruces = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
        if flo_banda is not None and (not len(cruces) or
                                      np.min(np.abs(f[cruces] - f_centro)) > abs(fcen - f_centro)):
            # no hay nada más cercano: se queda la banda lejana
            flo, fhi = flo_banda, fhi_banda
        elif len(cruces):
            i = cruces[np.argmin(np.abs(f[cruces] - f_centro))]
            fcen = f[i] + (f[i + 1] - f[i])*(-x[i])/(x[i + 1] - x[i])
            criterio = tr('reactancia nula en los terminales (no llega a −10 dB cerca del objetivo)')
        else:
            borde = int(0.03*len(f))
            j = borde + int(np.argmin(s11_db[borde:-borde]))
            fcen = f[j]
            en_borde = j <= borde + 1 or j >= len(f) - borde - 2
            criterio = tr('mínimo de S11 (no llega a −10 dB)')
        if flo is None:
            avisos.append(tr('No llega a −10 dB cerca del objetivo (mínimo {0:.1f} dB): adaptación pobre; resonancia por {1}.', smn, criterio))
    # Cortocircuito: |S11|≈1 en todo el rango y Z≈0 a baja frecuencia
    if s11_db.max() - s11_db.min() < 1.0 and abs(zin[0]) < 5:
        avisos.append(tr('S11 plano y Z≈0: el modelo parece en cortocircuito (hueco no resuelto por la malla).'))
    res_out = {'f_Hz': f, 's11': s11, 'zin': zin, 'f_resonancia_Hz': fcen, 'banda_Hz': (flo, fhi),
               'f_min_s11_Hz': fmn, 's11_min_dB': smn, 'celdas': n_celdas, 'paso_malla_mm': res,
               'criterio': criterio, 'en_borde': en_borde, 'rango_Hz': (fmin, fmax),
               'tiempo_s': round(t_sim, 1), 'avisos': avisos, 'precision': precision}
    if nf2ff:
        progreso(tr('Calculando el diagrama de radiación…'))
        theta = np.arange(0, 181, 3.0)
        phi = np.arange(0, 361, 6.0)
        centro = [((x0 + x1)/2)*1e-3, ((y0 + y1)/2)*1e-3, h/2*1e-3]   # en metros
        f_rad = f_radiacion or fcen
        res_out['f_radiacion_Hz'] = f_rad
        # sin read_cached: nf2ff.h5 guarda una sola frecuencia y con otra f_radiacion da error
        r = caja.CalcNF2FF(sim_path, f_rad, theta, phi, center=centro, read_cached=False)
        port.CalcPort(sim_path, [f_rad])
        p_acc, p_inc = float(port.P_acc[0]), float(port.P_inc[0])
        prad = float(r.Prad[0])
        d = r.E_norm[0]**2
        d_dbi = 10*np.log10(d/d.max()*r.Dmax[0])
        res_out.update({'theta': theta, 'phi': phi, 'directividad_dBi_grid': d_dbi,
                        'directividad_dBi': float(10*np.log10(r.Dmax[0])),
                        'eficiencia_radiacion': prad/p_acc if p_acc > 0 else float('nan'),
                        'eficiencia_total': prad/p_inc if p_inc > 0 else float('nan')})
        res_out['ganancia_dBi'] = res_out['directividad_dBi'] + 10*math.log10(max(res_out['eficiencia_radiacion'], 1e-6))
        if res_out['eficiencia_radiacion'] < 0.10:
            avisos.append(tr('Eficiencia de radiación del {0:.0f} %: casi no radia en {1:.0f} MHz. Probable resonancia falsa (pieza desconectada en el modelo o resonancia de la línea), revisa la geometría.', 100*res_out["eficiencia_radiacion"], f_rad/1e6))
        it, ip = np.unravel_index(np.argmax(d_dbi), d_dbi.shape)
        res_out['direccion_max'] = {'theta': float(theta[it]), 'phi': float(phi[ip])}
        try:
            # Polarización: razón axial y sentido de giro (E con dependencia e^{jωt}; RHCP = Eθ + jEφ dominante)
            e_th, e_ph = r.E_theta[0], r.E_phi[0]
            er, el = np.abs(e_th + 1j*e_ph)/math.sqrt(2), np.abs(e_th - 1j*e_ph)/math.sqrt(2)
            ar = 20*np.log10((er + el)/np.maximum(np.abs(er - el), 1e-12))
            res_out['ar_dB_max'] = float(ar[it, ip])
            res_out['ar_dB_theta0'] = float(ar[0, 0])
            res_out['pol_max'] = 'RHCP' if er[it, ip] > el[it, ip] else 'LHCP'
            res_out['pol_theta0'] = 'RHCP' if er[0, 0] > el[0, 0] else 'LHCP'
        except Exception:
            pass
    if os.environ.get('ANTENAS_BORRAR_SIM') == '1':
        # campañas largas: los volcados de campos ocupan GB por simulación y la caché no se reutiliza
        shutil.rmtree(sim_path, ignore_errors=True)
    if antena.parametros.get('red_L'):
        res_out = aplicar_red_bucle(antena, res_out, f_centro, sustrato)      # bucle con su red en L (por circuito)
    return res_out


# ------------------------------------------------------------------ ajuste
def _ajustar_toma(clave, q, nombre_sustrato, s, f_obj, precision, paso, progreso, historial, max_sim=7,
                  malla='uniforme'):
    """J-pole: busca Z = 50 Ω en f_obj moviendo a la vez la toma (sobre todo cambia R) y el largo
    del adaptador, factor_adaptador (sobre todo cambia X: si el adaptador no resuena en f_obj, subir
    la toma solo añade reactancia).

    Newton en dos variables con jacobiano inicial por diferencias y actualización de Broyden;
    pasos acotados. Devuelve la mejor configuración simulada (nunca una sin simular).
    """
    from . import tipos
    lim_inf, lim_sup = np.array([0.7, 0.03]), np.array([1.3, 0.9])

    def evaluar(x):
        qq = dict(q, factor_adaptador=round(float(x[0]), 3), toma=round(float(x[1]), 3))
        r = simular(tipos.generar(clave, qq, nombre_sustrato), s, f_obj, precision, nf2ff=False, progreso=progreso,
                    paso=paso, malla=malla)
        s11, z = _s11_en(r, f_obj)
        progreso(tr('Adaptador ×{0:.3f}, toma {1:.3f}: Z = {2:.1f} {3:+.1f}j Ω en el objetivo, S11 {4:.1f} dB', qq["factor_adaptador"], qq["toma"], z.real, z.imag, s11))
        historial.append({'escala_mm': qq['largo_radiador'], 'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2),
                          'error_%': round(100*(r['f_resonancia_Hz'] - f_obj)/f_obj, 2), 'tiempo_s': r['tiempo_s'],
                          'valido': True, 'factor_adaptador': qq['factor_adaptador'], 'toma': qq['toma'],
                          'S11_obj_dB': round(s11, 1)})
        return qq, np.array([(z.real - 50)/50, z.imag/50]), s11

    x = np.array([q.get('factor_adaptador', 1.0), q['toma']], float)
    q0, F, s11 = evaluar(x)
    mejor = (s11, q0)
    n = 1
    if s11 > -15:
        # jacobiano inicial por diferencias finitas
        J = np.zeros((2, 2))
        for k, dx in enumerate((0.04, 0.06 if x[1] < 0.5 else -0.06)):
            x1 = x.copy(); x1[k] += dx
            q1, F1, s1 = evaluar(x1); n += 1
            mejor = min(mejor, (s1, q1), key=lambda m: m[0])
            J[:, k] = (F1 - F)/dx
        while n < max_sim and mejor[0] > -15:
            try:
                paso_x = -np.linalg.solve(J, F)
            except np.linalg.LinAlgError:
                break
            paso_x = np.clip(paso_x, [-0.1, -0.15], [0.1, 0.15])
            x_n = np.clip(x + paso_x, lim_inf, lim_sup)
            dx = x_n - x
            if np.max(np.abs(dx)) < 1e-3:
                break
            qn, Fn, sn = evaluar(x_n); n += 1
            mejor = min(mejor, (sn, qn), key=lambda m: m[0])
            J += np.outer((Fn - F) - J @ dx, dx)/(dx @ dx)          # Broyden
            x, F = x_n, Fn
    q = mejor[1]
    return q, tipos.generar(clave, q, nombre_sustrato)

def _s11_en(r, f_obj):
    k = int(np.argmin(np.abs(r['f_Hz'] - f_obj)))
    return float(20*np.log10(np.abs(r['s11'][k]))), r['zin'][k]


# Parámetro que adapta cada tipo sin mover mucho la frecuencia (se busca el mínimo de S11 en f_obj)
PARAM_ADAPTACION = {'yagi_koch': 'alto_cps', 'yagi_boom': 'separacion_reflector',
                    'panel_dipolos': 'separacion_reflector'}


def _param_adaptacion(clave, q):
    """(parámetro, primer paso multiplicativo). Yagi con boom y transformador: su impedancia."""
    if clave == 'yagi_boom' and int(q.get('alimentacion', 0)) == 1:
        return 'z_transformador', 1.25
    if clave == 'panel_dipolos':
        return 'separacion_reflector', 1.25        # 0,25 → 0,31 λ0: la R del dipolo cambia mucho
    if _con_muesca(clave, q):
        return 'muesca', 1.15                      # R ∝ cos²(π·d/L): cambia deprisa con la profundidad
    return PARAM_ADAPTACION[clave], 1.5


def _con_muesca(clave, q):
    return clave in ('parche_rectangular', 'parche_minkowski', 'parche_circular', 'parche_ranura', 'parche_apilado') and int(q.get('alimentacion', 0)) == 1


def _ajustar_adaptacion(clave, q, nombre_sustrato, s, f_obj, precision, paso, progreso, historial, s11_ini,
                        max_sim=3, malla='uniforme'):
    """Busca el valor del parámetro de adaptación (_param_adaptacion) que da menos S11 en f_obj (pasos
    multiplicativos; si empeora se invierte y se acorta el paso). Quasi-Yagi: el largo de la CPS
    (distancia del dipolo al reflector) cambia la resistencia del dipolo y la transforma como una línea."""
    from . import tipos
    nombre, factor = _param_adaptacion(clave, q)
    par = next(pp for pp in tipos.CATALOGO[clave].parametros if pp.nombre == nombre)
    if nombre == 'muesca' and not q.get('muesca'):
        # 0 = estimada: se parte del valor que usó el generador
        q = dict(q, muesca=tipos.generar(clave, q, nombre_sustrato).info['muesca_mm'])
    if nombre == 'muesca':
        # Más honda → menos R. Con la Z simulada se elige el sentido del primer paso
        r0 = simular(tipos.generar(clave, q, nombre_sustrato), s, f_obj, precision, nf2ff=False, progreso=progreso,
                     paso=paso, malla=malla)
        factor = factor if _s11_en(r0, f_obj)[1].real > 50 else 1/factor
    mejor_q, mejor_s = q, s11_ini
    unidad = 'Ω' if nombre.startswith('z_') else 'mm'
    if nombre == 'z_transformador':
        # R vista = Zt²/R_antena: el Zt que da 50 Ω es Zt·√(50/R) (la simulación de q está en caché)
        r0 = simular(tipos.generar(clave, q, nombre_sustrato), s, f_obj, precision, nf2ff=False, progreso=progreso,
                     paso=paso, malla=malla)
        z0 = _s11_en(r0, f_obj)[1]
        factor = min(max(math.sqrt(50/max(z0.real, 1.0)), 0.7), 1.4)
    for n in range(max_sim):
        if mejor_s < -15:
            break
        x = min(max(round(mejor_q[nombre]*factor, 2), par.minimo), par.maximo)
        if x == mejor_q[nombre]:
            break
        qq = dict(mejor_q, **{nombre: x})
        progreso(tr('Adaptación {0}: {1} = {2:.2f} {3}', n + 1, nombre, x, unidad))
        r = simular(tipos.generar(clave, qq, nombre_sustrato), s, f_obj, precision, nf2ff=False, progreso=progreso,
                    paso=paso, malla=malla)
        s11, z = _s11_en(r, f_obj)
        progreso(tr('  → Z = {0:.1f} {1:+.1f}j Ω en el objetivo, S11 {2:.1f} dB (resonancia {3:.1f} MHz)', z.real, z.imag, s11, r["f_resonancia_Hz"]/1e6))
        historial.append({'escala_mm': qq[tipos.CATALOGO[clave].escala], nombre: x,
                          'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2),
                          'error_%': round(100*(r['f_resonancia_Hz'] - f_obj)/f_obj, 2), 'tiempo_s': r['tiempo_s'],
                          'valido': True, 'S11_obj_dB': round(s11, 1)})
        if s11 < mejor_s:
            mejor_q, mejor_s = qq, s11
        else:
            factor = 1/math.sqrt(factor)          # se invierte el sentido con un paso menor
    return mejor_q, tipos.generar(clave, mejor_q, nombre_sustrato)


# Umbrales de verificar_malla, sacados de simulaciones reales (11-11-2026) con el paso ×0,85 y ×1,15:
# monopolo recto a 2,4 GHz (normal): Δf −1,8 y −4,0 %, ΔS11 0,2 y 3,3 dB; J-pole bibanda a 868 MHz + 2,4 GHz
# (sensible, lección 70): ΔS11 de 1,2 a 15 dB en la banda alta. Un cambio del paso de ±15 % mueve una antena
# normal hasta ~4 % (la resonancia no es monótona con el paso: depende de cómo caen las líneas sobre los bordes).
# El S11 solo cuenta si el cambio importa: de −25 a −15 dB no cambia nada, de −9 a −4 dB sí. Se marca cuando varía
# más de UMBRAL_MALLA_S11_DB y alguno de los dos queda por encima de −10 dB (el monopolo de Koch dio +5,3 dB entre
# −17 y −12 dB: sin esa condición saltaba un aviso sin sentido).
def _datos_red_bucle(antena, r, sustrato):
    """(f, z_anillo, ee, d_z1, d_comp, y_puerto, comp) para la red en L del bucle: la impedancia del anillo sin la línea de
    50 Ω hasta él (la Z simulada en el conector, de-embebida) y las distancias de línea entre anillo, Z1 y las derivaciones."""
    w = antena.puerto['ancho_linea']
    ee = eps_eff_microstrip(sustrato.er, sustrato.h_linea, w)
    comp = {c['ref']: c for c in antena.ajuste['componentes']}
    if 'Z1' not in comp or 'Z3' not in comp:
        return None
    f = r['f_Hz']
    l_lin = antena.puerto['largo_linea_mm']
    t = np.tan(2*np.pi*f*math.sqrt(ee)/C0*l_lin*1e-3)
    z_anillo = 50*(r['zin'] - 1j*50*t)/(50 - 1j*r['zin']*t)               # quitando la línea de 50 Ω hasta el anillo
    y_puerto = antena.puerto['borde'][1] + antena.puerto.get('inicio_mm', BORDE_COBRE)
    d_z1 = y_puerto + l_lin - comp['Z1']['y']
    d_comp = abs(comp['Z3']['y'] - comp['Z1']['y'])
    return f, z_anillo, ee, d_z1, d_comp, y_puerto, comp


def red_adaptacion_bucle(antena, r, f_obj, sustrato):
    """Red en L (valores E24, con las pérdidas de los componentes y la línea entre ellos) que adapta el bucle en `f_obj`
    a partir de la impedancia simulada SIN red. `r`: resultado de `simular` de la antena sin `red_L`.
    Devuelve el dict de `ajuste.mejor_red_l` más 'z_anillo_ohm' y 'banda_circuito_MHz' (a −10 dB por circuito), o None."""
    from . import ajuste as aj_mod
    d = _datos_red_bucle(antena, r, sustrato)
    if d is None:
        return None
    f, z_anillo, ee, d_z1, d_comp, _, _ = d
    sol = aj_mod.mejor_red_l(z_anillo, f, f_obj, d_z1, d_comp, ee)
    if sol is None:
        return None
    k = int(np.argmin(np.abs(f - f_obj)))
    sol['z_anillo_ohm'] = [round(float(z_anillo[k].real), 2), round(float(z_anillo[k].imag), 2)]
    cb = centro_banda(f, sol['s11_f_dB'], -10.0, (0.8*f_obj, 1.25*f_obj))
    if cb[1] is not None:
        sol['banda_circuito_MHz'] = [round(cb[1]/1e6, 1), round(cb[2]/1e6, 1)]
    return sol


def aplicar_red_bucle(antena, r, f_obj, sustrato):
    """Aplica por circuito la red en L de `antena.parametros['red_L']` al resultado `r` de la simulación del anillo SIN red
    (la FDTD con la red como elementos concentrados no es fiable con C ≥ ~2 pF: ver `ajuste.montar_red`). Cambia S11, Z, banda y
    eficiencia total (con las pérdidas de los componentes); el diagrama y la ganancia son los del anillo. Devuelve un
    resultado nuevo (`r` no se toca) con 'red': {…, 's11_sin_red_dB'}; si no hay red o no se puede, devuelve `r`."""
    from . import ajuste as aj_mod
    red = antena.parametros.get('red_L')
    d = _datos_red_bucle(antena, r, sustrato) if red else None
    if d is None:
        return r
    f, z_anillo, ee, d_z1, d_comp, y_puerto, comp = d
    top, cs, cp = red['posicion'], tuple(red['serie']), tuple(red['derivacion'])
    z_red = aj_mod.zin_red_l(f, z_anillo, top, cs, cp, d_z1, d_comp, ee)
    y_plano = comp['Z2' if top == 'Z2' else 'Z1']['y'] if 'Z2' in comp else comp['Z1']['y']
    z_puerto = aj_mod._trasladar(z_red, 2*np.pi*f*math.sqrt(ee)/C0*(y_plano - y_puerto)*1e-3)   # hasta el conector
    s11 = (z_puerto - 50)/(z_puerto + 50)
    s11_db = 20*np.log10(np.abs(s11) + 1e-12)
    out = dict(r)
    out.update({'s11': s11, 'zin': z_puerto})
    fcen, flo, fhi, fmn, smn = centro_banda(f, s11_db, -10.0, (0.6*f_obj, 1.4*f_obj))
    out.update({'f_min_s11_Hz': fmn, 's11_min_dB': smn})
    if flo is not None:
        out.update({'f_resonancia_Hz': fcen, 'banda_Hz': (flo, fhi), 'criterio': tr('centro de la banda a −10 dB')})
    else:
        out['banda_Hz'] = (None, None)
    out['avisos'] = [a for a in r.get('avisos', []) if 'No llega a −10 dB' not in a]
    if flo is None:
        out['avisos'].append(tr('Con la red en L no llega a −10 dB (mínimo {0:.1f} dB): los valores E24 no bastan, retoca la red.', smn))
    k = int(np.argmin(np.abs(f - f_obj)))
    f_rad = r.get('f_radiacion_Hz', f_obj)
    kr = int(np.argmin(np.abs(f - f_rad)))
    eta_red = aj_mod.eficiencia_red_l(f[k], z_anillo[k], top, cs, cp, d_z1, d_comp, ee)
    if 'eficiencia_radiacion' in r and not math.isnan(r.get('eficiencia_total', float('nan'))):
        # la total del anillo ya incluía su propio desacoplo (casi total sin red): se rehace con el de la red
        out['eficiencia_total'] = r['eficiencia_radiacion']*aj_mod.eficiencia_red_l(f[kr], z_anillo[kr], top, cs, cp, d_z1, d_comp, ee) \
            * (1 - abs(s11[kr])**2)
    out['red'] = {'posicion': top, 'serie': list(cs), 'derivacion': list(cp), 's11_dB': round(float(s11_db[k]), 1),
                  's11_sin_red_dB': round(float(20*np.log10(abs(r['s11'][k]))), 1), 'eficiencia_red': round(eta_red, 3),
                  'z_anillo_ohm': [round(float(z_anillo[k].real), 2), round(float(z_anillo[k].imag), 2)]}
    return out


UMBRAL_MALLA_F_PCT = 5.0     # desplazamiento máximo de la resonancia al cambiar el paso
UMBRAL_MALLA_S11_DB = 5.0    # y del S11 en las frecuencias de interés
LIMITE_S11_DB = -10.0


def verificar_malla(antena, sustrato, base, frecuencias_Hz, precision='normal', factores=(0.85, 1.15),
                    rango=(0.6, 1.4), malla='uniforme', progreso=print, usar_f=True):
    """Repite la simulación `base` con el paso de malla multiplicado por cada factor y dice si el resultado
    depende de la malla (lecciones 52 y 70: el panel y la bibanda cambian hasta un 10 % de frecuencia o 8 dB de S11).

    base: resultado de `simular` (se usa su paso, su resonancia y su S11); rango: el mismo que se usó en `base`.
    frecuencias_Hz: donde se compara el S11 (la de diseño; con dos bandas, las dos).
    usar_f: compara también la frecuencia de resonancia (con dos bandas no vale: es la del mínimo global, que salta
    de una banda a otra; se pasa False y solo cuenta el S11).
    Veredicto «estable» si en todos los factores |Δf| ≤ UMBRAL_MALLA_F_PCT y el S11 no varía más de
    UMBRAL_MALLA_S11_DB en ninguna frecuencia con alguno de los dos valores por encima de −10 dB; si no, «sensible». Sin diagrama de radiación (nf2ff=False): ~2× el tiempo de `base` con 0,85.
    """
    f_centro = base['rango_Hz'][0]/rango[0]
    s11_base = [_s11_en(base, f)[0] for f in frecuencias_Hz]
    filas = []
    for fac in factores:
        paso = round(base['paso_malla_mm']*fac, 3)
        progreso(tr('Verificación de la malla: paso {0:.3f} mm (×{1:g})', paso, fac))
        r = simular(antena, sustrato, f_centro, precision, nf2ff=False, progreso=lambda m: None, paso=paso, malla=malla,
                    rango=rango)
        s11 = [_s11_en(r, f)[0] for f in frecuencias_Hz]
        d_f = 100*(r['f_resonancia_Hz'] - base['f_resonancia_Hz'])/base['f_resonancia_Hz']
        d_s = [b - a for a, b in zip(s11_base, s11)]
        filas.append({'factor': fac, 'paso_mm': paso, 'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2),
                      'dif_f_pct': round(d_f, 2), 's11_dB': [round(x, 1) for x in s11], 'dif_s11_dB': [round(x, 1) for x in d_s],
                      'tiempo_s': r['tiempo_s']})
        progreso(tr('  → resonancia {0:.1f} MHz ({1:+.2f} %), S11 {2}', r['f_resonancia_Hz']/1e6, d_f,
                    ' / '.join(f'{x:.1f} dB' for x in s11)))
    def s11_importa(x):
        return any(abs(d) > UMBRAL_MALLA_S11_DB and max(b, v) > LIMITE_S11_DB
                   for d, b, v in zip(x['dif_s11_dB'], s11_base, x['s11_dB']))
    sensible = any((usar_f and abs(x['dif_f_pct']) > UMBRAL_MALLA_F_PCT) or s11_importa(x) for x in filas)
    return {'veredicto': 'sensible' if sensible else 'estable', 'filas': filas, 'compara_f': usar_f,
            'frecuencias_MHz': [round(f/1e6, 2) for f in frecuencias_Hz], 's11_base_dB': [round(x, 1) for x in s11_base],
            'paso_base_mm': base['paso_malla_mm'], 'umbral_f_pct': UMBRAL_MALLA_F_PCT, 'umbral_s11_dB': UMBRAL_MALLA_S11_DB}


TOLERANCIAS = (('er', 0.05, N_('εr ±5 %')), ('h', 0.10, N_('grosor ±10 %')), ('cobre', 0.05, N_('cobre ±0,05 mm')))


def tolerancias(antena, sustrato, f_obj, banda, base, precision='normal', malla='uniforme', rango=(0.6, 1.4), progreso=print):
    """Cómo cambia la resonancia con las tolerancias de fabricación (una variable cada vez, malla fija, sin diagrama de radiación).

    Simula la antena con la εr un ±5 %, el grosor del FR4 un ±10 % y el cobre ±0,05 mm (`buffer` de las dos caras): 6 simulaciones.
    banda: (f_inf, f_sup) en Hz que hay que cubrir. base: resultado de la antena nominal (da el paso de malla y la referencia).
    Devuelve el desplazamiento por variable, la suma cuadrática, la banda que sobrevive (intersección de las bandas a −10 dB de los 7 casos)
    y un veredicto: 'cubre' (la banda que sobrevive contiene la objetivo), 'justo' (la nominal la cubre, la que sobrevive no) o 'no_cubre'.
    """
    import copy
    import dataclasses
    paso = base.get('paso_malla_mm')
    f0 = base['f_resonancia_Hz']
    bandas = [base['banda_Hz']]
    filas = []
    for var, frac, etq in TOLERANCIAS:
        fila = {'variable': var, 'etiqueta': etq, 'df_pct': [], 'f_MHz': [], 'banda_MHz': []}
        for signo in (-1, 1):
            a, s = antena, sustrato
            if var == 'er':
                s = dataclasses.replace(sustrato, er=sustrato.er*(1 + signo*frac))
            elif var == 'h':
                s = dataclasses.replace(sustrato, h=round(sustrato.h*(1 + signo*frac), 4),
                                        h_ref=round(sustrato.h_ref*(1 + signo*frac), 4))
            else:
                a = copy.copy(antena)
                a.capas = {capa: antena.cobre(capa).buffer(signo*frac, join_style='mitre') for capa in ('F.Cu', 'B.Cu')}
            progreso(tr('Tolerancias: {0} ({1:+d})…', tr(etq), signo))
            r = simular(a, s, f_obj, precision, nf2ff=False, progreso=lambda m: None, rango=rango, paso=paso, malla=malla)
            fila['f_MHz'].append(round(r['f_resonancia_Hz']/1e6, 2))
            fila['df_pct'].append(round(100*(r['f_resonancia_Hz']/f0 - 1), 2))
            flo, fhi = r['banda_Hz']
            fila['banda_MHz'].append(None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)])
            bandas.append(r['banda_Hz'])
        fila['max_df_pct'] = max(abs(v) for v in fila['df_pct'])
        filas.append(fila)
    lo, hi = banda
    validas = [b for b in bandas if b[0] is not None]
    inter = None
    if len(validas) == len(bandas):
        i0, i1 = max(b[0] for b in validas), min(b[1] for b in validas)
        inter = (i0, i1) if i1 > i0 else None
    nominal = base['banda_Hz']
    cubre_nominal = nominal[0] is not None and nominal[0] <= lo and nominal[1] >= hi
    if inter and inter[0] <= lo and inter[1] >= hi:
        veredicto = 'cubre'
    elif cubre_nominal:
        veredicto = 'justo'
    else:
        veredicto = 'no_cubre'
    return {'filas': filas, 'df_total_pct': round(math.sqrt(sum(f['max_df_pct']**2 for f in filas)), 2),
            'banda_sobrevive_MHz': None if inter is None else [round(inter[0]/1e6, 1), round(inter[1]/1e6, 1)],
            'banda_nominal_MHz': None if nominal[0] is None else [round(nominal[0]/1e6, 1), round(nominal[1]/1e6, 1)],
            'banda_objetivo_MHz': [round(lo/1e6, 2), round(hi/1e6, 2)], 'veredicto': veredicto, 'f_nominal_MHz': round(f0/1e6, 2)}


def efecto_entorno(antena, sustrato, f_obj, nombres, base, precision='normal', malla='uniforme', rango=(0.6, 1.4), progreso=print):
    """Cuánto cambian la frecuencia y la eficiencia al poner el entorno (carcasa, batería, mano: ver `entorno.py`).

    Se comparan dos simulaciones con la MISMA malla: una con los bloques de verdad y otra con ellos convertidos en aire
    (`entorno.neutro`). Comparar con la antena sola mezclaría el efecto físico con el de las líneas de malla nuevas, que
    mueven la frecuencia un ~2 % por sí solas. base: resultado de la antena sola (da el paso de malla y la referencia
    de la eficiencia). Devuelve un dict con el cambio de frecuencia, de eficiencia y de S11, o con 'error'.
    """
    import copy
    from . import entorno as ent
    bloques = ent.bloques(antena, sustrato.h, nombres)
    paso = base.get('paso_malla_mm')
    res = {}
    for etq, lista in (('aire', [ent.neutro(b) for b in bloques]), ('entorno', bloques)):
        a = copy.copy(antena)
        a.entorno = lista
        progreso(tr('Entorno ({0}): simulando {1}…', ', '.join(nombres), tr('con los bloques') if etq == 'entorno' else tr('el control, sin material')))
        res[etq] = simular(a, sustrato, f_obj, precision, nf2ff=True, progreso=lambda m: None, rango=rango, paso=paso, malla=malla)
    c, e = res['aire'], res['entorno']
    return {'nombres': list(nombres),
            'f_sin_MHz': round(c['f_resonancia_Hz']/1e6, 2), 'f_con_MHz': round(e['f_resonancia_Hz']/1e6, 2),
            'df_pct': round(100*(e['f_resonancia_Hz']/c['f_resonancia_Hz'] - 1), 2),
            's11_sin_dB': round(c['s11_min_dB'], 1), 's11_con_dB': round(e['s11_min_dB'], 1),
            'eta_sin_%': round(100*c['eficiencia_radiacion'], 1), 'eta_con_%': round(100*e['eficiencia_radiacion'], 1),
            'ganancia_sin_dBi': round(c['ganancia_dBi'], 2), 'ganancia_con_dBi': round(e['ganancia_dBi'], 2)}


def ajustar(clave, parametros, nombre_sustrato, f_obj, precision='normal', max_sim=5, tolerancia=0.01,
            progreso=print, malla='uniforme'):
    """Ajusta el parámetro de escala del tipo simulando (secante) hasta resonar en f_obj.

    Si la antena tiene sobrelargo para recortar (marcas de corte), el objetivo de la simulación
    es la frecuencia SIN recortar, f_obj/(1 + sobrelargo): al cortar por las marcas se llega a f_obj.
    """
    from . import tipos, ajuste as aj_mod
    tipo = tipos.CATALOGO[clave]
    s = tipos.sustrato(nombre_sustrato)
    p = tipos.dimensionar(clave, f_obj, parametros, nombre_sustrato, fijos=tuple(parametros or ()))
    p.pop('_aviso', None)
    p.pop('red_L', None)                          # la red del bucle se vuelve a calcular al final
    if aj_mod.activo(p) and int(p.get('marcas', 0)) == 1 and p.get('sobrelargo', 0) > 0:
        f_final = f_obj
        f_obj = f_obj/(1 + p['sobrelargo']/100)
        progreso(tr('Con sobrelargo del {0:g} %: se ajusta para que SIN cortar resuene en {1:.1f} MHz (cortando por las marcas se llega a {2:.1f} MHz).', p["sobrelargo"], f_obj/1e6, f_final/1e6))
    esc = tipo.escala
    proporciones = {k: p[k]/p[esc] for k in tipo.escala_conjunta}
    cuadrado = abs(p.get('ancho', 0) - p.get('largo', -1)) < 1e-6 and clave in ('parche_minkowski', 'parche_circular', 'array_parches')

    def con_escala(x):
        q = dict(p, **{esc: round(x, 3)})
        for k, r in proporciones.items():
            q[k] = round(r*x, 3)
        if cuadrado:
            q['ancho'] = q[esc]
        return q

    multi = int(p.get('multibanda', 0) or 0) == 1               # dos bandas: la segunda cae a ~3× (rango ancho, sin iterar)
    rango = (0.45, 3.8) if multi else (0.6, 1.4)
    historial = []
    x = max(p[esc], 0.05) if esc == 'capacidad_pF' else p[esc]       # el bucle sin condensador (0 pF) parte de 0,05 pF
    ultimo = None
    paso = None                                   # malla fija durante todo el ajuste
    par = next(pp for pp in tipo.parametros if pp.nombre == esc)
    for n in range(max_sim):
        q = con_escala(x)
        a = tipos.generar(clave, q, nombre_sustrato)
        progreso(tr('Iteración {0}: {1} = {2:.3f} mm', n + 1, esc, x))
        r = simular(a, s, f_obj, precision, nf2ff=False, progreso=progreso, paso=paso, malla=malla, rango=rango)
        if paso is None:
            # se fija con un 10 % de holgura por si la antena encoge y sus detalles con ella
            paso = round(0.9*r['paso_malla_mm'], 3)
        fr = r['f_resonancia_Hz']
        err = (fr - f_obj)/f_obj
        historial.append({'escala_mm': round(x, 3), 'f_resonancia_MHz': round(fr/1e6, 2), 'error_%': round(100*err, 2),
                          'tiempo_s': r['tiempo_s'], 'valido': not r['en_borde'],
                          'S11_obj_dB': round(_s11_en(r, f_obj)[0], 1)})
        progreso(tr('  → resonancia {0:.1f} MHz ({1:+.2f} %, {2}), S11 mín {3:.1f} dB', fr/1e6, 100*err, r["criterio"], r["s11_min_dB"]))
        ultimo = (q, a, r)
        if multi or (not r['en_borde'] and abs(err) < tolerancia):
            break
        if tipo.familia in ('panel', 'array'):
            # La red corporativa (y el reflector del panel) dan un S11 ondulado y ancho (−10…−15 dB en ~1,9–3 GHz):
            # el centro de la banda a −10 dB salta cientos de MHz con cambios mínimos y la secante oscila (el
            # array 2×2: 28,6 mm → 2382 MHz y 27,9 mm → 2105 MHz). El largo sale de la estimación (calibrada);
            # lo que importa es S11 y ganancia en el objetivo.
            break
        if r['avisos'] and 'cortocircuito' in ' '.join(r['avisos']):
            break
        validos = [h_ for h_ in historial if h_['valido']]
        if r['en_borde']:
            # la resonancia está fuera del rango simulado: salto grande en la dirección adecuada
            x_nuevo = x*1.25 if fr > f_obj else x/1.25
            progreso('  (la resonancia cae fuera del rango simulado: salto grande)')
        elif len(validos) < 2:
            x_nuevo = x*fr/f_obj                  # f ∝ 1/tamaño
        else:
            a1, a2 = validos[-2], validos[-1]
            pend = (a2['f_resonancia_MHz'] - a1['f_resonancia_MHz'])/(a2['escala_mm'] - a1['escala_mm'] or 1e-9)
            # la frecuencia debe bajar al crecer la antena; si no, la secante no es fiable
            x_nuevo = a2['escala_mm'] + (f_obj/1e6 - a2['f_resonancia_MHz'])/pend if pend < 0 else x*fr/f_obj
        x_nuevo = min(max(x_nuevo, 0.7*x), 1.3*x)  # pasos acotados (±30 %)
        x = min(max(x_nuevo, par.minimo), par.maximo)
    # Mejor iteración (menor error) para la simulación final
    mejor = min(range(len(historial)), key=lambda i: (not historial[i]['valido'], abs(historial[i]['error_%'])))
    q = con_escala(historial[mejor]['escala_mm'])
    a = tipos.generar(clave, q, nombre_sustrato)
    if tipo.familia == 'jpole' and not multi:
        q, a = _ajustar_toma(clave, q, nombre_sustrato, s, f_obj, precision, paso, progreso, historial,
                             malla=malla)
    elif (clave in PARAM_ADAPTACION or _con_muesca(clave, q)) and historial[mejor]['S11_obj_dB'] > -10:
        progreso(tr('Resuena en el objetivo pero con S11 {0} dB: se ajusta la adaptación', historial[mejor]["S11_obj_dB"]))
        q, a = _ajustar_adaptacion(clave, q, nombre_sustrato, s, f_obj, precision, paso, progreso, historial,
                                   historial[mejor]['S11_obj_dB'], malla=malla)
    progreso(tr('Simulación final con diagrama de radiación…'))
    r = simular(a, s, f_obj, precision, nf2ff=True, progreso=progreso, paso=paso, malla=malla, rango=rango,
                f_radiacion=f_obj if (multi or tipo.familia in ('panel', 'array')) else None)
    if tipo.familia == 'bucle' and aj_mod.activo(q) and int(q.get('red_pi', 0)) == 1:
        # el bucle (R de entrada de pocos ohmios) no adapta sin red: con la Z simulada del anillo se calcula una red en L con
        # valores E24 y pérdidas, y se aplica por circuito (no hace falta otra FDTD: ver `aplicar_red_bucle`)
        progreso(tr('Calculando la red de adaptación con la impedancia simulada…'))
        red = red_adaptacion_bucle(a, r, f_obj, s)
        if red:
            q = dict(q, red_L={'posicion': red['posicion'], 'serie': list(red['serie']), 'derivacion': list(red['derivacion'])})
            a = tipos.generar(clave, q, nombre_sustrato)
            r = aplicar_red_bucle(a, r, f_obj, s)
            progreso(tr('Red: serie {0}, derivación {1} en {2}: S11 {3:.1f} dB en el objetivo (sin red, {4:.1f} dB).',
                        aj_mod.texto_componente(*red['serie']), aj_mod.texto_componente(*red['derivacion']), red['posicion'],
                        r['red']['s11_dB'], r['red']['s11_sin_red_dB']))
    f_est = a.info.get('f_sin_cortar_MHz')
    if f_est and tipo.familia not in ('panel', 'array'):
        # las marcas se rotulaban con la estimación analítica (un 5 % baja en el monopolo de 868):
        # se corrige con la resonancia simulada de la antena sin cortar
        q = dict(q, k_sim=round(tipos.k_sim(q)*r['f_resonancia_Hz']/(f_est*1e6), 4))
        a = tipos.generar(clave, q, nombre_sustrato)
        progreso(tr('Marcas de corte rotuladas con la simulación (×{0:.4f} sobre la estimación)', q["k_sim"]))
    return q, a, r, historial
