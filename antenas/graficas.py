"""Gráficas de Plotly para los resultados de simulación (S11, Smith y diagrama de radiación)."""
import numpy as np
import plotly.graph_objects as go

_MARGEN = dict(l=40, r=10, t=30, b=40)


def s11(f, s, banda=None):
    db = 20*np.log10(np.abs(s))
    fig = go.Figure()
    if banda:
        fig.add_vrect(x0=banda[0]/1e6, x1=banda[1]/1e6, fillcolor='orange', opacity=0.2, line_width=0,
                      annotation_text='banda', annotation_position='top left')
    fig.add_hline(y=-10, line_dash='dash', line_color='grey', line_width=1)
    fig.add_trace(go.Scatter(x=f/1e6, y=db, mode='lines', line=dict(color='#5e35b1', width=2), name='|S11|',
                             hovertemplate='%{x:.1f} MHz<br>%{y:.1f} dB<extra></extra>'))
    fig.update_layout(title='Adaptación |S11|', xaxis_title='MHz', yaxis_title='dB', margin=_MARGEN,
                      plot_bgcolor='white', showlegend=False)
    fig.update_xaxes(gridcolor='#eee'); fig.update_yaxes(gridcolor='#eee')
    return fig


COLORES_MEDIDAS = ['#00897b', '#e53935', '#1e88e5', '#f9a825', '#6d4c41', '#8e24aa']


def s11_comparada(curvas, banda=None, titulo='|S11| simulado frente a medido'):
    """Varias curvas |S11| superpuestas: curvas = [(nombre, f [Hz], s11 complejo, simulada?)]."""
    fig = go.Figure()
    if banda:
        fig.add_vrect(x0=banda[0]/1e6, x1=banda[1]/1e6, fillcolor='orange', opacity=0.2, line_width=0,
                      annotation_text='banda', annotation_position='top left')
    fig.add_hline(y=-10, line_dash='dash', line_color='grey', line_width=1)
    i = 0
    for nombre, f, s, simulada in curvas:
        if simulada:
            linea = dict(color='#5e35b1', width=2, dash='dash')
        else:
            linea = dict(color=COLORES_MEDIDAS[i % len(COLORES_MEDIDAS)], width=2)
            i += 1
        fig.add_trace(go.Scatter(x=np.asarray(f)/1e6, y=20*np.log10(np.abs(s)), mode='lines', line=linea, name=nombre,
                                 hovertemplate='%{x:.1f} MHz<br>%{y:.1f} dB<extra>' + nombre + '</extra>'))
    fig.update_layout(title=titulo, xaxis_title='MHz', yaxis_title='dB', margin=_MARGEN, plot_bgcolor='white',
                      legend=dict(orientation='h', y=-0.25))
    fig.update_xaxes(gridcolor='#eee'); fig.update_yaxes(gridcolor='#eee')
    return fig


def smith(f, s):
    fig = go.Figure()
    t = np.linspace(0, 2*np.pi, 200)
    rejilla = dict(color='#ddd', width=1)
    fig.add_trace(go.Scatter(x=np.cos(t), y=np.sin(t), mode='lines', line=dict(color='#999', width=1), hoverinfo='skip'))
    for r in (0.2, 0.5, 1, 2, 5):
        c, rad = r/(1 + r), 1/(1 + r)
        fig.add_trace(go.Scatter(x=c + rad*np.cos(t), y=rad*np.sin(t), mode='lines', line=rejilla, hoverinfo='skip'))
    for x in (0.2, 0.5, 1, 2, 5):
        for sg in (1, -1):
            z = 1j*sg*x + np.logspace(-3, 3, 200)
            g = (z - 1)/(z + 1)
            fig.add_trace(go.Scatter(x=g.real, y=g.imag, mode='lines', line=rejilla, hoverinfo='skip'))
    z = 50*(1 + s)/(1 - s)
    fig.add_trace(go.Scatter(x=s.real, y=s.imag, mode='lines', line=dict(color='#5e35b1', width=2),
                             customdata=np.stack([f/1e6, z.real, z.imag], axis=1),
                             hovertemplate='%{customdata[0]:.1f} MHz<br>Z = %{customdata[1]:.1f} %{customdata[2]:+.1f}j Ω<extra></extra>'))
    fig.update_layout(title='Carta de Smith', margin=dict(l=10, r=10, t=30, b=10), showlegend=False,
                      plot_bgcolor='white', xaxis=dict(visible=False, range=[-1.05, 1.05]),
                      yaxis=dict(visible=False, range=[-1.05, 1.05], scaleanchor='x', scaleratio=1))
    return fig


def _corte(theta, phi, d, phi0):
    """Corte completo (0–360°) en el plano φ = phi0 usando φ0 y φ0+180."""
    ip = int(np.argmin(np.abs(phi - phi0)))
    iq = int(np.argmin(np.abs(phi - (phi0 + 180) % 360)))
    ang = np.concatenate([theta, 360 - theta[::-1]])
    val = np.concatenate([d[:, ip], d[::-1, iq]])
    return ang, val


def cortes_polares(theta, phi, d, piso=-25):
    fig = go.Figure()
    dmax = float(np.max(d))
    for phi0, color, nombre in ((0, '#5e35b1', 'Plano φ=0° (XZ)'), (90, '#e65100', 'Plano φ=90° (YZ)')):
        ang, val = _corte(theta, phi, d, phi0)
        fig.add_trace(go.Scatterpolar(theta=ang, r=np.maximum(val, dmax + piso), mode='lines', name=nombre,
                                      line=dict(color=color, width=2)))
    fig.update_layout(title=f'Diagrama (directividad, máx {dmax:.1f} dBi)', margin=dict(l=20, r=20, t=40, b=20),
                      polar=dict(radialaxis=dict(range=[dmax + piso, dmax + 1], ticksuffix=' dBi'),
                                 angularaxis=dict(direction='clockwise', rotation=90)),
                      legend=dict(orientation='h', y=-0.1))
    return fig


def diagrama_3d(theta, phi, d, piso=-20):
    """Superficie 3D: radio proporcional a la directividad en dB por encima del piso."""
    dmax = float(np.max(d))
    r = np.clip(d - (dmax + piso), 0, None)
    th, ph = np.meshgrid(np.radians(theta), np.radians(phi), indexing='ij')
    x = r*np.sin(th)*np.cos(ph)
    y = r*np.sin(th)*np.sin(ph)
    z = r*np.cos(th)
    fig = go.Figure(go.Surface(x=x, y=y, z=z, surfacecolor=d, colorscale='Plasma', cmin=dmax + piso, cmax=dmax,
                               colorbar=dict(title='dBi', thickness=12),
                               hovertemplate='%{surfacecolor:.1f} dBi<extra></extra>'))
    eje = dict(showticklabels=False, title='', showgrid=False, zeroline=False, showbackground=False)
    fig.update_layout(title='Diagrama 3D (Z: perpendicular a la placa)', margin=dict(l=0, r=0, t=30, b=0),
                      scene=dict(xaxis=eje, yaxis=eje, zaxis=eje, aspectmode='data'))
    return fig
