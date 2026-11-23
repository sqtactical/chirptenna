"""Vista 3D de la carcasa (Plotly) con la placa: montada, abierta (base + placa) y explosionada (base, placa y tapa separadas).

Usa las mallas de `carcasa.montada` (mismas coordenadas que la simulación: la placa en el plano XY con su cara inferior en z = 0)
y la placa de `vista3d._placa`, desplazada en z para la vista explosionada. Solo en el escritorio: la carcasa necesita shapely ≥ 2.1.
"""
import numpy as np
import plotly.graph_objects as go

from . import carcasa, vista3d
from .i18n import tr, N_

MODOS = {'montada': N_('Montada'), 'abierta': N_('Abierta: base + placa'), 'explosionada': N_('Explosionada')}
COL_PLASTICO, COL_TORNILLO = '#8fa3b8', '#b0b0b0'


def _malla(fig, tris, dz=0.0, opacidad=0.45, nombre=''):
    """Añade una pieza (lista de triángulos) desplazada `dz` en z."""
    t = np.asarray(tris, float)
    if len(t) == 0:
        return
    n = len(t)
    v = t.reshape(-1, 3)
    idx = np.arange(3*n).reshape(-1, 3)
    fig.add_trace(go.Mesh3d(x=v[:, 0], y=v[:, 1], z=v[:, 2] + dz, i=idx[:, 0], j=idx[:, 1], k=idx[:, 2], color=COL_PLASTICO,
                            opacity=opacidad, flatshading=True, name=nombre, hoverinfo='name', showlegend=False,
                            lighting=dict(ambient=0.55, diffuse=0.8)))


def _placa_desplazada(fig, antena, h, dz):
    """La placa de `vista3d._placa` con todas sus trazas subidas `dz`."""
    aux = go.Figure()
    vista3d._placa(aux, antena, h)
    for tr_ in aux.data:
        tr_.z = np.asarray(tr_.z, float) + dz
        fig.add_trace(tr_)


def _tornillos(fig, d, c, dz_tapa):
    """Un trazo por tornillo (cabeza arriba) en las esquinas, para la vista explosionada."""
    if c['fijacion'] == 'adhesivo':
        return
    xs, ys, zs, cx, cy, cz = [], [], [], [], [], []
    for ex, ey in carcasa._esquinas(d):
        xs += [ex, ex, None]; ys += [ey, ey, None]
        zs += [d['z_arriba'] + dz_tapa, d['z_fondo'] + 1.0, None]
        cx.append(ex); cy.append(ey); cz.append(d['z_arriba'] + dz_tapa)
    fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color=COL_TORNILLO, width=4), hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter3d(x=cx, y=cy, z=cz, mode='markers', marker=dict(size=4, color=COL_TORNILLO), name=tr('Tornillo {0}', c['tornillo']),
                               hoverinfo='name', showlegend=False))


def figura(antena, h_mm, c=None, modo='montada'):
    """Figura 3D de la carcasa de `antena`. `modo`: 'montada', 'abierta' o 'explosionada' (ver `MODOS`). Lanza ValueError si no se puede."""
    r = carcasa.montada(antena, h_mm, c)
    d, c = r['dims'], r['parametros']
    fig = go.Figure()
    ancho = max(d['xo1'] - d['xo0'], d['yo1'] - d['yo0'])
    sep = max(12.0, 0.25*ancho)                    # separación de la vista explosionada
    dz_placa, dz_tapa = (0.0, 0.0)
    if modo == 'explosionada':
        dz_placa, dz_tapa = sep, 2*sep + c['espacio_arriba']
    _malla(fig, r['base'], 0.0, 0.5 if modo == 'abierta' else 0.4, tr('Base'))
    _placa_desplazada(fig, antena, h_mm, dz_placa)
    if modo != 'abierta':
        _malla(fig, r['tapa'], dz_tapa, 0.35, tr('Tapa'))
    if modo == 'explosionada':
        _tornillos(fig, d, c, dz_tapa)
        # guías de trazos entre las piezas
        gx, gy, gz = [], [], []
        for ex, ey in carcasa._esquinas(d):
            gx += [ex, ex, None]; gy += [ey, ey, None]; gz += [d['z_fondo'], d['z_arriba'] + dz_tapa, None]
        fig.add_trace(go.Scatter3d(x=gx, y=gy, z=gz, mode='lines', line=dict(color='#888', width=1, dash='dot'), hoverinfo='skip',
                                   showlegend=False))
    eje = dict(showticklabels=False, title='', showgrid=False, zeroline=False, showbackground=False)
    titulo = {'montada': tr('Carcasa montada con la placa dentro'), 'abierta': tr('Base de la carcasa con la placa puesta (sin tapa)'),
              'explosionada': tr('Carcasa explosionada: base, placa y tapa')}[modo]
    titulo += ' · ' + tr('{0:g} × {1:g} × {2:g} mm', d['xo1'] - d['xo0'], d['yo1'] - d['yo0'], d['z_arriba'] - d['z_fondo'])
    alto = d['z_arriba'] - d['z_fondo'] + dz_tapa
    zoom = 1.0 + max(0.0, alto/ancho - 0.3)*0.5
    fig.update_layout(title=titulo, margin=dict(l=0, r=0, t=30, b=0), showlegend=False,
                      scene=dict(xaxis=eje, yaxis=eje, zaxis=eje, aspectmode='data',
                                 camera=dict(eye=dict(x=1.3*zoom, y=-1.6*zoom, z=1.0*zoom))))
    return fig
