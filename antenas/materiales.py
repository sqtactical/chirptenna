"""Sustratos disponibles y síntesis de líneas microstrip."""
from dataclasses import dataclass

import numpy as np

C0 = 299792458.0


@dataclass(frozen=True)
class Sustrato:
    nombre: str
    er: float
    tand: float
    h: float           # grosor del dieléctrico [mm]
    cobre_um: float = 35.0
    nota: str = ''


# εr del FR4: valor de la calculadora de impedancias de JLC para 2 capas (pendiente de
# medir con el cupón). RO4350B: εr "de diseño" de Rogers (3,66), no la de proceso (3,48).
SUSTRATOS = {
    'FR4 JLC 1,6 mm': Sustrato('FR4 JLC 1,6 mm', 4.5, 0.02, 1.6, nota='εr pendiente de medir con el cupón'),
    'FR4 JLC 1,2 mm': Sustrato('FR4 JLC 1,2 mm', 4.5, 0.02, 1.2),
    'FR4 JLC 1,0 mm': Sustrato('FR4 JLC 1,0 mm', 4.5, 0.02, 1.0),
    'FR4 JLC 0,8 mm': Sustrato('FR4 JLC 0,8 mm', 4.5, 0.02, 0.8),
    'RO4350B 1,52 mm': Sustrato('RO4350B 1,52 mm', 3.66, 0.0037, 1.524, nota='confirmar grosores en JLC'),
    'RO4350B 0,76 mm': Sustrato('RO4350B 0,76 mm', 3.66, 0.0037, 0.762, nota='confirmar grosores en JLC'),
}
SUSTRATO_POR_DEFECTO = 'FR4 JLC 1,6 mm'


def ancho_microstrip(z0, er, h):
    """Ancho de pista microstrip para impedancia z0 (Wheeler/Hammerstad), mismas unidades que h."""
    a = z0/60*np.sqrt((er + 1)/2) + (er - 1)/(er + 1)*(0.23 + 0.11/er)
    wh = 8*np.exp(a)/(np.exp(2*a) - 2)
    if wh > 2:
        b = 377*np.pi/(2*z0*np.sqrt(er))
        wh = 2/np.pi*(b - 1 - np.log(2*b - 1) + (er - 1)/(2*er)*(np.log(b - 1) + 0.39 - 0.61/er))
    return float(wh*h)


def eps_eff_microstrip(er, h, w):
    if w/h >= 1:
        return (er + 1)/2 + (er - 1)/2/np.sqrt(1 + 12*h/w)
    return (er + 1)/2 + (er - 1)/2*(1/np.sqrt(1 + 12*h/w) + 0.04*(1 - w/h)**2)


def lambda0_mm(f):
    return C0/f*1e3
