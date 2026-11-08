"""Resume todos los barridos de salidas/_barridos en una tabla (docs/desarrollo/barridos_gpu.md y .csv).

Uso (desde la raíz):  python herramientas/resumen_barridos.py
Por cada barrido, la mejor configuración (menor peor S11 en la banda), con ganancia y eficiencia si se calcularon.
Veredicto: «va» si el peor S11 de la banda es ≤ −10 dB, «justo» entre −10 y −6 dB, «no va» por encima de −6 dB.
"""
import os
import csv
import glob
import json
import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def veredicto(db):
    return 'va' if db <= -10 else ('justo' if db <= -6 else 'no va')


def main():
    filas = []
    for ruta in sorted(glob.glob(os.path.join(RAIZ, 'salidas', '_barridos', '*', 'resumen.json'))):
        nombre = os.path.basename(os.path.dirname(ruta))
        r = json.load(open(ruta, encoding='utf-8'))
        if 'filas' not in r:                          # DIAG_*/RAD_*: no son barridos
            continue
        def radiacion(f):
            return f.get('radiacion') or next((m.get('radiacion') for m in r.get('mejores', []) if m['cambios'] == f['cambios']), None) or {}

        def atras(f):
            """Yagi cuyo haz sale hacia el reflector (φ 90° = +y, hacia los directores): no sirve aunque adapte."""
            phi = (radiacion(f).get('direccion_max') or {}).get('phi')
            return r['tipo'] in ('yagi_boom', 'yagi_koch') and phi is not None and 180 <= phi <= 360

        buenas = sorted([f for f in r['filas'] if 'peor_banda_dB' in f], key=lambda f: (atras(f), f['peor_banda_dB']))
        if not buenas:
            continue
        f = buenas[0]
        rad = radiacion(f)
        ver = veredicto(f['peor_banda_dB']) + (' (haz atrás)' if atras(f) else '')
        filas.append({'barrido': nombre, 'tipo': r['tipo'], 'f_MHz': r['f_MHz'], 'configs': len(r['filas']),
                      'peor_banda_dB': f['peor_banda_dB'], 'veredicto': ver,
                      'f_res_MHz': f['f_res_MHz'], 'banda_10dB': f['banda_10dB'],
                      'ganancia_dBi': rad.get('ganancia_dBi'), 'eficiencia_%': rad.get('eficiencia_%'),
                      'pol': rad.get('pol_theta0'), 'ar_dB': rad.get('ar_dB_theta0'),
                      'mejor': json.dumps(f['cambios'], ensure_ascii=False)})
    filas.sort(key=lambda x: (x['tipo'], x['f_MHz'], x['barrido']))
    destino = os.path.join(RAIZ, 'docs', 'desarrollo')
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, 'barridos_gpu.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, list(filas[0]), delimiter=';')
        w.writeheader()
        w.writerows(filas)
    with open(os.path.join(destino, 'barridos_gpu.md'), 'w', encoding='utf-8') as fh:
        fh.write(f"# Barridos en GPU: qué va y qué no ({datetime.date.today():%d-%m-%Y})\n\n")
        fh.write("Generado por `python herramientas/resumen_barridos.py` a partir de `salidas/_barridos/*/resumen.json`.\n"
                 "Solo simulación (openEMS en GPU, FR4 de 1,6 mm con εr 4,5): sin medir ninguna placa. La ganancia y la eficiencia en GPU "
                 "salen algo altas. En las Yagi se prefiere la mejor configuración cuyo haz sale hacia los directores («haz atrás» = solo adapta radiando al revés). «Peor S11» es el peor valor en toda la banda de uso; va ≤ −10 dB, justo hasta −6 dB. "
                 "Etiquetas: `A_` = tamaño base de `dimensionar`; `B_` = barrido de parámetros; sin prefijo = campaña de los tipos nuevos.\n\n")
        fh.write("| Tipo | f (MHz) | Barrido | Configs | Peor S11 (dB) | Veredicto | f res. (MHz) | Banda −10 dB | G (dBi) | η (%) | Mejor |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        for x in filas:
            fh.write(f"| {x['tipo']} | {x['f_MHz']:g} | {x['barrido']} | {x['configs']} | {x['peor_banda_dB']} | **{x['veredicto']}** | "
                     f"{x['f_res_MHz']} | {x['banda_10dB']} | {x['ganancia_dBi'] if x['ganancia_dBi'] is not None else ''} | "
                     f"{x['eficiencia_%'] if x['eficiencia_%'] is not None else ''} | `{x['mejor']}` |\n")
    print(f'{len(filas)} barridos -> docs/desarrollo/barridos_gpu.md')


if __name__ == '__main__':
    main()