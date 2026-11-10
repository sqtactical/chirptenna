"""Modelo de la segunda Yagi comercial de 2,4 GHz del usuario (placa trapezoidal con dipolo plegado y 3 directores), para estudiarla.

Uso (desde la raíz del proyecto):
    python -m referencias.yagi_comercial_b [dibujar|simular] [--variante acopla|via|dif|abierto] [--sustrato S] [--paso mm] [--precision normal]

Geometría leída de dos fotos con regla (cara superior y cara inferior), ±1 mm. y = distancia desde el borde del conector, x = transversal.
Las fotos no están en el repositorio. Lo que se ve:
  - Placa trapezoidal de ~100 mm de largo: 49 mm de ancho junto al conector (se mantiene 15 mm) y 34–36 mm en la punta.
    Dos agujeros de montaje junto al conector. FR4 de ~0,8 mm (una línea de 50 Ω de 1,5 mm de ancho, como la de la foto).
  - Conector SMA de canto en el borde. Línea microstrip en la cara superior: sale recta, tiene un escalón de ~2 mm con una pequeña
    pata de adaptación (stub) a 13 mm y sigue hasta 37 mm, donde gira y baja ~5 mm (una «barra de alimentación» vertical).
  - Dipolo plegado a 36–43 mm: en la cara inferior un anillo rectangular de 7 × 40 mm (barra de 2 mm); en la superior la misma forma
    abierta por el centro (dos «C» de ±7 a ±20 mm); vías en sus bordes. El anillo inferior se une al reflector por una tira
    (1,5 mm) desde el centro de su lado izquierdo.
  - Reflector: barra de 9 × 48 mm a 14–23 mm, en la cara inferior.
  - Tres directores de 6,8 mm de ancho, en las dos caras con vías en el perímetro, de 37,7, 36,8 y 34,4 mm de largo, centrados a
    58,6, 76,7 y 95,8 mm (separación 18–19 mm ≈ 0,15 λ).
  - Flecha de serigrafía hacia los directores.
El usuario confirma (10-11) que el elemento central de la cara superior va UNIDO, pero por el lado de los directores (no por el de la
línea): una «]» con la barra continua de ±20 mm y los dos brazos hacia el reflector; la barra de alimentación de la línea queda
suelta, dentro de la abertura y encima de la barra izquierda del anillo de abajo. No se sabe cómo se alimenta el anillo de abajo (¿acoplo capacitivo a través del FR4 o una vía?) ni qué hace la tira
al reflector: de ahí las variantes. `acopla` (elemento superior unido por la derecha, sin vía), `via` (además, una vía de la barra de la línea al anillo, a +2 mm del centro: una
toma desplazada de la tira a masa, como una F invertida), `dif` (puerto diferencial ideal entre las dos «C», sin línea) y `abierto` (las dos
«C» separadas, el primer modelo).
Salidas en salidas/_referencias/yagi_comercial_b/<variante>/: geometria.png y resultado.json.
"""
import os
import sys
import json

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from antenas import geometria as g
from antenas import simulacion as sim
from antenas import tipos
from antenas.modelo import Antena

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'salidas', '_referencias', 'yagi_comercial_b')
SUSTRATO = 'FR4 JLC 0,8 mm'

LARGO, ANCHO_ATRAS, ANCHO_PUNTA, Y_ESTRECHA = 100.0, 49.0, 35.0, 15.0
BORDE = 0.5
W_LINEA = 1.5
# línea de la cara superior
Y_ESCALON, DX_LINEA, Y_FIN_LINEA, X_BAJA = 13.2, 2.0, 37.3, 5.2
# dipolo plegado
Y_ANILLO0, Y_ANILLO1, MEDIO_ANILLO, W_BARRA, HUECO_C = 36.0, 43.2, 20.0, 2.1, 7.0
# reflector
Y_REFL0, Y_REFL1, W_TIRA = 14.0, 23.0, 1.5
DIRECTORES = [(37.7, 58.6), (36.8, 76.7), (34.4, 95.8)]       # (largo, y del centro)
W_DIR = 6.8
PASO_VIAS = 2.0


def contorno():
    return Polygon([(0, -ANCHO_ATRAS/2), (Y_ESTRECHA, -ANCHO_ATRAS/2), (LARGO, -ANCHO_PUNTA/2), (LARGO, ANCHO_PUNTA/2),
                    (Y_ESTRECHA, ANCHO_ATRAS/2), (0, ANCHO_ATRAS/2)])


def vias_perimetro(x0, y0, x1, y1, retranqueo=0.6, paso=PASO_VIAS):
    xa, xb, ya, yb = x0 + retranqueo, x1 - retranqueo, y0 + retranqueo, y1 - retranqueo
    v = [(x, y) for x in np.arange(xa, xb + 1e-6, paso) for y in (ya, yb)]
    v += [(x, y) for y in np.arange(ya + paso, yb - 1e-6, paso) for x in (xa, xb)]
    return v


def rect(y0, x0, y1, x1):
    """Rectángulo con y (a lo largo de la placa) y x (transversal); en el modelo se usa (x=largo, y=ancho): se intercambian."""
    return g.rectangulo(y0, x0, y1, x1)


def generar(variante='acopla'):
    """Coordenadas del modelo: x = a lo largo de la placa (desde el conector), y = transversal."""
    cont = contorno()
    interior = cont.buffer(-BORDE, join_style='mitre')
    sup, inf, vias = [], [], []
    # --- cara inferior: reflector, tira, anillo y directores
    inf.append(rect(Y_REFL0, -24.0, Y_REFL1, 24.0))
    inf.append(rect(Y_REFL1 - 0.1, -W_TIRA/2, Y_ANILLO0 + 0.1, W_TIRA/2))
    ext = rect(Y_ANILLO0, -MEDIO_ANILLO, Y_ANILLO1, MEDIO_ANILLO)
    hueco = rect(Y_ANILLO0 + W_BARRA, -MEDIO_ANILLO + W_BARRA, Y_ANILLO1 - W_BARRA, MEDIO_ANILLO - W_BARRA)
    inf.append(ext.difference(hueco))
    # masa del conector SMA de canto: patas en las dos caras junto al borde (la línea sale de ahí sin más masa hasta el reflector)
    inf.append(rect(BORDE, -4.0, 6.5, 4.0))
    for s in (-1, 1):
        sup.append(rect(BORDE, min(s*2.0, s*5.0), 5.0, max(s*2.0, s*5.0)))
        vias += [(2.0, s*3.5), (4.0, s*3.5)]
    # --- cara superior: línea microstrip y barra de alimentación
    sup.append(rect(BORDE, -W_LINEA/2, Y_ESCALON + W_LINEA/2, W_LINEA/2))                      # tramo recto
    sup.append(rect(Y_ESCALON - W_LINEA/2, -2.4, Y_ESCALON + W_LINEA/2, DX_LINEA + W_LINEA/2))  # escalón con la pata
    sup.append(rect(Y_ESCALON - W_LINEA/2, DX_LINEA - W_LINEA/2, Y_FIN_LINEA + W_LINEA/2, DX_LINEA + W_LINEA/2))
    sup.append(rect(Y_FIN_LINEA - W_LINEA/2, DX_LINEA - X_BAJA, Y_FIN_LINEA + W_LINEA/2, DX_LINEA + W_LINEA/2))  # barra que baja
    # «C» superiores: el anillo sin el centro
    for s in (-1, 1):
        c = rect(Y_ANILLO0, min(s*HUECO_C, s*MEDIO_ANILLO), Y_ANILLO1, max(s*HUECO_C, s*MEDIO_ANILLO))
        sup.append(c.difference(rect(Y_ANILLO0 + W_BARRA, min(s*HUECO_C, s*(MEDIO_ANILLO - W_BARRA)),
                                     Y_ANILLO1 - W_BARRA, max(s*HUECO_C, s*(MEDIO_ANILLO - W_BARRA)))))
        vias += [(Y_ANILLO0 + W_BARRA/2, s*y) for y in np.arange(HUECO_C + 0.5, MEDIO_ANILLO - 0.4, 2.0)]
        vias += [(Y_ANILLO1 - W_BARRA/2, s*y) for y in np.arange(HUECO_C + 0.5, MEDIO_ANILLO - 0.4, 2.0)]
        vias += [(x, s*(MEDIO_ANILLO - W_BARRA/2)) for x in np.arange(Y_ANILLO0 + 0.8, Y_ANILLO1 - 0.3, 2.0)]
    if variante not in ('abierto', 'dif'):
        # el elemento central de la cara superior va unido por el lado de los directores (dato del usuario, 09-11): una «]»
        sup.append(rect(Y_ANILLO1 - W_BARRA, -HUECO_C - 0.1, Y_ANILLO1, HUECO_C + 0.1))
        vias += [(Y_ANILLO1 - W_BARRA/2, y) for y in np.arange(-HUECO_C + 0.5, HUECO_C - 0.4, 2.0)]
    if variante == 'via':
        vias.append((Y_FIN_LINEA, DX_LINEA - 1.0))
    # --- directores en las dos caras
    for largo, y in DIRECTORES:
        r = rect(y - W_DIR/2, -largo/2, y + W_DIR/2, largo/2).intersection(interior)
        sup.append(r); inf.append(r)
        x0, y0, x1, y1 = r.bounds
        vias += vias_perimetro(x0, y0, x1, y1)
    cobre_sup = unary_union(sup).intersection(interior)
    cobre_inf = unary_union(inf).intersection(interior)
    if variante == 'dif':
        # sin línea: puerto ideal entre las dos «C» (en el centro del lado izquierdo del anillo)
        sup_dif = unary_union([p for p in g.poligonos(cobre_sup) if abs(p.centroid.y) > 5 or p.centroid.x > 50])
        cobre_sup = sup_dif
        puerto = {'tipo': 'coaxial', 'borde': (0.0, 0.0), 'direccion': (1, 0), 'alimentacion': (Y_ANILLO0 + W_BARRA/2, 0.0),
                  'puntos': [(Y_ANILLO0 + W_BARRA/2, -HUECO_C), (Y_ANILLO0 + W_BARRA/2, HUECO_C)], 'ancho_linea': W_BARRA}
        info = {'pista_minima_mm': W_BARRA, 'hueco_minimo_mm': 2*HUECO_C}
    else:
        puerto = {'borde': (0.0, 0.0), 'direccion': (1, 0), 'alimentacion': (BORDE, 0.0), 'ancho_linea': W_LINEA}
        info = {'pista_minima_mm': 1.2, 'hueco_minimo_mm': 1.0}
    return Antena(tipo='yagi_comercial_b', parametros={}, capas={'F.Cu': cobre_sup, 'B.Cu': cobre_inf},
                  radiador=unary_union([cobre_sup, cobre_inf]), contorno=cont, vias=vias, puerto=puerto, info=info)


def dibujar(a, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 1, figsize=(11, 9), tight_layout=True)
    for ax, capa, titulo in ((axs[0], 'F.Cu', 'Cara superior (línea)'), (axs[1], 'B.Cu', 'Cara inferior')):
        for p in g.poligonos(a.cobre(capa)):
            ax.fill(*p.exterior.xy, color='#c8892b' if capa == 'F.Cu' else '#7f9ed6')
            for h in p.interiors:
                ax.fill(*h.xy, color='white')
        ax.plot(*a.contorno.exterior.xy, 'k-', lw=1)
        if a.vias:
            vx, vy = zip(*a.vias)
            ax.plot(vx, vy, 'k.', ms=2)
        ax.set_aspect('equal'); ax.set_title(titulo)
    fig.savefig(ruta, dpi=110)
    plt.close(fig)


def _opcion(nombre, defecto=None):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


def main():
    variante = _opcion('--variante', 'acopla')
    paso = _opcion('--paso')
    sustrato = _opcion('--sustrato', SUSTRATO)
    etiqueta = variante + ('' if sustrato == SUSTRATO else '_' + sustrato.replace(' ', '').replace(',', '').replace('mm', 'mm')) + (f'_p{paso}' if paso else '')
    salida = os.path.join(SALIDA, etiqueta)
    os.makedirs(salida, exist_ok=True)
    a = generar(variante)
    dibujar(a, os.path.join(salida, 'geometria.png'))
    print(f'Vías: {len(a.vias)}; placa {[round(v, 1) for v in a.contorno.bounds]}')
    if 'simular' not in sys.argv:
        return
    os.environ.setdefault('ANTENAS_GPU', '1')
    import importlib.util
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    lock = barrido._bloqueo() if os.environ['ANTENAS_GPU'] != '0' else None
    try:
        s = tipos.sustrato(sustrato)
        r = sim.simular(a, s, 2.4e9, _opcion('--precision', 'normal'), nf2ff=True, malla='adaptada',
                        paso=None if paso is None else float(paso), progreso=lambda m: print('PROGRESO', m, flush=True))
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)
    f = r['f_Hz']
    db = 20*np.log10(np.abs(r['s11']))
    flo, fhi = r['banda_Hz']
    resumen = {'variante': variante, 'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 1),
               'banda_MHz': None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)],
               's11_min_dB': round(r['s11_min_dB'], 1), 'f_min_s11_MHz': round(r['f_min_s11_Hz']/1e6, 1),
               's11_2441_dB': round(float(db[np.argmin(np.abs(f - 2441.75e6))]), 1),
               'directividad_dBi': round(r['directividad_dBi'], 2), 'ganancia_dBi': round(r['ganancia_dBi'], 2),
               'eficiencia_radiacion_%': round(100*r['eficiencia_radiacion'], 1), 'direccion_max': r['direccion_max'],
               'celdas': r['celdas'], 'tiempo_s': r['tiempo_s'], 'avisos': r['avisos']}
    json.dump(resumen, open(os.path.join(salida, 'resultado.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False, default=float)
    np.savez_compressed(os.path.join(salida, 'datos.npz'), f=f, s11=r['s11'], zin=r['zin'])
    print(json.dumps(resumen, indent=2, ensure_ascii=False, default=float))


if __name__ == '__main__':
    main()
