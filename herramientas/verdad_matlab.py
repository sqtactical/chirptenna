"""Segundo solver: MATLAB (Antenna Toolbox) contra openEMS sobre la misma placa generada por el proyecto.

Uso (desde la raíz):
    python herramientas/verdad_matlab.py [dipolo] [monopolo] [parche] [--malla-mm 2.5] [--f-ini 2000 --f-fin 3000 --puntos 21]

Para cada tipo toma `tipos.dimensionar` a 2441,75 MHz, saca el cobre de F.Cu y B.Cu y el contorno, los pasa a un
`pcbStack` de MATLAB (FR4 εr 4,5, tanδ 0,02, cobre PEC, alimentación vertical de 0,5 mm en el arranque de la línea
de 50 Ω) y compara con `salidas/_verdad/verdad.json` (lo escribe `herramientas/verdad.py`: ejecutarlo antes).

Compara la resonancia (mínimo de S11 y cruce de reactancia) y la directividad máxima. Tolerancias: 5 % en f y 1,0 dB en
directividad; son dos solvers distintos (momentos frente a FDTD) y la alimentación no es idéntica (puerto de línea frente a
sonda), así que lo que se busca es que no haya un fallo grande, no que coincidan al decimal.

Salida en `salidas/_verdad_matlab/`: `<tipo>_entrada.json`, `<tipo>_salida.json` y `comparacion.json`. Código 1 si
alguna comparación falla. No va en la CI (necesita MATLAB con Antenna Toolbox, que es una licencia del usuario). Busca
`matlab.exe` en `MATLAB_EXE` o en `Program Files\\MATLAB\\*\\bin`.
"""
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

F_MHZ = 2441.75
TIPOS = {'dipolo': 'dipolo', 'monopolo': 'monopolo_recto', 'parche': 'parche_rectangular'}
TOL_F = 0.05
TOL_D = 1.0
SALIDA = os.path.join(RAIZ, 'salidas', '_verdad_matlab')


def buscar_matlab():
    from antenas import simular_matlab
    return simular_matlab.ejecutable()


def entrada_matlab(clave, malla_mm):
    from antenas import tipos, simular_matlab
    p = tipos.dimensionar(clave, F_MHZ*1e6)
    p.pop('_aviso', None)
    a = tipos.generar(clave, p)
    return p, simular_matlab.entrada(a, tipos.sustrato(), malla_mm, 2000.0, 3000.0, 21)

def _openems():
    ruta = os.path.join(RAIZ, 'salidas', '_verdad', 'verdad.json')
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)['resultados']


def _valor(lista, texto):
    for c in lista:
        if c.get('nombre', '').startswith(texto) and 'valor' in c:
            return c['valor']
    return None


def main():
    argv = sys.argv[1:]
    opciones = {}
    for nombre, tipo in (('--malla-mm', float), ('--f-ini', float), ('--f-fin', float), ('--puntos', int)):
        if nombre in argv:
            i = argv.index(nombre)
            opciones[nombre] = tipo(argv[i + 1])
            del argv[i:i + 2]
    malla = opciones.get('--malla-mm', 2.5)
    args = [a for a in argv if not a.startswith('--')]
    elegidas = args or list(TIPOS)
    for e in elegidas:
        if e not in TIPOS:
            sys.exit(f'Prueba desconocida: {e}. Hay: {", ".join(TIPOS)}')
    matlab = buscar_matlab()
    if not matlab:
        sys.exit('No encuentro matlab.exe (define MATLAB_EXE).')
    os.makedirs(SALIDA, exist_ok=True)
    ref = _openems()
    if not ref:
        print('Aviso: no hay salidas/_verdad/verdad.json; solo se muestran los números de MATLAB (ejecuta herramientas/verdad.py).')
    todo, mal = {}, 0
    for e in elegidas:
        print(f'=== {e} a {F_MHZ} MHz (MATLAB, malla {malla} mm)', flush=True)
        p, datos = entrada_matlab(TIPOS[e], malla)
        datos['f_ini_MHz'] = opciones.get('--f-ini', datos['f_ini_MHz'])
        datos['f_fin_MHz'] = opciones.get('--f-fin', datos['f_fin_MHz'])
        datos['puntos'] = opciones.get('--puntos', datos['puntos'])
        ent, sal = (os.path.join(SALIDA, f'{e}_{x}.json') for x in ('entrada', 'salida'))
        with open(ent, 'w', encoding='utf-8') as f:
            json.dump(datos, f)
        if os.path.exists(sal):
            os.remove(sal)
        r = subprocess.run([matlab, '-batch', f"addpath('{os.path.join(RAIZ, 'herramientas')}'); verdad_caso('{ent}','{sal}')"],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if not os.path.exists(sal):
            print(f'    ✗ MATLAB no dio resultado: {(r.stdout + r.stderr).strip()[-600:]}', flush=True)
            todo[e] = {'ok': False, 'error': (r.stdout + r.stderr).strip()[-600:]}
            mal += 1
            continue
        with open(sal, encoding='utf-8') as f:
            m = json.load(f)
        f_oe, d_oe = _valor(ref.get(e, []), 'f resonancia'), _valor(ref.get(e, []), 'directividad')
        fila = {'f_min_S11_MHz': m['f_min_S11_MHz'], 'S11_min_dB': m['S11_min_dB'], 'f_cruce_X_MHz': m['f_cruce_X_MHz'],
                'Z_en_minimo': m['Z_en_minimo'], 'directividad_matlab_dBi': m['directividad_max_dBi'],
                'f_openems_MHz': f_oe, 'directividad_openems_dBi': d_oe, 'ok': True}
        cruce = m['f_cruce_X_MHz']                                         # NaN sale como null: no hubo cruce de reactancia
        texto_x = f'{cruce:.0f} MHz' if cruce is not None else 'sin cruce'
        d_m = m['directividad_max_dBi']
        print(f"    MATLAB: S11 mín {m['S11_min_dB']:.1f} dB a {m['f_min_S11_MHz']:.0f} MHz, X=0 a {texto_x}, "
              f"Z {m['Z_en_minimo'][0]:.0f}{m['Z_en_minimo'][1]:+.0f}j Ω, "
              f"D {f'{d_m:.2f} dBi' if d_m is not None else 'no calculada'}", flush=True)
        if f_oe is not None and d_m is not None:
            f_m = cruce if cruce is not None else m['f_min_S11_MHz']
            df = (f_m - f_oe)/f_oe
            dd = m['directividad_max_dBi'] - d_oe
            fila['dif_f_pct'], fila['dif_D_dB'] = round(df*100, 2), round(dd, 2)
            fila['ok'] = abs(df) <= TOL_F and abs(dd) <= TOL_D
            print(f"    openEMS: {f_oe:.0f} MHz, {d_oe:.2f} dBi  →  Δf {df*100:+.1f} %, ΔD {dd:+.2f} dB  "
                  f"{'✓' if fila['ok'] else '✗'}", flush=True)
        mal += 0 if fila['ok'] else 1
        todo[e] = fila
    with open(os.path.join(SALIDA, 'comparacion.json'), 'w', encoding='utf-8') as f:
        json.dump({'f_MHz': F_MHZ, 'malla_mm': malla, 'resultados': todo}, f, indent=1, ensure_ascii=False)
    print('TODO BIEN' if not mal else f'{mal} comparación(es) fallan', flush=True)
    sys.exit(1 if mal else 0)


if __name__ == '__main__':
    main()
