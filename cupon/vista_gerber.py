"""Dibuja un cupón a partir de sus Gerber/taladros (lo que recibe JLC), para revisarlo.

Uso: python vista_gerber.py [cupon_A|cupon_B]   ->  <cupón>/vista_gerber.png
"""
import os
import sys
import glob
import warnings

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'analisis'))
warnings.simplefilter('ignore')
import analizar_placas as ap   # noqa: E402
from gerbonara import ExcellonFile   # noqa: E402
from gerbonara.utils import MM   # noqa: E402

placa = sys.argv[1] if len(sys.argv) > 1 else 'cupon_A'
d = os.path.join(AQUI, placa, 'gerber')
sup, _, _ = ap.leer_cobre(glob.glob(os.path.join(d, '*F_Cu.gtl'))[0])
inf, _, _ = ap.leer_cobre(glob.glob(os.path.join(d, '*B_Cu.gbl'))[0])
fig, ax = plt.subplots(figsize=(9, 9), tight_layout=True)
for geom, color, alfa in ((inf, '#9db3e0', 0.5), (sup, '#c8892b', 0.95)):
    for p in ap.poligonos(geom):
        if p.area > 0:
            ax.add_patch(MplPolygon(np.array(p.exterior.coords), fc=color, ec='none', alpha=alfa))
            for hueco in p.interiors:
                ax.add_patch(MplPolygon(np.array(hueco.coords), fc='white', ec='none'))
for f in glob.glob(os.path.join(d, '*.drl')):
    for t in ExcellonFile.open(f).drills():
        ax.add_patch(plt.Circle((t.x, t.y), t.tool.diameter/2, color='k'))
ax.set_aspect('equal'); ax.autoscale(); ax.invert_yaxis() if False else None
ax.set_title(f'{placa} desde los Gerber\nmarrón: cobre superior · azul: masa inferior · negro: taladros')
ax.set_xlabel('mm (coordenadas Gerber)'); ax.set_ylabel('mm')
fig.savefig(os.path.join(AQUI, placa, 'vista_gerber.png'), dpi=110)
print('Área cobre superior', round(sup.area, 1), 'mm² | inferior', round(inf.area, 1), 'mm²')
