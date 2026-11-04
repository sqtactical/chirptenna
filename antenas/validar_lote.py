"""Valida varios tipos simulando y ajustando a la frecuencia, uno tras otro.

Uso: python -m antenas.validar_lote <carpeta_salida> [--malla adaptada] [--paralelo 2] [--hilos 6]
     [clave:f_MHz:precision[:json_params] ...]
Con --paralelo N corre N casos a la vez, cada uno con --hilos hilos (por defecto 3/8 de la CPU).
Escribe en la carpeta un subdirectorio por caso (resultado.json + datos.npz) y resumen.json.
"""
import os
import sys
import json
import time
import subprocess

CASOS_POR_DEFECTO = [                      # de más rápido a más lento
    ('jpole', 2441.75, 'normal', {}),
    ('jpole_koch', 2441.75, 'normal', {}),
    ('monopolo_meandro', 2441.75, 'normal', {}),
    ('monopolo_sierpinski', 2441.75, 'normal', {}),
    ('monopolo_koch', 2441.75, 'normal', {'ajuste': 1}),
    ('parche_rectangular', 2441.75, 'normal', {}),
    ('parche_minkowski', 2441.75, 'normal', {}),
    ('yagi_koch', 2441.75, 'normal', {'directores': 1}),
    ('monopolo_hilbert', 866.5, 'normal', {}),
    ('monopolo_hilbert', 2441.75, 'normal', {'orden': 2}),
    ('array_parches', 2441.75, 'rápida', {'tamano': 2}),
]


def _correr(caso, salida, malla, ruta_resumen, cerrojo, hilos):
    clave, f, prec, extra = caso
    nombre = f'{clave}_{f:g}MHz' + ''.join(f'_{k}{v}' for k, v in extra.items())
    carpeta = os.path.join(salida, nombre)
    os.makedirs(carpeta, exist_ok=True)
    trabajo = {'clave': clave, 'parametros': extra, 'sustrato': 'FR4 JLC 1,6 mm', 'f_obj_Hz': f*1e6,
               'precision': prec, 'ajustar': True, 'salida': carpeta, 'malla': malla}
    ruta = os.path.join(carpeta, 'trabajo.json')
    json.dump(trabajo, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'=== {nombre} ({prec})', flush=True)
    t0 = time.time()
    entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
    if hilos:
        entorno['ANTENAS_HILOS'] = str(hilos)
    proc = subprocess.Popen([sys.executable, '-u', '-m', 'antenas.simular_cli', ruta], env=entorno,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                            errors='replace')
    for linea in proc.stdout:                       # con varios casos a la vez, cada línea lleva su caso
        print(f'[{nombre}] {linea.rstrip()}', flush=True)
    proc.wait()
    r = json.load(open(os.path.join(carpeta, 'resultado.json'), encoding='utf-8'))
    r['caso'] = nombre
    r['tiempo_total_s'] = round(time.time() - t0)
    with cerrojo:
        # se relee: otro caso (u otro lote) puede haberlo actualizado mientras tanto
        resumen = json.load(open(ruta_resumen, encoding='utf-8')) if os.path.exists(ruta_resumen) else []
        resumen = [x for x in resumen if x.get('caso') != nombre]
        resumen.append({k: r.get(k) for k in ('caso', 'ok', 'error', 'historial', 'f_resonancia_MHz', 'banda_MHz',
                                              'ancho_banda_MHz', 's11_min_dB', 'directividad_dBi', 'ganancia_dBi',
                                              'eficiencia_radiacion_%', 'celdas', 'paso_malla_mm', 'avisos',
                                              'tiempo_total_s')})
        json.dump(resumen, open(ruta_resumen, 'w', encoding='utf-8'), indent=2, ensure_ascii=False, default=float)
    print(f'--- {nombre}: {r.get("f_resonancia_MHz")} MHz, {r.get("tiempo_total_s")} s, ok={r.get("ok")}', flush=True)


def main():
    import threading
    from concurrent.futures import ThreadPoolExecutor
    args = sys.argv[1:]
    opciones = {'--malla': 'uniforme', '--paralelo': '1', '--hilos': None}
    for op in list(opciones):
        if op in args:
            i = args.index(op)
            opciones[op] = args[i + 1]
            del args[i:i + 2]
    malla, paralelo = opciones['--malla'], int(opciones['--paralelo'])
    # en paralelo, cada simulación con una parte de los núcleos (CPU híbrida: ver RETOMAR.md)
    hilos = int(opciones['--hilos']) if opciones['--hilos'] else (max(1, (os.cpu_count() or 2)*3//8) if paralelo > 1 else 0)
    salida = os.path.abspath(args[0])
    os.makedirs(salida, exist_ok=True)
    casos = CASOS_POR_DEFECTO
    if len(args) > 1:
        casos = []
        for a in args[1:]:
            partes = a.split(':', 3)
            casos.append((partes[0], float(partes[1]), partes[2], json.loads(partes[3]) if len(partes) > 3 else {}))
    ruta_resumen = os.path.join(salida, 'resumen.json')    # se añade al que ya hubiera
    cerrojo = threading.Lock()
    with ThreadPoolExecutor(max_workers=paralelo) as ex:
        for fut in [ex.submit(_correr, c, salida, malla, ruta_resumen, cerrojo, hilos) for c in casos]:
            fut.result()


if __name__ == '__main__':
    main()