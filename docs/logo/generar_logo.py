"""Logo de Chirptenna: un grillo visto desde arriba con las antenas en curva de Koch, del color del
cobre de una PCB (las antenas se dibujan con la misma `geometria.koch` que usa el generador).

Uso (desde la raíz del proyecto):  python docs/logo/generar_logo.py
-> docs/logo/chirptenna.svg / .png (icono) y chirptenna_texto.svg / .png (icono + nombre)
"""
import os
import sys
import math

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Polygon as MplPolygon, PathPatch
from matplotlib.path import Path

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))
from antenas import geometria as g   # noqa: E402

COBRE = '#c8892b'            # cobre de la PCB (el mismo tono que las vistas del programa)
VERDE = '#2f6b3a'
VERDE_CLARO = '#4f9a5c'
VERDE_OSCURO = '#1f4a28'
TEXTO = '#1f2a24'


def antena(lado):
    """Antena de grillo: arco de la cabeza hacia fuera y arriba, cada tramo una curva de Koch."""
    s = lado
    arco = [(s*0.12, 1.25), (s*0.75, 2.35), (s*1.55, 3.05), (s*2.55, 3.45)]
    pts = []
    for a, b in zip(arco, arco[1:]):
        # que las muescas apunten hacia fuera del cuerpo en las dos antenas
        tramo = g.koch(2, a, b, 60.0) if s > 0 else g.koch(2, b, a, 60.0)[::-1]
        pts.extend(tramo if not pts else tramo[1:])
    return np.array(pts)


def pata(ax, puntos, ancho):
    ax.plot(*np.array(puntos).T, color=VERDE_OSCURO, lw=ancho, solid_capstyle='round',
            solid_joinstyle='round', zorder=1)


def grillo(ax):
    # Antenas de Koch (cobre), rellenas como una pista del generador: con una línea gruesa los picos salían cortados
    for s in (1, -1):
        pista = g.engordar(antena(s), 0.085)
        for pol in g.poligonos(pista):
            ax.add_patch(MplPolygon(np.array(pol.exterior.coords), closed=True, color=COBRE, lw=0, zorder=2))
    # Patas: delanteras, medias y las traseras de salto (fémur grueso y tibia)
    for s in (1, -1):
        pata(ax, [(s*0.42, 0.45), (s*1.05, 0.95), (s*1.25, 1.45)], 6)
        pata(ax, [(s*0.5, 0.0), (s*1.25, -0.15), (s*1.6, 0.25)], 6)
        pata(ax, [(s*0.55, -0.55), (s*1.35, -1.25), (s*1.2, -2.55)], 12)    # fémur
        pata(ax, [(s*1.2, -2.55), (s*1.55, -3.35)], 5)                          # tibia
        pata(ax, [(s*0.18, -2.95), (s*0.42, -3.6)], 3.5)                         # cercos
    # Abdomen con las alas plegadas
    ax.add_patch(Ellipse((0, -1.45), 1.35, 2.75, color=VERDE, zorder=3))
    alas = Path([(0, -0.35), (0.62, -1.2), (0.38, -2.75), (0, -2.85), (-0.38, -2.75), (-0.62, -1.2), (0, -0.35)],
                [Path.MOVETO] + [Path.LINETO]*5 + [Path.CLOSEPOLY])
    ax.add_patch(PathPatch(alas, color=VERDE_CLARO, zorder=4))
    for y in (-1.05, -1.6, -2.15):           # nervios de las alas, como pistas
        ax.plot([-0.42, 0.42], [y, y], color=VERDE, lw=2.2, zorder=5)
    ax.plot([0, 0], [-0.4, -2.8], color=VERDE, lw=2.2, zorder=5)
    # Tórax (pronoto) y cabeza
    ax.add_patch(Ellipse((0, 0.35), 1.25, 0.95, color=VERDE_OSCURO, zorder=6))
    ax.add_patch(Circle((0, 1.05), 0.48, color=VERDE, zorder=7))
    for s in (1, -1):                          # ojos
        ax.add_patch(Circle((s*0.25, 1.2), 0.11, color=TEXTO, zorder=8))
        ax.add_patch(Circle((s*0.22, 1.24), 0.035, color='white', zorder=9))


def guardar(fig, nombre):
    for ext in ('svg', 'png'):
        fig.savefig(os.path.join(AQUI, f'{nombre}.{ext}'), transparent=True, dpi=200 if ext == 'png' else None)
    plt.close(fig)


def main():
    # Icono
    fig, ax = plt.subplots(figsize=(4, 4))
    grillo(ax)
    ax.set_xlim(-3.1, 3.1); ax.set_ylim(-3.9, 4.0); ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)
    guardar(fig, 'chirptenna')
    # Icono + nombre
    fig, ax = plt.subplots(figsize=(9, 3))
    grillo(ax)
    ax.text(3.6, 0.35, 'Chirp', color=TEXTO, fontsize=58, fontweight='bold', va='center', ha='left',
            family='DejaVu Sans')
    ax.text(3.6 + 6.05, 0.35, 'tenna', color=COBRE, fontsize=58, fontweight='bold', va='center', ha='left',
            family='DejaVu Sans')
    ax.text(3.65, -1.85, 'PCB antenna generator · openEMS · KiCad', color=VERDE, fontsize=15, va='center',
            ha='left', family='DejaVu Sans')
    ax.set_xlim(-3.1, 17.5); ax.set_ylim(-3.9, 4.0); ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)
    guardar(fig, 'chirptenna_texto')
    print('Logo guardado en', AQUI)


if __name__ == '__main__':
    main()
