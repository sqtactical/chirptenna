# Hoja de medida del pedido de JLC (2,4 GHz): predicciones congeladas y reglas contra el autoengaño

Esta hoja se escribe **antes de medir** (17-11-2026). Parte de `predicciones_2G4.md` (11-11) y de `placas_pedidas_2G4.md` (guion con el NanoVNA).
Su objetivo no es que la simulación «salga bien»: es poder decir, con las 5 unidades de cada placa, **si la simulación acierta o falla y en qué**,
sin que la medida se interprete a posteriori para darnos la razón.

## 0. Reglas que se fijan ahora y no se cambian después

1. **Congelar.** Las secciones 2, 3 y 4 se commitean antes de la primera medida (el hash del commit es la fecha de la predicción). Después solo se
   **añaden** líneas a la «Fe de erratas» (sección 9, con fecha y motivo); nunca se editan las predicciones ni los umbrales.
2. **Dos etapas (conjunto de ajuste y conjunto de prueba).** Los **cupones** son el único conjunto con el que se puede ajustar la εr. Las **antenas**
   son el conjunto de prueba: la εr medida en los cupones se fija, se **vuelven a escribir las predicciones de las antenas con ella** (sección 4, antes de medir
   ninguna antena) y solo entonces se miden. Ajustar la εr con las propias antenas y luego decir que «casan» no demuestra nada.
3. **Un solo parámetro libre.** Al comparar solo se puede ajustar la εr (y, si el cupón lo exige, la tanδ). Cambiar el largo de un brazo, la malla, el modelo del conector,
   etc. para que «cuadre» está prohibido en esta fase: cada una de esas explicaciones es una **hipótesis nueva** que se prueba con otra simulación o con otra medida, y
   se apunta como tal (sección 8), no como corrección.
4. **Datos crudos primero.** Cada medida se guarda en su `.s1p` (con `vna/medir_antena_pc.py`, sin retocar) y se anota en la hoja **antes** de abrir la simulación o la predicción al lado.
   Al medir no se mira la curva simulada.
5. **Se miden y se informan todas las unidades.** Ninguna se descarta salvo por un criterio escrito aquí (sección 6) y anotando el motivo. «Esta salió rara» no es un motivo.
6. **Se anotan también los fallos.** Medidas repetidas, antenas mal soldadas y calibraciones que fallan quedan en la hoja, con su resultado.
7. **Predecir antes de ver.** Cada medida lleva una predicción previa con su rango y una probabilidad (sección 3). Al final se cuentan los aciertos y se mira si las probabilidades eran razonables
   (por ejemplo, de diez cosas dadas al 70 %, deberían acertarse unas siete).

## 1. Qué se mide y cómo (resumen del guion)

- Calibración completa de referencia `completa_50k_2700M`; **se verifica al empezar, a mitad y al terminar cada sesión** (`calibrar_pc.py verificar`, con carga, abierto y corto); la deriva
  se anota. Una sesión con la verificación final fuera de tolerancia (sección 6) se repite entera.
- `vna/medir_antena_pc.py <nombre> completa_50k_2700M --zoom 2000 3000`; mismo rango y puntos en todas las unidades.
- Orden de las unidades de cada placa **aleatorio** (tirar dados o sortear), no «la mejor primero».
- Mismas condiciones en toda la serie: cable, SMA, posición, distancia a objetos y manos. Lo que cambia (ferrita, giro de 90°, mano cerca) está en la columna `condicion` de la plantilla.
- Cada unidad se mide **dos veces** seguidas sin tocarla (repetibilidad del instrumento) y, si se vuelve a conectar, una tercera (repetibilidad de la conexión).

## 2. Predicciones de partida (εr 4,5, antes de medir los cupones)

Resonancia = centro de la banda a −10 dB. Intervalo = de la simulación con εr 4,8 a la de εr 4,2, ensanchado un **±1,3 %** (la incertidumbre de la propia simulación: diferencia entre
la ficha original y la simulación de hoy del Sierpinski). Salen de `salidas/_barridos/SENS_er_pedido/` y de `predicciones_2G4.md`.

| Placa | f simulada (εr 4,5) | Intervalo (εr 4,2–4,8 ±1,3 %) | Pendiente (MHz por unidad de εr) | P(f medida dentro de ±2 % de la simulada con εr 4,5) | P(banda −10 dB incluye 2441,75 MHz) |
|---|---|---|---|---|---|
| Dipolo con coaxial (Y59) | 2466 | 2414–2519 | −69 | 55 % | 75 % |
| Sierpinski (Y56) | 2476 | 2421–2533 | −81 | 50 % | 70 % |
| Yagi recta 2 dir. (Y54) | 2447 | 2375–2522 | −139 | 45 % | 65 % |
| Koch ajustable (Y57), sin recortar | 2328 | 2270–2389 | −97 | 45 % | 15 % (sale largo a propósito) |
| J-pole de Koch (Y58) | 2458 | 2396–2524 | −107 | 35 % | 40 % |
| Parche rectangular (Y55) | 2439 | 2334–2554 | −259 | 25 % | 30 % (banda de 37 MHz) |

(Las probabilidades son mi juicio subjetivo, escrito antes de medir; no salen de ninguna cuenta. Sirven para comprobar después si estamos sobreconfiados.)

**Predicción del S11:** la profundidad de S11 en la resonancia depende mucho de cómo se suelde el SMA y del cable, y no se predice con precisión. Solo se predice que **a la frecuencia
de resonancia el S11 sea ≤ −10 dB** en el dipolo, el Sierpinski y la Yagi (P 70 %), y no se hace predicción numérica de la profundidad.

**Predicción de la εr (cupones):** εr media del FR4 de los cupones = **4,4**, con un intervalo del 80 % de 4,15 a 4,65 (mi estimación previa). La dispersión entre las 5 unidades de un mismo cupón: **≤ 0,10** (desviación típica de la εr inferida), con P 70 %.

## 3. Pruebas que podrían refutar la simulación (fijadas ahora)

| # | Qué se comprueba | Se considera **fallo del modelo** si… |
|---|---|---|
| T1 | **Coherencia de la εr** entre los cupones y las antenas: con la pendiente de la tabla 2, cada antena da una εr_i = 4,5 + (f_medida − f_sim)/pendiente | las εr_i de las antenas difieren entre sí en más de **0,25**, o la media de las antenas difiere de la de los cupones en más de **0,2** |
| T2 | **Mismo sentido de desplazamiento** de las seis antenas respecto a la simulación | alguna se desplaza en sentido contrario al resto (la causa no es la εr) |
| T3 | **Dispersión entre unidades** de la misma placa | la desviación de f entre las 5 unidades supera **1 %** (entonces la medida de una sola unidad no sirve para calibrar) |
| T4 | **Criterio de salida de la hoja de ruta (F1):** f simulada a ≤ 2 % de la medida en al menos 5 de las 6 antenas, con la εr medida de los cupones | cumplen menos de 5 → no se declara «validado» ningún tipo: solo se describe la diferencia y se busca la causa |
| T5 | **Orden de sensibilidad:** el parche debe moverse más que la J-pole, y esta más que el dipolo (por la pendiente) | el orden se invierte con la misma εr |

Un tipo solo pasa a «Medida» en `problemas.ESTADO` si cumple T3 y su f medida queda a ≤ 2 % de la simulada con la εr de los cupones. Una sola unidad que case **no** basta.

## 4. Predicciones de la etapa 2 (se rellenan DESPUÉS de los cupones y ANTES de medir ninguna antena)

Rellenar con `herramientas/sensibilidad_er.py` usando la εr medida (y tanδ si hace falta), sin tocar la geometría; escribir la fecha y hacer un commit.

| Placa | εr usada | f simulada (MHz) | Banda −10 dB simulada (MHz) | Fecha y hora | Hash del commit |
|---|---|---|---|---|---|
| Dipolo con coaxial | | | | | |
| Sierpinski | | | | | |
| Yagi recta 2 dir. | | | | | |
| Koch ajustable (sin recortar) | | | | | |
| J-pole de Koch | | | | | |
| Parche rectangular | | | | | |

## 5. Hoja de medidas (datos crudos)

Usar la plantilla `plantilla_medidas_2G4.csv` (una fila por medida), con columnas: `fecha_hora`, `placa`, `unidad` (u1–u5), `orden_aleatorio`, `condicion`, `archivo_s1p`,
`cal_verificada_inicio`, `cal_verificada_fin`, `f_res_MHz` (centro de la banda a −10 dB), `banda_ini_MHz`, `banda_fin_MHz`, `S11_min_dB`, `f_S11_min_MHz`, `S11_2441_75_dB`, `observaciones`.
Se rellena **a mano en el momento** y se guarda el `.s1p` sin tocar. La comparación con la predicción se hace después, en una tabla aparte (sección 7).

## 6. Criterios de exclusión (los únicos admitidos)

- **Calibración fuera de tolerancia:** al verificar con la carga, |S11| > −35 dB, o diferencia entre la verificación inicial y la final de más de 0,5 dB. Se repite la sesión.
- **Defecto visible de la placa** (cobre levantado, pista cortada, pad arrancado), anotado con foto antes de medir.
- **Soldadura mal hecha** reconocida antes de ver la medida (frío, puente, SMA torcido), con foto; esa unidad se rehace o se anota como «con defecto» y se informa aparte.
- Cualquier otra cosa **no** excluye: se informa y se estudia.

## 7. Tabla de resultados (se rellena al final, con las predicciones congeladas arriba)

Para cada antena: la mediana y el rango de las 5 unidades; Δf respecto a la simulación con εr de cupones; si cae dentro del intervalo de la sección 2; la εr_i inferida (T1); resultado de T1–T5.
Al terminar, contar cuántas de las predicciones con probabilidad dada se cumplieron y escribirlo aquí: **«Acertadas / dadas»** por franja de probabilidad (≤ 40 %, 40–60 %, ≥ 60 %).

## 8. Hipótesis nuevas (no son correcciones)

Cada explicación que aparezca al ver los datos («el cable», «el conector», «la máscara», «la malla»…) se apunta aquí con su predicción comprobable **y se prueba aparte** (otra medida, otra simulación o ambas) antes
de aplicarla. Formato: *fecha · hipótesis · qué debería pasar si es cierta · qué debería pasar si es falsa · resultado*.

## 9. Fe de erratas (solo se añade, con fecha)

(vacía)
