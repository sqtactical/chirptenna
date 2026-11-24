# Chirptenna · estado y siguientes pasos (24-11-2026)

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo se ejecuta,
reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md); el plan por fases, en [`ROADMAP.md`](ROADMAP.md); lo
publicado en cada versión, en [`CHANGELOG.md`](CHANGELOG.md). El diario antiguo, incluido el estado de esta nota hasta el
23-11, está en [`docs/desarrollo/historial.md`](docs/desarrollo/historial.md).

## Estado

- **Versiones.** Publicada: **v0.5.0-alpha** (17-11, pre-release en GitHub y web lite). Preparada y empujada:
  **0.6.0-alpha** (`b5a0674` + `66a727c`, CHANGELOG del 24-11): falta que la CI de `66a727c` salga verde, la etiqueta
  `v0.6.0-alpha`, `gh release create … --prerelease` y `gh workflow run web.yml --ref main`, con el visto bueno del
  usuario. Un commit local posterior (ROADMAP, idea del bowtie con alimentación axial) espera para no relanzar la CI.
- **Medidas reales (22-11, NanoVNA, calibración `completa_50k_2700M`)**: detalle en
  [`docs/desarrollo/placas_pedidas_2G4.md`](docs/desarrollo/placas_pedidas_2G4.md).
  - Cupones A y B: stub S80 repetible (0,03 %); S30 sale un +6 % sobre la simulación; εr del FR4 entre 4,5 y 5,0, sin
    cerrar. La causa del 6 % del S30 se estudia con `cupon/simular_placa_B.py` (placa B entera).
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
    (aparcada). Sin simular: `monopolo_uwb`, `parche_cp`, `uwb_cpw` (necesita puerto coplanar).
  - Bandas de recepción (UAT 978, ADS-B, GPS L5, GNSS L1) y grupo «Solo recepción» en la galería; el bowtie va mejor en
    todas (−19 a −28 dB).
  - **Sin simular**: `yagi_cruz` (dos placas encajadas por una ranura, dos puertos; `info['sin_simulacion']`) y
    `yagi_bibanda` (2,4 + 5,8 GHz en la misma línea).
  - Carcasa 3D (STL, simulación con carcasa, efecto de los tornillos), medida de plásticos con el cupón C y conexión
    con Chirptenna VNA (`.s1p` simulado): en la 0.6.0, sin probar con una carcasa impresa ni un plástico medido.
- **Integración (fase 3, 12-11)**: hecho casi todo en parte (antena integrada, importar `.kicad_pcb`, huella con
  exclusión, pad de RF, 4 capas, entorno, tolerancias, informe PDF, CSV del diagrama). Falta probarlo con una placa
  real del usuario y en KiCad con interfaz; F3.8 (antena chip) bloqueada sin hoja de datos.
- **Pruebas**: 323 en `pruebas/` (pytest, sin openEMS); i18n en/fr/de 1686/1686; `comprobar_tipos.py` y
  `prueba_interfaz.py` en la CI; `prueba_web.py` solo en la CI (en local falta Playwright).
- **GPU**: parada. Sin cola pendiente (las colas antiguas de `salidas/_cola` y `%LOCALAPPDATA%\antenas\cola` están
  abandonadas; `0008_array_parches` sigue colgada en `en_curso` desde el 02-11 y se puede borrar).

## Siguientes pasos

1. **Release 0.6.0-alpha** cuando la CI esté verde y el usuario lo diga (ver «Cómo ejecutar»). Si `prueba_web.py`
   falla con `yagi_cruz` o `yagi_bibanda`, arreglarlo antes.
2. **Fase 1 (medir)**: medir Y55, Y57, Y58 y Y59; repetir la Yagi con ferrita; comparar con
   `herramientas/comparar_medida.py`; cerrar la εr del FR4 (stubs + Sierpinski apuntan a 4,2–4,6); después recalibrar
   `calibracion_estimaciones.json` y crear el estado «Medida» (ROADMAP fase 1).
3. **Simular lo que está sin simular**: `yagi_bibanda` (`barrido.py --modo bayes`), `yagi_cruz` (dos puertos y el
   desfase de ~87°), `monopolo_uwb` en banda ancha (hace falta un modo de banda ancha en `barrido.py`), `parche_cp`;
   calibrar las `K_*` de `planares.py`. Comprobar la bobina de la espiral con una L concentrada en la FDTD.
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
