# Chirptenna · estado y siguientes pasos (24-11-2026)

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo se ejecuta,
reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md); el plan por fases, en [`ROADMAP.md`](ROADMAP.md); lo
publicado en cada versión, en [`CHANGELOG.md`](CHANGELOG.md). El diario antiguo, incluido el estado de esta nota hasta el
23-11, está en [`docs/desarrollo/historial.md`](docs/desarrollo/historial.md).

## Estado

- **Versiones.** Publicada: **v0.6.0-alpha** (25-11, pre-release en GitHub sobre `c0d7bf4`, CI verde; web lite
  publicada a mano con `web.yml`). Antes: v0.5.0-alpha (17-11).
- **Chirptenna Wire** (25-11): spin-off para planos de antenas de varilla con NEC2, en su propio repositorio local
  `Documentos\Chirptenna-Wire` y en GitHub `sqtactical/Chirptenna-Wire`, **público desde el 25-11 con la release
  v0.1.0-alpha** (dipolo y J-pole simulados, sin medir; fase 1 y hoja de ruta W1–W5 en su `ROADMAP.md`). No se desarrolla
  aquí.
- **Medidas reales (22-11, NanoVNA, calibración `completa_50k_2700M`)**: detalle en
  [`docs/desarrollo/placas_pedidas_2G4.md`](docs/desarrollo/placas_pedidas_2G4.md).
  - Cupones A y B: stub S80 repetible (0,03 %); S30 sale un +6 % sobre la simulación; εr del FR4 entre 4,5 y 5,0, sin
    cerrar. **Placa B entera simulada el 24-11** (tras corregir una ranura de masa en el modelo de `simular_placa_B.py`, que
    sigue sin commitear en `cupon/`): los vecinos suben el S30 solo un +2,1 % y el S80 un +0,2 %; la razón S30/S80 no casa
    en ningún modelo, así que la sospecha pasa al cuerpo del SMA. Detalle en
    `docs/desarrollo/medidas/resultados_stubs_cupon_B.md`.
  - Yagi de 2 directores (Y54): 2534 MHz, +3,6 % sobre lo simulado, −12,1 dB, banda de 88 MHz frente a 166 simulados.
    La simulación de la Yagi depende de la malla (~3 %); falta medirla con ferrita en el cable.
  - Monopolo de Sierpinski (Y56): 2502 MHz, +1,0 %, −34 dB, banda ≥ 425 MHz. Es el tipo mejor validado.
  - **Sin medir**: parche (Y55), Koch ajustable (Y57), J-pole de Koch (Y58) y dipolo con coaxial (Y59). Ningún tipo
    nuevo desde el 23-11 se ha medido.
- **Cupón C en standby (23-11, por decisión del usuario)**: no se pide ni se toca. `cupon/generar_cupon.py C` ya genera
  stubs S25/S43/S59/S86 y los lanzadores LANZ_A/LANZ_C (DRC limpio). Cambios en `cupon/` **sin commitear a propósito**.
- **Catálogo**: 45 tipos (miniaturas en `antenas/miniaturas/`), estados en `antenas/problemas.py` y
  [`docs/ESTADO_REAL.md`](docs/ESTADO_REAL.md) (generado). Novedades de la 0.6.0:
  - Planares (`antenas/planares.py`, 23–24-11): dipolo plegado (−16,4 dB) y log-periódica (−22,7 dB) validados en
    simulación; ranura optimizada −28,6 dB (η 73 %); **espiral** grande (radio 28 mm a 2,44 GHz) con bobina serie de
    3,5 nH aplicada por circuito: Z 42,9 − j2,1 Ω, banda −10 dB 1677–3036 MHz, razón axial 1,5 dB (la bobina no está
    comprobada con FDTD ni medida). No funcionan: Moxon (R 15–25 Ω, ni con `z_transformador`), torniquete (razón axial
    12 dB: necesita retardo real), `array_serie` (−3,5 a −7,2 dB). `antena_siw` adapta a 2,4 GHz pero η 12 %
    (aparcada). `monopolo_uwb`: −18 dB a 2,4 GHz y, en banda ancha (24-11, `salidas/_barridos/DB_monopolo_uwb`),
    ≤ −8,6 dB de 2,4 a 8 GHz sin llegar a −10 dB en 5–8 GHz. `parche_cp` no adapta (2,4 GHz −1,2 dB; GNSS L1 centrado
    −5,4 dB, η 26 %, razón axial 10 dB; `NUEVO_parche_cp_GNSSL1`). Sin simular: `uwb_cpw` (necesita puerto coplanar).
  - Bandas de recepción (UAT 978, ADS-B, GPS L5, GNSS L1) y grupo «Solo recepción» en la galería; el bowtie va mejor en
    todas (−19 a −28 dB).
  - `yagi_bibanda` simulada el 24-11 (`salidas/_barridos/DB_yagi_bibanda`, 9 variantes): 5,8 GHz adapta (−10,5 a
    −20,5 dB) pero 2,4 GHz no (−1,7 dB): el tramo de línea hasta el dipolo alto hace de stub sobre el bajo; hace falta
    otra topología (dipolo alto antes que el bajo, o una trampa). **Sin simular**: `yagi_cruz` (dos placas encajadas por
    una ranura, dos puertos; `info['sin_simulacion']`: el simulador solo admite un puerto).
  - Carcasa 3D (STL, simulación con carcasa, efecto de los tornillos), medida de plásticos con el cupón C y conexión
    con Chirptenna VNA (`.s1p` simulado): en la 0.6.0, sin probar con una carcasa impresa ni un plástico medido.
- **Integración (fase 3, 12-11)**: hecho casi todo en parte (antena integrada, importar `.kicad_pcb`, huella con
  exclusión, pad de RF, 4 capas, entorno, tolerancias, informe PDF, CSV del diagrama). Falta probarlo con una placa
  real del usuario y en KiCad con interfaz; F3.8 (antena chip) bloqueada sin hoja de datos.
- **Pruebas**: 323 en `pruebas/` (pytest, sin openEMS); i18n en/fr/de 1686/1686; `comprobar_tipos.py` y
  `prueba_interfaz.py` en la CI; `prueba_web.py` solo en la CI (en local falta Playwright).
- **GPU**: parada desde el 24-11 a las 22:53. Sin cola pendiente (las colas antiguas de `salidas/_cola` y
  `%LOCALAPPDATA%\antenas\cola` están abandonadas; la entrada colgada `0008_array_parches` se borró el 24-11).
  `mantener_despierto.ps1` no detecta `doble_banda.py` (se cierra a los 10 min): con esa herramienta, pedir otra forma
  de mantener el equipo despierto.

## Siguientes pasos

1. **Release 0.6.0-alpha**: hecha el 25-11.
2. **Fase 1 (medir)**: medir Y55, Y57, Y58 y Y59; repetir la Yagi con ferrita; comparar con
   `herramientas/comparar_medida.py`; cerrar la εr del FR4 (stubs + Sierpinski apuntan a 4,2–4,6); después recalibrar
   `calibracion_estimaciones.json` y crear el estado «Medida» (ROADMAP fase 1).
3. **Lo que queda de simulación**: rediseñar la topología de `yagi_bibanda` (lo simulado el 24-11 no da la banda baja);
   `yagi_cruz` y `uwb_cpw` necesitan cambios en el simulador (dos puertos, puerto coplanar); afinar el hueco del
   `monopolo_uwb` para bajar de −10 dB en 5–8 GHz; calibrar las `K_*` de `planares.py`. La bobina de la espiral en FDTD
   choca con la lección 77 (L pequeñas inestables): seguir por circuito hasta medirla.
4. **Medidas en los textos (hecho el 24-11)**: interfaz, web, LÉEME del zip, `MANUAL`, `CONTRIBUTING` y README ya dicen
   «casi todo validado solo en simulación» y citan las medidas. Al medir más placas, actualizar esas frases, la tabla
   «Problemas conocidos» de los README y `docs/desarrollo/placas_pedidas_2G4.md`.
5. **Capturas del README**: rehechas el 24-11 (`capturas_readme.py --lanzador herramientas/lanzar_app_claude.py`).
6. Otras ideas y tareas sin fecha: ROADMAP («Ideas a más largo plazo» y fases 2–5).

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
