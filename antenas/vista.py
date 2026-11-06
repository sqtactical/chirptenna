"""Vista previa de una antena con matplotlib (PNG) y figura de Plotly (interfaz)."""
import numpy as np

from .geometria import poligonos
from .i18n import tr


def _anillos(geom):
    """Contornos (exterior + huecos) de cada polígono, para dibujar con relleno par-impar."""
    out = []
    for p in poligonos(geom):
        out.append([np.array(p.exterior.coords)] + [np.array(h.coords) for h in p.interiors])
    return out


def dibujar_png(antena, ruta, titulo=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    fig, ax = plt.subplots(figsize=(8, 8), tight_layout=True)

    def pintar(geom, color, alfa):
        for anillos in _anillos(geom):
            verts = np.concatenate(anillos)
            codigos = np.concatenate([[Path.MOVETO] + [Path.LINETO]*(len(a) - 2) + [Path.CLOSEPOLY] for a in anillos])
            ax.add_patch(PathPatch(Path(verts, codigos), fc=color, ec='none', alpha=alfa))

    if antena.reflector:
        x, y = antena.reflector['contorno'].exterior.xy
        ax.plot(x, y, '--', color='#888', lw=1)
    for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):   # con las ventanas de aligerado
        x, y = anillo.xy
        ax.plot(x, y, 'k-', lw=1)
    pintar(antena.cobre('B.Cu'), '#9db3e0', 0.5)
    pintar(antena.cobre('F.Cu'), '#c8892b', 0.95)
    bx, by = antena.puerto['borde']
    ax.plot(bx, by, 'r>', ms=12)
    ax.set_aspect('equal'); ax.autoscale()
    ax.set_title(titulo or tr('{0} — f estimada {1} MHz', antena.tipo, antena.info.get('f_estimada_MHz')))
    ax.set_xlabel('mm'); ax.set_ylabel('mm')
    fig.savefig(ruta, dpi=110)
    plt.close(fig)


def figura_plotly(antena):
    import plotly.graph_objects as go
    fig = go.Figure()

    def trazas(geom, color, nombre, opacidad):
        primero = True
        for anillos in _anillos(geom):
            xs, ys = [], []
            for a in anillos:
                xs += list(a[:, 0]) + [None]
                ys += list(a[:, 1]) + [None]
            fig.add_trace(go.Scatter(x=xs, y=ys, fill='toself', fillcolor=color, mode='lines',
                                     line=dict(color=color, width=0.5), opacity=opacidad, name=nombre,
                                     legendgroup=nombre, showlegend=primero, hoverinfo='skip'))
            primero = False

    if antena.reflector:
        x, y = antena.reflector['contorno'].exterior.xy
        fig.add_trace(go.Scatter(x=list(x), y=list(y), mode='lines', line=dict(color='#888', width=1.5, dash='dash'),
                                 name=f'Reflector (a {antena.reflector["separacion_mm"]:.1f} mm por detrás)',
                                 hoverinfo='skip'))
    xs, ys = [], []
    for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):   # con las ventanas de aligerado
        x, y = anillo.xy
        xs += list(x) + [None]
        ys += list(y) + [None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line=dict(color='#444', width=1.5),
                             name='Contorno de la placa', hoverinfo='skip'))
    taladros = list(antena.taladros)
    if antena.puerto.get('tipo') == 'pasante':
        taladros.append((*antena.puerto['alimentacion'], antena.puerto['taladro_mm']))
    for tx_, ty_, d in taladros:
        fig.add_shape(type='circle', x0=tx_ - d/2, x1=tx_ + d/2, y0=ty_ - d/2, y1=ty_ + d/2,
                      line=dict(color='#444', width=1))
    trazas(antena.cobre('B.Cu'), '#7f9ed6', tr('Masa (cara inferior)'), 0.45)
    trazas(antena.cobre('F.Cu'), '#c8892b', tr('Cobre (cara superior)'), 0.95)
    aj = antena.ajuste or {}
    # Componentes de ajuste (red en π, puentes): contorno de cada pad y su referencia
    xs, ys, tx, ty, tt = [], [], [], [], []
    for c in aj.get('componentes', []):
        r = int(round(c['rot']/90.0)) % 4
        for dx, dy, w, h in c['pads']:
            rx, ry = [(dx, dy), (-dy, dx), (-dx, -dy), (dy, -dx)][r]
            sw, sh = (h, w) if r % 2 else (w, h)
            x0, y0 = c['x'] + rx - sw/2, c['y'] + ry - sh/2
            xs += [x0, x0 + sw, x0 + sw, x0, x0, None]
            ys += [y0, y0, y0 + sh, y0 + sh, y0, None]
        tx.append(c['x']); ty.append(c['y']); tt.append(f"{c['ref']}: {c['valor']}")
    if xs:
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line=dict(color='#00897b', width=1.5),
                                 name='Componentes de ajuste', hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=tx, y=ty, mode='markers', marker=dict(size=4, color='#00897b'), text=tt,
                                 hovertemplate='%{text}<extra></extra>', showlegend=False))
    # Marcas de corte (serigrafía)
    xs, ys, tx, ty, tt = [], [], [], [], []
    for m in aj.get('marcas', []):
        (ax, ay), (bx_, by_) = m['linea']
        xs += [ax, bx_, None]; ys += [ay, by_, None]
        tx.append(m['pos'][0]); ty.append(m['pos'][1]); tt.append(m['texto'])
    if xs:
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line=dict(color='black', width=2),
                                 name='Marcas de corte (MHz)', hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=tx, y=ty, mode='text', text=tt, textfont=dict(size=10), showlegend=False,
                                 hoverinfo='skip'))
    bx, by = antena.puerto['borde']
    fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(symbol='triangle-right', size=14, color='red'),
                             name=(tr('Toma del coaxial') if antena.puerto.get('tipo') in ('coaxial', 'pasante') or antena.puerto.get('conector') == 2 else
                                   tr('Conector ({0})', "IPEX" if antena.puerto.get("conector") == 1 else "SMA"))))
    if antena.puerto.get('conector') == 1:
        from .conector import pads_ipex
        pads, vias, _ = pads_ipex(antena.puerto)
        for nombre, (x, y), (sx, sy) in pads:
            fig.add_shape(type='rect', x0=x - sx/2, x1=x + sx/2, y0=y - sy/2, y1=y + sy/2,
                          line=dict(color='red', width=1), fillcolor='rgba(255,0,0,0.25)')
    fig.update_yaxes(scaleanchor='x', scaleratio=1, title='mm')
    fig.update_xaxes(title='mm')
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation='h', y=-0.12),
                      plot_bgcolor='white', dragmode='pan')
    return fig
