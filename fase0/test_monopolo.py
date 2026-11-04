"""Prueba B: monopolo impreso de 2,45 GHz en FR4 1,6 mm con ajuste automático.

Placa tipo JLC (FR4, εr 4,4, tanδ 0,02, 1,6 mm): plano de masa en la cara
inferior, línea microstrip de 50 Ω encima y, pasado el borde de masa, una tira
radiante. El programa estima la longitud con una fórmula sencilla, simula y
corrige la longitud (método de la secante) hasta centrar la banda a -10 dB en
la frecuencia objetivo. Al final calcula diagrama de radiación y eficiencia.
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
from openEMS.physical_constants import C0, EPS0

F_OBJ = 2.45e9
ER, TAND, H = 4.4, 0.02, 1.6     # FR4 genérico de JLC
W_PLACA, L_MASA = 40.0, 40.0     # [mm]
W_MONO = 2.0                     # ancho de la tira radiante [mm]
W_LINEA = comun.ancho_microstrip(50, ER, H)
TOLERANCIA = 0.01                # error relativo admitido en frecuencia
MAX_SIM = 5
fino = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

f0, fc = 2.4e9, 1.4e9
f = np.linspace(1.0e9, 3.8e9, 1401)


def simular(l_mono, nf2ff=False):
    """Simula la placa con una tira radiante de longitud l_mono [mm]."""
    sim_path = os.path.join(tempfile.gettempdir(), f'fase0_monopolo_{l_mono:.3f}')
    FDTD = openEMS(NrTS=80000, EndCriteria=1e-5)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    res_aire = C0/(f0 + fc)/1e-3/20/fino
    res_placa = res_aire/np.sqrt((ER + 1)/2)
    margen = 70.0

    l_placa = L_MASA + l_mono + 5.0
    kappa = 2*np.pi*f0*EPS0*ER*TAND
    sustrato = CSX.AddMaterial('FR4', epsilon=ER, kappa=kappa)
    sustrato.AddBox([-W_PLACA/2, 0, 0], [W_PLACA/2, l_placa, H], priority=0)

    masa = CSX.AddMetal('masa')
    masa.AddBox([-W_PLACA/2, 0, 0], [W_PLACA/2, L_MASA, 0], priority=10)
    cobre = CSX.AddMetal('cobre_sup')
    cobre.AddBox([-W_LINEA/2, 0, H], [W_LINEA/2, L_MASA, H], priority=10)
    cobre.AddBox([-W_MONO/2, L_MASA, H], [W_MONO/2, L_MASA + l_mono, H], priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=[masa, cobre], metal_edge_res=0.5/fino)

    port = FDTD.AddLumpedPort(1, 50, [-W_LINEA/2, 0, 0], [W_LINEA/2, 0, H], 'z', 1.0, priority=5)

    mesh.AddLine('x', [-W_PLACA/2 - margen, -W_PLACA/2, 0, W_PLACA/2, W_PLACA/2 + margen])
    mesh.AddLine('y', [-margen, 0, l_placa, l_placa + margen])
    mesh.AddLine('z', np.linspace(0, H, 5))
    mesh.AddLine('z', [-margen, H + margen])
    mesh.SmoothMeshLines('all', res_placa, 1.3)

    caja = FDTD.CreateNF2FFBox() if nf2ff else None

    # Caché: si ya hay resultados de esta geometría no se vuelve a simular
    necesarios = ['port_ut_1', 'port_it_1'] + (['nf2ff_E_0.h5'] if nf2ff else [])
    t0 = time.time()
    if all(os.path.exists(os.path.join(sim_path, n)) for n in necesarios):
        cache = True
    else:
        cache = False
        FDTD.Run(sim_path, cleanup=True, verbose=0)
    t_sim = time.time() - t0

    port.CalcPort(sim_path, f)
    s11_db = 20*np.log10(np.abs(port.uf_ref/port.uf_inc))
    zin = port.uf_tot/port.if_tot
    # Impedancia en los terminales de la antena (sin los L_MASA mm de microstrip)
    eps_eff = comun.eps_eff_microstrip(ER, H, W_LINEA)
    z_ant = comun.quitar_linea(f, zin, 50.0, eps_eff, L_MASA*1e-3)
    banda = (f > 0.6*F_OBJ) & (f < 1.4*F_OBJ)
    f_x0, r_x0 = comun.cruce_reactancia(f[banda], z_ant[banda])
    f_min, s11_min = comun.minimo_s11(f[banda], s11_db[banda])
    f_centro = comun.centro_banda(f, s11_db)
    out = {'l_mono_mm': round(l_mono, 3),
           'f_resonancia_GHz': None if f_x0 is None else round(f_x0/1e9, 4),
           'R_resonancia_ohm': None if r_x0 is None else round(float(r_x0), 1),
           'f_centro_banda_GHz': None if f_centro is None else round(f_centro/1e9, 4),
           'f_min_S11_GHz': round(f_min/1e9, 4),
           'S11_min_dB': round(float(s11_min), 1),
           'tiempo_s': None if cache else round(t_sim, 1),
           'celdas': [len(mesh.GetLines(d)) for d in 'xyz'],
           '_s11_db': s11_db, '_z_ant': z_ant,
           # Criterio de ajuste: centrar la banda a -10 dB en el objetivo. Con
           # planos de masa pequeños la curva tiene varios mínimos y el mínimo
           # de S11 (o Im{Zin}=0) salta entre modos; el centro de banda no.
           '_fr': f_centro if f_centro is not None else f_min}
    bw = comun.ancho_banda(f, s11_db)
    out['banda_-10dB_GHz'] = None if bw is None else [round(bw[0]/1e9, 3), round(bw[1]/1e9, 3)]

    if nf2ff:
        theta = np.arange(0, 361, 2.0)
        phi = [0.0, 90.0]
        centro = [0, L_MASA*1e-3, H/2*1e-3]   # en metros, no en unidades de malla
        r = caja.CalcNF2FF(sim_path, F_OBJ, theta, phi, center=centro)
        port.CalcPort(sim_path, [F_OBJ])
        p_acc, p_inc = float(port.P_acc[0]), float(port.P_inc[0])
        prad = float(r.Prad[0])
        out['directividad_dBi'] = round(10*np.log10(r.Dmax[0]), 2)
        out['eficiencia_radiacion_%'] = round(100*prad/p_acc, 1)
        out['eficiencia_total_%'] = round(100*prad/p_inc, 1)
        out['ganancia_dBi'] = round(10*np.log10(r.Dmax[0]*prad/p_acc), 2)
        out['_patron'] = (theta, 20*np.log10(r.E_norm[0]/np.max(r.E_norm[0])) + 10*np.log10(r.Dmax[0]))
    return out


def main():
    # Estimación inicial: λ/4 con εeff ≈ (εr+1)/2 (tira impresa sobre sustrato en aire)
    l_est = C0/(4*F_OBJ*np.sqrt((ER + 1)/2))*1e3
    print(f'Línea 50 Ω: {W_LINEA:.2f} mm | longitud estimada de la tira: {l_est:.2f} mm')

    historial = []
    l = l_est
    for n in range(MAX_SIM):
        r = simular(l)
        historial.append(r)
        err = (r['_fr'] - F_OBJ)/F_OBJ
        print(f'  sim {n+1}: L={l:.3f} mm -> centro banda={r["_fr"]/1e9:.4f} GHz '
              f'({100*err:+.2f} %), banda={r["banda_-10dB_GHz"]}, '
              f'S11min={r["S11_min_dB"]} dB, {r["tiempo_s"]} s', flush=True)
        if abs(err) < TOLERANCIA:
            break
        if len(historial) == 1:
            l = l*r['_fr']/F_OBJ      # primer paso: escalado proporcional
        else:
            a, b = historial[-2], historial[-1]
            pend = (b['_fr'] - a['_fr'])/(b['l_mono_mm'] - a['l_mono_mm'])
            l = b['l_mono_mm'] + (F_OBJ - b['_fr'])/pend

    final = simular(historial[-1]['l_mono_mm'], nf2ff=True)

    fig, ax = plt.subplots(figsize=(8, 4.5), tight_layout=True)
    for i, r in enumerate(historial):
        ax.plot(f/1e9, r['_s11_db'], lw=1.2, label=f'sim {i+1}: L={r["l_mono_mm"]:.2f} mm')
    ax.axvline(F_OBJ/1e9, color='k', ls=':', lw=1)
    ax.axhline(-10, color='gray', ls='--', lw=0.8)
    ax.set_xlabel('Frecuencia (GHz)'); ax.set_ylabel('|S11| (dB)')
    ax.set_title('Monopolo impreso FR4 1,6 mm: ajuste automático a 2,45 GHz')
    ax.grid(); ax.legend()
    comun.guardar_figura(fig, 'monopolo_s11.png')

    theta, patron = final['_patron']
    fig = plt.figure(figsize=(9, 4.5), tight_layout=True)
    for k, nombre in enumerate(['Plano XZ (φ=0°, transversal a la tira)', 'Plano YZ (φ=90°, a lo largo de la tira)']):
        ax = fig.add_subplot(1, 2, k + 1, projection='polar')
        ax.plot(np.deg2rad(theta), np.maximum(patron[:, k], -30), 'b-')
        ax.set_rlim(-30, max(5, np.ceil(patron.max()))); ax.set_title(nombre, fontsize=9)
    fig.suptitle(f'Directividad (dBi) a {F_OBJ/1e9:.2f} GHz')
    comun.guardar_figura(fig, 'monopolo_patron.png')

    limpiar = lambda r: {k: v for k, v in r.items() if not k.startswith('_')}
    resumen = {
        'prueba': 'Monopolo impreso FR4 1,6 mm, ajuste automático',
        'f_objetivo_GHz': F_OBJ/1e9, 'er': ER, 'tand': TAND, 'h_mm': H,
        'placa_mm': [W_PLACA, round(L_MASA + final['l_mono_mm'] + 5, 2)],
        'ancho_linea_50ohm_mm': round(W_LINEA, 3),
        'l_estimada_mm': round(l_est, 3),
        'iteraciones': [limpiar(r) for r in historial],
        'final': limpiar(final),
        'resultado': 'OK' if abs(final['_fr'] - F_OBJ)/F_OBJ < TOLERANCIA else 'NO CONVERGE',
    }
    comun.guardar_json('monopolo.json', resumen)
    for k, v in limpiar(final).items():
        print(f'{k}: {v}')
    print('resultado:', resumen['resultado'])


if __name__ == '__main__':
    main()
