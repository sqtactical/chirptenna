"""Comprobación rápida de todos los tipos de antena (sin simular): para antes de cada release o PR.

Para cada tipo del catálogo y cada banda: dimensiona, genera, comprueba las reglas de fabricación y exporta
(placa KiCad, Gerber, DXF) con el DRC de KiCad. Escribe un resumen en la carpeta de salida.

Uso (desde la raíz):  python herramientas/comprobar_tipos.py [carpeta_salida] [--bandas 866.5,2441.75] [--solo tipo1,tipo2]
Sale con código 1 si algún tipo falla al generar o exportar, o tiene errores de DRC o de reglas.
"""
import os
import sys
import json
import time
import argparse
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from antenas import tipos, exportar, fabricacion, __version__   # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('salida', nargs='?', default=os.path.join(RAIZ, 'salidas', '_comprobar_tipos'))
    ap.add_argument('--bandas', default='866.5,2441.75', help='frecuencias en MHz, separadas por comas')
    ap.add_argument('--solo', default='', help='tipos a comprobar, separados por comas (por defecto, todos)')
    a = ap.parse_args()
    bandas = [float(x) for x in a.bandas.split(',') if x]
    claves = [c for c in tipos.CATALOGO if not a.solo or c in a.solo.split(',')]
    resumen, fallos = [], 0
    print(f'Chirptenna {__version__}: {len(claves)} tipos × {len(bandas)} bandas -> {a.salida}')
    for clave in claves:
        for f in bandas:
            t0 = time.time()
            fila = {'tipo': clave, 'f_MHz': f}
            try:
                p = tipos.dimensionar(clave, f*1e6, {})
                p.pop('_aviso', None)
                ant = tipos.generar(clave, p)
                errores_fab = [m for n, m in fabricacion.comprobar(ant) if n == 'error']
                nombre = f'{clave}_{f:g}MHz'
                r = exportar.exportar_todo(ant, os.path.join(a.salida, nombre), nombre)
                fila.update(placa_mm=ant.info.get('placa_mm'), drc=r['drc'], fabricacion=errores_fab,
                            logo_mm=r['serigrafia']['logo_mm'], ok=not r['drc'] and not errores_fab)
            except Exception as ex:
                fila.update(ok=False, error=f'{type(ex).__name__}: {ex}', traza=traceback.format_exc())
            fila['s'] = round(time.time() - t0, 1)
            fallos += not fila['ok']
            resumen.append(fila)
            estado = 'OK ' if fila['ok'] else 'MAL'
            detalle = fila.get('error') or '; '.join([f'{t}: {d}' for t, _, d in fila.get('drc', [])][:2] +
                                                    fila.get('fabricacion', [])[:2])
            print(f"  {estado} {clave:22s} {f:8g} MHz  placa {fila.get('placa_mm')}  logo {fila.get('logo_mm')}  "
                  f"{fila['s']:5.1f} s  {detalle}")
    # Guía de la interfaz (galería, básicos y ayudas): cada tipo y parámetro tiene que estar documentado
    from antenas import guia
    for e in guia.comprobar():
        print(f'  MAL guía: {e}')
        fallos += 1
    os.makedirs(a.salida, exist_ok=True)
    with open(os.path.join(a.salida, 'resumen.json'), 'w', encoding='utf-8') as fh:
        json.dump({'version': __version__, 'fallos': fallos, 'casos': resumen}, fh, indent=2, ensure_ascii=False,
                  default=str)
    print(f'{len(resumen) - fallos}/{len(resumen)} bien')
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
