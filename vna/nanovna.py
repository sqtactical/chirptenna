"""Control de NanoVNA-H/H4 (firmware DiSlord 1.2.x) por USB serie.

El firmware expone una consola de texto: se envía "comando\\r", el equipo
devuelve el eco, la salida y el prompt "ch> ".
"""
import time

import numpy as np
import serial
from serial.tools import list_ports

VID_PID = (0x0483, 0x5740)   # STM32 Virtual COM Port
PROMPT = b'ch> '


def buscar_puerto():
    """Puerto COM del primer NanoVNA conectado, o None."""
    for p in list_ports.comports():
        if (p.vid, p.pid) == VID_PID:
            return p.device
    return None


class NanoVNA:
    # El timeout se fija una sola vez: en Windows, reconfigurar el puerto CDC
    # en caliente falla a veces con "el dispositivo no funciona" (error 31).
    def __init__(self, puerto=None, timeout=60.0):
        puerto = puerto or buscar_puerto()
        if puerto is None:
            raise RuntimeError('No se encuentra ningún NanoVNA conectado por USB')
        self.puerto = puerto
        for intento in range(4):
            try:
                self.ser = serial.Serial(puerto, 115200, timeout=timeout)
                break
            except serial.SerialException:
                if intento == 3:
                    raise
                time.sleep(1.0)
        self._sincronizar()

    def _sincronizar(self):
        """Vacía lo pendiente y espera un prompt limpio."""
        self.ser.reset_input_buffer()
        self.ser.write(b'\r')
        self.ser.read_until(PROMPT)
        self.ser.reset_input_buffer()

    def comando(self, cmd):
        """Envía un comando y devuelve sus líneas de salida (sin eco ni prompt)."""
        self.ser.write(cmd.encode() + b'\r')
        resp = self.ser.read_until(PROMPT)
        if not resp.endswith(PROMPT):
            raise TimeoutError(f'Sin respuesta completa a "{cmd}"')
        lineas = resp[:-len(PROMPT)].decode(errors='replace').splitlines()
        if lineas and lineas[0].strip() == cmd:
            lineas = lineas[1:]
        return [l.rstrip() for l in lineas if l.strip()]

    def version(self):
        return self.comando('version')

    def info(self):
        return self.comando('info')

    def barrido_actual(self):
        """(inicio_Hz, fin_Hz, puntos) del barrido configurado en el equipo."""
        v = self.comando('sweep')[0].split()
        return int(v[0]), int(v[1]), int(v[2])

    def fijar_barrido(self, inicio, fin, puntos):
        self.comando(f'sweep {int(inicio)} {int(fin)} {int(puntos)}')

    def medir(self, inicio, fin, puntos=101):
        """Barrido único. Devuelve (f [Hz], S11 complejo, S21 complejo)."""
        lineas = self.comando(f'scan {int(inicio)} {int(fin)} {int(puntos)} 7')
        datos = np.array([[float(x) for x in l.split()] for l in lineas])
        f = datos[:, 0]
        s11 = datos[:, 1] + 1j*datos[:, 2]
        s21 = datos[:, 3] + 1j*datos[:, 4]
        return f, s11, s21

    def listar_sd(self):
        """[(nombre, bytes)] de los ficheros de la tarjeta SD."""
        out = []
        for l in self.comando('sd_list'):
            partes = l.rsplit(' ', 1)
            if len(partes) == 2 and partes[1].isdigit():
                out.append((partes[0], int(partes[1])))
        return out

    def leer_sd(self, nombre):
        """Contenido binario de un fichero de la SD (solo lectura).

        El firmware responde: eco, 4 bytes con el tamaño (little endian), los
        datos en bruto y el prompt.
        """
        cmd = f'sd_read {nombre}'
        self.ser.write(cmd.encode() + b'\r')
        eco = self.ser.read_until(b'\n')
        if cmd.encode() not in eco:
            raise RuntimeError(f'Respuesta inesperada a sd_read: {eco!r}')
        tam = int.from_bytes(self.ser.read(4), 'little')
        datos = self.ser.read(tam)
        if len(datos) != tam:
            raise TimeoutError(f'Leídos {len(datos)} de {tam} bytes de {nombre}')
        self.ser.read_until(PROMPT)
        return datos

    def cerrar(self):
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cerrar()


def guardar_s1p(ruta, f, s11, comentario=''):
    """Touchstone 1 puerto, formato RI, referencia 50 Ω."""
    with open(ruta, 'w', encoding='utf-8') as fh:
        if comentario:
            for l in comentario.splitlines():
                fh.write(f'! {l}\n')
        fh.write('# HZ S RI R 50\n')
        for fi, s in zip(f, s11):
            fh.write(f'{fi:.0f} {s.real:.6e} {s.imag:.6e}\n')
