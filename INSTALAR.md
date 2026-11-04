# Instalar Chirptenna en Windows (paso a paso)

Esta guía es para quien no ha usado nunca Python. No hace falta saber programar ni ser
administrador del ordenador. Hay un instalador que lo descarga y lo prepara todo; tardas unos
**10 minutos** (la mayor parte es descarga).

*[English version](INSTALL.en.md)*

## Qué necesitas

- Windows 10 u 11 de 64 bits.
- Conexión a internet durante la instalación (descarga unos 250 MB).
- Unos 1,5 GB libres en el disco (2,5 GB más si instalas KiCad).
- Opcional: un **NanoVNA-H** para medir las antenas.

## 1. Descarga el programa

1. Entra en la página de versiones del proyecto: https://github.com/sqtactical/chirptenna/releases
2. En la versión más reciente (arriba), abre **Assets** y pulsa **Source code (zip)**.
3. Busca el archivo en tu carpeta **Descargas** (por ejemplo, `chirptenna-0.1.1-alpha.zip`).
4. Haz clic derecho sobre él → **Extraer todo…** → elige una carpeta que vayas a conservar,
   por ejemplo `Documentos`. Te quedará una carpeta como `chirptenna-0.1.1-alpha`: es la carpeta del programa.

> ¿Quieres lo último aunque esté sin probar? En la página principal del proyecto, botón verde
> **Code** → **Download ZIP** (`chirptenna-main`). Para usar el programa, mejor una versión publicada.

> Si más adelante borras o mueves esa carpeta, el acceso directo del escritorio dejará de
> funcionar: vuelve a ejecutar el instalador desde el sitio nuevo.

## 2. Ejecuta el instalador

1. Abre la carpeta del programa y haz **doble clic en `instalar.bat`**.
2. Windows puede mostrar un aviso azul: **«Windows protegió su PC»**. Es normal con programas
   descargados de internet que no se venden en una tienda. Pulsa **Más información** →
   **Ejecutar de todas formas**.
3. Se abre una ventana negra que va contando los pasos:

   | Paso | Qué hace | Tamaño |
   |---|---|---|
   | 1 | Instala **Python 3.14** desde python.org, solo para tu usuario. Comprueba antes su firma digital | 33 MB |
   | 2 | Descarga el simulador **openEMS 0.37** de su página oficial y comprueba que el archivo es el correcto (SHA-256) | 65 MB |
   | 3 | Crea un entorno de Python propio del programa, para no mezclarse con nada más | — |
   | 4 | Instala las librerías que usa el programa | ~150 MB |
   | 5 | Mira si tienes **KiCad** (ver el apartado 3) | — |
   | 6 | Pregunta si quieres un **acceso directo** en el escritorio (pulsa Intro para decir que sí) | — |

4. Al final debe poner **«Instalación terminada»**. Pulsa una tecla para cerrar la ventana.

Si algo falla, la ventana dice qué ha pasado. Arréglalo (normalmente es la conexión a internet)
y vuelve a ejecutar `instalar.bat`: lo que ya estaba hecho no se repite.

## 3. Instala KiCad (opcional, pero recomendado)

KiCad es un programa gratuito de diseño de placas. Chirptenna lo usa para sacar los
**archivos Gerber** que se mandan a fabricar (por ejemplo, a JLCPCB) y para revisar la placa (DRC).
Sin KiCad puedes diseñar, simular y exportar el DXF y la placa de KiCad, pero no los Gerber.

1. Entra en https://www.kicad.org/download/windows/ y descarga la última versión.
2. Ejecuta el instalador y deja **todas las opciones por defecto**.
3. No hace falta volver a ejecutar `instalar.bat`: Chirptenna encuentra KiCad solo.

## 4. Abre Chirptenna

- Doble clic en el acceso directo **Chirptenna** del escritorio, o en `iniciar.bat` dentro
  de la carpeta del programa.
- Se abre una ventana negra (**déjala abierta** mientras usas el programa) y, al momento, el
  navegador en **http://localhost:8080**. El programa funciona en tu ordenador; no se envía
  nada a internet.
- Para cerrar el programa, cierra la ventana negra.

Tus diseños se guardan en `Documentos\Chirptenna\disenos`.

## 5. NanoVNA (opcional)

Conéctalo por USB. Windows 10 y 11 lo reconocen sin instalar nada. En Chirptenna, pestaña
**Medir**, el asistente te guía para calibrarlo y medir la antena.

## Actualizar a una versión nueva

Descarga el ZIP nuevo (paso 1), sustituye la carpeta antigua y vuelve a ejecutar `instalar.bat`.
Tus diseños no se tocan.

## Problemas frecuentes

| Problema | Solución |
|---|---|
| El navegador dice «No se puede acceder a este sitio» | Espera unos segundos y recarga la página: el programa tarda un poco en arrancar. Mira si la ventana negra muestra algún error |
| La ventana negra se cierra sola al abrir el programa | Ejecuta `instalar.bat` otra vez: si falta algo, lo dirá |
| «El puerto 8080 está en uso» | Ya tienes Chirptenna abierto en otra ventana negra: usa esa, o ciérrala y vuelve a abrir el programa |
| El antivirus bloquea la descarga | Permite `python.org` y `github.com`, o descarga a mano (ver abajo) |
| Quieres saber qué tienes instalado sin cambiar nada | Abre una ventana de comandos en la carpeta del programa y ejecuta `instalar.bat -Comprobar` |

## Desinstalar

1. Borra la carpeta del programa y el acceso directo del escritorio.
2. Borra estas carpetas (pega la ruta en la barra del Explorador de archivos):
   - `%LOCALAPPDATA%\antenas` (entorno de Python, descargas y caché de simulaciones)
   - `%LOCALAPPDATA%\Programs\openEMS`
3. Si Python lo instaló el instalador y no lo usas para nada más: **Configuración → Aplicaciones**
   → «Python 3.14…» → Desinstalar.
4. Tus diseños están en `Documentos\Chirptenna`: bórralos solo si ya no los quieres.

## Instalación manual (para quien sabe usar la consola)

Lo mismo que hace el instalador, paso a paso:

1. Python **3.13 o 3.14** de 64 bits (las wheels de openEMS 0.37 solo existen para esas versiones):
   https://www.python.org/downloads/windows/
2. openEMS: descarga `openEMS_x64_v0.37.0_msvc.zip` de
   https://github.com/thliebig/openEMS-Project/releases/tag/v0.37.0 (SHA-256
   `e4f14fd6e9be7d0c1fd9c244768c21c1c2b62b8aa81f08253ebf6e06040cda5a`) y descomprímelo de forma que
   exista `%LOCALAPPDATA%\Programs\openEMS\openEMS\openEMS.exe` (o fija `CSXCAD_INSTALL_PATH` a su carpeta).
3. Crea el entorno **fuera de rutas largas** (dentro de OneDrive o de carpetas profundas Windows supera los
   260 caracteres y fallan las DLL de shapely):

   ```bash
   python -m venv %LOCALAPPDATA%\antenas\venv
   ```

4. Instala los paquetes desde la carpeta del programa:

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS CSXCAD
   ```

5. KiCad 8 o posterior (opcional). Se busca en `Program Files\KiCad\<versión>\bin\kicad-cli.exe`, en el
   PATH o en la variable `KICAD_CLI`.
6. Arranca con `iniciar.bat` o con `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui\app.py`.

Opciones del instalador: `-Comprobar` (solo informa), `-SinPreguntas`, `-SinAccesoDirecto` y
`-Python <ruta a python.exe>` (usar un Python 3.13/3.14 que ya tengas).
