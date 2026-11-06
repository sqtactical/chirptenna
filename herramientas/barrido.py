"""Barrido de parámetros de cualquier tipo de antena, simulando con openEMS (GPU por defecto).

Uso (desde la raíz):
    python herramientas/barrido.py <tipo> <f_MHz | banda> [param=v1,v2,…]… [opciones]

  tipo      clave del catálogo (monopolo_koch, parche_circular, vivaldi…)
  f_MHz     frecuencia objetivo, o el nombre de una banda («2,4 GHz», «868», «915 ISM»…)
  param=…   un valor fija el parámetro; varios valores, separados por comas, lo barren. Los parámetros no
            nombrados salen de `tipos.dimensionar` (tamaño ajustado a la frecuencia). Un valor con «x» delante
            (`alto=x0.9,x1,x1.1`) es un factor sobre el que da `dimensionar` (o sobre el diseño centrado con
            --centrar): sirve para cualquier banda. El primer valor de cada lista es el de la configuración base.

Opciones:
  --centrar         antes de barrer, ajusta el tamaño principal a la frecuencia por simulación (secante,
                    `simulacion.ajustar`) y barre alrededor de ese diseño centrado; guarda su diagrama
  --modo M          cruz (recomendado con --centrar): la base, cada parámetro por separado y, al final, la
                    combinación de los mejores valores; grid (por defecto): todas las combinaciones;
                    uno: solo la base y cada parámetro por separado
  --corte N         se para si las N primeras configuraciones salen todas peor de −3 dB (por defecto 3; 0 = nunca)
  --bw MHz          ancho de la banda objetivo (por defecto el de la banda; 5 MHz si f es un número suelto)
  --sustrato S      por defecto «FR4 JLC 1,6 mm»
  --etiqueta E      nombre de la carpeta de resultados (salidas/_barridos/<E>); por defecto tipo_f_fecha
  --paso mm         paso de malla fijo (por defecto 0,9 × el más fino de todas las configuraciones)
  --top N           cuántas mejores configuraciones se repiten con el diagrama de radiación (1)
  --radiacion       calcula el diagrama (ganancia, eficiencia, dirección, polarización) en todas las
                    configuraciones, en la misma simulación (no hace falta --top)
  --max N           límite de configuraciones (60)
  --max-celdas M    salta las configuraciones con más de M millones de celdas estimadas (sin límite)
  --max-ajuste N    simulaciones máximas del centrado (5)
  --cpu             usa la CPU en vez de la GPU
  --solo-lista      solo muestra las configuraciones y el coste estimado (con --centrar, sin centrar)
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
    pos, par, opt = [], {}, {'modo': 'grid', 'top': 1, 'max': 60, 'corte': 3, 'max-ajuste': 5}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            k = a[2:]
            if k in ('cpu', 'solo-lista', 'rehacer', 'radiacion', 'centrar'):
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


def _radiacion(r):
    rad = {'directividad_dBi': round(r['directividad_dBi'], 2), 'ganancia_dBi': round(r['ganancia_dBi'], 2),
           'eficiencia_%': round(100*r['eficiencia_radiacion'], 1), 'direccion_max': r.get('direccion_max')}
    for k in ('ar_dB_max', 'ar_dB_theta0', 'pol_max', 'pol_theta0'):
        if k in r:
            rad[k] = round(r[k], 1) if isinstance(r[k], float) else r[k]
    return rad


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
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')          # no acumular GB de volcados en %TEMP%
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
    esc, conj = tipo.escala, tipo.escala_conjunta
    espec = {}                                      # parámetro -> especificaciones: ('v', valor) o ('x', factor)
    for k, vs in par_txt.items():
        if k not in nombres:
            sys.exit(f'«{k}» no es un parámetro de {clave}. Parámetros: {", ".join(nombres)}')
        espec[k] = [('x', float(v[1:])) if v.startswith('x') else ('v', _valor(nombres[k], v)) for v in vs]
    discreto = lambda k: bool(nombres[k].entero or getattr(nombres[k], 'opciones', None))
    fijos_abs = {k: sp[0][1] for k, sp in espec.items() if sp[0][0] == 'v'}      # valores absolutos: dimensionar no los toca
    disc0 = {k: v for k, v in fijos_abs.items() if discreto(k)}                   # configuración base: parámetros discretos
    cache_base = {}
    centrado = None                                  # diseño centrado por simulación (--centrar)
    base_centrada = None

    etiqueta = opt.get('etiqueta') or f'{clave}_{f_MHz:g}MHz_{datetime.datetime.now():%m%d_%H%M}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    ruta_jl = os.path.join(carpeta, 'resultados.jsonl')
    ruta_centrado = os.path.join(carpeta, 'centrado.json')

    lock = None
    if not opt.get('solo-lista') and os.environ['ANTENAS_GPU'] != '0':
        lock = _bloqueo()
    try:
        if opt.get('centrar') and not opt.get('solo-lista'):
            if os.path.exists(ruta_centrado) and not opt.get('rehacer'):
                centrado = json.load(open(ruta_centrado, encoding='utf-8'))
                base_centrada = centrado['parametros']
                print(f'=== centrado ya hecho: {json.dumps(centrado["historial"][-1], ensure_ascii=False)}', flush=True)
            else:
                t0 = time.time()
                print(f'=== centrando {clave} en {f_MHz:g} MHz (hasta {opt["max-ajuste"]} simulaciones)…', flush=True)
                q, a_c, r_c, hist = simulacion.ajustar(clave, dict(fijos_abs), sus_nombre, f_obj,
                                                       max_sim=int(opt['max-ajuste']), progreso=lambda m: None)
                lo, hi = f_MHz - bw_MHz/2, f_MHz + bw_MHz/2
                s11c = [simulacion._s11_en(r_c, (lo + (hi - lo)*i/4)*1e6)[0] for i in range(5)]
                flo, fhi = r_c['banda_Hz']
                centrado = {'parametros': q, 'historial': hist, 'peor_banda_dB': round(max(s11c), 1),
                            's11_obj_dB': round(simulacion._s11_en(r_c, f_obj)[0], 1),
                            'f_res_MHz': round(r_c['f_resonancia_Hz']/1e6, 1),
                            'paso': r_c.get('paso_malla_mm'),
                            'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
                            'radiacion': _radiacion(r_c) if 'ganancia_dBi' in r_c else None, 's': round(time.time() - t0)}
                json.dump(centrado, open(ruta_centrado, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
                base_centrada = q
                print(f'  centrado: {json.dumps({k: centrado[k] for k in ("peor_banda_dB", "s11_obj_dB", "f_res_MHz", "banda_10dB", "s")})}'
                      f'  G {(centrado["radiacion"] or {}).get("ganancia_dBi")} dBi', flush=True)

        def base_de(disc):
            """Tamaño ajustado a la frecuencia con los parámetros discretos de la combinación (iteración, orden…).
            Con --centrar, la base es el diseño centrado; las variantes discretas usan `dimensionar` corregido
            con el mismo factor de tamaño que resultó del centrado."""
            k_b = json.dumps(disc, sort_keys=True)
            if k_b in cache_base:
                return cache_base[k_b]
            if base_centrada is not None and disc == disc0:
                cache_base[k_b] = dict(base_centrada)
                return cache_base[k_b]
            fj = dict(fijos_abs)
            fj.update(disc)
            b = tipos.dimensionar(clave, f_obj, dict(fj), sus_nombre, fijos=tuple(fj))
            b.pop('_aviso', None)
            if base_centrada is not None:
                fj0 = dict(fijos_abs)
                b0 = tipos.dimensionar(clave, f_obj, dict(fj0), sus_nombre, fijos=tuple(fj0))
                factor = base_centrada[esc]/b0[esc] if b0[esc] else 1.0
                b[esc] = round(b[esc]*factor, 3)
                for kk in conj:
                    b[kk] = round(b[kk]*factor, 3)
            cache_base[k_b] = b
            return b

        def resolver(combo):
            disc = {k: sp[1] for k, sp in combo.items() if discreto(k) and sp[0] == 'v'}
            b = base_de(disc)
            cambios = {k: (sp[1] if sp[0] == 'v' else round(b[k]*sp[1], 3)) for k, sp in combo.items()}
            q = dict(b)
            prop = {k: b[k]/b[esc] for k in conj}
            for k, v in cambios.items():
                q[k] = v
                if k == esc:                              # las medidas ligadas al tamaño principal lo siguen
                    for kk, r_ in prop.items():
                        if kk not in cambios:
                            q[kk] = round(r_*v, 3)
            return cambios, q

        fijos = {k: sp[0] for k, sp in espec.items() if len(sp) == 1}
        barridos = {k: sp for k, sp in espec.items() if len(sp) > 1}
        modo = opt['modo']
        if modo in ('uno', 'cruz'):
            base_sp = {k: sp[0] for k, sp in barridos.items()}
            crudos = [dict(base_sp)]
            for k, sp in barridos.items():
                crudos += [dict(base_sp, **{k: v}) for v in sp[1:]]
        else:
            ks = list(barridos)
            crudos = [dict(zip(ks, vs)) for vs in itertools.product(*barridos.values())] if ks else [{}]
        if len(crudos) > int(opt['max']):
            sys.exit(f'{len(crudos)} configuraciones: más del límite ({opt["max"]}). Sube --max o reduce los valores.')

        cfg = simulacion.PRECISIONES['normal']
        lam_min = simulacion.C0/(1.4*f_obj)*1e3

        def natural(a):
            sup = a.cobre('F.Cu')
            w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
            s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
            return max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2,
                           cfg['factor_detalle']*s_min/2), 0.08)

        def preparar(cr):
            cambios, q = resolver(dict(fijos, **cr))
            try:
                return cambios, q, tipos.generar(clave, q, sus_nombre), None
            except Exception as ex:
                return cambios, q, None, f'{type(ex).__name__}: {ex}'

        antenas = [preparar(cr) for cr in crudos]
        naturales = [natural(a) for _, _, a, _ in antenas if a is not None]
        fino = round(0.9*min(naturales or [0.4]), 3)
        if 'paso' in opt:
            paso = float(opt['paso'])
        elif centrado and centrado.get('paso'):
            # la misma malla que el centrado (si no, la frecuencia salta ~2 %), salvo que alguna variante sea mucho más fina
            paso = centrado['paso'] if fino >= 0.5*centrado['paso'] else fino
        else:
            paso = fino

        def celdas_de(a):
            x0, y0, x1, y1 = a.contorno.bounds
            return ((x1 - x0)/paso + 40)*((y1 - y0)/paso + 40)*(s.h/paso + 24)/1e6

        print(f'=== {etiqueta}: {clave} a {f_MHz:g} MHz (banda {f_MHz - bw_MHz/2:g}–{f_MHz + bw_MHz/2:g}), {len(crudos)} '
              f'configuraciones ({modo}), malla fija {paso} mm, {"GPU" if os.environ["ANTENAS_GPU"] != "0" else "CPU"}', flush=True)
        for c, q, a, err in antenas:
            if a is None:
                print('  ✗', json.dumps(c), err)
            else:
                print(f'  · {json.dumps(c, ensure_ascii=False)}  placa {a.info.get("placa_mm")}  ~{celdas_de(a):.1f} M celdas  f_est {a.info.get("f_estimada_MHz")} MHz')
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
        con_rad = bool(opt.get('radiacion'))
        filas, cortada = [], False

        def simular_una(c, q, a):
            """Simula una configuración (o la recupera si ya estaba hecha). Devuelve la fila o None si se salta."""
            clave_c = json.dumps(c, sort_keys=True)
            if clave_c in hechos:
                print(f'  (ya hecha) {json.dumps(c, ensure_ascii=False)}', flush=True)
                return hechos[clave_c]
            if max_celdas and celdas_de(a) > max_celdas:
                print(f'  (saltada: demasiadas celdas) {json.dumps(c, ensure_ascii=False)}', flush=True)
                return None
            t0 = time.time()
            fila = {'cambios': c, 'f_MHz': f_MHz, 'paso': paso, 'parametros': q}
            try:
                r = simulacion.simular(a, s, f_obj, 'normal', nf2ff=con_rad, progreso=lambda m: None, paso=paso,
                                       f_radiacion=f_obj if con_rad else None)
                lo, hi = f_MHz - bw_MHz/2, f_MHz + bw_MHz/2
                s11 = [simulacion._s11_en(r, (lo + (hi - lo)*i/4)*1e6)[0] for i in range(5)]
                s_obj, z = simulacion._s11_en(r, f_obj)
                flo, fhi = r['banda_Hz']
                fila.update({'peor_banda_dB': round(max(s11), 1), 's11_obj_dB': round(s_obj, 1),
                             'z_obj': [round(float(z.real), 1), round(float(z.imag), 1)],
                             'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
                             'f_res_MHz': round(r['f_resonancia_Hz']/1e6, 1), 'celdas_M': round(r['celdas']/1e6, 1),
                             's': round(time.time() - t0), 'avisos': r['avisos'][:2]})
                if con_rad:
                    fila['radiacion'] = _radiacion(r)
            except Exception as ex:
                fila.update({'error': f'{type(ex).__name__}: {ex}', 's': round(time.time() - t0)})
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print('  ', json.dumps({k: v for k, v in fila.items() if k not in ('parametros', 'paso', 'f_MHz', 'avisos')},
                                   ensure_ascii=False, default=float), flush=True)
            return fila

        corte = int(opt['corte'])
        filas_cr = []                                     # (crudo, fila) de la fase 1
        for cr, (c, q, a, err) in zip(crudos, antenas):
            if a is None:
                continue
            fila = simular_una(c, q, a)
            if fila is None:
                continue
            filas.append(fila)
            filas_cr.append((cr, fila))
            if corte and len(filas) == corte and all(f.get('peor_banda_dB', 0) > -3 for f in filas):
                print(f'  (cortado: las {corte} primeras configuraciones salen peor de −3 dB)', flush=True)
                cortada = True
                break

        if modo == 'cruz' and not cortada and barridos and len(filas_cr) > 1:
            # combinación de los mejores valores de cada parámetro
            base_sp = {k: sp[0] for k, sp in barridos.items()}
            mejor_sp = {}
            for k, sp in barridos.items():
                cand = [(f.get('peor_banda_dB', 99), cr[k]) for cr, f in filas_cr
                        if all(cr[kk] == base_sp[kk] for kk in barridos if kk != k)]
                mejor_sp[k] = min(cand, key=lambda t: t[0])[1] if cand else base_sp[k]
            if mejor_sp != base_sp and mejor_sp not in [cr for cr, _ in filas_cr]:
                c, q, a, err = preparar(mejor_sp)
                print(f'  combinación de los mejores valores: {json.dumps(c, ensure_ascii=False)}', flush=True)
                if a is not None:
                    fila = simular_una(c, q, a)
                    if fila is not None:
                        fila['combinacion'] = True
                        filas.append(fila)

        buenas = sorted([f for f in filas if 'peor_banda_dB' in f], key=lambda f: f['peor_banda_dB'])
        print('\n--- ordenadas por el peor S11 en la banda ---')
        for f in buenas[:10]:
            g_ = f.get('radiacion', {})
            print(f"  {f['peor_banda_dB']:6.1f} dB  obj {f['s11_obj_dB']:6.1f}  res {f['f_res_MHz']:7.1f} MHz  banda {f['banda_10dB']}"
                  + (f"  G {g_.get('ganancia_dBi')} dBi η {g_.get('eficiencia_%')} %" if g_ else '') + f"  {json.dumps(f['cambios'], ensure_ascii=False)}")
        mejores = []
        for f in ([] if con_rad else buenas[:int(opt['top'])]):
            a = tipos.generar(clave, f['parametros'], sus_nombre)
            r = simulacion.simular(a, s, f_obj, 'normal', nf2ff=True, progreso=lambda m: None, paso=paso, f_radiacion=f_obj)
            rad = _radiacion(r)
            f['radiacion'] = rad
            mejores.append(f)
            print('  RADIACIÓN', json.dumps(f['cambios'], ensure_ascii=False), json.dumps(rad, ensure_ascii=False), flush=True)
        json.dump({'tipo': clave, 'f_MHz': f_MHz, 'bw_MHz': bw_MHz, 'sustrato': sus_nombre, 'paso': paso, 'modo': modo,
                   'cortada': cortada, 'centrado': centrado, 'filas': filas, 'mejores': mejores},
                  open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
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
