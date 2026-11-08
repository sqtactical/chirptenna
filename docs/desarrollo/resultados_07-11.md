# Resultados de los barridos del 07–08-11-2026 (cola 2, bibanda y arreglos)

Solo simulación (openEMS en GPU, FR4 de 1,6 mm con εr 4,5, salvo cuando se indica RO4350B). «Peor S11» es el peor valor en
toda la banda de uso. Las tablas completas están en `barridos_gpu.md` / `.csv` (`python herramientas/resumen_barridos.py`) y
los datos en bruto en `salidas/_barridos/<etiqueta>/` (locales, fuera del repositorio). Actualizado el 08-11 a las 04:00;
la cola seguía corriendo (los barridos `P_*`, `Z_*`, `V_*` y `U_*` aún no se habían ejecutado).

## Antenas que llegan a −10 dB

| Antena | Banda | Peor S11 | Detalle |
|---|---|---|---|
| J-pole recta (valores por defecto del generador, sin centrar) | 868 / 915 MHz / 1,2 / 2,4 GHz / GPS L1 | −15,4 / −10,1 / −9,7 / −12,0 / −11,8 dB | desde el 08-11 `dimensionar` da el hueco ampliado y la toma al 26 %: η 86–92 % |
| J-pole recta | 868 MHz | −12,9 dB | `hueco` ×5 (14,1 mm), `toma` 0,26, `factor_adaptador` 1: banda −10 dB 841–879 MHz, η 92 % |
| J-pole de Koch | 1,2 GHz | −10,6 dB | `toma` 0,369, `factor_adaptador` 1,13–1,16: banda 1226–1311 MHz, η 92 % |
| Parche rectangular con ranura | 5,8 GHz | −10,6 dB | `alimentacion` 1, ranura estimada, `largo_alimentacion` 4,21 mm: toda la banda 5725–5875, η 60 %, 4,7 dBi |
| Colineal de dipolos | 2,4 GHz | −12,7 dB | `factor_linea` 1,0 (el 0,9 empeora a −8,4): banda 2357–2520 MHz, η 59 %, 4,1 dBi |
| Yagi con boom | 5,8 GHz | −16,4 dB | `factor_director` 0,81, `factor_reflector` 1,15, `ancho_boom` 8, `separacion_reflector` 0,39: haz hacia delante (φ 96°), 5,9 dBi, η 74 % |
| IFA | 1,2 GHz | −14,0 dB | `separacion_toma` 6,73, `altura` 12,1, `ancho_pista` 1,92: banda 1223–1326 MHz, η 91 % |
| PIFA | 1,2 GHz | −13,7 dB | centrada: banda 1152–1361 MHz, η 95 % |
| Dipolo | 1,2 GHz | −14,4 dB | `largo_brazo` 43,5, `ancho_pista` 2,88: η 97 % |
| Dipolo bowtie | 2,4 y 5,8 GHz | −13,0 y −11,6 dB | apertura 55°, `ancho_pista` 1,5 (2,4 GHz) y 0,63 (5,8 GHz): η 98 % y 88 % |
| Dipolo con manga (sleeve) | 5,8 GHz | −17,9 dB | `alto` 8,48, `largo_masa` 10,1, `ancho_placa` 13: η 90 % |
| Vivaldi | 5,8 GHz | −12,3 dB | `tasa` 4, `ancho_apertura` 24, `largo_aleta` 68,6: banda 5645–6303 MHz, η 66 % |
| Colineal de dipolos | 5,8 GHz | −13,8 dB | 4 elementos, `factor_linea` 1,1, `ancho_brazo` ×1,05: banda 5448–6090 MHz, η 50 %, 3,5 dBi |
| J-pole recta | 2,4 GHz | −10,9 dB | `hueco` 6 mm, `toma` 0,26: banda 2375–2491 MHz, η 85 % |
| Monopolo recto con IPEX | 2,4 GHz | −14,6 dB | masa manual (`largo_masa` 25, `ancho_placa` 40): banda 2206–2595 MHz, η 95 % (con masa automática −6,9 dB) |
| Monopolo de flecha de Sierpinski | 2,4 GHz | −15,9 dB | iteración 1, `ancho_pista` 0,786: η 93 % (la iteración 3 no adapta) |
| Panel de dipolos 2×2 | 2,4 GHz | −10,1 dB | brazo 19,906, reflector 0,125–0,163 λ: 12,1–12,7 dBi |
| Yagi con boom de Koch iteración 2 | 2,4 GHz | −14,4 dB | `factor_director` 0,76, `factor_reflector` 1,35, 2 directores: haz hacia delante (φ 66°), η 81 %, solo 2,6 dBi |
| **Bibanda: dos J-pole unidas** | 868 MHz + 2,4 GHz | −11,2 y −10,6 dB | diseño del usuario; `jpole_dual.py --modo union k2=1 sep2=3 a2=0,9 toma2=0,25 factor_adaptador=0,95`; placa ~21 × 207 mm; η 63 % / 87 %, G 0,5 / 4,0 dBi |
| **Bibanda: IFA con segunda rama** | 868 MHz + 2,4 GHz | −11,7 y −10,8 dB | `rama_dual.py ifa x_largo_brazo=1.17 k2=1 h2=0.6`; placa ~63 × 100 mm; η 79 % / 82 % |

Las dos bibanda son estrechas: los puntos vecinos de la rejilla caen a −8 dB o menos, así que habrá que ajustarlas con las
marcas de corte en la placa real. Ninguna está medida.

### Radiación de los bibanda (`radiacion_bibanda.py`, 868 / 2441,75 MHz)

| Diseño | S11 en esa frecuencia | η | Ganancia |
|---|---|---|---|
| J-pole unida | −11,2 / −29,0 dB | 63 / 87 % | 0,5 / 4,0 dBi |
| IFA con rama | −12,3 / −14,6 dB | 79 / 82 % | 1,4 / 2,4 dBi |
| Monopolo con rama | −11,9 / −8,4 dB | 89 / 84 % | 2,1 / 3,3 dBi |
| Dipolo de Sierpinski | −11,1 / −3,9 dB | 64 / 73 % | 1,3 / 4,1 dBi |

Todos irradian (ninguno disipa la potencia). El diagrama de la J-pole unida (`diagrama_bibanda.py`) es un toro de 2,5 dBi a
869 MHz y tiene varios lóbulos a 2,4 GHz (máx 4,7 dBi, la placa mide 1,7 λ).

## Casi (entre −10 y −8 dB)

J-pole de Koch a 2,4 GHz (−9,2), dipolo a 1,25 GHz (−9,0), colineal de dipolos a 5,8 GHz (−8,7; η 35 %), Minkowski a 5,8 GHz
(−8,5), panel de dipolos a 5,8 GHz (−8,4; con el brazo ×0,82) y a 2,4 GHz (−9,3 con el reflector a 0,2 λ), bowtie a 5,8 GHz (−8,3),
dipolo de Sierpinski bibanda (−8,5/−9,5 con `iteracion_s` 1, apertura 120°, brazo 40 mm) y monopolo con rama bibanda (−8,2 a 2,4 GHz,
−11,9 a 868 MHz).

## No van

| Antena | Mejor | Causa probable |
|---|---|---|
| J-pole bibanda de Koch (radiador 868 MHz de Koch, radiador 2,4 GHz de Koch o los dos; ~40 simulaciones) | −0,8 a −5,0 dB | a 868 MHz el Koch no acorta (152 mm frente a 144 mm recto); cada ajuste que sube una banda baja la otra |
| J-pole en abanico (un adaptador, dos radiadores) | −2,9 dB | el adaptador de 868 MHz no sirve a 2,4 GHz |
| J-pole recta a 5,8 GHz | −6,5 dB | la parte real se queda en ~20 Ω con cualquier `toma` o `hueco` |
| Parche circular (GPS L1 y 2,4 GHz) | −4,4 dB (RO4350B, GPS L1), −5,9 dB (2,4 GHz) | razón axial ≥ 6 dB; la alimentación por el borde no da polarización circular; el generador no varía la posición de la entrada |
| Quasi-Yagi de Koch iteración 3 | −2,6 dB | el haz sale hacia atrás |
| Yagi de Koch iteraciones 2 y 3 (2,4 GHz) | −7,1 / −7,2 dB | adaptan poco |
| Dipolo de Sierpinski a 915 MHz + 2,4 GHz | −4,1 dB | la segunda banda no cae donde toca |
| Parche con ranura en FR4, 2,4 GHz | −7,3 dB | η 48 % y banda estrecha |
| Monopolo de Hilbert, 2,4 GHz | −1,4 dB | pista de 0,2 mm (orden 2): pierde y desadapta |
| Minkowski en FR4, 2,4 GHz | −5,9 dB | η 29 % |
| Array de parches 5,8 GHz | −7,7 dB | η 12 % |
| Parche rectangular 1,2 GHz | −0,5 dB | placa enorme; el centrado tardó 89 min |
| Franklin 2,4 y 5,8 GHz | −7,8 y −1,7 dB | poca banda y parte real de 416 Ω a 5,8 GHz |
| Parche con parásito (apilado plano), 2,4 GHz | −0,6 dB | η 7 % con todas las variantes de hueco y factor |
| COCO, 2,4 GHz | −4,1 dB | η 24–35 % con 2 a 6 secciones |
| Dipolo con brazos anchos tipo parche | −6,7 a −1,6 dB (2,4 GHz) | el dipolo recto se desadapta al ensancharlo aun recentrando; el bowtie sí funciona |

## Recortes de aligerado (Yagi con boom y panel)

| Caso | Sin recortes | Con recortes |
|---|---|---|
| Yagi 868 MHz | −8,6 dB, η 81 % | −8,6 dB, η 87 % (la frecuencia sube 66 MHz) |
| Yagi 2,4 GHz | −12,8 dB, 6,0 dBi, haz delante | margen por defecto −2,3 dB, haz atrás; margen 6 mm −6,0 dB, η 75 %, 6,0 dBi, haz delante |
| Yagi 5,8 GHz | −13,3 dB | −12,0 dB, η 72 % |
| Panel 2×2 2,4 GHz | −10,1 dB, 12,7 dBi | −7,8 dB, 11,9 dBi |

Los recortes son inocuos a 868 MHz y 5,8 GHz y no a 2,4 GHz con el margen por defecto. Simular antes de fabricar.

## Monopolo de placa («parche sin plano de tierra»)

A 2,4 GHz: placa de 3 mm −12,9 dB (η 99 %), 6 mm −10,0 dB con banda 2398–2660 MHz, 10 mm −8,9 dB. Funciona, pero no mejora al
monopolo de pista fina.

## Topologías nuevas (`herramientas/topologias.py`, en curso)

Torniquete de dipolos cruzados (GPS L1), antena de ranura (2,4 GHz) e IFA de tres bandas. La ranura con el largo teórico resuena a
~3000 MHz (−2,4 dB) y hay que agrandarla un ~20 %. El torniquete falló en la primera tanda por una clave que faltaba en el puerto
(corregido). Los resultados se añadirán aquí.

## Lecciones de método

1. Las distancias entre pistas de una variante deben superar el ancho de pista del tipo a esa frecuencia (a 868 MHz, 2,81 mm).
   Un hueco de 0,19 mm bajó la malla a 0,07 mm y una simulación llevaba 78 min sin acabar.
2. Si se mata una simulación a mano quedan el `openEMS.exe` huérfano y el bloqueo `%LOCALAPPDATA%\antenas\gpu.lock`: la cola
   espera para siempre. Cerrar el `openEMS.exe` y borrar el bloqueo.
3. `doble_banda.py` no tiene `--solo-lista`: lanzarlo «para validar» arranca una simulación real.
4. En una Yagi hay que mirar `direccion_max` (φ 90° = hacia los directores) además del S11.
5. Con `--koch` el adaptador de la segunda J-pole se escalaba con el de la curva de Koch (un 35 % más largo): las referencias de
   una variante salen del diseño recto de la misma frecuencia. Corregido en `jpole_dual.py`.
6. Con `--centrar` el tamaño base cambia de un barrido a otro: el mismo punto puede dar −5,7 y −8,2 dB. Comparar dentro de un barrido.
7. GPS L1 + 2,4 GHz no cabe en el mecanismo del Sierpinski de dos bandas (razón 1,55; el Sierpinski da ~3×).

## Pendiente

~60 barridos en la cola (`salidas/_cola/pendientes.txt`): `P_*` (masa, relación de aspecto, ángulo de Koch, separaciones), `Z_*`,
`V_*`, `U_*` (Hilbert, Minkowski, apilado, COCO) y los refinamientos `R_*` que encole la tarea horaria de la sesión de Claude.
Falta también medir con el NanoVNA cualquiera de estas placas: todo lo anterior es simulación.
