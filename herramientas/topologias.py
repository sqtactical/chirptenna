"""Topologías nuevas de prueba (08-11): torniquete de dipolos para polarización circular, antena de ranura e IFA de tres bandas.

Uso (desde la raíz):
    python herramientas/topologias.py <torniquete|ranura|ifa_tribanda> [param=v1,v2,…]… [--f MHz] [--bandas "lo-hi;lo-hi"]
                                      [--sustrato S] [--etiqueta E] [--paso mm] [--sin-radiacion] [--solo-lista]

  Es un banco de pruebas, no tipos del catálogo (no salen en la interfaz ni se exportan todavía). Cada configuración es una
  simulación; los resultados van a salidas/_barridos/<E> (resultados.jsonl y resumen.json) y el peor S11 de cada banda se
  imprime ordenado. `param=` con varios valores barre todas las combinaciones.

  torniquete   (GPS L1 por defecto: --f 1575.42): dos dipolos cruzados, uno por cada cara del FR4, alimentados a la vez por un
               único puerto vertical en el centro (cada cara es una «L»: un brazo del dipolo X y uno del Y). Con largos distintos
               los dos dipolos quedan uno inductivo y otro capacitivo: el desfase de ~90° sale de la propia longitud, sin red.
               Parámetros: s (escala del largo base ≈ 55200/f_MHz mm), d (asimetría: largo X = L(1+d), largo Y = L(1−d)),
               ancho (mm de los brazos), c (lado del cuadrado central, mm).
  ranura       (2,4 GHz por defecto): ranura de λ/2 en la cara inferior (masa) alimentada por una microstrip que la cruza y
               acaba en un stub abierto. Parámetros: s (escala del largo de la ranura, base λ0/(2√((εr+1)/2))), ws (ancho de la
               ranura, mm), stub (largo del stub tras la ranura, mm), xoff (desplazamiento de la línea respecto al centro de la
               ranura, mm), masa (lado de la masa en múltiplos del largo de la ranura, defecto 2,2).
  ifa_tribanda (868 MHz + 2,4 + 5,8 GHz, --bandas por defecto "863-870;2400-2483.5;5725-5875"): IFA con el brazo principal
               ×1,17 y dos ramas cortas que salen del pie de la F. Parámetros: x (escala del brazo), k2 y h2 (largo y altura de
               la rama de 2,4 GHz), k3 y h3 (idem para 5,8 GHz). Simula en banda ancha (0,45–7,3 × 868 MHz).
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


# ------------------------------------------------------------------ generadores
def torniquete(tipos, g, sus, f_MHz, p):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from antenas import ajuste
    from antenas.modelo import Antena
    L = 55200.0/f_MHz*p.get('s', 1.0)
    d = p.get('d', 0.08)
    w, c = p.get('ancho', 3.0), p.get('c', 3.0)
    lx, ly = L*(1 + d), L*(1 - d)
    cuadro = g.rectangulo(-c/2, -c/2, c/2, c/2)
    sup = unary_union([g.engordar([(0, 0), (-lx, 0)], w), g.engordar([(0, 0), (0, ly)], w), cuadro])
    inf = unary_union([g.engordar([(0, 0), (lx, 0)], w), g.engordar([(0, 0), (0, -ly)], w), cuadro])
    m = 3.0
    contorno = g.rectangulo(-lx - m, -ly - m, lx + m, ly + m)
    return Antena(tipo='torniquete', parametros=dict(p), capas={'F.Cu': sup, 'B.Cu': inf}, ajuste=ajuste.vacio(),
                  radiador=sup, contorno=contorno, zona_libre=contorno,
                  puerto={'tipo': 'pasante', 'borde': (0.0, 0.0), 'direccion': (0, 1), 'alimentacion': (0.0, 0.0),
                          'ancho_linea': c, 'ancho_puerto': c},
                  info={'placa_mm': [round(2*(lx + m), 1), round(2*(ly + m), 1)], 'pista_minima_mm': min(w, c),
                        'largo_x_mm': round(lx, 2), 'largo_y_mm': round(ly, 2), 'avisos': []})


def ranura(tipos, g, sus, f_MHz, p):
    from shapely.ops import unary_union
    from antenas import ajuste
    from antenas.modelo import Antena
    from antenas.materiales import C0, ancho_microstrip
    lam0 = C0/(f_MHz*1e6)*1e3
    ls = 0.5*lam0/math.sqrt((sus.er + 1)/2)*p.get('s', 1.0)
    ws, stub, xoff = p.get('ws', 3.0), p.get('stub', 17.0), p.get('xoff', 0.0)
    gx = gy = ls*p.get('masa', 2.2)
    w50 = ancho_microstrip(50, sus.er, sus.h)
    masa = g.rectangulo(-gx/2, -gy/2, gx/2, gy/2).difference(g.rectangulo(-ls/2, -ws/2, ls/2, ws/2))
    linea = g.rectangulo(xoff - w50/2, -gy/2 + 0.5, xoff + w50/2, ws/2 + stub)
    contorno = g.rectangulo(-gx/2, -gy/2, gx/2, gy/2)
    return Antena(tipo='ranura', parametros=dict(p), capas={'F.Cu': linea, 'B.Cu': masa}, ajuste=ajuste.vacio(),
                  radiador=linea, contorno=contorno, zona_libre=contorno,
                  puerto={'borde': (xoff, -gy/2), 'direccion': (0, 1), 'alimentacion': (xoff, -gy/2 + 0.5),
                          'ancho_linea': w50, 'largo_linea_mm': gy/2 - ws/2},
                  info={'placa_mm': [round(gx, 1), round(gy, 1)], 'pista_minima_mm': w50, 'hueco_minimo_mm': ws,
                        'largo_ranura_mm': round(ls, 2), 'avisos': []})


def ifa_tribanda(tipos, g, sus_nombre, f_MHz, p):
    from shapely.ops import unary_union
    base = tipos.dimensionar('ifa', f_MHz*1e6, {}, sus_nombre)
    base.pop('_aviso', None)
    base['largo_brazo'] = round(base['largo_brazo']*p.get('x', 1.17), 3)
    a = tipos.generar('ifa', base, sus_nombre)
    w = base.get('ancho_pista', 1.0)
    lg = a.puerto['alimentacion'][1]
    le = tipos._longitud_equivalente('ifa', base)
    h = base['altura']
    partes = [a.capas['F.Cu']]
    for k, hk, f_k in ((p.get('k2', 1.0), p.get('h2', 0.6), 2441.75), (p.get('k3', 1.0), p.get('h3', 0.3), 5800.0)):
        l_k = k*le*f_MHz/f_k
        partes.append(g.engordar([(0.0, lg + hk*h), (max(l_k - hk*h, 3.0), lg + hk*h)], w))
    cobre = unary_union(partes)
    margen = base.get('margen_borde', 2.0)
    a.capas['F.Cu'] = cobre
    a.radiador = unary_union([a.radiador, cobre])
    a.contorno = unary_union([a.contorno, cobre.buffer(margen)])
    a.zona_libre = unary_union([a.zona_libre, cobre.buffer(margen)])
    a.info['hueco_minimo_mm'] = min(a.info.get('hueco_minimo_mm') or 99, 0.25*h - w)
    a.info['placa_mm'] = [round(a.contorno.bounds[2] - a.contorno.bounds[0], 2), round(a.contorno.bounds[3] - a.contorno.bounds[1], 2)]
    return a


TOPOLOGIAS = {
    # nombre: (generador, f_MHz, bandas, rango, con radiación, usa el nombre del sustrato (True) o el objeto (False))
    'torniquete': (torniquete, 1575.42, '1565.42-1585.42', (0.6, 1.4), True, False),
    'ranura': (ranura, 2441.75, '2400-2483.5', (0.6, 1.4), True, False),
    'ifa_tribanda': (ifa_tribanda, 868.0, '863-870;2400-2483.5;5725-5875', (0.45, 7.3), False, True),
}


def main():
    pos, par_txt, opt, i = [], {}, {'sustrato': 'FR4 JLC 1,6 mm'}, 1
    args = sys.argv[1:]
    while i - 1 < len(args):
        a = args[i - 1]
        if a in ('--solo-lista', '--sin-radiacion'):
            opt[a[2:]] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par_txt[k] = [float(x.replace(',', '.')) for x in v.split(',')]
        else:
            pos.append(a)
        i += 1
    if not pos or pos[0] not in TOPOLOGIAS:
        sys.exit(__doc__)
    nombre = pos[0]
    gen, f_def, bandas_def, rango, con_rad, por_nombre = TOPOLOGIAS[nombre]
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion, geometria as g
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    sus_nombre = opt['sustrato']
    s = tipos.sustrato(sus_nombre)
    f = float(opt.get('f', f_def))
    bandas = [tuple(float(x) for x in b.split('-')) for b in opt.get('bandas', bandas_def).split(';')]
    con_rad = con_rad and 'sin-radiacion' not in opt
    ks = list(par_txt)
    configs = [dict(zip(ks, comb)) for comb in itertools.product(*[par_txt[k] for k in ks])] or [{}]
    antenas = [(c, gen(tipos, g, sus_nombre if por_nombre else s, f, c)) for c in configs]
    if 'solo-lista' in opt:
        for c, a in antenas:
            extra = {k: v for k, v in a.info.items() if k in ('largo_x_mm', 'largo_y_mm', 'largo_ranura_mm')}
            print(json.dumps(c), 'placa', a.info['placa_mm'], json.dumps(extra))
        return
    etiqueta = opt.get('etiqueta') or f'T_{nombre}_{datetime.datetime.now():%m%d_%H%M}'
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
    f_max = max(rango[1]*f, max(b[1] for b in bandas))
    lam_min = simulacion.C0/(f_max*1e6)*1e3

    def natural(a):
        sup = a.cobre('F.Cu')
        w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
        s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
        return max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2, cfg['factor_detalle']*s_min/2), 0.08)
    paso = float(opt['paso']) if 'paso' in opt else round(0.9*min(natural(a) for _, a in antenas), 3)
    f_centro = f
    print(f'=== {etiqueta}: {nombre} a {f:g} MHz, {len(configs)} configuraciones, bandas {bandas}, malla {paso} mm', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for c, a in antenas:
            clave_c = json.dumps(c, sort_keys=True)
            if clave_c in hechos:
                filas.append(hechos[clave_c])
                continue
            t0 = time.time()
            fila = {'cambios': c, 'placa': a.info.get('placa_mm'), 'paso': paso}
            try:
                f_rad = sum(bandas[0])/2*1e6
                r = simulacion.simular(a, s, f_centro*1e6, 'normal', nf2ff=con_rad, progreso=lambda m: None, rango=rango,
                                       paso=paso, f_radiacion=f_rad if con_rad else None)
                fh = r['f_Hz']/1e6
                s11 = 20*np.log10(np.abs(r['s11']))
                fila['bandas'] = {f'{lo:g}-{hi:g}': round(float(s11[(fh >= lo) & (fh <= hi)].max()), 1) for lo, hi in bandas}
                fila['peor'] = max(fila['bandas'].values())
                fila['resonancias_MHz'] = [int(round(fh[j])) for j in range(1, len(fh) - 1)
                                           if s11[j] < s11[j - 1] and s11[j] <= s11[j + 1] and s11[j] < -6]
                if con_rad:
                    fila['radiacion'] = barrido._radiacion(r)
            except Exception as ex:
                fila['error'] = f'{type(ex).__name__}: {ex}'
            fila['s'] = round(time.time() - t0)
            filas.append(fila)
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print(' ', json.dumps(fila, ensure_ascii=False, default=float), flush=True)
        buenas = sorted([x for x in filas if 'peor' in x], key=lambda x: x['peor'])
        print('\n--- ordenadas por el peor S11 de todas las bandas ---')
        for x in buenas[:8]:
            rad = x.get('radiacion') or {}
            print(f"  {x['peor']:6.1f} dB  {json.dumps(x['cambios'])}  {x['bandas']}  placa {x['placa']}  η {rad.get('eficiencia_%')} "
                  f"AR {rad.get('ar_dB_theta0')} {rad.get('pol_theta0')}  resonancias {x['resonancias_MHz']}")
        json.dump({'tipo': nombre, 'f_MHz': f, 'bandas': opt.get('bandas', bandas_def), 'sustrato': sus_nombre, 'paso': paso,
                   'filas': filas}, open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'), indent=1,
                  ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
