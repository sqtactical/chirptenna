"""Compara la malla uniforme con la adaptada en geometrías ya ajustadas por un lote de validación.

Uso: python -m antenas.comparar_mallas <carpeta_lote> [caso ...]
Para cada caso toma los parámetros finales y el paso de malla de su resultado.json, simula con
las dos mallas (la uniforme suele estar en caché) y escribe <carpeta_lote>/comparar_mallas.json.
La adaptada se da por buena si la resonancia no se mueve más de un 0,5 % y S11, ganancia y
eficiencia apenas cambian.
"""
import os
import sys
import json

from . import tipos, simulacion as sim


def main():
    lote = os.path.abspath(sys.argv[1])
    casos = sys.argv[2:] or sorted(d for d in os.listdir(lote) if os.path.isfile(os.path.join(lote, d, 'resultado.json')))
    salida = []
    for caso in casos:
        r0 = json.load(open(os.path.join(lote, caso, 'resultado.json'), encoding='utf-8'))
        t = json.load(open(os.path.join(lote, caso, 'trabajo.json'), encoding='utf-8-sig'))
        if not r0.get('ok'):
            continue
        a = tipos.generar(r0['clave'], r0['parametros'], t['sustrato'])
        s = tipos.sustrato(t['sustrato'])
        fila = {'caso': caso}
        for malla in ('uniforme', 'adaptada'):
            print(f'=== {caso} ({malla})', flush=True)
            r = sim.simular(a, s, t['f_obj_Hz'], t['precision'], nf2ff=True, paso=r0['paso_malla_mm'], malla=malla,
                            progreso=lambda m: print('PROGRESO', m, flush=True))
            fila[malla] = {'f_resonancia_MHz': round(r['f_resonancia_Hz']/1e6, 2),
                           's11_min_dB': round(r['s11_min_dB'], 1),
                           's11_obj_dB': round(sim._s11_en(r, t['f_obj_Hz'])[0], 1),
                           'ganancia_dBi': round(r['ganancia_dBi'], 2),
                           'eficiencia_%': round(100*r['eficiencia_radiacion'], 1),
                           'celdas_M': round(r['celdas']/1e6, 2), 'tiempo_s': r['tiempo_s']}
        u, ad = fila['uniforme'], fila['adaptada']
        fila['diferencia_f_%'] = round(100*(ad['f_resonancia_MHz'] - u['f_resonancia_MHz'])/u['f_resonancia_MHz'], 2)
        salida.append(fila)
        print(f"--- {caso}: Δf {fila['diferencia_f_%']:+.2f} %, celdas {u['celdas_M']} → {ad['celdas_M']} M", flush=True)
        json.dump(salida, open(os.path.join(lote, 'comparar_mallas.json'), 'w', encoding='utf-8'), indent=2,
                  ensure_ascii=False, default=float)


if __name__ == '__main__':
    main()
