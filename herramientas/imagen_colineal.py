"""Imagen comparando las formas de brazo de la colineal de dipolos (U, bowtie, Sierpinski): la placa entera y un dipolo ampliado.

Uso (desde la raíz):
    python herramientas/imagen_colineal.py [salida.png] [f_MHz] [elementos]

Dibuja la cara superior (vivo, naranja) y la inferior (masa, azul) de cada forma a la frecuencia dada con `tipos.dimensionar` (sin centrar), en una sola
placa. Por defecto `salidas/_vistas/colineal_formas.png` a 2441,75 MHz y 4 dipolos.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

FORMAS = ((0, 'U (dos patas)'), (1, 'Bowtie (triángulo)'), (2, 'Bowtie de Sierpinski (iteración 2)'))


def _giro(geom):
    """Gira la geometría para que la línea quede horizontal: (x, y) → (y, x)."""
    from shapely import affinity
    return affinity.affine_transform(geom, [0, 1, 1, 0, 0, 0])


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    import numpy as np
    from antenas import tipos
    from antenas.geometria import poligonos

    salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'salidas', '_vistas', 'colineal_formas.png')
    f_MHz = float(sys.argv[2]) if len(sys.argv) > 2 else 2441.75
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    def pintar(ax, geom, color, alfa, ec='none'):
        for pol in poligonos(geom):
            anillos = [np.array(pol.exterior.coords)] + [np.array(h.coords) for h in pol.interiors]
            verts = np.concatenate(anillos)
            codigos = np.concatenate([[Path.MOVETO] + [Path.LINETO]*(len(a) - 2) + [Path.CLOSEPOLY] for a in anillos])
            ax.add_patch(PathPatch(Path(verts, codigos), fc=color, ec=ec, lw=0.4, alpha=alfa))

    fig, ejes = plt.subplots(len(FORMAS), 2, figsize=(15, 2.7*len(FORMAS)), gridspec_kw={'width_ratios': [3.2, 1]})
    for fila, (forma, nombre) in enumerate(FORMAS):
        p = tipos.dimensionar('colineal_dipolos', f_MHz*1e6, {'forma': forma, 'elementos': n, 'modular': 0})
        p.pop('_aviso', None)
        a = tipos.generar('colineal_dipolos', p)
        sup, inf, cont = _giro(a.cobre('F.Cu')), _giro(a.cobre('B.Cu')), _giro(a.contorno)
        # (1) la placa entera
        ax = ejes[fila][0]
        pintar(ax, cont, '#2e7d32', 0.18, ec='#2e7d32')
        pintar(ax, inf, '#7f9ed6', 0.55)
        pintar(ax, sup, '#c8892b', 0.95)
        bx, by = a.puerto['borde']
        ax.plot(by, bx, 'r<', ms=9)
        x0, y0, x1, y1 = cont.bounds
        ax.set_xlim(x0 - 4, x1 + 4); ax.set_ylim(y0 - 4, y1 + 4); ax.set_aspect('equal')
        ax.set_title(f"{nombre} · {n} dipolos · brazo {p['largo_brazo']:.1f} mm · placa {x1 - x0:.0f} × {y1 - y0:.0f} mm", loc='left', fontsize=11)
        ax.set_yticks([]); ax.set_xlabel('mm' if fila == len(FORMAS) - 1 else '')
        # (2) un dipolo ampliado (el segundo), con el cobre de las dos caras y el contorno
        ax = ejes[fila][1]
        ys = a.info.get('longitud_linea_mm', 80)
        yc = p['largo_brazo'] + p.get('largo_entrada', 8) + 0.5 + ys                  # centro del 2.º dipolo
        pintar(ax, inf, '#7f9ed6', 0.55)
        pintar(ax, sup, '#c8892b', 0.95)
        ancho = max(2.4*p['largo_brazo'], 40)
        ax.set_xlim(yc - ancho/2, yc + ancho/2); ax.set_ylim(y0, y1); ax.set_aspect('equal')
        ax.set_title('un dipolo ampliado', loc='left', fontsize=10); ax.set_yticks([])
    fig.suptitle(f'Colineal de dipolos a {f_MHz:g} MHz (FR4 de 1,6 mm): formas de brazo · cara superior (vivo) en naranja, inferior (masa) en azul', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(salida, dpi=120)
    print(salida)


if __name__ == '__main__':
    main()
