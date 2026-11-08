"""Radiación (ganancia, eficiencia, haz, polarización) de los diseños bibanda en cada una de sus bandas.

Uso (desde la raíz):  python herramientas/radiacion_bibanda.py [diseño …] [--etiqueta E]
  diseños: jpole_union, ifa_dual, monopolo_dual, sierpinski (por defecto, todos)
Cada diseño se simula dos veces en banda ancha (0,45–3,8 × 868 MHz) con el diagrama calculado en 868 MHz y en 2441,75 MHz.
Un S11 bueno no basta: una antena puede adaptar y disipar la potencia (parche circular de GPS: −0,6 dB, η 3,6 %). Aquí se
mira η = potencia radiada / aceptada, la ganancia y la dirección del máximo. Resultados en salidas/_barridos/<E>/radiacion.json.
"""
import os
import sys
import json
import math
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(RAIZ, 'herramientas', nombre + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    args = sys.argv[1:]
    etiqueta = 'RAD_bibanda'
    if '--etiqueta' in args:
        i = args.index('--etiqueta')
        etiqueta = args[i + 1]
        del args[i:i + 2]
    quiero = args or ['jpole_union', 'ifa_dual', 'monopolo_dual', 'sierpinski']
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    from antenas import tipos, simulacion, geometria as g
    barrido = _cargar('barrido')
    jd, rd = _cargar('jpole_dual'), _cargar('rama_dual')
    sus = 'FR4 JLC 1,6 mm'
    s = tipos.sustrato(sus)
    f_baja, f_alta = 868.0, 2441.75

    def base(clave, fijos=None, mult=None):
        b = tipos.dimensionar(clave, f_baja*1e6, dict(fijos or {}), sus, fijos=tuple(fijos or ()))
        b.pop('_aviso', None)
        for k, v in (mult or {}).items():
            b[k] = round(b[k]*v, 3)
        return b

    disenos = {}
    b = base('jpole')
    b['factor_adaptador'] = 0.95
    disenos['jpole_union'] = ('J-pole unida: k2 1, sep2 3, a2 0,9, toma2 0,25, factor_adaptador 0,95',
                              lambda: jd.construir_union(tipos, g, sus, b, 1.0, 3.0, 0.9, 0.25, f_baja, f_alta))
    bi = base('ifa', mult={'largo_brazo': 1.17})
    disenos['ifa_dual'] = ('IFA con rama: largo_brazo ×1,17, k2 1, h2 0,6',
                           lambda: rd.construir(tipos, g, sus, 'ifa', bi, 1.0, 5.0, 0.6, f_baja, f_alta))
    bm = base('monopolo_recto')
    disenos['monopolo_dual'] = ('Monopolo con rama: k2 1,25, sep2 7, y2 8',
                                lambda: rd.construir(tipos, g, sus, 'monopolo_recto', bm, 1.25, 7.0, 0.5, f_baja, f_alta, 8.0))
    bs = base('dipolo_bowtie', {'forma': 2, 'iteracion_s': 1, 'apertura': 120.0, 'largo_brazo': 40.0})
    disenos['sierpinski'] = ('Dipolo de Sierpinski: iteracion_s 1, apertura 120, brazo 40',
                             lambda: tipos.generar('dipolo_bowtie', bs, sus))
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, 'radiacion.json')
    res = json.load(open(ruta, encoding='utf-8')) if os.path.exists(ruta) else {}
    cfg = simulacion.PRECISIONES['normal']
    lam_min = simulacion.C0/(3.8*f_baja*1e6)*1e3
    lock = barrido._bloqueo()
    try:
        for nombre in quiero:
            desc, hacer = disenos[nombre]
            a = hacer()
            sup = a.cobre('F.Cu')
            w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
            s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
            paso = round(0.9*max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2,
                                     cfg['factor_detalle']*s_min/2), 0.08), 3)
            for f in (f_baja, f_alta):
                clave = f'{nombre}@{f:g}'
                if clave in res and 'error' not in res[clave]:
                    continue
                print(f'=== {clave}: {desc} (malla {paso} mm)', flush=True)
                try:
                    r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=True, progreso=lambda m: None,
                                           rango=(0.45, 3.8), paso=paso, f_radiacion=f*1e6)
                    d = barrido._radiacion(r)
                    d['s11_en_f_dB'] = round(float(simulacion._s11_en(r, f*1e6)[0]), 1)
                    res[clave] = d
                except Exception as ex:
                    res[clave] = {'error': f'{type(ex).__name__}: {ex}'}
                print(' ', json.dumps(res[clave], ensure_ascii=False, default=float), flush=True)
                json.dump(res, open(ruta, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
