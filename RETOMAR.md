# Chirptenna · estado y siguientes pasos (04-11-2026)

Nota de traspaso entre sesiones: qué hay hecho, qué falta y en qué orden. Lo estable (estructura, cómo
se ejecuta, reglas y lecciones aprendidas) está en [`CLAUDE.md`](CLAUDE.md). El diario completo de lo
hecho hasta ahora (validaciones, simulaciones, fallos y decisiones) está en
[`docs/desarrollo/historial.md`](docs/desarrollo/historial.md).

## Estado

- **Versión publicada: v0.1.1-alpha** (pre-release en GitHub, código AGPL-3.0; la v0.1.0-alpha salió con
  GPL-3.0). Repositorio **privado**. Nombre comprobado en TMview: libre.
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
   - [ ] El usuario: hacer público el repositorio (Settings → Danger Zone).
   - [ ] El usuario: subir la imagen para compartir (Settings → Social preview, `docs/logo/chirptenna_texto.png`).
   - [ ] Proteger `main` contra borrados y `push --force` (cuando sea público).
   - [ ] Opcional: pedir a GitHub que purgue los commits antiguos de antes de reescribir el historial (tenían el usuario de Windows).
   - [ ] Para los beta testers mientras sea privado: una organización gratuita con permiso Read (en un repo personal, los colaboradores tienen escritura).
2. **Cuando lleguen las placas de JLC:**
   1. Medir los cupones y meter la εr real en `antenas/materiales.py`.
   2. Medir las 7 antenas y comparar simulado frente a medido.
   3. Recalibrar las estimaciones (`herramientas/calibrar_estimaciones.py`).
   4. Poner las curvas medidas en el README.
   5. Probar el asistente del NanoVNA con el equipo (con el usuario delante).
   6. Sacar la v0.2.0-alpha.
3. **Pendientes técnicos** (detalle en el historial):
   - Simular una Yagi aligerada (desplazamiento de frecuencia por quitar FR4).
   - Panel: el haz inclinado ~9° parece un artefacto de la simulación (buscar la causa). Proponer `simetrico` = 0
     por defecto: no corrige la inclinación y empeora S11.
   - J-pole recta (adapta mal), Franklin (revisar horquillas), Minkowski it. 3 (borde a ~14 Ω: probar
     transformador λ/4), transición IPEX, quasi-Yagi de Koch (radia hacia atrás).
   - Calibrar εeff(h/λ) a 868 MHz (monopolos, Yagi, J-pole) y validar más tipos fuera de 2,4 GHz.
   - Placa C de cupones (antenas de referencia).
   - Yagi comercial: la simulación no coincide con la medida (1856 frente a 2344 MHz); aparcada.
   - Rendimiento: reparto óptimo de hilos de openEMS (`ANTENAS_HILOS`).
4. **Más adelante:** interfaz en inglés, pruebas automáticas en GitHub Actions, versión para Linux.

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
