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
    ('experimental', 'Experimentales', 'Para probar y aprender: tienen problemas conocidos.'),
]

# Por tipo: grupo de la galería, resumen de una línea y parámetros básicos (el resto, en «Ajustes avanzados»)
TIPOS = {
    'monopolo_recto': ('portatil', 'Una tira recta sobre un plano de masa. La más predecible: la referencia para comparar.',
                       ['alto', 'masa', 'conector', 'ajuste']),
    'monopolo_meandro': ('portatil', 'Una tira en zigzag: más baja que la recta, para placas cortas.',
                         ['alto', 'vueltas', 'masa', 'conector', 'ajuste']),
    'monopolo_koch': ('portatil', 'Monopolo fractal de Koch: más compacto que el recto, con buena banda. Recomendado.',
                      ['alto', 'iteracion', 'masa', 'conector', 'ajuste']),
    'monopolo_sierpinski': ('portatil', 'Triángulo fractal de Sierpinski: mucho ancho de banda, tolera desajustes.',
                            ['alto', 'iteracion', 'masa', 'conector', 'ajuste']),
    'parche_rectangular': ('directiva', 'Parche sobre plano de masa: algo directivo (~5 dBi) y de banda estrecha.',
                           ['largo', 'ancho', 'alimentacion', 'conector', 'ajuste']),
    'yagi_boom': ('directiva', 'Yagi impresa con directores: 6–7 dBi hacia delante, en una placa plana.',
                  ['largo_brazo', 'directores', 'iteracion', 'alimentacion', 'conector', 'aligerado']),
    'panel_dipolos': ('directiva', 'Dipolos o bowtie sobre un reflector (segunda placa): 1 elemento o 2×2 / 4×4, '
                      'hasta 17 dBi para enlaces largos.',
                      ['tamano', 'elemento', 'largo_brazo', 'simetrico', 'aligerado']),
    'dipolo': ('sin_masa', 'Dipolo impreso (recto, de Koch o bowtie) con balun: no necesita masa, radiación simétrica.',
               ['largo_brazo', 'forma', 'iteracion', 'alimentacion', 'conector']),
    'jpole_koch': ('sin_masa', 'J-pole con radiador de Koch: sin masa, se alimenta con coaxial. Para mástil.',
                   ['largo_radiador', 'iteracion', 'ajuste']),
    'monopolo_hilbert': ('experimental', 'Curva de Hilbert: muy compacta, pero adapta mal sin red en π.',
                         ['lado', 'orden', 'masa', 'conector', 'ajuste']),
    'parche_minkowski': ('experimental', 'Parche fractal de Minkowski: más pequeño que el rectangular, pero pierde más.',
                         ['largo', 'iteracion', 'alimentacion', 'conector', 'ajuste']),
    'array_parches': ('experimental', 'Array de 2×2 o 4×4 parches: mucha ganancia, pero sin terminar de validar.',
                      ['tamano', 'elemento', 'largo', 'conector', 'ajuste']),
    'colineal_coco': ('experimental', 'Colineal coaxial impresa: radia, pero las pérdidas del FR4 se comen la ganancia.',
                      ['largo_seccion', 'secciones']),
    'colineal_franklin': ('experimental', 'Colineal Franklin con horquillas: adapta, pero con poca banda y poca ganancia.',
                          ['largo_elemento', 'elementos', 'masa', 'conector']),
    'jpole': ('experimental', 'J-pole recta: casi adapta (−8 a −9 dB); la J-pole de Koch es mejor.',
              ['largo_radiador', 'ajuste']),
    'yagi_koch': ('experimental', 'Quasi-Yagi con dipolo de Koch: radia hacia atrás en simulación.',
                  ['largo_brazo', 'iteracion', 'directores', 'conector', 'ajuste', 'aligerado']),
}

# Con «Ajuste tras fabricar» activado, estas opciones también son básicas
BASICOS_AJUSTE = ['red_pi', 'sobrelargo', 'tramos']

# Ayuda de cada parámetro (por nombre). AYUDAS_TIPO la cambia para un tipo concreto cuando el mismo nombre
# significa otra cosa. Sin entrada aquí se usa `Parametro.ayuda`.
AYUDAS = {
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
    'largo_masa': 'Largo del plano de masa cuando es manual. Por debajo de λ/4 la frecuencia sube y hay que alargar el radiador.',
    'margen_masa': 'Plano de masa que sobresale alrededor del parche. Con menos de ~λ/20 la radiación hacia atrás aumenta.',
    'contorno': 'Forma de la placa: rectangular o ajustada a la antena (esquinas redondeadas, menos FR4).',
    'margen_borde': 'Distancia mínima del cobre al borde de la placa (el fabricante no deja cobre pegado al canto).',
    'escalado': '«Proporcionales»: al cambiar de frecuencia, pistas, huecos y demás medidas se escalan con la longitud '
                'de onda. Pasa a «Manuales» en cuanto fijas una a mano, para no pisarla.',
    'conector': 'SMA de canto (para probar y medir) o IPEX/U.FL encima de la placa (para meterla en un equipo).',
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
    'dipolo': {'forma': 'Forma de los brazos: pista recta o de Koch (con la iteración de Koch), bowtie (dos '
                        'triángulos) o bowtie de Sierpinski. La bowtie aguanta mejor los desajustes de frecuencia.',
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
