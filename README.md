<p align="center"><img src="docs/logo/chirptenna_texto.png" alt="Chirptenna" width="560"></p>

# Chirptenna: generador de antenas para PCB

*[English version](README.en.md)*

> **Estado: alpha (v0.1.0-alpha).** Validado solo en simulación: todavía no se ha medido ninguna
> placa fabricada. **Se buscan medidas reales**: si fabricas una antena y la mides, compártela con
> la plantilla [«Medida real»](../../issues/new/choose). Cómo colaborar: [CONTRIBUTING.md](CONTRIBUTING.md).

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

1. Eliges el tipo de antena, la banda (433, 868, 2,4 GHz u otra) y el sustrato.
2. El programa dimensiona la antena con fórmulas **calibradas con simulaciones anteriores** y
   comprueba las reglas de fabricación de JLC.
3. Opcionalmente la **simula con openEMS** y ajusta su tamaño hasta que resuena en la frecuencia
   pedida (S11, carta de Smith, diagrama de radiación, ganancia y eficiencia).
4. La exporta: placa de prueba de KiCad con SMA de canto o IPEX, Gerber con taladros para JLC,
   DXF y huella para usarla dentro de otra placa. Pasa el DRC de KiCad y rotula la serigrafía.
5. Puede añadir **ajuste tras fabricar** sin componentes: sobrelargo con marcas de corte rotuladas
   en MHz y tramos que se cierran con un puente de estaño (o red en π opcional).
6. Guarda cada diseño en **Mis diseños** (`Documentos\Chirptenna\disenos`) con su simulación, su
   exportación y sus medidas, y un **asistente del NanoVNA** te guía: calibrar en el rango de la
   antena, comprobar, medir (también en vivo mientras cortas) y qué cortar o qué poner en la red en π,
   con la curva medida superpuesta a la simulada.
7. Las Yagi y el panel pueden llevar **recortes de aligerado**: ventanas sin FR4 entre el cobre y el
   borde (sin simular todavía: la frecuencia puede subir un poco).

## Tipos de antena

| Tipo | Familia | Estado en simulación |
|---|---|---|
| Monopolo recto, meandro, Koch | monopolo | ✅ validados (2,4 GHz y 868 MHz) |
| Monopolo de Sierpinski | monopolo | ✅ validado (2,4 GHz) |
| Monopolo de Hilbert | monopolo | ⚠️ resuena, pero sin red en π no adapta |
| Parche rectangular | parche | ✅ validado (banda estrecha) |
| Parche de Minkowski | parche | ⚠️ iteración 1 bien; la 3 tiene poca eficiencia en FR4 |
| Dipolo impreso (balun impreso o coaxial al centro) | dipolo | ✅ validado (2,4 GHz) |
| J-pole y J-pole de Koch | jpole | ✅ Koch validada; la recta, en revisión |
| Yagi con boom (doble cara) | yagi | ✅ elementos rectos (6–7 dBi); con Koch, experimental |
| Quasi-Yagi con dipolo de Koch | yagi | ⚠️ experimental |
| Panel de dipolos 2×2 / 4×4 sobre reflector | panel | ✅ 2×2 ≈ 12,7 dBi, 4×4 ≈ 16,6 dBi |
| Array de parches 2×2 / 4×4 | array | ⚠️ sin terminar de validar |
| Colineal coaxial impresa (COCO) | colineal | ⚠️ radia, pero las pérdidas del FR4 se comen la ganancia |
| Colineal Franklin | colineal | ⚠️ experimental |

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
| Parche de Minkowski | Iteración 1: η ~33 %. Iteración ≥ 2: impedancia de borde ~14 Ω, S11 ≈ −5 dB y η ~23 % (la ranura no lo arregla). |
| J-pole recta | Resuena pero adapta mal (R ≈ 6–10 Ω). Usar la J-pole de Koch. |
| Yagi con boom de Koch | Adapta mal y radia más hacia atrás que hacia los directores. Usar elementos rectos. |
| Yagi con boom, dipolo plegado | Radia hacia atrás (F/B −3,6 dB). Usar alimentación directa (el reflector queda a ~0,39 λ0 y la placa es más larga). |
| Yagi con boom, transformador λ/4 | Banda estrecha (~50 MHz) y η ~55 %. |
| Quasi-Yagi de Koch | Radia hacia atrás y adapta mal (−3,5 dB). Experimental. |
| Panel de dipolos | En simulación el haz sale ~9° inclinado (probablemente un artefacto). La disposición «simétrica» empeora la adaptación. |
| Array de parches | Sin terminar de validar: el centro de banda salta mucho y cada simulación tarda horas. |
| Colineal COCO | Radia, pero las pérdidas del FR4 dejan η ~53 % y ~1,9 dBi. |
| Colineal Franklin | Adapta mal (−5,3 dB) y solo ~1,8 dBi. Experimental. |
| Recortes de aligerado | Sin simular: quitar FR4 sube algo la frecuencia. |
| Fuera de 2,4 GHz | Solo los monopolos recto, meandro y Koch están validados también a 868 MHz. |

Los detalles de cada simulación y los errores encontrados por el camino están en
[`CLAUDE.md`](CLAUDE.md) (lecciones aprendidas) y [`RETOMAR.md`](RETOMAR.md) (estado).

## Requisitos

- **Windows 10/11** de 64 bits (es donde se ha desarrollado; el código no depende de él salvo las
  rutas por defecto).
- **Python 3.13 o 3.14** (las wheels de openEMS 0.37 solo existen para esas versiones).
- **openEMS v0.37** con sus wheels de Python (`openEMS`, `CSXCAD`).
- **KiCad 8 o posterior** (`kicad-cli`, probado con la 10) para generar los Gerber y pasar el DRC.
  Sin él se exportan el `.kicad_pcb` y el DXF, pero no los Gerber.
- Opcional: un **NanoVNA-H** (firmware DiSlord) para medir.

## Instalación

**Sin saber nada de Python:** descarga el ZIP, haz doble clic en **`instalar.bat`** y luego abre el
programa con el acceso directo del escritorio o con **`iniciar.bat`**. El instalador descarga Python y
openEMS de sus páginas oficiales (comprobando la firma y el SHA-256), crea el entorno e instala los
paquetes, sin permisos de administrador. Guía paso a paso, problemas frecuentes, desinstalación e
instalación manual: **[INSTALAR.md](INSTALAR.md)**.

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

- **Código:** [GNU GPL v3.0](LICENSE).
- **Diseños publicados por el autor** (antenas y cupones exportados): [CC BY-NC 4.0](LICENSE-DISENOS.md).
- Los diseños que generes tú con el programa son tuyos.
