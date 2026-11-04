"""Caracteriza un latiguillo coaxial con el extremo lejano al aire (OPEN).

Mide con una calibración guardada en el PC (por defecto la más reciente).
Calcula el retardo (para descontarlo después), la longitud eléctrica, el
factor de velocidad y la pérdida.

Uso: python medir_latiguillo.py <nombre> [longitud_fisica_mm] [calibracion]
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
import calibracion

C0 = 299792458.0
DIR_MEDIDAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas')
os.makedirs(DIR_MEDIDAS, exist_ok=True)


def main():
    nombre = sys.argv[1]
    l_fisica = float(sys.argv[2]) if len(sys.argv) > 2 and float(sys.argv[2]) > 0 else None
    nombre_cal = sys.argv[3] if len(sys.argv) > 3 else calibracion.listar()[-1]
    c = calibracion.Calibracion.cargar(nombre_cal)

    with nv.NanoVNA() as vna:
        f, s11, _ = c.medir(vna)
    ini, fin, pts = f[0], f[-1], len(f)
    cal = nombre_cal

    # Retardo de ida y vuelta: pendiente de la fase desenrollada (se ignora < 100 MHz)
    usar = f > 100e6
    fase = np.unwrap(np.angle(s11))
    pend, ordenada = np.polyfit(2*np.pi*f[usar], fase[usar], 1)
    tau_ida_vuelta = -pend
    tau = tau_ida_vuelta/2
    perdida_db = -20*np.log10(np.abs(s11))/2          # pérdida de un sentido
    res = {
        'latiguillo': nombre,
        'fecha': datetime.datetime.now().isoformat(timespec='seconds'),
        'calibracion': f'PC: {cal}',
        'barrido_MHz': [ini/1e6, fin/1e6, pts],
        'retardo_ps': round(tau*1e12, 1),
        'longitud_electrica_mm': round(tau*C0*1e3, 1),
        'perdida_1GHz_dB': round(float(np.interp(1e9, f, perdida_db)), 2),
        'perdida_2_4GHz_dB': round(float(np.interp(2.4e9, f, perdida_db)), 2),
        'residuo_fase_max_grados': round(float(np.degrees(np.max(np.abs(
            fase[usar] - (pend*2*np.pi*f[usar] + ordenada))))), 1),
    }
    if l_fisica:
        res['longitud_fisica_mm'] = l_fisica
        res['factor_velocidad'] = round(l_fisica/(tau*C0*1e3), 3)

    base = os.path.join(DIR_MEDIDAS, nombre)
    nv.guardar_s1p(base + '.s1p', f, s11, f'{nombre} (extremo al aire)\n{res["fecha"]}')
    with open(base + '.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4), tight_layout=True)
    a1.plot(f/1e9, np.degrees(fase), 'b.', ms=3, label='medida')
    a1.plot(f/1e9, np.degrees(pend*2*np.pi*f + ordenada), 'r-', lw=1, label=f'ajuste: τ={tau*1e12:.0f} ps')
    a1.set_xlabel('GHz'); a1.set_ylabel('Fase S11 desenrollada (°)'); a1.grid(); a1.legend()
    a2.plot(f/1e9, perdida_db, 'g-')
    a2.set_xlabel('GHz'); a2.set_ylabel('Pérdida en un sentido (dB)'); a2.grid()
    a2.set_title(nombre)
    fig.savefig(base + '.png', dpi=120)
    plt.close(fig)

    for k, v in res.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
