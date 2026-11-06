"""Barrido de parámetros de cualquier tipo de antena, simulando con openEMS (GPU por defecto).

Uso (desde la raíz):
    python herramientas/barrido.py <tipo> <f_MHz | banda> [param=v1,v2,…]… [opciones]

  tipo      clave del catálogo (monopolo_koch, parche_circular, vivaldi…)
  f_MHz     frecuencia objetivo, o el nombre de una banda («2,4 GHz», «868», «915 ISM»…)
  param=…   un valor fija el parámetro; varios valores, separados por comas, lo barren. Los parámetros no
            nombrados salen de `tipos.dimensionar` (tamaño ajustado a la frecuencia).

Opciones:
  --modo grid|uno   grid (por defecto): todas las combinaciones; uno: cada parámetro por separado alrededor
                    del primer valor de los demás
  --bw MHz          ancho de la banda objetivo (por defecto el de la banda; 5 MHz si f es un número suelto)
  --sustrato S      por defecto «FR4 JLC 1,6 mm»
  --etiqueta E      nombre de la carpeta de resultados (salidas/_barridos/<E>); por defecto tipo_f_fecha
  --paso mm         paso de malla fijo (por defecto 0,9 × el más fino de todas las configuraciones)
  --top N           cuántas mejores configuraciones se repiten con el diagrama de radiación (1)
  --max N           límite de configuraciones (60)
  --max-celdas M    salta las configuraciones con más de M millones de celdas estimadas (sin límite)
  --cpu             usa la CPU en vez de la GPU
  --solo-lista      solo muestra las configuraciones y el coste estimado
  --rehacer         ignora lo que ya hay guardado

La malla se fija para todo el barrido (si cambia, la frecuencia salta varios %). El criterio es el peor S11
en toda la banda objetivo. Cada configuración se guarda en resultados.jsonl: si se corta, al repetir el
comando continúa por donde iba. Con la GPU solo corre un barrido a la vez (bloqueo en %LOCALAPPDATA%\\antenas).
"""
import os
import sys
import json
import math
import time
import itertools
import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def _opciones(argv):
    pos, par, opt = [], {}, {'modo': 'grid', 'top': 1, 'max': 60}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            k = a[2:]
            if k in ('cpu', 'solo-lista', 'rehacer'):
                opt[k] = True
            else:
                i += 1
                opt[k] = argv[i]
        elif '=' in a:
            k, v = a.split('=', 1)
            par[k] = v.split(',')
        else:
            pos.append(a)
        i += 1
    return pos, par, opt


def _valor(parametro, texto):
    v = float(texto.replace(',', '.')) if not isinstance(texto, (int, float)) else float(texto)
    return int(round(v)) if parametro.entero else v


def _bloqueo():
    """Un solo barrido con GPU a la vez: archivo de bloqueo que espera si otro lo tiene."""
    ruta = os.path.join(os.environ.get('LOCALAPPDATA', RAIZ), 'antenas', 'gpu.lock')
    while True:
        try:
            fd = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return ruta
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(ruta) > 6*3600:      # bloqueo viejo de un proceso muerto
                    os.remove(ruta)
                    continue
            except OSError:
                pass
            print('  esperando a que acabe otro barrido en la GPU…', flush=True)
            time.sleep(60)


def main():
    pos, par_txt, opt = _opciones(sys.argv[1:])
    if len(pos) < 2:
        sys.exit(__doc__)
    if opt.get('cpu'):
        os.environ['ANTENAS_GPU'] = '0'
    else:
        os.environ.setdefault('ANTENAS_GPU', '1')
    from antenas import tipos, simulacion, presentacion
    clave, objetivo = pos[0], pos[1]
    if clave not in tipos.CATALOGO:
        sys.exit(f'Tipo desconocido: {clave}. Tipos: {", ".join(tipos.CATALOGO)}')
    tipo = tipos.CATALOGO[clave]
    banda = presentacion.BANDAS.get(objetivo)
    if banda:
        f_MHz, bw_MHz = (banda[0] + banda[1])/2, banda[1] - banda[0]
    else:
        f_MHz, bw_MHz = float(objetivo.replace(',', '.')), 5.0
    bw_MHz = float(opt.get('bw', bw_MHz))
    f_obj = f_MHz*1e6
    sus_nombre = opt.get('sustrato', 'FR4 JLC 1,6 mm')
    s = tipos.sustrato(sus_nombre)
    nombres = {q.nombre: q for q in tipo.parametros}
    listas = {}
    for k, vs in par_txt.items():
        if k not in nombres:
            sys.exit(f'«{k}» no es un parámetro de {clave}. Parámetros: {", ".join(nombres)}')
        listas[k] = [_valor(nombres[k], v) for v in vs]
    fijos = {k: v[0] for k, v in listas.items() if len(v) == 1}
    barridos = {k: v for k, v in listas.items() if len(v) > 1}
    base = tipos.dimensionar(clave, f_obj, dict(fijos), sus_nombre, fijos=tuple(listas))
    base.pop('_aviso', None)
    esc, conj = tipo.escala, tipo.escala_conjunta
    prop = {k: base[k]/base[esc] for k in conj}

    def config(cambios):
        q = dict(base)
        for k, v in cambios.items():
            q[k] = v
            if k == esc:                                  # las medidas ligadas al tamaño principal lo siguen
                for kk, r_ in prop.items():
                    if kk not in cambios and kk not in listas:
                        q[kk] = round(r_*v, 3)
        return q

    if opt['modo'] == 'uno':
        combos = [{}]
        for k, vs in barridos.items():
            combos += [{k: v} for v in vs if v != vs[0]]
        combos = [dict({k: vs[0] for k, vs in barridos.items()}, **c) for c in combos]
    else:
        ks = list(barridos)
        combos = [dict(zip(ks, vs)) for vs in itertools.product(*barridos.values())] if ks else [{}]
    if len(combos) > int(opt['max']):
        sys.exit(f'{len(combos)} configuraciones: más del límite ({opt["max"]}). Sube --max o reduce los valores.')

    etiqueta = opt.get('etiqueta') or f'{clave}_{f_MHz:g}MHz_{datetime.datetime.now():%m%d_%H%M}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    ruta_jl = os.path.join(carpeta, 'resultados.jsonl')

    # antenas y paso de malla común
    antenas, naturales = [], []
    for c in combos:
        q = config(c)
        try:
            a = tipos.generar(clave, q, sus_nombre)
        except Exception as ex:
            antenas.append((c, q, None, f'{type(ex).__name__}: {ex}'))
            continue
        cfg = simulacion.PRECISIONES['normal']
        lam_min = simulacion.C0/(1.4*f_obj)*1e3
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        nat = max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2), 0.08)
        naturales.append(nat)
        antenas.append((c, q, a, None))
    paso = float(opt['paso']) if 'paso' in opt else round(0.9*min(naturales), 3)
    print(f'=== {etiqueta}: {clave} a {f_MHz:g} MHz (banda {f_MHz - bw_MHz/2:g}–{f_MHz + bw_MHz/2:g}), '
          f'{len(combos)} configuraciones, malla fija {paso} mm, {"GPU" if os.environ["ANTENAS_GPU"] != "0" else "CPU"}', flush=True)
    for c, q, a, err in antenas:
        if a is None:
            print('  ✗', json.dumps(c), err)
            continue
        x0, y0, x1, y1 = a.contorno.bounds
        celdas = ((x1 - x0)/paso + 40)*((y1 - y0)/paso + 40)*(s.h/paso + 24)/1e6
        print(f'  · {json.dumps(c, ensure_ascii=False)}  placa {a.info.get("placa_mm")}  ~{celdas:.1f} M celdas  f_est {a.info.get("f_estimada_MHz")} MHz')
    if opt.get('solo-lista'):
        return

    hechos = {}
    if os.path.exists(ruta_jl) and not opt.get('rehacer'):
        for linea in open(ruta_jl, encoding='utf-8'):
            try:
                d = json.loads(linea)
                if d.get('paso') == paso and d.get('f_MHz') == f_MHz:
                    hechos[json.dumps(d['cambios'], sort_keys=True)] = d
            except ValueError:
                pass
    max_celdas = float(opt['max-celdas']) if 'max-celdas' in opt else None
    lock = None if os.environ['ANTENAS_GPU'] == '0' else _bloqueo()
    filas = []
    try:
        for c, q, a, err in antenas:
            clave_c = json.dumps(c, sort_keys=True)
            if a is None:
                continue
            if clave_c in hechos:
                filas.append(hechos[clave_c])
                print(f'  (ya hecha) {json.dumps(c, ensure_ascii=False)}', flush=True)
                continue
            if max_celdas:
                x0, y0, x1, y1 = a.contorno.bounds
                if ((x1 - x0)/paso + 40)*((y1 - y0)/paso + 40)*(s.h/paso + 24)/1e6 > max_celdas:
                    print(f'  (saltada: demasiadas celdas) {json.dumps(c, ensure_ascii=False)}', flush=True)
                    continue
            t0 = time.time()
            fila = {'cambios': c, 'f_MHz': f_MHz, 'paso': paso, 'parametros': q}
            try:
                r = simulacion.simular(a, s, f_obj, 'normal', nf2ff=False, progreso=lambda m: None, paso=paso)
                lo, hi = f_MHz - bw_MHz/2, f_MHz + bw_MHz/2
                puntos = [lo + (hi - lo)*i/4 for i in range(5)]
                s11 = [simulacion._s11_en(r, fm*1e6)[0] for fm in puntos]
                s_obj, z = simulacion._s11_en(r, f_obj)
                flo, fhi = r['banda_Hz']
                fila.update({'peor_banda_dB': round(max(s11), 1), 's11_obj_dB': round(s_obj, 1),
                             'z_obj': [round(float(z.real), 1), round(float(z.imag), 1)],
                             'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
                             'f_res_MHz': round(r['f_resonancia_Hz']/1e6, 1), 'celdas_M': round(r['celdas']/1e6, 1),
                             's': round(time.time() - t0), 'avisos': r['avisos'][:2]})
            except Exception as ex:
                fila.update({'error': f'{type(ex).__name__}: {ex}', 's': round(time.time() - t0)})
            filas.append(fila)
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print('  ', json.dumps({k: v for k, v in fila.items() if k not in ('parametros', 'paso', 'f_MHz', 'avisos')},
                                   ensure_ascii=False, default=float), flush=True)

        buenas = sorted([f for f in filas if 'peor_banda_dB' in f], key=lambda f: f['peor_banda_dB'])
        print('\n--- ordenadas por el peor S11 en la banda ---')
        for f in buenas[:10]:
            print(f"  {f['peor_banda_dB']:6.1f} dB  obj {f['s11_obj_dB']:6.1f}  res {f['f_res_MHz']:7.1f} MHz  banda {f['banda_10dB']}  {json.dumps(f['cambios'], ensure_ascii=False)}")
        # radiación de las mejores
        mejores = []
        for f in buenas[:int(opt['top'])]:
            a = tipos.generar(clave, f['parametros'], sus_nombre)
            r = simulacion.simular(a, s, f_obj, 'normal', nf2ff=True, progreso=lambda m: None, paso=paso, f_radiacion=f_obj)
            rad = {'directividad_dBi': round(r['directividad_dBi'], 2), 'ganancia_dBi': round(r['ganancia_dBi'], 2),
                   'eficiencia_%': round(100*r['eficiencia_radiacion'], 1), 'direccion_max': r.get('direccion_max')}
            for k in ('ar_dB_max', 'ar_dB_theta0', 'pol_max', 'pol_theta0'):
                if k in r:
                    rad[k] = round(r[k], 1) if isinstance(r[k], float) else r[k]
            f['radiacion'] = rad
            mejores.append(f)
            print('  RADIACIÓN', json.dumps(f['cambios'], ensure_ascii=False), json.dumps(rad, ensure_ascii=False), flush=True)
        json.dump({'tipo': clave, 'f_MHz': f_MHz, 'bw_MHz': bw_MHz, 'sustrato': sus_nombre, 'paso': paso,
                   'filas': filas, 'mejores': mejores}, open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False, default=float)
        with open(os.path.join(carpeta, 'resumen.csv'), 'w', encoding='utf-8') as fh:
            ks = sorted({k for f in filas for k in f['cambios']})
            fh.write(';'.join(ks + ['peor_banda_dB', 's11_obj_dB', 'f_res_MHz', 'banda_10dB', 's']) + '\n')
            for f in filas:
                fh.write(';'.join([str(f['cambios'].get(k, '')) for k in ks] +
                                  [str(f.get(k, f.get('error', ''))) for k in ('peor_banda_dB', 's11_obj_dB', 'f_res_MHz', 'banda_10dB', 's')]) + '\n')
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()