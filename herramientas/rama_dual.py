"""Prueba de monopolo o IFA de dos bandas: una rama más corta para la banda alta, desde el mismo punto de alimentación.

Uso (desde la raíz):
    python herramientas/rama_dual.py <tipo> <f_baja_MHz> --bandas "lo-hi;lo-hi" [k2=v1,v2,…] [sep2=…] [h2=…] [--etiqueta E] [--sustrato S] [--solo-lista]

  tipo   monopolo_recto o ifa (cualquiera de la familia monopolo con `alto` o `largo_brazo` + `altura`)
  f_baja tamaño base de `dimensionar`; la banda alta es el centro de la última de --bandas.
  k2     largo de la rama 2 en veces el λ/4 teórico de la banda alta (largo equivalente × f_baja / f_alta). Por defecto 1.
  sep2   (monopolo) distancia horizontal de la rama 2 a la 1, en mm. Por defecto 5.
  x_<param>=F  multiplica ese parámetro de la base (p. ej. x_largo_brazo=1.2 para centrar la IFA en la banda baja)
  y2     (monopolo) altura de la salida de la rama sobre el borde de la masa, mm. Por defecto 0 (a ras: se acopla a la masa).
  h2     (IFA) altura de la rama 2 como fracción de la del brazo principal. Por defecto 0,5.
El monopolo lleva la rama 2 como una pista que sale del punto de alimentación hacia la derecha `sep2` mm y sube; la IFA, un
segundo brazo que sale del pie de la F a la altura h2 × altura. Una simulación por configuración (rango 0,45–3,8 × f_baja).
Resultados en salidas/_barridos/<E> (resultados.jsonl y resumen.json).
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


def construir(tipos, g, nombre_sus, clave, base, k2, sep2, h2, f_baja, f_alta, y2=0.0):
    from shapely.ops import unary_union
    a = tipos.generar(clave, base, nombre_sus)
    w = base.get('ancho_pista', 1.0)
    lg = a.puerto['alimentacion'][1]                        # el radiador arranca en (0, lg)
    le = tipos._longitud_equivalente(clave, base)
    l2 = k2*le*f_baja/f_alta
    if clave in ('ifa', 'pifa'):
        h = base['altura']
        y2 = lg + h2*h
        rama = g.engordar([(0.0, y2), (l2 - h2*h, y2)], w)
        a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, (1 - h2)*h - w)
    else:
        # la rama sale de la pista a `y2` mm por encima del borde de la masa (a ras de él se acopla a la masa y no resuena)
        l2 = max(l2 - y2 - sep2, 5.0)
        rama = g.engordar([(0.0, lg + y2), (sep2, lg + y2), (sep2, lg + y2 + l2)], w)
        a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, sep2 - w)
    a.capas['F.Cu'] = unary_union([a.capas['F.Cu'], rama])
    margen = base.get('margen_borde', 2.0)
    a.radiador = unary_union([a.radiador, rama])
    a.contorno = unary_union([a.contorno, rama.buffer(margen)])
    a.zona_libre = unary_union([a.zona_libre, rama.buffer(margen)])
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_rama2_mm'] = round(l2, 2)
    return a


def main():
    pos, par_txt, opt, i = [], {}, {'sustrato': 'FR4 JLC 1,6 mm'}, 1
    args = sys.argv[1:]
    while i - 1 < len(args):
        a = args[i - 1]
        if a == '--solo-lista':
            opt['solo-lista'] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par_txt[k] = [float(x.replace(',', '.')) for x in v.split(',')]
        else:
            pos.append(a)
        i += 1
    if len(pos) < 2 or 'bandas' not in opt:
        sys.exit(__doc__)
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion, geometria as g
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    clave, f_baja = pos[0], float(pos[1].replace(',', '.'))
    sus = opt['sustrato']
    s = tipos.sustrato(sus)
    bandas = [tuple(float(x) for x in b.split('-')) for b in opt['bandas'].split(';')]
    f_alta = sum(bandas[-1])/2
    base = tipos.dimensionar(clave, f_baja*1e6, {}, sus)
    base.pop('_aviso', None)
    ejes = {'k2': par_txt.get('k2', [1.0])}
    for k in par_txt:
        if k.startswith('x_'):                                     # x_<parametro>=F: multiplica ese parámetro de la base
            ejes[k] = par_txt[k]
    if clave in ('ifa', 'pifa'):
        ejes['h2'] = par_txt.get('h2', [0.5])
    else:
        ejes['sep2'] = par_txt.get('sep2', [5.0])
        if 'y2' in par_txt:
            ejes['y2'] = par_txt['y2']
    ks = list(ejes)
    configs = [dict(zip(ks, comb)) for comb in itertools.product(*[ejes[k] for k in ks])]

    def base_de(c):
        q = dict(base)
        for k, v in c.items():
            if k.startswith('x_'):
                q[k[2:]] = round(base[k[2:]]*v, 3)
        return q
    antenas =[(c, construir(tipos, g, sus, clave, base_de(c), c['k2'], c.get('sep2', 5.0), c.get('h2', 0.5), f_baja, f_alta, c.get('y2', 0.0))) for c in configs]
    if 'solo-lista' in opt:
        for c, a in antenas:
            print(json.dumps(c), 'placa', a.info['placa_mm'], 'rama 2', a.info['largo_rama2_mm'], 'mm')
        return
    etiqueta = opt.get('etiqueta') or f'RD_{clave}_{datetime.datetime.now():%m%d_%H%M}'
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
    cfg = simulacion.PRECISIONES['normal']
    lam_min = simulacion.C0/(3.8*f_baja*1e6)*1e3

    def natural(a):
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        return max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2), 0.08)
    paso = float(opt['paso']) if 'paso' in opt else round(0.9*min(natural(a) for _, a in antenas), 3)
    print(f'=== {etiqueta}: {clave} dos ramas, base a {f_baja:g} MHz, {len(configs)} configuraciones, bandas {opt["bandas"]}, malla {paso} mm', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for c, a in antenas:
            clave_c = json.dumps(c, sort_keys=True)
            if clave_c in hechos:
                filas.append(hechos[clave_c])
                continue
            t0 = time.time()
            fila = {'cambios': c, 'placa': a.info.get('placa_mm'), 'rama2_mm': a.info['largo_rama2_mm'], 'paso': paso}
            try:
                r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=False, progreso=lambda m: None, rango=(0.45, 3.8), paso=paso)
                f = r['f_Hz']/1e6
                s11 = 20*np.log10(np.abs(r['s11']))
                fila['bandas'] = {f'{lo:g}-{hi:g}': round(float(s11[(f >= lo) & (f <= hi)].max()), 1) for lo, hi in bandas}
                fila['peor'] = max(fila['bandas'].values())
                fila['resonancias_MHz'] = [int(round(f[j])) for j in range(1, len(f) - 1) if s11[j] < s11[j - 1] and s11[j] <= s11[j + 1] and s11[j] < -6]
            except Exception as ex:
                fila['error'] = f'{type(ex).__name__}: {ex}'
            fila['s'] = round(time.time() - t0)
            filas.append(fila)
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print(' ', json.dumps(fila, ensure_ascii=False, default=float), flush=True)
        buenas = sorted([x for x in filas if 'peor' in x], key=lambda x: x['peor'])
        print('\n--- ordenadas por el peor S11 de todas las bandas ---')
        for x in buenas[:8]:
            print(f"  {x['peor']:6.1f} dB  {json.dumps(x['cambios'])}  {x['bandas']}  placa {x['placa']}  resonancias {x['resonancias_MHz']}")
        json.dump({'tipo': clave + '_dual', 'f_baja_MHz': f_baja, 'bandas': opt['bandas'], 'sustrato': sus, 'paso': paso, 'filas': filas},
                  open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
