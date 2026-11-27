"""Red de alimentación de la hélice cuadrifilar (QHA): híbrido de 90° y una red en L por dipolo.

La QHA son dos dipolos helicoidales cruzados (1–3 y 2–4) que hay que alimentar con 90° de desfase y la misma amplitud. Cada uno
tiene unos 15 Ω de entrada, lejos de los 50 Ω. Un híbrido de 90° ideal (divisor 3 dB: puertos 0° y −90°, el cuarto cargado con
50 Ω) da el desfase y, con **cargas iguales**, la entrada del híbrido queda adaptada aunque los dipolos no lo estén: lo
reflejado por los dos dipolos va a la carga del puerto aislado y se pierde. Por eso adaptar cada dipolo con una red en L no
arregla la S11 que ve el receptor (ya es buena) sino la **potencia que llega a la antena**.

Todo es circuito (sin openEMS): recibe la impedancia de cada dipolo (de `herramientas/helice_flex.py`, dos puertos) y devuelve la
red, la eficiencia de adaptación en frecuencia y la desviación de fase y de amplitud entre los dos dipolos.
"""

from __future__ import annotations

import math

import numpy as np

Z0 = 50.0
Q_BOBINA, Q_CONDENSADOR = 40.0, 150.0       # de catálogo para 0402/0603 de RF a 1,5 GHz; sin medir


def z_componente(tipo: str, valor: float, f_Hz: float, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR) -> complex:
    """Impedancia de una bobina (nH) o un condensador (pF) con su pérdida (Q a esa frecuencia)."""
    w = 2*math.pi*f_Hz
    if tipo == 'L':
        x = w*valor*1e-9
        return x/q_l + 1j*x
    x = 1/(w*valor*1e-12)
    return x/q_c - 1j*x


def zin_red_l(z_ant, f_Hz, red: dict, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR):
    """Impedancia de entrada de la red L (`ajuste.redes_l`: 'posicion', 'serie', 'derivacion') cargada con `z_ant` (escalar o array)."""
    zs = 0 if red['serie'][0] not in ('L', 'C') else z_componente(red['serie'][0], red['serie'][1], f_Hz, q_l, q_c)
    zp = z_componente(red['derivacion'][0], red['derivacion'][1], f_Hz, q_l, q_c)
    z_ant = np.asarray(z_ant, dtype=complex)
    if red['posicion'] == 'Z3':                       # derivación junto a la antena, serie hacia el conector
        return 1/(1/z_ant + 1/zp) + zs
    return 1/(1/(z_ant + zs) + 1/zp)                  # serie junto a la antena, derivación hacia el conector


def eficiencia_red(z_ant, f_Hz, red: dict | None, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR):
    """Fracción de la potencia que entra en la red que llega a la antena (el resto se pierde en la resistencia serie de las
    bobinas y los condensadores). Sin red vale 1."""
    z_ant = np.asarray(z_ant, dtype=complex)
    if red is None:
        return np.ones(z_ant.shape)
    zs = 0 if red['serie'][0] not in ('L', 'C') else z_componente(red['serie'][0], red['serie'][1], f_Hz, q_l, q_c)
    zp = z_componente(red['derivacion'][0], red['derivacion'][1], f_Hz, q_l, q_c)
    z_in = zin_red_l(z_ant, f_Hz, red, q_l, q_c)
    if red['posicion'] == 'Z3':                       # I_ant = I_in·Zpar/Z_ant
        zpar = 1/(1/z_ant + 1/zp)
        p_ant = z_ant.real*np.abs(zpar/z_ant)**2                   # por unidad de |I_in|²
        p_in = z_in.real
    else:                                             # I_ant = V_in/(Z_ant + Zs), I_in = V_in/Z_in
        p_ant = z_ant.real/np.abs(z_ant + zs)**2                   # por unidad de |V_in|²
        p_in = z_in.real/np.abs(z_in)**2
    return np.clip(p_ant/p_in, 0.0, 1.0)


def perdida_red_dB(z_ant, f_Hz, red: dict | None, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR):
    """Pérdida por disipación de la red L en dB (positiva). En recepción es lo que añade a la figura de ruido: una pérdida pasiva de L dB a la
    temperatura de referencia suma L dB a la figura de ruido si va antes del amplificador."""
    return -10*np.log10(eficiencia_red(z_ant, f_Hz, red, q_l, q_c))


def perdida_desadaptacion_dB(z_ant, f_Hz, red: dict | None, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR):
    """Pérdida de señal por desadaptación en los terminales de cada dipolo (dB, positiva): 10·log10(1/(1 − |Γ|²)). No añade ruido (lo
    reflejado se pierde en el puerto aislado del híbrido, sin dañar la entrada) pero baja la señal y con ello la relación señal/ruido."""
    z = np.asarray(z_ant, dtype=complex)
    z_in = z if red is None else zin_red_l(z, f_Hz, red, q_l, q_c)
    return -10*np.log10(eficiencia_adaptacion(z_in))


def eficiencia_adaptacion(z_in) -> np.ndarray:
    """Potencia que entra en la carga respecto a la incidente: 1 − |Γ|² con Γ respecto a 50 Ω."""
    g = (np.asarray(z_in, dtype=complex) - Z0)/(np.asarray(z_in, dtype=complex) + Z0)
    return 1.0 - np.abs(g)**2


def disenar_red(z_ant: complex, f0_Hz: float, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR) -> dict | None:
    """La mejor red L con valores E24 (de `ajuste.redes_l`) para un dipolo de impedancia `z_ant` a f0, con Q finito; None si no hay."""
    from . import ajuste
    mejor, mejor_eta = None, -1.0
    for sol in ajuste.redes_l(z_ant, f0_Hz):
        eta = float(eficiencia_adaptacion(zin_red_l(z_ant, f0_Hz, sol, q_l, q_c)) * eficiencia_red(z_ant, f0_Hz, sol, q_l, q_c))
        if eta > mejor_eta:
            mejor, mejor_eta = sol, eta
    if mejor is None:
        return None
    return dict(mejor, eficiencia_total=mejor_eta)


def evaluar(f_Hz, z_ant, red: dict | None, q_l: float = Q_BOBINA, q_c: float = Q_CONDENSADOR) -> dict:
    """Eficiencia de adaptación y S11 de cada dipolo (con su red, si la hay) en f. Con el híbrido ideal y las dos ramas iguales la
    S11 que ve el receptor es la del híbrido (muy buena), y lo reflejado se pierde en el puerto aislado: por eso lo que importa es
    la eficiencia."""
    z = np.asarray(z_ant, dtype=complex)
    z_in = z if red is None else zin_red_l(z, np.asarray(f_Hz), red, q_l, q_c)
    eta_adapt = eficiencia_adaptacion(z_in)
    g_dipolo = (z_in - Z0)/(z_in + Z0)
    return {'eficiencia_adaptacion': eta_adapt, 'eficiencia_red': eficiencia_red(z, f_Hz, red, q_l, q_c),
            'eficiencia_total': eta_adapt*eficiencia_red(z, f_Hz, red, q_l, q_c), 'S11_dipolo_dB': 20*np.log10(np.abs(g_dipolo) + 1e-12)}


def desbalance(z_a, z_b, f_Hz, red_a: dict | None, red_b: dict | None) -> dict:
    """Diferencia de potencia (dB) y de fase (°) que llega a los dos dipolos si no son idénticos (en la práctica: componentes
    con tolerancia). Con híbrido ideal y reflexión en cada puerto, la amplitud entregada es √(1 − |Γ|²) de la incidente."""
    ea = float(eficiencia_adaptacion(zin_red_l(z_a, f_Hz, red_a) if red_a else z_a) * eficiencia_red(z_a, f_Hz, red_a))
    eb = float(eficiencia_adaptacion(zin_red_l(z_b, f_Hz, red_b) if red_b else z_b) * eficiencia_red(z_b, f_Hz, red_b))
    return {'delta_potencia_dB': 10*math.log10(ea/eb), 'eficiencia_a': ea, 'eficiencia_b': eb}


def razon_axial_cenit_dB(delta_potencia_dB: float, delta_fase_deg: float = 0.0) -> float:
    """Razón axial en el cénit de dos dipolos cruzados con desbalance de amplitud (dB de potencia) y error de fase (° respecto de 90°).

    Con amplitudes a y b y fase 90° + e, el campo es una elipse: AR = (|A| + |B|)/(|A| − |B|) con los modos de giro derecho e izquierdo
    |A|, |B|. Se calcula con el vector de Jones (1, (b/a)·e^{j(90° + e)})."""
    r = 10**(delta_potencia_dB/20.0)                  # b/a
    psi = math.radians(90.0 + delta_fase_deg)
    ex, ey = 1.0, r*np.exp(1j*psi)
    er = abs(ex + 1j*ey)/math.sqrt(2)
    el = abs(ex - 1j*ey)/math.sqrt(2)
    if abs(er - el) < 1e-12:
        return 99.0
    return float(20*math.log10((er + el)/abs(er - el)))
