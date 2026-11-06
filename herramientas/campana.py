"""Campaña en GPU de todos los tipos y bandas: centrar y luego explorar la forma (herramientas/barrido.py).

Para cada tipo y banda, un barrido `--centrar --modo cruz --radiacion`:
  1. centra el tamaño principal en la frecuencia (secante, `simulacion.ajustar`);
  2. alrededor de ese diseño, varía cada parámetro de forma por separado (TABLA_FORMA, factores «x» sobre el
     centrado) y al final prueba la combinación de los mejores valores;
  3. se corta si las 3 primeras configuraciones salen peor de −3 dB.
Se hacen primero los tipos baratos y los pesados al final; `--horas N` no empieza ninguno nuevo pasadas N horas.

Uso (desde la raíz):
    python herramientas/campana.py [--bandas «2,4 GHz»;«5,8 GHz»;…] [--tipos t1,t2,…] [--max-celdas 20]
                                   [--horas N] [--lista]
Cada barrido deja salidas/_barridos/C_<tipo>_<banda>. Si se corta, al repetirlo se saltan los terminados.
Resumen: `python herramientas/resumen_barridos.py`. No hay banda de 433 MHz (placas de decenas de cm).
"""
import os
import sys
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
         'colineal_coco', 'monopolo_flecha', 'monopolo_hilbert', 'yagi_koch', 'panel_dipolos', 'colineal_dipolos', 'array_parches']
# Combinaciones que no tienen sentido o ya se sabe que no sirven
SALTAR = {('colineal_coco', '868'), ('monopolo_hilbert', '5,8 GHz'), ('yagi_koch', '5,8 GHz')}

# Parámetros de forma por tipo. El primer valor es el de la base («x1» o el valor por defecto); «xF» = F × el centrado.
TABLA_FORMA = {
    'monopolo_recto': [],             # ya funciona sin tocar: solo se centra
    'monopolo_koch': [],             # ya funciona sin tocar: solo se centra
    'monopolo_meandro': [],             # ya funciona sin tocar: solo se centra
    'monopolo_sierpinski': [],             # ya funciona sin tocar: solo se centra
    'monopolo_flecha': ['iteracion=3,2,4', 'ancho_pista=x1,x0.7,x1.4'],
    'monopolo_hilbert': ['orden=3,2'],
    'dipolo': [],             # ya funciona sin tocar: solo se centra
    'dipolo_bowtie': [],             # ya funciona sin tocar: solo se centra
    'dipolo_sleeve': ['largo_masa=x1,x0.8,x1.25', 'ancho_pista=x1,x0.6,x1.8'],
    'ifa': ['separacion_toma=x1,x0.6,x1.6', 'altura=x1,x0.7,x1.4', 'ancho_pista=x1,x0.6,x1.6'],
    'pifa': ['separacion_toma=x1,x0.6,x1.6', 'altura=x1,x0.7,x1.4', 'ancho_pista=x1,x0.6,x1.4'],
    'jpole': ['toma=x1,x0.7,x1.4', 'hueco=x1,x0.6,x1.6'],
    'jpole_koch': ['toma=x1,x0.7,x1.4', 'hueco=x1,x0.6,x1.6'],
    'parche_rectangular': ['ancho=x1,x0.85,x1.2', 'alimentacion=0,1'],
    'parche_circular': ['corte=x1,x0.6,x1.4'],
    'parche_ranura': ['ranura_ancho=x1,x0.8,x1.2', 'ranura_largo=x1,x0.75,x1.25'],
    'parche_apilado': ['parasito_hueco=x1,x0.6,x1.6', 'parasito_factor=x1,x0.96,x1.04'],
    'parche_minkowski': ['iteracion=1,2', 'profundidad=x1,x0.7,x1.3'],
    'yagi_boom': ['directores=2,1,3', 'separacion_reflector=x1,x0.8,x1.2'],
    'yagi_koch': ['directores=1,0,2'],
    'vivaldi': ['largo_aleta=x1,x0.8,x1.2', 'tasa=x1,x0.7,x1.4'],
    'colineal_franklin': ['factor_horquilla=x1,x0.9,x1.1', 'elementos=2,1,3'],
    'colineal_coco': ['ancho_exterior=x1,x0.8,x1.25', 'secciones=4,3,5'],
    'colineal_dipolos': ['factor_linea=x1,x0.9,x1.1', 'elementos=4,3,5'],
    'panel_dipolos': ['separacion_reflector=x1,x0.8,x1.2'],
    'array_parches': [],
}


def corto(banda):
    return banda.replace(' ', '').replace(',', '').replace('radioaficionado', '')


def main():
    args = sys.argv[1:]
    opt = {'max-celdas': '20', 'bandas': None, 'tipos': None, 'horas': None, 'lista': False}
    i = 0
    while i < len(args):
        k = args[i][2:]
        if k == 'lista':
            opt[k] = True
        else:
            i += 1
            opt[k] = args[i]
        i += 1
    from antenas import tipos as T
    bandas = [b.strip() for b in opt['bandas'].split(';')] if opt['bandas'] else BANDAS
    lista = [t.strip() for t in opt['tipos'].split(',')] if opt['tipos'] else [t for t in TIPOS if t in T.CATALOGO]
    for t in lista:                                          # los nombres de parámetros deben existir
        for pa in TABLA_FORMA.get(t, []):
            assert pa.split('=')[0] in {q.nombre for q in T.CATALOGO[t].parametros}, (t, pa)
    limite = time.time() + float(opt['horas'])*3600 if opt['horas'] else None
    os.makedirs(os.path.join(RAIZ, 'salidas', '_campana'), exist_ok=True)
    for banda in bandas:
        for tipo in lista:
            if (tipo, banda) in SALTAR:
                continue
            etiqueta = f'C_{tipo}_{corto(banda)}'
            if os.path.exists(os.path.join(RAIZ, 'salidas', '_barridos', etiqueta, 'resumen.json')):
                continue
            if opt['lista']:
                print(etiqueta, TABLA_FORMA.get(tipo, []))
                continue
            if limite and time.time() > limite:
                print('Tiempo agotado: se para antes de', etiqueta, flush=True)
                return
            print(f'[{time.strftime("%H:%M")}] {etiqueta}', flush=True)
            cmd = [sys.executable, '-X', 'utf8', os.path.join(RAIZ, 'herramientas', 'barrido.py'), tipo, banda,
                   *TABLA_FORMA.get(tipo, []), '--centrar', '--modo', 'cruz', '--radiacion',
                   '--etiqueta', etiqueta, '--max-celdas', opt['max-celdas'], '--max-ajuste', '3']
            with open(os.path.join(RAIZ, 'salidas', '_campana', f'{etiqueta}.log'), 'w', encoding='utf-8') as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=RAIZ,
                               env=dict(os.environ, PYTHONIOENCODING='utf-8'))


if __name__ == '__main__':
    main()