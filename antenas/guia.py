"""Guía de uso de cada tipo para la interfaz: resumen, para qué sirve, parámetros básicos y ayuda de cada parámetro.

La interfaz (escritorio y web) muestra primero una galería de tipos y, al elegir uno, solo sus parámetros
**básicos**; el resto va bajo «Ajustes avanzados». Cada parámetro lleva un icono con su ayuda.

Al añadir un tipo o un parámetro: darle resumen y grupo aquí, decidir si es básico y escribir su ayuda (la de
`Parametro.ayuda` se usa si no hay una aquí). `herramientas/comprobar_guia.py`… no existe: lo comprueba
`comprobar()` de este módulo, que pasa en la CI con `comprobar_tipos.py`.
"""
from . import tipos

# Grupos de la galería, en orden: (clave, título, descripción)
GRUPOS = [
    ('portatil', 'Nodo portátil u omnidireccional', 'Radian en todas direcciones: para nodos Meshtastic, trackers y '
                 'equipos que se mueven. Compactas.'),
    ('directiva', 'Enlace fijo o directiva', 'Concentran la señal hacia un lado: para enlazar dos puntos lejanos o un '
                  'repetidor que apunta a un valle.'),
    ('sin_masa', 'Sin plano de masa', 'No dependen de la placa a la que se conectan: buenas para ir en un mástil o '
                 'separadas del equipo.'),
    ('rx', 'Solo recepción (RX)', 'Para escuchar sin amplificador: banda ancha (UWB, SDR, ADS-B) o polarización circular (GNSS). '
             'Cuentan la eficiencia y la ganancia más que el S11. Sin validar.'),
    ('experimental', 'Experimentales', 'Más nuevas o con problemas conocidos: mira el estado de cada una.'),
]

# Por tipo: grupo de la galería, resumen de una línea y parámetros básicos (el resto, en «Ajustes avanzados»)
TIPOS = {
    'monopolo_recto': ('portatil', 'Una tira recta sobre un plano de masa. La más predecible: la referencia para comparar.',
                       ['alto', 'integrada', 'placa_x', 'placa_y', 'posicion', 'masa', 'conector', 'ajuste']),
    'monopolo_meandro': ('portatil', 'Una tira en zigzag: más baja que la recta, para placas cortas.',
                         ['alto', 'vueltas', 'integrada', 'placa_x', 'placa_y', 'posicion', 'masa', 'conector', 'ajuste']),
    'monopolo_koch': ('portatil', 'Monopolo fractal de Koch: más compacto que el recto, con buena banda. Recomendado.',
                      ['alto', 'iteracion', 'integrada', 'placa_x', 'placa_y', 'posicion', 'masa', 'conector', 'ajuste']),
    'monopolo_sierpinski': ('portatil', 'Triángulo fractal de Sierpinski: mucho ancho de banda, tolera desajustes; con «Dos bandas», cubre LoRa de 868/915 MHz y 2,4 GHz.',
                            ['alto', 'iteracion', 'multibanda', 'masa', 'conector', 'ajuste']),
    'parche_rectangular': ('directiva', 'Parche sobre plano de masa: algo directivo (~5 dBi) y de banda estrecha.',
                           ['largo', 'ancho', 'alimentacion', 'conector', 'ajuste']),
    'yagi_boom': ('directiva', 'Yagi impresa con directores: 6–7 dBi hacia delante, en una placa plana.',
                  ['largo_brazo', 'directores', 'iteracion', 'alimentacion', 'conector', 'aligerado']),
    'panel_dipolos': ('directiva', 'Dipolos o bowtie sobre un reflector (segunda placa): 1 elemento o 2×2 / 4×4, '
                      'hasta 17 dBi para enlaces largos.',
                      ['tamano', 'elemento', 'largo_brazo', 'simetrico', 'desfase', 'plano_desfase', 'aligerado']),
    'dipolo': ('sin_masa', 'Dipolo impreso (recto o de Koch) con balun: no necesita masa, radiación simétrica.',
               ['largo_brazo', 'iteracion', 'alimentacion', 'conector']),
    'dipolo_bowtie': ('sin_masa', 'Dipolo de brazos triangulares (bowtie): más banda que el recto, sin masa y simétrica.',
                      ['largo_brazo', 'forma', 'alimentacion', 'conector']),
    'jpole_koch': ('sin_masa', 'J-pole con radiador de Koch: sin masa, se alimenta con coaxial. Para mástil.',
                   ['largo_radiador', 'iteracion', 'ajuste']),
    'monopolo_flecha': ('experimental', 'Punta de flecha de Sierpinski: una pista que rellena un triángulo. Curiosidad: adapta con la iteración 1, no con las demás.',
                        ['alto', 'iteracion', 'masa', 'conector']),
    'monopolo_hilbert': ('experimental', 'Curva de Hilbert: muy compacta, pero adapta mal sin red en π.',
                         ['lado', 'orden', 'masa', 'conector', 'ajuste']),
    'ifa': ('portatil', 'Antena F invertida (J-pole en F): monopolo plegado con cortocircuito a masa.',
            ['largo_brazo', 'altura', 'separacion_toma', 'multibanda', 'integrada', 'placa_x', 'placa_y', 'posicion', 'masa', 'conector']),
    'pifa': ('portatil', 'PIFA: F invertida con brazo ancho, más banda.',
             ['largo_brazo', 'altura', 'separacion_toma', 'masa', 'conector']),
    'dipolo_sleeve': ('sin_masa', 'Dipolo con manga: tira λ/4 y manga de masa λ/4 debajo.',
                      ['alto', 'masa', 'largo_masa', 'conector']),
    'vivaldi': ('directiva', 'Vivaldi antipodal: directiva hacia la boca, en perfil de banda ancha (~4 dBi) o de alta ganancia (~6 dBi).',
                ['perfil', 'ancho_apertura', 'largo_aleta', 'conector']),
    'colineal_dipolos': ('sin_masa', 'Dipolos en serie (U al vivo, U invertida a la malla) unidos por microstrip de λg: más ganancia omni.',
                         ['largo_brazo', 'elementos', 'inclinacion', 'modular', 'encaje', 'conector']),
    'parche_ranura': ('experimental', 'Parche con ranura en U: más banda que el rectangular. Sin validar.',
                      ['largo', 'ancho', 'ranura_ancho', 'ranura_largo', 'alimentacion', 'conector']),
    'parche_apilado': ('experimental', 'Parche con parásito acoplado (más banda), en la misma cara. En simulación no adapta.',
                       ['largo', 'ancho', 'parasito_hueco', 'alimentacion', 'conector']),
    'parche_circular': ('experimental', 'Parche de polarización circular con una sola entrada (GPS, Iridium). En simulación no adapta ni da polarización circular.',
                        ['largo', 'corte', 'diagonal', 'alimentacion', 'conector']),
    'parche_minkowski': ('experimental', 'Parche fractal de Minkowski: más pequeño que el rectangular, pero pierde más.',
                         ['largo', 'iteracion', 'alimentacion', 'conector', 'ajuste']),
    'array_parches': ('experimental', 'Array de 2×2 o 4×4 parches: mucha ganancia, pero sin terminar de validar.',
                      ['tamano', 'elemento', 'largo', 'conector', 'ajuste']),
    'colineal_coco': ('experimental', 'Colineal coaxial impresa: radia, pero las pérdidas del FR4 se comen la ganancia.',
                      ['largo_seccion', 'secciones']),
    'colineal_franklin': ('experimental', 'Colineal Franklin con horquillas: adapta, pero con poca banda y poca ganancia.',
                          ['largo_elemento', 'elementos', 'masa', 'conector']),
    'jpole': ('sin_masa', 'J-pole recta: adapta de 868 MHz a 2,4 GHz (ya viene con el hueco ampliado); la J-pole de Koch es más compacta.',
              ['largo_radiador', 'multibanda', 'ajuste']),
    'bucle': ('experimental', 'Bucle pequeño con condensador de sintonía: poco sensible a la mano o al cuerpo, pero estrecho y con eficiencia baja. Necesita la red en π.',
              ['lado', 'capacidad_pF', 'forma', 'ancho_placa', 'largo_masa', 'conector', 'ajuste']),
    'yagi_koch': ('experimental', 'Quasi-Yagi con dipolo de Koch: radia hacia atrás en simulación.',
                  ['largo_brazo', 'iteracion', 'directores', 'conector', 'ajuste', 'aligerado']),
    'array_fase': ('experimental', 'Dos dipolos bowtie con una línea de retardo en una rama: el haz se inclina como en una sectorial. Un solo conector. Sin validar.',
                   ['largo_brazo', 'separacion', 'desfase', 'conector']),
    'dipolo_plegado': ('sin_masa', 'Dipolo de lazo cerrado con transformador λ/4: más banda que el dipolo recto. Sin validar.',
                       ['largo', 'separacion', 'conector']),
    'moxon': ('directiva', 'Rectángulo de Moxon: dos elementos doblados, ~6 dBi y buena relación delante/atrás en poco espacio. Sin validar.',
              ['ancho', 'hueco', 'conector']),
    'lpda': ('directiva', 'Log-periódica: fila de dipolos de largo creciente, directiva y de banda ancha (más de una octava). Placa larga. Sin validar.',
             ['largo_brazo', 'elementos', 'tau', 'conector']),
    'antena_ranura': ('experimental', 'Ranura de λ/2 en la masa alimentada por microstrip: bidireccional, polarización lineal. Sin validar.',
                      ['largo_ranura', 'largo_stub', 'desplazamiento', 'conector']),
    'espiral': ('rx', 'Espiral de dos brazos con coaxial por detrás: polarización circular y banda ancha, bidireccional. Sin validar.',
                ['radio', 'ancho_pista', 'hueco', 'sentido']),
    'torniquete': ('rx', 'Dos dipolos cruzados de distinto largo con un coaxial en el centro: circular (GPS) sin red de fase. Sin validar.',
                   ['largo', 'asimetria', 'ancho_pista']),
    'monopolo_uwb': ('rx', 'Disco, elipse, octógono o rectángulo biselado sobre masa parcial: banda ancha (de ~2,4 a más de 8 GHz), casi omnidireccional. Simulado a 2,4 GHz.',
                     ['radio', 'relacion', 'hueco', 'largo_masa', 'forma', 'conector']),
    'uwb_cpw': ('rx', 'Monopolo de banda ancha con línea coplanar (sin plano trasero): más compacto que el de microstrip. Sin simular: falta el puerto coplanar.',
                ['radio', 'relacion', 'hueco', 'chaflan', 'forma', 'conector']),
    'parche_cp': ('rx', 'Parche cuadrado con dos alimentaciones y 90° de retardo: polarización circular para GPS o Iridium. Sin validar.',
                  ['lado', 'z_ramas', 'sentido', 'conector']),
    'array_serie': ('directiva', 'Parches en fila unidos por una línea: ~10–12 dBi sin red de reparto, banda estrecha. Sin validar.',
                    ['largo', 'ancho', 'elementos', 'paso', 'conector']),
    'antena_siw': ('directiva', 'Guía de onda SIW (filas de vías) con ranuras alternadas: ganancia alta y poca pérdida. Sin validar.',
                   ['ancho_guia', 'elementos', 'largo_ranura', 'desplazamiento', 'conector']),
    'diedro': ('experimental', 'Dipolo bowtie con los brazos doblados en V (tres placas soldadas). Sin validar.',
               ['largo_brazo', 'angulo_v', 'forma', 'conector']),
    'reflector_esquina': ('experimental', 'Dipolo delante de dos placas reflectoras en esquina: ~9–11 dBi sin red de alimentación. Tres placas; sin validar.',
                          ['largo_brazo', 'apertura_diedro', 'separacion', 'ancho_reflector', 'largo_reflector', 'conector']),
    'helice_normal': ('experimental', 'Hélice de modo normal en flex enrollado sobre una placa de masa: monopolo compacto. Sin validar.',
                      ['diametro', 'vueltas', 'altura', 'ancho_placa', 'largo_placa', 'conector']),
    'helice_cuadrifilar': ('rx', 'Hélice cuadrifilar en flex enrollado para GPS (circular): geometría y tira, sin simulación aquí.',
                           ['diametro', 'vueltas', 'altura', 'sentido']),
}

# Con «Ajuste tras fabricar» activado, estas opciones también son básicas
BASICOS_AJUSTE = ['red_pi', 'sobrelargo', 'tramos']

# Ayuda de cada parámetro (por nombre). AYUDAS_TIPO la cambia para un tipo concreto cuando el mismo nombre
# significa otra cosa. Sin entrada aquí se usa `Parametro.ayuda`.
AYUDAS = {
    'forma': 'Forma del radiador del monopolo plano: disco o elipse (más suave) u octógono (esquinas cortadas, algo más de banda alta).',
    'separacion_te': 'Distancia desde la T de reparto hasta las esquinas del parche. Más distancia deja sitio al meandro de retardo pero alarga las ramas iguales.',
    'paso': 'Distancia entre centros de parches vecinos en longitudes de onda guiada (λg). 1,0 los pone en fase hacia delante; menos o más inclina el haz.',
    'ancho_enlace': 'Ancho de la línea que une un parche con el siguiente: estrecha, para que casi no cargue al parche (impedancia alta).',
    'ancho_guia': 'Distancia entre ejes de las dos filas de vías. La frecuencia de corte es c / (2 · ancho · √εr); el diseño va a 1,35 veces esa frecuencia.',
    'paso_via': 'Distancia entre vías de la misma fila. Menos de 2,5 mm con vías de 0,8 mm: la pared no deja escapar la onda.',
    'ancho_taper': 'Ancho donde acaba la transición de la línea de 50 Ω a la guía: más ancho, mejor paso al modo de la guía.',
    'largo_taper': 'Largo de la transición de la línea de 50 Ω a la guía (~λg/2 de la línea).',
    'cola_excitado': 'Cola doblada de cada brazo del elemento excitado, hacia el reflector (~0,05 λ).',
    'cola_reflector': 'Cola doblada de cada extremo del reflector, hacia el elemento excitado (~0,06 λ).',
    'largo_ranura': 'Largo de la ranura: ~media onda efectiva (λ0/(2√((εr+1)/2))); la simulación la pide un ~20 % más larga.',
    'ancho_ranura': 'Ancho de la ranura: más ancha, más banda.',
    'largo_stub': 'Stub abierto de la línea tras cruzar la ranura (~λg/4): afina la adaptación.',
    'lado_masa': 'Lado del plano de masa en largos de ranura: con menos de ~1,5 el diagrama se deforma.',
    'radio': 'Radio exterior de la espiral: la frecuencia más baja es la que tiene una circunferencia de una λ efectiva.',
    'lado_centro': 'Lado del cuadrado central donde se suelda el coaxial (cabe el pad y el taladro).',
    'bisagra': 'Distancia del centro del dipolo a la unión de cada ala con la placa central. 0 la deja automática (el ancho del boom más 2 mm).',
    'ancho_reflector': 'Lado de cada placa reflectora paralelo al dipolo. Cuanto más ancha, menos radiación hacia atrás; ~1,2–1,5 λ.',
    'largo_reflector': 'Lado de cada placa reflectora que se aleja del vértice. ~1 λ en el aire.',
    'diametro': 'Diámetro del tubo sobre el que se enrolla la tira de flex. La tira mide π·D de ancho.',
    'sentido': 'Sentido de giro de la hélice (a derechas o a izquierdas). En la cuadrifilar decide el sentido de la polarización circular.',
    'largo_placa': 'Largo de la placa de masa y del conector SMA bajo la hélice.',
    'altura': 'Altura del brazo horizontal sobre el borde de la masa. Más alto: más banda, algo más grande.',
    'separacion_toma': 'Distancia entre el cortocircuito a masa y la toma de alimentación. Fija la impedancia.',
    'ancho_corto': 'Ancho de la tira que une el brazo a la masa (con una vía).',
    'ranura_ancho': 'Anchura de la ranura en U, como fracción del ancho del parche.',
    'ranura_largo': 'Profundidad de la ranura en U, como fracción del largo del parche.',
    'ranura_hueco': 'Ancho de las rendijas que forman la ranura en U.',
    'parasito_hueco': 'Hueco entre el parche y el parásito acoplado. Menos hueco: más acoplo y más banda.',
    'parasito_factor': 'Largo del parásito respecto al del parche (algo menor que 1 ensancha la banda).',
    'ancho_apertura': 'Ancho de la boca de la Vivaldi: fija la frecuencia más baja (~λ/2).',
    'largo_aleta': 'Largo de las aletas: más largo, más ganancia y más banda, y placa más larga.',
    'tasa': 'Tasa de la apertura exponencial de las aletas.',
    'abertura_interior': 'Separación entre las dos aletas en la boca, como fracción del ancho.',
    'largo_entrada': 'Línea de 50 Ω entre el conector y el primer dipolo.',
    'ancho_brazo': 'Ancho de las tiras que forman las patas de cada U.',
    'separacion_patas': 'Distancia de las patas de la U al eje, a cada lado de la línea central.',
    # tamaño principal (lo calcula «Ajustar tamaño a la frecuencia»)
    'alto': 'Altura del radiador. Es la medida que fija la frecuencia: más alto, frecuencia más baja. '
            '«Ajustar tamaño a la frecuencia» la calcula sola.',
    'lado': 'Lado del cuadrado que ocupa la curva. Fija la frecuencia: más grande, más baja. Lo calcula «Ajustar».',
    'largo': 'Largo resonante del parche: fija la frecuencia (más largo, más baja). Lo calcula «Ajustar».',
    'largo_brazo': 'Largo de cada brazo del dipolo. Fija la frecuencia: más largo, más baja. Lo calcula «Ajustar».',
    'largo_radiador': 'Largo del radiador: fija la frecuencia (más largo, más baja). Lo calcula «Ajustar».',
    'largo_seccion': 'Largo de cada tramo de media onda: fija la frecuencia. Lo calcula «Ajustar».',
    'largo_elemento': 'Largo de cada elemento de media onda: fija la frecuencia. Lo calcula «Ajustar».',
    # forma del radiador
    'iteracion': 'Nivel del fractal. Más iteración: antena más compacta, pero menos banda y algo menos de eficiencia. '
                 '0 = sin fractal (recto). Lo habitual es 1–2.',
    'orden': 'Orden de la curva de Hilbert: cada orden más pliega la pista y encoge la antena, a cambio de peor '
             'adaptación y simulaciones más lentas.',
    'angulo': 'Ángulo de los picos de la curva de Koch. 60° es la curva clásica; más ángulo pliega más la pista.',
    'apertura': 'Ángulo del vértice del triángulo. 60° es el clásico; más apertura da un triángulo más ancho y con más banda.',
    'cuello': 'Ancho de las uniones entre triángulos. Evita que se toquen solo por un vértice (conexión dudosa al '
              'fabricar y al simular).',
    'vueltas': 'Número de idas y vueltas del zigzag. Más vueltas: antena más baja, pero menos banda.',
    'ancho_meandro': 'Anchura del zigzag. Más ancho: más corto en altura, pero ocupa más placa.',
    'tramo_inicial': 'Tramo recto antes del zigzag, para separarlo del plano de masa.',
    'separacion': 'Distancia entre la curva y el borde del plano de masa.',
    'profundidad': 'Profundidad de las muescas del fractal de Minkowski (fracción del tercio del lado). Más profundas: '
                   'parche más pequeño para la misma frecuencia.',
    'ancho_pista': 'Ancho de la pista. Más ancha: algo más de ancho de banda y menos pérdidas; mínimo de fábrica 0,13 mm.',
    'ancho': 'Ancho del parche. Más ancho: más banda y algo más de ganancia; no cambia mucho la frecuencia.',
    'ancho_dipolo': 'Ancho de los brazos. Más ancho: más ancho de banda (y dipolo algo más corto).',
    # masa y placa
    'masa': 'Cómo se calcula el plano de masa (la «otra mitad» de un monopolo). «λ/4» es la recomendada; las '
            'compactas encogen la placa pero hacen la antena más sensible a lo que se conecte detrás.',
    'ancho_placa': 'Ancho del plano de masa (y de la placa) cuando la masa es manual.',
    'integrada': 'Sí: la antena es una esquina de la placa de tu producto. La placa tiene el tamaño que indiques, la masa ocupa '
                 'todo menos la zona de antena (sin cobre en ninguna capa) y el conector queda en el borde opuesto.',
    'placa_x': 'Ancho de la placa de tu producto. La IFA depende mucho de él: por debajo de λ/4 la antena pierde banda y eficiencia.',
    'placa_y': 'Alto de la placa de tu producto, contando la zona de antena. Lo que queda debajo de la zona es el plano de masa.',
    'posicion': 'Dónde va la antena en el borde superior de la placa: en una esquina o centrada.',
    'zona_x': 'Ancho del rectángulo reservado a la antena. 0 = lo que ocupa el radiador más el margen; si pones más, la zona crece.',
    'zona_y': 'Alto del rectángulo reservado a la antena. 0 = lo que ocupa el radiador más el margen.',
    'margen_zona': 'Cobre retirado alrededor del radiador, dentro de la zona de antena (en todas las capas).',
    'largo_masa': 'Largo del plano de masa cuando es manual. Por debajo de λ/4 la frecuencia sube y hay que alargar el radiador.',
    'margen_masa': 'Plano de masa que sobresale alrededor del parche. Con menos de ~λ/20 la radiación hacia atrás aumenta.',
    'contorno': 'Forma de la placa: rectangular o ajustada a la antena (esquinas redondeadas, menos FR4).',
    'margen_borde': 'Distancia mínima del cobre al borde de la placa (el fabricante no deja cobre pegado al canto).',
    'escalado': '«Proporcionales»: al cambiar de frecuencia, pistas, huecos y demás medidas se escalan con la longitud '
                'de onda. Pasa a «Manuales» en cuanto fijas una a mano, para no pisarla.',
    'conector': 'SMA de canto (para probar y medir) o IPEX/U.FL encima de la placa (para meterla en un equipo). «Pad de RF»: sin conector, '
                'solo un pad al final de la línea de 50 Ω con dos vías de masa al lado, para la línea de tu producto.',
    # alimentación
    'alimentacion': 'Cómo llega la señal al radiador. Cada tipo tiene sus opciones; mira los problemas conocidos de cada una.',
    'largo_alimentacion': 'Largo de la línea de 50 Ω desde el conector hasta la antena.',
    'muesca': 'Profundidad de la ranura de alimentación dentro del parche. 0 = la calcula el programa para 50 Ω.',
    'hueco_muesca': 'Hueco entre la línea y el parche a cada lado de la ranura.',
    'z_transformador': 'Impedancia del tramo λ/4 que adapta el dipolo a 50 Ω.',
    'separacion_plegado': 'Distancia entre los dos conductores del dipolo plegado.',
    'hueco': 'Separación entre las dos pistas en la alimentación.',
    'toma': 'Altura a la que se suelda el coaxial en el adaptador: más arriba, más impedancia.',
    'factor_adaptador': 'Corrige el largo del adaptador λ/4 calculado (1 = sin corrección).',
    # directivas
    'directores': 'Número de directores (elementos delante del dipolo). Más directores: más ganancia y haz más '
                  'estrecho, pero placa más larga.',
    'separacion_director': 'Distancia entre el dipolo y los directores, y entre directores.',
    'factor_director': 'Largo del primer director respecto al dipolo. Más corto que el dipolo para que dirija hacia delante.',
    'reduccion_director': 'Cada director mide (1 − este valor) veces el anterior.',
    'factor_reflector': 'Largo del reflector respecto al dipolo. Más largo que el dipolo para que refleje hacia delante.',
    'separacion_reflector': 'Distancia del reflector al dipolo. En la Yagi, lo habitual es 0,15–0,25 λ0; en el '
                            'panel, 0,25 λ0 (un cuarto de onda) da la máxima ganancia.',
    'unir_boom': 'Une los directores a la tira central: toda la antena queda a masa en continua (protege de la estática).',
    'ancho_boom': 'Ancho de la tira central (el «boom»), que hace de masa y lleva la línea.',
    'ancho_rama': 'Ancho de las tiras de la línea que alimenta el dipolo.',
    'hueco_cps': 'Hueco entre las dos tiras de la línea que alimenta el dipolo.',
    'alto_cps': 'Largo de la línea de dos tiras: también ajusta la adaptación.',
    'largo_balun': 'Distancia entre el divisor de la alimentación y el borde de la masa.',
    'ancho_rodeo': 'Anchura del rodeo de media onda que desfasa una rama (el balun).',
    'tamano': 'Número de elementos: 2 = 2×2 (4 elementos), 4 = 4×4 (16 elementos, ~4–5 dB más y placa 4 veces mayor).',
    'elemento': 'Forma de cada parche: rectangular o fractal de Minkowski.',
    'bajada': 'Distancia entre la red de alimentación y los parches.',
    'simetrico': 'Disposición de los dipolos. «Todos iguales» adapta mejor; la simétrica no corrige la inclinación del haz.',
    'reflector': 'Con reflector el panel radia solo hacia delante. Sin reflector radia por las dos caras (bidireccional), '
                 'no anula una segunda banda más baja, y la ganancia baja unos 3 dB.',
    'margen_reflector': 'Cuánto sobresale el reflector de la placa por cada lado. Más grande: menos radiación hacia atrás.',
    'margen_placa': 'Margen de la placa alrededor del cobre (deja sitio a los taladros de las esquinas).',
    'taladro_coaxial': 'Taladro por el que pasa el coaxial hasta el centro. 1,7 mm para RG-316 / RG-174.',
    # colineales
    'secciones': 'Número de tramos. Más tramos: más ganancia en teoría y antena más larga.',
    'elementos': 'Número de elementos de media onda sobre la base. Más elementos: más ganancia y antena más larga.',
    'ancho_exterior': 'Ancho de la tira ancha (la «malla»). Debe ser bastante más ancha que la estrecha: iguales no radian.',
    'factor_horquilla': 'Corrige el largo de las horquillas de desfase (1 = λ/4 calculado).',
    'hueco_horquilla': 'Hueco entre las dos ramas de cada horquilla.',
    # ajuste tras fabricar
    'ajuste': '«Ajustable» añade formas de corregir la frecuencia y la adaptación una vez fabricada: sobrelargo con '
              'marcas de corte, tramos con puentes y red en π. Recomendado para la primera tirada.',
    'red_pi': 'Tres huellas de componente en la línea de 50 Ω (una en serie, dos a masa) para adaptar la antena con '
              'bobinas y condensadores tras medirla. De fábrica: 0 Ω en serie y las otras vacías.',
    'componentes': 'Tamaño de las huellas de la red en π y de los puentes: 0603 es más fácil de soldar a mano.',
    'sobrelargo': 'La antena sale este % más larga (frecuencia más baja) y la serigrafía marca dónde cortar para subirla.',
    'marcas': 'Rayas en la serigrafía con la frecuencia, en MHz, que queda al cortar por cada una.',
    'tramos': 'Tramos sueltos al final del radiador. Cada puente que cierras alarga la antena y baja la frecuencia un paso.',
    'paso_tramo': 'Cuánto baja la frecuencia cada tramo (el programa lo agranda si el tramo no cabe físicamente).',
    'puente': 'Cómo se cierra cada tramo: con una gota de estaño o con una resistencia de 0 Ω.',
    # aligerado
    'aligerado': 'Ventanas sin FR4 entre el cobre y el borde: menos peso. Sin simular: sube algo la frecuencia.',
    'margen_aligerado': 'Distancia mínima entre las ventanas y el cobre.',
    'nervio': 'Ancho del marco del borde y de los nervios que quedan entre ventanas.',
}
AYUDAS_TIPO = {
    'array_parches': {'separacion': 'Distancia entre parches, en longitudes de onda. ~0,7–0,8 λ0 da la máxima ganancia '
                                    'sin lóbulos laterales grandes.',
                      'largo': 'Largo de cada parche: fija la frecuencia. Lo calcula «Ajustar».',
                      'iteracion': 'Iteración del fractal de Minkowski de cada parche (si el elemento es Minkowski).'},
    'panel_dipolos': {'separacion': 'Distancia entre dipolos, en longitudes de onda. ~0,75 λ0 da la máxima ganancia.',
                      'tamano': 'Número de elementos: 1 = uno solo sobre el reflector (sin red, ~7–9 dBi), 2 = 2×2 '
                                '(4 elementos) y 4 = 4×4 (16, ~4–5 dB más y placa 4 veces mayor).',
                      'elemento': 'Forma de cada elemento: dipolo recto, bowtie (triángulos) o bowtie de Sierpinski. '
                                  'La bowtie aguanta mejor los desajustes de frecuencia (más banda).',
                      'iteracion_s': 'Nivel del Sierpinski de cada brazo (solo con «Bowtie de Sierpinski»). '
                                     'Más iteración: más huecos, brazo más largo eléctricamente y algo menos de banda.'},
    'dipolo': {'hueco': 'Hueco entre los brazos en el centro, donde se suelda el coaxial (alimentación por coaxial).',
               'largo_alimentacion': 'Largo del balun impreso (la tira central): separa la antena del conector.',
               'alimentacion': 'Balun impreso: conector en el borde y una tira que hace de balun (todo en la placa). '
                               'Coaxial al centro: sueldas el coaxial directamente en el centro del dipolo.'},
    'colineal_dipolos': {'elementos': 'Número de dipolos en serie. Más dipolos: más ganancia y una placa más larga (4 a 2,4 GHz: ~31 cm). '
                                      'En FR4, más de 4 no suben la ganancia (las pérdidas de la línea se la comen).',
                         'modular': 'Una placa por dipolo, todas iguales: se piden tantas placas como dipolos (la primera con el SMA) y se sueldan por el canto '
                                    'sobre las aperturas de máscara. Sirve para fabricar a 868 MHz, donde la placa entera pasa de 80 cm.',
                         'forma': 'U: cada brazo son dos patas finas a los lados de la línea. Bowtie: un triángulo que ocupa el mismo ancho, con la punta en la línea; '
                                  'más banda por dipolo. Bowtie de Sierpinski: ese triángulo con huecos fractales. La frecuencia del tamaño inicial no está calibrada '
                                  'para la bowtie ni el Sierpinski: usa «Ajustar tamaño a la frecuencia».',
                         'iteracion_s': 'Nivel del Sierpinski de cada brazo (solo con «Bowtie de Sierpinski»). Más iteración: huecos más pequeños (cuidado con las reglas de '
                                        'fabricación) y un brazo eléctricamente más largo.',
                         'conexion': 'En serie: dipolos a lo largo de la línea, todos con el vivo arriba y la masa abajo, separados una longitud de onda. Alternada: array de dipolos '
                                     'bowtie (como el del dipolo bowtie) con los brazos a los lados de la línea, separados media longitud de onda y cada uno con los brazos cambiados de cara '
                                     '(el vivo de uno queda junto a la masa del siguiente): la inversión y el retardo se compensan y radian en fase. La placa es más corta, no lleva vías y '
                                     'el haz sale perpendicular a la placa, no omnidireccional. Solo con brazos bowtie o de Sierpinski y en una sola placa. Sin validar.',
                         'apertura': 'Ángulo total de cada triángulo de la bowtie (solo con la conexión alternada). Más apertura: brazo más ancho y más alto; si pasa de la '
                                     'separación entre dipolos, se tocan.',
                         'encaje': 'Muescas en el canto de los módulos. Lengüetas y ranuras: alinean las placas (no se desplazan ni giran al soldar). '
                                   'Cola de milano: además impiden que se separen tirando de ellas; se montan juntándolas en el plano de la placa y bajando una sobre otra. '
                                   'La ranura de JLC va fresada: ancho mínimo 1 mm.'},
    'dipolo_bowtie': {'ancho_flecha': 'Ancho de la pista de cada brazo con la forma «Flecha de Sierpinski» (una pista fina que rellena un triángulo).',
                      'forma': 'Bowtie: dos triángulos como brazos, más banda que el dipolo recto. Bowtie de Sierpinski: '
                               'triángulos con huecos fractales. La bowtie aguanta mejor los desajustes de frecuencia.',
                      'iteracion_s': 'Nivel del Sierpinski de cada brazo (solo con «Bowtie de Sierpinski»). '
                                     'Más iteración: más huecos y un brazo eléctricamente más largo.',
                      'hueco': 'Hueco entre los brazos en el centro, donde se suelda el coaxial (alimentación por coaxial).',
                      'largo_alimentacion': 'Largo del balun impreso (la tira central): separa la antena del conector.',
                      'alimentacion': 'Balun impreso: conector en el borde y una tira que hace de balun (todo en la placa). '
                                      'Coaxial al centro: sueldas el coaxial directamente en el centro del dipolo.'},
    'yagi_boom': {'alimentacion': 'Directa: el dipolo va tal cual; adapta alejando el reflector (placa más larga), y es '
                                  'la validada. Transformador λ/4: adapta con el reflector cerca, pero con banda estrecha. '
                                  'Dipolo plegado: en simulación radió hacia atrás.'},
    'parche_rectangular': {'alimentacion': 'Por el borde: la línea llega al borde del parche con un transformador λ/4 '
                                           '(más larga). Por ranura: la línea entra en el parche hasta el punto de 50 Ω '
                                           '(más compacta).'},
    'parche_circular': {'alimentacion': 'Por el borde: la línea llega al borde del parche con un transformador λ/4 '
                                        '(más larga). Por ranura: la línea entra en el parche hasta el punto de 50 Ω '
                                        '(más compacta).'},
    'parche_minkowski': {'alimentacion': 'Por el borde: la línea llega al borde del parche con un transformador λ/4 '
                                         '(más larga). Por ranura: la línea entra en el parche hasta el punto de 50 Ω '
                                         '(más compacta).'},
    'colineal_coco': {'hueco': 'Hueco en cada cruce entre tramos (las tiras se cruzan con dos vías).'},
    'jpole': {'hueco': 'Hueco entre los dos brazos del adaptador λ/4.'},
    'jpole_koch': {'hueco': 'Hueco entre los dos brazos del adaptador λ/4.'},
    'yagi_koch': {'masa': 'Plano de masa, que hace de reflector detrás del dipolo.',
                  'ancho_placa': 'Ancho mínimo de la placa y del reflector.'},
    'monopolo_hilbert': {'separacion': 'Distancia entre la curva y el borde del plano de masa.'},
}


def info_tipo(clave):
    """(grupo, resumen, básicos) de un tipo; los tipos sin entrada van a experimentales con todo básico."""
    if clave in TIPOS:
        return TIPOS[clave]
    return ('experimental', tipos.CATALOGO[clave].descripcion, [p.nombre for p in tipos.CATALOGO[clave].parametros])


def basicos(clave, p=None):
    """Nombres de los parámetros básicos del tipo con estos valores (con ajuste activado, también sus opciones)."""
    b = list(info_tipo(clave)[2])
    if p and int(p.get('ajuste', 0) or 0) == 1:
        b += BASICOS_AJUSTE
    return b


def ayuda(clave, parametro):
    """Texto de ayuda de un parámetro (Parametro es el objeto del catálogo)."""
    return (AYUDAS_TIPO.get(clave, {}).get(parametro.nombre) or AYUDAS.get(parametro.nombre) or parametro.ayuda
            or parametro.etiqueta)


def comprobar():
    """Errores de la guía: tipos sin entrada, básicos que no existen y parámetros sin ayuda propia."""
    errores = []
    for clave, t in tipos.CATALOGO.items():
        if clave not in TIPOS:
            errores.append(f'{clave}: sin entrada en guia.TIPOS (grupo, resumen y básicos)')
            continue
        nombres = {p.nombre for p in t.parametros}
        for b in TIPOS[clave][2]:
            if b not in nombres:
                errores.append(f'{clave}: el básico «{b}» no es un parámetro del tipo')
        for p in t.parametros:
            if not (AYUDAS_TIPO.get(clave, {}).get(p.nombre) or AYUDAS.get(p.nombre) or p.ayuda):
                errores.append(f'{clave}: el parámetro «{p.nombre}» no tiene ayuda')
    return errores
