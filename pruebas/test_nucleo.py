"""Pruebas rápidas del núcleo (sin openEMS): `python -m pytest pruebas` desde la raíz del proyecto."""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antenas import ajuste, bucle, geometria, materiales, tipos  # noqa: E402

BANDAS = (868e6, 2441.75e6)


@pytest.mark.parametrize('n', [0, 1, 2, 3])
def test_longitud_koch(n):
    # cada iteración multiplica la longitud por 4/3
    assert geometria.longitud(geometria.koch(n)) == pytest.approx((4/3)**n, rel=1e-6)


@pytest.mark.parametrize('n', [0, 1, 2])
def test_area_sierpinski(n):
    # cada iteración deja 3/4 del área
    a0 = geometria.sierpinski(0, 10, 10).area
    assert geometria.sierpinski(n, 10, 10).area == pytest.approx(a0*0.75**n, rel=1e-3)


def test_ancho_microstrip_50_ohm():
    assert 2.9 <= materiales.ancho_microstrip(50, 4.5, 1.6) <= 3.1


@pytest.mark.parametrize('zl', [10 + 5j, 20 - 30j, 3 + 40j, 120 + 60j, 200 - 80j])
def test_redes_l_adaptan(zl):
    f = 868e6
    sols = ajuste.redes_l(zl, f)
    assert sols
    # los valores E24 redondean (y con R de pocos ohmios, mucho): la mejor solución debe quedar por debajo de -10 dB
    assert sols[0]['s11_dB'] < -10


@pytest.mark.parametrize('clave', sorted(tipos.CATALOGO))
@pytest.mark.parametrize('f_obj', BANDAS)
def test_dimensionar_estimar(clave, f_obj):
    p = tipos.dimensionar(clave, f_obj)
    if '_aviso' in p:
        pytest.skip('fuera de los límites del tipo a esta banda')
    p = {k: v for k, v in p.items() if not k.startswith('_')}
    f = tipos.estimar_f(clave, p)
    assert abs(f - f_obj)/f_obj <= 0.01


def test_bucle_estimar_f():
    p = tipos.CATALOGO['bucle'].defectos()
    f = bucle.estimar_f(p)
    assert 1e8 < f < 6e9
    # la fórmula sola y la calibrada difieren poco (el factor es ~1,03-1,05)
    assert abs(bucle.estimar_f(p, calibrada=False)/f - 1) < 0.15
    # más condensador -> frecuencia más baja
    assert bucle.estimar_f(dict(p, capacidad_pF=p['capacidad_pF']*2)) < f
