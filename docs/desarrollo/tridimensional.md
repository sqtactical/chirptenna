# Antenas de varias placas no coplanares y hélices de flex (16-11, sin validar)

Cuatro tipos nuevos (`antenas/tridimensional.py`), pedidos por el usuario desde las ideas de «Ideas a más largo plazo» del ROADMAP.
Todo está simulado a 2,4 GHz con malla gruesa (paso 1,2 mm, precisión «rápida», CPU) y **sin centrar ni medir**.

| Tipo | Qué es | Placas a fabricar | Simulado (2,4 GHz) |
|---|---|---|---|
| `diedro` | Dipolo bowtie antipodal con los dos brazos doblados hacia arriba un ángulo `angulo_v` (25° por defecto) | centro (SMA, línea y balun) + 2 alas, soldadas en las bisagras | 0° = bowtie plano exacto (−23,9 dB, D 2,2 dBi); 5° −25,6 dB; 25° −36,4 dB |
| `reflector_esquina` | Dipolo bowtie en el plano bisector de dos placas reflectoras de 90° (vértice truncado para dejar pasar la línea) | dipolo + 2 reflectores (FR4 con cobre en las dos caras, 150 × 110 mm) | S11 −48,8 dB, D 10,3 dBi, G 10,0 dBi, haz de frente (θ 90°, φ 90°) |
| `helice_normal` | Monopolo helicoidal de λ/4 de hilo sobre una placa de masa con SMA; el hilo es una tira de flex enrollada | placa de masa + tira de flex de π·D de ancho (rayas diagonales) | −6,4 dB, D 1,9 dBi (sin centrar) |
| `helice_cuadrifilar` | Cuatro brazos de λ/4 en una tira de flex enrollada (GPS L1, circular) | placa de masa + tira de flex | no se simula desde la interfaz |

## Cómo está hecho

- **Modelo** (`antenas/modelo.py`, `antenas/pose.py`): la `Antena` principal (la del conector y el puerto) es plana en XY. Las demás placas van en
  `Antena.placas3d` como `{nombre, antena (plana), origen, giros [(eje, grados)], fina}`: primero los giros alrededor del origen local, después el
  desplazamiento. Regla de la mano derecha, la misma de CSXCAD (`AddTransform('RotateAxis', eje, grados)`, grados). `Antena.hilos3d` guarda hilos
  `{puntos (n, 3), ancho}`. Las placas a fabricar van en `Antena.modulos`, como en la colineal modular (cada una exporta con su Gerber y su DRC).
- **Cobre simulado y fabricado** (`Antena.cobre_sim`): una unión soldada se simula como cobre continuo hasta la bisagra, pero se fabrica a 0,5 mm del
  canto (mínimo de KiCad). `cobre_sim` y `placas3d[i]['antena']` llevan el cobre continuo; las placas de `modulos`, el de fabricar.
- **Simulación** (`simulacion.simular`): FR4 y cobre de cada placa con la transformación de CSXCAD; los hilos con `AddCurve`. El dominio y la malla
  abarcan las piezas (`pose.caja_conjunto`); las marcadas `fina` ponen la rejilla uniforme y líneas en z con el paso fino sobre su proyección.
  **Trampa**: una lámina PEC de grosor cero girada no toca ninguna arista de la malla y desaparece sin avisar (el dipolo en V daba −1 dB con solo 5° de
  giro). El cobre de una placa girada se simula como una losa PEC de una celda de grosor (el paso fino en las alas, `λ/20` en un reflector grande).
  La clave de la caché lleva `placa3d_losa`: las cachés de la versión con láminas daban resultados falsos.
- **Vista 3D** (`vista3d._placa(..., pieza=)`, `_placas3d`): cada placa con su pose y los hilos como líneas.
- **Reflector de esquina**: el vértice queda a `separacion` del dipolo (por detrás de la placa del dipolo si el boom es corto) y las placas empiezan a
  `h + 1 mm` del plano de la placa del dipolo; la placa de abajo se baja `h` por su normal para que el grosor quede hacia fuera en las dos.
- **Hélices**: el hilo va a radio D/2 desde un pad de la línea de 50 Ω (z = h). Largo del hilo (modo normal) `N·√((πD)² + (H/N)²)`, resonancia
  `f = c/(4·L)`, sin calibrar (`K_HELICE_NORMAL` = 1). La cuadrifilar es solo geometría: la alimentación en cuadratura de dos puertos está en
  `herramientas/helice_flex.py` y no entra en `simular` (`info['sin_simulacion']` hace que `simular` lance un error claro).

## Falta

- Centrar cada tipo (la estimación de frecuencia no está calibrada), simular en GPU con malla fina y verificar la malla.
- Modelar la unión soldada y la escuadra o pieza que fija el ángulo; medir el diagrama de la V según el ángulo.
- El reflector de esquina con una Yagi pequeña delante, el vértice sin truncar y con la línea por una ranura.
- De la cuadrifilar: su simulación desde la interfaz, los componentes de la red (híbrido de 90° y una red L por dipolo) sobre la placa, y medirla; el flex de la hélice se simula sin su dieléctrico. **La red está calculada (28-11)**: con D 32 mm y ¼ de vuelta cada dipolo da 15,05 + j5,23 Ω a 1575,42 MHz; una bobina de 1,8 nH en serie junto al dipolo y un condensador de 3,0 pF en derivación hacia el híbrido (E24, Q 40 y 150) suben la eficiencia de adaptación de 0,71 a 0,96, con S11 del dipolo ≤ −10 dB de 1556 a 1594 MHz y razón axial de 0 dB en el cénit (con ±5 % en los componentes sigue en 0,0 dB y el desbalance de amplitud es de 0,02 dB). Con un híbrido de 90° ideal y ramas iguales la S11 del receptor es buena aunque los dipolos no lo estén (lo reflejado se pierde en el puerto aislado): la red mejora la potencia que llega a la antena. `herramientas/red_cuadrifilar.py` la recalcula para otros parámetros (dos simulaciones de ~20 s en GPU). Con `sentido` = −1 (a izquierdas en el modelo) la polarización sale RHCP, la de GPS; con +1, LHCP. `K_QHA` = 0,586 solo vale para ese diseño. **Es una antena de solo recepción (RX)**: lo que cuenta es la ganancia RHCP hacia el cielo, el ruido que añade la red y la tolerancia al desajuste, no la potencia radiada. Con el diseño centrado (`--centrar`): RHCP 2,9 dBi en el cénit, 2,1 a 60° de elevación, −0,1 a 30°, −2,4 a 10° y −3,9 a 0°; lóbulo trasero RHCP ≤ −8,5 dBi; la red disipa 0,19 dB (figura de ruido añadida con el híbrido ideal) y la desadaptación residual es de 0,006 dB. **El punto débil es el ancho de banda**: la eficiencia total ≥ 0,9 solo en 27 MHz (≥ 0,8 en 49 MHz) y con el brazo ±3 % la resonancia se mueve ≈ ∓35 MHz y se pierden 0,8–1,5 dB de señal por desadaptación (una carcasa de plástico o la mano la desplazan): hay que afinar con la carcasa puesta. Comparación con otros diámetros (centrados, con su red): D 24 mm ¼ de vuelta (k 0,645, R 10,7 Ω): 3,1 dBi, 0,24 dB de red, ≥ 0,9 en 17 MHz y ≥ 0,8 en 36 MHz; D 14 mm y media vuelta (k 0,729, R 2,6 Ω, el valor antiguo): 5,0 dBi pero 0,55 dB de red y ≥ 0,8 solo en 6 MHz; D ≥ 32 mm con media vuelta o D 40 mm con ¼ de vuelta no resuenan en L1 (el brazo no llega a dar la vuelta). D 32 mm y ¼ de vuelta es el más tolerante. **Efecto de una carcasa (28-11, `herramientas/carcasa_helice.py`, GPU, malla de 0,6 mm, D 32 mm y ¼ de vuelta)**: un tubo de plástico con base y tapa del mismo grosor alrededor de la hélice baja la resonancia: con PLA de 1,6 mm a 1 mm de la tira, **−6,3 %** (1490 MHz frente a 1591 sin carcasa); según la holgura entre la tira y el tubo: 0,2 mm −16 %, 0,5 mm −10 %, 1 mm −6,3 %, 2 mm −4,8 %, 4 mm −3,4 %, 8 mm −1,1 %; según la pared (a 1 mm): 0,8 mm −4,2 %, 1,2 mm −4,5 %, 2,4 mm −7,3 %, 3,2 mm −8,5 %; según el material (1,6 mm, 1 mm): PLA −6,3 %, PETG y ABS −6,6 %, PA12 −7,1 %, nailon con fibra de vidrio −9,0 %. Con malla de 1 mm los desplazamientos salen 2–4 puntos mayores (la pared cae entre líneas de malla): son orientativos, ±2 puntos. **Consecuencia práctica**: con D 32 mm el brazo ya no se puede acortar el 6 %: el brazo (k·λ/4) no llega a dar el cuarto de vuelta (`ValueError`); dentro de la carcasa hay que bajar a D ≈ 28 mm (k 0,545, R de entrada ≈ 11 Ω, red recalculada con `herramientas/red_cuadrifilar.py D=28 pared=1.6 holgura=1 er=2.715 tand=0.0071 --centrar`: RHCP 3,0 dBi en el cénit, 0,25 dB de red, eficiencia ≥ 0,9 en 19 MHz y ≥ 0,8 en 39 MHz). El plástico apenas añade pérdida (eficiencia de radiación 98 %). La tabla de holguras está en `tridimensional.CARCASA_QHA_HOLGURA`.
- Web: la web lite genera las placas y la tira, pero no tiene vista 3D.


## Barridos centrados en GPU (17-11, 2,4 GHz, FR4, `--centrar --radiacion`)

| Tipo | Parámetro | Peor S11 en banda | f res. (MHz) | G (dBi) | η | Haz (θ, φ) |
|---|---|---|---|---|---|---|
| `diedro` | ala 0° | −15,5 dB | 2421 | 2,5 | 99 % | 177°, 228° |
| `diedro` | ala 15° | −16,0 dB | 2547 | 2,4 | 98 % | 177°, 204° |
| `diedro` | ala 25° | −20,5 dB | 2616 | 2,8 | ~100 % | 3°, 252° |
| `diedro` | ala 40° | −18,2 dB | 2641 | 2,7 | ~100 % | 3°, 264° |
| `reflector_esquina` | 60° | −8,8 dB | 2458 | 9,9 | 91 % | 90°, 90° |
| `reflector_esquina` | 90° | −13,0 dB | 2403 | 10,9 | 95 % | 90°, 96° |
| `reflector_esquina` | 120° | −10,2 dB | 2854 | 10,7 | 95 % | 90°, 96° |
| `helice_normal` | altura 25 mm | −1,6 dB | 2375 | 1,8 | 84 % | 93°, 90° |
| `helice_normal` | altura 30 mm | −1,0 dB | 2219 | 1,2 | 72 % | 90°, 90° |
| `helice_normal` | altura 35 mm | −0,9 dB | 2127 | 0,9 | 67 % | 87°, 90° |

- **`diedro`**: adapta con todos los ángulos, pero cerrar la V sube la resonancia (2421 → 2641 MHz): hay que alargar los brazos. El haz y la ganancia casi no cambian con el ángulo (η > 100 % es ruido de la simulación).
- **`reflector_esquina`**: la de 90° es la mejor (−13 dB, 10,9 dBi, haz hacia +y). El −48,8 dB de la malla gruesa en CPU no era fiable.
- **`helice_normal`**: no adapta (−1 a −1,6 dB); falta calibrar `K_HELICE_NORMAL` o cambiar la alimentación.

## Calibración de las estimaciones (17-11, GPU, tamaño por defecto sin centrar)

| Tipo | Antes | Después |
|---|---|---|
| `reflector_esquina` 90° | brazo 22 mm (estimación 2675 MHz frente a 2403 simulados) | brazo 16,8 mm: 2446 MHz, −14,1 dB, 10,95 dBi (`K_REFLECTOR` 0,898) |
| `diedro` 15° / 25° / 40° | brazo 22 mm | brazo 19,8 mm: 2263 / 2296 / 2386 MHz, −10,7 / −11,6 / −14,3 dB (`K_DIEDRO_V` 0,093); sigue 2–7 % bajo: afinar con «Ajustar tamaño» |
| `helice_normal` | 2114 MHz estimados frente a 2375 | altura 23 mm: 2435 MHz, pero −2,1 dB |

La hélice normal resuena donde toca pero no adapta: su resistencia de entrada es de 3–6 Ω. Haría falta una red de adaptación (la red en L del bucle sirve de modelo) o una toma intermedia. La tira de flex de la cuadrifilar ya no deja astillas de cobre a 868 MHz (DRC limpio en los 98 casos de `comprobar_tipos.py`).

### Dipolo en V a 25°, centrado (17-11, GPU, `--centrar`)

Peor S11 −15,3 dB, resonancia 2405 MHz (1,5 % baja), 2,0 dBi, η 96 %. Con la corrección de frecuencia de `estimar_f_diedro` el tamaño por defecto queda a menos del 7 % y con «Ajustar tamaño» a menos del 2 %.