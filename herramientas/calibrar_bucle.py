"""Calibra la estimación de la frecuencia del bucle (`bucle.estimar_f`) con simulaciones del anillo SIN red.

Uso (desde la raíz):
    python herramientas/calibrar_bucle.py [--forma 0|1] [--f MHz,MHz,…] [--solo-lista]

  --forma   0 = cuadrado, 1 = redondo (por defecto 1)
  --f       frecuencias de diseño (por defecto 780,950,2200,2700: dos tamaños en cada banda)
Para cada frecuencia, `tipos.dimensionar('bucle', f, {forma})` da el lado y el condensador con la calibración actual, se simula
el anillo (FR4 de 1,6 mm, GPU) y la resonancia simulada es el paso por cero de la reactancia quitando la línea de 50 Ω hasta el
anillo (`simulacion.simular`, criterio «reactancia nula»). El factor f_simulada/f_fórmula (sin calibrar) es el de la tabla
`bucle.CALIBRACION_REDONDO` / `CALIBRACION`. Resultados en salidas/_barridos/CAL_bucle_forma<N>/resultados.jsonl (se retoma).
"""
import os
import sys
import json
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def main():
    args = sys.argv[1:]
    opt = {'forma': '1', 'f': '780,950,2200,2700'}
    solo_lista = '--solo-lista' in args
    args = [a for a in args if a != '--solo-lista']
    for i, a in enumerate(args):
        if a in ('--forma', '--f'):
            opt[a[2:]] = args[i + 1]
    os.environ.setdefault('ANTENAS_GPU', '1')
    from antenas import tipos, simulacion, bucle
    forma = int(opt['forma'])
    sus = 'FR4 JLC 1,6 mm'
    s = tipos.sustrato(sus)
    frecs = [float(x) for x in opt['f'].split(',')]
    disenos = []
    for f in frecs:
        p = tipos.dimensionar('bucle', f*1e6, {'forma': forma}, sus, fijos=('forma',))
        p.pop('_aviso', None)
        p['ajuste'] = 0                                       # sin red en π: solo el anillo
        a = tipos.generar('bucle', p, sus)
        disenos.append((f, p, a))
        print(f"f {f:g} MHz: lado {p['lado']} mm, C {p['capacidad_pF']} pF, placa {a.info['placa_mm']}, "
              f"estimada (con calibración actual) {bucle.estimar_f(p)/1e6:.0f} MHz, sin calibrar {bucle.estimar_f(p, calibrada=False)/1e6:.0f} MHz", flush=True)
    if solo_lista:
        return
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', f'CAL_bucle_forma{forma}')
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, 'resultados.jsonl')
    hechos = {}
    if os.path.exists(ruta):
        for linea in open(ruta, encoding='utf-8'):
            try:
                d = json.loads(linea)
                hechos[d['f_diseno_MHz']] = d
            except ValueError:
                pass
    paso = None
    for f, p, a in disenos:
        if f in hechos:
            continue
        t0 = time.time()
        r = simulacion.simular(a, s, f*1e6, 'normal', nf2ff=False, progreso=lambda m: None, paso=paso)
        if paso is None:
            paso = None                                       # cada tamaño con su propia malla: los lados son muy distintos
        f_sim = r['f_resonancia_Hz']/1e6
        f_formula = bucle.estimar_f(p, calibrada=False)/1e6
        fila = {'f_diseno_MHz': f, 'lado': p['lado'], 'C_pF': p['capacidad_pF'], 'forma': forma, 'f_sim_MHz': round(f_sim, 1),
                'f_formula_MHz': round(f_formula, 1), 'factor': round(f_sim/f_formula, 4), 'criterio': r['criterio'],
                's': round(time.time() - t0)}
        open(ruta, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False) + '\n')
        hechos[f] = fila
        print(json.dumps(fila, ensure_ascii=False), flush=True)
    print('\n--- factor f_simulada / f_fórmula (sin calibrar) ---')
    for f in frecs:
        x = hechos.get(f)
        if x:
            print(f"  fórmula {x['f_formula_MHz']:.0f} MHz → factor {x['factor']}  (simulada {x['f_sim_MHz']} MHz, lado {x['lado']} mm, C {x['C_pF']} pF)")


if __name__ == '__main__':
    main()
