"""Interfaz gráfica del generador de antenas (NiceGUI, se abre en el navegador).

Uso: python gui/app.py   ->   http://localhost:8080
"""
import os
import sys
import json
import time
import threading
import subprocess

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nicegui import ui   # noqa: E402

from antenas import tipos, vista, fabricacion, exportar, consejos, graficas, ajuste   # noqa: E402
from antenas.materiales import ancho_microstrip, eps_eff_microstrip   # noqa: E402
from nicegui import run   # noqa: E402

sys.path.insert(0, os.path.join(RAIZ, 'vna'))   # driver del NanoVNA y calibración del PC
from antenas.simulacion import PRECISIONES   # noqa: E402
from antenas.materiales import SUSTRATOS, SUSTRATO_POR_DEFECTO   # noqa: E402

DIR_SALIDAS = os.path.join(RAIZ, 'salidas')
# Bandas de uso: (inicio, fin) en MHz. La antena se centra en el centro de la banda.
# Los canales LoRa sueltos van en «Otra» (centro + ancho)
BANDAS = {'433': (433.05, 434.79), '868': (863.0, 870.0), '2,4 GHz': (2400.0, 2483.5), 'Otra': None}

estado = {
    'clave': 'monopolo_koch',
    'sustrato': SUSTRATO_POR_DEFECTO,
    'reglas': fabricacion.REGLAS_POR_DEFECTO,
    'f_MHz': 2441.75,
    'bw_MHz': 83.5,
    'params': tipos.CATALOGO['monopolo_koch'].defectos(),
    'antena': None,
}


def _fmt(v):
    if isinstance(v, float):
        return f'{v:.3f}'.rstrip('0').rstrip('.')
    if isinstance(v, dict):
        return ', '.join(f'{k}: {_fmt(x)}' for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return ' × '.join(_fmt(x) for x in v) if all(isinstance(x, (int, float)) for x in v) else '; '.join(map(str, v))
    return str(v)


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
    'f_sin_cortar_MHz': 'Frecuencia sin cortar [MHz]', 'muesca_mm': 'Profundidad de la ranura [mm]', 'largo_adaptador_mm': 'Largo del adaptador λ/4 [mm]',
    'altura_toma_mm': 'Altura de la toma [mm]',
}
ICONOS_CONSEJO = {'banda': ('podcasts', 'deep-orange'), 'diseño': ('lightbulb', 'amber-8'),
                  'montaje': ('construction', 'blue-grey'), 'medida': ('straighten', 'teal')}


@ui.page('/')
def pagina():
    ui.add_css('.q-field__label { font-size: 0.82rem; }')
    with ui.header().classes('bg-blue-grey-9 items-center'):
        ui.label('Generador de antenas para PCB').classes('text-h6')
        ui.space()
        ui.label('Fase 1 · geometría, comprobaciones y exportación').classes('text-caption')

    with ui.row().classes('w-full wrap items-start gap-4 p-2'):
        # ---------------------------------------------------------- panel izquierdo
        with ui.column().classes('w-full sm:w-[380px] gap-2'):
            with ui.card().classes('w-full'):
                ui.label('Antena').classes('text-subtitle1 text-weight-medium')
                sel_tipo = ui.select({k: t.nombre for k, t in tipos.CATALOGO.items()}, value=estado['clave'],
                                     label='Tipo').classes('w-full')
                desc = ui.label().classes('text-caption text-grey-8')
                ui.label('Banda de uso').classes('text-caption q-mt-sm')
                banda = ui.toggle(list(BANDAS), value='2,4 GHz').classes('w-full')
                with ui.row().classes('items-center w-full no-wrap gap-2'):
                    f_in = ui.number('Centro [MHz]', value=estado['f_MHz'], min=100, max=10000, step=0.005,
                                     format='%.3f').classes('grow')
                    bw_in = ui.number('Ancho necesario [MHz]', value=estado['bw_MHz'], min=0.05, max=5000, step=0.05,
                                      format='%.2f').classes('grow')
                rango = ui.label().classes('text-caption text-grey-8')
                sel_sus = ui.select(list(SUSTRATOS), value=estado['sustrato'], label='Sustrato').classes('w-full')
                sel_reg = ui.select(list(fabricacion.REGLAS), value=estado['reglas'],
                                    label='Reglas de fabricación').classes('w-full')
                btn_ajustar = ui.button('Ajustar tamaño a la frecuencia', icon='tune').props('color=primary').classes('w-full')
                btn_bw = ui.button('Ampliar ancho de banda', icon='open_in_full').props('outline color=primary').classes('w-full')
                aviso_ajuste = ui.label().classes('text-caption text-orange-9')

            with ui.card().classes('w-full'):
                ui.label('Parámetros').classes('text-subtitle1 text-weight-medium')
                cont_params = ui.column().classes('w-full gap-0')

            with ui.card().classes('w-full'):
                ui.label('Exportar').classes('text-subtitle1 text-weight-medium')
                nombre_in = ui.input('Nombre', value='antena').classes('w-full')
                btn_export = ui.button('Exportar KiCad + Gerber + DXF', icon='download').props('color=positive').classes('w-full')
                res_export = ui.column().classes('w-full gap-1')

        # ---------------------------------------------------------- panel derecho
        with ui.column().classes('grow basis-[320px] min-w-0 gap-2'):
            with ui.card().classes('w-full'):
                grafico = ui.plotly({}).classes('w-full h-[560px]')
            with ui.row().classes('w-full wrap items-start gap-2'):
                with ui.card().classes('grow basis-[280px]'):
                    ui.label('Resultado').classes('text-subtitle1 text-weight-medium')
                    tabla_info = ui.column().classes('w-full gap-0')
                with ui.card().classes('grow basis-[280px]'):
                    ui.label('Comprobaciones de fabricación').classes('text-subtitle1 text-weight-medium')
                    lista_drc = ui.column().classes('w-full gap-1')
            with ui.card().classes('w-full'):
                ui.label('Simulación (openEMS)').classes('text-subtitle1 text-weight-medium')
                with ui.row().classes('w-full items-center wrap gap-2'):
                    sel_prec = ui.select(list(PRECISIONES), value='normal', label='Precisión').classes('w-32')
                    chk_ajustar = ui.checkbox('Ajustar a la frecuencia simulando', value=True)
                    btn_sim = ui.button('Simular', icon='play_arrow').props('color=deep-purple')
                ui.label('Rápida: para tantear (±3 %). Normal: diseño. Fina: comprobación final (más lenta). '
                         'Cada simulación tarda de 1 a 15 min según el tamaño; el ajuste hace 2–5.'
                         ).classes('text-caption text-grey-8')
                registro = ui.log(max_lines=200).classes('w-full h-32 text-caption')
                res_sim = ui.column().classes('w-full gap-2')
            with ui.card().classes('w-full'):
                ui.label('Asistente de ajuste (con tu medida)').classes('text-subtitle1 text-weight-medium')
                ui.label('Fabrica la antena, mídela y el asistente te dice qué marca cortar, cuántos puentes '
                         'cerrar o qué poner en la red en π. Sube un .s1p o mide directamente con el NanoVNA.'
                         ).classes('text-caption text-grey-8')
                with ui.row().classes('w-full items-center wrap gap-2'):
                    subida = ui.upload(label='Subir .s1p', auto_upload=True, max_files=1).props('accept=.s1p,.S1P flat bordered').classes('w-64')
                    calibs = ['completa_50k_2700M']
                    try:
                        import calibracion as _cal
                        calibs = _cal.listar() or calibs
                    except Exception:
                        pass
                    sel_cal = ui.select(calibs, value=calibs[-1], label='Calibración del PC').classes('w-56')
                    btn_medir = ui.button('Medir con el NanoVNA', icon='settings_input_antenna').props('outline color=teal')
                res_asist = ui.column().classes('w-full gap-1')
            with ui.card().classes('w-full'):
                ui.label('Consejos').classes('text-subtitle1 text-weight-medium')
                lista_consejos = ui.column().classes('w-full gap-1')

    entradas = {}

    def construir_params():
        cont_params.clear()
        entradas.clear()
        tipo = tipos.CATALOGO[estado['clave']]
        desc.text = tipo.descripcion
        masa_auto = int(estado['params'].get('masa', 0)) != 0
        ajustable = int(estado['params'].get('ajuste', 0)) == 1
        muesca = int(estado['params'].get('alimentacion', 0)) == 1 and tipo.familia == 'parche'
        with cont_params:
            for p in tipo.parametros:
                if masa_auto and p.nombre in tipos.PARAMS_SOLO_MANUAL:
                    continue            # con masa automática el programa calcula estas medidas
                if not ajustable and p.nombre in ajuste.PARAMS_SOLO_AJUSTABLE:
                    continue            # opciones de ajuste solo si la antena es ajustable
                if not muesca and p.nombre in ('muesca', 'hueco_muesca'):
                    continue            # parches alimentados por el borde
                if muesca and p.nombre == 'largo_alimentacion':
                    continue            # con ranura la línea solo cruza el margen de masa
                valor = estado['params'].get(p.nombre, p.defecto)
                if p.opciones:
                    n = ui.select(p.opciones, value=int(valor), label=p.etiqueta).classes('w-full')
                else:
                    n = ui.number(p.etiqueta, value=valor, min=p.minimo, max=p.maximo, step=p.paso,
                                  format='%.0f' if p.entero else '%.2f').classes('w-full')
                if p.ayuda:
                    n.tooltip(p.ayuda)
                n.on_value_change(lambda e, nombre=p.nombre, entero=p.entero: cambiar_param(nombre, e.value, entero))
                entradas[p.nombre] = n

    def cambiar_param(nombre, valor, entero):
        if valor is None or estado.get('silencio'):
            return
        estado['params'][nombre] = int(round(valor)) if entero else float(valor)
        if nombre in tipos.ESCALABLES.get(estado['clave'], ()) and int(estado['params'].get('escalado', 0)) == 1:
            # el usuario fija una medida a mano: si siguiera en «proporcionales», el próximo ajuste la pisaría
            estado['params']['escalado'] = 0
            if 'escalado' in entradas:
                estado['silencio'] = True
                entradas['escalado'].value = 0
                estado['silencio'] = False
            ui.notify('Medidas secundarias pasadas a «Manuales» para respetar el valor que has puesto.')
        if nombre == 'escalado' and int(valor) == 1:
            ajustar()                   # vuelve a escalar las medidas con la frecuencia actual
            return
        if nombre == 'masa':
            # cambia qué medidas se muestran y la masa cambia la resonancia: se reajusta
            construir_params()
            ajustar()
            return
        if nombre == 'conector' and tipos.CATALOGO[estado['clave']].familia == 'monopolo':
            ajustar()                   # el conector fija la masa mínima, que mueve la resonancia
            return
        if nombre in ('ajuste', 'alimentacion'):
            construir_params()
        regenerar()

    def regenerar():
        try:
            a = tipos.generar(estado['clave'], estado['params'], estado['sustrato'])
        except Exception as ex:      # geometría imposible con estos parámetros
            ui.notify(f'No se puede generar: {ex}', type='negative')
            return
        estado['antena'] = a
        grafico.update_figure(vista.figura_plotly(a))
        lo, hi = banda_actual()
        tabla_info.clear()
        with tabla_info:
            bw = a.info.get('ancho_banda_estimado')
            if bw:
                cubre = bw['f_inf_MHz'] <= lo and bw['f_sup_MHz'] >= hi
                holgado = cubre and bw['MHz'] >= 1.5*(hi - lo)
                with ui.row().classes('w-full no-wrap items-center q-mb-xs'):
                    ui.icon('check_circle' if holgado else ('warning' if cubre else 'cancel'),
                            color='positive' if holgado else ('warning' if cubre else 'negative'))
                    ui.label(f"Banda estimada {bw['f_inf_MHz']:g}–{bw['f_sup_MHz']:g} MHz "
                             f"({bw['MHz']:g} MHz, {bw['porcentaje']:g} %) · necesaria {lo:g}–{hi:g} MHz"
                             ).classes('text-caption text-weight-medium')
            for k, v in a.info.items():
                # «v in (None, [], {})» falla con números de numpy (compara elemento a elemento)
                vacio = v is None or (isinstance(v, (list, tuple, dict)) and len(v) == 0)
                if vacio or k in ('avisos', 'ancho_banda_estimado', 'ajuste'):
                    continue
                with ui.row().classes('w-full no-wrap justify-between'):
                    ui.label(ETIQUETAS_INFO.get(k, k)).classes('text-caption text-grey-8')
                    ui.label(_fmt(v)).classes('text-caption text-weight-medium text-right')
        lista_consejos.clear()
        with lista_consejos:
            for cat, texto in consejos.consejos(a, estado['f_MHz']*1e6, (lo*1e6, hi*1e6)):
                icono, color = ICONOS_CONSEJO.get(cat, ('info', 'grey'))
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(icono, color=color).tooltip(cat)
                    ui.label(texto).classes('text-caption')
        lista_drc.clear()
        with lista_drc:
            colores = {'ok': 'positive', 'aviso': 'warning', 'error': 'negative', 'info': 'teal'}
            iconos = {'ok': 'check_circle', 'aviso': 'warning', 'error': 'error', 'info': 'build'}
            mensajes = (fabricacion.comprobar(a, estado['reglas']) + [('aviso', m) for m in a.info.get('avisos', [])]
                        + [('info', m) for m in (a.info.get('ajuste') or [])])
            for nivel, msg in mensajes:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(iconos[nivel], color=colores[nivel])
                    ui.label(msg).classes('text-caption')

    def cambiar_tipo(e):
        estado['clave'] = e.value
        estado['params'] = tipos.CATALOGO[e.value].defectos()
        aviso_ajuste.text = ''
        construir_params()
        ajustar()

    def banda_actual():
        return estado['f_MHz'] - estado['bw_MHz']/2, estado['f_MHz'] + estado['bw_MHz']/2

    def mostrar_rango():
        lo, hi = banda_actual()
        rango.text = f'Banda: {lo:g}–{hi:g} MHz'

    def cambiar_banda(e):
        b = BANDAS[e.value]
        if b is not None:
            estado['silencio_banda'] = True
            f_in.value = (b[0] + b[1])/2
            bw_in.value = b[1] - b[0]
            estado['silencio_banda'] = False
            estado['f_MHz'], estado['bw_MHz'] = (b[0] + b[1])/2, b[1] - b[0]
            mostrar_rango()
            ajustar()

    def cambiar_f(e):
        if e.value and not estado.get('silencio_banda'):
            estado['f_MHz'] = float(e.value)
            mostrar_rango()

    def cambiar_bw(e):
        if e.value and not estado.get('silencio_banda'):
            estado['bw_MHz'] = float(e.value)
            mostrar_rango()
            regenerar()

    def poner_params(p):
        estado['params'] = p
        estado['silencio'] = True           # no regenerar por cada campo que se actualiza
        try:
            for nombre, n in entradas.items():
                if n.value != p[nombre]:
                    n.set_value(p[nombre])
        finally:
            estado['silencio'] = False
        regenerar()

    def ajustar():
        p = tipos.dimensionar(estado['clave'], estado['f_MHz']*1e6, estado['params'], estado['sustrato'])
        aviso_ajuste.text = p.pop('_aviso', '')
        poner_params(p)

    def ampliar_bw():
        p, msg = tipos.ajustar_ancho_banda(estado['clave'], estado['f_MHz']*1e6, estado['bw_MHz']*1e6,
                                           estado['params'], estado['sustrato'])
        aviso_ajuste.text = msg
        ui.notify(msg, type='positive' if msg.startswith(('Ya', 'Ancho')) else 'warning', multi_line=True)
        poner_params(p)

    # ---------------------------------------------------------- simulación
    sim = {'proc': None, 'lineas': [], 'carpeta': None}

    def lector(proc):
        for linea in proc.stdout:
            linea = linea.rstrip()
            if linea.startswith('PROGRESO '):
                sim['lineas'].append(linea[9:])
        proc.wait()

    def simular_click():
        if sim['proc'] is not None:
            ui.notify('Ya hay una simulación en marcha', type='warning')
            return
        carpeta = os.path.join(DIR_SALIDAS, '_simulaciones', time.strftime('%Y%m%d_%H%M%S'))
        os.makedirs(carpeta, exist_ok=True)
        trabajo = {'clave': estado['clave'], 'parametros': estado['params'], 'sustrato': estado['sustrato'],
                   'f_obj_Hz': estado['f_MHz']*1e6, 'precision': sel_prec.value, 'ajustar': chk_ajustar.value,
                   'salida': carpeta}
        ruta = os.path.join(carpeta, 'trabajo.json')
        with open(ruta, 'w', encoding='utf-8') as fh:
            json.dump(trabajo, fh, ensure_ascii=False, default=float)
        registro.clear()
        registro.push(f'Simulando {tipos.CATALOGO[estado["clave"]].nombre} a {estado["f_MHz"]:g} MHz '
                      f'({sel_prec.value}{", con ajuste" if chk_ajustar.value else ""})…')
        entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
        proc = subprocess.Popen([sys.executable, '-u', '-m', 'antenas.simular_cli', ruta], cwd=RAIZ, env=entorno,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        sim.update(proc=proc, lineas=[], carpeta=carpeta, t0=time.time())
        threading.Thread(target=lector, args=(proc,), daemon=True).start()
        btn_sim.props('loading')

    def vigilar():
        while sim['lineas']:
            registro.push(sim['lineas'].pop(0))
        proc = sim['proc']
        if proc is not None and proc.poll() is not None and not sim['lineas']:
            sim['proc'] = None
            btn_sim.props(remove='loading')
            mostrar_simulacion(sim['carpeta'])

    def mostrar_simulacion(carpeta):
        ruta = os.path.join(carpeta, 'resultado.json')
        res_sim.clear()
        if not os.path.exists(ruta):
            registro.push('La simulación terminó sin resultado (mira la consola).')
            return
        r = json.load(open(ruta, encoding='utf-8'))
        if not r.get('ok'):
            registro.push(f'Error: {r.get("error")}')
            ui.notify(f'Error en la simulación: {r.get("error")}', type='negative', multi_line=True)
            return
        d = np.load(os.path.join(carpeta, 'datos.npz'))
        lo, hi = banda_actual()
        with res_sim:
            for av in r.get('avisos', []):
                with ui.row().classes('items-start no-wrap'):
                    ui.icon('warning', color='warning')
                    ui.label(av).classes('text-caption')
            filas = [('Resonancia', f"{r['f_resonancia_MHz']:g} MHz ({r.get('criterio') or 'centro de banda'})"),
                     ('Banda a −10 dB', '—' if not r['banda_MHz'] else
                      f"{r['banda_MHz'][0]:g}–{r['banda_MHz'][1]:g} MHz ({r['ancho_banda_MHz']:g} MHz)"),
                     ('Banda necesaria', f'{lo:g}–{hi:g} MHz'),
                     ('S11 mínimo', f"{r['s11_min_dB']:g} dB a {r['f_min_s11_MHz']:g} MHz"),
                     ('Directividad / ganancia', f"{r['directividad_dBi']:g} / {r['ganancia_dBi']:g} dBi"),
                     ('Eficiencia de radiación / total', f"{r['eficiencia_radiacion_%']:g} % / {r['eficiencia_total_%']:g} %"),
                     ('Malla / tiempo', f"{r['celdas']/1e6:.2f} M celdas, paso {r['paso_malla_mm']} mm, {r['tiempo_s']:g} s")]
            cubre = bool(r['banda_MHz']) and r['banda_MHz'][0] <= lo and r['banda_MHz'][1] >= hi
            with ui.row().classes('items-center no-wrap'):
                ui.icon('check_circle' if cubre else 'cancel', color='positive' if cubre else 'negative')
                ui.label('La simulación cubre la banda' if cubre else 'La simulación NO cubre la banda entera'
                         ).classes('text-caption text-weight-medium')
            with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-0'):
                for k, v in filas:
                    ui.label(k).classes('text-caption text-grey-8')
                    ui.label(v).classes('text-caption text-weight-medium')
            if r.get('historial'):
                ui.label('Ajuste: ' + ' → '.join(f"{h['escala_mm']} mm: {h['f_resonancia_MHz']} MHz ({h['error_%']:+} %)"
                                                for h in r['historial'])).classes('text-caption')
                ui.button('Aplicar los parámetros ajustados', icon='done_all',
                          on_click=lambda q=r['parametros']: poner_params({k: v for k, v in q.items()
                                                                          if not k.startswith('_')})) \
                    .props('outline color=deep-purple')
            with ui.row().classes('w-full wrap gap-2'):
                ui.plotly(graficas.s11(d['f'], d['s11'], (lo*1e6, hi*1e6))).classes('grow basis-[320px] h-[300px]')
                ui.plotly(graficas.smith(d['f'], d['s11'])).classes('grow basis-[300px] h-[300px]')
            if d['d'].size:
                with ui.row().classes('w-full wrap gap-2'):
                    ui.plotly(graficas.cortes_polares(d['theta'], d['phi'], d['d'])).classes('grow basis-[320px] h-[340px]')
                    ui.plotly(graficas.diagrama_3d(d['theta'], d['phi'], d['d'])).classes('grow basis-[320px] h-[340px]')
        ui.notify('Simulación terminada', type='positive')

    ui.timer(0.5, vigilar)

    # ---------------------------------------------------------- asistente de ajuste
    def mostrar_asistente(f, s11, origen):
        a = estado['antena']
        if a is None:
            return
        s = tipos.sustrato(estado['sustrato'])
        w50 = ancho_microstrip(50, s.er, s.h)
        rec = ajuste.asistente(a, f, s11, estado['f_MHz']*1e6, ajuste.distancia_conector_a_red(a),
                               eps_eff_microstrip(s.er, s.h, w50))
        lo, hi = banda_actual()
        res_asist.clear()
        with res_asist:
            ui.label(f'{origen}: resonancia medida {rec["f_medida_MHz"]:g} MHz ({rec["desvio_%"]:+g} % respecto a '
                     f'{estado["f_MHz"]:g} MHz), S11 mínimo {rec["s11_min_dB"]:g} dB; en el objetivo '
                     f'{rec["s11_en_f_obj_dB"]:g} dB, Z = {rec["Z_en_f_obj_ohm"][0]:g} {rec["Z_en_f_obj_ohm"][1]:+g}j Ω'
                     ).classes('text-caption text-weight-medium')
            for acc in rec['acciones']:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon('build', color='teal')
                    ui.label(acc).classes('text-caption')
            if rec.get('redes'):
                txt = lambda c: '0 Ω' if c[0] == '0 Ω' else (f'{c[1]:g} nH' if c[0] == 'L' else f'{c[1]:g} pF')
                ui.label('Alternativas para la red en π (valores comerciales E24):').classes('text-caption q-mt-xs')
                for r_ in rec['redes']:
                    ui.label(f'· Z1 = {txt(r_["serie"])}, {r_["posicion"]} = {txt(r_["derivacion"])} → |S11| ≈ '
                             f'{r_["s11_dB"]} dB').classes('text-caption')
            with ui.row().classes('w-full wrap gap-2'):
                ui.plotly(graficas.s11(f, s11, (lo*1e6, hi*1e6))).classes('grow basis-[320px] h-[280px]')
                ui.plotly(graficas.smith(f, s11)).classes('grow basis-[280px] h-[280px]')

    async def subir_s1p(e):
        try:
            datos = await e.file.read()          # NiceGUI 3
            nombre = e.file.name
        except AttributeError:
            datos = e.content.read()             # NiceGUI 2
            nombre = e.name
        try:
            f, s11 = ajuste.leer_s1p(datos.decode('utf-8', errors='replace'))
        except Exception as ex:
            ui.notify(f'No se puede leer el .s1p: {ex}', type='negative')
            return
        mostrar_asistente(f, s11, f'Medida «{nombre}»')
        subida.reset()

    def medir_vna(nombre_cal):
        import calibracion as cal
        import nanovna as nv
        c = cal.Calibracion.cargar(nombre_cal)
        with nv.NanoVNA() as v:
            f, s11, _ = c.medir(v)
        lo, hi = 0.5*estado['f_MHz']*1e6, 1.5*estado['f_MHz']*1e6
        m = (f >= lo) & (f <= hi)
        return f[m], s11[m]

    async def medir_click():
        btn_medir.props('loading')
        try:
            f, s11 = await run.io_bound(medir_vna, sel_cal.value)
            carpeta = os.path.join(DIR_SALIDAS, '_medidas')
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, time.strftime('%Y%m%d_%H%M%S') + f'_{estado["clave"]}.s1p')
            with open(ruta, 'w', encoding='utf-8') as fh:
                fh.write('# HZ S RI R 50\n' + '\n'.join(f'{fi:.0f} {z.real:.6e} {z.imag:.6e}' for fi, z in zip(f, s11)))
            mostrar_asistente(f, s11, 'Medida con el NanoVNA')
            ui.notify(f'Medida guardada en salidas/_medidas/{os.path.basename(ruta)}', type='positive')
        except Exception as ex:
            ui.notify(f'No se pudo medir: {ex}', type='negative', multi_line=True)
        finally:
            btn_medir.props(remove='loading')

    subida.on_upload(subir_s1p)
    btn_medir.on_click(medir_click)

    def exportar_click():
        a = estado['antena']
        if a is None:
            return
        nombre = ''.join(c for c in (nombre_in.value or 'antena') if c.isalnum() or c in '-_') or 'antena'
        carpeta = os.path.join(DIR_SALIDAS, nombre)
        try:
            titulo = f"{tipos.CATALOGO[a.tipo].nombre.split(' (')[0]} {a.info.get('f_estimada_MHz')} MHz"
            r = exportar.exportar_todo(a, carpeta, nombre, titulo)
        except Exception as ex:
            ui.notify(f'Error al exportar: {ex}', type='negative', multi_line=True)
            return
        res_export.clear()
        with res_export:
            ui.label(f'Guardado en salidas/{nombre}/').classes('text-caption')
            for clave, texto in (('gerber_zip', 'Gerber para JLC (.zip)'), ('placa', 'Placa de prueba KiCad (.kicad_pcb)'),
                                 ('huella', 'Huella KiCad (.kicad_mod)'), ('dxf', 'DXF para EasyEDA'),
                                 ('gerber_zip_reflector', 'Reflector: Gerber para JLC (.zip)'),
                                 ('placa_reflector', 'Reflector: placa KiCad (.kicad_pcb)'),
                                 ('dxf_reflector', 'Reflector: DXF (chapa o placa)')):
                if clave not in r:
                    continue
                ui.button(texto, icon='file_download', on_click=lambda r=r, c=clave: ui.download(r[c])) \
                    .props('flat dense no-caps').classes('w-full justify-start')
            if r['drc']:
                ui.label(f'DRC de KiCad: {len(r["drc"])} infracciones').classes('text-caption text-negative')
                for t, sev, d in r['drc'][:5]:
                    ui.label(f'· {t}: {d}').classes('text-caption')
            else:
                ui.label('DRC de KiCad sin errores').classes('text-caption text-positive')
        ui.notify(f'Exportado en salidas/{nombre}', type='positive')

    sel_tipo.on_value_change(cambiar_tipo)
    banda.on_value_change(cambiar_banda)
    f_in.on_value_change(cambiar_f)
    bw_in.on_value_change(cambiar_bw)
    btn_bw.on_click(ampliar_bw)
    btn_sim.on_click(simular_click)
    sel_sus.on_value_change(lambda e: (estado.update(sustrato=e.value), regenerar()))
    sel_reg.on_value_change(lambda e: (estado.update(reglas=e.value), regenerar()))
    btn_ajustar.on_click(ajustar)
    btn_export.on_click(exportar_click)

    mostrar_rango()
    construir_params()
    ajustar()


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Generador de antenas', port=8080, reload=False, show=False, favicon='📡')
