# Antena integrada: IFA y meandro frente al tamaño de la placa (F3.2, 12-11-2026)

Simulado en GPU (`simulacion.ajustar`, precisión normal salvo donde se dice, malla uniforme, FR4 JLC 1,6 mm, conector SMA, antena en la
esquina superior izquierda, zona de antena automática con 2 mm de margen). Objetivo: centrar la banda en 2441,75 MHz (o 866,5 MHz).
Cada fila es una sola simulación de ajuste (3–5 simulaciones del bucle); no es una medida.

## IFA a 2,4 GHz

| Placa [mm] | Sims | f [MHz] | Banda −10 dB [MHz] | Ancho [MHz] | S11 mín [dB] | Ganancia [dBi] | η rad. [%] | Brazo [mm] |
|---|---|---|---|---|---|---|---|---|
| 20 × 30 | — | — | — | — | — | — | — | no cabe: la zona mide 25,6 mm y la placa 20 |
| 25 × 40 | 3 | 2425 | 2364–2487 | 124 | −12,5 | 2,31 | 83 | 15,16 |
| 30 × 50 | 2 | 2465 | 2360–2575 | 215 | −18,7 | 1,62 | 88 | 15,26 |
| 50 × 80 | 4 | 2447 | 2312–2590 | 278 | −12,2 | 1,62 | 83 | 13,77 |
| 80 × 120 | 4 | 2438 | 2286–2600 | 314 | −23,1 | 2,98 | 79 | 14,81 |
| suelta (placa de prueba de 40 × 40) | 3 | 2430 | 2325–2539 | 215 | −29,8 | 2,18 | 90 | 18,2 |

Lectura: el brazo se acorta 2–4 mm respecto al de la IFA suelta (la masa de la placa es más corta que los 40 mm de masa de la
placa de prueba y el brazo ya no cae sobre ella) y **el ancho de banda crece con la placa** (124 → 314 MHz) mientras la eficiencia
baja un poco (83 → 79 %: más cobre, más pérdida en el FR4). Con 25 mm de ancho (0,2 λ) la banda se queda en la mitad. Por debajo de unos
26 mm de ancho la IFA de 2,4 GHz no cabe (la zona de antena mide ~22–26 mm).

## IFA a 868 MHz

| Placa [mm] | Sims | f [MHz] | Banda −10 dB [MHz] | Ancho [MHz] | S11 mín [dB] | Ganancia [dBi] | η rad. [%] |
|---|---|---|---|---|---|---|---|
| 80 × 120 | 5 | 865 | 834–898 | 64 | −23,0 | 2,23 | 88 |

La IFA de 868 MHz no cabe en 40 × 80 mm (la zona de antena mide ~66 mm de ancho); en 80 × 120 mm sí, pero el ajuste necesita 5 simulaciones
(la secante oscila: 796, 831, 920, 891, 865 MHz).

## Meandro

| Placa [mm] | Frecuencia | Sims | f [MHz] | S11 mín [dB] | Ganancia [dBi] | η rad. [%] | Nota |
|---|---|---|---|---|---|---|---|
| 30 × 50 | 2,4 GHz | 2 | 2630 | −5,1 | 1,29 | 76 | no centra: hueco de 0,54 mm con menos de 2 celdas |
| 30 × 50 (precisión fina) | 2,4 GHz | 4 | 2447 | −4,3 | 1,15 | 71 | centra la reactancia, pero no adapta |
| 50 × 80 | 2,4 GHz | 2 | 2644 | −9,3 | 1,58 | 80 | sin banda a −10 dB |
| 40 × 80 | 868 MHz | — | — | — | — | — | no cabe: el meandro tras el ajuste mide 68,6 mm de zona y la placa necesita ≥ 80,6 mm de alto |
| 80 × 120 | 868 MHz | 2 | 840 | −2,8 | 0,52 | 62 | no adapta |

El meandro integrado **no llega a −10 dB** en ninguna de las placas probadas (con la IFA sí): la masa corta le sube la impedancia y no hay
transformación. No se ha buscado un tamaño mínimo que lo adapte; se avisa en `consejos.py`.

## Criterio de F3.2 («centrado en ≤ 3 simulaciones»)

- IFA 30 × 50 mm a 2,4 GHz: **cumple** (2 simulaciones).
- IFA 25 × 40 a 2,4 GHz: cumple (3). 50 × 80 y 80 × 120: 4 (la secante rebota una vez).
- IFA a 868 MHz en 80 × 120: 5 simulaciones. El tamaño de placa mínimo documentado para 868 MHz es ~80 × 100 mm (no se probó entre medias).
- Meandro: **no cumple** (ni 2,4 GHz ni 868 MHz): queda como tipo sin validar en modo integrado.
