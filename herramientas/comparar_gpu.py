"""Compara la simulación en CPU y en GPU (openEMS con motor GPU, ver antenas/gpu.py).

    python herramientas/comparar_gpu.py [tipo ...] [--freq MHz] [--precision normal|fina]

Por cada tipo simula dos veces la misma antena (borra la caché entre una y otra), una con la CPU y otra con
`ANTENAS_GPU=1`, y compara tiempo, frecuencia de resonancia, S11 mínimo, impedancia y, con --radiacion,
ganancia y eficiencia. Sirve para decidir si se puede fiarse de la GPU. Resumen en `salidas/_comparar_gpu/`.
"""
import os
import sys
import json
import shutil
import tempfile

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from antenas import gpu, tipos, simulacion            # noqa: E402
from antenas.simulacion import _clave_cache           # noqa: E402


def _borrar_cache():
    shutil.rmtree(os.path.join(tempfile.gettempdir(), 'antenas_sim'), ignore_errors=True)


def _resumen(r):
    return {'tiempo_s': r['tiempo_s'], 'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 3),
            's11_min_dB': round(float(r['s11_min_dB']), 2), 'celdas_M': round(r['celdas']/1e6, 2),
            'ganancia_dBi': round(r['ganancia_dBi'], 2) if 'ganancia_dBi' in r else None,
            'eficiencia': round(r['eficiencia_radiacion'], 3) if 'eficiencia_radiacion' in r else None}


def main():
    args = sys.argv[1:]
    radiacion = '--radiacion' in args
    f = 2441.75
    precision = 'normal'
    claves = []
    i = 0
    while i < len(args):
        if args[i] == '--freq':
            f = float(args[i + 1]); i += 2
        elif args[i] == '--precision':
            precision = args[i + 1]; i += 2
        elif args[i] == '--radiacion':
            i += 1
        else:
            claves.append(args[i]); i += 1
    claves = claves or ['monopolo_recto']
    ok, motivo = gpu.disponible()
    print('GPU:', 'disponible' if ok else 'NO disponible', '-', motivo)
    if not ok:
        sys.exit(2)
    salida = os.path.join(RAIZ, 'salidas', '_comparar_gpu')
    os.makedirs(salida, exist_ok=True)
    todo = {}
    for clave in claves:
        p = tipos.dimensionar(clave, f*1e6)       # dimensionar trabaja en Hz
        a = tipos.generar(clave, p)
        sus = tipos.sustrato()
        res = {}
        for modo in ('cpu', 'gpu'):
            _borrar_cache()
            os.environ['ANTENAS_GPU'] = '1' if modo == 'gpu' else '0'
            print(f'--- {clave} {f} MHz: {modo.upper()}', flush=True)
            r = simulacion.simular(a, sus, f*1e6, precision, nf2ff=radiacion, progreso=print)
            res[modo] = (_resumen(r), r)
            print('   ', res[modo][0], flush=True)
        c, g = res['cpu'][1], res['gpu'][1]
        s11c, s11g = np.asarray(c['s11']), np.asarray(g['s11'])
        d = {'cpu': res['cpu'][0], 'gpu': res['gpu'][0],
             'speedup': round(res['cpu'][0]['tiempo_s']/max(res['gpu'][0]['tiempo_s'], 1e-6), 2),
             'dif_f_res_MHz': round(g['f_resonancia_Hz']/1e6 - c['f_resonancia_Hz']/1e6, 4),
             'max_dif_s11_dB': round(float(np.max(np.abs(20*np.log10(np.abs(s11g)) - 20*np.log10(np.abs(s11c))))), 4),
             'max_dif_zin_ohm': round(float(np.max(np.abs(np.asarray(g['zin']) - np.asarray(c['zin'])))), 4)}
        print('=>', d, flush=True)
        todo[clave] = d
    ruta = os.path.join(salida, 'resumen.json')
    previo = {}
    if os.path.exists(ruta):
        with open(ruta, encoding='utf-8') as fh:
            previo = json.load(fh)
    previo.update(todo)      # cada tipo se lanza en su proceso: se van sumando
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(previo, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
