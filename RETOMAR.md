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
4. **Tipos nuevos por implementar: bowtie de Sierpinski** (decidido el 05-11). Objetivo: tolerancia a desajustes
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
7. **Más adelante:** interfaz en inglés, versión para Linux, `dependabot.yml` (ya hay CI y versiones fijadas),
   mejoras de la web lite (abajo).
8. **Web lite** (05-11, hecha; `web/`, ver CLAUDE.md): 32/32 casos en Pyodide (~0,6 s por antena), zip del navegador
   con DRC de KiCad limpio, móvil y tema oscuro probados. Pendiente:
   - [x] Pages activado (build_type workflow) y publicada el 05-11: https://sqtactical.github.io/chirptenna/
     (`web.yml` vuelve a publicar con cada release o a mano: `gh workflow run web.yml`).
   - [x] `prueba_web.py` en la CI: 32/32 en Chromium con DRC de KiCad limpio (media 0,74 s, máx. 2,5 s por antena).
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
