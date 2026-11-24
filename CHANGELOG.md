# Cambios · Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones con
[versionado semántico](https://semver.org/lang/es/). *English summary under each version.*

## [Sin publicar]

*English summary: the interface, the web version, the README file in the download and the manuals no longer say that everything is validated only in simulation: they now say "almost everything" and mention the measured boards.*

### Corregido (24-11)

- Espiral y torniquete: el pad de masa del coaxial quedaba a 0,15 mm del taladro y el DRC de KiCad 10.0.8 daba
  `hole_clearance` (la CI falló en `66a727c`); ahora queda a 0,30 mm.

### Documentación (24-11)

- La interfaz, la web, el LÉEME del zip, `MANUAL.md`/`MANUAL.en.md` y `CONTRIBUTING.md` dicen ahora «casi todo validado
  solo en simulación» y citan las medidas del 22-11 (cupones A y B, monopolo de Sierpinski +1,0 %, Yagi +3,6 %).
- `RETOMAR.md` reescrito con el estado del 24-11 (lo anterior pasa a `docs/desarrollo/historial.md`) y `ROADMAP.md` al
  día con las tareas de las fases 3 y 4 hechas el 12-11.

## [0.6.0-alpha] · 2026-11-24

*English summary (0.6.0-alpha): a 3D enclosure generator with material, closure and screw options that is also simulated; plastic-property measurement with open stubs read in S11 (cupón C) for ordinary NanoVNAs; a receive-only (RX) gallery group with new GNSS, ADS-B and UAT bands; fourteen new planar and multi-board types (folded dipole, Moxon, log-periodic, slot, spiral, turnstile, UWB monopoles, circularly polarised patch, series array, SIW, crossed Yagi, dual-band Yagi), most of them still not validated. Simulated results at 2.4 GHz: slot −28.6 dB (η 73 %), folded dipole −16.4 dB, log-periodic −22.7 dB, and a large spiral (27.7 mm radius) with a 3.5 nH series coil that gives circular polarisation (axial ratio ~1 dB) and −19.8 dB across the band. The turnstile, the Moxon and the series array do not work yet. First real measurements (22-11, NanoVNA): coupons A and B and two manufactured antennas, a Sierpinski monopole (resonates 1.0 % above the simulation) and a Yagi (+3.6 %, half the simulated bandwidth); the new types of this release are still simulation-only.*

### Tipos nuevos y optimizaciones (23–24-11)
- **Grupo «Solo recepción (RX)»** en la galería (espiral, torniquete, monopolo UWB, UWB coplanar, parche de polarización circular, hélice cuadrifilar) y bandas nuevas: UAT 978 MHz, ADS-B 1090 MHz, GPS L5 y GNSS L1. Centradas en GPU con monopolo, dipolo, bowtie y sleeve (peor S11 en la banda: el bowtie va de −19 a −28 dB en las cuatro; el monopolo y el dipolo recto quedan justos).
- **Tipos planares** (`antenas/planares.py`, sin validar salvo lo dicho): dipolo plegado (−16,4 dB), Moxon, log-periódica (−22,7 dB), antena de ranura (optimizada: −28,6 dB, η 73 %), espiral, torniquete, monopolo UWB (disco de Ray, rectángulo, rectángulo biselado; −18 dB y 1763–3418 MHz a 2,4 GHz), **UWB coplanar** (`uwb_cpw`; no se simula: falta el puerto coplanar), `parche_cp`, `array_serie` y `antena_siw`. Con simulación a 2,4 GHz: el torniquete adapta pero no es circular (razón axial 11–13 dB, aunque se recentre el largo), el Moxon no adapta (R de 15–25 Ω; el nuevo `z_transformador` no lo arregla), `array_serie` no pasa de −7 dB (η 30 %) y la SIW adapta (−16,9 dB) con η 12 %.
- **Espiral con bobina en serie**: con el radio grande (28 mm a 2,44 GHz, antes 14,6) la espiral da polarización circular (razón axial 0,9–1,5 dB, RHCP delante y LHCP detrás, η 86 %) pero queda capacitiva; el parámetro nuevo `bobina_nH` (3,5 nH por defecto, escala con λ) se aplica por circuito sobre la impedancia simulada (`simulacion.aplicar_bobina_serie`) y deja −19,8 dB en 2,4 GHz y la banda a −10 dB de 1677 a 3036 MHz. `herramientas/espiral_l.py`. Sin comprobar con FDTD ni medida.
- **Yagi en cruz** (`yagi_cruz`): dos Yagi con boom encajadas en perpendicular por una ranura de h + 0,2 mm (la vertical entra por delante), dos conectores, el dipolo vertical queda ~87° de fase por delante del horizontal. Solo geometría, vista 3D y exportación por placa (DRC limpio); no se simula (dos puertos).
- **Yagi bibanda** (`yagi_bibanda`): dos Yagi con boom en una placa, 2,4 + 5,8 GHz (razón de bandas configurable), con la misma línea de 50 Ω; los directores de la banda baja van más allá del final de la línea. Solo geometría; sin simular.
- **Primeras medidas reales (22-11, NanoVNA, calibración completa de 50 kHz a 2,7 GHz)**: cupones A y B (stubs repetibles al 0,03 % en el S80; el S30 sale un 6 % por encima de la simulación y la εr del FR4 queda entre 4,5 y 5,0), y dos antenas fabricadas: el monopolo de Sierpinski resuena a 2502 MHz (+1,0 % frente a lo simulado, −34 dB) y la Yagi de 2 directores a 2534 MHz (+3,6 %, −12,1 dB, banda de 88 MHz frente a 166 simulados). Detalle en `docs/desarrollo/placas_pedidas_2G4.md` y `docs/desarrollo/medidas/`.
- Barridos: `barrido.py` acepta `--sustrato` y factores `xN` en rejilla; campañas de optimización `OPT_*`, `FUNC_*`, `NUEVO_*` (resultados en `salidas/_barridos/`, locales).
- Traducciones en/fr/de completas (1686 textos) y miniaturas nuevas; 323 pruebas.

### Cupón C con stubs abiertos en S11, para NanoVNA normales (22-11)
- Los NanoVNA normales llegan a 900 MHz y el anillo de 868 MHz no servía (su pico simulado era una joroba ancha entre dos ceros; la simulación paraba antes de tiempo con el criterio por defecto de openEMS). El cupón C pasa a **tres stubs abiertos de 43, 59 y 86 mm medidos en S11** (resonancias de 450 a 2625 MHz con los armónicos), con tiras de 24 mm de ancho y cuatro taladros M3 por stub. Ya no hace falta S21.
- `cupon/simular_stub.py` (openEMS 3D, 12–25 s por caso en GPU); 42 casos con muestra: la εr se recupera a ±1,1 % rms (3,3 % máx) con una corrección de cuatro coeficientes. La tanδ (desde la R en la resonancia) queda sin validar: solo vale por encima de ~0,03.
- `plastico.py`: `resonancias_stub`, `elegir_resonancia`, `medir_stub`, `tand_stub`, `er_fr4_stubs` (con varios stubs se elimina la longitud eléctrica del conector); solver con muestra de ancho finito. Los asistentes de Chirptenna y de Chirptenna VNA (que usa la última medida de S11 de la página) pasan a stubs. Detalle en `docs/desarrollo/plasticos.md`.

### Frecuencia y aviso de materiales genéricos (22-11)
- La carcasa usa la εr y la tanδ del material **a la frecuencia del diseño** (carcasa.propiedades(c, f_Hz)): la tabla es a 2,4 GHz y para otra frecuencia se aplica una tendencia genérica (εr +3 % por década hacia abajo, tanδ ∝ f^0,3; a 868 MHz, +1,3 % y −27 %), acotada a 0,3–6 GHz. Es una suposición: no hay medidas de estos filamentos a 868 MHz que se hayan encontrado. El material «Personalizado» no se escala.
- Aviso permanente bajo el selector («valores GENÉRICOS … mide el tuyo») y tras cada simulación con material de tabla; la interfaz enseña la εr y la tanδ que se usan a la frecuencia del diseño.

### Más materiales para la carcasa (22-11)
- Materiales: PLA, PETG, ABS, ASA, PC, PA12, PA6 y con fibra de vidrio (PLA-GF, PETG-GF, ABS-GF, PA-GF), con εr y tanδ típicas de hoja técnica (sin medir) y un parámetro **Relleno (%)** que baja la εr efectiva (mezcla con aire por índices de refracción). Sin fibra de carbono, grafito ni filamentos conductores o ESD: son conductores y apantallan la antena. «Personalizado» sigue siendo lo medido (cupón C), sin corrección de relleno.

### Medir las propiedades de un plástico (21-11)
- **Cupón C** (`python cupon/generar_cupon.py C` → `cupon/cupon_C/`, DRC limpio): los anillos de 868 MHz y 2,4 GHz del cupón A con la zona de la muestra marcada en la serigrafía (66 × 66 y 30 × 30 mm) y cuatro agujeros M3 para sujetarla. Se mide el pico de S21 de un anillo sin muestra y con el plástico encima.
- `antenas/plastico.py`: solver cuasiestático 2D de la sección (numpy; εeff dentro del 0,3 % de Hammerstad) y la inversión: εr de la muestra a partir del cociente de frecuencias y tanδ a partir de los Q, con incertidumbre (resolución de f, grosor, εr del FR4). `parametros_pico` saca f, pérdida, ancho a −3 dB y Q de una curva de S21.
- Fabricar → Carcasa → «Medir el plástico con el cupón C»: calcula εr y tanδ y los lleva al material **Personalizado** (εr y tanδ propias) de la carcasa.
- `cupon/simular_anillo.py --muestra εr,tanδ,grosor,lado` y GPU: simula el anillo con la muestra en openEMS para comparar.
- **Asistente de materiales** (Medir): qué medir (un plástico o el FR4 del cupón), preparar (STL de las muestras de 2, 3 y 4 mm con cuatro taladros M3: `plastico.muestras_stl`), medir sin y con muestra (sube un `.s2p`/CSV de S21 y busca el pico y el Q, o se escriben) y resultado con incertidumbre, que se lleva a la carcasa o al sustrato del diseño.
- **Validación en 3D**: el modelo 2D sobreestimaba la εr (+8 a +16 %); una corrección ajustada a 7 simulaciones de openEMS la deja a ≤ 1 % de la real, también en un caso que no entró en el ajuste. Solo para el anillo de 2,4 GHz, εr 2–10 y grosor 1,5–4,5 mm (fuera, avisa). Anillo de 868 MHz sin validar (docs/desarrollo/plasticos.md).
- Chirptenna VNA: el mismo cálculo en JS (`js/plastico.js`, probado contra los números de Python) y su asistente (`js/materiales.js`). Mide solo S11: el S21 se sube de un archivo.

### Carcasa 3D (21-11)
- `antenas/carcasa.py`: STL de la base y la tapa (reborde de apoyo, labio, orejetas para tornillos, abertura del conector; tapa boca abajo) para antenas de una placa plana; material PLA/PETG/ABS.
- Simulación: casilla «Ajustar y simular con la carcasa del diseño». `simulacion.ENTORNO_FIJO` (puesto por `simular_cli`) añade los bloques de la carcasa a toda simulación, también a las del ajuste; `resultado.json` guarda `carcasa` (frecuencia con y sin ella, con la misma malla).
- El diseño guarda los parámetros de la carcasa (`diseno.json` → `carcasa`).
- Cierre elegible: tornillo autorroscante, tornillo y tuerca (hexágono por debajo), tornillo e inserto de latón, o pegada; tornillos M2, M2,5 y M3. La simulación incluye las orejetas de plástico y el metal (cabeza, caña, tuerca o inserto) y da, además, la frecuencia con la carcasa sin su metal, para separar lo que pone el plástico de lo que ponen los tornillos.

### Conexión con Chirptenna VNA (20-11)
- Cada simulación guarda también `s11_simulado.s1p` (Touchstone RI, 50 Ω): el navegador no lee `datos.npz`, y así la web Chirptenna VNA puede cargarlo como referencia y superponerlo a la medida.
- Pestaña Medir: botón «.s1p simulado» (descarga) y «Abrir Chirptenna VNA» (abre la web con `?f=<MHz>&banda=<ini>-<fin>&nombre=<diseño>`; dirección en `CHIRPTENNA_VNA_URL`, por defecto `http://localhost:8765/`). Aviso: solo una de las dos aplicaciones puede tener el puerto del NanoVNA.
- En Chirptenna-VNA, `leerObjetivoUrl` (`js/puente.js`) lee esos parámetros y fija el objetivo.
- Pruebas de contrato en los dos repos (`pruebas/test_puente_vna.py`; `pruebas/expertos2.test.mjs`).

## [0.5.0-alpha] · 2026-11-17

*English summary (0.5.0-alpha): five new antenna types (V dipole, corner reflector, normal-mode helix, quadrifilar helix geometry, two-dipole array with a delay line), multi-board antennas with 3D poses, a beam-tilt study (series-fed tilt, delay-line array and delay-line 2×2 panel: none steers the beam in simulation), the alternating colinear array, a 3D view, Bayesian sweeps, thin-wire method-of-moments preselection, MATLAB as a second engine and custom substrates. GPU-centred results at 2.4 GHz: corner reflector −14 dB and 10.9 dBi, V dipole −15 to −20 dB, normal helix does not match (low radiation resistance). Still simulation-only: no manufactured board has been measured.*

- **Colineal con línea plegada (`linea_plegada` = 1, 17-11, simulada en GPU):** un bucle en «C» de la línea en el tramo libre entre dipolos los acerca de 78 a 55 mm (de 0,64 a 0,45 λ0). La U recta pasa de 301 a 216 mm (−28 %), de −12,1 a −19,7 dB y de 4,05 a 4,8 dBi (η 58 → 76 %); con U de Koch, 194 mm (−35 %), −20,6 dB y 4,3 dBi. El diagrama mejora: desaparecen los lóbulos de rejilla (6–8 lóbulos con la recta) y queda un anillo alrededor del eje largo. Una placa y en serie; sin medir. `herramientas/patrones_colineal.py` y `patrones_colineal_3d.py` dibujan los cortes y la vista 3D.
- **Colineal con U de Koch (`forma = 3`, 17-11, simulada en GPU):** cada pata de la U es una curva de Koch (`iteracion` 1–3, muescas hacia fuera). La iteración 1 acorta la placa un 18 % (300,6 → 247,8 mm, a costa de 35 mm de ancho) con 5,7 dBi y η 70 % frente a 4,0 dBi y 58 %, pero S11 −9,8 dB frente a −12,1. Las iteraciones 2 y 3 con patas de 2,5 mm se funden en un bloque macizo (el generador avisa). Detalle en `docs/desarrollo/colineal_modular.md`.
- **Calibración de las estimaciones 3D (17-11, GPU):** el reflector de esquina de 90° sale centrado con el tamaño por defecto (brazo 16,8 mm: 2446 MHz, −14,1 dB, 10,95 dBi; `K_REFLECTOR` 0,898). El dipolo en V sube la frecuencia al cerrar la V (+6 % a 15°, +9 % a 40°) y la estimación lo compensa (`K_DIEDRO_V`); con el brazo por defecto queda a ≤ 7 % (−10,7…−14,3 dB). La hélice normal queda a 2435 MHz pero no adapta (−2 dB: su resistencia de entrada es de 3–6 Ω, hace falta una red de adaptación).

*English summary: ideas taken from the open-source antenna-forge project: Bayesian optimisation for the sweeps, a minimal thin-wire method of moments to pre-select dipoles and Yagis in seconds, textbook checks of the generator (unit tests and a real openEMS run), a generated one-page status, and MATLAB (Antenna Toolbox, method of moments) as an optional second simulation engine in the interface, shown next to openEMS. Nothing here changes a design; everything is still simulation-only.*

- **Antenas 3D simuladas y centradas en GPU (17-11):** `diedro` adapta de 0° a 40° (−15…−20 dB, la resonancia sube con el ángulo), `reflector_esquina` a 90° da −13 dB y 10,9 dBi, `helice_normal` no adapta (−1 dB). Detalle en `docs/desarrollo/tridimensional.md`.
- **Resultado del retardo de fase (17-11, simulado):** ni el panel 2×2 con meandro (con y sin vías) ni `array_fase` inclinan el haz (0–9° con ±40°; esperado ~20°). Sin vías el panel adapta 2,5–3,6 dB mejor; `array_fase` en FR4 con tramo de 20 mm adapta (−12 dB), en PTFE no. Detalle en `docs/desarrollo/colineal_modular.md`.
- **Retardo de fase en el panel 2×2 (17-11, sin validar):** parámetros `desfase` (−120…120°) y `plano_desfase` (entre columnas o entre filas) del panel de dipolos: un meandro de retardo en las ramas de los dos dipolos de un lado inclina el haz (sen τ = Δφ·λ/(2π·d)). La red corporativa del panel (ramas independientes) evita el acoplo por línea común que arruinó la inclinación de la colineal. DRC limpio; simulaciones en cola.
- **Array de dos dipolos bowtie con línea de retardo (`array_fase`, 17-11, sin validar):** cada dipolo con su propia línea de 50 Ω desde un solo conector (T con transformador λ/4) y un meandro de retardo en una rama; el desfase (−120…120°) inclina el haz (sen τ = Δφ·λ/(2π·d)). Sustituye a la idea de inclinar la colineal en serie, que no concluyó porque los dipolos se acoplan por la línea común (el estudio de `inclinacion` dio S11 −1…−8 dB y ángulos que no seguían la fórmula). Exporta con DRC limpio; simulaciones encoladas.
- **Inclinación del haz de la colineal (16-11, sin validar):** parámetro `inclinacion` (−30…30°) que alarga o acorta los tramos de línea entre dipolos para inclinar el haz como una sectorial de telefonía con inclinación fija (un solo conector, sin desfasadores); sirve en serie, alternada y modular. La fórmula usa la εeff de la microstrip y no está calibrada; estudio de simulación encolado.
- **Antenas de varias placas no coplanares y hélices (16-11, sin validar):** cuatro tipos nuevos, `diedro` (dipolo bowtie en V con tres placas soldadas), `reflector_esquina` (dipolo bowtie delante de dos placas reflectoras), `helice_normal` (monopolo helicoidal de flex enrollado sobre una placa de masa) y `helice_cuadrifilar` (solo geometría, vista 3D y tira de flex). Base nueva: `Antena.placas3d` (placas con pose, `antenas/pose.py`), `Antena.hilos3d` (hilos en el espacio) y `Antena.cobre_sim` (cobre continuo en la simulación y con separación al fabricar); `simulacion.simular` las simula (placas giradas como losas PEC de una celda, hilos con `AddCurve`; una lámina de grosor cero girada desaparece de la malla) y `vista3d` las dibuja. Simulado a 2,4 GHz (malla gruesa, sin centrar): el dipolo en V con 0° da lo mismo que el bowtie plano (−23,9 dB), con 25° −36 dB; el reflector de esquina −48 dB y 10,3 dBi de frente; la hélice normal −6,4 dB. Exportación por placa con DRC limpio. Detalle en `docs/desarrollo/tridimensional.md`.
- **Colineal alternada, separación corregida (16-11, sin commit):** la primera simulación (bowtie y Sierpinski en FR4, bowtie en PTFE) adaptó en 2,4 GHz, pero en FR4 el haz salía casi horizontal (θ 105–117°, 2,5–2,8 dBi). Causa: la estimación delegaba en el dipolo bowtie (3895 MHz para un brazo que resuena a 2432 MHz) y la separación λg/2 quedaba un 40 % corta. Nueva dipolos.f_alternada (0,85·c/(4·L·√εr)); brazo por defecto 12,3 mm (FR4) y 16,0 mm (PTFE), separación 33,3 y 41,6 mm. Repetidas en la cola; resultados pendientes.
### Optimización bayesiana en los barridos
- `antenas/optimizacion.py`: proceso gaussiano y mejora esperada en numpy (sin scipy ni dependencias nuevas; no va en la web). Determinista: con la misma semilla, un barrido cortado repite los mismos puntos y recupera los ya simulados.
- `herramientas/barrido.py --modo bayes [--evals N] [--iniciales N] [--semilla N]`: en un parámetro continuo se dan el mínimo y el máximo (`alto=x0.8,x1.2`); en uno discreto, la lista de valores. Cada punto nuevo sale de lo ya simulado, en vez de recorrer la rejilla entera (N^d simulaciones).

### Preselección con hilos (método de momentos)
- `antenas/hilos.py`: Pocklington con base triangular y Galerkin para hilos finos paralelos en el aire (impedancia, corrientes, diagrama, directividad). Dipolo de λ/2: 86 + j46 Ω con radio 0,001 λ y resonancia a 0,476 λ; Yagi de 3 elementos de Balanis: 8–9 dBi y delante/atrás > 8 dB.
- `herramientas/preseleccion_hilos.py dipolo|yagi`: largo resonante del dipolo y rango de `factor_reflector`, `separacion_reflector`, `factor_director` y `separacion_director` de una Yagi (unos 10 s) para acotar el barrido `yagi_boom` de openEMS. No modela el FR4 ni la pista de alimentación: acota, no sustituye.

### Comprobaciones contra la teoría
- `pruebas/test_verdad.py` (22 pruebas, sin simular): microstrip de Hammerstad, largo del dipolo y del monopolo en λ, parche contra el modelo de la cavidad y coherencia de `dimensionar` con `estimar_f`.
- `herramientas/verdad.py`: simula con openEMS un dipolo, un monopolo y un parche a 2441,75 MHz y los compara con el libro (fuera de la CI: tarda minutos).

### Vista 3D de la antena
- Pestaña **Diseño**: conmutador **2D / 3D** sobre el dibujo. La vista 3D muestra la placa con su grosor (el grosor se exagera en placas largas y se avisa), el cobre de las dos caras, las vías, el conector y el reflector a su distancia real. En antenas modulares, la casilla **Explosionada** dibuja cada placa a fabricar por separado, en orden y con su cantidad; sin ella, la antena armada con las uniones marcadas.
- Pestaña **Simulación**: el diagrama de radiación 3D se dibuja sobre la placa en sus proporciones reales (también modular o con reflector), con la dirección del máximo.
- `antenas/vista3d.py`; 32 pruebas nuevas (todos los tipos se dibujan) y 11 textos traducidos. Sin versión web todavía.

### Colineal de dipolos con brazos bowtie
- **Conexión alternada**: parámetro nuevo «Conexión de los dipolos» (`conexion`): «En serie» (la de siempre) o «Alternada (vivo de uno a masa del siguiente, λg/2)». La alternada es un array de dipolos bowtie con los brazos a los lados de la línea (como el dipolo bowtie), a media longitud de onda y con los brazos cambiados de cara en cada dipolo, sin vías: la placa es más corta (21 × 128 mm a 2,4 GHz con 4 dipolos) y el haz sale perpendicular a la placa, no omnidireccional. Con su parámetro «Apertura de la bowtie». Solo con bowtie o Sierpinski y en una placa; sin simular todavía.
- La forma «Bowtie de Sierpinski» (triángulo con huecos fractales, con su iteración) también está disponible en la colineal; `herramientas/imagen_colineal.py` dibuja las tres formas.
- `colineal_dipolos` tiene el parámetro **Forma de los brazos**: «U (dos patas)» (la de siempre) o «Bowtie (triángulo)», que ocupa el mismo ancho y da más banda por dipolo. Funciona en una placa y en modular; el DRC de KiCad sale limpio a 868 MHz y 2,4 GHz. El tamaño inicial de la bowtie no está calibrado (~10 % más corto): se afina con «Ajustar tamaño a la frecuencia». Sin validar en simulación todavía.

### Sustrato personalizado y PTFE de JLC
- Opción **Personalizado…** en el selector de sustrato (escritorio y web): εr, tanδ y grosor del material que se vaya a usar (un PTFE o un Rogers que no está en la lista). Se guarda en el nombre del sustrato, así que funciona con guardar, simular y exportar como cualquier otro.
- Los cuatro PTFE de JLC (ZYF255DA, ZYF265D, ZYF300CA-C y ZYF300CA-P) tienen ahora cinco grosores (se añaden 0,76 y 1,52 mm) y la tolerancia de εr del datasheet (±0,04 / ±0,05, un 1,5–1,7 %): «Analizar tolerancias» la usa en vez del ±5 % del FR4.
- 22 pruebas nuevas y 10 textos traducidos.

### MATLAB como segundo motor de simulación
- Selector **Motor** en la pestaña Simulación: *openEMS*, *MATLAB (Antenna Toolbox)* u *openEMS + MATLAB* (aparece activo solo si hay MATLAB con la Antenna Toolbox). Con los dos, el S11 de ambos va superpuesto y se informa de la diferencia de frecuencia y directividad (coinciden si ≤ 5 % y ≤ 1 dB).
- `antenas/simular_matlab.py` y `herramientas/verdad_caso.m`: la placa del proyecto se simula con el método de momentos de MATLAB (`pcbStack`). Sin ajuste, ganancia ni eficiencia; solo placas sencillas con alimentación en el borde; resultados en caché. `simular_cli` acepta `motor`.
- `herramientas/verdad_matlab.py`: compara dipolo, monopolo y parche entre MATLAB y `herramientas/verdad.py`. Dipolo y monopolo coinciden en directividad (≤ 0,3 dB) con la frecuencia 3–9 % más alta en MATLAB; el parche no concuerda (2,6 frente a 6,2 dBi): su directividad en MATLAB no es fiable.
- 9 pruebas nuevas (sin MATLAB, con su salida simulada) y 34 textos traducidos a en/fr/de.

### Estado real y fallos mudos
- `docs/ESTADO_REAL.md`, generado por `herramientas/estado_real.py` desde `problemas.ESTADO`: qué está medido (nada), qué solo simulado, límites y comprobaciones. `pruebas/test_estado_real.py` falla si se desfasa.
- `simulacion.simular` ya no se traga el fallo del cálculo de la polarización: lo anota en los avisos. Revisado el resto de `antenas/`: no hay otro `except` que oculte un resultado.

## [0.4.1-alpha] · 2026-11-16

*English summary: modular collinear (one board per dipole, start / module / end boards joined edge to edge, with optional tabs-and-slots or dovetail fit, solder-mask openings and per-board Gerber and DRC, also in the web version); new README screenshots and manual (getting-started chapter, screenshots, language/theme/GPU/web chapter). Simulated only: the soldered junction between boards is neither simulated nor measured, and nothing has been measured on a manufactured board.*

### Colineal modular
- `colineal_dipolos` con **Construcción = módulos**: una placa por dipolo (inicio con el conector, módulo igual para los intermedios y una final corta) que se unen por el canto, con aperturas de máscara para el estaño, **encaje** opcional (lengüetas y ranuras, o cola de milano) y exportación de cada placa con su Gerber y su DRC (también en la versión web). Simulada la cadena a 2,4 GHz: 4 módulos −12,9 dB, 4,0 dBi, η 61 % en FR4; más de 4 no suben la ganancia (ver `docs/desarrollo/colineal_modular.md`). La unión soldada no está simulada ni medida.

### Documentación
- Capturas del README rehechas con la interfaz nueva (`herramientas/capturas_readme.py` las regenera).
- Manual (castellano e inglés): capítulo «Primeros pasos» de 10 minutos, capturas en Diseño, Simulación, Fabricar y Medir,
  capítulo nuevo «Idioma, tema, GPU y versión web», más problemas frecuentes y términos en el glosario.

### Interfaz
- El asistente del NanoVNA ya no sale con el fondo gris de Quasar: usa los colores del tema.

## [0.4.0-alpha] · 2026-11-13

*English summary: integrated antennas (the antenna as a corner of your product board, with KiCad footprint and keep-out, RF pad, KiCad board import, 4-layer JLC stack, case/hand/battery environment and manufacturing-tolerance analysis), matching network by circuit and parts list, simulated lumped components, PDF report, pattern CSV export and a redesigned interface (indigo with ENIG-gold accents, light and dark). Still validated in simulation only: no manufactured board has been measured. Known gaps are listed under each item.*

### Añadido

- **Antena integrada en una placa** (F3.1, `antenas/integracion.py`): IFA, monopolo recto, de Koch y en meandro pueden ser una esquina de la
  placa de tu producto. Parámetros `integrada`, `placa_x`, `placa_y`, `posicion` (esquina izquierda, derecha o centrada), `zona_x`, `zona_y`
  y `margen_zona`: la masa ocupa toda la placa menos la zona de antena (sin cobre en ninguna capa) y el conector se queda en el borde
  opuesto para medir el prototipo. Si algo no cabe, el error dice cuántos mm faltan. Interfaz de escritorio y web.
- **Interfaz renovada**: nueva paleta con fondo índigo y acentos dorados (tipo ENIG) en claro y oscuro, cabecera con degradado y logo, pestañas en píldora, tarjetas redondeadas con borde, campos con contorno y una
  portada en la galería («Diseña la antena de tu placa»). Inspirada en compilador.albacetemesh.es. Comprobada en escritorio y móvil.
- **Exportar el diagrama** (F4.6, `antenas/diagrama.py`): «Exportar diagrama (CSV)» en Simulación (θ, φ, directividad y ganancia en dBi); el máximo coincide con el del resultado.
- **Informe en PDF** (F4.5, `antenas/informe.py`): botón «Informe en PDF» en Fabricar con la portada y la vista, los parámetros, los problemas conocidos y los consejos y, si el diseño
  tiene simulación, S11, ROE, Smith, diagrama, ganancia, eficiencia, tolerancias, entorno y red de adaptación. En castellano, inglés, francés y alemán.
- **Asistente de ajuste con piezas y tolerancias** (F4.3, en parte): con una medida, además de la red en π propone la lista de piezas (descripción, sin números de pieza), el S11
  por circuito, la banda que quedaría y el peor caso con componentes ±5 %. Falta probarlo adaptando una antena real.
- **Componentes de la red en π en la simulación** (F4.1, en parte): parámetros `z1`, `z2`, `z3` («C 1,2 pF», «L 3,9 nH», «0R») en los monopolos con red en π (de momento solo desde
  `diseno.json` o el código, no desde la interfaz). El serie y las bobinas a masa van a la FDTD (S11 a ±0,5 dB del circuito); los condensadores a masa, por circuito. Con la red calculada
  por F4.2 la FDTD da −10,3 dB y el circuito −38 dB: falta llevar los parásitos del montaje al circuito.
- **Red de adaptación por circuito** (F4.2, en parte): «Calcular red de adaptación» en Simulación (monopolos con red en π) da las piezas E24 (Z1 en serie y derivación a masa), el S11
  con ±5 % de tolerancia y la banda que se mantiene, a partir de la impedancia simulada y sin otra simulación.
- **Sustrato de 4 capas** (F3.5): «FR4 JLC 4 capas 1,6 mm» (apilado JLC04161H-7628) para antenas integradas (IFA y monopolos): línea de 50 Ω de 0,4 mm sobre la masa de In1.Cu, masa en
  In1.Cu, In2.Cu y B.Cu, apilado en el `.kicad_pcb` y capas internas en el Gerber. IFA de 30 × 50 mm a 2,4 GHz: 2418 MHz (2 capas: 2465), banda 205 MHz, S11 −19 dB, η 86 %.
  La εr sale de una transcripción de la calculadora de JLC: compruébala antes de fabricar.
- **Importar la placa de tu producto** (F3.6, `antenas/sexp.py` y `antenas/importar_kicad.py`): en el modo integrado del escritorio, «Importar la placa de tu producto (.kicad_pcb)» lee el
  contorno (con arcos y recortes), el cobre, los taladros y el grosor; la antena se coloca en el borde superior (con «Girar 90°» eliges lado), el cobre importado es la masa y avisa del cobre
  que haya en la zona de antena. Probado con una placa exportada por el programa y una en L escrita a mano; falta una placa real.
- **Reglas de integración y manual** (F3.10): categoría de consejos «integración» (🧩) con las antenas integradas (masa continua, zona vacía, vías de
  cosido cada λ/20, distancia a batería y blindajes, línea de 50 Ω corta, red en π junto al chip) y capítulo 14 del manual («Integrar la antena en tu
  placa», en castellano e inglés) con el caso del nodo LoRa de 868 MHz: en 40 × 80 mm no cabe, y explica qué hacer.
- **Tolerancias de fabricación** (F3.9): «Analizar tolerancias» en Simulación simula con εr ±5 %, grosor ±10 % y cobre ±0,05 mm y dice si la banda
  sigue cubierta (monopolo recto de 2,4 GHz: cubre, ~2,2 %; parche rectangular: no cubre, la εr sola lo saca de la banda).
- **Entorno en la simulación** (F3.7): «Entorno» en Simulación (carcasa de ABS, batería metálica, mano) simula la antena con y sin esos bloques con la
  misma malla y dice cuánto cambian la frecuencia, la eficiencia y la ganancia (monopolo de 2,4 GHz: carcasa −6,6 %, mano −3,7 % con η de 97 a 23 %).
- **Pad de RF** (F3.4): nuevo valor del parámetro «Conector» sin conector: la línea de 50 Ω acaba en un pad con dos vías de masa a los lados, para
  llegar a él con la línea de tu producto (la red en π, si se activa, va junto al pad). Sin línea CPWG ni punto de prueba U.FL todavía.
- **Huella para integrar** (F3.3): con una antena integrada, el export añade `Antenas.pretty/<nombre>_integrar.kicad_mod` (zona de exclusión
  en todas las capas de cobre, pad pasante de la vía a masa y marca del borde de placa) y `<nombre>_ejemplo_integrada.kicad_pcb` (placa con
  masa y la huella en su esquina; DRC limpio). También en la web (zip con LÉEME de pasos) y en la interfaz de escritorio.
- **Barrido de la IFA integrada** (F3.2, `docs/desarrollo/integracion_ifa.md`): a 2,4 GHz se centra en 2–4 simulaciones con placas de 25 × 40 a
  80 × 120 mm y la banda crece con la placa (124 → 314 MHz); el meandro integrado no adapta. Consejos nuevos para la antena integrada.
- **Pruebas con pytest** (`pruebas/test_nucleo.py`, `requirements-dev.txt`): Koch, Sierpinski, microstrip de 50 Ω, redes en L,
  `dimensionar`/`estimar_f` de todos los tipos a 868 y 2441,75 MHz y el bucle; 68 pruebas en menos de 1 s, también en la CI.
- **Sustratos**: cuatro PTFE de JLC (ZYF255DA, ZYF265D, ZYF300CA-C y ZYF300CA-P, de 0,65 / 0,9 / 1,65 mm) y poliimida flex de 25 y 50 µm, con
  las reglas de fabricación «JLC alta frecuencia y flex (0,1 mm)» y consejos por sustrato. La simulación usa 2 celdas en z con sustratos de
  menos de 0,4 mm. Parche en PTFE: η ~90 % pero banda de 33 MHz; dipolo, bowtie y J-pole simulados en flex de 50 µm.
- **Bucle impreso** (`bucle`, experimental): anillo cuadrado o redondo con un condensador de sintonía (elemento concentrado en la simulación, con su Q), la línea
  a un extremo y el otro a masa por una vía; sale con la red en π activada. Simulado: 868 MHz −25,6 dB (9 MHz, η 43 %) y 2,4 GHz −29,9 dB (52 MHz, η 53 %) con
  la red en L calculada; sin ella, S11 ~ 0 dB. La simulación admite condensadores concentrados (`Antena.ajuste['condensadores']`).
- `herramientas/helice_flex.py`: hélice cuadrifilar para GPS L1 que se imprime plana en flex y se enrolla (banco de pruebas).
- `referencias/yagi_comercial_b.py`: segunda Yagi comercial de 2,4 GHz del usuario (placa trapezoidal, dipolo plegado, 3 directores), para estudiarla.

## [0.3.0-alpha] · 2026-11-09

### Añadido

- **J-pole e IFA de dos bandas en la interfaz**: parámetro básico «Bandas» (como el Sierpinski) en `jpole` e `ifa`; con «Dos bandas»
  la J-pole son dos J-pole unidas con un puente en B.Cu y la IFA lleva una segunda rama (`antenas/bibanda.py`, medidas de
  `jpole_dual.py` y `rama_dual.py`). Banda alta siempre 2,4 GHz. **Frágil**: con malla de 1,012 mm −11,2/−10,4 dB (J-pole) y
  −11,7/−10,8 dB (IFA), pero con 0,7 mm la banda alta cae a −2,6 y −6,9 dB. Experimental, sin medir.
- **Campaña de simulaciones en GPU** (06–07-11, 146 barridos en 7 bandas: 868 MHz, 915 ISM, 1,2 GHz, GPS L1, Iridium,
  2,4 y 5,8 GHz): `herramientas/barrido.py` (barrido genérico, centrado por simulación y modo `cruz`),
  `herramientas/campana.py` (todos los tipos en todas las bandas), `doble_banda.py`, `cola_extra.py` y la tabla de
  resultados `docs/desarrollo/barridos_gpu.md`. Guía y flujo de GitHub Actions para compilar openEMS con GPU
  (`docs/GPU.md`, `compilar-gpu.yml`).
- Monopolo de punta de flecha de Sierpinski (curiosidad; adapta con la iteración 1), Sierpinski de dos bandas (868/915 + 2,4 GHz,
  `multibanda`) y bandas «LoRa 863–928 MHz».
- Panel de dipolos con o sin reflector; calibraciones de las estimaciones de tamaño con los diseños centrados.
- **Bibanda 868 MHz + 2,4 GHz** (tanda del 07–08-11, solo simulación; la J-pole y la IFA ya están en la interfaz, ver arriba): `herramientas/jpole_dual.py`
  (dos J-pole unidas por un puente en B.Cu, −11,2 y −10,6 dB; el abanico de radiadores no va y con radiadores de Koch
  tampoco), `rama_dual.py` (IFA y monopolo con una segunda rama; IFA −11,7 y −10,8 dB), `radiacion_bibanda.py` y
  `diagrama_bibanda.py` (η, ganancia y diagramas de radiación en cada banda). Informe: `docs/desarrollo/resultados_07-11.md`. Banco de pruebas
  `topologias.py` (torniquete de dipolos para polarización circular, antena de ranura, IFA de tres bandas), en simulación.

### Cambiado

- **Instalador con motor de GPU opcional** (paso 6 de 7 de `instalar.ps1`): si `nvidia-smi` ve una GPU NVIDIA con compute capability 7.5, 8.0, 8.6, 8.9 o 12.0 (RTX 20 a 50), pregunta
  si instala el openEMS con motor GPU de la release v0.2.0-alpha (12 MB, SHA-256 fijado) en `%LOCALAPPDATA%\Programs\gpu-build` y comprueba que el programa lo reconoce. Sin
  GPU NVIDIA o con otra arquitectura lo salta y se simula en la CPU; `-SinGPU` lo omite. `-Comprobar` lo informa sin instalar. Guías `INSTALAR.md` / `INSTALL.en.md` al día.
- **Bucle: red en L automática y anillo redondo calibrado**: «Ajustar a la frecuencia simulando» calcula con la impedancia simulada del anillo una red
  en L con valores E24 (serie Z1 + derivación Z2 o Z3, con las pérdidas de los componentes y la línea entre ellos), la guarda en `red_L` y la
  aplica **por circuito** (`simulacion.aplicar_red_bucle`): 868 MHz, 0,56 nH en serie y 12 pF a masa, −33 dB con 9 MHz de banda (η 43 %); 2,4 GHz, 2,4 pF y 2 pF,
  −30 dB con 44 MHz (η 50 %). La interfaz la muestra y la fabricación lista los valores de Z1/Z2. Anillo redondo calibrado de 750 a 1224 MHz (±0,3 % en
  868 y 1000 MHz) y no se genera con menos de 16 mm. **Arreglo**: la caché de simulación no distinguía valores de condensador o bobina con el mismo cobre.
  `herramientas/calibrar_bucle.py`. La FDTD con la red como componentes concentrados no es fiable con C ≥ 2 pF (derivación en cortocircuito).
- **Bibanda (J-pole unida e IFA de dos ramas) medida frente a la malla** (`herramientas/robustez_bibanda.py`, informe en
  `docs/desarrollo/bibanda_robustez.md`): 18 variantes de las medidas de la segunda rama con tres pasos de malla; ninguna da −8 dB en las
  dos bandas con todos (mejores −6,8 y −1,2 dB). La opción «Bandas» se mantiene, con el aviso actualizado.
- **Panel de dipolos calibrado por banda**: el factor de malla fina (`directivas.K_MALLA_FINA_PANEL`) pasa de un valor único a una
  tabla por frecuencia (868 MHz y 2,4 GHz, 0,85; 5,8 GHz, 0,696). A 5,8 GHz el 2×2 por defecto resonaba a 4800–4970 MHz (−14 %) y ahora
  sale con el brazo de 6,6 mm: −10,5 dB en toda la banda 5725–5875 MHz, 11 dBi. 2,4 GHz no cambia (mismo brazo y placa). **A 5,8 GHz el
  S11 es caótico con el largo del brazo y depende de la malla** (un +15 % de paso lo deja en −4,7 dB): simularlo y medirlo. 868 MHz sin
  simular (placa de 383 × 283 mm). `herramientas/barrido_panel.py` admite `--f`, `--banda` y `--solo-lista`.
- **Verificación con otra malla** (`simulacion.verificar_malla`, casilla «Verificar con otra malla» en Simulación): repite la
  simulación final con el paso ×0,85 y ×1,15 y avisa si la frecuencia se mueve más de un 5 % o el S11 más de 5 dB cruzando
  −10 dB. Siempre con dos bandas, paneles y arrays. Medido: monopolo recto y de Koch estables; J-pole bibanda sensible (ΔS11 hasta
  15 dB). Arreglado de paso: una simulación sin ajuste con «Dos bandas» ahora usa el rango ancho (antes solo 0,6–1,4 ×).
- Galería: los tipos validados en simulación salen de «Experimentales» a su grupo de uso: IFA y PIFA en «Nodo portátil»,
  Vivaldi en «Enlace fijo o directiva», dipolo con manga, colineal de dipolos y J-pole recta en «Sin plano de masa». En
  «Experimentales» quedan los que no funcionan o están sin validar, y la flecha de Sierpinski (curiosidad).
- El grupo «Experimentales» de la galería sale **plegado** (escritorio y web): lo primero que ve un usuario nuevo son los tipos
  validados; al pinchar en el título se despliega. El selector de tipo de la barra los sigue listando.
- **J-pole recta arreglada**: `dimensionar` ahora da el hueco entre brazos ampliado (×5 a 868 MHz, ×6 a 2,4 GHz, interpolado entre
  las dos) y la toma al 26 %, con el largo del radiador recalibrado. Simulada sin centrar: −15 dB a 868 MHz, −10 dB a 915 MHz,
  −9,7 dB a 1,2 GHz, −11,8 dB en GPS L1 y −12 dB a 2,4 GHz (antes −7 dB). A 5,8 GHz sigue sin adaptar. El hueco puede llegar a
  40 mm. Sin medir.
- Estados de los tipos según la campaña: IFA, PIFA, dipolo con manga, Vivaldi y colineal de dipolos pasan a
  «Validada en simulación»; monopolos, dipolo y bowtie, de 868 MHz a 5,8 GHz. La Yagi con elementos de Koch sigue sin
  funcionar: la configuración que adapta (−21 dB) radia hacia atrás.
- Tanda del 07–08-11: la J-pole recta pasa a «Validada» a 868 MHz (−12,9 dB con el hueco ×5), la J-pole de Koch también
  a 1,2 GHz (−10,6 dB), el parche rectangular a 5,8 GHz con ranura (−10,6 dB) y la Yagi con boom a 5,8 GHz (−10,8 dB con
  el haz hacia delante). La colineal de dipolos a 2,4 GHz da −12,7 dB con el factor de línea por defecto. El parche
  circular pasa a «No funciona» (mejor −4,4 dB, razón axial ≥ 6 dB). Más resultados: la IFA y la PIFA a 1,2 GHz, el dipolo a
  1,2 GHz, el bowtie a 2,4 y 5,8 GHz, el sleeve y el Vivaldi a 5,8 GHz, la colineal de dipolos a 5,8 GHz, la J-pole recta a
  2,4 GHz, el monopolo con IPEX a 2,4 GHz (con masa manual) y la flecha de Sierpinski con iteración 1 llegan a −10 dB; la Yagi
  con boom de Koch de iteración 2 funciona a 2,4 GHz con el haz hacia delante (2,6 dBi). El parche con parásito y la COCO pasan a «No funciona». Los recortes de
  aligerado de la Yagi casi no cambian nada a 868 MHz y 5,8 GHz, pero con el margen por defecto rompen la de 2,4 GHz.

### Corregido

- Cambiar «Bandas» en la interfaz (o en la web lite) no redimensionaba la antena: el Sierpinski de dos bandas salía con el
  tamaño de una banda hasta pulsar «Ajustar tamaño a la frecuencia». Ahora se redimensiona al cambiarlo.
- Con «Dos bandas», la estimación de la J-pole y de la IFA salía un 10 % fuera de la banda baja (usaba la calibración de una banda).
- Avisos de la Yagi aligerada y del panel aligerado al día con las simulaciones; aviso grave si se elige «Dos bandas» con la
  banda de uso por encima de 1 GHz (la banda de uso es la baja).

*English: GPU simulation campaign over 7 bands (868 MHz to 5.8 GHz); most antenna types are now validated in
simulation (J-pole at 868 MHz and 2.4 GHz, Koch J-pole at 868 MHz and 1.2 GHz, IFA and PIFA from 868 MHz to 5.8 GHz,
Vivaldi, bowtie, sleeve, dipole collinear, Yagi with boom at 868 MHz, 2.4 and 5.8 GHz, slot-fed patch at 5.8 GHz);
the circular patch, the patch with a parasitic, the COCO and the Hilbert monopole are marked as not working. New
experimental tools: dual-band 868 MHz + 2.4 GHz antennas (two joined J-poles, IFA with a second branch), now also in the
interface as the «Bands» option of the J-pole and the IFA, but fragile: −11 dB in both bands with a 1 mm mesh, the high
band drops with other meshes. The straight J-pole now matches by default from 868 MHz to 2.4 GHz (wider gap, tap at 26 %).
Fixed: changing «Bands» did not resize the antenna. Also: radiation and sensitivity-to-εr tools, and a test bench for new topologies
(crossed-dipole turnstile, slot antenna, tri-band IFA). Everything is simulation only: no board has been measured yet; the
first measurements (εr coupons and 2.4 GHz antennas ordered from JLC) are expected soon.*

## [0.2.0-alpha] · 2026-11-06

### Añadido

- **Versión web lite** (https://sqtactical.github.io/chirptenna/): diseñar, ver y descargar la antena para KiCad
  (`.kicad_pcb`, huella, DXF, `diseno.json` y un LÉEME con los pasos hasta los Gerber) sin instalar nada. Python
  corre en el navegador (Pyodide); no se envía nada a ningún servidor. Enlaces para compartir un diseño, abrir un
  `diseno.json` de la aplicación y tema claro/oscuro. No simula ni pasa el DRC de KiCad.
- **Interfaz más sencilla** (escritorio y web): al entrar, una galería de tipos con miniatura, descripción y estado
  («Validada», «Pendiente de validación», «No funciona»), agrupados por uso. Al elegir uno solo se ven los parámetros
  básicos; el resto está en «Ajustes avanzados». Cada parámetro tiene un botón «?» que explica qué hace. El selector de
  tipo también muestra la descripción y el estado de cada antena.
- Prueba automática de la web en la CI: los 25 tipos a 868 MHz y 2,4 GHz generados dentro del navegador y con el DRC
  de KiCad.

- **Idiomas** (escritorio y web lite): castellano, inglés, francés y alemán, con selector en la cabecera, y un
  easter egg. Los catálogos son `antenas/idiomas/<código>.json` (`python herramientas/i18n.py nuevo it Italiano` crea
  uno); la CI falla si falta alguna traducción. Las traducciones al francés y al alemán están por revisar por
  hablantes nativos. `MANUAL.en.md`: el manual en inglés.
- **Bandas nuevas**: 915 ISM, 1,2 GHz radioaficionado, GPS L1, Iridium y 5,8 GHz (selector de banda como desplegable).
  Solo 868 MHz y 2,4 GHz están simuladas; las demás avisan de que el tamaño está interpolado y, en 5,8 GHz, de las pérdidas del FR4.
- **Tipos nuevos sin testear ni validar**: parche de polarización circular, parche con ranura en U, parche con parásito
  acoplado, antena F invertida, PIFA, dipolo con manga, Vivaldi antipodal y colineal de dipolos en serie por microstrip.
- **Conector «coaxial soldado en la línea»** (sin conector): pads de vivo y malla con la máscara abierta, para los tipos
  alimentados por línea.
- **Dipolo bowtie y bowtie de Sierpinski** (ahora un tipo aparte, `dipolo_bowtie`), y **panel con elementos bowtie** (de 1 elemento, 2×2 o 4×4): más
  banda que el dipolo recto. Simulados a 2,4 GHz y 868 MHz; el 2×2 de Sierpinski da 12,6 dBi.
- **Aceleración por GPU** (experimental, NVIDIA): casilla en la pestaña Simulación; ~10× más rápido que la CPU.
  Hay que compilar openEMS con motor GPU: guía en [`docs/GPU.md`](docs/GPU.md) ([English](docs/GPU.en.md)), reconstruida y aún sin verificar desde cero.
- **Estados actualizados** con ~40 simulaciones nuevas: dipolo, Yagi con boom, J-pole de Koch, monopolo Sierpinski
  y colineal Franklin a 868 MHz; Franklin y Minkowski de iteración 3 mejoran respecto a lo que decían los avisos.

### Cambiado

- El texto del logo de la serigrafía va precalculado (ya no hace falta matplotlib para exportar).
- Las comprobaciones de fabricación usan operaciones de geometría robustas (no fallan con geometrías delicadas).

*English: web lite version (design in the browser and download for KiCad, no install, nothing leaves your
browser), with a CI test that generates every type inside the browser and runs KiCad's DRC on it. Simpler interface
(desktop and web): a gallery of antenna types with thumbnails, descriptions and status; basic parameters first with
the rest under “advanced settings”; a “?” help bubble on every parameter.*

## [0.1.2-alpha] · 2026-11-04

### Añadido

- **Manual de uso** ([MANUAL.md](MANUAL.md)): cada pestaña, medir con el NanoVNA y ajustar la antena
  fabricada (marcas, puentes y red en π con ejemplos, cómo leer la carta de Smith y qué componentes comprar).
- Guía de instalación ampliada (requisitos, qué se instala y dónde, prueba de que funciona, más problemas
  frecuentes, cómo pedir ayuda), en castellano e inglés.
- CI en GitHub Actions: instalador, los 16 tipos con el DRC de KiCad y prueba de la interfaz.
- `SECURITY.md`, código de conducta y Discussions.

### Cambiado

- Versiones de las dependencias fijadas: rangos en `requirements.txt` y versiones exactas en
  `requirements-lock.txt`, que es lo que instala el instalador.

*English: user manual (Spanish), expanded installation guide, CI, security policy, code of conduct and
pinned dependency versions.*

## [0.1.1-alpha] · 2026-11

Igual que la 0.1.0-alpha salvo la licencia del código. *Same as 0.1.0-alpha except for the code licence.*

### Cambiado

- **Licencia del código: de GPL-3.0 a AGPL-3.0.** Igual que la GPL, pero quien ofrezca una versión
  modificada como servicio por internet también tiene que publicar su código. La v0.1.0-alpha sigue
  disponible con GPL-3.0. Los diseños publicados siguen con CC BY-NC 4.0.
- La interfaz enlaza al código fuente y a la licencia (pie de la página).

*Code licence changed from GPL-3.0 to AGPL-3.0 (network use also requires sharing the source of modified
versions). v0.1.0-alpha remains available under GPL-3.0.*

## [0.1.0-alpha] · 2026-11

Primera versión pública. **Alpha: todo está validado solo en simulación**; todavía no se ha medido
ninguna placa fabricada. Se buscan medidas reales (plantilla de issue «Medida real»).

### Qué incluye

- **16 tipos de antena** para PCB, dimensionados para cualquier frecuencia (433 / 868 MHz, 2,4 GHz u otra):
  monopolos (recto, meandro, Koch, Hilbert, Sierpinski), parches (rectangular, Minkowski; alimentación por
  el borde o por ranura), dipolo impreso (balun impreso o coaxial al centro), J-pole y J-pole de Koch,
  colineales (COCO, Franklin), directivas (Yagi de doble cara con boom, quasi-Yagi de Koch, array de parches
  2×2/4×4, panel de dipolos 2×2/4×4 sobre reflector).
- **Simulación con openEMS** desde la interfaz: S11, ROE, carta de Smith con la banda marcada, diagrama de
  radiación (cortes y 3D con la placa dentro), ganancia y eficiencia; **ajuste automático** a la frecuencia
  (y a la adaptación en los tipos que lo necesitan). Estimaciones calibradas con simulaciones anteriores.
- **Fabricación**: comprobación de reglas de JLC, placa de prueba de KiCad con SMA de canto o IPEX, Gerber con
  taladros para JLC, DXF y huella; DRC de KiCad automático. Serigrafía con el logo de Chirptenna (grande,
  pequeño u opcional) e inscripciones a elegir. Recortes para aligerar Yagi y paneles.
- **Ajuste tras fabricar** sin componentes: marcas de corte rotuladas en MHz, tramos con puente de estaño y
  red en π opcional.
- **NanoVNA-H**: asistente para conectar, calibrar en el PC (OSL guiada), comprobar, medir (también en vivo) y
  saber qué cortar o qué poner en la red en π, con la medida superpuesta a la simulación.
- **Mis diseños**: biblioteca en `Documentos\Chirptenna\disenos` con geometría, simulación, exportación,
  medidas y notas de cada diseño.
- Interfaz en el navegador (NiceGUI) por fases, con modo claro/oscuro; avisos de los problemas conocidos de
  cada tipo.
- **Instalador para Windows** (`instalar.bat`, sin permisos de administrador) y guía paso a paso.
- Cupones de calibración para medir la εr real del FR4 (`cupon/`).

### Limitaciones conocidas

- Validado solo en simulación, con εr 4,5 para el FR4 de JLC.
- Tipos que no funcionan bien en simulación: J-pole recta, colineal Franklin, quasi-Yagi de Koch, Yagi con
  elementos de Koch, parche de Minkowski de iteración ≥ 2, Hilbert sin red en π. Detalle en
  «Problemas conocidos» del README.
- Solo Windows; interfaz solo en castellano; sin pruebas automáticas en CI (hay una comprobación manual:
  `python herramientas/comprobar_tipos.py`).

### English summary

First public release. **Alpha: validated in simulation only**; no manufactured board has been measured yet.
Includes 16 PCB antenna types for any frequency, openEMS simulation with automatic tuning, KiCad/Gerber/DXF
export with DRC and a silkscreen logo, post-manufacture tuning aids, a NanoVNA calibration and measurement
assistant, a design library, a dark mode and a Windows installer. Windows only; Spanish GUI. See “Known issues”
in the README.

[0.1.2-alpha]: https://github.com/sqtactical/chirptenna/releases/tag/v0.1.2-alpha
[0.1.1-alpha]: https://github.com/sqtactical/chirptenna/releases/tag/v0.1.1-alpha
[0.1.0-alpha]: https://github.com/sqtactical/chirptenna/releases/tag/v0.1.0-alpha
