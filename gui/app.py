"""Interfaz gráfica de Chirptenna (NiceGUI, se abre en el navegador).

Uso: python gui/app.py   ->   http://localhost:8080

Organización por fases: una barra fija con el diseño (nombre, tipo y banda) y pestañas
Diseño → Simulación → Fabricar → Medir → Mis diseños. Los diseños se guardan en
Documentos\\Chirptenna\\disenos (módulo `antenas.biblioteca`).
"""
import os
import sys
import json
import asyncio
import time
import threading
import subprocess

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nicegui import app, ui, run, background_tasks   # noqa: E402

from antenas import tipos, vista, fabricacion, exportar, consejos, graficas, ajuste, biblioteca, problemas   # noqa: E402
from antenas.materiales import ancho_microstrip, eps_eff_microstrip   # noqa: E402

sys.path.insert(0, os.path.join(RAIZ, 'vna'))   # driver del NanoVNA y calibración del PC
from antenas.simulacion import PRECISIONES   # noqa: E402
from antenas.materiales import SUSTRATOS, SUSTRATO_POR_DEFECTO   # noqa: E402

DIR_SALIDAS = os.path.join(RAIZ, 'salidas')
LOGO = os.path.join(RAIZ, 'docs', 'logo', 'chirptenna.png')
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
    'diseno': None,          # nombre del diseño abierto de la biblioteca (None = sin guardar)
    'sucio': False,          # hay cambios sin guardar
}


def _fmt(v):
    if isinstance(v, float):
        return f'{v:.3f}'.rstrip('0').rstrip('.')
    if isinstance(v, dict):
        return ', '.join(f'{k}: {_fmt(x)}' for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return ' × '.join(_fmt(x) for x in v) if all(isinstance(x, (int, float)) for x in v) else '; '.join(map(str, v))
    return str(v)


def _banda_de(f_MHz, bw_MHz):
    """Nombre de la banda predefinida que coincide con (centro, ancho), o 'Otra'."""
    for n, b in BANDAS.items():
        if b and abs((b[0] + b[1])/2 - f_MHz) < 0.01 and abs((b[1] - b[0]) - bw_MHz) < 0.01:
            return n
    return 'Otra'


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
ICONOS_CONSEJO = {'banda': ('podcasts', 'deep-orange'), 'diseño': ('lightbulb', 'amber-8'),
                  'montaje': ('construction', 'blue-grey'), 'medida': ('straighten', 'teal')}


def _titulo_card(texto, icono=None):
    with ui.row().classes('items-center gap-1 no-wrap'):
        if icono:
            ui.icon(icono).classes('icono-titulo')
        ui.label(texto).classes('text-subtitle1 text-weight-medium')


@ui.page('/')
def pagina():
    ui.add_css('''
        body.body--light { background: #eef1f3; }
        body.body--dark { background: #121417; }
        /* Colores propios: los de Quasar (text-grey-8…) van en un @layer con !important y no se pueden
           cambiar para el tema oscuro, así que aquí no se usan. */
        .texto-sec { color: #5f6b73; }
        .body--dark .texto-sec { color: #b4c0c8; }
        .texto-aviso { color: #bf360c; }
        .body--dark .texto-aviso { color: #ffb74d; }
        .texto-violeta { color: #5e35b1; }
        .body--dark .texto-violeta { color: #c5b3f0; }
        .icono-titulo { color: #546e7a; }
        .body--dark .icono-titulo { color: #90a4ae; }
        .pestanas { color: #37474f; }
        .body--dark .pestanas { color: #e3e9ed; }
        .pestanas .q-tab--active { color: #1976d2; }
        .body--dark .pestanas .q-tab--active { color: #64b5f6; }
        .body--dark .q-field__label { color: #b4c0c8; }
        .body--dark .q-table tbody td { color: #e6ebee; }
        .q-field__label { font-size: 0.82rem; }
        .q-tab__label { font-size: 0.85rem; }
    ''')
    # ================================================================== cabecera
    with ui.header().classes('bg-blue-grey-9 items-center q-py-xs gap-3'):
        if os.path.exists(LOGO):
            ui.image(LOGO).classes('w-9 h-9')
        ui.label('Chirptenna').classes('text-h6')
        ui.label('antenas impresas para PCB').classes('text-caption text-blue-grey-2 gt-xs')
        ui.space()
        lbl_diseno = ui.label().classes('text-subtitle2')
        lbl_resumen = ui.label().classes('text-caption text-blue-grey-2 gt-sm')
        btn_tema = ui.button().props('flat round dense color=white')

    # ================================================================== tema claro / oscuro
    # 'auto' sigue al sistema; la preferencia se guarda en app.storage.general (.nicegui/ en la raíz)
    modo_oscuro = ui.dark_mode()
    tema = {'modo': app.storage.general.get('tema', 'auto'), 'oscuro': False}
    if tema['modo'] != 'auto':              # modo fijo: se aplica ya, antes de dibujar nada
        tema['oscuro'] = tema['modo'] == 'oscuro'
        modo_oscuro.value = tema['oscuro']
    ICONOS_TEMA = {'auto': ('brightness_auto', 'Tema: automático (como el sistema)'),
                   'claro': ('light_mode', 'Tema: claro'), 'oscuro': ('dark_mode', 'Tema: oscuro')}

    def T(fig):
        """Adapta una figura de Plotly al tema actual (se llama en cada ui.plotly / update_figure)."""
        if not tema['oscuro']:
            return fig
        fondo, rejilla, texto = '#1d2023', '#3a3f44', '#e0e0e0'
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=fondo,
                          font_color=texto)
        fig.update_xaxes(gridcolor=rejilla, zerolinecolor='#555')
        fig.update_yaxes(gridcolor=rejilla, zerolinecolor='#555')
        if fig.layout.polar is not None:
            fig.update_polars(bgcolor=fondo, radialaxis_gridcolor=rejilla, angularaxis_gridcolor=rejilla)
        for tr in fig.data:
            linea = getattr(tr, 'line', None)
            if linea is not None and linea.color in ('#444', 'black', '#999', '#ddd'):
                tr.line.color = {'#999': '#777', '#ddd': '#3f4449'}.get(linea.color, '#cfd8dc')
            if getattr(tr, 'mode', None) == 'text':
                tr.textfont.color = texto
        for sh in fig.layout.shapes or ():
            if sh.line is not None and sh.line.color == '#444':
                sh.line.color = '#cfd8dc'
        return fig

    async def aplicar_tema(repintar=True):
        modo = tema['modo']
        if modo == 'auto':
            modo_oscuro.value = None
            try:
                await ui.context.client.connected()
                oscuro = bool(await ui.run_javascript(
                    "window.matchMedia('(prefers-color-scheme: dark)').matches", timeout=3))
            except Exception:
                oscuro = False
        else:
            oscuro = modo == 'oscuro'
            modo_oscuro.value = oscuro
        icono, ayuda = ICONOS_TEMA[modo]
        btn_tema.props(f'icon={icono}')
        btn_tema.tooltip(ayuda)
        cambia = oscuro != tema['oscuro']
        tema['oscuro'] = oscuro
        if repintar and cambia:
            repintar_graficas()

    async def cambiar_tema():
        orden = ['auto', 'claro', 'oscuro']
        tema['modo'] = orden[(orden.index(tema['modo']) + 1) % 3]
        app.storage.general['tema'] = tema['modo']
        await aplicar_tema()
        ui.notify(ICONOS_TEMA[tema['modo']][1])

    btn_tema.on_click(cambiar_tema)

    # ================================================================== barra del diseño (siempre visible)
    with ui.card().classes('w-full barra-diseno q-pa-sm').props('flat bordered'):
        with ui.row().classes('w-full items-end wrap gap-x-3 gap-y-1'):
            nombre_in = ui.input('Nombre del diseño', value='antena').classes('w-48')
            sel_tipo = ui.select({k: t.nombre for k, t in tipos.CATALOGO.items()}, value=estado['clave'],
                                 label='Tipo de antena').classes('w-72')
            with ui.column().classes('gap-0'):
                ui.label('Banda de uso').classes('text-caption texto-sec')
                banda = ui.toggle(list(BANDAS), value='2,4 GHz').props('dense no-caps')
            f_in = ui.number('Centro [MHz]', value=estado['f_MHz'], min=100, max=10000, step=0.005,
                             format='%.3f').classes('w-32')
            bw_in = ui.number('Ancho [MHz]', value=estado['bw_MHz'], min=0.05, max=5000, step=0.05,
                              format='%.2f').classes('w-28')
            rango = ui.label().classes('text-caption texto-sec self-center')
            ui.space()
            btn_guardar = ui.button('Guardar diseño', icon='save').props('color=primary no-caps')
        desc = ui.label().classes('text-caption texto-sec')
        cont_problemas = ui.column().classes('w-full gap-0')

    # ================================================================== pestañas
    with ui.tabs().classes('w-full pestanas').props('align=left inline-label no-caps') as pestanas:
        t_diseno = ui.tab('Diseño', icon='architecture')
        t_sim = ui.tab('Simulación', icon='insights')
        t_fab = ui.tab('Fabricar', icon='precision_manufacturing')
        t_medir = ui.tab('Medir', icon='settings_input_antenna')
        t_bib = ui.tab('Mis diseños', icon='folder_special')

    with ui.tab_panels(pestanas, value=t_diseno).classes('w-full bg-transparent'):
        # -------------------------------------------------------------- 1. Diseño
        with ui.tab_panel(t_diseno).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.column().classes('w-full sm:w-[380px] gap-2'):
                    with ui.card().classes('w-full'):
                        _titulo_card('Tamaño y material', 'straighten')
                        sel_sus = ui.select(list(SUSTRATOS), value=estado['sustrato'], label='Sustrato').classes('w-full')
                        btn_ajustar = ui.button('Ajustar tamaño a la frecuencia', icon='tune') \
                            .props('color=primary no-caps').classes('w-full')
                        btn_bw = ui.button('Ampliar ancho de banda', icon='open_in_full') \
                            .props('outline color=primary no-caps').classes('w-full')
                        aviso_ajuste = ui.label().classes('text-caption text-orange-9')
                    with ui.card().classes('w-full'):
                        _titulo_card('Parámetros', 'tune')
                        cont_params = ui.column().classes('w-full gap-0')
                with ui.column().classes('grow basis-[320px] min-w-0 gap-2'):
                    with ui.card().classes('w-full'):
                        grafico = ui.plotly({}).classes('w-full h-[560px]')
                    with ui.row().classes('w-full wrap items-start gap-2'):
                        with ui.card().classes('grow basis-[280px]'):
                            _titulo_card('Resultado (estimación)', 'analytics')
                            tabla_info = ui.column().classes('w-full gap-0')
                        with ui.card().classes('grow basis-[280px]'):
                            _titulo_card('Consejos', 'lightbulb')
                            lista_consejos = ui.column().classes('w-full gap-1')

        # -------------------------------------------------------------- 2. Simulación
        with ui.tab_panel(t_sim).classes('q-pa-sm'):
            with ui.card().classes('w-full'):
                _titulo_card('Simulación con openEMS', 'insights')
                with ui.row().classes('w-full items-center wrap gap-2'):
                    sel_prec = ui.select(list(PRECISIONES), value='normal', label='Precisión').classes('w-32')
                    chk_ajustar = ui.checkbox('Ajustar a la frecuencia simulando', value=True)
                    btn_sim = ui.button('Simular', icon='play_arrow').props('color=deep-purple no-caps')
                ui.label('Rápida: para tantear (±3 %). Normal: diseño. Fina: comprobación final (más lenta). '
                         'Cada simulación tarda de 1 a 15 min según el tamaño; el ajuste hace 2–5. '
                         'Si el diseño está guardado, el resultado se guarda con él.'
                         ).classes('text-caption texto-sec')
                registro = ui.log(max_lines=200).classes('w-full h-32 text-caption')
            res_sim = ui.column().classes('w-full gap-2 q-mt-sm')

        # -------------------------------------------------------------- 3. Fabricar
        with ui.tab_panel(t_fab).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.card().classes('grow basis-[340px]'):
                    _titulo_card('Comprobaciones de fabricación', 'rule')
                    sel_reg = ui.select(list(fabricacion.REGLAS), value=estado['reglas'],
                                        label='Reglas del fabricante').classes('w-full')
                    lista_drc = ui.column().classes('w-full gap-1 q-mt-sm')
                with ui.card().classes('grow basis-[340px]'):
                    _titulo_card('Exportar', 'download')
                    ui.label('Guarda el diseño y exporta la placa de prueba KiCad, la huella, los Gerber para JLC '
                             '(con taladros) y el DXF en la carpeta «fabricacion» del diseño. Pasa el DRC de KiCad.'
                             ).classes('text-caption texto-sec')
                    btn_export = ui.button('Exportar KiCad + Gerber + DXF', icon='download') \
                        .props('color=positive no-caps').classes('w-full q-mt-sm')
                    res_export = ui.column().classes('w-full gap-1')

        # -------------------------------------------------------------- 4. Medir
        with ui.tab_panel(t_medir).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.card().classes('w-full sm:w-[420px] q-pa-none'):
                    with ui.row().classes('items-center q-px-md q-pt-sm'):
                        _titulo_card('Asistente del NanoVNA', 'settings_input_antenna')
                    with ui.stepper().props('vertical flat header-nav').classes('w-full') as pasos_vna:
                        # ---- 1. conectar
                        with ui.step('Conectar el NanoVNA', icon='usb'):
                            ui.label('Conéctalo por USB. Solo se lee su estado: su calibración y sus slots '
                                     'guardados no se tocan.').classes('text-caption texto-sec')
                            info_vna = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                btn_conectar = ui.button('Buscar el NanoVNA', icon='search').props('color=teal no-caps')
                                ui.button('Saltar (subir un .s1p)', on_click=lambda: pasos_vna.set_value('Medir y ajustar')
                                          ).props('flat no-caps')
                        # ---- 2. calibrar
                        with ui.step('Calibración', icon='tune'):
                            ui.label('Calibra al final del latiguillo que vayas a usar con la antena: el plano de '
                                     'medida queda ahí.').classes('text-caption texto-sec')
                            modo_cal = ui.toggle({0: 'Usar una guardada', 1: 'Calibrar ahora'}, value=0) \
                                .props('dense no-caps')
                            cont_cal_guardada = ui.column().classes('w-full gap-1')
                            with cont_cal_guardada:
                                calibs = []
                                try:
                                    import calibracion as _cal
                                    calibs = _cal.listar()
                                except Exception:
                                    pass
                                sel_cal = ui.select(calibs, value=(calibs[-1] if calibs else None),
                                                    label='Calibración del PC').classes('w-full')
                                info_cal = ui.label().classes('text-caption')
                            cont_cal_nueva = ui.column().classes('w-full gap-1')
                            with cont_cal_nueva:
                                with ui.row().classes('w-full no-wrap gap-2'):
                                    cal_ini = ui.number('Desde [MHz]', format='%.1f', min=0.05, max=6000).classes('grow')
                                    cal_fin = ui.number('Hasta [MHz]', format='%.1f', min=0.05, max=6000).classes('grow')
                                    cal_pts = ui.number('Puntos', value=301, min=11, max=2020, step=1, format='%.0f'
                                                        ).classes('w-20')
                                cal_nombre = ui.input('Nombre de la calibración').classes('w-full')
                                btn_cal_empezar = ui.button('Empezar', icon='play_arrow').props('outline color=teal no-caps')
                                filas_cal = ui.column().classes('w-full gap-1')
                                btn_cal_guardar = ui.button('Guardar calibración', icon='save') \
                                    .props('color=teal no-caps').classes('w-full')
                                res_cal = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                ui.button('Siguiente', on_click=lambda: pasos_vna.next()).props('color=teal no-caps')
                                ui.button('Atrás', on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                        # ---- 3. comprobar
                        with ui.step('Comprobar la calibración', icon='fact_check'):
                            ui.label('Pon la CARGA de 50 Ω al final del latiguillo. Bien calibrado, |S11| queda '
                                     'por debajo de −30 dB.').classes('text-caption texto-sec')
                            res_verif = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                btn_verif = ui.button('Comprobar', icon='fact_check').props('color=teal no-caps')
                                ui.button('Siguiente', on_click=lambda: pasos_vna.next()).props('flat no-caps')
                                ui.button('Atrás', on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                        # ---- 4. medir y ajustar
                        with ui.step('Medir y ajustar', icon='straighten'):
                            ui.label('Conecta la antena. Cada medida se guarda en el diseño con su etiqueta; el modo '
                                     'en vivo repite la medida cerca de la banda mientras cortas o cambias la red '
                                     'en π, sin guardarla.').classes('text-caption texto-sec')
                            etiqueta_in = ui.input('Etiqueta', placeholder='p. ej. sin cortar, tras la marca 2') \
                                .classes('w-full')
                            notas_medida = ui.input('Notas (opcional)').classes('w-full')
                            with ui.row().classes('w-full items-center gap-2'):
                                btn_medir = ui.button('Medir y guardar', icon='add_chart').props('color=teal no-caps')
                                sw_vivo = ui.switch('En vivo')
                            vivo_txt = ui.label().classes('text-caption text-weight-medium')
                            vivo_graf = ui.plotly({}).classes('w-full h-[220px]')
                            vivo_graf.set_visibility(False)
                            btn_guardar_vivo = ui.button('Guardar esta medida', icon='save') \
                                .props('outline color=teal no-caps')
                            btn_guardar_vivo.set_visibility(False)
                            ui.separator().classes('q-my-sm')
                            subida = ui.upload(label='…o sube un .s1p', auto_upload=True, max_files=1) \
                                .props('accept=.s1p,.S1P flat bordered').classes('w-full')
                            with ui.stepper_navigation():
                                ui.button('Atrás', on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                with ui.column().classes('grow basis-[340px] min-w-0 gap-2'):
                    with ui.card().classes('w-full'):
                        _titulo_card('Simulado frente a medido', 'stacked_line_chart')
                        lista_medidas = ui.column().classes('w-full gap-0')
                        cont_comparacion = ui.column().classes('w-full')
                    with ui.card().classes('w-full'):
                        _titulo_card('Asistente de ajuste', 'build')
                        ui.label('A partir de una medida te dice qué marca cortar, cuántos puentes cerrar o qué '
                                 'poner en la red en π. Pulsa «Analizar» en una medida.'
                                 ).classes('text-caption texto-sec')
                        res_asist = ui.column().classes('w-full gap-1')

        # -------------------------------------------------------------- 5. Mis diseños
        with ui.tab_panel(t_bib).classes('q-pa-sm'):
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center'):
                    _titulo_card('Mis diseños', 'folder_special')
                    ui.space()
                    ui.label(biblioteca.carpeta_base()).classes('text-caption texto-sec')
                    ui.button(icon='folder_open', on_click=lambda: os.startfile(biblioteca.carpeta_base())) \
                        .props('flat round dense').tooltip('Abrir la carpeta')
                    ui.button(icon='refresh', on_click=lambda: refrescar_biblioteca()).props('flat round dense') \
                        .tooltip('Actualizar')
                columnas = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left', 'sortable': True},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo_txt', 'align': 'left', 'sortable': True},
                    {'name': 'f', 'label': 'Objetivo [MHz]', 'field': 'f_txt', 'sortable': True},
                    {'name': 'sim', 'label': 'Simulada [MHz]', 'field': 'sim_txt'},
                    {'name': 'fab', 'label': 'Exportada', 'field': 'fab_txt'},
                    {'name': 'medidas', 'label': 'Medidas', 'field': 'medidas', 'sortable': True},
                    {'name': 'mod', 'label': 'Modificado', 'field': 'modificado', 'sortable': True},
                    {'name': 'notas', 'label': 'Notas', 'field': 'notas', 'align': 'left',
                     'classes': 'ellipsis', 'style': 'max-width: 260px'},
                ]
                tabla_bib = ui.table(columns=columnas, rows=[], row_key='nombre', selection='single',
                                     pagination=15).classes('w-full').props('dense flat')
                with ui.row().classes('items-center gap-2'):
                    btn_abrir = ui.button('Abrir', icon='open_in_new').props('color=primary no-caps')
                    btn_carpeta = ui.button('Abrir carpeta', icon='folder_open').props('outline no-caps')
                    btn_renombrar = ui.button('Renombrar', icon='drive_file_rename_outline').props('outline no-caps')
                    btn_archivar = ui.button('Archivar', icon='archive').props('outline color=grey-8 no-caps') \
                        .tooltip('Lo aparta a la subcarpeta _archivados (no borra nada)')
            with ui.card().classes('w-full'):
                _titulo_card('Notas del diseño abierto', 'edit_note')
                notas_in = ui.textarea(placeholder='Pedido, fecha de fabricación, qué se cortó, resultados…') \
                    .classes('w-full').props('autogrow')
                btn_notas = ui.button('Guardar notas', icon='save').props('outline no-caps')

    entradas = {}

    # ================================================================== estado del diseño
    def actualizar_cabecera():
        n = estado['diseno']
        lbl_diseno.text = (f'{n}{" •" if estado["sucio"] else ""}' if n else 'Diseño sin guardar')
        lo, hi = banda_actual()
        lbl_resumen.text = f'{tipos.CATALOGO[estado["clave"]].nombre.split(" (")[0]} · {lo:g}–{hi:g} MHz'
        btn_guardar.props(f'color={"orange-9" if (estado["sucio"] or not n) else "primary"}')

    def marcar_cambio():
        estado['sucio'] = True
        actualizar_cabecera()

    # ================================================================== parámetros
    def construir_params():
        cont_params.clear()
        entradas.clear()
        tipo = tipos.CATALOGO[estado['clave']]
        desc.text = tipo.descripcion
        p_act = estado['params']
        masa_auto = int(p_act.get('masa', 0)) != 0
        ajustable = int(p_act.get('ajuste', 0)) == 1
        muesca = int(p_act.get('alimentacion', 0)) == 1 and tipo.familia == 'parche'
        aligerado = int(p_act.get('aligerado', 0)) == 1
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
                if not aligerado and p.nombre in tipos.PARAMS_SOLO_ALIGERADO:
                    continue            # medidas de las ventanas solo si se aligera
                valor = p_act.get(p.nombre, p.defecto)
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
        marcar_cambio()
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
        if nombre in ('ajuste', 'alimentacion', 'aligerado'):
            construir_params()
        regenerar()

    def regenerar():
        try:
            a = tipos.generar(estado['clave'], estado['params'], estado['sustrato'])
        except Exception as ex:      # geometría imposible con estos parámetros
            ui.notify(f'No se puede generar: {ex}', type='negative')
            return
        estado['antena'] = a
        grafico.update_figure(T(vista.figura_plotly(a)))
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
                    ui.label(ETIQUETAS_INFO.get(k, k)).classes('text-caption texto-sec')
                    ui.label(_fmt(v)).classes('text-caption text-weight-medium text-right')
        lista_consejos.clear()
        with lista_consejos:
            for cat, texto in consejos.consejos(a, estado['f_MHz']*1e6, (lo*1e6, hi*1e6)):
                icono, color = ICONOS_CONSEJO.get(cat, ('info', 'grey'))
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(icono, color=color).tooltip(cat)
                    ui.label(texto).classes('text-caption')
        mostrar_drc()
        mostrar_problemas()
        actualizar_cabecera()

    ICONOS_PROBLEMA = {'grave': ('error', 'negative', 'text-negative'),
                       'aviso': ('warning', 'orange-8', 'texto-aviso'),
                       'info': ('info', 'blue-grey-6', 'texto-sec')}

    def mostrar_problemas():
        """Problemas conocidos del tipo con estos parámetros (lo que ha fallado en simulación)."""
        cont_problemas.clear()
        lista = problemas.problemas(estado['clave'], estado['params'], estado['f_MHz'])
        with cont_problemas:
            for nivel, texto in lista:
                icono, color, clase = ICONOS_PROBLEMA[nivel]
                with ui.row().classes('items-start no-wrap gap-1'):
                    ui.icon(icono, color=color, size='xs').classes('q-mt-xs')
                    ui.label(texto).classes(f'text-caption {clase}')
        return lista

    def mostrar_drc():
        a = estado['antena']
        lista_drc.clear()
        if a is None:
            return
        with lista_drc:
            graves = [t for n, t in problemas.problemas(estado['clave'], estado['params'], estado['f_MHz'])
                      if n in ('grave', 'aviso')]
            for t in graves:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon('report', color='negative')
                    ui.label('Problema conocido: ' + t).classes('text-caption text-negative')
            with ui.row().classes('items-start no-wrap'):
                ui.icon('science', color='blue-grey-6')
                ui.label(problemas.AVISO_GENERAL).classes('text-caption texto-sec')
            colores = {'ok': 'positive', 'aviso': 'warning', 'error': 'negative', 'info': 'teal'}
            iconos = {'ok': 'check_circle', 'aviso': 'warning', 'error': 'error', 'info': 'build'}
            mensajes = (fabricacion.comprobar(a, estado['reglas']) + [('aviso', m) for m in a.info.get('avisos', [])]
                        + [('info', m) for m in (a.info.get('ajuste') or [])])
            for nivel, msg in mensajes:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(iconos[nivel], color=colores[nivel])
                    ui.label(msg).classes('text-caption')

    def cambiar_tipo(e):
        if estado.get('silencio'):
            return
        estado['clave'] = e.value
        estado['params'] = tipos.CATALOGO[e.value].defectos()
        aviso_ajuste.text = ''
        marcar_cambio()
        construir_params()
        ajustar()

    def banda_actual():
        return estado['f_MHz'] - estado['bw_MHz']/2, estado['f_MHz'] + estado['bw_MHz']/2

    def mostrar_rango():
        lo, hi = banda_actual()
        rango.text = f'{lo:g}–{hi:g} MHz'

    def cambiar_banda(e):
        if estado.get('silencio_banda'):
            return
        b = BANDAS[e.value]
        if b is not None:
            estado['silencio_banda'] = True
            f_in.value = (b[0] + b[1])/2
            bw_in.value = b[1] - b[0]
            estado['silencio_banda'] = False
            estado['f_MHz'], estado['bw_MHz'] = (b[0] + b[1])/2, b[1] - b[0]
            mostrar_rango()
            marcar_cambio()
            ajustar()

    def cambiar_f(e):
        if e.value and not estado.get('silencio_banda'):
            estado['f_MHz'] = float(e.value)
            mostrar_rango()
            marcar_cambio()

    def cambiar_bw(e):
        if e.value and not estado.get('silencio_banda'):
            estado['bw_MHz'] = float(e.value)
            mostrar_rango()
            marcar_cambio()
            regenerar()

    def poner_params(p):
        estado['params'] = p
        estado['silencio'] = True           # no regenerar por cada campo que se actualiza
        try:
            for nombre, n in entradas.items():
                if nombre in p and n.value != p[nombre]:
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
        marcar_cambio()
        poner_params(p)

    # ================================================================== biblioteca
    def nombre_actual():
        return biblioteca.nombre_valido(nombre_in.value)

    def guardar_diseno(forzar=False):
        """Guarda el diseño con el nombre de la barra. Pide confirmación antes de pisar otro diseño."""
        nombre = nombre_actual()
        if nombre != nombre_in.value:
            nombre_in.value = nombre
        if not forzar and nombre != estado['diseno'] and biblioteca.existe(nombre):
            confirmar(f'Ya hay un diseño llamado «{nombre}». ¿Sustituir su geometría por la actual? '
                      'Sus simulaciones, medidas y notas se conservan.', lambda: guardar_diseno(True))
            return False
        a = estado['antena']
        biblioteca.guardar(nombre, estado['clave'], estado['params'], estado['sustrato'], estado['reglas'],
                           estado['f_MHz'], estado['bw_MHz'], info=a.info if a else None)
        estado['diseno'] = nombre
        estado['sucio'] = False
        actualizar_cabecera()
        refrescar_biblioteca()
        mostrar_medidas()
        notas_in.value = (biblioteca.cargar(nombre) or {}).get('notas', '')
        ui.notify(f'Diseño «{nombre}» guardado', type='positive')
        return True

    def asegurar_guardado():
        """Para medir o exportar hace falta un diseño guardado: lo guarda si no lo está."""
        if estado['diseno'] and estado['diseno'] == nombre_actual():
            if estado['sucio']:
                guardar_diseno(True)
            return True
        return guardar_diseno()

    def confirmar(texto, accion):
        with ui.dialog() as dlg, ui.card():
            ui.label(texto)
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancelar', on_click=dlg.close).props('flat no-caps')
                ui.button('Sí', on_click=lambda: (dlg.close(), accion())).props('color=primary no-caps')
        dlg.open()

    def abrir_diseno(nombre):
        d = biblioteca.cargar(nombre)
        if not d or d.get('tipo') not in tipos.CATALOGO:
            ui.notify(f'No se puede abrir «{nombre}»', type='negative')
            return
        estado.update(clave=d['tipo'], sustrato=d.get('sustrato', SUSTRATO_POR_DEFECTO),
                      reglas=d.get('reglas', fabricacion.REGLAS_POR_DEFECTO),
                      f_MHz=float(d['f_objetivo_MHz']), bw_MHz=float(d['ancho_banda_MHz']))
        params = tipos.CATALOGO[d['tipo']].defectos()
        params.update(d.get('parametros', {}))
        estado['params'] = params
        estado['silencio'] = estado['silencio_banda'] = True
        try:
            sel_tipo.value = d['tipo']
            f_in.value = estado['f_MHz']
            bw_in.value = estado['bw_MHz']
            banda.value = _banda_de(estado['f_MHz'], estado['bw_MHz'])
            sel_sus.value = estado['sustrato']
            sel_reg.value = estado['reglas']
            nombre_in.value = nombre
        finally:
            estado['silencio'] = estado['silencio_banda'] = False
        aviso_ajuste.text = ''
        mostrar_rango()
        construir_params()
        estado['diseno'] = nombre
        regenerar()                          # sin reajustar: se respeta la geometría guardada
        estado['sucio'] = False
        actualizar_cabecera()
        notas_in.value = d.get('notas', '')
        res_export.clear()
        res_asist.clear()
        sim_g = biblioteca.leer_simulacion(nombre)
        res_sim.clear()
        registro.clear()
        if sim_g:
            registro.push(f'Simulación guardada con el diseño ({sim_g[0].get("precision", "")}).')
            pintar_simulacion(*sim_g)
        mostrar_medidas()
        pestanas.value = t_diseno
        ui.notify(f'Diseño «{nombre}» abierto', type='positive')

    def refrescar_biblioteca():
        filas = []
        for d in biblioteca.listar():
            t = tipos.CATALOGO.get(d['tipo'])
            filas.append(dict(d, tipo_txt=t.nombre.split(' (')[0] if t else d['tipo'],
                              f_txt=f"{d['f_objetivo_MHz']:g}" if d['f_objetivo_MHz'] else '',
                              sim_txt=f"{d['simulado']:g}" if d['simulado'] else '—',
                              fab_txt='sí' if d['fabricado'] else '—'))
        tabla_bib.rows = filas
        tabla_bib.update()

    def seleccionado():
        if not tabla_bib.selected:
            ui.notify('Elige un diseño de la lista', type='warning')
            return None
        return tabla_bib.selected[0]['nombre']

    def renombrar_click():
        n = seleccionado()
        if not n:
            return
        with ui.dialog() as dlg, ui.card():
            nuevo = ui.input('Nuevo nombre', value=n).classes('w-64')

            def hacer():
                try:
                    final = biblioteca.renombrar(n, nuevo.value)
                except Exception as ex:
                    ui.notify(str(ex), type='negative')
                    return
                dlg.close()
                if estado['diseno'] == n:
                    estado['diseno'] = final
                    nombre_in.value = final
                    actualizar_cabecera()
                refrescar_biblioteca()
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancelar', on_click=dlg.close).props('flat no-caps')
                ui.button('Renombrar', on_click=hacer).props('color=primary no-caps')
        dlg.open()

    def archivar_click():
        n = seleccionado()
        if not n:
            return

        def hacer():
            biblioteca.archivar(n)
            if estado['diseno'] == n:
                estado['diseno'] = None
                actualizar_cabecera()
                mostrar_medidas()
            refrescar_biblioteca()
            ui.notify(f'«{n}» movido a _archivados', type='positive')
        confirmar(f'¿Archivar «{n}»? Se mueve a la subcarpeta _archivados; no se borra nada.', hacer)

    def guardar_notas():
        if not estado['diseno']:
            ui.notify('Guarda primero el diseño', type='warning')
            return
        biblioteca.guardar_notas(estado['diseno'], notas_in.value or '')
        refrescar_biblioteca()
        ui.notify('Notas guardadas', type='positive')

    # ================================================================== simulación
    sim = {'proc': None, 'lineas': [], 'carpeta': None, 'diseno': None}

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
        # el resultado se guarda en el diseño que estaba abierto (y sin cambios) al lanzarla
        sim.update(proc=proc, lineas=[], carpeta=carpeta, t0=time.time(),
                   diseno=estado['diseno'] if not estado['sucio'] else None)
        threading.Thread(target=lector, args=(proc,), daemon=True).start()
        btn_sim.props('loading')

    def vigilar():
        while sim['lineas']:
            registro.push(sim['lineas'].pop(0))
        proc = sim['proc']
        if proc is not None and proc.poll() is not None and not sim['lineas']:
            sim['proc'] = None
            btn_sim.props(remove='loading')
            terminar_simulacion(sim['carpeta'], sim['diseno'])

    def terminar_simulacion(carpeta, diseno):
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
        if diseno and biblioteca.existe(diseno):
            biblioteca.guardar_simulacion(diseno, carpeta)
            registro.push(f'Resultado guardado en el diseño «{diseno}».')
            refrescar_biblioteca()
            if diseno == estado['diseno']:
                mostrar_medidas()
        else:
            registro.push('El diseño no estaba guardado (o cambió durante la simulación): '
                          'el resultado queda solo en salidas/_simulaciones.')
        pintar_simulacion(r, dict(np.load(os.path.join(carpeta, 'datos.npz'))))
        ui.notify('Simulación terminada', type='positive')

    def antena_simulada(r):
        """Geometría que se simuló (con los parámetros ajustados, si los hay); si no se puede, la actual."""
        clave = r.get('clave') or estado['clave']
        q = {k: v for k, v in (r.get('parametros') or {}).items() if not str(k).startswith('_')}
        if q and clave in tipos.CATALOGO:
            try:
                p = tipos.CATALOGO[clave].defectos()
                p.update(q)
                return tipos.generar(clave, p, estado['sustrato'])
            except Exception:
                pass
        return estado['antena']

    def pintar_simulacion(r, d):
        sim['mostrada'] = (r, d)            # para repintarla al cambiar de tema
        lo, hi = banda_actual()
        res_sim.clear()
        with res_sim:
            with ui.card().classes('w-full'):
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
                         ('Eficiencia de radiación / total',
                          f"{r['eficiencia_radiacion_%']:g} % / {r['eficiencia_total_%']:g} %"),
                         ('Malla / tiempo', f"{r['celdas']/1e6:.2f} M celdas, paso {r['paso_malla_mm']} mm, "
                                            f"{r['tiempo_s']:g} s")]
                cubre = bool(r['banda_MHz']) and r['banda_MHz'][0] <= lo and r['banda_MHz'][1] >= hi
                with ui.row().classes('items-center no-wrap'):
                    ui.icon('check_circle' if cubre else 'cancel', color='positive' if cubre else 'negative')
                    ui.label('La simulación cubre la banda' if cubre else 'La simulación NO cubre la banda entera'
                             ).classes('text-caption text-weight-medium')
                with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-0'):
                    for k, v in filas:
                        ui.label(k).classes('text-caption texto-sec')
                        ui.label(v).classes('text-caption text-weight-medium')
                if r.get('historial'):
                    ui.label('Ajuste: ' + ' → '.join(f"{h['escala_mm']} mm: {h['f_resonancia_MHz']} MHz "
                                                    f"({h['error_%']:+} %)" for h in r['historial'])
                             ).classes('text-caption')
                    ui.button('Aplicar los parámetros ajustados', icon='done_all',
                              on_click=lambda q=r['parametros']: aplicar_ajustados(q)) \
                        .props('outline color=deep-purple no-caps')
            with ui.row().classes('w-full wrap gap-2'):
                banda = (lo*1e6, hi*1e6)
                f_obj = estado['f_MHz']*1e6
                ui.plotly(T(graficas.s11(d['f'], d['s11'], banda))).classes('grow basis-[300px] h-[300px]')
                ui.plotly(T(graficas.roe(d['f'], d['s11'], banda, f_obj))).classes('grow basis-[300px] h-[300px]')
                ui.plotly(T(graficas.smith(d['f'], d['s11'], banda, f_obj))).classes('grow basis-[300px] h-[300px]')
            if d['d'].size:
                with ui.row().classes('w-full wrap gap-2'):
                    ui.plotly(T(graficas.cortes_polares(d['theta'], d['phi'], d['d']))).classes('grow basis-[320px] h-[420px]')
                    ui.plotly(T(graficas.diagrama_3d(d['theta'], d['phi'], d['d'], antena=antena_simulada(r),
                                                     h_mm=tipos.sustrato(estado['sustrato']).h))
                              ).classes('grow basis-[420px] h-[420px]')

    def repintar_graficas():
        """Vuelve a dibujar las gráficas visibles con el tema actual."""
        if estado['antena'] is not None:
            grafico.update_figure(T(vista.figura_plotly(estado['antena'])))
        if sim.get('mostrada'):
            pintar_simulacion(*sim['mostrada'])
        pintar_comparacion()
        res_asist.clear()                   # la carta de Smith del asistente se rehace al volver a analizar

    def aplicar_ajustados(q):
        marcar_cambio()
        poner_params({k: v for k, v in q.items() if not k.startswith('_')})
        ui.notify('Parámetros ajustados aplicados. Guarda el diseño para conservarlos.', type='positive')

    ui.timer(0.5, vigilar)

    # ================================================================== medidas
    visibles = {}            # fichero -> mostrar en la comparación

    def mostrar_medidas():
        lista_medidas.clear()
        cont_comparacion.clear()
        n = estado['diseno']
        if not n:
            with lista_medidas:
                ui.label('Guarda el diseño (o haz una medida) para ver aquí sus medidas y su simulación.'
                         ).classes('text-caption texto-sec')
            return
        ms = biblioteca.medidas(n)
        sim_g = biblioteca.leer_simulacion(n)
        with lista_medidas:
            if not ms and not sim_g:
                ui.label('Este diseño aún no tiene simulación ni medidas.').classes('text-caption texto-sec')
            if sim_g:
                r = sim_g[0]
                ui.checkbox(f"Simulación ({r['f_resonancia_MHz']:g} MHz, {r.get('precision', '')})",
                            value=visibles.get('_sim', True),
                            on_change=lambda e: (visibles.__setitem__('_sim', e.value), pintar_comparacion()))
            for fichero, meta in ms:
                texto = meta.get('etiqueta') or fichero[:15]
                with ui.row().classes('w-full items-center no-wrap gap-1'):
                    ui.checkbox(f"{texto} · {meta.get('fecha', '')} · {meta.get('origen', '')}",
                                value=visibles.get(fichero, True),
                                on_change=lambda e, f=fichero: (visibles.__setitem__(f, e.value), pintar_comparacion())
                                ).classes('grow')
                    if meta.get('notas'):
                        ui.icon('notes', color='grey-7').tooltip(meta['notas'])
                    ui.button('Analizar', icon='build', on_click=lambda f=fichero, t=texto: analizar_medida(f, t)) \
                        .props('flat dense no-caps color=teal')
                    ui.button(icon='download',
                              on_click=lambda f=fichero: ui.download(os.path.join(biblioteca.carpeta(n, 'medidas'), f))
                              ).props('flat dense round').tooltip('Descargar .s1p')
        pintar_comparacion()

    def pintar_comparacion():
        cont_comparacion.clear()
        n = estado['diseno']
        if not n:
            return
        curvas = []
        sim_g = biblioteca.leer_simulacion(n)
        if sim_g and visibles.get('_sim', True):
            curvas.append(('Simulación', sim_g[1]['f'], sim_g[1]['s11'], True))
        for fichero, meta in biblioteca.medidas(n):
            if not visibles.get(fichero, True):
                continue
            try:
                f, s = biblioteca.leer_medida(n, fichero)
            except Exception:
                continue
            curvas.append((meta.get('etiqueta') or fichero[:15], f, s, False))
        if not curvas:
            return
        lo, hi = banda_actual()
        fig = graficas.s11_comparada(curvas, (lo*1e6, hi*1e6))
        if sim_g:   # encuadre: la banda de la simulación (las medidas suelen ser mucho más anchas)
            fs = sim_g[1]['f']
            fig.update_xaxes(range=[fs.min()/1e6, fs.max()/1e6])
        with cont_comparacion:
            ui.plotly(T(fig)).classes('w-full h-[360px]')

    def analizar_medida(fichero, texto):
        try:
            f, s11 = biblioteca.leer_medida(estado['diseno'], fichero)
        except Exception as ex:
            ui.notify(f'No se puede leer la medida: {ex}', type='negative')
            return
        mostrar_asistente(f, s11, f'Medida «{texto}»')

    def recomendacion(f, s11):
        a = estado['antena']
        s = tipos.sustrato(estado['sustrato'])
        w50 = ancho_microstrip(50, s.er, s.h)
        return ajuste.asistente(a, f, s11, estado['f_MHz']*1e6, ajuste.distancia_conector_a_red(a),
                                eps_eff_microstrip(s.er, s.h, w50))

    def mostrar_asistente(f, s11, origen, anterior=None):
        a = estado['antena']
        if a is None:
            return
        rec = recomendacion(f, s11)
        res_asist.clear()
        with res_asist:
            if anterior is not None:
                try:
                    (fa, sa), etiqueta_a = anterior
                    ra = recomendacion(fa, sa)
                    d = rec['f_medida_MHz'] - ra['f_medida_MHz']
                    ui.label(f'Respecto a «{etiqueta_a}»: resonancia {ra["f_medida_MHz"]:g} → {rec["f_medida_MHz"]:g} MHz '
                             f'({d:+.1f} MHz); en el objetivo {ra["s11_en_f_obj_dB"]:g} → {rec["s11_en_f_obj_dB"]:g} dB'
                             ).classes('text-caption texto-violeta')
                except Exception:
                    pass
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
            lo, hi = banda_actual()
            ui.plotly(T(graficas.smith(f, s11, (lo*1e6, hi*1e6), estado['f_MHz']*1e6))).classes('w-full h-[300px]')

    def nueva_medida(f, s11, origen):
        """Guarda la medida en el diseño, la añade a la comparación y la analiza."""
        if not asegurar_guardado():
            return       # hay que confirmar antes de pisar otro diseño; la medida se pierde: avisar
        etiqueta = (etiqueta_in.value or '').strip()
        anterior = None
        previas = biblioteca.medidas(estado['diseno'])
        if previas:
            fich, meta = previas[-1]
            try:
                anterior = (biblioteca.leer_medida(estado['diseno'], fich), meta.get('etiqueta') or fich[:15])
            except Exception:
                pass
        ruta = biblioteca.guardar_medida(estado['diseno'], f, s11, origen, etiqueta, notas_medida.value or '')
        etiqueta_in.value = ''
        notas_medida.value = ''
        mostrar_medidas()
        refrescar_biblioteca()
        mostrar_asistente(f, s11, f'Medida «{etiqueta or os.path.basename(ruta)}»', anterior)
        ui.notify(f'Medida guardada en el diseño «{estado["diseno"]}»', type='positive')

    async def subir_s1p(e):
        try:
            datos = await e.file.read()          # NiceGUI 3
            nombre = e.file.name
        except AttributeError:
            datos = e.content.read()             # NiceGUI 2
            nombre = e.name
        subida.reset()
        try:
            f, s11 = ajuste.leer_s1p(datos.decode('utf-8', errors='replace'))
        except Exception as ex:
            ui.notify(f'No se puede leer el .s1p: {ex}', type='negative')
            return
        if not len(f):
            ui.notify('El .s1p no tiene datos', type='negative')
            return
        if not etiqueta_in.value:
            etiqueta_in.value = os.path.splitext(nombre)[0]
        nueva_medida(f, s11, f'subida ({nombre})')

    # ================================================================== asistente del NanoVNA
    vna = {'cal_guiada': None, 'vivo': False, 'ultima': None}

    def _modulo_vna():
        import asistente_vna
        return asistente_vna

    async def tarea_vna(boton, funcion, *args):
        """Ejecuta una operación del NanoVNA fuera del hilo de la interfaz, con el botón en espera."""
        boton.props('loading')
        try:
            return await run.io_bound(funcion, *args)
        except Exception as ex:
            ui.notify(f'NanoVNA: {ex}', type='negative', multi_line=True)
            return None
        finally:
            boton.props(remove='loading')

    async def conectar_click():
        av = _modulo_vna()
        i = await tarea_vna(btn_conectar, av.info_equipo)
        if i is None:
            info_vna.text = 'No se ha podido conectar.'
            return
        ini, fin, pts = i['barrido']
        info_vna.text = (f"{i['version'].split()[0] if i['version'] else 'NanoVNA'} en {i['puerto']} · barrido "
                         f"{ini/1e6:g}–{fin/1e6:g} MHz, {pts} puntos · calibración del equipo: {i['cal'] or '—'}")
        pasos_vna.next()

    def mostrar_modo_cal():
        cont_cal_guardada.set_visibility(modo_cal.value == 0)
        cont_cal_nueva.set_visibility(modo_cal.value == 1)

    def sugerir_calibracion():
        """Rango y nombre propuestos a partir de la frecuencia del diseño."""
        av = _modulo_vna()
        lo, hi = av.rango_sugerido(estado['f_MHz']*1e6)
        cal_ini.value, cal_fin.value = round(lo/1e6, 1), round(hi/1e6, 1)
        cal_nombre.value = f"cal_{lo/1e6:.0f}_{hi/1e6:.0f}M_{time.strftime('%Y%m%d')}"

    def mostrar_info_cal():
        info_cal.text = ''
        if not sel_cal.value:
            info_cal.text = 'No hay calibraciones guardadas: calibra ahora.'
            return
        i = _modulo_vna().info_calibracion(sel_cal.value)
        if not i:
            return
        lo, hi = banda_actual()
        dentro = i['f_ini_Hz'] <= lo*1e6 and i['f_fin_Hz'] >= hi*1e6
        info_cal.text = (f"{i['f_ini_Hz']/1e6:g}–{i['f_fin_Hz']/1e6:g} MHz, {i['puntos']} puntos, "
                         f"{', '.join(i['estandares']).upper()} · {i['fecha'][:16].replace('T', ' ')}"
                         + ('' if dentro else ' · ⚠ no cubre la banda del diseño'))
        info_cal.classes(replace='text-caption ' + ('' if dentro else 'text-negative'))

    def pintar_pasos_cal():
        filas_cal.clear()
        cg = vna['cal_guiada']
        btn_cal_guardar.set_visibility(cg is not None)
        if cg is None:
            return
        textos = {'open': 'Pon el OPEN (abierto)', 'short': 'Pon el SHORT (cortocircuito)',
                  'load': 'Pon la CARGA de 50 Ω'}
        with filas_cal:
            for paso in cg.PASOS:
                hecho = paso in cg.hechos()
                with ui.row().classes('w-full items-center no-wrap gap-2'):
                    ui.icon('check_circle' if hecho else 'radio_button_unchecked',
                            color='positive' if hecho else 'grey-6')
                    ui.label(textos[paso]).classes('text-caption grow')
                    b = ui.button(paso.upper(), icon='straighten').props(
                        f'{"flat" if hecho else ""} dense color=teal no-caps')
                    b.on_click(lambda e, p=paso, b=b: medir_estandar(p, b))

    def empezar_calibracion():
        try:
            nombre = biblioteca.nombre_valido(cal_nombre.value)
            vna['cal_guiada'] = _modulo_vna().CalibracionGuiada(nombre, float(cal_ini.value)*1e6,
                                                                float(cal_fin.value)*1e6, int(cal_pts.value))
        except Exception as ex:
            ui.notify(f'No se puede empezar: {ex}', type='negative')
            return
        res_cal.text = (f'{cal_ini.value:g}–{cal_fin.value:g} MHz, {int(cal_pts.value)} puntos '
                        f'({-(-int(cal_pts.value)//101)} barridos por estándar).')
        pintar_pasos_cal()

    async def medir_estandar(paso, boton):
        cg = vna['cal_guiada']
        r = await tarea_vna(boton, cg.medir, paso)
        if r is None:
            return
        bien, texto = r
        if bien:
            ui.notify(f'{paso.upper()} medido. {texto}', type='positive')
        else:
            ui.notify(f'{paso.upper()} NO guardado: {texto}', type='warning', multi_line=True)
        pintar_pasos_cal()

    async def guardar_calibracion():
        cg = vna['cal_guiada']
        if cg is None:
            return
        r = await tarea_vna(btn_cal_guardar, cg.terminar)
        if r is None:
            return
        nombre, errores = r
        res_cal.text = ('Guardada. Autocomprobación: ' +
                        ', '.join(f'{k.upper()} {v:.0e}' for k, v in errores.items()))
        import calibracion as _c
        sel_cal.options = _c.listar()
        sel_cal.value = nombre
        sel_cal.update()
        vna['cal_guiada'] = None
        pintar_pasos_cal()
        modo_cal.value = 0
        ui.notify(f'Calibración «{nombre}» guardada en vna/calibraciones', type='positive')
        pasos_vna.next()

    async def verificar_click():
        if not sel_cal.value:
            ui.notify('Elige o haz antes una calibración', type='warning')
            return
        r = await tarea_vna(btn_verif, _modulo_vna().verificar, sel_cal.value)
        if r is None:
            return
        bien = r['max_dB'] < -25
        res_verif.text = (f"|S11| con la carga: mediana {r['mediana_dB']:.1f} dB, peor {r['max_dB']:.1f} dB "
                          f"a {r['f_max_MHz']:.0f} MHz · " + ('bien' if bien else
                          'revisa: ¿está la carga puesta? Si sí, el latiguillo o los conectores han cambiado: recalibra'))
        res_verif.classes(replace='text-caption ' + ('text-positive' if bien else 'text-negative'))

    def ventana_medida(ancho=0.5):
        """Intervalo de medida alrededor de la frecuencia objetivo (±ancho/2 relativo)."""
        f0 = estado['f_MHz']*1e6
        return f0*(1 - ancho/2), f0*(1 + ancho/2)

    async def medir_click():
        if not sel_cal.value:
            ui.notify('Elige o haz antes una calibración', type='warning')
            return
        r = await tarea_vna(btn_medir, _modulo_vna().medir, sel_cal.value, *ventana_medida(1.0))
        if r is not None:
            nueva_medida(r[0], r[1], f'NanoVNA ({sel_cal.value})')

    async def bucle_vivo():
        av = _modulo_vna()
        while vna['vivo']:
            try:
                f, s11 = await run.io_bound(av.medir, sel_cal.value, *ventana_medida(0.5))
            except Exception as ex:
                ui.notify(f'NanoVNA: {ex}', type='negative', multi_line=True)
                sw_vivo.value = False
                break
            vna['ultima'] = (f, s11)
            lo, hi = banda_actual()
            vivo_graf.update_figure(T(graficas.s11(f, s11, (lo*1e6, hi*1e6))))
            a = estado['antena']
            try:
                s = tipos.sustrato(estado['sustrato'])
                w50 = ancho_microstrip(50, s.er, s.h)
                rec = ajuste.asistente(a, f, s11, estado['f_MHz']*1e6, ajuste.distancia_conector_a_red(a),
                                       eps_eff_microstrip(s.er, s.h, w50))
                vivo_txt.text = (f'{time.strftime("%H:%M:%S")} · resonancia {rec["f_medida_MHz"]:g} MHz '
                                 f'({rec["desvio_%"]:+g} %) · en el objetivo {rec["s11_en_f_obj_dB"]:g} dB · '
                                 + (rec['acciones'][0] if rec['acciones'] else ''))
            except Exception:
                db = 20*np.log10(np.abs(s11))
                vivo_txt.text = f'{time.strftime("%H:%M:%S")} · S11 mínimo {db.min():.1f} dB a {f[db.argmin()]/1e6:.1f} MHz'
            await asyncio.sleep(0.3)

    def cambiar_vivo(e):
        if e.value and not sel_cal.value:
            ui.notify('Elige o haz antes una calibración', type='warning')
            sw_vivo.value = False
            return
        vna['vivo'] = bool(e.value)
        vivo_graf.set_visibility(vna['vivo'])
        btn_guardar_vivo.set_visibility(vna['vivo'])
        if vna['vivo']:
            background_tasks.create(bucle_vivo(), name='medida_en_vivo')
        else:
            vivo_txt.text = ''

    def guardar_vivo():
        if vna['ultima'] is None:
            return
        f, s11 = vna['ultima']
        nueva_medida(f, s11, f'NanoVNA en vivo ({sel_cal.value})')

    # ================================================================== exportación
    def exportar_click():
        a = estado['antena']
        if a is None or not asegurar_guardado():
            return
        nombre = estado['diseno']
        carpeta = biblioteca.carpeta(nombre, 'fabricacion')
        try:
            titulo = f"{tipos.CATALOGO[a.tipo].nombre.split(' (')[0]} {a.info.get('f_estimada_MHz')} MHz"
            r = exportar.exportar_todo(a, carpeta, nombre, titulo)
        except Exception as ex:
            ui.notify(f'Error al exportar: {ex}', type='negative', multi_line=True)
            return
        refrescar_biblioteca()
        res_export.clear()
        with res_export:
            with ui.row().classes('items-center no-wrap'):
                ui.label(f'Guardado en {carpeta}').classes('text-caption')
                ui.button(icon='folder_open', on_click=lambda: os.startfile(carpeta)).props('flat round dense')
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
        ui.notify(f'Exportado en el diseño «{nombre}»', type='positive')

    # ================================================================== eventos
    sel_tipo.on_value_change(cambiar_tipo)
    banda.on_value_change(cambiar_banda)
    f_in.on_value_change(cambiar_f)
    bw_in.on_value_change(cambiar_bw)
    btn_bw.on_click(ampliar_bw)
    btn_sim.on_click(simular_click)
    sel_sus.on_value_change(lambda e: None if estado.get('silencio') else
                            (estado.update(sustrato=e.value), marcar_cambio(), regenerar()))
    sel_reg.on_value_change(lambda e: None if estado.get('silencio') else
                            (estado.update(reglas=e.value), marcar_cambio(), mostrar_drc()))
    btn_ajustar.on_click(lambda: (marcar_cambio(), ajustar()))
    btn_export.on_click(exportar_click)
    btn_guardar.on_click(lambda: guardar_diseno())
    nombre_in.on('keydown.enter', lambda: guardar_diseno())
    subida.on_upload(subir_s1p)
    btn_medir.on_click(medir_click)
    btn_conectar.on_click(conectar_click)
    modo_cal.on_value_change(lambda e: mostrar_modo_cal())
    sel_cal.on_value_change(lambda e: mostrar_info_cal())
    btn_cal_empezar.on_click(empezar_calibracion)
    btn_cal_guardar.on_click(guardar_calibracion)
    btn_verif.on_click(verificar_click)
    sw_vivo.on_value_change(cambiar_vivo)
    btn_guardar_vivo.on_click(guardar_vivo)
    pestanas.on_value_change(lambda e: (sugerir_calibracion(), mostrar_info_cal()) if e.value == 'Medir' else None)
    btn_abrir.on_click(lambda: (n := seleccionado()) and abrir_diseno(n))
    btn_carpeta.on_click(lambda: (n := seleccionado()) and os.startfile(biblioteca.carpeta(n)))
    btn_renombrar.on_click(renombrar_click)
    btn_archivar.on_click(archivar_click)
    btn_notas.on_click(guardar_notas)
    tabla_bib.on('rowDblclick', lambda e: abrir_diseno(e.args[1]['nombre']))

    mostrar_rango()
    construir_params()
    ajustar()
    estado['sucio'] = False
    actualizar_cabecera()
    refrescar_biblioteca()
    mostrar_medidas()
    ui.timer(0.05, aplicar_tema, once=True)    # en «auto» pregunta al navegador si el sistema está en oscuro
    ui.context.client.on_disconnect(lambda: vna.update(vivo=False))   # no seguir midiendo sin nadie delante
    mostrar_modo_cal()
    pintar_pasos_cal()
    sugerir_calibracion()
    mostrar_info_cal()


if __name__ in {'__main__', '__mp_main__'}:
    # CHIRPTENNA_ABRIR=1 (lo pone iniciar.bat) abre el navegador al arrancar.
    # Solo se escucha en este ordenador: NiceGUI usa 0.0.0.0 por defecto y cualquiera en la misma red podría
    # simular, escribir archivos o usar el NanoVNA. CHIRPTENNA_HOST=0.0.0.0 lo abre a la red a propósito.
    ui.run(title='Chirptenna', host=os.environ.get('CHIRPTENNA_HOST', '127.0.0.1'), port=8080, reload=False,
           show=os.environ.get('CHIRPTENNA_ABRIR') == '1', favicon=LOGO if os.path.exists(LOGO) else '📡',
           dark=False)
