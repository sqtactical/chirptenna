# Cambios · Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones con
[versionado semántico](https://semver.org/lang/es/). *English summary under each version.*

## [Sin publicar]

### Añadido

- **Antena integrada en una placa** (F3.1, `antenas/integracion.py`): IFA, monopolo recto, de Koch y en meandro pueden ser una esquina de la
  placa de tu producto. Parámetros `integrada`, `placa_x`, `placa_y`, `posicion` (esquina izquierda, derecha o centrada), `zona_x`, `zona_y`
  y `margen_zona`: la masa ocupa toda la placa menos la zona de antena (sin cobre en ninguna capa) y el conector se queda en el borde
  opuesto para medir el prototipo. Si algo no cabe, el error dice cuántos mm faltan. Interfaz de escritorio y web.
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
