"""Genera `docs/ESTADO_REAL.md`: una sola página que dice qué es real y qué no (idea de `HONEST_STATUS.md` de antenna-forge).

Uso (desde la raíz):
    python herramientas/estado_real.py            reescribe el archivo
    python herramientas/estado_real.py --ver      lo escribe en la salida estándar

La tabla de tipos sale de `antenas/problemas.ESTADO` (la misma fuente que la interfaz y los README), así que no se
desfasa: `pruebas/test_estado_real.py` falla si el archivo no coincide con lo que genera esto. El texto de las
secciones fijas se mantiene aquí: al cambiar lo medido, los límites o las comprobaciones, editarlo en este archivo y volver a ejecutarlo.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

RUTA = os.path.join(RAIZ, 'docs', 'ESTADO_REAL.md')

MEDIDO = [
    'Ninguna placa fabricada se ha medido todavía. Los cupones de εr (`cupon/`) y las primeras antenas de 2,4 GHz están pedidos a JLCPCB; '
    'hasta que lleguen y se midan con el NanoVNA, todo lo de abajo es **simulación**.',
    'Lo que sí está medido: el NanoVNA (calibración OSL + THRU, `vna/`) y el latiguillo; nada del generador.',
]

LIMITES = [
    '**Unión soldada de la colineal modular**: no está simulada (la cadena se simula como una pieza) ni medida; la cola de milano no se ha probado en una placa real '
    'y no se ha consultado a JLC el ancho mínimo de las ranuras fresadas.',
    '**Colineal modular a 868 MHz**: sin centrar (resuena a 1034 MHz); solo está centrada a 2,4 GHz.',
    '**Red de adaptación en π**: −38 dB por circuito frente a −10 dB en la FDTD con los mismos componentes (F4.1 sin resolver). Se fía más de la FDTD.',
    '**Bibandas** (`multibanda` = 1 en J-pole e IFA): dependen de la malla; ninguna cumple −8 dB en las dos bandas con tres pasos de malla distintos.',
    '**Importación de placas KiCad** y **zona de exclusión de la huella integrada**: sin probar con una placa real ni con KiCad con interfaz.',
    '**εr del FR4 de 4 capas** (4,4 de la calculadora de JLC, la web de JLC da 4,6): por comprobar.',
    '**Parches**: la banda de ~36 MHz en FR4 no cubre la ISM de 2,4 GHz; la eficiencia en FR4 ronda el 47 %.',
    '**Eficiencia y ganancia de la colineal modular en FR4**: no suben con más de 4 módulos (en RO4350B sí).',
    '**Antena de chip** (F3.8): sin modelo del fabricante; no se ha simulado.',
]

COMPROBACIONES = [
    '`python -m pytest pruebas` (sin openEMS, < 5 s): geometría, exportación, tamaños iniciales, idiomas, método de momentos de hilos, '
    'optimización, y `pruebas/test_verdad.py` (el generador frente a fórmulas de libro: microstrip de Hammerstad, dipolo, monopolo y parche por el modelo de la cavidad).',
    '`python herramientas/comprobar_tipos.py` (~2 min, KiCad): genera y exporta los tipos a 868 y 2441,75 MHz y pasa el DRC. Va en la CI.',
    '`python herramientas/verdad.py` (openEMS, minutos): simula un dipolo, un monopolo y un parche y los compara con el libro. **No** va en la CI; se pasa antes de una release.',
    '`herramientas/validar_lote`, `barrido.py` y `campana.py`: las simulaciones de validación de cada tipo; los resultados están en `docs/desarrollo/barridos_gpu.md` y `resultados_07-11.md`.',
    'La simulación nunca devuelve un resultado analítico si falla: `simular` lanza el error, y los avisos (η < 10 %, S11 plano, malla sensible) salen en el resultado.',
]


def generar():
    from antenas import problemas, tipos
    por_estado = {'validada': [], 'pendiente': [], 'no_funciona': []}
    for clave, (est, texto) in problemas.ESTADO.items():
        por_estado[est].append((tipos.CATALOGO[clave].nombre if clave in tipos.CATALOGO else clave, clave, texto))
    sin_estado = [c for c in tipos.CATALOGO if c not in problemas.ESTADO]
    L = ['# Estado real de Chirptenna', '',
         '*Archivo generado por `herramientas/estado_real.py` a partir de `antenas/problemas.ESTADO`; no se edita a mano.*', '',
         '## Qué está medido', '']
    L += [f'- {t}' for t in MEDIDO]
    n = len(problemas.ESTADO)
    L += ['', '## Tipos de antena', '',
          f'{n} tipos: **{len(por_estado["validada"])} validados en simulación**, {len(por_estado["pendiente"])} pendientes de validación y '
          f'{len(por_estado["no_funciona"])} que no funcionan. «Validada» significa que openEMS la da adaptada (S11 ≤ −10 dB en la banda) y radiando; '
          'no significa medida.', '']
    for est, titulo in (('validada', 'Validados en simulación'), ('pendiente', 'Pendientes de validación'), ('no_funciona', 'No funcionan')):
        L += [f'### {titulo}', '', '| Tipo | Clave | Estado |', '|---|---|---|']
        L += [f'| {nom} | `{clave}` | {texto} |' for nom, clave, texto in sorted(por_estado[est])]
        L.append('')
    if sin_estado:
        L += ['### Sin estado asignado (cuentan como pendientes)', ''] + [f'- `{c}`' for c in sin_estado] + ['']
    L += ['## Límites conocidos', ''] + [f'- {t}' for t in LIMITES]
    L += ['', '## Cómo se comprueba', ''] + [f'- {t}' for t in COMPROBACIONES]
    return '\n'.join(L) + '\n'


def main():
    texto = generar()
    if '--ver' in sys.argv:
        sys.stdout.reconfigure(encoding='utf-8')
        print(texto)
        return
    with open(RUTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)
    print('escrito', RUTA)


if __name__ == '__main__':
    main()
