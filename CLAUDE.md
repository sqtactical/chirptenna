# Chirptenna: generador de antenas fractales para PCB

Objetivo final: un programa que genere antenas (fractales) impresas en PCB para una
frecuencia objetivo. Las ajusta simulando con openEMS, exporta a KiCad/DXF/Gerber y tiene
interfaz gráfica. Antes de eso se valida el simulador y se mide la εr real del FR4 con un
NanoVNA, para que las simulaciones coincidan con las placas fabricadas.

**Estado actual y siguientes pasos: leer `RETOMAR.md` al empezar.** Es la nota de traspaso
entre sesiones: mantenla al día cuando se avance o cambie el plan. Este archivo recoge lo
estable: cómo está montado, cómo se ejecuta y las reglas.

**Mantenimiento**: al terminar una tarea, actualiza este archivo con lo que haya cambiado o
se haya aprendido, y `RETOMAR.md` con el estado. Hazlo de forma concisa y sin duplicar
entre los dos. Un hook `Stop` (`.claude/settings.json` →
`.claude/hooks/recordar_claude_md.ps1`) lo recuerda una vez por tanda de cambios cuando hay
archivos modificados después de la última revisión. La marca de esa revisión es
`.claude/ultima_revision_claude_md`.

## Entorno (Windows)

- Python: `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe`. Está fuera del proyecto a
  propósito: la ruta de OneDrive o de la sesión supera los 260 caracteres de Windows y
  fallan las DLL de shapely. **No crear un `.venv` en la raíz.**
- openEMS v0.37.0 (MSVC) en `%LOCALAPPDATA%\Programs\openEMS\openEMS`, con las wheels
  `openems-0.37.0` y `csxcad-0.7.0`. Se instalan con
  `pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS`.
- Dependencias en `requirements.txt` (numpy, h5py, matplotlib, pyserial, gerbonara, shapely,
  nicegui, plotly, ezdxf; rango probado `>=actual,<siguiente mayor`) + openEMS desde sus wheels. El instalador usa
  `requirements-lock.txt` (versiones exactas, `pip freeze` del venv sin openEMS/CSXCAD): **regenerarlo al subir
  una dependencia** y ajustar el mínimo del rango. Comandos en `RETOMAR.md`.
- CI (`.github/workflows/comprobar.yml`, Windows, en cada push/PR y los lunes): ejecuta `instalar.ps1`, instala
  KiCad con choco, pasa `comprobar_tipos.py` y `herramientas/prueba_interfaz.py` (arranca la interfaz con una
  biblioteca temporal y abre cada pestaña en claro y oscuro). Dos variantes: `lock` y `rangos` (lo más nuevo que
  permiten los rangos; si solo falla esta, ha salido una versión de un paquete que rompe algo). No simula.
- KiCad 10.0.1: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (Gerber, taladros, DRC, SVG). `exportar` busca
  la versión más nueva en `Program Files\KiCad\*` (o `KICAD_CLI`, o el PATH); también hay una 9.0 instalada.
- Instalador para usuarios (`instalar.bat` → `instalar/instalar.ps1`, guía en `INSTALAR.md` / `INSTALL.en.md`):
  Python 3.14 de python.org (firma comprobada), openEMS 0.37 de GitHub (SHA-256 fijado), venv, paquetes, KiCad
  (solo avisa), acceso directo a `iniciar.bat`. Idempotente; `-Comprobar` solo informa. El `.ps1` va en UTF-8
  **con BOM** y CRLF (PowerShell 5.1; `.gitattributes`). Probado desde cero con `LOCALAPPDATA` temporal y
  `-Python` (4 min). Si cambian las versiones de Python u openEMS, actualizar URL y SHA-256 del script.
- Los scripts de `fase0/`, `vna/`, `cupon/`, `placa_sim/` se ejecutan desde su propia carpeta
  (importan módulos hermanos). El paquete `antenas/` se usa desde la raíz (`gui/app.py` añade la
  raíz a `sys.path`). Interfaz: `python gui/app.py` → http://localhost:8080
  (`.claude/launch.json`: "generador-antenas"). Escucha solo en 127.0.0.1 (NiceGUI usa 0.0.0.0 por defecto y
  dejaba la interfaz abierta a la red local); `CHIRPTENNA_HOST=0.0.0.0` la abre a propósito.
  `.claude/launch.json` y `.claude/settings.json` son locales (rutas de este ordenador) y no van al repositorio.
- Está en OneDrive y en el repositorio git privado https://github.com/sqtactical/chirptenna
  (rama `main`). git y gh son portables: `%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe` y
  `%LOCALAPPDATA%\Programs\gh\bin\gh.exe` (no están en el PATH; para gh, `GH_CONFIG_DIR` =
  `%LOCALAPPDATA%\Programs\gh\config`). Commits con el correo noreply de GitHub, nunca el personal. Documentación pública: `README.md`
  (castellano) y `README.en.md` (inglés); licencias: `LICENSE` (código, AGPL-3.0 desde el 04-11; la v0.1.0-alpha salió con GPL-3.0) y `LICENSE-DISENOS.md`
  (diseños publicados, CC BY-NC 4.0). El `.gitignore` deja fuera `salidas/`, `placas/` (Gerber de
  terceros), los cupones generados y **cualquier Gerber**: el repositorio es el generador, no sus salidas.
  Al cambiar tipos o su estado, actualizar la tabla de tipos de los dos README.
- `code-review-graph` (en el Python 3.14 del sistema): grafo de código en `%LOCALAPPDATA%\antenas\crg`
  (`build --repo . --data-dir …`; para consultarlo, `CRG_DATA_DIR` con esa ruta). La carpeta vacía
  `.code-review-graph/` de la raíz es solo su marcador de proyecto.

## Estructura

| Carpeta | Contenido |
|---|---|
| `fase0/` | Validación de openEMS. `comun.py` tiene utilidades (síntesis microstrip, de-embedding, centro de banda −10 dB, cruce de reactancia, guardar JSON/PNG). Contiene `test_dipolo.py [refinado]` y `test_monopolo.py [refinado]`. Las salidas van a `fase0/resultados/` |
| `vna/` | Control del NanoVNA y medidas (detalle abajo). Las salidas van a `vna/medidas/` (`.s1p` + `.json` + `.png`) y a `vna/calibraciones/`, que son **locales** (fuera del repositorio: cada usuario hace las suyas) |
| `docs/` | `logo/`, `capturas/` (las del README: Edge sin ventana contra `gui/app.py --puerto 8091 --disenos <biblioteca de demo>` y la URL `/?diseno=…&pestana=…&tema=claro`) y `desarrollo/historial.md` (diario antiguo de RETOMAR) |
| `analisis/` | `analizar_placas.py` busca en los Gerber de EasyEDA pistas aptas para medir εr. `pines.py` lista los pines de componentes desde `FlyingProbeTesting.json`. `ver_aptas.py` filtra `resumen.json` |
| `antenas/` | **Paquete del generador (Fase 1).** `geometria` (sistemas L: Koch, Minkowski; Hilbert; Sierpinski; meandro; isla de Minkowski hacia dentro; `sin_agujeros`), `materiales` (sustratos JLC FR4/RO4350B, síntesis microstrip), `modelo` (`Antena`: capas F.Cu/B.Cu, radiador, contorno, puerto, zona libre, info, vías, taladros, reflector), `tipos` (catálogo `CATALOGO`, `generar`, `estimar_f`, `dimensionar`), `directivas` (quasi-Yagi de Koch, Yagi de doble cara con boom, arrays de parches 2×2/4×4 y panel de dipolos 2×2/4×4 sobre reflector), `fabricacion` (reglas JLC), `problemas` (problemas conocidos por tipo y opción, que la interfaz muestra bajo el tipo y en Fabricar; **mantenerlo al día junto con la tabla «Problemas conocidos» de los dos README** cuando una simulación o medida cambie el estado de un tipo), `ancho_banda` (estimación −10 dB), `consejos` (recomendaciones), `simulacion` (modelo openEMS de cualquier `Antena`, `simular`, `ajustar` por secante; caché en `%TEMP%\antenas_sim\<hash>`), `simular_cli` (proceso aparte: `python -m antenas.simular_cli trabajo.json` → `resultado.json` + `datos.npz`), `graficas` (Plotly: S11, ROE, Smith con la banda y el objetivo marcados, cortes polares, 3D con la placa dentro —contorno, cobre, reflector, ejes y dirección del máximo, en las coordenadas de la simulación—; la interfaz rehace la antena desde los parámetros del `resultado.json`), `jpole` (J-pole y J-pole de Koch, sin masa, puerto coaxial), `dipolos` (dipolo recto/Koch con SMA y balun impreso o coaxial al centro; colineal COCO: tramos λg/2 de dos tiras superpuestas que se cruzan con 2 vías en cada unión; colineal Franklin: λ/4 sobre masa + elementos λ/2 con horquillas λ/4 alternas), `ajuste` (red en π, marcas de corte, tramos con puentes, asistente con `.s1p`, redes L con valores E24), `tipos_base` (`Parametro`), `validar_lote` (`python -m antenas.validar_lote <salida> [--malla adaptada] [--paralelo 2] [--hilos 6]`: simula y ajusta varios tipos, seguidos o N a la vez; `ANTENAS_HILOS` limita los hilos de openEMS), `comparar_mallas` (malla uniforme frente a adaptada sobre un lote), `conector` (parámetro `conector`: SMA de canto o IPEX/U.FL encima de la placa; con IPEX la línea arranca en su pad central y el puerto de la simulación va ahí; fija la masa y el ancho mínimos de los monopolos), `exportar` (placa/huella KiCad, Gerber, DRC, DXF; con reflector, segunda placa `<nombre>_reflector`), `vista` (PNG y Plotly) |
| `gui/` | `app.py`: interfaz NiceGUI por fases: barra fija (nombre, tipo, banda, guardar) y pestañas Diseño / Simulación / Fabricar / Medir (asistente del NanoVNA) / Mis diseños. `antenas/biblioteca.py` guarda cada diseño en `Documentos\Chirptenna\disenos\<nombre>` (`diseno.json`, `simulacion/`, `fabricacion/`, `medidas/`); `CHIRPTENNA_DISENOS` cambia la ruta (úsala en pruebas para no ensuciar la del usuario) |
| `cupon/` | Cupones de εr en placas de 100 × 100 mm: `generar_cupon.py` → `cupon_A/` (anillos 868 MHz y 2,4 GHz) y `cupon_B/` (anillo 5,8 GHz n=3, líneas abiertas S80/S30, líneas en L L64/L17, CPWG de 50 Ω con valla de vías y microstrip de 100 Ω), cada una con placa, Gerber, zip para JLC, DRC, `diseno.json` y leyenda en la serigrafía inferior; radios de los anillos ×0,93 (`CORRECCION_ANILLO`). `vista_gerber.py <cupón>`, `simular_anillo.py <anillo>` (openEMS con puertos MSL; caché por radio). `_antiguo_185x100/`: el cupón anterior |
| `placa_sim/` | Importador Gerber → openEMS de una placa entera (`simular_placa.py`) y `comparar_sim.py` |
| `salidas/` | Exportaciones de la interfaz (`salidas/<nombre>/`); `_pruebas/` son pruebas internas |
| `referencias/` | Modelos de antenas reales para comparar simulación y medida: `yagi_comercial.py` (Yagi 2,4/5,8 del usuario: dipolo plegado apilado con balun de «U», `python -m referencias.yagi_comercial [dibujar\|simular]` → `salidas/_referencias/`) |
| `herramientas/` | `comprobar_tipos.py`: **antes de cada release o cambio en un tipo**, genera y exporta los 16 tipos a 868 y 2441,75 MHz (DRC + reglas, ~2 min, código 1 si algo falla; resumen en `salidas/_comprobar_tipos`). `cola.py`: **cola FIFO de simulaciones** en `%LOCALAPPDATA%\antenas\cola` (`pendientes/`, `en_curso/`, `hechos/`, `registros/`): `añadir <nombre> <comando…>`, `ver`, `trabajar [--hilos 6]` (dos trabajadores = dos simulaciones a la vez; cogen por orden de nombre, así que se reordena renombrando; acaban tras 10 min sin trabajo). Usarla en vez de encadenar scripts de espera. `mantener_despierto.ps1`: evita la suspensión mientras haya simulaciones (SetThreadExecutionState; la pantalla sí puede apagarse); se cierra solo tras 10 min sin ellas (las detecta por línea de comandos o por un python con > 30 s de CPU por minuto). Lanzarlo en segundo plano junto a lotes largos |
| `placas/` | Gerber + taladros + `FlyingProbeTesting.json` (EasyEDA/JLC) de 6 placas: Scho_Ka_mesh_v1.0, Scout_2.4_V1.3, Stick_18650_2.4G_v1.0, Stick_21700_v1.1, Stick_Touch_raw_v1.0 y Tracker_21700_v1.0. **Son datos de entrada: no modificarlos** |

### `vna/`
- `nanovna.py`: driver por USB serie (VID:PID 0483:5740, 115200 baudios, prompt `ch> `).
  Funciones: `medir()` (con `scan … 7`, máximo 101 puntos por barrido), `barrido_actual`,
  `fijar_barrido`, `listar_sd` / `leer_sd` (solo lectura) y `guardar_s1p` (Touchstone RI,
  50 Ω). El timeout del puerto se fija una sola vez, porque reconfigurarlo en caliente
  falla en Windows (error 31).
- `calibracion.py`: calibración en el PC. Para S11 usa el modelo de 3 términos (Ed, Es, Er);
  para S21, respuesta + aislamiento. Mide en bruto (`cal off`) en tramos de 101 puntos y
  luego restaura el estado del equipo. Se guarda en `calibraciones/<nombre>.npz` + `.json`.
- `calibrar_pc.py`: calibración guiada, un paso por ejecución: `iniciar <nombre> <MHz_ini>
  <MHz_fin> <puntos> [--equipo]` → `open` / `short` / `load` / `isoln` / `thru` →
  `terminar`. `verificar [nombre]` comprueba una calibración ya guardada. Detecta
  estándares mal puestos comparándolos con el OPEN.
- `asistente_vna.py`: operaciones para la interfaz (info del equipo, `CalibracionGuiada` OSL, verificar con
  la carga, medir en una ventana de la rejilla de calibración); cerrojo para no hablar con el equipo dos veces
  a la vez. `calibracion.comprobar_estandar` detecta estándares mal puestos (lo usan esto y `calibrar_pc.py`).
- `calibrar.py`: calibración SOL antigua, solo en la RAM del equipo, con 101 puntos.
  Queda sustituida por `calibrar_pc.py`.
- `medir_antena.py <nombre> <MHz_ini> <MHz_fin> [centro ini fin]`: genera S11, ROE, Smith
  y `.s1p`. Usa la calibración que tenga el equipo, no la del PC.
- `medir_antena_pc.py <nombre> [calibración] [--zoom MHz_ini MHz_fin]`: S11 de una antena con la
  calibración del PC (por defecto `completa_50k_2700M`, todo su rango); `.s1p` + `.json` (bandas a
  −10 dB, aviso si |S11| > 0,5 dB) + `.png` (S11, zoom, R/X).
- `medir_latiguillo.py <nombre> [long_mm|0] [calibración]`: retardo, longitud eléctrica,
  factor de velocidad y pérdida, con el extremo al aire. Usa la calibración del PC.
- `comparar.py <salida.png> a.s1p b.s1p … [--banda ini fin]`: superpone varias medidas.

## Reglas con el NanoVNA (obligatorias)

- NanoVNA-H, firmware DiSlord 1.2.42.
- **Nunca enviar `save`**: no se pisan los slots C0–C4 del equipo. `recall` solo lee.
- Después de medir, restaurar siempre el barrido y el estado de calibración del equipo
  (`try/finally`).
- La SD solo se lee por USB. Las calibraciones del equipo las guarda el usuario desde el menú.
- Calibración de referencia: `vna/calibraciones/completa_50k_2700M` (50 kHz–2,7 GHz,
  1010 puntos, OSL + THRU, sin aislamiento porque solo hay una carga). En la SD del equipo
  hay una copia de 101 puntos (`CAL-PCB.CAL`). Antes de medir, comprobarla con
  `calibrar_pc.py verificar`.
- Los scripts que tocan el equipo se ejecutan con el usuario delante: entre pasos hay que
  cambiar estándares o conexiones a mano. Pedirle que conecte lo necesario y esperar a
  que confirme.

## Convenciones de código

- Todo en español: nombres, comentarios, docstrings, mensajes y claves de JSON.
- Unidades: la geometría de openEMS en mm (`SetDeltaUnit(1e-3)`) y las frecuencias
  internas en Hz. En la línea de comandos se pasan MHz y en los resúmenes se escriben GHz
  o MHz, con la unidad en el nombre de la clave (`f_centro_banda_GHz`, `longitud_mm`).
- Cada script de prueba o medida genera un `.json` resumen y un `.png` con matplotlib
  (backend `Agg`). Las claves que empiezan por `_` son datos internos y no se guardan.
- Las simulaciones van a `%TEMP%\fase0_*`, con caché por geometría: si ya existen
  `port_ut_1` / `port_it_1` (y `nf2ff_E_0.h5`), no se vuelve a simular.
- Hay que importar `comun` **antes** que `CSXCAD` / `openEMS`, porque fija `CSXCAD_INSTALL_PATH`.
- El material por defecto es el FR4 de JLC: εr 4,5 (valor de su calculadora de impedancias
  para 2 capas; los scripts de `fase0` aún usan 4,4), tanδ 0,02 y 1,6 mm. En openEMS las
  pérdidas se modelan con `kappa = 2π f0 ε0 εr tanδ`.

## Lecciones aprendidas (no repetir errores)

1. La fórmula analítica del monopolo falla un 27 %. Hay que meter la simulación en el
   bucle de ajuste (secante, 1–3 iteraciones).
2. El criterio de ajuste es el **centro geométrico de la banda a −10 dB**, no el mínimo de
   S11 ni Im{Zin}=0. Con planos de masa pequeños hay varios mínimos y van saltando de uno a otro.
3. El centro de NF2FF (`CalcNF2FF(center=…)`) se pasa en **metros**, no en unidades de malla.
4. Precisión de malla: ×1 es rápida para iterar (la frecuencia sale un ~2 % baja en el
   dipolo) y ×2 sirve para el diseño final. ×4 tarda unos 35 min.
5. Dipolo validado: L/λ = 0,456 / 0,461 / 0,465 (×1/×2/×4) y R ≈ 72 Ω, frente a la teoría
   (≈0,47 y 70–73 Ω). Monopolo de 2,45 GHz ajustado: tira de 23,63 mm, ganancia 3,1 dBi
   y eficiencia de radiación del 90 %.
6. Medir εr con pistas de placas reales: la masa incompleta debajo no descarta una pista,
   porque la geometría real se simula y se ajusta εr. Lo que sí la descarta son ramas,
   vías, varios anchos, longitud < 30 mm o no tener masa a menos de 3 mm de un extremo.
7. Al guiar al usuario para soldar en la cara inferior, la imagen va **espejada** (como se
   ve al darle la vuelta a la placa) y se puede girar 180° con `--giro180` para que
   coincida con su foto.
8. Las coordenadas de `FlyingProbeTesting.json` están en mil (×0,0254 → mm).
9. Medir εr con una placa real sin montar (Scout) no funciona: la placa entera radia y
   resuena con el cobre suelto, y simularla exige resolver huecos de ~0,2 mm (si no, el
   modelo queda en cortocircuito). Para εr hace falta un cupón dedicado.
10. En openEMS, un hueco más fino que la malla cortocircuita el cobre a ambos lados.
    Comprobar siempre Z a baja frecuencia (abierto ≈ capacitivo, no ≈ 0 Ω) antes de ajustar.
11. Ficheros `.kicad_pcb` escritos a mano (formato v8, `version 20240108`; KiCad 10 los lee):
    dentro de una huella, la posición de los pads y propiedades es **relativa a la huella** y el
    ángulo del pad es absoluto. El cobre con forma libre va como **pad custom** (con net) o como
    **zona rellena** con `filled_polygon`; los `gr_poly` en cobre no tienen net y el DRC los ve
    como cortocircuitos. Zonas de la misma net que se solapan con la misma prioridad dan error:
    fundirlas antes. Cobre a ≥ 0,5 mm del borde (mínimo por defecto de KiCad).
12. `AddMSLPort` de openEMS necesita la malla ya definida (≥ 5 líneas en la dirección de propagación).
13. Al reescribir ficheros desde PowerShell 5.1, `Get-Content`/`Set-Content` sin `-Encoding utf8`
    rompen las tildes: usar las herramientas de edición o `[IO.File]` con UTF-8.
15. Plano de masa de los monopolos (`tipos.largo_masa_monopolo`, `_f_monopolo`): modelo de dipolo
    asimétrico. Si la masa es ≥ λ/4 efectivo no influye; si es más corta, radiador + masa ≈ λ/2
    efectivo y hay que alargar el radiador. Encoger la masa no reduce el largo total: lo que
    compacta es el ancho automático y el radiador fractal. Modos: manual, λ/4, λ/8 y mínimo (12 mm,
    para el SMA). Sin validar con simulación (Fase 2).
16. Con contorno no rectangular (`geometria.contorno_placa`), recortar también la masa con
    `contorno.buffer(-BORDE_COBRE)`: si no, las esquinas redondeadas dejan cobre fuera del margen
    y el DRC de KiCad da `copper_edge_clearance`.
17. `FDTD.Run` de openEMS **cambia el directorio de trabajo** al de la simulación: todas las rutas
    de salida tienen que ser absolutas.
18. Los JSON escritos con `Set-Content -Encoding utf8` (PowerShell 5.1) llevan BOM: leer con
    `encoding='utf-8-sig'`.
19. En la interfaz, la simulación va en un subproceso (`subprocess.Popen` + hilo lector +
    `ui.timer`), con `PYTHONIOENCODING=utf-8`; así la página no se bloquea durante minutos.
20. Malla de `simulacion.simular`: paso en la placa = mín(λ_sustrato/N, pista mín./2, hueco mín./2).
    `hueco_minimo` usa un umbral relativo a s × perímetro para no confundir las muescas en V de
    Koch con huecos; los huecos conocidos (paso del Hilbert/meandro, CPS de la Yagi, muesca de
    inserción del array) se pasan en `info['hueco_minimo_mm']`.
21. Ajuste por simulación: mantener la **malla fija** entre iteraciones (si cambia, la frecuencia salta
    varios % y la secante oscila); pasos acotados a ±30 %; si no hay banda a −10 dB usar el cruce
    por cero de la reactancia en los terminales (quitando la línea de 50 Ω) y no fiarse de un
    mínimo de S11 en el borde del rango.
22. Ajustabilidad física: a 2,4 GHz un 1 % de frecuencia son ~0,25 mm de pista; los tramos con
    puente necesitan ≥ 1,5 mm (estaño) o 2,2 mm (0 Ω 0603) y las marcas ≥ 1,2 mm de separación, así
    que los pasos reales son más gruesos que los pedidos (el programa los recalcula y los indica).
23. Exportación con ajuste: cada pieza de cobre de la cara superior es un pad custom con su net
    (ANT en el conector, GND en las islas de la red en π, ANT_n el resto) para que el DRC no vea
    cortocircuitos entre tramos, componentes y radiador.
24. Lo que toca el NanoVNA (incluido el botón «Medir» de la interfaz) solo con el usuario delante.
25. `ancho_minimo` no ve una pista estrecha si es corta respecto al perímetro total (el transformador
    de 0,7 mm del parche): la malla quedó en 1,2 mm, el parche salió desconectado y el ajuste persiguió
    una resonancia falsa (η 2 %). Cada generador debe declarar `info['pista_minima_mm']` y
    `info['hueco_minimo_mm']`; `simular` avisa si η < 10 %.
26. El Sierpinski se toca en vértices (ancho cero) y su vértice inferior es un punto: conexión
    dependiente de la malla y resonancias que saltan. Ahora lleva `cuello` (uniones de ~1 mm) y la
    línea entra en el triángulo hasta su ancho.
27. La quasi-Yagi resuena donde toca pero da ~15 Ω en el objetivo: tras ajustar la frecuencia,
    `simulacion._ajustar_adaptacion` varía `alto_cps` (`PARAM_ADAPTACION`) buscando el mínimo de S11.
28. Coste del FDTD: el paso de tiempo lo fija la celda más pequeña, así que una pista fina a baja
    frecuencia es carísima (Hilbert de 868 MHz con celdas de 0,22 mm: >3 h por iteración). La malla
    adaptada (`malla='adaptada'`, `lineas_adaptadas`) reduce celdas pero no los pasos. Sus líneas
    finas deben caer en la rejilla de la uniforme: con rejillas sueltas por zona salían celdas
    diminutas (más lenta) y el meandro se rompió (−8,7 %, η 0,8 %). Alineada, validada con
    `comparar_mallas` (meandro, Koch, Yagi, J-pole de Koch): |Δf| ≤ 0,1 %, misma ganancia y η
    (±0,2 dB / ±5 %); hasta ~30 % más rápida en placas alargadas, igual en las compactas.
29. Exportación: una pieza de B.Cu con huecos se parte (`sin_agujeros`) en trozos que se solapan;
    cada trozo lleva una prioridad de zona distinta para que el DRC no dé `zones_intersect`.
30. Vías en la simulación: `Antena.vias` [(x, y)] → hilo PEC vertical (`AddBox` degenerado) de cara a
    cara; una caja del diámetro real, más fina que la celda, puede desaparecer de la malla. **El hilo solo
    existe si cae exactamente en una línea de malla** (openEMS lo descarta sin avisar): `simular` lo lleva
    a la línea más cercana una vez hecha la malla. Hasta el 01-11 no se hacía: las vías de la Yagi
    comercial y el hilo del coaxial del panel no estaban en el modelo (la caché lleva 'en_malla' en la clave).
31. Yagi: con parásitos cerca, el dipolo excitado baja a ~10–15 Ω (física de toda Yagi, no del tipo
    de dipolo). Con alimentación directa solo adapta alejando el reflector (~0,35 λ); para una placa
    compacta hace falta transformar (λ/4 en el boom) o un dipolo plegado. Las separaciones de una
    Yagi van en λ0, no proporcionales al largo de los elementos (con Koch encogerían).
32. Los valores por defecto de los parámetros están pensados para 2,4 GHz (salvo el Hilbert, de
    868 MHz). Al cambiar de banda, `dimensionar` escala con λ las medidas de `tipos.ESCALABLES`
    (modo `escalado` = 1); sin ello, a 868/433 MHz las pistas de 1 mm quedan finas (malla fina y paso
    de tiempo pequeño → simulación muy lenta) y a 5,8 GHz los huecos quedan grandes. `ajustar` llama a
    `dimensionar(..., fijos=parámetros recibidos)` para no deshacer una medida fijada a mano. No escalar lo
    fijado por la impedancia con el grosor del FR4 ni lo de fabricación/conector; en los fractales
    densos la pista va con el paso de la curva, no con λ.
33. `antena.info` solo con tipos de Python (float, no `np.float64`): la interfaz hacía
    `v in (None, [], {})` y con numpy revienta (error 500 al elegir el array). Tras cambiar `gui/app.py`
    hay que reiniciar el servidor de la interfaz (no recarga solo).
14. Las curvas densas (Hilbert de orden alto) pueden pisarse y fundirse en un bloque macizo sin
    que se note en los huecos: `fabricacion.comprobar` compara el área con largo × ancho.34. Panel de dipolos (`panel_dipolos`): reflector = `Antena.reflector` (lámina PEC en z = −separación + hilo
    vertical de la malla del coaxial); puerto `tipo='pasante'` (vertical en el centro). Al exportar, el
    taladro del coaxial es un NPTH con el cobre retirado alrededor (`HOLGURA_TALADRO`); las aperturas de
    máscara van como `fp_poly` dentro de la huella con `allow_soldermask_bridges` (como `gr_poly` sueltos
    el DRC da `solder_mask_bridge`) y una zona sin ningún pad de su net da `isolated_copper` (se añade un pad GND).
35. Arrays con red corporativa (panel 2×2): S11 ondulado de −10…−15 dB en ~1,9–3 GHz, así que el centro de
    la banda a −10 dB salta ±20 % con cambios de 0,5 mm y la secante oscila. `ajustar` no itera la frecuencia
    en la familia `panel` (una simulación, luego adaptación si S11 > −10 dB) y calcula el diagrama en f_obj
    (`simular(..., f_radiacion=)`); lo que fija la frecuencia útil es la ganancia frente a f, no S11. Igual en la
    familia `array` (el 2×2 de parches: 28,6 mm → 2382 MHz y 27,9 mm → 2105 MHz; 5 h por iteración).
36. Panel con todos los dipolos antipodales iguales: el haz del 2×2 sale 9° inclinado en el plano E (−1,1 dB
    de frente; 3° en el 4×4). No es el coaxial (sin su hilo sale idéntico: el hilo de λ/4 al reflector hace de
    choque) ni el dipolo (solo, es simétrico): las columnas se desfasan ~45° por el acoplo distinto. Por
    defecto (`simetrico` = 1) cada bloque 2×2 lleva la columna izquierda espejada y un cruce de tiras con dos
    vías en su rama (`directivas.HUECO_CRUCE`). `exportar.placa_kicad` saca `Antena.vias` y reparte nets por
    grupos conectados a través de ellas (ANT el del conector, GND el del cobre inferior): con el cruce hay
    cobre inferior ANT y superior GND. **La inclinación resultó ser un artefacto de la simulación**: el panel
    entero reflejado en x (variante `espejo`) también sale hacia φ 180°, y el simétrico con las vías ya
    conectadas igual (9°). La causa sigue sin aparecer.
37. Mirar siempre `FDTD timestep is` en el log: las líneas del puerto y de los bordes no caen en la rejilla y,
    si quedan a micras de otra, la celda diminuta hunde el paso (6e-19 s en la quasi-Yagi y el array de
    parches, 27× menor en el Hilbert): 400 000 pasos sin converger y resultado basura. `simular` funde las
    líneas a menos de `FUSION_LINEAS` × paso (prioridad: puerto > rejilla y caras > resto; la primera
    versión quitaba a veces la línea del puerto y el Hilbert corrió 40 min con energía 0: ahora `simular`
    se para si alguna coordenada del puerto no está en la malla); esas
    mallas guardan la caché en `<clave>_f`. La caché solo cuenta si la tensión del puerto se apagó
    (`_terminada`): antes bastaba con que existiera `port_ut_1`, y una simulación parada a mano dejaba
    una caché «hecha» de una muestra (error `index 1 is out of bounds` en `CalcPort`).
41. **Calibración de las estimaciones** (`herramientas/calibrar_estimaciones.py` → `antenas/calibracion_estimaciones.json`):
    factor f_simulada/f_fórmula por tipo (y por iteración en los fractales: `tipos.clave_calibracion`), por
    banda e interpolado en log f; `estimar_f` (y con ello `dimensionar` e `info['f_estimada_MHz']`) lo aplica;
    `estimar_f(..., calibrada=False)` da la fórmula sola. Los rótulos de las marcas NO lo usan (van con
    `k_sim`). Solo usa `_validacion2..4` (lo anterior es de otros generadores). Con ella el tamaño inicial
    queda a 0–3 % del ajustado (antes hasta 20 %). Regenerarla tras nuevas simulaciones y reiniciar la interfaz.
42. Mirar SIEMPRE la dirección del haz en las directivas (`direccion_max`; φ 90° = +y, hacia los directores):
    la Yagi con boom de Koch (3 directores) y la quasi-Yagi de Koch salen hacia −y (hacia el reflector),
    y las rectas hacia +y. Causa (`herramientas/diag_yagi_boom.py`: recto bien con reflector 1,05; Koch al
    revés con 1,05): el excitado son dos brazos de Koch de L/2 y los parásitos eran una sola curva de Koch
    de L, con muescas el doble de grandes y eléctricamente más corta: el reflector hacía de director.
    Corregido en `directivas._elemento` (parásitos con la forma del excitado; rectos sin cambios).
43. Ranura del parche: su profundidad se mide desde el borde radiante (el más bajo del parche), no desde la
    entrada; en el Minkowski de iteración 3 la entrante central ya mete la entrada ~L/6 y la línea llegaba al
    centro (1,7 Ω, −15 dBi).
44. COCO impresa: cada tramo debe ser una microstrip (tira estrecha = vivo arriba, ancha = malla abajo). Con
    las dos tiras iguales la línea queda equilibrada, las corrientes se cancelan y no radia (η 8 %, −6 dBi).
    Lo que radia es la corriente por la cara exterior de las mallas, que el cruce de vías pone en fase.
45. Yagi con boom, `alimentacion` = 2: dipolo plegado (brazo partido como el normal + conductor superior entero
    en F.Cu, unido al brazo inferior por una vía en el extremo izquierdo): ×4 la impedancia, para adaptar con
    el reflector cerca sin transformador. La antena queda en cortocircuito en continua (vivo–masa por la
    vía): `exportar.placa_kicad` lo detecta (grupo del conector con cobre inferior) y lo pone todo en GND,
    pad central del SMA incluido; si no, el DRC da `shorting_items`.
40. Serigrafía de las placas exportadas: `exportar_todo(..., etiqueta=[líneas])` rotula la cara inferior sobre
    la masa (o, sin masa, lejos del cobre superior) y a > 7,5 mm del SMA (sus vías), buscando en rejilla
    dónde cabe (`_hueco_texto`, letra 1,2 → 0,8 mm, trazo ≥ 0,15 mm, girada si hace falta; quita líneas por
    el final si no cabe). «vivo»/«malla» y las referencias de los puentes buscan sitio dentro de la placa
    (en puntas estrechas, solo el número del puente). Comprobar con `kicad-cli pcb render`.
    **Logo** (`exportar_todo(..., logo=True)`, `antenas/logo.py`): el grillo y «Chirptenna» como polígonos de
    shapely (texto con `TextPath` de DejaVu Sans Bold, par-impar para los huecos de las letras), trazos ≥ 0,16 mm,
    `gr_poly` rellenos en B.SilkS espejados en x; girado −90° para leerse como el texto girado de KiCad. Hay que
    pasar la geometría por `_valida` (make_valid + `set_precision` 1 µm): las Koch engordadas dan
    «non-noded intersection» en GEOS. `_serigrafia` prueba logo→texto y texto→logo y prioriza: logo (si se pidió),
    1.ª línea, resto de líneas, tamaño. `logo`: 'grande' (14 → 7 mm, luego el pequeño), 'pequeno' (6 → 4 mm,
    solo el grillo en placas estrechas) o None; con logo, si no cabe ni el grillo, la palabra «Chirptenna».
    **Decisión del usuario (04-11): logo grande por defecto, pero se puede quitar**, con un aviso amable que pide
    mencionar el proyecto (`AVISO_SIN_LOGO`). No forzarlo: es software libre (AGPL; se quita igual) y la placa es del usuario.
    La selección (`serigrafia` en `diseno.json`; `logo` antes era bool) se recupera al abrir. La huella
    `.kicad_mod` no lleva logo.
38. Las marcas de corte y `f_sin_cortar_MHz` se rotulan con la estimación analítica, que falla un ~5 %. Al
    acabar, `ajustar` guarda en los parámetros `k_sim` = f simulada sin cortar / estimada (`tipos.k_sim`), y
    los generadores con marcas (monopolos, parche, J-pole, quasi-Yagi) lo aplican solo a los rótulos; la
    geometría de las marcas es relativa y no cambia.
46. Aligerado (`tipos._aligerar`, `geometria.ventanas_aligerado`): las ventanas son **huecos del contorno**
    (`contorno.interiors`). Todo lo que use el contorno debe mirar también los interiores: simulación (aire con
    prioridad 1 sobre el FR4), Edge.Cuts, vista y distancia del cobre al borde (`contorno.boundary`). Evitan
    taladros, el SMA y el coaxial pasante, y dejan una espina central y nervios cada `paso`.
47. Interfaz: el fondo de la página se fija en CSS (`body.body--light` / `body.body--dark`): transparente se
    veía negro con el navegador en tema oscuro. Tema automático/claro/oscuro con el botón de la cabecera
    (`ui.dark_mode`; preferencia en `app.storage.general`, carpeta `.nicegui/` ignorada por git). Toda figura
    de Plotly pasa por `T(fig)` para adaptarse al tema; una gráfica nueva sin `T()` sale blanca en oscuro.
    **No usar las clases de color de Quasar para texto** (`text-grey-8`, `text-blue-grey-9`, `color=` de
    `ui.icon`…): en NiceGUI 3 van en un `@layer` con `!important` y ninguna regla propia las puede cambiar en
    oscuro. Usar las propias de `gui/app.py`: `texto-sec`, `texto-aviso`, `texto-violeta`, `icono-titulo`,
    `pestanas` (cada una con su variante `.body--dark`).
39. Parches (`parche_rectangular`, `parche_minkowski`): `alimentacion` 0 = por el borde con transformador
    λ/4; 1 = por ranura (inset) hasta R = R_borde·cos²(π·d/L) = 50 Ω (`muesca` en mm, 0 = estimada;
    `hueco_muesca`). Con ranura la línea solo cruza el margen de masa (se ignora `largo_alimentacion`) y
    `ajustar` afina la profundidad de la ranura como parámetro de adaptación. En la interfaz se llama
    «ranura» para no confundirla con la «muesca» del fractal de Minkowski. Minkowski de 868 MHz:
    93 × 148 mm con transformador, 93 × 93 mm con ranura.
