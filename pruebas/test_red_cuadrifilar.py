"""Red de alimentación de la hélice cuadrifilar: híbrido de 90° + red en L por dipolo (circuito puro, sin openEMS)."""

import math

import numpy as np

from antenas import red_cuadrifilar as red
from antenas import tipos, tridimensional

F0 = 1575.42e6
Z_DIPOLO = 15.05 + 5.23j          # de la simulación de dos puertos (D 32 mm, ¼ de vuelta)


def test_la_red_pasa_de_15_ohm_a_50_con_poca_pérdida():
    r = red.disenar_red(Z_DIPOLO, F0)
    assert r is not None and r['serie'] == ('L', 1.8) and r['derivacion'] == ('C', 3.0)
    sin = float(red.eficiencia_adaptacion(Z_DIPOLO))
    con = float(red.eficiencia_adaptacion(red.zin_red_l(Z_DIPOLO, F0, r))*red.eficiencia_red(Z_DIPOLO, F0, r))
    assert 0.65 < sin < 0.75 and 0.94 < con < 0.99 and con == float(r['eficiencia_total'])


def test_sin_pérdidas_el_resultado_es_el_de_la_teoría():
    r = red.disenar_red(Z_DIPOLO, F0, q_l=1e9, q_c=1e9)
    assert abs(red.eficiencia_red(Z_DIPOLO, F0, r, 1e9, 1e9) - 1.0) < 1e-6
    assert float(red.eficiencia_adaptacion(red.zin_red_l(Z_DIPOLO, F0, r, 1e9, 1e9))) > 0.999


def test_el_hibrido_con_ramas_iguales_no_desbalancea():
    r = red.disenar_red(Z_DIPOLO, F0)
    d = red.desbalance(Z_DIPOLO, Z_DIPOLO, F0, r, r)
    assert abs(d['delta_potencia_dB']) < 1e-9
    assert red.razon_axial_cenit_dB(0.0) < 0.01


def test_razon_axial_crece_con_el_desbalance_y_el_error_de_fase():
    assert 1.5 < red.razon_axial_cenit_dB(3.0) < 3.5          # 3 dB entre los dos dipolos ≈ 3 dB de razón axial
    assert red.razon_axial_cenit_dB(0.0, 10.0) > 0.5
    assert red.razon_axial_cenit_dB(1.0) < red.razon_axial_cenit_dB(3.0)


def test_el_tipo_lleva_los_valores_simulados_y_la_red():
    p = tipos.dimensionar('helice_cuadrifilar', F0, {})
    assert p['diametro'] == 32 and p['vueltas'] == 0.25 and p['sentido'] == -1
    assert abs(tipos.estimar_f('helice_cuadrifilar', p) - F0)/F0 < 0.03
    a = tipos.generar('helice_cuadrifilar', p)
    assert a.info['red_alimentacion'] == tridimensional.RED_QHA and len(a.info['avisos']) == 4


def test_con_otro_diametro_no_hay_red_calculada():
    p = dict(tipos.dimensionar('helice_cuadrifilar', F0, {}), diametro=14, vueltas=0.5)
    assert tridimensional.red_alimentacion_qha(p) is None


def test_perdidas_para_recepcion():
    r = red.disenar_red(Z_DIPOLO, F0)
    disipa = float(red.perdida_red_dB(Z_DIPOLO, F0, r))
    assert 0.1 < disipa < 0.3                                    # la red añade ≈ 0,2 dB de ruido con Q 40 y 150
    assert float(red.perdida_red_dB(Z_DIPOLO, F0, None)) == 0.0
    assert float(red.perdida_desadaptacion_dB(Z_DIPOLO, F0, None)) > 1.0       # sin red se pierde 1,5 dB de señal
    assert float(red.perdida_desadaptacion_dB(Z_DIPOLO, F0, r)) < 0.1


def test_la_carcasa_baja_la_resonancia_mas_cuanto_mas_cerca():
    f = tridimensional.factor_carcasa_qha
    assert f(0.2) < f(0.5) < f(1.0) < f(2.0) < f(4.0) < f(8.0) < 1.0
    assert abs(f(1.0) - 0.9365) < 1e-9 and f(0.0) == f(0.2) and f(100.0) == f(8.0)
    assert 0.9365 < f(1.5) < 0.9515                                # interpolado
