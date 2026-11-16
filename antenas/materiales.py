"""Sustratos disponibles y síntesis de líneas microstrip."""
import re
from dataclasses import dataclass

import numpy as np

from .i18n import tr

C0 = 299792458.0


@dataclass(frozen=True)
class Sustrato:
    nombre: str
    er: float
    tand: float
    h: float           # grosor del dieléctrico [mm]
    cobre_um: float = 35.0
    nota: str = ''
    capas: int = 2     # capas de cobre de la placa (4: In1.Cu y In2.Cu entre las dos caras)
    h_ref: float = 0.0  # con 4 capas: distancia de F.Cu a la masa In1.Cu [mm] (la línea de 50 Ω ve esta, no `h`)
    er_tol: float = 0.05  # tolerancia relativa de εr (fracción) para el análisis de tolerancias: 5 % supuesto en FR4; los PTFE traen la suya

    @property
    def h_linea(self):
        """Grosor de dieléctrico que ve la microstrip: bajo ella está la masa más cercana."""
        return self.h_ref if self.capas > 2 and self.h_ref > 0 else self.h

    @property
    def z_masa(self):
        """Cota de la masa respecto a la cara inferior [mm]: 0 con 2 capas; con 4, la de In1.Cu."""
        return self.h - self.h_ref if self.capas > 2 and self.h_ref > 0 else 0.0


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
# grosores 0,65 / 0,9 / 1,65 mm (más 0,76 y 1,52 mm, que el usuario ve en el pedido de PTFE de JLC, 16-11). εr y tanδ son los del laminador (ZYF…, a 10 GHz), sin tolerancias publicadas: medir con el
# cupón. Sin confirmar qué combinaciones de material y grosor tiene JLC en stock.
# Datasheet del laminador (ZYST, `PTFE_Teflon_Datasheet.pdf`, 16-11): Dk ±0,04 (ZYF255DA y ZYF265D) y ±0,05 (los dos ZYF300CA), a 10 GHz; εr en
# la última columna. El análisis de tolerancias usa esa tolerancia (1,5–1,7 %) en vez del ±5 % que se supone para el FR4.
PTFE_JLC = (('ZYF255DA', 2.55, 0.0018, 0.04), ('ZYF265D', 2.65, 0.0019, 0.04), ('ZYF300CA-C', 2.94, 0.0016, 0.05), ('ZYF300CA-P', 3.0, 0.0018, 0.05))
for _n, _er, _td, _tol in PTFE_JLC:
    for _h in (1.65, 1.52, 0.9, 0.76, 0.65):         # 1,52 y 0,76 mm: grosores que el usuario ve para el PTFE en JLC (16-11), sin confirmar
        _k = f'PTFE {_n} {_h:g} mm'.replace('.', ',')
        SUSTRATOS[_k] = Sustrato(_k, _er, _td, _h, er_tol=round(_tol/_er, 4),
                                 nota='εr y tanδ del laminador, sin medir; combinación sin confirmar en JLC')

# Flex de JLC (poliimida de 25 o 50 µm, cobre de 18 µm): εr 3,3 (núcleo) de su página de capacidades; tanδ 0,004 (su blog da
# 0,002–0,003 y otras fuentes hasta 0,007). Sin el coverlay (εr 2,9 con adhesivo) ni el adhesivo: la placa se modela plana.
# JLC no ofrece impedancia controlada en flex y una microstrip de 50 Ω sale de ~0,05–0,09 mm: no se puede fabricar.
for _h, _k in ((0.05, 'Flex PI 50 µm'), (0.025, 'Flex PI 25 µm')):
    SUSTRATOS[_k] = Sustrato(_k, 3.3, 0.004, _h, cobre_um=18.0, nota='flex: sin coverlay ni adhesivo; sin impedancia controlada')

# 4 capas de JLC, apilado JLC04161H-7628 (1,6 mm): cobre 35 µm fuera y 15,2 µm dentro, prepreg 7628 de 0,2104 mm (εr 4,4) entre F.Cu y
# In1.Cu, núcleo NP-155F de 1,065 mm (εr 4,43) entre In1.Cu e In2.Cu. Fuente: la transcripción de la calculadora de impedancias de JLC de
# https://gist.github.com/biergaizi/21954da168b29b4435d420730ff26b17 (no he podido leer la tabla en la web de JLC; su página de capacidades da
# 4,6 para el prepreg 7628: **comprobar en la calculadora de JLC antes de fabricar**). Se modela con una sola εr (4,4) y el grosor del dieléctrico
# entre las dos caras (0,2104·2 + 0,0152·2 + 1,065 = 1,516 mm); la masa de la simulación es la de In1.Cu (las de In2.Cu y B.Cu se funden con ella).
SUSTRATOS['FR4 JLC 4 capas 1,6 mm'] = Sustrato('FR4 JLC 4 capas 1,6 mm', 4.4, 0.02, 1.516, capas=4, h_ref=0.2104,
                                               nota='4 capas JLC04161H-7628: línea de 50 Ω de ~0,4 mm sobre In1.Cu; εr sin medir')
SUSTRATO_POR_DEFECTO = 'FR4 JLC 1,6 mm'

# Sustrato personalizado (por ejemplo un PTFE o un Rogers que no está en la lista): su nombre lleva los valores, así que viaja tal cual en
# `diseno.json`, en el trabajo de simulación y en la web, y `sustrato_por_nombre` lo reconstruye sin otra tabla. Siempre de 2 capas.
PERSONALIZADO = 'Personalizado'
LIMITES_PERSONALIZADO = {'er': (1.0, 20.0), 'tand': (0.0, 0.2), 'h': (0.02, 6.0)}
_NUM = r'(\d+(?:,\d+)?)'
_RE_PERSONALIZADO = re.compile(rf'^{PERSONALIZADO} \(εr {_NUM}; tanδ {_NUM}; {_NUM} mm\)$')


def _texto_num(x):
    return f'{x:.6f}'.rstrip('0').rstrip('.').replace('.', ',')


def nombre_personalizado(er, tand, h):
    """Nombre canónico de un sustrato personalizado: «Personalizado (εr 2,65; tanδ 0,0019; 1,65 mm)»."""
    for clave, valor in (('er', er), ('tand', tand), ('h', h)):
        lo, hi = LIMITES_PERSONALIZADO[clave]
        if valor is None or not lo <= float(valor) <= hi:
            etiqueta = {'er': 'εr', 'tand': 'tanδ', 'h': 'grosor [mm]'}[clave]
            raise ValueError(tr('{0} fuera de rango ({1:g} a {2:g}): {3}', etiqueta, lo, hi, valor))
    return f'{PERSONALIZADO} (εr {_texto_num(er)}; tanδ {_texto_num(tand)}; {_texto_num(h)} mm)'


def es_personalizado(nombre):
    return bool(nombre) and _RE_PERSONALIZADO.match(nombre) is not None


def valores_personalizado(nombre):
    """(εr, tanδ, grosor mm) de un nombre personalizado, o None si no lo es."""
    m = _RE_PERSONALIZADO.match(nombre or '')
    return None if m is None else tuple(float(g.replace(',', '.')) for g in m.groups())


def sustrato_por_nombre(nombre):
    """Sustrato de la tabla o personalizado (`KeyError` si no existe, como antes con la tabla sola)."""
    if nombre in SUSTRATOS:
        return SUSTRATOS[nombre]
    v = valores_personalizado(nombre)
    if v is None:
        raise KeyError(nombre)
    er, tand, h = v
    nombre_personalizado(er, tand, h)                  # valida los rangos
    return Sustrato(nombre, er, tand, h, nota='personalizado: εr y tanδ puestos por el usuario, sin medir')


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
