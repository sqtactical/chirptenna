# Chirptenna · estado y siguientes pasos (09-11-2026)

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo
se ejecuta, reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md). El diario completo de lo
hecho hasta ahora (validaciones, simulaciones, fallos y decisiones) está en
[`docs/desarrollo/historial.md`](docs/desarrollo/historial.md). **Hacia dónde va el proyecto y en qué orden:
[`ROADMAP.md`](ROADMAP.md)** (11-11): fase 1 = medir cupones y antenas del pedido de JLC; después, consolidar (v0.4) e
integrar antenas en la PCB de un producto (v0.5). Las ideas pendientes de abajo (arrays, colineales) están recogidas allí. **Hechas el 11-11:** F1.1 (`docs/desarrollo/medidas/predicciones_2G4.md`: lo que predice la simulación para las 6 antenas pedidas con εr 4,2/4,5/4,8) y F1.2 (`herramientas/comparar_medida.py`). Siguiente: F1.3 (verificar la calibración del NanoVNA, con el usuario delante) en cuanto lleguen las placas; mientras, F2.2–F2.6.

## Estado

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
- **Versión publicada: v0.3.0-alpha** (09-11; pre-release en GitHub, código AGPL-3.0; la v0.1.0-alpha salió con
  GPL-3.0). Antes: v0.2.0-alpha (06-11) y v0.1.x. Repositorio **público** desde el 04-11 (alpha abierto). Nombre comprobado en TMview: libre.
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

1. **Alpha abierto** (el usuario no quiere esperar a las medidas):
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
   - **Pruebas unitarias con `pytest`** (barata, interés alto): `ajuste.redes_l`, `leer_s1p`, el desembebido de la
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
   - [ ] Rehacer las capturas del README con la galería (`docs/capturas/`).
   - [ ] **Service worker** (idea, para la v0.3.0; ~2 h): `web/sw.js` registrado desde `app.js` que guarda en caché Pyodide
     (CDN), sus paquetes (numpy, shapely; ezdxf viene de PyPI por micropip) y los ficheros de la web, para cargar rápido
     en visitas repetidas y funcionar sin conexión (con `manifest` sería instalable como PWA). Hay que poner la versión de
     la release en el nombre de la caché (lo hace `construir_web.py`) para que una release nueva no deje ficheros viejos, y
     avisar «hay una versión nueva, recarga». Alcance `/chirptenna/` en GitHub Pages. Ampliar `prueba_web.py`: segunda carga
     desde la caché y arranque sin red. Cuidado con una caché obsoleta pegada.
   - [ ] Mejoras: versión en inglés (hecha en la v0.2.0, con es/en/fr/de), «Ajuste tras fabricar» explicado en la web.

## Cómo ejecutar

```
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui/app.py                    # interfaz en http://localhost:8080
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe herramientas/comprobar_tipos.py   # antes de cada release
```

Instalar o recrear el entorno: `instalar.bat` (guía en [`INSTALAR.md`](INSTALAR.md)). Para una release:
1. Subir `antenas.__version__`.
2. Añadir una sección al CHANGELOG.
3. Pasar `comprobar_tipos.py`.
4. `gh release create vX.Y.Z-alpha --prerelease`.
5. `gh workflow run web.yml --ref main`: el flujo que lanza la release falla siempre («Tag … is not allowed to deploy to
   github-pages»: el entorno solo acepta `main`), así que la web se publica a mano. Si la CI falla al descargar KiCad
   (504 de GitHub), relanzar con `gh run rerun <id> --failed`.

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
