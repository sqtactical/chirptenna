"""Calibración del NanoVNA hecha y guardada en el PC.

El equipo mide en bruto (cal off) y la corrección se aplica aquí:
  - S11: modelo de 3 términos (Ed, Es, Er) con OPEN, SHORT y LOAD ideales.
  - S21: respuesta + aislamiento (Et con THRU, Ex con cargas en los dos puertos).
Ventajas frente a la del equipo: tantos puntos como se quiera (barridos de 101
puntos encadenados), se guarda en un fichero del PC y no ocupa ni pisa los
slots del NanoVNA.
"""
import os
import json
import datetime

import numpy as np

DIR_CAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calibraciones')
ESTANDARES = ('open', 'short', 'load', 'isoln', 'thru')
MAX_PUNTOS_SCAN = 101


def rejilla(f_ini, f_fin, puntos):
    """Rejilla lineal; se mide en tramos de <= 101 puntos que la respetan exactamente."""
    return np.linspace(f_ini, f_fin, int(puntos))


def medir_bruto(vna, f):
    """S11 y S21 sin corregir en la rejilla f. Deja el equipo como estaba."""
    estado = ' '.join(vna.comando('cal'))
    barrido = vna.barrido_actual()
    s11 = np.empty(len(f), complex)
    s21 = np.empty(len(f), complex)
    vna.comando('cal off')
    try:
        for i in range(0, len(f), MAX_PUNTOS_SCAN):
            tramo = f[i:i + MAX_PUNTOS_SCAN]
            ft, a, b = vna.medir(tramo[0], tramo[-1], len(tramo))
            if not np.allclose(ft, tramo, atol=2.0):
                raise RuntimeError('El equipo no ha respetado la rejilla de frecuencias')
            s11[i:i + len(tramo)], s21[i:i + len(tramo)] = a, b
    finally:
        if "cal'ed" in estado:
            vna.comando('cal on')
        vna.fijar_barrido(*barrido)
    return s11, s21


class Calibracion:
    def __init__(self, f, brutos, info=None):
        self.f = np.asarray(f)
        self.brutos = brutos            # {'open': (s11, s21), ...}
        self.info = info or {}
        self._calcular()

    def _calcular(self):
        o, s, l = (self.brutos[k][0] for k in ('open', 'short', 'load'))
        self.ed = l
        a, b = o - l, s - l
        self.es = (a + b)/(a - b)
        self.er = -2*a*b/(a - b)
        self.ex = self.brutos['isoln'][1] if 'isoln' in self.brutos else np.zeros_like(o)
        self.et = (self.brutos['thru'][1] - self.ex) if 'thru' in self.brutos else None

    def corregir(self, s11m, s21m=None, idx=slice(None)):
        d = s11m - self.ed[idx]
        s11 = d/(self.er[idx] + self.es[idx]*d)
        if s21m is None or self.et is None:
            return s11, None
        return s11, (s21m - self.ex[idx])/self.et[idx]

    def medir(self, vna, f_min=None, f_max=None):
        """Mide con esta calibración. Devuelve (f, S11, S21 corregidos).

        Con f_min/f_max solo mide los puntos de la rejilla de calibración dentro de ese
        intervalo (más rápido: sirve para medir en vivo mientras se ajusta la antena).
        """
        idx = slice(None)
        if f_min is not None or f_max is not None:
            m = np.nonzero((self.f >= (f_min or 0)) & (self.f <= (f_max or np.inf)))[0]
            if len(m) < 2:
                raise ValueError('El intervalo pedido no está dentro del rango de la calibración')
            idx = slice(m[0], m[-1] + 1)
        s11m, s21m = medir_bruto(vna, self.f[idx])
        s11, s21 = self.corregir(s11m, s21m, idx)
        return self.f[idx], s11, s21

    @property
    def rango_Hz(self):
        return float(self.f[0]), float(self.f[-1])

    def guardar(self, nombre):
        os.makedirs(DIR_CAL, exist_ok=True)
        datos = {'f': self.f}
        for k, (a, b) in self.brutos.items():
            datos[f'{k}_s11'], datos[f'{k}_s21'] = a, b
        np.savez_compressed(os.path.join(DIR_CAL, nombre + '.npz'), **datos)
        with open(os.path.join(DIR_CAL, nombre + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(self.info, fh, indent=2, ensure_ascii=False)
        return os.path.join(DIR_CAL, nombre + '.npz')

    @classmethod
    def cargar(cls, nombre):
        d = np.load(os.path.join(DIR_CAL, nombre + '.npz'))
        brutos = {k: (d[f'{k}_s11'], d[f'{k}_s21']) for k in ESTANDARES if f'{k}_s11' in d}
        ruta_info = os.path.join(DIR_CAL, nombre + '.json')
        info = json.load(open(ruta_info, encoding='utf-8')) if os.path.exists(ruta_info) else {}
        return cls(d['f'], brutos, info)


def comprobar_estandar(paso, s11, s21, d):
    """Detecta un estándar mal puesto comparándolo con el OPEN ya medido.

    d: {'open_s11': ..., 'isoln_s21': ...} con lo medido hasta ahora.
    Devuelve (aviso o None, texto informativo).
    """
    m = np.abs(s11)
    if paso == 'open':
        return (None if np.median(m) > 0.05 else 'casi no hay reflexión: ¿está puesto el OPEN?'), \
            f'|Γ| mediano {np.median(m):.2f}'
    ref = d.get('open_s11')
    if ref is None:
        return 'mide primero el OPEN', ''
    rel = s11/ref
    mag = np.median(np.abs(rel))
    fase = np.degrees(np.median(np.abs(np.angle(rel))))
    texto = f'respecto al OPEN: |Γ| ×{mag:.2f}, desfase mediano {fase:.0f}°'
    if paso == 'short':
        if mag < 0.5:
            return 'refleja mucho menos que el OPEN: ¿está puesta la CARGA?', texto
        if fase < 90:
            return 'misma fase que el OPEN: ¿sigue puesto el OPEN?', texto
    if paso in ('load', 'isoln') and mag > 0.3:
        return 'refleja casi como OPEN/SHORT: ¿está puesta la CARGA de 50 Ω en CH0?', texto
    if paso == 'thru':
        if 'isoln_s21' in d and np.median(np.abs(s21)) < 10*np.median(np.abs(d['isoln_s21'])):
            return 'apenas llega señal a CH1: ¿está conectado el THRU entre CH0 y CH1?', texto
    return None, texto


def autocomprobacion(c):
    """Error máximo de los propios estándares corregidos (debe ser ~1e-15)."""
    return {k: float(np.max(np.abs(c.corregir(c.brutos[k][0])[0] - ideal)))
            for k, ideal in (('open', 1), ('short', -1), ('load', 0)) if k in c.brutos}


def listar():
    if not os.path.isdir(DIR_CAL):
        return []
    return sorted(n[:-4] for n in os.listdir(DIR_CAL) if n.endswith('.npz'))


def ahora():
    return datetime.datetime.now().isoformat(timespec='seconds')
