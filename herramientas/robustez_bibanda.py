"""Robustez de la J-pole unida y de la IFA con segunda rama (868 MHz + 2,4 GHz) frente al paso de malla.

Una bibanda «vale» si el peor S11 de las dos bandas queda por debajo del umbral (−8 dB) con TODOS los pasos de malla
(lección 70: el mismo diseño daba −11/−10 dB con una malla y −10/−3 dB con otra). Lo que se simula es lo que genera la
aplicación (`tipos.dimensionar` + `tipos.generar` con `multibanda` = 1): las constantes de `antenas/bibanda.py` se cambian en
memoria para cada punto de la rejilla.

Uso (desde la raíz):
    python herramientas/robustez_bibanda.py <ifa|jpole> CONSTANTE=v1,v2,… [CONSTANTE=…] [--pasos 0.7,1.0,1.15]
           [--bandas "863-870;2400-2483.5"] [--umbral -8] [--f MHz] [--etiqueta E] [--solo-lista]

  CONSTANTE  nombre de una constante de bibanda.py (IFA_H2, IFA_X_BRAZO, JPOLE_SEP2, JPOLE_TOMA2, JPOLE_RADIADOR2…); sin valores
             usa la actual. Se prueban todas las combinaciones.
  --pasos    pasos de malla en la placa [mm] (por defecto 0,7, 1,0 y 1,15)
  --f        frecuencia de la banda baja (por defecto 866,5 MHz)
Una simulación de banda ancha (0,45–3,8 ×) por punto y paso, en GPU. Resultados en salidas/_barridos/<E>/ (resultados.jsonl se
retoma si se corta, y resumen.json). Con --solo-lista no simula: da el tamaño de la placa de cada punto.
"""
import os
import sys
import json
import time
import itertools
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def main():
    args = sys.argv[1:]
    opt, rejilla, pos, i = {}, {}, [], 0
    while i < len(args):
        a = args[i]
        if a == '--solo-lista':
            opt['solo-lista'] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i + 1]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            rejilla[k] = [float(x.replace(',', '.')) for x in v.split(',')]
        else:
            pos.append(a)
        i += 1
    if len(pos) != 1 or pos[0] not in ('ifa', 'jpole'):
        sys.exit(__doc__)
    clave = pos[0]
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion, bibanda
    for k in rejilla:
        if not hasattr(bibanda, k):
            sys.exit(f'bibanda.py no tiene la constante {k}')
    sus = 'FR4 JLC 1,6 mm'
    s = tipos.sustrato(sus)
    f_baja = float(opt.get('f', 866.5))
    pasos = [float(x) for x in opt.get('pasos', '0.7,1.0,1.15').split(',')]
    bandas = [tuple(float(x) for x in b.split('-')) for b in opt.get('bandas', '863-870;2400-2483.5').split(';')]
    umbral = float(opt.get('umbral', -8.0))
    nombres = list(rejilla)
    puntos = [dict(zip(nombres, c)) for c in itertools.product(*[rejilla[k] for k in nombres])] or [{}]
    originales = {k: getattr(bibanda, k) for k in nombres}

    def antena(punto):
        for k, v in punto.items():
            setattr(bibanda, k, v)
        p = tipos.dimensionar(clave, f_baja*1e6, {'multibanda': 1}, sus, fijos=('multibanda',))
        p.pop('_aviso', None)
        return p, tipos.generar(clave, p, sus)

    if 'solo-lista' in opt:
        for pt in puntos:
            p, a = antena(pt)
            print(json.dumps(pt), 'placa', a.info['placa_mm'], 'pista min', a.info.get('pista_minima_mm'), 'hueco min', a.info.get('hueco_minimo_mm'))
        return
    etiqueta = opt.get('etiqueta') or f'ROB_{clave}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    ruta_jl = os.path.join(carpeta, 'resultados.jsonl')
    hechos = {}
    if os.path.exists(ruta_jl):
        for l in open(ruta_jl, encoding='utf-8'):
            try:
                d = json.loads(l)
                hechos[(json.dumps(d['punto'], sort_keys=True), d['paso'])] = d
            except ValueError:
                pass
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    print(f'=== {etiqueta}: {clave}, {len(puntos)} puntos × {len(pasos)} pasos {pasos}, bandas {bandas}, umbral {umbral} dB', flush=True)
    lock = barrido._bloqueo()
    filas = []
    try:
        for pt in puntos:
            p, a = antena(pt)
            for paso in pasos:
                clave_h = (json.dumps(pt, sort_keys=True), paso)
                if clave_h in hechos:
                    filas.append(hechos[clave_h])
                    continue
                t0 = time.time()
                fila = {'punto': pt, 'paso': paso, 'largo': p.get('largo_brazo', p.get('largo_radiador')), 'placa': a.info.get('placa_mm')}
                try:
                    r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=False, progreso=lambda m: None,
                                           rango=(0.45, 3.8), paso=paso)
                    f = r['f_Hz']/1e6
                    s11 = 20*np.log10(np.abs(r['s11']))
                    fila['bandas'] = [round(float(s11[(f >= lo) & (f <= hi)].max()), 1) for lo, hi in bandas]
                    fila['celdas_M'] = round(r['celdas']/1e6, 2)
                except Exception as ex:
                    fila['error'] = f'{type(ex).__name__}: {ex}'
                fila['s'] = round(time.time() - t0)
                filas.append(fila)
                open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
                print(' ', json.dumps(fila, ensure_ascii=False, default=float), flush=True)
        print('\n--- peor S11 de las bandas con todos los pasos (válido si ≤ %g dB) ---' % umbral)
        resumen = []
        for pt in puntos:
            fs = [x for x in filas if x['punto'] == pt and 'bandas' in x]
            if len(fs) < len(pasos):
                continue
            peor = max(max(x['bandas']) for x in fs)
            resumen.append({'punto': pt, 'peor_dB': peor, 'valido': peor <= umbral,
                            'por_paso': {str(x['paso']): x['bandas'] for x in fs}})
        for x in sorted(resumen, key=lambda x: x['peor_dB']):
            print(f"  {x['peor_dB']:6.1f} dB {'VALE' if x['valido'] else '    '} {json.dumps(x['punto'])}  {json.dumps(x['por_paso'])}")
        json.dump({'tipo': clave, 'umbral_dB': umbral, 'pasos': pasos, 'bandas': bandas, 'resumen': resumen, 'filas': filas},
                  open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)
        for k, v in originales.items():
            setattr(bibanda, k, v)


if __name__ == '__main__':
    main()
