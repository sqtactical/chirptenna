"""Miniaturas SVG de cada tipo de antena para la galería (escritorio y web).

`svg(clave)` dibuja el tipo con sus valores por defecto dimensionados a 2441,75 MHz (868 MHz si su diseño de
partida es de esa banda): contorno, masa (cara inferior) y cobre (cara superior), sin texto. Colores fijos que se
leen en tema claro y oscuro. `herramientas/generar_miniaturas.py` las guarda en `antenas/miniaturas/<clave>.svg`
(las usa el escritorio; la web las vuelve a generar al construirse). Regenerarlas si cambia un generador.
"""
from . import tipos
from .geometria import poligonos

F_MINIATURA = {'monopolo_hilbert': 866.5e6}       # el resto, a 2441,75 MHz
COBRE, MASA, BORDE, FONDO = '#c8892b', '#7f9ed6', '#8a969c', 'rgba(138,150,156,0.12)'


def _ruta(geom, flip):
    trozos = []
    for p in poligonos(geom):
        for anillo in [p.exterior] + list(p.interiors):
            trozos.append('M' + 'L'.join(f'{x:.2f},{flip - y:.2f}' for x, y in anillo.coords) + 'Z')
    return ''.join(trozos)


def svg(clave, ancho_px=160, alto_px=120):
    p = tipos.dimensionar(clave, F_MINIATURA.get(clave, 2441.75e6), {})
    p.pop('_aviso', None)
    a = tipos.generar(clave, p)
    geoms = [a.contorno] + ([a.reflector['contorno']] if a.reflector else [])
    x0 = min(g.bounds[0] for g in geoms); y0 = min(g.bounds[1] for g in geoms)
    x1 = max(g.bounds[2] for g in geoms); y1 = max(g.bounds[3] for g in geoms)
    m = 0.04*max(x1 - x0, y1 - y0)
    flip = y0 + y1                                    # y hacia arriba en el modelo, hacia abajo en SVG
    g = max(x1 - x0, y1 - y0)/160
    partes = []
    if a.reflector:
        partes.append(f'<path d="{_ruta(a.reflector["contorno"], flip)}" fill="none" stroke="{BORDE}" '
                      f'stroke-width="{1.2*g:.3f}" stroke-dasharray="{3*g:.3f} {2*g:.3f}"/>')
    partes.append(f'<path d="{_ruta(a.contorno, flip)}" fill="{FONDO}" fill-rule="evenodd" stroke="{BORDE}" '
                  f'stroke-width="{1.2*g:.3f}"/>')
    inf = a.cobre('B.Cu')
    if inf is not None and not inf.is_empty:
        partes.append(f'<path d="{_ruta(inf, flip)}" fill="{MASA}" fill-opacity="0.55" fill-rule="evenodd"/>')
    partes.append(f'<path d="{_ruta(a.cobre("F.Cu"), flip)}" fill="{COBRE}" fill-rule="evenodd"/>')
    vb = f'{x0 - m:.2f} {flip - y1 - m:.2f} {x1 - x0 + 2*m:.2f} {y1 - y0 + 2*m:.2f}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{ancho_px}" height="{alto_px}" '
            f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="{tipos.CATALOGO[clave].nombre}">'
            + ''.join(partes) + '</svg>')
