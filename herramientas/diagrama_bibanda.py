"""Diagramas de radiación de la J-pole bibanda (dos J-pole unidas) en 869 y 2441,75 MHz.

Uso (desde la raíz):  python herramientas/diagrama_bibanda.py [--etiqueta E]
Simula el diseño (k2 1, sep2 3, a2 0,9, toma2 0,25, factor_adaptador 0,95) en banda ancha con el diagrama calculado en cada
frecuencia y guarda en salidas/_barridos/<E>/ los datos (datos.npz) y la figura (diagrama_bibanda.png): cortes polares de
directividad en los dos planos que contienen la normal a la placa (φ = 0° es el plano XZ, perpendicular al eje largo de la
antena; φ = 90° es el plano YZ, que contiene el eje largo) y superficie 3D (radio = dBi sobre −20 dB).
"""
import os
import sys
import json
import math
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(RAIZ, 'herramientas', nombre + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def dibujar(carpeta, datos):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import cm
    fig = plt.figure(figsize=(16, 10))
    piso = -20.0
    for fila, (f, d) in enumerate(datos.items()):
        theta, phi, g = d['theta'], d['phi'], d['d']
        dmax = float(g.max())
        for col, (phi0, nombre) in enumerate(((0, 'plano XZ (perpendicular al eje largo)'), (90, 'plano YZ (contiene el eje largo)'))):
            ax = fig.add_subplot(2, 3, fila*3 + col + 1, projection='polar')
            ip = int(np.argmin(np.abs(phi - phi0)))
            iq = int(np.argmin(np.abs(phi - (phi0 + 180) % 360)))
            ang = np.radians(np.concatenate([theta, 360 - theta[::-1]]))
            val = np.concatenate([g[:, ip], g[::-1, iq]])
            ax.plot(ang, np.maximum(val, dmax + piso), color='#c0392b', lw=2)
            ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
            ax.set_rlim(dmax + piso, dmax + 1)
            ax.set_title(f'{f:g} MHz · {nombre}\nmáx {dmax:.1f} dBi', fontsize=9)
            ax.tick_params(labelsize=7)
        ax3 = fig.add_subplot(2, 3, fila*3 + 3, projection='3d')
        th, ph = np.meshgrid(np.radians(theta), np.radians(phi), indexing='ij')
        r = np.maximum(g - dmax, piso) - piso
        x, y, z = r*np.sin(th)*np.cos(ph), r*np.sin(th)*np.sin(ph), r*np.cos(th)
        ax3.plot_surface(x, y, z, facecolors=cm.viridis((g - dmax - piso)/(-piso)), linewidth=0, antialiased=True, shade=False)
        ax3.set_title(f'{f:g} MHz · 3D (x, y = plano de la placa; z = normal)', fontsize=9)
        ax3.set_box_aspect((1, 1, 1)); ax3.tick_params(labelsize=6)
        lim = -piso
        ax3.set_xlim(-lim, lim); ax3.set_ylim(-lim, lim); ax3.set_zlim(-lim, lim)
    fig.suptitle('J-pole bibanda (dos J-pole unidas) · directividad simulada (FR4 1,6 mm)', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta, 'diagrama_bibanda.png'), dpi=110)


def main():
    args = sys.argv[1:]
    etiqueta = 'DIAG_bibanda'
    if '--etiqueta' in args:
        etiqueta = args[args.index('--etiqueta') + 1]
    os.environ.setdefault('ANTENAS_GPU', '1')
    os.environ.setdefault('ANTENAS_BORRAR_SIM', '1')
    import numpy as np
    from antenas import tipos, simulacion, geometria as g
    barrido = _cargar('barrido')
    jd = _cargar('jpole_dual')
    sus = 'FR4 JLC 1,6 mm'
    s = tipos.sustrato(sus)
    f_baja = 868.0
    b = tipos.dimensionar('jpole', f_baja*1e6, {}, sus)
    b.pop('_aviso', None)
    b['factor_adaptador'] = 0.95
    a = jd.construir_union(tipos, g, sus, b, 1.0, 3.0, 0.9, 0.25, f_baja, 2441.75)
    cfg = simulacion.PRECISIONES['normal']
    lam_min = simulacion.C0/(3.8*f_baja*1e6)*1e3
    sup = a.cobre('F.Cu')
    w_min = min(simulacion.ancho_minimo(sup, 3.0), a.info.get('pista_minima_mm') or 99)
    s_min = min(simulacion.hueco_minimo(sup, 3.0), a.info.get('hueco_minimo_mm') or 99)
    paso = round(0.9*max(min(lam_min/math.sqrt(s.er)/cfg['lam_div'], cfg['factor_detalle']*w_min/2,
                             cfg['factor_detalle']*s_min/2), 0.08), 3)
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    lock = barrido._bloqueo()
    datos, resumen = {}, {}
    try:
        for f in (869.0, 2441.75):
            print(f'=== diagrama a {f:g} MHz (malla {paso} mm)', flush=True)
            r = simulacion.simular(a, s, f_baja*1e6, 'normal', nf2ff=True, progreso=lambda m: None, rango=(0.45, 3.8),
                                   paso=paso, f_radiacion=f*1e6)
            datos[f] = {'theta': np.asarray(r['theta']), 'phi': np.asarray(r['phi']), 'd': np.asarray(r['directividad_dBi_grid'])}
            resumen[f] = barrido._radiacion(r)
            resumen[f]['s11_dB'] = round(float(simulacion._s11_en(r, f*1e6)[0]), 1)
            print(' ', json.dumps(resumen[f], ensure_ascii=False, default=float), flush=True)
        np.savez(os.path.join(carpeta, 'datos.npz'), **{f'{f:g}_{k}': v for f, d in datos.items() for k, v in d.items()})
        json.dump({f'{f:g}': v for f, v in resumen.items()}, open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False, default=float)
        dibujar(carpeta, datos)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
