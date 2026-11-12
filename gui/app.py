"""Interfaz gráfica de Chirptenna (NiceGUI, se abre en el navegador).

Chirptenna · Copyright (C) 2026 sqtactical · Software libre bajo la GNU AGPL v3.0 (ver LICENSE).

Uso: python gui/app.py   ->   http://localhost:8080

Organización por fases: una barra fija con el diseño (nombre, tipo y banda) y pestañas
Diseño → Simulación → Fabricar → Medir → Mis diseños. Los diseños se guardan en
Documentos\\Chirptenna\\disenos (módulo `antenas.biblioteca`).
"""
import os
import sys
import contextlib
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
from antenas import guia, gpu, entorno   # noqa: E402
from antenas import i18n   # noqa: E402
from antenas.i18n import tr   # noqa: E402
from antenas import __version__   # noqa: E402
from antenas.materiales import ancho_microstrip, eps_eff_microstrip   # noqa: E402

sys.path.insert(0, os.path.join(RAIZ, 'vna'))   # driver del NanoVNA y calibración del PC
from antenas.simulacion import PRECISIONES   # noqa: E402
from antenas.materiales import SUSTRATOS, SUSTRATO_POR_DEFECTO   # noqa: E402

DIR_SALIDAS = os.path.join(RAIZ, 'salidas')
URL_PROYECTO = 'https://github.com/sqtactical/chirptenna'
# Si publicas una versión modificada como servicio por red, la AGPL-3.0 te obliga a ofrecer su código:
# cambia URL_PROYECTO por la dirección de tu código.
LOGO = os.path.join(RAIZ, 'docs', 'logo', 'chirptenna.png')
# Bandas, serigrafía, etiquetas y formatos: compartidos con la versión web (antenas/presentacion.py)
from antenas import presentacion   # noqa: E402
from antenas.presentacion import (BANDAS, SERIGRAFIA_OPCIONES, LOGO_OPCIONES, AVISO_SIN_LOGO,   # noqa: E402
                                  SERIGRAFIA_DEFECTO)

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

estado['serigrafia'] = dict(SERIGRAFIA_DEFECTO)
_banda_de = presentacion.banda_de
ICONOS_CONSEJO = {'banda': ('podcasts', 'deep-orange'), 'diseño': ('lightbulb', 'amber-8'),
                  'montaje': ('construction', 'blue-grey'), 'medida': ('straighten', 'teal')}


def _titulo_card(texto, icono=None):
    with ui.row().classes('items-center gap-1 no-wrap'):
        if icono:
            ui.icon(icono).classes('icono-titulo')
        ui.label(texto).classes('text-subtitle1 text-weight-medium')


PESTANAS_URL = ('galeria', 'diseno', 'simulacion', 'fabricar', 'medir', 'disenos')
DIR_MINIATURAS = os.path.join(RAIZ, 'antenas', 'miniaturas')
COLOR_ESTADO = {'validada': 'positive', 'pendiente': 'orange-8', 'no_funciona': 'negative'}


def _orden_galeria():
    """Claves de los tipos en el orden de la galería (por grupo de uso)."""
    orden = [g[0] for g in guia.GRUPOS]
    return sorted(tipos.CATALOGO, key=lambda k: orden.index(guia.info_tipo(k)[0]))


def _etiqueta_tipo(clave):
    """Etiqueta del selector de tipos: «nombre|resumen|estado|comentario» (la parte el slot de la lista)."""
    est, comentario = problemas.estado(clave)
    return '|'.join([tr(tipos.CATALOGO[clave].nombre), tr(guia.info_tipo(clave)[1]), est, tr(comentario),
                     tr(problemas.ESTADO_TEXTO[est])])


def _miniatura(clave):
    """SVG de la galería (antenas/miniaturas, generadas con herramientas/generar_miniaturas.py)."""
    ruta = os.path.join(DIR_MINIATURAS, f'{clave}.svg')
    if os.path.exists(ruta):
        with open(ruta, encoding='utf-8') as fh:
            return fh.read()
    from antenas import miniaturas
    return miniaturas.svg(clave)


# Lista desplegable de tipos con descripción y estado (Quasar): la etiqueta lleva los campos separados por «|»
SLOT_OPCION_TIPO = r'''
<q-item v-bind="props.itemProps">
  <q-item-section>
    <q-item-label>
      {{ props.opt.label.split('|')[0] }}
      <q-badge v-if="props.opt.label.split('|')[2] !== 'validada'" class="q-ml-xs"
               :color="props.opt.label.split('|')[2] === 'no_funciona' ? 'negative' : 'orange-8'">
        {{ props.opt.label.split('|')[4] }}
      </q-badge>
    </q-item-label>
    <q-item-label caption>{{ props.opt.label.split('|')[1] }}</q-item-label>
    <q-item-label caption v-if="props.opt.label.split('|')[2] !== 'validada'">⚠ {{ props.opt.label.split('|')[3] }}</q-item-label>
  </q-item-section>
</q-item>'''
SLOT_ELEGIDO_TIPO = r'''<span>{{ props.opt.label.split('|')[0] }}</span>'''


@ui.page('/')
def pagina(pestana: str = '', diseno: str = '', tema: str = '', idioma: str = ''):
    """Página única. Parámetros de la URL (opcionales), p. ej. `/?diseno=mi_yagi&pestana=simulacion`:
    pestana (una de PESTANAS_URL), diseno (nombre en «Mis diseños») y tema ('claro'/'oscuro', sin guardarlo)."""
    # idioma: el de la URL (sin guardarlo), si no el guardado, si no CHIRPTENNA_IDIOMA o el castellano
    i18n.fijar_idioma(i18n.idioma_inicial(idioma or app.storage.general.get('idioma')))
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
        .tarjeta-tipo { transition: box-shadow .15s, transform .15s; }
        .tarjeta-tipo .q-badge { margin-top: auto; align-self: flex-start; }
        .tarjeta-tipo:hover { box-shadow: 0 3px 10px rgba(0,0,0,.18); transform: translateY(-2px); }
        .miniatura svg { width: 200px; height: 110px; display: block; }
        .ayuda-param { color: #78909c; cursor: help; }
        .body--dark .ayuda-param { color: #90a4ae; }
        .q-field__label { font-size: 0.82rem; }
        .q-tab__label { font-size: 0.85rem; }
    ''')
    # ================================================================== cabecera
    # Easter egg: 5 pinchazos seguidos en el grillo pasan al «idioma LoRa» (y otros 5 lo quitan)
    clics_logo = {'n': 0, 't': 0.0}

    def clic_logo():
        ahora = time.time()
        clics_logo['n'] = clics_logo['n'] + 1 if ahora - clics_logo['t'] < 1.5 else 1
        clics_logo['t'] = ahora
        if clics_logo['n'] >= 5:
            clics_logo['n'] = 0
            app.storage.general['idioma'] = i18n.IDIOMA_BASE if i18n.idioma() == i18n.IDIOMA_LORA else i18n.IDIOMA_LORA
            ui.navigate.to('/')

    with ui.header().classes('bg-blue-grey-9 items-center q-py-xs gap-3'):
        if os.path.exists(LOGO):
            ui.image(LOGO).classes('w-9 h-9').on('click', clic_logo)
        ui.label(tr('Chirptenna')).classes('text-h6')
        ui.label(tr('antenas impresas para PCB')).classes('text-caption text-blue-grey-2 gt-xs')
        ui.badge(f'v{__version__}', color='orange-9').props('outline').classes('gt-xs') \
            .tooltip(tr('Alpha: validado solo en simulación. Mide siempre la antena fabricada.'))
        ui.space()
        sel_idioma = ui.select(i18n.idiomas(), value=i18n.idioma()).props('dense borderless options-dense dark') \
            .classes('text-caption w-28').tooltip(tr('Idioma de la interfaz'))
        lbl_diseno = ui.label().classes('text-subtitle2')
        lbl_resumen = ui.label().classes('text-caption text-blue-grey-2 gt-sm')
        btn_tema = ui.button().props('flat round dense color=white')

    # ================================================================== tema claro / oscuro
    # 'auto' sigue al sistema; la preferencia se guarda en app.storage.general (.nicegui/ en la raíz)
    modo_oscuro = ui.dark_mode()
    tema_url = {'claro': 'claro', 'oscuro': 'oscuro'}.get(tema)
    tema = {'modo': tema_url or app.storage.general.get('tema', 'auto'), 'oscuro': False}
    if tema['modo'] != 'auto':              # modo fijo: se aplica ya, antes de dibujar nada
        tema['oscuro'] = tema['modo'] == 'oscuro'
        modo_oscuro.value = tema['oscuro']
    ICONOS_TEMA = {'auto': ('brightness_auto', tr('Tema: automático (como el sistema)')),
                   'claro': ('light_mode', tr('Tema: claro')), 'oscuro': ('dark_mode', tr('Tema: oscuro'))}

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
        for traza in fig.data:
            linea = getattr(traza, 'line', None)
            if linea is not None and linea.color in ('#444', 'black', '#999', '#ddd'):
                traza.line.color = {'#999': '#777', '#ddd': '#3f4449'}.get(linea.color, '#cfd8dc')
            if getattr(traza, 'mode', None) == 'text':
                traza.textfont.color = texto
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

    def cambiar_idioma(e):
        if e.value == i18n.idioma():
            return
        app.storage.general['idioma'] = e.value
        ui.navigate.to('/')            # la página se reconstruye entera con el idioma nuevo (y sin parámetros de URL)

    sel_idioma.on_value_change(cambiar_idioma)

    # ================================================================== barra del diseño (siempre visible)
    with ui.card().classes('w-full barra-diseno q-pa-sm').props('flat bordered'):
        with ui.row().classes('w-full items-end wrap gap-x-3 gap-y-1'):
            nombre_in = ui.input(tr('Nombre del diseño'), value='antena').classes('w-48')
            sel_tipo = ui.select({k: _etiqueta_tipo(k) for k in _orden_galeria()}, value=estado['clave'],
                                 label=tr('Tipo de antena')).classes('w-80')
            sel_tipo.add_slot('option', SLOT_OPCION_TIPO)
            sel_tipo.add_slot('selected-item', SLOT_ELEGIDO_TIPO)
            with ui.column().classes('gap-0'):
                ui.label(tr('Banda de uso')).classes('text-caption texto-sec')
                banda = ui.select({k: tr(k) for k in BANDAS}, value='2,4 GHz').props('dense outlined options-dense').classes('w-48')
            f_in = ui.number(tr('Centro [MHz]'), value=estado['f_MHz'], min=100, max=10000, step=0.005,
                             format='%.3f').classes('w-32')
            bw_in = ui.number(tr('Ancho [MHz]'), value=estado['bw_MHz'], min=0.05, max=5000, step=0.05,
                              format='%.2f').classes('w-28')
            rango = ui.label().classes('text-caption texto-sec self-center')
            ui.space()
            btn_guardar = ui.button(tr('Guardar diseño'), icon='save').props('color=primary no-caps')
        desc = ui.label().classes('text-caption texto-sec')
        cont_problemas = ui.column().classes('w-full gap-0')

    # ================================================================== pestañas
    with ui.tabs().classes('w-full pestanas').props('align=left inline-label no-caps') as pestanas:
        t_gal = ui.tab(tr('Elegir antena'), icon='apps')
        t_diseno = ui.tab(tr('Diseño'), icon='architecture')
        t_sim = ui.tab(tr('Simulación'), icon='insights')
        t_fab = ui.tab(tr('Fabricar'), icon='precision_manufacturing')
        t_medir = ui.tab(tr('Medir'), icon='settings_input_antenna')
        t_bib = ui.tab(tr('Mis diseños'), icon='folder_special')

    with ui.tab_panels(pestanas, value=t_gal).classes('w-full bg-transparent'):
        # -------------------------------------------------------------- 0. Galería de tipos
        with ui.tab_panel(t_gal).classes('q-pa-sm'):
            with ui.row().classes('w-full items-center gap-2'):
                ui.label(tr('Elige el tipo de antena')).classes('text-h6')
                ui.space()
                ui.button(tr('Abrir un diseño guardado'), icon='folder_open',
                          on_click=lambda: pestanas.set_value(t_bib)).props('outline no-caps')
            ui.label(tr('Al elegirla se dimensiona para la banda de la barra de arriba. Solo verás los parámetros '
                     'básicos; el resto está en «Ajustes avanzados». Todo está validado solo en simulación.')
                     ).classes('text-caption texto-sec')
            for g_clave, g_titulo, g_desc in guia.GRUPOS:
                claves = [k for k in _orden_galeria() if guia.info_tipo(k)[0] == g_clave]
                if not claves:
                    continue
                if g_clave == 'experimental':
                    # plegado: un usuario nuevo no debe ver primero lo que no funciona o está sin validar
                    marco = ui.expansion(tr(g_titulo), caption=tr(g_desc), icon='science').classes('w-full q-mt-md')
                else:
                    marco = contextlib.nullcontext()
                    ui.label(tr(g_titulo)).classes('text-subtitle1 text-weight-medium q-mt-md')
                    ui.label(tr(g_desc)).classes('text-caption texto-sec')
                with marco, ui.row().classes('w-full wrap gap-3 items-stretch'):
                    for k in claves:
                        est, comentario = problemas.estado(k)
                        with ui.card().classes('w-60 cursor-pointer tarjeta-tipo q-pa-sm') \
                                .on('click', lambda k=k: elegir_tipo(k)):
                            ui.html(_miniatura(k), sanitize=False).classes('miniatura self-center')
                            ui.label(tr(tipos.CATALOGO[k].nombre).split(' (')[0]).classes('text-weight-medium')
                            ui.label(tr(guia.info_tipo(k)[1])).classes('text-caption')
                            ui.badge(tr(problemas.ESTADO_TEXTO[est]), color=COLOR_ESTADO[est]) \
                                .props('outline' if est == 'validada' else '').tooltip(tr(comentario))

        # -------------------------------------------------------------- 1. Diseño
        with ui.tab_panel(t_diseno).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.column().classes('w-full sm:w-[380px] gap-2'):
                    with ui.card().classes('w-full'):
                        _titulo_card(tr('Tamaño y material'), 'straighten')
                        sel_sus = ui.select({k: tr(k) for k in SUSTRATOS}, value=estado['sustrato'], label=tr('Sustrato')).classes('w-full')
                        btn_ajustar = ui.button(tr('Ajustar tamaño a la frecuencia'), icon='tune') \
                            .props('color=primary no-caps').classes('w-full')
                        btn_bw = ui.button(tr('Ampliar ancho de banda'), icon='open_in_full') \
                            .props('outline color=primary no-caps').classes('w-full')
                        aviso_ajuste = ui.label().classes('text-caption text-orange-9')
                    with ui.card().classes('w-full'):
                        _titulo_card(tr('Parámetros'), 'tune')
                        cont_params = ui.column().classes('w-full gap-0')
                with ui.column().classes('grow basis-[320px] min-w-0 gap-2'):
                    with ui.card().classes('w-full'):
                        grafico = ui.plotly({}).classes('w-full h-[560px]')
                    with ui.row().classes('w-full wrap items-start gap-2'):
                        with ui.card().classes('grow basis-[280px]'):
                            _titulo_card(tr('Resultado (estimación)'), 'analytics')
                            tabla_info = ui.column().classes('w-full gap-0')
                        with ui.card().classes('grow basis-[280px]'):
                            _titulo_card(tr('Consejos'), 'lightbulb')
                            lista_consejos = ui.column().classes('w-full gap-1')

        # -------------------------------------------------------------- 2. Simulación
        with ui.tab_panel(t_sim).classes('q-pa-sm'):
            with ui.card().classes('w-full'):
                _titulo_card(tr('Simulación con openEMS'), 'insights')
                with ui.row().classes('w-full items-center wrap gap-2'):
                    sel_prec = ui.select(list(PRECISIONES), value='normal', label=tr('Precisión')).classes('w-32')
                    chk_ajustar = ui.checkbox(tr('Ajustar a la frecuencia simulando'), value=True)
                    gpu_ok, gpu_motivo = gpu.disponible()
                    chk_malla = ui.checkbox(tr('Verificar con otra malla'), value=False).tooltip(
                        tr('Repite la simulación con el paso de malla un 15 % menor y un 15 % mayor y avisa si el resultado '
                           'cambia mucho (tarda el triple). Se hace siempre con dos bandas, paneles y arrays.'))
                    sel_entorno = ui.select({k: tr(v) for k, v in entorno.PREDEFINIDOS.items()}, value=[], multiple=True, clearable=True,
                                            label=tr('Entorno')).classes('w-64').tooltip(
                        tr('Simula además con una carcasa de ABS, una batería metálica o una mano cerca y dice cuánto cambian la frecuencia y la '
                           'eficiencia (2 simulaciones más).'))
                    chk_gpu = ui.checkbox(tr('Aceleración por GPU (experimental)'), value=gpu_ok)
                    if gpu_ok:
                        chk_gpu.tooltip(tr('Usa el openEMS compilado con motor GPU: en las pruebas, ~10× más rápido. '
                                           'Si falla, usa la CPU.'))
                    else:
                        chk_gpu.props('disable')
                        chk_gpu.tooltip(tr('No disponible: {0}. Hay que compilar openEMS con GPU (ver RETOMAR.md).',
                                           gpu_motivo))
                    btn_sim = ui.button(tr('Simular'), icon='play_arrow').props('color=deep-purple no-caps')
                ui.label(tr('Rápida: para tantear (±3 %). Normal: diseño. Fina: comprobación final (más lenta). '
                         'Cada simulación tarda de 1 a 15 min según el tamaño; el ajuste hace 2–5. '
                         'Si el diseño está guardado, el resultado se guarda con él.')
                         ).classes('text-caption texto-sec')
                registro = ui.log(max_lines=200).classes('w-full h-32 text-caption')
            res_sim = ui.column().classes('w-full gap-2 q-mt-sm')

        # -------------------------------------------------------------- 3. Fabricar
        with ui.tab_panel(t_fab).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.card().classes('grow basis-[340px]'):
                    _titulo_card(tr('Comprobaciones de fabricación'), 'rule')
                    sel_reg = ui.select({k: tr(k) for k in fabricacion.REGLAS}, value=estado['reglas'],
                                        label=tr('Reglas del fabricante')).classes('w-full')
                    lista_drc = ui.column().classes('w-full gap-1 q-mt-sm')
                with ui.card().classes('grow basis-[340px]'):
                    _titulo_card(tr('Exportar'), 'download')
                    ui.label(tr('Guarda el diseño y exporta la placa de prueba KiCad, la huella, los Gerber para JLC '
                             '(con taladros) y el DXF en la carpeta «fabricacion» del diseño. Pasa el DRC de KiCad.')
                             ).classes('text-caption texto-sec')
                    btn_export = ui.button(tr('Exportar KiCad + Gerber + DXF'), icon='download') \
                        .props('color=positive no-caps').classes('w-full q-mt-sm')
                    res_export = ui.column().classes('w-full gap-1')
                with ui.card().classes('grow basis-[340px]'):
                    _titulo_card(tr('Serigrafía (inscripciones)'), 'format_paint')
                    ui.label(tr('Van en la cara de abajo, espejadas para leerse al darle la vuelta, donde no estorban: '
                             'sobre la masa o lejos de la antena. Si no cabe todo, se mantienen el logo y la primera '
                             'línea y se quitan las últimas. Las marcas de corte, «vivo»/«malla» y las referencias de '
                             'los componentes se ponen siempre.')).classes('text-caption texto-sec')
                    sel_logo = ui.select({k: tr(v) for k, v in LOGO_OPCIONES.items()}, value=estado['serigrafia'].get('logo', 'grande'),
                                         label=tr('Logo de Chirptenna')).classes('w-full')
                    aviso_logo = ui.label(tr(AVISO_SIN_LOGO)).classes('text-caption texto-violeta')
                    aviso_logo.set_visibility(estado['serigrafia'].get('logo') == 'ninguno')
                    chk_seri = {}
                    for clave_s, texto_s in SERIGRAFIA_OPCIONES:
                        chk_seri[clave_s] = ui.checkbox(tr(texto_s), value=bool(estado['serigrafia'].get(clave_s)))
                    seri_libre = ui.textarea(tr('Texto libre (una línea por renglón)'),
                                             value=estado['serigrafia'].get('libre', '')) \
                        .classes('w-full').props('autogrow dense')
                    ui.label(tr('Así quedará el texto:')).classes('text-caption texto-sec q-mt-sm')
                    seri_vista = ui.column().classes('w-full gap-0 q-pa-xs').style(
                        'font-family: monospace; border: 1px dashed #8a9aa3; border-radius: 4px')

        # -------------------------------------------------------------- 4. Medir
        with ui.tab_panel(t_medir).classes('q-pa-sm'):
            with ui.row().classes('w-full wrap items-start gap-4'):
                with ui.card().classes('w-full sm:w-[420px] q-pa-none'):
                    with ui.row().classes('items-center q-px-md q-pt-sm'):
                        _titulo_card(tr('Asistente del NanoVNA'), 'settings_input_antenna')
                    with ui.stepper().props('vertical flat header-nav').classes('w-full') as pasos_vna:
                        # ---- 1. conectar
                        with ui.step(tr('Conectar el NanoVNA'), icon='usb'):
                            ui.label(tr('Conéctalo por USB. Solo se lee su estado: su calibración y sus slots '
                                     'guardados no se tocan.')).classes('text-caption texto-sec')
                            info_vna = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                btn_conectar = ui.button(tr('Buscar el NanoVNA'), icon='search').props('color=teal no-caps')
                                ui.button(tr('Saltar (subir un .s1p)'), on_click=lambda: pasos_vna.set_value('Medir y ajustar')
                                          ).props('flat no-caps')
                        # ---- 2. calibrar
                        with ui.step(tr('Calibración'), icon='tune'):
                            ui.label(tr('Calibra al final del latiguillo que vayas a usar con la antena: el plano de '
                                     'medida queda ahí.')).classes('text-caption texto-sec')
                            modo_cal = ui.toggle({0: tr('Usar una guardada'), 1: tr('Calibrar ahora')}, value=0) \
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
                                                    label=tr('Calibración del PC')).classes('w-full')
                                info_cal = ui.label().classes('text-caption')
                            cont_cal_nueva = ui.column().classes('w-full gap-1')
                            with cont_cal_nueva:
                                with ui.row().classes('w-full no-wrap gap-2'):
                                    cal_ini = ui.number(tr('Desde [MHz]'), format='%.1f', min=0.05, max=6000).classes('grow')
                                    cal_fin = ui.number(tr('Hasta [MHz]'), format='%.1f', min=0.05, max=6000).classes('grow')
                                    cal_pts = ui.number(tr('Puntos'), value=301, min=11, max=2020, step=1, format='%.0f'
                                                        ).classes('w-20')
                                cal_nombre = ui.input(tr('Nombre de la calibración')).classes('w-full')
                                btn_cal_empezar = ui.button(tr('Empezar'), icon='play_arrow').props('outline color=teal no-caps')
                                filas_cal = ui.column().classes('w-full gap-1')
                                btn_cal_guardar = ui.button(tr('Guardar calibración'), icon='save') \
                                    .props('color=teal no-caps').classes('w-full')
                                res_cal = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                ui.button(tr('Siguiente'), on_click=lambda: pasos_vna.next()).props('color=teal no-caps')
                                ui.button(tr('Atrás'), on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                        # ---- 3. comprobar
                        with ui.step(tr('Comprobar la calibración'), icon='fact_check'):
                            ui.label(tr('Pon la CARGA de 50 Ω al final del latiguillo. Bien calibrado, |S11| queda '
                                     'por debajo de −30 dB.')).classes('text-caption texto-sec')
                            res_verif = ui.label().classes('text-caption')
                            with ui.stepper_navigation():
                                btn_verif = ui.button(tr('Comprobar'), icon='fact_check').props('color=teal no-caps')
                                ui.button(tr('Siguiente'), on_click=lambda: pasos_vna.next()).props('flat no-caps')
                                ui.button(tr('Atrás'), on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                        # ---- 4. medir y ajustar
                        with ui.step(tr('Medir y ajustar'), icon='straighten'):
                            ui.label(tr('Conecta la antena. Cada medida se guarda en el diseño con su etiqueta; el modo '
                                     'en vivo repite la medida cerca de la banda mientras cortas o cambias la red '
                                     'en π, sin guardarla.')).classes('text-caption texto-sec')
                            etiqueta_in = ui.input(tr('Etiqueta'), placeholder='p. ej. sin cortar, tras la marca 2') \
                                .classes('w-full')
                            notas_medida = ui.input(tr('Notas (opcional)')).classes('w-full')
                            with ui.row().classes('w-full items-center gap-2'):
                                btn_medir = ui.button(tr('Medir y guardar'), icon='add_chart').props('color=teal no-caps')
                                sw_vivo = ui.switch(tr('En vivo'))
                            vivo_txt = ui.label().classes('text-caption text-weight-medium')
                            vivo_graf = ui.plotly({}).classes('w-full h-[220px]')
                            vivo_graf.set_visibility(False)
                            btn_guardar_vivo = ui.button(tr('Guardar esta medida'), icon='save') \
                                .props('outline color=teal no-caps')
                            btn_guardar_vivo.set_visibility(False)
                            ui.separator().classes('q-my-sm')
                            subida = ui.upload(label=tr('…o sube un .s1p'), auto_upload=True, max_files=1) \
                                .props('accept=.s1p,.S1P flat bordered').classes('w-full')
                            with ui.stepper_navigation():
                                ui.button(tr('Atrás'), on_click=lambda: pasos_vna.previous()).props('flat no-caps')
                with ui.column().classes('grow basis-[340px] min-w-0 gap-2'):
                    with ui.card().classes('w-full'):
                        _titulo_card(tr('Simulado frente a medido'), 'stacked_line_chart')
                        lista_medidas = ui.column().classes('w-full gap-0')
                        cont_comparacion = ui.column().classes('w-full')
                    with ui.card().classes('w-full'):
                        _titulo_card(tr('Asistente de ajuste'), 'build')
                        ui.label(tr('A partir de una medida te dice qué marca cortar, cuántos puentes cerrar o qué '
                                 'poner en la red en π. Pulsa «Analizar» en una medida.')
                                 ).classes('text-caption texto-sec')
                        res_asist = ui.column().classes('w-full gap-1')

        # -------------------------------------------------------------- 5. Mis diseños
        with ui.tab_panel(t_bib).classes('q-pa-sm'):
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center'):
                    _titulo_card(tr('Mis diseños'), 'folder_special')
                    ui.space()
                    ui.label(biblioteca.carpeta_base()).classes('text-caption texto-sec')
                    ui.button(icon='folder_open', on_click=lambda: os.startfile(biblioteca.carpeta_base())) \
                        .props('flat round dense').tooltip(tr('Abrir la carpeta'))
                    ui.button(icon='refresh', on_click=lambda: refrescar_biblioteca()).props('flat round dense') \
                        .tooltip(tr('Actualizar'))
                columnas = [
                    {'name': 'nombre', 'label': tr('Nombre'), 'field': 'nombre', 'align': 'left', 'sortable': True},
                    {'name': 'tipo', 'label': tr('Tipo'), 'field': 'tipo_txt', 'align': 'left', 'sortable': True},
                    {'name': 'f', 'label': tr('Objetivo [MHz]'), 'field': 'f_txt', 'sortable': True},
                    {'name': 'sim', 'label': tr('Simulada [MHz]'), 'field': 'sim_txt'},
                    {'name': 'fab', 'label': tr('Exportada'), 'field': 'fab_txt'},
                    {'name': 'medidas', 'label': tr('Medidas'), 'field': 'medidas', 'sortable': True},
                    {'name': 'mod', 'label': tr('Modificado'), 'field': 'modificado', 'sortable': True},
                    {'name': 'notas', 'label': tr('Notas'), 'field': 'notas', 'align': 'left',
                     'classes': 'ellipsis', 'style': 'max-width: 260px'},
                ]
                tabla_bib = ui.table(columns=columnas, rows=[], row_key='nombre', selection='single',
                                     pagination=15).classes('w-full').props('dense flat')
                with ui.row().classes('items-center gap-2'):
                    btn_abrir = ui.button(tr('Abrir'), icon='open_in_new').props('color=primary no-caps')
                    btn_carpeta = ui.button(tr('Abrir carpeta'), icon='folder_open').props('outline no-caps')
                    btn_renombrar = ui.button(tr('Renombrar'), icon='drive_file_rename_outline').props('outline no-caps')
                    btn_archivar = ui.button(tr('Archivar'), icon='archive').props('outline color=grey-8 no-caps') \
                        .tooltip(tr('Lo aparta a la subcarpeta _archivados (no borra nada)'))
            with ui.card().classes('w-full'):
                _titulo_card(tr('Notas del diseño abierto'), 'edit_note')
                notas_in = ui.textarea(placeholder=tr('Pedido, fecha de fabricación, qué se cortó, resultados…')) \
                    .classes('w-full').props('autogrow')
                btn_notas = ui.button(tr('Guardar notas'), icon='save').props('outline no-caps')

    # Pie: versión, licencia y enlace al código fuente (la AGPL pide ofrecerlo a quien use el programa por red)
    with ui.row().classes('w-full justify-center items-center gap-2 q-pa-md text-caption texto-sec'):
        ui.label(tr('Chirptenna v{0} · software libre', __version__))
        ui.link(tr('código fuente'), URL_PROYECTO, new_tab=True)
        ui.label('·')
        ui.link(tr('licencia AGPL-3.0'), URL_PROYECTO + '/blob/main/LICENSE', new_tab=True)
        ui.label(tr('· diseños publicados: CC BY-NC 4.0'))

    entradas = {}

    # ================================================================== estado del diseño
    def actualizar_cabecera():
        n = estado['diseno']
        lbl_diseno.text = (f'{n}{" •" if estado["sucio"] else ""}' if n else tr('Diseño sin guardar'))
        lo, hi = banda_actual()
        lbl_resumen.text = tr('{0} · {1:g}–{2:g} MHz', tr(tipos.CATALOGO[estado["clave"]].nombre).split(" (")[0], lo, hi)
        btn_guardar.props(f'color={"orange-9" if (estado["sucio"] or not n) else "primary"}')

    def marcar_cambio():
        estado['sucio'] = True
        actualizar_cabecera()

    # ================================================================== parámetros
    def construir_params():
        cont_params.clear()
        entradas.clear()
        tipo = tipos.CATALOGO[estado['clave']]
        desc.text = tr(tipo.descripcion)
        p_act = estado['params']
        visibles = set(presentacion.parametros_visibles(estado['clave'], p_act))
        basicos = set(guia.basicos(estado['clave'], p_act))
        visibles_p = [p for p in tipo.parametros if p.nombre in visibles]   # el resto no aplica con estos valores

        def campo(p):
            valor = p_act.get(p.nombre, p.defecto)
            with ui.row().classes('w-full no-wrap items-center gap-1'):
                if p.opciones:
                    n = ui.select({k: tr(v) for k, v in p.opciones.items()}, value=int(valor), label=tr(p.etiqueta)).classes('grow')
                else:
                    n = ui.number(tr(p.etiqueta), value=valor, min=p.minimo, max=p.maximo, step=p.paso,
                                  format='%.0f' if p.entero else '%.2f').classes('grow')
                # ayuda del parámetro: burbuja al pinchar el icono (se cierra al pinchar fuera)
                texto_ayuda = tr(guia.ayuda(estado['clave'], p))
                with ui.button(icon='help_outline').props('flat round dense size=sm').classes('ayuda-param'):
                    with ui.menu().props('anchor="top right" self="top left"').classes('q-pa-sm'):
                        ui.label(texto_ayuda).classes('text-body2').style('max-width: 320px')
            n.on_value_change(lambda e, nombre=p.nombre, entero=p.entero: cambiar_param(nombre, e.value, entero))
            entradas[p.nombre] = n

        with cont_params:
            for p in visibles_p:
                if p.nombre in basicos:
                    campo(p)
            avanzados = [p for p in visibles_p if p.nombre not in basicos]
            if avanzados:
                exp_av = ui.expansion(tr('Ajustes avanzados ({0})', len(avanzados)), icon='tune',
                                      value=estado.get('avanzados_abiertos', False)).classes('w-full q-mt-sm') \
                    .props('dense')
                exp_av.on_value_change(lambda e: estado.update(avanzados_abiertos=bool(e.value)))
                with exp_av:
                    for p in avanzados:
                        campo(p)

    def cambiar_param(nombre, valor, entero):
        if valor is None or estado.get('silencio'):
            return
        estado['params'][nombre] = int(round(valor)) if entero else float(valor)
        estado['params'].pop('red_L', None)     # la red en L del bucle se calculó para otro anillo: se vuelve a calcular al simular
        marcar_cambio()
        if nombre in tipos.ESCALABLES.get(estado['clave'], ()) and int(estado['params'].get('escalado', 0)) == 1:
            # el usuario fija una medida a mano: si siguiera en «proporcionales», el próximo ajuste la pisaría
            estado['params']['escalado'] = 0
            if 'escalado' in entradas:
                estado['silencio'] = True
                entradas['escalado'].value = 0
                estado['silencio'] = False
            ui.notify(tr('Medidas secundarias pasadas a «Manuales» para respetar el valor que has puesto.'))
        if nombre == 'escalado' and int(valor) == 1:
            ajustar()                   # vuelve a escalar las medidas con la frecuencia actual
            return
        if nombre in ('masa', 'multibanda', 'integrada'):
            # cambia qué medidas se muestran y la masa (o las dos bandas) cambian el tamaño: se reajusta
            construir_params()
            ajustar()
            return
        if nombre in tipos.integracion.SOLO_INTEGRADA and int(estado['params'].get('integrada', 0)) == 1:
            ajustar()                   # el tamaño de la placa y de la zona fija la masa, que mueve la resonancia
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
            ui.notify(tr('No se puede generar: {0}', ex), type='negative')
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
                    ui.label(tr('Banda estimada {0:g}–{1:g} MHz ({2:g} MHz, {3:g} %) · necesaria {4:g}–{5:g} MHz', bw['f_inf_MHz'], bw['f_sup_MHz'], bw['MHz'], bw['porcentaje'], lo, hi)
                             ).classes('text-caption text-weight-medium')
            for etiqueta, valor in presentacion.filas_info(a.info):
                with ui.row().classes('w-full no-wrap justify-between'):
                    ui.label(tr(etiqueta)).classes('text-caption texto-sec')
                    ui.label(valor).classes('text-caption text-weight-medium text-right')
        lista_consejos.clear()
        with lista_consejos:
            for cat, texto in consejos.consejos(a, estado['f_MHz']*1e6, (lo*1e6, hi*1e6)):
                icono, color = ICONOS_CONSEJO.get(cat, ('info', 'grey'))
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(icono, color=color).tooltip(tr(cat))
                    ui.label(tr(texto)).classes('text-caption')
        mostrar_drc()
        mostrar_problemas()
        actualizar_cabecera()
        mostrar_serigrafia()                # la primera línea lleva el tipo y la frecuencia

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
                    ui.label(tr(texto)).classes(f'text-caption {clase}')
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
                    ui.label(tr('Problema conocido: ') + tr(t)).classes('text-caption text-negative')
            with ui.row().classes('items-start no-wrap'):
                ui.icon('science', color='blue-grey-6')
                ui.label(tr(problemas.AVISO_GENERAL)).classes('text-caption texto-sec')
            colores = {'ok': 'positive', 'aviso': 'warning', 'error': 'negative', 'info': 'teal'}
            iconos = {'ok': 'check_circle', 'aviso': 'warning', 'error': 'error', 'info': 'build'}
            mensajes = (fabricacion.comprobar(a, estado['reglas']) + [('aviso', m) for m in a.info.get('avisos', [])]
                        + [('info', m) for m in (a.info.get('ajuste') or [])])
            for nivel, msg in mensajes:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon(iconos[nivel], color=colores[nivel])
                    ui.label(tr(msg)).classes('text-caption')

    def elegir_tipo(clave):
        """Desde la galería: pone el tipo (lo dimensiona para la banda actual) y pasa a la pestaña Diseño."""
        if sel_tipo.value != clave:
            sel_tipo.value = clave           # dispara cambiar_tipo
        pestanas.set_value(t_diseno)

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
        rango.text = tr('{0:g}–{1:g} MHz', lo, hi)

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
        estado['params'].pop('red_L', None)
        p = tipos.dimensionar(estado['clave'], estado['f_MHz']*1e6, estado['params'], estado['sustrato'])
        aviso_ajuste.text = p.pop('_aviso', '')
        poner_params(p)

    def ampliar_bw():
        p, msg = tipos.ajustar_ancho_banda(estado['clave'], estado['f_MHz']*1e6, estado['bw_MHz']*1e6,
                                           estado['params'], estado['sustrato'])
        aviso_ajuste.text = msg
        ui.notify(msg, type='positive' if msg.startswith((tr('Ya'), tr('Ancho'))) else 'warning', multi_line=True)
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
            confirmar(tr('Ya hay un diseño llamado «{0}». ¿Sustituir su geometría por la actual? Sus simulaciones, medidas y notas se conservan.', nombre), lambda: guardar_diseno(True))
            return False
        a = estado['antena']
        biblioteca.guardar(nombre, estado['clave'], estado['params'], estado['sustrato'], estado['reglas'],
                           estado['f_MHz'], estado['bw_MHz'], info=a.info if a else None,
                           serigrafia=estado['serigrafia'])
        estado['diseno'] = nombre
        estado['sucio'] = False
        actualizar_cabecera()
        mostrar_serigrafia()
        refrescar_biblioteca()
        mostrar_medidas()
        notas_in.value = (biblioteca.cargar(nombre) or {}).get('notas', '')
        ui.notify(tr('Diseño «{0}» guardado', nombre), type='positive')
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
                ui.button(tr('Cancelar'), on_click=dlg.close).props('flat no-caps')
                ui.button(tr('Sí'), on_click=lambda: (dlg.close(), accion())).props('color=primary no-caps')
        dlg.open()

    def abrir_diseno(nombre, avisar=True):
        d = biblioteca.cargar(nombre)
        if not d or d.get('tipo') not in tipos.CATALOGO:
            ui.notify(tr('No se puede abrir «{0}»', nombre), type='negative')
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
        poner_serigrafia(d.get('serigrafia'))
        estado['sucio'] = False
        actualizar_cabecera()
        mostrar_serigrafia()
        notas_in.value = d.get('notas', '')
        res_export.clear()
        res_asist.clear()
        sim_g = biblioteca.leer_simulacion(nombre)
        res_sim.clear()
        registro.clear()
        if sim_g:
            registro.push(tr('Simulación guardada con el diseño ({0}).', sim_g[0].get("precision", "")))
            pintar_simulacion(*sim_g)
        mostrar_medidas()
        pestanas.value = t_diseno
        if avisar:
            ui.notify(tr('Diseño «{0}» abierto', nombre), type='positive')

    def refrescar_biblioteca():
        filas = []
        for d in biblioteca.listar():
            t = tipos.CATALOGO.get(d['tipo'])
            filas.append(dict(d, tipo_txt=t.nombre.split(' (')[0] if t else d['tipo'],
                              f_txt=f"{d['f_objetivo_MHz']:g}" if d['f_objetivo_MHz'] else '',
                              sim_txt=f"{d['simulado']:g}" if d['simulado'] else '—',
                              fab_txt=tr('sí') if d['fabricado'] else '—'))
        tabla_bib.rows = filas
        tabla_bib.update()

    def seleccionado():
        if not tabla_bib.selected:
            ui.notify(tr('Elige un diseño de la lista'), type='warning')
            return None
        return tabla_bib.selected[0]['nombre']

    def renombrar_click():
        n = seleccionado()
        if not n:
            return
        with ui.dialog() as dlg, ui.card():
            nuevo = ui.input(tr('Nuevo nombre'), value=n).classes('w-64')

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
                ui.button(tr('Cancelar'), on_click=dlg.close).props('flat no-caps')
                ui.button(tr('Renombrar'), on_click=hacer).props('color=primary no-caps')
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
            ui.notify(tr('«{0}» movido a _archivados', n), type='positive')
        confirmar(tr('¿Archivar «{0}»? Se mueve a la subcarpeta _archivados; no se borra nada.', n), hacer)

    def guardar_notas():
        if not estado['diseno']:
            ui.notify(tr('Guarda primero el diseño'), type='warning')
            return
        biblioteca.guardar_notas(estado['diseno'], notas_in.value or '')
        refrescar_biblioteca()
        ui.notify(tr('Notas guardadas'), type='positive')

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
            ui.notify(tr('Ya hay una simulación en marcha'), type='warning')
            return
        carpeta = os.path.join(DIR_SALIDAS, '_simulaciones', time.strftime('%Y%m%d_%H%M%S'))
        os.makedirs(carpeta, exist_ok=True)
        # los resultados que se sabe que dependen de la malla (dos bandas, paneles, arrays) se verifican siempre
        sensible = (int(estado['params'].get('multibanda', 0) or 0) == 1
                    or tipos.CATALOGO[estado['clave']].familia in ('panel', 'array'))
        trabajo = {'clave': estado['clave'], 'parametros': estado['params'], 'sustrato': estado['sustrato'],
                   'f_obj_Hz': estado['f_MHz']*1e6, 'precision': sel_prec.value, 'ajustar': chk_ajustar.value,
                   'verificar_malla': bool(chk_malla.value or sensible), 'entorno': list(sel_entorno.value or []), 'salida': carpeta}
        ruta = os.path.join(carpeta, 'trabajo.json')
        with open(ruta, 'w', encoding='utf-8') as fh:
            json.dump(trabajo, fh, ensure_ascii=False, default=float)
        registro.clear()
        registro.push(tr('Simulando {0} a {1:g} MHz ({2}{3}{4})…', tr(tipos.CATALOGO[estado["clave"]].nombre),
                         estado["f_MHz"], sel_prec.value, tr(', con ajuste') if chk_ajustar.value else '',
                         ', GPU' if chk_gpu.value else ''))
        entorno = dict(os.environ, PYTHONIOENCODING='utf-8', CHIRPTENNA_IDIOMA=i18n.idioma(),
                       ANTENAS_GPU='1' if chk_gpu.value else '0')
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
            registro.push(tr('La simulación terminó sin resultado (mira la consola).'))
            return
        r = json.load(open(ruta, encoding='utf-8'))
        if not r.get('ok'):
            registro.push(tr('Error: {0}', r.get("error")))
            ui.notify(tr('Error en la simulación: {0}', r.get("error")), type='negative', multi_line=True)
            return
        if diseno and biblioteca.existe(diseno):
            biblioteca.guardar_simulacion(diseno, carpeta)
            registro.push(tr('Resultado guardado en el diseño «{0}».', diseno))
            refrescar_biblioteca()
            if diseno == estado['diseno']:
                mostrar_medidas()
        else:
            registro.push(tr('El diseño no estaba guardado (o cambió durante la simulación): '
                          'el resultado queda solo en salidas/_simulaciones.'))
        pintar_simulacion(r, dict(np.load(os.path.join(carpeta, 'datos.npz'))))
        ui.notify(tr('Simulación terminada'), type='positive')

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
                filas = [(tr('Resonancia'), tr('{0:g} MHz ({1})', r['f_resonancia_MHz'], r.get('criterio') or 'centro de banda')),
                         (tr('Banda a −10 dB'), '—' if not r['banda_MHz'] else
                          tr('{0:g}–{1:g} MHz ({2:g} MHz)', r['banda_MHz'][0], r['banda_MHz'][1], r['ancho_banda_MHz'])),
                         (tr('Banda necesaria'), tr('{0:g}–{1:g} MHz', lo, hi)),
                         (tr('S11 mínimo'), tr('{0:g} dB a {1:g} MHz', r['s11_min_dB'], r['f_min_s11_MHz'])),
                         (tr('Directividad / ganancia'), tr('{0:g} / {1:g} dBi', r['directividad_dBi'], r['ganancia_dBi'])),
                         (tr('Eficiencia de radiación / total'),
                          f"{r['eficiencia_radiacion_%']:g} % / {r['eficiencia_total_%']:g} %"),
                         (tr('Malla / tiempo'), tr('{0:.2f} M celdas, paso {1} mm, {2:g} s', r['celdas']/1e6, r['paso_malla_mm'], r['tiempo_s']))]
                red = r.get('red')
                if red:
                    with ui.row().classes('items-start no-wrap'):
                        ui.icon('electrical_services', color='primary')
                        ui.label(tr('Red de adaptación: Z1 en serie = {0}; {1} a masa = {2}. S11 en el objetivo {3:g} dB (sin la red, {4:g} dB); '
                                    'los componentes pierden el {5:.0f} % de la potencia. Calculada por circuito con la impedancia simulada del anillo '
                                    '(Q de 250 en los condensadores y de 40 en las bobinas); monta estos valores en Z1 y {1} y deja la otra derivación sin montar.',
                                    ajuste.texto_componente(*red['serie']), red['posicion'], ajuste.texto_componente(*red['derivacion']),
                                    red['s11_dB'], red['s11_sin_red_dB'], 100*(1 - red.get('eficiencia_red', 1.0)))
                                 ).classes('text-caption')
                en = r.get('entorno')
                if en and en.get('error'):
                    with ui.row().classes('items-start no-wrap'):
                        ui.icon('warning', color='warning')
                        ui.label(tr('No se pudo simular el entorno: {0}', en['error'])).classes('text-caption')
                elif en:
                    grave = en['df_pct'] < -5 or abs(en['eta_con_%'] - en['eta_sin_%']) > 20
                    with ui.row().classes('items-start no-wrap'):
                        ui.icon('warning' if grave else 'check_circle', color='warning' if grave else 'positive')
                        ui.label(tr('Con {0}: la frecuencia pasa de {1:g} a {2:g} MHz ({3:+.1f} %), la eficiencia de radiación de {4:g} a {5:g} % y la ganancia de '
                                    '{6:g} a {7:g} dBi. Una carcasa o una mano lo bajan y lo empeoran: deja margen y vuelve a ajustar con ellas puestas.',
                                    ', '.join(tr(entorno.PREDEFINIDOS[n]).split(' (')[0] for n in en['nombres']), en['f_sin_MHz'], en['f_con_MHz'],
                                    en['df_pct'], en['eta_sin_%'], en['eta_con_%'], en['ganancia_sin_dBi'], en['ganancia_con_dBi'])
                                 ).classes('text-caption' + (' texto-aviso' if grave else ''))
                v = r.get('verificacion_malla')
                if v and v.get('error'):
                    with ui.row().classes('items-start no-wrap'):
                        ui.icon('warning', color='warning')
                        ui.label(tr('No se pudo verificar la malla: {0}', v['error'])).classes('text-caption')
                elif v:
                    detalle = '; '.join(
                        (tr('paso ×{0:g}: Δf {1:+.1f} %, ΔS11 {2} dB', x['factor'], x['dif_f_pct'],
                            ' / '.join(f'{d:+.1f}' for d in x['dif_s11_dB']))
                         if v.get('compara_f', True) else
                         tr('paso ×{0:g}: ΔS11 {1} dB', x['factor'], ' / '.join(f'{d:+.1f}' for d in x['dif_s11_dB'])))
                        for x in v['filas'])
                    sens = v['veredicto'] == 'sensible'
                    with ui.row().classes('items-start no-wrap'):
                        ui.icon('warning' if sens else 'check_circle', color='warning' if sens else 'positive')
                        ui.label((tr('El resultado depende de la malla: no te fíes de un solo punto, mide la antena. ')
                                  if sens else tr('El resultado no depende de la malla. ')) + '(' + detalle + ')'
                                 ).classes('text-caption' + (' texto-aviso' if sens else ''))
                cubre = bool(r['banda_MHz']) and r['banda_MHz'][0] <= lo and r['banda_MHz'][1] >= hi
                with ui.row().classes('items-center no-wrap'):
                    ui.icon('check_circle' if cubre else 'cancel', color='positive' if cubre else 'negative')
                    ui.label(tr('La simulación cubre la banda') if cubre else tr('La simulación NO cubre la banda entera')
                             ).classes('text-caption text-weight-medium')
                with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-0'):
                    for k, v in filas:
                        ui.label(tr(k)).classes('text-caption texto-sec')
                        ui.label(v).classes('text-caption text-weight-medium')
                if r.get('historial'):
                    ui.label(tr('Ajuste: ') + ' → '.join(tr('{0} mm: {1} MHz ({2:+} %)', h['escala_mm'], h['f_resonancia_MHz'], h['error_%']) for h in r['historial'])
                             ).classes('text-caption')
                    ui.button(tr('Aplicar los parámetros ajustados'), icon='done_all',
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
        ui.notify(tr('Parámetros ajustados aplicados. Guarda el diseño para conservarlos.'), type='positive')

    ui.timer(0.5, vigilar)

    # ================================================================== medidas
    visibles = {}            # fichero -> mostrar en la comparación

    def mostrar_medidas():
        lista_medidas.clear()
        cont_comparacion.clear()
        n = estado['diseno']
        if not n:
            with lista_medidas:
                ui.label(tr('Guarda el diseño (o haz una medida) para ver aquí sus medidas y su simulación.')
                         ).classes('text-caption texto-sec')
            return
        ms = biblioteca.medidas(n)
        sim_g = biblioteca.leer_simulacion(n)
        with lista_medidas:
            if not ms and not sim_g:
                ui.label(tr('Este diseño aún no tiene simulación ni medidas.')).classes('text-caption texto-sec')
            if sim_g:
                r = sim_g[0]
                ui.checkbox(tr('Simulación ({0:g} MHz, {1})', r['f_resonancia_MHz'], r.get('precision', '')),
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
                    ui.button(tr('Analizar'), icon='build', on_click=lambda f=fichero, t=texto: analizar_medida(f, t)) \
                        .props('flat dense no-caps color=teal')
                    ui.button(icon='download',
                              on_click=lambda f=fichero: ui.download(os.path.join(biblioteca.carpeta(n, 'medidas'), f))
                              ).props('flat dense round').tooltip(tr('Descargar .s1p'))
        pintar_comparacion()

    def pintar_comparacion():
        cont_comparacion.clear()
        n = estado['diseno']
        if not n:
            return
        curvas = []
        sim_g = biblioteca.leer_simulacion(n)
        if sim_g and visibles.get('_sim', True):
            curvas.append((tr('Simulación'), sim_g[1]['f'], sim_g[1]['s11'], True))
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
            ui.notify(tr('No se puede leer la medida: {0}', ex), type='negative')
            return
        mostrar_asistente(f, s11, tr('Medida «{0}»', texto))

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
                    ui.label(tr('Respecto a «{0}»: resonancia {1:g} → {2:g} MHz ({3:+.1f} MHz); en el objetivo {4:g} → {5:g} dB', etiqueta_a, ra["f_medida_MHz"], rec["f_medida_MHz"], d, ra["s11_en_f_obj_dB"], rec["s11_en_f_obj_dB"])
                             ).classes('text-caption texto-violeta')
                except Exception:
                    pass
            ui.label(tr('{0}: resonancia medida {1:g} MHz ({2:+g} % respecto a {3:g} MHz), S11 mínimo {4:g} dB; en el objetivo {5:g} dB, Z = {6:g} {7:+g}j Ω', origen, rec["f_medida_MHz"], rec["desvio_%"], estado["f_MHz"], rec["s11_min_dB"], rec["s11_en_f_obj_dB"], rec["Z_en_f_obj_ohm"][0], rec["Z_en_f_obj_ohm"][1])
                     ).classes('text-caption text-weight-medium')
            for acc in rec['acciones']:
                with ui.row().classes('items-start no-wrap'):
                    ui.icon('build', color='teal')
                    ui.label(acc).classes('text-caption')
            if rec.get('redes'):
                txt = lambda c: '0 Ω' if c[0] == '0 Ω' else (tr('{0:g} nH', c[1]) if c[0] == 'L' else tr('{0:g} pF', c[1]))
                ui.label(tr('Alternativas para la red en π (valores comerciales E24):')).classes('text-caption q-mt-xs')
                for r_ in rec['redes']:
                    ui.label(tr('· Z1 = {0}, {1} = {2} → |S11| ≈ {3} dB', txt(r_["serie"]), r_["posicion"], txt(r_["derivacion"]), r_["s11_dB"])).classes('text-caption')
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
        mostrar_asistente(f, s11, tr('Medida «{0}»', etiqueta or os.path.basename(ruta)), anterior)
        ui.notify(tr('Medida guardada en el diseño «{0}»', estado["diseno"]), type='positive')

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
            ui.notify(tr('No se puede leer el .s1p: {0}', ex), type='negative')
            return
        if not len(f):
            ui.notify(tr('El .s1p no tiene datos'), type='negative')
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
            ui.notify(tr('NanoVNA: {0}', ex), type='negative', multi_line=True)
            return None
        finally:
            boton.props(remove='loading')

    async def conectar_click():
        av = _modulo_vna()
        i = await tarea_vna(btn_conectar, av.info_equipo)
        if i is None:
            info_vna.text = tr('No se ha podido conectar.')
            return
        ini, fin, pts = i['barrido']
        info_vna.text = (tr('{0} en {1} · barrido {2:g}–{3:g} MHz, {4} puntos · calibración del equipo: {5}', i['version'].split()[0] if i['version'] else 'NanoVNA', i['puerto'], ini/1e6, fin/1e6, pts, i['cal'] or '—'))
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
            info_cal.text = tr('No hay calibraciones guardadas: calibra ahora.')
            return
        i = _modulo_vna().info_calibracion(sel_cal.value)
        if not i:
            return
        lo, hi = banda_actual()
        dentro = i['f_ini_Hz'] <= lo*1e6 and i['f_fin_Hz'] >= hi*1e6
        info_cal.text = (tr('{0:g}–{1:g} MHz, {2} puntos, {3} · {4}', i['f_ini_Hz']/1e6, i['f_fin_Hz']/1e6, i['puntos'], ', '.join(i['estandares']).upper(), i['fecha'][:16].replace('T', ' '))
                         + ('' if dentro else tr(' · ⚠ no cubre la banda del diseño')))
        info_cal.classes(replace='text-caption ' + ('' if dentro else 'text-negative'))

    def pintar_pasos_cal():
        filas_cal.clear()
        cg = vna['cal_guiada']
        btn_cal_guardar.set_visibility(cg is not None)
        if cg is None:
            return
        textos = {'open': tr('Pon el OPEN (abierto)'), 'short': tr('Pon el SHORT (cortocircuito)'),
                  'load': tr('Pon la CARGA de 50 Ω')}
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
            ui.notify(tr('No se puede empezar: {0}', ex), type='negative')
            return
        res_cal.text = (tr('{0:g}–{1:g} MHz, {2} puntos ({3} barridos por estándar).', cal_ini.value, cal_fin.value, int(cal_pts.value), -(-int(cal_pts.value)//101)))
        pintar_pasos_cal()

    async def medir_estandar(paso, boton):
        cg = vna['cal_guiada']
        r = await tarea_vna(boton, cg.medir, paso)
        if r is None:
            return
        bien, texto = r
        if bien:
            ui.notify(tr('{0} medido. {1}', paso.upper(), texto), type='positive')
        else:
            ui.notify(tr('{0} NO guardado: {1}', paso.upper(), texto), type='warning', multi_line=True)
        pintar_pasos_cal()

    async def guardar_calibracion():
        cg = vna['cal_guiada']
        if cg is None:
            return
        r = await tarea_vna(btn_cal_guardar, cg.terminar)
        if r is None:
            return
        nombre, errores = r
        res_cal.text = (tr('Guardada. Autocomprobación: ') +
                        ', '.join(f'{k.upper()} {v:.0e}' for k, v in errores.items()))
        import calibracion as _c
        sel_cal.options = _c.listar()
        sel_cal.value = nombre
        sel_cal.update()
        vna['cal_guiada'] = None
        pintar_pasos_cal()
        modo_cal.value = 0
        ui.notify(tr('Calibración «{0}» guardada en vna/calibraciones', nombre), type='positive')
        pasos_vna.next()

    async def verificar_click():
        if not sel_cal.value:
            ui.notify(tr('Elige o haz antes una calibración'), type='warning')
            return
        r = await tarea_vna(btn_verif, _modulo_vna().verificar, sel_cal.value)
        if r is None:
            return
        bien = r['max_dB'] < -25
        res_verif.text = (tr('|S11| con la carga: mediana {0:.1f} dB, peor {1:.1f} dB a {2:.0f} MHz · ', r['mediana_dB'], r['max_dB'], r['f_max_MHz']) + ('bien' if bien else
                          tr('revisa: ¿está la carga puesta? Si sí, el latiguillo o los conectores han cambiado: recalibra')))
        res_verif.classes(replace='text-caption ' + ('text-positive' if bien else 'text-negative'))

    def ventana_medida(ancho=0.5):
        """Intervalo de medida alrededor de la frecuencia objetivo (±ancho/2 relativo)."""
        f0 = estado['f_MHz']*1e6
        return f0*(1 - ancho/2), f0*(1 + ancho/2)

    async def medir_click():
        if not sel_cal.value:
            ui.notify(tr('Elige o haz antes una calibración'), type='warning')
            return
        r = await tarea_vna(btn_medir, _modulo_vna().medir, sel_cal.value, *ventana_medida(1.0))
        if r is not None:
            nueva_medida(r[0], r[1], tr('NanoVNA ({0})', sel_cal.value))

    async def bucle_vivo():
        av = _modulo_vna()
        while vna['vivo']:
            try:
                f, s11 = await run.io_bound(av.medir, sel_cal.value, *ventana_medida(0.5))
            except Exception as ex:
                ui.notify(tr('NanoVNA: {0}', ex), type='negative', multi_line=True)
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
                vivo_txt.text = (tr('{0} · resonancia {1:g} MHz ({2:+g} %) · en el objetivo {3:g} dB · ', time.strftime("%H:%M:%S"), rec["f_medida_MHz"], rec["desvio_%"], rec["s11_en_f_obj_dB"])
                                 + (rec['acciones'][0] if rec['acciones'] else ''))
            except Exception:
                db = 20*np.log10(np.abs(s11))
                vivo_txt.text = tr('{0} · S11 mínimo {1:.1f} dB a {2:.1f} MHz', time.strftime("%H:%M:%S"), db.min(), f[db.argmin()]/1e6)
            await asyncio.sleep(0.3)

    def cambiar_vivo(e):
        if e.value and not sel_cal.value:
            ui.notify(tr('Elige o haz antes una calibración'), type='warning')
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
        nueva_medida(f, s11, tr('NanoVNA en vivo ({0})', sel_cal.value))

    # ================================================================== serigrafía
    def lineas_serigrafia():
        """Líneas de texto de la serigrafía según lo elegido (la primera es la que más importa)."""
        s = estado['serigrafia']
        r = None
        if s.get('sim') and estado['diseno'] and not estado['sucio']:
            r = biblioteca.leer_simulacion(estado['diseno'], solo_resultado=True)
        return presentacion.lineas_serigrafia(s, estado['clave'], estado['f_MHz'], nombre_actual(), r)

    def mostrar_serigrafia():
        seri_vista.clear()
        lineas = lineas_serigrafia()
        with seri_vista:
            modo = estado['serigrafia'].get('logo', 'grande')
            if modo != 'ninguno':
                ui.label(tr('[logo grande: grillo + Chirptenna]') if modo == 'grande'
                         else tr('[logo pequeño de Chirptenna]')).classes('text-caption texto-sec')
            elif not lineas:
                ui.label('(sin inscripciones)').classes('text-caption texto-sec')
            for t in lineas:
                ui.label(t).classes('text-caption')
            if estado['serigrafia'].get('sim') and not any(t.startswith('sim ') for t in lineas):
                ui.label(tr('La línea de la simulación aparece cuando el diseño está guardado, sin cambios y '
                         'simulado.')).classes('text-caption texto-aviso')

    def cambiar_serigrafia(clave_s, valor):
        if estado.get('silencio'):
            return
        estado['serigrafia'][clave_s] = valor
        marcar_cambio()
        mostrar_serigrafia()

    def poner_serigrafia(s):
        estado['serigrafia'] = dict(SERIGRAFIA_DEFECTO, **(s or {}))
        logo_s = estado['serigrafia'].get('logo')
        if logo_s is True or logo_s not in LOGO_OPCIONES:      # diseños guardados con el formato antiguo (bool)
            estado['serigrafia']['logo'] = 'ninguno' if logo_s is False else 'grande'
        estado['silencio'] = True
        try:
            sel_logo.value = estado['serigrafia']['logo']
            aviso_logo.set_visibility(estado['serigrafia']['logo'] == 'ninguno')
            for clave_s, chk in chk_seri.items():
                chk.value = bool(estado['serigrafia'].get(clave_s))
            seri_libre.value = estado['serigrafia'].get('libre', '')
        finally:
            estado['silencio'] = False
        mostrar_serigrafia()

    # ================================================================== exportación
    def exportar_click():
        a = estado['antena']
        if a is None or not asegurar_guardado():
            return
        nombre = estado['diseno']
        carpeta = biblioteca.carpeta(nombre, 'fabricacion')
        try:
            titulo = tr('{0} {1} MHz', tr(tipos.CATALOGO[a.tipo].nombre).split(' (')[0], a.info.get('f_estimada_MHz'))
            modo_logo = estado['serigrafia'].get('logo', 'grande')
            r = exportar.exportar_todo(a, carpeta, nombre, titulo, etiqueta=lineas_serigrafia(),
                                       logo=None if modo_logo == 'ninguno' else modo_logo)
        except Exception as ex:
            ui.notify(tr('Error al exportar: {0}', ex), type='negative', multi_line=True)
            return
        refrescar_biblioteca()
        res_export.clear()
        with res_export:
            with ui.row().classes('items-center no-wrap'):
                ui.label(tr('Guardado en {0}', carpeta)).classes('text-caption')
                ui.button(icon='folder_open', on_click=lambda: os.startfile(carpeta)).props('flat round dense')
            for clave, texto in (('gerber_zip', tr('Gerber para JLC (.zip)')), ('placa', tr('Placa de prueba KiCad (.kicad_pcb)')),
                                 ('huella', tr('Huella KiCad (.kicad_mod)')), ('dxf', tr('DXF para EasyEDA')),
                                 ('huella_integrar', tr('Huella para tu placa, con zona de exclusión (.kicad_mod)')),
                                 ('placa_ejemplo', tr('Placa de ejemplo con la huella en su esquina (.kicad_pcb)')),
                                 ('gerber_zip_reflector', tr('Reflector: Gerber para JLC (.zip)')),
                                 ('placa_reflector', tr('Reflector: placa KiCad (.kicad_pcb)')),
                                 ('dxf_reflector', tr('Reflector: DXF (chapa o placa)'))):
                if clave not in r:
                    continue
                ui.button(texto, icon='file_download', on_click=lambda r=r, c=clave: ui.download(r[c])) \
                    .props('flat dense no-caps').classes('w-full justify-start')
            s = r.get('serigrafia') or {}
            if s.get('logo_forma') == 'texto':
                ui.label(tr('Serigrafía: no cabe el grillo; va la palabra «Chirptenna»')).classes('text-caption texto-aviso')
            elif s.get('logo_mm'):
                forma = 'solo el grillo' if s.get('logo_forma') == 'icono' else 'grillo + nombre'
                ui.label(tr('Serigrafía: logo de {0:g} mm ({1})', s['logo_mm'], forma)).classes('text-caption')
            else:
                ui.label(tr('Serigrafía sin logo. Si compartes la placa, menciona Chirptenna. ¡Gracias!')) \
                    .classes('text-caption texto-violeta')
            if s.get('quitadas'):
                ui.label(tr('No caben en la serigrafía: ') + ' · '.join(s['quitadas'])).classes('text-caption texto-aviso')
            if r['drc']:
                ui.label(tr('DRC de KiCad: {0} infracciones', len(r["drc"]))).classes('text-caption text-negative')
                for t, sev, d in r['drc'][:5]:
                    ui.label(f'· {t}: {d}').classes('text-caption')
            else:
                ui.label(tr('DRC de KiCad sin errores')).classes('text-caption text-positive')
        ui.notify(tr('Exportado en el diseño «{0}»', nombre), type='positive')

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
    for _clave_s, _chk in chk_seri.items():
        _chk.on_value_change(lambda e, c=_clave_s: cambiar_serigrafia(c, bool(e.value)))
    seri_libre.on_value_change(lambda e: cambiar_serigrafia('libre', e.value or ''))

    def cambiar_logo(e):
        if estado.get('silencio') or e.value is None:
            return
        aviso_logo.set_visibility(e.value == 'ninguno')
        if e.value == 'ninguno':
            ui.notify(tr(AVISO_SIN_LOGO), type='info', multi_line=True, timeout=9000)
        cambiar_serigrafia('logo', e.value)
    sel_logo.on_value_change(cambiar_logo)
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

    def al_entrar_en_diseno(e):
        # Plotly no se inicializa si la figura se pone con la pestaña oculta (el programa arranca en la galería):
        # se vuelve a enviar al entrar
        if e.value == 'Diseño' and estado.get('antena') is not None:
            grafico.update_figure(T(vista.figura_plotly(estado['antena'])))
    pestanas.on_value_change(al_entrar_en_diseno)
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
    # Parámetros de la URL: abrir un diseño y una pestaña concretos
    if diseno and biblioteca.existe(diseno):
        abrir_diseno(diseno, avisar=False)          # abre en la pestaña Diseño
    if pestana in PESTANAS_URL:
        pestanas.value = (t_gal, t_diseno, t_sim, t_fab, t_medir, t_bib)[PESTANAS_URL.index(pestana)]


if __name__ in {'__main__', '__mp_main__'}:
    # CHIRPTENNA_ABRIR=1 (lo pone iniciar.bat) abre el navegador al arrancar.
    # Solo se escucha en este ordenador: NiceGUI usa 0.0.0.0 por defecto y cualquiera en la misma red podría
    # simular, escribir archivos o usar el NanoVNA. CHIRPTENNA_HOST=0.0.0.0 lo abre a la red a propósito.
    # Opciones: --puerto N (por defecto 8080) y --disenos <carpeta> (otra biblioteca, p. ej. para pruebas o capturas)
    import argparse
    _ap = argparse.ArgumentParser(description='Interfaz de Chirptenna')
    _ap.add_argument('--puerto', type=int, default=int(os.environ.get('CHIRPTENNA_PUERTO', 8080)))
    _ap.add_argument('--disenos', default='', help='carpeta de la biblioteca de diseños')
    _args, _ = _ap.parse_known_args()
    if _args.disenos:
        os.environ['CHIRPTENNA_DISENOS'] = os.path.abspath(_args.disenos)
    ui.run(title='Chirptenna', host=os.environ.get('CHIRPTENNA_HOST', '127.0.0.1'), port=_args.puerto, reload=False,
           show=os.environ.get('CHIRPTENNA_ABRIR') == '1', favicon=LOGO if os.path.exists(LOGO) else '📡',
           dark=False)
