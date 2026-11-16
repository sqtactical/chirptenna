"""Comprobaciones «de verdad»: el generador frente a la teoría de libro y a las simulaciones ya validadas.

Idea tomada de antenna-forge (dipolo contra el libro, parche contra el modelo de cavidad). No simulan: comparan
las fórmulas y la calibración del generador con una implementación independiente (aquí abajo, escrita a partir de
las referencias, sin importar nada de `antenas` para el cálculo del libro) y con los números que dieron las
simulaciones de openEMS (lecciones 5, 41 y 69 de CLAUDE.md). Si una de estas falla tras un cambio, el tamaño con el
que arranca un diseño ha dejado de coincidir con la física: no se arregla subiendo la tolerancia.

Las simulaciones reales contra el libro están en `herramientas/verdad.py` (necesitan openEMS).
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from antenas import materiales, tipos

C0 = 299792458.0
ER, H = 4.5, 1.6                       # FR4 de JLC (calculadora de impedancias de 2 capas)


# ---- el libro (Hammerstad-Jensen, Balanis), implementado aparte ----

def z0_microstrip(w, h, er):
    """Impedancia característica de una microstrip (Hammerstad-Jensen, sin grosor del cobre)."""
    u = w/h
    if u <= 1:
        ee = (er + 1)/2 + (er - 1)/2*((1 + 12/u)**-0.5 + 0.04*(1 - u)**2)
        return 60/math.sqrt(ee)*math.log(8/u + u/4)
    ee = (er + 1)/2 + (er - 1)/2*(1 + 12/u)**-0.5
    return 120*math.pi/(math.sqrt(ee)*(u + 1.393 + 0.667*math.log(u + 1.444)))


def f_parche_cavidad(largo, ancho, h, er):
    """Parche rectangular, modelo de la cavidad con ΔL de Hammerstad (Balanis 14.2)."""
    ee = (er + 1)/2 + (er - 1)/2*(1 + 12*h/ancho)**-0.5
    dl = 0.412*h*(ee + 0.3)*(ancho/h + 0.264)/((ee - 0.258)*(ancho/h + 0.8))
    return C0/(2*(largo + 2*dl)*1e-3*math.sqrt(ee))


# ---- microstrip ----

@pytest.mark.parametrize('z0', [50, 75, 100])
def test_ancho_microstrip_da_la_impedancia_pedida(z0):
    w = materiales.ancho_microstrip(z0, ER, H)
    assert z0_microstrip(w, H, ER) == pytest.approx(z0, rel=0.02)


def test_linea_de_50_ohm_en_fr4_de_1_6_mm_mide_unos_3_mm():
    # la calculadora de JLC da ~3,0 mm para 50 Ω con εr 4,5; el cupón del proyecto usa 3,01 mm
    assert materiales.ancho_microstrip(50, ER, H) == pytest.approx(3.0, abs=0.15)


def test_permitividad_efectiva_entre_aire_y_sustrato():
    for w in (0.5, 1.6, 3.0, 8.0):
        ee = materiales.eps_eff_microstrip(ER, H, w)
        assert 1 < ee < ER
    # más ancha, más campo en el dieléctrico
    assert materiales.eps_eff_microstrip(ER, H, 8.0) > materiales.eps_eff_microstrip(ER, H, 0.5)
    # valor de libro: w/h = 1,875 en εr 4,5 → ~3,4
    assert materiales.eps_eff_microstrip(ER, H, 3.0) == pytest.approx(3.4, abs=0.1)


# ---- los tamaños con los que arranca cada tipo ----

@pytest.mark.parametrize('f_MHz', [868.0, 2441.75])
def test_dipolo_mide_entre_0_35_y_0_5_lambda(f_MHz):
    # dipolo de hilo en el aire: 0,47 λ (lección 5: 0,456–0,465 simulado); impreso en FR4 y con pista ancha, menos
    p = tipos.dimensionar('dipolo', f_MHz*1e6)
    total = 2*p['largo_brazo'] + p['hueco']
    lam = C0/(f_MHz*1e6)*1e3
    assert 0.35 < total/lam < 0.50


@pytest.mark.parametrize('f_MHz', [868.0, 2441.75])
def test_monopolo_recto_mide_entre_0_17_y_0_25_lambda(f_MHz):
    # λ/4 teórico = 0,25 λ; el monopolo de 2,45 GHz ajustado por simulación midió 23,63 mm (0,193 λ, lección 5)
    p = tipos.dimensionar('monopolo_recto', f_MHz*1e6)
    lam = C0/(f_MHz*1e6)*1e3
    assert 0.17 < p['alto']/lam < 0.25


def test_monopolo_de_2_45_ghz_ajustado_coincide_con_la_simulacion():
    # lección 5: la tira de 23,63 mm resonaba a 2,45 GHz con pista de 1 mm; la estimación calibrada debe dar lo mismo ±3 %
    f = tipos.estimar_f('monopolo_recto', {'alto': 23.63, 'ancho_pista': 1.0})
    assert f/1e6 == pytest.approx(2450, rel=0.03)


@pytest.mark.parametrize('f_MHz', [868.0, 2441.75])
def test_parche_rectangular_contra_el_modelo_de_cavidad(f_MHz):
    p = tipos.dimensionar('parche_rectangular', f_MHz*1e6)
    f_libro = f_parche_cavidad(p['largo'], p['ancho'], H, ER)
    # el libro y el parche calibrado por simulación difieren un par de %: 3,1 % en antenna-forge, ≤ 5 % aquí
    assert f_libro/1e6 == pytest.approx(f_MHz, rel=0.05)


@pytest.mark.parametrize('clave', ['monopolo_recto', 'dipolo', 'parche_rectangular', 'jpole'])
@pytest.mark.parametrize('f_MHz', [868.0, 2441.75])
def test_dimensionar_y_estimar_f_son_coherentes(f_MHz, clave):
    # lección 41: el tamaño inicial queda a 0–3 % de la frecuencia pedida
    p = tipos.dimensionar(clave, f_MHz*1e6)
    p.pop('_aviso', None)
    assert tipos.estimar_f(clave, p)/1e6 == pytest.approx(f_MHz, rel=0.03)


def test_la_calibracion_corrige_en_el_sentido_y_tamano_conocidos():
    # lección 41: la fórmula sola sale ~2–5 % alta en monopolos y dipolo (sin calibrar queda por encima de la frecuencia pedida) y
    # ~5 % alta en el parche; la calibración la baja. Nunca debe pasar del 12 %.
    for clave in ('monopolo_recto', 'dipolo', 'parche_rectangular'):
        for f_MHz in (868.0, 2441.75):
            p = tipos.dimensionar(clave, f_MHz*1e6)
            p.pop('_aviso', None)
            cal = tipos.estimar_f(clave, p)
            sin = tipos.estimar_f(clave, p, calibrada=False)
            assert abs(sin/cal - 1) < 0.12, (clave, f_MHz, sin/cal)


def test_escalado_con_lambda():
    # el mismo tipo a la mitad de frecuencia mide entre 1,6 y 2,1 veces más (λ ×2, algo menos por el FR4)
    a = tipos.dimensionar('monopolo_recto', 2441.75e6)['alto']
    b = tipos.dimensionar('monopolo_recto', 1220.875e6)['alto']
    assert 1.8 < b/a < 2.2
