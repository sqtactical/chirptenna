"""Problemas conocidos de cada tipo de antena (lo encontrado al simular), para avisar en la interfaz.

`problemas(clave, parametros, f_MHz)` devuelve [(nivel, texto)] con nivel en
{'grave', 'aviso', 'info'}: 'grave' = con esta configuración no ha funcionado bien en simulación;
'aviso' = funciona con limitaciones; 'info' = falta validarlo. Mantener al día con README.md /
README.en.md («Problemas conocidos») y con las lecciones de CLAUDE.md.
"""
from .i18n import tr

# Tipos validados en simulación también a 868 MHz (el resto solo a 2,4 GHz)
VALIDADOS_868 = {'monopolo_recto', 'monopolo_meandro', 'monopolo_koch', 'monopolo_sierpinski', 'jpole_koch', 'dipolo', 'dipolo_bowtie',
                 'yagi_boom', 'colineal_franklin'}

# Estado de cada tipo para el selector y la galería: (estado, comentario breve). Estados: 'validada' (en
# simulación), 'pendiente' (pendiente de validación) y 'no_funciona'. Mantener al día con FIJOS y los README.
ESTADO = {
    'monopolo_recto': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_meandro': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_koch': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'monopolo_hilbert': ('no_funciona', 'No funciona sin red en π'),
    'monopolo_flecha': ('pendiente', 'Sin testear ni validar (curiosidad)'),
    'monopolo_sierpinski': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
    'parche_rectangular': ('validada', 'Validada en simulación (banda estrecha)'),
    'parche_minkowski': ('pendiente', 'Pendiente de validación (eficiencia baja en FR4)'),
    'parche_circular': ('pendiente', 'Sin testear ni validar'),
    'parche_ranura': ('pendiente', 'Sin testear ni validar'),
    'parche_apilado': ('pendiente', 'Sin testear ni validar'),
    'ifa': ('pendiente', 'Sin testear ni validar'),
    'pifa': ('pendiente', 'Sin testear ni validar'),
    'dipolo_sleeve': ('pendiente', 'Sin testear ni validar'),
    'vivaldi': ('pendiente', 'Sin testear ni validar'),
    'colineal_dipolos': ('pendiente', 'Sin testear ni validar'),
    'yagi_koch': ('no_funciona', 'No funciona: radia hacia atrás'),
    'yagi_boom': ('validada', 'Validada en simulación con elementos rectos (2,4 GHz y 868 MHz)'),
    'array_parches': ('pendiente', 'Pendiente de validación'),
    'panel_dipolos': ('validada', 'Validada en simulación (2×2 con dipolos o Sierpinski, 2,4 GHz)'),
    'dipolo': ('validada', 'Validada en simulación (recto y Koch; 2,4 GHz y 868 MHz)'),
    'dipolo_bowtie': ('validada', 'Validada en simulación (bowtie y bowtie de Sierpinski; 2,4 GHz y 868 MHz)'),
    'colineal_coco': ('pendiente', 'Pendiente de validación (poca ganancia en FR4; a 868 MHz no sirve)'),
    'colineal_franklin': ('pendiente', 'Adapta, pero con poca banda y poca ganancia'),
    'jpole': ('pendiente', 'Casi adapta (−8 a −9 dB): mejor la de Koch'),
    'jpole_koch': ('validada', 'Validada en simulación (2,4 GHz y 868 MHz)'),
}
ESTADO_TEXTO = {'validada': 'Validada', 'pendiente': 'Pendiente de validación', 'no_funciona': 'No funciona'}


def estado(clave):
    """(estado, comentario) del tipo; los tipos nuevos sin entrada cuentan como pendientes de validación."""
    return ESTADO.get(clave, ('pendiente', tr('Pendiente de validación')))

# Problemas que no dependen de los parámetros
FIJOS = {
    'monopolo_meandro': [
        ('aviso', 'La frecuencia salta varios % con pequeños cambios del alto (ruido de malla con el meandro): '
                  'el ajuste puede necesitar más iteraciones. Con masa pequeña puede no llegar a −10 dB.'),
    ],
    'monopolo_flecha': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido, y no se conoce ninguna antena publicada con esta curva. '
                  'Como el Hilbert, es una pista larga y fina (más cara de simular y sensible a la fabricación): el tamaño y la '
                  'longitud equivalente son una estimación sin calibrar.'),
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
    'ifa': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. El largo del brazo y la distancia de la toma al '
                  'cortocircuito no están calibrados; la toma fija la impedancia y hay que afinarla simulando.'),
    ],
    'pifa': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. Sobre una placa de 1,6 mm, el brazo ancho '
                  'da más banda que la F invertida fina, pero el tamaño y la toma no están calibrados.'),
    ],
    'dipolo_sleeve': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. Con el conector SMA, la manga de masa es el '
                  'segundo brazo; el cable puede radiar si la manga es corta (usa una ferrita al medir).'),
    ],
    'vivaldi': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. El tamaño de la boca y la tasa de apertura no '
                  'están calibrados; la transición de la línea a las aletas puede necesitar ajuste. A 868 MHz la placa '
                  'sale muy grande.'),
    ],
    'colineal_dipolos': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. La ganancia de apilar dipolos se la comen en parte '
                  'las pérdidas del FR4 en los tramos de microstrip (~0,05 dB/cm a 2,4 GHz); con muchos dipolos la '
                  'ganancia deja de crecer. La placa es larga. El cable coaxial real, pegado a la placa, no está modelado: '
                  'en la simulación la alimentación es la línea desde el borde.'),
    ],
    'parche_ranura': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. La ranura en U ensancha la banda, pero su '
                  'tamaño y posición no están calibrados y desplazan la frecuencia: simula y ajusta.'),
    ],
    'parche_apilado': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. Es un parásito acoplado en la misma cara, no un '
                  'apilado de verdad (que necesitaría una segunda placa). El hueco y el largo del parásito no están calibrados.'),
    ],
    'parche_circular': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. Ni el tamaño ni el corte de las esquinas están '
                  'calibrados, y no se ha comprobado la razón axial ni el sentido de giro (GPS e Iridium son de giro derecho). '
                  'La polarización circular solo se mantiene en un ancho de banda muy pequeño y el FR4 (εr ±2–3 %) la desajusta fácilmente.'),
    ],
    'parche_minkowski': [
        ('aviso', 'Eficiencia baja en FR4 (~33 % en la iteración 1, ganancia ~1 dBi) y banda estrecha (~36–41 MHz).'),
    ],
    'jpole': [
        ('aviso', 'La J-pole recta resuena donde toca pero apenas adapta (−8 a −9 dB a 2,4 GHz y 868 MHz en '
                  'simulación): mover la toma no lo arregla del todo. La J-pole de Koch adapta mejor.'),
    ],
    'yagi_koch': [
        ('grave', 'Radia hacia atrás (hacia el reflector) y adapta mal (−3,5 dB) en simulación. Experimental: '
                  'no fabricarla todavía.'),
    ],
    'yagi_boom': [
        ('aviso', 'Con alimentación directa, la Yagi solo adapta alejando el reflector (~0,39 λ0), lo que alarga la '
                  'placa. La versión probada: elementos rectos, 2 directores, 7,2 dBi (2,4 GHz y 868 MHz).'),
    ],
    'array_parches': [
        ('aviso', 'Sin terminar de validar: el centro de la banda salta mucho con cambios pequeños y cada iteración '
                  'tarda horas (17 M celdas en el 2×2); con el tamaño por defecto resuena un 16 % por debajo y la '
                  'eficiencia es ~22 %.'),
    ],
    'panel_dipolos': [
        ('info', 'El ajuste no itera la frecuencia (el S11 de la red corporativa es ondulado): el tamaño inicial está '
                 'calibrado con simulaciones 2×2 a 2,4 GHz; en otras bandas y en el 4×4, simúlala. Con la malla fina el '
                 'haz sale casi de frente (0–3°): la inclinación de 9° de antes era un artefacto de la malla. En el 2×2 de '
                 'Sierpinski las iteraciones 1, 2 y 3 dan lo mismo (≈12,6 dBi, mismo largo de brazo).'),
    ],
    'colineal_coco': [
        ('aviso', 'Radia (D 4,7 dBi) pero las pérdidas del FR4 dejan la eficiencia en ~53 % y la ganancia en ~1,9 dBi: '
                  'no se nota la ganancia de colineal. A 868 MHz sale peor (η 26 %, −2 dBi, S11 −7,8 dB): no la uses ahí.'),
    ],
    'colineal_franklin': [
        ('aviso', 'Adapta (−19 dB a 2,4 GHz, −35 dB a 868 MHz) pero con poca banda (62 y 23 MHz) y solo 2,2–2,8 dBi: '
                  'no se nota la ganancia de colineal. Experimental.'),
    ],
}


def problemas(clave, p=None, f_MHz=None):
    p = p or {}
    out = list(FIJOS.get(clave, []))
    it = int(p.get('iteracion', 0) or 0)
    if clave == 'yagi_boom':
        if it > 0:
            out.append(('grave', tr('Con elementos de Koch la Yagi ha salido mal en simulación (adapta mal y radia más '
                                 'hacia atrás que hacia los directores). Usar elementos rectos (iteración 0).')))
        alim = int(p.get('alimentacion', 0) or 0)
        if alim == 1:
            out.append(('aviso', tr('Con transformador λ/4: radia hacia delante, pero banda estrecha (~50 MHz) y '
                                 'eficiencia ~55 %.')))
        elif alim == 2:
            out.append(('grave', tr('Con dipolo plegado ha salido radiando hacia atrás (F/B −3,6 dB) y con menos '
                                 'ganancia (5,6 dBi). Usar alimentación directa.')))
        if int(p.get('unir_boom', 0) or 0) == 1:
            out.append(('aviso', tr('Con los directores unidos al boom la frecuencia salta entre modos durante el '
                                 'ajuste y adapta algo peor que con directores sueltos.')))
    if clave == 'parche_minkowski' and it >= 2:
        out.append(('grave', tr('Iteración {0}: eficiencia ~30 % y ganancia < 1 dBi en simulación (adapta, pero casi no radia); la estimación del tamaño falla 10–40 %. Usar la iteración 1.', it)))
    if clave == 'array_parches' and int(p.get('elemento', 0) or 0) == 1 and it >= 3:
        out.append(('aviso', tr('Minkowski de iteración 3 en el array: los cuellos pueden quedar por debajo de las '
                             'reglas de fabricación.')))
    if clave == 'panel_dipolos' and int(p.get('simetrico', 0) or 0) == 1:
        out.append(('aviso', tr('La disposición simétrica con cruce no corrige la inclinación del haz y empeora la '
                             'adaptación (−10 dB frente a −15,7 dB de la normal). Mejor «Todos iguales».')))
    if clave == 'dipolo' and it > 1:
        out.append(('info', tr('Dipolo de Koch: solo está simulada la iteración 1 (el recto, también).')))
    if clave == 'dipolo_bowtie':
        out.append(('info', tr('Bowtie y bowtie de Sierpinski (iteración 2): simulados a 2,4 GHz y 868 MHz, con más '
                               'banda que el dipolo recto; otras iteraciones de Sierpinski, sin calibrar.')))
    if clave == 'panel_dipolos' and int(p.get('tamano', 2) or 2) == 1:
        out.append(('aviso', tr('Panel de un solo elemento: el S11 salta mucho con el largo del brazo y con el '
                               'reflector (resuena lejos del objetivo con el tamaño por defecto). Simúlala y '
                               'ajústala antes de fabricar.')))
    if clave == 'panel_dipolos' and int(p.get('elemento', 0) or 0) == 1 and int(p.get('tamano', 2) or 2) >= 2:
        out.append(('info', tr('Panel con bowtie liso: en simulación adapta de forma más irregular que con dipolos '
                               'rectos o bowtie de Sierpinski (2,4 GHz).')))
    if int(p.get('conector', 0) or 0) == 1 and clave.startswith('monopolo'):
        out.append(('aviso', tr('Con IPEX el monopolo recto adaptó mal en simulación (−7 dB): la transición del pad '
                             'central está en revisión. Con SMA va bien.')))
    if int(p.get('aligerado', 0) or 0) == 1:
        if clave == 'yagi_boom':
            out.append(('info', tr('Yagi aligerada simulada a 2,4 GHz: la ganancia baja ~1,3 dBi (de 7,2 a 5,9) y hay '
                                   'que reajustar el reflector. Simúlala antes de fabricar.')))
        else:
            out.append(('info', tr('Los recortes de aligerado no se han simulado todavía: quitar FR4 sube algo la '
                                   'frecuencia. Simúlala antes de fabricar.')))
    if clave == 'monopolo_sierpinski' and int(p.get('multibanda', 0) or 0) == 1:
        out.append(('info', tr('Dos bandas: simulado solo con la banda baja en 869 MHz y la alta en 2,4 GHz (S11 de −13 y −11,6 dB, 2,2 y 4,5 dBi); '
                               'para otras parejas de bandas, simúlalo. Placa grande (~96 × 115 mm a 869 MHz).')))
    if f_MHz and f_MHz > 4000:
        out.append(('aviso', tr('5,8 GHz: sin simular ni validar. Las estimaciones de tamaño no están calibradas a esta '
                                'frecuencia y las pistas y huecos son muy pequeños. Simula y mide antes de fabricar.')))
        if clave in ('monopolo_hilbert', 'yagi_koch'):
            out.append(('grave', tr('A 5,8 GHz este tipo no se puede fabricar: la pista queda por debajo de lo que JLC '
                                    'admite o las piezas chocan en el DRC de KiCad. Usa otro tipo.')))
        out.append(('aviso', tr('Pérdidas a 5,8 GHz: el FR4 de JLC (tanδ 0,02) pierde del orden de 0,1 dB por cm de línea y '
                                'la eficiencia de la antena baja bastante; en arrays y paneles, la red de alimentación '
                                'puede sumar varios dB. Con RO4350B las pérdidas son mucho menores.')))
    elif f_MHz and 800 < f_MHz < 2600 and abs(f_MHz - 866.5)/866.5 > 0.02 and abs(f_MHz - 2441.75)/2441.75 > 0.02:
        out.append(('info', tr('Entre las frecuencias simuladas (868 MHz y 2,4 GHz): el tamaño se interpola y no se ha '
                               'simulado a esta frecuencia. Simúlala antes de fabricar.')))
        if 1500 < f_MHz < 1700:
            out.append(('aviso', tr('GPS e Iridium emiten con polarización circular y esta antena es lineal: pierdes '
                                    '~3 dB. Para recibir con buena sensibilidad hace falta un parche de polarización circular.')))
    elif f_MHz and abs(f_MHz - 2441.75)/2441.75 > 0.2 and clave not in VALIDADOS_868:
        out.append(('info', tr('Este tipo solo se ha validado en simulación a 2,4 GHz: a otras frecuencias la estimación '
                            'puede fallar más. Simúlala.')))
    return out


AVISO_GENERAL = ('Todo lo validado hasta ahora es en simulación, con εr 4,5 para el FR4 de JLC: falta medir placas '
                 'fabricadas y la εr real con el cupón. Mide siempre antes de dar una antena por buena.')
