"""Sensibilidad de las placas pedidas a la εr del FR4 (la geometría es la impresa; solo cambia la εr simulada).

Uso (desde la raíz):
    python herramientas/sensibilidad_er.py [carpeta_pedido] [nombre …] [--er 4.2,4.5,4.8] [--tand 0.02] [--etiqueta E] [--solo-lista]

  carpeta_pedido  por defecto salidas/pedido_2G4 (cada subcarpeta con su ficha.json: clave y parámetros del diseño exportado)
  --er            εr a simular (la que usa el generador es 4,5; el FR4 de JLC real suele estar entre 4,2 y 4,6)
Para cada diseño y εr, una simulación a 2441,75 MHz (rango 0,6–1,4 ×) con la malla fija de la εr de 4,5. Da la resonancia, la banda
a −10 dB y el S11 en 2441,75 MHz: lo que cabe esperar si la medida sale desplazada. Resultados en salidas/_barridos/<E>.
"""
import os
import sys
import json
import math
import time
import dataclasses
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def main():
    args = sys.argv[1:]
    opt, pos, i = {}, [], 0
    while i < len(args):
        a = args[i]
        if a == '--solo-lista':
            opt['solo-lista'] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i + 1]
            i += 1
        else:
            pos.append(a)
        i += 1
    carpeta_pedido = pos[0] if pos and os.path.isdir(pos[0]) else os.path.join('salidas', 'pedido_2G4')
    nombres = [p for p in pos if not os.path.isdir(p)]
    ers = [float(x) for x in opt.get('er', '4.2,4.5,4.8').split(',')]
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    from antenas import tipos, simulacion
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    base = tipos.sustrato('FR4 JLC 1,6 mm')
    tand = float(opt.get('tand', base.tand))
    f_obj = 2441.75
    cfg = simulacion.PRECISIONES['normal']
    lam_min = simulacion.C0/(1.4*f_obj*1e6)*1e3
    disenos = []
    for d in sorted(os.listdir(carpeta_pedido)):
        ruta = os.path.join(carpeta_pedido, d, 'ficha.json')
        if not os.path.exists(ruta) or (nombres and d not in nombres):
            continue
        ficha = json.load(open(ruta, encoding='utf-8-sig'))
        p = dict(ficha['parametros'])
        a = tipos.generar(ficha['clave'], p, 'FR4 JLC 1,6 mm')
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        paso = round(0.9*max(min(lam_min/math.sqrt(base.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2,
                                 cfg['factor_detalle']*s_min/2), 0.08), 3)
        disenos.append((d, ficha, a, paso))
    if 'solo-lista' in opt:
        for d, ficha, a, paso in disenos:
            print(d, ficha['clave'], 'placa', a.info.get('placa_mm'), 'malla', paso, 'mm')
        return
    etiqueta = opt.get('etiqueta', 'SENS_er_pedido')
    salida = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(salida, exist_ok=True)
    ruta_jl = os.path.join(salida, 'resultados.jsonl')
    hechos = {}
    if os.path.exists(ruta_jl):
        for l in open(ruta_jl, encoding='utf-8'):
            try:
                x = json.loads(l)
                if 'f_res_MHz' in x:
                    hechos[(x['diseno'], x['er'])] = x
            except ValueError:
                pass
    print(f'=== {etiqueta}: {len(disenos)} diseños × εr {ers}, tanδ {tand}', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for d, ficha, a, paso in disenos:
            for er in ers:
                if (d, er) in hechos:
                    filas.append(hechos[(d, er)])
                    continue
                s = dataclasses.replace(base, nombre=f'FR4 εr {er}', er=er, tand=tand)
                t0 = time.time()
                fila = {'diseno': d, 'er': er, 'paso': paso}
                try:
                    r = simulacion.simular(a, s, f_obj*1e6, 'normal', nf2ff=False, progreso=lambda m: None, paso=paso)
                    flo, fhi = r['banda_Hz']
                    fila.update({'f_res_MHz': round(r['f_resonancia_Hz']/1e6, 1), 'criterio': r['criterio'],
                                 'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
                                 'S11_2441_dB': round(float(simulacion._s11_en(r, f_obj*1e6)[0]), 1)})
                except Exception as ex:
                    fila['error'] = f'{type(ex).__name__}: {ex}'
                fila['s'] = round(time.time() - t0)
                filas.append(fila)
                open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
                print(' ', json.dumps(fila, ensure_ascii=False, default=float), flush=True)
        print('\n--- resonancia (MHz) por εr ---')
        for d, *_ in disenos:
            xs = [x for x in filas if x['diseno'] == d and 'f_res_MHz' in x]
            print(f'  {d:30s}', '  '.join(f"εr {x['er']}: {x['f_res_MHz']} (S11 {x['S11_2441_dB']} dB)" for x in xs))
        json.dump({'ers': ers, 'tand': tand, 'filas': filas}, open(os.path.join(salida, 'resumen_sensibilidad.json'), 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', salida, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
