"""Espiral grande con una bobina en serie en el conector (24-11).

La espiral de radio ×1,9 (27,7 mm) da razón axial 0,9 dB pero queda reactiva (Z ≈ 40 − j52 Ω a 2,44 GHz). Aquí se simula una vez y se aplica por
circuito una L en serie (valores E24, con la Q de la bobina) a la impedancia simulada: S11 en la banda, L ideal y valores comerciales.

    python herramientas/espiral_l.py [radio_mm ...]      (por defecto 27,72)
Resultado en salidas/_espiral_l/resultado.json (+ .png).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from antenas import tipos, simulacion          # noqa: E402

F_OBJ = 2441.75e6
BANDA = (2400e6, 2483.5e6)
Q_BOBINA = 40.0
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]


def s11_con_l(f, zin, l_nh):
    z = zin + 1j*2*np.pi*f*l_nh*1e-9 + 2*np.pi*f*l_nh*1e-9/Q_BOBINA
    return 20*np.log10(np.abs((z - 50)/(z + 50)))


def main():
    radios = [float(a) for a in sys.argv[1:]] or [27.72]
    s = tipos.sustrato('FR4 JLC 1,6 mm')
    salida = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'salidas', '_espiral_l')
    os.makedirs(salida, exist_ok=True)
    resultados = []
    for radio in radios:
        p = tipos.dimensionar('espiral', F_OBJ)
        p.pop('_aviso', None)
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'salidas', '_barridos', 'FUNC_espiral', 'centrado.json')
        if os.path.exists(base):                    # el diseño centrado a 2,44 GHz del barrido (hueco y ancho de pista)
            p.update(json.load(open(base, encoding='utf-8-sig'))['parametros'])
        p['radio'] = radio
        a = tipos.generar('espiral', p)
        r = simulacion.simular(a, s, F_OBJ, 'normal', nf2ff=True, progreso=lambda m: None, paso=0.36, f_radiacion=F_OBJ)
        f, zin = np.asarray(r['f_Hz']), np.asarray(r['zin'], complex)
        k = int(np.argmin(np.abs(f - F_OBJ)))
        l_ideal = float(-zin[k].imag/(2*np.pi*F_OBJ)*1e9)
        en_banda = (f >= BANDA[0]) & (f <= BANDA[1])
        mejor = None
        for l in [0.0] + [v*10**e for e in (-1, 0) for v in E24 if 0.3 <= v*10**e <= 12]:
            peor = float(np.max(s11_con_l(f[en_banda], zin[en_banda], l)))
            if mejor is None or peor < mejor[1]:
                mejor = (l, peor)
        fila = {'radio_mm': radio, 'Z_obj': [round(float(zin[k].real), 1), round(float(zin[k].imag), 1)], 'L_ideal_nH': round(l_ideal, 2),
                'sin_L_peor_banda_dB': round(float(np.max(s11_con_l(f[en_banda], zin[en_banda], 0.0))), 1),
                'mejor_L_nH': mejor[0], 'con_L_peor_banda_dB': round(mejor[1], 1), 'f_res_MHz': round(r['f_resonancia_Hz']/1e6, 1),
                'barrido_L': {str(l): round(float(np.max(s11_con_l(f[en_banda], zin[en_banda], l))), 1) for l in (1.5, 2.2, 3.0, 3.3, 3.9, 4.7)}}
        for clave in ('directividad_dBi', 'ganancia_dBi', 'eficiencia_radiacion', 'ar_dB_theta0', 'ar_dB_max', 'pol_theta0', 'direccion_max'):
            if clave in r:
                fila[clave] = r[clave] if not isinstance(r[clave], np.generic) else float(r[clave])
        resultados.append(fila)
        print(json.dumps(fila, ensure_ascii=False, default=float), flush=True)
    json.dump(resultados, open(os.path.join(salida, 'resultado.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    main()
