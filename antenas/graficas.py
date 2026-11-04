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


def roe(f, s, banda=None, f_obj=None, techo=6.0):
    """ROE (VSWR) frente a la frecuencia, con las líneas de 2 (≈ −10 dB) y 1,5 (≈ −14 dB)."""
    g = np.minimum(np.abs(s), 0.999)
    v = (1 + g)/(1 - g)
    fig = go.Figure()
    if banda:
        fig.add_vrect(x0=banda[0]/1e6, x1=banda[1]/1e6, fillcolor='orange', opacity=0.2, line_width=0,
                      annotation_text='banda', annotation_position='top left')
    fig.add_hline(y=2, line_dash='dash', line_color='grey', line_width=1, annotation_text='2 (−10 dB)',
                  annotation_position='bottom right')
    fig.add_hline(y=1.5, line_dash='dot', line_color='grey', line_width=1)
    fig.add_trace(go.Scatter(x=f/1e6, y=np.minimum(v, techo), mode='lines', line=dict(color='#00897b', width=2),
                             customdata=v, name='ROE',
                             hovertemplate='%{x:.1f} MHz<br>ROE %{customdata:.2f}<extra></extra>'))
    titulo = 'ROE'
    if f_obj:
        vo = float(np.interp(f_obj, f, v))
        titulo += f' · {vo:.2f} en {f_obj/1e6:g} MHz'.replace('.', ',', 1)
        fig.add_vline(x=f_obj/1e6, line_color='#e53935', line_width=1)
    fig.update_layout(title=titulo, xaxis_title='MHz', yaxis_title='ROE', margin=_MARGEN, plot_bgcolor='white',
                      showlegend=False, yaxis=dict(range=[1, techo]))
    fig.update_xaxes(gridcolor='#eee'); fig.update_yaxes(gridcolor='#eee')
    return fig


def smith(f, s, banda=None, f_obj=None):
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
    # Círculo de ROE 2 (|Γ| = 1/3, ≈ −10 dB): lo que quede dentro está adaptado
    fig.add_trace(go.Scatter(x=np.cos(t)/3, y=np.sin(t)/3, mode='lines', hoverinfo='skip',
                             line=dict(color='#43a047', width=1, dash='dash')))
    # Bordes de la banda (●) y frecuencia objetivo (★)
    marcas = []
    if banda:
        marcas += [(banda[0], 'circle', '#fb8c00', 'inicio de banda'), (banda[1], 'circle', '#fb8c00', 'fin de banda')]
    if f_obj:
        marcas.append((f_obj, 'star', '#e53935', 'objetivo'))
    for fm, simbolo, color, texto in marcas:
        if not (f[0] <= fm <= f[-1]):
            continue
        sm = np.interp(fm, f, s.real) + 1j*np.interp(fm, f, s.imag)
        zm = 50*(1 + sm)/(1 - sm)
        fig.add_trace(go.Scatter(x=[sm.real], y=[sm.imag], mode='markers',
                                 marker=dict(symbol=simbolo, size=12 if simbolo == 'star' else 9, color=color),
                                 hovertemplate=f'{texto}: {fm/1e6:g} MHz<br>Z = {zm.real:.1f} {zm.imag:+.1f}j Ω'
                                               '<extra></extra>'))
    fig.update_layout(title='Smith' + (' · ★ objetivo ● banda' if marcas else ''), margin=dict(l=10, r=10, t=30, b=10), showlegend=False,
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


def _malla_poligono(geom, z):
    """Triangulación (Delaunay restringida) de un polígono de shapely para un Mesh3d plano a altura z."""
    import shapely
    from .geometria import poligonos
    xs, ys, ii, jj, kk = [], [], [], [], []
    for pol in poligonos(geom):
        for tri in shapely.constrained_delaunay_triangles(pol).geoms:
            c = np.array(tri.exterior.coords[:3])
            n = len(xs)
            xs += list(c[:, 0]); ys += list(c[:, 1])
            ii.append(n); jj.append(n + 1); kk.append(n + 2)
    return np.array(xs), np.array(ys), np.full(len(xs), z), ii, jj, kk


def diagrama_3d(theta, phi, d, piso=-20, antena=None, h_mm=1.6):
    """Superficie 3D: radio proporcional a la directividad en dB por encima del piso.

    Con `antena`, dibuja también la placa (contorno, FR4, cobre de las dos caras, reflector y conector) en
    sus coordenadas reales, centrada y escalada a ~0,7 del radio del diagrama, más los
    ejes X/Y/Z y la dirección del máximo. Los ejes del diagrama son los mismos que los de la vista 2D.
    """
    dmax = float(np.max(d))
    R = -piso                                     # radio del diagrama (dB por encima del piso)
    r = np.clip(d - (dmax + piso), 0, None)
    th, ph = np.meshgrid(np.radians(theta), np.radians(phi), indexing='ij')
    x = r*np.sin(th)*np.cos(ph)
    y = r*np.sin(th)*np.sin(ph)
    z = r*np.cos(th)
    fig = go.Figure(go.Surface(x=x, y=y, z=z, surfacecolor=d, colorscale='Plasma', cmin=dmax + piso, cmax=dmax,
                               colorbar=dict(title='dBi', thickness=12), opacity=0.45 if antena else 1.0,
                               name='Diagrama', hovertemplate='%{surfacecolor:.1f} dBi<extra></extra>'))
    titulo = 'Diagrama 3D (Z: perpendicular a la placa)'
    if antena is not None:
        x0, y0, x1, y1 = antena.contorno.bounds
        cx, cy = (x0 + x1)/2, (y0 + y1)/2
        semi = max(np.hypot(x1 - x0, y1 - y0)/2, 1e-3)
        k = 0.7*R/semi                            # mm → unidades del diagrama
        esp = max(h_mm*k, 0.25)                   # grosor exagerado para que se vean las dos caras

        def plano(geom, zz, color, opacidad, nombre):
            if geom is None or geom.is_empty:
                return
            px, py, pz, i, j, kk = _malla_poligono(geom, zz)
            if len(i):
                fig.add_trace(go.Mesh3d(x=(px - cx)*k, y=(py - cy)*k, z=pz, i=i, j=j, k=kk, color=color,
                                        opacity=opacidad, name=nombre, hoverinfo='name', showlegend=False,
                                        flatshading=True))

        plano(antena.contorno, 0.0, '#2e7d32', 0.35, 'FR4')
        plano(antena.cobre('B.Cu'), -0.02, '#7f9ed6', 0.95, 'Cara inferior')
        plano(antena.cobre('F.Cu'), esp, '#c8892b', 1.0, 'Cara superior')
        if antena.reflector:
            plano(antena.reflector['contorno'], -antena.reflector['separacion_mm']*k, '#9e9e9e', 0.6, 'Reflector')
        for anillo in [antena.contorno.exterior] + list(antena.contorno.interiors):
            ax_, ay_ = np.array(anillo.coords).T
            fig.add_trace(go.Scatter3d(x=(ax_ - cx)*k, y=(ay_ - cy)*k, z=np.zeros(len(ax_)), mode='lines',
                                       line=dict(color='#444', width=3), hoverinfo='skip', showlegend=False))
        bx, by = antena.puerto['borde']
        fig.add_trace(go.Scatter3d(x=[(bx - cx)*k], y=[(by - cy)*k], z=[esp], mode='markers',
                                   marker=dict(size=5, color='red'), name='Conector', hoverinfo='name',
                                   showlegend=False))
        # Ejes y dirección del máximo
        L = 1.15*R
        for (ex, ey, ez), nombre in (((L, 0, 0), 'X'), ((0, L, 0), 'Y'), ((0, 0, L), 'Z')):
            fig.add_trace(go.Scatter3d(x=[0, ex], y=[0, ey], z=[0, ez], mode='lines+text', text=['', nombre],
                                       textposition='top center', line=dict(color='#444', width=3),
                                       textfont=dict(size=13), hoverinfo='skip', showlegend=False))
        it, ip = np.unravel_index(np.argmax(d), d.shape)
        t_, p_ = np.radians(theta[it]), np.radians(phi[ip])
        u = np.array([np.sin(t_)*np.cos(p_), np.sin(t_)*np.sin(p_), np.cos(t_)])*R*1.08
        fig.add_trace(go.Scatter3d(x=[0, u[0]], y=[0, u[1]], z=[0, u[2]], mode='lines+markers+text',
                                   text=['', f'máx {dmax:.1f} dBi'], textposition='top center',
                                   marker=dict(size=[0, 6], color='#e53935'), line=dict(color='#e53935', width=5),
                                   textfont=dict(color='#e53935'), hoverinfo='skip', showlegend=False))
        titulo = f'Diagrama 3D con la placa · máximo θ {theta[it]:.0f}°, φ {phi[ip]:.0f}°'
    eje = dict(showticklabels=False, title='', showgrid=False, zeroline=False, showbackground=False)
    fig.update_layout(title=titulo, margin=dict(l=0, r=0, t=30, b=0),
                      scene=dict(xaxis=eje, yaxis=eje, zaxis=eje, aspectmode='data',
                                 camera=dict(eye=dict(x=1.3, y=-1.5, z=0.9))))
    return fig
