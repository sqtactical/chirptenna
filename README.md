<p align="center"><img src="docs/logo/chirptenna_texto.png" alt="Chirptenna" width="560"></p>

# Chirptenna: generador de antenas para PCB

[![Comprobar](https://github.com/sqtactical/chirptenna/actions/workflows/comprobar.yml/badge.svg)](https://github.com/sqtactical/chirptenna/actions/workflows/comprobar.yml)

*[English version](README.en.md)*

> **Estado: alpha (v0.2.0-alpha).** Validado solo en simulación: todavía no se ha medido ninguna
> placa fabricada. **Se buscan medidas reales**: si fabricas una antena y la mides, compártela con
> la plantilla [«Medida real»](../../issues/new/choose). Cómo colaborar: [CONTRIBUTING.md](CONTRIBUTING.md).
> Cambios de cada versión: [CHANGELOG.md](CHANGELOG.md).

**Chirptenna** (de *chirp*, la modulación de LoRa, y *antenna*) es un programa que genera **antenas impresas en PCB** (fractales, directivas y de referencia) para una
frecuencia objetivo, las **ajusta simulándolas con openEMS** (FDTD) y las **exporta a KiCad,
Gerber y DXF** listas para fabricar. Tiene interfaz gráfica en el navegador y herramientas de
línea de comandos. Pensado para los nodos LoRa de Meshtastic (433 / 868 MHz) y para 2,4 GHz.

Incluye además el control de un **NanoVNA-H** (calibración en el PC y medida de antenas) y unos
**cupones de calibración** para medir la εr real del FR4, de modo que la simulación coincida con
las placas fabricadas.

> **Estado del proyecto:** todo lo que se indica aquí está **simulado, no medido**. Las placas
> están pedidas; la εr del FR4 de JLC (4,5 por defecto) está pendiente de medir con el cupón.
> Trátalo como un proyecto en desarrollo.

## Qué hace

1. Eliges el tipo de antena, la banda (433, 868, 915 ISM, 1,2 GHz radioaficionado, GPS L1, Iridium, 2,4 GHz, 5,8 GHz u otra; las que no son 868 ni 2,4 GHz están sin simular, y a 5,8 GHz el FR4 pierde mucho) y el sustrato.
2. El programa dimensiona la antena con fórmulas **calibradas con simulaciones anteriores** y
   comprueba las reglas de fabricación de JLC.
3. Opcionalmente la **simula con openEMS** y ajusta su tamaño hasta que resuena en la frecuencia
   pedida (S11, carta de Smith, diagrama de radiación, ganancia y eficiencia).
4. La exporta: placa de prueba de KiCad con SMA de canto o IPEX, Gerber con taladros para JLC,
   DXF y huella para usarla dentro de otra placa. Pasa el DRC de KiCad y rotula la serigrafía con el
   logo de Chirptenna y las inscripciones que elijas (tipo y frecuencia, resultado de la simulación,
   licencia, fecha, texto libre…).
5. Puede añadir **ajuste tras fabricar** sin componentes: sobrelargo con marcas de corte rotuladas
   en MHz y tramos que se cierran con un puente de estaño (o red en π opcional).
6. Guarda cada diseño en **Mis diseños** (`Documentos\Chirptenna\disenos`) con su simulación, su
   exportación y sus medidas, y un **asistente del NanoVNA** te guía: calibrar en el rango de la
   antena, comprobar, medir (también en vivo mientras cortas) y qué cortar o qué poner en la red en π,
   con la curva medida superpuesta a la simulada.
7. Las Yagi y el panel pueden llevar **recortes de aligerado**: ventanas sin FR4 entre el cobre y el
   borde (sin simular todavía: la frecuencia puede subir un poco).
8. **Interfaz en castellano, inglés, francés y alemán** (selector en la cabecera; también en la web lite). Los
   idiomas son ficheros `antenas/idiomas/<código>.json`: añadir otro es traducir un fichero.
9. **Aceleración por GPU** (experimental, tarjetas NVIDIA): con un openEMS compilado con motor GPU, las simulaciones
   van ~10 veces más rápido. La frecuencia, el S11 y la impedancia coinciden con la CPU; la ganancia y la eficiencia
   salen algo altas, así que confirma el diseño final en CPU. Ver [`RETOMAR.md`](RETOMAR.md).

## Capturas

**Elegir antena**: al entrar, una galería de tipos agrupados por uso, con dibujo, descripción y estado.

![Galería de tipos de antena](docs/capturas/galeria.png)

**Diseño**: eliges tipo y banda, y el programa dimensiona la antena y avisa de sus problemas conocidos.

![Pestaña Diseño con un monopolo de Sierpinski a 2,4 GHz](docs/capturas/diseno.png)

**Simulación con openEMS**: S11, ROE, carta de Smith con la banda marcada, diagrama de radiación y
diagrama 3D con la placa dentro (aquí, una Yagi de 2450 MHz: 7,2 dBi hacia los directores).

![Pestaña Simulación de una Yagi de 2450 MHz](docs/capturas/simulacion.png)

**Fabricar**: reglas de JLC, exportación a KiCad, Gerber y DXF, y las inscripciones de la serigrafía.

![Pestaña Fabricar con las comprobaciones, la exportación y la serigrafía](docs/capturas/fabricar.png)

La placa resultante (render de KiCad): cara superior y cara inferior con el logo y las inscripciones.

<p align="center"><img src="docs/capturas/placa_yagi.png" alt="Placa de la Yagi: cara superior e inferior" width="640"></p>

**Medir**: asistente del NanoVNA (conectar, calibrar, comprobar, medir) con la medida superpuesta a la simulación.

![Pestaña Medir con el asistente del NanoVNA](docs/capturas/medir.png)

## Tipos de antena

| Tipo | Familia | Estado en simulación |
|---|---|---|
| Monopolo recto, meandro, Koch | monopolo | ✅ validados (2,4 GHz y 868 MHz) |
| Monopolo de Sierpinski | monopolo | ✅ validado (2,4 GHz y 868 MHz) |
| Monopolo de Hilbert | monopolo | ⚠️ resuena, pero sin red en π no adapta |
| Parche rectangular | parche | ✅ validado (banda estrecha) |
| Parche de Minkowski | parche | ⚠️ iteración 1 bien; la 3 tiene poca eficiencia en FR4 |
| Parche de polarización circular (esquinas cortadas, una sola entrada; GPS, Iridium) | parche | ⚠️ sin testear ni validar |
| Parche con ranura en U | parche | ⚠️ sin testear ni validar |
| Parche con parásito acoplado (alternativa plana al apilado) | parche | ⚠️ sin testear ni validar |
| Antena F invertida (J-pole en F) y PIFA | monopolo | ⚠️ sin testear ni validar |
| Dipolo con manga (sleeve) | monopolo | ⚠️ sin testear ni validar |
| Vivaldi antipodal | vivaldi | ⚠️ sin testear ni validar |
| Colineal de dipolos en serie (línea microstrip) | colineal | ⚠️ sin testear ni validar |
| Dipolo impreso (recto o de Koch; balun impreso o coaxial al centro) | dipolo | ✅ validado (2,4 GHz y 868 MHz) |
| Dipolo bowtie (pajarita) o bowtie de Sierpinski | dipolo_bowtie | ✅ validado (2,4 GHz y 868 MHz); da el doble de banda que el recto |
| J-pole y J-pole de Koch | jpole | ✅ Koch validada (2,4 GHz y 868 MHz); la recta casi adapta (−8 a −9 dB) |
| Yagi con boom (doble cara) | yagi | ✅ elementos rectos (6–7 dBi; 2,4 GHz y 868 MHz); con Koch, experimental |
| Quasi-Yagi con dipolo de Koch | yagi | ⚠️ experimental |
| Panel de dipolos, bowtie o bowtie de Sierpinski, 2×2 / 4×4, sobre reflector | panel | ✅ 2×2 ≈ 12,1 dBi (dipolos) y 12,6 dBi (Sierpinski), 4×4 ≈ 14,6–16,6 dBi; un solo elemento, sin afinar |
| Array de parches 2×2 / 4×4 | array | ⚠️ sin terminar de validar |
| Colineal coaxial impresa (COCO) | colineal | ⚠️ radia, pero las pérdidas del FR4 se comen la ganancia (a 868 MHz no sirve) |
| Colineal Franklin | colineal | ⚠️ adapta, pero con poca banda y ~2,5 dBi |

## ⚠️ Problemas conocidos

**Todo lo validado hasta ahora es en simulación**, con εr 4,5 para el FR4 de JLC. Todavía no se ha
medido ninguna placa fabricada ni la εr real (para eso están los cupones). Mide siempre la antena
antes de darla por buena. La interfaz muestra estos avisos al elegir el tipo y al exportar.

| Tipo / opción | Problema |
|---|---|
| Monopolo de Hilbert | Resuena, pero sin red en π adapta muy mal (−2,7 dB a 2,4 GHz, −4,6 dB a 868 MHz). A 868 MHz cada simulación tarda más de 3 h. |
| Monopolo en meandro | La frecuencia salta varios % con cambios pequeños del alto; con masa pequeña puede no llegar a −10 dB. |
| Monopolos con IPEX | El monopolo recto con IPEX adaptó mal (−7 dB): la transición del pad central está en revisión. Con SMA va bien. |
| Parche rectangular | Banda estrecha en FR4 de 1,6 mm (~36 MHz): no cubre toda la ISM de 2,4 GHz. η ~47 %. |
| Parche de Minkowski | Iteración 1: η ~33 % y ~1 dBi. Iteración 3: adapta (−17,5 dB) pero η ~30 % y < 1 dBi. |
| J-pole recta | Resuena pero apenas adapta (−8 a −9 dB). La J-pole de Koch adapta mejor. |
| Yagi con boom de Koch | Adapta mal y radia más hacia atrás que hacia los directores. Usar elementos rectos. |
| Yagi con boom, dipolo plegado | Radia hacia atrás (F/B −3,6 dB). Usar alimentación directa (el reflector queda a ~0,39 λ0 y la placa es más larga). |
| Yagi con boom, transformador λ/4 | Banda estrecha (~50 MHz) y η ~55 %. |
| Quasi-Yagi de Koch | Radia hacia atrás y adapta mal (−3,5 dB). Experimental. |
| Panel de dipolos | El ajuste no itera la frecuencia (S11 ondulado): el tamaño inicial está calibrado con el 2×2 a 2,4 GHz. Con malla fina el haz sale de frente (0–3°). El panel de un solo elemento resuena lejos del objetivo. La disposición «simétrica» empeora la adaptación. |
| Array de parches | Sin terminar de validar: el 2×2 resuena un 16 % por debajo con el tamaño por defecto, η ~22 % y cada simulación tarda horas. |
| Colineal COCO | Radia, pero las pérdidas del FR4 dejan η ~53 % y ~1,9 dBi a 2,4 GHz; a 868 MHz, η 26 %, −2 dBi y S11 −7,8 dB. |
| Colineal Franklin | Adapta (−19 dB a 2,4 GHz, −35 dB a 868 MHz) pero con 62 y 23 MHz de banda y 2,2–2,8 dBi. Experimental. |
| Recortes de aligerado | Yagi aligerada simulada: −1,3 dBi y hay que reajustar el reflector; en el resto, sin simular. |
| Fuera de 2,4 GHz | A 868 MHz están simulados los monopolos recto, meandro, Koch y Sierpinski, el dipolo, la J-pole de Koch, la Yagi con boom y las colineales Franklin y COCO; el resto, solo a 2,4 GHz. |

Los detalles de cada simulación y los errores encontrados por el camino están en
[`CLAUDE.md`](CLAUDE.md) (lecciones aprendidas), [`RETOMAR.md`](RETOMAR.md) (estado) y
[`docs/desarrollo/historial.md`](docs/desarrollo/historial.md) (diario de desarrollo).

## Requisitos

- **Windows 10/11** de 64 bits (es donde se ha desarrollado; el código no depende de él salvo las
  rutas por defecto).
- **Python 3.13 o 3.14** (las wheels de openEMS 0.37 solo existen para esas versiones).
- **openEMS v0.37** con sus wheels de Python (`openEMS`, `CSXCAD`).
- **KiCad 8 o posterior** (`kicad-cli`, probado con la 10) para generar los Gerber y pasar el DRC.
  Sin él se exportan el `.kicad_pcb` y el DXF, pero no los Gerber.
- Opcional: un **NanoVNA-H** (firmware DiSlord) para medir.

## Pruébalo sin instalar

**[Chirptenna web lite](https://sqtactical.github.io/chirptenna/)**: diseña la antena en el navegador y descárgala
para **KiCad** (`.kicad_pcb`, huella, DXF y `diseno.json`). Todo se calcula en tu navegador (Python con Pyodide),
sin enviar nada a ningún servidor. No simula ni pasa el DRC de KiCad: abre la placa en KiCad, pasa su DRC y saca
allí los Gerber (el zip trae un LÉEME con los pasos). Para simular y medir, instala la aplicación.

## Instalación

**Sin saber nada de Python:** descarga el ZIP de la última versión en
[Releases](https://github.com/sqtactical/chirptenna/releases), haz doble clic en **`instalar.bat`** y luego abre el
programa con el acceso directo del escritorio o con **`iniciar.bat`**. El instalador descarga Python y
openEMS de sus páginas oficiales (comprobando la firma y el SHA-256), crea el entorno e instala los
paquetes, sin permisos de administrador. Guía paso a paso, problemas frecuentes, desinstalación e
instalación manual: **[INSTALAR.md](INSTALAR.md)**.

**Manual de uso:** **[MANUAL.md](MANUAL.md)** (inglés: [MANUAL.en.md](MANUAL.en.md)). Cubre cada pestaña, cómo medir con el NanoVNA y cómo
ajustar la antena fabricada (marcas de corte, puentes y **red en π**, con ejemplos y qué componentes comprar).

## Uso

**Interfaz gráfica** (http://localhost:8080):

```bash
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui/app.py
```

Las pestañas siguen el orden de trabajo: **Diseño → Simulación → Fabricar → Medir → Mis diseños**.
La carpeta de los diseños se puede cambiar con la variable de entorno `CHIRPTENNA_DISENOS`.

**Simular y ajustar varios diseños desde la línea de comandos** (resultados en la carpeta indicada):

```bash
python -m antenas.validar_lote salidas/lote --malla adaptada --hilos 6 monopolo_recto:866.5:normal "dipolo:2441.75:normal:{\"alimentacion\":1}"
```

**Cola de simulaciones** (dos trabajadores a la vez como máximo):

```bash
python herramientas/cola.py añadir mi_trabajo python -m antenas.validar_lote salidas/lote monopolo_koch:2441.75:normal
```

```bash
python herramientas/cola.py trabajar --hilos 6
```

**Recalibrar las estimaciones** con todas las simulaciones hechas:

```bash
python herramientas/calibrar_estimaciones.py
```

**Generar los cupones de calibración de εr**:

```bash
cd cupon && python generar_cupon.py
```

Las simulaciones son lentas: de minutos (monopolos a 2,4 GHz) a horas (arrays, o cualquier cosa a
868 MHz con pistas finas). Se guardan en caché en `%TEMP%\antenas_sim`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `antenas/` | Paquete principal: catálogo (`tipos`), geometría, generadores, simulación con openEMS, ajuste, exportación, consejos |
| `gui/` | Interfaz NiceGUI |
| `vna/` | Control del NanoVNA, calibración en el PC y medidas |
| `cupon/` | Generador de cupones de εr y simulación de sus anillos |
| `fase0/` | Validación inicial de openEMS (dipolo y monopolo) |
| `referencias/` | Modelos de antenas comerciales para comparar simulación y medida |
| `herramientas/` | Cola de simulaciones, calibración de estimaciones, diagnósticos |
| `analisis/`, `placa_sim/` | Herramientas para estudiar placas existentes a partir de sus Gerber |
| `docs/logo/` | Logo (un grillo con antenas de Koch) y el script que lo genera |

`salidas/` (exportaciones), `placas/` (Gerber de terceros) y los cupones generados no están en el
repositorio: se regeneran con el programa.

## Licencia

- **Código:** [GNU AGPL v3.0](LICENSE) (la v0.1.0-alpha se publicó con GPL v3.0; las siguientes, con AGPL).
  Puedes usarlo, modificarlo y venderlo, pero si distribuyes una versión modificada **o la ofreces como
  servicio por internet**, tienes que publicar su código fuente con la misma licencia.
- **Diseños publicados por el autor** (antenas y cupones exportados): [CC BY-NC 4.0](LICENSE-DISENOS.md).
- Los diseños que generes tú con el programa son tuyos.
