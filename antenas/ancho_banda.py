"""Estimación orientativa del ancho de banda a −10 dB (±50 %; la buena sale simulando).

- Parches: Jackson-Alexopoulos (radiación) más las pérdidas del dieléctrico:
  1/Q = 1/Q_rad + tanδ, y FBW(−10 dB) ≈ 0,667/Q.
- Monopolos y Yagi: límite de Chu para la esfera que encierra la antena (en los monopolos,
  radiador + masa, porque la masa también radia), multiplicado por un factor de cada forma.
  El factor del monopolo recto (2,8 con pista de 2 mm) sale de la Fase 0: banda simulada
  2,02–3,00 GHz con placa de 40 × 69 mm. Las pistas finas estrechan la banda.
"""
import math

from .materiales import lambda0_mm

S_10DB = 0.667          # (VSWR−1)/√VSWR para |S11| = −10 dB (VSWR 1,925)

FACTOR_Q = {'monopolo_recto': 2.8, 'monopolo_meandro': 3.5, 'monopolo_koch': 3.0,
            'monopolo_hilbert': 4.0, 'monopolo_sierpinski': 2.2, 'yagi_koch': 1.6,
            'yagi_boom': 1.6,
            # panel: el reflector a ~λ/4 y los λ/4 de la red estrechan la banda (~10–15 %)
            'panel_dipolos': 4.0,
            # J-pole: el adaptador λ/4 almacena energía y estrecha la banda (~5–10 %)
            'jpole': 8.0, 'jpole_koch': 10.0}


def q_chu(ka):
    return 1/ka**3 + 1/ka


def _factor_pista(w):
    """Corrección por el ancho de pista (referencia: 2 mm)."""
    return max(0.6, 1 + 0.5*math.log(2.0/max(w, 0.05)))


def estimar(antena, f, sustrato):
    """Devuelve {'fbw': fracción, 'f_lo', 'f_hi'} en Hz para la frecuencia central f."""
    tipo = antena.tipo
    p = antena.parametros
    lam = lambda0_mm(f)
    if tipo in ('parche_rectangular', 'parche_minkowski', 'parche_circular', 'array_parches'):
        W, L, h, er = p['ancho'], p['largo'], sustrato.h, sustrato.er
        fbw_rad = 3.77*(er - 1)/er**2*(W/L)*(h/lam)
        if tipo == 'parche_minkowski' or (tipo == 'array_parches' and int(p.get('elemento', 0)) == 1):
            fbw_rad /= (1 + 0.2*p.get('profundidad', 0.5)*int(p.get('iteracion', 0)))**2
        q = 1/(fbw_rad/S_10DB + sustrato.tand)
        fbw = S_10DB/q
    else:
        if tipo in ('yagi_boom', 'panel_dipolos'):
            a = antena.info['largo_dipolo_mm']/2      # la banda la limita el dipolo excitado
        elif tipo == 'yagi_koch':
            minx, miny, maxx, maxy = antena.radiador.bounds
            a = max(maxx - minx, maxy - miny)/2
        else:
            minx, miny, maxx, maxy = antena.contorno.bounds
            a = math.hypot(maxx - minx, maxy - miny)/2
        ka = 2*math.pi/lam*a
        q = FACTOR_Q.get(tipo, 3.0)*q_chu(ka)*_factor_pista(p.get('ancho_pista', p.get('ancho_dipolo', 2.0)))
        fbw = min(S_10DB/q, 0.8)
    return {'fbw': fbw, 'f_lo': f*(1 - fbw/2), 'f_hi': f*(1 + fbw/2)}
