"""Informe PDF (castellano e inglés) de las medidas del 22-11-2026: cupones A y B y dos antenas de 2,4 GHz.

Uso: python herramientas/informe_medidas_22_11.py [salida.pdf]
Lee los .s1p/.s2p crudos de vna/medidas/ y dibuja las gráficas; las cifras de las tablas son las de
docs/desarrollo/medidas/resultados_stubs_cupon_B.md (se calcularon con los mismos datos).
"""
import sys
import textwrap
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

RAIZ = Path(__file__).resolve().parents[1]
MED = RAIZ / 'vna' / 'medidas'
SALIDA = RAIZ / 'docs' / 'desarrollo' / 'medidas' / 'informe_medidas_22-11-2026.pdf'
C0 = 299792458.0
A4 = (8.27, 11.69)
AZUL, ROJO, VERDE, NARANJA, GRIS = '#1f4e9c', '#c0392b', '#2e8b57', '#d98324', '#777777'
plt.rcParams.update({'font.size': 8, 'axes.grid': True, 'grid.alpha': 0.3, 'font.family': 'DejaVu Sans'})


def s1p(n):
    a = np.array([l.split() for l in open(MED / f'{n}.s1p', encoding='utf-8') if l.strip() and l[0] not in '!#'], float)
    return a[:, 0]/1e6, a[:, 1] + 1j*a[:, 2]


def s2p(n):
    a = np.array([l.split() for l in open(MED / f'{n}.s2p', encoding='utf-8') if l.strip() and l[0] not in '!#'], float)
    return a[:, 0]/1e6, a[:, 1] + 1j*a[:, 2], a[:, 3] + 1j*a[:, 4]


def db(s):
    return 20*np.log10(np.maximum(np.abs(s), 1e-9))


def sin_artefacto(f, y):
    y = np.array(y, float)
    y[(f > 2090) & (f < 2125)] = np.nan
    return y


# ---------- utilidades de página ----------
def pagina(L, titulo, n):
    fig = plt.figure(figsize=A4)
    fig.text(0.07, 0.955, titulo, fontsize=14, weight='bold', color=AZUL)
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.945, 0.945], color=AZUL, lw=1))
    fig.text(0.93, 0.02, f'{n}', ha='right', fontsize=8, color=GRIS)
    fig.text(0.07, 0.02, ('Chirptenna · medidas 22-11-2026', 'Chirptenna · measurements 22-11-2026')[L], fontsize=8, color=GRIS)
    return fig


def bloque(fig, y, texto, size=9, ancho=92, paso=0.0155, x=0.07, color='black', negrita=False):
    for par in texto.split('\n'):
        if not par.strip():
            y -= paso*0.6
            continue
        ind = '   ' if par.startswith('• ') else ''
        for linea in textwrap.wrap(par, ancho, subsequent_indent=ind) or ['']:
            fig.text(x, y, linea, fontsize=size, va='top', color=color, weight='bold' if negrita else 'normal')
            y -= paso
    return y


def tabla(fig, rect, filas, anchos, size=7.5, cab=1):
    ax = fig.add_axes(rect)
    ax.axis('off')
    t = ax.table(cellText=filas, colWidths=anchos, loc='upper center', cellLoc='left')
    t.auto_set_font_size(False)
    t.set_fontsize(size)
    t.scale(1, 1.35)
    for (i, j), c in t.get_celld().items():
        c.set_edgecolor('#cccccc')
        if i < cab:
            c.set_facecolor('#dfe7f4')
            c.set_text_props(weight='bold')
    return t


def ejes(fig, rect):
    return fig.add_axes(rect)


# ---------- figuras ----------
def fig_stubs(fig, rect, L):
    ax = ejes(fig, rect)
    for k, c in zip((1, 2, 3), (AZUL, VERDE, NARANJA)):
        f, s = s1p(f'cuponB_u1_S80_r{k}')
        z = 50*(1 + s)/(1 - s)
        ax.plot(f, np.clip(z.imag, -200, 200), c=c, lw=0.9, label=f'S80 r{k}')
    f, s = s1p('cuponB_u1_S30_r1')
    z = 50*(1 + s)/(1 - s)
    ax.plot(f, np.clip(z.imag, -200, 200), c=ROJO, lw=0.9, label='S30 r1')
    for fm, nombre in [(454.0, 'S80 n=1'), (1378.0, 'n=2'), (2287.0, 'n=3'), (1095.8, 'S30')]:
        ax.axvline(fm, color=GRIS, ls=':', lw=0.8)
    for fs in (451.9, 1358.7, 2261.7, 1034.0):
        ax.axvline(fs, color=ROJO, ls='--', lw=0.6, alpha=0.6)
    ax.axhline(0, color='black', lw=0.6)
    ax.set_xlim(300, 2500)
    ax.set_ylim(-200, 200)
    ax.set_xlabel('MHz')
    ax.set_ylabel(('Reactancia X (Ω)', 'Reactance X (Ω)')[L])
    ax.set_title(('Stubs abiertos del cupón B: X(f). Punteado gris = medido; rayas rojas = simulación 3D (εr 4,5)',
                  'Cupon B open stubs: X(f). Grey dotted = measured; red dashes = 3D simulation (εr 4.5)')[L], fontsize=8)
    ax.legend(fontsize=7, ncol=4, loc='upper left')


def fig_anillos(fig, rect, L):
    ax = ejes(fig, rect)
    for n, lo, hi, c, et in [('cuponA_R868', 300, 2700, AZUL, 'R868'), ('cuponA_R2G4', 1400, 2800, VERDE, 'R2G4'),
                              ('cuponB_R5G8', 1400, 2800, NARANJA, 'R5G8')]:
        f, _, s21 = s2p(f'{n}_r1')
        m = (f >= lo) & (f <= min(hi, 2700))
        ax.plot(f[m], sin_artefacto(f[m], db(s21[m])), c=c, lw=0.9, label=et)
    for fs, c in [(890.6, AZUL), (2397.1, VERDE), (1937.6, NARANJA)]:
        ax.axvline(fs, color=c, ls='--', lw=0.7, alpha=0.7)
    ax.set_ylim(-60, 0)
    ax.set_xlim(300, 2700)
    ax.set_xlabel('MHz')
    ax.set_ylabel('|S21| (dB)')
    ax.set_title(('Anillos: |S21| medido (línea) y pico simulado 3D (rayas). Se omite el artefacto del THRU 2095–2125 MHz',
                  'Rings: measured |S21| (solid) and 3D simulated peak (dashed). THRU artefact 2095–2125 MHz omitted')[L], fontsize=8)
    ax.legend(fontsize=7, loc='lower right')


def fig_lineas(fig, rect1, rect2, L):
    f, _, a17 = s2p('cuponB_L17_r1')
    _, _, a64 = s2p('cuponB_L64_r1')
    m = (f > 50) & (f < 1000)
    ph = np.unwrap(np.angle(a64[m]/a17[m]))
    k = np.polyfit(f[m]*1e6, ph, 1)
    tau = -k[0]/(2*np.pi)
    ax = ejes(fig, rect1)
    ax.plot(f[m], np.degrees(ph), c=AZUL, lw=1, label=('fase S21(L64)/S21(L17)', 'phase S21(L64)/S21(L17)')[L])
    ax.plot(f[m], np.degrees(np.polyval(k, f[m]*1e6)), c=ROJO, ls='--', lw=1,
            label=('ajuste: %.3f ns, εeff %.2f' if L == 0 else 'fit: %.3f ns, εeff %.2f') % (tau*1e9, (tau*C0/0.047)**2))
    ax.set_xlabel('MHz')
    ax.set_ylabel(('grados', 'degrees')[L])
    ax.set_title(('L64 − L17 (Δl = 47 mm)', 'L64 − L17 (Δl = 47 mm)')[L], fontsize=8)
    ax.legend(fontsize=7)
    ax = ejes(fig, rect2)
    for n, c in [('cuponB_L17_r1', VERDE), ('cuponB_L64_r1', ROJO)]:
        f, s11, s21 = s2p(n)
        m = f < 1800
        ax.plot(f[m], sin_artefacto(f[m], db(s21[m])), c=c, lw=0.9, label=n.split('_')[1] + ' |S21|')
        ax.plot(f[m], db(s11[m]), c=c, lw=0.9, ls=':', label=n.split('_')[1] + ' |S11|')
    ax.set_ylim(-30, 3)
    ax.set_xlabel('MHz')
    ax.set_ylabel('dB')
    ax.set_title(('Módulo de S21 y S11', 'S21 and S11 magnitude')[L], fontsize=8)
    ax.legend(fontsize=7, ncol=2)


def fig_ms_cpwg(fig, rect1, rect2, L):
    ax = ejes(fig, rect1)
    for k, c in zip((1, 2, 3), (AZUL, VERDE, NARANJA)):
        f, s11, s21 = s2p(f'cuponB_MS100_r{k}')
        m = f < 2090
        ax.plot(f[m], db(s11[m]), c=c, lw=0.8, label=f'|S11| r{k}')
        ax.plot(f[m], db(s21[m]), c=c, lw=0.8, ls=':')
    for fm in (896, 1798):
        ax.axvline(fm, color=ROJO, ls='--', lw=0.7)
    ax.set_ylim(-40, 2)
    ax.set_xlabel('MHz')
    ax.set_ylabel('dB')
    ax.set_title(('MS100 (100 Ω): |S11| continuo, |S21| punteado; mínimos de |S11| en 896 y 1798 MHz',
                  'MS100 (100 Ω): |S11| solid, |S21| dotted; |S11| minima at 896 and 1798 MHz')[L], fontsize=8)
    ax.legend(fontsize=7, ncol=3)
    ax = ejes(fig, rect2)
    for k, c in zip((1, 2, 3), (AZUL, VERDE, NARANJA)):
        f, s11, s21 = s2p(f'cuponB_CPWG_r{k}')
        m = f < 1800
        ax.plot(f[m], db(s11[m]), c=c, lw=0.8, label=f'|S11| r{k}')
        ax.plot(f[m], sin_artefacto(f[m], db(s21[m])), c=c, lw=0.8, ls=':')
    ax.set_ylim(-40, 2)
    ax.set_xlabel('MHz')
    ax.set_ylabel('dB')
    ax.set_title(('CPWG50: |S11| continuo, |S21| punteado', 'CPWG50: |S11| solid, |S21| dotted')[L], fontsize=8)
    ax.legend(fontsize=7, ncol=3)


def fig_antenas(fig, rect1, rect2, L):
    for rect, nom, tit, fsim in [(rect1, 'yagi_recta_2dir_2G4', ('Yagi 2,4 GHz, 2 directores', 'Yagi 2.4 GHz, 2 directors')[L], 2445),
                                 (rect2, 'sierpinski_2G4', ('Monopolo de Sierpinski 2,4 GHz', 'Sierpinski monopole 2.4 GHz')[L], 2462)]:
        ax = ejes(fig, rect)
        f, s = s1p(nom + '_cal_completa')
        m = (f >= 2200) & (f <= 2700)
        ax.plot(f[m], db(s[m]), c=AZUL, lw=1.2, label=('calibración amplia (50 kHz–2,7 GHz)', 'wide calibration (50 kHz–2.7 GHz)')[L])
        f2, s2 = s1p(nom + '_cal_usuario')
        ax.plot(f2, db(s2), c=VERDE, lw=1.0, label=('calibración del usuario (2,35–2,5 GHz)', 'user calibration (2.35–2.5 GHz)')[L])
        ax.axhline(-10, color=GRIS, ls='--', lw=0.8)
        ax.axvline(fsim, color=ROJO, ls='--', lw=0.8, label=('mínimo simulado', 'simulated minimum')[L] + f' {fsim} MHz')
        ax.set_xlim(2200, 2700)
        ax.set_ylim(-40, 0)
        ax.set_xlabel('MHz')
        ax.set_ylabel('|S11| (dB)')
        ax.set_title(tit, fontsize=8, pad=6)
        ax.legend(fontsize=7, loc='lower left')


def fig_calibracion(fig, rect, L):
    ax = ejes(fig, rect)
    etapas = [('inicio', 'start'), ('tras stubs', 'after stubs'), ('tras anillos', 'after rings'),
              ('tras líneas', 'after lines'), ('final', 'end')]
    med = [-44.3, -45.5, -39.0, -38.2, -41.6]
    peor = [-29.8, -25.0, -21.6, -22.9, -21.6]
    x = np.arange(5)
    ax.bar(x - 0.18, med, 0.36, color=AZUL, label=('mediana |S11|', 'median |S11|')[L])
    ax.bar(x + 0.18, peor, 0.36, color=NARANJA, label=('peor valor', 'worst value')[L])
    ax.set_xticks(x)
    ax.set_xticklabels([e[L] for e in etapas], fontsize=7)
    ax.set_ylabel('|S11| (dB)')
    ax.set_title(('Verificación con la carga de 50 Ω, calibración «cal_latiguillo_B_22-11»',
                  '50 Ω load check, calibration "cal_latiguillo_B_22-11"')[L], fontsize=8)
    ax.invert_yaxis()
    ax.legend(fontsize=7)


# ---------- contenido ----------
def construir(L):
    t = lambda es, en: (es, en)[L]
    pags = []

    # 1: portada y resumen
    fig = pagina(L, t('Informe de medidas: cupones de εr y antenas de 2,4 GHz', 'Measurement report: εr coupons and 2.4 GHz antennas'), 1)
    y = 0.925
    y = bloque(fig, y, t('22 de noviembre de 2026 · NanoVNA-H (firmware 1.2.42) · una placa de cada cupón (A y B) y dos antenas de la tanda JLC.',
                          '22 November 2026 · NanoVNA-H (firmware 1.2.42) · one board of each coupon (A and B) and two antennas from the JLC batch.'), size=9, color=GRIS)
    y -= 0.01
    y = bloque(fig, y, t('Resumen', 'Summary'), size=12, negrita=True, color=AZUL)
    y = bloque(fig, y, t(
        '• Calibración de PC (OSL + THRU) en el extremo de los latiguillos, verificada con la carga de 50 Ω al empezar y cuatro veces más: |S11| mediana −38…−46 dB, sin pasos bruscos. Sin aislamiento (suelo de |S21| ≈ −50 dB).\n'
        '• Stubs abiertos del cupón B (S80 y S30): resonancias limpias y repetibles (0,03 % en S80), pero la εr del FR4 que sale con dos stubs, 5,03, y el lanzamiento, −0,3 mm, no son creíbles: el método con dos stubs no basta.\n'
        '• Líneas del cupón B: la diferencia de fase L64 − L17 da εeff 3,71 (εr ≈ 4,9). La MS100 y la CPWG coinciden en un FR4 más «lento» que el modelo: la CPWG, un 9–17 % en εeff.\n'
        '• Anillos: R5G8 1967,0 MHz (+1,5 % sobre la simulación), R2G4 2428,4 MHz (+1,3 %) y R868 882,3 MHz (−0,9 %). El R868 sí da un pico limpio con tres modos (n = 1, 2, 3), al contrario de lo que decía la simulación.\n'
        '• Antenas: Yagi 2,4 GHz de 2 directores, mínimo en 2534 MHz con −12,1 dB (+3,6 % sobre la simulación); monopolo de Sierpinski, mínimo en 2502 MHz con −34,3 dB y banda por debajo de −10 dB desde 2274 MHz.\n'
        '• Predicciones registradas antes de medir: 8 cumplen, 10 fallan y 2 no se han podido comprobar (ver la tabla).\n'
        '• εr del FR4, tras revisar las simulaciones (puertos corregidos, ruido de malla): los resonadores (S80, anillos, Sierpinski, MS100) coinciden en εr ≈ 4,2–4,55, cerca del 4,5 nominal; no usar 4,9. Quedan sin explicar la Yagi (su simulación se mueve ±3 % con la malla), S30 (≈ 4,1) y el retardo de la línea de 50 Ω (≈ 4,85). El grosor (±10 %) no es la causa.',
        '• PC calibration (OSL + THRU) at the patch-cable ends, checked with the 50 Ω load at the start and four more times: median |S11| −38…−46 dB, with no jumps. No isolation (|S21| floor ≈ −50 dB).\n'
        '• Cupon B open stubs (S80 and S30): clean, repeatable resonances (0.03 % for S80), but the FR4 εr that two stubs give, 5.03, and the launch length, −0.3 mm, are not credible: two stubs are not enough for the method.\n'
        '• Cupon B lines: the L64 − L17 phase difference gives εeff 3.71 (εr ≈ 4.9). MS100 and CPWG agree on an FR4 that is «slower» than the model: the CPWG εeff is 9–17 % higher.\n'
        '• Rings: R5G8 1967.0 MHz (+1.5 % over simulation), R2G4 2428.4 MHz (+1.3 %) and R868 882.3 MHz (−0.9 %). R868 does show a clean peak with three modes (n = 1, 2, 3), contrary to what the simulation said.\n'
        '• Antennas: 2.4 GHz Yagi with 2 directors, minimum at 2534 MHz with −12.1 dB (+3.6 % over simulation); Sierpinski monopole, minimum at 2502 MHz with −34.3 dB and below −10 dB from 2274 MHz.\n'
        '• Predictions registered before measuring: 8 hold, 10 fail and 2 could not be checked (see the table).\n'
        '• FR4 εr, after reviewing the simulations (corrected ports, mesh noise): the resonators (S80, rings, Sierpinski, MS100) agree on εr ≈ 4.2–4.55, close to the nominal 4.5; do not use 4.9. Unexplained: the Yagi (its simulation moves ±3 % with the mesh), S30 (≈ 4.1) and the 50 Ω line delay (≈ 4.85). Thickness (±10 %) is not the cause.'),
        size=9)
    tabla(fig, [0.07, 0.15, 0.86, 0.32], [
        [t('Resultado clave', 'Key result'), t('Valor medido', 'Measured value')],
        [t('εr del FR4, dos stubs (modo 1)', 'FR4 εr, two stubs (mode 1)'), '5.03 ± 0.05 (' + t('no concluyente', 'inconclusive') + ')' if L else '5,03 ± 0,05 (no concluyente)'],
        [t('εeff microstrip 50 Ω, L64 − L17', '50 Ω microstrip εeff, L64 − L17'), '3.71 ± 0.03 (εr ≈ 4.9)' if L else '3,71 ± 0,03 (εr ≈ 4,9)'],
        [t('Anillo R868 n=1 / R2G4 / R5G8', 'Ring R868 n=1 / R2G4 / R5G8'), '882.3 / 2428.4 / 1967.0 MHz' if L else '882,3 / 2428,4 / 1967,0 MHz'],
        [t('Período del rizado de la MS100', 'MS100 ripple period'), '≈ 898 MHz'],
        [t('Retardo de la CPWG (εeff ≈ 3,4)', 'CPWG delay (εeff ≈ 3.4)'), '0.631 ns' if L else '0,631 ns'],
        [t('Yagi 2,4 GHz, 2 directores', 'Yagi 2.4 GHz, 2 directors'), '2534 MHz, −12.1 dB' if L else '2534 MHz, −12,1 dB'],
        [t('Monopolo de Sierpinski 2,4 GHz', 'Sierpinski monopole 2.4 GHz'), '2502 MHz, −34.3 dB' if L else '2502 MHz, −34,3 dB'],
    ], [0.55, 0.45], size=8.5)
    pags.append(fig)

    # 2: método y calibración
    fig = pagina(L, t('Método y calibración', 'Method and calibration'), 2)
    y = 0.925
    y = bloque(fig, y, t(
        'Se usó la calibración de PC «cal_latiguillo_B_22-11» (OSL + THRU, 50 kHz–2,7 GHz, 1010 puntos de 2,67 MHz, equipo con edelay 0) con dos latiguillos: el plano de medida está en su extremo, así que el conector SMA de la placa y su lanzamiento forman parte del dispositivo. No se hizo de-embedding: solo había una carga de 50 Ω (sin aislamiento) y no hay estándares montados en los SMA de los cupones. Para las antenas se usó además la calibración amplia «completa_50k_2700M» y la calibración del usuario de 2,35–2,5 GHz guardada en el equipo.\n'
        'Reglas seguidas: nunca se envió «save» al equipo; el barrido y el estado se restauran tras cada medida; las medidas de los cupones se hicieron con el usuario delante; datos crudos primero y comparación con predicciones escritas antes de medir; tres reconexiones por estructura.',
        'The PC calibration «cal_latiguillo_B_22-11» (OSL + THRU, 50 kHz–2.7 GHz, 1010 points of 2.67 MHz, device edelay 0) was used with two patch cables: the reference plane is at their ends, so the board SMA connector and its launch are part of the device under test. No de-embedding was done: there was only one 50 Ω load (no isolation) and no standards mounted on the coupon SMAs. For the antennas, the wide calibration «completa_50k_2700M» and the user\'s 2.35–2.5 GHz calibration stored in the device were also used.\n'
        'Rules followed: «save» was never sent to the device; the sweep and state are restored after every measurement; the coupon measurements were made with the user present; raw data first and comparison against predictions written before measuring; three reconnections per structure.'),
        size=9)
    fig_calibracion(fig, [0.10, 0.50, 0.82, 0.22], L)
    y = 0.44
    y = bloque(fig, y, t('Otras verificaciones con la carga de 50 Ω', 'Other 50 Ω load checks'), size=10, negrita=True, color=AZUL)
    tabla(fig, [0.07, 0.22, 0.86, 0.20], [
        [t('Calibración', 'Calibration'), t('Banda', 'Band'), t('Mediana |S11|', 'Median |S11|'), t('Peor valor', 'Worst value')],
        [t('amplia 50 kHz–2,7 GHz', 'wide 50 kHz–2.7 GHz'), t('completa', 'full'), '−51,3 / −49,9 dB'.replace(',', '.') if L else '−51,3 / −49,9 dB', '−32,7 / −31,7 dB'.replace(',', '.') if L else '−32,7 / −31,7 dB'],
        [t('amplia', 'wide'), '2350–2500 MHz', '−43,0 / −41,5 dB'.replace(',', '.') if L else '−43,0 / −41,5 dB', '−36,0 / −35,1 dB'.replace(',', '.') if L else '−36,0 / −35,1 dB'],
        [t('del usuario (slot correcto)', 'user (correct slot)'), '2350–2500 MHz', '−36,2 dB'.replace(',', '.') if L else '−36,2 dB', '−30,7 dB'.replace(',', '.') if L else '−30,7 dB'],
        [t('del usuario (otro estado, «Et»)', 'user (other state, «Et»)'), '2350–2500 MHz', '−8,9 dB'.replace(',', '.') if L else '−8,9 dB', '−0,8 dB'.replace(',', '.') if L else '−0,8 dB'],
    ], [0.34, 0.2, 0.24, 0.22])
    bloque(fig, 0.29, t(
        'La última fila es un estado distinto del equipo (había cambiado el slot activo); no corresponde a las medidas de las antenas, que se hicieron con «load isoln Es Er cal\'ed». Con el estado correcto la carga sale a −36 dB de mediana.',
        'The last row is a different device state (the active slot had changed); it does not correspond to the antenna measurements, which were made with «load isoln Es Er cal\'ed». With the correct state the load gives a median of −36 dB.'),
        size=8, color=GRIS)
    pags.append(fig)

    # 3: stubs
    fig = pagina(L, t('Cupón B: stubs abiertos S80 y S30 (S11)', 'Cupon B: open stubs S80 and S30 (S11)'), 3)
    fig_stubs(fig, [0.09, 0.62, 0.84, 0.28], L)
    y = 0.57
    tabla(fig, [0.07, 0.38, 0.86, 0.18], [
        [t('Stub / modo', 'Stub / mode'), t('Medido (media de 3, MHz)', 'Measured (mean of 3, MHz)'), t('Dispersión', 'Spread'), t('Simulación 3D, εr 4,5', '3D simulation, εr 4.5')],
        ['S80 n=1', '454.00' if L else '454,00', '0.03 %' if L else '0,03 %', '451.9' if L else '451,9'],
        ['S80 n=2', '1377.95' if L else '1377,95', '0.04 %' if L else '0,04 %', '1358.7' if L else '1358,7'],
        ['S80 n=3', '2287.00' if L else '2287,00', '0.04 %' if L else '0,04 %', '2261.7' if L else '2261,7'],
        ['S30 n=1', '1095.79' if L else '1095,79', '0.20 % (0.5 % range)' if L else '0,20 % (rango 0,5 %)', '1034.0' if L else '1034,0'],
    ], [0.2, 0.3, 0.25, 0.25])
    bloque(fig, 0.43, t(
        '• La razón de modos de S80 (f₂/f₁ = 3,035; f₃/f₁ = 5,037) cumple la predicción de 3,00 ± 0,04 y 5,00 ± 0,08, y f₁ está dentro del rango previsto (420–475 MHz).\n'
        '• S80 coincide con la simulación 3D con εr 4,5 (+0,5 %), pero S30 queda un 6 % por encima (1095,8 frente a 1034 MHz). Con los dos stubs en el modo 1, la recta 1/f frente al largo da εr 5,03 ± 0,05 y un lanzamiento de −0,33 mm (se esperaba 4,4 y 2–6 mm). Un lanzamiento negativo refuta la prueba T3.\n'
        '• R en la resonancia: 0,29–0,31 Ω (S80) y 0,38–0,42 Ω (S30). Son del orden del residuo de la calibración (±0,3–0,6 Ω), así que no se concluye nada sobre tanδ.\n'
        '• Con una sola unidad no se pudo comprobar la dispersión entre unidades (P7, T4).',
        '• The S80 mode ratios (f₂/f₁ = 3.035; f₃/f₁ = 5.037) meet the 3.00 ± 0.04 and 5.00 ± 0.08 prediction, and f₁ is inside the expected range (420–475 MHz).\n'
        '• S80 matches the 3D simulation with εr 4.5 (+0.5 %), but S30 is 6 % above it (1095.8 vs 1034 MHz). With both stubs in mode 1, the 1/f-versus-length line gives εr 5.03 ± 0.05 and a launch length of −0.33 mm (4.4 and 2–6 mm were expected). A negative launch length triggers refutation test T3.\n'
        '• R at resonance: 0.29–0.31 Ω (S80) and 0.38–0.42 Ω (S30). That is of the order of the calibration residual (±0.3–0.6 Ω), so nothing is concluded about tanδ.\n'
        '• With a single unit the unit-to-unit spread could not be checked (P7, T4).'),
        size=9)
    pags.append(fig)

    # 4: anillos
    fig = pagina(L, t('Anillos de los cupones A y B (S21)', 'Rings of coupons A and B (S21)'), 4)
    fig_anillos(fig, [0.09, 0.62, 0.84, 0.28], L)
    tabla(fig, [0.07, 0.40, 0.86, 0.19], [
        [t('Anillo', 'Ring'), t('Predicción 3D', '3D prediction'), t('Medido', 'Measured'), t('Desvío', 'Deviation'), 'S21'],
        ['R5G8 n=1 (B)', '1937.6 MHz' if L else '1937,6 MHz', '1967.0 MHz' if L else '1967,0 MHz', '+1.5 %' if L else '+1,5 %', '−13.9 dB' if L else '−13,9 dB'],
        ['R2G4 n=1 (A)', '2397.1 MHz' if L else '2397,1 MHz', '2428.4 MHz' if L else '2428,4 MHz', '+1.3 %' if L else '+1,3 %', '−10.4 / −12.7 / −10.5 dB' if L else '−10,4 / −12,7 / −10,5 dB'],
        ['R868 n=1 (A)', t('890,6 MHz (joroba)', '890.6 MHz (hump)'), '882.3 MHz' if L else '882,3 MHz', '−0.9 %' if L else '−0,9 %', '−21.6 dB' if L else '−21,6 dB'],
        ['R868 n=2', '1740 MHz', '1763.0 MHz' if L else '1763,0 MHz', '+1.3 %' if L else '+1,3 %', '−19.5 dB' if L else '−19,5 dB'],
        ['R868 n=3', '2600 MHz', '2634.1 MHz' if L else '2634,1 MHz', '+1.3 %' if L else '+1,3 %', '−13.3 dB' if L else '−13,3 dB'],
    ], [0.2, 0.22, 0.2, 0.14, 0.24])
    bloque(fig, 0.44, t(
        '• Repetibilidad al reconectar: frecuencia ≤ 0,06 %; nivel ≤ 0,2 dB salvo una medida del R2G4 (−12,7 dB, probablemente un contacto peor).\n'
        '• El R868 muestra los tres modos con cocientes 1,998 y 2,986 respecto a n = 1. La simulación 3D lo daba como una joroba ancha de −30 dB, inservible como sensor; el hardware lo contradice. Falta medir su desplazamiento con una muestra puesta.\n'
        '• Los tres anillos salen entre +1,3 y +1,5 % por encima de la simulación (el R868 n=1, −0,9 %). En el simulador, una εr ≈ 4,3–4,4 los reproduciría; con 4,9 saldrían más bajos (signo contrario). Queda sin resolver.\n'
        '• El pico de +49 dB en torno a 2100 MHz es un artefacto del THRU (mínimo muy profundo al dividir); se ignora esa banda.',
        '• Reconnection repeatability: frequency ≤ 0.06 %; level ≤ 0.2 dB except one R2G4 measurement (−12.7 dB, probably a worse contact).\n'
        '• R868 shows the three modes with ratios 1.998 and 2.986 relative to n = 1. The 3D simulation had it as a wide −30 dB hump, useless as a sensor; the hardware contradicts that. Its shift with a sample on top still has to be measured.\n'
        '• All three rings come out between +1.3 and +1.5 % above the simulation (R868 n=1, −0.9 %). In the simulator an εr ≈ 4.3–4.4 would reproduce them; with 4.9 they would come out lower (opposite sign). Still unresolved.\n'
        '• The +49 dB peak around 2100 MHz is a THRU artefact (a very deep minimum when dividing); that band is ignored.'),
        size=9)
    pags.append(fig)

    # 5: líneas L17/L64
    fig = pagina(L, t('Cupón B: líneas L17 y L64 (dos puertos)', 'Cupon B: L17 and L64 lines (two ports)'), 5)
    fig_lineas(fig, [0.09, 0.62, 0.38, 0.28], [0.57, 0.62, 0.38, 0.28], L)
    bloque(fig, 0.56, t(
        'Método: L64 y L17 llevan el mismo codo y los mismos conectores; solo difieren en 47,0 mm de línea recta. El cociente S21(L64)/S21(L17) elimina el conector y el codo y deja la fase de esa tira. Con las 9 combinaciones de reconexión, entre 50 y 1000 MHz:\n'
        '• Retardo diferencial 0,301 ns y εeff = 3,71 ± 0,03 (3,69 en 300–1000 MHz; 3,97 en 50–600 MHz, ventana poco fiable porque la fase diferencial es pequeña). La predicción era 3,3–3,6: falla por poco, pero queda dentro del criterio de refutación (3,0–3,9).\n'
        '• Con la geometría de diseño de la microstrip de 50 Ω, εeff 3,71 corresponde a εr ≈ 4,9, de acuerdo con los stubs (5,03).\n'
        '• Offset de fase del cociente ≈ −0,013 rad (≈ 0): el conector y el codo se cancelan.\n'
        '• |S21| de L17 hasta 1 GHz ≈ 0 dB (cumple) y de L64 a 2 GHz −1,2 dB (cumple). Por encima de 1,2 GHz el módulo de S21 tiene rizado y picos > 0 dB: la calibración corrige S21 solo con THRU, sin aislamiento ni corrección de S22. Ese tramo no se usa.\n'
        '• Retardo de L17 (0,195 ns) menos 16,6 mm de línea: el conector y el codo equivalen a unos 13,8 mm de línea (hay que comprobar si los 16,6 mm de L17 son entre transiciones).',
        'Method: L64 and L17 have the same elbow and the same connectors; they differ only in 47.0 mm of straight line. The ratio S21(L64)/S21(L17) removes the connector and elbow and leaves the phase of that strip. With the 9 reconnection combinations, between 50 and 1000 MHz:\n'
        '• Differential delay 0.301 ns and εeff = 3.71 ± 0.03 (3.69 in 300–1000 MHz; 3.97 in 50–600 MHz, an unreliable window because the differential phase is small). The prediction was 3.3–3.6: it misses by a little, but stays within the refutation criterion (3.0–3.9).\n'
        '• With the design geometry of the 50 Ω microstrip, εeff 3.71 corresponds to εr ≈ 4.9, in line with the stubs (5.03).\n'
        '• Phase offset of the ratio ≈ −0.013 rad (≈ 0): the connector and elbow cancel.\n'
        '• |S21| of L17 up to 1 GHz ≈ 0 dB (holds) and of L64 at 2 GHz −1.2 dB (holds). Above 1.2 GHz the S21 magnitude has ripple and peaks > 0 dB: the calibration corrects S21 only with THRU, without isolation or an S22 correction. That range is not used.\n'
        '• L17 delay (0.195 ns) minus 16.6 mm of line: the connector and elbow are equivalent to about 13.8 mm of line (to check whether the 16.6 mm of L17 is between transitions).'),
        size=9)
    pags.append(fig)

    # 6: MS100 y CPWG
    fig = pagina(L, t('Cupón B: microstrip de 100 Ω y coplanar de 50 Ω', 'Cupon B: 100 Ω microstrip and 50 Ω coplanar'), 6)
    fig_ms_cpwg(fig, [0.09, 0.69, 0.84, 0.22], [0.09, 0.42, 0.84, 0.20], L)
    bloque(fig, 0.34, t(
        'MS100 (ancho 0,69 mm, 88,6 mm entre transiciones, εeff de Hammerstad 3,08 con εr 4,5):\n'
        '• Una línea de 100 Ω en 50 Ω da un rizado de |S11|; sus mínimos (media onda) están en 896 y 1798 MHz, con repetibilidad del 0,3 %. El período, ≈ 898 MHz, queda un 3,5 % por debajo de lo previsto (930–970 MHz): εeff 3,55 con 88,6 mm, o εeff 3,31 (εr 4,9) más ~3 mm de línea eléctrica extra del conector. |S11| máximo −5,9 dB y |S21| mínimo −2,2 dB, ambos dentro de lo previsto.\n'
        'CPWG50 (hilo 1,61 mm, hueco 0,3 mm, valla de vías, 88,6 mm, εeff de diseño 2,88):\n'
        '• Bien adaptada: |S11| < −17 dB hasta 1 GHz. |S21| mínimo −0,88 a −0,94 dB (se esperaba mejor que −0,7 dB).\n'
        '• Retardo 0,631 ns (σ 0,3 %), fuera de lo previsto (0,50–0,56 ns) y fuera del límite de refutación (0,62 ns). Descontando el retardo del conector, εeff ≈ 3,4, entre un 9 % (εr 4,9) y un 17 % (εr 4,5) por encima del diseño. Hipótesis sin comprobar: la valla de vías y la masa inferior no están en el modelo cuasi-estático; se comprobaría simulando la CPWG en 3D con las vías.',
        'MS100 (width 0.69 mm, 88.6 mm between transitions, Hammerstad εeff 3.08 with εr 4.5):\n'
        '• A 100 Ω line in 50 Ω gives an |S11| ripple; its minima (half-wave) are at 896 and 1798 MHz, with 0.3 % repeatability. The period, ≈ 898 MHz, is 3.5 % below what was expected (930–970 MHz): εeff 3.55 with 88.6 mm, or εeff 3.31 (εr 4.9) plus ~3 mm of extra electrical line from the connector. Maximum |S11| −5.9 dB and minimum |S21| −2.2 dB, both as expected.\n'
        'CPWG50 (1.61 mm trace, 0.3 mm gap, via fence, 88.6 mm, design εeff 2.88):\n'
        '• Well matched: |S11| < −17 dB up to 1 GHz. Minimum |S21| −0.88 to −0.94 dB (better than −0.7 dB was expected).\n'
        '• Delay 0.631 ns (σ 0.3 %), outside the expected 0.50–0.56 ns and outside the refutation limit (0.62 ns). Removing the connector delay, εeff ≈ 3.4, 9 % (εr 4.9) to 17 % (εr 4.5) above the design. Untested hypothesis: the via fence and the bottom ground are not in the quasi-static model; it would be checked by simulating the CPWG in 3D with the vias.'),
        size=9)
    pags.append(fig)

    # 7: tabla de predicciones
    fig = pagina(L, t('Predicciones registradas antes de medir frente a resultados', 'Predictions registered before measuring vs results'), 7)
    si, no, nc = t('Cumple', 'Holds'), t('Falla', 'Fails'), t('Sin comprobar', 'Not checked')
    filas = [[t('Id', 'Id'), t('Predicción', 'Prediction'), t('Medido', 'Measured'), t('Resultado', 'Result')],
             ['P1', t('f₂/f₁ = 3,00 ± 0,04; f₃/f₁ = 5,00 ± 0,08', 'f₂/f₁ = 3.00 ± 0.04; f₃/f₁ = 5.00 ± 0.08'), '3.035; 5.037' if L else '3,035; 5,037', si],
             ['P2', t('εr FR4 (dos stubs, modo 1) 4,4 (4,1–4,7)', 'FR4 εr (two stubs, mode 1) 4.4 (4.1–4.7)'), '5.03 ± 0.05' if L else '5,03 ± 0,05', no],
             ['P3', t('Lanzamiento 2–6 mm', 'Launch 2–6 mm'), '−0.33 mm' if L else '−0,33 mm', no],
             ['P4', t('f₁ de S80 420–475 MHz', 'S80 f₁ 420–475 MHz'), '454.0 MHz' if L else '454,0 MHz', si],
             ['P5', t('f₁ de S30 960–1070 MHz', 'S30 f₁ 960–1070 MHz'), '1095.8 MHz' if L else '1095,8 MHz', no],
             ['P6', t('R de S80, modo 1: 1–6 Ω', 'S80 R, mode 1: 1–6 Ω'), t('0,30 Ω (< residuo cal.)', '0.30 Ω (< cal. residual)'), no],
             ['P7', t('Dispersión entre 5 unidades ≤ 0,5 %', 'Spread across 5 units ≤ 0.5 %'), t('una unidad', 'one unit'), nc],
             ['P8', t('Reconexión ≤ 0,3 % en f', 'Reconnection ≤ 0.3 % in f'), 'S80 0.03 %, S30 σ 0.2 %' if L else 'S80 0,03 %, S30 σ 0,2 %', si],
             ['L1', t('εeff microstrip 50 Ω (L64−L17) 3,3–3,6', '50 Ω microstrip εeff (L64−L17) 3.3–3.6'), '3.71 ± 0.03' if L else '3,71 ± 0,03', no],
             ['L2', t('|S21| de L17 hasta 1 GHz > −1 dB', 'L17 |S21| up to 1 GHz > −1 dB'), '≈ 0 dB', si],
             ['L3', t('|S21| de L64 a 2 GHz −0,5…−2,0 dB', 'L64 |S21| at 2 GHz −0.5…−2.0 dB'), '−1.2 dB' if L else '−1,2 dB', si],
             ['L4', t('Repetibilidad de |S21| ≤ 0,3 dB', '|S21| repeatability ≤ 0.3 dB'), t('no analizada', 'not analysed'), nc],
             ['M1', t('Período del rizado de MS100 930–970 MHz', 'MS100 ripple period 930–970 MHz'), '896–899 MHz', no],
             ['M2', t('|S11| máx. −3…−6 dB cerca de 470–490 MHz', 'max |S11| −3…−6 dB near 470–490 MHz'), '−5.9 dB, 440–455 MHz' if L else '−5,9 dB, 440–455 MHz', si],
             ['M3', t('|S21| mín. −1,5…−3,0 dB', 'min |S21| −1.5…−3.0 dB'), '−2.2 dB' if L else '−2,2 dB', si],
             ['M4', t('εeff de MS100 3,1–3,5', 'MS100 εeff 3.1–3.5'), '3.55' if L else '3,55', no],
             ['C1', t('Retardo CPWG 0,50–0,56 ns', 'CPWG delay 0.50–0.56 ns'), '0.631 ns' if L else '0,631 ns', no],
             ['C2', t('|S11| CPWG < −15 dB hasta 1 GHz', 'CPWG |S11| < −15 dB up to 1 GHz'), '−17 dB', si],
             ['C3', t('|S21| CPWG > −0,7 dB hasta 1 GHz', 'CPWG |S21| > −0.7 dB up to 1 GHz'), '−0.88…−0.94 dB' if L else '−0,88…−0,94 dB', no],
             ['C4', t('CPWG más corta que MS100', 'CPWG shorter than MS100'), '0.631 vs 0.627 ns' if L else '0,631 frente a 0,627 ns', no]]
    tabla(fig, [0.07, 0.30, 0.86, 0.62], filas, [0.07, 0.43, 0.30, 0.20], size=7.5)
    bloque(fig, 0.45, t(
        'Total: 8 cumplen, 10 fallan, 2 sin comprobar. Los anillos se compararon con la simulación 3D (tabla de la página 4), pero no llevaban un criterio de aceptación escrito antes de medir. Los fallos no son todos del mismo tipo: P2, P3, P5, L1, M1 y M4 comparten una causa probable (εr real más alta que 4,5 y longitud eléctrica extra del conector); P6 no es concluyente por el residuo de calibración.',
        'Total: 8 hold, 10 fail, 2 not checked. The rings were compared against the 3D simulation (table on page 4), but had no acceptance criterion written before measuring. The failures are not all of one kind: P2, P3, P5, L1, M1 and M4 share a probable cause (real εr higher than 4.5 and extra electrical length from the connector); P6 is inconclusive because of the calibration residual.'),
        size=8.5)
    pags.append(fig)

    # 8: antenas
    fig = pagina(L, t('Antenas de 2,4 GHz de la tanda JLC', '2.4 GHz antennas from the JLC batch'), 8)
    fig_antenas(fig, [0.09, 0.69, 0.84, 0.21], [0.09, 0.42, 0.84, 0.21], L)
    tabla(fig, [0.07, 0.31, 0.86, 0.08], [
        [t('Antena', 'Antenna'), t('Simulación', 'Simulation'), t('Medida (cal. amplia)', 'Measured (wide cal.)'), t('Banda −10 dB', '−10 dB band')],
        ['Yagi 2 directores', '2445 MHz, −19.7 dB' if L else '2445 MHz, −19,7 dB', '2534 MHz, −12.1 dB' if L else '2534 MHz, −12,1 dB', '2489–2577 MHz'],
        ['Sierpinski', '2462 MHz, −59 dB', '2502 MHz, −34.3 dB' if L else '2502 MHz, −34,3 dB', t('desde 2274 MHz hasta ≥ 2700 MHz', 'from 2274 MHz to ≥ 2700 MHz')],
    ], [0.2, 0.25, 0.25, 0.3])
    bloque(fig, 0.28, t(
        '• Con la calibración del usuario y la amplia, las dos antenas coinciden dentro de |ΔΓ| = 0,03 rms (0,053 máximo), que es el error de la calibración del usuario (su suelo en la carga es −31…−36 dB). Por debajo de −25 dB no se distinguen: la profundidad del Sierpinski debe leerse como «mejor que −30 dB».\n'
        '• La Yagi resuena un 3,6 % por encima de lo simulado con εr 4,5 (2447 MHz) y el Sierpinski un 1,0 % (centro de banda simulado, 2476 MHz). Simulado en 3D (tanδ 0,02): el Sierpinski es estable con la malla (2476–2487 MHz con εr 4,5; con 4,2 da 2501, igual que lo medido), así que pide εr ≈ 4,2–4,4. La Yagi no: su frecuencia simulada cae un 3 % al cambiar el paso de malla ±15 % (2364–2447 MHz con εr 4,5) y la medida (2534) queda por encima de todo ese rango; con εr 4,9 quedaría aún más lejos (2394). Un grosor de 1,45 mm tampoco lo explica (+0,7 %). La Yagi además tiene la banda más estrecha (88 frente a 166 MHz) y peor adaptación (−12,1 frente a −17,6 dB): no todo es la εr (cable sin ferrita, SMA, tolerancias).\n'
        '• Se midieron con latiguillos; no consta si había ferrita en el cable (la hoja del pedido la pedía para masas pequeñas).',
        '• With the user\'s and the wide calibration, both antennas agree within |ΔΓ| = 0.03 rms (0.053 maximum), which is the error of the user\'s calibration (its floor on the load is −31…−36 dB). Below −25 dB they cannot be told apart: the Sierpinski depth should be read as «better than −30 dB».\n'
        '• The Yagi resonates 3.6 % above the εr 4.5 simulation (2447 MHz) and the Sierpinski 1.0 % (simulated band centre, 2476 MHz). Simulated in 3D (tanδ 0.02): the Sierpinski is mesh-stable (2476–2487 MHz with εr 4.5; with 4.2 it gives 2501, same as measured), so it asks for εr ≈ 4.2–4.4. The Yagi does not: its simulated frequency drops 3 % when the mesh step changes ±15 % (2364–2447 MHz with εr 4.5) and the measurement (2534) lies above that whole range; with εr 4.9 it would be even further (2394). A 1.45 mm thickness does not explain it either (+0.7 %). The Yagi also has a narrower band (88 vs 166 MHz) and worse matching (−12.1 vs −17.6 dB): not everything is εr (cable without ferrite, SMA, tolerances).\n'
        '• They were measured with patch cables; it is not recorded whether a ferrite was on the cable (the order sheet asked for one for small ground planes).'),
        size=8.5)
    pags.append(fig)

    # 9: conclusiones
    fig = pagina(L, t('Conclusiones, límites y pendientes', 'Conclusions, limits and open items'), 9)
    y = 0.925
    y = bloque(fig, y, t('Conclusiones', 'Conclusions'), size=11, negrita=True, color=AZUL)
    y = bloque(fig, y, t(
        '• El instrumento y la calibración funcionan: stubs, anillos y líneas son repetibles a 0,03–0,3 % en frecuencia.\n'
        '• Los resonadores (S80, anillos, Sierpinski, MS100) coinciden en εr ≈ 4,2–4,55 con el simulador 3D corregido, cerca del 4,5 nominal; no se debe usar 4,9. Quedan sin explicar la Yagi (simulación inestable con la malla), S30 (≈ 4,1) y el retardo de la línea de 50 Ω (≈ 4,85); el grosor no es la causa.\n'
        '• El método de los stubs con solo dos largos no separa la εr del conector; hace falta un tercer largo (cupón C) o resolver la reactancia del conector.\n'
        '• El R868 es utilizable como sensor de plásticos (pico limpio, tres modos); falta medir su desplazamiento con una muestra.\n'
        '• La CPWG real es más lenta que su modelo de diseño.',
        '• The instrument and calibration work: stubs, rings and lines are repeatable to 0.03–0.3 % in frequency.\n'
        '• The resonators (S80, rings, Sierpinski, MS100) agree on εr ≈ 4.2–4.55 with the corrected 3D simulator, close to the nominal 4.5; 4.9 should not be used. Unexplained: the Yagi (mesh-unstable simulation), S30 (≈ 4.1) and the 50 Ω line delay (≈ 4.85); thickness is not the cause.\n'
        '• The stub method with only two lengths does not separate εr from the connector; a third length (coupon C) or a connector reactance model is needed.\n'
        '• R868 is usable as a plastics sensor (clean peak, three modes); its shift with a sample still has to be measured.\n'
        '• The real CPWG is slower than its design model.'), size=9)
    y -= 0.01
    y = bloque(fig, y, t('Límites de estas medidas', 'Limits of these measurements'), size=11, negrita=True, color=AZUL)
    y = bloque(fig, y, t(
        '• Una sola unidad de cada cupón; sin dispersión entre unidades.\n'
        '• Sin de-embedding: conector y lanzamiento van dentro de la medida.\n'
        '• S21 sin aislamiento ni corrección de S22: el suelo está en torno a −50 dB y el módulo por encima de 1,2 GHz es poco fiable; hay un artefacto del THRU en 2095–2125 MHz.\n'
        '• La resistencia de los stubs (décimas de ohmio) queda por debajo del residuo de la calibración: no hay tanδ. Tampoco son fiables la R ni los niveles de S21 simulados (dependen del puerto y de la banda); las frecuencias de los stubs y anillos simulados tenían ±1 % de incertidumbre por un puerto mal configurado (corregido el 22-11 en las líneas).\n'
        '• La calibración del usuario cambió de estado una vez durante la sesión (slot activo); las medidas de las antenas se hicieron con el estado correcto, y la amplia es la referencia.\n'
        '• Nada de esto está commiteado en el repositorio.',
        '• One unit of each coupon; no unit-to-unit spread.\n'
        '• No de-embedding: the connector and launch are inside the measurement.\n'
        '• S21 without isolation or an S22 correction: the floor is around −50 dB and the magnitude above 1.2 GHz is unreliable; there is a THRU artefact at 2095–2125 MHz.\n'
        '• The stub resistance (tenths of an ohm) is below the calibration residual: no tanδ. The simulated R and S21 levels are not reliable either (they depend on the port and the band); the simulated stub and ring frequencies carried ±1 % uncertainty from a misconfigured port (fixed on 22-11 in the line script).\n'
        '• The user\'s calibration changed state once during the session (active slot); the antenna measurements were made with the correct state, and the wide one is the reference.\n'
        '• None of this is committed to the repository.'), size=9)
    y -= 0.01
    y = bloque(fig, y, t('Siguientes pasos', 'Next steps'), size=11, negrita=True, color=AZUL)
    bloque(fig, y, t(
        '1. Medir el tercer stub (cupón C) y ajustar la εr con tres largos.\n'
        '2. Repetir la Yagi con malla más fina y con y sin ferrita en el cable; averiguar por qué el retardo de la línea de 50 Ω (L64 − L17) da εr ≈ 4,85 y el resto 4,2–4,55.\n'
        '3. Simular la CPWG en 3D con las vías y la masa inferior.\n'
        '4. Medir un anillo (R868) con una muestra de plástico de εr conocida.\n'
        '5. Repetir el Sierpinski con y sin ferrita y medir el resto de antenas del pedido (parche, Koch, J-pole, dipolo).',
        '1. Measure the third stub (coupon C) and fit εr with three lengths.\n'
        '2. Repeat the Yagi with a finer mesh and with and without a ferrite on the cable; find out why the 50 Ω line delay (L64 − L17) gives εr ≈ 4.85 and the rest 4.2–4.55.\n'
        '3. Simulate the CPWG in 3D with the vias and bottom ground.\n'
        '4. Measure a ring (R868) with a plastic sample of known εr.\n'
        '5. Repeat the Sierpinski with and without a ferrite and measure the remaining antennas of the order (patch, Koch, J-pole, dipole).'), size=9)
    pags.append(fig)
    return pags


def main():
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else SALIDA
    salida.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(salida) as pdf:
        for L in (0, 1):
            portada = plt.figure(figsize=A4)
            portada.text(0.5, 0.62, ('Informe de medidas', 'Measurement report')[L], ha='center', fontsize=26, weight='bold', color=AZUL)
            portada.text(0.5, 0.56, ('Cupones de εr A y B y antenas de 2,4 GHz', 'εr coupons A and B and 2.4 GHz antennas')[L], ha='center', fontsize=14)
            portada.text(0.5, 0.52, 'Chirptenna · 22-11-2026', ha='center', fontsize=11, color=GRIS)
            portada.text(0.5, 0.48, ('Versión en castellano', 'English version')[L], ha='center', fontsize=11, color=GRIS)
            pdf.savefig(portada)
            plt.close(portada)
            for fig in construir(L):
                pdf.savefig(fig)
                plt.close(fig)
        d = pdf.infodict()
        d['Title'] = 'Informe de medidas 22-11-2026 / Measurement report 22-11-2026'
        d['Author'] = 'Chirptenna'
    print(salida)
    for L, sufijo in ((0, 'es'), (1, 'en')):          # un PDF por idioma
        ruta = salida.with_name(salida.stem + f'_{sufijo}.pdf')
        with PdfPages(ruta) as pdf:
            portada = plt.figure(figsize=A4)
            portada.text(0.5, 0.62, ('Informe de medidas', 'Measurement report')[L], ha='center', fontsize=26, weight='bold', color=AZUL)
            portada.text(0.5, 0.56, ('Cupones de εr A y B y antenas de 2,4 GHz', 'εr coupons A and B and 2.4 GHz antennas')[L], ha='center', fontsize=14)
            portada.text(0.5, 0.52, 'Chirptenna · 22-11-2026', ha='center', fontsize=11, color=GRIS)
            pdf.savefig(portada)
            plt.close(portada)
            for fig in construir(L):
                pdf.savefig(fig)
                plt.close(fig)
        print(ruta)


if __name__ == '__main__':
    main()
