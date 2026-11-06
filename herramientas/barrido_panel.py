"""Barrido del largo del brazo del panel (2x2 o 4x4): elige el que da mejor S11 en TODA la banda ISM 2,4 GHz.
El 'centro de banda' del panel salta (S11 ondulado), asi que el criterio es el peor S11 en 2400-2483,5 MHz."""
import os, sys, json, time
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ); sys.path.insert(0, RAIZ); os.environ['ANTENAS_GPU'] = '1'
from antenas import tipos, simulacion
F_OBJ = 2441.75e6; SUS = 'FR4 JLC 1,6 mm'; clave = 'panel_dipolos'
tamano = int(sys.argv[1]); e = int(sys.argv[2]); largos = [float(x) for x in sys.argv[3].split(',')]
etiqueta = sys.argv[4] if len(sys.argv) > 4 else f'{tamano}x{tamano}_e{e}'
extra = {k: float(v) for k, v in (a.split('=') for a in sys.argv[5].split(','))} if len(sys.argv) > 5 else {}
tipo = tipos.CATALOGO[clave]; s = tipos.sustrato(SUS); esc = tipo.escala
p = tipos.dimensionar(clave, F_OBJ, {'tamano': tamano, 'elemento': e, **extra}, SUS, fijos=('tamano', 'elemento', *extra)); p.pop('_aviso', None)
prop = {k: p[k]/p[esc] for k in tipo.escala_conjunta}
def con(x):
    q = dict(p, **{esc: round(x, 3)})
    for k, r_ in prop.items(): q[k] = round(r_*x, 3)
    return q
r0 = simulacion.simular(tipos.generar(clave, con(largos[0]), SUS), s, F_OBJ, 'normal', nf2ff=False, progreso=lambda m: None)
paso = round(0.9*r0['paso_malla_mm'], 3)
print(f'=== {etiqueta}: malla fijada {paso} mm', flush=True)
filas = []
for x in largos:
    t0 = time.time()
    r = simulacion.simular(tipos.generar(clave, con(x), SUS), s, F_OBJ, 'normal', nf2ff=False, progreso=lambda m: None, paso=paso)
    banda = [simulacion._s11_en(r, f*1e6)[0] for f in (2400, 2420, 2441.75, 2460, 2483.5)]
    flo, fhi = r['banda_Hz']
    fila = {'x': x, 'peor_banda_dB': round(max(banda), 1), 's11_obj_dB': round(banda[2], 1), 'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
            'f_res_MHz': round(r['f_resonancia_Hz']/1e6), 's': round(time.time() - t0)}
    filas.append(fila); print('  ', json.dumps(fila), flush=True)
mejor = min(filas, key=lambda f: f['peor_banda_dB'])
print('  mejor', mejor, flush=True)
a = tipos.generar(clave, con(mejor['x']), SUS)
r = simulacion.simular(a, s, F_OBJ, 'normal', nf2ff=True, progreso=lambda m: None, paso=paso, f_radiacion=F_OBJ)
flo, fhi = r['banda_Hz']
res = {'etiqueta': etiqueta, 'largo_brazo': mejor['x'], 'barrido': filas, 's11_obj_dB': round(simulacion._s11_en(r, F_OBJ)[0], 1),
       'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)], 'dir_dBi': round(r['directividad_dBi'], 2),
       'ganancia_dBi': round(r['ganancia_dBi'], 2), 'eficiencia_%': round(100*r['eficiencia_radiacion'], 1),
       'direccion_max': r.get('direccion_max'), 'placa_mm': a.info.get('placa_mm'), 'parametros': con(mejor['x'])}
print('  RESULTADO', json.dumps({k: v for k, v in res.items() if k not in ('barrido', 'parametros')}, ensure_ascii=False), flush=True)
os.makedirs(os.path.join(RAIZ, 'salidas', '_afinado_panel'), exist_ok=True)
json.dump(res, open(os.path.join(RAIZ, 'salidas', '_afinado_panel', f'{etiqueta}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
print('TERMINADO', flush=True)

