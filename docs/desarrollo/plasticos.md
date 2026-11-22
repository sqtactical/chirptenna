# Medir las propiedades de un plástico con el cupón C (22-11-2026)

Objetivo: que cualquiera pueda medir la εr (y, de forma aproximada, la tanδ) de **su** plástico (el de la carcasa, un radomo) con un NanoVNA y meterlas en la simulación
(material «Personalizado» de la carcasa), en vez de fiarse de valores típicos.

**Restricción de hardware**: un NanoVNA normal llega a **900 MHz** (los H/H4, a 1,5 GHz; el del proyecto, con armónicos, a 2,7 GHz), así que el cupón no puede depender de 2,4 GHz. La
primera versión (anillos resonantes medidos en S21) no servía por debajo de 1 GHz (ver «Historia» al final); la actual usa **stubs abiertos medidos en S11**.

## El cupón C

`python cupon/generar_cupon.py C` → `cupon/cupon_C/` (placa KiCad, Gerber, `cupon_C_JLC.zip`, DRC limpio). Placa de 100 × 100 mm de FR4 de 1,6 mm con masa inferior y **tres líneas de 50 Ω**
(3,01 mm) que acaban en circuito abierto, cada una con su conector SMA de canto en el borde de arriba:

| Stub | largo (borde → extremo) | λ/4 (modo 1) | modo 2 (3λ/4) | modo 3 (5λ/4) |
|---|---|---|---|---|
| S86 | 86 mm | 450 MHz | 1354 MHz | 2253 MHz |
| S59 | 59 mm | 646 MHz | 1943 MHz | — |
| S43 | 43 mm | 870 MHz | 2625 MHz | — |

(frecuencias de la simulación 3D con εr 4,5 y sin conector; el real cae unos puntos más bajo). Un NanoVNA normal mide los tres modos 1; uno de 1,5 o 2,7 GHz, también los armónicos: hasta siete frecuencias
entre 450 y 2625 MHz para ver cómo cambia el plástico con la frecuencia. Cada stub lleva su recuadro de muestra en la serigrafía y **cuatro taladros M3** con círculo libre en la masa (12 en total; los puentes
de ancho cero del plano de masa son como los escribe KiCad).

Un stub abierto de largo L resuena (X = 0 con pendiente positiva, R mínima) con L = λg/4, 3λg/4, 5λg/4…: f_n = (2n−1)·c/(4·L·√εeff). La muestra sube el εeff y baja f_n; su pérdida sube la R en la resonancia.
Se mide con **un solo puerto (S11)**, que es lo que hacen el NanoVNA y Chirptenna VNA (ya no hace falta traer el S21 de un archivo).

## Las piezas impresas: tiras con taladros, sin pisador

`antenas.plastico.muestras_stl(carpeta)` (botón en Medir → Asistente de materiales; salida en `salidas/muestras_cupon_C/`): tiras de **24 mm de ancho** y el largo de cada stub (de 4 mm del borde a 3 mm más allá del extremo)
de 2, 3 y 4 mm, con cuatro taladros de M3 que coinciden con los del cupón. Se fijan con tornillos y tuercas de nailon (cabeza bajo la placa, tuerca y arandela encima), apretados a mano: los tornillos **centran la muestra**
(±0,2 mm) y **no hay nada de plástico sobre el stub**. Se imprimen planas con el **mismo material, relleno y orientación** que la carcasa; el grosor real, con calibre.

**Por qué no hay pisador**: una placa de 4 mm del mismo plástico sobre la muestra sube la εr aparente un 9–17 % (εr 2,8 y 3 mm: 3,04, +8,6 %; εr 2,8 y 2 mm: 3,28, +17 %; εr 4 y 3 mm: 4,47, +12 %), porque mete otro dieléctrico en el
campo; y además la muestra se movía al ponerlo. (`eps_eff(..., cub=(εr, grosor, rendija))` lo calcula.) Con 24 mm de ancho el borde de la muestra casi no cuenta (−0,04 % en εeff frente a una muestra infinita; 12 mm: −0,4 %). Los taladros están a ≥ 5 mm del borde
de la pista (prueba `test_las_tiras_caben_en_la_placa_y_los_taladros_lejos_del_stub`).

## El cálculo (`antenas/plastico.py`, igual en `js/plastico.js` de Chirptenna VNA)

1. **Solver cuasiestático 2D** de la sección (masa, FR4, rendija de aire, tira de 24 mm, aire): volúmenes finitos con SOR rojo-negro en numpy (sin scipy). Da εeff = C/C_aire y la fracción de energía en cada material.
   Sin muestra: εeff 3,384 frente a 3,394 de Hammerstad (−0,3 %).
2. **εr de la muestra**: (f_vacío/f_cargado)² = 1 + κ·(εeff_cargado/εeff_vacío − 1), con κ = 0,947 + 0,0001·t + 0,0845·Δ − 0,017·(modo−1), ajustado a la simulación 3D (abajo). Sale de `medir_stub`.
3. **Resonancias en un S11**: `resonancias_stub(f, s11)` pasa a Z = 50·(1+S11)/(1−S11) y busca los cruces de X por cero con pendiente positiva (da f, R y dX/df); `elegir_resonancia` toma la de la frecuencia esperada.
4. **tanδ** (aproximada): en la resonancia serie Z = Z0·tanh(αL) ≈ Z0·αL, y la pérdida del dieléctrico es α_d = (π·f·√εeff/c)·Σ qᵢ·tanδᵢ (q = fracción de energía). Con las R de vacío y con muestra, el offset del conector se resta
   y el cobre se toma ∝ √f (`ALFA_C_1GHZ` = 0,06 Np/m). **Es la parte débil**: ΔR es de unas décimas de ohmio y un NanoVNA da ±0,25 Ω, así que la tanδ solo se distingue por encima de ~0,03; la interfaz da su incertidumbre y avisa
   «no fiable» si es mayor que el valor.
5. **εr del FR4 del cupón** (`er_fr4_stubs`): con la resonancia del mismo modo de varios stubs, la recta c/(4f)·(2n−1) frente al largo tiene por pendiente √εeff y por ordenada la longitud eléctrica del conector (que no se conoce) y se elimina.
6. **Incertidumbre**: resolución de frecuencia (±0,3 MHz), grosor (±0,1 mm), εr del FR4 (±0,15), residuo de la corrección 3D y **±2 mm de línea sin muestra por el conector** (±0,04 en κ), en cuadratura.

## Validación contra openEMS 3D (`cupon/simular_stub.py <S43|S59|S86> --muestra εr,tanδ,grosor,ancho`, GPU, 12–25 s por caso)

Modelo 3D: la línea de 50 Ω hasta el borde (plano de medida), el pad del SMA de 1,27 mm, la transición cónica y el stub; cobre PEC; FR4 de εr 4,5 y tanδ 0,02. 42 casos con muestra (εr 2,2–10, grosor 2–4 mm, 3 stubs, 2–3 modos cada uno):

- Resonancias sin muestra: S43 869,7 / 2624,9 MHz; S59 646,2 / 1942,6; S86 450,3 / 1353,6 / 2253,1 (R ≈ 1,3–3,2 Ω).
- **El modelo 2D sin corregir** da el desplazamiento algo alto (κ 0,91–1,0; error de εr −3 % de media, 7 % máx). Con la corrección de arriba, **εr a ±1,1 % rms (3,3 % máx; n = 45)**. (Con el anillo de la primera versión el sesgo era de +8 a +16 %.)
- **tanδ**: con PEC y las R simuladas sale el orden de magnitud en el modo 1 (0,0195 con 0,02 real) pero mal en el modo 2 y con tanδ pequeña (ΔR de 0,05–0,2 Ω, comparable al ruido de la propia simulación). Se considera **no validada**.
- **FR4**: con las resonancias 3D de εr 4,5, `er_fr4_stubs` da 4,65 (+3 %: la malla de FDTD da un εeff algo alto) y un lanzamiento de ~3 mm: no se puede fiar el valor absoluto a mejor de ±3 %.

## Precisión: ¿es peor medir con stubs?

Cerca de |Γ| = 1, un error pequeño de S11 mueve mucho X (≈ 26 Ω por unidad de Γ), así que el cruce por cero de un stub es sensible a la calibración. Monte Carlo (22-11) sobre las curvas S11 3D de los stubs
(paso de 1,35 MHz, más grueso que el de un NanoVNA), añadiendo ruido complejo por punto (σ) y un error sistemático complejo de calibración (|ε|), 150 repeticiones, εr recuperada (media ± desviación):

| caso (εr real) | σ 0,005 / ε 0,01, **misma calibración** en las dos medidas | calibración **distinta** en cada una | σ 0,01 / ε 0,02, misma | distinta |
|---|---|---|---|---|
| S43 modo 1, PLA 2,8, 3 mm | 2,82 ± 0,04 (1,4 %) | 2,82 ± 0,13 (4,6 %) | 2,84 ± 0,14 | 2,91 ± 0,77 |
| S43 modo 1, εr 6, 2 mm | 6,10 ± 0,07 | 6,08 ± 0,21 | 6,13 ± 0,18 | 6,16 ± 0,42 |
| S43 **modo 2**, PLA 2,8, 3 mm | 2,77 ± 0,01 (0,4 %) | 2,77 ± 0,03 | 2,78 ± 0,03 | 2,77 ± 0,07 |
| S86 modo 1, PLA 2,8, 3 mm | 2,77 ± 0,04 | 2,78 ± 0,13 | 2,77 ± 0,09 | 2,76 ± 0,28 |

Conclusiones:
- **Lo que manda es la repetibilidad de la calibración entre las dos medidas**, no el ruido: con la misma calibración el error es de 1–2 %; si se recalibra entre medio, se triplica. Por eso el asistente pide medir sin y con muestra sin recalibrar ni mover el cable.
- **Los armónicos son 3–4 veces mejores** (el mismo error absoluto en MHz es una fracción menor de una frecuencia mayor): un NanoVNA que llegue a 1,5–2,7 GHz debe usar los modos 2 y 3.
- Con un NanoVNA normal (≤ 900 MHz, solo modo 1) se espera 1,5–5 %, no el 1 % de la validación 3D (que no tiene ruido de medida ni conector). El cruce se toma de una **recta ajustada a X(f) en ±3 puntos** (no entre dos puntos): baja el ruido a la mitad.
- Frente al anillo (S21): su pico tiene un Q de ~12 y es muy plano, y un error de 0,3 dB en S21 lo mueve decenas de MHz (estimación, no simulada con ruido); el cruce de X de un stub tiene pendiente (0,09 Ω/MHz) y es, en general, más preciso, además de medirse con la calibración OSL estándar.
- La tolerancia de frecuencia de `medir_stub` pasa de 0,3 a **1 MHz** (el valor del Monte Carlo con la misma calibración); la de cada tira se suma a la del grosor, la del FR4 y la del conector.
- Es una simulación del error, no una medida: el NanoVNA real puede tener derivas, ruido de cable y otras fuentes que aquí no entran.

## Límites

- La muestra es plana y **sin rendija**: una rendija de 0,1 mm baja el efecto un 10–20 %; el asistente pide una estimación y la mete en el modelo. Montar de nuevo y repetir da la dispersión.
- El conector real (SMA de canto) y su unión no están en la simulación 3D: de ahí los ±2 mm de la incertidumbre.
- Impresión 3D: anisótropa y dependiente del relleno. Es el valor efectivo de ese trozo, no del filamento.
- Sin medir con una placa real todavía: pendiente de pedir el cupón C y de validar con una muestra conocida (PTFE, FR4).

## Chirptenna VNA

`js/plastico.js` (mismo cálculo, probado contra los números de Python en `pruebas/plastico.test.mjs`) y `js/materiales.js` + tarjeta «Asistente de materiales (cupón C)» (modo Avanzado): **usa la última medida
de la página** (S11 en vivo con el NanoVNA), sube un `.s1p` o se escriben f y R; da εr y tanδ.

## Historia: el anillo (descartado)

La primera versión usaba los anillos del cupón A (868 MHz y 2,4 GHz) medidos en S21. El de 2,4 GHz se validó (corrección ajustada a 7 simulaciones, εr a ≤ 1 %), pero el de 868 MHz no sirve:
con el criterio de fin por defecto de openEMS (1e-5) la simulación paraba antes de que el anillo, poco acoplado, resonara (curva lisa sin pico); con `--fin 1e-9` (40 min) sale una joroba ancha de −30 dB a 890,6 MHz entre dos ceros que con PLA se
desplaza un 46 % más que el modelo (κ = 1,46): no es un resonador limpio. Además un NanoVNA normal no llega a 2,4 GHz, y el S21 exige otra calibración. Las funciones del anillo (`er_fr4`, `CORR_3D['R2G4']`) siguen en `plastico.py` para el cupón A, y
`cupon/simular_anillo.py` conserva `--fin`, `--pasos` y `--muestra`. **Lección**: en una simulación de resonador poco acoplado, bajar `--fin` y comprobar que el S21 tiene forma de pico.