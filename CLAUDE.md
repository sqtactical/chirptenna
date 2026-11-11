# Chirptenna: generador de antenas fractales para PCB

Objetivo final: un programa que genere antenas (fractales) impresas en PCB para una
frecuencia objetivo. Las ajusta simulando con openEMS, exporta a KiCad/DXF/Gerber y tiene
interfaz gráfica. Antes de eso se valida el simulador y se mide la εr real del FR4 con un
NanoVNA, para que las simulaciones coincidan con las placas fabricadas.

**Estado actual y siguientes pasos: leer `RETOMAR.md` al empezar.** Es la nota de traspaso
entre sesiones: mantenla al día cuando se avance o cambie el plan. Este archivo recoge lo
estable: cómo está montado, cómo se ejecuta y las reglas. **El plan a medio plazo está en
`ROADMAP.md`** (fases, con casillas): el rumbo es integrar antenas en la PCB de un producto real
y no se añaden tipos nuevos hasta medir las placas (fase 1). Al terminar una tarea de ahí,
márcala; si el usuario no pide otra cosa, lo siguiente sale de la primera fase sin cerrar.
Cada tarea (F1.1, F2.3…) tiene sus pasos, pruebas y criterio de «hecho» en
`docs/desarrollo/roadmap/` (**leer antes `00_como_trabajar.md`**); las guías citan funciones y
archivos del 11-11: si algo ya no existe, buscarlo antes de inventarlo.

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
  Al cambiar tipos o su estado, actualizar la tabla de tipos de los dos README. `MANUAL.md` (manual de uso,
  solo en castellano) cita los textos de la interfaz y los valores por defecto del ajuste (`antenas/ajuste.py`):
  **actualizarlo al cambiar etiquetas, pestañas o el asistente**; sus ejemplos de red en π salen de `ajuste.redes_l`.
  `INSTALAR.md` e `INSTALL.en.md` van en paralelo (mismos apartados).
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
| `gui/` | `app.py`: interfaz NiceGUI por fases: barra fija (nombre, tipo, banda, guardar) y pestañas **Elegir antena** (galería por grupos de uso con miniatura, resumen y estado; es la de entrada) / Diseño / Simulación / Fabricar / Medir (asistente del NanoVNA) / Mis diseños. El selector de tipo muestra resumen y estado con slots de Quasar (etiqueta «nombre\|resumen\|estado\|comentario»). En Diseño solo los parámetros **básicos**; el resto bajo «Ajustes avanzados» (`ui.expansion`); cada parámetro lleva un botón «?» con su ayuda en un `ui.menu` (burbuja al pinchar). Galería, básicos y ayudas salen de `antenas/guia.py` (`GRUPOS`, `TIPOS`, `BASICOS_AJUSTE`, `AYUDAS`, `AYUDAS_TIPO`; `guia.comprobar()` lo exige completo y lo pasa `comprobar_tipos.py`) y el estado («Validada», «Pendiente de validación», «No funciona») de `problemas.ESTADO`; **al añadir un tipo o un parámetro, completar los dos**. Miniaturas: `antenas/miniaturas/*.svg` (`herramientas/generar_miniaturas.py`; regenerarlas si cambia un generador). Plotly no se inicializa si su figura se pone con la pestaña oculta: se reenvía al entrar en Diseño. `antenas/biblioteca.py` guarda cada diseño en `Documentos\Chirptenna\disenos\<nombre>` (`diseno.json`, `simulacion/`, `fabricacion/`, `medidas/`); `CHIRPTENNA_DISENOS` cambia la ruta (úsala en pruebas para no ensuciar la del usuario) |
| `web/` | **Versión web lite** (GitHub Pages, https://sqtactical.github.io/chirptenna/): diseñar, ver y descargar para KiCad (`.kicad_pcb`, huella, DXF, `diseno.json`, LÉEME); sin simulación ni DRC de KiCad. Mismo flujo que el escritorio: galería (sale al instante con `catalogo.json` y `miniaturas/` precalculados por `construir_web.py`, mientras Pyodide carga), selector de tipo propio con descripción y estado, básicos + «Ajustes avanzados» y burbuja «?» por parámetro. `index.html` + `app.js` (interfaz, sin frameworks; SVG propio) + `motor.js` (Web Worker con **Pyodide 0.29.3**: numpy, shapely, ezdxf por micropip). Python corre en el navegador: `antenas/web_api.py` (JSON de entrada y salida: `catalogo`, `dimensionar`, `generar`, `exportar` → zip; `VERSION_API`). `herramientas/construir_web.py [salida]` copia `web/` y empaqueta el **núcleo** (`NUCLEO`: lo que importa `web_api`, sin openEMS/NanoVNA/NiceGUI/matplotlib/KiCad; falla si se cuela algo) en `py/antenas.zip`; en local, launch.json "web-lite" (puerto 8095, sirve `salidas/web`). Textos compartidos con el escritorio en `antenas/presentacion.py` (bandas, serigrafía, etiquetas de `info`, parámetros visibles). `herramientas/prueba_web.py`: Playwright + Chromium genera los 32 casos dentro de Pyodide y pasa el DRC de KiCad (en la CI; `PRUEBA_WEB_CANAL=msedge` en local). `.github/workflows/web.yml` publica con cada release (o a mano) |
| `cupon/` | Cupones de εr en placas de 100 × 100 mm: `generar_cupon.py` → `cupon_A/` (anillos 868 MHz y 2,4 GHz) y `cupon_B/` (anillo 5,8 GHz n=3, líneas abiertas S80/S30, líneas en L L64/L17, CPWG de 50 Ω con valla de vías y microstrip de 100 Ω), cada una con placa, Gerber, zip para JLC, DRC, `diseno.json` y leyenda en la serigrafía inferior; radios de los anillos ×0,93 (`CORRECCION_ANILLO`). `vista_gerber.py <cupón>`, `simular_anillo.py <anillo>` (openEMS con puertos MSL; caché por radio). `_antiguo_185x100/`: el cupón anterior |
| `placa_sim/` | Importador Gerber → openEMS de una placa entera (`simular_placa.py`) y `comparar_sim.py` |
| `salidas/` | Exportaciones de la interfaz (`salidas/<nombre>/`); `_pruebas/` son pruebas internas |
| `referencias/` | Modelos de antenas reales para comparar simulación y medida: `yagi_comercial.py` (Yagi 2,4/5,8 del usuario: dipolo plegado apilado con balun de «U», `python -m referencias.yagi_comercial [dibujar\|simular]` → `salidas/_referencias/`) |
| `herramientas/` | `comprobar_tipos.py`: **antes de cada release o cambio en un tipo**, genera y exporta los 16 tipos a 868 y 2441,75 MHz (DRC + reglas, ~2 min, código 1 si algo falla; resumen en `salidas/_comprobar_tipos`). `cola.py`: **cola FIFO de simulaciones** en `%LOCALAPPDATA%\antenas\cola` (`pendientes/`, `en_curso/`, `hechos/`, `registros/`): `añadir <nombre> <comando…>`, `ver`, `trabajar [--hilos 6]` (dos trabajadores = dos simulaciones a la vez; cogen por orden de nombre, así que se reordena renombrando; acaban tras 10 min sin trabajo). Usarla en vez de encadenar scripts de espera. `comparar_medida.py <simulado> <medida.s1p> [--banda a b] [--ventana a b]`: compara S11 simulado y medido (centro de banda a −10 dB, ancho, mínimo; `.json` + `.png`; hoja de ruta F1.2). `mantener_despierto.ps1`: evita la suspensión mientras haya simulaciones (SetThreadExecutionState; la pantalla sí puede apagarse); se cierra solo tras 10 min sin ellas (las detecta por línea de comandos o por un python con > 30 s de CPU por minuto). Lanzarlo en segundo plano junto a lotes largos. **Barridos** (`barrido.py`, `campana.py`, `cola_extra.py`, `resumen_barridos.py`, `doble_banda.py`) y **bibanda experimental** (`jpole_dual.py`, `rama_dual.py`, `radiacion_bibanda.py`, `diagrama_bibanda.py`, `topologias.py`, `sensibilidad_er.py`; ver lecciones 56–57 y 64–69) |
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
- **Idiomas de la interfaz (i18n, rama `i18n`)**: el castellano es el texto fuente y sirve de clave (estilo gettext).
  `antenas/i18n.py`: `tr('texto {0}', x)` traduce y formatea (si falta la traducción sale el castellano, nunca
  falla); `N_()` solo marca. Un idioma es `antenas/idiomas/<código>.json` (`_nombre` + `textos`): **para añadir uno,
  `python herramientas/i18n.py nuevo it Italiano`, traducir los valores y listo** (sale solo en el selector de la
  cabecera). Hoy: `es` (fuente), `en`, `fr` y `de` (traducidas por Claude, a revisar por hablantes nativos) y el
  easter egg **`lora`**: pseudoidioma calculado (`i18n.chirp`, sin fichero) que cambia cada letra por `/`, `\` o `_`
  y respeta números, unidades y marcas `{0}`; no sale en el selector (se activa con `?idioma=lora` o pinchando 5
  veces el grillo de la cabecera, y otros 5 lo quitan). Reglas: todo texto nuevo de la interfaz o de un mensaje al usuario va con `tr(...)`; en f-strings,
  `tr('plantilla {0:.1f}', valor)` (nunca f-string dentro de `tr`); **nada de `tr` a nivel de módulo ni en
  valores por defecto** (se evalúa al importar, con el idioma equivocado): los textos de datos estáticos
  (`guia`, `tipos`, `problemas.FIJOS`…) se dejan en castellano y la interfaz los traduce al mostrarlos
  (`tr(p.etiqueta)`). Las claves internas (nombres de tipo/parámetro de `diseno.json`, `BANDAS`, categorías de
  consejos) no se traducen. `herramientas/i18n.py faltan [código]` lista lo que falta (código 1; lo pasa la CI),
  `actualizar` añade claves nuevas, `limpiar` quita las que sobran. El idioma es global del proceso (interfaz de un
  solo usuario): `app.storage.general['idioma']`, `?idioma=en` en la URL o `CHIRPTENNA_IDIOMA`; el subproceso de
  simulación lo hereda. **Web lite**: `web/app.js` usa `T('texto {0}', x)` y los elementos con `data-t` de
  `index.html` (vacío = su texto; `data-t='…'` = la clave, con marcas HTML), carga `idiomas/<código>.json` (los mismos
  catálogos, copiados por `construir_web.py`) y manda `idioma` a Python, que traduce consejos, avisos, comprobaciones y
  el LÉEME del zip; `herramientas/i18n.py` extrae también esos textos. La serigrafía de la placa usa el idioma
  elegido (`vivo`/`malla`, texto del reflector).
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
49. **Entorno de la sesión de Claude** (no del usuario): el venv `%LOCALAPPDATA%\antenas` lo creó un proceso de la app de
    Claude y vive virtualizado en `AppData\Local\Packages\Claude_…\LocalCache`; `Path.resolve()` de un archivo da esa ruta
    y la de su carpeta no. Consecuencias: NiceGUI responde **403** a sus módulos ESM (Plotly sale en blanco) y pip falla
    («Resource name escapes package»). Para verificar la interfaz aquí, lanzarla con un envoltorio que acepte las dos
    rutas en `is_relative_to` (launch.json «escritorio-prueba», script en el scratchpad); los menús de Quasar no se abren
    con el panel del navegador oculto: usar Edge sin ventana por CDP. En el ordenador del usuario no pasa nada de esto.
48. **Versión web (Pyodide)**: todas las versiones de Pyodide (0.27–0.29) traen shapely 2.0.7 con **GEOS 3.12**, más
    antiguo que el de escritorio, y uniones o diferencias delicadas (Sierpinski, aperturas de `fabricacion.comprobar`)
    lanzan `TopologyException`/«non-noded intersection». En Pyodide esa excepción de C++ **tumba el intérprete**
    («Pyodide has suffered a fatal error»), no se puede capturar. `antenas/robusto.activar()` (solo en el navegador,
    desde `web_api`) hace que union/difference/intersection/symmetric_difference/union_all usen `grid_size` = 0,1 µm:
    GEOS pasa al redondeo robusto, que no falla. Validado: DRC de KiCad 32/32 con el modo robusto, cobre ±0,19 mm².
    `fabricacion.comprobar` ya usa `grid_size` siempre. Al añadir código de geometría, probarlo también en la web
    (`prueba_web.py`). El texto del logo («Chirptenna») va precalculado en `antenas/logo_texto.json`
    (`herramientas/generar_logo_texto.py`) para no necesitar matplotlib.
39. Parches (`parche_rectangular`, `parche_minkowski`): `alimentacion` 0 = por el borde con transformador
    λ/4; 1 = por ranura (inset) hasta R = R_borde·cos²(π·d/L) = 50 Ω (`muesca` en mm, 0 = estimada;
    `hueco_muesca`). Con ranura la línea solo cruza el margen de masa (se ignora `largo_alimentacion`) y
    `ajustar` afina la profundidad de la ranura como parámetro de adaptación. En la interfaz se llama
    «ranura» para no confundirla con la «muesca» del fractal de Minkowski. Minkowski de 868 MHz:
    93 × 148 mm con transformador, 93 × 93 mm con ranura.
50. **Unidades de `tipos.dimensionar` y `simulacion.simular`: Hz** (la CLI y la interfaz trabajan en MHz y
    multiplican). Pasar MHz da antenas de kilómetros (el parche) o topadas contra el límite del parámetro (los
    monopolos) y la malla revienta sin avisar.
51. **GPU (rama `gpu-pruebas`, publicada el 06-11; en la v0.2.0 va en `main` como opción)**: `antenas/gpu.py` lanza el `openEMS.exe` de `master` con `--engine=gpu`
    (escribe el XML con `FDTD.Write2XML`; el wheel 0.37 no elige motor). Por defecto se usa si está disponible;
    `ANTENAS_GPU=0` fuerza la CPU (ajustes finales). Se compiló en `%LOCALAPPDATA%\Programs\gpu-build` (CMake, Ninja,
    CUDA 12.9 redistribuible, cabeceras HIP, vcpkg, MSVC 14.44 portable: nvcc 12.9 no soporta el 14.51 de VS 18).
    `herramientas/comparar_gpu.py <tipo…> [--radiacion]` compara CPU y GPU (~10–13× más rápida en una RTX 3050
    Laptop; f ≤ 0,06 %, S11 ≤ 0,6 dB, Z ≤ 3 Ω). Con una sola GPU, una simulación a la vez.
52. **Panel y malla (06-11)**: en el panel la frecuencia sale hasta ~10 % distinta según la malla (la primera iteración de
    `ajustar`, con malla automática, da 2525 MHz y las siguientes, con el paso fijado al 90 %, 2284 MHz con el mismo
    largo). Para afinarlo, fijar el paso con una simulación de calibración y elegir por **S11 en toda la banda**, no por
    el «centro de banda» (salta con el S11 ondulado): `herramientas/barrido_panel.py <tamano> <elemento> <largos,…> [etiqueta] [param=valor,…]` (GPU). Resultados 2,4 GHz: Sierpinski it. 2 a 18,2 mm (−23,6 dB, 12,6 dBi), recto a
    19,14 mm (−16,3 dB, 12,1 dBi), bowtie liso a 18,4 mm (irregular); las iteraciones 1, 2 y 3 de Sierpinski dan lo mismo
    (18,2 mm, −20,9/−23,6/−24,8 dB, 12,6 dBi, η 78 %): el largo no depende de la iteración. COCO a 868 MHz: η 26 %, −2 dBi. Con malla fina el haz del 2×2 sale de frente
    (0–3°): la inclinación de 9° de la lección 36 era un artefacto de la malla. `directivas.K_BOWTIE_PANEL` y
    `K_MALLA_FINA_PANEL` y `dipolos.K_BOWTIE`/`K_SIERPINSKI` salen de ahí.
53. **Bowtie = tipo propio** (dipolo_bowtie, 06-11): mismo generador que el dipolo (dipolos.generar_dipolo; con orma > 0 el Antena.tipo sale dipolo_bowtie) pero entrada propia en la galería y en el catálogo. El dipolo ya no tiene orma/pertura/iteracion_s. Un diseno.json viejo con clave dipolo y orma > 0 sigue generando (los parámetros extra se aplican igual).
54. **Parche circular (parche_circular, 06-11): sin testear ni validar.** Parche casi cuadrado con dos esquinas opuestas cortadas (corte = fracción del lado, diagonal elige cuáles) y alimentación por el borde; reutiliza _generar_parche (poligono_parche aplica el corte). Falta: simular la razón axial (el NF2FF solo guarda ganancia), el sentido de giro (GPS e Iridium son RHCP) y calibrar tamaño y corte. Bandas nuevas (915 ISM, 1,2 GHz, GPS L1, Iridium, 5,8 GHz) en presentacion.BANDAS: solo 868 MHz y 2,4 GHz están simuladas.
55. **Siete tipos nuevos sin validar (06-11)**: ifa y pifa (F invertida; familia monopolo, vía de cortocircuito a masa en Antena.vias, el exportador la trata como un cortocircuito en continua), dipolo_sleeve (monopolo con masa manual en forma de manga), ivaldi (antipodal, dipolos.generar_vivaldi), colineal_dipolos (dipolos en fila: brazo inferior bajo la línea y superior a continuación, unidos por microstrip de λg; dipolos.generar_colineal_dipolos), parche_ranura (ranura en U en poligono_parche) y parche_apilado (en realidad un parásito acoplado en la misma cara: un apilado de verdad necesita segunda placa y no está modelado). Todos con estado «pendiente» y aviso de sin testear en problemas.py; faltan simulación, calibración y revisión. La colineal con coaxial real a lo largo de la placa no se hizo: openEMS solo modela el coaxial como puerto.
56. **Barrido genérico de parámetros** (`herramientas/barrido.py <tipo> <f_MHz|banda> param=v1,v2… [--modo grid|uno] [--top N]`): simula en GPU todas las combinaciones (o cada parámetro por separado) con la malla fija del paso más fino, y da el peor S11 en la banda, la banda a −10 dB, Z en el objetivo y, de las mejores, ganancia, eficiencia, dirección y polarización (`simulacion.simular` guarda `ar_dB_max`, `ar_dB_theta0`, `pol_max`, `pol_theta0`; RHCP = Eθ + jEφ dominante con e^{jωt}: comprobar el sentido con un parche circular conocido). Resultados en `salidas/_barridos/<etiqueta>/`; se retoma si se corta; un bloqueo (`%LOCALAPPDATA%\antenas\gpu.lock`) evita dos barridos a la vez en la GPU. `herramientas/campana_nuevos.ps1` lanza los de los 8 tipos nuevos.
57. **Campaña de barridos en GPU (`herramientas/campana.py`)**: etapa A = una simulación por tipo y banda (868, 915 ISM, 1,2 GHz, GPS L1, Iridium, 2,4 y 5,8 GHz) con el tamaño de `dimensionar`; etapa B = barrido de varios parámetros (`TABLA_B`, factores `xF` sobre el tamaño ajustado: valen en cualquier banda) donde A sale mal (peor S11 en la banda > −10 dB o resonancia a más del 3 %). Todo con `--radiacion` (ganancia, eficiencia y polarización en cada configuración). Resultados en `salidas/_barridos/<A|B>_<tipo>_<banda>` y `salidas/_campana/resumen.csv`; reanudable. En `barrido.py`, los parámetros discretos (iteración, orden…) recalculan el tamaño base de cada combinación.
58. **Monopolo de punta de flecha de Sierpinski (`monopolo_flecha`, 06-11): curiosidad, sin validar.** Una sola pista (sistema L de 60°, `geometria.flecha_sierpinski`) que rellena un triángulo con la base sobre el eje de alimentación; longitud total = base·(3/2)^iteración; la pista va con la base (`escala_conjunta`) para que las vueltas no se pisen. No hay una antena publicada conocida con esta curva (la búsqueda solo dio el gasket de Sierpinski). Longitud equivalente = base·(1 + 0,35·(1,5^it − 1)) sin calibrar. Entra en `herramientas/campana.py`.
59. **Sierpinski de dos bandas (`multibanda` = 1, 06-11)**: el monopolo de Sierpinski resuena en un armónico a ~3× la fundamental (no ×2: con apertura 60° la razón es 3,3 y baja con la apertura hasta ~3,1 a 90°; más allá aparecen modos nuevos y empeora). Con apertura 85°, iteración 2 y altura = 0,98 × el tamaño de una banda se cubren 868–870 MHz y 2400–2483,5 MHz con una sola alimentación (S11 −13 y −11,6 dB con malla de 0,7 mm; G 2,2 y 4,5 dBi, η 92 y 88 %; placa ~96 × 115 mm). `tipos.dimensionar` lo aplica (`MULTIBANDA_SIERPINSKI`) y `simulacion.ajustar` hace una sola simulación de banda ancha (0,45–3,8 ×) con el diagrama en f_obj. Solo simulado con esa pareja de bandas; probado con el monopolo, no con el bowtie de Sierpinski.
60. **Sierpinski de dos bandas para LoRa (06-11)**: con apertura 85°, iteración 2 y altura 50,17 mm se cubren 868–870 y 2400–2483,5 MHz (−13,0 y −11,6 dB); con 49,7 mm, 902–928 (915) o 863–928 MHz (antena «universal») y 2,4 GHz a −10,0 y −9,7 dB (justo, sin centrar, una simulación por configuración). `tipos.MULTIBANDA_ALTURAS` guarda esos puntos simulados y la banda predefinida «LoRa 863–928 MHz» (`presentacion.BANDAS`) elige el universal. A 915 MHz la banda alta (razón 2,67) es la que se queda corta; subir la altura mejora 2,4 GHz y empeora la banda baja.
61. **Campaña de GPU del 06–07-11 (resultados en `docs/desarrollo/barridos_gpu.md`)**: de 868 MHz a 5,8 GHz van (S11 ≤ −10 dB en
    simulación, centrados) los monopolos recto/Koch/meandro/Sierpinski, dipolo, bowtie y sleeve; IFA y PIFA a 868 MHz, 2,4 y
    5,8 GHz (no a 1,2 GHz); Vivaldi a 2,4 y 5,8 GHz; colineal de dipolos a 2,4 GHz (con `factor_linea` 0,9); Yagi recta a 868 MHz,
    2,4 GHz y (con el haz por revisar) 5,8 GHz. No van: parches (el rectangular solo a 5,8 GHz; a 2,4 GHz la banda de ~36 MHz no
    cubre la ISM), Minkowski, circular, ranura (η 4 %), apilado, array, J-pole recta (−2 a −3 dB), J-pole de Koch a 5,8 y 1,2 GHz,
    COCO, Franklin a 5,8 GHz, flecha e Hilbert (ni siquiera en armónicos). Parches en RO4350B: η 89 % pero no adapta con 3
    simulaciones de centrado; sin masa bajo la alimentación (`masa=0`) empeora: el FR4 y su pérdida, no la masa, limitan al parche.
62. **El «va» de una Yagi hay que mirarlo con la dirección del haz** (`direccion_max`, φ 90° = hacia los directores): en la Yagi
    de Koch de iteración 1 el −21 dB corresponde a φ 270° (hacia atrás) y las configuraciones con el haz hacia delante dan −6,6 y
    −8,6 dB. `resumen_barridos.py` ya marca «haz atrás» y prefiere las que radian hacia delante.
63. **Panel**: el largo del brazo apenas mueve la resonancia (+4 % de largo baja solo ~1 %; a 5,8 GHz el 2×2 resuena a 4800 MHz con el
    tamaño por defecto, −17 %): el factor de malla `K_MALLA_FINA_PANEL` no vale igual en todas las bandas. Pendiente
    calibrarlo por banda.
64. **Bibanda 868 MHz + 2,4 GHz (07–08-11, solo simulación, fuera de la interfaz)**: tres herramientas que simulan en banda ancha
    (0,45–3,8 × f_baja) y miden el peor S11 en cada banda: `doble_banda.py` (cualquier tipo; **no** tiene `--solo-lista`: no se
    lanza para validar), `jpole_dual.py` y `rama_dual.py` (sí la tienen). Funcionan: **dos J-pole unidas** (`jpole_dual.py --modo
    union`: brazo corto y barra compartidos, brazos largos unidos por una tira en B.Cu con vías; `k2` 1, `sep2` 3, `a2` 0,9,
    `toma2` 0,25, `factor_adaptador` 0,95: −11,2 y −10,6 dB, η 63/87 %) e **IFA con segunda rama** (`rama_dual.py ifa x_largo_brazo=1.17
    k2=1 h2=0.6`: −11,7 y −10,8 dB, η 79/82 %). Son estrechas (los vecinos del punto caen a −8 dB). No funcionan: la J-pole en
    abanico (un adaptador, dos radiadores; −2,9 dB) y la J-pole unida con radiadores de Koch (−0,8 a −5 dB en ~40 simulaciones: a
    868 MHz el Koch no acorta, 152 mm frente a 144 mm recto, y cada ajuste que sube una banda baja la otra). El Sierpinski
    bibanda del dipolo llega a −8,5/−9,5 dB. `radiacion_bibanda.py` y `diagrama_bibanda.py` dan η, ganancia y diagramas en cada
    banda (los cuatro mejores irradian bien, η 63–89 %; la J-pole unida a 2,4 GHz tiene varios lóbulos porque la placa mide 1,7 λ).
65. **Errores de método de la tanda del 07–08-11**: (a) las distancias entre pistas de una variante deben superar el ancho de
    pista del tipo a esa frecuencia (a 868 MHz `ancho_pista` es 2,81 mm: un `sep2` de 3 mm dejó 0,19 mm de hueco, malla de
    0,07 mm y 78 min sin acabar una simulación); (b) matar una simulación a mano deja el `openEMS.exe` huérfano y el
    bloqueo `%LOCALAPPDATA%\antenas\gpu.lock` apuntando a un proceso muerto, y la cola espera para siempre; (c) con `--koch` el
    adaptador de la segunda J-pole se escalaba con el de la curva de Koch (un 35 % más largo): las referencias de una variante
    salen siempre del diseño recto de la misma frecuencia; (d) con `--centrar` el tamaño base cambia de un barrido a otro, así
    que el mismo punto puede dar −5,7 y −8,2 dB en dos barridos: comparar dentro de un mismo barrido; (e) `mantener_despierto.ps1`
    se para solo con frecuencia: relanzarlo con cada revisión de la cola.
66. **Resultados de una sola banda de la tanda** (en `docs/desarrollo/resultados_07-11.md`): llegan a −10 dB la J-pole recta a 868 MHz
    (hueco ×5 = 14 mm, `toma` 0,26: −12,9 dB, η 92 %), la J-pole de Koch a 1,2 GHz (`toma` 0,37, `factor_adaptador` 1,13–1,16:
    −10,6 dB), el parche rectangular con ranura a 5,8 GHz (−10,6 dB en toda la banda, η 60 %), la colineal de dipolos a 2,4 GHz
    (factor de línea 1,0: −12,7 dB; **0,9 empeora**, ya no hace falta) y la Yagi con boom a 5,8 GHz (−10,8 dB con el haz hacia delante;
    la mejor por S11, −17,7 dB, radiaba hacia atrás). No van: el parche circular (GPS L1 y 2,4 GHz: ≥ −5,9 dB, razón axial ≥ 6 dB;
    la alimentación por el borde no da polarización circular y el generador no varía la posición de la entrada), la J-pole recta
    a 5,8 GHz (la parte real se queda en ~20 Ω) y el parche en ranura en U.
67. **Más resultados de la misma tanda (08-11, GPU)**: llegan a −10 dB la IFA a 1,2 GHz (`separacion_toma` 6,7, `altura` 12,1,
    `ancho_pista` 1,9: −14,0 dB), la PIFA a 1,2 GHz centrada (−13,7 dB), el dipolo a 1,2 GHz (`largo_brazo` 43,5, `ancho_pista` 2,9:
    −14,4 dB), el bowtie (apertura 55°: −13,0 dB a 2,4 GHz y −11,6 dB a 5,8 GHz), el sleeve a 5,8 GHz (−17,9 dB, `alto` 8,5,
    `largo_masa` 10, `ancho_placa` 13), el Vivaldi a 5,8 GHz (**la aleta, no la apertura, mueve la resonancia**: `largo_aleta` 68,6 mm,
    `tasa` 4: −12,3 dB), la colineal de dipolos a 5,8 GHz (4 elementos, `factor_linea` 1,1, `ancho_brazo` ×1,05: −13,8 dB, η 50 %), la
    J-pole recta a 2,4 GHz (`hueco` 6 mm: −10,9 dB), el monopolo con **IPEX** a 2,4 GHz (**masa manual** `largo_masa` 25 / `ancho_placa`
    40: −14,6 dB; con la masa automática −6,9), el panel a 2,4 GHz (reflector a 0,125–0,163 λ: −10,1 dB) y la Yagi con boom a 5,8 GHz
    (`factor_reflector` 1,15: −16,4 dB, haz hacia delante). **La flecha de Sierpinski adapta con iteración 1** (−15,9 dB, η 93 %): lo que
    fallaba era la iteración 3. **La Yagi con boom de Koch de iteración 2 funciona a 2,4 GHz** con el haz hacia delante (−14,4 dB, η 81 %,
    `factor_reflector` 1,35, `factor_director` 0,76) aunque con 2,6 dBi. No van: Hilbert (−1,4 dB, pista de 0,2 mm), Minkowski en FR4
    (η 29 %), array de parches a 5,8 GHz (η 12 %), Franklin a 5,8 y 2,4 GHz, parche rectangular a 1,2 GHz (el centrado tardó 89 min).
    Los barridos con `--centrar` no son comparables entre sí (lección 65 d).
68. **Aligerado, plano de tierra y topologías nuevas (08-11)**: (a) los recortes de aligerado de la Yagi con boom casi no cambian nada a
    868 MHz (−8,6 dB en los dos casos, η 87 %) ni a 5,8 GHz (−12,0 frente a −13,3 dB), pero a 2,4 GHz con el margen por defecto bajan
    de −12,8 a −2,3 dB, suben la frecuencia un 7 % e invierten el haz (φ 270°): con `margen_aligerado` 6 mm da −6,0 dB con el haz
    delante; el panel aligerado a 2,4 GHz da −7,8 dB (sin recortes −10,1). Simular siempre antes de fabricar. (b) **Sin plano de
    tierra**: un parche de verdad no existe (la cavidad la forma la masa); una placa rectangular sin masa debajo es un monopolo de
    placa y a 2,4 GHz funciona (3 mm −12,9 dB η 99 %; 6 mm −10,0 dB con 260 MHz de banda) sin mejorar a la pista fina; el dipolo con
    brazos anchos tipo parche NO funciona ni recentrado (−6,7 a −1,6 dB): el bowtie es la forma buena. (c) Parche con parásito
    (−0,6 dB, η 7 %) y COCO (−4,1 dB, η 24–35 %) no van. (d) `herramientas/topologias.py` es un banco de pruebas con tres generadores
    (torniquete de dipolos cruzados para GPS L1 con un puerto vertical pasante y largos distintos para el desfase de 90°, ranura de
    λ/2 en la masa alimentada por microstrip, IFA de tres bandas): el puerto `pasante` necesita también las claves `borde` y
    `direccion` (sin ellas `simular` lanza `KeyError: 'borde'`); la ranura de largo λ0/(2√((εr+1)/2)) resuena un ~20 % alta.
69. **J-pole recta arreglada (08-11)**: el diseño por defecto adaptaba mal porque el hueco entre brazos era demasiado pequeño. Ahora
    `tipos.dimensionar('jpole', …)` multiplica el hueco escalado con λ por `JPOLE_HUECO` (×5 a 868 MHz = 14,1 mm, ×6 a 2,4 GHz = 6,0 mm,
    interpolado en log f) y pone la toma a `JPOLE_TOMA` = 0,26, salvo lo que esté en `fijos`; el largo del radiador sale de una
    calibración propia de la J-pole en `calibracion_estimaciones.json` (`calibrar_estimaciones.muestras_jpole`: los diseños por defecto
    simulados sin centrar, `V_jpole_defecto_*`; **si se regeneran, hay que simular de nuevo esos cuatro**). Resultado con los valores por defecto:
    868 MHz −15,4 dB, 915 MHz −10,1 dB, 1,2 GHz −9,7 dB, GPS L1 −11,8 dB, 2,4 GHz −12,0 dB (η 86–92 %); 5,8 GHz no se ha calibrado ni va.
    Dos fallos de método: (a) `factor_calibracion` se consulta con la frecuencia de la FÓRMULA, no con la simulada: con factores de ~1,25 la
    abscisa de los puntos de la calibración tiene que ser la de la fórmula (`f_x_MHz`); (b) cortar la salida de `barrido.py` con
    `Select-Object -First 1` mata el proceso antes de su `finally` y deja `gpu.lock` colgado: el siguiente barrido espera para siempre.
70. **Bibanda en la interfaz (09-11)**: `multibanda` = 1 en `jpole` (dos J-pole unidas) e `ifa` (segunda rama); código en `antenas/bibanda.py`,
    constantes de `jpole_dual.py`/`rama_dual.py` escaladas con `ancho_pista`/2,81 (banda alta fija en 2,4 GHz); `dimensionar` las aplica sin
    el hueco ampliado de la lección 69 y `ajustar` hace una sola simulación (sin `_ajustar_toma`). **El resultado depende de la malla**: paso
    1,012 mm −11,2/−10,4 dB (J-pole) y −11,7/−10,8 (IFA); 1,124 mm −9,0/−10,7 y −14,6/−3,9; 0,7 mm −9,9/−2,6 y −10,4/−6,9. Los «−11 dB en
    las dos bandas» de las pruebas del 07-11 eran un punto afortunado de la malla: antes de dar una bibanda por buena, simularla con 2–3 pasos.
    Revisión previa a la 0.3.0 (09-11): (a) al añadir un módulo que importe el núcleo (`tipos`), meterlo en `construir_web.NUCLEO` o la web
    no se construye; (b) cambiar `multibanda` debe redimensionar (`gui/app.py` `cambiar_param` y `web/app.js`, como `masa`); (c) con dos
    bandas `estimar_f` de la J-pole y la IFA va anclada a `bibanda` (la calibración de una banda daba un 10 % de error) y `dimensionar`
    parte del tamaño de una banda (`multibanda=0`) para no alargar la IFA dos veces. El bowtie de Sierpinski no tiene dos bandas (−8,5/−9,5 dB).
71. **PTFE, flex y hélice en flex (10-11)**: `materiales.SUSTRATOS` lleva los cuatro PTFE de JLC (`PTFE_JLC`: ZYF255DA 2,55, ZYF265D 2,65, ZYF300CA-C 2,94,
    ZYF300CA-P 3,0; tanδ 0,0016–0,0019; 0,65 / 0,9 / 1,65 mm; los nombres se generan, así que **no están en los catálogos de idioma** y salen en
    castellano: `i18n limpiar` no los toca porque no son claves) y «Flex PI 25/50 µm» (εr 3,3, tanδ 0,004, sin coverlay). Regla nueva `fabricacion.REGLAS`
    «JLC alta frecuencia y flex (0,1 mm)»; `consejos` avisa por sustrato. `simulacion.simular` usa 2 celdas en z si h < 0,4 mm (con 4, la celda de 12 µm
    hunde el paso de tiempo). Resultados: el parche en PTFE da η ~90 % (FR4 ~47 %) pero la banda sigue en ~33 MHz (S_parche_ZYF265D_165_24GHz y
    S_parche_ZYF300C_165_24GHz): el PTFE no ensancha. En flex de 50 µm, a 2,4 GHz: dipolo −14,8 dB, bowtie −17,3 dB, J-pole −10,3 dB (F_*_flex50_24GHz);
    a 868 MHz el dipolo −17,1 dB; una microstrip de 50 Ω no sirve en flex (0,06–0,12 mm). La J-pole de Koch en flex y la J-pole a 868 MHz tardan > 1 h:
    se pararon. **`herramientas/helice_flex.py`** (hélice cuadrifilar para GPS L1, hilos PEC en un cilindro, dos puertos por separado y campos combinados
    con ±90°): la razón axial es 0 dB en el cénit (simetría), 3–5 dBi circulares, pero R de entrada 2–15 Ω (D = 14 mm: 2 Ω; D = 32 mm, ¼ de vuelta,
    k 0,6: 1545 MHz, 14,6 Ω, tira de 100 × 13,5 mm). Con la malla de 1 mm es orientativo. La E de NF2FF es ~1e-10: los suelos de `np.maximum` deben ser relativos.
    Al matar un barrido a mano hay que borrar `%LOCALAPPDATA%\antenas\gpu.lock` y el siguiente toma el turno (lección 65 b).
72. **Bucle (`bucle`, 10-11)**: `antenas/bucle.py`; anillo (cuadrado o redondo) con la línea de 50 Ω a un extremo y el otro a masa por una vía, y un condensador en serie
    en el lado opuesto: elemento concentrado de openEMS (`CSX.AddLumpedElement(..., LEtype=1)` con R = 1/(ωCQ); `Antena.ajuste['condensadores']`, el hueco del
    condensador no cuenta para la malla). Funciona en GPU. **Trampa**: la impedancia en el conector incluye la línea de 50 Ω hasta el anillo (λ/4 a 2,4 GHz), que
    invierte Z: la «resonancia» que medí así (2341 MHz) era un artefacto; hay que quitar la línea (`puerto['largo_linea_mm']`) antes de buscar el cruce de X.
    f = 1/(2π√(L(C + 0,016·lado))) con L de Grover, ×1,04 a 868 MHz (5 simulaciones, ±4 %). Con C < 0,1 pF no hay condensador (`C_MINIMA_MONTADO_PF`) y
    `dimensionar` afina el lado. R de entrada 3–15 Ω (Rrad ~1,5 Ω) y η 40–55 % (domina el ESR del condensador): adapta solo con una red en L (`ajuste.redes_l` con la Z
    sin la línea): 868 MHz −25,6 dB y 9 MHz, 2,4 GHz −29,9 dB y 52 MHz. Sale con `ajuste` = 1 (red en π) por defecto.
73. **Segunda Yagi comercial de 2,4 GHz (`referencias/yagi_comercial_b.py`, 10-11)**: modelo leído de dos fotos (placa trapezoidal de 100 mm, de 49 a 35 mm; dipolo
    plegado de 7 × 40 mm: anillo cerrado abajo unido al reflector por una tira, y arriba una «]» unida por el lado de los directores —dato del usuario— con la
    barra de la línea suelta en la abertura; 3 directores de 6,8 mm en las dos caras con vías en el perímetro; reflector de 9 × 48 mm). **Ninguna de las cuatro
    lecturas resuena a 2,4 GHz con haz hacia delante** (resuenan a ~2,9–3,2 GHz con 0,8 mm y la «acopla» a 1,9 GHz con 1,6 mm; ganancia ~2 dBi): faltan datos
    (grosor del FR4, dónde está la vía o el acoplo de la alimentación y qué hace la tira al reflector). Pedir al usuario cotas con calibre y una foto macro.
74. **Verificar la malla (11-11)**: `simulacion.verificar_malla` (casilla en Simulación; siempre con `multibanda` = 1, paneles y arrays) repite con el paso ×0,85 y
    ×1,15. **Una antena normal también se mueve**: el monopolo recto de 2,4 GHz da −1,8 y −4,0 % (no es monótono con el paso: depende de cómo caen las
    líneas sobre los bordes), así que el 2 % de la guía no servía; umbrales 5 % de f y 5 dB de S11 solo si alguno queda por encima de −10 dB (de −25 a −15 dB no
    importa). Con dos bandas no se compara la f (es la del mínimo global). Una simulación sin ajuste con `multibanda` = 1 usaba el rango 0,6–1,4 × y no veía la
    banda alta: `simular_cli` ya usa 0,45–3,8 ×.
75. **Panel por banda (11-11)**: `directivas.K_MALLA_FINA_PANEL` es una tabla por frecuencia (868 MHz y 2,4 GHz 0,85; 5,8 GHz 0,696). **La misma estimación escalaba la
    disposición** (separaciones y líneas en λ0), así que cambiar K movía todo: el barrido de 5,8 GHz solo valía con la disposición antigua; `f_diseno_panel` la
    mantiene con el K de 2,4 GHz y `estimar_f_panel` (K por banda) solo da el brazo. **Antes de tocar K, repetir el barrido con la K nueva ya puesta** (brazo y
    disposición cambian juntos). A 5,8 GHz el S11 es caótico con el largo del brazo (−1,4 a −10,5 dB entre 5,4 y 7,2 mm) y depende de la malla: brazo 6,6 mm da
    −10,5 dB y `verificar_malla` lo marca «sensible». Con `ajustar = False` la simulación usa la malla automática y el panel resuena un 20 % alto (2,4 GHz) o da
    −9 dB (5,8 GHz): la calibración vale para el paso al 90 % que fija `ajustar` (lección 52). A 868 MHz la placa de 383 × 283 mm sale de lo razonable (~30 min por punto).
76. **Bibanda no robusta (11-11)**: `herramientas/robustez_bibanda.py <ifa|jpole> CONSTANTE=v,…` (cambia en memoria las constantes de `bibanda.py`, simula con 3 pasos de
    malla y pide ≤ −8 dB en las dos bandas con todos). IFA de dos ramas (12 puntos) y J-pole unida (6 puntos): **ninguno cumple** (mejores −6,8 y −1,2 dB); informe en
    `docs/desarrollo/bibanda_robustez.md`. Mover las constantes no arregla la dependencia de la malla. Decisión del usuario (11-11): se deja `multibanda` en la interfaz con el aviso (`problemas.py` cita las 18 variantes).
