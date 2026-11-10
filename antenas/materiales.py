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

# PTFE («teflón») de la página de alta frecuencia de JLC (09-11): 2 capas, cobre de 1 oz, ENIG, pista y hueco ≥ 0,1 mm,
# grosores 0,65 / 0,9 / 1,65 mm. εr y tanδ son los del laminador (ZYF…, a 10 GHz), sin tolerancias publicadas: medir con el
# cupón. Sin confirmar qué combinaciones de material y grosor tiene JLC en stock.
PTFE_JLC = (('ZYF255DA', 2.55, 0.0018), ('ZYF265D', 2.65, 0.0019), ('ZYF300CA-C', 2.94, 0.0016), ('ZYF300CA-P', 3.0, 0.0018))
for _n, _er, _td in PTFE_JLC:
    for _h in (1.65, 0.9, 0.65):
        _k = f'PTFE {_n} {_h:g} mm'.replace('.', ',')
        SUSTRATOS[_k] = Sustrato(_k, _er, _td, _h, nota='εr y tanδ del laminador, sin medir; combinación sin confirmar en JLC')

# Flex de JLC (poliimida de 25 o 50 µm, cobre de 18 µm): εr 3,3 (núcleo) de su página de capacidades; tanδ 0,004 (su blog da
# 0,002–0,003 y otras fuentes hasta 0,007). Sin el coverlay (εr 2,9 con adhesivo) ni el adhesivo: la placa se modela plana.
# JLC no ofrece impedancia controlada en flex y una microstrip de 50 Ω sale de ~0,05–0,09 mm: no se puede fabricar.
for _h, _k in ((0.05, 'Flex PI 50 µm'), (0.025, 'Flex PI 25 µm')):
    SUSTRATOS[_k] = Sustrato(_k, 3.3, 0.004, _h, cobre_um=18.0, nota='flex: sin coverlay ni adhesivo; sin impedancia controlada')
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
