"""Operaciones booleanas de shapely robustas para la versión web (Pyodide).

Pyodide trae shapely 2.0 con GEOS 3.12, más antiguo que el de escritorio. Con él, uniones y diferencias de
geometrías delicadas (curvas de Koch engordadas, el Sierpinski, aperturas de morfología) lanzan a veces
«TopologyException» o «non-noded intersection», y en Pyodide esa excepción de C++ **tumba el intérprete**.

`activar()` hace que union/difference/intersection/symmetric_difference/union_all usen por defecto una rejilla
de 0,1 µm (`grid_size`): GEOS pasa entonces al redondeo robusto (snap rounding), que no puede fallar. Las
coordenadas se desplazan como mucho 0,05 µm, muy por debajo de la precisión con que se escribe la placa.
Solo se activa en el navegador (web_api); el escritorio sigue igual.
"""
import functools

import shapely

REJILLA = 1e-4          # mm
_OPERACIONES = ('union', 'difference', 'intersection', 'symmetric_difference', 'union_all', 'unary_union')


def _con_rejilla(f):
    @functools.wraps(f)
    def envuelta(*args, grid_size=None, **kw):
        return f(*args, grid_size=REJILLA if grid_size is None else grid_size, **kw)
    envuelta._robusta = True
    return envuelta


def activar():
    """Cambia las operaciones de shapely (módulo y métodos de las geometrías) para que usen la rejilla."""
    import shapely.set_operations as so
    for nombre in _OPERACIONES:
        for modulo in (shapely, so):
            f = getattr(modulo, nombre, None)
            if f is not None and not getattr(f, '_robusta', False):
                setattr(modulo, nombre, _con_rejilla(f))
