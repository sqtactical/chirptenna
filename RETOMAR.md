# Chirptenna · estado y siguientes pasos (04-11-2026)

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo
se ejecuta, reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md). El diario completo de lo
hecho hasta ahora (validaciones, simulaciones, fallos y decisiones) está en
[`docs/desarrollo/historial.md`](docs/desarrollo/historial.md).

## Estado

- **Versión publicada: v0.1.2-alpha** (pre-release en GitHub, código AGPL-3.0; la v0.1.0-alpha salió con
  GPL-3.0). Repositorio **público** desde el 04-11 (alpha abierto). Nombre comprobado en TMview: libre.
- **Programa completo de principio a fin**, validado **solo en simulación** (εr 4,5 supuesta):
  - 16 tipos de antena; `herramientas/comprobar_tipos.py` los genera y exporta a 868 y 2441,75 MHz con DRC limpio (32/32).
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
   6. Sacar la v0.2.0-alpha.
3. **Pendientes técnicos** (detalle en el historial):
   - **Máscara en la simulación**: las antenas exportadas y los cupones llevan máscara encima del cobre (solo se
     abre en los pads para soldar), pero `simulacion` no la modela. Añadir una capa de ~20 µm (εr ≈ 3,8, tanδ ≈ 0,025)
     y validarla con las medidas de JLC (se espera −0,5 a −3 % de frecuencia, más en meandro/Hilbert/Koch).
     Tenerlo en cuenta al sacar la εr de los cupones (la medida ya incluye la máscara).
   - Simular una Yagi aligerada (desplazamiento de frecuencia por quitar FR4).
   - Panel: el haz inclinado ~9° parece un artefacto de la simulación (buscar la causa). Proponer `simetrico` = 0
     por defecto: no corrige la inclinación y empeora S11.
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
7. **A estudiar: aceleración por GPU de openEMS** (05-11; lo comentó Jorropo en Discord: de 150 a 4700 MC/s con una
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
   - Por hacer, en orden:
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
   - [ ] Mejoras: caché sin conexión (service worker), versión en inglés, «Ajuste tras fabricar» explicado en la web.

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
