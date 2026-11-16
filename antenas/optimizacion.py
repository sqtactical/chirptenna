"""Optimización bayesiana para los barridos de simulación (idea tomada de antenna-forge, solo con numpy).

Una simulación FDTD cuesta de minutos a horas: una rejilla de N valores por parámetro gasta N^d simulaciones.
Aquí se ajusta un proceso gaussiano (núcleo RBF isótropo, escala elegida por máxima verosimilitud) a lo ya
simulado y se propone el punto de mayor mejora esperada (EI). No hay dependencias nuevas (ni scipy), y la
versión web no la usa: no está en `construir_web.NUCLEO`.

Todo es determinista (la semilla fija el diseño inicial y las propuestas dependen solo del historial), de modo
que un barrido cortado y repetido recorre los mismos puntos y recupera los ya simulados.

Uso típico (lo hace `herramientas/barrido.py --modo bayes`):

    esp = Espacio({'alto': ('x', 0.8, 1.2), 'iteracion': ('v', [1, 2, 3])})
    inicio = [esp.decodificar(u) for u in diseno_inicial(4, esp.dimension, semilla=1)]
    ...                                   # simular, anotar el objetivo y de cada punto
    u = proponer(X, y, semilla=1)[0]      # siguiente punto, en [0, 1]^d
    esp.decodificar(u)
"""
import math

import numpy as np


class Espacio:
    """Espacio de búsqueda en el cubo unidad.

    `dims`: {nombre: (clase, límites)} con clase 'v' (valor absoluto) o 'x' (factor sobre el diseño base).
    Los límites son (mín, máx) para un parámetro continuo o una lista de valores para uno discreto
    (iteración, opciones…): ahí el cubo se reparte por igual entre los valores.
    """

    def __init__(self, dims):
        self.nombres = list(dims)
        self.dims = {}
        for k, (clase, lim) in dims.items():
            if clase not in ('v', 'x'):
                raise ValueError(f'«{k}»: la clase debe ser v o x, no {clase!r}')
            if isinstance(lim, (list, tuple)) and len(lim) == 2 and not isinstance(lim, list):
                lo, hi = float(lim[0]), float(lim[1])
                if not hi > lo:
                    raise ValueError(f'«{k}»: el máximo debe superar al mínimo')
                self.dims[k] = (clase, lo, hi, None)
            else:
                vals = sorted(set(lim))
                if len(vals) < 2:
                    raise ValueError(f'«{k}»: hacen falta al menos dos valores distintos')
                self.dims[k] = (clase, vals[0], vals[-1], vals)

    @property
    def dimension(self):
        return len(self.nombres)

    def decodificar(self, u):
        """Punto del cubo unidad → {nombre: (clase, valor)}."""
        u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0)
        sal = {}
        for ui, k in zip(u, self.nombres):
            clase, lo, hi, vals = self.dims[k]
            if vals is None:
                sal[k] = (clase, round(lo + ui*(hi - lo), 4))
            else:
                i = min(int(ui*len(vals)), len(vals) - 1)
                sal[k] = (clase, vals[i])
        return sal

    def codificar(self, combo):
        """{nombre: (clase, valor)} → punto del cubo unidad (centro de la casilla en los discretos)."""
        u = []
        for k in self.nombres:
            clase, lo, hi, vals = self.dims[k]
            v = combo[k][1]
            if vals is None:
                u.append((v - lo)/(hi - lo))
            else:
                i = min(range(len(vals)), key=lambda j: abs(vals[j] - v))
                u.append((i + 0.5)/len(vals))
        return np.array(u)


def diseno_inicial(n, d, semilla=0):
    """Hipercubo latino de n puntos en d dimensiones (cada eje cubierto de forma uniforme)."""
    rng = np.random.default_rng(semilla)
    u = np.empty((n, d))
    for j in range(d):
        u[:, j] = (rng.permutation(n) + rng.random(n))/n
    return u


def _nucleo(a, b, escala):
    d2 = ((a[:, None, :] - b[None, :, :])**2).sum(axis=2)
    return np.exp(-0.5*d2/escala**2)


def _ajustar(X, z):
    """Elige la escala del núcleo por máxima verosimilitud marginal. Devuelve (escala, L, alfa)."""
    mejor = None
    for escala in (0.1, 0.15, 0.2, 0.3, 0.45, 0.7, 1.0, 1.5):
        K = _nucleo(X, X, escala) + 1e-6*np.eye(len(X))
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            continue
        alfa = np.linalg.solve(L.T, np.linalg.solve(L, z))
        ll = -0.5*float(z @ alfa) - float(np.log(np.diag(L)).sum())
        if mejor is None or ll > mejor[0]:
            mejor = (ll, escala, L, alfa)
    if mejor is None:
        raise np.linalg.LinAlgError('no se pudo ajustar el proceso gaussiano')
    return mejor[1:]


_erf = np.vectorize(math.erf)


def mejora_esperada(X, y, candidatos, xi=0.01):
    """EI (para minimizar `y`) en cada candidato, con X en el cubo unidad."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    media, desv = float(y.mean()), float(y.std()) or 1.0
    z = (y - media)/desv
    escala, L, alfa = _ajustar(X, z)
    ks = _nucleo(candidatos, X, escala)
    mu = ks @ alfa
    v = np.linalg.solve(L, ks.T)
    var = np.maximum(1.0 - (v**2).sum(axis=0), 1e-12)
    sd = np.sqrt(var)
    mejor = float(z.min())
    imp = mejor - mu - xi
    t = imp/sd
    cdf = 0.5*(1 + _erf(t/math.sqrt(2)))
    pdf = np.exp(-0.5*t**2)/math.sqrt(2*math.pi)
    return imp*cdf + sd*pdf


def proponer(X, y, semilla=0, n_cand=3000, cuantos=60, xi=0.01):
    """Puntos candidatos del cubo unidad ordenados de mayor a menor mejora esperada (los `cuantos` primeros).

    El primero es la propuesta; los demás sirven de reserva si el primero cae en un valor discreto que ya se
    simuló. Se descartan los que quedan a < 1e-3 de un punto ya evaluado.
    """
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    d = X.shape[1]
    rng = np.random.default_rng(1000003*semilla + len(X))
    cand = rng.random((n_cand, d))
    i_mejor = int(np.argmin(y))
    local = np.clip(X[i_mejor] + rng.normal(0, 0.06, (n_cand//3, d)), 0, 1)       # exploración alrededor del mejor
    cand = np.vstack([cand, local])
    lejos = (np.sqrt(((cand[:, None, :] - X[None, :, :])**2).sum(axis=2)).min(axis=1) > 1e-3)
    cand = cand[lejos]
    if len(cand) == 0:
        return rng.random((1, d))
    if len(X) < 2 or float(np.ptp(y)) == 0.0:
        return cand[:cuantos]                       # sin información: al azar
    ei = mejora_esperada(X, y, cand, xi)
    orden = np.argsort(-ei)[:cuantos]
    return cand[orden]
