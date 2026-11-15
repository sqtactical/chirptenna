# Colineal modular: ¿cuánta ganancia da cada módulo? (15-11-2026)

Idea: placas iguales (un dipolo y su tramo de línea de λg) que el usuario une en serie según la ganancia que quiera.
Antes de diseñar el módulo, se simuló la colineal de dipolos actual (`colineal_dipolos`) con 1 a 8 elementos, con
`herramientas/barrido.py` en GPU, malla fija de 0,63 mm (2,4 GHz) o 1,08 mm (868 MHz) y los tamaños de `dimensionar`
**sin centrar** (los S11 de N ≤ 3 y los de 868 MHz salen desadaptados: la ganancia es la de la antena en el objetivo,
sin descontar la desadaptación). Resultados crudos en `salidas/_barridos/colineal_N_24`, `colineal_N_24_ro` y `colineal_N_868`.

## 2,4 GHz, FR4 JLC 1,6 mm (η = eficiencia de radiación)

| N | Placa (mm) | Peor S11 en banda | D (dBi) | G (dBi) | η |
|---|---|---|---|---|---|
| 1 | 20,5 × 66 | −3,1 dB | 2,9 | 1,7 | 75 % |
| 2 | 20,5 × 144 | −7,8 dB | 3,6 | 1,5 | 62 % |
| 3 | 20,5 × 223 | −6,3 dB | 4,8 | 2,4 | 58 % |
| 4 | 20,5 × 301 | −12,7 dB (banda 2357–2520 MHz) | 6,4 | 4,1 | 59 % |
| 6 | 20,5 × 457 | −10,9 dB (resuena a 2191 MHz) | 7,2 | 4,0 | 48 % |
| 8 | 20,5 × 614 | −9,7 dB (resuena a 2114 MHz) | — | 5,3 | 38 % |

**La directividad sube ~+1,5 dB por módulo, pero la eficiencia cae del 75 % al 38 %**: la línea de λg en FR4 se come la
ganancia. N = 4 da 4,1 dBi (un monopolo ajustado da 3,1 dBi con η 90 %) y pasar de 4 a 6 módulos no mejora nada. A partir
de N = 6 la resonancia baja un 10 % (hay que acortar el tramo).

## 2,4 GHz, RO4350B 1,52 mm (misma geometría, sin centrar)

| N | G (dBi) | η | Peor S11 |
|---|---|---|---|
| 2 | 4,3 | 97 % | −4,2 dB |
| 4 | 6,0 | 93 % | −5,7 dB |
| 8 | 8,9 | 91 % | −8,6 dB |

Sin pérdidas la ganancia sí crece ~+2 dB por duplicación: **el límite es el FR4, no la idea**. Con RO4350B o PTFE el módulo
escala bien, aunque con tamaños de FR4 sin centrar (la resonancia sale a +10 % o −5 %).

## 868 MHz, FR4 1,6 mm (50,5 mm de ancho)

| N | Placa (mm) | Peor S11 | G (dBi) | η |
|---|---|---|---|---|
| 1 | 50,5 × 182 | −2,1 dB | 1,3 | 72 % |
| 2 | 50,5 × 402 | −5,7 dB | 1,9 | 73 % |
| 4 | 50,5 × 843 | −6,2 dB (resuena a 907 MHz) | 4,6 | 69 % |

A 868 MHz la placa de N = 4 mide 843 mm (en RETOMAR/README figuraba 722 mm), lo que sí justifica partirla en módulos de ~200 mm.
La eficiencia aguanta mejor que a 2,4 GHz (la línea pierde menos por mm) pero hacen falta 4 módulos para llegar a 4,6 dBi.

## Cadena de módulos (implementada, 15-11-2026)

`colineal_dipolos` con `modular` = 1 (y `encaje` 0/1/2): una placa por dipolo, dipolo a `y_d` del canto de abajo (así la línea que
precede al primero y no hay un tramo abierto sobrante: un primer diseño con el dipolo en el centro y la línea hasta el canto
perdía 12 puntos de η por el tramo abierto de λg/2) y tres placas: inicio (con el SMA), módulo (igual en todos los
intermedios) y final (tapa corta que acaba la línea en la barra del último dipolo). La cadena simulada es la suma de las placas
(`barrido.py … modular=1 elementos=N`):

| Cadena | Peor S11 | Banda a −10 dB | G (dBi) | η |
|---|---|---|---|---|
| 4 módulos, 2,4 GHz, FR4 (con encaje) | −12,9 dB | 2342–2541 MHz | 4,0 | 61 % |
| 2 módulos, 2,4 GHz, FR4 | −8,5 dB (sin centrar) | — | 1,9 | 65 % |
| 4 módulos, 868 MHz, FR4 (sin centrar) | −5,6 dB, resuena a 1034 MHz | — | 3,9 | 69 % |

Encaje (`encaje`): 1 = dos lengüetas rectangulares de 3 × 3 mm en el canto de arriba, que entran en ranuras con 0,15 mm de holgura en
el canto de abajo del siguiente (alinean), 2 = cola de milano (cuello 2,0 mm, punta 3,6 mm: sujeta al tirar). El cobre va a ≥ 0,5 mm del
borde también junto a las ranuras. La simulación no incluye las muescas (despreciables) ni la unión soldada.
Exportación: una carpeta por placa (`modulos/<inicio|modulo|final>`) con Gerber, KiCad y DRC (limpio), más la cadena entera en una sola placa.
Aperturas de máscara de 3 mm en cada canto de unión y un pad GND sobre la tira de masa de las placas sin conector (evita `isolated_copper`).

## Conclusiones

- Modularizar es viable geométricamente, y a 868 MHz resuelve un problema real (placa de 0,4–0,8 m).
- **En FR4 el tope útil es N = 4 (~4 dBi a 2,4 GHz; ~4,6 dBi a 868 MHz).** Más módulos no dan ganancia (η cae al 38–48 %).
- Con sustrato de bajas pérdidas (RO4350B, PTFE) la ganancia escala (~+2 dB por duplicación, η > 90 % hasta N = 8), a costa de precio.
- Faltan: (a) centrar la frecuencia por N (el largo de tramo cambia con N), (b) modelar la unión entre módulos (discontinuidad
  y masa B.Cu), (c) el haz sale inclinado ~25° de la normal a la placa (alimentación por un extremo), (d) comprobar el
  efecto del conector/mástil. Sin medir, como todo lo demás.
- Antes de hacer el tipo, decidir con el usuario si el módulo se hace en FR4 (N ≤ 4) o también con sustratos de bajas pérdidas.
