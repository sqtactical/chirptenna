"""Método de momentos de hilos (antenas/hilos.py) frente a los valores de libro (Balanis, Kraus)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from antenas import hilos

F = 300e6
LAM = hilos.C0/F*1e3                          # 999,3 mm
A = 0.002*LAM                                 # radio de 0,002 λ


def test_dipolo_de_media_onda_contra_el_libro():
    r = hilos.resolver(hilos.dipolo(0.5*LAM, A), F)
    z = r['Z']
    assert 70 < z.real < 95                    # 73 Ω de la teoría de hilo infinitamente fino; sube con el radio
    assert 20 < z.imag < 55                    # +42,5 Ω en el límite fino
    assert hilos.directividad(r)[0] == pytest.approx(2.15, abs=0.12)
    assert hilos.directividad(r)[1] == pytest.approx(90.0, abs=2)       # máximo en el plano perpendicular al hilo


def test_resonancia_un_poco_por_debajo_de_media_onda():
    L = hilos.largo_dipolo_resonante(F, A)
    assert 0.46 < L/LAM < 0.49                 # 0,47–0,48 λ para hilos finos (Kraus)
    z = hilos.resolver(hilos.dipolo(L, A), F)['Z']
    assert abs(z.imag) < 1.0 and 65 < z.real < 85


def test_converge_al_refinar_el_mallado():
    z40 = hilos.resolver(hilos.dipolo(0.5*LAM, A), F, seg_por_lambda=40)['Z']
    z80 = hilos.resolver(hilos.dipolo(0.5*LAM, A), F, seg_por_lambda=80)['Z']
    assert abs(z40 - z80)/abs(z80) < 0.04


def test_dipolo_corto_es_capacitivo_y_largo_inductivo():
    assert hilos.resolver(hilos.dipolo(0.40*LAM, A), F)['Z'].imag < -20
    assert hilos.resolver(hilos.dipolo(0.55*LAM, A), F)['Z'].imag > 80


def test_dipolo_corto_tiene_poca_resistencia():
    # l = λ/10: R = 20 π² (l/λ)² = 1,97 Ω en el modelo de corriente triangular
    z = hilos.resolver(hilos.dipolo(0.1*LAM, A), F)['Z']
    assert 1.0 < z.real < 3.5


def test_directividad_de_un_dipolo_largo_sube_de_2_15_a_unos_5_dbi_en_1_5_lambda():
    r = hilos.resolver(hilos.dipolo(1.5*LAM, A), F)
    assert 3.0 < hilos.directividad(r)[0] < 4.2          # lóbulos laterales: unos 3,5 dBi


def test_yagi_de_tres_elementos_da_ganancia_y_va_hacia_delante():
    # Balanis (Yagi de 3 elementos, ~0,25 λ entre ellos; reflector 0,482 λ, excitado 0,473 λ, director 0,442 λ)
    largos = [0.482*LAM, 0.473*LAM, 0.442*LAM]
    r = hilos.resolver(hilos.yagi(largos, [-0.25*LAM, 0.0, 0.25*LAM], A), F, excitado=1)
    g_ad = hilos.directividad_en(r, 90.0, 90.0)
    g_at = hilos.directividad_en(r, 90.0, 270.0)
    assert 7.0 < g_ad < 11.0                              # ~8–9 dBi
    assert g_ad - g_at > 8.0                               # el reflector manda hacia atrás


def test_yagi_sin_reflector_ni_director_es_un_dipolo():
    r1 = hilos.resolver(hilos.yagi([0.47*LAM], [0.0], A), F, excitado=0)
    r2 = hilos.resolver(hilos.dipolo(0.47*LAM, A), F)
    assert r1['Z'] == pytest.approx(r2['Z'])


def test_reciprocidad_de_los_hilos_acoplados():
    # dos dipolos separados λ/2: la matriz de impedancias es simétrica (el medio es recíproco)
    h = hilos.yagi([0.47*LAM, 0.47*LAM], [0.0, 0.5*LAM], A)
    M = hilos._impedancias(*hilos._nodos(h, 40, LAM), 2*3.141592653589793/LAM)
    assert abs(M - M.T).max()/abs(M).max() < 2e-3


def test_reflexion():
    g, s11 = hilos.reflexion(50 + 0j)
    assert g == pytest.approx(0) and s11 < -150
    g, s11 = hilos.reflexion(100 + 0j)
    assert g == pytest.approx(1/3) and s11 == pytest.approx(-9.54, abs=0.01)
