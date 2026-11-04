"""Diagnóstico de la Yagi con boom que radia hacia atrás: dipolo + reflector solos (sin directores),
recto y de Koch, con el reflector actual (1,05 × el dipolo) y uno claramente largo (1,30 ×). Si el
reflector de 1,05 hace de director (por ir dimensionado con el largo físico del dipolo excitado, al que
el boom baja la resonancia un 13 %), el haz irá hacia −y con él y hacia +y con el de 1,30.

Una simulación por caso (sin ajuste), diagrama en la resonancia. Escribe salidas/_diag_yagi/diag.json.
Uso: python herramientas/diag_yagi_boom.py
"""
import os
import sys
import json

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from antenas import tipos, simulacion   # noqa: E402

F = 2441.75e6
SALIDA = os.path.join(RAIZ, 'salidas', '_diag_yagi')
os.makedirs(SALIDA, exist_ok=True)
res = {}
for it in (0, 2):
    for fr in (1.05, 1.30):
        x = {'iteracion': it, 'directores': 0, 'factor_reflector': fr}
        p = tipos.dimensionar('yagi_boom', F, x, fijos=tuple(x))
        p.pop('_aviso', None)
        a = tipos.generar('yagi_boom', p)
        nombre = f'it{it}_reflector{fr:.2f}'
        print('===', nombre, flush=True)
        r = simulacion.simular(a, tipos.sustrato(), F, 'normal', nf2ff=True, malla='adaptada',
                               progreso=lambda m: print('   ', m, flush=True))
        th, ph, d = r['theta'], r['phi'], r['directividad_dBi_grid']
        i90 = int(np.argmin(abs(th - 90)))
        g = lambda q: round(float(d[i90, int(np.argmin(abs(ph - q)))]), 1)
        res[nombre] = {'f_res_MHz': round(r['f_resonancia_Hz']/1e6, 1), 'S11_min_dB': round(r['s11_min_dB'], 1),
                       'D_mas_y_dBi': g(90), 'D_menos_y_dBi': g(270), 'G_dBi': round(r['ganancia_dBi'], 2),
                       'eficiencia_%': round(100*r['eficiencia_radiacion'], 1), 'direccion_max': r['direccion_max']}
        print('   →', res[nombre], flush=True)
        json.dump(res, open(os.path.join(SALIDA, 'diag.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
