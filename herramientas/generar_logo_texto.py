"""Precalcula el contorno de la palabra «Chirptenna» (DejaVu Sans Bold) para el logo de la serigrafía.

`antenas.logo.texto` lo lee de `antenas/logo_texto.json` en vez de llamar a matplotlib, que no está en la
versión web (Pyodide) y tarda en cargar. Volver a ejecutar solo si cambia la fuente o el texto del logo.

Uso (desde la raíz):  python herramientas/generar_logo_texto.py
"""
import os
import json

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTOS = ['Chirptenna']


def main():
    prop = FontProperties(family='DejaVu Sans', weight='bold')
    datos = {'fuente': 'DejaVu Sans Bold (tamaño 1)',
             'alto_mayusculas': TextPath((0, 0), 'H', size=1.0, prop=prop).get_extents().height,
             'textos': {}}
    for t in TEXTOS:
        anillos = [[[float(x), float(y)] for x, y in a] for a in TextPath((0, 0), t, size=1.0, prop=prop).to_polygons()]
        datos['textos'][t] = anillos
    ruta = os.path.join(RAIZ, 'antenas', 'logo_texto.json')
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, ensure_ascii=False)
    print(f'{ruta}: {len(TEXTOS)} texto(s), {sum(len(v) for v in datos["textos"].values())} anillos')


if __name__ == '__main__':
    main()
