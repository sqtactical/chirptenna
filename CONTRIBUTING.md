# Cómo colaborar con Chirptenna

*English summary at the end.*

Gracias por querer ayudar. Chirptenna está en **alpha**: funciona de principio a fin, pero todo está
validado solo en simulación. Por eso hay dos formas de colaborar, y la primera no requiere programar.

Al participar aceptas el [código de conducta](CODE_OF_CONDUCT.md). Los fallos de seguridad se avisan en
privado ([SECURITY.md](SECURITY.md)) y las dudas van a [Discussions](https://github.com/sqtactical/chirptenna/discussions).

## 1. Medidas reales (lo que más falta)

Si fabricas una antena generada con Chirptenna y la mides con un VNA, abre un issue con la plantilla
**«Medida real»**. Con el `.s1p`, el `diseno.json` y una foto se puede comparar con la simulación y
corregir el programa (la εr del FR4, las estimaciones de cada tipo, las marcas de corte…).
Una sola medida bien documentada vale más que muchas líneas de código ahora mismo.

## 2. Código (pull requests)

### Antes de empezar

- Para algo más grande que un arreglo pequeño, **abre antes un issue** («Propuesta» o «Fallo») y
  coméntalo: así no trabajas en algo que luego no encaja.
- Prepara el entorno con `instalar.bat` (ver [INSTALAR.md](INSTALAR.md)). Usa el Python del entorno
  del programa: `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe`.
- La estructura del código y las **lecciones aprendidas** (errores ya cometidos con openEMS, KiCad,
  la malla…) están en [CLAUDE.md](CLAUDE.md). Léelo: ahorra horas. El proyecto se ha desarrollado con
  ayuda de IA (Claude Code); ese archivo es también la guía que sigue el asistente.

### Convenciones

- **Todo en castellano**: nombres de variables y funciones, comentarios, docstrings, mensajes de la
  interfaz y claves de JSON. (Los issues y las PR pueden ser en inglés.)
- **Unidades**: geometría en mm; frecuencias internas en Hz; en la línea de comandos MHz; en los
  resúmenes, la unidad va en el nombre de la clave (`f_centro_MHz`, `longitud_mm`).
- Los scripts de prueba o medida generan un `.json` resumen y un `.png` (matplotlib, backend `Agg`).
- Importa `antenas.simulacion` (o `fase0/comun`) **antes** que `CSXCAD`/`openEMS`: fija
  `CSXCAD_INSTALL_PATH`.
- `antena.info` solo con tipos de Python (`float`, no `np.float64`): la interfaz los muestra tal cual.
- En la interfaz, no uses las clases de color de Quasar para el texto (`text-grey-8`…): no se pueden
  adaptar al modo oscuro. Usa las propias (`texto-sec`, `texto-aviso`…) y pasa toda figura de Plotly por `T()`.

### Qué no debe entrar en el repositorio

- **Ningún Gerber, taladro, `.zip` de fabricación, `.kicad_pcb`, `.kicad_mod` ni DXF generado**: el
  repositorio es el generador, no sus salidas (el `.gitignore` ya los excluye).
- Placas o datos de terceros, y nada con rutas o datos personales.
- Resultados de simulación pesados (van en `salidas/`, que está excluida).

### Si tocas un tipo de antena

1. Pasa la comprobación de todos los tipos, que los genera y exporta **a 868 MHz y a 2,4 GHz** con el DRC de
   KiCad y las reglas de fabricación (unos 2 min; debe salir todo «OK»):
   `python herramientas/comprobar_tipos.py` (o `--solo tipo1,tipo2`). Si tocas la interfaz:
   `python herramientas/prueba_interfaz.py`. La CI de GitHub pasa las dos en cada PR (Windows, ~20 min).
2. Si cambia la geometría que se simula, **simúlalo** (`python -m antenas.validar_lote …`) e indica en la PR
   la resonancia, la banda a −10 dB, la ganancia y la eficiencia antes y después.
3. Un tipo nuevo necesita: su entrada en `tipos.CATALOGO`, `info['pista_minima_mm']` y
   `info['hueco_minimo_mm']` (para la malla), sus avisos en `antenas/problemas.py` si se sabe que falla
   algo, y una fila en la tabla de tipos de los **dos README**.
4. Si una simulación o una medida cambia el estado de un tipo, actualiza `antenas/problemas.py` y la tabla
   «Problemas conocidos» de los dos README.

### NanoVNA (obligatorio si tocas `vna/`)

- **Nunca enviar `save`** al equipo: no se pisan sus calibraciones guardadas. `recall` solo lee.
- Después de medir, **restaurar siempre** el barrido y el estado de calibración (`try/finally`).
- La tarjeta SD solo se lee.

### La pull request

- Una PR por cambio, con una descripción de **qué** cambia y **por qué**.
- Rellena la lista de la plantilla: qué probaste y cómo.
- No hay pruebas automáticas todavía: lo que pruebes a mano, cuéntalo.

## Licencias

- El **código** es AGPL-3.0 ([LICENSE](LICENSE)); los **diseños de antena publicados** en el proyecto, CC BY-NC 4.0
  ([LICENSE-DISENOS.md](LICENSE-DISENOS.md)).
- Al enviar una PR aceptas que tu aportación se publique con esas mismas licencias. Al compartir una medida con
  la plantilla, aceptas que los datos se usen y se publiquen en el proyecto.

---

## English summary

Chirptenna is in **alpha**: validated in simulation only. The most valuable contribution right now is a
**real measurement**: build an antenna, measure it with a VNA and open a “Real measurement” issue with the
`.s1p`, the `diseno.json` and a photo.

For code: open an issue first for anything non-trivial; set up with `instalar.bat`; read
[CLAUDE.md](CLAUDE.md) (structure and lessons learned). Code, comments and GUI are in **Spanish**
(issues and PRs can be in English). Never commit Gerbers or other generated manufacturing files. If you
change an antenna type, export it at 868 MHz and 2.4 GHz with a clean KiCad DRC, simulate it if the
geometry changes, and update `antenas/problemas.py` and both READMEs. Never send `save` to the NanoVNA.
Contributions are licensed under AGPL-3.0 (code) and CC BY-NC 4.0 (published designs).
By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md); report security issues privately
([SECURITY.md](SECURITY.md)) and ask questions in [Discussions](https://github.com/sqtactical/chirptenna/discussions).
