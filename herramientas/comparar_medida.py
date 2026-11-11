"""Compara el S11 simulado con el medido (NanoVNA u otro): frecuencia central, ancho de banda y mínimo.

Uso (desde la raíz):
    python herramientas/comparar_medida.py <simulado> <medida.s1p> [--banda ini_MHz fin_MHz]
                                           [--ventana ini_MHz fin_MHz] [--salida carpeta] [--nombre texto]

  simulado   carpeta con datos.npz (la de una simulación), un datos.npz o un .s1p
  medida     .s1p medido (Touchstone de 1 puerto; RI, MA o DB)
  --banda    banda objetivo (se sombrea en la gráfica); por defecto 2400–2483,5 MHz
  --ventana  rango de frecuencias donde buscar el mínimo (por defecto, todo el rango común de las dos curvas;
             pásalo si el barrido incluye otros mínimos lejos de la antena)
  --salida   carpeta de salida (por defecto, la carpeta de la medida)

Escribe <nombre>_comparacion.json y <nombre>_comparacion.png. La frecuencia central es el centro geométrico de la
banda a −10 dB (criterio del proyecto, lección 2); si la curva no baja de −10 dB, se usa el mínimo y se avisa.
Código de salida 0 si se pudo comparar.
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from antenas import ajuste  # noqa: E402  (leer_s1p)
from antenas.simulacion import centro_banda  # noqa: E402

UMBRAL_DB = -10.0


def leer_simulado(ruta):
    """(f_Hz, s11 complejo) de una carpeta con datos.npz, un .npz o un .s1p."""
    if os.path.isdir(ruta):
        ruta = os.path.join(ruta, 'datos.npz')
    if ruta.lower().endswith('.npz'):
        d = np.load(ruta)
        return np.asarray(d['f'], float), np.asarray(d['s11'])
    return ajuste.leer_s1p(open(ruta, encoding='utf-8-sig').read())


def metricas(f, s11, ventana_Hz):
    """Diccionario con los números de una curva (frecuencias en MHz)."""
    db = 20*np.log10(np.maximum(np.abs(s11), 1e-9))
    fc, flo, fhi, fmin, smin = centro_banda(f, db, UMBRAL_DB, ventana_Hz)
    hay_banda = flo is not None
    return {
        'f_centro_MHz': round(float(fc)/1e6, 2),
        'banda_MHz': [round(float(flo)/1e6, 2), round(float(fhi)/1e6, 2)] if hay_banda else None,
        'ancho_MHz': round(float(fhi - flo)/1e6, 2) if hay_banda else 0.0,
        'f_min_MHz': round(float(fmin)/1e6, 2),
        's11_min_dB': round(float(smin), 2),
        'llega_a_menos_10_dB': bool(hay_banda),
    }


def comparar(simulado, medida, banda=(2400.0, 2483.5), ventana=None, salida=None, nombre=None):
    fs, ss = leer_simulado(simulado)
    fm, sm = ajuste.leer_s1p(open(medida, encoding='utf-8-sig').read())
    lo, hi = max(fs.min(), fm.min()), min(fs.max(), fm.max())
    if hi <= lo:
        raise ValueError('Las curvas no comparten rango de frecuencias')
    v = (lo, hi) if ventana is None else (max(lo, ventana[0]*1e6), min(hi, ventana[1]*1e6))
    sim, med = metricas(fs, ss, v), metricas(fm, sm, v)
    r = {
        'simulado': os.path.abspath(simulado), 'medida': os.path.abspath(medida),
        'ventana_MHz': [round(v[0]/1e6, 1), round(v[1]/1e6, 1)],
        'f_centro_sim_MHz': sim['f_centro_MHz'], 'f_centro_med_MHz': med['f_centro_MHz'],
        'desviacion_f_pct': round(100*(med['f_centro_MHz'] - sim['f_centro_MHz'])/sim['f_centro_MHz'], 2),
        'ancho_sim_MHz': sim['ancho_MHz'], 'ancho_med_MHz': med['ancho_MHz'],
        's11_min_sim_dB': sim['s11_min_dB'], 's11_min_med_dB': med['s11_min_dB'],
        'f_min_sim_MHz': sim['f_min_MHz'], 'f_min_med_MHz': med['f_min_MHz'],
        'banda_sim_MHz': sim['banda_MHz'], 'banda_med_MHz': med['banda_MHz'],
        'avisos': [],
    }
    if sim['ancho_MHz'] > 0 and med['ancho_MHz'] > 0:
        r['desviacion_ancho_pct'] = round(100*(med['ancho_MHz'] - sim['ancho_MHz'])/sim['ancho_MHz'], 1)
    if not sim['llega_a_menos_10_dB']:
        r['avisos'].append('La simulación no baja de −10 dB en la ventana: el centro es el mínimo')
    if not med['llega_a_menos_10_dB']:
        r['avisos'].append('La medida no baja de −10 dB en la ventana: el centro es el mínimo')
    if (fm[1:] > fm[:-1]).all() and len(fm) < 50:
        r['avisos'].append('La medida tiene pocos puntos (%d): la frecuencia central tiene poca resolución' % len(fm))

    salida = salida or os.path.dirname(os.path.abspath(medida))
    os.makedirs(salida, exist_ok=True)
    nombre = nombre or os.path.splitext(os.path.basename(medida))[0]
    base = os.path.join(salida, nombre + '_comparacion')
    json.dump(r, open(base + '.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fig, ax = plt.subplots(figsize=(8, 4.5), tight_layout=True)
    ax.plot(fs/1e6, 20*np.log10(np.abs(ss)), label='Simulado', color='tab:blue')
    ax.plot(fm/1e6, 20*np.log10(np.abs(sm)), label='Medido', color='tab:red')
    ax.axhline(UMBRAL_DB, color='gray', ls='--', lw=0.8)
    if banda:
        ax.axvspan(banda[0], banda[1], color='orange', alpha=0.2, label='Banda objetivo')
    ax.axvline(r['f_centro_sim_MHz'], color='tab:blue', ls=':', lw=1)
    ax.axvline(r['f_centro_med_MHz'], color='tab:red', ls=':', lw=1)
    ax.set_xlim(v[0]/1e6, v[1]/1e6)
    ax.set_xlabel('Frecuencia (MHz)')
    ax.set_ylabel('|S11| (dB)')
    ax.set_title(f"{nombre}: centro sim {r['f_centro_sim_MHz']:.0f} MHz, med {r['f_centro_med_MHz']:.0f} MHz "
                 f"({r['desviacion_f_pct']:+.1f} %)")
    ax.grid(alpha=0.4)
    ax.legend()
    fig.savefig(base + '.png', dpi=120)
    plt.close(fig)
    r['_json'], r['_png'] = base + '.json', base + '.png'
    return r


def main():
    args = sys.argv[1:]
    opc = {}
    pos = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--banda', '--ventana'):
            opc[a[2:]] = (float(args[i + 1]), float(args[i + 2]))
            i += 2
        elif a in ('--salida', '--nombre'):
            opc[a[2:]] = args[i + 1]
            i += 1
        else:
            pos.append(a)
        i += 1
    if len(pos) != 2:
        print(__doc__)
        return 2
    r = comparar(pos[0], pos[1], banda=opc.get('banda', (2400.0, 2483.5)), ventana=opc.get('ventana'),
                 salida=opc.get('salida'), nombre=opc.get('nombre'))
    print(f"centro  simulado {r['f_centro_sim_MHz']} MHz | medido {r['f_centro_med_MHz']} MHz | "
          f"desviación {r['desviacion_f_pct']:+.2f} %")
    print(f"ancho   simulado {r['ancho_sim_MHz']} MHz | medido {r['ancho_med_MHz']} MHz")
    print(f"S11 min simulado {r['s11_min_sim_dB']} dB | medido {r['s11_min_med_dB']} dB")
    for a in r['avisos']:
        print('AVISO:', a)
    print('->', r['_png'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
