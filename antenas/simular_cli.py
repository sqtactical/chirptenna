"""Simulación en un proceso aparte (la usa la interfaz para no bloquearse).

Uso: python -m antenas.simular_cli <trabajo.json>
El trabajo indica: clave, parametros, sustrato, f_obj_Hz, precision, ajustar (bool), salida (carpeta)
y, opcional, malla ('uniforme' o 'adaptada').
Escribe en la salida resultado.json (resumen) y datos.npz (curvas y diagrama). Cada línea
que empieza por «PROGRESO» es un mensaje para el usuario.
"""
import os
import sys
import json
import traceback

import numpy as np


def progreso(msg):
    print(f'PROGRESO {msg}', flush=True)


def main():
    trabajo = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    from antenas import tipos, simulacion
    clave, p, sus = trabajo['clave'], trabajo['parametros'], trabajo['sustrato']
    f_obj, prec = trabajo['f_obj_Hz'], trabajo.get('precision', 'normal')
    malla = trabajo.get('malla', 'uniforme')
    salida = os.path.abspath(trabajo['salida'])   # openEMS cambia el directorio de trabajo al simular
    os.makedirs(salida, exist_ok=True)
    try:
        if trabajo.get('ajustar'):
            q, a, r, hist = simulacion.ajustar(clave, p, sus, f_obj, prec, progreso=progreso, malla=malla)
        else:
            q, hist = p, []
            a = tipos.generar(clave, p, sus)
            r = simulacion.simular(a, tipos.sustrato(sus), f_obj, prec, nf2ff=True, progreso=progreso, malla=malla)
        flo, fhi = r['banda_Hz']
        resumen = {
            'ok': True, 'clave': clave, 'parametros': q, 'historial': hist,
            'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2), 'criterio': r.get('criterio'),
            'banda_MHz': None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)],
            'ancho_banda_MHz': None if flo is None else round((fhi - flo)/1e6, 1),
            's11_min_dB': round(r['s11_min_dB'], 1), 'f_min_s11_MHz': round(r['f_min_s11_Hz']/1e6, 2),
            'directividad_dBi': round(r.get('directividad_dBi', float('nan')), 2),
            'ganancia_dBi': round(r.get('ganancia_dBi', float('nan')), 2),
            'eficiencia_radiacion_%': round(100*r.get('eficiencia_radiacion', float('nan')), 1),
            'eficiencia_total_%': round(100*r.get('eficiencia_total', float('nan')), 1),
            'direccion_max': r.get('direccion_max'), 'celdas': r['celdas'], 'paso_malla_mm': round(r['paso_malla_mm'], 3),
            'tiempo_s': r['tiempo_s'], 'avisos': r['avisos'], 'precision': prec, 'malla': malla,
        }
        np.savez_compressed(os.path.join(salida, 'datos.npz'), f=r['f_Hz'], s11=r['s11'], zin=r['zin'],
                            theta=r.get('theta', []), phi=r.get('phi', []),
                            d=r.get('directividad_dBi_grid', np.zeros((0, 0))))
    except Exception as ex:
        resumen = {'ok': False, 'error': f'{type(ex).__name__}: {ex}', 'traza': traceback.format_exc()}
        progreso(f'ERROR {ex}')
    with open(os.path.join(salida, 'resultado.json'), 'w', encoding='utf-8') as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False, default=float)
    progreso('FIN')


if __name__ == '__main__':
    main()
