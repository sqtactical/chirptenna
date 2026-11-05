"""Problemas conocidos de cada tipo de antena (lo encontrado al simular), para avisar en la interfaz.

`problemas(clave, parametros, f_MHz)` devuelve [(nivel, texto)] con nivel en
{'grave', 'aviso', 'info'}: 'grave' = con esta configuración no ha funcionado bien en simulación;
'aviso' = funciona con limitaciones; 'info' = falta validarlo. Mantener al día con README.md /
README.en.md («Problemas conocidos») y con las lecciones de CLAUDE.md.
"""

# Tipos validados en simulación también a 868 MHz (el resto solo a 2,4 GHz)
VALIDADOS_868 = {'monopolo_recto', 'monopolo_meandro', 'monopolo_koch'}

# Estado de cada tipo para el selector y la galería: (estado, comentario breve). Estados: 'validada' (en
# simulación), 'pendiente' (pendiente de validación) y 'no_funciona'. Mantener al día con FIJOS y los README.
ESTADO = {
    'monopolo_recto': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_meandro': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_koch': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_hilbert': ('no_funciona', 'No funciona sin red en π'),
    'monopolo_sierpinski': ('validada', 'Validada en simulación (2,4 GHz)'),
    'parche_rectangular': ('validada', 'Validada en simulación (banda estrecha)'),
    'parche_minkowski': ('pendiente', 'Pendiente de validación (eficiencia baja en FR4)'),
    'yagi_koch': ('no_funciona', 'No funciona: radia hacia atrás'),
    'yagi_boom': ('validada', 'Validada en simulación con elementos rectos'),
    'array_parches': ('pendiente', 'Pendiente de validación'),
    'panel_dipolos': ('validada', 'Validada en simulación (2,4 GHz)'),
    'dipolo': ('validada', 'Validada en simulación (recto, 2,4 GHz)'),
    'colineal_coco': ('pendiente', 'Pendiente de validación (poca ganancia en FR4)'),
    'colineal_franklin': ('no_funciona', 'No funciona: adapta mal'),
    'jpole': ('no_funciona', 'No funciona: adapta mal (usa la de Koch)'),
    'jpole_koch': ('validada', 'Validada en simulación (2,4 GHz)'),
}
ESTADO_TEXTO = {'validada': 'Validada', 'pendiente': 'Pendiente de validación', 'no_funciona': 'No funciona'}


def estado(clave):
    """(estado, comentario) del tipo; los tipos nuevos sin entrada cuentan como pendientes de validación."""
    return ESTADO.get(clave, ('pendiente', 'Pendiente de validación'))

# Problemas que no dependen de los parámetros
FIJOS = {
    'monopolo_meandro': [
        ('aviso', 'La frecuencia salta varios % con pequeños cambios del alto (ruido de malla con el meandro): '
                  'el ajuste puede necesitar más iteraciones. Con masa pequeña puede no llegar a −10 dB.'),
    ],
    'monopolo_hilbert': [
        ('grave', 'Resuena, pero sin red en π adapta muy mal (−2,7 dB a 2,4 GHz y −4,6 dB a 868 MHz en simulación). '
                  'Usar la versión ajustable con red en π. A 868 MHz cada simulación tarda más de 3 h.'),
    ],
    'monopolo_sierpinski': [
        ('info', 'Banda muy ancha: durante el ajuste el centro de banda puede saltar entre dos resonancias.'),
    ],
    'parche_rectangular': [
        ('aviso', 'Banda estrecha en FR4 de 1,6 mm (~36 MHz a 2,4 GHz): no cubre toda la ISM de 83,5 MHz. '
                  'Eficiencia ~47 % por las pérdidas del FR4.'),
    ],
    'parche_minkowski': [
        ('aviso', 'Eficiencia baja en FR4 (~33 % en la iteración 1) y banda estrecha (~41 MHz).'),
    ],
    'jpole': [
        ('grave', 'La J-pole recta resuena donde toca pero adapta mal (R ≈ 6–10 Ω): mover la toma no lo arregla. '
                  'Modelo en revisión; usar la J-pole de Koch.'),
    ],
    'yagi_koch': [
        ('grave', 'Radia hacia atrás (hacia el reflector) y adapta mal (−3,5 dB) en simulación. Experimental: '
                  'no fabricarla todavía.'),
    ],
    'yagi_boom': [
        ('aviso', 'Con alimentación directa, la Yagi solo adapta alejando el reflector (~0,39 λ0), lo que alarga la '
                  'placa. La versión probada: elementos rectos, 2 directores, 7,2 dBi.'),
    ],
    'array_parches': [
        ('aviso', 'Sin terminar de validar: el centro de la banda salta mucho con cambios pequeños y cada iteración '
                  'tarda horas; el ajuste no itera la frecuencia (una simulación y se mira la ganancia).'),
    ],
    'panel_dipolos': [
        ('info', 'En simulación el haz sale ~9° inclinado (3° en el 4×4); parece un artefacto de la simulación, '
                 'sin confirmar. El ajuste no itera la frecuencia.'),
    ],
    'colineal_coco': [
        ('aviso', 'Radia (D 4,7 dBi) pero las pérdidas del FR4 dejan la eficiencia en ~53 % y la ganancia en ~1,9 dBi: '
                  'no se nota la ganancia de colineal.'),
    ],
    'colineal_franklin': [
        ('grave', 'Adapta mal (−5,3 dB) y solo da ~1,8 dBi: no se consigue la ganancia de colineal. Experimental '
                  '(revisar las horquillas).'),
    ],
}


def problemas(clave, p=None, f_MHz=None):
    p = p or {}
    out = list(FIJOS.get(clave, []))
    it = int(p.get('iteracion', 0) or 0)
    if clave == 'yagi_boom':
        if it > 0:
            out.append(('grave', 'Con elementos de Koch la Yagi ha salido mal en simulación (adapta mal y radia más '
                                 'hacia atrás que hacia los directores). Usar elementos rectos (iteración 0).'))
        alim = int(p.get('alimentacion', 0) or 0)
        if alim == 1:
            out.append(('aviso', 'Con transformador λ/4: radia hacia delante, pero banda estrecha (~50 MHz) y '
                                 'eficiencia ~55 %.'))
        elif alim == 2:
            out.append(('grave', 'Con dipolo plegado ha salido radiando hacia atrás (F/B −3,6 dB) y con menos '
                                 'ganancia (5,6 dBi). Usar alimentación directa.'))
        if int(p.get('unir_boom', 0) or 0) == 1:
            out.append(('aviso', 'Con los directores unidos al boom la frecuencia salta entre modos durante el '
                                 'ajuste y adapta algo peor que con directores sueltos.'))
    if clave == 'parche_minkowski' and it >= 2:
        out.append(('grave', f'Iteración {it}: impedancia de borde muy baja (~14 Ω), S11 ≈ −5 dB y eficiencia ~23 % en '
                             'simulación (la ranura no lo arregla); la estimación del tamaño falla 10–40 %. '
                             'Usar la iteración 1.'))
    if clave == 'array_parches' and int(p.get('elemento', 0) or 0) == 1 and it >= 3:
        out.append(('aviso', 'Minkowski de iteración 3 en el array: los cuellos pueden quedar por debajo de las '
                             'reglas de fabricación.'))
    if clave == 'panel_dipolos' and int(p.get('simetrico', 0) or 0) == 1:
        out.append(('aviso', 'La disposición simétrica con cruce no corrige la inclinación del haz y empeora la '
                             'adaptación (−10 dB frente a −15,7 dB de la normal). Mejor «Todos iguales».'))
    if clave == 'dipolo' and it > 0:
        out.append(('info', 'Dipolo de Koch sin validar en simulación (el recto sí).'))
    if int(p.get('conector', 0) or 0) == 1 and clave.startswith('monopolo'):
        out.append(('aviso', 'Con IPEX el monopolo recto adaptó mal en simulación (−7 dB): la transición del pad '
                             'central está en revisión. Con SMA va bien.'))
    if int(p.get('aligerado', 0) or 0) == 1:
        out.append(('info', 'Los recortes de aligerado no se han simulado todavía: quitar FR4 sube algo la frecuencia. '
                            'Simúlala antes de fabricar.'))
    if f_MHz and abs(f_MHz - 2441.75)/2441.75 > 0.2 and clave not in VALIDADOS_868:
        out.append(('info', 'Este tipo solo se ha validado en simulación a 2,4 GHz: a otras frecuencias la estimación '
                            'puede fallar más. Simúlala.'))
    return out


AVISO_GENERAL = ('Todo lo validado hasta ahora es en simulación, con εr 4,5 para el FR4 de JLC: falta medir placas '
                 'fabricadas y la εr real con el cupón. Mide siempre antes de dar una antena por buena.')
