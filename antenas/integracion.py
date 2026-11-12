"""Antena integrada en la placa de un producto (F3.1).

Hasta ahora la placa generada era solo antena: un plano de masa justo y la antena encima. Aquí la antena pasa a ser
**una esquina de la placa anfitriona**: la placa tiene un tamaño dado, la masa ocupa todo menos la **zona de antena**
(un rectángulo en el borde superior, sin cobre en ninguna capa salvo la propia antena) y el conector sigue en el borde
opuesto, para poder medir el prototipo.

No hay un generador nuevo por tipo: `tipos` genera el monopolo de siempre y le pide a este módulo la forma de la placa
y de la masa. Coordenadas en mm, con la alimentación en x = 0 y el borde inferior de la placa en y = 0.
"""
from shapely.geometry import box

from .tipos_base import Parametro

BORDE_COBRE = 0.5            # retranqueo del cobre respecto al borde de la placa [mm] (el mismo que `tipos.BORDE_COBRE`)
TIPOS = ('monopolo_recto', 'monopolo_meandro', 'monopolo_koch', 'ifa')   # los que tienen sentido en una esquina de placa
POSICIONES = {0: 'Esquina superior izquierda', 1: 'Esquina superior derecha', 2: 'Centrada en el borde superior'}

PARAMETROS = [
    Parametro('integrada', 'Antena integrada en una placa', 0, 0, 1, 1, True,
              opciones={0: 'No: placa de prueba, solo la antena', 1: 'Sí: la antena es una esquina de la placa del producto'},
              ayuda='Sí: la placa tiene el tamaño de tu producto, la masa ocupa todo menos la zona de antena y el '
                    'conector queda en el borde opuesto'),
    Parametro('placa_x', 'Ancho de la placa anfitriona [mm]', 40, 10, 400, 1),
    Parametro('placa_y', 'Alto de la placa anfitriona [mm]', 60, 15, 400, 1),
    Parametro('posicion', 'Posición de la antena', 0, 0, 2, 1, True, opciones=POSICIONES),
    Parametro('zona_x', 'Ancho de la zona de antena [mm] (0 = lo que ocupa la antena)', 0, 0, 400, 0.5),
    Parametro('zona_y', 'Alto de la zona de antena [mm] (0 = lo que ocupa la antena)', 0, 0, 400, 0.5),
    Parametro('margen_zona', 'Cobre retirado alrededor del radiador [mm]', 2.0, 0.5, 20, 0.5),
]
NOMBRES = {q.nombre for q in PARAMETROS}
SOLO_INTEGRADA = NOMBRES - {'integrada'}
# Con la antena integrada la placa y la masa las fija la placa anfitriona: estas medidas no se usan
SOBRAN_INTEGRADA = {'masa', 'ancho_placa', 'largo_masa', 'margen_masa', 'contorno', 'margen_borde'}


def activa(p, clave=None):
    """True si el diseño es de una antena integrada (y el tipo lo admite, si se da)."""
    return int(p.get('integrada', 0) or 0) == 1 and (clave is None or clave in TIPOS)


def importada(p):
    """Placa importada de KiCad guardada en los parámetros (`importar_kicad.a_dato`), o None."""
    d = p.get('placa_importada')
    return d if isinstance(d, dict) and d.get('contorno') else None


def placa(p):
    """(ancho, alto) de la placa anfitriona: los de la placa importada si la hay, si no `placa_x` y `placa_y`."""
    d = importada(p)
    return (float(d['ancho']), float(d['alto'])) if d else (p['placa_x'], p['placa_y'])


def alto_zona(p, rad_arriba):
    """Alto de la zona de antena. rad_arriba: lo que sube el radiador sobre el borde de la masa (sin margen)."""
    return max(float(p.get('zona_y', 0) or 0), rad_arriba + p['margen_zona'])


def largo_masa(p, rad_arriba):
    """Largo de la masa bajo la zona de antena [mm] (puede salir ≤ 0 si la zona no cabe: quien genera lo comprueba)."""
    return placa(p)[1] - alto_zona(p, rad_arriba)


def geometria(p, radiador, lg, semiancho_min):
    """Contorno, masa y zona libre de la placa anfitriona. radiador: polígono ya puesto sobre la masa (y ≥ lg).

    semiancho_min: lo que necesita el conector a cada lado de la alimentación (x = 0). Devuelve un dict con
    `contorno`, `masa`, `zona`, `gx0`, `gx1`, `alto_placa`. Lanza ValueError con lo que falta si algo no cabe.
    """
    from .i18n import tr
    minx, _, maxx, maxy = radiador.bounds
    m = p['margen_zona']
    zy = max(float(p.get('zona_y', 0) or 0), maxy - lg + m)
    ancho, alto = placa(p)[0], lg + zy
    zx_pedido = float(p.get('zona_x', 0) or 0)
    # el conector está en x = 0, en el borde inferior: necesita masa a los dos lados
    necesita = semiancho_min + BORDE_COBRE
    pos = int(p.get('posicion', 0))
    if pos == 0:
        gx0 = min(minx - m, -necesita)             # el radiador, a `m` de la esquina; si el conector no cabe, se corre la esquina
        gx1 = gx0 + ancho
        zx0, zx1 = gx0, gx0 + max(zx_pedido, maxx + m - gx0)
    elif pos == 1:
        gx1 = max(maxx + m, necesita)
        gx0 = gx1 - ancho
        zx0, zx1 = gx1 - max(zx_pedido, gx1 - (minx - m)), gx1
    else:
        c = (minx + maxx)/2
        gx0, gx1 = c - ancho/2, c + ancho/2
        zx = max(zx_pedido, (maxx - minx) + 2*m)
        zx0, zx1 = c - zx/2, c + zx/2
    zx = zx1 - zx0
    if zx > ancho + 1e-9:
        raise ValueError(tr('La zona de antena mide {0:.1f} mm de ancho y la placa solo {1:.1f}: faltan {2:.1f} mm.',
                            zx, ancho, zx - ancho))
    if -gx0 < necesita - 1e-9 or gx1 < necesita - 1e-9:
        falta = necesita - min(-gx0, gx1)
        raise ValueError(tr('La alimentación queda a {0:.1f} mm de un lado de la placa y el conector necesita {1:.1f} mm: '
                            'faltan {2:.1f} mm de ancho de placa (o cambia la posición de la antena).',
                            min(-gx0, gx1), necesita, falta))
    contorno = box(gx0, 0, gx1, alto)
    zona_caja = box(zx0, lg, zx1, alto)
    masa = (box(gx0, 0, gx1, alto).difference(zona_caja)
            .intersection(contorno.buffer(-BORDE_COBRE, join_style='mitre')))
    extra = {}
    d = importada(p)
    if d:
        from . import importar_kicad as ik
        from shapely import affinity
        cont_imp, cobre_imp = ik.desde_dato(d)
        mover = (gx0, 0)
        contorno = affinity.translate(cont_imp, *mover)
        cobre_imp = affinity.translate(cobre_imp, *mover)
        zona = zona_caja.intersection(contorno)
        if not cobre_imp.is_empty:
            en_zona = cobre_imp.intersection(zona_caja).area
            if en_zona > 0.5:
                extra['cobre_en_zona_mm2'] = round(en_zona, 1)
            # el cobre de la placa es la masa; junto al conector se asegura un trozo de masa para soldarlo
            base = ik.masa_desde_cobre(cobre_imp, contorno).difference(zona_caja)
            conector_masa = box(-necesita, 0, necesita, 8).intersection(contorno)
            masa = base.union(conector_masa).intersection(contorno.buffer(-BORDE_COBRE, join_style='mitre')) \
                .difference(zona_caja)
        else:
            masa = contorno.buffer(-BORDE_COBRE, join_style='mitre').difference(zona_caja)
        return {'contorno': contorno, 'masa': masa, 'zona': zona, 'gx0': gx0, 'gx1': gx1, 'alto_placa': alto,
                'zona_mm': (round(zx, 2), round(zy, 2)), **extra}
    return {'contorno': contorno, 'masa': masa, 'zona': zona_caja.intersection(contorno),
            'gx0': gx0, 'gx1': gx1, 'alto_placa': alto, 'zona_mm': (round(zx, 2), round(zy, 2))}
