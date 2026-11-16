"""Método de momentos mínimo para hilos finos paralelos en el vacío (preselección rápida, tipo NEC2).

Idea tomada de antenna-forge: NEC2 halla el largo de un dipolo en 16 llamadas y diseña una Yagi en miles; aquí
la FDTD tarda de minutos a horas por punto. Este módulo resuelve la ecuación de Pocklington con base triangular
(corriente nula en los extremos) y colocación en los nodos para N hilos rectos **paralelos** entre sí (dipolos,
Yagi, colineal de dipolos separados): impedancia de entrada, corrientes, diagrama y directividad. Solo numpy;
no está en el núcleo de la web.

**Qué NO modela**: el dieléctrico (FR4), la pista de alimentación, la masa ni el cobre real. Da el tamaño
relativo de una Yagi o de una colineal en el aire (razones reflector/excitado, director/excitado, separaciones en λ),
que sirven para acotar el rango del barrido FDTD (`barrido.py --modo bayes`), no para sustituirlo. Para una antena
impresa hay que simular con openEMS.

Convenio: los hilos son paralelos al eje z; su posición en el plano (x, y) es la del hilo. Un dipolo de una Yagi
impresa (elementos en x, boom en y) se resuelve con los elementos a lo largo de z y el boom en y. Longitudes en mm.
"""
import math
from dataclasses import dataclass

import numpy as np

C0 = 299792458.0
ETA0 = 376.730313668

# Gauss-Legendre para la parte suave de cada mitad del triángulo; la parte singular 1/R se integra exacta
_T, _W = np.polynomial.legendre.leggauss(12)


@dataclass
class Hilo:
    """Hilo recto paralelo a z, en (x, y), de z0 a z1, con el radio dado (mm)."""
    x: float
    y: float
    z0: float
    z1: float
    radio: float = 0.5

    @property
    def largo(self):
        return self.z1 - self.z0


def _nodos(hilos, seg_por_lambda, lam):
    """Nodos interiores de cada hilo (n − 1 con n segmentos pares, así hay un nodo central). Listas por nodo."""
    X, Y, Z, D, A, W = [], [], [], [], [], []
    for i, h in enumerate(hilos):
        n = max(6, int(math.ceil(h.largo/(lam/seg_por_lambda))))
        n += n % 2
        d = h.largo/n
        for j in range(1, n):
            X.append(h.x)
            Y.append(h.y)
            Z.append(h.z0 + j*d)
            D.append(d)
            A.append(h.radio)
            W.append(i)
    return [np.array(v, dtype=float) for v in (X, Y, Z, D, A)] + [np.array(W)]


def _impedancias(X, Y, Z, D, A, W, k):
    """Matriz M[m, n] = ∫ T_m(z) (−E_z[T_n])(z) dz (Ω): Galerkin con triángulos (la colocación en puntos con
    triángulos no converge: Pocklington es una ecuación de segundo orden)."""
    M = 0
    for lado in (-1, 1):
        for t, w in zip(_T, _W):
            x = Z + lado*0.5*D + 0.5*D*t                    # punto de prueba en una mitad del triángulo m
            peso = w*0.5*D*(1 - np.abs(x - Z)/D)
            M = M + peso[:, None]*_campo_triangulo(X, Y, Z, D, A, W, k, x)
    return M


def _campo_triangulo(X, Y, Z, D, A, W, k, zobs):
    """Matriz F[m, n] = −E_z de un triángulo de corriente unidad en el nodo n, en el punto z = zobs[m] del hilo de m
    (V/mm por A, núcleo reducido).

    (k² + ∂²/∂z²) aplicado a un triángulo de nodo n da k²·∫T·G dz' + [G(z_n+Δ) − 2G(z_n) + G(z_n−Δ)]/Δ.
    """
    n = len(X)
    zm, zn, d = zobs[:, None], Z[None, :], D[None, :]
    mismo = (W[:, None] == W[None, :])
    rho2 = np.where(mismo, A[None, :]**2, (X[:, None] - X[None, :])**2 + (Y[:, None] - Y[None, :])**2)
    rho = np.sqrt(rho2)

    def G(z):
        R = np.sqrt(rho2 + (zm - z)**2)
        return np.exp(-1j*k*R)/R

    IG = np.zeros((n, n), dtype=complex)
    for lado in (-1, 1):                                    # mitad izquierda y derecha del triángulo
        centro = zn + lado*0.5*d
        semi = 0.5*d
        for t, w in zip(_T, _W):
            x = centro + semi*t
            R = np.sqrt(rho2 + (zm - x)**2)
            tri = 1 - np.abs(x - zn)/d
            IG += w*semi*tri*np.expm1(-1j*k*R)/R           # parte suave: T·(e^{-jkR} − 1)/R
        # parte singular T/R, exacta: T = α + βx en esta mitad
        alfa = 1 + lado*zn/d
        beta = -lado/d
        u_lo = (zn + (0 if lado == 1 else -1)*d) - zm
        u_hi = (zn + (1 if lado == 1 else 0)*d) - zm
        IG += ((alfa + beta*zm)*(np.arcsinh(u_hi/rho) - np.arcsinh(u_lo/rho))
               + beta*(np.sqrt(rho2 + u_hi**2) - np.sqrt(rho2 + u_lo**2)))
    termino = k**2*IG + (G(zn + d) - 2*G(zn) + G(zn - d))/d
    return 1j*ETA0/(4*math.pi*k)*termino


def resolver(hilos, f_Hz, excitado=0, seg_por_lambda=40, V=1.0):
    """Resuelve los hilos con un generador de V voltios en el nodo central del hilo `excitado`.

    Devuelve un dict: `Z` (impedancia de entrada, Ω), `corrientes` (A, por nodo), `segmentos` (x, y, z, paso en mm)
    y `k` (rad/mm).
    """
    lam = C0/f_Hz*1e3
    k = 2*math.pi/lam                                        # rad/mm
    X, Y, Z, D, A, W = _nodos(hilos, seg_por_lambda, lam)
    M = _impedancias(X, Y, Z, D, A, W, k)
    ids = np.where(W == excitado)[0]
    fuente = ids[len(ids)//2]
    b = np.zeros(len(X), dtype=complex)
    b[fuente] = V                                            # hueco de tensión (delta) en el nodo central: ∫T·Vδ = V
    I = np.linalg.solve(M, b)
    return {'Z': complex(V/I[fuente]), 'corrientes': I, 'segmentos': (X, Y, Z, D), 'k': k, 'hilo': W, 'fuente': int(fuente)}


def _campo(res, theta, phi):
    """|E_θ| relativo (sin constantes) para arrays de θ y φ (rad)."""
    X, Y, Z, D = res['segmentos']
    k, I = res['k'], res['corrientes']
    th, ph = np.asarray(theta, float)[..., None], np.asarray(phi, float)[..., None]
    fase = k*(X*np.sin(th)*np.cos(ph) + Y*np.sin(th)*np.sin(ph) + Z*np.cos(th))
    return np.abs(np.sin(th[..., 0])*(I*D*np.exp(1j*fase)).sum(axis=-1))


def _esfera(res, n_theta=91, n_phi=72):
    th = np.linspace(0, math.pi, n_theta)
    ph = np.linspace(0, 2*math.pi, n_phi, endpoint=False)
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    U = _campo(res, TH, PH)**2
    pot = (U*np.sin(TH)).sum()*(th[1] - th[0])*(ph[1] - ph[0])
    return th, ph, U, pot


def directividad(res, n_theta=91, n_phi=72):
    """Directividad máxima (dBi) y su dirección (θ, φ en grados) integrando el diagrama sobre la esfera."""
    th, ph, U, pot = _esfera(res, n_theta, n_phi)
    i = np.unravel_index(np.argmax(U), U.shape)
    return 10*math.log10(4*math.pi*U[i]/pot), math.degrees(th[i[0]]), math.degrees(ph[i[1]])


def directividad_en(res, theta_grados, phi_grados):
    """Directividad (dBi) en una dirección dada (θ desde el eje z, φ desde x)."""
    _, _, _, pot = _esfera(res)
    u = _campo(res, np.array([math.radians(theta_grados)]), np.array([math.radians(phi_grados)]))[0]**2
    return 10*math.log10(max(4*math.pi*u/pot, 1e-12))


def reflexion(Z, z0=50.0):
    """(|Γ|, S11 en dB) de la impedancia Z frente a z0."""
    g = abs((Z - z0)/(Z + z0))
    return g, 20*math.log10(max(g, 1e-9))


# ---- diseños de referencia ----

def dipolo(largo_mm, radio_mm=0.5):
    """Un dipolo vertical centrado en el origen."""
    return [Hilo(0.0, 0.0, -largo_mm/2, largo_mm/2, radio_mm)]


def yagi(largos_mm, posiciones_mm, radio_mm=0.5):
    """Yagi de elementos paralelos a z, en fila a lo largo de y: reflector, excitado, directores… (el excitado es
    el índice 1). El haz sale hacia +y (φ = 90°)."""
    return [Hilo(0.0, y, -l/2, l/2, radio_mm) for l, y in zip(largos_mm, posiciones_mm)]


def largo_dipolo_resonante(f_Hz, radio_mm=0.5, seg_por_lambda=40):
    """Largo (mm) al que un dipolo tiene reactancia nula, por bisección (λ/2 con hilo fino da ~0,48 λ)."""
    lam = C0/f_Hz*1e3
    lo, hi = 0.40*lam, 0.52*lam
    for _ in range(30):
        mid = 0.5*(lo + hi)
        x = resolver(dipolo(mid, radio_mm), f_Hz, seg_por_lambda=seg_por_lambda)['Z'].imag
        if x > 0:
            hi = mid
        else:
            lo = mid
    return 0.5*(lo + hi)
