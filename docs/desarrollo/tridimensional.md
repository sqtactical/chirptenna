# Antenas de varias placas no coplanares y hélices de flex (16-11, sin validar)

Cuatro tipos nuevos (`antenas/tridimensional.py`), pedidos por el usuario desde las ideas de «Ideas a más largo plazo» del ROADMAP.
Todo está simulado a 2,4 GHz con malla gruesa (paso 1,2 mm, precisión «rápida», CPU) y **sin centrar ni medir**.

| Tipo | Qué es | Placas a fabricar | Simulado (2,4 GHz) |
|---|---|---|---|
| `diedro` | Dipolo bowtie antipodal con los dos brazos doblados hacia arriba un ángulo `angulo_v` (25° por defecto) | centro (SMA, línea y balun) + 2 alas, soldadas en las bisagras | 0° = bowtie plano exacto (−23,9 dB, D 2,2 dBi); 5° −25,6 dB; 25° −36,4 dB |
| `reflector_esquina` | Dipolo bowtie en el plano bisector de dos placas reflectoras de 90° (vértice truncado para dejar pasar la línea) | dipolo + 2 reflectores (FR4 con cobre en las dos caras, 150 × 110 mm) | S11 −48,8 dB, D 10,3 dBi, G 10,0 dBi, haz de frente (θ 90°, φ 90°) |
| `helice_normal` | Monopolo helicoidal de λ/4 de hilo sobre una placa de masa con SMA; el hilo es una tira de flex enrollada | placa de masa + tira de flex de π·D de ancho (rayas diagonales) | −6,4 dB, D 1,9 dBi (sin centrar) |
| `helice_cuadrifilar` | Cuatro brazos de λ/4 en una tira de flex enrollada (GPS L1, circular) | placa de masa + tira de flex | no se simula desde la interfaz |

## Cómo está hecho

- **Modelo** (`antenas/modelo.py`, `antenas/pose.py`): la `Antena` principal (la del conector y el puerto) es plana en XY. Las demás placas van en
  `Antena.placas3d` como `{nombre, antena (plana), origen, giros [(eje, grados)], fina}`: primero los giros alrededor del origen local, después el
  desplazamiento. Regla de la mano derecha, la misma de CSXCAD (`AddTransform('RotateAxis', eje, grados)`, grados). `Antena.hilos3d` guarda hilos
  `{puntos (n, 3), ancho}`. Las placas a fabricar van en `Antena.modulos`, como en la colineal modular (cada una exporta con su Gerber y su DRC).
- **Cobre simulado y fabricado** (`Antena.cobre_sim`): una unión soldada se simula como cobre continuo hasta la bisagra, pero se fabrica a 0,5 mm del
  canto (mínimo de KiCad). `cobre_sim` y `placas3d[i]['antena']` llevan el cobre continuo; las placas de `modulos`, el de fabricar.
- **Simulación** (`simulacion.simular`): FR4 y cobre de cada placa con la transformación de CSXCAD; los hilos con `AddCurve`. El dominio y la malla
  abarcan las piezas (`pose.caja_conjunto`); las marcadas `fina` ponen la rejilla uniforme y líneas en z con el paso fino sobre su proyección.
  **Trampa**: una lámina PEC de grosor cero girada no toca ninguna arista de la malla y desaparece sin avisar (el dipolo en V daba −1 dB con solo 5° de
  giro). El cobre de una placa girada se simula como una losa PEC de una celda de grosor (el paso fino en las alas, `λ/20` en un reflector grande).
  La clave de la caché lleva `placa3d_losa`: las cachés de la versión con láminas daban resultados falsos.
- **Vista 3D** (`vista3d._placa(..., pieza=)`, `_placas3d`): cada placa con su pose y los hilos como líneas.
- **Reflector de esquina**: el vértice queda a `separacion` del dipolo (por detrás de la placa del dipolo si el boom es corto) y las placas empiezan a
  `h + 1 mm` del plano de la placa del dipolo; la placa de abajo se baja `h` por su normal para que el grosor quede hacia fuera en las dos.
- **Hélices**: el hilo va a radio D/2 desde un pad de la línea de 50 Ω (z = h). Largo del hilo (modo normal) `N·√((πD)² + (H/N)²)`, resonancia
  `f = c/(4·L)`, sin calibrar (`K_HELICE_NORMAL` = 1). La cuadrifilar es solo geometría: la alimentación en cuadratura de dos puertos está en
  `herramientas/helice_flex.py` y no entra en `simular` (`info['sin_simulacion']` hace que `simular` lance un error claro).

## Falta

- Centrar cada tipo (la estimación de frecuencia no está calibrada), simular en GPU con malla fina y verificar la malla.
- Modelar la unión soldada y la escuadra o pieza que fija el ángulo; medir el diagrama de la V según el ángulo.
- El reflector de esquina con una Yagi pequeña delante, el vértice sin truncar y con la línea por una ranura.
- La red de 90° o el balun de la cuadrifilar y su simulación desde la interfaz; el flex de la hélice se simula sin su dieléctrico.
- Web: la web lite genera las placas y la tira, pero no tiene vista 3D.
