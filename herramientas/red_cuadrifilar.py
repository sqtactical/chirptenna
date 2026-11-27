"""Red de alimentación de la hélice cuadrifilar (híbrido de 90° + una red en L por dipolo) a partir de la simulación de dos puertos.

Uso (desde la raíz):
    python herramientas/red_cuadrifilar.py [D=32] [vueltas=0.25] [k=0.59] [sentido=-1] [--f MHz] [--etiqueta E] [--q-l 40] [--q-c 150] [--centrar] [--sin-tolerancia]

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
        if a in ('--centrar', '--sin-tolerancia'):
            opt[a[2:]] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i + 1]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par[k] = float(v.replace(',', '.'))
        i += 1
    p = dict(hf.DEFECTOS, **{**dict(D=32.0, vueltas=0.25, k=0.59, sentido=-1.0), **par})
    f_MHz = float(opt.get('f', '1575.42').replace(',', '.'))
    q_l, q_c = float(opt.get('q-l', red.Q_BOBINA)), float(opt.get('q-c', red.Q_CONDENSADOR))
    etiqueta = opt.get('etiqueta', 'QHA_red')
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    os.environ.setdefault('ANTENAS_GPU', '1')
    if 'centrar' in opt:                                       # ajusta k para que X = 0 caiga en f0 (dos pasadas, un puerto)
        for _ in range(2):
            hh = hashlib.md5(json.dumps([p, f_MHz, 1.0], sort_keys=True).encode()).hexdigest()[:10]
            s0, _c, j0 = hf.simular_helice(p, f_MHz, 1.0, os.path.join(tempfile.gettempdir(), 'antenas_sim', 'qha_' + hh + '_A'), 1)
            x0 = np.imag(s0['Z'])
            cr = np.where((x0[:-1] < 0) & (x0[1:] >= 0))[0]
            if not len(cr):
                break
            p['k'] = round(p['k']*float(s0['f'][cr[0]])/(f_MHz*1e6), 4)
        print('k centrada:', p['k'], flush=True)
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
    comb = hf.combinar(sA, cA, sB, cB, i0)
    resumen['pol'] = comb
    for umbral in (0.9, 0.8):                                   # ancho de banda con la red diseñada a f0: dónde la eficiencia total supera el umbral
        buenos = np.where(ev_con['eficiencia_total'] >= umbral)[0]
        resumen[f'ancho_eficiencia_{int(umbral*100)}%_MHz'] = round(float((f[buenos[-1]] - f[buenos[0]])/1e6), 1) if len(buenos) else 0.0
    # --- recepción (solo RX): lo que cuenta es la ganancia RHCP hacia el cielo, la pérdida antes del amplificador y la tolerancia al desajuste
    cur = {int(th): (r_, l_) for th, r_, l_ in comb['curva_theta_RHCP_LHCP_dBi']}
    pierde_red = float(red.perdida_red_dB(zA[i0], f0, redA, q_l, q_c))
    pierde_adapt = float(red.perdida_desadaptacion_dB(zA[i0], f0, redA, q_l, q_c))
    pol_buena = 0 if comb['pol'] == 'RHCP' else 1                     # columna de la polarización de GPS (RHCP) en la curva
    g_rhcp = {f'elevacion_{90 - th}': cur[th][0] for th in (0, 30, 60, 80, 90) if th in cur}
    resumen['recepcion'] = {
        'ganancia_RHCP_dBi_por_elevacion_grados': g_rhcp,
        'ganancia_LHCP_cenit_dBi': cur[0][1] if 0 in cur else None,
        'mejor_lóbulo_trasero_RHCP_dBi': max(v[0] for th, v in cur.items() if th >= 110),
        'perdida_red_dB': round(pierde_red, 3), 'perdida_desadaptacion_dB': round(pierde_adapt, 3),
        'figura_ruido_añadida_dB': round(pierde_red, 3),
        'ganancia_RHCP_cenit_menos_perdida_total_dBi': round(cur[0][0] - pierde_red - pierde_adapt, 2) if 0 in cur else None,
        'nota': 'ideal en el híbrido; la polarización de GPS es RHCP' if comb['pol'] == 'RHCP' else 'la hélice sale LHCP: cambia el sentido (sentido = -1 para RHCP)'}
    # tolerancia al desajuste (carcasa, mano, tolerancia del flex): la misma red con k ±3 %
    desv = {}
    if 'sin-tolerancia' not in opt:
        for fac in (0.97, 1.03):
            q = dict(p, k=p['k']*fac)
            h2 = hashlib.md5(json.dumps([q, f_MHz, 1.0], sort_keys=True).encode()).hexdigest()[:10]
            b2 = os.path.join(tempfile.gettempdir(), 'antenas_sim', 'qha_' + h2)
            sA2, cA2, j0 = hf.simular_helice(q, f_MHz, 1.0, b2 + '_A', 1)
            z2 = sA2['Z']
            ev2 = red.evaluar(sA2['f'], z2, redA, q_l, q_c)
            cruces = np.where((np.imag(z2)[:-1] < 0) & (np.imag(z2)[1:] >= 0))[0]
            desv[f'k_x{fac}'] = {'f_resonancia_MHz': round(float(sA2['f'][cruces[0]]/1e6)) if len(cruces) else None,
                                 'Z_f0': [round(float(z2[j0].real), 1), round(float(z2[j0].imag), 1)],
                                 'eficiencia_total_f0': round(float(ev2['eficiencia_total'][j0]), 3),
                                 'perdida_desadaptacion_dB': round(float(red.perdida_desadaptacion_dB(z2[j0], f0, redA, q_l, q_c)), 2)}
        resumen['recepcion']['tolerancia_k_3%'] = desv
    json.dump(resumen, open(os.path.join(carpeta, 'red.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
    print(json.dumps(resumen, indent=1, ensure_ascii=False, default=float))


if __name__ == '__main__':
    main()
