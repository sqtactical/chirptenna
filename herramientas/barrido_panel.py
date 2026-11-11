"""Barrido del largo del brazo del panel (2x2 o 4x4): elige el que da mejor S11 en TODA la banda de uso.
El 'centro de banda' del panel salta (S11 ondulado), asi que el criterio es el peor S11 en la banda.

Uso (desde la raiz):
    python herramientas/barrido_panel.py <tamano> <elemento> <largos,...> [etiqueta] [param=valor,...]
                                         [--f MHz] [--banda ini fin] [--solo-lista]

  --f MHz        frecuencia de diseno (por defecto 2441,75)
  --banda a b    banda donde se mide el peor S11, en MHz (por defecto la ISM de 2,4 GHz: 2400 2483,5; para 5,8 GHz: 5725 5875)
  --solo-lista   no simula: da la placa y el paso de malla de cada largo
Resultados en salidas/_afinado_panel/<etiqueta>.json (el tamano de malla se fija con el primer largo)."""
import os, sys, json, time
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ); sys.path.insert(0, RAIZ); os.environ.setdefault('ANTENAS_GPU', '1')
from antenas import tipos, simulacion

args = sys.argv[1:]
F_MHZ, BANDA, SOLO_LISTA = 2441.75, (2400.0, 2483.5), False
for opc, n in (('--f', 1), ('--banda', 2), ('--solo-lista', 0)):
    if opc in args:
        k = args.index(opc)
        if opc == '--f':
            F_MHZ = float(args[k + 1])
        elif opc == '--banda':
            BANDA = (float(args[k + 1]), float(args[k + 2]))
        else:
            SOLO_LISTA = True
        del args[k:k + 1 + n]
F_OBJ = F_MHZ*1e6; SUS = 'FR4 JLC 1,6 mm'; clave = 'panel_dipolos'
tamano = int(args[0]); e = int(args[1]); largos = [float(x) for x in args[2].split(',')]
etiqueta = args[3] if len(args) > 3 else f'{tamano}x{tamano}_e{e}'
extra = {k: float(v) for k, v in (a.split('=') for a in args[4].split(','))} if len(args) > 4 else {}
tipo = tipos.CATALOGO[clave]; s = tipos.sustrato(SUS); esc = tipo.escala
p = tipos.dimensionar(clave, F_OBJ, {'tamano': tamano, 'elemento': e, **extra}, SUS, fijos=('tamano', 'elemento', *extra)); p.pop('_aviso', None)
prop = {k: p[k]/p[esc] for k in tipo.escala_conjunta}
def con(x):
    q = dict(p, **{esc: round(x, 3)})
    for k, r_ in prop.items(): q[k] = round(r_*x, 3)
    return q
puntos = [BANDA[0], (BANDA[0] + BANDA[1])/2 - (BANDA[1] - BANDA[0])/4, F_MHZ, (BANDA[0] + BANDA[1])/2 + (BANDA[1] - BANDA[0])/4, BANDA[1]]
if SOLO_LISTA:
    for x in largos:
        a = tipos.generar(clave, con(x), SUS)
        print(f'largo {x}: placa {a.info.get("placa_mm")} mm, pista min {a.info.get("pista_minima_mm")}, hueco min {a.info.get("hueco_minimo_mm")}')
    sys.exit(0)
r0 = simulacion.simular(tipos.generar(clave, con(largos[0]), SUS), s, F_OBJ, 'normal', nf2ff=False, progreso=lambda m: None)
paso = round(0.9*r0['paso_malla_mm'], 3)
print(f'=== {etiqueta}: {F_MHZ:g} MHz, banda {BANDA[0]:g}-{BANDA[1]:g} MHz, malla fijada {paso} mm ({r0["celdas"]/1e6:.2f} M celdas)', flush=True)
filas = []
for x in largos:
    t0 = time.time()
    r = simulacion.simular(tipos.generar(clave, con(x), SUS), s, F_OBJ, 'normal', nf2ff=False, progreso=lambda m: None, paso=paso)
    banda = [simulacion._s11_en(r, f*1e6)[0] for f in puntos]
    flo, fhi = r['banda_Hz']
    fila = {'x': x, 'peor_banda_dB': round(max(banda), 1), 's11_obj_dB': round(banda[2], 1), 'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)],
            'f_res_MHz': round(r['f_resonancia_Hz']/1e6), 's': round(time.time() - t0)}
    filas.append(fila); print('  ', json.dumps(fila), flush=True)
mejor = min(filas, key=lambda f: f['peor_banda_dB'])
print('  mejor', mejor, flush=True)
a = tipos.generar(clave, con(mejor['x']), SUS)
r = simulacion.simular(a, s, F_OBJ, 'normal', nf2ff=True, progreso=lambda m: None, paso=paso, f_radiacion=F_OBJ)
flo, fhi = r['banda_Hz']
res = {'etiqueta': etiqueta, 'f_MHz': F_MHZ, 'banda_MHz': BANDA, 'largo_brazo': mejor['x'], 'barrido': filas,
       's11_obj_dB': round(simulacion._s11_en(r, F_OBJ)[0], 1),
       'banda_10dB': None if flo is None else [round(flo/1e6), round(fhi/1e6)], 'dir_dBi': round(r['directividad_dBi'], 2),
       'ganancia_dBi': round(r['ganancia_dBi'], 2), 'eficiencia_%': round(100*r['eficiencia_radiacion'], 1),
       'direccion_max': r.get('direccion_max'), 'placa_mm': a.info.get('placa_mm'), 'parametros': con(mejor['x'])}
print('  RESULTADO', json.dumps({k: v for k, v in res.items() if k not in ('barrido', 'parametros')}, ensure_ascii=False), flush=True)
os.makedirs(os.path.join(RAIZ, 'salidas', '_afinado_panel'), exist_ok=True)
json.dump(res, open(os.path.join(RAIZ, 'salidas', '_afinado_panel', f'{etiqueta}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=float)
print('TERMINADO', flush=True)
