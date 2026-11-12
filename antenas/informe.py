"""Informe en PDF de un diseño (F4.5): portada con la vista, parámetros, avisos y consejos y, si hay simulación, S11, ROE, Smith,
diagrama, ganancia, eficiencia, tolerancias, entorno y red de adaptación. Solo matplotlib (`PdfPages`), sin dependencias nuevas.

`generar(ruta, antena, ...)` escribe el PDF en A4 vertical. Los textos van con `tr` (idioma del proceso). El texto largo se parte
en líneas y salta de página: nunca queda cortado.
"""
import textwrap
import time

import numpy as np

from . import consejos as consejos_mod
from . import presentacion, problemas
from .geometria import poligonos
from .i18n import tr

A4 = (8.27, 11.69)
ANCHO_TEXTO = 98            # caracteres por línea con letra de 9 pt


class _Pagina:
    """Escribe texto de arriba abajo en páginas A4 y abre otra cuando se acaba el espacio."""

    def __init__(self, pdf, pie):
        import matplotlib.pyplot as plt
        self.plt, self.pdf, self.pie, self.n = plt, pdf, pie, 0
        self.fig = None
        self.y = 0.0
        self.nueva()

    def nueva(self):
        if self.fig is not None:
            self.cerrar()
        self.n += 1
        self.fig = self.plt.figure(figsize=A4)
        self.y = 0.95

    def cerrar(self):
        self.fig.text(0.5, 0.02, f'{self.pie} · {self.n}', ha='center', fontsize=7, color='#777')
        self.pdf.savefig(self.fig)
        self.plt.close(self.fig)
        self.fig = None

    def espacio(self, alto):
        if self.y - alto < 0.06:
            self.nueva()

    def titulo(self, texto, tam=14):
        self.espacio(0.06)
        self.fig.text(0.07, self.y, texto, fontsize=tam, fontweight='bold', va='top')
        self.y -= 0.035 + tam/600

    def parrafo(self, texto, tam=9, sangria=0.0, color='black', ancho=ANCHO_TEXTO):
        for i, linea in enumerate(textwrap.wrap(texto, ancho - int(sangria*100)) or ['']):
            self.espacio(0.022)
            self.fig.text(0.07 + sangria, self.y, linea if i == 0 else linea, fontsize=tam, va='top', color=color)
            self.y -= 0.0165*tam/9 + 0.004

    def fila(self, etiqueta, valor, tam=9):
        lineas = textwrap.wrap(str(valor), 62) or ['']
        self.espacio(0.022*len(lineas))
        self.fig.text(0.07, self.y, f'{etiqueta}', fontsize=tam, va='top', color='#444')
        for l in lineas:
            self.fig.text(0.40, self.y, l, fontsize=tam, va='top')
            self.y -= 0.0165*tam/9 + 0.004

    def hueco(self, alto=0.015):
        self.y -= alto

    def eje(self, alto, izq=0.08, ancho=0.84, **kw):
        """Ejes de matplotlib dentro de la página, de `alto` de altura (fracción) bajo el texto escrito."""
        self.espacio(alto + 0.06)
        ax = self.fig.add_axes([izq, self.y - alto, ancho, alto - 0.05], **kw)
        self.y -= alto + 0.01
        return ax


def _valor_parametro(par, valor):
    if par.opciones:
        try:
            return tr(par.opciones[int(valor)])
        except (KeyError, ValueError, TypeError):
            return str(valor)
    return f'{float(valor):g}'


def _pintar_antena(ax, antena):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path

    def pintar(geom, color, alfa):
        for p in poligonos(geom):
            anillos = [np.array(p.exterior.coords)] + [np.array(h.coords) for h in p.interiors]
            verts = np.concatenate(anillos)
            codigos = np.concatenate([[Path.MOVETO] + [Path.LINETO]*(len(a) - 2) + [Path.CLOSEPOLY] for a in anillos])
            ax.add_patch(PathPatch(Path(verts, codigos), fc=color, ec='none', alpha=alfa))
    for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):
        ax.plot(*anillo.xy, 'k-', lw=0.8)
    pintar(antena.cobre('B.Cu'), '#9db3e0', 0.5)
    pintar(antena.cobre('F.Cu'), '#c8892b', 0.95)
    bx, by = antena.puerto['borde']
    ax.plot(bx, by, 'r>', ms=8)
    ax.set_aspect('equal')
    ax.autoscale()
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')


def _smith(ax, f, s, banda, f_obj):
    t = np.linspace(0, 2*np.pi, 200)
    ax.plot(np.cos(t), np.sin(t), color='#999', lw=0.8)
    for r in (0.2, 0.5, 1, 2, 5):
        ax.plot(r/(1 + r) + np.cos(t)/(1 + r), np.sin(t)/(1 + r), color='#ddd', lw=0.6)
    for x in (0.2, 0.5, 1, 2, 5):
        for sg in (1, -1):
            g = (1j*sg*x + np.logspace(-3, 3, 200) - 1)/(1j*sg*x + np.logspace(-3, 3, 200) + 1)
            ax.plot(g.real, g.imag, color='#ddd', lw=0.6)
    ax.plot(np.cos(t)/3, np.sin(t)/3, '--', color='#43a047', lw=0.8)
    ax.plot(s.real, s.imag, color='#5e35b1', lw=1.4)
    if f_obj and f[0] <= f_obj <= f[-1]:
        sm = np.interp(f_obj, f, s.real) + 1j*np.interp(f_obj, f, s.imag)
        ax.plot(sm.real, sm.imag, '*', color='#e53935', ms=9)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(tr('Smith'), fontsize=9)


def _pagina_simulacion(pag, r, d, banda_MHz, f_obj_MHz):
    from . import graficas
    f, s = np.asarray(d['f'], float), np.asarray(d['s11'], complex)
    f_mhz = f/1e6
    db = 20*np.log10(np.abs(s) + 1e-12)
    pag.titulo(tr('Simulación'))
    ax = pag.eje(0.24)
    ax.plot(f_mhz, db, color='#5e35b1', lw=1.4)
    ax.axhline(-10, color='#e53935', ls='--', lw=0.8)
    if banda_MHz:
        ax.axvspan(banda_MHz[0], banda_MHz[1], color='#fb8c00', alpha=0.2)
    ax.set_xlabel('MHz')
    ax.set_ylabel('|S11| [dB]')
    ax.set_title(tr('S11'), fontsize=9)
    ax.grid(alpha=0.3)
    gam = np.abs(s)
    roe = (1 + gam)/(1 - np.minimum(gam, 0.999))
    ax = pag.eje(0.2)
    ax.plot(f_mhz, np.minimum(roe, 6), color='#00897b', lw=1.4)
    ax.axhline(2, color='#e53935', ls='--', lw=0.8)
    if banda_MHz:
        ax.axvspan(banda_MHz[0], banda_MHz[1], color='#fb8c00', alpha=0.2)
    ax.set_xlabel('MHz')
    ax.set_ylabel(tr('ROE'))
    ax.set_title(tr('ROE'), fontsize=9)
    ax.set_ylim(1, 6)
    ax.grid(alpha=0.3)
    ax = pag.eje(0.3, izq=0.27, ancho=0.46)
    _smith(ax, f, s, banda_MHz, f_obj_MHz*1e6 if f_obj_MHz else None)
    # resultados en texto
    pag.titulo(tr('Resultados de la simulación'), 11)
    pag.fila(tr('Resonancia'), tr('{0:g} MHz ({1})', r['f_resonancia_MHz'], r.get('criterio') or tr('centro de la banda a −10 dB')))
    pag.fila(tr('Banda a −10 dB'), '—' if not r.get('banda_MHz') else tr('{0:g}–{1:g} MHz ({2:g} MHz)', r['banda_MHz'][0], r['banda_MHz'][1], r['ancho_banda_MHz']))
    if banda_MHz:
        pag.fila(tr('Banda necesaria'), tr('{0:g}–{1:g} MHz', *banda_MHz))
    pag.fila(tr('S11 mínimo'), tr('{0:g} dB a {1:g} MHz', r['s11_min_dB'], r['f_min_s11_MHz']))
    pag.fila(tr('Directividad / ganancia'), tr('{0:g} / {1:g} dBi', r['directividad_dBi'], r['ganancia_dBi']))
    pag.fila(tr('Eficiencia de radiación / total'), f"{r['eficiencia_radiacion_%']:g} % / {r['eficiencia_total_%']:g} %")
    for av in r.get('avisos', []):
        pag.parrafo('• ' + av, color='#b45309')
    red = r.get('red')
    if red:
        from . import ajuste
        pag.parrafo(tr('Red de adaptación: Z1 en serie = {0}; {1} a masa = {2}. S11 en el objetivo {3:g} dB (sin la red, {4:g} dB).',
                       ajuste.texto_componente(*red['serie']), red['posicion'], ajuste.texto_componente(*red['derivacion']),
                       red['s11_dB'], red['s11_sin_red_dB']))
    tol = r.get('tolerancias')
    if tol and not tol.get('error'):
        veredicto = {'cubre': tr('Cubre la banda con margen aunque la fabricación se desvíe dentro de esas tolerancias.'),
                     'justo': tr('Justo: la antena nominal cubre la banda, pero con esas tolerancias puede quedarse fuera. Deja margen o prevé ajustarla tras fabricar.'),
                     'no_cubre': tr('No cubre la banda: necesita ajuste tras fabricar (o una antena de más banda).')}[tol['veredicto']]
        pag.parrafo(veredicto)
        pag.parrafo(tr('Tolerancias de fabricación: desplazamiento máximo de la frecuencia {0}; suma cuadrática {1:.1f} %. Banda que sobrevive: {2}.',
                       '; '.join(tr('{0} {1:.1f} %', tr(f_['etiqueta']), f_['max_df_pct']) for f_ in tol['filas']), tol['df_total_pct'],
                       tr('{0:g}–{1:g} MHz', *tol['banda_sobrevive_MHz']) if tol['banda_sobrevive_MHz'] else tr('ninguna')))
    en = r.get('entorno')
    if en and not en.get('error'):
        from . import entorno
        pag.parrafo(tr('Con {0}: la frecuencia pasa de {1:g} a {2:g} MHz ({3:+.1f} %), la eficiencia de radiación de {4:g} a {5:g} % y la ganancia de '
                       '{6:g} a {7:g} dBi.', ', '.join(tr(entorno.PREDEFINIDOS[n]).split(' (')[0] for n in en['nombres']), en['f_sin_MHz'], en['f_con_MHz'],
                       en['df_pct'], en['eta_sin_%'], en['eta_con_%'], en['ganancia_sin_dBi'], en['ganancia_con_dBi']))
    v = r.get('verificacion_malla')
    if v and not v.get('error'):
        pag.parrafo(tr('El resultado depende de la malla: no te fíes de un solo punto, mide la antena. ') if v['veredicto'] == 'sensible'
                    else tr('El resultado no depende de la malla. '))
    theta, phi, dd = np.asarray(d.get('theta', [])), np.asarray(d.get('phi', [])), np.asarray(d.get('d', []))
    if theta.size and phi.size and dd.ndim == 2 and dd.size:
        pag.nueva()
        pag.titulo(tr('Diagrama de radiación'))
        dmax = float(np.max(dd))
        for phi0, color, nombre in ((0, '#5e35b1', tr('Plano φ=0° (XZ)')), (90, '#e65100', tr('Plano φ=90° (YZ)'))):
            ang, val = graficas._corte(theta, phi, dd, phi0)
            ax = pag.eje(0.32, izq=0.25, ancho=0.5, projection='polar')
            ax.plot(np.radians(ang), np.maximum(val, dmax - 25), color=color, lw=1.6)
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.set_rlim(dmax - 25, dmax + 1)
            ax.set_title(nombre, fontsize=9)
        pag.parrafo(tr('Diagrama (directividad, máx {0:.1f} dBi)', dmax))
        dm = r.get('direccion_max')
        if dm:
            pag.parrafo(tr('Dirección del máximo: θ {0:g}°, φ {1:g}°', dm['theta'], dm['phi']))


def generar(ruta, antena, nombre, clave, parametros, sustrato, f_MHz, banda_MHz=None, resultado=None, datos=None):
    """Escribe el informe PDF de `antena` en `ruta`. nombre: del diseño; clave: tipo de antena; parametros: los del diseño;
    sustrato: nombre; f_MHz: frecuencia central; banda_MHz: (inf, sup) o None. resultado/datos: `resultado.json` y `datos.npz` de
    la simulación (opcionales). Devuelve `ruta`."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.backends.backend_pdf import PdfPages

    from .tipos import CATALOGO
    tipo = CATALOGO[clave]
    pie = f'Chirptenna · {nombre}'
    with PdfPages(ruta) as pdf:
        pag = _Pagina(pdf, pie)
        pag.fig.text(0.07, 0.95, nombre, fontsize=22, fontweight='bold', va='top')
        pag.fig.text(0.07, 0.91, tr(tipo.nombre), fontsize=12, va='top', color='#444')
        pag.fig.text(0.07, 0.885, time.strftime('%Y-%m-%d'), fontsize=8, va='top', color='#777')
        pag.y = 0.85
        ax = pag.fig.add_axes([0.12, 0.55, 0.76, 0.29])
        _pintar_antena(ax, antena)
        pag.y = 0.47
        pag.fila(tr('Frecuencia central'), f'{f_MHz:g} MHz')
        if banda_MHz:
            pag.fila(tr('Banda necesaria'), tr('{0:g}–{1:g} MHz', *banda_MHz))
        pag.fila(tr('Sustrato'), tr(sustrato))
        est, comentario = problemas.estado(clave)
        pag.fila(tr('Estado del tipo'), tr(problemas.ESTADO_TEXTO.get(est, est)) + (f' · {tr(comentario)}' if comentario else ''))
        for etiqueta, valor in presentacion.filas_info(antena.info):
            if etiqueta in presentacion.ETIQUETAS_INFO.values():       # las claves sin etiqueta son internas
                pag.fila(tr(etiqueta), valor)
        for av in antena.info.get('avisos', []):
            pag.parrafo('• ' + av, color='#b45309')
        # parámetros
        pag.hueco(0.02)
        pag.titulo(tr('Parámetros'))
        visibles = set(presentacion.parametros_visibles(clave, parametros))
        for par in tipo.parametros:
            if par.nombre in visibles and par.nombre in parametros:
                try:
                    pag.fila(tr(par.etiqueta), _valor_parametro(par, parametros[par.nombre]))
                except (TypeError, ValueError):
                    pass
        # problemas conocidos y consejos
        pag.hueco()
        probs = problemas.problemas(clave, parametros, f_MHz)
        if probs:
            pag.titulo(tr('Problemas conocidos'), 12)
            for nivel, texto in probs:
                pag.parrafo(f'• {tr(texto)}', color='#b91c1c' if nivel == 'grave' else 'black')
        pag.parrafo(tr(problemas.AVISO_GENERAL), color='#555')
        pag.hueco()
        banda_hz = (banda_MHz[0]*1e6, banda_MHz[1]*1e6) if banda_MHz else None
        cons = consejos_mod.consejos(antena, f_MHz*1e6, banda_hz)
        if cons:
            pag.titulo(tr('Consejos'), 12)
            for cat, texto in cons:
                pag.parrafo(f'• [{tr(cat)}] {tr(texto)}')
        if resultado and datos is not None and 'f' in datos:
            pag.nueva()
            _pagina_simulacion(pag, resultado, datos, banda_MHz, f_MHz)
        else:
            pag.hueco()
            pag.parrafo(tr('Este diseño no tiene simulación: el informe solo recoge la geometría, los parámetros y los consejos.'), color='#555')
        pag.cerrar()
    return ruta
