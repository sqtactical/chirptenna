# Predicciones de la simulación antes de medir (pedido JLC de 2,4 GHz)

Escrito el 11-11-2026 (tarea F1.1 de la hoja de ruta), **antes de medir**. Geometría = la impresa (`ficha.json` de
`salidas/pedido_2G4/<diseño>/`), sin ajustar. Resonancia = centro de la banda a −10 dB; simulación en GPU a 2441,75 MHz
(rango 0,6–1,4 ×) con la malla fija de la εr 4,5 y tanδ 0,02 (`herramientas/sensibilidad_er.py`, resultados en
`salidas/_barridos/SENS_er_pedido/`, 08-11-2026).

Se pidieron **6 antenas** (Y54–Y59) y los dos cupones; el meandro y el panel 2×2 no se pidieron (la hoja de ruta hablaba de 7).

## Resonancia según la εr

| Pedido | Diseño | f (εr 4,2) MHz | f (εr 4,5) MHz | f (εr 4,8) MHz | Pendiente | Banda −10 dB con εr 4,5 | S11 a 2441,75 MHz (dB) | G (dBi) | η (%) |
|---|---|---|---|---|---|---|---|---|---|
| Y54 | `yagi_recta_2dir_2G4` | 2490 | **2447** | 2406 | -139 MHz por unidad de εr | 2365–2531 (166 MHz) | -17.6 | 7.2 | 75 |
| Y55 | `parche_rectangular_2G4` | 2521 | **2439** | 2365 | -259 MHz por unidad de εr | 2421–2458 (37 MHz) | -12.7 | 2.9 | 47 |
| Y56 | `monopolo_sierpinski_2G4` | 2501 | **2476** | 2453 | -81 MHz por unidad de εr | 2186–2803 (617 MHz) | -30.7 | 2.2 | 94 |
| Y57 | `monopolo_koch_2G4_ajustable` | 2358 | **2328** | 2300 | -97 MHz por unidad de εr | 2180–2487 (307 MHz) | -12.2 | 2.0 | 91 |
| Y58 | `jpole_koch_2G4` | 2492 | **2458** | 2428 | -107 MHz por unidad de εr | 2430–2486 (56 MHz) | -11.5 | 2.1 | 86 |
| Y59 | `dipolo_coaxial_2G4` | 2487 | **2466** | 2446 | -69 MHz por unidad de εr | 2323–2618 (295 MHz) | -28.0 | 1.8 | 96 |

Lectura: por cada +0,1 de εr real, la resonancia baja unos 7–10 MHz (dipolo y monopolos), 11 MHz (J-pole), 14 MHz (Yagi)
y 26 MHz (parche). El parche es el más sensible: con εr 4,2 o 4,8 la banda de 37 MHz se va fuera de 2441,75 MHz (S11 −3 dB).

## Comprobación del 09-11 con el generador actual (`salidas/pedido_2G4/verificacion.json`, εr 4,5)

| Diseño | f original (MHz) | f hoy (MHz) | Diferencia | S11 a 2441,75 MHz (dB) |
|---|---|---|---|---|
| `monopolo_sierpinski_2G4` | 2462 | 2430 | −1,30 % | -22.9 |
| `monopolo_koch_2G4_ajustable` | 2328 | 2343 | +0,65 % | -13.1 |
| `jpole_koch_2G4` | 2460 | 2460 | +0,03 % | -11.4 |
| `parche_rectangular_2G4` | 2434 | 2438 | +0,17 % | -13.1 |

(El meandro no se pidió.) La diferencia entre la ficha original y la simulación de hoy llega al 1,3 % en el Sierpinski:
ese es el orden de la incertidumbre de la propia simulación (malla, versión del generador) y hay que descontarlo al
comparar con la medida.

## Qué esperar al medir

- Si la εr real está en 4,2–4,6 (rango habitual del FR4 de JLC), todas las resonancias medidas deben moverse **en el mismo
  sentido**: con εr menor, más alta en frecuencia. Si unas suben y otras bajan, la causa no es la εr (cable, conector, malla).
- El Koch ajustable sale a propósito largo (2328 MHz): se recorta por las marcas hasta 2441,75 MHz.
- Dipolo, Sierpinski y Yagi tienen banda ancha (≥ 165 MHz): toleran ±0,3 de εr. El parche y la J-pole, no.
