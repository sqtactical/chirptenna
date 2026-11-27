"""Red de alimentación de la hélice cuadrifilar (híbrido de 90° + una red en L por dipolo) a partir de la simulación de dos puertos.

Uso (desde la raíz):
    python herramientas/red_cuadrifilar.py [D=32] [vueltas=0.25] [k=0.59] [sentido=-1] [--f MHz] [--etiqueta E] [--q-l 40] [--q-c 150]

Simula la QHA con `herramientas/helice_flex.py` (dos simulaciones de ~20 s en GPU), toma la impedancia de cada dipolo en toda la
banda, diseña con `antenas.red_cuadrifilar` la red en L (valores E24) de cada uno y da la eficiencia de adaptación en frecuencia,
con y sin red, y la razón axial en el cénit si los componentes tienen tolerancia. Resultado en `salidas/_barridos/<E>/red.json`.
Sentido −1 = hélice a izquierdas, RHCP (GPS). Es un modelo de circuito con el híbrido ideal: el real tiene pérdida y error de fase.
"""
import os
import sys
import json
import importlib.util
import itertools
import tempfile
import hashlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def cargar_helice():
    spec = importlib.util.spec_from_file_location('helice_flex', os.path.join(RAIZ, 'herramientas', 'helice_flex.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    import numpy as np
    from antenas import red_cuadrifilar as red
    hf = cargar_helice()
    par, opt, args, i = {}, {}, sys.argv[1:], 0
    while i < len(args):
        a = args[i]
        if a.startswith('--'):
            opt[a[2:]] = args[i + 1]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par[k] = float(v.replace(',', '.'))
        i += 1
    p = dict(hf.DEFECTOS, D=32.0, vueltas=0.25, k=0.59, sentido=-1.0, **par)
    f_MHz = float(opt.get('f', '1575.42').replace(',', '.'))
    q_l, q_c = float(opt.get('q-l', red.Q_BOBINA)), float(opt.get('q-c', red.Q_CONDENSADOR))
    etiqueta = opt.get('etiqueta', 'QHA_red')
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    os.environ.setdefault('ANTENAS_GPU', '1')
    h = hashlib.md5(json.dumps([p, f_MHz, 1.0], sort_keys=True).encode()).hexdigest()[:10]
    base = os.path.join(tempfile.gettempdir(), 'antenas_sim', 'qha_' + h)
    sA, cA, i0 = hf.simular_helice(p, f_MHz, 1.0, base + '_A', 1)
    sB, cB, _ = hf.simular_helice(p, f_MHz, 1.0, base + '_B', 2)
    f = sA['f']
    zA, zB = sA['Z'], sB['Z']
    f0 = f_MHz*1e6
    redA, redB = red.disenar_red(zA[i0], f0, q_l, q_c), red.disenar_red(zB[i0], f0, q_l, q_c)
    ev_sin = red.evaluar(f, zA, None, q_l, q_c)
    ev_con = red.evaluar(f, zA, redA, q_l, q_c)
    banda = (np.abs(f - f0) <= 1.023e6)                      # ±1,023 MHz: la banda de GPS L1 (C/A)
    resumen = {'f_MHz': f_MHz, 'parametros': p, 'Z_dipolo_A_f0': [round(float(zA[i0].real), 2), round(float(zA[i0].imag), 2)],
               'Z_dipolo_B_f0': [round(float(zB[i0].real), 2), round(float(zB[i0].imag), 2)],
               'red_A': redA, 'red_B': redB,
               'eficiencia_total_f0_sin_red': round(float(ev_sin['eficiencia_total'][i0]), 3),
               'eficiencia_total_f0_con_red': round(float(ev_con['eficiencia_total'][i0]), 3),
               'eficiencia_total_banda_min_con_red': round(float(ev_con['eficiencia_total'][banda].min()), 3),
               'S11_dipolo_f0_con_red_dB': round(float(ev_con['S11_dipolo_dB'][i0]), 1),
               'banda_S11_dipolo_-10dB_MHz': None}
    ok = np.where(ev_con['S11_dipolo_dB'] <= -10)[0]
    if len(ok):
        resumen['banda_S11_dipolo_-10dB_MHz'] = [round(float(f[ok[0]]/1e6), 1), round(float(f[ok[-1]]/1e6), 1)]
    # tolerancia: una de las dos redes con ±5 % en cada valor → desbalance de amplitud y razón axial
    peores = []
    if redA:
        for sa, sd in itertools.product((0.95, 1.05), repeat=2):
            r2 = dict(redA, serie=(redA['serie'][0], redA['serie'][1]*sa) if redA['serie'][0] in ('L', 'C') else redA['serie'],
                      derivacion=(redA['derivacion'][0], redA['derivacion'][1]*sd))
            d = red.desbalance(zA[i0], zB[i0], f0, r2, redB)
            peores.append((red.razon_axial_cenit_dB(d['delta_potencia_dB']), d['delta_potencia_dB']))
    if peores:
        resumen['razon_axial_cenit_peor_con_5%_dB'] = round(max(a for a, _ in peores), 1)
        resumen['desbalance_peor_dB'] = round(max(abs(d) for _, d in peores), 2)
    resumen['pol'] = hf.combinar(sA, cA, sB, cB, i0)
    json.dump(resumen, open(os.path.join(carpeta, 'red.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
    print(json.dumps(resumen, indent=1, ensure_ascii=False, default=float))


if __name__ == '__main__':
    main()
