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

## Cadena de módulos en PTFE ZYF265D 1,65 mm (16-11, sin centrar)

Mismas cadenas (`barrido.py colineal_dipolos … modular=1 elementos=N --sustrato "PTFE ZYF265D 1,65 mm" --radiacion`, GPU, malla fija de
0,367 mm a 2,4 GHz y de 1,08 mm a 868 MHz) con los tamaños de `dimensionar` **sin centrar**: la resonancia sale un 10–12 % fuera de la
banda (los factores de calibración son de FR4), así que el S11 no es comparable con el de FR4; la ganancia y la eficiencia sí lo son.
Resultados en `salidas/_barridos/colineal_ptfe_24_N4`, `colineal_ptfe_24_N8` y `colineal_ptfe_868_N4`.

| Cadena | Placa (mm) | Resonancia | D (dBi) | G (dBi) | η | G en FR4 con la misma N |
|---|---|---|---|---|---|---|
| 4 módulos, 2,4 GHz | 20,5 × 362 | 2165 MHz (−11 %) | 6,6 | 6,4 | 96 % | 4,0–4,1 dBi, η 59–61 % |
| 8 módulos, 2,4 GHz | 20,5 × 752 | 2747 MHz (+12 %) | 9,0 | 8,8 | 95 % | 5,3 dBi, η 38 % |
| 4 módulos, 868 MHz | 50,5 × 1008 | 781 MHz (−10 %) | 7,3 | 7,5 (η 105 %: artefacto) | — | 4,6 dBi, η 69 % |

- **El PTFE quita el tope de 4 módulos del FR4**: con 4 y 8 módulos η se queda en el 95 % y la ganancia sube +2,4 dB al duplicar (6,4 → 8,8 dBi),
  la misma que con RO4350B (8,9 dBi con 8). En FR4, 8 módulos daban 5,3 dBi.
- A 868 MHz la η sale de 105 % (G > D): es un error numérico de la normalización del NF2FF (malla gruesa, placa de 1 m), así que la ganancia
  de 7,5 dBi es orientativa; la directividad de 7,3 dBi sí es creíble (FR4: 4,6 dBi de ganancia con η 69 %).
- El haz sale inclinado (θ 156–165° del eje de la placa, es decir, 15–24° de la normal) y con polarización circular de razón axial
  baja (RHCP a 2,4 GHz, LHCP a 868 MHz): hay que mirar si es real o un efecto de la alimentación por un extremo.
- Pendiente para dar los números por buenos: **centrar** cada cadena (acortar los tramos un 10 %: a 2,4 GHz N=4 resuena a 2165 MHz y
  N=8 a 2747 MHz, cambian en sentidos opuestos) y repetir con el tamaño centrado.

## Alternada: array de dipolos bowtie transversales (16-11, centrada, 4 dipolos, 2,4 GHz)

`barrido.py colineal_dipolos forma=1|2 conexion=1 elementos=4 --centrar --radiacion` (GPU). Resultados en `salidas/_barridos/colineal_alt_*_24_N4_c`.

| Caso | Brazo | Peor S11 en la banda | Banda a −10 dB | G (dBi) | η | Haz (θ, φ) |
|---|---|---|---|---|---|---|
| Bowtie, FR4 | 11,8 mm | −13,4 dB | 2362–2505 MHz | 2,8 | 72 % | 105°, 306° |
| Bowtie, PTFE ZYF265D 1,65 mm | 16,7 mm | −9,9 dB | 2367–2482 MHz | 6,5 | ~100 % (ruido) | 6°, 276° |
| Sierpinski it. 2, FR4 | 11,5 mm | −11,1 dB | 2388–2505 MHz | 2,5 | 71 % | 117°, 306° |

Adaptan las tres, pero solo el PTFE da el haz esperado (perpendicular a la placa). **Causa del haz casi horizontal en FR4: la separación entre dipolos.**
`tipos.estimar_f` delegaba en el dipolo bowtie, que da 3895 MHz para un brazo de 11,8 mm que en la alternada resuena a 2432 MHz (en PTFE 3086 frente a
2424). La separación λg/2 se calculaba con esa frecuencia y salía ~20 mm en vez de ~33 mm: cada dipolo quedaba desfasado ~0,37π y el haz se tumbaba hacia
el lado del conector (end-fire). En PTFE el error era menor (×0,79) y el haz salió casi bien.
Corrección: `dipolos.f_alternada` = 0,85·c/(4·L·√εr), ajustada con los puntos del centrado (FR4: L 10,5–18,8 mm; PTFE: 16,7–21 mm; ±5 %). Con ella el brazo
por defecto sale de 12,3 mm (FR4) y 16,0 mm (PTFE) y la separación de 33,3 y 41,6 mm. Repetidas en la cola (`0018a1–3`); resultados pendientes.
La razón axial de 6–13 dB y el «RHCP/LHCP» no son una polarización real: con dipolos lineales son ruido de la medida.
### Alternada con la separación corregida (16-11)

Repetidas con `dipolos.f_alternada` (`salidas/_barridos/colineal_alt_*_24_N4_c2`), 4 dipolos, centradas:

| Caso | Brazo | Peor S11 | f res. | G (dBi) | η | Haz (θ, φ) |
|---|---|---|---|---|---|---|
| Bowtie, FR4 | 13,7 mm | −8,5 dB | 2420 MHz | 2,8 | 64 % | 33°, 102° (33° hacia +y) |
| Bowtie, PTFE | 14,3 mm | −4,4 dB | 2395 MHz | 5,4 | ~100 % (ruido) | 3°, 198° (perpendicular) |
| Sierpinski, FR4 | 13,8 mm | −7,8 dB | 2464 MHz | 2,4 | 58 % | 150°, 96° (casi horizontal) |

El haz de FR4 ya no sale tumbado (antes θ 105–117°) pero tampoco perpendicular, y ninguno adapta a −10 dB tras centrar. En PTFE el haz sale perpendicular.

### Inclinación del haz (16-11, `inclinacion`, lección 86 de CLAUDE.md)

Primer estudio (`incl_*`, centrado solo en τ = 0, así que **desadaptado al inclinar**: la resonancia se mueve hasta +11 % y el S11 cae a −1…−5 dB). Haz (θ, φ) por τ:

- **Alternada bowtie PTFE N = 4:** τ = −15° → θ 177° (perpendicular por detrás); −7° → 6°; 0° → 3°; +7° → 3°; **+15° → θ 15°, φ 96° (15° hacia +y: el ángulo pedido)**. Con τ = +7° debería salir 7° y sale 3°.
- **Alternada bowtie FR4 N = 4:** −15° → θ 3° (perpendicular), −7° → 21°, 0° → 33°, +7° → 39°, +15° → 126°. En FR4 el haz sale perpendicular con τ ≈ −15°: la separación real es ~12 % más corta que la de la microstrip ideal (el índice efectivo real es mayor: arcos de brazos y acoplo).
- **Sierpinski FR4 N = 4:** confuso (−15° → θ 3°, −7° → 9°, 0° → 150°, +7° → 36°, +15° → 48°).
- **Bowtie FR4 N = 8:** τ = −10° → G −1,0 dBi, η 14 %; 0° → G 3,7 dBi, θ 18°; +10° → θ 27°. No concluyente.
- **En serie (U y bowtie, N = 4):** los máximos caen en lóbulos del plano de la placa y se mueven sin un sentido claro (la inclinación hay que medirla desde el eje de la colineal, no desde Z: `direccion_max` da un solo máximo). Con τ = ±10° baja la ganancia (U: 4,1 → 2,5 y 2,9 dBi; bowtie: 3,4 → −1,8 y 0,2 dBi).

Conclusiones provisionales: la fórmula acierta el sentido y, en PTFE, el ángulo (+15°); en FR4 el índice efectivo hay que calibrarlo (probar `factor_linea` ≈ 0,88). **Hay que centrar cada τ por separado** (el tamaño del brazo y la separación se acoplan) y medir el ángulo desde el eje de la colineal. Encoladas (`0018c1–8`, sin simular): PTFE con τ = −10, −5, 5, 10, 15° y FR4 con `factor_linea` 0,88 y τ = 0, 8, −8°, cada una con su propio centrado.
## Conclusiones

- Modularizar es viable geométricamente, y a 868 MHz resuelve un problema real (placa de 0,4–0,8 m).
- **En FR4 el tope útil es N = 4 (~4 dBi a 2,4 GHz; ~4,6 dBi a 868 MHz).** Más módulos no dan ganancia (η cae al 38–48 %).
- Con sustrato de bajas pérdidas (RO4350B, PTFE) la ganancia escala (~+2 dB por duplicación, η > 90 % hasta N = 8), a costa de precio.
  Confirmado en PTFE de JLC (16-11): 6,4 dBi con 4 módulos y 8,8 dBi con 8, η 95 % (sección anterior), sin centrar.
- Faltan: (a) centrar la frecuencia por N (el largo de tramo cambia con N), (b) modelar la unión entre módulos (discontinuidad
  y masa B.Cu), (c) el haz sale inclinado ~25° de la normal a la placa (alimentación por un extremo), (d) comprobar el
  efecto del conector/mástil. Sin medir, como todo lo demás.
- Antes de hacer el tipo, decidir con el usuario si el módulo se hace en FR4 (N ≤ 4) o también con sustratos de bajas pérdidas.


## Retardo de fase con alimentación separada (17-11, simulado en GPU, 2,4 GHz)

Resultados de `array_fase` (2 dipolos bowtie, línea de retardo en una rama) y del panel 2×2 con meandro de retardo. Ninguno inclina el haz.

**`array_fase`, FR4, tramo de 20 mm** (`0040`): el 30 mm de la primera versión era el fallo (S11 −3 dB). Ahora:

| Desfase | Peor S11 en banda | G (dBi) | η | Haz (θ, φ) |
|---|---|---|---|---|
| 0° | −12,2 dB | 3,3 | 74 % | 93°, 6° |
| +40° | −5,3 dB | 3,3 | 68 % | 99°, 6° |
| −40° | −9,6 dB | 1,8 | 74 % | 165°, 12° |
| +80° | −3,2 dB | 1,6 | 56 % | 153°, 60° |

Con 0° y +40° el haz no se mueve (φ 6°), cuando +40° debería dar ~19° hacia +y. PTFE (`0041`) no adapta (−3,6 a −6,5 dB): falta calibrar `K_ARRAY_FASE` para ese sustrato.

**Panel 2×2 con retardo** (`barrido_panel.py 2 2 18.2 … desfase=…`, FR4): la disposición sin cruce ni vías (`simetrico=0`) adapta 2,5–3,6 dB mejor que la que cruza con vías (0°: −10,3 frente a −7,8 dB; −40° entre columnas: −13,0 frente a −9,4 dB). Ganancia 12,6–12,8 dBi con cualquier desfase y haz a 0–9° del frente (esperado ~20° con ±40°). El meandro no inclina el haz ni con vías ni sin ellas.

Conclusión: el retardo de una rama, tal como está modelado, no da dirección controlada. Posibles causas aún sin separar: el meandro radia o acopla con los brazos, el retardo real difiere del de la fórmula (λg de la línea cargada), o el haz de dos elementos es demasiado ancho para que ±40° se note.

## U de Koch en la colineal (`forma = 3`, 17-11, GPU, 2,4 GHz, FR4, 4 dipolos, centrada)

Cada pata de la U es una curva de Koch de cuerda `largo_brazo` con las muescas hacia fuera (`iteracion` 1–3, estimación con la longitud equivalente `_eq_koch`, sin calibrar). Idea del usuario: acortar la colineal con patas fractales.

| Variante | Brazo (cuerda) | Placa (mm) | Peor S11 en banda | f res. (MHz) | G (dBi) | η |
|---|---|---|---|---|---|---|
| U recta (referencia) | 27,8 | 20,5 × 300,6 | −12,1 dB | 2444 | 4,05 | 58 % |
| U de Koch, iteración 1 | 20,8 | 35,0 × 247,8 | −9,8 dB | 2360 | 5,72 | 70 % |
| U de Koch, iteración 2, patas de 2,5 mm | 18,2 | — | −6,1 dB | 2817 | 5,51 | 77 % |
| U de Koch, iteración 3, patas de 2,5 mm | 15,7 | — | −3,0 dB | 2788 | 3,57 | 69 % |
| U de Koch, iteración 2, patas de 1 mm | 22,3 | 32,9 × 294,2 | −9,4 dB | 2434 | 3,59 | 55 % |

- **Iteración 1 acorta de verdad**: la placa pasa de 300,6 a 247,8 mm (−18 %) a cambio de ensancharse de 20,5 a 35 mm, con más ganancia (5,7 frente a 4,0 dBi) y η 70 %, pero con S11 de −9,8 dB (la U recta da −12,1) y la resonancia 3,5 % baja. Sin la calibración del Koch la frecuencia sale algo corta; hay que afinar con «Ajustar tamaño».
- **Iteraciones 2 y 3 con patas de 2,5 mm no valen**: la muesca (largo/3^it = 2,0 y 0,7 mm) es más fina que la pata y se funde en un bloque macizo; desadapta y el DRC de distancia falla en el módulo. El generador lo avisa (`Las muescas de Koch… se funden`).
- **Iteración 2 con patas de 1 mm** adapta (−9,4 dB) pero ya no acorta la placa (294 mm) y baja η a 55 %: la pata fina pierde más.
- La línea de λg entre dipolos es lo que más largo ocupa (la placa mide ~250–300 mm con 4 dipolos); el Koch solo acorta lo que depende del brazo, y lo que se ve aquí en la placa viene de que el brazo más corto sube la frecuencia estimada y con ella acorta los tramos. Para acortar más haría falta plegar la línea de λg (meandro), que no está hecho.
- El haz de la U recta sale a θ 156° y el de la iteración 1 a θ 3° (casi en el eje z): hay que mirar el diagrama completo antes de dar por buena la forma.

### U de Koch, iteración 1: ajuste de la línea y módulos (17-11, GPU)

| `factor_linea` | Peor S11 | f res. (MHz) | G (dBi) | η |
|---|---|---|---|---|
| 0,92 | −12,2 dB | 2293 | 5,6 | 73 % |
| 1,00 | −9,4 dB | 2257 | 5,3 | 65 % |
| 1,08 | −15,9 dB | 2548 | 5,2 | 65 % |

- Con el tamaño por defecto (sin centrar) el S11 no es monótono con el tramo de línea (0,92: −12,2; 1,00: −9,4; 1,08: −15,9), la misma sensibilidad a la malla de la lección 74. Hay que centrar cada punto.
- **En módulos no funciona**: 4 placas con `forma = 3`, iteración 1, centrada: S11 −1,4 dB, 0,5 dBi y η 43 %. La U de Koch solo vale hoy en una placa.

### Línea plegada entre dipolos: cuenta previa (17-11, sin implementar)

Idea: acortar la colineal plegando en meandro el tramo de λg entre dipolos. Con 4 dipolos a 2,4 GHz en FR4 (tamaño por defecto): tramo entre dipolos Ls = 66,6 mm, dos brazos 2·La = 47,4 mm (U recta) o 42,4 mm (U de Koch 1). Los brazos de un dipolo y los del siguiente no pueden solaparse en Y, así que **solo se puede plegar el tramo libre: 19–24 mm** por hueco (3 huecos). Un meandro de microstrip necesita ~3–5 mm entre tramos (3·h para no acoplarse), con lo que 19 mm de línea caben en ~10 mm de largo como mucho: ahorro de ~5–9 mm por hueco, **unos 15–27 mm de 258 (6–10 %)**, con riesgo de radiación y acoplo con los dipolos vecinos. **No compensa**: lo que ocupa el largo son los propios dipolos (2·La ≈ 70 % del tramo), no la línea. (Mi estimación previa de que «el tramo de línea ocupa casi todo el largo» era errónea.) Para acortar más habría que reducir el dipolo (Koch, ya probado: −9 a −18 %) o ir a una conexión alternada (λg/2, placa de 128 mm con 4 dipolos).

### Línea plegada entre dipolos: resultado (17-11, GPU, 2,4 GHz, FR4, 4 dipolos, centradas) — corrige la cuenta previa

Se implementó (`linea_plegada` = 1: un bucle en «C» de la línea en el tramo libre entre dipolos, con un parche de masa más ancho debajo; solo en una placa y en serie) y **sí compensa**, más de lo calculado antes (que daba un 6–10 %): al acercar los dipolos baja también la pérdida de la línea de FR4.

| Antena | Placa | Peor S11 | f res. (MHz) | D (dBi) | G (dBi) | η | Separación entre dipolos |
|---|---|---|---|---|---|---|---|
| U recta | 20,5 × 300,6 mm | −12,1 dB | 2444 | 6,4 | 4,05 | 58 % | ~78 mm (0,64 λ0) |
| U recta plegada | 20,5 × 216,1 mm (−28 %) | −19,7 dB | 2440 | 6,0 | 4,82 | 76 % | ~55 mm (0,45 λ0) |
| U de Koch 1 plegada | 34,2 × 194,1 mm (−35 %) | −20,6 dB | 2368 | 5,6 | 4,34 | 75 % | ~52 mm |

**Diagrama** (cortes y vista 3D con `herramientas/patrones_colineal.py` y `herramientas/patrones_colineal_3d.py`, figuras en `salidas/_vistas/colineal_patrones*.png`): la U recta y la de Koch sin plegar tienen 6–8 lóbulos casi iguales (lóbulos de rejilla: dipolos a 0,64 λ0 > λ0/2), y el máximo del barrido caía en θ 156–165°. La plegada (0,45 λ0) no los tiene: queda un anillo ancho alrededor del eje largo, con nulos a lo largo de él, como se espera de una colineal; el lóbulo principal queda a ~12° de la normal de la placa. Con el tamaño por defecto las placas miden 229 mm (U recta, −11 %) y 209 mm (Koch, −17 %): el centrado acorta el brazo y suma otro ahorro.

Lo que se aprendió: el tramo plegable es solo el libre entre brazos (19–24 mm), pero acercar los dipolos por debajo de media longitud de onda es lo que limpia el diagrama. Sin medir; el bucle no está probado con placa real.