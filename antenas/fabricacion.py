"""Comprobaciones de fabricación (reglas del fabricante) sobre el cobre de una antena."""
import shapely

from .geometria import poligonos

# Rejilla de 0,1 µm para las diferencias: con ella GEOS usa el redondeo robusto y no puede fallar
# («TopologyException: Ring edge missing» con el GEOS 3.12 de la versión web, que además tumba Pyodide)
REJILLA = 1e-4

# Mínimos de JLC para 2 capas y 1 oz (pista / hueco / cobre al borde).
REGLAS = {
    'JLC estándar': {'pista_min': 0.127, 'hueco_min': 0.127, 'borde_min': 0.3},
    'JLC mínimo (0,09 mm)': {'pista_min': 0.09, 'hueco_min': 0.09, 'borde_min': 0.2},
    'Holgado (0,2 mm)': {'pista_min': 0.2, 'hueco_min': 0.2, 'borde_min': 0.5},
}
REGLAS_POR_DEFECTO = 'JLC estándar'


def comprobar(antena, nombre_reglas=REGLAS_POR_DEFECTO):
    """Devuelve una lista de (nivel, mensaje); nivel en {'ok', 'aviso', 'error'}."""
    r = REGLAS[nombre_reglas]
    res = []
    for capa in ('F.Cu', 'B.Cu'):
        cobre = antena.cobre(capa)
        if cobre is None or cobre.is_empty:
            continue
        nombre = 'cara superior' if capa == 'F.Cu' else 'cara inferior'
        # Partes más estrechas que la pista mínima: desaparecen al encoger y volver a engordar
        w = r['pista_min']
        abierto = cobre.buffer(-w/2*0.999, join_style='mitre').buffer(w/2*0.999, join_style='mitre')
        perdido = shapely.difference(cobre, abierto, grid_size=REJILLA).area
        if perdido > w*w*2:
            res.append(('error', f'{nombre}: hay cobre más estrecho que {w} mm ({perdido:.3f} mm²)'))
        # Huecos más estrechos que el mínimo: se cierran al engordar y volver a encoger
        s = r['hueco_min']
        cerrado = cobre.buffer(s/2*0.999, join_style='mitre').buffer(-s/2*0.999, join_style='mitre')
        relleno = shapely.difference(cerrado, cobre, grid_size=REJILLA).area
        if relleno > s*s*2:
            res.append(('error', f'{nombre}: hay huecos más estrechos que {s} mm ({relleno:.3f} mm²)'))
        # Distancia al borde de la placa
        d_borde = antena.contorno.boundary.distance(cobre)       # borde exterior y ventanas de aligerado
        if d_borde < r['borde_min'] - 1e-6 and capa == 'B.Cu':
            res.append(('aviso', f'{nombre}: cobre a {d_borde:.2f} mm del borde (mínimo {r["borde_min"]} mm)'))
    # Vueltas de la pista que se pisan (el área real es menor que largo × ancho)
    solape = antena.info.get('solape_pistas')
    if solape is not None and solape > 0.08:
        res.append(('error', f'Las vueltas de la pista se pisan ({100*solape:.0f} % del área): '
                             'la curva es demasiado densa para ese ancho; baja la iteración/orden, '
                             'estrecha la pista o agranda la antena'))
    # Piezas sueltas en la cara superior (directores de la Yagi son intencionados)
    piezas = len(poligonos(antena.cobre('F.Cu')))
    aj = antena.ajuste or {}
    esperadas = 1 + (1 if aj.get('cortes') else 0) + len(aj.get('islas_masa', [])) + \
        aj.get('tramos', 0)*(2 if antena.tipo == 'yagi_koch' else 1)
    if piezas > esperadas and not antena.tipo.startswith('yagi'):
        res.append(('aviso', f'La cara superior tiene {piezas} piezas de cobre separadas'))
    # Pista y hueco mínimos que usa realmente el diseño (informativo)
    p = antena.parametros
    if 'ancho_pista' in p and p['ancho_pista'] < r['pista_min']:
        res.append(('error', f'Ancho de pista {p["ancho_pista"]} mm < {r["pista_min"]} mm'))
    if not any(n == 'error' for n, _ in res):
        res.insert(0, ('ok', f'Cumple las reglas «{nombre_reglas}» (pista ≥ {r["pista_min"]} mm, hueco ≥ {r["hueco_min"]} mm)'))
    return res
