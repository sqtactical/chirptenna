"""Problemas conocidos de cada tipo de antena (lo encontrado al simular), para avisar en la interfaz.

`problemas(clave, parametros, f_MHz)` devuelve [(nivel, texto)] con nivel en
{'grave', 'aviso', 'info'}: 'grave' = con esta configuración no ha funcionado bien en simulación;
'aviso' = funciona con limitaciones; 'info' = falta validarlo. Mantener al día con README.md /
README.en.md («Problemas conocidos») y con las lecciones de CLAUDE.md.
"""
from .i18n import tr

# Tipos validados en simulación también a 868 MHz (el resto solo a 2,4 GHz)
VALIDADOS_868 = {'monopolo_recto', 'monopolo_meandro', 'monopolo_koch', 'monopolo_sierpinski', 'jpole', 'jpole_koch', 'dipolo', 'dipolo_bowtie',
                 'yagi_boom', 'colineal_franklin'}

# Estado de cada tipo para el selector y la galería: (estado, comentario breve). Estados: 'validada' (en
# simulación), 'pendiente' (pendiente de validación) y 'no_funciona'. Mantener al día con FIJOS y los README.
ESTADO = {
    'monopolo_recto': ('validada', 'Validada en simulación (de 868 MHz a 5,8 GHz)'),
    'monopolo_meandro': ('validada', 'Validada en simulación (de 868 MHz a 5,8 GHz)'),
    'monopolo_koch': ('validada', 'Validada en simulación (de 868 MHz a 5,8 GHz)'),
    'monopolo_hilbert': ('no_funciona', 'No funciona sin red en π'),
    'monopolo_flecha': ('validada', 'Validada en simulación a 2,4 GHz con la iteración 1 (las iteraciones 2 y 3 no adaptan)'),
    'monopolo_sierpinski': ('validada', 'Validada en simulación (de 868 MHz a 5,8 GHz)'),
    'parche_rectangular': ('validada', 'Validada en simulación (banda estrecha; a 5,8 GHz con ranura)'),
    'parche_minkowski': ('pendiente', 'Pendiente de validación (eficiencia baja en FR4)'),
    'parche_circular': ('no_funciona', 'No adapta ni da polarización circular en simulación (−4 a −6 dB, razón axial ≥ 6 dB)'),
    'parche_ranura': ('pendiente', 'Sin testear ni validar'),
    'parche_apilado': ('no_funciona', 'No adapta en simulación (−0,6 dB, η 7 %)'),
    'ifa': ('validada', 'Validada en simulación (868 MHz, 2,4 y 5,8 GHz)'),
    'pifa': ('validada', 'Validada en simulación (868 MHz, 2,4 y 5,8 GHz)'),
    'dipolo_sleeve': ('validada', 'Validada en simulación (de 868 MHz a 5,8 GHz)'),
    'vivaldi': ('validada', 'Validada en simulación (2,4 y 5,8 GHz)'),
    'colineal_dipolos': ('validada', 'Validada en simulación (2,4 GHz)'),
    'yagi_koch': ('no_funciona', 'No funciona: radia hacia atrás'),
    'yagi_boom': ('validada', 'Validada en simulación con elementos rectos (868 MHz, 2,4 y 5,8 GHz)'),
    'array_parches': ('pendiente', 'Pendiente de validación'),
    'panel_dipolos': ('validada', 'Validada en simulación (2×2 con dipolos o Sierpinski, 2,4 GHz)'),
    'dipolo': ('validada', 'Validada en simulación (recto y Koch; de 868 MHz a 5,8 GHz)'),
    'dipolo_bowtie': ('validada', 'Validada en simulación (bowtie y bowtie de Sierpinski; de 868 MHz a 5,8 GHz)'),
    'colineal_coco': ('no_funciona', 'No adapta bien ni radia con eficiencia en FR4 (−4 dB, η 24–35 %)'),
    'colineal_franklin': ('pendiente', 'Adapta, pero con poca banda y poca ganancia'),
    'jpole': ('validada', 'Validada en simulación a 868 MHz y 2,4 GHz (con el hueco ampliado); a 1,2 y 5,8 GHz no llega'),
    'jpole_koch': ('validada', 'Validada en simulación (868 MHz y 1,2 GHz; 2,4 GHz casi)'),
}
ESTADO_TEXTO = {'validada': 'Validada', 'pendiente': 'Pendiente de validación', 'no_funciona': 'No funciona'}


def estado(clave):
    """(estado, comentario) del tipo; los tipos nuevos sin entrada cuentan como pendientes de validación."""
    return ESTADO.get(clave, ('pendiente', tr('Pendiente de validación')))

# Problemas que no dependen de los parámetros
FIJOS = {
    'monopolo_recto': [
        ('info', 'Con el conector IPEX a 2,4 GHz la masa automática da −6,9 dB; con la masa manual (largo 25 mm, ancho 40 mm) '
                 'adapta (−14,6 dB, η 95 %).'),
        ('info', 'Con una placa en vez de una pista (monopolo de placa, sin masa bajo la placa) también adapta a 2,4 GHz: 3 mm de ancho '
                 '−12,9 dB (η 99 %), 6 mm −10,0 dB con 260 MHz de banda; no mejora a la pista fina.'),
    ],
    'dipolo': [
        ('aviso', 'Con brazos anchos de tipo parche no funciona: de 4 a 12 veces el ancho de pista da de −6,7 a −1,6 dB a 2,4 GHz y '
                  'de −5,8 a −2,2 dB a 5,8 GHz aun recentrando el largo. Para más banda usa el bowtie.'),
    ],
    'monopolo_meandro': [
        ('aviso', 'La frecuencia salta varios % con pequeños cambios del alto (ruido de malla con el meandro): '
                  'el ajuste puede necesitar más iteraciones. Con masa pequeña puede no llegar a −10 dB.'),
    ],
    'monopolo_flecha': [
        ('aviso', 'Simulada a 2,4 GHz: con la iteración 1 y la pista de 0,79 mm adapta (−15,9 dB, η 93 %, 2,2 dBi); las iteraciones 2 y 3 '
                  'no (−3 a −7 dB). No se conoce ninguna antena publicada con esta curva. El tamaño y la longitud equivalente son una '
                  'estimación sin calibrar. Sin medir.'),
    ],
    'monopolo_hilbert': [
        ('grave', 'Resuena, pero sin red en π adapta muy mal (−2,7 dB a 2,4 GHz y −4,6 dB a 868 MHz en simulación). '
                  'Usar la versión ajustable con red en π. A 868 MHz cada simulación tarda más de 3 h. Con orden 2 y pista de 0,2 mm el mejor es −1,4 dB a 2,4 GHz.'),
    ],
    'monopolo_sierpinski': [
        ('info', 'Banda muy ancha: durante el ajuste el centro de banda puede saltar entre dos resonancias.'),
    ],
    'parche_rectangular': [
        ('aviso', 'Banda estrecha en FR4 de 1,6 mm (~36 MHz a 2,4 GHz): no cubre toda la ISM de 83,5 MHz. '
                  'Eficiencia ~47 % por las pérdidas del FR4. A 5,8 GHz con alimentación por ranura (alimentacion = 1, ranura estimada) '
                  'adapta en toda la banda (−10,6 dB, η 60 %, 4,7 dBi); a 1,2 GHz no.'),
    ],
    'ifa': [
        ('info', 'Simulada a 868 MHz, 1,2 GHz, 2,4 y 5,8 GHz (−11 a −17 dB; −14 dB a 1,2 GHz con la altura y la toma ajustadas) con la toma y la altura centradas por simulación. '
                 'La toma fija la impedancia: afínala simulando. Sin medir.'),
        ('info', 'Con una segunda rama corta para la banda alta (herramienta herramientas/rama_dual.py, aún no está en la interfaz) '
                 'cubre 868 MHz y 2,4 GHz a la vez en simulación (−11,7 y −10,8 dB, η 79–82 %). Es estrecha: ajústala simulando.'),
    ],
    'pifa': [
        ('info', 'Simulada a 868 MHz, 1,2 GHz (−13,7 dB), 2,4 y 5,8 GHz (−12 a −22 dB, con más banda que la IFA fina) con la toma, la altura y '
                 'el ancho del brazo centrados por simulación. Sin medir.'),
    ],
    'dipolo_sleeve': [
        ('aviso', 'Simulada de 868 MHz a 5,8 GHz (−13 a −18 dB), sin medir. Con el conector SMA, la manga de masa es el '
                  'segundo brazo; el cable puede radiar si la manga es corta (usa una ferrita al medir).'),
    ],
    'vivaldi': [
        ('aviso', 'Simulada a 2,4 GHz (−18 dB, banda muy ancha) y a 5,8 GHz (−12,3 dB con la aleta de 69 mm y la tasa 4), sin medir; la transición de la línea a las aletas '
                  'puede necesitar ajuste. A 868 MHz la placa sale muy grande y no se ha simulado.'),
    ],
    'colineal_dipolos': [
        ('aviso', 'Simulada a 2,4 GHz (−12,7 dB, banda 2357–2520 MHz, 4,1 dBi, η 59 %) con el factor de línea por defecto (1,0: '
                  'acortar las líneas un 10 % empeora, −8,4 dB); a 5,8 GHz −13,8 dB con 4 elementos, factor de línea 1,1 y ancho de brazo ×1,05 (η 50 %, 3,5 dBi; con el factor 1,0, −7,7 dB). Las pérdidas del FR4 en los tramos de '
                  'microstrip (~0,05 dB/cm a 2,4 GHz) se comen parte de la ganancia: con RO4350B sube a 7 dBi, pero deja de adaptar. '
                  'La placa es larga. El cable coaxial real, pegado a la placa, no está modelado: en la simulación la alimentación '
                  'es la línea desde el borde.'),
    ],
    'parche_ranura': [
        ('aviso', 'Sin testear ni validar: no se ha simulado ni medido. La ranura en U ensancha la banda, pero su '
                  'tamaño y posición no están calibrados y desplazan la frecuencia: simula y ajusta.'),
    ],
    'parche_apilado': [
        ('aviso', 'Simulado a 2,4 GHz: no adapta (−0,6 dB, η 7 %) con ninguna variante del hueco (0,2 a 0,6 mm) ni del factor (0,94 a 0,98) '
                  'del parásito. Es un parásito acoplado en la misma cara, no un apilado de verdad (que necesitaría una segunda placa).'),
    ],
    'parche_circular': [
        ('grave', 'Simulado en GPS L1, 2,4 y 5,8 GHz: no llega a −10 dB en la banda (mejor −4,4 dB en RO4350B en GPS L1 y −5,9 dB '
                  'a 2,4 GHz) y la razón axial no baja de 6 dB (hace falta < 3 dB para polarización circular). Con FR4 la eficiencia '
                  'es del 4 al 44 %. La diagonal elige el sentido de giro (0: derecho, 1: izquierdo). La alimentación por el borde no '
                  'da polarización circular en estas pruebas: no usarlo para GPS.'),
    ],
    'parche_minkowski': [
        ('aviso', 'Eficiencia baja en FR4 (~33 % en la iteración 1, ganancia ~1 dBi) y banda estrecha (~36–41 MHz). En RO4350B η 76 % y '
                  '5,2 dBi, pero la banda es de solo ~19 MHz. A 5,8 GHz −8,5 dB.'),
    ],
    'jpole': [
        ('aviso', 'J-pole recta: a 868 MHz adapta (−12,9 dB, η 92 %, banda 841–879 MHz) con el hueco entre brazos ×5 (14 mm). '
                  'A 2,4 GHz también adapta (−10,9 dB, η 85 %) con el hueco ×6 (6 mm); a 1,2 GHz da como mucho −9,8 dB (hueco ×8) y a 5,8 GHz −6,5 dB: '
                  'la parte real se queda en ~20 Ω. La J-pole de Koch adapta mejor.'),
        ('info', 'Con dos J-pole unidas por un puente en la cara inferior (herramienta herramientas/jpole_dual.py, modo union; '
                 'aún no está en la interfaz) cubre 868 MHz y 2,4 GHz en simulación (−11,2 y −10,6 dB, η 63 % y 87 %), pero es '
                 'estrecha. Con radiadores de Koch no funciona (−5 dB como mucho).'),
    ],
    'jpole_koch': [
        ('info', 'Simulada a 868 MHz (−17,5 a −19,8 dB), 1,2 GHz (−10,6 dB con la toma 0,37 y el adaptador ×1,13) y 2,4 GHz '
                 '(−9,2 dB); a 5,8 GHz no adapta (−3 dB). Eficiencia del 89 al 94 %. Sin medir. A 868 MHz el Koch no acorta el '
                 'radiador: sale más grande que el recto.'),
    ],
    'yagi_koch': [
        ('grave', 'Radia hacia atrás (hacia el reflector) y adapta mal (−3,5 dB) en simulación. Experimental: '
                  'no fabricarla todavía.'),
    ],
    'yagi_boom': [
        ('aviso', 'Con alimentación directa, la Yagi solo adapta alejando el reflector (~0,39 λ0), lo que alarga la '
                  'placa. La versión probada: elementos rectos, 2 directores, 7,2 dBi (2,4 GHz y 868 MHz); a 5,8 GHz adapta con el haz '
                  'hacia delante (−16,4 dB, 5,9 dBi, η 74 %, con el reflector ×1,15).'),
        ('info', 'Con recortes de aligerado (aligerado = 1): a 868 MHz y a 5,8 GHz casi no cambia (−8,6 dB y −12,0 dB, η 87 % y 72 %; '
                 'la frecuencia sube un 6–8 %), pero a 2,4 GHz con el margen por defecto la adaptación cae a −2,3 dB y el haz se invierte; '
                 'con el margen a 6 mm da −6,0 dB, η 75 %, con el haz hacia delante. Simula siempre una Yagi aligerada antes de fabricarla.'),
    ],
    'array_parches': [
        ('aviso', 'Sin terminar de validar: el centro de la banda salta mucho con cambios pequeños y cada iteración '
                  'tarda horas (17 M celdas en el 2×2); con el tamaño por defecto resuena un 16 % por debajo y la '
                  'eficiencia es ~22 %. A 5,8 GHz, agrandado ×1,2, llega a −7,7 dB pero con η 12 %.'),
    ],
    'panel_dipolos': [
        ('info', 'El ajuste no itera la frecuencia (el S11 de la red corporativa es ondulado): el tamaño inicial está '
                 'calibrado con simulaciones 2×2 a 2,4 GHz; en otras bandas y en el 4×4, simúlala. Con la malla fina el '
                 'haz sale casi de frente (0–3°): la inclinación de 9° de antes era un artefacto de la malla. En el 2×2 de '
                 'Sierpinski las iteraciones 1, 2 y 3 dan lo mismo (≈12,6 dBi, mismo largo de brazo). A 2,4 GHz −10,1 dB con el reflector '
                 'a 0,125–0,163 λ y el brazo ×1,04; a 5,8 GHz −9,8 dB con el reflector a 0,175 λ y el brazo ×0,82. Con recortes de aligerado a 2,4 GHz, −7,8 dB '
                 '(la frecuencia sube un 3 %).'),
    ],
    'colineal_coco': [
        ('aviso', 'Radia (D 4,7 dBi) pero las pérdidas del FR4 dejan la eficiencia en ~53 % y la ganancia en ~1,9 dBi: '
                  'no se nota la ganancia de colineal. A 868 MHz sale peor (η 26 %, −2 dBi, S11 −7,8 dB): no la uses ahí. Con 2 a 6 secciones, otro ancho exterior y otro hueco, a 2,4 GHz el mejor da −4,1 dB y η 24–35 %.'),
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
            out.append(('aviso', tr('Con elementos de Koch: la iteración 1 adapta (−21 dB) pero radia hacia atrás; la iteración 2 '
                                 'a 2,4 GHz sí funciona con el haz hacia delante (−14,4 dB, η 81 %, con el reflector ×1,35 y '
                                 'el director ×0,76), pero con solo 2,6 dBi. Los elementos rectos dan más ganancia (iteración 0).')))
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
        out.append(('info', tr('Dos bandas: simulado con la banda baja en 868–870, 902–928 o 863–928 MHz y la alta en 2400–2483,5 MHz '
                               '(S11 de −10 a −13 dB en las dos, ~2 dBi abajo y ~4,5 dBi arriba); para otras bandas, simúlalo. '
                               'Placa grande (~96 × 115 mm).')))
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
