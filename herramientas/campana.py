"""Campaña de simulaciones en GPU de todos los tipos y bandas (etapas A y B), con herramientas/barrido.py.

Etapa A: una simulación por tipo y banda con el tamaño que da `dimensionar` (con diagrama de radiación).
Etapa B: donde A sale mal (peor S11 en la banda > −10 dB o resonancia a más de un 3 % del objetivo), un barrido
         de varios parámetros (TABLA_B, con factores «x» sobre el tamaño ajustado, válidos en cualquier banda).

Uso (desde la raíz):
    python herramientas/campana.py [--etapa A|B|AB] [--bandas «2,4 GHz»,«5,8 GHz»,…] [--tipos t1,t2,…]
                                   [--max-celdas 20] [--horas N] [--lista]

  --lista       solo muestra qué se lanzaría (sin simular)
  --horas N     no empieza ningún barrido nuevo pasadas N horas
Cada barrido deja su carpeta en salidas/_barridos/<etiqueta> (A_<tipo>_<banda>, B_<tipo>_<banda>). Si se corta,
al repetir el comando se saltan los ya terminados. Resumen: salidas/_campana/resumen.csv y resumen.md.
No hay banda de 433 MHz (las placas de decenas de cm no se simulan en esta campaña).
"""
import os
import sys
import csv
import json
import time
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

BANDAS = ['2,4 GHz', '5,8 GHz', '1,2 GHz radioaficionado', 'GPS L1', 'Iridium', '915 ISM', '868']
# De más barato a más caro
TIPOS = ['monopolo_recto', 'monopolo_koch', 'monopolo_meandro', 'monopolo_sierpinski', 'dipolo', 'dipolo_bowtie',
         'dipolo_sleeve', 'ifa', 'pifa', 'jpole', 'jpole_koch', 'parche_rectangular', 'parche_circular',
         'parche_ranura', 'parche_apilado', 'parche_minkowski', 'yagi_boom', 'vivaldi', 'colineal_franklin',
         'colineal_coco', 'colineal_dipolos', 'monopolo_hilbert', 'yagi_koch', 'panel_dipolos', 'array_parches']
# Combinaciones que no tienen sentido o ya se sabe que no sirven
SALTAR = {('colineal_coco', '868'), ('monopolo_hilbert', '5,8 GHz'), ('yagi_koch', '5,8 GHz')}
# A ya hecha a mano en la campaña de los tipos nuevos (campana_nuevos.ps1): a 2,4 GHz sus barridos incluyen el tamaño base
HECHO_24 = {'ifa', 'pifa', 'dipolo_sleeve', 'parche_circular', 'parche_ranura', 'parche_apilado', 'vivaldi',
            'colineal_dipolos'}

# Etapa B: parámetros a barrer por tipo. «xF» = F × el valor de dimensionar; un número suelto, valor absoluto.
TABLA_B = {
    'monopolo_recto': ['alto=x0.92,x1,x1.08', 'ancho_pista=x1,x2'],
    'monopolo_koch': ['alto=x0.92,x1,x1.08', 'iteracion=1,2,3'],
    'monopolo_meandro': ['alto=x0.92,x1,x1.08', 'ancho_meandro=x0.8,x1,x1.2'],
    'monopolo_sierpinski': ['alto=x0.92,x1,x1.08', 'iteracion=1,2,3'],
    'monopolo_hilbert': ['lado=x0.9,x1,x1.1', 'orden=2,3'],
    'dipolo': ['largo_brazo=x0.94,x1,x1.06', 'ancho_pista=x1,x2'],
    'dipolo_bowtie': ['largo_brazo=x0.94,x1,x1.06', 'apertura=60,70,80'],
    'dipolo_sleeve': ['alto=x0.92,x1,x1.08', 'largo_masa=x0.8,x1,x1.2'],
    'ifa': ['largo_brazo=x0.85,x1,x1.15', 'separacion_toma=x0.6,x1,x1.5'],
    'pifa': ['largo_brazo=x0.85,x1,x1.15', 'separacion_toma=x0.6,x1,x1.5'],
    'jpole': ['largo_radiador=x0.94,x1,x1.06', 'toma=x0.7,x1,x1.4'],
    'jpole_koch': ['largo_radiador=x0.94,x1,x1.06', 'toma=x0.7,x1,x1.4'],
    'parche_rectangular': ['largo=x0.97,x1,x1.03', 'ancho=x0.9,x1,x1.1'],
    'parche_circular': ['corte=x0.6,x1,x1.4', 'diagonal=0,1'],
    'parche_ranura': ['ranura_ancho=x0.8,x1,x1.2', 'ranura_largo=x0.75,x1,x1.25'],
    'parche_apilado': ['parasito_hueco=x0.6,x1,x1.6', 'parasito_factor=x0.96,x1,x1.04'],
    'parche_minkowski': ['largo=x0.92,x1,x1.08', 'iteracion=1,2'],
    'yagi_boom': ['largo_brazo=x0.95,x1,x1.05', 'separacion_reflector=x0.8,x1,x1.2'],
    'yagi_koch': ['largo_brazo=x0.92,x1,x1.08', 'separacion_director=x0.8,x1,x1.2'],
    'vivaldi': ['ancho_apertura=x0.85,x1,x1.15', 'largo_aleta=x0.8,x1,x1.2'],
    'colineal_franklin': ['largo_elemento=x0.94,x1,x1.06', 'factor_horquilla=x0.9,x1,x1.1'],
    'colineal_coco': ['largo_seccion=x0.94,x1,x1.06', 'ancho_exterior=x0.8,x1,x1.2'],
    'colineal_dipolos': ['largo_brazo=x0.9,x1,x1.1', 'factor_linea=x0.9,x1,x1.1'],
    'panel_dipolos': ['largo_brazo=x0.95,x1,x1.05', 'separacion_reflector=x0.8,x1,x1.2'],
    'array_parches': ['largo=x0.97,x1,x1.03'],
}


def corto(banda):
    return banda.replace(' ', '').replace(',', '').replace('radioaficionado', '')


def lanzar(etiqueta, tipo, banda, params, max_celdas, extra=()):
    """Ejecuta barrido.py y devuelve resumen.json (o None si no se pudo)."""
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    ruta = os.path.join(carpeta, 'resumen.json')
    if os.path.exists(ruta):
        return json.load(open(ruta, encoding='utf-8'))
    cmd = [sys.executable, '-X', 'utf8', os.path.join(RAIZ, 'herramientas', 'barrido.py'), tipo, banda, *params,
           '--etiqueta', etiqueta, '--radiacion', '--max-celdas', str(max_celdas), *extra]
    os.makedirs(os.path.join(RAIZ, 'salidas', '_campana'), exist_ok=True)
    with open(os.path.join(RAIZ, 'salidas', '_campana', f'{etiqueta}.log'), 'w', encoding='utf-8') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=RAIZ, env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    return json.load(open(ruta, encoding='utf-8')) if os.path.exists(ruta) else None


def malo(res, f_obj):
    """¿La etapa A no sale bien? (peor S11 > −10 dB o resonancia lejos del objetivo)."""
    filas = [f for f in res['filas'] if 'peor_banda_dB' in f]
    if not filas:
        return True
    f = filas[0]
    return f['peor_banda_dB'] > -10 or abs(f['f_res_MHz'] - f_obj)/f_obj > 0.03


def main():
    args = sys.argv[1:]
    opt = {'etapa': 'AB', 'max-celdas': '20', 'bandas': None, 'tipos': None, 'horas': None, 'lista': False}
    i = 0
    while i < len(args):
        k = args[i][2:]
        if k == 'lista':
            opt[k] = True
        else:
            i += 1
            opt[k] = args[i]
        i += 1
    from antenas import tipos as T, presentacion
    bandas = [b.strip() for b in opt['bandas'].split(';')] if opt['bandas'] else BANDAS
    lista_tipos = [t.strip() for t in opt['tipos'].split(',')] if opt['tipos'] else [t for t in TIPOS if t in T.CATALOGO]
    for t in lista_tipos:                                    # los nombres de parámetros de TABLA_B deben existir
        for pa in TABLA_B.get(t, []):
            assert pa.split('=')[0] in {q.nombre for q in T.CATALOGO[t].parametros}, (t, pa)
    limite = time.time() + float(opt['horas'])*3600 if opt['horas'] else None
    banda_f = lambda b: (sum(presentacion.BANDAS[b])/2 if b in presentacion.BANDAS else float(b))
    banda_n = {'868': '868'}
    filas_resumen = []
    pendientes_B = []

    def resumir(etapa, tipo, banda, res):
        if not res or not res['filas']:
            filas_resumen.append({'etapa': etapa, 'tipo': tipo, 'banda': banda, 'estado': 'saltada o sin resultado'})
            return
        buenas = sorted([f for f in res['filas'] if 'peor_banda_dB' in f], key=lambda f: f['peor_banda_dB'])
        if not buenas:
            filas_resumen.append({'etapa': etapa, 'tipo': tipo, 'banda': banda, 'estado': 'error: ' + str(res['filas'][0].get('error', ''))[:80]})
            return
        f = buenas[0]
        r = f.get('radiacion', {})
        filas_resumen.append({'etapa': etapa, 'tipo': tipo, 'banda': banda, 'configs': len(res['filas']),
                              'peor_banda_dB': f['peor_banda_dB'], 's11_obj_dB': f['s11_obj_dB'], 'f_res_MHz': f['f_res_MHz'],
                              'banda_10dB': f['banda_10dB'], 'ganancia_dBi': r.get('ganancia_dBi'),
                              'eficiencia_%': r.get('eficiencia_%'), 'mejor': json.dumps(f['cambios'], ensure_ascii=False),
                              'estado': 'ok' if f['peor_banda_dB'] <= -10 else 'mal'})

    for etapa in ('A', 'B'):
        if etapa not in opt['etapa']:
            continue
        for banda in bandas:
            for tipo in lista_tipos:
                if (tipo, banda) in SALTAR or (etapa == 'B' and tipo not in TABLA_B):
                    continue
                if etapa == 'B' and tipo in HECHO_24 and banda == '2,4 GHz':
                    continue
                f_obj = banda_f(banda)
                etiqueta = f'{etapa}_{tipo}_{corto(banda)}'
                if etapa == 'A' and tipo in HECHO_24 and banda == '2,4 GHz':
                    continue
                if etapa == 'B':
                    a = json.load(open(os.path.join(RAIZ, 'salidas', '_barridos', f'A_{tipo}_{corto(banda)}', 'resumen.json'), encoding='utf-8')) \
                        if os.path.exists(os.path.join(RAIZ, 'salidas', '_barridos', f'A_{tipo}_{corto(banda)}', 'resumen.json')) else None
                    if a is None or not a['filas'] or not malo(a, f_obj):
                        continue                         # sin A, saltada o ya buena
                if opt['lista']:
                    print(etiqueta, '→', tipo, banda, TABLA_B[tipo] if etapa == 'B' else '(tamaño base)')
                    continue
                if limite and time.time() > limite:
                    print('Tiempo agotado: se para antes de', etiqueta, flush=True)
                    break
                print(f'[{time.strftime("%H:%M")}] {etiqueta}', flush=True)
                res = lanzar(etiqueta, tipo, banda, TABLA_B[tipo] if etapa == 'B' else [], opt['max-celdas'])
                resumir(etapa, tipo, banda, res)
    if not opt['lista']:
        os.makedirs(os.path.join(RAIZ, 'salidas', '_campana'), exist_ok=True)
        campos = ['etapa', 'tipo', 'banda', 'estado', 'configs', 'peor_banda_dB', 's11_obj_dB', 'f_res_MHz', 'banda_10dB',
                  'ganancia_dBi', 'eficiencia_%', 'mejor']
        with open(os.path.join(RAIZ, 'salidas', '_campana', 'resumen.csv'), 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, campos, delimiter=';')
            w.writeheader()
            w.writerows(filas_resumen)
        print('Resumen: salidas/_campana/resumen.csv', flush=True)


if __name__ == '__main__':
    main()