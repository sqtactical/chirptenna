# Cambios · Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones con
[versionado semántico](https://semver.org/lang/es/). *English summary under each version.*

## [Sin publicar]

### Añadido

- **Versión web lite** (https://sqtactical.github.io/chirptenna/): diseñar, ver y descargar la antena para KiCad
  (`.kicad_pcb`, huella, DXF, `diseno.json` y un LÉEME con los pasos hasta los Gerber) sin instalar nada. Python
  corre en el navegador (Pyodide); no se envía nada a ningún servidor. Enlaces para compartir un diseño, abrir un
  `diseno.json` de la aplicación y tema claro/oscuro. No simula ni pasa el DRC de KiCad.
- **Interfaz más sencilla** (escritorio y web): al entrar, una galería de tipos con miniatura, descripción y estado
  («Validada», «Pendiente de validación», «No funciona»), agrupados por uso. Al elegir uno solo se ven los parámetros
  básicos; el resto está en «Ajustes avanzados». Cada parámetro tiene un botón «?» que explica qué hace. El selector de
  tipo también muestra la descripción y el estado de cada antena.
- Prueba automática de la web en la CI: los 16 tipos a 868 MHz y 2,4 GHz generados dentro del navegador y con el DRC
  de KiCad.

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
