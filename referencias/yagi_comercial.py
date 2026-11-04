"""Modelo de la Yagi comercial 2,4/5,8 GHz del usuario y comparación con su medida.

Uso (desde la raíz del proyecto):
    python -m referencias.yagi_comercial [dibujar|simular] [--precision normal]

Geometría sacada de fotos con calibre (±0,5–1 mm), y = distancia desde el borde del conector:
  - FR4 1,6 mm; placa trapezoidal 56,6 mm (conector) → 37 mm (punta), 118 mm de largo.
  - Reflector: banda de masa de todo el ancho, 0–6 mm, en las dos caras.
  - Boom de 4 mm: cara inferior entero; en la superior, hasta el dipolo, coplanar con masa
    (dos tiras a masa con vías a los lados de la pista viva) y, tras la «U», boom macizo.
  - Dipolo plegado «apilado»: en la cara superior partido en dos mitades (ensanchadas hacia las
    puntas) alimentadas en contrafase por un balun microstrip (el vivo se divide: rama directa a la
    mitad izquierda y rama con una «U» de retardo a la derecha); en la inferior, un elemento recto de
    ~6 mm (el ancho de las puntas) unido al boom; vías solo en las puntas. Por eso el conector está en cortocircuito en continua.
  - 5 directores de 3,7 mm de ancho más una barra final, en las dos caras con vías en el perímetro,
    unidos al boom.
Salidas en salidas/_referencias/yagi_comercial/: geometria.png, resultado.json, comparacion.png.
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
SALIDA = os.path.join(RAIZ, 'salidas', '_referencias', 'yagi_comercial')
MEDIDA = os.path.join(RAIZ, 'vna', 'medidas', 'yagi_comercial_2g4_5g8.s1p')
SUSTRATO = 'FR4 JLC 1,6 mm'

LARGO, ANCHO_ATRAS, ANCHO_PUNTA = 118.0, 56.6, 37.0
BORDE = 0.5
BOOM = 4.0
W_VIVO, HUECO_CPW = 1.6, 0.25
Y_BANDA = 6.0                              # reflector: banda de 0 a 6 mm
# Dipolo: canto delantero recto, trasero inclinado (más ancho en la punta)
Y_DIP_DEL, ALTO_PUNTA, ALTO_CENTRO, MEDIO_DIP, HUECO_CENTRO = 28.0, 5.9, 2.7, 39.5/2, 2.5
Y_SPLIT = 24.0                             # donde se divide el vivo
Y_FONDO_U, W_U, X_U1, X_U2 = 36.6, 1.2, -0.15, 1.4
Y_BOOM_SUP = 37.6                          # el boom de la cara superior empieza tras la «U»
DIRECTORES = [(39.7, 42.8), (38.7, 57.6), (37.6, 71.8), (36.6, 86.5), (35.8, 101.3), (37.0, 115.5)]
W_DIR = 3.7
PASO_VIAS = 2.0


def contorno():
    return Polygon([(-ANCHO_ATRAS/2, 0), (ANCHO_ATRAS/2, 0), (ANCHO_PUNTA/2, LARGO), (-ANCHO_PUNTA/2, LARGO)])


def vias_perimetro(x0, y0, x1, y1, retranqueo=0.6, paso=PASO_VIAS):
    """Vías a lo largo del perímetro de un rectángulo (cosido de las dos caras)."""
    xa, xb, ya, yb = x0 + retranqueo, x1 - retranqueo, y0 + retranqueo, y1 - retranqueo
    v = [(x, y) for x in np.arange(xa, xb + 1e-6, paso) for y in (ya, yb)]
    v += [(x, y) for y in np.arange(ya + paso, yb - 1e-6, paso) for x in (xa, xb)]
    return v


def generar(variante='base'):
    """variante: 'base' (modelo completo con el balun) o 'dif' (sin balun ni coplanar: puerto
    diferencial ideal entre las dos mitades del dipolo, para ver la resonancia del radiador solo)."""
    cont = contorno()
    interior = cont.buffer(-BORDE, join_style='mitre')
    sup, inf, vias = [], [], []
    # Reflector (banda) y boom
    banda = g.rectangulo(-ANCHO_ATRAS/2, BORDE, ANCHO_ATRAS/2, Y_BANDA)
    inf += [banda, g.rectangulo(-BOOM/2, BORDE, BOOM/2, LARGO - BORDE)]
    y_toma = Y_DIP_DEL - ALTO_CENTRO/2
    y_boom_sup = Y_BOOM_SUP
    if variante == 'dif':
        sup.append(banda)
        vias += [(x, Y_BANDA - 0.6) for x in np.arange(-ANCHO_ATRAS/2 + 1.5, ANCHO_ATRAS/2 - 1.4, PASO_VIAS)]
    elif variante == 'v2':
        # Segunda lectura de la foto macro: la masa coplanar derecha se desplaza al centro y sigue como
        # tira de masa (con vías) entre las dos ramas; el vivo se va a la izquierda, alimenta la mitad
        # izquierda por un puente, sigue hacia delante, rodea el final de la tira central y vuelve por la
        # derecha hasta la mitad derecha. Ramas blindadas por la masa central (no acopladas entre sí).
        w_v, g_cpw, w_r, w_c = 1.6, HUECO_CPW, 1.4, 1.2
        x_ida, x_vuelta = -(w_c/2 + g_cpw + w_r/2), w_c/2 + g_cpw + w_r/2
        x_masa_d = (w_v/2 + g_cpw + BOOM/2)/2          # centro de la tira de masa derecha del coplanar
        y_fin_centro, y_giro = 36.65, 37.9
        y_boom_sup = 38.15
        hueco_vivo = g.rectangulo(-w_v/2 - g_cpw, 0, w_v/2 + g_cpw, Y_BANDA + 1)
        sup.append(banda.difference(hueco_vivo))
        vias += [(x, Y_BANDA - 0.6) for x in np.arange(-ANCHO_ATRAS/2 + 1.5, ANCHO_ATRAS/2 - 1.4, PASO_VIAS)
                 if abs(x) > 1.6]
        # masa coplanar izquierda (acaba antes del desvío) y derecha, que se va al centro
        sup.append(g.rectangulo(-BOOM/2, Y_BANDA - 0.1, -(w_v/2 + g_cpw), 23.0))
        vias += [(-x_masa_d, y) for y in np.arange(Y_BANDA + 1, 22.5, 1.5)]
        sup.append(g.engordar([(x_masa_d, Y_BANDA - 0.1), (x_masa_d, 24.6), (0.0, 26.0), (0.0, y_fin_centro)], w_c))
        sup.append(g.rectangulo(w_v/2 + g_cpw, Y_BANDA - 0.1, BOOM/2, 24.6))
        vias += [(x_masa_d, y) for y in np.arange(Y_BANDA + 1, 23.6, 1.5)]
        vias += [(0.0, y) for y in np.arange(26.8, y_fin_centro - 0.5, 1.7)]
        # vivo: recto hasta 23,6, desvío a la izquierda y rama de ida hasta el giro
        sup.append(g.rectangulo(-w_v/2, BORDE, w_v/2, 23.6))
        sup.append(g.engordar([(0.0, 23.3), (x_ida, 25.0), (x_ida, y_giro - 0.5)], w_r))
        sup.append(g.rectangulo(x_ida - w_r/2, y_giro - 1.0, x_vuelta + w_r/2, y_giro))     # giro
        sup.append(g.rectangulo(x_vuelta - w_r/2, 26.6, x_vuelta + w_r/2, y_giro))         # vuelta
        # puente a la mitad izquierda y unión de la vuelta con la mitad derecha
        sup.append(g.rectangulo(-HUECO_CENTRO - 0.3, y_toma - 0.55, x_ida, y_toma + 0.55))
        sup.append(g.rectangulo(x_vuelta, 26.6, HUECO_CENTRO + 0.3, Y_DIP_DEL - 0.1))
    else:
        hueco_vivo = g.rectangulo(-W_VIVO/2 - HUECO_CPW, 0, W_VIVO/2 + HUECO_CPW, Y_BANDA + 1)
        sup.append(banda.difference(hueco_vivo))
        vias += [(x, Y_BANDA - 0.6) for x in np.arange(-ANCHO_ATRAS/2 + 1.5, ANCHO_ATRAS/2 - 1.4, PASO_VIAS)
                 if abs(x) > 1.6]
        # Coplanar con masa a los lados del vivo, hasta el dipolo
        for s in (-1, 1):
            x_in, x_out = s*(W_VIVO/2 + HUECO_CPW), s*BOOM/2
            sup.append(g.rectangulo(min(x_in, x_out), Y_BANDA - 0.1, max(x_in, x_out), Y_SPLIT - 0.6))
            vias += [((x_in + x_out)/2, y) for y in np.arange(Y_BANDA + 1, Y_SPLIT - 1, 1.5)]
        # Vivo y balun: rama directa a la mitad izquierda y rama con «U» a la derecha
        sup.append(g.rectangulo(-W_VIVO/2, BORDE, W_VIVO/2, Y_SPLIT))
        sup.append(g.engordar([(0, Y_SPLIT - 0.3), (-1.2, y_toma), (-HUECO_CENTRO - 0.3, y_toma)], 0.9))
        sup.append(g.engordar([(X_U1, Y_SPLIT - 0.3), (X_U1, Y_FONDO_U), (X_U2, Y_FONDO_U), (X_U2, y_toma),
                               (HUECO_CENTRO + 0.3, y_toma)], W_U))
    # Dipolo plegado: mitades arriba, continuo abajo, vías en las puntas
    y_tras_punta, y_tras_centro = Y_DIP_DEL - ALTO_PUNTA, Y_DIP_DEL - ALTO_CENTRO
    for s in (-1, 1):
        sup.append(Polygon([(s*MEDIO_DIP, y_tras_punta), (s*HUECO_CENTRO, y_tras_centro),
                            (s*HUECO_CENTRO, Y_DIP_DEL), (s*MEDIO_DIP, Y_DIP_DEL)]))
        vias += [(s*(MEDIO_DIP - 0.6), y) for y in np.arange(y_tras_punta + 0.6, Y_DIP_DEL - 0.5, 1.0)]
    # cara inferior: elemento recto del ancho de las puntas (foto de la cara de atrás), no una copia
    inf.append(g.rectangulo(-MEDIO_DIP, y_tras_punta, MEDIO_DIP, Y_DIP_DEL))
    # Boom superior tras la «U» y directores en las dos caras
    sup.append(g.rectangulo(-BOOM/2, y_boom_sup, BOOM/2, LARGO - BORDE))
    vias += [(s*1.5, y) for y in np.arange(y_boom_sup + 0.8, LARGO - 1, PASO_VIAS) for s in (-1, 1)]
    for largo, y in DIRECTORES:
        r = g.rectangulo(-largo/2, y - W_DIR/2, largo/2, y + W_DIR/2).intersection(interior)
        sup.append(r); inf.append(r)
        x0, y0, x1, y1 = r.bounds
        vias += [v for v in vias_perimetro(x0, y0, x1, y1) if abs(v[0]) > 2.2]
    cobre_sup = unary_union(sup).intersection(interior)
    cobre_inf = unary_union(inf).intersection(interior)
    if variante == 'dif':
        # puerto horizontal en el hueco central, de mitad a mitad (como el de la J-pole)
        puerto = {'tipo': 'coaxial', 'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, y_toma),
                  'puntos': [(-HUECO_CENTRO, y_toma), (HUECO_CENTRO, y_toma)], 'ancho_linea': ALTO_CENTRO}
        info = {'pista_minima_mm': ALTO_CENTRO, 'hueco_minimo_mm': 2*HUECO_CENTRO}
    else:
        puerto = {'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, Y_SPLIT), 'ancho_linea': W_VIVO}
        info = {'pista_minima_mm': 0.9, 'hueco_minimo_mm': HUECO_CPW}
    return Antena(tipo='yagi_comercial', parametros={}, capas={'F.Cu': cobre_sup, 'B.Cu': cobre_inf},
                  radiador=unary_union([cobre_sup, cobre_inf]), contorno=cont, vias=vias,
                  puerto=puerto, info=info)


def dibujar(a, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(12, 12), tight_layout=True)
    for ax, capa, titulo in ((axs[0], 'F.Cu', 'Cara superior (pista)'), (axs[1], 'B.Cu', 'Cara inferior')):
        for p in g.poligonos(a.cobre(capa)):
            ax.fill(*p.exterior.xy, color='#c8892b' if capa == 'F.Cu' else '#7f9ed6')
            for h in p.interiors:
                ax.fill(*h.xy, color='white')
        ax.plot(*a.contorno.exterior.xy, 'k-', lw=1)
        vx, vy = zip(*a.vias)
        ax.plot(vx, vy, 'k.', ms=2)
        ax.set_aspect('equal'); ax.set_title(titulo); ax.invert_yaxis()
    fig.savefig(ruta, dpi=110)
    plt.close(fig)


def leer_s1p(ruta):
    f, s = [], []
    for l in open(ruta, encoding='utf-8'):
        if l.startswith(('!', '#')) or not l.strip():
            continue
        x = [float(v) for v in l.split()]
        f.append(x[0]); s.append(x[1] + 1j*x[2])
    return np.array(f), np.array(s)


def _opcion(nombre, defecto=None):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


def main():
    """Opciones: --variante base|dif, --paso <mm> (malla gruesa para diagnosticar), --precision."""
    variante = _opcion('--variante', 'base')
    paso = _opcion('--paso')
    salida = SALIDA if variante == 'base' and paso is None else os.path.join(SALIDA, f'{variante}_p{paso or "auto"}')
    os.makedirs(salida, exist_ok=True)
    a = generar(variante)
    dibujar(a, os.path.join(salida, 'geometria.png'))
    print(f'Vías: {len(a.vias)}; placa {a.contorno.bounds}')
    if 'simular' not in sys.argv:
        return
    prec = _opcion('--precision', 'normal')
    s = tipos.sustrato(SUSTRATO)
    r = sim.simular(a, s, 2.4e9, prec, nf2ff=True, malla='adaptada', paso=None if paso is None else float(paso),
                    progreso=lambda m: print('PROGRESO', m, flush=True))
    f, s11 = r['f_Hz'], r['s11']
    db = 20*np.log10(np.abs(s11))
    fm, sm = leer_s1p(MEDIDA)
    dbm = 20*np.log10(np.abs(sm))
    flo, fhi = r['banda_Hz']
    resumen = {'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 1),
               'banda_MHz': None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)],
               's11_min_dB': round(r['s11_min_dB'], 1), 'f_min_s11_MHz': round(r['f_min_s11_Hz']/1e6, 1),
               'directividad_dBi': round(r['directividad_dBi'], 2), 'ganancia_dBi': round(r['ganancia_dBi'], 2),
               'eficiencia_radiacion_%': round(100*r['eficiencia_radiacion'], 1),
               'direccion_max': r['direccion_max'], 'celdas': r['celdas'], 'tiempo_s': r['tiempo_s'],
               'avisos': r['avisos'],
               'medida': {'banda_MHz': [2306.6, 2461.8], 'f_min_MHz': 2344.1, 's11_min_dB': -36.3}}
    # impedancia simulada donde están las resonancias medidas
    for fz in (1790e6, 2127e6, 2344e6, 2440e6):
        z = r['zin'][np.argmin(np.abs(f - fz))]
        resumen[f'Z_{fz/1e6:.0f}MHz_ohm'] = [round(float(z.real), 1), round(float(z.imag), 1)]
    json.dump(resumen, open(os.path.join(salida, 'resultado.json'), 'w', encoding='utf-8'), indent=2,
              ensure_ascii=False, default=float)
    np.savez_compressed(os.path.join(salida, 'datos.npz'), f=f, s11=s11, zin=r['zin'], theta=r['theta'],
                        phi=r['phi'], d=r['directividad_dBi_grid'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5), tight_layout=True)
    ax.plot(fm/1e6, dbm, label='Medida (NanoVNA, calibración del PC)')
    ax.plot(f/1e6, db, label=f'Simulación (openEMS, variante {variante})')
    ax.axhline(-10, ls='--', c='gray'); ax.set_xlim(1500, 3300); ax.grid(True); ax.legend()
    ax.set_xlabel('MHz'); ax.set_ylabel('S11 [dB]'); ax.set_title('Yagi comercial: medida frente a simulación')
    fig.savefig(os.path.join(salida, 'comparacion.png'), dpi=100)
    print(json.dumps(resumen, indent=2, ensure_ascii=False, default=float))


if __name__ == '__main__':
    main()
