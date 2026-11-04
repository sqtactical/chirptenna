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

    def corregir(self, s11m, s21m=None):
        d = s11m - self.ed
        s11 = d/(self.er + self.es*d)
        if s21m is None or self.et is None:
            return s11, None
        return s11, (s21m - self.ex)/self.et

    def medir(self, vna):
        """Mide con esta calibración. Devuelve (f, S11, S21 corregidos)."""
        s11m, s21m = medir_bruto(vna, self.f)
        s11, s21 = self.corregir(s11m, s21m)
        return self.f, s11, s21

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


def listar():
    if not os.path.isdir(DIR_CAL):
        return []
    return sorted(n[:-4] for n in os.listdir(DIR_CAL) if n.endswith('.npz'))


def ahora():
    return datetime.datetime.now().isoformat(timespec='seconds')
