"""Genera el informe PDF de un diseño de prueba en los cuatro idiomas, con y sin simulación (F4.5).

Uso: python herramientas/prueba_informe.py [carpeta_de_simulacion] [salida]
Sin simulación sale solo el informe de geometría. Con una carpeta con `resultado.json` y `datos.npz` (la de una simulación hecha
desde la interfaz, o `salidas/_simulaciones/...`), sale también la parte de simulación. Código de salida 1 si algo falla.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import numpy as np  # noqa: E402

from antenas import i18n, informe, tipos  # noqa: E402


def main():
    sim = sys.argv[1] if len(sys.argv) > 1 else None
    salida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'salidas', '_pruebas', 'informe')
    os.makedirs(salida, exist_ok=True)
    resultado = datos = None
    if sim:
        resultado = json.load(open(os.path.join(sim, 'resultado.json'), encoding='utf-8-sig'))
        datos = dict(np.load(os.path.join(sim, 'datos.npz')))
    clave = (resultado or {}).get('clave', 'ifa')
    p = tipos.CATALOGO[clave].defectos()
    p.update({k: v for k, v in ((resultado or {}).get('parametros') or {}).items() if not str(k).startswith('_')})
    if not resultado:
        p = tipos.dimensionar(clave, 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50})
    sustrato = 'FR4 JLC 4 capas 1,6 mm' if 'capas' in json.dumps(resultado or {}) else None
    a = tipos.generar(clave, p, sustrato)
    mal = 0
    for cod in ('es', 'en', 'fr', 'de'):
        i18n.fijar_idioma(cod)
        for con in ((False, True) if resultado else (False,)):
            ruta = os.path.join(salida, f'informe_{cod}_{"sim" if con else "geom"}.pdf')
            try:
                informe.generar(ruta, a, f'prueba_{cod}', clave, p, a.info['sustrato'], 2441.75, (2400, 2483.5),
                                resultado if con else None, datos if con else None)
                print('OK ', ruta, os.path.getsize(ruta)//1024, 'KB')
            except Exception as ex:
                mal += 1
                import traceback
                traceback.print_exc()
                print('FALLA', cod, con, ex)
    sys.exit(1 if mal else 0)


if __name__ == '__main__':
    main()
