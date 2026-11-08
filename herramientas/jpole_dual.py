"""Prueba de J-pole de dos bandas: un adaptador compartido y dos radiadores en abanico (experimento, no es un tipo del catálogo).

Uso (desde la raíz):
    python herramientas/jpole_dual.py <f_baja_MHz> --bandas "lo-hi;lo-hi" [k2=v1,v2,…] [sep2=…] [alto2=…] [toma=…] [factor_adaptador=…]
                                      [--modo union (a2=… toma2=… w2=…)] [--modo multi f2=… f3=… f4=… k_i a_i toma_i sep2 --rango-max N] [--koch2 N] [--koch N] [--etiqueta E] [--sustrato S] [--solo-lista]

  El adaptador (dos brazos unidos por una barra, toma de coaxial) y el radiador 1 son los de la J-pole normal
  para f_baja. El radiador 2 parte del brazo largo, a la altura `alto2` × el adaptador, y sube en paralelo al 1, a
  `sep2` mm de él; su largo es k2 × (largo del radiador 1) × f_baja / f_alta, con f_alta = centro de la última banda.
  Con la relación de bandas ≈ 3 el adaptador de λ/4 de la baja se comporta como de 3λ/4 en la alta (un cortocircuito
  visto desde la toma sigue siendo un bucle inductivo/alto), así que un solo adaptador puede servir a las dos.
  `--koch N`: radiador 1 de Koch de iteración N (el 2 queda recto).
Una simulación por configuración (rango 0,45–3,8 × f_baja, sin diagrama). Resultados en salidas/_barridos/<E>.
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


def construir(tipos, g, nombre_sus, base, k2, sep2, alto2, f_baja, f_alta, clave='jpole'):
    """J-pole de `base` con un segundo radiador recto en abanico."""
    from shapely.ops import unary_union
    a = tipos.generar(clave, base, nombre_sus)
    w = base['ancho_pista']
    ls = a.info['largo_adaptador_mm']
    gap = base['hueco']
    xr = gap/2 + w/2
    y0 = alto2*ls
    l1 = a.info['longitud_traza_mm']
    l2 = k2*l1*f_baja/f_alta
    x2 = xr + sep2 + w
    union = g.engordar([(xr, y0), (x2, y0)], w)
    rad2 = g.engordar([(x2, y0), (x2, ls + l2)], w)
    cobre = unary_union([a.capas['F.Cu'], union, rad2])
    a.capas['F.Cu'] = cobre
    a.radiador = cobre
    a.contorno = g.contorno_placa([cobre.buffer(base.get('margen_borde', 2.0))], int(base.get('contorno', 1)))
    a.zona_libre = a.contorno
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, sep2)
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_radiador2_mm'] = round(l2, 2)
    return a


def construir_union(tipos, g, nombre_sus, base, k2, sep2, a2, toma2, f_baja, f_alta, clave='jpole', koch2=0, w2=None):
    """Dos J-pole unidas (diseño del usuario): comparten el brazo corto (masa) y la barra de cortocircuito.

    A la derecha del brazo corto, la J-pole normal (adaptador y radiador 1 para f_baja). A la izquierda, el brazo largo
    de la segunda: adaptador de a2 × (λ/4 de f_alta, es decir ls × f_baja/f_alta) y radiador 2 que se separa `sep2` mm
    hacia fuera al salir del adaptador para no acoplarse al brazo corto. Los dos brazos largos son el «vivo»: se unen
    por una tira en B.Cu con una vía en cada extremo (de la toma del 1 a la toma `toma2` del 2, fracción de su adaptador).
    """
    from shapely.ops import unary_union
    a = tipos.generar(clave, base, nombre_sus)
    w = base['ancho_pista']
    ls = a.info['largo_adaptador_mm']
    gap = base['hueco']
    xl, xr = -(gap/2 + w/2), gap/2 + w/2
    x2 = xl - (gap + w)
    # el adaptador 2 se escala con el de la J-pole RECTA de f_baja, no con el del radiador de Koch (en jpole_koch es un 35 % más
    # largo: usarlo alargaba el adaptador 2 y descentraba la banda alta en las pruebas F_* con --koch)
    ls_ref = ls if clave == 'jpole' else tipos.generar('jpole', dict(tipos.dimensionar('jpole', f_baja*1e6, {}, nombre_sus), factor_adaptador=base.get('factor_adaptador', 1.0)), nombre_sus).info['largo_adaptador_mm']
    ls2 = a2*ls_ref*f_baja/f_alta
    from antenas import jpole as jp
    # λ/2 recto a f_baja (lo que mide el radiador 1 si no fuese fractal): la referencia del radiador 2 aunque el 1 sea de Koch
    br = tipos.dimensionar('jpole', f_baja*1e6, {}, nombre_sus)
    l1 = br['largo_radiador']
    l2 = k2*l1*f_baja/f_alta
    x3 = x2 - sep2
    w2 = w2 or w
    if koch2:
        # radiador 2 de Koch: el largo extremo a extremo se acorta para que el equivalente sea l2; las muescas, hacia fuera (a la izquierda)
        L2 = l2/(1 + 0.35*((4/3)**int(koch2) - 1))
        pts2 = g.koch(int(koch2), (0, 0), (0, L2), base.get('angulo', 60)) + [x3, ls2]
        rad2 = g.engordar(pts2, w2)
        l2 = L2
    else:
        rad2 = g.engordar([(x3, ls2), (x3, ls2 + l2)], w2)
    piezas = [a.capas['F.Cu'],
              g.engordar([(x2, ls2), (x2, 0), (xl, 0)], w),                  # brazo largo 2 y barra hasta el brazo corto
              g.engordar([(x2, ls2), (x3, ls2)], w), rad2]                  # desvío hacia fuera y radiador 2
    cobre = unary_union(piezas)
    y_t1 = a.puerto['alimentacion'][1]
    y_t2 = toma2*ls2
    a.capas['F.Cu'] = cobre
    a.capas['B.Cu'] = g.engordar([(xr, y_t1), (x2, y_t2)], w)
    a.vias = [(xr, y_t1), (x2, y_t2)]
    a.radiador = cobre
    a.contorno = g.contorno_placa([unary_union([cobre, a.capas['B.Cu']]).buffer(base.get('margen_borde', 2.0))], int(base.get('contorno', 1)))
    a.zona_libre = a.contorno
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, gap)
    a.info['pista_minima_mm'] = min(a.info.get('pista_minima_mm') or 99, w2)
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_radiador2_mm'] = round(l2, 2)
    a.info['largo_adaptador2_mm'] = round(ls2, 2)
    return a


def construir_union_multi(tipos, g, nombre_sus, base, extras, f_baja, clave='jpole'):
    """Varias J-pole unidas (tres o cuatro bandas): la J-pole de f_baja y hasta tres brazos largos más, todos sobre una barra común.

    Disposición: [brazo largo 2 | masa | brazo largo 1 (f_baja) | masa 3 | brazo largo 3 | masa 5 | brazo largo 4]. El brazo 2 va a la
    izquierda de la masa del par original, con el radiador desviado `sep` mm hacia fuera; los brazos 3 y 4 van a la derecha, cada
    uno con su propio brazo de masa de la longitud de su adaptador (λ/4 de su banda × a), y el radiador recto hacia arriba. Todos los
    brazos largos son el «vivo»: se unen al del brazo 1 por tiras en B.Cu con una vía en cada extremo (a la altura `toma` × su adaptador).
    `extras`: lista de dicts con f (MHz de la banda), k (largo del radiador × el λ/2 teórico), a (largo del adaptador × el teórico),
    toma (fracción del adaptador) y sep (desvío del radiador, solo el brazo 2).
    """
    from shapely.ops import unary_union
    a = tipos.generar(clave, base, nombre_sus)
    w = base['ancho_pista']
    ls = a.info['largo_adaptador_mm']
    gap = base['hueco']
    d = gap + w
    xl, xr = -(gap/2 + w/2), gap/2 + w/2
    br = tipos.dimensionar('jpole', f_baja*1e6, {}, nombre_sus)
    l1 = br['largo_radiador']
    y_t1 = a.puerto['alimentacion'][1]
    piezas = [a.capas['F.Cu']]
    puentes, vias = [], [(xr, y_t1)]
    xmin, xmax = xl, xr
    derecha = xr
    largos = []
    for idx, e in enumerate(extras):
        ls_i = e['a']*ls*f_baja/e['f']
        l_i = e['k']*l1*f_baja/e['f']
        wi = e.get('w') or w                                 # ancho de pista del brazo (más fina en las bandas altas)
        largos.append((round(ls_i, 2), round(l_i, 2)))
        if idx == 0:
            x_l = xl - d
            x_rad = x_l - e.get('sep', 6.0)
            piezas += [g.engordar([(x_l, 0), (x_l, ls_i), (x_rad, ls_i), (x_rad, ls_i + l_i)], wi)]
            xmin = min(xmin, x_l)
        else:
            x_s = derecha + d
            x_l = x_s + d
            piezas += [g.engordar([(x_s, 0), (x_s, ls_i)], wi), g.engordar([(x_l, 0), (x_l, ls_i + l_i)], wi)]
            derecha = x_l
            xmax = max(xmax, x_l)
        y_t = e['toma']*ls_i
        puentes.append(g.engordar([(xr, y_t1), (x_l, y_t)], min(w, wi)))
        vias.append((x_l, y_t))
    piezas.append(g.engordar([(xmin, 0), (xmax, 0)], w))                 # barra común de cortocircuito
    cobre = unary_union(piezas)
    inf = unary_union(puentes)
    a.capas['F.Cu'] = cobre
    a.capas['B.Cu'] = inf
    a.vias = vias
    a.radiador = cobre
    a.contorno = g.contorno_placa([unary_union([cobre, inf]).buffer(base.get('margen_borde', 2.0))], int(base.get('contorno', 1)))
    a.zona_libre = a.contorno
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, gap)
    a.info['pista_minima_mm'] = min([a.info.get('pista_minima_mm') or 99, w] + [e['w'] for e in extras if e.get('w')])
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    a.info['largo_radiador2_mm'] = largos[0][1] if largos else 0
    a.info['adaptadores_y_radiadores_mm'] = largos
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
    if not pos or 'bandas' not in opt:
        sys.exit(__doc__)
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion, geometria as g
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    f_baja = float(pos[0].replace(',', '.'))
    sus = opt['sustrato']
    s = tipos.sustrato(sus)
    bandas = [tuple(float(x) for x in b.split('-')) for b in opt['bandas'].split(';')]
    f_alta = sum(bandas[-1])/2
    clave = 'jpole_koch' if 'koch' in opt else 'jpole'
    fijos = {k: par_txt[k][0] for k in ('toma', 'factor_adaptador', 'hueco', 'ancho_pista') if k in par_txt and len(par_txt[k]) == 1}
    if 'koch' in opt:
        fijos['iteracion'] = int(opt['koch'])
    base = tipos.dimensionar(clave, f_baja*1e6, dict(fijos), sus, fijos=tuple(fijos))
    base.pop('_aviso', None)
    multi = opt.get('modo') == 'multi'
    union = opt.get('modo') == 'union'
    ejes = {'k2': par_txt.get('k2', [1.0]), 'sep2': par_txt.get('sep2', [6.0])}
    if multi:
        # f2, f3, f4 (MHz): bandas de los brazos extra; para cada una k, a, toma (y sep en la 2)
        nb = [i for i in (2, 3, 4) if f'f{i}' in par_txt]
        ejes = {}
        for i in nb:
            for n, v in (('k', 1.0), ('a', 1.0), ('toma', 0.3)) + ((('sep', 6.0),) if i == 2 else ()) + ((('w', None),) if f'w{i}' in par_txt else ()):
                ejes[f'{n}{i}'] = par_txt.get(f'{n}{i}', [v])
    elif union:
        ejes.update({'a2': par_txt.get('a2', [1.0]), 'toma2': par_txt.get('toma2', [0.3])})
        if 'w2' in par_txt:
            ejes['w2'] = par_txt['w2']
    else:
        ejes['alto2'] = par_txt.get('alto2', [1.0])
    for k in ('toma', 'factor_adaptador', 'hueco'):
        if k in par_txt and len(par_txt[k]) > 1:
            ejes[k] = par_txt[k]
    ks = list(ejes)
    configs = []
    for comb in itertools.product(*[ejes[k] for k in ks]):
        c = dict(zip(ks, comb))
        q = dict(base)
        for k in ('toma', 'factor_adaptador', 'hueco'):
            if k in c:
                q[k] = c[k]
        configs.append((c, q))
    etiqueta = opt.get('etiqueta') or f'JD_{datetime.datetime.now():%m%d_%H%M}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    rmax = float(opt.get('rango-max', opt.get('rango_max', 3.8)))     # --rango-max N (el analizador deja el guion en la clave)
    if multi:
        def extras_de(c):
            return [dict(f=par_txt[f'f{i}'][0], k=c[f'k{i}'], a=c[f'a{i}'], toma=c[f'toma{i}'], sep=c.get('sep2', 6.0), w=c.get(f'w{i}')) for i in nb]
        antenas = [(c, q, construir_union_multi(tipos, g, sus, q, extras_de(c), f_baja, clave)) for c, q in configs]
    elif union:
        antenas = [(c, q, construir_union(tipos, g, sus, q, c['k2'], c['sep2'], c['a2'], c['toma2'], f_baja, f_alta, clave, int(opt.get('koch2', 0)), c.get('w2'))) for c, q in configs]
    else:
        antenas = [(c, q, construir(tipos, g, sus, q, c['k2'], c['sep2'], c['alto2'], f_baja, f_alta, clave)) for c, q in configs]
    if 'solo-lista' in opt:
        for c, q, a in antenas:
            sup = a.cobre('F.Cu')
            print(json.dumps(c), 'placa', a.info['placa_mm'], 'radiador 2', a.info['largo_radiador2_mm'], 'mm',
                  'pista_min %.2f hueco_min %.2f' % (simulacion.ancho_minimo(sup, 3.0), simulacion.hueco_minimo(sup, 3.0)))
        return
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
    lam_min = simulacion.C0/(rmax*f_baja*1e6)*1e3

    def natural(a):
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        return max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2), 0.08)
    paso = float(opt['paso']) if 'paso' in opt else round(0.9*min(natural(a) for _, _, a in antenas), 3)
    print(f'=== {etiqueta}: {clave} dual, base a {f_baja:g} MHz, {len(configs)} configuraciones, bandas {opt["bandas"]}, malla {paso} mm', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for c, q, a in antenas:
            clave_c = json.dumps(c, sort_keys=True)
            if clave_c in hechos:
                filas.append(hechos[clave_c])
                continue
            t0 = time.time()
            fila = {'cambios': c, 'placa': a.info.get('placa_mm'), 'radiador2_mm': a.info['largo_radiador2_mm'], 'paso': paso, 'brazos_mm': a.info.get('adaptadores_y_radiadores_mm')}
            try:
                r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=False, progreso=lambda m: None, rango=(0.45, rmax), paso=paso)
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
