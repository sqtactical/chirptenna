"""Simulación en un proceso aparte (la usa la interfaz para no bloquearse).

Uso: python -m antenas.simular_cli <trabajo.json>
El trabajo indica: clave, parametros, sustrato, f_obj_Hz, precision, ajustar (bool), salida (carpeta)
y, opcional, malla ('uniforme' o 'adaptada') y verificar_malla (bool: repite con el paso ×0,85 y ×1,15 y
guarda `verificacion_malla` en resultado.json).
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
        # con dos bandas la simulación cubre de 0,45 a 3,8 × f (como `ajustar`); sin ellas, de 0,6 a 1,4 ×
        multi = int(p.get('multibanda', 0) or 0) == 1
        rango = (0.45, 3.8) if multi else (0.6, 1.4)
        if trabajo.get('ajustar'):
            q, a, r, hist = simulacion.ajustar(clave, p, sus, f_obj, prec, progreso=progreso, malla=malla)
        else:
            q, hist = p, []
            a = tipos.generar(clave, p, sus)
            r = simulacion.simular(a, tipos.sustrato(sus), f_obj, prec, nf2ff=True, progreso=progreso, malla=malla,
                                   rango=rango, f_radiacion=f_obj if multi else None)
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
        if trabajo.get('verificar_malla'):
            # el resultado ya está calculado: si la verificación falla, no se pierde
            try:
                f_base = r['rango_Hz'][0]/rango[0]
                # con dos bandas se mira el S11 en las dos (la alta, fija en 2,4 GHz: ver antenas/bibanda.py)
                frecs = [f_base, 2441.75e6] if multi else [f_base]
                resumen['verificacion_malla'] = simulacion.verificar_malla(
                    a, tipos.sustrato(sus), r, frecs, prec, rango=rango, malla=malla, progreso=progreso, usar_f=not multi)
            except Exception as ex:
                resumen['verificacion_malla'] = {'error': f'{type(ex).__name__}: {ex}'}
                progreso(f'ERROR en la verificación de la malla: {ex}')
    except Exception as ex:
        resumen = {'ok': False, 'error': f'{type(ex).__name__}: {ex}', 'traza': traceback.format_exc()}
        progreso(f'ERROR {ex}')
    with open(os.path.join(salida, 'resultado.json'), 'w', encoding='utf-8') as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False, default=float)
    progreso('FIN')


if __name__ == '__main__':
    main()
