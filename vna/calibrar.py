"""Calibración guiada SOL (puerto 1) del NanoVNA, solo en RAM.

Uso, un paso cada vez (entre pasos se cambia el estándar en el puerto 1):
    python calibrar.py preparar <f_inicio_MHz> <f_fin_MHz>
    python calibrar.py open | short | load
    python calibrar.py terminar
    python calibrar.py estado

Nunca se usa el comando "save": las calibraciones guardadas en el equipo no se
tocan. Al apagar y encender el NanoVNA vuelve a cargar la calibración guardada.
"""
import os
import sys

import numpy as np

import nanovna as nv

PASOS = ('open', 'short', 'load')


REF_OPEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas', 'cal_ref_open.npy')


def comprobar_estandar(vna, paso):
    """Lectura rápida de S11 para detectar un estándar equivocado.

    Tras "cal reset" la lectura es bruta y su escala absoluta no significa nada
    (en modo armónico sale atenuada ~10 dB), así que SHORT y LOAD se comparan
    punto a punto con la lectura del OPEN.
    Se restaura el barrido porque "scan" puede dejar fijado su número de puntos
    y la calibración se toma sobre el barrido configurado.
    """
    original = vna.barrido_actual()
    try:
        _, s11, _ = vna.medir(original[0], original[1], 11)
    finally:
        vna.fijar_barrido(*original)
    print(f'  S11 bruto: |Γ| medio={np.mean(np.abs(s11)):.3f}')
    if paso == 'open':
        if np.mean(np.abs(s11)) < 0.05:
            return 'no hay apenas reflexión: ¿está conectado el OPEN?'
        np.save(REF_OPEN, s11)
        return None
    if not os.path.exists(REF_OPEN):
        return 'falta la referencia del OPEN; mide primero el OPEN'
    ref = np.load(REF_OPEN)
    rel = s11/ref
    mag = np.mean(np.abs(rel))
    fase = np.degrees(np.mean(np.abs(np.angle(rel))))
    print(f'  Respecto al OPEN: |Γ| x{mag:.2f}, desfase {fase:.0f}°')
    if paso == 'short':
        if mag < 0.5:
            return 'refleja mucho menos que el OPEN: ¿está conectada la CARGA?'
        if fase < 90:
            return 'tiene la misma fase que el OPEN: ¿sigue conectado el OPEN?'
    if paso == 'load' and mag > 0.3:
        return 'refleja casi como el OPEN/SHORT: ¿está conectada la CARGA de 50 Ω?'
    return None


def main():
    accion = sys.argv[1].lower()
    with nv.NanoVNA() as vna:
        if accion == 'preparar':
            ini, fin = float(sys.argv[2])*1e6, float(sys.argv[3])*1e6
            vna.fijar_barrido(ini, fin, 101)
            vna.comando('cal reset')
            print(f'Barrido fijado a {ini/1e6:g}–{fin/1e6:g} MHz, 101 puntos. Calibración en RAM reiniciada.')
            print('Estado:', vna.comando('cal'))
        elif accion in PASOS:
            aviso = comprobar_estandar(vna, accion)
            if aviso:
                print(f'NO se ha medido {accion.upper()}: {aviso}')
                sys.exit(2)
            vna.comando(f'cal {accion}')
            print(f'{accion.upper()} medido. Estado:', vna.comando('cal'))
        elif accion == 'terminar':
            vna.comando('cal done')
            print('Calibración aplicada (solo RAM). Estado:', vna.comando('cal'))
            print('Barrido:', vna.barrido_actual())
        elif accion == 'estado':
            print('Estado:', vna.comando('cal'), '| Barrido:', vna.barrido_actual())
        else:
            sys.exit(__doc__)


if __name__ == '__main__':
    main()
