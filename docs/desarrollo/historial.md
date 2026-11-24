# Historial de desarrollo de Chirptenna (hasta el 04-11-2026, más la nota de traspaso archivada el 24-11)

> Diario de trabajo interno, tal como se fue escribiendo entre sesiones: validaciones, simulaciones,
> errores encontrados y decisiones. Tiene notas desordenadas u obsoletas (rutas del scratchpad, colas
> de simulación que ya no existen…). El estado actual y los siguientes pasos están en
> [`RETOMAR.md`](../../RETOMAR.md); lo estable y las lecciones aprendidas, en [`CLAUDE.md`](../../CLAUDE.md).

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
0. **v0.1.1-alpha publicada (04-11)**: igual que la 0.1.0 pero con el código en **AGPL-3.0** (la 0.1.0-alpha
   queda con GPL-3.0). **TMview comprobado por el usuario: nada parecido a «Chirptenna».** Repositorio aún
   privado. Plan acordado: alpha cerrado con los beta testers (recomendado: organización de GitHub gratuita
   y testers con permiso Read; en un repo personal los colaboradores tienen escritura) y alpha abierto
   (público) cuando haya medidas reales de las placas de JLC, capturas en el README y `RETOMAR.md` ordenado.
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

## Estado de `RETOMAR.md` archivado el 24-11-2026

> Texto de la nota de traspaso tal como estaba antes de reescribirla el 24-11 (escrito entre el 05-11 y el 23-11).
> Muchas cosas ya están hechas, publicadas o descartadas: el estado vigente está en `RETOMAR.md`.

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo
se ejecuta, reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md). El diario completo de lo
hecho hasta ahora (validaciones, simulaciones, fallos y decisiones) está en
[`docs/desarrollo/historial.md`](docs/desarrollo/historial.md). **Hacia dónde va el proyecto y en qué orden:
[`ROADMAP.md`](ROADMAP.md)** (11-11): fase 1 = medir cupones y antenas del pedido de JLC; después, consolidar (v0.4) e
integrar antenas en la PCB de un producto (v0.5). Las ideas pendientes de abajo (arrays, colineales) están recogidas allí. **Hechas el 11-11:** F1.1 (`docs/desarrollo/medidas/predicciones_2G4.md`: lo que predice la simulación para las 6 antenas pedidas con εr 4,2/4,5/4,8) y F1.2 (`herramientas/comparar_medida.py`). Siguiente: F1.3 (verificar la calibración del NanoVNA, con el usuario delante) en cuanto lleguen las placas; mientras, F2.2–F2.6.

## Estado

- **Cupón C en standby (23-11, por decisión del usuario)**: no se pide ni se toca hasta nuevo aviso. Estado: `cupon/generar_cupon.py C` ya genera el diseño con tres estructuras nuevas (S25: stub abierto de 25 mm en x = 32,5; LANZ_A: SMA con 4 mm de línea abierta en x = 67,5; LANZ_C: lo mismo en corto, borde de abajo, x = 85), DRC 0 infracciones; **sin commitear** (cambios en `generar_cupon.py`; los Gerber de `cupon/cupon_C/` son locales). Pendiente antes de pedirlo: (a) simulación 3D de la placa B entera (`cupon/simular_placa_B.py S30|S80`, relanzada el 23-11 con la línea de alimentación unida al cobre que empieza a 0,5 mm del borde) para ver si los vecinos o esos 0,5 mm explican el 6 % del S30; (b) simular el S25 con `cupon/simular_stub.py` y añadirlo a `REF_STUBS`/`er_fr4_stubs(largos=…)`; (c) decidir si se pide una segunda unidad para ver la dispersión del conector. La mesa de madera no explica nada (`simular_stub.py --mesa`: −0,02 a −0,09 %). La idea de medir εr(f) con los armónicos (868 MHz–2,6 GHz) queda anotada: el software ya admite `modo` 1–3 en `medir_stub`; falta una función que dé εr por resonancia y una curva εr(f).
- **Tipos planares nuevos (23-11)**: diez tipos en `antenas/planares.py`. Seis simulados a 2,4 GHz en GPU (`salidas/_barridos/NUEVO_*`): dipolo plegado −16,4 dB y log-periódica −22,7 dB (validados en simulación); Moxon −5,9 dB (Z 16 Ω), ranura −10,7, espiral −10,1 (23 MHz) y torniquete −21,8 dB con razón axial 12 dB (sin circularidad) siguen pendientes. Cuatro más con generador y DRC limpio, **sin simular**: `monopolo_uwb`, `parche_cp` (doble alimentación y meandro λg/4), `array_serie` y `antena_siw` (guía SIW de ~200 vías); sus constantes `K_*` no están calibradas. **Resultados del 24-11 (GPU parada; `salidas/_barridos/OPT_*`, `FUNC_*`, `NUEVO_*`)**: ranura optimizada −28,6 dB (η 73 %; `largo_stub` 12,7, `desplazamiento` 2,28, `ancho_ranura` 3,72); `array_serie` no adapta (−3,5 a −7,2 dB, η ~30 %; parada); `antena_siw` a 2,4 GHz adapta (−16,9 dB) pero η 12 %; torniquete y Moxon (también con `z_transformador` nuevo, 22–40 Ω: −5,6 dB) no funcionan; **espiral con `radio` ×1,9 (27,7 mm): razón axial 0,9 dB, η 87 %, 3,4 dBi, pero Z 40 − j52 Ω (S11 −5,8 dB): una L en serie de 3,3–3,6 nH da −19,6 dB en toda la banda (`herramientas/espiral_l.py`, por circuito; η 86 %, 3,1 dBi, RHCP delante)**; falta llevarla a un tipo con la bobina en la placa. Bandas RX (UAT 978, ADS-B, GPS L5, GNSS L1) centradas: el bowtie va mejor (−19 a −28 dB). Tipos añadidos sin simular: `yagi_cruz` (dos placas encajadas, dos puertos) y `yagi_bibanda` (2,4 + 5,8 GHz). Siguiente: calibrar `K_*` de `planares.py`, afinar la espiral grande, simular la Yagi bibanda con `barrido.py` (bayes) y actualizar `problemas.ESTADO` con lo anterior. HF aparcado (PCB de 100×100 mm: solo recepción o NFC viable). Rectenna sin hacer (lleva diodo, no se simula como S11). Sin empujar: commits locales desde `108f5e7`.
- **F3.1 hecha (12-11): antena integrada en una placa rectangular** (`antenas/integracion.py`; IFA, monopolo recto, Koch y meandro). Probada: IFA de 2,4 GHz en 30 × 50 mm, centrada en 2 simulaciones (2465 MHz, banda 2360–2575, η 88 %; la suelta da 2430 MHz y η 90 %), verificación de malla «estable». DRC limpio. **F3.2 hecha en parte (12-11)**: tabla en `docs/desarrollo/integracion_ifa.md` (IFA bien; el meandro integrado no adapta). **F3.3 hecha en parte (12-11)**: huella `_integrar` y placa de ejemplo (DRC limpio); `kicad-cli` no aplica la zona de exclusión de una huella al rellenar, así que **falta que el usuario la pruebe en KiCad con interfaz** (ver `fase3.md`). **F3.4 hecha en parte (12-11)**: `conector` = «Pad de RF» (sin CPWG ni punto de prueba U.FL). **F3.7 hecha (12-11)**: entorno en la simulación (carcasa −6,6 %, mano −3,7 %, batería +6 % en un monopolo de 2,4 GHz). **F3.9 hecha (12-11)**: «Analizar tolerancias» (monopolo cubre, parche no). **F3.10 hecha (12-11)**: consejos «integración» y capítulo 14 del manual (es/en; el caso de 868 MHz en 40 × 80 mm no cabe, documentado). **F3.5 hecha en parte (12-11)**: sustrato de 4 capas JLC04161H-7628 con IFA integrada (2418 MHz, 205 MHz de banda; εr 4,4 de una transcripción de la calculadora de JLC, **comprobar**). **F3.6 hecha en parte (12-11)**: importar `.kicad_pcb` (botón en el modo integrado; **falta una placa real del usuario**). **F4.2 hecha en parte (12-11)**: botón «Calcular red de adaptación» por circuito (monopolos con red en π; sin comprobar con FDTD, que depende de F4.1). **Interfaz renovada (13-11)**: nuevo aspecto (variables CSS en `gui/app.py`, ver lección 47); pendiente regenerar las capturas del README (`docs/capturas/`). **F4.5 hecha (12-11)**: informe PDF (`antenas/informe.py`, botón en Fabricar sin probar con clic; `herramientas/prueba_informe.py`). **F4.6 hecha (12-11)**: CSV del diagrama (`antenas/diagrama.py`, botón en Simulación sin probar con clic; falta el formato de la herramienta de cobertura del usuario). Fase 4 agotada salvo F4.4 (hardware) y lo que quedó en parte. **F4.3 hecha en parte (12-11)**: el asistente da piezas, banda y peor caso ±5 % (falta una antena real adaptada por el usuario; F4.4 bloqueada sin hardware). **F4.1 hecha en parte (12-11)**: parámetros `z1/z2/z3`; serie y bobinas en la FDTD, condensadores a masa por circuito (la FDTD no los reproduce); **la red calculada por F4.2 da −10,3 dB simulada frente a −38 dB por circuito**: falta llevar los parásitos (hueco, vía, isla) al circuito. F3.8 (antena chip) está bloqueada: necesita modelo y hoja de datos del usuario; de fase 3 solo quedan sus pruebas con placas reales. Después, fases 1 y 2 pendientes de hardware (NanoVNA, placas JLC).
- **Simulaciones GPU de la v0.2.0 terminadas (06-11)**: lotes en `salidas/_validacion_gpu*` y `_afinado_panel`.
- **v0.2.0-alpha preparada en la rama local `v0.2.0`** (worktree `%LOCALAPPDATA%\antenas\wt-v020`; fusiona `main` con
  bowtie, `i18n` y `gpu-pruebas`): idiomas es/en/fr/de + lora en escritorio y web, bowtie, GPU opcional, estados al día
  con ~50 simulaciones nuevas, `MANUAL.en.md`, versión 0.2.0-alpha y `CHANGELOG.md`. Probada: `comprobar_tipos` 46/46,
  `prueba_interfaz` (todos los idiomas) y `prueba_web` 32/32 con el cambio de idioma. **Sin empujar, etiquetar ni publicar**:
  falta el visto bueno del usuario (`git push`, `gh release create v0.2.0-alpha --prerelease`, y `gpu-pruebas` ya está
  publicada). Antes de publicar: fusionar `v0.2.0` en `main` (`main` local lleva además el commit de los bowtie).
- **Tipos y bandas añadidos tras la preparación (06-11)**: bowtie como tipo propio, bandas 915/1,2 GHz/GPS L1/Iridium/5,8 GHz, 8 tipos sin validar (`parche_circular`, `parche_ranura`, `parche_apilado`, `ifa`, `pifa`, `dipolo_sleeve`, `vivaldi`, `colineal_dipolos`) y el conector «coaxial soldado». **Pendientes de validar en simulación** (el usuario lo hará el fin de semana): `CLAUDE.md` lecciones 53–55. `dipolo_sleeve` es casi un monopolo recto con masa estrecha: se deja por ahora. Idea sin hacer: colineal con coaxial real a lo largo de la placa (openEMS solo modela el coaxial como puerto).
- **Campaña de barridos en GPU terminada (07-11)**: `herramientas/campana.py` (etapas A y B, 7 bandas) y la cola de pruebas (`cola_extra.py`). Resultados crudos en `salidas/_barridos/*` y la tabla en `docs/desarrollo/barridos_gpu.md` (`python herramientas/resumen_barridos.py` la regenera). Conclusiones en `CLAUDE.md` lecciones 61–63; estados ya en `problemas.py` y los README. Recalibradas las estimaciones (`calibrar_estimaciones.py`, 07-11; reiniciar la interfaz). Si C: se llena: parar las campañas, vaciar `%TEMP%\antenas_sim` (permiso del usuario) y relanzar. Flujo de GPU en GitHub Actions (`compilar-gpu.yml`) funciona; zip de 12 MB en la release. Opción en el instalador hecha el 12-11 (paso 6 de `instalar.ps1`); pendiente probarlo en otra GPU.
- **Idea pendiente: más tipos de arrays (06-11)**: ver otras disposiciones además del 2×2 y 4×4 del panel (`panel_dipolos`): **2×1, 3×3, 1×N en columna**, etc., **con y sin reflector**. Sin reflector sale un array omnidireccional (collinear) o bidireccional, y no cancela la banda baja de una antena de dos bandas. Interés principal: **868/915 MHz + 2,4 GHz** con elementos bowtie de Sierpinski. Notas de la discusión: el elemento de dos bandas solo se ha comprobado con el *monopolo* de Sierpinski (`multibanda`), no con el bowtie; para dos bandas hay que usar una red de alimentación de **caminos iguales** y de banda ancha (los transformadores λ/4 del panel actual son de una sola banda); la separación entre elementos la fija el tamaño del elemento a 868 MHz (~120 mm), que a 2,4 GHz es ~0,98 λ (al límite de los lóbulos secundarios) y a 868 MHz solo ~0,35 λ (casi sin ganancia de array); el reflector a λ/4 de 2,4 GHz (31 mm) está a 0,09 λ de 868 MHz y anula la radiación de la banda baja. Empezar por el bowtie de Sierpinski solo (¿el armónico cae a ~3×?) y después un 2×1 sin reflector con `herramientas/barrido.py`.
- **Idea pendiente: colineales con elementos bowtie y colineales acortadas con fractales (06-11)**: (1) una **colineal con elementos bowtie** (o de Sierpinski): parámetro de forma de los brazos en `colineal_dipolos` (tira, bowtie, Sierpinski), que da más banda y ~20 % menos largo por elemento (a 868 MHz: dipolo 132 mm, bowtie 105, Sierpinski 100 a lo largo del eje; el ancho pasa de 58 a ~93 mm); (2) **acortar una colineal convencional con fractales**: en la U de microstrip (`colineal_dipolos`) y en la COCO, cargar las líneas de fase o los tramos con Koch/meandro (más longitud eléctrica en menos longitud física), porque lo que domina el largo son los tramos de λg (a 868 MHz: 188 mm cada uno, placa de 722 mm con 4 dipolos), no los elementos; con la COCO la fase invierte cada λg/2, así que el tramo debe conservar su longitud eléctrica. El Sierpinski solo gana ~5 % de largo sobre el bowtie liso: por sí solo no compensa en monobanda, su interés es la doble banda 868/915 + 2,4 GHz (el armónico impar mantiene la fase en una colineal con razón ≈ 3). Se barre con `herramientas/barrido.py`; ver también la nota de arrays.
- **Cola 2 de arreglos y bibanda (07–08-11, terminada en parte; ver `docs/desarrollo/resultados_07-11.md`)**: los resultados ya están en `problemas.py`, los README, el CHANGELOG y `CLAUDE.md` (lecciones 64–66). Llegan a −10 dB en simulación: J-pole recta a 868 MHz, J-pole de Koch a 1,2 GHz, parche con ranura a 5,8 GHz, colineal de dipolos a 2,4 GHz, Yagi con boom a 5,8 GHz y, en 868 MHz + 2,4 GHz, **dos J-pole unidas** (diseño del usuario) e **IFA con segunda rama** (herramientas `jpole_dual.py` y `rama_dual.py`, aún fuera de la interfaz). No van: J-pole bibanda de Koch, J-pole en abanico, J-pole recta a 5,8 GHz y parche circular (GPS L1 y 2,4 GHz). Sin medir con el NanoVNA.
- **Versión publicada: v0.4.1-alpha** (16-11: colineal modular, capturas y manual nuevos; antes v0.4.0-alpha, 13-11; pre-release en GitHub con la web publicada a mano con `web.yml`; el flujo de la release falló como siempre; CI verde en `d87d3e2`;
  código AGPL-3.0; la v0.1.0-alpha salió con GPL-3.0). Antes: v0.3.0-alpha (09-11), v0.2.0-alpha (06-11) y v0.1.x. **Colineal modular (15-11)**: `colineal_dipolos` con `modular` = 1 (placas inicio/módulo/final con encaje, exportación por placa; cadena de 4 en FR4 −12,9 dB, 4,0 dBi, η 61 % a 2,4 GHz; a 868 MHz sin centrar; unión soldada sin simular; ver `docs/desarrollo/colineal_modular.md`). Capturas del README y manuales rehechas con el diseño nuevo el 14-11 (`herramientas/capturas_readme.py`), sin publicar aún. Repositorio **público** desde el 04-11 (alpha abierto). Nombre comprobado en TMview: libre.
- **Sustrato personalizado (16-11, sin publicar)**: opción «Personalizado…» (εr, tanδ, grosor) en escritorio y web, y PTFE de JLC con 0,76 y 1,52 mm (del usuario, sin confirmar) y `Sustrato.er_tol` del datasheet (CLAUDE.md lección 82). **Falta**: confirmar en JLC los grosores del PTFE y qué materiales hay en stock; medir un cupón de PTFE. Yagi con boom modular anotada en ROADMAP («Ideas a más largo plazo»).
- **Ideas de antenna-forge hechas (16-11, sin publicar)**: optimización bayesiana en `barrido.py --modo bayes`, método de momentos de hilos (`antenas/hilos.py`, `herramientas/preseleccion_hilos.py`), comprobaciones contra el libro (`pruebas/test_verdad.py`, `herramientas/verdad.py`), `docs/ESTADO_REAL.md` generado y el aviso de polarización que ya no falla en silencio (CLAUDE.md lección 80, CHANGELOG «Sin publicar»). **MATLAB ya tiene Antenna Toolbox (16-11)** y es un segundo motor en la interfaz (selector «Motor», `antenas/simular_matlab.py`, CLAUDE.md lección 81): dipolo y monopolo concuerdan con openEMS en directividad, MATLAB sale 3–9 % alto en frecuencia; **el parche no concuerda** (2,6 frente a 6,2 dBi; la malla de 1,5 mm no acaba). 147 pruebas. **Falta**: (a) probar `--modo bayes` en una Yagi real (`preseleccion_hilos.py yagi` da el comando) y comparar con el barrido en rejilla de `docs/desarrollo/barridos_gpu.md`; (b) descubrir por qué MATLAB no da bien el parche (¿malla en el sustrato fino?, ¿alimentación por sonda frente a línea?) o dejarlo marcado como no fiable; (c) el modo «ambos» ya se probó por `simular_cli` con el dipolo (openEMS 2469 MHz, 2,34 dBi; MATLAB 2675 MHz por centro de banda, 1,81 dBi: la interfaz lo marcaría como «difieren»); falta verlo pintado en el navegador y con una antena ajustada. `PCBWriter` y `pcbComponent` ya probados (lección 81): Gerber incompleto y parche inestable; queda `PCBReader` (importar nuestros Gerber) y el solver FEM.
- **Programa completo de principio a fin**, validado **solo en simulación** (εr 4,5 supuesta):
  - 25 tipos de antena (8 de ellos nuevos y sin validar); `herramientas/comprobar_tipos.py` los genera y exporta a 868 y 2441,75 MHz con DRC limpio.
  - Simulación y ajuste con openEMS.
  - Exportación KiCad/Gerber/DXF con logo e inscripciones a elegir.
  - Ajuste tras fabricar.
  - Asistente del NanoVNA.
  - Biblioteca «Mis diseños», modo oscuro, instalador de Windows y guía paso a paso.
- **Validados en simulación:** monopolos recto/meandro/Koch (2,4 GHz y 868 MHz), Sierpinski, dipolo, J-pole de
  Koch, Yagi con boom recta (7,2 dBi), panel 2×2 (12,7 dBi) y 4×4 (16,6 dBi), parche rectangular.
- **Problemas conocidos:** `antenas/problemas.py` y la tabla de los README. Son la J-pole recta, Franklin,
  quasi-Yagi y Yagi de Koch, Minkowski it. ≥ 2, Hilbert sin red en π, IPEX y el aligerado sin simular.
- **Pedido a JLC hecho** (2,4 GHz, FR4 1,6 mm, HASL), en `salidas/pedido_2G4/`, exportado antes del logo:
  - los cupones A y B;
  - meandro, Sierpinski, Koch ajustable, J-pole de Koch y parche;
  - el dipolo con coaxial;
  - la Yagi recta de 2 directores.
- Medidas y calibraciones del NanoVNA: locales (`vna/medidas`, `vna/calibraciones`, fuera del repositorio).

## Siguientes pasos

**Carcasa 3D (21-11, sin commitear):** `antenas/carcasa.py` (STL base y tapa, bloques para simular), tarjeta «Carcasa 3D» en Fabricar y casilla «Ajustar y simular con la carcasa» en Simulación (`simulacion.ENTORNO_FIJO`, lección 91). Probado con un dipolo: ajusta a +0,9 % con carcasa de PLA (−4,6 % respecto a sin ella). Pendiente: imprimir una y medir dentro de ella; εr/tanδ de PLA/PETG sin medir; sin vista previa 3D en la interfaz; no hay versión web (shapely de Pyodide < 2.1).

**Conexión con Chirptenna VNA (20-11, sin commitear):** `s11_simulado.s1p` por simulación, botones «.s1p simulado» y «Abrir Chirptenna VNA» en Medir, `?f=&banda=&nombre=` en la web VNA. Pendiente: pendiente de εr por placa en el puente (la hoja de medidas usa `SENS_er_pedido`, no (εr+1)/2), abrir `diseno.json` en la web VNA, aviso de puerto serie compartido ya puesto.

1. **Alpha abierto** (el usuario no quiere esperar a las medidas):
   - **Hecho (17-11): panel 2×2 con retardo y `array_fase`** (lecciones 87 y 88; resultados en `docs/desarrollo/colineal_modular.md`, apartado «Retardo de fase con alimentación separada»). **Ninguno inclina el haz**: el panel (con y sin vías) queda a 0–9° del frente con ±40°, y `array_fase` (FR4, tramo de 20 mm: −12 dB a 0°) no mueve el haz con +40°. Sin vías el panel adapta 2,5–3,6 dB mejor. Causas sin separar: el meandro radia o acopla, el λg real, el haz ancho de 2 elementos. `array_fase` en PTFE no adapta (falta calibrar `K_ARRAY_FASE`). Siguiente si se insiste: simular el meandro aislado o probar 4 elementos.
   - **Hecho (17-11): colineal con línea plegada** (`linea_plegada`): −28 % de largo, −19,7 dB, 4,8 dBi y sin lóbulos de rejilla (`colineal_modular.md`); es lo mejor de la colineal en serie. Pendiente: probarla en módulos y a 868 MHz, calibrar la frecuencia con Koch. **Hecho (17-11): colineal con U de Koch** (`forma = 3`; resultados en `colineal_modular.md`): la iteración 1 acorta la placa un 18 % pero ensancha y adapta peor (−9,8 dB); falta calibrar su frecuencia y probar el módulo. Pendiente de estudio: antena UWB de 50 × 50 mm (ROADMAP). **Versión 0.5.0-alpha preparada (17-11, sin etiqueta ni release; commit local):** versión en `antenas/__init__.py`, READMEs y CHANGELOG. Estimaciones 3D calibradas en GPU (reflector centrado: −14 dB, 10,95 dBi; diedro ≤ 7 % bajo; hélice normal resuena pero −2 dB: falta red de adaptación). Falta: etiqueta `v0.5.0-alpha` y release, que el usuario decide. **Hecho (17-11): 3D centrados en GPU** (`docs/desarrollo/tridimensional.md`): `diedro` adapta con todos los ángulos (−15…−20 dB; la resonancia sube al cerrar la V: alargar brazos), `reflector_esquina` 90° −13 dB y 10,9 dBi, `helice_normal` no adapta (−1 dB: calibrar `K_HELICE_NORMAL`). La cuadrifilar sigue sin simulación.
   - **Hecho (17-11): cadenas `0019`–`0023`** terminadas (resultados aún sin apuntar en `colineal_modular.md`). Cola vacía salvo `0008_array_parches`, colgada en `en_curso` desde el 02-11.
   - **Pendiente (16-11): estudio de la inclinación del haz** (`inclinacion` de la colineal; lección 86), **primer estudio hecho y apuntado** en `docs/desarrollo/colineal_modular.md` (el haz se inclina en el sentido esperado; en PTFE +15° da 15°; en FR4 hace falta `factor_linea` ≈ 0,88). **Cola de GPU PARADA el 16-11 a petición del usuario** (trabajador detenido, `gpu.lock` borrado, `0019` devuelta a pendientes): quedan `0018c1–8` (inclinación centrada por separado) y las cadenas `0019`–`0023`; reanudar con `python herramientas/cola.py trabajar --hilos 6` y `mantener_despierto.ps1`. `0008_array_parches` sigue colgada en `en_curso` desde el 02-11.
   - **Hecho el 16-11, sin commit:** los cuatro tipos de varias placas (`diedro`, `reflector_esquina`, `helice_normal`, `helice_cuadrifilar`; `docs/desarrollo/tridimensional.md`, lección 85 de CLAUDE.md). Probados a 2,4 GHz con CPU y malla gruesa; falta centrarlos y simularlos en GPU con malla fina (nada en la cola), probar la V según el ángulo y medir. La web no tiene vista 3D.
   - **Pendiente (16-11, cola de GPU):** colineal alternada con la separación corregida (0018a1–3 en %LOCALAPPDATA%\antenas\cola: bowtie FR4, bowtie PTFE, Sierpinski FR4, centradas): ver si el haz sale perpendicular a la placa y con cuánta ganancia (antes 2,5–2,8 dBi en FR4, 6,5 dBi en PTFE). Detrás van las cadenas en serie centradas (0018–0023). Resultados a docs/desarrollo/colineal_modular.md. Cambios sin commit: dipolos.py, tipos.py, docs. La entrada 0008_array_parches lleva desde el 02-11 en en_curso (colgada).

   - [x] Capturas en los README (`docs/capturas/`).
   - [x] `RETOMAR.md` ordenado.
   - [x] Descripción y temas del repositorio.
   - [x] Medidas y calibraciones fuera del repositorio.
   - [x] Repositorio público (04-11) con imagen para compartir.
   - [x] `main` protegida (ruleset «Proteger main»: sin borrados ni `push --force`).
   - [x] Secret scanning, push protection, Dependabot, aviso privado de vulnerabilidades y `SECURITY.md`.
   - [x] Discussions activadas (enlazadas desde la página de nueva issue).
   - [ ] Opcional: pedir a GitHub que purgue los commits antiguos de antes de reescribir el historial (tenían el usuario de Windows).
   - [ ] Anunciarlo (comunidad Meshtastic: foro, Discord, Reddit) pidiendo medidas reales.
2. **Cuando lleguen las placas de JLC:**
   1. Medir los cupones y meter la εr real en `antenas/materiales.py`.
   2. Medir las 7 antenas y comparar simulado frente a medido.
   3. Recalibrar las estimaciones (`herramientas/calibrar_estimaciones.py`).
   4. Poner las curvas medidas en el README.
   5. Probar el asistente del NanoVNA con el equipo (con el usuario delante).
   6. Sacar la v0.3.0-alpha con las medidas (la v0.2.0-alpha sale antes, con idiomas, bowtie y GPU).
3. **Pendientes técnicos** (detalle en el historial):
   - **Máscara en la simulación**: las antenas exportadas y los cupones llevan máscara encima del cobre (solo se
     abre en los pads para soldar), pero `simulacion` no la modela. Añadir una capa de ~20 µm (εr ≈ 3,8, tanδ ≈ 0,025)
     y validarla con las medidas de JLC (se espera −0,5 a −3 % de frecuencia, más en meandro/Hilbert/Koch).
     Tenerlo en cuenta al sacar la εr de los cupones (la medida ya incluye la máscara).
   - Yagi aligerada: simulada a 2,4 GHz (G 5,9 dBi, S11 −10,8 dB: reajustar el reflector); falta a otras bandas.
   - Panel: con malla fina fija el haz sale de frente (0–3°): la inclinación de 9° era un artefacto de la malla (la
     frecuencia depende de la malla hasta un 10 %: el barrido de `barrido_panel.py` fija el paso). Proponer
     `simetrico` = 0 por defecto: no corrige nada y empeora S11. Panel 4×4, 1 elemento y 868 MHz sin afinar. Sierpinski it. 1–3 equivalentes en el 2×2; COCO a 868 MHz no sirve.
   - J-pole recta (adapta mal), Franklin (revisar horquillas), Minkowski it. 3 (borde a ~14 Ω: probar
     transformador λ/4), transición IPEX, quasi-Yagi de Koch (radia hacia atrás).
   - Calibrar εeff(h/λ) a 868 MHz (monopolos, Yagi, J-pole) y validar más tipos fuera de 2,4 GHz.
   - Placa C de cupones (antenas de referencia).
   - Yagi comercial: la simulación no coincide con la medida (1856 frente a 2344 MHz); aparcada.
   - Rendimiento: reparto óptimo de hilos de openEMS (`ANTENAS_HILOS`).
4. **Bowtie de Sierpinski: implementados como opciones (05-11, rama `gpu-pruebas`), pendientes de simular.** Sin
   catálogo propio todavía: `dipolo` con `forma` = 1 (bowtie) o 2 (bowtie de Sierpinski, `iteracion_s`, `apertura`) y
   `panel_dipolos` con `elemento` = 0/1/2 y `tamano` = 1 (un solo elemento sobre reflector, sin red), 2 o 4. Pasan
   DRC y reglas de JLC (18/18 en `comprobar_tipos.py`, que ahora incluye `VARIANTES`) pero **el tamaño inicial sale de una
   estimación sin calibrar** (K = 0,85) y no se ha simulado ninguno: el lote `salidas/_validacion_gpu` los simula en GPU.
   Si pasan, darles entrada propia en la galería (bowtie, bowtie con reflector, array de bowtie) y calibrar la estimación.
   Texto original del plan: (decidido el 05-11). Objetivo: tolerancia a desajustes
   (εr, máscara, caja) gracias a su ancho de banda, no más ganancia. Sacarlos como experimentales en
   `problemas.py` hasta simularlos.
   1. **Bowtie sola** (dipolo de Sierpinski): parámetro «forma» del `dipolo` (recto / Koch / Sierpinski).
      Reutilizar su alimentación (balun impreso o coaxial al centro) y el `cuello` del Sierpinski (lección 26).
      Impedancia esperada ~100–200 Ω: hará falta un balun 4:1 o un transformador λ/4.
   2. **Bowtie + reflector**: elemento Sierpinski en el panel (`panel_dipolos`, 1 elemento) aprovechando el
      reflector, el coaxial pasante y la placa del reflector. Esperado ~7–9 dBi y buen delante/detrás. La más
      interesante para nodos fijos de 868 MHz.
   3. **Array 2×2 y 4×4 de bowties sobre reflector**: con la red corporativa del panel. Misma ganancia que el
      panel de dipolos (~13 / ~18 dBi en teoría); la ventaja sería más banda. A 868 MHz solo tiene sentido el
      2×2 (~50 × 50 cm); el 4×4, a 2,4 GHz (~35 cm). Vigilar el acoplo y la inclinación del haz (lección 36).
5. **A estudiar: reducir las pérdidas del FR4 sin pasar a Rogers** (05-11). Solo importa donde el campo va por
   dentro del sustrato: parches (η 23–47 %), COCO (53 %) y redes de los arrays y paneles (~1–2 dB en el 4×4).
   Monopolos, dipolos, Yagi y J-pole ya están en η ~85–90 %: no compensa tocarlos.
   - **Parche suspendido**, la opción principal: el parche en una placa fina sobre un hueco de aire de unos mm hasta
     la masa, con separadores. Se espera η ~80–90 % y más banda. Sería un tipo nuevo con dos placas, como el
     panel con su reflector: la del parche y la de masa con el conector, más los taladros de los separadores.
   - Ranuras fresadas donde va el campo (entre pistas del meandro/Hilbert, huecos de la COCO, bordes radiantes),
     como el aligerado de la Yagi/panel.
   - Arrays y paneles: alimentar con latiguillos coaxiales, o solo la red en una placa de RO4350B.
   - Mantener 1,6 mm en RF y líneas de 50 Ω cortas.
6. **A estudiar: ideas de [antenna-forge](https://github.com/1ove9/antenna-forge)** (05-11; MIT, compatible con
   AGPL citándolo). El proyecto anuncia más de lo que tiene hecho (IA generativa sin conectar, simuladores comerciales en
   la hoja de ruta) y su Yagi de 5 elementos con +12,6 dBi parece alta: comprobar antes de reutilizar nada.
   - **Comprobación de «respuesta conocida» en la CI** (barata, interés alto): trabajo semanal que simula el dipolo
     y el monopolo de referencia en precisión rápida y falla si se salen de lo validado en `fase0` (L/λ, R ≈ 72 Ω,
     3,1 dBi). Protege `simulacion.py`, sobre todo antes de añadir la máscara.
   - **Pruebas con `pytest`**: empezadas el 12-11 (`pruebas/test_nucleo.py`, 68 pruebas). Faltan `leer_s1p`, el desembebido de la
     línea, `normalizado` (E24) e invariantes de la geometría (contorno válido, cobre dentro del margen).
   - **Optimización de varios parámetros a la vez** (bayesiana, 20–50 simulaciones; no evolución diferencial):
     reflector, directores y separaciones de las directivas buscando ganancia + delante/detrás + S11, lanzada de
     noche con `cola.py`. Después de tener medidas reales.
   - **NEC2 (`necpp`) como preoptimizador rápido** de la Yagi (no modela el FR4: solo con factor de velocidad) y
     posible tipo nuevo: Yagi de varillas metálicas para 868 MHz. Después de tener medidas reales.
   - Descartado: IA generativa, infraestructura de servidor, simuladores comerciales y 3D completo.
7. **Aceleración por GPU de openEMS** (guía de compilación para NVIDIA en Windows: [`docs/GPU.md`](docs/GPU.md), reconstruida a partir de lo instalado; **falta verificarla compilando de cero** y automatizarla con un script; ojo: el plugin se compiló solo para `sm_86`, hay que poner la arquitectura de cada tarjeta). Notas históricas: (05-11; lo comentó Jorropo en Discord: de 150 a 4700 MC/s con una
   Intel Arc A770). Comprobado en [thliebig/openEMS](https://github.com/thliebig/openEMS): **existe, pero solo en
   `master`; la v0.37.0 que usamos no lo trae**, así que hay que compilar openEMS desde git.
   - Estado (a 05-11): motor `--engine=gpu` fusionado en `master` el 17-10 (commit `c3a956b`, backends **HIP**, que en
     Windows se compila como CUDA con `OPENEMS_HIP_AS_CUDA`, y **Metal**). Backends como plugins cargables.
     **SYCL (Intel, Arc/Level Zero)** en la PR [#243](https://github.com/thliebig/openEMS/pull/243), en borrador
     (plugin `openEMS_gpu_sycl`, se compila con `icpx` de oneAPI). Hay también PR de nf2ff con CUDA (#233).
   - Uso: `openEMS caso.xml --engine=gpu`. Sin GPU utilizable falla (no vuelve solo a la CPU).
     `--engine=gpu-reference` es una referencia en CPU para pruebas.
   - Ganancias publicadas (MC/s, no comparables entre equipos): Arc B580 SYCL 13 374 (ideal) y 8 013 (PML) frente a
     703 y 305 de una CPU Ultra 9 285K; RTX 3060 portátil 15–94× sobre la CPU multihilo (más con materiales
     dispersivos); RX 6800 ~12–19×; **Apple M4 ~1×** (no compensa). Con un caso real (antena LTE, 28,7 M celdas):
     209 → 1 950 MC/s en la B580. Los resultados son idénticos bit a bit a la CPU en los casos probados.
   - Qué instalar para compilarlo (según la GPU; lo indicó la misma persona de Discord): **AMD** ROCm; **NVIDIA** CUDA
     + HIP; **Apple Silicon** Metal integrado, sin toolkit; **Intel Arc** oneAPI + la PR #243 de SYCL (borrador).
     Benchmark de comparación en el propio repositorio: `benchmark/README.md`. Medidas de esa persona (con algunos
     parches): Arc A770 ~4 200 MC/s, RX 6600 ~2 270, Ryzen 5 3600 (CPU) ~183, es decir ~12–23× sobre la CPU.
     Para comparar con nuestras simulaciones, usar siempre MC/s con el mismo caso.
   - Interés para Chirptenna: alto. Ajustar es iterativo (1–3 simulaciones por tipo; la Hilbert a 868 MHz tarda >3 h
     por iteración). Con 10× serían minutos.
   - **Progreso (05-11)**, todo fuera del proyecto en `%LOCALAPPDATA%\Programs\gpu-build` (sin admin): CMake, Ninja,
     CUDA 12.9 redistribuible (nvcc, cudart; sin instalar), cabeceras HIP 7.2.4 y vcpkg. Compilados `fparser`,
     `CSXCAD` y `openEMS` de `master` (`opt\bin\openEMS.exe`, solo CPU). **Bloqueado:** el plugin `openEMS_gpu_hip_nvidia`
     no se construye porque `nvcc` 12.9 no soporta el MSVC 14.51 de Visual Studio 18 (`cudafe++` da ACCESS_VIOLATION).
     Hace falta un MSVC 14.4x (VS 2022 17.x): instalarlo desde el instalador de Visual Studio (componente «MSVC v143»)
     o bajarlo portable; después, configurar con `-DCMAKE_CUDA_HOST_COMPILER=` apuntando a ese `cl.exe`.
     Cuando funcione: la API de Python de `master` admite `FDTD.Run(..., engine='gpu', gpu_device=0)`, pero el wheel 0.37
     no: o se recompila el wheel o se genera el XML con `setup_only=True` y se llama a `openEMS.exe --engine=gpu`.
   - **Resuelto (05-11): compilado y funcionando** en la rama local **`gpu-pruebas`** (no subida a GitHub). Ver
     `antenas/gpu.py` (`ANTENAS_GPU=1`, `OPENEMS_GPU_DIR`), la casilla «Aceleración por GPU (experimental)» de
     Simulación y `herramientas/comparar_gpu.py <tipo…> [--radiacion]`. Lo que hizo falta: **MSVC 14.44** portable
     (con `vsdownload.py` de msvc-wine, en `gpu-build\msvc17`) porque nvcc 12.9 se cae con el 14.51 de VS 18, y copiar
     junto al `openEMS.exe` las DLL de vcpkg y `cudart64_12.dll`. Como el wheel 0.37 no elige motor, se escribe el XML
     con `FDTD.Write2XML` y se llama al `openEMS.exe` de `master` con `--engine=gpu`.
   - **Medidas en la RTX 3050 Laptop (4 GB), 2,44 GHz, precisión normal, con diagrama** (CPU 0.37 → GPU):
     monopolo recto 0,78 M celdas 203 → 15 s (13×); Koch 1,81 M 266 → 26 s (10×); meandro 2,82 M 680 → 60 s (11×);
     dipolo 4,59 M 1 063 → 95 s (11×). Diferencias GPU–CPU: f de resonancia ≤ 0,06 %, S11 ≤ 0,6 dB en el máximo
     (≤ 0,1 dB salvo Koch), Z ≤ 3 Ω, ganancia ±0,1 dBi, eficiencia ±0,5 %. No es idéntico bit a bit (el 0.37 y el
     `master` difieren), pero queda por debajo del error de ajuste.
   - **Corrección:** las primeras medidas (arriba) salieron con antenas sobredimensionadas porque el script pasó MHz a
     `tipos.dimensionar`, que trabaja en **Hz** (el parche salió de 27 km y el motor abortó; no es un bug del
     repositorio). Los monopolos topaban con el límite del parámetro. Sirven para comparar CPU y GPU sobre la misma
     geometría, pero no representan el tamaño real: se rehacen en `salidas/_comparar_gpu/` con tamaños reales.
   - Por hacer, en orden (los pasos 1–3 hechos en la rama; faltan 4–5 y revisar el parche):
     1. Mirar qué GPU tiene el usuario y si hay que compilar HIP/CUDA (NVIDIA, AMD) o SYCL (Intel). Compilar openEMS
        de `master` en Windows (MSVC, con CSXCAD y fparser) y probarlo con un caso de `fase0/` (dipolo): comparar S11 y
        tiempo con la CPU. Hacerlo con el usuario presente; la compilación puede costar horas.
     2. `simulacion.py` usa la API de Python (`FDTD.Run(..., numThreads=)`): comprobar si el motor se elige desde ahí
        (argumentos extra) o si hay que llamar al ejecutable `openEMS` con `--engine=gpu`.
     3. Botón/opción «Aceleración por GPU» en Simulación: detectar si el openEMS instalado la soporta, desactivarlo si
        no, y caer a la CPU con aviso si falla. Revisar que la caché (`%TEMP%\antenas_sim\<hash>`) incluya el motor.
     4. Instalador: ofrecer el openEMS con GPU como opción, no como obligación (el 0.37 de GitHub sigue siendo el
        predeterminado y el SHA-256 está fijado). Mantener el límite de 2 simulaciones a la vez: con GPU, una sola.
     5. Avisar de los límites: no hay ni GPU ni plugin en el openEMS oficial, simple precisión posible según el
        backend, y habrá que revalidar la ganancia y eficiencia frente a la CPU (`comparar_mallas` sirve de modelo).
   - Un usuario dijo también que hay **otra implementación de CPU que tiene en cuenta la caché** y podría ser mucho más
     rápida que la actual: no la he encontrado en el repositorio (solo «SSE2 multihilo»). Preguntar a Jorropo cuál es.
8. **Para la v0.2.0: idiomas con i18n** (decidido 05-11; **hecha la interfaz de escritorio el 06-11 en la rama local
   `i18n`**, worktree `%LOCALAPPDATA%\antenas\wt-i18n`, sin fusionar ni empujar). Mecanismo y reglas en CLAUDE.md
   («Idiomas de la interfaz»): `antenas/i18n.py` (`tr`), `antenas/idiomas/en.json` (773 textos, todos traducidos),
   `herramientas/i18n.py`, selector de idioma en la cabecera. Probado en inglés en todas las pestañas sin castellano
   suelto. Falta: **(a)** pasar `herramientas/i18n.py faltan` a la CI (`comprobar.yml`); **(b)** web lite (`web/app.js`,
   `web_api.py`, `catalogo.json`, descarga del idioma al navegador: hoy `i18n` va en el núcleo pero sin catálogo);
   **(c)** exportación (serigrafía y textos del `.kicad_pcb`/LÉEME siguen en castellano salvo el nombre del tipo);
   **(d)** `MANUAL.md` en inglés; **(e)** revisar la traducción inglesa (la hizo Claude); **(f)** fusionar con
   `gpu-pruebas` (conflicto previsible en `gui/app.py`: la casilla de GPU); **(g)** probar la pestaña Medir y la
   Simulación con simulación real en inglés (el subproceso hereda `CHIRPTENNA_IDIOMA`).
   - **Lote en GPU (06-11, `salidas/_validacion_gpu`, 19 casos, todos terminaron).** Ajustados a 2,44 GHz salvo
     indicación; f = resonancia final. Son valores de iterar: confirmar ganancia y eficiencia en CPU (la GPU las da
     algo altas). Bowtie: dipolo bowtie 2424 MHz (−0,7 %, BW 607, G 2,5 dBi, η 99 %), bowtie Sierpinski 2379 MHz (−2,6 %,
     BW 506, G 2,1); ambos con el tamaño inicial ~7 % grande: calibrar `K_BOWTIE`. Panel de 1 elemento con reflector:
     no adapta en f objetivo (resuena en 3,05–3,07 GHz con la separación 0,40, G 4,7 dBi; a 866,5 MHz sí: 811 MHz,
     BW 240, G 5,2): revisar la separación ideal del reflector con bowtie. Panel 2×2 Sierpinski: 2284 MHz (−6 %),
     G 12,9 dBi, η 76 %; 4×4: 2140 MHz (−12 %), G 14,6 dBi, η 53 % (una simulación, sin iterar f). Pendientes:
     J-pole recta −9,0 dB (sigue mal), Franklin −18,8 dB pero BW 62 MHz, G 2,2 (ya adapta; antes −5,3 dB), COCO
     G 1,9, η 53 % (igual), parche Minkowski it. 1 η 33 %, it. 3 η 30 % y S11 −17,5 dB (antes −5 dB y η 23 %),
     Hilbert sin π −3,7 dB (868) y −2,8 dB (2,4 GHz, orden 2) (siguen sin adaptar), monopolo IPEX −7,0 dB (igual),
     Yagi aligerada 2441 MHz, −10,8 dB, G 5,9 dBi (antes 7,2 sin aligerar), array de parches 2×2 2051 MHz (−16 %),
     G 5,2 dBi, η 22 %, 17 M celdas, 66 min. Falta actualizar `problemas.py` y los README con esto.
8. **Para la v0.2.0: idiomas con i18n** (05-11, decidido; de momento solo inglés además del castellano). Hoy los textos
   están escritos a mano en castellano en `gui/app.py`, `antenas/presentacion.py`, `antenas/guia.py` (ayudas,
   resúmenes), `antenas/problemas.py`, `antenas/consejos.py`, `web/app.js` y `web_api.py`. Plan: catálogo de textos por
   clave (JSON `es`/`en`) compartido entre escritorio y web, selector de idioma que se recuerda, y la prueba de la CI
   comprobando que no falte ninguna clave en `en`. Los nombres de tipo y de parámetro de `diseno.json` no se traducen
   (son claves). `MANUAL.md` y `INSTALAR.md` ya tienen o tendrán su versión inglesa aparte.
9. **Más adelante:** interfaz en inglés, versión para Linux, `dependabot.yml` (ya hay CI y versiones fijadas),
   mejoras de la web lite (abajo).
8. **Web lite** (05-11, hecha; `web/`, ver CLAUDE.md): 32/32 casos en Pyodide (~0,6 s por antena), zip del navegador
   con DRC de KiCad limpio, móvil y tema oscuro probados. Pendiente:
   - [x] Pages activado (build_type workflow) y publicada el 05-11: https://sqtactical.github.io/chirptenna/
     (`web.yml` vuelve a publicar con cada release o a mano: `gh workflow run web.yml`).
   - [x] `prueba_web.py` en la CI: 32/32 en Chromium con DRC de KiCad limpio (media 0,74 s, máx. 2,5 s por antena).
   - [x] Interfaz simplificada (05-11, escritorio y web): galería de tipos con miniatura, resumen y estado, selector con
     descripción, básicos + «Ajustes avanzados» y «?» con la ayuda de cada parámetro (`antenas/guia.py`).
   - [x] Rehacer las capturas del README con la galería (`docs/capturas/`; 14-11, `herramientas/capturas_readme.py`).
   - [ ] **Service worker** (idea, para la v0.3.0; ~2 h): `web/sw.js` registrado desde `app.js` que guarda en caché Pyodide
     (CDN), sus paquetes (numpy, shapely; ezdxf viene de PyPI por micropip) y los ficheros de la web, para cargar rápido
     en visitas repetidas y funcionar sin conexión (con `manifest` sería instalable como PWA). Hay que poner la versión de
     la release en el nombre de la caché (lo hace `construir_web.py`) para que una release nueva no deje ficheros viejos, y
     avisar «hay una versión nueva, recarga». Alcance `/chirptenna/` en GitHub Pages. Ampliar `prueba_web.py`: segunda carga
     desde la caché y arranque sin red. Cuidado con una caché obsoleta pegada.
   - [ ] Mejoras: versión en inglés (hecha en la v0.2.0, con es/en/fr/de), «Ajuste tras fabricar» explicado en la web.

### Diario de la cola de simulaciones (08–10-11)

- **Cola de simulaciones y tarea horaria (08-11)**: `salidas/_cola/pendientes.txt` con `herramientas/cola_extra.py` (dos trabajadores; lo hecho va a `hechas.txt`; se relee entre órdenes, así que se insertan barridos nuevos tras la cabecera). Quedan ~60 barridos: `P_*` (masa, relación de aspecto, ángulo de Koch, separaciones), `Z_*`, `V_*`, `U_*` (Hilbert, Minkowski, apilado, COCO) y refinamientos `R_*`. **Instrucción permanente del usuario**: seguir arreglando antenas y añadir simulaciones sin esperar; una tarea de la sesión de Claude (cron, cada hora, minuto 17) revisa la cola, relanza `cola_extra.py` y `mantener_despierto.ps1` (se para solo), lee resultados y encola hasta 15 barridos nuevos por ciclo. Vive solo en esa sesión y caduca a los 7 días: si se cierra, relanzar la cola a mano (`python herramientas/cola_extra.py`) y repetir el ciclo. Sin commit ni push por su cuenta.
- **Pendiente tras esta tanda**: (1) al acabar `P_*`/`Z_*`/`V_*`/`U_*`, `resumen_barridos.py`, `calibrar_estimaciones.py` y pasar lo nuevo a `problemas.py`/README; (2) hecho el 09-11: J-pole e IFA con la opción «Bandas» (`antenas/bibanda.py`), frágiles con la malla (lección 70); falta un diseño bibanda que aguante varias mallas; (3) el parche circular necesita variar la posición de la entrada para dar polarización circular; (4) medir con el NanoVNA alguna de las placas (J-pole recta de 868 MHz, J-pole unida, IFA bibanda). Si C: se llena, vaciar `%TEMP%\antenas_sim` (permiso del usuario).

- 08-11 04:21: RESUELTO (falta pasarlo a problemas.py/README): colineal de dipolos a 5,8 GHz (R_colineal_dipolos_58GHz): elementos 4, factor_linea 1,1, ancho_brazo ×1,05 -> -13,8 dB (banda -10 dB 5448-6090 MHz, eta 50 %, G 3,5 dBi); con 2 elementos -11,2 dB, eta 70 %, G 3,6 dBi (res 6258: algo alta). El factor_linea 1,1 ayuda a 5,8 GHz; 1,0 daba -7,7 (eta 35 %).

- 08-11 05:21: RESUELTOS (falta pasarlos a problemas.py/README): monopolo recto con IPEX a 2,4 GHz (R_monopolo_IPEX_masa_24GHz: masa manual, largo_masa 25, ancho_placa 40: -14,6 dB, eta 95 %, banda 2206-2595; con la masa automatica daba -6,9); PIFA a 1,2 GHz centrada (-13,7 dB, eta 95 %, banda 1152-1361: antes se daba por no adaptada). IFA 1,2 GHz -9,7 dB (eta 93 %): encolado R_ifa_12GHz. NO VA: Franklin 5,8 GHz (-1,7, parte real 416 ohm). Array de parches 5,8 GHz -4,8 dB (res 7147): encolado R_array_parches_58GHz con tamano x1,2-1,25.

- 08-11 06:21: parche rectangular 1,2 GHz: NO VA (centrado -0,5 dB, G -13,9 dBi; la placa es enorme y el centrado tardo 89 min): parado a mano el barrido Y_parche_rectangular_12GHz para liberar la GPU.

- 08-11 07:21: RESUELTOS (falta pasarlos a problemas.py/README): IFA a 1,2 GHz (R_ifa_12GHz: separacion_toma 6,73, altura 12,1, ancho_pista 1,92: -14,0 dB, eta 91 %, banda 1223-1326); J-pole recta a 2,4 GHz (Z_jpole_hueco_24GHz: hueco 6 mm, toma 0,26: -10,9 dB, eta 85 %); panel de dipolos a 2,4 GHz (Z_panel_reflector_24GHz: brazo 19,906, reflector 0,125-0,163 lambda: -10,1 dB, G 12,1-12,7 dBi). Casi: J-pole 1,2 GHz -9,8 (hueco x8, borde), panel 5,8 GHz -9,8 (reflector 0,175), dipolo 1,2 GHz -7,9; encolados R_jpole_hueco_12GHz, R_panel_reflector_58GHz, R_dipolo_12GHz. NO VA: array de parches 5,8 GHz (-7,7 dB pero eta 12 %).

- 08-11 08:21: RESUELTOS (falta pasarlos a problemas.py/README): Yagi con boom 5,8 GHz con el haz delante (Z_yagi_58GHz_afinar: factor_director 0,81, factor_reflector 1,15, ancho_boom 8, separacion_reflector 0,39: -16,4 dB, G 5,9 dBi, eta 74 %, phi 96); dipolo 1,2 GHz (R_dipolo_12GHz: largo_brazo 43,5, ancho_pista 2,88: -14,4 dB, eta 97 %); bowtie 2,4 GHz (Z_bowtie_24GHz: apertura 55, ancho_pista 1,5: -13,0 dB, eta 98 %) y 5,8 GHz (apertura 55, ancho_pista 0,63: -11,6 dB, eta 88 %); sleeve 5,8 GHz (Z_sleeve_58GHz: alto 8,48, largo_masa 10,1, ancho_placa 13: -17,9 dB, eta 90 %). Casi: Vivaldi 5,8 GHz -8,8 (R_vivaldi_58GHz), panel 5,8 GHz -9,8 (atascado), J-pole 1,2 GHz inestable (-3,9 a -9,8 segun el centrado). NO VAN: Minkowski con ranura 5,8 GHz (-1,9), Franklin 2,4 GHz (-5,4), flecha 2,4 GHz (-2,8), Yagi de Koch con 1 director (-7,3).

- 08-11 09:21: RESUELTOS (falta pasarlos a problemas.py/README): flecha de Sierpinski 2,4 GHz (V_flecha_iter_24GHz: iteracion 1, ancho_pista 0,786: -15,9 dB, eta 93 %, G 2,2 dBi: el tipo SI adapta con iteracion 1); Yagi con boom de Koch it. 2 a 2,4 GHz con el haz delante (V_yagi_koch_it2_borde_24GHz: factor_director 0,76, factor_reflector 1,35, 2 directores, separacion 0,39: -14,4 dB, phi 66, eta 81 %, pero solo 2,6 dBi); IFA 2,4 GHz centrada -15,1 dB; PIFA 2,4 GHz largo_brazo 22 -11,3 dB. Casi: Vivaldi 5,8 GHz -9,1 (res 6798: R_vivaldi2_58GHz alarga la aleta). NO VAN: parche rectangular con ranura/margen de masa (-4 a -6 dB), Franklin 2,4 GHz (-7,8).

- 08-11 10:21: RESUELTO (falta pasarlo a problemas.py/README): Vivaldi 5,8 GHz (R_vivaldi2_58GHz: tasa 4, ancho_apertura 24, largo_aleta 68,6: -12,3 dB, banda 5645-6303, eta 66 %). NO VAN (tras 3 o mas intentos): monopolo de Hilbert 2,4 GHz (mejor -1,4 dB, orden 2, pista de 0,2 mm: la pista fina pierde y desadapta); Minkowski 2,4 GHz en FR4 (-5,9 dB, eta 29 %); parche rectangular de mayor ancho (-5,0 dB, eta 33 %); apilado en curso.

- 08-11 10:50: documentacion al dia con los resultados hasta las 10:21 (problemas.py, README es/en, CHANGELOG, CLAUDE.md lec. 67, resultados_07-11.md; traducciones 978/978). Tarea horaria nueva fe020990: ademas de experimentar, documenta sola cuando hay 3 o mas resultados nuevos (sin commit ni push).

- 08-11 11:47: Q_ y R_ (falta documentarlo en problemas.py/README cuando acaben las aligeradas): parche sin plano de tierra = monopolo de placa a 2,4 GHz (Q_parche_sin_masa_monopolo_24GHz: placa de 3 mm -12,9 dB eta 99,5 %; 6 mm -10,0 dB banda 2398-2660; 10 mm -8,9; no mejora al monopolo recto de pista fina); dipolo con brazos parche (Q_dipolo_parches: x4-x12 de ancho, recentrado -6,7 a -1,6 dB a 2,4 GHz y -5,8 a -2,2 dB a 5,8 GHz: NO VA, el bowtie es la forma buena); parche apilado 2,4 GHz (U_apilado: -0,6 dB, eta 7 %: NO VA). YAGI ALIGERADA a 2,4 GHz (R_yagi_aligerada_24GHz): sin recortes -12,8 dB, G 6,0 dBi, haz delante; CON recortes -2,3 dB, res 2627 MHz (+7 %), G 4,2, haz atras (phi 270): los recortes NO son inocuos; probar margen_aligerado mayor (R_yagi_aligerada2_24GHz). Faltan las aligeradas a 5,8 GHz, 868 MHz y el panel.

- 08-11 12:00 (ideas de topologia nueva propuestas al usuario): dipolos cruzados (torniquete) para polarizacion circular GPS/Iridium; monopolo de placa o eliptico para 2,4 + 5,8 GHz a la vez (encolado Q_monopolo_placa_2banda_24_58); helice impresa con vias para 868 MHz compacto; antena de ranura de lambda/2; IFA de tres bandas (868/2,4/5,8) con dos ramas.

- 08-11 12:30: version: la ultima publicada es v0.2.0-alpha (etiqueta en origin, c0e63c6; tambien v0.1.0/0.1.1/0.1.2). main lleva 29 commits mas que la rama v0.2.0 y todo lo de la campana GPU y esta tanda (J-pole, bibanda, estados nuevos) esta en [Sin publicar] del CHANGELOG: iria en la siguiente (propuesta v0.3.0-alpha; pendiente de que el usuario lo decida). Nuevo banco de pruebas herramientas/topologias.py (torniquete de dipolos para GPS L1, antena de ranura, IFA tribanda); encolados T_torniquete_GPSL1, T_ranura_24GHz, T_ifa_tribanda (27 configuraciones). Aun no son tipos del catalogo.

- 08-11 12:40: el usuario aprueba el numero v0.3.0-alpha para publicar todo esto (sin fecha: cuando acabe la cola; antes, commit, pruebas y su visto bueno). Instruccion: seguir optimizando y probando las topologias nuevas (T_*: torniquete GPS L1, ranura 2,4 GHz, IFA tribanda; Q_monopolo_placa_2banda).

- 08-11 12:45: documentado (problemas.py, README es/en, CHANGELOG, CLAUDE.md lec. 68, informe; traducciones 982/982; comprobar_tipos 70/70): parche apilado y COCO -> No funciona; aligerado casi inocuo a 868 MHz y 5,8 GHz pero rompe la Yagi de 2,4 GHz (margen 6 mm: -6,0 dB); monopolo de placa y dipolo de brazos anchos. T_torniquete fallo por falta de la clave 'borde' en el puerto pasante (corregido, repetido como T2_torniquete_GPSL1); T_ranura resuena a ~3000 MHz (repetido mas grande como T2_ranura_24GHz); T_ifa_tribanda en curso; R_yagi_aligerada3_24GHz encolado.

- 08-11 13:18: topologias nuevas, ronda 1: IFA tribanda (T_ifa_tribanda: k3 0,8 h3 0,2: -9,5 / -10,0 / -10,6 dB en 868 / 2,4 / 5,8 GHz, banda baja a 911 MHz); torniquete GPS L1 (T2: s 1,05 d 0,04: -21,4 dB, eta 98 %, pero AR 8,8 dB; d 0,08-0,12: AR 5,0-5,2, S11 -13 a -14); ranura 2,4 GHz (T2: s 1,2 xoff 18: -11,9 dB, eta 79 %, 4,3 dBi: FUNCIONA); monopolo de placa para 2,4 + 5,8 GHz: NO VA (-3,6 dB a 5,8). Yagi aligerada 2,4 GHz con margen 10 mm: -3,1 dB: la aligerada de 2,4 GHz no va. P_masa_*: el tamano de la masa apenas importa (todos -12 a -19 dB); PIFA 2,4 GHz con ancho_placa 20: -18,8 dB. Encolada la ronda 2 (T3_*).

- 08-11 13:40: J-pole de tres y cuatro bandas con el diseno del usuario: jpole_dual.py --modo multi (brazo 2 a la izquierda de la masa con desvio; brazos 3 y 4 a la derecha, cada uno con su brazo de masa de la longitud de su adaptador y radiador recto; todos unidos por puentes en B.Cu); --rango-max N para la banda mas alta. Encolados U3_jpole_tribanda_868_24_58 (9 conf.) y U4_jpole_cuatribanda_433_868_24_58 (4 conf., placa ~80 x 411 mm). Riesgo: la J-pole sola a 5,8 GHz no pasaba de -6,5 dB.

- 08-11 14:10: el usuario tiene placas pedidas a JLC en camino (aun sin recibir; no se sabe cuales). Pendiente: congelar el diseno.json y el resultado simulado de cada placa pedida para compararlos con el NanoVNA, simular su sensibilidad a la epsilon_r del FR4 (4,2 / 4,5 / 4,8) y preparar el guion de medida (vna/medir_antena_pc.py con la calibracion completa_50k_2700M). Seguir anadiendo tipos, todo marcado como sin medir.

- 08-11 14:30: las placas pedidas a JLC (Y52 cupon A, Y53 cupon B, Y54 Yagi recta 2 dir., Y55 parche rectangular, Y56 monopolo Sierpinski, Y57 monopolo Koch ajustable, Y58 J-pole de Koch, Y59 dipolo con coaxial; Y62 es otra placa) estan en camino (Shipped). Todas a 2,4 GHz; no se ha pedido ninguna bibanda ni de 868 MHz. Datos, simulacion esperada y guion de medida en docs/desarrollo/placas_pedidas_2G4.md; sensibilidad a la epsilon_r en herramientas/sensibilidad_er.py (encolado SENS_er_pedido).

- 08-11 14:20: sensibilidad a la eps_r (SENS_er_pedido, parcial): bajar la eps_r de 4,5 a 4,2 (-6,7 %) sube la resonancia: dipolo +21 MHz (+0,9 %), monopolo de Sierpinski +26 (+1,0 %), monopolo de Koch +30 (+1,3 %), J-pole de Koch +34 (+1,4 %), parche +81 MHz (+3,3 %: casi f ~ 1/sqrt(eps_r)). Subir a 4,8 baja casi lo mismo. Las antenas con el campo en el aire pierden ~0,3-0,4 del efecto del parche. El parche (banda 41 MHz) sale de la ISM con cualquier error de eps_r de este tamano; la J-pole de Koch tambien (banda ~57 MHz). Faltan la Yagi y el parche a 4,8; documentar al acabar. P_apilado_aspecto: -0,6 dB, eta 7 %: no va.

- 08-11 14:35: BUG corregido en jpole_dual.py: --rango-max se guardaba en opt['rango-max'] y se leia opt['rango_max'] (siempre 3,8): U3_jpole_tribanda simulo hasta 3,3 GHz y fallo (banda de 5,8 GHz sin puntos); repetido como U3b_. U4_ (cuatribanda) ya corre con el codigo corregido. Sensibilidad eps_r completa: parche 4,2/4,5/4,8 -> 2521/2439/2365 MHz (S11 en 2441,75: -3,0/-12,7/-3,1 dB); Yagi 2490/2447/2406 MHz (-13,2/-17,6/-17,6 dB).

- 08-11 15:15: U3b_ (tribanda de J-pole 868 + 2,4 + 5,8 GHz, 9 conf.): 868 MHz -10,7 a -11,0 dB; 2,4 GHz -6,3 a -9,6 dB (mejor con a3 1,2); 5,8 GHz -1,1 a -1,6 dB y NO cambia con k3 ni a3: el brazo de 5,8 GHz (adaptador ~9 mm, pista de 2,8 mm) no resuena. jpole_dual.py admite w3/w4 (pista del brazo); encolado U3c_ (pista 0,8 y 1,5 mm, toma 0,3 y 0,6). U4_ (cuatribanda 433) sigue pendiente.

- 08-11 18:35: el usuario manda PARAR las simulaciones: cola_extra, el barrido en curso (U4 cuatribanda, 3 de 4 configuraciones hechas: -0,8 a -0,9 dB, no va), mantener_despierto y la tarea horaria 059dd228 detenidos; bloqueo de GPU liberado. Quedan 18 barridos (94 configuraciones) en salidas/_cola/pendientes.txt: reanudar con python herramientas/cola_extra.py (dos trabajadores) y volver a crear la tarea horaria si se quiere seguir sola. Sin commit.

- **Preview v0.3.0-alpha (08-11)**: rama local `v0.3.0` (commit eb9ff58, partiendo de `main`), version 0.3.0-alpha, CHANGELOG con fecha 08-11. Probada: comprobar_tipos 70/70, prueba_interfaz bien, idiomas 982/982, construir_web bien (prueba_web no se pudo pasar: falta Playwright en el venv; la pasa la CI). Sin push, sin etiqueta, sin release. Para publicar: fusionar en main, git push, comprobar la CI, gh release create v0.3.0-alpha --prerelease y gh workflow run web.yml --ref main (todo con el visto bueno del usuario). Simulaciones paradas el 08-11 18:35 (18 barridos pendientes en salidas/_cola).

- 08-11 21:00: J-pole recta ARREGLADA en el generador (rama v0.3.0): tipos.dimensionar da hueco x5 (868 MHz) a x6 (2,4 GHz) interpolado y toma 0,26; calibracion propia de la J-pole (calibrar_estimaciones.muestras_jpole con V_jpole_defecto_*, abscisa f_x_MHz). Sin centrar: 868 -15,4 dB, 915 -10,1, 1,2 GHz -9,7, GPS L1 -11,8, 2,4 GHz -12,0. 5,8 GHz sigue sin ir. Comprobado: comprobar_tipos 70/70, prueba_interfaz, i18n 982/982. Cuidado: cortar la salida de barrido.py con Select-Object -First 1 deja gpu.lock colgado.

- 09-11: J-pole e IFA tienen la opcion Bandas (multibanda=1, antenas/bibanda.py). Resultado fragil con la malla (leccion 70): experimental. Pendiente: buscar un diseno bibanda que aguante 2-3 pasos de malla, y medirlo.

- 10-11: PTFE (4) y flex (25/50 µm) como sustratos; hélice cuadrifilar en flex (herramientas/helice_flex.py, R de entrada 2-15 Ω: falta red de adaptación); segunda Yagi del usuario en referencias/yagi_comercial_b.py (ninguna lectura de las fotos resuena a 2,4 GHz: pedir grosor del FR4, cotas con calibre y foto macro de la alimentación). Sin commit de esta tanda hasta pasar comprobaciones.
