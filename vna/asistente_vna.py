"""Operaciones del NanoVNA para el asistente de la interfaz (conectar, calibrar, comprobar y medir).

Todas abren y cierran el puerto en cada operación y pasan por un cerrojo, para que dos
botones no hablen con el equipo a la vez. Reglas: nunca se envía `save` (los slots C0–C4
del equipo no se tocan) y `medir_bruto` deja el barrido y el estado de calibración del
equipo como estaban.
"""
import threading

import numpy as np

import nanovna as nv
import calibracion as cal

CERROJO = threading.Lock()
F_MIN_HZ = 50e3
F_MAX_HZ = 2.7e9          # lo útil del NanoVNA-H con el firmware DiSlord (armónicos por encima de 1,5 GHz)


def info_equipo():
    """Puerto, versión, barrido y estado de calibración del equipo (solo lectura)."""
    puerto = nv.buscar_puerto()
    if puerto is None:
        raise RuntimeError('No se encuentra ningún NanoVNA por USB. Conéctalo y vuelve a intentarlo.')
    with CERROJO, nv.NanoVNA(puerto) as v:
        return {'puerto': v.puerto, 'version': ' '.join(v.version()), 'barrido': v.barrido_actual(),
                'cal': ' '.join(v.comando('cal'))}


def rango_sugerido(f_obj_Hz):
    """Rango de calibración para una antena: ±40 % de la frecuencia objetivo, dentro del equipo."""
    return max(F_MIN_HZ, 0.6*f_obj_Hz), min(F_MAX_HZ, 1.4*f_obj_Hz)


def info_calibracion(nombre):
    """(f_ini, f_fin, puntos, fecha) de una calibración guardada, o None."""
    try:
        c = cal.Calibracion.cargar(nombre)
    except Exception:
        return None
    return {'f_ini_Hz': float(c.f[0]), 'f_fin_Hz': float(c.f[-1]), 'puntos': len(c.f),
            'fecha': c.info.get('fin') or c.info.get('inicio', ''), 'estandares': sorted(c.brutos)}


class CalibracionGuiada:
    """Calibración OSL del S11 hecha paso a paso desde la interfaz y guardada en el PC."""
    PASOS = ('open', 'short', 'load')

    def __init__(self, nombre, f_ini_Hz, f_fin_Hz, puntos):
        if not (F_MIN_HZ <= f_ini_Hz < f_fin_Hz):
            raise ValueError('Rango de frecuencias no válido')
        self.nombre = nombre
        self.f = cal.rejilla(f_ini_Hz, f_fin_Hz, int(puntos))
        self.d = {}
        self.info = {'nombre': nombre, 'inicio': cal.ahora(), 'f_ini_Hz': float(f_ini_Hz),
                     'f_fin_Hz': float(f_fin_Hz), 'puntos': int(puntos), 'origen': 'interfaz', 'medidos': []}

    def medir(self, paso):
        """Mide un estándar. Devuelve (bien, texto). Si parece mal puesto no se guarda."""
        with CERROJO, nv.NanoVNA() as v:
            s11, s21 = cal.medir_bruto(v, self.f)
        aviso, texto = cal.comprobar_estandar(paso, s11, s21, self.d)
        if aviso:
            return False, aviso
        self.d[f'{paso}_s11'], self.d[f'{paso}_s21'] = s11, s21
        self.info['medidos'] = sorted(set(self.info['medidos']) | {paso})
        return True, texto

    def hechos(self):
        return [p for p in self.PASOS if f'{p}_s11' in self.d]

    def terminar(self):
        """Calcula y guarda la calibración. Devuelve (nombre, errores de la autocomprobación)."""
        faltan = [p for p in self.PASOS if p not in self.hechos()]
        if faltan:
            raise RuntimeError(f'Faltan estándares: {", ".join(faltan).upper()}')
        self.info['fin'] = cal.ahora()
        brutos = {p: (self.d[f'{p}_s11'], self.d[f'{p}_s21']) for p in self.PASOS}
        c = cal.Calibracion(self.f, brutos, self.info)
        c.guardar(self.nombre)
        return self.nombre, cal.autocomprobacion(c)


def verificar(nombre_cal):
    """Mide lo conectado (debe ser la CARGA) con la calibración: |S11| en dB (mediana y máximo)."""
    c = cal.Calibracion.cargar(nombre_cal)
    with CERROJO, nv.NanoVNA() as v:
        f, s11, _ = c.medir(v)
    db = 20*np.log10(np.maximum(np.abs(s11), 1e-9))
    return {'mediana_dB': float(np.median(db)), 'max_dB': float(db.max()), 'f_max_MHz': float(f[db.argmax()]/1e6)}


def medir(nombre_cal, f_min_Hz=None, f_max_Hz=None):
    """S11 corregido con la calibración del PC, solo en [f_min, f_max] si se indica."""
    c = cal.Calibracion.cargar(nombre_cal)
    lo, hi = c.rango_Hz
    f_min_Hz = max(lo, f_min_Hz) if f_min_Hz else None
    f_max_Hz = min(hi, f_max_Hz) if f_max_Hz else None
    with CERROJO, nv.NanoVNA() as v:
        f, s11, _ = c.medir(v, f_min_Hz, f_max_Hz)
    return f, s11
