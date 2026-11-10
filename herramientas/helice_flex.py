"""Hélice cuadrifilar (QHA) impresa en flex y enrollada, para GPS L1 y otras bandas de polarización circular (banco de pruebas).

Uso (desde la raíz):
    python herramientas/helice_flex.py [param=v1,v2,…]… [--f MHz] [--etiqueta E] [--res mm] [--dibujar] [--solo-lista]

  Es una antena de polarización circular que cabe en una tira de flex: cuatro brazos helicoidales de λ/4 (de media vuelta, por
  defecto) sobre un cilindro de diámetro D; se imprimen planos (cuatro rayas diagonales en un rectángulo de π·D de ancho) y se
  enrollan. Son dos dipolos helicoidales cruzados (brazos 1–3 y 2–4), alimentados en cuadratura (90°). Sin plano de masa.
  Parámetros (`param=` con varios valores barre todas las combinaciones; cada configuración son DOS simulaciones):
    D        diámetro del cilindro, mm (defecto 14)
    k        largo de cada brazo en veces λ/4 del aire (defecto 1,0; el flex de 50 µm acorta ~1–2 %)
    vueltas  vueltas de cada brazo (defecto 0,5)
    sentido  +1 hélice a derechas, −1 a izquierdas (defecto +1)
    ancho    ancho de la tira, mm (defecto 1,0; solo para el dibujo: el modelo es un hilo, de radio equivalente ancho/4)
  --f MHz     frecuencia (defecto 1575,42: GPS L1)
  --res mm    paso de malla en la antena (defecto 1,0)
  --dibujar   solo dibuja la tira plana (PNG y DXF en salidas/_barridos/<E>) y no simula
  --solo-lista  muestra las dimensiones de cada configuración

Modelo: cada brazo es un hilo PEC (`AddCurve`, como el tutorial de la hélice de openEMS) y el pie de cada brazo se une por una
tira radial al centro, donde hay una rendija de 1 mm con un puerto de 50 Ω (dos puertos: uno para el dipolo 1–3 y otro para el
2–4). Se simula cada puerto por separado y se combinan los campos con 90° de desfase (superposición exacta: el sistema es
lineal). Con el sentido de giro de la hélice y el signo de los 90° salen RHCP o LHCP; se dan los dos y se queda el mejor.
Es un modelo de hilo con malla de ~1 mm: sirve para comparar dimensiones, no para fiarse de ±2 % en frecuencia.
Resultados en salidas/_barridos/<E> (resultados.jsonl y resumen.json).
"""
import os
import sys
import json
import math
import time
import itertools
import datetime
import tempfile
import hashlib
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

C0 = 299792458.0
DEFECTOS = {'D': 14.0, 'k': 1.0, 'vueltas': 0.5, 'sentido': 1.0, 'ancho': 1.0}


def dimensiones(f_MHz, p):
    """Altura y largo de cada brazo para los parámetros p."""
    lam = C0/(f_MHz*1e6)*1e3
    arco = p['k']*lam/4
    giro = p['vueltas']*math.pi*p['D']                 # lo que avanza el brazo alrededor del cilindro, mm
    if arco <= giro:
        raise ValueError(f'el brazo ({arco:.1f} mm) no llega a dar {p["vueltas"]} vueltas con D = {p["D"]} mm')
    return {'lambda_mm': lam, 'arco_mm': arco, 'altura_mm': math.sqrt(arco**2 - giro**2), 'ancho_tira_mm': math.pi*p['D']}


def brazo(p, h, k, paso):
    """Puntos (x, y, z) del brazo k (0–3) de la hélice, con el pie en z = 0."""
    import numpy as np
    r = p['D']/2
    arco = math.hypot(h, p['vueltas']*math.pi*p['D'])
    n = max(int(math.ceil(arco/paso)), 8)
    z = np.linspace(0.0, h, n + 1)
    fi = math.radians(90.0*k) + p['sentido']*2*math.pi*p['vueltas']*z/h
    return np.array([r*np.cos(fi), r*np.sin(fi), z])


def tira_plana(f_MHz, p):
    """Los cuatro brazos desenrollados: polígonos de shapely en un rectángulo de π·D × altura (mm), y el rectángulo."""
    import numpy as np
    from shapely.ops import unary_union
    from antenas import geometria as g
    d = dimensiones(f_MHz, p)
    W, h = d['ancho_tira_mm'], d['altura_mm']
    piezas = []
    for k in range(4):
        z = np.linspace(0.0, h, 200)
        x = (W*(k/4 + p['sentido']*p['vueltas']*z/h)) % W
        tramo = [(x[0], z[0])]
        for i in range(1, len(z)):
            if abs(x[i] - x[i - 1]) > W/2:                       # salta de un borde al otro: se corta la raya
                if len(tramo) > 1:
                    piezas.append(g.engordar(tramo, p['ancho']))
                tramo = []
            tramo.append((x[i], z[i]))
        if len(tramo) > 1:
            piezas.append(g.engordar(tramo, p['ancho']))
    return unary_union(piezas), (W, h), d


def dibujar(f_MHz, p, carpeta, nombre):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import ezdxf
    from antenas import geometria as g
    cobre, (W, h), d = tira_plana(f_MHz, p)
    fig, ax = plt.subplots(figsize=(6, 6*(h + 8)/(W + 8)))
    ax.add_patch(plt.Rectangle((0, 0), W, h, fill=False, ec='0.5'))
    for pol in g.poligonos(cobre):
        xs, ys = pol.exterior.xy
        ax.fill(xs, ys, fc='#d08a2c', ec='#8a5a10')
    ax.set_aspect('equal')
    ax.set_title(f'QHA {f_MHz:g} MHz: tira de flex {W:.1f} × {h:.1f} mm (enrollar en D = {p["D"]:g} mm)', fontsize=9)
    ax.set_xlabel('mm (alrededor del cilindro; los bordes se juntan al enrollar)')
    fig.savefig(os.path.join(carpeta, nombre + '.png'), dpi=130, bbox_inches='tight')
    plt.close(fig)
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (W, 0), (W, h), (0, h)], close=True, dxfattribs={'layer': 'CONTORNO'})
    for pol in g.poligonos(cobre):
        msp.add_lwpolyline(list(pol.exterior.coords), close=True, dxfattribs={'layer': 'COBRE'})
    doc.saveas(os.path.join(carpeta, nombre + '.dxf'))


def simular_helice(p, f_MHz, res, sim_dir, puerto_activo):
    """Una simulación (sólo el puerto `puerto_activo` 1 o 2 excitado). Devuelve (S-parámetros a rejilla, campos en f0)."""
    import numpy as np
    from antenas import gpu, simulacion          # simulacion fija CSXCAD_INSTALL_PATH: tiene que ir antes que CSXCAD
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    d = dimensiones(f_MHz, p)
    h, r = d['altura_mm'], p['D']/2
    f0 = f_MHz*1e6
    fc = 0.4*f0
    lam_min = C0/(f0 + fc)*1e3
    FDTD = openEMS(NrTS=400000, EndCriteria=1e-4)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8']*6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    gap = 0.5
    # malla: fina junto a la antena, más gruesa hacia fuera
    for dim, fijas in (('x', [-r - 2, -gap, 0, gap, r + 2]), ('y', [-r - 2, -gap, 0, gap, r + 2]), ('z', [-2, 0, h, h + 2])):
        mesh.AddLine(dim, fijas)
        mesh.SmoothMeshLines(dim, res)
    margen = lam_min*1.3
    mesh.AddLine('x', [-r - margen, r + margen])
    mesh.AddLine('y', [-r - margen, r + margen])
    mesh.AddLine('z', [-margen, h + margen])
    for dim in 'xyz':
        mesh.SmoothMeshLines(dim, lam_min/20, ratio=1.4)
    metal = CSX.AddMetal('hilos')
    for k in range(4):
        metal.AddCurve(brazo(p, h, k, res/2), priority=10)
    # pies de los brazos: tira radial hasta la rendija central (los brazos 1–3 por el eje x, los 2–4 por el y)
    metal.AddCurve(np.array([[r, gap], [0, 0], [0, 0]]), priority=10)
    metal.AddCurve(np.array([[-r, -gap], [0, 0], [0, 0]]), priority=10)
    metal.AddCurve(np.array([[0, 0], [r, gap], [0, 0]]), priority=10)
    metal.AddCurve(np.array([[0, 0], [-r, -gap], [0, 0]]), priority=10)
    p1 = FDTD.AddLumpedPort(1, 50, [-gap, 0, 0], [gap, 0, 0], 'x', 1.0 if puerto_activo == 1 else 0.0, priority=20)
    p2 = FDTD.AddLumpedPort(2, 50, [0, -gap, 0], [0, gap, 0], 'y', 1.0 if puerto_activo == 2 else 0.0, priority=20)
    caja = FDTD.CreateNF2FFBox()
    os.makedirs(sim_dir, exist_ok=True)
    if not (gpu.activa() and gpu.ejecutar(FDTD, sim_dir, lambda m: None)):
        FDTD.Run(sim_dir, cleanup=True, verbose=0, numThreads=int(os.environ.get('ANTENAS_HILOS', '0')))
    f = np.linspace(f0 - fc, f0 + fc, 801)
    p1.CalcPort(sim_dir, f)
    p2.CalcPort(sim_dir, f)
    theta = np.arange(0, 181, 2.0)
    phi = np.arange(0, 361, 5.0)
    rad = caja.CalcNF2FF(sim_dir, f0, theta, phi, center=[0, 0, h/2*1e-3], read_cached=False)
    act, pas = (p1, p2) if puerto_activo == 1 else (p2, p1)
    i0 = int(np.argmin(np.abs(f - f0)))
    s = {'f': f, 'Saa': act.uf_ref/act.uf_inc, 'Spa': pas.uf_ref/act.uf_inc, 'P_inc': act.P_inc, 'P_acc': act.P_acc,
         'Z': act.uf_tot/act.if_tot}
    return s, {'theta': theta, 'phi': phi, 'E_theta': rad.E_theta[0], 'E_phi': rad.E_phi[0], 'Prad': float(rad.Prad[0])}, i0


def combinar(sA, cA, sB, cB, i0):
    """Alimenta los dos dipolos a la vez con ±90° de desfase: el mejor de los dos signos. Devuelve un diccionario de resultados."""
    import numpy as np
    theta, phi = cA['theta'], cA['phi']
    dth, dph = np.radians(theta[1] - theta[0]), np.radians(phi[1] - phi[0])
    seno = np.sin(np.radians(theta))[:, None]

    def integral(e_th, e_ph):
        return float(np.sum((np.abs(e_th)**2 + np.abs(e_ph)**2)*seno)*dth*dph)

    K = cA['Prad']/integral(cA['E_theta'], cA['E_phi'])                 # potencia radiada por unidad de integral de |E|²
    S = np.array([[sA['Saa'][i0], sB['Spa'][i0]], [sA['Spa'][i0], sB['Saa'][i0]]])      # [[S11, S12], [S21, S22]]
    p_inc = float(sA['P_inc'][i0])
    mejor = None
    for psi in (math.pi/2, -math.pi/2):
        a = np.array([1.0, np.exp(1j*psi)])
        b = S @ a
        p_acc = p_inc*(np.sum(np.abs(a)**2) - np.sum(np.abs(b)**2))
        e_th = cA['E_theta'] + np.exp(1j*psi)*cB['E_theta']
        e_ph = cA['E_phi'] + np.exp(1j*psi)*cB['E_phi']
        i_tot = integral(e_th, e_ph)
        p_rad = K*i_tot
        eta = p_rad/p_acc if p_acc > 0 else float('nan')
        d_lin = 4*math.pi*(np.abs(e_th)**2 + np.abs(e_ph)**2)/i_tot
        er = np.abs(e_th + 1j*e_ph)/math.sqrt(2)
        el = np.abs(e_th - 1j*e_ph)/math.sqrt(2)
        d_r, d_l = 4*math.pi*er**2/i_tot, 4*math.pi*el**2/i_tot
        ar = 20*np.log10((er + el)/np.maximum(np.abs(er - el), 1e-9*np.maximum(er, el)))      # suelo relativo: E es muy pequeño
        ihor = int(np.argmax(np.maximum(d_r, d_l)[:, 0]))
        itz = int(np.argmin(np.abs(theta - 0)))
        pol = 'RHCP' if d_r.max() > d_l.max() else 'LHCP'
        dcp = d_r if pol == 'RHCP' else d_l
        it, ip = np.unravel_index(int(np.argmax(dcp)), dcp.shape)
        # semiespacio superior (θ ≤ 90°): lo que ve un receptor GPS
        sup = theta <= 90
        res = {'psi_deg': round(math.degrees(psi)), 'pol': pol, 'eficiencia_%': round(100*eta, 1),
               'directividad_CP_dBi': round(10*math.log10(dcp.max()), 2),
               'ganancia_CP_dBi': round(10*math.log10(max(dcp.max()*eta, 1e-9)), 2),
               'ganancia_CP_cenit_dBi': round(10*math.log10(max(dcp[itz, 0]*eta, 1e-9)), 2),
               'AR_cenit_dB': round(float(ar[itz, 0]), 1),
               'AR_max_theta_dB': round(float(ar[it, ip]), 1), 'theta_max': float(theta[it]),
               'AR_media_theta<60_dB': round(float(np.mean(ar[theta < 60, :])), 1),
               'cruzada_cenit_dB': round(10*math.log10(max(min(d_r[itz, 0], d_l[itz, 0]), 1e-12*max(d_r[itz, 0], d_l[itz, 0], 1e-30))/max(max(d_r[itz, 0], d_l[itz, 0]), 1e-30)), 1)}
        if mejor is None or res['ganancia_CP_cenit_dBi'] > mejor['ganancia_CP_cenit_dBi']:
            mejor = res
    return mejor


def main():
    pos, par_txt, opt, i = [], {}, {}, 0
    args = sys.argv[1:]
    while i < len(args):
        a = args[i]
        if a in ('--solo-lista', '--dibujar'):
            opt[a[2:]] = '1'
        elif a.startswith('--'):
            opt[a[2:]] = args[i + 1]
            i += 1
        elif '=' in a:
            k, v = a.split('=', 1)
            par_txt[k] = [float(x.replace(',', '.')) for x in v.split(',')]
        else:
            pos.append(a)
        i += 1
    for k in par_txt:
        if k not in DEFECTOS:
            sys.exit(f'«{k}» no es un parámetro. Parámetros: {", ".join(DEFECTOS)}')
    f_MHz = float(opt.get('f', '1575.42').replace(',', '.'))
    res = float(opt.get('res', '1.0').replace(',', '.'))
    ks = list(par_txt)
    configs = [dict(DEFECTOS, **dict(zip(ks, comb))) for comb in itertools.product(*[par_txt[k] for k in ks])] if ks else [dict(DEFECTOS)]
    etiqueta = opt.get('etiqueta') or f'QHA_{f_MHz:g}MHz_{datetime.datetime.now():%m%d_%H%M}'
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', etiqueta)
    os.makedirs(carpeta, exist_ok=True)
    print(f'=== {etiqueta}: hélice cuadrifilar a {f_MHz:g} MHz, {len(configs)} configuraciones, malla {res} mm', flush=True)
    for n, p in enumerate(configs):
        try:
            d = dimensiones(f_MHz, p)
        except ValueError as ex:
            print('  ✗', {k: p[k] for k in ks}, ex)
            continue
        print(f'  · {json.dumps({k: p[k] for k in ks})}  brazo {d["arco_mm"]:.1f} mm  altura {d["altura_mm"]:.1f} mm  tira {d["ancho_tira_mm"]:.1f} × {d["altura_mm"]:.1f} mm')
        if 'dibujar' in opt:
            dibujar(f_MHz, p, carpeta, f'tira_{n}')
    if 'solo-lista' in opt or 'dibujar' in opt:
        return
    os.environ.setdefault('ANTENAS_GPU', '1')
    spec = importlib.util.spec_from_file_location('barrido', os.path.join(RAIZ, 'herramientas', 'barrido.py'))
    barrido = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barrido)
    import numpy as np
    ruta_jl = os.path.join(carpeta, 'resultados.jsonl')
    hechos = {}
    if os.path.exists(ruta_jl):
        for linea in open(ruta_jl, encoding='utf-8'):
            try:
                d_ = json.loads(linea)
                hechos[json.dumps(d_['parametros'], sort_keys=True)] = d_
            except ValueError:
                pass
    lock = barrido._bloqueo() if os.environ['ANTENAS_GPU'] != '0' else None
    filas = []
    try:
        for p in configs:
            clave = json.dumps({k: p[k] for k in ks}, sort_keys=True)
            if clave in hechos:
                filas.append(hechos[clave])
                print('  (ya hecha)', clave, flush=True)
                continue
            try:
                d = dimensiones(f_MHz, p)
            except ValueError:
                continue
            t0 = time.time()
            fila = {'parametros': {k: p[k] for k in ks}, 'altura_mm': round(d['altura_mm'], 2), 'arco_mm': round(d['arco_mm'], 2)}
            try:
                h = hashlib.md5(json.dumps([p, f_MHz, res], sort_keys=True).encode()).hexdigest()[:10]
                base = os.path.join(tempfile.gettempdir(), 'antenas_sim', 'qha_' + h)
                sA, cA, i0 = simular_helice(p, f_MHz, res, base + '_A', 1)
                sB, cB, _ = simular_helice(p, f_MHz, res, base + '_B', 2)
                f = sA['f']/1e6
                s11 = 20*np.log10(np.abs(sA['Saa']))
                s22 = 20*np.log10(np.abs(sB['Saa']))
                s21 = 20*np.log10(np.abs(sA['Spa']))
                z = sA['Z']
                x = np.imag(z)
                cruces = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
                fila.update({'Z_f0': [round(float(z[i0].real), 1), round(float(z[i0].imag), 1)],
                             'cruces_X0_MHz': [round(float(f[c])) for c in cruces][:4],
                             'R_en_cruces': [round(float(z[c].real), 1) for c in cruces][:4]})
                fila.update({'S11_f0_dB': round(float(s11[i0]), 1), 'S22_f0_dB': round(float(s22[i0]), 1), 'S21_f0_dB': round(float(s21[i0]), 1),
                             'f_min_S11_MHz': round(float(f[np.argmin(s11)])), 'S11_min_dB': round(float(s11.min()), 1)})
                fila.update(combinar(sA, cA, sB, cB, i0))
                if os.environ.get('ANTENAS_BORRAR_SIM') == '1':
                    import shutil
                    for suf in ('_A', '_B'):
                        shutil.rmtree(base + suf, ignore_errors=True)
            except Exception as ex:
                fila['error'] = f'{type(ex).__name__}: {ex}'
            fila['s'] = round(time.time() - t0)
            filas.append(fila)
            open(ruta_jl, 'a', encoding='utf-8').write(json.dumps(fila, ensure_ascii=False, default=float) + '\n')
            print(' ', json.dumps(fila, ensure_ascii=False, default=float), flush=True)
        json.dump({'f_MHz': f_MHz, 'res': res, 'filas': filas}, open(os.path.join(carpeta, 'resumen.json'), 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False, default=float)
        print('TERMINADO ->', carpeta, flush=True)
    finally:
        if lock and os.path.exists(lock):
            os.remove(lock)


if __name__ == '__main__':
    main()
