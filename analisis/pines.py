"""Lista los pines de los componentes indicados (posición en mm, capa, net).

Uso: python pines.py <FlyingProbeTesting.json> REF [REF ...]
"""
import sys
import json

MIL = 0.0254

d = json.load(open(sys.argv[1], encoding='utf-8'))
refs = set(sys.argv[2:])
campos = d['pins']['fields']
for fila in d['pins']['rows']:
    p = dict(zip(campos, fila))
    if p['PIN_NAME'].rsplit('_', 1)[0] in refs:
        print(f"{p['PIN_NAME']:8s} x={p['PIN_X']*MIL:6.2f} y={p['PIN_Y']*MIL:6.2f} mm  capa={p['LAYER']}  "
              f"net={p['NET_NAME']:12s} pad={p['PAD_SIZEX']*MIL:.1f}x{p['PAD_SIZEY']*MIL:.1f} mm")
