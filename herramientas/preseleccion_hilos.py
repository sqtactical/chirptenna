"""Preselección de dipolos y Yagi con el método de momentos de hilos (`antenas/hilos.py`), en segundos.

Uso (desde la raíz):
    python herramientas/preseleccion_hilos.py dipolo [f_MHz]                  largo del dipolo resonante en el aire
    python herramientas/preseleccion_hilos.py yagi [f_MHz] [--directores N] [--evals N] [--radio mm]

`yagi` busca con la optimización bayesiana (`antenas/optimizacion.py`) el factor del reflector, la separación del
reflector, el factor de los directores y su separación que dan más ganancia hacia delante con buena relación
delante/atrás, y escribe el rango de `factor_reflector`, `separacion_reflector`, `factor_director` y
`separacion_director` para pasar a `barrido.py yagi_boom … --modo bayes`.

IMPORTANTE: es el aire, sin FR4, sin pista de alimentación y con hilos finos. El rango sirve para acotar el barrido de
openEMS (la placa real baja las frecuencias y encoge los elementos un 5–15 %), no para fabricar. Ver el encabezado de
`antenas/hilos.py`. Resultado en `salidas/_preseleccion/`.
"""
import json
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import numpy as np

from antenas import hilos, optimizacion

LARGO_EXCITADO = 0.47            # en λ0; el excitado de una Yagi se acorta un poco frente al aislado (0,476)


def _opcion(args, nombre, defecto, tipo=float):
    if nombre in args:
        return tipo(args[args.index(nombre) + 1])
    return tipo(defecto)


def evaluar_yagi(lam, radio, n_dir, factor_refl, sep_refl, factor_dir, sep_dir):
    """Ganancia hacia delante (dBi), relación delante/atrás (dB) e impedancia de una Yagi en el aire (longitudes en λ)."""
    l_exc = LARGO_EXCITADO
    largos = [factor_refl*l_exc, l_exc] + [factor_dir*l_exc]*n_dir
    pos = [-sep_refl, 0.0] + [sep_dir*(i + 1) for i in range(n_dir)]
    res = hilos.resolver(hilos.yagi([l*lam for l in largos], [p*lam for p in pos], radio), hilos.C0/(lam*1e-3), excitado=1)
    g_ad = hilos.directividad_en(res, 90.0, 90.0)
    g_at = hilos.directividad_en(res, 90.0, 270.0)
    return g_ad, g_ad - g_at, res['Z']


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('dipolo', 'yagi'):
        sys.exit(__doc__)
    modo = args[0]
    f_MHz = float(args[1].replace(',', '.')) if len(args) > 1 and not args[1].startswith('--') else 2441.75
    f = f_MHz*1e6
    lam = hilos.C0/f*1e3
    radio = _opcion(args, '--radio', 0.5)
    os.makedirs(os.path.join(RAIZ, 'salidas', '_preseleccion'), exist_ok=True)
    if modo == 'dipolo':
        L = hilos.largo_dipolo_resonante(f, radio)
        r = hilos.resolver(hilos.dipolo(L, radio), f)
        sal = {'f_MHz': f_MHz, 'radio_mm': radio, 'largo_mm': round(L, 2), 'largo_en_lambda': round(L/lam, 4),
               'Z': [round(r['Z'].real, 1), round(r['Z'].imag, 1)], 'directividad_dBi': round(hilos.directividad(r)[0], 2)}
        print(json.dumps(sal, ensure_ascii=False))
        json.dump(sal, open(os.path.join(RAIZ, 'salidas', '_preseleccion', f'dipolo_{f_MHz:g}.json'), 'w', encoding='utf-8'), indent=1)
        return
    n_dir = int(_opcion(args, '--directores', 3, int))
    evals = int(_opcion(args, '--evals', 60, int))
    esp = optimizacion.Espacio({'factor_reflector': ('x', (1.0, 1.15)), 'separacion_reflector': ('v', (0.10, 0.30)),
                                'factor_director': ('x', (0.80, 0.98)), 'separacion_director': ('v', (0.10, 0.40))})

    def costo(u):
        c = esp.decodificar(u)
        g, fb, z = evaluar_yagi(lam, radio, n_dir, c['factor_reflector'][1], c['separacion_reflector'][1],
                                c['factor_director'][1], c['separacion_director'][1])
        return -g - 0.2*min(fb, 20.0), g, fb, z

    X = optimizacion.diseno_inicial(10, esp.dimension, 1)
    filas = [costo(u) for u in X]
    y = np.array([f_[0] for f_ in filas])
    while len(X) < evals:
        u = optimizacion.proponer(X, y, 1)[0]
        X = np.vstack([X, u])
        filas.append(costo(u))
        y = np.append(y, filas[-1][0])
    ib = int(np.argmin(y))
    c = esp.decodificar(X[ib])
    _, g, fb, z = filas[ib]
    cerca = [esp.decodificar(X[i]) for i in np.argsort(y)[:max(4, evals//8)]]
    rango = {k: [min(d[k][1] for d in cerca), max(d[k][1] for d in cerca)] for k in c}
    sal = {'f_MHz': f_MHz, 'directores': n_dir, 'radio_mm': radio, 'mejor': {k: v[1] for k, v in c.items()},
           'ganancia_adelante_dBi': round(g, 2), 'delante_atras_dB': round(fb, 1), 'Z_ohm': [round(z.real, 1), round(z.imag, 1)],
           'rango_de_los_mejores': rango, 'evaluaciones': len(X),
           'aviso': 'en el aire y con hilos finos: acota el barrido de openEMS, no sustituye a la simulación de la placa'}
    print(json.dumps(sal, ensure_ascii=False, indent=1))
    json.dump(sal, open(os.path.join(RAIZ, 'salidas', '_preseleccion', f'yagi_{n_dir}d_{f_MHz:g}.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print(f'\nSiguiente paso: python herramientas/barrido.py yagi_boom {f_MHz:g} --modo bayes --centrar '
          + ' '.join(f'{k}={rango[k][0]:.3g},{rango[k][1]:.3g}' for k in rango) + f' directores={n_dir} --evals 20 --radiacion')


if __name__ == '__main__':
    main()
