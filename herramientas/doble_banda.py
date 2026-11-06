"""Búsqueda de una antena de varias bandas: simula en banda ancha y mide el peor S11 en cada banda a la vez.

Uso (desde la raíz):
    python herramientas/doble_banda.py <tipo> <f_baja_MHz> [param=v1,v2,…]… --bandas "lo-hi;lo-hi;…" [opciones]

  f_baja_MHz   frecuencia con la que `dimensionar` da el tamaño base (centro de la banda baja)
  param=…      un valor fija el parámetro; varios lo barren (todas las combinaciones). «xF» = F × el valor de dimensionar.
  --bandas     bandas de uso en MHz, p. ej. "868-870;902-928;863-928;2400-2483.5"
  --etiqueta E carpeta de resultados salidas/_barridos/<E> (por defecto D_<tipo>_<fecha>)
  --sustrato S por defecto «FR4 JLC 1,6 mm»;  --paso mm: malla fija (por defecto 0,9 × la más fina de todas)
Una simulación por configuración (rango 0,45–3,8 × f_baja, sin diagrama), con el bloqueo de la GPU compartido con
barrido.py. Resultados en resultados.jsonl y resumen.json; ordenados por el peor S11 de todas las bandas.
"""
import os
import sys
import json
import math
import time
import itertools
import datetime
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def main():
    pos, par_txt, opt, i = [], {}, {'sustrato': 'FR4 JLC 1,6 mm'}, 1
    args = sys.argv[1:]
    while i - 1 < len(args):
        a = args[i - 1]
        if a.startswith('--'):
            opt[a[2:]] = args[i]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par_txt[k] = v.split(',')
        else:
            pos.append(a)
        i += 1
    if len(pos) < 2 or 'bandas' not in opt:
        sys.exit(__doc__)
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    clave, f_baja = pos[0], float(pos[1].replace(',', '.'))
    sus = opt['sustrato']
    s = tipos.sustrato(sus)
    nombres = {q.nombre: q for q in tipos.CATALOGO[clave].parametros}
    bandas = [tuple(float(x) for x in b.split('-')) for b in opt['bandas'].split(';')]
    espec = {k: [('x', float(v[1:])) if v.startswith('x') else ('v', float(v.replace(',', '.'))) for v in vs] for k, vs in par_txt.items()}
    fijos_abs = {k: (int(sp[0][1]) if nombres[k].entero else sp[0][1]) for k, sp in espec.items() if sp[0][0] == 'v'}
    base = tipos.dimensionar(clave, f_baja*1e6, dict(fijos_abs), sus, fijos=tuple(fijos_abs))
    base.pop('_aviso', None)
    ks = list(espec)
    configs = []
    for comb in itertools.product(*[espec[k] for k in ks]):
        q = dict(base)
        for k, (tipo_v, v) in zip(ks, comb):
            val = v if tipo_v == 'v' else round(base[k]*v, 3)
            q[k] = int(val) if nombres[k].entero else val
        configs.append(({k: q[k] for k in ks}, q))
    etiqueta = opt.get('etiqueta') or f'D_{clave}_{datetime.datetime.now():%m%d_%H%M}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    ruta_jl = os.path.join(carpeta, 'resultados.jsonl')
    hechos = {}
    if os.path.exists(ruta_jl):
        for l in open(ruta_jl, encoding='utf-8'):
            try:
                d = json.loads(l)
                hechos[json.dumps(d['cambios'], sort_keys=True)] = d
            except ValueError:
                pass
    antenas = [(c, q, tipos.generar(clave, q, sus)) for c, q in configs]
    cfg = simulacion.PRECISIONES['normal']
    lam_min = simulacion.C0/(3.8*f_baja*1e6)*1e3

    def natural(a):
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        return max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2), 0.08)
    paso = float(opt['paso']) if 'paso' in opt else round(0.9*min(natural(a) for _, _, a in antenas), 3)
    print(f'=== {etiqueta}: {clave}, base a {f_baja:g} MHz, {len(configs)} configuraciones, bandas {opt["bandas"]}, malla {paso} mm', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for c, q, a in antenas:
            clave_c = json.dumps(c, sort_keys=True)
            if clave_c in hechos:
                filas.append(hechos[clave_c])
                continue
            t0 = time.time()
            fila = {'cambios': c, 'parametros': q, 'placa': a.info.get('placa_mm'), 'paso': paso}
            try:
                r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=False, progreso=lambda m: None, rango=(0.45, 3.8), paso=paso)
                f = r['f_Hz']/1e6
                s11 = 20*np.log10(np.abs(r['s11']))
                fila['bandas'] = {f'{lo:g}-{hi:g}': round(float(s11[(f >= lo) & (f <= hi)].max()), 1) for lo, hi in bandas}
                fila['peor'] = max(fila['bandas'].values())
                pk = [int(round(f[j])) for j in range(1, len(f) - 1) if s11[j] < s11[j - 1] and s11[j] <= s11[j + 1] and s11[j] < -6]
                fila['resonancias_MHz'] = pk
            except Exception as ex:
                fila['error'] = f'{type(ex).__name__}: {ex}'
            fila['s'] = round(time.time() - t0)
            filas.append(fila)
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print(' ', json.dumps({k: v for k, v in fila.items() if k != 'parametros'}, ensure_ascii=False, default=float), flush=True)
        buenas = sorted([x for x in filas if 'peor' in x], key=lambda x: x['peor'])
        print('\n--- ordenadas por el peor S11 de todas las bandas ---')
        for x in buenas[:8]:
            print(f"  {x['peor']:6.1f} dB  {json.dumps(x['cambios'])}  {x['bandas']}  placa {x['placa']}  resonancias {x['resonancias_MHz']}")
        json.dump({'tipo': clave, 'f_baja_MHz': f_baja, 'bandas': opt['bandas'], 'sustrato': sus, 'paso': paso, 'filas': filas},
                  open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()