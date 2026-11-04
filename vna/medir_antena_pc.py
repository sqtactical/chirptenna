"""Mide el S11 de una antena con una calibración guardada en el PC (no la del equipo).

Uso: python medir_antena_pc.py <nombre> [calibración] [--zoom MHz_ini MHz_fin]
Mide en todo el rango de la calibración (por defecto completa_50k_2700M) y guarda en medidas/:
<nombre>.s1p, <nombre>.json (bandas a −10 dB, mínimos, comprobación de |S11| ≤ 0 dB) y
<nombre>.png (S11 completo, zoom y resistencia/reactancia). La calibración.medir restaura el
barrido y el estado del equipo al terminar; no se envía «save».
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import nanovna as nv
import calibracion as cal

DIR_MEDIDAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas')


def bandas_bajo(f, db, umbral=-10.0):
    """Tramos contiguos con |S11| < umbral: [(f_ini, f_fin, f_min, s11_min)]."""
    out, i = [], 0
    while i < len(f):
        if db[i] < umbral:
            j = i
            while j + 1 < len(f) and db[j + 1] < umbral:
                j += 1
            k = i + int(np.argmin(db[i:j + 1]))
            out.append((f[i], f[j], f[k], float(db[k])))
            i = j + 1
        else:
            i += 1
    return out


def main():
    args = sys.argv[1:]
    zoom = None
    if '--zoom' in args:
        i = args.index('--zoom')
        zoom = (float(args[i + 1])*1e6, float(args[i + 2])*1e6)
        del args[i:i + 3]
    if not args:
        sys.exit(__doc__)
    nombre = args[0]
    nombre_cal = args[1] if len(args) > 1 else 'completa_50k_2700M'
    c = cal.Calibracion.cargar(nombre_cal)
    with nv.NanoVNA() as vna:
        f, s11, _ = c.medir(vna)
    db = 20*np.log10(np.abs(s11))
    z = 50*(1 + s11)/(1 - s11)
    os.makedirs(DIR_MEDIDAS, exist_ok=True)
    base = os.path.join(DIR_MEDIDAS, nombre)
    nv.guardar_s1p(base + '.s1p', f, s11, f'{nombre}, calibración del PC {nombre_cal}')
    bandas = bandas_bajo(f, db)
    resumen = {'nombre': nombre, 'calibracion': nombre_cal, 'puntos': len(f),
               'rango_MHz': [round(f[0]/1e6, 3), round(f[-1]/1e6, 1)],
               's11_max_dB': round(float(db.max()), 2),
               'aviso_calibracion': bool(db.max() > 0.5),
               'bandas_10dB_MHz': [{'inicio': round(a/1e6, 1), 'fin': round(b/1e6, 1), 'ancho': round((b - a)/1e6, 1),
                                    'f_min': round(m/1e6, 1), 's11_min_dB': round(s, 1)} for a, b, m, s in bandas]}
    json.dump(resumen, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    fig, ax = plt.subplots(3, 1, figsize=(10, 11))
    ax[0].plot(f/1e6, db); ax[0].set_title(f'{nombre}: S11 (calibración {nombre_cal})')
    zf = zoom or (max(f[0], 0.7*f[int(np.argmin(db))]), f[-1])
    m = (f >= zf[0]) & (f <= zf[1])
    ax[1].plot(f[m]/1e6, db[m]); ax[1].set_title('S11 (zoom)')
    for a in ax[:2]:
        a.axhline(-10, ls='--', c='gray'); a.set_ylabel('dB'); a.grid(True)
    ax[2].plot(f[m]/1e6, z[m].real, label='R'); ax[2].plot(f[m]/1e6, z[m].imag, label='X')
    ax[2].axhline(50, ls=':', c='gray'); ax[2].set_ylim(-150, 250); ax[2].legend(); ax[2].grid(True)
    ax[2].set_ylabel('Ω'); ax[2].set_xlabel('MHz')
    fig.tight_layout(); fig.savefig(base + '.png', dpi=100)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
