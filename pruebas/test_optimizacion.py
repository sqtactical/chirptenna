"""Optimización bayesiana (antenas/optimizacion.py): sin openEMS, solo numpy."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from antenas import optimizacion as op


def _bucle(f, d, n_total, semilla=1):
    n0 = max(4, 2*d)
    X = op.diseno_inicial(n0, d, semilla)
    y = np.array([f(u) for u in X])
    while len(X) < n_total:
        u = op.proponer(X, y, semilla)[0]
        X = np.vstack([X, u])
        y = np.append(y, f(u))
    return X, y


def test_espacio_codifica_y_decodifica():
    e = op.Espacio({'alto': ('x', (0.8, 1.2)), 'iteracion': ('v', [1, 2, 3])})
    assert e.dimension == 2
    c = e.decodificar([0.5, 0.99])
    assert c['alto'] == ('x', 1.0) and c['iteracion'] == ('v', 3)
    assert e.decodificar([0.0, 0.0]) == {'alto': ('x', 0.8), 'iteracion': ('v', 1)}
    # codificar es la inversa en continuos y cae en el centro de la casilla en discretos
    u = e.codificar({'alto': ('x', 1.1), 'iteracion': ('v', 2)})
    assert u[0] == pytest.approx(0.75) and u[1] == pytest.approx(0.5)
    assert e.decodificar(u) == {'alto': ('x', 1.1), 'iteracion': ('v', 2)}


def test_espacio_rechaza_limites_malos():
    with pytest.raises(ValueError):
        op.Espacio({'a': ('v', (2.0, 1.0))})
    with pytest.raises(ValueError):
        op.Espacio({'a': ('v', [3])})
    with pytest.raises(ValueError):
        op.Espacio({'a': ('z', (0, 1))})


def test_diseno_inicial_cubre_cada_eje():
    u = op.diseno_inicial(8, 3, semilla=5)
    assert u.shape == (8, 3) and u.min() >= 0 and u.max() < 1
    for j in range(3):
        assert sorted((u[:, j]*8).astype(int)) == list(range(8))        # un punto por franja


def test_encuentra_el_minimo_con_pocas_evaluaciones():
    f = lambda u: float((u[0] - 0.3)**2 + (u[1] - 0.7)**2)
    X, y = _bucle(f, 2, 18)
    assert y.min() < 0.01                       # una rejilla 5×5 (25 puntos) no pasaría de ~0,02
    # y mejora al azar con el mismo presupuesto
    azar = np.random.default_rng(0).random((18, 2))
    assert y.min() < min(f(u) for u in azar)


def test_funciona_con_una_funcion_con_ruido_de_banda_estrecha():
    # parecido a un S11 contra el largo: un valle estrecho, plano fuera de él
    f = lambda u: float(-12*np.exp(-((u[0] - 0.62)/0.05)**2) + 0.5*u[1])
    X, y = _bucle(f, 2, 24)
    assert y.min() < -9


def test_determinista_y_reanudable():
    f = lambda u: float(np.sin(5*u[0]) + (u[1] - 0.4)**2)
    a = _bucle(f, 2, 10, semilla=3)
    b = _bucle(f, 2, 10, semilla=3)
    assert np.allclose(a[0], b[0])
    # con otra semilla el recorrido cambia
    c = _bucle(f, 2, 10, semilla=4)
    assert not np.allclose(a[0], c[0])


def test_propuestas_no_repiten_puntos():
    f = lambda u: float(u[0]**2)
    X, y = _bucle(f, 1, 8)
    assert len({round(float(v), 4) for v in X[:, 0]}) == len(X)


def test_sin_informacion_propone_al_azar():
    X = np.array([[0.2, 0.2], [0.8, 0.8]])
    y = np.array([-5.0, -5.0])
    p = op.proponer(X, y, 1)
    assert p.shape[1] == 2 and len(p) > 0
