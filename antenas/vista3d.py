"""Vista 3D de una antena (Plotly): placas con su grosor, cobre de las dos caras, reflector, vías, taladros, módulos y, si se pasa,
el diagrama de radiación sobre ellas. Se usa como vista previa en Diseño y, con el diagrama, para ver el resultado de una simulación.

Las coordenadas son las de la simulación (mm; la placa en el plano XY, Z hacia arriba, la cara superior es F.Cu), así que el diagrama
de `simulacion.simular` (θ desde +Z, φ desde +X) queda orientado como la antena. El grosor de la placa se **exagera** cuando es
ínfimo frente al tamaño (una colineal de 30 cm con 1,6 mm no se vería): se avisa en el título.

`figura(antena, h_mm, explosionada=False, diagrama=None)`: con `explosionada` y una antena modular dibuja cada placa a fabricar por separado,
en orden y con su cantidad; si no, la antena armada con las uniones marcadas.
"""
import numpy as np
import plotly.graph_objects as go

from . import conector
from .geometria import poligonos
from .graficas import _malla_poligono
from .i18n import tr, N_

COL_FR4, COL_SUP, COL_INF, COL_REF = '#2e7d32', '#c8892b', '#7f9ed6', '#9e9e9e'
GROSOR_MIN_REL = 0.012          # el grosor dibujado no baja de esta fracción del lado mayor
NOMBRES_MODULO = {'inicio': N_('inicio'), 'modulo': N_('módulo'), 'final': N_('final')}


def _dim(antena):
    x0, y0, x1, y1 = antena.contorno.bounds
    return max(x1 - x0, y1 - y0)


def _paredes(contorno, z0, z1):
    """Cantos de la placa (exterior y ventanas) como triángulos entre z0 y z1: (x, y, z, i, j, k)."""
    xs, ys, zs, ii, jj, kk = [], [], [], [], [], []
    for pol in poligonos(contorno):
        for anillo in [pol.exterior] + list(pol.interiors):
            c = np.array(anillo.coords)
            for (xa, ya), (xb, yb) in zip(c[:-1], c[1:]):
                n = len(xs)
                xs += [xa, xb, xb, xa]; ys += [ya, yb, yb, ya]; zs += [z0, z0, z1, z1]
                ii += [n, n]; jj += [n + 1, n + 2]; kk += [n + 2, n + 3]
    return np.array(xs), np.array(ys), np.array(zs), ii, jj, kk


def _unir(partes):
    """Une varias mallas (x, y, z, i, j, k) en una sola."""
    xs, ys, zs, ii, jj, kk, n = [], [], [], [], [], [], 0
    for x, y, z, i, j, k in partes:
        if len(x) == 0:
            continue
        xs.append(x); ys.append(y); zs.append(z)
        ii += [v + n for v in i]; jj += [v + n for v in j]; kk += [v + n for v in k]
        n += len(x)
    if not xs:
        return None
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(zs), ii, jj, kk


def _placa(fig, antena, h, dy=0.0, etiqueta=None, primera=True):
    """Dibuja una placa (FR4 con grosor `h`, cobre arriba y abajo, contorno, vías y conector) desplazada `dy` en Y."""
    e = 0.02*h
    losa = _unir([_malla_poligono(antena.contorno, 0.0), _malla_poligono(antena.contorno, h), _paredes(antena.contorno, 0.0, h)])
    if losa is not None:
        x, y, z, i, j, k = losa
        fig.add_trace(go.Mesh3d(x=x, y=y + dy, z=z, i=i, j=j, k=k, color=COL_FR4, opacity=0.35, flatshading=True,
                                name='FR4', hoverinfo='name', showlegend=primera and etiqueta is None))
    for capa, z0, color, nombre, op in (('B.Cu', -e, COL_INF, tr('Cara inferior'), 0.95), ('F.Cu', h + e, COL_SUP, tr('Cara superior'), 1.0)):
        cobre = antena.cobre(capa)
        m = _malla_poligono(cobre, z0) if cobre is not None and not cobre.is_empty else None
        if m is not None and len(m[3]):
            x, y, z, i, j, k = m
            fig.add_trace(go.Mesh3d(x=x, y=y + dy, z=z, i=i, j=j, k=k, color=color, opacity=op, flatshading=True,
                                    name=nombre, hoverinfo='name', showlegend=False))
    xs, ys, zs = [], [], []
    for pol in poligonos(antena.contorno):
        for anillo in [pol.exterior] + list(pol.interiors):
            c = np.array(anillo.coords)
            xs += list(c[:, 0]) + [None]; ys += list(c[:, 1] + dy) + [None]; zs += [h] * len(c) + [None]
    fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='#444', width=2), hoverinfo='skip', showlegend=False))
    if antena.vias:
        vx, vy, vz = [], [], []
        for x, y in antena.vias:
            vx += [x, x, None]; vy += [y + dy, y + dy, None]; vz += [-e, h + e, None]
        fig.add_trace(go.Scatter3d(x=vx, y=vy, z=vz, mode='lines', line=dict(color='#b71c1c', width=5), name=tr('Vías'),
                                   hoverinfo='name', showlegend=False))
    bx, by = antena.puerto['borde']
    if antena.puerto.get('conector') != conector.SIN:                  # los módulos intermedios no llevan conector
        fig.add_trace(go.Scatter3d(x=[bx], y=[by + dy], z=[h + e], mode='markers', marker=dict(size=5, color='red'),
                                   name=tr('Conector'), hoverinfo='name', showlegend=False))
    if etiqueta:
        x0, y0, x1, y1 = antena.contorno.bounds
        fig.add_trace(go.Scatter3d(x=[(x0 + x1)/2], y=[(y0 + y1)/2 + dy], z=[h*3], mode='text', text=[etiqueta], textposition='top center',
                                   textfont=dict(size=11), hoverinfo='skip', showlegend=False))


def _reflector(fig, antena, h):
    r = antena.reflector
    if not r:
        return
    z = -r['separacion_mm']
    m = _malla_poligono(r['contorno'], z)
    if len(m[3]):
        x, y, zz, i, j, k = m
        fig.add_trace(go.Mesh3d(x=x, y=y, z=zz, i=i, j=j, k=k, color=COL_REF, opacity=0.55, flatshading=True,
                                name=tr('Reflector'), hoverinfo='name', showlegend=False))
    hilos = r.get('hilos') or []
    if hilos:
        xs, ys, zs = [], [], []
        for x, y in hilos:
            xs += [x, x, None]; ys += [y, y, None]; zs += [z, 0.0, None]
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='#555', width=4), hoverinfo='skip', showlegend=False))


def _uniones(fig, antena, h):
    """Marca con una línea de trazos cada unión entre las placas de una antena modular armada."""
    x0, _, x1, _ = antena.contorno.bounds
    y = 0.0
    xs, ys, zs = [], [], []
    piezas = [m for m in antena.modulos for _ in range(int(m['cantidad']))]
    for m in piezas[:-1]:
        y += m['antena'].contorno.bounds[3]
        xs += [x0, x1, None]; ys += [y, y, None]; zs += [h*1.6, h*1.6, None]
    if xs:
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='#e53935', width=3, dash='dash'),
                                   name=tr('Uniones entre placas'), hoverinfo='name', showlegend=False))


def _diagrama(fig, antena, h, theta, phi, d, piso=-20):
    """Superficie del diagrama (radio ∝ dB sobre el piso) centrada en la placa, con la dirección del máximo."""
    x0, y0, x1, y1 = antena.contorno.bounds
    cx, cy, cz = (x0 + x1)/2, (y0 + y1)/2, h/2
    dmax = float(np.max(d))
    R = 0.65*max(_dim(antena), 40.0)                 # radio del diagrama: sobresale de la placa pero la deja ver
    r = np.clip(d - (dmax + piso), 0, None)/(-piso)*R
    th, ph = np.meshgrid(np.radians(theta), np.radians(phi), indexing='ij')
    fig.add_trace(go.Surface(x=cx + r*np.sin(th)*np.cos(ph), y=cy + r*np.sin(th)*np.sin(ph), z=cz + r*np.cos(th), surfacecolor=d,
                             colorscale='Plasma', cmin=dmax + piso, cmax=dmax, opacity=0.45, name=tr('Diagrama'),
                             colorbar=dict(title='dBi', thickness=12), hovertemplate='%{surfacecolor:.1f} dBi<extra></extra>'))
    it, ip = np.unravel_index(np.argmax(d), d.shape)
    t_, p_ = np.radians(theta[it]), np.radians(phi[ip])
    u = np.array([np.sin(t_)*np.cos(p_), np.sin(t_)*np.sin(p_), np.cos(t_)])*R*1.08
    fig.add_trace(go.Scatter3d(x=[cx, cx + u[0]], y=[cy, cy + u[1]], z=[cz, cz + u[2]], mode='lines+markers+text',
                               text=['', tr('máx {0:.1f} dBi', dmax)], textposition='top center', marker=dict(size=[0, 6], color='#e53935'),
                               line=dict(color='#e53935', width=5), textfont=dict(color='#e53935'), hoverinfo='skip', showlegend=False))
    return theta[it], phi[ip], dmax


def figura(antena, h_mm=1.6, explosionada=False, diagrama=None):
    """Figura 3D de la antena. diagrama = (theta, phi, d) de un resultado de simulación (superficie sobre la placa)."""
    dim = _dim(antena)
    h = max(float(h_mm), GROSOR_MIN_REL*dim)
    exagerado = h > h_mm*1.01
    fig = go.Figure()
    titulo = tr('Vista 3D')
    if explosionada and antena.modulos:
        gap = max(10.0, 0.06*dim)
        dy = 0.0
        for m in antena.modulos:
            n = int(m['cantidad'])
            for c in range(n):
                nombre = tr(NOMBRES_MODULO.get(m['nombre'], m['nombre']))
                _placa(fig, m['antena'], h, dy, etiqueta=nombre + (f' {c + 1}/{n}' if n > 1 else ''), primera=dy == 0.0)
                dy += m['antena'].contorno.bounds[3] + gap
        titulo = tr('Vista 3D explosionada: placas a fabricar')
    else:
        _placa(fig, antena, h)
        _reflector(fig, antena, h)
        if antena.modulos:
            _uniones(fig, antena, h)
        if diagrama is not None:
            t, p, dm = _diagrama(fig, antena, h, *diagrama)
            titulo = tr('Diagrama 3D con la placa · máximo θ {0:.0f}°, φ {1:.0f}°', t, p)
    if exagerado:
        titulo += ' · ' + tr('grosor exagerado')
    eje = dict(showticklabels=False, title='', showgrid=False, zeroline=False, showbackground=False)
    fig.update_layout(title=titulo, margin=dict(l=0, r=0, t=30, b=0), showlegend=False,
                      scene=dict(xaxis=eje, yaxis=eje, zaxis=eje, aspectmode='data', camera=dict(eye=_camara(fig, antena, explosionada))))
    return fig


def _camara(fig, antena, explosionada):
    """Cámara oblicua que enfoca toda la escena: más lejos cuanto más alargada es (una colineal de 30 cm, o las placas en fila)."""
    xs = [float(v) for t in fig.data if t.type == 'mesh3d' for v in (min(t.x), max(t.x))]
    ys = [float(v) for t in fig.data if t.type == 'mesh3d' for v in (min(t.y), max(t.y))]
    ancho, largo = (max(xs) - min(xs)), (max(ys) - min(ys))
    alargada = max(largo, ancho)/max(min(largo, ancho), 1.0)
    zoom = 1.0 + min(alargada, 16.0)*0.12
    return dict(x=1.2*zoom, y=-1.6*zoom, z=1.0*zoom)
