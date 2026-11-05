"""Genera las miniaturas SVG de la galería: antenas/miniaturas/<clave>.svg (o en la carpeta indicada).

Uso (desde la raíz):  python herramientas/generar_miniaturas.py [carpeta]
Volver a ejecutar si cambia un generador o se añade un tipo (la web las regenera al construirse).
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from antenas import tipos, miniaturas   # noqa: E402


def generar(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    total = 0
    for clave in tipos.CATALOGO:
        texto = miniaturas.svg(clave)
        with open(os.path.join(carpeta, f'{clave}.svg'), 'w', encoding='utf-8') as fh:
            fh.write(texto)
        total += len(texto)
    return total


if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'antenas', 'miniaturas')
    print(f'{len(tipos.CATALOGO)} miniaturas en {destino} ({generar(destino)//1024} kB)')
