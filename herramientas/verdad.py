"""Simulaciones «de verdad»: openEMS contra el libro (idea de antenna-forge: dipolo y parche contra la teoría).

Uso (desde la raíz):
    python herramientas/verdad.py [dipolo] [parche] [monopolo] [--cpu] [--malla normal|fina]

Sin argumentos, las tres. Cada una simula el diseño que da `tipos.dimensionar` a 2441,75 MHz y compara:
  dipolo     directividad 2,15 dBi (dipolo de media onda) ±0,6 dB y resonancia a ±4 % de lo pedido
  monopolo   directividad 2,0–5,5 dBi (con la masa de 40 mm sale ~2,5 dBi, como un dipolo; con masa infinita serían 5,2 dBi) y resonancia ±4 %
  parche     resonancia a ±5 % del modelo de la cavidad (Balanis) y directividad 5–8 dBi

Resultado en `salidas/_verdad/verdad.json`. Código de salida 1 si alguna falla. No va en la CI (necesita openEMS y
minutos de cálculo): se pasa antes de una release o tras tocar `simulacion.py`, `materiales.py` o la calibración.
Las comprobaciones sin simular están en `pruebas/test_verdad.py`.
"""
import json
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

F_MHZ = 2441.75
ER, H = 4.5, 1.6


def _f_cavidad(largo, ancho):
    ee = (ER + 1)/2 + (ER - 1)/2*(1 + 12*H/ancho)**-0.5
    dl = 0.412*H*(ee + 0.3)*(ancho/H + 0.264)/((ee - 0.258)*(ancho/H + 0.8))
    return 299792458.0/(2*(largo + 2*dl)*1e-3*math.sqrt(ee))/1e6


def _simular(clave, malla):
    from antenas import tipos, simulacion
    f = F_MHZ*1e6
    p = tipos.dimensionar(clave, f)
    p.pop('_aviso', None)
    a = tipos.generar(clave, p)
    r = simulacion.simular(a, tipos.sustrato(), f, malla, nf2ff=True, progreso=lambda m: None, f_radiacion=f)
    return p, r


def _comprobar(nombre, valor, minimo, maximo, unidad=''):
    ok = minimo <= valor <= maximo
    print(f'    {"✓" if ok else "✗"} {nombre}: {valor:.2f}{unidad} (esperado {minimo:.2f} a {maximo:.2f})', flush=True)
    return {'nombre': nombre, 'valor': round(valor, 3), 'minimo': minimo, 'maximo': maximo, 'ok': ok}


def verdad_dipolo(malla):
    p, r = _simular('dipolo', malla)
    f_res = r['f_resonancia_Hz']/1e6
    return [_comprobar('f resonancia (MHz)', f_res, F_MHZ*0.96, F_MHZ*1.04),
            _comprobar('directividad (dBi)', r['directividad_dBi'], 2.15 - 0.6, 2.15 + 0.6)]


def verdad_monopolo(malla):
    p, r = _simular('monopolo_recto', malla)
    f_res = r['f_resonancia_Hz']/1e6
    return [_comprobar('f resonancia (MHz)', f_res, F_MHZ*0.96, F_MHZ*1.04),
            # con la masa por defecto (40 mm, ~λ/3) radiador + masa forman un dipolo asimétrico (lección 15): ~2,5 dBi; solo con una
            # masa grande se acerca a los 5,2 dBi del monopolo ideal sobre masa infinita. 2,0 es el suelo de un dipolo (2,15 dBi) menos tolerancia
            _comprobar('directividad (dBi)', r['directividad_dBi'], 2.0, 5.5)]


def verdad_parche(malla):
    p, r = _simular('parche_rectangular', malla)
    f_res = r['f_resonancia_Hz']/1e6
    f_libro = _f_cavidad(p['largo'], p['ancho'])
    return [_comprobar('f resonancia frente a la cavidad (MHz)', f_res, f_libro*0.95, f_libro*1.05),
            _comprobar('directividad (dBi)', r['directividad_dBi'], 5.0, 8.0)]


PRUEBAS = {'dipolo': verdad_dipolo, 'monopolo': verdad_monopolo, 'parche': verdad_parche}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    malla = 'normal'
    if '--malla' in sys.argv:
        malla = sys.argv[sys.argv.index('--malla') + 1]
        args = [a for a in args if a != malla]
    if '--cpu' in sys.argv:
        os.environ['ANTENAS_GPU'] = '0'
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    elegidas = args or list(PRUEBAS)
    for e in elegidas:
        if e not in PRUEBAS:
            sys.exit(f'Prueba desconocida: {e}. Hay: {", ".join(PRUEBAS)}')
    todo, mal = {}, 0
    for e in elegidas:
        print(f'=== {e} a {F_MHZ} MHz (malla {malla})', flush=True)
        try:
            res = PRUEBAS[e](malla)
        except Exception as ex:                       # un fallo de la simulación cuenta como fallo, no se oculta
            print(f'    ✗ no se pudo simular: {type(ex).__name__}: {ex}', flush=True)
            res = [{'nombre': 'simulación', 'ok': False, 'error': f'{type(ex).__name__}: {ex}'}]
        todo[e] = res
        mal += sum(1 for c in res if not c['ok'])
    salida = os.path.join(RAIZ, 'salidas', '_verdad')
    os.makedirs(salida, exist_ok=True)
    json.dump({'f_MHz': F_MHZ, 'malla': malla, 'resultados': todo}, open(os.path.join(salida, 'verdad.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('TODO BIEN' if not mal else f'{mal} comprobación(es) fallan', flush=True)
    sys.exit(1 if mal else 0)


if __name__ == '__main__':
    main()
