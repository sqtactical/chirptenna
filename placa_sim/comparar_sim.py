"""Compara S11 simulado de la placa con el medido y estima el factor de escala en frecuencia.

Si la εr real difiere de la simulada, los rasgos del S11 aparecen desplazados:
medida(f) ≈ simulación(f·s). Se busca la s que mejor alinea las curvas (|S11| en
dB recortado a −30 dB) en la banda indicada. Con dos simulaciones a εr distintas
se interpola la εr que da s = 1.

Uso: python comparar_sim.py <medida.s1p> <retardo_latiguillo_ps> <sim1.s1p> [<sim2.s1p> ...]
                            [--banda 250 1450] [--salida comparacion.png]
"""
import os
import re
import sys
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'vna'))
from comparar import leer_s1p   # noqa: E402

RECORTE_DB = -30.0


def db(s):
    return np.maximum(20*np.log10(np.abs(s)), RECORTE_DB)


def mejor_escala(f_med, y_med, f_sim, y_sim, banda, escalas=np.linspace(0.80, 1.20, 801)):
    m = (f_med >= banda[0]) & (f_med <= banda[1])
    fm, ym = f_med[m], y_med[m] - y_med[m].mean()
    errores = []
    for s in escalas:
        ys = np.interp(fm*s, f_sim, y_sim, left=np.nan, right=np.nan)
        ok = ~np.isnan(ys)
        if ok.mean() < 0.9:
            errores.append(np.inf)
            continue
        ys = ys[ok] - ys[ok].mean()
        errores.append(np.sqrt(np.mean((ys - ym[ok])**2)))
    errores = np.array(errores)
    i = int(np.argmin(errores))
    return escalas[i], errores[i], escalas, errores


def er_de_nombre(ruta):
    m = re.search(r'_er([0-9.]+)_', os.path.basename(ruta))
    return float(m.group(1)) if m else None


def main():
    args = sys.argv[1:]
    banda = (250e6, 1450e6)
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados', 'comparacion.png')
    if '--banda' in args:
        k = args.index('--banda'); banda = (float(args[k + 1])*1e6, float(args[k + 2])*1e6); args = args[:k] + args[k + 3:]
    if '--salida' in args:
        k = args.index('--salida'); salida = args[k + 1]; args = args[:k] + args[k + 2:]
    medida, tau, sims = args[0], float(args[1])*1e-12, args[2:]

    f_med, s_med = leer_s1p(medida)
    s_med = s_med*np.exp(1j*2*np.pi*f_med*2*tau)   # quitar el latiguillo
    y_med = db(s_med)

    fig, axs = plt.subplots(len(sims) + 1, 1, figsize=(12, 3.2*(len(sims) + 1)), tight_layout=True)
    resultados = []
    for ax, ruta in zip(axs, sims):
        f_sim, s_sim = leer_s1p(ruta)
        y_sim = db(s_sim)
        s, err, escalas, errores = mejor_escala(f_med, y_med, f_sim, y_sim, banda)
        er = er_de_nombre(ruta)
        resultados.append({'simulacion': os.path.basename(ruta), 'er_simulada': er,
                           'escala_s': round(float(s), 4), 'error_rms_dB': round(float(err), 2)})
        ax.plot(f_med/1e6, y_med, 'k-', lw=1.2, label='medida (sin latiguillo)')
        ax.plot(f_sim/1e6, y_sim, 'b-', lw=0.8, alpha=0.6, label=f'simulación εr={er}')
        ax.plot(f_sim/s/1e6, y_sim, 'r-', lw=0.9, label=f'simulación desplazada ×1/{s:.3f}')
        ax.axvspan(banda[0]/1e6, banda[1]/1e6, color='orange', alpha=0.08)
        ax.set_xlim(f_med[0]/1e6, min(f_med[-1], f_sim[-1]/0.9)/1e6)
        ax.set_ylabel('|S11| (dB)'); ax.grid(); ax.legend(fontsize=8)
        axs[-1].plot(escalas, errores, label=f'εr={er}')
    axs[-1].set_xlabel('escala s'); axs[-1].set_ylabel('error rms (dB)'); axs[-1].grid(); axs[-1].legend()

    # εr que daría s = 1, interpolando en s² (≈ εeff_real/εeff_sim)
    est = None
    if len(resultados) >= 2:
        er_ = np.array([r['er_simulada'] for r in resultados])
        s2 = np.array([r['escala_s']**2 for r in resultados])
        p = np.polyfit(er_, s2, 1)
        est = float((1 - p[1])/p[0])
    elif len(resultados) == 1 and resultados[0]['er_simulada']:
        # Aproximación con una sola simulación: εeff ∝ εr (cota alta del desplazamiento)
        r = resultados[0]
        est = r['er_simulada']*r['escala_s']**2
    fig.suptitle(f'Medida frente a simulación — εr estimada ≈ {est:.2f}' if est else 'Medida frente a simulación')
    fig.savefig(salida, dpi=110)
    plt.close(fig)
    out = {'medida': os.path.basename(medida), 'banda_MHz': [banda[0]/1e6, banda[1]/1e6],
           'simulaciones': resultados, 'er_estimada': None if est is None else round(est, 3)}
    with open(os.path.splitext(salida)[0] + '.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
