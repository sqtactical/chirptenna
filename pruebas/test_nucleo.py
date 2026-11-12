"""Pruebas rápidas del núcleo (sin openEMS): `python -m pytest pruebas` desde la raíz del proyecto."""
import math
import os
import sys

import pytest
from shapely.geometry import box

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


@pytest.mark.parametrize('clave', ['ifa', 'monopolo_recto', 'monopolo_meandro', 'monopolo_koch'])
@pytest.mark.parametrize('posicion', [0, 1, 2])
def test_antena_integrada(clave, posicion):
    # F3.1: placa de 30 × 50 mm a 2,4 GHz; ni masa ni cobre de ninguna capa en la zona de antena, salvo la propia antena
    p = tipos.dimensionar(clave, 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50, 'posicion': posicion})
    a = tipos.generar(clave, p)
    x0, y0, x1, y1 = a.contorno.bounds
    assert (x1 - x0, y1 - y0) == pytest.approx((30, 50), abs=1e-6)
    assert a.info['integrada'] is True
    assert a.cobre('B.Cu').intersection(a.zona_libre).area == pytest.approx(0, abs=1e-6)
    assert a.contorno.contains(a.cobre('F.Cu')) and a.contorno.contains(a.cobre('B.Cu'))
    # el radiador cae en la zona (salvo el arranque de la pista y el cortocircuito de la IFA, que entran en la masa)
    zx0, zy0, zx1, zy1 = a.zona_libre.bounds
    assert a.radiador.intersection(box(zx0 - 1, zy0, zx1 + 1, zy1 + 1)).within(a.zona_libre.buffer(1e-6))


def test_integrada_no_cabe():
    # la IFA de 868 MHz no cabe en 40 mm de ancho: error claro con lo que falta
    p = tipos.dimensionar('ifa', 868e6, {'integrada': 1, 'placa_x': 40, 'placa_y': 80})
    with pytest.raises(ValueError, match='faltan'):
        tipos.generar('ifa', p)


def test_bucle_estimar_f():
    p = tipos.CATALOGO['bucle'].defectos()
    f = bucle.estimar_f(p)
    assert 1e8 < f < 6e9
    # la fórmula sola y la calibrada difieren poco (el factor es ~1,03-1,05)
    assert abs(bucle.estimar_f(p, calibrada=False)/f - 1) < 0.15
    # más condensador -> frecuencia más baja
    assert bucle.estimar_f(dict(p, capacidad_pF=p['capacidad_pF']*2)) < f
