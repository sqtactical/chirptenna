# Chirptenna (antenas para PCB) — estado a 04-11-2026

## Hecho

- **Fase 0** (`fase0/`): openEMS v0.37.0 validado (dipolo frente a teoría) y monopolo impreso
  de 2,45 GHz en FR4 ajustado automáticamente. Ver `fase0/README.md`.
- **Control del NanoVNA** (`vna/`): driver, medida de antenas/líneas/latiguillos y calibración
  guardada en el PC (`completa_50k_2700M`, 1010 puntos, OSL + THRU). Copias de la SD del equipo
  en `vna/calibraciones/sd_backup/` (`CAL-PCB.CAL` es la misma calibración, 101 puntos).
- **Intento de medir εr con la Scout** (`analisis/`, `placa_sim/`, `vna/medidas/scout_*`):
  descartado. La placa sin montar radia y resuena con el cobre suelto, y simularla exige
  resolver huecos de ~0,2 mm. Queda el importador Gerber → openEMS (`placa_sim/simular_placa.py`).
- **Cupón de calibración** (`cupon/`): diseño completo en una placa de 185 × 100 mm (anillos de
  868 MHz, 2,4 GHz y 5,8 GHz modo 3; líneas de un puerto S80/S30; líneas de dos puertos en L
  L71/L22; SMA de canto Samtec SMA-J-P-H-ST-EM1). `generar_cupon.py` → `cupon_er.kicad_pcb`,
  `gerber/`, `cupon_er_JLC.zip`; DRC limpio. Simulado el anillo de 2,4 GHz
  (`simular_anillo.py`): resuena a **2,236 GHz** (−7 % respecto al diseño), pico de S21 de −15 dB.
- **Fase 1** (`antenas/`, `gui/`): generador con interfaz gráfica.
  - Catálogo: monopolos recto, meandro, Koch, Hilbert y Sierpinski; parches rectangular y de
    Minkowski; **directivas**: quasi-Yagi con dipolo de Koch (balun microstrip→CPS, 0–2
    directores) y arrays de parches 2×2/4×4 (rectangulares o Minkowski, alimentación con
    inserción, red corporativa en el pasillo entre filas, U de λg/2 para la fila girada).
  - **Panel de dipolos 2×2 / 4×4 sobre reflector** (`panel_dipolos`, 01-11-2026, a petición del
    usuario como antena «panel»): dipolos impresos con un brazo en cada cara, red en H de tiras
    paralelas (100 Ω al dipolo, uniones a 50 Ω y λ/4 de 70,7 Ω), coaxial por detrás al centro
    (taladro + pads vivo/malla) y reflector aparte a 0,25 λ0 (segunda placa exportada con taladros M3
    alineados y taladro de SMA de panel, o chapa por DXF). 2441 MHz: 2×2 placa 153 × 111 mm, reflector
    202 × 160, ~12 dBi estimados; 4×4 337 × 295 / 386 × 344 mm, ~16,6 dBi (red −2,5 dB). DRC limpio en
    las dos placas. Ajuste: largo del brazo (frecuencia) y `separacion_reflector` (adaptación).
    `K_DIPOLO_PANEL` = 0,95 sin calibrar. Malla adaptada: 1,45 M celdas (2×2) y 5,6 M (4×4).
    1.ª simulación del 2×2 (brazo 22,52 mm): −15,5 dB y Z ≈ 39 − 11j Ω en 2441, S11 < −10 dB en
    ~2,0–2,8 GHz con ondulaciones; la secante por centro de banda saltó (2494 → 2881 → 1963 MHz) y se
    paró (lección 35). **Resultado (brazo 22,52 mm, sin ajustar, 20 min)**
    (`salidas/_validacion_panel/panel_2x2_ganancia.json`): de 2300 a 2600 MHz S11 −13…−15,6 dB
    (Z ≈ 35–40 − 11j Ω), D 13,4–13,8 dBi, **G 12,3–12,8 dBi (12,7 en 2441)**, η 78 %. La estimación
    (12,2 dBi) acierta. Haz inclinado 9–12° hacia −x (plano de los dipolos), sin explicar todavía
    (resultó ser un artefacto de la simulación, ver abajo). No hace falta ajustar nada.
    Diagrama (`panel_2x2_base_cortes.png`/`_3d.html`): de frente 11,6 dBi (−1,1 dB), plano E −27…+6°
    a −3 dB con lóbulo de −2 dBi solo en +40°; plano H ±18° simétrico; F/B 21 dB. Diagnóstico: sin el
    hilo del coaxial sale **idéntico** (no es el modo común: el hilo de λ/4 al reflector hace de choque);
    un dipolo solo sobre el reflector tiene el plano E simétrico (8,0 dBi, η 91 %). Es un desfase de
    ~40–50° entre columnas en el array. **Corregido en el generador (01-11, a petición del usuario)**:
    parámetro `simetrico` (por defecto 1): columna izquierda de cada bloque espejada + cruce de tiras con 2
    vías; exportación con vías y nets por grupos; DRC limpio en 2×2 y 4×4 (2,4 GHz) y 2×2 a 869,5 MHz
    (placa 401 × 283 mm: a 868 el 2×2 ya es grande). 1.ª simulación del simétrico: S11 −1,4 dB,
    Z ≈ 4 + 17j, mismo haz inclinado: **las vías no estaban en el modelo** (hilo fuera de las líneas de
    malla, lección 30); la rama izquierda quedaba como un tramo abierto de ~λ/4 que cortocircuitaba la
    entrada. Corregido en `simular`; repitiéndose en la cola A. Consecuencias: la prueba «sin hilo» del
    coaxial no probó nada (el hilo tampoco existía) y **la Yagi comercial se simuló sin vías**: puede
    ser la causa del −21,5 % (repetirla, ~6 h, antes de seguir con las hipótesis de las fotos).
    En cola (`scratchpad/cola_yagi.ps1`, tras la cola de 868): v2 con `--paso 0.125` y todas las vías;
    el resultado antiguo (sin vías) se guardó en `_referencias/yagi_comercial/v2_p0.125_sin_vias`.
    **Simétrico con las vías ya en el modelo (01-11)**: G 12,7 dBi, η 78 %, S11 −10,0 dB (Z 29 − 15j,
    peor que el normal: −15,6), y **el mismo θ 9° hacia φ 180°**. La variante `espejo` (panel entero
    reflejado en x) también sale a φ 180° y el dipolo solo a θ 9°: si fuera física, el espejo saldría
    hacia +x. **La inclinación es un artefacto de la simulación** (algo del montaje que no se refleja:
    caja NF2FF, malla, puerto pasante o convenio de φ). Pendiente: buscarlo y decidir con el usuario si
    `simetrico` vuelve a 0 por defecto (no mejora el haz, empeora S11 y añade vías). Ojo: el normal se
    simuló sin el hilo del coaxial (no existía), así que el −10 dB del simétrico puede ser del hilo y no
    del cruce. En cola el primero (`scratchpad/cola_868.ps1` reordenada): `panel_diagrama.py base 2` con
    el modelo corregido, en el primer hueco (si es el de la cola B, el Hilbert 868 pasa al final).
    **Resultado (01-11)**: normal con el hilo del coaxial S11 −15,7 dB, G 12,7 dBi, mismo θ 9°: el
    −10 dB del simétrico es del cruce, no del hilo → proponer al usuario volver a `simetrico` = 0.
    **4×4 (5,6 M celdas, ~1,5 h, `panel_4x4_ganancia.json`)**: S11 −13…−19,6 dB en 2300–2600 MHz,
    D 18,8–19,6 dBi, **G 15,9–16,8 dBi (16,6 en 2442, igual que la estimación)**, η 51–53 % (pérdidas de
    la red en FR4), haz casi recto (θ 3°), F/B 31 dB, haz a −3 dB ~12° (E) × 15° (H).
  - Dimensionado orientativo a la frecuencia (monopolos/Yagi ±20 %, calibrado con la Fase 0;
    parche rectangular ±3–5 %). Estimación de pérdidas de la red de los arrays.
  - Contorno de placa ajustado a la antena (envolvente convexa con esquinas redondeadas) o
    rectangular, y margen del cobre al borde configurable (2 mm por defecto). Yagi con 0–8
    directores, cada uno un `reduccion_director` más corto, y ganancia estimada 4 + 2,2·log2(1+n) dBi.
  - Ancho de banda (−10 dB) estimado (`antenas/ancho_banda.py`: Jackson-Alexopoulos + pérdidas
    en parches; Chu × factor por forma en monopolos/Yagi, calibrado con la Fase 0; ±50 %),
    bandas de uso EU 868 (863–870) e ISM 2,4 (2400–2483,5) centradas en su centro, botón
    «Ampliar ancho de banda» (`tipos.ajustar_ancho_banda`: ensancha pista o parche con margen ×1,5)
    y panel de consejos (`antenas/consejos.py`: generales por familia/tipo y según el diseño).
  - Plano de masa automático (manual / λ/4 / λ/8 / mínimo en monopolos; mínimo que cabe en la
    Yagi; margen 6h en parches y arrays), con aviso de pérdida de eficiencia en los compactos.
  - Comprobaciones de fabricación (pista/hueco mínimos de JLC, solape de vueltas).
  - Exportación: placa de prueba KiCad con SMA, huella `.kicad_mod` (pad de forma libre), Gerber +
    taladros en `.zip` (kicad-cli), DXF (capas COBRE_SUP/COBRE_INF/CONTORNO) y JSON; DRC de
    KiCad automático. Salidas en `salidas/<nombre>/`.

- **Fase 2** (`antenas/simulacion.py`, `simular_cli.py`, `graficas.py`, tarjeta «Simulación» de la
  interfaz): cualquier antena del catálogo se simula con openEMS (S11, banda −10 dB, Smith,
  directividad, ganancia, eficiencia, cortes polares y diagrama 3D) y se ajusta a la frecuencia por
  secante sobre el centro de banda; botón para aplicar los parámetros ajustados. Validado con el
  monopolo recto a 2441,75 MHz: 2 simulaciones, −0,27 %, banda 2297–2582 MHz, 2,2 dBi, η 92 %.
  Monopolo de Koch (iter. 2): la estimación iba +7,5 %; 3 simulaciones → −0,48 %, altura 18,1 mm
  (22 % menos que la recta), banda 340 MHz, 2,1 dBi, η 92 %. Factor de Koch de la estimación
  recalibrado de 0,5 a 0,35 (monopolo y Yagi). ~2–4 min por simulación en estas placas.
  Pendiente: validar Hilbert, Yagi y parches (más lentos por la malla fina o el tamaño).

- **J-pole** impresa y **J-pole de Koch** (`antenas/jpole.py`): radiador λ/2 + adaptador λ/4 de
  tiras, sin masa, toma ajustable, pads para coaxial en KiCad.
- **Ajuste tras fabricar** (`antenas/ajuste.py`), selector «No ajustable / Ajustable»: red en π
  (0603/0402, serie 0 Ω, derivaciones sin montar), marcas de corte con la frecuencia en MHz
  (sobrelargo %), tramos con puente de estaño o 0 Ω (abiertos; cada uno baja la frecuencia) y
  asistente en la interfaz (subir `.s1p` o medir con el NanoVNA y calibración del PC): qué marca
  cortar, cuántos puentes cerrar y valores E24 de la red en π. DRC limpio en los 10 tipos con todo
  activado. La simulación da por montado el 0 Ω y, con sobrelargo, ajusta a f/(1+sobrelargo).
  Pendiente: probar el botón «Medir» con el usuario y el NanoVNA.

- **Lote de validación 2** (`salidas/_validacion2/resumen.json`, malla uniforme, 31-10-2026):
  J-pole de Koch +0,7 % (−12,5 dB, 2,2 dBi, η 86 %); meandro +0,4 % (estimación +24 %, 5 sim.);
  Koch con sobrelargo −1,8 % sobre f/(1,03); parche de Minkowski −0,5 % (η 31 %); Yagi 1 director
  +0,7 % pero ~15 Ω (−5,6 dB) en el objetivo, 5,7 dBi. Fallos y correcciones ya hechas en el código:
  parche rectangular (transformador no resuelto → resonancia falsa), Sierpinski (uniones de ancho
  cero → no converge), Yagi (adaptación por `alto_cps`), J-pole recta (simulada sin `_ajustar_toma`).
  El Hilbert de 868 MHz tarda >3 h por iteración (ver lección 28 de CLAUDE.md); se paró en la
  iteración 3: lado 16,0 mm → 738,6 MHz (−14,8 %, sin −10 dB); 13,64 mm → 794,2 MHz (−8,35 %,
  −18 dB). La frecuencia cambia poco con el lado (la masa y la línea pesan): seguir desde ~10,6 mm.
  No se llegaron a simular el Hilbert de 2,4 GHz ni el array 2×2.

## Dónde nos quedamos

Fase 1 terminada y probada (interfaz en el navegador: cambiar tipo/banda, ajustar, exportar;
DRC limpio en Koch, Sierpinski, Yagi y array). Toca volver a **los cupones de validación**.

## Siguientes pasos

0. Tanda 3 de validación, cuando la CPU quede libre:
   1. `python -m antenas.comparar_mallas salidas\_validacion2 monopolo_meandro_2441.75MHz
      monopolo_koch_2441.75MHz_ajuste1 yagi_koch_2441.75MHz_directores1 jpole_koch_2441.75MHz`
      → si Δf ≤ 0,5 % y S11/ganancia/η casi iguales, la malla adaptada pasa a ser la de por defecto.
   2. `python -m antenas.validar_lote salidas\_validacion3 [--malla adaptada] jpole:2441.75:normal
      parche_rectangular:2441.75:normal parche_minkowski:2441.75:normal
      monopolo_sierpinski:2441.75:normal yagi_koch:2441.75:normal:{"directores":1}`
   La Yagi del lote 2 radia **hacia atrás** (máximo en −y, F/B −16 dB): la masa (reflector) mide
   38 mm, físicamente como el dipolo de Koch pero eléctricamente más corta, y actúa de director.
   En la tanda 3 se prueba con masa manual de 65 mm (≈ λ0/2) en vez del caso por defecto; si sale
   hacia +y, cambiar en `directivas.generar_yagi` el ancho automático del reflector.
   J-pole recta en la tanda 3 (31-10): −0,86 % pero mal adaptada. Subir la toma sube R (6 → 24 →
   47 Ω) pero añade X muy capacitiva (−93j, −254j): el adaptador no resuena en f_obj. `_ajustar_toma`
   rehecho como Newton/Broyden en (factor_adaptador, toma); repetir la J-pole.
   **Yagi de doble cara con boom** (`yagi_boom`, propuesta del usuario; `directivas.generar_yagi_boom`):
   microstrip por el boom, medio dipolo en cada cara, reflector en la inferior unido a la masa,
   directores sueltos (arriba) o unidos al boom (abajo, `unir_boom`). Sin vías: cada pieza va entera
   en una cara. Elementos rectos o de Koch. Adaptación por `separacion_reflector`. DRC limpio en
   recta, Koch y unida. Sin opciones de ajuste tras fabricar todavía (grupo `sin_ajuste`).
   Resultado `yagi_boom` recta, 1 director, directores sueltos (tanda 3): frecuencia bien a la primera
   (−0,23 %) pero Z ≈ 10 Ω; solo adapta con el reflector a 42,5 mm (0,35 λ): −11,6 dB, banda
   2378–2465 MHz, haz hacia +y (directores) con F/B 7 dB, D 7,3 dBi, G 6,0 dBi, η 75 %. El dipolo
   partido tiene R demasiado baja → pasar a dipolo plegado con balun (como la Yagi comercial).
   Añadido: `alimentacion` (0 directa, 1 transformador λ/4 de `z_transformador` Ω en el boom; por
   defecto 0), separaciones en λ0 (0,17 / 0,15; antes en mm y encogían con Koch), estimación
   calibrada (`K_DIPOLO_BOOM` 0,87), tira de unión hasta el vértice de los directores de Koch.
   Resultado `yagi_boom` recta **unida al boom** (`unir_boom` 1, tanda 3, 2,4 h): la secante de
   frecuencia salta entre modos (2497 → 2404 → 2151 → 2700 MHz); el ajuste de adaptación deja el
   reflector a 0,39 λ (49 mm): −9,6 dB en el objetivo (Z 25,6 + 6,5j Ω), G 5,3 dBi, η 77 %, F/B 5,6 dB,
   placa 48 × 79 mm. Algo peor que con directores sueltos: confirma que hace falta el dipolo plegado.
   Koch (iteración 2) unida al boom (2,2 h): la secante salta entre modos (2298 ↔ 2530 MHz); queda en
   banda 2458–2614 MHz (centro 2535, +3,8 %), −8,4 dB en el objetivo, G 6,6 dBi, η 77 % y **radia hacia
   atrás** (φ 270°: 7,7 dBi; hacia los directores −3,2 dBi). No sirve tal cual: los parásitos de Koch,
   con largos en fracción del dipolo entre extremos, no hacen de reflector/director como los rectos.
   Placa con transformador y 1 director: 47 × 51 mm (frente a 71 mm con alimentación directa).
   Adaptación con transformador: `z_transformador`, primer paso Zt·√(50/R).
   Resultado con transformador (tanda 3, 4 iteraciones, 2,4 h): 2437,6 MHz (−0,17 %), −14,2 dB,
   banda solo 2417–2458 MHz (41 MHz), D 6,1 dBi, G 3,6 dBi, η 56 % y **radia hacia atrás**
   (φ 270°: 6,1 dBi; hacia los directores 4,6 dBi; F/B −1,6 dB). Adapta pero el haz lo dominan las
   corrientes de modo común del boom (alimentación desequilibrada sin balun), que el transformador
   ancho refuerza. Conclusión: el transformador no sirve; la alimentación buena es el dipolo plegado
   con balun de «U» de la Yagi comercial. `alimentacion` vuelve a 0 por defecto.
   Después de validar la simple: variante como la Yagi comercial del usuario, **reflector y
   directores en las dos caras unidos por vías** (en la cara superior el reflector partido para dejar
   pasar la pista; si van unidos al boom, el boom superior empieza tras el dipolo para no cortocircuitar
   la alimentación). Vías como cilindros PEC en openEMS; nets por pieza también en B.Cu al exportar.
   Comparar con la simple (largo para resonar, banda, ganancia, η, F/B, tamaño).
   Parche rectangular (tanda 3, malla adaptada, 31 min): estimación −3,8 %, 2 sim. → −0,34 %,
   L 27,5 × W 37,0 mm, banda 2416–2452 MHz (36 MHz: NO cubre la ISM de 83,5 MHz en FR4 1,6 mm),
   S11 −12,6 dB (transformador algo desajustado), D 6,2 dBi, G 2,9 dBi, η 47 %, haz a +z.
   **Yagi comercial 2,4/5,8 del usuario** (fotos en la conversación del 31-10; trapecio de ~58 → 36 mm
   × ~115 mm, ~7 pares de elementos en las dos caras con vías): medida directa al NanoVNA con la
   calibración del PC (`vna/medidas/yagi_comercial_2g4_5g8.*`): −10 dB de 2307 a 2462 MHz (155 MHz,
   mínimo −36 dB en 2344 MHz), otra resonancia estrecha en 2127 MHz, −4…−7 dB por encima de
   2,5 GHz. Repetida con la calibración del equipo 2350–2500 MHz
   (`yagi_comercial_2350_2500.*`): coincide; mínimo −44 dB en 2351,5 MHz, −10 dB hasta 2471,5 MHz,
   −13,7 dB (33 Ω) en 2441,75 y −8,95 dB en 2483,5. Banda estrecha (~6,5 %): es Yagi (confirmado a contraluz), no log-periódica;
   centrada bajo para la ISM (2462–2483,5 MHz en ~−9 dB). Anunciada con 12 dBi (estimado real 8–10).
   Geometría (foto con calibre, ±0,5–1 mm; y desde el borde del conector): placa 118 × 56,6→37 mm,
   FR4 1,6 mm; reflector = banda de masa 0–6,5 mm de todo el ancho; dipolo 39,5 mm en y 25,7
   (ensanchado hacia las puntas, ~5,8 mm); directores 39,7/38,7/37,6/36,6/35,8 mm en y
   42,8/57,6/71,8/86,5/101,3, ancho ~3,7 mm; barra final ~37 mm en y 115,5; boom ~3,5–4 mm.
   Todos los elementos en las dos caras, unidos al boom; vías en el perímetro de los parásitos y
   solo en las puntas del dipolo. Alimentación: el vivo sube por el boom y se divide en «Y» hacia
   las dos mitades del dipolo (cara superior); en la inferior, un elemento recto de ~6 mm unido a
   masa por el centro (dipolo plegado apilado; modelo en `referencias/yagi_comercial.py`) → corto en continua (medido Z ≈ 7 + 8j Ω a 1,5 GHz). Hipótesis: una rama con retardo
   ~λg/2 (el rectángulo del boom entre dipolo y D1) para ir en contrafase. Plan: añadir vías al
   simulador, modelarla con ramas iguales y con retardo, y quedarse con la que reproduzca la medida.
   Tanda 3 (`salidas/_validacion3`, malla adaptada): parche rectangular −0,34 % (G 2,9 dBi, η 47 %,
   36 MHz); parche de Minkowski (iteración 1) +0,56 % en 2 iteraciones: radiador 25,2 × 25,2 mm
   (−38 % de área frente al rectangular), placa 44 × 57 mm, banda 2435–2476 MHz (41 MHz, no cubre la
   ISM), G 1,0 dBi, η 33 %; la estimación sale un 3 % alta (2534 MHz). 1.ª iteración 3,6 h con 3
   simulaciones a la vez (1,6 M celdas de 0,25 mm), la 2.ª 36 min. En cola: Sierpinski, J-pole,
   yagi_boom unida recta y Koch (alimentación directa). Con 1,6 M celdas, 3 simulaciones a la vez
   saturan la memoria: máximo 2 en este portátil.
   **Yagi comercial simulada (6 h, 4,3 M celdas): no coincide.** Resonancia principal 1839 MHz
   (−26,6 dB) frente a 2344 MHz medidos (−21,5 %), sin banda en 2300–2470 MHz; la resonancia estrecha
   de 2115 MHz sí coincide con la medida de 2127 MHz (−0,6 %). D 4,0 dBi, G 1,7 dBi, η 59 %, máximo en
   θ 66°. El modelo de `referencias/yagi_comercial.py` tiene algo eléctricamente demasiado largo
   (¿dipolo plegado/vías de las puntas, el balun de «U» o la unión con el boom?). Pendiente de
   investigar antes de copiar su alimentación en `yagi_boom`.
   Diagnóstico con puerto diferencial ideal entre las mitades del dipolo, sin balun
   (`--variante dif --paso 0.3`, 53 min): Z ≈ 2–7 Ω + j(48…82) Ω en 2,2–2,5 GHz, sin resonancia
   paralela hasta 3,3 GHz. El dipolo plegado apilado, tal como está modelado, no resuena solo en
   2,35 GHz: la adaptación de la antena real la hace la red de alimentación (ramas + «U»), así que
   la discrepancia viene de la geometría de esa zona (medidas de fotos ±0,5–1 mm). Siguiente paso:
   escaneo de las dos caras a 600–1200 ppp para medir el dipolo, las ramas y la «U» con precisión.
   No hay escáner. Releyendo la foto macro (recuperada del historial de la sesión, ampliada y con
   contraste) el modelo base estaba mal: dentro de la «U» hay una **tira de masa central con vías**
   (la masa coplanar derecha se desplaza al centro); el vivo se desvía a la izquierda, alimenta la
   mitad izquierda por un puente, va hacia delante, rodea el final de la tira central (~36,7 mm) y
   vuelve por la derecha a la otra mitad. Ramas de ~1,4 mm blindadas por la masa central, no
   acopladas entre sí. Modelado como `--variante v2`.
   **v2 (`--paso 0.125`, 6,1 h, 3,9 M celdas): igual que la base.** Resonancia principal 1843 MHz
   (−26,9 dB; la base daba 1839), segunda débil en ~2090 MHz (−11 dB) frente a 2127 medidos, G 1,7 dBi,
   η 57 %, máximo en θ 48°. Cambiar el recorrido de la alimentación no mueve nada, así que el error no
   está en el balun sino en el dipolo apilado (mitades arriba + elemento inferior de 39,5 × 5,9 mm con
   vías en las puntas). Pista: 2344/1843 = 1,27 ≈ √(4,5/2,8), es decir, el modo simulado parece ir
   con el campo dentro del FR4, entre las dos caras, y el real con el campo fuera. Sospecha: en la placa
   real el elemento inferior no queda debajo de las mitades (más estrecho, desplazado o más corto).
   Huella a baja frecuencia de la medida (las simulaciones empezaban en 1,44 GHz y no la ven): corto
   con ~15–20 nH a 300–500 MHz, resonancia paralela fuerte hacia 800–850 MHz, capacitiva a 1–1,2 GHz.
   Plan si se retoma: simular 0,1–3,4 GHz con paso 0,3 (~1 h) y comparar esa huella (depende de la
   topología, no de ±1 mm); luego variantes gruesas (vías de las puntas, barra unida o no, puentes,
   εr/grosor); prueba de perturbación con el NanoVNA (tocar dipolo/directores y ver qué resonancia se
   mueve). El usuario prefiere seguir antes con el panel (01-11).
   Revisadas las fotos a contraluz del 31-10 (`foto_06`/`foto_07` de la sesión): la cara de atrás
   tiene una barra recta del largo del dipolo (~40 × 6,5 mm) unida al boom, que va desde la banda del
   reflector hasta el final; es lo que ya tiene el modelo, así que otra foto no resuelve nada. Causa
   sin aislar (¿posición/número de vías de las puntas, grosor o εr real de la placa?). Cada prueba
   cuesta ~6 h: **aparcada** salvo que haga falta; lo aprovechable (dipolo plegado con balun) se puede
   diseñar y ajustar directamente en `yagi_boom`.
   **Sierpinski (tanda 3, con `cuello` 1 mm) bien**: +0,82 % en 4 iteraciones, banda 2175–2787 MHz
   (612 MHz, 25 %), −28 dB en el objetivo, η 94 %, G 2,2 dBi, placa 25 × 43 mm, alto 18,1 mm. La
   estimación sale +4,9 % alta. La 3.ª iteración saltó (18,25 mm → −8,35 % frente a 18,04 → +1,4 %):
   con una banda tan ancha el centro de banda es inestable (dos resonancias juntas).
   **J-pole recta (tanda 3) sigue mal**: resonancia −0,86 % (cruce de reactancia) pero R ≈ 6 Ω en
   la toma 0,2; subirla a 0,26–0,35 solo da 10 Ω con −15…−19j; `_ajustar_toma` (Broyden) explora y
   vuelve al punto de partida (7 sim., 54 min). La J-pole de Koch sí adapta. Pendiente: revisar el
   modelo de la recta (¿el cruce de reactancia engancha el modo del adaptador?, hueco/puerto).
   **Conector seleccionable** (31-10): SMA de canto o IPEX/U.FL (`antenas/conector.py`); DRC limpio en
   los 10 tipos (salvo J-pole, que va con coaxial) con ambos. Con IPEX la masa mínima del monopolo
   baja a 7 mm y el ancho a 8 mm. Sin simular todavía con IPEX.
   Estimaciones: `eps_eff_monopolo` es constante (calibrada a 2,45 GHz), pero con el FR4 de 1,6 mm
   fijo la εeff de una pista radiante baja a baja frecuencia (h/λ menor) y sube a 5,8 GHz; el
   adaptador de la J-pole (CPS, campo en el hueco) apenas cambia. Por eso la relación radiador /
   adaptador (2,36 en todas las bandas) no debería ser fija. Calibrar εeff(h/λ) simulando la J-pole
   (y un monopolo) a 868 MHz además de a 2,4 GHz; afecta a monopolos, Yagi y J-pole.
   **Escalado con λ de las medidas secundarias** (todos los tipos, parámetro `escalado`, por defecto
   «proporcionales»): `tipos.ESCALABLES` + `escalar_secundarios` en `dimensionar`, referencia 2,4 GHz
   (pistas, huecos de la J-pole, cuello del Sierpinski, masa manual, largo de alimentación de los
   parches, balun de la quasi-Yagi…). Hilbert: pista y separación van con el lado (escala_conjunta).
   Comprobado en 433/868/2441/5800 MHz: geometría y reglas de JLC bien salvo Hilbert orden 3 a
   5,8 GHz (pista 0,12 mm: bajar el orden) y un hueco mínimo en la quasi-Yagi a 5,8 GHz. En la
   interfaz, tocar a mano una medida escalable pasa el modo a «manual» (sin probar en el navegador).
   Sin simular fuera de 2,4 GHz todavía.
   Array: con valores por defecto cumple JLC y DRC a 2,4 GHz. Corregido: con Minkowski de iteración 3
   la muesca de inserción partía cada parche en dos (cuello central estrecho); ahora se acorta la
   inserción y avisa. Iteración 3 con profundidad 0,7 deshace el parche (cuellos < 0,127 mm): límite
   del fractal a ese tamaño.
   **Tanda 4 en cola (01-11, `salidas/_validacion4`, malla adaptada, dos colas de una en una con
   6 hilos: `scratchpad/cola_tanda4.ps1 A|B` de la sesión; la A empieza con el panel espejado)**: monopolo recto con IPEX, monopolo recto y J-pole de Koch a 866,5 MHz (calibrar
   εeff a baja frecuencia), quasi-Yagi con masa manual de 65 mm, Hilbert 2,4 (orden 2), array de
   parches 2×2 y Hilbert 868 desde lado 10,6 mm (el más lento, al final). Fuera: J-pole recta (revisar
   el modelo antes) y array de parches 4×4 (demasiado grande por ahora).
   Hechos: monopolo recto con IPEX 2445 MHz pero solo −7,1 dB (G 2,2 dBi: con IPEX adapta mal, revisar
   la transición del pad central); monopolo recto a 866,5 MHz: estimación +5 % (910), ajustado a
   866,9 MHz, −11,8 dB, banda 838,8–896 MHz (57 MHz), G 1,9 dBi, η 93 %, placa 16 × 142 mm (masa
   15 × 69,6 mm; antes ponía «113 × 185», mal leído de `ancho_placa`). **Exportado como beta para
   fabricar** en `salidas/monopolo_868_beta/` (Gerber JLC, DRC sin errores): con ajuste (sobrelargo 3 %
   → sin cortar ~842 MHz, una marca «867», 3 tramos con puente de estaño de −2,1 % cada uno y red en π
   0603 con Z1 = 0 Ω o puente de estaño), placa 16 × 150 mm. Los rótulos de las marcas salían de la
   estimación analítica (825 MHz, un 5 % baja): ahora `k_sim` (lección 38). En cola tras la A (`scratchpad/cola_868.ps1`): meandro y Koch a
   866,5 MHz con ajuste tras fabricar, para diseños públicos con SMA (el usuario prefiere 868 porque
   muchos VNA no llegan a 2,4 GHz).
   Fallos de la cola A: **J-pole de Koch 868** 1009 → 595 → error `index 1 is out of bounds` en la
   iteración 3 (la secante saltó −31 %: S11 con varias bandas; el error es un fallo de `ajustar` con un
   solo punto). **Quasi-Yagi con masa de 65 mm**: paso de tiempo 6,4e-19 s (dos líneas de malla casi
   iguales), parada a mano. El array de parches (5,6e-19 s) y el Hilbert 2,4 (iteraciones 2–5 con paso
   27× menor, sin converger, siempre «2237,9 MHz») tenían lo mismo: líneas de puerto pegadas a la
   rejilla, y la J-pole leyó una caché a medias. Corregido (lección 37) y repitiéndose todo en
   `scratchpad/cola_rehacer.ps1` (J-pole Koch 868, Hilbert 2,4, quasi-Yagi, parches 2×2, Hilbert 868), en
   paralelo con `cola_868.ps1` (panel normal en marcha → meandro y Koch 868); después `cola_100.ps1`
   y la Yagi comercial.
   **Meandro y Koch de 868 con SMA y ajuste (01-11, `_validacion4/*_ajuste1`)**: meandro sin cortar
   857,9 MHz (+2 % sobre el objetivo de 841,3; la secante osciló: 36,5 mm → 823, 34,6 → 858, 35,5 → 812,
   ruido de malla con el meandro), banda 806–912 MHz, G 1,8 dBi, η 92 %, k_sim 1,215 (la estimación del
   meandro falla un 21 %). Koch sin cortar 834,7 MHz (−0,8 %), banda 785–887, G 1,8 dBi, η 93 %, k_sim
   1,043. Los dos con marcas ya rotuladas con la simulación: candidatos a diseño público.
   **Meandro de 868 en 100 × 100 mm, ajustable solo soldando** (petición del usuario, 01-11): masa manual
   55 × 90 mm, 3 vueltas, `red_pi` 0, marca de corte + tramos con puente de estaño; estimación 90 × 87 mm
   (~92 tras el +18 % de alto que suele pedir el meandro). En `scratchpad/cola_100.ps1`. Otros que cabrían:
   Hilbert 37 × 87 (sin validar), meandro con masa λ/4 (26 × ~104, justo fuera). El parche de Minkowski
   (93 × 149), el Koch (28 × 129) y el Sierpinski no caben.
   **Resultado (01-11)**: sin cortar 831,2 MHz (−1,2 % sobre 841,3), alto 31,3 mm, pero **S11 mín −8,3 dB**
   (no llega a −10 dB; ROE ~2,3), G 1,5 dBi, η 88 %. La frecuencia vuelve a saltar con el alto (958 → 887 →
   906 → 831). Sin red en π no hay con qué adaptarlo. El usuario decide dejarlo así (no probar más masa).
   **Parches con alimentación por ranura** (petición del usuario, 01-11; lección 39): DRC limpio en
   rectangular y Minkowski a 868 y 2441 MHz, con y sin marcas; probado en la interfaz. Sin validar
   con simulación. Para el pedido a JLC el usuario quiere el Minkowski de **iteración 3** con ranura:
   868 MHz 82 × 82 mm, 2,4 GHz 41 × 41 mm (una pieza; dientes de ~0,4 mm a 2,4 GHz). En cola
   `scratchpad/cola_parche2.ps1` (los dos, tras `cola_100`; la Yagi comercial espera a todas).
   Corregido: `dimensionar` con `escalado` = 1 machacaba la masa manual (y cualquier medida de
   `ESCALABLES`) al volver a llamarla `ajustar`; ahora `fijos` respeta lo pasado explícitamente.
   Interfaz: banda nueva «433» (433,05–434,79); los canales LoRa sueltos van en «Otra» (el centro
   admite 3 decimales y el ancho 0,05 MHz; el usuario no quiere preajuste de LongFast). Todo lo demás ya escalaba con
   la frecuencia (`ESCALABLES`, separaciones del panel/Yagi en λ0).
   3. Después: Hilbert (868 y 2,4) y array 2×2 con malla adaptada; recalibrar las estimaciones
      (meandro ×1,18 en el alto; Sierpinski muy desviada).

0. **Nuevos tipos (01-11, petición del usuario)**: `dipolo` (SMA + balun impreso o coaxial al centro; recto o
   Koch), `colineal_coco` y `colineal_franklin` (`antenas/dipolos.py`). DRC limpio a 868 y 2441 MHz; malla y
   puerto comprobados. Tamaños a 2,4 GHz: dipolo 51 × 23 mm, COCO 18 × 139 (4 tramos), Franklin 45 × 148;
   a 868: COCO 18 × 378, Franklin 120 × 414 (las horquillas ensanchan). Sin simular: en la FIFO
   (`0002f`–`0002i`, a 2,4 GHz). Sin opciones de ajuste todavía (`sin_ajuste`).
   **Resultados (01-11 noche)**: Minkowski it3 2,4 GHz con ranura corregida: resuena en 2418 MHz (lado
   25,3 mm, la estimación falla un 11 %), pero Z ≈ 14 + 11j Ω sea cual sea la ranura (7,3–9 mm), S11 −4,7 dB,
   η 23 %, G −0,6 dBi: **no vale para el pedido**; el de 868 se paró (mismo problema y simulación larga).
   Si se retoma: con el borde a ~14 Ω la ranura no sirve (solo baja R); probar transformador λ/4 desde el
   borde con la R real. Yagi con boom de Koch con parásitos corregidos: tampoco va bien (al ajustar la
   adaptación movió el reflector a 0,39 λ0 y la resonancia a 2775 MHz; en 2441, −7,6 dB, 3,3 dBi y más hacia
   −y que hacia +y). Pendiente de estudiar; para el pedido se propone la **Yagi recta con 3 directores**
   (47 × 87 mm; el diagnóstico recto dio bien la dirección): `0002e1` en la FIFO.
   **Resultados de la noche (02-11, `_validacion4`)**: Yagi con boom RECTA 3 directores: 2392 MHz, −17,3 dB en
   2441, banda 2279–2510, **7,0 dBi hacia +y**, η 78 %; pero el ajuste llevó el reflector de 0,17 a 0,39 λ0
   para adaptar (lección 31) y la placa quedó en 48 × 116 mm (no cabe en 100 × 100). En la FIFO la de **2
   directores con reflector a 0,39 λ0 (47 × 96 mm)**: 2419 MHz, −12,3 dB en 2441, banda 2365–2474, G 6,7 dBi
   hacia +y, F/B 5,4 dB, η 73 %, placa 46,8 × 95,1 mm → candidata al pedido (pendiente de que el usuario
   diga si se exporta). Dipolo con coaxial exportado en `pedido_2G4/dipolo_coaxial_2G4`.
   El usuario pidió que cubra hasta 2482 MHz: en la FIFO, a 2450 MHz, (a) la de 2 directores con reflector a
   0,39 λ0, (b) 3 directores con reflector a 0,17 λ0 y transformador λ/4 (¿sigue radiando hacia atrás con el
   código actual?) y (c) 3 directores con reflector a 0,17 λ0 y **dipolo plegado** (nuevo, lección 45;
   47 × 87 mm, DRC limpio). Elegir la mejor de las tres para el pedido.
   Resultados: (a) 2445 MHz, banda 2363–2530 (−13,4/−18,4/−18,7 dB en 2400/2450/2483), **G 7,2 dBi**, η 75 %,
   F/B 7,3 dB → la mejor hasta ahora. (b) transformador: ya radia hacia delante (D +y 9,6, −y 1,6), G 7,0 dBi,
   pero banda estrecha 2425–2474 y η 55 %. (c) plegado: 2464 MHz, banda 2432–2496 (−6,2 dB en 2400), G 5,6 dBi,
   η 69 %, **F/B −3,6 dB (hacia atrás)**: peor. Gana (a): placa final 49,2 × 99,6 mm (justo bajo 100).
   **Exportada (a) para el pedido**: `salidas/pedido_2G4/yagi_recta_2dir_2G4` (DRC limpio, rótulo detrás).
   Pedido 2,4 GHz dentro de 100 × 100: 2 cupones + meandro, Sierpinski, Koch ajustable, J-pole de Koch,
   parche, dipolo con coaxial y esta Yagi. Dipolo con balun
   2466 MHz, −15,9 dB, 1,8 dBi, η 92 %; dipolo con coaxial 2464 MHz, −28,6 dB, η 96 %. Franklin 2365 MHz,
   −5,3 dB, solo 1,8 dBi (no da ganancia de colineal: revisar horquillas). COCO v1 no radiaba (lección 44):
   corregida: v2 (4 tramos, tramo 30,0 mm) 2430 MHz, −15,3 dB en 2441, D 4,7 dBi pero η 53 % → G 1,9 dBi
   (radia, pero las pérdidas del FR4 se comen la ganancia de colineal). Hilbert 2,4 (−2,7 dB, −1,7 dBi) y 868 (−4,6 dB,
   −0,5 dBi): resuenan pero adaptan muy mal sin red en π. Quasi-Yagi de Koch: hacia atrás, −3,5 dB.
   Yagi comercial con vías: 1856 MHz (sin vías 1843) frente a 2344 medidos: las vías no eran la causa.
   Recalibradas las estimaciones con todo ello.
   **Decisión del usuario (01-11)**: la Yagi de Koch sale del pedido; la quasi-Yagi de Koch (`0002c2`) se deja
   terminar por curiosidad, pero **no simular más Yagi fractales** por ahora.
   Array de parches 2×2 (02-11): la 1.ª iteración dio 2382 MHz y −18,2 dB (largo 28,6 mm); la 2.ª, 2105 MHz con
   el parche más corto (salto del centro de banda); parado. `ajustar` ya no itera la frecuencia en los arrays
   (como en el panel). Si se retoma: una simulación con el largo calibrado y mirar la ganancia frente a f.
   Antes: array de parches 2×2 parado a petición del usuario (5,5 M celdas de 0,2 mm: −6 dB de energía en 1,5 h,
   6–12 h por iteración); reencolado el último (`0008_array_parches_2x2_2G4_al_final`).
   **Yagi de Koch al revés: causa encontrada y corregida** (lección 42). Repetidas en la FIFO la Yagi con
   boom de Koch y 3 directores (`0002c1`) y la quasi-Yagi de Koch (`0002c2`), las primeras.
0. **Yagi con boom de Koch, 3 directores (01-11)**: ajustada a 2458,7 MHz (+0,7 %), banda 2434–2484, −10,8 dB
   en 2441, G 6,5 dBi, η 75 %, pero **radia hacia atrás** (7,7 dBi hacia −y, −1,9 hacia +y; lección 42). No
   pedirla hasta resolverlo: `0002c_diag_yagi_boom` en la FIFO (dipolo + reflector 1,05/1,30, recto y Koch).
   Si se confirma, dimensionar reflector y directores con el largo resonante de un elemento suelto (sin
   `K_DIPOLO_BOOM`) y revisar también la quasi-Yagi de Koch (también sale hacia −y).
   Minkowski it3 con ranura: primera simulación inválida (lección 43); repetidos `0002d` (2,4) y `0002e` (868).
   Calibración de estimaciones hecha (lección 41).
0. **Preparación para GitHub (04-11)**: hechos `README.md` + `README.en.md`, `LICENSE` (GPL-3.0, texto oficial
   sacado de la licencia de numpy), `LICENSE-DISENOS.md` (CC BY-NC 4.0 para los diseños publicados),
   `.gitignore` (sin Gerber, `salidas/`, `placas/`, cupones generados ni resultados derivados de placas de
   terceros), `fase0/README.md` corregido y código muerto quitado (`geometria.minkowski`,
   `exportar._piezas_cobre`). **Subido** al repositorio privado https://github.com/sqtactical/chirptenna
   (107 ficheros, sin Gerber). Renombrado a **Chirptenna** (04-11; descartados Fractalia —empresa española— y nombres con Fract-/Hertz por marcas). Logo en `docs/logo/` (grillo con antenas de Koch, `generar_logo.py`). Antes de hacerlo público: el usuario debe buscar «Chirptenna» en TMview.
0. **Release v0.1.0-alpha preparada (04-11)**: `CHANGELOG.md`, guías de instalación apuntando a Releases,
   `herramientas/comprobar_tipos.py` (32/32 bien: 16 tipos × 868/2441,75 MHz, DRC limpio, todos con logo) y la
   release creada en GitHub **como borrador** (pre-release; el usuario la publica, y al publicarla se crea la
   etiqueta `v0.1.0-alpha`). Para la siguiente versión: subir `antenas.__version__`, añadir sección al
   CHANGELOG, pasar `comprobar_tipos.py` y crear otra release.
0. **Preparación para publicar (04-11)**: interfaz solo en 127.0.0.1; `.claude/launch.json` y `settings.json`
   fuera del repositorio; **historial reescrito** (filter-branch) para quitar de todos los commits esos dos
   archivos con la ruta personal, y subido con `--force-with-lease` (los identificadores de commit cambiaron:
   el último antiguo era `b89a709`, el nuevo `aa7c6eb`). Copia del historial anterior:
   `%LOCALAPPDATA%\antenas\copia_git_20261104_145210.bundle`. Pendiente antes de hacerlo público: TMview,
   medir placas reales, capturas en el README, ordenar `RETOMAR.md` y decidir qué hacer con
   `vna/medidas` y `vna/calibraciones` (calibración de un latiguillo concreto, medidas de la Scout).
0. **Interfaz nueva, biblioteca, asistente del NanoVNA y aligerado (04-11, petición del usuario)**:
   - Interfaz por fases: barra fija (nombre, tipo, banda, «Guardar diseño»; naranja si hay cambios sin
     guardar) y pestañas Diseño / Simulación / Fabricar / Medir / Mis diseños. Probada en el navegador
     (cambiar tipo, aligerado, guardar, abrir desde la tabla, comparación de medidas, «Analizar»).
   - Biblioteca (`antenas/biblioteca.py`) en `Documentos\Chirptenna\disenos\<nombre>` (fuera del repo):
     `diseno.json`, `simulacion/` (se copia sola si el diseño estaba guardado y sin cambios al lanzar),
     `fabricacion/` (la exportación va ahí), `medidas/*.s1p` + `medidas.json` (etiqueta, origen, notas).
     Archivar = mover a `_archivados` (no se borra nada).
   - Asistente del NanoVNA (pestaña Medir, `vna/asistente_vna.py`): conectar (solo lee) → calibración
     guardada o nueva OSL guiada (rango sugerido ±40 % de f, máx. 2,7 GHz; guarda en `vna/calibraciones`)
     → comprobar con la carga (< −25 dB) → medir y guardar con etiqueta, o modo en vivo (ventana ±25 %,
     sin guardar) con resonancia, S11 en el objetivo y la acción sugerida; compara con la medida anterior.
     **Sin probar con el equipo**: hacerlo con el usuario delante.
   - Aligerado (`aligerado` en Yagi con boom, quasi-Yagi y panel): ventanas sin FR4 a `margen_aligerado` del
     cobre con nervios de `nervio` mm; aire en la simulación, Edge.Cuts interiores al exportar. DRC limpio en
     yagi_boom 2450 (8 ventanas, 47 % de FR4 quitado), quasi-Yagi (30 %), panel 2×2 (65 %), yagi_boom 866
     (69 %). **Sin simular** (el usuario pidió no simular de momento): el desplazamiento de frecuencia es
     desconocido; simular una Yagi aligerada antes de fabricarla.
0. **Cola FIFO (01-11, `herramientas/cola.py`)**, a petición del usuario: sustituye a las colas encadenadas
   del scratchpad. Orden cargado: verificar pedido 2,4 GHz → Minkowski it3 2,4 → Minkowski it3 868 → array
   de parches 2×2 → Hilbert 2,4 → Hilbert 868 → Yagi comercial con vías. Dos trabajadores arrancan al
   acabar el anillo R2G4 del cupón y la quasi-Yagi de masa 65 (`scratchpad/traspaso_fifo.ps1`).
   `python herramientas/cola.py ver` para ver el estado. Añadida `0002b`: Yagi con boom de Koch (iteración 2,
   3 directores, 38 × 96 mm, la de una captura del usuario: le interesa para el pedido). Ninguna Yagi con
   boom está simulada con las separaciones en λ0.
0. **Pedido a JLC (01-11)**: el usuario ya tiene los dos cupones en el carrito (FR4 1,6 mm, HASL). Quiere
   antenas de 2,4 GHz ya simuladas para él y deja las de 868 para beta testers de confianza.
   `salidas/pedido_2G4/` (`preparar_pedido.py`): meandro, Sierpinski, Koch con marcas, J-pole de Koch y
   parche rectangular, exportados con los parámetros de su simulación, sin red en π, DRC limpio. La
   Yagi con boom se quitó: sus separaciones ahora van en λ0 y los parámetros viejos dan 7 m de placa.
   Añadido `panel_dipolos_2x2_2G4` (disposición normal, la simulada hoy con el hilo: −15,7 dB, 12,7 dBi,
   η 78 %): placa 153 × 111 mm + reflector 202 × 160 mm a 30,7 mm (Gerber o DXF para chapa), DRC limpio.
   **El usuario no lo pide**: solo la placa de dipolos ya cuesta 13 € las 5. Para el pedido, priorizar placas
   ≤ 100 × 100 mm (las baratas de JLC).
   El Hilbert 2,4 de `cola_rehacer` corrió sin excitación (fusión de líneas, lección 37; corregido): repetido
   en `scratchpad/cola_hilbert24.ps1` tras `cola_rehacer`.
   **Verificación hecha (19:10, `salidas/pedido_2G4/verificacion.json`)**: meandro 2451 → 2520 MHz (+2,8 %,
   sigue cubriendo la ISM, −18,7 dB en 2441), Sierpinski −1,3 % (−22,9 dB), Koch ajustable +0,65 % sin
   cortar, J-pole de Koch +0,03 % (banda 2432–2489, −11,4 dB), parche +0,17 % (−13,1 dB, η 46 %): las cinco
   valen para el pedido. El usuario las pide tal cual (5 de cada; solo el Koch es ajustable; no quiere
   rehacer parche ni J-pole como ajustables). Minkowski it3 2,4 GHz: la estimación falla un 38 % (22 mm → 3380 MHz); va
   creciendo (36,7 mm en la 4.ª iteración), así que la placa ya no será de 41 mm.
   Era pendiente: `verificar` (simula cada placa exportada con el código actual) en `scratchpad/cola_pedido.ps1`
   (anillo R2G4 corregido → verificación → Minkowski it3 2,4/868 → Yagi comercial), tras `cola_100`.
0. **Cupones rehechos (01-11)** para el pedido a JLC: `cupon/cupon_A` y `cupon/cupon_B` (100 × 100 mm,
   DRC limpio, serigrafía con rótulo en cada SMA y leyenda detrás). En el sitio libre del B: CPWG de
   50 Ω (W 1,61, s 0,3, vías cada 3 mm; εeff 2,88 calculada) y microstrip de 100 Ω (W 0,69). Las líneas
   en L ahora miden 63,6 y 16,6 mm (L64/L17). **Anillo R2G4 corregido simulado: pico en 2,397 GHz (−0,1 %,
   S21 −14,6 dB)**; la corrección ×0,93 funciona. Pendiente: la placa C de antenas de referencia.
1. Cupones (plan original con el usuario; A y B ya hechos):
   - Partir el cupón en placas ≤ 100 × 100 mm (A: anillos 868 + 2,4; B: anillo 5,8 + líneas +
     THRU para TRL; C: antenas de referencia en subplacas con V-cut: monopolo recto 2,45 GHz,
     monopolo de Koch 2,45 GHz y monopolo de Hilbert/meandro 868 MHz).
   - Opcional en B: líneas de 100 Ω en dos longitudes y divisor en T (para arrays); CPWG si se
     van a meter pistas de RF en las placas de nodos.
   - Ajustar el radio del anillo de 2,4 GHz (×0,93) para que la simulación caiga en 2,4 GHz.
   - Las antenas de referencia de la placa C se generan con el programa de la Fase 1.
2. Fase 2: simular con openEMS cualquier antena del catálogo desde la interfaz y ajustar a la
   frecuencia (secante sobre el centro de banda a −10 dB), con diagrama y ganancia.
3. Medir εr con el cupón cuando llegue y meterla en `antenas/materiales.py`.
4. Uso de CPU: openEMS solo llega al ~40–50 % (i5-12500H híbrido 4P+8E: el FDTD está limitado por
   la memoria y cada paso espera al hilo más lento; los hilos de HT no ayudan). `ANTENAS_HILOS`
   fija los hilos de `simular` para correr dos simulaciones a la vez. Pendiente: medir con la CPU
   libre la velocidad con 4/6/8/12/16 hilos y elegir el reparto óptimo.
5. Velocidad de simulación (para más adelante; decidido seguir en CPU con openEMS, sin GPU):
   malla no uniforme ya implementada como opción (`malla='adaptada'`), pendiente de validar en la
   tanda 3. Otras ideas sin riesgo: iterar en
   «rápida» y última pasada en «normal», mejores estimaciones iniciales, criterio de fin −40 dB.
   Referencia: la J-pole de Koch tardó 44 min en el lote de validación 2.

## Cómo ejecutar

El entorno de Python está fuera del proyecto, en una ruta corta (la de la sesión superaba el
límite de 260 caracteres de Windows para las DLL de shapely):

```
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui/app.py      # interfaz en http://localhost:8080
```

Para recrear el entorno:

```
python -m venv %LOCALAPPDATA%\antenas\venv
%LOCALAPPDATA%\antenas\venv\Scripts\python -m pip install -r requirements.txt
%LOCALAPPDATA%\antenas\venv\Scripts\python -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS
```
