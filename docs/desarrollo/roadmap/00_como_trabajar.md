# Cómo trabajar una tarea de la hoja de ruta

Guía para quien ejecute las tareas de [`ROADMAP.md`](../../../ROADMAP.md) (una persona o un agente). Léela entera
antes de empezar cualquier tarea. Las reglas generales del proyecto están en [`CLAUDE.md`](../../../CLAUDE.md) y
mandan sobre este archivo si hay conflicto.

## 1. Antes de empezar

1. Lee `RETOMAR.md` (estado) y el archivo de la fase (`fase1.md` … `fase4.md`, `ideas.md`).
2. Elige **la primera tarea sin marcar cuya línea «Depende de» esté cumplida**. No saltes de fase.
3. Mira la línea **«Quién»** de la tarea:
   - **Agente**: se puede hacer sin el usuario.
   - **Usuario delante**: toca el NanoVNA, hay que soldar o cambiar conexiones. **Para y pide al usuario** lo que
     indica la tarea; no envíes ningún comando al equipo hasta que confirme.
   - **Decisión del usuario**: prepara las opciones con datos y pregunta; no decidas tú.
4. Si un nombre de función, parámetro o archivo citado aquí no existe, **búscalo antes de inventarlo** (`Grep`). Las
   guías se escribieron el 11-11-2026 y el código cambia. Si de verdad no existe, dilo en el informe.

## 2. Comandos (PowerShell, desde la raíz del proyecto)

```powershell
$PY = "$env:LOCALAPPDATA\antenas\venv\Scripts\python.exe"
$GIT = "$env:LOCALAPPDATA\Programs\MinGit\cmd\git.exe"
```

| Para | Comando |
|---|---|
| Generar y exportar todos los tipos (DRC + reglas, ~2 min) | `& $PY herramientas\comprobar_tipos.py` |
| Probar la interfaz (todas las pestañas, claro y oscuro) | `& $PY herramientas\prueba_interfaz.py` |
| Textos sin traducir | `& $PY herramientas\i18n.py faltan` |
| Añadir claves nuevas a los catálogos / quitar las que sobran | `& $PY herramientas\i18n.py actualizar` / `limpiar` |
| Construir la web lite (falla si falta un módulo en `NUCLEO`) | `& $PY herramientas\construir_web.py salidas\web` |
| Regenerar miniaturas de la galería | `& $PY herramientas\generar_miniaturas.py` |
| Simular un punto o un barrido en GPU | `& $PY herramientas\barrido.py <tipo> <f_MHz> [param=v1,v2] --radiacion --etiqueta <nombre>` |
| Solo listar lo que se simularía (sin simular) | añadir `--solo-lista` |
| Arrancar la interfaz | `& $PY gui\app.py` (http://localhost:8080) |

`prueba_web.py` necesita Playwright, que no está instalado en local: la pasa la CI al subir.

## 3. Reglas que no se saltan

- **Unidades**: `tipos.dimensionar` y `simulacion.simular` reciben **Hz**; la línea de comandos, MHz.
- **GPU**: una simulación a la vez. Si matas una, borra `%LOCALAPPDATA%\antenas\gpu.lock` y comprueba que no queda
  un `openEMS.exe` huérfano. No cortes la salida de un barrido con `Select-Object -First`.
- **Simulaciones largas** (> 2 min): en segundo plano, con `herramientas\mantener_despierto.ps1` lanzado. Antes de
  lanzar, estima el coste: paso de malla × tamaño de placa; una pista o un hueco fino a 868 MHz puede tardar horas.
- **Mira siempre** en el log `FDTD timestep is` (si es ~1e-18 s o menor, hay una celda diminuta: para) y, en las
  directivas, la dirección del haz (`direccion_max`; φ 90° = hacia los directores).
- **Un resultado sensible a la malla no vale con un solo paso**: repítelo con el paso ×0,85 y ×1,15.
- **NanoVNA**: nunca `save`; restaurar el barrido al acabar; solo con el usuario delante.
- **Idioma**: todo en castellano. Todo texto nuevo de interfaz con `tr(...)` y traducido a en/fr/de.
- **No modificar** `placas/` ni las medidas del usuario en `vna/medidas`.
- **No subir a GitHub ni publicar** sin que el usuario lo pida. Commits locales sí, con el correo noreply.

## 4. Definición de «hecho»

Una tarea está hecha cuando se cumplen **todas**:

1. Se cumple su apartado **«Hecho cuando»** y lo has comprobado tú (ejecutando, no suponiendo).
2. `comprobar_tipos.py` acaba con código 0 (si tocaste generadores, exportación o reglas).
3. `prueba_interfaz.py` pasa (si tocaste `gui/app.py`, `guia.py`, `problemas.py` o textos).
4. `i18n.py faltan` no lista nada (si añadiste textos).
5. `construir_web.py` construye (si añadiste un módulo o tocaste el núcleo).
6. Documentación al día, solo lo que aplique: tabla de tipos y de problemas de los dos README, `MANUAL.md` y
   `MANUAL.en.md` (si cambian etiquetas o pestañas), `CHANGELOG.md` (sección «Sin publicar»), una lección en
   `CLAUDE.md` si se aprendió algo no obvio, y el estado en `RETOMAR.md`.
7. Casilla marcada en `ROADMAP.md` con la fecha, y commit local.

Si algo de la lista falla y no sabes arreglarlo en dos intentos, **para y cuéntalo**; no lo tapes.

## 5. Informe al usuario al acabar cada tarea

Corto y con números. Plantilla:

```
Tarea F2.3 — hecha / a medias / bloqueada
Qué cambió: archivos y una línea por cada uno.
Resultado: los números (f, S11, banda, η, tiempo de simulación).
Comprobado: qué pruebas pasaron (con el recuento, p. ej. comprobar_tipos 76/76).
Sin comprobar: lo que no pudiste probar y por qué.
Siguiente: la tarea que toca.
```

## 6. Cuándo parar y preguntar

- La tarea pide una decisión de diseño que no está escrita (qué valor por defecto, quitar o no un tipo).
- El resultado contradice una lección de `CLAUDE.md` o un estado de `problemas.py`.
- Una simulación va a tardar más de 1 hora.
- Hay que tocar el hardware, gastar dinero (pedido a JLC) o publicar.
