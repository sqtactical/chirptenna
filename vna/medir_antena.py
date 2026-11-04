"""Mide el S11 de una antena con el NanoVNA y genera informe.

Uso: python medir_antena.py <nombre> <f_inicio_MHz> <f_fin_MHz> [f_centro_banda_MHz f_ini_banda f_fin_banda]

Restaura siempre el barrido que tuviera configurado el equipo.
"""
import os
import sys
import json
import datetime

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import nanovna as nv

DIR_MEDIDAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas')
os.makedirs(DIR_MEDIDAS, exist_ok=True)


def carta_smith(ax):
    t = np.linspace(0, 2*np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), 'k-', lw=1)
    for r in [0.2, 0.5, 1, 2, 5]:
        c, rad = r/(1 + r), 1/(1 + r)
        ax.plot(c + rad*np.cos(t), rad*np.sin(t), color='0.8', lw=0.6)
    for x in [0.2, 0.5, 1, 2, 5]:
        for s in (1, -1):
            z = 1j*s*x + np.logspace(-3, 3, 400)
            g = (z - 1)/(z + 1)
            ax.plot(g.real, g.imag, color='0.8', lw=0.6)
    ax.axhline(0, color='0.8', lw=0.6)
    ax.set_aspect('equal'); ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05)
    ax.axis('off')


def main():
    nombre = sys.argv[1]
    f_ini, f_fin = float(sys.argv[2])*1e6, float(sys.argv[3])*1e6
    banda = [float(x)*1e6 for x in sys.argv[4:7]] if len(sys.argv) >= 7 else None

    with nv.NanoVNA() as vna:
        original = vna.barrido_actual()
        try:
            f, s11, _ = vna.medir(f_ini, f_fin, 101)
        finally:
            vna.fijar_barrido(*original)
        cal = vna.comando('cal')

    s11_db = 20*np.log10(np.abs(s11))
    roe = (1 + np.abs(s11))/(1 - np.abs(s11))
    z = 50*(1 + s11)/(1 - s11)

    i = int(np.argmin(s11_db))
    res = {'antena': nombre,
           'fecha': datetime.datetime.now().isoformat(timespec='seconds'),
           'barrido_MHz': [f_ini/1e6, f_fin/1e6, len(f)],
           'calibracion_equipo': cal,
           'f_min_S11_MHz': round(f[i]/1e6, 2),
           'S11_min_dB': round(float(s11_db[i]), 2),
           'ROE_min': round(float(roe[i]), 2),
           'Z_en_min_ohm': [round(float(z[i].real), 1), round(float(z[i].imag), 1)]}
    debajo = s11_db < -10
    if debajo[i]:
        lo, hi = i, i
        while lo > 0 and debajo[lo - 1]:
            lo -= 1
        while hi < len(f) - 1 and debajo[hi + 1]:
            hi += 1
        res['banda_-10dB_MHz'] = [round(float(f[lo])/1e6, 1), round(float(f[hi])/1e6, 1)]
        res['ancho_banda_-10dB_MHz'] = round(float(f[hi] - f[lo])/1e6, 1)
    else:
        res['banda_-10dB_MHz'] = None
    if banda:
        for etiqueta, fb in zip(['centro', 'inicio', 'fin'], banda):
            s = np.interp(fb, f, s11.real) + 1j*np.interp(fb, f, s11.imag)
            zb = 50*(1 + s)/(1 - s)
            res[f'en_{etiqueta}_{fb/1e6:g}MHz'] = {
                'S11_dB': round(float(20*np.log10(abs(s))), 2),
                'ROE': round(float((1 + abs(s))/(1 - abs(s))), 2),
                'Z_ohm': [round(float(zb.real), 1), round(float(zb.imag), 1)]}

    base = os.path.join(DIR_MEDIDAS, nombre)
    nv.guardar_s1p(base + '.s1p', f, s11, f'{nombre}\nNanoVNA, {res["fecha"]}')
    with open(base + '.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    fig = plt.figure(figsize=(13, 4.6), tight_layout=True)
    a1 = fig.add_subplot(1, 3, 1)
    a1.plot(f/1e6, s11_db, 'b-')
    a1.axhline(-10, color='gray', ls='--', lw=0.8)
    a1.set_xlabel('Frecuencia (MHz)'); a1.set_ylabel('|S11| (dB)'); a1.grid()
    a1.set_title(f'{nombre}: mínimo {f[i]/1e6:.1f} MHz, {s11_db[i]:.1f} dB')
    a2 = fig.add_subplot(1, 3, 2)
    a2.plot(f/1e6, roe, 'g-'); a2.set_ylim(1, 6)
    a2.set_xlabel('Frecuencia (MHz)'); a2.set_ylabel('ROE (VSWR)'); a2.grid()
    if banda:
        for ax in (a1, a2):
            ax.axvspan(banda[1]/1e6, banda[2]/1e6, color='orange', alpha=0.25)
    a3 = fig.add_subplot(1, 3, 3)
    carta_smith(a3)
    a3.plot(s11.real, s11.imag, 'b-')
    a3.plot(s11.real[i], s11.imag[i], 'ro')
    a3.set_title('Carta de Smith')
    fig.savefig(base + '.png', dpi=120)

    for k, v in res.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
