"""Mide una pista abierta de PCB alimentada por un latiguillo y busca sus resonancias.

Descuenta el retardo del latiguillo (medido antes con medir_latiguillo.py) y
localiza dónde la fase de S11 cruza múltiplos de -180°:
  -180°, -540°, ... -> resonancias λ/4, 3λ/4, ... (la pista se ve como un corto)
  -360°, -720°, ... -> resonancias λ/2, λ, ...   (la pista se ve como un abierto)
Con la longitud física da una εeff aproximada. La εr buena saldrá de ajustar la
simulación de la geometría real a esta medida.

Uso: python medir_linea.py <nombre> <latiguillo> <longitud_pista_mm> [calibracion]
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
from medir_antena import carta_smith

C0 = 299792458.0
DIR_MEDIDAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas')


def cruces(f, fase_grados):
    """Frecuencias donde la fase desenrollada cruza múltiplos de -180°."""
    out = []
    for k in range(1, int(-fase_grados.min()//180) + 1):
        obj = -180.0*k
        i = np.where((fase_grados[:-1] > obj) & (fase_grados[1:] <= obj))[0]
        if len(i):
            i = i[0]
            t = (obj - fase_grados[i])/(fase_grados[i + 1] - fase_grados[i])
            out.append((k, f[i] + t*(f[i + 1] - f[i])))
    return out


def main():
    nombre, latiguillo, l_pista = sys.argv[1], sys.argv[2], float(sys.argv[3])
    nombre_cal = sys.argv[4] if len(sys.argv) > 4 else calibracion.listar()[-1]
    tau = json.load(open(os.path.join(DIR_MEDIDAS, latiguillo + '.json'), encoding='utf-8'))['retardo_ps']*1e-12
    c = calibracion.Calibracion.cargar(nombre_cal)

    with nv.NanoVNA() as vna:
        f, s11_med, _ = c.medir(vna)
    s11 = s11_med*np.exp(1j*2*np.pi*f*2*tau)        # plano de referencia en la soldadura
    fase = np.degrees(np.unwrap(np.angle(s11)))
    s11_db = 20*np.log10(np.abs(s11))

    resonancias = []
    for k, fr in cruces(f, fase):
        tipo = 'λ/4 impar (corto)' if k % 2 else 'λ/2 (abierto)'
        # fase -180·k  <=>  longitud eléctrica k·λ/4
        eps_eff = (k*C0/(4*fr*l_pista*1e-3))**2
        resonancias.append({'orden_cuartos_onda': k, 'tipo': tipo,
                            'f_MHz': round(fr/1e6, 2), 'eps_eff_aprox': round(eps_eff, 3)})

    res = {'medida': nombre, 'fecha': datetime.datetime.now().isoformat(timespec='seconds'),
           'calibracion': nombre_cal, 'latiguillo': latiguillo, 'retardo_descontado_ps': round(tau*1e12, 1),
           'longitud_pista_mm': l_pista, 'resonancias': resonancias}
    os.makedirs(DIR_MEDIDAS, exist_ok=True)
    base = os.path.join(DIR_MEDIDAS, nombre)
    nv.guardar_s1p(base + '.s1p', f, s11_med, f'{nombre} (sin descontar el latiguillo)\n{res["fecha"]}')
    with open(base + '.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    fig = plt.figure(figsize=(14, 4.6), tight_layout=True)
    a1 = fig.add_subplot(1, 3, 1)
    a1.plot(f/1e9, s11_db, 'b-'); a1.set_xlabel('GHz'); a1.set_ylabel('|S11| (dB)'); a1.grid()
    a1.set_title(nombre)
    a2 = fig.add_subplot(1, 3, 2)
    a2.plot(f/1e9, fase, 'k-'); a2.set_xlabel('GHz'); a2.set_ylabel('Fase S11 sin latiguillo (°)'); a2.grid()
    for r in resonancias:
        for ax in (a1, a2):
            ax.axvline(r['f_MHz']/1e3, color='r' if r['orden_cuartos_onda'] % 2 else 'g', lw=0.8, ls='--')
    a3 = fig.add_subplot(1, 3, 3)
    carta_smith(a3); a3.plot(s11.real, s11.imag, 'b-', lw=0.8); a3.set_title('Smith (sin latiguillo)')
    fig.savefig(base + '.png', dpi=120)
    plt.close(fig)

    for k, v in res.items():
        if k != 'resonancias':
            print(f'{k}: {v}')
    for r in resonancias:
        print(f"  {r['orden_cuartos_onda']}·λ/4  {r['f_MHz']:8.2f} MHz  {r['tipo']:18s} εeff≈{r['eps_eff_aprox']}")


if __name__ == '__main__':
    main()
