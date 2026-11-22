# Predicción y guion: stubs abiertos del cupón B (22-11-2026)

Escrito **antes de medir**. Objetivo: comprobar con hardware el método de los stubs abiertos en S11 (`antenas/plastico.py`: `resonancias_stub`, `er_fr4_stubs`) con una placa que ya tenemos: el
**cupón B** (JLC, Y53) lleva dos stubs abiertos, **S80** y **S30** (largo desde el borde de la placa: 85,7 y 35,7 mm; 80 y 30 mm desde el fin de la transición del SMA). Es la misma estructura que el cupón C,
sin muestra. No se prueba aquí la parte del plástico (el cupón B no tiene taladros), solo la resonancia, su resistencia y la εr del FR4.

## Reglas (las mismas de `hoja_medidas_2G4.md`)

1. Esta hoja se escribe antes de medir; después solo se añade a la «Fe de erratas», con fecha.
2. Datos crudos primero: cada medida va a su `.s1p` sin retocar; se compara con las predicciones después.
3. Se miden y se informan **todas las unidades** (hay 5 cupones B), en orden aleatorio, y cada una **tres veces reconectando** (repetibilidad de la conexión).
4. Un solo parámetro libre al comparar: la εr del FR4. No se «corrige» el largo, el conector ni la malla para que cuadre: cada idea de esas es una hipótesis nueva (sección 5).
5. Reglas con el NanoVNA: nunca `save`; con el usuario delante; se restaura el barrido y el estado del equipo al acabar; calibración `completa_50k_2700M` verificada con la carga al empezar y al terminar.

## 1. Predicciones de la simulación 3D (`cupon/simular_stub.py`, εr 4,5 ± 0,3, tanδ 0,02, cobre PEC, sin conector)

| Stub | modo | εr 4,2 | εr 4,5 | εr 4,8 |
|---|---|---|---|---|
| S80 (85,7 mm) | 1 (λ/4) | 467,5 MHz | 451,9 | 438,6 |
| S80 | 2 (3λ/4) | 1401,3 | 1358,7 | 1319,3 |
| S80 | 3 (5λ/4) | 2333,4 | 2261,7 | 2196,5 |
| S30 (35,7 mm) | 1 | 1066,3 | 1034,0 | 1004,2 |

R en la resonancia (3D, sin pérdida de cobre): S80 2,3–3,3 Ω (sube con el modo), S30 1,1 Ω.

## 2. Predicciones para la medida real (mías, con su probabilidad subjetiva)

La simulación 3D tiene dos diferencias con la placa real que no sé cuantificar bien: la malla de FDTD da un εeff ≈ 3 % alto (las frecuencias salen ≈ 1,5 % bajas respecto a la física) y **el conector SMA de canto añade
unos mm de línea eléctrica** (lo contrario: bajaría las frecuencias, unos 2–8 %). Por eso las predicciones más fuertes son las que no dependen de eso:

| # | Qué | Predicción | P |
|---|---|---|---|
| P1 | **Cociente de modos de S80**: f₂/f₁ y f₃/f₁ | 3,00 ± 0,04 y 5,00 ± 0,08 (no depende de εr ni del largo del lanzamiento si es una línea del mismo tipo) | 70 % |
| P2 | **εr del FR4 con los dos stubs en el modo 1** (`er_fr4_stubs`, que elimina el conector con la recta 1/f frente al largo) | 4,4 (intervalo 4,1–4,7) | 70 % |
| P3 | **Longitud eléctrica del conector** que sale de esa recta | 2–6 mm | 60 % |
| P4 | f₁ de S80 (con el conector y εr real) | 420–475 MHz | 65 % |
| P5 | f₁ de S30 | 960–1070 MHz | 60 % |
| P6 | R en la resonancia de S80, modo 1 | 1–6 Ω (3D 2,5; el cobre y el contacto suman décimas) | 60 % |
| P7 | Dispersión de f entre las 5 unidades (misma conexión) | ≤ 0,5 % | 70 % |
| P8 | Repetibilidad reconectando una misma unidad | ≤ 0,3 % en f | 70 % |

## 3. Pruebas que podrían refutar el método

| # | Fallo del método si… |
|---|---|
| T1 | f₂/f₁ de S80 se sale de 3 ± 0,08 (la línea no es la que creemos, o la calibración falla a esas frecuencias) |
| T2 | la εr del FR4 sale de 3,8–5,0 (JLC da 4,2–4,6 para este grosor) |
| T3 | el lanzamiento sale negativo o > 10 mm |
| T4 | la dispersión entre unidades supera 1 % (entonces una sola unidad no sirve) |
| T5 | el cruce de X por cero no se encuentra o salta entre dos reconexiones más de 1 % |

## 4. Guion de medida (con el usuario delante)

1. Conectar el NanoVNA; `python vna\calibrar_pc.py verificar completa_50k_2700M` con la carga puesta (tolerancias de `hoja_medidas_2G4.md`).
2. Cupón B, **orden aleatorio** de las 5 unidades. En cada una, SMA de **S80** (la serigrafía lo rotula) al cable; el resto de puertos al aire:
   `python vna\medir_antena_pc.py cuponB_u<N>_S80_r<k> completa_50k_2700M --zoom 300 2500`, tres reconexiones (`k` = 1–3). Igual con **S30**.
3. Verificar la calibración a mitad y al final de la sesión.
4. Después (no antes): `resonancias_stub` sobre cada `.s1p`, y `er_fr4_stubs({'B80': f1_S80, 'B30': f1_S30}, 1, largos={'B80': 85.7, 'B30': 35.7})`.
   La rejilla de la calibración es de 2,67 MHz (1010 puntos de 50 kHz a 2,7 GHz): el cruce sale de una recta ajustada, pero un barrido más fino cerca de 450 MHz (una calibración de 400–500 MHz con 101 puntos) daría más precisión.

## 5. Hipótesis nuevas (no son correcciones)

(vacía: se apuntan aquí con su predicción comprobable y se prueban aparte)

## 6. Fe de erratas (solo se añade, con fecha)

- 22-11-2026, antes de medir: solo hay conectores SMA para **una** unidad, así que se mide una sola (nombre `cuponB_u1_*`), no las 5 de la regla 3. Se mantienen las 3 reconexiones por stub. **P7 y T4 (dispersión entre unidades) quedan sin comprobar**; el resto no cambia. Calibración: `cal_latiguillo_B_22-11` (OSL + THRU, 50 kHz–2,7 GHz, 1010 puntos), verificada con la carga: |S11| mediana −44,3 dB, peor −29,8 dB.
