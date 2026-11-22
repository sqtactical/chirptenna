"""Simulación en un proceso aparte (la usa la interfaz para no bloquearse).

Uso: python -m antenas.simular_cli <trabajo.json>
El trabajo indica: clave, parametros, sustrato, f_obj_Hz, precision, ajustar (bool), salida (carpeta)
y, opcional, motor ('openems' por defecto, 'matlab' o 'ambos': openEMS y después MATLAB con la antena ajustada; ver `simular_matlab`),
malla ('uniforme' o 'adaptada') y verificar_malla (bool: repite con el paso ×0,85 y ×1,15 y
guarda `verificacion_malla` en resultado.json) y entorno (lista de predefinidos de `entorno.PREDEFINIDOS`: carcasa, bateria, mano;
guarda `entorno` con el cambio de frecuencia y de eficiencia) y tolerancias (bool, con `banda_MHz` = [inf, sup]: 6 simulaciones más con
εr ±5 %, grosor ±10 % y cobre ±0,05 mm; guarda `tolerancias`).
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


def _num(x, decimales, factor=1):
    """Número redondeado, o None si falta (MATLAB no da ganancia ni eficiencia): el JSON no lleva NaN."""
    if x is None or x != x:
        return None
    return round(factor*x, decimales)


def main():
    trabajo = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    from antenas import tipos, simulacion
    from antenas.i18n import tr
    clave, p, sus = trabajo['clave'], trabajo['parametros'], trabajo['sustrato']
    f_obj, prec = trabajo['f_obj_Hz'], trabajo.get('precision', 'normal')
    malla = trabajo.get('malla', 'uniforme')
    salida = os.path.abspath(trabajo['salida'])   # openEMS cambia el directorio de trabajo al simular
    os.makedirs(salida, exist_ok=True)
    motor = trabajo.get('motor', 'openems')                # 'openems', 'matlab' o 'ambos' (openEMS y luego MATLAB con la antena resultante)
    caja = trabajo.get('carcasa') if motor != 'matlab' else None      # carcasa del diseño: se simula y se ajusta DENTRO de ella
    try:
        if caja:
            from antenas import carcasa
            motivo = carcasa.no_soporta(tipos.generar(clave, p, sus))
            if motivo:
                raise ValueError(motivo)
            simulacion.ENTORNO_FIJO = lambda ant, h, f: carcasa.bloques(ant, h, caja, f)
            progreso(tr('Con la carcasa del diseño ({0}, pared de {1:g} mm): se ajusta con ella puesta.', caja.get('material', 'PLA'), caja.get('pared', 1.6)))
        # con dos bandas la simulación cubre de 0,45 a 3,8 × f (como `ajustar`); sin ellas, de 0,6 a 1,4 ×
        multi = int(p.get('multibanda', 0) or 0) == 1
        rango = (0.45, 3.8) if multi else (0.6, 1.4)
        if motor == 'matlab':
            from antenas import simular_matlab
            if trabajo.get('ajustar'):
                progreso(tr('El ajuste automático solo existe con openEMS: se simula el diseño tal cual.'))
            q, hist = p, []
            a = tipos.generar(clave, p, sus)
            r = simular_matlab.simular(a, tipos.sustrato(sus), f_obj, rango=rango, progreso=progreso)
        elif trabajo.get('ajustar'):
            q, a, r, hist = simulacion.ajustar(clave, p, sus, f_obj, prec, progreso=progreso, malla=malla)
        else:
            q, hist = p, []
            a = tipos.generar(clave, p, sus)
            r = simulacion.simular(a, tipos.sustrato(sus), f_obj, prec, nf2ff=True, progreso=progreso, malla=malla,
                                   rango=rango, f_radiacion=f_obj if multi else None)
        flo, fhi = r['banda_Hz']
        extra = {}
        resumen_matlab = None
        if motor == 'ambos':
            # MATLAB simula la antena ya ajustada por openEMS; si falla, el resultado de openEMS no se pierde
            try:
                from antenas import simular_matlab
                rm = simular_matlab.simular(a, tipos.sustrato(sus), f_obj, rango=rango, progreso=progreso)
                resumen_matlab = simular_matlab.resumen(rm)
                extra = {'f_matlab': rm['f_Hz'], 's11_matlab': rm['s11'], 'zin_matlab': rm['zin']}
                if 'directividad_dBi_grid' in rm:
                    extra['d_matlab'] = rm['directividad_dBi_grid']
            except Exception as ex:
                resumen_matlab = {'error': f'{type(ex).__name__}: {ex}'}
                progreso(f'ERROR en la simulación de MATLAB: {ex}')
        resumen = {
            'ok': True, 'clave': clave, 'parametros': q, 'historial': hist, 'motor': motor,
            'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2), 'criterio': r.get('criterio'),
            'banda_MHz': None if flo is None else [round(flo/1e6, 1), round(fhi/1e6, 1)],
            'ancho_banda_MHz': None if flo is None else round((fhi - flo)/1e6, 1),
            's11_min_dB': round(r['s11_min_dB'], 1), 'f_min_s11_MHz': round(r['f_min_s11_Hz']/1e6, 2),
            'directividad_dBi': _num(r.get('directividad_dBi'), 2),
            'ganancia_dBi': _num(r.get('ganancia_dBi'), 2),
            'eficiencia_radiacion_%': _num(r.get('eficiencia_radiacion'), 1, 100),
            'eficiencia_total_%': _num(r.get('eficiencia_total'), 1, 100),
            'direccion_max': r.get('direccion_max'), 'celdas': r['celdas'], 'paso_malla_mm': round(r['paso_malla_mm'], 3),
            'tiempo_s': r['tiempo_s'], 'avisos': r['avisos'], 'precision': prec, 'malla': malla,
        }
        if resumen_matlab is not None:
            resumen['matlab'] = resumen_matlab
        if r.get('red'):
            resumen['red'] = r['red']             # bucle: red en L aplicada por circuito (valores E24)
        np.savez_compressed(os.path.join(salida, 'datos.npz'), f=r['f_Hz'], s11=r['s11'], zin=r['zin'],
                            theta=r.get('theta', []), phi=r.get('phi', []),
                            d=r.get('directividad_dBi_grid', np.zeros((0, 0))), **extra)
        try:     # S11 simulado como Touchstone: lo lee Chirptenna VNA (el navegador no lee datos.npz)
            from antenas import biblioteca
            biblioteca.escribir_s1p(os.path.join(salida, 's11_simulado.s1p'), r['f_Hz'], r['s11'],
                                    f"Chirptenna · simulación {clave} · {motor} · {resumen['f_resonancia_MHz']} MHz")
        except Exception as ex:
            progreso(f'AVISO: no se pudo escribir s11_simulado.s1p: {ex}')
        if trabajo.get('tolerancias') and motor != 'matlab':
            try:
                resumen['tolerancias'] = simulacion.tolerancias(a, tipos.sustrato(sus), f_obj, tuple(x*1e6 for x in trabajo['banda_MHz']), r,
                                                                prec, malla, rango, progreso)
            except Exception as ex:
                resumen['tolerancias'] = {'error': f'{type(ex).__name__}: {ex}'}
                progreso(f'ERROR en el análisis de tolerancias: {ex}')
        if caja:
            # cuánto mueve la carcasa la frecuencia: misma malla con los bloques de aire (control) y de material
            try:
                bl = carcasa.bloques(a, tipos.sustrato(sus).h, caja, f_obj)
                # con tornillos, una simulación más con la carcasa sin su metal: separa lo que pone el plástico de lo que ponen los tornillos
                var = {'sin_metal': carcasa.sin_metal(bl)} if any(b['tipo'] == 'metal' for b in bl) else None
                resumen['carcasa'] = simulacion.efecto_entorno(a, tipos.sustrato(sus), f_obj, ['carcasa'], r, prec, malla, rango, progreso,
                                                               bloques=bl, variantes=var)
                resumen['carcasa']['parametros'] = carcasa.completar(caja)
            except Exception as ex:
                resumen['carcasa'] = {'error': f'{type(ex).__name__}: {ex}'}
                progreso(f'ERROR en el efecto de la carcasa: {ex}')
        if trabajo.get('entorno') and motor != 'matlab':
            try:
                resumen['entorno'] = simulacion.efecto_entorno(a, tipos.sustrato(sus), f_obj, trabajo['entorno'], r, prec, malla, rango, progreso)
            except Exception as ex:
                resumen['entorno'] = {'error': f'{type(ex).__name__}: {ex}'}
                progreso(f'ERROR en la simulación del entorno: {ex}')
        if trabajo.get('verificar_malla') and motor != 'matlab':
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
