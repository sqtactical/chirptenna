"""Textos y formatos que comparten la interfaz de escritorio (gui/app.py) y la versión web (web_api).

Solo datos y funciones puras: nada de NiceGUI ni de archivos, para que funcione también en el navegador.
"""
import time

from . import tipos
from . import __version__
from .i18n import tr

# Bandas de uso: (inicio, fin) en MHz. La antena se centra en el centro de la banda.
# Los canales LoRa sueltos van en «Otra» (centro + ancho)
BANDAS = {'433': (433.05, 434.79), '868': (863.0, 870.0), '915 ISM': (902.0, 928.0), 'LoRa 863–928 MHz': (863.0, 928.0), '1,2 GHz radioaficionado': (1240.0, 1300.0),
          'GPS L1': (1565.42, 1585.42), 'Iridium': (1616.0, 1626.5), '2,4 GHz': (2400.0, 2483.5),
          '5,8 GHz': (5725.0, 5875.0), 'Otra': None}

# Inscripciones de la serigrafía (cara inferior): (clave, texto en la interfaz), en el orden en que se imprimen
SERIGRAFIA_OPCIONES = [
    ('tipo', 'Tipo de antena y frecuencia'),
    ('nombre', 'Nombre del diseño'),
    ('sim', 'Resultado de la simulación (banda y ganancia), si está guardada'),
    ('licencia', 'Licencia CC BY-NC 4.0 (diseños que vayas a publicar)'),
    ('fecha', 'Fecha y versión del programa'),
]
LOGO_OPCIONES = {'grande': 'Grande (recomendado)', 'pequeno': 'Pequeño', 'ninguno': 'Sin logo'}
AVISO_SIN_LOGO = ('Sin problema, el logo es opcional y la placa es tuya. Si la compartes o la vendes, nos ayudaría '
                  'mucho que menciones Chirptenna (en la descripción, con un enlace al proyecto…). '
                  'Así más gente puede encontrarlo y mejorarlo. ¡Gracias!')
SERIGRAFIA_DEFECTO = {'logo': 'grande', 'tipo': True, 'nombre': False, 'sim': True, 'licencia': False, 'fecha': True,
                      'libre': ''}

ETIQUETAS_INFO = {
    'f_estimada_MHz': 'Frecuencia estimada [MHz]', 'precision_estimacion': 'Precisión de la estimación',
    'placa_mm': 'Placa de prueba [mm]', 'radiador_mm': 'Radiador [mm]', 'longitud_traza_mm': 'Longitud de pista [mm]',
    'ancho_linea_50ohm_mm': 'Línea de 50 Ω [mm]', 'perdida_red_estimada_dB': 'Pérdida de la red (estimada) [dB]',
    'ganancia_estimada_dBi': 'Ganancia estimada [dBi]', 'directividad_ideal_dBi': 'Directividad ideal [dBi]',
    'ganancia_tipica_dBi': 'Ganancia típica [dBi]', 'separacion_mm': 'Separación entre elementos [mm]',
    'largo_dipolo_mm': 'Largo del dipolo [mm]', 'largo_lambda4_mm': 'Tramos λ/4 de 70,7 Ω [mm]',
    'separacion_reflector_mm': 'Separación placa–reflector [mm]', 'reflector_mm': 'Reflector [mm]',
    'grosor_total_mm': 'Grosor del conjunto [mm]',
    'insercion_mm': 'Inserción de la alimentación [mm]', 'R_borde_estimada_ohm': 'R de borde estimada [Ω]',
    'transformador': 'Transformador λ/4', 'lineas_mm': 'Anchos de línea [mm]', 'retardo_balun_mm': 'Rodeo del balun [mm]',
    'sustrato': 'Sustrato', 'solape_pistas': 'Solape de pistas', 'avisos': 'Avisos',
    'masa_mm': 'Plano de masa [mm]', 'area_placa_cm2': 'Área de la placa [cm²]',
    'largos_directores_mm': 'Largo de los directores [mm]',
    'ancho_banda_estimado': 'Ancho de banda estimado (−10 dB)',
    'hueco_minimo_mm': 'Hueco mínimo [mm]', 'pista_minima_mm': 'Pista mínima [mm]',
    'f_sin_cortar_MHz': 'Frecuencia sin cortar [MHz]', 'muesca_mm': 'Profundidad de la ranura [mm]',
    'largo_adaptador_mm': 'Largo del adaptador λ/4 [mm]', 'altura_toma_mm': 'Altura de la toma [mm]',
    'ventanas_aligerado': 'Ventanas de aligerado', 'fr4_quitado_%': 'FR4 quitado [%]',
}


def formatear(v):
    """Valor de `antena.info` como texto corto para la tabla de resultados."""
    if isinstance(v, float):
        return f'{v:.3f}'.rstrip('0').rstrip('.')
    if isinstance(v, dict):
        return ', '.join(f'{k}: {formatear(x)}' for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return ' × '.join(formatear(x) for x in v) if all(isinstance(x, (int, float)) for x in v) else '; '.join(map(str, v))
    return str(v)


def filas_info(info):
    """[(etiqueta, valor)] de `antena.info` para mostrar (sin vacíos ni lo que se muestra aparte)."""
    filas = []
    for k, v in info.items():
        # «v in (None, [], {})» falla con números de numpy (compara elemento a elemento)
        vacio = v is None or (isinstance(v, (list, tuple, dict)) and len(v) == 0)
        if vacio or k in ('avisos', 'ancho_banda_estimado', 'ajuste'):
            continue
        filas.append((ETIQUETAS_INFO.get(k, k), formatear(v)))
    return filas


def banda_de(f_MHz, bw_MHz):
    """Nombre de la banda predefinida que coincide con (centro, ancho), o 'Otra'."""
    for n, b in BANDAS.items():
        if b and abs((b[0] + b[1])/2 - f_MHz) < 0.01 and abs((b[1] - b[0]) - bw_MHz) < 0.01:
            return n
    return 'Otra'


def parametros_visibles(clave, p):
    """Nombres de los parámetros que se muestran con estos valores (oculta los que no aplican)."""
    from . import ajuste
    tipo = tipos.CATALOGO[clave]
    masa_auto = int(p.get('masa', 0)) != 0
    ajustable = int(p.get('ajuste', 0)) == 1
    muesca = int(p.get('alimentacion', 0)) == 1 and tipo.familia == 'parche'
    aligerado = int(p.get('aligerado', 0)) == 1
    visibles = []
    for par in tipo.parametros:
        if masa_auto and par.nombre in tipos.PARAMS_SOLO_MANUAL:
            continue            # con masa automática el programa calcula estas medidas
        if not ajustable and par.nombre in ajuste.PARAMS_SOLO_AJUSTABLE:
            continue            # opciones de ajuste solo si la antena es ajustable
        if not muesca and par.nombre in ('muesca', 'hueco_muesca'):
            continue            # parches alimentados por el borde
        if muesca and par.nombre == 'largo_alimentacion':
            continue            # con ranura la línea solo cruza el margen de masa
        if int(p.get('reflector', 1)) == 0 and par.nombre in ('separacion_reflector', 'margen_reflector'):
            continue            # sin reflector no hay separación ni margen que ajustar
        if not aligerado and par.nombre in tipos.PARAMS_SOLO_ALIGERADO:
            continue            # medidas de las ventanas solo si se aligera
        visibles.append(par.nombre)
    return visibles


def lineas_serigrafia(s, clave, f_MHz, nombre='', resultado_sim=None):
    """Líneas de texto de la serigrafía según lo elegido (la primera es la que más importa).

    s: selección ({'tipo': bool, …, 'libre': str}); resultado_sim: resultado.json de la simulación guardada."""
    lineas = []
    if s.get('tipo'):
        lineas.append(f"{tr(tipos.CATALOGO[clave].nombre).split(' (')[0]} {f_MHz:g} MHz")
    if s.get('nombre') and nombre:
        lineas.append(nombre)
    if s.get('sim') and resultado_sim:
        r = resultado_sim
        banda_s = (f"{r['banda_MHz'][0]:g}-{r['banda_MHz'][1]:g} MHz" if r.get('banda_MHz')
                   else f"{r['f_resonancia_MHz']:g} MHz")
        lineas.append(f"sim {banda_s} {r['ganancia_dBi']:g} dBi")
    lineas += [t.strip() for t in (s.get('libre') or '').splitlines() if t.strip()]
    if s.get('licencia'):
        lineas.append('CC BY-NC 4.0')
    if s.get('fecha'):
        lineas.append(f"{time.strftime('%Y-%m')} v{__version__}")
    return lineas
