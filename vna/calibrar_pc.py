"""Calibración guiada guardada en el PC (no toca los slots del NanoVNA).

Con --equipo, en cada paso también se calibra el propio NanoVNA (101 puntos,
mismo rango, solo en RAM) para que luego se pueda guardar desde su menú.

Uso, un paso cada vez (entre pasos se cambian los estándares):
    python calibrar_pc.py iniciar <nombre> <f_inicio_MHz> <f_fin_MHz> <puntos> [--equipo]
    python calibrar_pc.py open | short | load      (estándar en CH0)
    python calibrar_pc.py isoln                    (cargas de 50 Ω en CH0 y CH1)
    python calibrar_pc.py thru                     (cable THRU entre CH0 y CH1)
    python calibrar_pc.py terminar                 (calcula y guarda)
    python calibrar_pc.py verificar [nombre]       (mide lo conectado en CH0 con la calibración)
"""
import os
import sys
import json

import numpy as np

import nanovna as nv
import calibracion as cal

SESION = os.path.join(cal.DIR_CAL, '_sesion.npz')
SESION_INFO = os.path.join(cal.DIR_CAL, '_sesion.json')


def cargar_sesion():
    if not os.path.exists(SESION_INFO):
        sys.exit('No hay ninguna calibración en curso: empieza con "iniciar".')
    info = json.load(open(SESION_INFO, encoding='utf-8'))
    d = dict(np.load(SESION)) if os.path.exists(SESION) else {}
    return info, d


def guardar_sesion(info, d):
    os.makedirs(cal.DIR_CAL, exist_ok=True)
    np.savez_compressed(SESION, **d)
    with open(SESION_INFO, 'w', encoding='utf-8') as fh:
        json.dump(info, fh, indent=2, ensure_ascii=False)


def comprobar(paso, s11, s21, d):
    """Detecta estándares equivocados comparando con el OPEN ya medido."""
    m = np.abs(s11)
    if paso == 'open':
        return None if np.median(m) > 0.05 else 'casi no hay reflexión: ¿está puesto el OPEN?'
    ref = d.get('open_s11')
    if ref is None:
        return 'mide primero el OPEN'
    rel = s11/ref
    mag = np.median(np.abs(rel))
    fase = np.degrees(np.median(np.abs(np.angle(rel))))
    print(f'  respecto al OPEN: |Γ| x{mag:.2f}, desfase mediano {fase:.0f}°')
    if paso == 'short':
        if mag < 0.5:
            return 'refleja mucho menos que el OPEN: ¿está puesta la CARGA?'
        if fase < 90:
            return 'misma fase que el OPEN: ¿sigue puesto el OPEN?'
    if paso in ('load', 'isoln') and mag > 0.3:
        return 'refleja casi como OPEN/SHORT: ¿está puesta la CARGA de 50 Ω en CH0?'
    if paso == 'thru':
        if 'isoln_s21' in d and np.median(np.abs(s21)) < 10*np.median(np.abs(d['isoln_s21'])):
            return 'apenas llega señal a CH1: ¿está conectado el THRU entre CH0 y CH1?'
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    accion = sys.argv[1].lower()

    if accion == 'iniciar':
        nombre, f_ini, f_fin, pts = sys.argv[2], float(sys.argv[3])*1e6, float(sys.argv[4])*1e6, int(sys.argv[5])
        tambien_equipo = '--equipo' in sys.argv
        with nv.NanoVNA() as vna:
            equipo = {'version': vna.version(), 'bandwidth': vna.comando('bandwidth'),
                      'edelay': vna.comando('edelay'), 'cal_en_equipo': vna.comando('cal')}
            if tambien_equipo:
                vna.fijar_barrido(f_ini, f_fin, cal.MAX_PUNTOS_SCAN)
                vna.comando('cal reset')   # solo RAM; los slots guardados no se tocan
        info = {'nombre': nombre, 'inicio': cal.ahora(), 'f_ini_Hz': f_ini, 'f_fin_Hz': f_fin,
                'puntos': pts, 'equipo': equipo, 'calibrar_equipo': tambien_equipo, 'medidos': []}
        guardar_sesion(info, {'f': cal.rejilla(f_ini, f_fin, pts)})
        print(f'Calibración "{nombre}": {f_ini/1e6:g}–{f_fin/1e6:g} MHz, {pts} puntos '
              f'({-(-pts//cal.MAX_PUNTOS_SCAN)} barridos por estándar).')
        if tambien_equipo:
            print(f'También se calibra el NanoVNA: {f_ini/1e6:g}–{f_fin/1e6:g} MHz, 101 puntos (RAM).')
        print('Equipo:', equipo)
        return

    if accion in cal.ESTANDARES:
        info, d = cargar_sesion()
        with nv.NanoVNA() as vna:
            s11, s21 = cal.medir_bruto(vna, d['f'])
            aviso = comprobar(accion, s11, s21, d)
            if aviso:
                print(f'NO se ha guardado {accion.upper()}: {aviso}')
                sys.exit(2)
            if info.get('calibrar_equipo'):
                vna.comando(f'cal {accion}')
                print('  NanoVNA:', vna.comando('cal'))
        d[f'{accion}_s11'], d[f'{accion}_s21'] = s11, s21
        info['medidos'] = sorted(set(info['medidos']) | {accion})
        guardar_sesion(info, d)
        print(f'{accion.upper()} guardado. Medidos: {info["medidos"]}')
        return

    if accion == 'terminar':
        info, d = cargar_sesion()
        faltan = [k for k in ('open', 'short', 'load') if k not in info['medidos']]
        if faltan:
            sys.exit(f'Faltan estándares: {faltan}')
        brutos = {k: (d[f'{k}_s11'], d[f'{k}_s21']) for k in info['medidos']}
        info['fin'] = cal.ahora()
        c = cal.Calibracion(d['f'], brutos, info)
        ruta = c.guardar(info['nombre'])
        # Auto-comprobación: los propios estándares corregidos
        for k, ideal in (('open', 1), ('short', -1), ('load', 0)):
            r, _ = c.corregir(brutos[k][0])
            print(f'  {k:5s} corregido: error máx {np.max(np.abs(r - ideal)):.2e}')
        if 'thru' in brutos:
            _, t = c.corregir(brutos['thru'][0], brutos['thru'][1])
            print(f'  thru  corregido: |S21| = {20*np.log10(np.median(np.abs(t))):.3f} dB')
        os.remove(SESION); os.remove(SESION_INFO)
        print(f'Calibración guardada en {ruta}')
        if info.get('calibrar_equipo'):
            with nv.NanoVNA() as vna:
                vna.comando('cal done')
                print('NanoVNA calibrado (solo RAM):', vna.comando('cal'), vna.barrido_actual())
        return

    if accion == 'verificar':
        nombre = sys.argv[2] if len(sys.argv) > 2 else cal.listar()[-1]
        c = cal.Calibracion.cargar(nombre)
        with nv.NanoVNA() as vna:
            f, s11, s21 = c.medir(vna)
        db = 20*np.log10(np.abs(s11))
        print(f'Con "{nombre}": |S11| mediana {np.median(db):.1f} dB, máx {db.max():.1f} dB '
              f'a {f[db.argmax()]/1e6:.1f} MHz, mín {db.min():.1f} dB')
        if s21 is not None:
            d21 = 20*np.log10(np.abs(s21))
            print(f'               |S21| mediana {np.median(d21):.1f} dB (máx {d21.max():.1f} dB)')
        return

    sys.exit(__doc__)


if __name__ == '__main__':
    main()
