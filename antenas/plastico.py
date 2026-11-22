"""Medir la εr y la tanδ de un plástico con el cupón C (anillos resonantes de microstrip con la muestra encima).

Se mide la resonancia de un anillo en vacío y con la muestra apoyada sobre él. La muestra sube la permitividad efectiva de
la línea (εeff) y la frecuencia baja en la proporción (f_vacío/f_cargado)² = εeff_cargado/εeff_vacío; si además tiene pérdidas,
el factor de calidad cae. Aquí se calcula εeff y cuánta energía del campo queda en cada material con un solver cuasiestático 2D (numpy, SOR)
de la sección (microstrip: masa, FR4, rendija de aire opcional, muestra y aire), y se invierte:
  - εr de la muestra: la que da el cociente de εeff medido (se parte de la εr del FR4, que sale del cupón A);
  - tanδ de la muestra: 1/Q_cargado − 1/Q_vacío = Δ(q_FR4)·tanδ_FR4 + q_muestra·tanδ_muestra, con q = fracción de energía.
Hipótesis: modo cuasi-TEM, muestra plana de grosor conocido que cubre el anillo entero y la línea, y la geometría del anillo igual
en vacío y cargado (por eso solo importa el cociente de frecuencias). Es un modelo de la sección, no una simulación 3D:
`cupon/simular_anillo.py R2G4 --muestra εr,tanδ,grosor,lado` simula el anillo con la muestra en openEMS para compararlo.
"""
import math

import numpy as np

from .i18n import tr

# Dominio de la sección (mm): semianchura y altura de la caja; la masa es y = 0
X_CAJA, Y_CAJA = 24.0, 28.0
DX_MIN, DY_MIN = 0.1, 0.08
_CACHE = {}


def _eje(puntos, n_min):
    """Mallado 1D: líneas en `puntos` (ordenados) con un máximo de paso que crece con la distancia a los puntos de interés."""
    pts = sorted(set(round(p, 6) for p in puntos))
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(n_min, int(math.ceil((b - a)/DY_MIN)))
        out += list(np.linspace(a, b, n + 1)[1:])
    return np.array(out)


def _malla_x(w, borde=None):
    # fino cerca del borde de la pista (x = w/2) y estirado hacia la pared; orde = línea extra (el canto de una muestra estrecha)
    a = np.arange(0.0, w/2 + 1e-9, DX_MIN*1.2)
    if abs(a[-1] - w/2) > 1e-9:
        a = np.append(a, w/2)
    paso, x = DX_MIN*1.2, [a[-1]]
    while x[-1] < X_CAJA - 1e-9:
        paso = min(paso*1.12, 1.6)
        x.append(min(x[-1] + paso, X_CAJA))
    xs = np.concatenate([a[:-1], x])
    if borde is not None and w/2 < borde < X_CAJA:
        xs = np.unique(np.round(np.concatenate([xs, np.linspace(borde - 0.4, borde + 0.4, 5), [borde]]), 6))
    return xs


def _malla_y(h, gap, t, cub=None):
    cortes = [0.0, h]
    if gap > 0:
        cortes.append(h + gap)
    cortes.append(h + gap + t if t > 0 else h + gap)
    if cub:                                            # cubierta (pisador): εr, grosor y rendija sobre la muestra
        z0 = cortes[-1] + cub[2]
        cortes += ([z0] if cub[2] > 0 else []) + [z0 + cub[1]]
    base = _eje(cortes, 4)
    y = list(base)
    paso = DY_MIN*2
    while y[-1] < Y_CAJA - 1e-9:
        paso = min(paso*1.12, 1.6)
        y.append(min(y[-1] + paso, Y_CAJA))
    return np.array(sorted(set(np.round(y, 6))))


def _energia(w, h, er_sub, er_m, t, gap, cub=None, ancho=None):
    """Energía total (∝ capacidad) y fracciones de energía {'sustrato', 'muestra'} de la microstrip con la muestra (t > 0) encima.

    cub = (εr, grosor, rendija): una cubierta encima de la muestra (un pisador); su energía va en la fracción 'cubierta'."""
    clave = (round(w, 4), round(h, 4), round(er_sub, 5), round(er_m, 5), round(t, 4), round(gap, 4), tuple(round(v, 4) for v in cub) if cub else None, round(ancho, 4) if ancho else None)
    if clave in _CACHE:
        return _CACHE[clave]
    x, y = _malla_x(w, ancho/2 if ancho else None), _malla_y(h, gap, t, cub)
    nx, ny = len(x), len(y)
    dx, dy = np.diff(x), np.diff(y)
    ycen = (y[:-1] + y[1:])/2
    eps_y = np.ones(ny - 1)
    capa = np.zeros(ny - 1, int)                       # 0 aire, 1 sustrato, 2 muestra
    eps_y[ycen < h] = er_sub
    capa[ycen < h] = 1
    if t > 0:
        m = (ycen > h + gap) & (ycen < h + gap + t)
        eps_y[m] = er_m
        capa[m] = 2
    if cub:
        z0 = h + gap + t + cub[2]
        m = (ycen > z0) & (ycen < z0 + cub[1])
        eps_y[m] = cub[0]
        capa[m] = 3
    E = np.repeat(eps_y[None, :], nx - 1, axis=0)      # ε de cada celda [i, j]
    if ancho:                                          # muestra estrecha (una tira): fuera de su ancho hay aire
        xc = (x[:-1] + x[1:])/2
        fuera = (xc > ancho/2)[:, None] & (capa == 2)[None, :]
        E = np.where(fuera, 1.0, E)
        capa_2d = np.where(fuera, 0, capa[None, :])
    else:
        capa_2d = np.repeat(capa[None, :], nx - 1, axis=0)
    DX, DY = dx[:, None]*np.ones((1, ny - 1)), np.ones((nx - 1, 1))*dy[None, :]

    # conductancias de las aristas (volúmenes finitos sobre los nodos)
    gx = np.zeros((nx - 1, ny))                        # arista (i,j)-(i+1,j)
    gx[:, 1:] += E*DY/2
    gx[:, :-1] += E*DY/2
    gx /= dx[:, None]
    gy = np.zeros((nx, ny - 1))                        # arista (i,j)-(i,j+1)
    gy[1:, :] += E*DX/2
    gy[:-1, :] += E*DX/2
    gy /= dy[None, :]

    fi = np.zeros((nx, ny))
    fija = np.zeros((nx, ny), bool)
    fija[:, 0] = fija[-1, :] = fija[:, -1] = True       # masa, pared lateral y tapa a 0 V
    j_h = int(np.argmin(np.abs(y - h)))
    i_w = int(np.argmin(np.abs(x - w/2)))
    fija[:i_w + 1, j_h] = True
    fi[:i_w + 1, j_h] = 1.0                             # la pista (la mitad: x = 0 es el eje de simetría)
    libre = ~fija

    def suma_vecinos(f):
        s = np.zeros_like(f)
        d = np.zeros_like(f)
        s[1:, :] += gx*f[:-1, :]; d[1:, :] += gx          # vecino izquierdo
        s[:-1, :] += gx*f[1:, :]; d[:-1, :] += gx         # derecho
        s[:, 1:] += gy*f[:, :-1]; d[:, 1:] += gy          # abajo
        s[:, :-1] += gy*f[:, 1:]; d[:, :-1] += gy         # arriba
        return s, d

    # el eje de simetría (x = 0) es de Neumann: el nodo no tiene vecino izquierdo y el derecho cuenta doble
    gx0 = gx[0, :].copy()
    par = (np.add.outer(np.arange(nx), np.arange(ny)) % 2 == 0)
    omega = 1.9
    for it in range(8000):
        cambio = 0.0
        for color in (par, ~par):
            s, d = suma_vecinos(fi)
            s[0, :] += gx0*fi[1, :]; d[0, :] += gx0         # espejo en x = 0
            nuevo = np.where(d > 0, s/np.where(d > 0, d, 1), fi)
            m = libre & color
            dif = omega*(nuevo - fi)
            fi = np.where(m, fi + dif, fi)
            cambio = max(cambio, float(np.abs(np.where(m, dif, 0)).max()))
        if cambio < 1e-6:
            break

    # energía por celda con el gradiente medio de sus cuatro nodos
    ex = ((fi[1:, :-1] - fi[:-1, :-1]) + (fi[1:, 1:] - fi[:-1, 1:]))/(2*DX)
    ey = ((fi[:-1, 1:] - fi[:-1, :-1]) + (fi[1:, 1:] - fi[1:, :-1]))/(2*DY)
    energia = E*(ex**2 + ey**2)*DX*DY
    total = float(energia.sum())
    fr = {'sustrato': float(energia[capa_2d == 1].sum())/total, 'muestra': float(energia[capa_2d == 2].sum())/total}
    if cub:
        fr['cubierta'] = float(energia[capa_2d == 3].sum())/total
    _CACHE[clave] = (total, fr)
    return _CACHE[clave]


def eps_eff(w, h, er_sub, er_m=1.0, t=0.0, gap=0.0, cub=None, ancho=None):
    """(εeff, {'sustrato': fracción de energía, 'muestra': fracción}) de la microstrip de ancho w sobre un sustrato de grosor h y εr,
    con una muestra de εr y grosor t sobre ella, separada por una rendija de aire de `gap` mm (todo en mm)."""
    w, h, er_sub, er_m, t, gap = float(w), float(h), float(er_sub), float(er_m), float(t), float(gap)
    total, fr = _energia(w, h, er_sub, er_m, t, gap, cub, ancho)
    aire = (1.0, cub[1], cub[2]) if cub else None              # la referencia es todo aire, la cubierta también
    return total/_energia(w, h, 1.0, 1.0, t, gap, aire, ancho)[0], fr


_NODOS = (1.0, 2.0, 3.0, 4.5, 7.0, 11.0, 18.0)       # εr de la muestra en los que se resuelve la sección
ER_MAX = 18.0


def _curva(w, h, er_sub, t, gap, ancho=None):
    """Polinomio de εeff frente a ln(εr de la muestra) ajustado a 7 soluciones de la sección (εeff es suave en εr)."""
    clave = ('curva', round(w, 4), round(h, 4), round(er_sub, 5), round(t, 4), round(gap, 4), round(ancho, 4) if ancho else None)
    if clave not in _CACHE:
        ee = [eps_eff(w, h, er_sub, er, t, gap, None, ancho)[0] for er in _NODOS]
        _CACHE[clave] = np.polyfit(np.log(_NODOS), ee, 5)
    return _CACHE[clave]


# El modelo 2D no ve los huecos de acoplo ni la curvatura del anillo: la muestra desplaza la resonancia algo MÁS de lo que predice (un 8–16 %).
# Δ(f₀/f)² medido en openEMS 3D (`cupon/simular_anillo.py R2G4 --muestra …`, 7 casos con εr 2,2–10 y grosor 2–4 mm, muestra de 30 mm) =
# Δ_modelo·(c0 + c1·t + c2·Δ_modelo); el ajuste deja ≤ 0,002 de residuo en Δ. Solo vale para ese anillo y dentro de ese rango.
CORR_3D = {'R2G4': (1.2047, -0.0317, 0.0398),
           # stubs del cupón C (cupon/simular_stub.py, 3 stubs y 2–3 modos cada uno, 42 casos con εr 2,2–10 y grosor 2–4 mm, muestra de 24 mm): el modelo 2D va
           # mucho mejor que con el anillo (κ ≈ 0,95; error sin corregir −3 % de media, 7 % máx). Cuarto término: modo del stub (0 = λ/4, 1 = 3λ/4, 2 = 5λ/4).
           'STUB': (0.947, 0.0001, 0.0845, -0.017)}
RANGO_CORR = {'er': (2.0, 10.0), 't': (1.5, 4.5)}
TOL_LANZAMIENTO = 0.04
TOL_MODELO_DELTA = 0.002          # residuo del ajuste (en Δ): entra en la incertidumbre de la εr


def er_muestra(f_vacio, f_cargado, w, h, er_sub, t, gap=0.0, anillo=None, ancho=None, modo=1, dk=0.0):
    """εr de la muestra que explica el cociente de frecuencias del anillo (bisección sobre la curva εeff(εr); de 1 a 18). None si no hay solución.

    Con `anillo` calibrado en `CORR_3D` se corrige el desplazamiento con lo simulado en 3D."""
    objetivo = (f_vacio/f_cargado)**2
    e0 = eps_eff(w, h, er_sub, 1.0, 0.0, 0.0, None, ancho)[0]
    coef = _curva(w, h, er_sub, t, gap, ancho)
    cc = tuple(CORR_3D.get(anillo, (1.0, 0.0, 0.0))) + (0.0,)
    c0, c1, c2, c3 = cc[:4]

    def razon(er):
        d = float(np.polyval(coef, math.log(er)))/e0 - 1.0
        return 1.0 + (c0 + dk + c1*t + c2*d + c3*(modo - 1))*d

    lo, hi = 1.0, ER_MAX
    if not razon(lo) <= objetivo <= razon(hi):
        return None
    for _ in range(50):
        med = (lo + hi)/2
        if razon(med) < objetivo:
            lo = med
        else:
            hi = med
    return (lo + hi)/2


def q_sin_carga(q_cargado, il_db):
    """Q propio de un resonador de dos puertos acoplado débil y simétrico: Q_u = Q_L/(1 − |S21|) con |S21| en el pico."""
    return q_cargado/(1 - 10**(il_db/20.0))


def tand_muestra(er_m, q_vacio, q_cargado, w, h, er_sub, t, tand_sub=0.02, gap=0.0):
    """tanδ de la muestra a partir de los Q propios del anillo en vacío y cargado. Puede salir negativa si el ruido manda: ver `medir`."""
    _, f0 = eps_eff(w, h, er_sub)
    _, f1 = eps_eff(w, h, er_sub, er_m, t, gap)
    if f1['muestra'] <= 1e-6:
        return None
    return ((1/q_cargado - 1/q_vacio) - (f1['sustrato'] - f0['sustrato'])*tand_sub)/f1['muestra']


def medir(f_vacio_MHz, f_cargado_MHz, grosor_mm, w_mm=3.0, h_mm=1.6, er_sustrato=4.5, gap_mm=0.0, q_vacio=None, q_cargado=None,
          tand_sustrato=0.02, tol_f_MHz=0.5, tol_grosor_mm=0.1, tol_er_sustrato=0.15, anillo=None, con_incertidumbre=True, ancho=None, modo=1):
    """εr y tanδ de la muestra y su incertidumbre a partir de lo medido con el cupón C.

    f_*: resonancia (pico de S21) del anillo en vacío y con la muestra. q_vacio, q_cargado: factores de calidad propios (opcionales;
    de `q_sin_carga`). gap_mm: rendija de aire estimada entre muestra y pista (una muestra impresa rara vez es plana a décimas).
    La incertidumbre sale de variar a la vez la resolución de frecuencia, el grosor y la εr del FR4 dentro de sus tolerancias y
    quedarse con el peor caso de cada uno por separado, sumados en cuadratura.
    """
    f0, f1, t = f_vacio_MHz*1e6, f_cargado_MHz*1e6, grosor_mm
    er = er_muestra(f0, f1, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo)
    if er is None:
        return {'ok': False, 'motivo': tr('El cociente de frecuencias no tiene solución con ese grosor (¿resonancia mal identificada?).')}
    k_modelo = f1*TOL_MODELO_DELTA/2                       # Δ(f₀/f)² = 0,002 equivale a mover f1 un 0,1 %
    if not con_incertidumbre:                              # más rápido: las variaciones resuelven la sección unas 40 veces
        return {'ok': True, 'er': round(er, 3), 'er_incertidumbre': None, 'calibrado_3d': anillo in CORR_3D,
                'fuera_de_calibracion': anillo in CORR_3D and not (RANGO_CORR['er'][0] <= er <= RANGO_CORR['er'][1] and RANGO_CORR['t'][0] <= t <= RANGO_CORR['t'][1])}
    variaciones = [er_muestra(f0, f1 + tol_f_MHz*1e6, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo),
                   er_muestra(f0, f1 - tol_f_MHz*1e6, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo),
                   er_muestra(f0, f1, w_mm, h_mm, er_sustrato, t + tol_grosor_mm, gap_mm, anillo, ancho, modo),
                   er_muestra(f0, f1, w_mm, h_mm, er_sustrato, max(t - tol_grosor_mm, 0.05), gap_mm, anillo, ancho, modo),
                   er_muestra(f0, f1, w_mm, h_mm, er_sustrato + tol_er_sustrato, t, gap_mm, anillo, ancho, modo),
                   er_muestra(f0, f1, w_mm, h_mm, er_sustrato - tol_er_sustrato, t, gap_mm, anillo, ancho, modo)]
    if anillo in CORR_3D:
        variaciones += [er_muestra(f0, f1 + k_modelo, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo),
                        er_muestra(f0, f1 - k_modelo, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo)]
    if anillo == 'STUB':          # el conector real suma o resta unos mm de línea sin muestra que la simulación 3D no tiene (±2 mm de 47 ≈ ±0,04 en κ)
        variaciones += [er_muestra(f0, f1, w_mm, h_mm, er_sustrato, t, gap_mm, anillo, ancho, modo, dk) for dk in (TOL_LANZAMIENTO, -TOL_LANZAMIENTO)]
    pares = [(variaciones[i], variaciones[i + 1]) for i in range(0, len(variaciones), 2)]
    err = math.sqrt(sum((max(abs((a if a is not None else er) - er), abs((b if b is not None else er) - er)))**2 for a, b in pares))
    out = {'ok': True, 'er': round(er, 3), 'er_incertidumbre': round(err, 3), 'desplazamiento_pct': round(100*(f1/f0 - 1), 2),
           'eps_eff_vacio': round(eps_eff(w_mm, h_mm, er_sustrato)[0], 3),
           'eps_eff_cargado': round(eps_eff(w_mm, h_mm, er_sustrato, er, t, gap_mm, None, ancho)[0], 3),
           'fraccion_energia_muestra': round(eps_eff(w_mm, h_mm, er_sustrato, er, t, gap_mm, None, ancho)[1]['muestra'], 3),
           'calibrado_3d': anillo in CORR_3D}
    if anillo in CORR_3D:
        out['fuera_de_calibracion'] = not (RANGO_CORR['er'][0] <= er <= RANGO_CORR['er'][1] and RANGO_CORR['t'][0] <= t <= RANGO_CORR['t'][1])
    if q_vacio and q_cargado:
        td = tand_muestra(er, q_vacio, q_cargado, w_mm, h_mm, er_sustrato, t, tand_sustrato, gap_mm)
        out['tand'] = None if td is None else round(td, 4)
        # tanδ: una décima de ruido de Q a Q moderados ya mueve el resultado; se avisa si es menor que su incertidumbre
        dq = 0.05
        tds = [tand_muestra(er, q_vacio*(1 + s*dq), q_cargado*(1 - s*dq), w_mm, h_mm, er_sustrato, t, tand_sustrato, gap_mm) for s in (1, -1)]
        tds = [v for v in tds if v is not None]
        if td is not None and tds:
            out['tand_incertidumbre'] = round(max(abs(v - td) for v in tds), 4)
            out['tand_fiable'] = td > out['tand_incertidumbre']
    return out


def parametros_pico(f_Hz, s21_dB, f_centro_Hz=None, ventana=0.15):
    """Resonancia de un anillo a partir de su curva de S21 [dB]: {'f_MHz', 'il_dB', 'ancho_3dB_MHz', 'q_cargado', 'q_propio'}.

    Busca el máximo (cerca de `f_centro_Hz` si se da, dentro de ±`ventana` en proporción), mide el ancho a −3 dB por interpolación
    lineal y saca los Q. Devuelve None si el pico no es claro (menos de 6 dB sobre la mediana o sin cruces de −3 dB)."""
    f, s = np.asarray(f_Hz, float), np.asarray(s21_dB, float)
    sel = np.ones(len(f), bool) if f_centro_Hz is None else np.abs(f/f_centro_Hz - 1) <= ventana
    if sel.sum() < 5:
        return None
    idx = np.where(sel)[0]
    i0 = idx[int(np.argmax(s[idx]))]
    if s[i0] - np.median(s[idx]) < 6.0:
        return None
    umbral = s[i0] - 3.0
    i1 = i0
    while i1 > 0 and s[i1] > umbral:
        i1 -= 1
    i2 = i0
    while i2 < len(f) - 1 and s[i2] > umbral:
        i2 += 1
    if s[i1] > umbral or s[i2] > umbral:
        return None
    fa = f[i1] + (umbral - s[i1])/(s[i1 + 1] - s[i1])*(f[i1 + 1] - f[i1])
    fb = f[i2 - 1] + (umbral - s[i2 - 1])/(s[i2] - s[i2 - 1])*(f[i2] - f[i2 - 1])
    ancho = fb - fa
    q_l = f[i0]/ancho
    return {'f_MHz': round(f[i0]/1e6, 3), 'il_dB': round(float(s[i0]), 2), 'ancho_3dB_MHz': round(ancho/1e6, 3),
            'q_cargado': round(q_l, 1), 'q_propio': round(q_sin_carga(q_l, float(s[i0])), 1)}


# ----------------------------------------------------------------------------- Cupón C: stubs abiertos medidos en S11, y sus muestras
# Tres líneas de 50 Ω (3,01 mm sobre FR4 de 1,6 mm) que acaban en circuito abierto, cada una con un conector SMA de canto en el borde de arriba de la placa. Un stub
# abierto de largo L (del borde de la placa al extremo) resuena (X = 0 con pendiente positiva, R mínima) en L = λg/4, 3λg/4, 5λg/4…: f_n = (2n−1)·c/(4·L·√εeff).
# Se mide en S11 (un solo puerto: un NanoVNA normal, que llega a 900 MHz, mide los modos más bajos; uno de 1,5 o 2,7 GHz, también los armónicos).
# La muestra es una tira de 24 mm de ancho (con ≥ 20 mm el borde casi no cuenta: −0,04 % en εeff) que cubre el stub desde 4 mm del borde hasta 3 mm más allá del
# extremo, con cuatro taladros M3: los tornillos de nailon la centran y la sujetan sin poner nada de plástico sobre el stub (un pisador sube la εr aparente un 9–17 %).
STUBS = {'S43': {'x': 85.0, 'L': 43.0}, 'S59': {'x': 50.0, 'L': 59.0}, 'S86': {'x': 15.0, 'L': 86.0}}
ANCHO_MUESTRA, Y0_MUESTRA, MARGEN_PUNTA, INSET_TALADRO = 24.0, 4.0, 3.0, 3.0
D_PASO_M3 = 3.4                                  # taladro de la muestra para un tornillo M3 (el de la placa es de 3,2)
# Resonancias medidas en la simulación 3D del cupón (`cupon/simular_stub.py`, εr 4,5): se rellenan en REF_STUBS al calibrar


def muestra_de(stub):
    """Recuadro de la muestra de un stub en la placa: {'origen': (x, y) de la esquina de menor x e y, 'ancho', 'largo'} (mm; y hacia abajo desde el borde)."""
    s = STUBS[stub]
    y1 = s['L'] + MARGEN_PUNTA
    return {'origen': (s['x'] - ANCHO_MUESTRA/2, Y0_MUESTRA), 'ancho': ANCHO_MUESTRA, 'largo': y1 - Y0_MUESTRA}


def agujeros(stub):
    """Posiciones (x, y) en la placa de los cuatro taladros de la muestra de un stub."""
    m = muestra_de(stub)
    x0, y0 = m['origen']
    a = INSET_TALADRO
    return [(x0 + a, y0 + a), (x0 + m['ancho'] - a, y0 + a), (x0 + a, y0 + m['largo'] - a), (x0 + m['ancho'] - a, y0 + m['largo'] - a)]


def muestras_stl(carpeta, grosores=(2.0, 3.0, 4.0), nombre_material='plastico'):
    """STL de las muestras de ensayo del cupón C: una tira de 24 mm de ancho y el largo de cada stub, con cuatro taladros de M3, para cada grosor.
    Devuelve {'archivos': [rutas], 'lista': [(archivo, texto)]}.

    Se sujetan con tornillos y tuercas de nailon M3 (la cabeza debajo de la placa, la tuerca encima con una arandela de nailon): nada de metal ni de
    pisador sobre el stub. Imprímelas planas (la cara de abajo sobre la cama), con el MISMO material, relleno y orientación que tu carcasa: lo que
    mides es el plástico impreso, no el filamento.
    """
    import os
    from shapely.geometry import Point, box
    from . import carcasa
    os.makedirs(carpeta, exist_ok=True)
    out, lista = [], []
    for t in grosores:
        for etq in STUBS:
            m = muestra_de(etq)
            pos = [(x - m['origen'][0], y - m['origen'][1]) for x, y in agujeros(etq)]
            prismas = [(0.0, float(t), box(0, 0, m['ancho'], m['largo']), '+')]
            prismas += [(-0.01, float(t) + 0.01, Point(x, y).buffer(D_PASO_M3/2, quad_segs=16), '-') for x, y in pos]
            ruta = os.path.join(carpeta, f'muestra_{etq}_{t:g}mm.stl')
            carcasa.escribir_stl(ruta, carcasa.malla(prismas), nombre_material)
            out.append(ruta)
            lista.append((os.path.basename(ruta), tr('Muestra de {0:g} × {1:g} × {2:g} mm para el stub {3}, con 4 taladros M3', m['ancho'], m['largo'], t, etq)))
    return {'archivos': out, 'lista': lista}

# ----------------------------------------------------------------------------- εr del FR4 del propio cupón (anillo en vacío)
# Resonancia simulada en openEMS 3D del anillo (`cupon/simular_anillo.py`, εr 4,5): la geometría del anillo (curvatura, huecos de
# acoplo) se queda en esta constante y solo cambia εeff, que sí calcula el solver 2D.
REF_ANILLOS = {'R2G4': {'f_MHz': 2397.1, 'er': 4.5, 'w_mm': 3.01, 'h_mm': 1.6, 'r_mm': 10.036}}
_NODOS_SUSTRATO = (2.5, 3.5, 4.5, 5.5, 7.0)


def er_fr4(f_MHz, anillo='R2G4', tol_f_MHz=0.5, tol_ancho_mm=0.05, tol_radio_mm=0.05):
    """εr del FR4 de un cupón a partir de la resonancia de un anillo medida SIN muestra: {'ok', 'er', 'er_incertidumbre'}.

    La frecuencia escala con 1/√εeff respecto a la simulación 3D de referencia (εr 4,5); el solver 2D da la εr que explica el εeff.
    La incertidumbre suma la resolución de frecuencia, el ancho de pista y el radio reales (el grabado los cambia ±0,05 mm)."""
    ref = REF_ANILLOS.get(anillo)
    if ref is None:
        return {'ok': False, 'motivo': tr('No hay referencia simulada para este anillo (de momento solo R2G4).')}
    w, h = ref['w_mm'], ref['h_mm']

    def resolver(f, w_):
        e_ref = eps_eff(w, h, ref['er'])[0]        # la referencia 3D es del ancho nominal
        objetivo = e_ref*(ref['f_MHz']/f)**2
        ee = [eps_eff(w_, h, er)[0] for er in _NODOS_SUSTRATO]
        coef = np.polyfit(_NODOS_SUSTRATO, ee, 3)
        lo, hi = _NODOS_SUSTRATO[0], _NODOS_SUSTRATO[-1]
        if not np.polyval(coef, lo) <= objetivo <= np.polyval(coef, hi):
            return None
        for _ in range(50):
            med = (lo + hi)/2
            lo, hi = (med, hi) if np.polyval(coef, med) < objetivo else (lo, med)
        return (lo + hi)/2

    er = resolver(f_MHz, w)
    if er is None:
        return {'ok': False, 'motivo': tr('La frecuencia queda fuera de lo esperable para un FR4 (εr de 2,5 a 7): ¿pico equivocado?')}
    var = ([resolver(f_MHz + s*tol_f_MHz, w) for s in (1, -1)] + [resolver(f_MHz, w + s*tol_ancho_mm) for s in (1, -1)]
           + [resolver(f_MHz*(1 + s*tol_radio_mm/ref['r_mm']), w) for s in (1, -1)])
    pares = [(var[0], var[1]), (var[2], var[3]), (var[4], var[5])]
    err = math.sqrt(sum(max(abs((a if a is not None else er) - er), abs((b if b is not None else er) - er))**2 for a, b in pares))
    return {'ok': True, 'er': round(er, 3), 'er_incertidumbre': round(err, 3), 'f_ref_MHz': ref['f_MHz'], 'er_ref': ref['er']}


def leer_s21(texto):
    """Curva de S21 en dB de un `.s2p` (Touchstone de 2 puertos, RI/MA/DB, Hz/kHz/MHz/GHz) o de un CSV de dos columnas «frecuencia, dB»
    (frecuencia en Hz, o en MHz/GHz si es pequeña). Devuelve (f_Hz, s21_dB)."""
    escala, formato = None, 'MA'
    f, s = [], []
    for linea in texto.splitlines():
        linea = linea.split('!')[0].strip()
        if not linea:
            continue
        if linea.startswith('#'):
            t = linea[1:].upper().split()
            escala = {'HZ': 1, 'KHZ': 1e3, 'MHZ': 1e6, 'GHZ': 1e9}.get(t[0], 1e9) if t else 1e9
            for fm in ('RI', 'MA', 'DB'):
                if fm in t:
                    formato = fm
            continue
        partes = linea.replace(';', ',').replace(',', ' ').split()
        try:
            v = [float(x) for x in partes]
        except ValueError:
            continue                                  # cabecera de un CSV
        if len(v) >= 9:                               # .s2p: f, S11, S21, S12, S22 (cada uno en dos columnas)
            a, b = v[3], v[4]
            if formato == 'RI':
                mag = math.hypot(a, b)
            elif formato == 'DB':
                mag = 10**(a/20)
            else:
                mag = a
            f.append(v[0]*(escala or 1e9))
            s.append(20*math.log10(max(mag, 1e-12)))
        elif len(v) >= 2:
            f.append(v[0]*(escala or 1))
            s.append(v[1])
    f, s = np.array(f), np.array(s)
    if len(f) and escala is None:                     # CSV sin cabecera Touchstone: la frecuencia puede venir en MHz o GHz
        f = f*(1e9 if f.max() < 100 else (1e6 if f.max() < 1e5 else 1))
    return f, s


# ----------------------------------------------------------------------------- análisis de un stub abierto medido en S11
C0_MM_S = 299792458.0
ALFA_C_1GHZ = 0.06          # Np/m: pérdida del cobre de la línea de 3 mm (1 oz, rugosidad incluida) a 1 GHz; ∝ √f. Con PEC (simulación 3D) es 0.
Z0 = 50.0


def resonancias_stub(f_Hz, s11, n_ajuste=3):
    """Resonancias serie de un stub abierto en una curva de S11 (complejo, referida a 50 Ω): cruces de X por cero con pendiente positiva.

    Devuelve [{'f_MHz', 'R_ohm', 'dXdf_ohm_MHz'}] de menor a mayor frecuencia. R es la resistencia en la resonancia (Z0·αL: da la pérdida de la línea) y dX/df, su selectividad.
    Cerca de |Γ| = 1 un error pequeño de S11 mueve mucho X (≈ 26 Ω por unidad de Γ), así que el cruce no se toma entre dos puntos sino de una **recta ajustada por
    mínimos cuadrados** a X(f) en ±`n_ajuste` puntos (y R con otra recta evaluada en el cruce): con ruido σ = 0,005 en S11 baja el error de la frecuencia unas 2–3 veces."""
    f = np.asarray(f_Hz, float)
    s = np.asarray(s11, complex)
    z = Z0*(1 + s)/(1 - s)
    x, r = z.imag, z.real
    out = []
    for i in range(len(f) - 1):
        if x[i] < 0 <= x[i + 1] and np.isfinite(x[i]) and np.isfinite(x[i + 1]):
            lo, hi = max(i - n_ajuste + 1, 0), min(i + 1 + n_ajuste, len(f) - 1)
            fs, xs, rs = f[lo:hi + 1], x[lo:hi + 1], r[lo:hi + 1]
            if len(fs) >= 3 and np.all(np.isfinite(xs)):
                ax, bx = np.polyfit(fs - f[i], xs, 1)                # X ≈ ax·(f − f_i) + bx
                if ax > 0:
                    fr_ = f[i] - bx/ax
                    ar, br = np.polyfit(fs - f[i], rs, 1)
                    out.append({'f_MHz': round(float(fr_)/1e6, 4), 'R_ohm': round(float(ar*(fr_ - f[i]) + br), 3), 'dXdf_ohm_MHz': round(float(ax*1e6), 4)})
                    continue
            u = -x[i]/(x[i + 1] - x[i])
            out.append({'f_MHz': round(float(f[i] + u*(f[i + 1] - f[i]))/1e6, 4), 'R_ohm': round(float(r[i] + u*(r[i + 1] - r[i])), 3),
                        'dXdf_ohm_MHz': round(float((x[i + 1] - x[i])/(f[i + 1] - f[i])*1e6), 4)})
    return out

def elegir_resonancia(resonancias, f_esperada_MHz, ventana=0.25):
    """La resonancia más cercana a la esperada (dentro de ±`ventana` en proporción), o None."""
    c = [r for r in resonancias if abs(r['f_MHz']/f_esperada_MHz - 1) <= ventana]
    return min(c, key=lambda r: abs(r['f_MHz'] - f_esperada_MHz)) if c else None


def tand_stub(er_m, f0_MHz, r0, f1_MHz, r1, w, h, er_sub, t, modo=1, tand_sub=0.02, gap=0.0, ancho=ANCHO_MUESTRA, alfa_c_1ghz=ALFA_C_1GHZ):
    """tanδ de la muestra a partir de la resistencia (Ω) del stub en su resonancia, en vacío (r0 a f0) y con la muestra (r1 a f1).

    En la resonancia serie Z_in = Z0·tanh(αL) ≈ Z0·αL: αL = R/Z0 (el offset de contacto del conector se resta al restar las dos medidas). La pérdida del dieléctrico es
    α_d = (π·f·√εeff/c)·Σ q_i·tanδ_i (q = fracción de energía de cada material, del solver 2D) y la del cobre se toma ∝ √f."""
    e0, fr0 = eps_eff(w, h, er_sub)
    e1, fr1 = eps_eff(w, h, er_sub, er_m, t, gap, None, ancho)
    if fr1['muestra'] <= 1e-6:
        return None
    f0, f1 = f0_MHz*1e6, f1_MHz*1e6
    largo_e = (2*modo - 1)*C0_MM_S/(4*f0*math.sqrt(e0))                  # m: largo eléctrico de la línea (de f0, que se mide con precisión)
    ac0 = alfa_c_1ghz*math.sqrt(f0/1e9)
    ad0 = math.pi*f0*math.sqrt(e0)/C0_MM_S*fr0['sustrato']*tand_sub
    ad1 = ad0 + (r1 - r0)/(Z0*largo_e) - ac0*(math.sqrt(f1/f0) - 1)
    return (ad1/(math.pi*f1*math.sqrt(e1)/C0_MM_S) - fr1['sustrato']*tand_sub)/fr1['muestra']


def medir_stub(f_vacio_MHz, f_cargado_MHz, grosor_mm, r_vacio=None, r_cargado=None, modo=1, w_mm=3.01, h_mm=1.6, er_sustrato=4.5, gap_mm=0.0,
               tand_sustrato=0.02, tol_f_MHz=1.0, tol_grosor_mm=0.1, tol_er_sustrato=0.15, tol_r_ohm=0.25, con_incertidumbre=True, alfa_c_1ghz=ALFA_C_1GHZ):
    """εr y tanδ de una muestra a partir de un stub del cupón C medido en S11: frecuencia y resistencia de su resonancia (modo 1, 3, 5…) sin muestra y con ella.

    Es `medir` con la muestra estrecha (24 mm) y la corrección 3D del stub; la tanδ sale de la resistencia en la resonancia. La incertidumbre de la tanδ
    suma la de R (tol_r_ohm, un NanoVNA calibrado cerca de |Γ| = 1 da ±0,2–0,3 Ω). 	ol_f_MHz = 1 MHz sale de un Monte Carlo sobre las curvas 3D con ruido de S11 de 0,005 y un error de
    calibración de 0,01 (ver docs/desarrollo/plasticos.md): vale si las dos medidas se hacen SIN recalibrar ni mover el cable; si se recalibra entre medio, el error de la frecuencia es unas 3 veces mayor."""
    r = medir(f_vacio_MHz, f_cargado_MHz, grosor_mm, w_mm, h_mm, er_sustrato, gap_mm, None, None, tand_sustrato, tol_f_MHz, tol_grosor_mm,
              tol_er_sustrato, 'STUB', con_incertidumbre, ANCHO_MUESTRA, modo)
    if not r.get('ok'):
        return r
    r['modo'] = modo
    if r_vacio is not None and r_cargado is not None:
        td = tand_stub(r['er'], f_vacio_MHz, r_vacio, f_cargado_MHz, r_cargado, w_mm, h_mm, er_sustrato, grosor_mm, modo, tand_sustrato, gap_mm, ANCHO_MUESTRA, alfa_c_1ghz)
        r['tand'] = None if td is None else round(td, 4)
        if td is not None:
            ts = [tand_stub(r['er'], f_vacio_MHz, r_vacio + s*tol_r_ohm, f_cargado_MHz, r_cargado - s*tol_r_ohm, w_mm, h_mm, er_sustrato, grosor_mm, modo,
                            tand_sustrato, gap_mm, ANCHO_MUESTRA, alfa_c_1ghz) for s in (1, -1)]
            r['tand_incertidumbre'] = round(max(abs(v - td) for v in ts if v is not None), 4)
            r['tand_fiable'] = td > r['tand_incertidumbre']
    return r


# Resonancias de cada stub en la simulación 3D con εr 4,5 (`cupon/simular_stub.py`, sin conector): modo 1 = λ/4, 2 = 3λ/4, 3 = 5λ/4. Ver `er_fr4_stubs`.
REF_STUBS = {'S43': [869.678, 2624.945], 'S59': [646.167, 1942.56], 'S86': [450.3, 1353.565, 2253.05]}


def er_fr4_stubs(frecuencias_MHz, modo=1, w_mm=3.01, h_mm=1.6, tol_f_MHz=1.0, tol_largo_mm=0.1, largos=None):
    """εr del FR4 del cupón a partir de la resonancia de modo `modo` de VARIOS stubs: frecuencias_MHz = {'S43': f, 'S59': f, …} (al menos dos).

    Para cada stub, (2·modo−1)·c/(4·f) = √εeff·(L + ℓ), con L el largo de la placa y ℓ la longitud eléctrica del lanzamiento (el conector y su pad), que
    no se conoce: ajustando una recta de c/(4f)·(2·modo−1) frente a L, la pendiente es √εeff (ℓ sale de la ordenada, y se comprueba que es de unos mm).
    Con la εeff, el solver 2D da la εr. Devuelve {'ok', 'er', 'er_incertidumbre', 'lanzamiento_mm'}."""
    largos = largos or {k: s['L'] for k, s in STUBS.items()}          # largos = {nombre: mm}: p. ej. los S80 y S30 del cupón B (85,7 y 35,7 mm desde el borde)
    pts = [(largos[k], f) for k, f in frecuencias_MHz.items() if k in largos and f]
    if len(pts) < 2:
        return {'ok': False, 'motivo': tr('Hacen falta las resonancias de al menos dos stubs distintos.')}

    def ajustar(delta_f=None, delta_L=0.0):
        L = np.array([p_[0] + (delta_L if i == 0 else 0.0) for i, p_ in enumerate(pts)])
        y = np.array([(2*modo - 1)*C0_MM_S/(4*(p_[1] + (delta_f if (delta_f is not None and i == 0) else 0.0))*1e6)*1e3 for i, p_ in enumerate(pts)])   # mm
        a, b = np.polyfit(L, y, 1)
        return a, b
    a, b = ajustar()
    ee = a*a                                     # εeff = pendiente²
    # εr del FR4 que da ese εeff con el solver (curva de 5 puntos)
    nodos = (2.5, 3.5, 4.5, 5.5, 7.0)
    c = np.polyfit(nodos, [eps_eff(w_mm, h_mm, er)[0] for er in nodos], 3)
    def a_er(e):
        if not np.polyval(c, nodos[0]) <= e <= np.polyval(c, nodos[-1]):
            return None
        lo, hi = nodos[0], nodos[-1]
        for _ in range(50):
            med = (lo + hi)/2
            lo, hi = (med, hi) if np.polyval(c, med) < e else (lo, med)
        return (lo + hi)/2
    er = a_er(ee)
    if er is None:
        return {'ok': False, 'motivo': tr('La frecuencia queda fuera de lo esperable para un FR4 (εr de 2,5 a 7): ¿pico equivocado?')}
    variaciones = []
    for df in (tol_f_MHz, -tol_f_MHz):
        variaciones.append(a_er(ajustar(df)[0]**2))
    for dl in (tol_largo_mm, -tol_largo_mm):
        variaciones.append(a_er(ajustar(None, dl)[0]**2))
    err = math.sqrt(sum(max(abs((u if u is not None else er) - er), abs((v if v is not None else er) - er))**2
                        for u, v in ((variaciones[0], variaciones[1]), (variaciones[2], variaciones[3]))))
    return {'ok': True, 'er': round(er, 3), 'er_incertidumbre': round(err, 3), 'lanzamiento_mm': round(b/a, 2), 'eps_eff': round(ee, 3)}
