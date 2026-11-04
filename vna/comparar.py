"""Superpone varias medidas .s1p (|S11| y ROE).

Uso: python comparar.py <salida.png> <a.s1p> <b.s1p> ... [--banda ini_MHz fin_MHz]
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def leer_s1p(ruta):
    f, s = [], []
    with open(ruta, encoding='utf-8') as fh:
        for l in fh:
            if l.startswith(('!', '#')) or not l.strip():
                continue
            v = [float(x) for x in l.split()]
            f.append(v[0]); s.append(v[1] + 1j*v[2])
    return np.array(f), np.array(s)


def main():
    args = sys.argv[1:]
    banda = None
    if '--banda' in args:
        k = args.index('--banda')
        banda = (float(args[k + 1]), float(args[k + 2]))
        args = args[:k] + args[k + 3:]
    salida, ficheros = args[0], args[1:]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5), tight_layout=True)
    for ruta in ficheros:
        f, s = leer_s1p(ruta)
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        a1.plot(f/1e6, 20*np.log10(np.abs(s)), label=nombre)
        a2.plot(f/1e6, (1 + np.abs(s))/(1 - np.abs(s)), label=nombre)
    a1.axhline(-10, color='gray', ls='--', lw=0.8)
    a1.set_ylabel('|S11| (dB)'); a2.set_ylabel('ROE (VSWR)'); a2.set_ylim(1, 4)
    for ax in (a1, a2):
        if banda:
            ax.axvspan(*banda, color='orange', alpha=0.25)
        ax.set_xlabel('Frecuencia (MHz)'); ax.grid(); ax.legend()
    fig.savefig(salida, dpi=120)


if __name__ == '__main__':
    main()
