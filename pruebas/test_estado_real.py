"""`docs/ESTADO_REAL.md` debe coincidir con lo que genera `herramientas/estado_real.py` (si no, se olvidó regenerarlo)."""
import importlib.util
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


def _generador():
    espec = importlib.util.spec_from_file_location('estado_real', os.path.join(RAIZ, 'herramientas', 'estado_real.py'))
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    return m


def test_estado_real_esta_al_dia():
    m = _generador()
    esperado = m.generar()
    real = io.open(m.RUTA, encoding='utf-8', newline='').read().replace('\r\n', '\n')
    assert real == esperado, 'docs/ESTADO_REAL.md desfasado: ejecuta `python herramientas/estado_real.py`'


def test_todos_los_tipos_tienen_estado():
    from antenas import problemas, tipos
    assert [c for c in tipos.CATALOGO if c not in problemas.ESTADO] == []
    assert all(est in ('validada', 'pendiente', 'no_funciona') for est, _ in problemas.ESTADO.values())
