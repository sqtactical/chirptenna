"""Mide S11 y S21 de un dispositivo de dos puertos (anillo del cupón A/B, línea) con una calibración del PC.

Uso: python medir_s21_pc.py <nombre> <calibración> [--zoom MHz_ini MHz_fin]
La calibración debe tener THRU (S21 corregido). Sin aislamiento el suelo de S21 es ~ −50 dB (ver
`calibrar_pc.py verificar`): sirve para picos de anillo (−15…−30 dB), no para medir acoplos < −45 dB.
Puerto 1 = CH0 (S11 y S21), puerto 2 = CH1. Solo se mide S11 y S21: en el `.s2p` S12 = S21 (reciprocidad
supuesta) y S22 = 0 (no medido). Guarda en medidas/ `<nombre>.s2p`, `.json` (picos de S21) y `.png`.
Restaura el barrido y el estado del equipo; no se envía «save».
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


def escribir_s2p(ruta, f, s11, s21, comentario=''):
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write(f'! {comentario}\n! S12 = S21 (reciprocidad supuesta); S22 no medido (0)\n# Hz S RI R 50\n')
        for fi, a, b in zip(f, s11, s21):
            fh.write(f'{fi:.1f} {a.real:.8f} {a.imag:.8f} {b.real:.8f} {b.imag:.8f} '
                     f'{b.real:.8f} {b.imag:.8f} 0 0\n')


def picos(f, db, prominencia=3.0, n=6):
    """Máximos locales de S21 (dB) con prominencia ≥ `prominencia` dB sobre la mediana del entorno."""
    out = []
    for i in range(2, len(f) - 2):
        if db[i] >= db[i - 1] and db[i] > db[i + 1] and db[i] > db[i - 2] and db[i] > db[i + 2]:
            ref = float(np.median(db[max(0, i - 40):i + 40]))
            if db[i] - ref >= prominencia:
                out.append((float(db[i]), float(f[i])))
    out.sort(reverse=True)
    return [{'f_MHz': round(fi/1e6, 2), 'S21_dB': round(d, 1)} for d, fi in out[:n]]


def main():
    args = sys.argv[1:]
    zoom = None
    if '--zoom' in args:
        i = args.index('--zoom')
        zoom = (float(args[i + 1])*1e6, float(args[i + 2])*1e6)
        del args[i:i + 3]
    if len(args) < 2:
        sys.exit(__doc__)
    nombre, nombre_cal = args[0], args[1]
    c = cal.Calibracion.cargar(nombre_cal)
    if c.et is None:
        sys.exit('Esta calibración no tiene THRU: no hay S21 corregido.')
    with nv.NanoVNA() as vna:
        f, s11, s21 = c.medir(vna)
    db21 = 20*np.log10(np.maximum(np.abs(s21), 1e-9))
    db11 = 20*np.log10(np.abs(s11))
    os.makedirs(DIR_MEDIDAS, exist_ok=True)
    base = os.path.join(DIR_MEDIDAS, nombre)
    escribir_s2p(base + '.s2p', f, s11, s21, f'{nombre}, calibración del PC {nombre_cal}')
    resumen = {'nombre': nombre, 'calibracion': nombre_cal, 'puntos': len(f),
               's21_max_dB': round(float(db21.max()), 1), 's21_mediana_dB': round(float(np.median(db21)), 1),
               's11_max_dB': round(float(db11.max()), 2), 'picos_s21': picos(f, db21)}
    json.dump(resumen, open(base + '.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    zf = zoom or (f[0], f[-1])
    m = (f >= zf[0]) & (f <= zf[1])
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    ax[0].plot(f[m]/1e6, db21[m]); ax[0].set_ylabel('|S21| dB'); ax[0].set_title(f'{nombre} (calibración {nombre_cal})')
    ax[1].plot(f[m]/1e6, db11[m]); ax[1].set_ylabel('|S11| dB'); ax[1].set_xlabel('MHz')
    for a in ax:
        a.grid(True)
    fig.tight_layout(); fig.savefig(base + '.png', dpi=100)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
