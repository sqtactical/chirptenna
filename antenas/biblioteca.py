"""Biblioteca de diseños del usuario («Mis diseños»).

Cada diseño es una carpeta en `Documentos\\Chirptenna\\disenos\\<nombre>` (fuera del repositorio):

    diseno.json        tipo, parámetros, frecuencia, banda, sustrato, reglas, fechas y notas
    simulacion/        resultado.json + datos.npz de la última simulación guardada
    fabricacion/       placa KiCad, Gerber, DXF (exportados desde la interfaz)
    medidas/           <fecha>_<etiqueta>.s1p (NanoVNA o subidos) + medidas.json con sus notas

La ruta base se puede cambiar con la variable de entorno CHIRPTENNA_DISENOS.
"""
import os
import json
import time
import shutil

import numpy as np


def _documentos():
    """Carpeta «Documentos» real del usuario (puede estar movida a OneDrive)."""
    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            import uuid
            # FOLDERID_Documents
            guid = uuid.UUID('{FDD39AD0-238F-46AF-ADB4-6C85480369C7}')

            class GUID(ctypes.Structure):
                _fields_ = [('d1', wintypes.DWORD), ('d2', wintypes.WORD), ('d3', wintypes.WORD),
                            ('d4', ctypes.c_ubyte*8)]
            g = GUID(guid.fields[0], guid.fields[1], guid.fields[2],
                     (ctypes.c_ubyte*8).from_buffer_copy(guid.bytes[8:]))
            ruta = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(ruta)) == 0:
                valor = ruta.value
                ctypes.windll.ole32.CoTaskMemFree(ruta)
                if valor and os.path.isdir(valor):
                    return valor
        except Exception:
            pass
    for nombre in ('Documents', 'Documentos'):
        r = os.path.join(os.path.expanduser('~'), nombre)
        if os.path.isdir(r):
            return r
    return os.path.expanduser('~')


def carpeta_base():
    base = os.environ.get('CHIRPTENNA_DISENOS') or os.path.join(_documentos(), 'Chirptenna', 'disenos')
    os.makedirs(base, exist_ok=True)
    return base


def nombre_valido(nombre):
    """Nombre de carpeta seguro: letras, números, '-', '_' y '.' (sin '..')."""
    limpio = ''.join(c if (c.isalnum() or c in '-_.') else '_' for c in (nombre or '').strip())
    limpio = limpio.strip('._')
    return limpio or 'antena'


def carpeta(nombre, sub=None):
    r = os.path.join(carpeta_base(), nombre_valido(nombre))
    if sub:
        r = os.path.join(r, sub)
    return r


def existe(nombre):
    return os.path.exists(os.path.join(carpeta(nombre), 'diseno.json'))


def _escribir_json(ruta, datos):
    tmp = ruta + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2, default=float)
    os.replace(tmp, ruta)


def _leer_json(ruta, defecto=None):
    try:
        with open(ruta, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return defecto


def guardar(nombre, clave, parametros, sustrato, reglas, f_MHz, bw_MHz, notas=None, info=None):
    """Crea o actualiza un diseño. Conserva la fecha de creación (y las notas si no se pasan)."""
    nombre = nombre_valido(nombre)
    dir_ = carpeta(nombre)
    os.makedirs(dir_, exist_ok=True)
    ruta = os.path.join(dir_, 'diseno.json')
    previo = _leer_json(ruta, {}) or {}
    ahora = time.strftime('%Y-%m-%d %H:%M')
    datos = {
        'nombre': nombre,
        'tipo': clave,
        'parametros': {k: v for k, v in parametros.items() if not str(k).startswith('_')},
        'sustrato': sustrato,
        'reglas': reglas,
        'f_objetivo_MHz': float(f_MHz),
        'ancho_banda_MHz': float(bw_MHz),
        'notas': previo.get('notas', '') if notas is None else notas,
        'creado': previo.get('creado', ahora),
        'modificado': ahora,
    }
    if info:
        datos['resumen'] = {k: info[k] for k in ('f_estimada_MHz', 'placa_mm', 'ganancia_estimada_dBi',
                                                   'fr4_quitado_%') if k in info}
    _escribir_json(ruta, datos)
    return dir_


def cargar(nombre):
    return _leer_json(os.path.join(carpeta(nombre), 'diseno.json'))


def guardar_notas(nombre, notas):
    d = cargar(nombre)
    if d is None:
        return
    d['notas'] = notas
    d['modificado'] = time.strftime('%Y-%m-%d %H:%M')
    _escribir_json(os.path.join(carpeta(nombre), 'diseno.json'), d)


def listar():
    """Diseños guardados, del más reciente al más antiguo, con un resumen para la tabla."""
    base = carpeta_base()
    out = []
    for n in os.listdir(base):
        d = _leer_json(os.path.join(base, n, 'diseno.json'))
        if not d:
            continue
        sim = leer_simulacion(n, solo_resultado=True)
        out.append({
            'nombre': n,
            'tipo': d.get('tipo'),
            'f_objetivo_MHz': d.get('f_objetivo_MHz'),
            'modificado': d.get('modificado', ''),
            'simulado': None if not sim else sim.get('f_resonancia_MHz'),
            'medidas': len(medidas(n)),
            'fabricado': os.path.isdir(carpeta(n, 'fabricacion')),
            'notas': d.get('notas', ''),
        })
    out.sort(key=lambda x: x['modificado'], reverse=True)
    return out


def renombrar(viejo, nuevo):
    nuevo = nombre_valido(nuevo)
    if existe(nuevo):
        raise ValueError(f'Ya existe un diseño llamado «{nuevo}»')
    os.rename(carpeta(viejo), carpeta(nuevo))
    d = cargar(nuevo)
    if d:
        d['nombre'] = nuevo
        _escribir_json(os.path.join(carpeta(nuevo), 'diseno.json'), d)
    return nuevo


def archivar(nombre):
    """Aparta un diseño a `disenos/_archivados/` (no se borra nada)."""
    destino = os.path.join(carpeta_base(), '_archivados')
    os.makedirs(destino, exist_ok=True)
    final = os.path.join(destino, nombre_valido(nombre) + time.strftime('_%Y%m%d_%H%M%S'))
    shutil.move(carpeta(nombre), final)
    return final


# ---------------------------------------------------------------- simulación
def guardar_simulacion(nombre, carpeta_sim):
    """Copia el resultado de una simulación (resultado.json + datos.npz) al diseño."""
    dir_ = carpeta(nombre, 'simulacion')
    os.makedirs(dir_, exist_ok=True)
    for f in ('resultado.json', 'datos.npz', 'trabajo.json'):
        origen = os.path.join(carpeta_sim, f)
        if os.path.exists(origen):
            shutil.copy2(origen, os.path.join(dir_, f))
    return dir_


def leer_simulacion(nombre, solo_resultado=False):
    """(resultado, datos) de la simulación guardada, o None. Solo cuenta si terminó bien."""
    dir_ = carpeta(nombre, 'simulacion')
    r = _leer_json(os.path.join(dir_, 'resultado.json'))
    if not r or not r.get('ok'):
        return None
    if solo_resultado:
        return r
    ruta = os.path.join(dir_, 'datos.npz')
    if not os.path.exists(ruta):
        return None
    return r, dict(np.load(ruta))


# ---------------------------------------------------------------- medidas
def _indice_medidas(nombre):
    return os.path.join(carpeta(nombre, 'medidas'), 'medidas.json')


def guardar_medida(nombre, f, s11, origen, etiqueta='', notas=''):
    """Guarda un S11 medido como Touchstone (.s1p, RI, 50 Ω) en `medidas/` del diseño."""
    dir_ = carpeta(nombre, 'medidas')
    os.makedirs(dir_, exist_ok=True)
    marca = time.strftime('%Y%m%d_%H%M%S')
    base = marca + ('_' + nombre_valido(etiqueta) if etiqueta else '')
    fichero, n = base + '.s1p', 2
    while os.path.exists(os.path.join(dir_, fichero)):     # dos medidas en el mismo segundo
        fichero, n = f'{base}_{n}.s1p', n + 1
    ruta = os.path.join(dir_, fichero)
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write(f'! Chirptenna · diseño {nombre_valido(nombre)} · {origen}\n')
        if notas:
            fh.write('! ' + notas.replace('\n', ' ') + '\n')
        fh.write('# HZ S RI R 50\n')
        fh.write('\n'.join(f'{fi:.0f} {z.real:.6e} {z.imag:.6e}' for fi, z in zip(f, s11)) + '\n')
    indice = _leer_json(_indice_medidas(nombre), {}) or {}
    indice[fichero] = {'fecha': time.strftime('%Y-%m-%d %H:%M'), 'origen': origen, 'etiqueta': etiqueta,
                       'notas': notas}
    _escribir_json(_indice_medidas(nombre), indice)
    return ruta


def medidas(nombre):
    """[(fichero, metadatos)] de las medidas del diseño, de la más antigua a la más nueva."""
    dir_ = carpeta(nombre, 'medidas')
    if not os.path.isdir(dir_):
        return []
    indice = _leer_json(_indice_medidas(nombre), {}) or {}
    return [(f, indice.get(f, {})) for f in sorted(os.listdir(dir_)) if f.lower().endswith('.s1p')]


def leer_medida(nombre, fichero):
    from .ajuste import leer_s1p
    with open(os.path.join(carpeta(nombre, 'medidas'), os.path.basename(fichero)), encoding='utf-8',
              errors='replace') as fh:
        return leer_s1p(fh.read())
