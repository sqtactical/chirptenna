# Instalar Chirptenna en Windows (paso a paso)

*[English version](INSTALL.en.md)* · Cuando lo tengas instalado: **[manual de uso](MANUAL.md)**.

Esta guía es para quien no ha usado nunca Python. No hace falta saber programar ni ser administrador
del ordenador. Hay un instalador que lo descarga y lo prepara todo. Tardas unos **10 minutos**, casi todo
en descargas.

**Índice**

1. [Antes de empezar](#0-antes-de-empezar)
2. [Descarga el programa](#1-descarga-el-programa)
3. [Ejecuta el instalador](#2-ejecuta-el-instalador)
4. [Instala KiCad](#3-instala-kicad-opcional-pero-recomendado)
5. [Abre Chirptenna](#4-abre-chirptenna)
6. [Comprueba que todo funciona](#5-comprueba-que-todo-funciona)
7. [NanoVNA](#6-nanovna-opcional)
8. [Actualizar](#actualizar-a-una-versión-nueva) · [Problemas frecuentes](#problemas-frecuentes) ·
   [Pedir ayuda](#pedir-ayuda) · [Desinstalar](#desinstalar) · [Instalación manual](#instalación-manual-para-quien-sabe-usar-la-consola)

---

## 0. Antes de empezar

### Qué necesitas

| | Mínimo | Recomendado |
|---|---|---|
| Sistema | Windows 10 de 64 bits | Windows 11 |
| Memoria | 8 GB | 16 GB (para simular arrays y paneles) |
| Procesador | 4 núcleos | 6 núcleos o más (las simulaciones van mucho más rápido) |
| Disco | 1,5 GB libres | 4 GB (con KiCad y la caché de simulaciones) |
| Internet | Solo durante la instalación (unos 250 MB, más 1,5 GB si instalas KiCad) | |

Opcional: un **NanoVNA-H** u otro analizador de antenas para medir lo que fabriques.

**¿Mi Windows es de 64 bits?** Pulsa `Windows + Pausa` o ve a **Configuración → Sistema → Información**.
En «Tipo de sistema» debe poner **«Sistema operativo de 64 bits»**. Los Windows de 32 bits y los ordenadores
con procesador ARM (algunos portátiles Surface y Snapdragon) no están soportados.

### Qué se instala y dónde

El instalador no toca nada fuera de tu usuario y no necesita permisos de administrador:

| Qué | Dónde | Para qué |
|---|---|---|
| La carpeta del programa | Donde la descomprimas (paso 1) | El programa en sí |
| Python 3.14 | `%LOCALAPPDATA%\Programs\Python\Python314` | El lenguaje en el que está hecho. Si ya tienes Python 3.13 o 3.14, usa ese |
| openEMS 0.37 | `%LOCALAPPDATA%\Programs\openEMS` | El simulador electromagnético |
| Motor de GPU (opcional, solo con una tarjeta NVIDIA compatible) | `%LOCALAPPDATA%\Programs\gpu-build` | El mismo simulador con aceleración por GPU: ~10 veces más rápido |
| Entorno del programa | `%LOCALAPPDATA%\antenas\venv` | Las librerías de Chirptenna, aparte de cualquier otro Python que tengas |
| Tus diseños | `Documentos\Chirptenna\disenos` | Se crea la primera vez que guardas un diseño |

> `%LOCALAPPDATA%` es una carpeta oculta de tu usuario (normalmente `C:\Users\<tú>\AppData\Local`). Para
> abrirla, pega `%LOCALAPPDATA%` en la barra de direcciones del Explorador de archivos.

---

## 1. Descarga el programa

1. Entra en la página de versiones: **https://github.com/sqtactical/chirptenna/releases**
2. La primera versión de la lista es la más reciente (lleva la etiqueta *Pre-release* mientras el proyecto
   esté en alpha). Baja hasta su apartado **Assets** y pulsa **Source code (zip)**. No hace falta tener
   cuenta en GitHub.
3. El archivo queda en tu carpeta **Descargas**, con un nombre como `chirptenna-0.1.2-alpha.zip`.
4. **Descomprímelo** (no lo abras con doble clic; así solo se ve por dentro y el instalador no funciona):
   clic derecho sobre el zip → **Extraer todo…** → elige una carpeta que vayas a conservar, por ejemplo
   `Documentos` → **Extraer**.
5. Te queda una carpeta como `Documentos\chirptenna-0.1.2-alpha`. Esa es **la carpeta del programa**. Dentro
   tiene que haber, entre otras cosas, `instalar.bat`, `iniciar.bat` y las carpetas `antenas` y `gui`.

> **¿Dónde la pongo?** Vale cualquier carpeta, también dentro de OneDrive. Evita solo las rutas muy
> largas o con caracteres raros. Si más adelante la mueves o la borras, el acceso directo del escritorio
> dejará de funcionar: vuelve a ejecutar `instalar.bat` desde el sitio nuevo.

> ¿Quieres lo último aunque esté sin probar? En la página principal del proyecto, botón verde **Code** →
> **Download ZIP** (`chirptenna-main`). Para usar el programa con normalidad, mejor una versión publicada.

---

## 2. Ejecuta el instalador

1. Abre la carpeta del programa y haz **doble clic en `instalar.bat`**. Si Windows oculta las extensiones,
   aparecerá como `instalar` con un icono de engranaje.
2. Puede salir un aviso azul: **«Windows protegió su PC»**. Pasa con todos los programas descargados de
   internet que no vienen de una tienda. Pulsa **Más información** → **Ejecutar de todas formas**.
3. Se abre una ventana negra que va contando los pasos. Cada línea empieza por un indicador:
   - `OK` (verde): ese paso está bien.
   - `!` (amarillo): aviso. No impide seguir (por ejemplo, que falta KiCad).
   - `X` (rojo): error. La instalación se para y explica por qué.

   | Paso | Qué hace | Descarga | Tiempo aprox. |
   |---|---|---|---|
   | 1 | Busca Python 3.13 o 3.14. Si no lo tienes, descarga **Python 3.14** de python.org, **comprueba su firma digital** y lo instala solo para tu usuario, sin tocar el PATH | 33 MB | 1–2 min |
   | 2 | Descarga el simulador **openEMS 0.37** de su página oficial, comprueba que el archivo es exactamente el esperado (**SHA-256**) y lo descomprime | 65 MB | 1 min |
   | 3 | Crea un entorno de Python propio del programa, para no mezclarse con nada más | — | segundos |
   | 4 | Instala las librerías con las **versiones exactas probadas** (`requirements-lock.txt`) y los módulos de openEMS | ~150 MB | 2–5 min |
   | 5 | Mira si tienes **KiCad** (apartado 3). Si no, avisa y pregunta si abrir su web de descarga | — | — |
   | 6 | Si tienes una **GPU NVIDIA** compatible (RTX 20, 30, 40 o 50; la detecta con `nvidia-smi`), pregunta si instalas el **motor de GPU** (comprueba su SHA-256). Sin tarjeta NVIDIA lo salta y se simula en la CPU. Con `-SinGPU` no lo instala | 12 MB | segundos |
   | 7 | Pregunta si quieres un **acceso directo** en el escritorio. Pulsa **Intro** para decir que sí | — | — |

4. Al final hace una comprobación y debe poner **«OK el programa carga bien»** y **«Instalación
   terminada»**. Pulsa una tecla para cerrar la ventana.

Si algo falla, la ventana dice qué ha pasado. Corrígelo (casi siempre es la conexión a internet o el
antivirus; mira los [problemas frecuentes](#problemas-frecuentes)) y vuelve a ejecutar `instalar.bat`: lo
que ya estaba hecho no se repite ni se vuelve a descargar.

> **¿Es seguro?** El instalador solo descarga de python.org, de la página oficial de openEMS en GitHub y (el motor de GPU, opcional) de la release del proyecto, y
> comprueba lo que descarga antes de usarlo. Si la firma o el SHA-256 no coinciden, se detiene. Puedes leer
> lo que hace en `instalar\instalar.ps1`: es texto y está comentado.

---

## 3. Instala KiCad (opcional, pero recomendado)

KiCad es un programa gratuito de diseño de placas. Chirptenna lo usa para dos cosas:
- sacar los **archivos Gerber** que se mandan a fabricar (por ejemplo, a JLCPCB);
- revisar la placa con su **DRC** (comprobación de reglas de diseño).

Sin KiCad puedes diseñar, simular y exportar el DXF y la placa de KiCad, pero no los Gerber.

1. Entra en **https://www.kicad.org/download/windows/** y descarga la última versión estable (8 o
   posterior; se prueba con la 10). Son unos 1,5 GB.
2. Ejecuta el instalador de KiCad y deja **todas las opciones por defecto**. Este sí pide permisos de
   administrador.
3. No hace falta volver a ejecutar `instalar.bat`: Chirptenna encuentra KiCad solo. Si lo has instalado
   en otra carpeta, crea una variable de entorno `KICAD_CLI` con la ruta completa de `kicad-cli.exe`.

---

## 4. Abre Chirptenna

1. Doble clic en el acceso directo **Chirptenna** del escritorio, o en `iniciar.bat` dentro de la carpeta
   del programa.
2. Se abre una **ventana negra**. Es el programa en sí: **déjala abierta** mientras lo usas (puedes
   minimizarla).
3. Al momento se abre tu navegador en **http://localhost:8080** con la interfaz. Chirptenna funciona en tu
   ordenador: el navegador solo sirve de pantalla y **no se envía nada a internet**. La interfaz solo es
   accesible desde tu propio ordenador.
4. Para cerrar el programa, **cierra la ventana negra**. Cerrar la pestaña del navegador no lo apaga.

> Si cierras la pestaña sin querer, vuelve a abrir **http://localhost:8080** en el navegador (guárdalo en
> favoritos). No hace falta volver a lanzar el programa mientras la ventana negra siga abierta.

---

## 5. Comprueba que todo funciona

Una prueba de 2 minutos para saber que la instalación está completa:

1. En la barra superior, **Tipo de antena** → *Monopolo recto (referencia)*, y **Banda de uso** → *2,4 GHz*.
2. Pestaña **Diseño** → **Ajustar tamaño a la frecuencia**. Debe aparecer el dibujo de la antena.
3. Escribe `prueba` en **Nombre del diseño** (arriba a la izquierda). Pestaña **Fabricar** → **Exportar
   KiCad + Gerber + DXF**. El diseño se guarda solo y, al acabar, aparece la carpeta de salida con los
   archivos para descargar (Gerber para JLC, placa KiCad, huella, DXF) y el resultado del DRC sin errores.
   Sin KiCad sale «Error al exportar: No se encuentra kicad-cli»: es lo esperado, y la placa KiCad y el DXF
   sí quedan en la carpeta `fabricacion` del diseño.
4. Opcional, para probar el simulador: pestaña **Simulación** → precisión **rápida** → desmarca «Ajustar a
   la frecuencia simulando» → **Simular**. Con un monopolo de 2,4 GHz tarda unos minutos y acaba mostrando
   las gráficas de S11 y del diagrama de radiación.

Si todo eso funciona, ya está. Sigue con el **[manual de uso](MANUAL.md)**.

---

## 6. NanoVNA (opcional)

1. Conéctalo por USB. Windows 10 y 11 lo reconocen solos como un puerto serie (COM); no hace falta
   instalar drivers.
2. En Chirptenna, pestaña **Medir** → **Buscar el NanoVNA**.
3. Si no lo encuentra:
   - prueba otro cable USB (muchos cables solo cargan y no llevan datos);
   - cierra cualquier otro programa que lo esté usando (NanoVNA-Saver, NanoVNA-App…). Solo un programa
     a la vez puede hablar con él;
   - mira en el **Administrador de dispositivos** → *Puertos (COM y LPT)* que aparece un
     «Dispositivo serie USB» al enchufarlo.

Está probado con el **NanoVNA-H con firmware DiSlord**. Chirptenna nunca guarda nada en la memoria del
equipo: tus calibraciones de los slots C0–C4 no se tocan. Si tienes otro analizador, puedes medir con su
programa y subir el archivo `.s1p` en la pestaña **Medir**.

---

## Actualizar a una versión nueva

1. Descarga y descomprime el zip nuevo (paso 1). Puedes dejarlo junto al antiguo.
2. Ejecuta `instalar.bat` desde la carpeta **nueva**: reutiliza Python y openEMS, actualiza las librerías
   si hace falta y apunta el acceso directo a la carpeta nueva.
3. Cuando compruebes que funciona, borra la carpeta antigua.

**Tus diseños no se tocan**: están en `Documentos\Chirptenna\disenos`, no en la carpeta del programa.
Las novedades de cada versión están en el [CHANGELOG](CHANGELOG.md).

---

## Problemas frecuentes

### Durante la instalación

| Problema | Solución |
|---|---|
| Doble clic en `instalar.bat` y la ventana se cierra al instante | Seguramente estás dentro del zip sin descomprimir. Haz **Extraer todo…** (paso 1) |
| «Windows protegió su PC» y no aparece «Ejecutar de todas formas» | Pulsa primero **Más información** |
| `X` en la descarga, o «No se puede establecer una conexión» | Revisa la conexión. En redes de empresa o de universidad con proxy, prueba desde otra red o haz la [instalación manual](#instalación-manual-para-quien-sabe-usar-la-consola) |
| El antivirus bloquea la descarga o borra un archivo | Permite `python.org` y `github.com`, o añade una excepción para `%LOCALAPPDATA%\antenas`. Vuelve a ejecutar el instalador |
| «La firma del instalador de Python no es válida» o «El SHA-256 de openEMS no coincide» | La descarga se ha corrompido o la ha cambiado algo (proxy, antivirus). Borra `%LOCALAPPDATA%\antenas\descargas` y vuelve a ejecutar. **No lo fuerces** |
| «Falló la instalación de los paquetes» | Casi siempre es la conexión. Vuelve a ejecutar `instalar.bat`. Si persiste, copia los mensajes de la ventana y [pide ayuda](#pedir-ayuda) |
| Ya tenías otro Python (3.12, 3.11…) | No pasa nada: el instalador pone Python 3.14 aparte y no toca el tuyo |
| Tenías un entorno de una versión antigua de Chirptenna con otro Python | El instalador lo aparta a `venv.antiguo_<fecha>` y crea uno nuevo. Puedes borrar el antiguo |

### Al abrir el programa

| Problema | Solución |
|---|---|
| El navegador dice «No se puede acceder a este sitio» | Espera unos segundos y recarga: la primera vez tarda en arrancar. Mira si la ventana negra muestra algún error |
| La ventana negra dice «Chirptenna no está instalado» | Ejecuta `instalar.bat` |
| La ventana negra se cierra sola | Ejecuta `instalar.bat` otra vez: si falta algo, lo dirá |
| «El puerto 8080 está en uso» o «address already in use» | Ya tienes Chirptenna abierto en otra ventana negra: usa esa, o ciérrala y vuelve a abrir el programa |
| El acceso directo no hace nada | Has movido o borrado la carpeta del programa. Ejecuta `instalar.bat` desde donde esté ahora |
| La interfaz se ve rara o a medias | Recarga con `Ctrl + F5`. Usa un navegador actual (Edge, Chrome o Firefox) |

### Al usarlo

| Problema | Solución |
|---|---|
| Al exportar: «Error al exportar: No se encuentra kicad-cli» | Instala KiCad (apartado 3). Si ya lo está en otra carpeta, define `KICAD_CLI` |
| La simulación no avanza o va muy lenta | Es normal que tarde: de minutos a horas según la antena y la banda (más en 868 MHz). El registro de la pestaña Simulación muestra el progreso. Usa la precisión **rápida** para tantear |
| Se ha llenado el disco | La caché de simulaciones está en `%TEMP%\antenas_sim`. Se puede borrar entera sin perder nada que no se pueda repetir |

**Para saber qué tienes instalado sin cambiar nada:** abre una ventana de comandos en la carpeta del
programa (en el Explorador, escribe `cmd` en la barra de direcciones y pulsa Intro) y ejecuta:

```bash
instalar.bat -Comprobar
```

---

## Pedir ayuda

Si nada de lo anterior lo resuelve, abre una incidencia en
**https://github.com/sqtactical/chirptenna/issues/new/choose** → «Fallo». Incluye:

1. Tu versión de Windows y la de Chirptenna (aparece abajo del todo en la interfaz, o en el nombre del zip).
2. La salida de `instalar.bat -Comprobar` (selecciónala en la ventana y cópiala).
3. El mensaje de error completo de la ventana negra.

Antes de pegarlo, **quita tu nombre de usuario** de las rutas si no quieres que se vea
(`C:\Users\<tú>\...`). Para dudas que no son fallos, usa
[Discussions](https://github.com/sqtactical/chirptenna/discussions).

---

## Desinstalar

1. Borra la carpeta del programa y el acceso directo del escritorio.
2. Borra estas carpetas (pega cada ruta en la barra del Explorador de archivos):
   - `%LOCALAPPDATA%\antenas` (entorno de Python y descargas);
   - `%LOCALAPPDATA%\Programs\openEMS`;
   - `%LOCALAPPDATA%\Programs\gpu-build` (motor de GPU, si lo instalaste);
   - `%TEMP%\antenas_sim` (caché de simulaciones).
3. Si Python lo instaló el instalador y no lo usas para nada más: **Configuración → Aplicaciones** →
   «Python 3.14…» → Desinstalar.
4. Tus diseños están en `Documentos\Chirptenna`: bórralos solo si ya no los quieres.

---

## Instalación manual (para quien sabe usar la consola)

Lo mismo que hace el instalador, paso a paso:

1. Python **3.13 o 3.14** de 64 bits (las wheels de openEMS 0.37 solo existen para esas versiones):
   https://www.python.org/downloads/windows/
2. openEMS: descarga `openEMS_x64_v0.37.0_msvc.zip` de
   https://github.com/thliebig/openEMS-Project/releases/tag/v0.37.0 (SHA-256
   `e4f14fd6e9be7d0c1fd9c244768c21c1c2b62b8aa81f08253ebf6e06040cda5a`) y descomprímelo de forma que
   exista `%LOCALAPPDATA%\Programs\openEMS\openEMS\openEMS.exe` (o fija `CSXCAD_INSTALL_PATH` a su carpeta).
3. Crea el entorno **fuera de rutas largas**. Dentro de OneDrive o de carpetas profundas, Windows supera los
   260 caracteres y fallan las DLL de shapely:

   ```bash
   python -m venv %LOCALAPPDATA%\antenas\venv
   ```

4. Instala los paquetes desde la carpeta del programa. `requirements-lock.txt` tiene las versiones exactas
   probadas; `requirements.txt`, los rangos admitidos:

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install -r requirements-lock.txt
   ```

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS CSXCAD
   ```

5. KiCad 8 o posterior (opcional). Se busca en `Program Files\KiCad\<versión>\bin\kicad-cli.exe`, en el
   PATH o en la variable `KICAD_CLI`.
6. Motor de GPU (opcional, tarjeta NVIDIA RTX 20, 30, 40 o 50): descarga
   `openEMS-gpu-win64-cuda12.9-sm75-80-86-89-120.zip` de la release v0.2.0-alpha del proyecto (SHA-256
   `9cb3d3e6dd7239c7a8f211df05faf17e7ab4557d70c114bf3a3af1a424af6b3d`) y descomprímelo en `%LOCALAPPDATA%\Programs\gpu-build`
   (debe existir `gpu-build\opt\bin\openEMS.exe`). Guía y otras tarjetas: `docs/GPU.md`.
7. Arranca con `iniciar.bat` o con `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui\app.py`.
   Opciones: `--puerto 8081` (otro puerto), `--disenos <carpeta>` (otra biblioteca de diseños, igual que la
   variable `CHIRPTENNA_DISENOS`).

Opciones del instalador: `-Comprobar` (solo informa), `-SinPreguntas`, `-SinAccesoDirecto`, `-SinGPU` y
`-Python <ruta a python.exe>` (usar un Python 3.13/3.14 que ya tengas).
