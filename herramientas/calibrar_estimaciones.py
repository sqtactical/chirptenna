"""Calibra las estimaciones de frecuencia de antenas/tipos.py con los resultados simulados.

Para cada resultado.json de los lotes de validación compara la frecuencia simulada (de la antena tal
como se simuló, sin cortar si lleva sobrelargo) con la de la fórmula para esa misma geometría, y saca
un factor f_simulada/f_fórmula por tipo y banda. Lo guarda en antenas/calibracion_estimaciones.json,
que tipos.estimar_f aplica (y con ello dimensionar): el ajuste por simulación empieza más cerca.

Uso (desde la raíz):  python herramientas/calibrar_estimaciones.py
Volver a ejecutarlo cuando haya simulaciones nuevas (y reiniciar la interfaz).
"""
import os
import sys
import glob
import json
import math

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from antenas import tipos   # noqa: E402

# _validacion (la primera) es de antes de cambios grandes en los generadores; de la 2 en adelante,
# la verificación del pedido de 2,4 GHz confirmó que coinciden con el código actual (±3 %)
LOTES = ('_validacion2', '_validacion3', '_validacion4')
EXCLUIR_FAMILIAS = ('panel',)          # el panel no itera la frecuencia (S11 ondulado)
# resultados de una geometría que ya no existe: el Sierpinski de _validacion2 no tenía los cuellos
EXCLUIR = {('_validacion2', 'monopolo_sierpinski')}
CAMBIO_PARASITOS_KOCH = __import__('time').mktime((2026, 11, 1, 21, 40, 0, 0, 0, -1))


def muestras():
    vistos = set()
    for ruta in sorted(glob.glob(os.path.join(RAIZ, 'salidas', '*', '*', 'resultado.json'))):
        lote = os.path.basename(os.path.dirname(os.path.dirname(ruta)))
        if lote not in LOTES:
            continue
        r = json.load(open(ruta, encoding='utf-8'))
        clave = r.get('clave')
        if not r.get('ok') or clave not in tipos.CATALOGO or tipos.CATALOGO[clave].familia in EXCLUIR_FAMILIAS:
            continue
        if (lote, clave) in EXCLUIR:
            continue
        # las Yagi de Koch simuladas antes de dar a los parásitos la forma del dipolo (01-11 21:40)
        if (clave in ('yagi_boom', 'yagi_koch') and int(r['parametros'].get('iteracion', 0)) > 0
                and os.path.getmtime(ruta) < CAMBIO_PARASITOS_KOCH):
            continue
        if (r.get('eficiencia_radiacion_%') or 100) < 10:
            continue                       # resonancia falsa (cobre desconectado en la malla)
        p = dict(r['parametros'])
        p.pop('k_sim', None)
        try:
            a = tipos.generar(clave, p)
        except Exception:                  # parámetros de una versión anterior del generador
            continue
        if max(a.info.get('placa_mm') or [0]) > 2000:
            continue                       # p. ej. la Yagi con boom de antes de las separaciones en λ0
        # la simulación es de la antena sin cortar: con sobrelargo se compara con su frecuencia
        f_form = tipos.estimar_f(clave, p, calibrada=False)/1e6
        if a.info.get('f_sin_cortar_MHz'):
            f_form /= 1 + p.get('sobrelargo', 0)/100
        f_sim = r['f_resonancia_MHz']
        k = f_sim/f_form
        if not 0.6 < k < 1.6:
            continue
        clave_dup = (clave, json.dumps(p, sort_keys=True))
        if clave_dup in vistos:
            continue
        vistos.add(clave_dup)
        yield {'clave': tipos.clave_calibracion(clave, p), 'origen': os.path.relpath(os.path.dirname(ruta), RAIZ), 'f_formula_MHz': round(f_form, 1),
               'f_simulada_MHz': f_sim, 'factor': round(k, 4), 'criterio': r.get('criterio')}


def main():
    por_tipo = {}
    for m in muestras():
        por_tipo.setdefault(m['clave'], []).append(m)
    salida = {}
    print(f'{"tipo":22s} {"n":>2s}  factor por banda                 dispersión')
    for clave, ms in sorted(por_tipo.items()):
        bandas = {}
        for m in ms:
            bandas.setdefault('868' if m['f_simulada_MHz'] < 1500 else '2400', []).append(m)
        puntos = []
        for b, mb in sorted(bandas.items()):
            lk = [math.log(m['factor']) for m in mb]
            puntos.append([round(math.exp(sum(math.log(m['f_simulada_MHz']) for m in mb)/len(mb)), 1),
                           round(math.exp(sum(lk)/len(lk)), 4)])
        # dispersión: desviación de cada muestra respecto al factor de su banda (en %), solo en las
        # bandas con dos o más muestras (con una sola no hay con qué compararla)
        desv = []
        for b, mb in bandas.items():
            if len(mb) > 1:
                kb = math.exp(sum(math.log(m['factor']) for m in mb)/len(mb))
                desv += [100*(m['factor']/kb - 1) for m in mb]
        disp = round(math.sqrt(sum(d*d for d in desv)/len(desv)), 1) if desv else None
        salida[clave] = {'puntos': puntos, 'n': len(ms), 'dispersion_%': disp, 'muestras': ms}
        print(f'{clave:22s} {len(ms):2d}  ' + ', '.join(f'{f:.0f} MHz ×{k:.3f}' for f, k in puntos).ljust(32) +
              (f' ±{disp:.1f} %' if disp is not None else ' (sin datos de dispersión)'))
    with open(tipos.RUTA_CALIBRACION, 'w', encoding='utf-8') as fh:
        json.dump(salida, fh, indent=2, ensure_ascii=False)
    print('Guardado', tipos.RUTA_CALIBRACION)


if __name__ == '__main__':
    main()
