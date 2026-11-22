# Resultados: stubs abiertos del cupón B (22-11-2026)

Medidas contra `prediccion_stubs_cupon_B.md` (escrita antes). **Una sola unidad** (`u1`; solo había SMA para una, ver su fe de erratas): P7 y T4 quedan sin comprobar. Calibración `cal_latiguillo_B_22-11` (OSL + THRU, 50 kHz–2,7 GHz, 1010 puntos, rejilla de 2,67 MHz), verificada con la carga al empezar (|S11| mediana −44,3 dB, peor −29,8 dB) y al acabar (−45,5 y −25,0 dB). Datos crudos: `vna/medidas/cuponB_u1_{S80,S30}_r{1,2,3}.s1p`. Tres reconexiones por stub, `resonancias_stub` sin retoques, `er_fr4_stubs` con largos 85,7 y 35,7 mm.

## Datos

| Stub | modo | r1 | r2 | r3 | media | dispersión (σ) |
|---|---|---|---|---|---|---|
| S80 | 1 | 454,13 | 453,82 | 454,05 | **454,00 MHz** | 0,03 % |
| S80 | 2 | 1377,27 | 1377,83 | 1378,76 | **1377,95** | 0,04 % |
| S80 | 3 | 2286,27 | 2286,48 | 2288,24 | **2287,00** | 0,04 % |
| S30 | 1 | 1092,99 | 1096,04 | 1098,34 | **1095,79** | 0,20 % (rango 0,5 %) |

R en la resonancia: S80 0,29–0,31 Ω (modo 1), 0,72–0,80 Ω (modo 2), 0,66–0,71 Ω (modo 3); S30 0,38–0,42 Ω.

## Contraste con las predicciones

| # | Predicción | Medido | Resultado |
|---|---|---|---|
| P1 | f₂/f₁ = 3,00 ± 0,04; f₃/f₁ = 5,00 ± 0,08 | 3,035; 5,037 | **Cumple** (en el borde alto de la banda) |
| P2 | εr FR4 con los dos stubs, modo 1: 4,4 (4,1–4,7) | **5,03 ± 0,05** | **Falla** |
| P3 | lanzamiento 2–6 mm | **−0,33 mm** | **Falla** |
| P4 | f₁ S80 420–475 MHz | 454,0 | Cumple (la simulación 3D con εr 4,5 daba 451,9) |
| P5 | f₁ S30 960–1070 MHz | 1095,8 | **Falla** (por arriba; 3D con εr 4,5: 1034) |
| P6 | R de S80 modo 1: 1–6 Ω | 0,30 Ω | **Falla, pero no concluyente** (ver abajo) |
| P7 | dispersión entre unidades ≤ 0,5 % | — | Sin comprobar (una unidad) |
| P8 | repetibilidad al reconectar ≤ 0,3 % | S80 0,03 %; S30 σ 0,2 % (rango 0,5 %) | Cumple en S80; en S30 cumple por σ y no por rango |

Pruebas de refutación: **T2** (εr fuera de 3,8–5,0): 5,03, en el límite y fuera por unas centésimas. **T3** (lanzamiento negativo o > 10 mm): −0,33 mm, **se dispara**. T1 y T5 no se disparan.

## Lectura

- El método funciona como instrumento: las tres resonancias de S80 son limpias, repetibles al 0,03 % y su razón de modos es la esperada.
- **El número final del FR4 (5,0) no se sostiene**: depende de solo dos puntos, y S80 coincide con la simulación 3D (εr 4,5) mientras S30 sale un 6 % más alto. Dos stubs en un mismo modo no bastan para separar εr y conector si el conector no es una longitud pura. Que f₂/f₁ sea 3,035 (>3, cuando la dispersión del FR4 tendería a dar <3) apunta a un término reactivo que no es proporcional a la longitud.
- **R de 0,3 Ω no se puede interpretar**: es del orden del residuo de la calibración (|Γ| ≈ −45 dB ⇒ ±0,3–0,6 Ω), y la simulación 3D no lleva pérdida de cobre. No se concluye nada sobre tanδ.
- Aviso de calibración en S30 (|S11| hasta +0,8 dB a 2470 MHz): artefacto repetible fuera de las resonancias usadas.

## 5. Hipótesis nuevas (no son correcciones; cada una con su prueba)

Se apuntan aquí, no en la hoja de predicciones, para respetar su regla 4.

1. **El conector SMA aporta una reactancia fija (no solo longitud).** Predicción: la recta 1/f frente al largo tiene el mismo εr con un tercer stub; la prueba es medir un tercer largo (S43/S59/S86 del cupón C, cuando llegue) y ver si los tres caen en una recta con εr ≈ 4,3–4,6.
2. **S30 se desvía por su cercanía al conector.** Predicción: S30 en 3D con el SMA modelado (hoy solo pad y taper) sube ~4–6 % respecto a 1034 MHz.
3. **La rejilla de 2,67 MHz sesga el cruce del modo 1 de S30.** Predicción: una calibración fina de 900–1300 MHz con 101 puntos da el mismo valor a ±0,3 %.

## Predicciones registradas antes de medir los anillos (22-11-2026, simulación 3D `cupon/simulaciones/`)

Con `vna/medir_s21_pc.py`, calibración `cal_latiguillo_B_22-11` (THRU, sin aislamiento: suelo de S21 ~ −50 dB), puerto A en CH0 y B en CH1:

| Anillo | Cupón | Pico previsto | S21 previsto | Nota |
|---|---|---|---|---|
| R5G8 (n=1) | B | 1937,6 MHz (diseño 1933) | −14,6 dB | simulación con εr 4,5 |
| R2G4 (n=1) | A | 2397,1 MHz | −14,6 dB | |
| R868 | A | joroba ancha hacia 890,6 MHz | −29,8 dB | poco acoplado; inservible como sensor |

Los picos reales pueden desplazarse unos % por la εr real del FR4 (la medida de los stubs da ~4,5–5,0).

## Resultados de los anillos (22-11-2026)

Una placa de cada cupón (A y B), CH0 en el puerto A y CH1 en el B, tres reconexiones por anillo, `vna/medir_s21_pc.py`, mismas calibración y condiciones. Picos afinados con una parábola sobre la rejilla de 2,67 MHz. Crudos: `vna/medidas/cupon{A_R2G4,A_R868,B_R5G8}_r{1,2,3}.s2p`. Verificación final con la carga: |S11| mediana −39,0 dB, peor −21,6 dB (a 2700 MHz); empezó en −44,3 / −29,8 dB (algo peor, sin llegar a invalidar).

| Anillo | Predicción 3D | Medido (media de 3) | Desvío | S21 medido | S21 previsto |
|---|---|---|---|---|---|
| R5G8 n=1 (cupón B) | 1937,6 MHz | **1967,0 MHz** (±0,1) | +1,5 % | −13,9 dB | −14,6 dB |
| R2G4 n=1 (cupón A) | 2397,1 MHz | **2428,4 MHz** (±0,05) | +1,3 % | −10,4 / −12,7 / −10,5 dB | −14,6 dB |
| R868 n=1 (cupón A) | 890,6 MHz (joroba) | **882,3 MHz** (±0,05) | −0,9 % | −21,6 dB | −29,8 dB |
| R868 n=2 | 1740 (diseño) | **1763,0 MHz** | +1,3 % | −19,5 dB | — |
| R868 n=3 | 2600 (diseño) | **2634,1 MHz** | +1,3 % | −13,3 dB | — |

- Repetibilidad al reconectar: frecuencia ≤ 0,05–0,06 % (por debajo de la rejilla); nivel ≤ 0,2 dB salvo R2G4 (una de tres a −12,7 dB: contacto).
- **El R868 sí da un pico limpio** (n=1,2,3 con cocientes 1,998 y 2,986). La simulación 3D de la joroba (−30 dB) lo daba por inservible; el hardware lo contradice. **Pendiente: medir su desplazamiento con una muestra** (κ simulado 1,46) antes de usarlo como sensor.
- Los tres anillos salen +1,3…+1,5 % altos respecto a la simulación (R868 n=1 sale −0,9 %): un offset común sugiere una εr real algo menor que 4,5, o la malla FDTD (εeff +3 % lenta), no un fallo de un anillo. Con solo estos datos no se separa. Si fuera εr: (1,014)² ⇒ εeff −2,8 % ⇒ εr ≈ 4,2–4,3, que además contradice el 5,0 de los stubs: hay que resolverlo con un tercer stub o una εr medida por otro método.
- Artefacto del THRU entre 2100 y 2119 MHz (S21 hasta +49 dB): se ignora esa banda.
- El conector y el lanzamiento van dentro de la medida (sin de-embedding).

## Predicciones registradas antes de medir las líneas L64 y L17 (22-11-2026)

Dos puertos, CH0 en A y CH1 en B, sin OSL en la placa (el conector y el codo, iguales en L64 y L17, se cancelan al restar). Misma calibración y script (`medir_s21_pc.py`, rango completo, ignorando 2100–2119 MHz).

| # | Qué | Predicción | P |
|---|---|---|---|
| L1 | εeff de la microstrip de 50 Ω de la diferencia de fase L64 − L17 (Δl = 47,0 mm), por debajo de 1 GHz | 3,3–3,6 (Hammerstad 3,39 con εr 4,5; εr 4,3–4,8) | 60 % |
| L2 | |S21| de L17 hasta 1 GHz | > −1,0 dB | 70 % |
| L3 | |S21| de L64 a 2 GHz | entre −0,5 y −2,0 dB | 60 % |
| L4 | Repetibilidad de |S21| al reconectar | ≤ 0,3 dB | 60 % |

Refuta el método: εeff fuera de 3,0–3,9 o una diferencia entre L64 y L17 que cambie más de 0,5 dB entre reconexiones.

## Resultados de L17 y L64 (22-11-2026)

Cupón B, CH0 en el puerto B y CH1 en el A (misma orientación en todas), tres reconexiones cada una; crudos `vna/medidas/cuponB_L{17,64}_r{1,2,3}.s2p`. εeff de la pendiente de la fase de S21(L64)/S21(L17), Δl = 47,0 mm, con las 9 combinaciones de reconexión:

| Ventana de ajuste | εeff media | σ | mín–máx |
|---|---|---|---|
| 50–1000 MHz | **3,71** | 0,03 | 3,68–3,75 |
| 300–1000 MHz | 3,69 | 0,02 | 3,67–3,72 |
| 50–600 MHz | 3,97 | 0,05 | 3,93–4,04 |

- L1: **3,7** (predicción 3,3–3,6): falla por poco por arriba; dentro del criterio de refutación (3,0–3,9) salvo la ventana de 50–600 MHz (3,97), que depende de la ventana: a baja frecuencia la fase diferencial es pequeña (0,19 rad a 100 MHz) y cualquier deriva pesa más. No tomo esa ventana como valor.
- L2 (|S21| de L17 < 1 GHz > −1 dB): **cumple** (−0,03 a 0,03 dB hasta 1 GHz).
- L3 (|S21| de L64 a 2 GHz entre −0,5 y −2,0 dB): **cumple** (−1,2 dB).
- L4 (repetibilidad de |S21| ≤ 0,3 dB): sin analizar con detalle (S21 mediana −0,1/−0,1/−0,2 dB en L64; igual en L17); el S11 máximo de L64 pasó de −8,98 a −8,58 dB en la tercera.
- Offset de fase del cociente ≈ −0,013 rad (≈ 0): el conector y el codo se cancelan.
- Con εeff 3,7 y la geometría de diseño (w/h para εr 4,5), Hammerstad da **εr ≈ 4,9**: coincide con el 5,03 de los stubs (sección 1) y no con 4,2–4,3.
- Por encima de 1,2 GHz el módulo de S21 tiene rizado y picos > 0 dB (hasta +2,8 dB en L17, +75 dB en L64 por el artefacto del THRU a 2100 MHz); no se usa. Causa: calibración de S21 sin aislamiento ni corrección de S22.

## Predicciones registradas antes de medir la MS100 (22-11-2026)

Microstrip de 100 Ω (`MS100`, W 0,69 mm, 88,6 mm entre transiciones, Hammerstad εeff 3,08 con εr 4,5; 3,31 con εr 4,9). **Orientación de esta línea: CH0 en A y CH1 en B** (las anteriores llevaban CH0 en B). Misma calibración y script, 3 reconexiones.

| # | Qué | Predicción | P |
|---|---|---|---|
| M1 | Período del rizado de \|S11\| (distancia entre mínimos, que son los puntos de media onda) | 930–970 MHz con εr 4,5–4,9; el conector y las transiciones lo acortan un 2–4 % | 60 % |
| M2 | \|S11\| máximo (cuarto de onda, sin pérdidas Γ = 0,6) | −3 a −6 dB cerca de 470–490 MHz | 65 % |
| M3 | \|S21\| mínimo en el cuarto de onda (ideal 0,8 = −1,9 dB) | −1,5 a −3,0 dB | 55 % |
| M4 | εeff de la línea de 100 Ω según el período del rizado (longitud eléctrica 88,6 mm + transiciones) | 3,1–3,5 | 55 % |

Refuta: sin rizado de \|S11\| (el conector domina), o período fuera de 850–1050 MHz.

## Resultados de la MS100 (22-11-2026)

Tres reconexiones, CH0 en A, CH1 en B; crudos `vna/medidas/cuponB_MS100_r{1,2,3}.s2p`. Extremos por parábola sobre la rejilla de 2,67 MHz:

| | r1 | r2 | r3 |
|---|---|---|---|
| mínimo 1 de \|S11\| (media onda) | 895,7 MHz (−35,3 dB) | 893,5 (−33,2) | 896,1 (−34,8) |
| mínimo 2 de \|S11\| | 1799,3 (−24,9) | 1798,2 (−22,6) | 1798,5 (−25,3) |
| máximo de \|S11\| (cuarto de onda) | −5,9 dB | −5,9 | −5,9 |
| mínimo de \|S21\| | −2,2 dB (417 MHz) | −2,2 | −2,2 |

- M1 (período 930–970 MHz): **falla**; período real ≈ **896–899 MHz** (la repetibilidad es 0,3 %). Dentro del límite de refutación (850–1050).
- M2 (\|S11\| máx. −3 a −6 dB a 470–490 MHz): nivel **cumple** (−5,9 dB); la frecuencia queda en 440–455 MHz (por debajo del rango previsto).
- M3 (\|S21\| mín. −1,5 a −3,0 dB): **cumple** (−2,2 dB).
- M4 (εeff 3,1–3,5 con 88,6 mm nominales): **3,55**, por poco arriba. Equivale a εeff 3,31 (εr 4,9) con ~3 mm de línea eléctrica extra de conectores y transiciones, la misma cifra que el rango previsto del lanzamiento (2–6 mm) y compatible con L17/L64 (εeff 3,7 con la geometría de 50 Ω). **Hipótesis, no corrección.**
- Conjunto de las líneas: stubs (εr 5,03), L64−L17 (εr ≈ 4,9) y MS100 (εr ≈ 4,9 + ~3 mm de conector) coinciden en un FR4 con **εr ≈ 4,9–5,0**, por encima del 4,5 del diseño. Los anillos (+1,3…+1,5 % sobre la simulación con εr 4,5) apuntan a lo contrario si se interpretan sin la sobre-εeff de la malla FDTD (+3 %): sin resolver.

## Predicciones registradas antes de medir la CPWG50 (22-11-2026)

Coplanar con masa de 50 Ω (`CPWG50`, hilo 1,61 mm, hueco 0,3 mm, valla de vías cada 3 mm, 88,6 mm entre transiciones, εeff de diseño 2,88 con εr 4,5; ~3,09 con εr 4,9). Verificación de la calibración justo antes: |S11| mediana −38,2 dB, peor −22,9 dB. Orientación CH0 en A y CH1 en B, 3 reconexiones.

| # | Qué | Predicción | P |
|---|---|---|---|
| C1 | Retardo de grupo de S21 (pendiente de la fase, 50–1000 MHz), conectores incluidos (+~3 mm) | 0,50–0,56 ns | 55 % |
| C2 | \|S11\| hasta 1 GHz | < −15 dB (50 Ω de diseño; los conectores y el taper del puerto lo empeoran) | 50 % |
| C3 | \|S21\| hasta 1 GHz | > −0,7 dB | 65 % |
| C4 | Diferencia de retardo CPWG − MS100 (3 mm iguales de conector) | CPWG más corto: 0,50–0,56 ns frente al ~0,60 ns de la MS100 | 55 % |

Refuta: retardo fuera de 0,45–0,62 ns, o \|S11\| > −8 dB por debajo de 1 GHz (la valla de vías o el coplanar no se comportan como la simulación).

## Resultados de la CPWG50 (22-11-2026)

Tres reconexiones (`vna/medidas/cuponB_CPWG_r{1,2,3}.s2p`), CH0 en A, CH1 en B. Retardo de la pendiente de la fase de S21 (50–1000 MHz): 0,633 / 0,630 / 0,630 ns (σ 0,3 %); \|S11\| máx. < 1 GHz: −16,9 / −17,0 / −17,0 dB; \|S21\| mín. < 1 GHz: −0,94 / −0,91 / −0,88 dB.

- C1 (retardo 0,50–0,56 ns): **falla** (0,631 ns), fuera del límite de refutación (0,45–0,62 ns).
- C2 (\|S11\| < −15 dB hasta 1 GHz): **cumple** (−16,9 a −17,0).
- C3 (\|S21\| > −0,7 dB): **falla por poco** (−0,88 a −0,94).
- C4 (CPWG más corta que la MS100): **falla**; ambos retardos (0,631 y 0,627 ns) son casi iguales, y el de la MS100 no es fiable por su rizado.

Separando el conector con los retardos de L17 (0,195 ns) y L64 (0,497 ns), de los que sale 6,42 ps/mm (εeff 3,71):

- L17 menos 16,6 mm de línea = **0,089 ns de retardo del conector y el codo** (equivale a 13,8 mm de línea; P3 de los stubs daba −0,3 mm: no coinciden, y aquí el valor incluye dos conectores y el codo; comprobar si los 16,6 mm de `L17` son entre transiciones).
- CPWG − ese retardo = 0,543 ns ⇒ **εeff de la CPWG ≈ 3,4** frente a 2,88 de diseño (3,09 con εr 4,9): un **9–17 % más lenta** que la simulación cuasi-estática. Hipótesis (sin probar): la valla de vías y la masa inferior bajo el coplanar no están en el modelo del diseño. Se comprobaría simulando la CPWG en 3D con las vías.

## Fe de erratas

(vacía)
