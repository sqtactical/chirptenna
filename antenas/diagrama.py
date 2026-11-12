"""Exportar el diagrama de radiación simulado (F4.6): CSV con θ, φ, directividad y ganancia en dBi."""
import csv

import numpy as np


def filas(r, d):
    """[(θ°, φ°, directividad dBi, ganancia dBi)] del resultado `r` (`resultado.json`) y los datos `d` (`datos.npz`).

    La ganancia es la directividad menos la pérdida de la eficiencia de radiación, que es la misma en todas las direcciones
    (`ganancia_dBi − directividad_dBi` del resultado). Lanza ValueError si la simulación no tiene diagrama."""
    theta, phi, dd = np.asarray(d.get('theta', [])), np.asarray(d.get('phi', [])), np.asarray(d.get('d', []))
    if not theta.size or not phi.size or dd.ndim != 2 or dd.shape != (theta.size, phi.size):
        raise ValueError('La simulación no tiene diagrama de radiación (se hizo sin NF2FF).')
    g, dir_ = r.get('ganancia_dBi'), r.get('directividad_dBi')
    # pérdida de eficiencia: la diferencia entre ganancia y directividad en el máximo (NaN si la eficiencia no se pudo calcular)
    perdida = float(g) - float(dir_) if g is not None and dir_ is not None and np.isfinite(g) and np.isfinite(dir_) else 0.0
    return [(float(theta[i]), float(phi[j]), float(dd[i, j]), float(dd[i, j]) + perdida) for i in range(theta.size) for j in range(phi.size)]


def exportar_csv(ruta, r, d):
    """Escribe `ruta` (CSV con coma, cabecera `theta_deg,phi_deg,directividad_dBi,ganancia_dBi`). Devuelve el máximo de ganancia."""
    datos = filas(r, d)
    with open(ruta, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['theta_deg', 'phi_deg', 'directividad_dBi', 'ganancia_dBi'])
        for t, p, dr, ga in datos:
            w.writerow([f'{t:.2f}', f'{p:.2f}', f'{dr:.3f}', f'{ga:.3f}'])
    return max(x[3] for x in datos)
