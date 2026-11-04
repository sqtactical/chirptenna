"""Prueba A: dipolo de media onda en espacio libre frente a la teoría.

Un dipolo delgado resuena (Im{Zin} = 0) con una longitud de ~0,46-0,49 λ y
una resistencia de entrada de ~60-80 Ω. Si openEMS lo reproduce, el solver,
el mallado y el post-proceso están bien montados.
"""
import os
import sys
import time
import tempfile

import numpy as np
import matplotlib.pyplot as plt

import comun  # antes de openEMS
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0

L = 60.0     # longitud total del dipolo [mm]
w = 1.0      # ancho de la tira [mm] (radio equivalente w/4)
gap = 1.0    # hueco de alimentación [mm]
f0, fc = 2.4e9, 1.4e9
fino = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0  # factor de refinado de malla
sufijo = '' if fino == 1.0 else f'_x{fino:g}'

sim_path = os.path.join(tempfile.gettempdir(), 'fase0_dipolo' + sufijo)

FDTD = openEMS(NrTS=80000, EndCriteria=1e-5)
FDTD.SetGaussExcite(f0, fc)
FDTD.SetBoundaryCond(['PML_8']*6)

CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(1e-3)
res_aire = C0/(f0 + fc)/1e-3/20/fino
margen = 70.0

dip = CSX.AddMetal('dipolo')
dip.AddBox([-w/2, 0, gap/2], [w/2, 0, L/2], priority=10)
dip.AddBox([-w/2, 0, -L/2], [w/2, 0, -gap/2], priority=10)
FDTD.AddEdges2Grid(dirs='xz', properties=dip, metal_edge_res=0.5/fino)

port = FDTD.AddLumpedPort(1, 50, [-w/2, 0, -gap/2], [w/2, 0, gap/2], 'z', 1.0, priority=5)

mesh.AddLine('x', [-margen, 0, margen])
mesh.AddLine('y', [-margen, 0, margen])
mesh.AddLine('z', [-L/2 - margen, -gap/2, 0, gap/2, L/2 + margen])
mesh.SmoothMeshLines('all', res_aire, 1.3)

t0 = time.time()
FDTD.Run(sim_path, cleanup=True, verbose=0)
t_sim = time.time() - t0

f = np.linspace(1.0e9, 3.8e9, 1401)
port.CalcPort(sim_path, f)
zin = port.uf_tot/port.if_tot
s11_db = 20*np.log10(np.abs(port.uf_ref/port.uf_inc))

fr, rr = comun.cruce_reactancia(f, zin)
lam = C0/fr*1e3
l_lambda = L/lam
ok = (0.46 <= l_lambda <= 0.49) and (60 <= rr <= 80)

celdas = [len(mesh.GetLines(d)) for d in 'xyz']
resumen = {
    'prueba': 'Dipolo λ/2 en espacio libre',
    'L_mm': L, 'ancho_mm': w,
    'f_resonancia_GHz': round(fr/1e9, 4),
    'L_sobre_lambda': round(l_lambda, 4),
    'R_resonancia_ohm': round(float(rr), 1),
    'esperado': 'L/λ entre 0,46 y 0,49; R entre 60 y 80 Ω',
    'resultado': 'OK' if ok else 'FUERA DE RANGO',
    'refinado_malla': fino,
    'malla_celdas': celdas, 'tiempo_s': round(t_sim, 1),
}
comun.guardar_json(f'dipolo{sufijo}.json', resumen)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4), tight_layout=True)
a1.plot(f/1e9, np.real(zin), 'k-', label='Re{Zin}')
a1.plot(f/1e9, np.imag(zin), 'r--', label='Im{Zin}')
a1.axvline(fr/1e9, color='gray', lw=0.8)
a1.set_ylim(-300, 300); a1.set_xlabel('Frecuencia (GHz)'); a1.set_ylabel('Ω')
a1.set_title(f'Dipolo L={L:.0f} mm: resonancia {fr/1e9:.3f} GHz, R={rr:.1f} Ω')
a1.grid(); a1.legend()
a2.plot(f/1e9, s11_db, 'b-')
a2.set_xlabel('Frecuencia (GHz)'); a2.set_ylabel('|S11| (dB, ref. 50 Ω)'); a2.grid()
a2.set_title('S11')
comun.guardar_figura(fig, f'dipolo{sufijo}.png')

for k, v in resumen.items():
    print(f'{k}: {v}')
