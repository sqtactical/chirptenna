"""Consejos de diseño: generales de cada tipo y otros que dependen del diseño concreto.

consejos(antena, f_obj, banda) -> lista de (categoría, texto). Categorías: 'diseño',
'montaje', 'medida', 'banda'.
"""
from .i18n import tr
from .materiales import lambda0_mm
GENERALES = {
    'monopolo': [
        ('montaje', 'Deja sin cobre, en las dos caras, toda la zona del radiador (el recuadro de la huella). '
                    'Ni pistas, ni rellenos, ni vías debajo.'),
        ('montaje', 'Coloca la antena en un borde o esquina de la placa, con el radiador hacia fuera, y '
                    'lejos (≥ λ/10) de baterías, pantallas o piezas metálicas.'),
        ('montaje', 'Prevé una red en π (huellas 0402/0603: serie + dos a masa) junto a la alimentación para '
                    'ajustar la adaptación una vez fabricada.'),
        ('medida', 'Una carcasa de plástico baja la frecuencia un 2–5 %: mide y ajusta con la antena dentro.'),
    ],
    'yagi': [
        ('diseño', 'Los directores apuntan hacia donde quieres la ganancia. Más directores: más ganancia y haz '
                   'más estrecho, pero placa más larga y banda algo menor.'),
        ('diseño', 'Separación típica entre directores 0,15–0,3 λ0; los directores un 5–20 % más cortos que el dipolo.'),
        ('medida', 'Para medir la ganancia relativa, compara con un monopolo recto de referencia a la misma distancia.'),
    ],
    'parche': [
        ('diseño', 'El plano de masa debajo del parche debe ser continuo; sobresalir al menos 6 veces el grosor '
                   'del sustrato por cada lado.'),
        ('diseño', 'Más grosor de sustrato da más ancho de banda y eficiencia; en FR4 de 1,6 mm un parche a '
                   '2,4 GHz anda por un 2–3 % de banda y un 50–70 % de eficiencia.'),
        ('montaje', 'Radia hacia el lado del parche: no lo tapes con metal ni lo pegues a la carcasa.'),
    ],
    'jpole': [
        ('montaje', 'La J-pole no lleva plano de masa: suelda el coaxial en los pads de la toma (vivo al brazo '
                    'largo, malla al corto) y sácalo hacia abajo, siguiendo el eje del adaptador.'),
        ('montaje', 'Pon una ferrita (o unas vueltas del coaxial) justo bajo la toma: sin choque, la malla '
                    'radia y desplaza la resonancia.'),
        ('diseño', 'La altura de la toma ajusta la impedancia: súbela si el S11 queda en la zona de baja '
                   'impedancia de la carta de Smith y bájala si queda en la de alta.'),
        ('diseño', 'Diagrama omnidireccional en el plano perpendicular al radiador, con ~2 dBi; colócala vertical.'),
    ],
    'dipolo': [
        ('diseño', 'Diagrama omnidireccional en el plano perpendicular a los brazos, con ~2 dBi; para Meshtastic, '
                   'monta los brazos en vertical.'),
        ('montaje', 'Con coaxial al centro: vivo al brazo derecho y malla al izquierdo, y saca el cable '
                    'perpendicular a los brazos al menos λ/4 antes de doblarlo; una ferrita junto a la soldadura '
                    'evita que la malla radie.'),
        ('montaje', 'Con balun impreso: el boom (la tira de masa bajo la línea) forma parte del balun; no lo '
                    'recortes ni pongas cobre a sus lados.'),
    ],
    'colineal': [
        ('diseño', 'Omnidireccional con el haz aplastado hacia el horizonte: más tramos o elementos, más ganancia '
                   'pero haz vertical más estrecho y banda más estrecha. Móntala vertical.'),
        ('diseño', 'La alimentación va por un extremo: los tramos lejanos reciben menos corriente, así que '
                   'pasar de 4–5 tramos apenas gana.'),
        ('montaje', 'Ferrita (o choke de λ/4) en el cable junto al conector: sin ella, la malla radia y '
                    'desplaza la resonancia y el diagrama.'),
        ('medida', 'Mide con la antena vertical y lejos de mesas o paredes metálicas: es larga y la afecta todo '
                   'lo que tenga cerca.'),
    ],
    'array': [
        ('diseño', 'Separación entre parches 0,7–0,8 λ0: con más de ~0,9 λ0 aparecen lóbulos de difracción.'),
        ('diseño', 'Las pérdidas de la red crecen con el tamaño: en FR4, un 4×4 a 2,4 GHz pierde ~3,5 dB. '
                   'Para arrays grandes o a 5,8 GHz, considera RO4350B.'),
        ('montaje', 'Todas las líneas de la red deben ir sobre masa continua y lejos (≥ 3h) de los bordes de los parches.'),
    ],
    'panel': [
        ('montaje', 'Son dos piezas: la placa de dipolos y el reflector (la segunda placa que se exporta, o una chapa '
                    'de aluminio del mismo tamaño), unidas por las esquinas con separadores de nailon M3 del largo '
                    'de la separación. Nada de separadores ni tornillos metálicos.'),
        ('montaje', 'Alimentación por detrás: SMA hembra de panel en el taladro central del reflector y un tramo '
                    'recto de RG-316 hasta la placa. La malla, soldada al pad grande de la cara inferior; el '
                    'dieléctrico atraviesa el taladro y el vivo se suelda al pad pequeño de la cara superior.'),
        ('montaje', 'Disposición simétrica: tras el cruce de las vías, el cobre de la cara inferior de la mitad '
                    'izquierda va al vivo, no a masa. La malla solo se suelda al pad central; no unas ningún otro '
                    'cobre de la placa al reflector ni al coaxial.'),
        ('diseño', 'La separación placa–reflector ajusta la impedancia: medir y, si hace falta, cambiar el largo '
                   'de los separadores (±2–3 mm) antes de tocar nada más.'),
        ('diseño', 'El haz sale por el lado de los dipolos (lejos del reflector), con polarización paralela a los '
                   'brazos: para Meshtastic, monta el panel con los brazos en vertical.'),
        ('medida', 'Mide con la antena apuntando a un espacio despejado: un objeto delante, a menos de ~1 m, '
                   'cambia la adaptación.'),
    ],
}

POR_TIPO = {
    'yagi_koch': [('diseño', 'El plano de masa hace de reflector: debe ser eléctricamente más largo que el dipolo '
                             '(≈ λ0/2 de ancho o más); si es más estrecho actúa de director y el haz va hacia atrás.'),
                  ('montaje', 'No pongas cobre fuera del plano de masa (zona del dipolo y directores) en ninguna cara.')],
    'yagi_boom': [('diseño', 'El reflector debe ser un 5–10 % más largo que el dipolo y estar a 0,15–0,25 λ0; '
                             'acercarlo baja la impedancia y la eficiencia.'),
                  ('montaje', 'Saca el coaxial hacia atrás, por el lado del reflector, pegado al eje del boom; '
                              'una ferrita en el cable evita que la malla radie.'),
                  ('montaje', 'Sin cobre ajeno cerca de los elementos: la placa entera es antena.')],
    'monopolo_koch': [('diseño', 'Cada iteración de Koch reduce la altura, pero también la banda y la eficiencia; '
                                 'más allá de la iteración 3 apenas se gana.')],
    'monopolo_hilbert': [('diseño', 'El Hilbert es muy compacto pero sensible a la fabricación: mantén el hueco '
                                    'entre vueltas ≥ 2 veces el ancho de pista.')],
    'monopolo_sierpinski': [('diseño', 'Multibanda con bandas a razón ~2 (la apertura del triángulo las desplaza). '
                                       '868 MHz y 2,4 GHz están a razón 2,8: no cuadran con el Sierpinski clásico.')],
    'monopolo_meandro': [('diseño', 'En el meandro, los tramos horizontales se cancelan en parte: cuantas más vueltas, '
                                    'más compacto pero menos eficiente.')],
    'parche_minkowski': [('diseño', 'Las muescas de Minkowski reducen el parche un 10–25 % a costa de banda; '
                                    'la profundidad de la muesca es el parámetro que más influye.')],
}

BANDAS = {
    'EU 868': (863e6, 870e6),
    'ISM 2,4 GHz': (2400e6, 2483.5e6),
    'ISM 5,8 GHz': (5725e6, 5875e6),
    'ISM 915 MHz': (902e6, 928e6),
    'Radioaficionado 1,2 GHz': (1240e6, 1300e6),
    'GPS L1': (1565.42e6, 1585.42e6),
    'Iridium': (1616e6, 1626.5e6),
}


def consejos(antena, f_obj=None, banda=None):
    """banda: (f_inf, f_sup) en Hz de la banda que hay que cubrir, o None."""
    from .tipos import CATALOGO
    tipo = CATALOGO[antena.tipo]
    out = list(GENERALES.get(tipo.familia, [])) + list(POR_TIPO.get(antena.tipo, []))
    p, info = antena.parametros, antena.info
    sustrato = info.get('sustrato', '')
    f_est = info.get('f_estimada_MHz', 0)*1e6

    # Banda: centrar y comprobar cobertura
    if banda:
        lo, hi = banda
        centro = (lo + hi)/2
        if f_obj and abs(f_obj - centro)/centro > 0.005:
            out.insert(0, ('banda', tr('La banda va de {0:g} a {1:g} MHz: centra la antena en {2:g} MHz, no en {3:g} MHz.', lo/1e6, hi/1e6, centro/1e6, f_obj/1e6)))
        bw = info.get('ancho_banda_estimado')
        if bw:
            if bw['f_inf_MHz']*1e6 > lo or bw['f_sup_MHz']*1e6 < hi:
                out.insert(0, ('banda', tr('El ancho de banda estimado ({0:g} MHz) no cubre la banda de {1:g} MHz: pulsa «Ampliar ancho de banda» o cambia de tipo.', bw["MHz"], (hi - lo)/1e6)))
            elif (bw['MHz']*1e6)/(hi - lo) < 1.5:
                out.insert(0, ('banda', tr('Cubre la banda pero con poco margen: las tolerancias de fabricación '
                                        '(εr ±2–3 %) pueden sacarte de ella. Deja margen o prevé la red en π.')))
    # Sustrato
    if 'FR4' in sustrato and f_est > 3e9:
        out.append(('diseño', tr('Por encima de ~3 GHz el FR4 pierde bastante y su εr varía entre lotes: '
                              'considera RO4350B.')))
    if 'FR4' in sustrato:
        out.append(('medida', tr('La εr del FR4 de JLC está pendiente de medir con el cupón: la frecuencia real '
                              'puede moverse un ±2–3 %.')))
    if 'PTFE' in sustrato:
        out.append(('medida', tr('La εr y la tanδ del PTFE son las del laminador (sin medir) y JLC no publica tolerancias: '
                              'mide la frecuencia real con el cupón. Pide la placa en su servicio de alta frecuencia (2 capas, ENIG).')))
        if antena.tipo.startswith('parche') or antena.tipo == 'array_parches':
            out.append(('diseño', tr('El PTFE sube la eficiencia del parche (~90 % frente a ~47 % en FR4) pero no ensancha la banda: '
                                  'con 1,65 mm sigue en ~35 MHz a 2,4 GHz. Para más banda hace falta más grosor o más εr baja.')))
    if 'Flex' in sustrato:
        out.append(('diseño', tr('Flex de JLC: sin impedancia controlada, y una microstrip de 50 Ω saldría de ~0,06–0,12 mm. '
                              'Usa tipos con el coaxial soldado en la antena (dipolo, bowtie, J-pole) y las reglas «JLC alta frecuencia y flex (0,1 mm)».')))
        out.append(('montaje', tr('Se simula plana y sin coverlay: doblada o pegada a una superficie, la frecuencia cambia. '
                               'Ajusta la antena ya montada y respeta el radio de curvatura (≥ 6 veces el grosor).')))
    # Conector IPEX
    if antena.puerto.get('conector') == 1:
        out.append(('montaje', tr('IPEX / U.FL (MHF1, no MHF4): aguanta ~30 conexiones. El latiguillo de 1,13 mm pierde '
                               '~0,5 dB cada 10 cm a 2,4 GHz (~0,3 dB a 868 MHz): úsalo lo más corto posible.')))
        out.append(('medida', tr('Para medir con el NanoVNA hace falta un latiguillo IPEX–SMA: mídelo antes con '
                              'vna/medir_latiguillo.py y descuenta su retardo, o la frecuencia aparente se mueve.')))
    # Masa compacta
    if int(p.get('masa', 0)) in (2, 3) and tipo.familia == 'monopolo':
        out.append(('medida', tr('Con masa compacta el cable forma parte de la antena: mide con una ferrita en el '
                              'coaxial a 2–3 cm de la placa y sin tocar la placa.')))
    # Antena integrada en una placa (F3.2: IFA a 2,4 GHz en GPU: 25 × 40 mm 124 MHz de banda, 30 × 50 215 MHz, 50 × 80 278 MHz, 80 × 120 314 MHz)
    if info.get('integrada'):
        out.append(('diseño', tr('Antena integrada: la placa es parte de la antena. Simula con el tamaño real de tu placa y vuelve a ajustar si lo cambias '
                              'o si añades una batería o una carcasa metálica cerca de la zona de antena.')))
        f_hz = f_obj or info.get('f_estimada_MHz', 0)*1e6
        # 25 mm a 2,4 GHz = 0,2 λ (λ = 123 mm) ya da la mitad de banda que 30 mm: el aviso salta por debajo de 0,22 λ
        if antena.tipo == 'ifa' and f_hz and p.get('placa_x', 1e9) < 0.22*lambda0_mm(f_hz):
            out.append(('diseño', tr('Masa corta: con una placa tan estrecha la IFA pierde banda (a 2,4 GHz, ~125 MHz con 25 mm de ancho frente a ~215 MHz con 30 mm y ~300 MHz con 80 mm). '
                                  'Si la placa de tu producto es más grande, úsala entera.')))
        if antena.tipo == 'monopolo_meandro':
            out.append(('diseño', tr('El meandro adapta mal en una placa pequeña (en simulación, a 2,4 GHz y 868 MHz no llega a −10 dB con placas de hasta 80 × 120 mm): '
                                  'para una placa de producto, la IFA es la opción probada.')))
    # Iteraciones altas
    if int(p.get('iteracion', 0)) >= 3 and antena.tipo in ('monopolo_koch', 'yagi_koch'):
        out.append(('diseño', tr('Iteración 3 o más: los detalles son pequeños y la ganancia de tamaño, marginal; '
                              'la iteración 2 suele ser el mejor compromiso.')))
    if int(p.get('orden', 0)) >= 4:
        out.append(('diseño', tr('Hilbert de orden 4 o más: hueco entre vueltas muy pequeño; revisa las '
                              'comprobaciones de fabricación y la tolerancia de JLC.')))
    if int(p.get('directores', 0)) >= 5:
        out.append(('diseño', tr('Con {0} directores la Yagi gana poco por director extra (~0,5–1 dB) y la placa crece mucho.', int(p["directores"]))))
    if info.get('perdida_red_estimada_dB', 0) > 2.5:
        out.append(('diseño', tr('La red pierde ~{0:.1f} dB: con este sustrato el array grande compensa poco frente a uno más pequeño.', info["perdida_red_estimada_dB"])))
    return out
