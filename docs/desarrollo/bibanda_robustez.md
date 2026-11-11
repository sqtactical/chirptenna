# Robustez de la bibanda frente a la malla (F2.5, 11-11-2026)

`herramientas/robustez_bibanda.py` simula lo que genera la aplicación (`multibanda` = 1, 868 MHz + 2,4 GHz, FR4 de 1,6 mm,
GPU, banda ancha 0,45–3,8 ×) con tres pasos de malla y mide el peor S11 en 863–870 MHz y en 2400–2483,5 MHz. **Criterio:**
un diseño vale si queda ≤ −8 dB en las dos bandas con los tres pasos. Resultados crudos en `salidas/_barridos/ROB_ifa/`,
`ROB_jpole/` y `ROB_ifa_prueba/` (locales).

**Conclusión: ningún punto de las rejillas cumple.** El «−11 dB en las dos bandas» de las pruebas del 07-11 era un punto afortunado
de la malla (lección 70), y moviendo las constantes no aparece uno robusto.

## IFA con segunda rama (`IFA_H2` × `IFA_X_BRAZO`; pasos 0,7 / 1,0 / 1,15 mm)

Cada celda: peor S11 (dB) de la banda baja / alta con ese paso. El actual es H2 0,6 y X 1,17.

| IFA_H2 | IFA_X_BRAZO | paso 0.7 mm | paso 1.0 mm | paso 1.15 mm | Peor |
|---|---|---|---|---|---|
| 0.5 | 1.1 | -6.2 / -6.7 | -6 / -5.4 | -5.5 / -2.5 | **-2.5** |
| 0.5 | 1.14 | -8.1 / -7.6 | -6.9 / -5.4 | -13 / -5.8 | **-5.4** |
| 0.5 | 1.2 | -13.1 / -7.3 | -11.2 / -5 | -11.1 / -2.2 | **-2.2** |
| 0.5 | 1.25 | -10.7 / -6.4 | -7.1 / -2.3 | -6.5 / -2.5 | **-2.3** |
| 0.6 | 1.1 | -6.1 / -9.9 | -5.8 / -10.9 | -5.2 / -5.8 | **-5.2** |
| 0.6 | 1.14 | -7.9 / -7.2 | -6.8 / -10.3 | -12.6 / -6.9 | **-6.8** |
| 0.6 | 1.2 | -12.9 / -6.5 | -11 / -9.5 | -10.8 / -4.1 | **-4.1** |
| 0.6 | 1.25 | -10.6 / -7.1 | -7.1 / -4.3 | -6.5 / -2.4 | **-2.4** |
| 0.7 | 1.1 | -6 / -3.2 | -5.7 / -3.2 | -5.1 / -2.1 | **-2.1** |
| 0.7 | 1.14 | -7.9 / -2.7 | -6.6 / -3 | -12.7 / -7.4 | **-2.7** |
| 0.7 | 1.2 | -12.7 / -2.5 | -10.8 / -3 | -10.3 / -2.1 | **-2.1** |
| 0.7 | 1.25 | -10.5 / -3 | -6.8 / -5.1 | -6.6 / -2.8 | **-2.8** |

Punto actual (H2 0,6, X 1,17; `ROB_ifa_prueba`): 0,7 mm → −10,7 / −6,9; 1,0 mm → −14,6 / −10,8; 1,15 mm → −9,7 / −5,3 (peor −5,3 dB).

## J-pole unida (`JPOLE_SEP2` × `JPOLE_TOMA2`; pasos 0,9 / 1,13 / 1,3 mm)

| JPOLE_SEP2 | JPOLE_TOMA2 | paso 0.9 mm | paso 1.13 mm | paso 1.3 mm | Peor |
|---|---|---|---|---|---|
| 3 | 0.2 | -2.3 / -0.5 | -9.7 / -7.4 | -5.3 / -1.2 | **-0.5** |
| 3 | 0.25 | -2.4 / -0.5 | -9.2 / -10.1 | -5.3 / -0.7 | **-0.5** |
| 3 | 0.3 | -2.4 / -0.5 | -8.6 / -8.4 | -5.4 / -0.6 | **-0.5** |
| 4.5 | 0.2 | -5 / -4.6 | -2 / -1 | -4.7 / -1.2 | **-1** |
| 4.5 | 0.25 | -4.8 / -4.1 | -2.1 / -1.1 | -4.7 / -0.6 | **-0.6** |
| 4.5 | 0.3 | -4.5 / -3.6 | -2.1 / -1.2 | -7.6 / -9.8 | **-1.2** |

El actual es SEP2 3,0 y TOMA2 0,25: −9,2 / −10,1 con el paso 1,13 mm (el de la aplicación), pero −2,4 / −0,5 con 0,9 mm y −5,3 / −0,7 con 1,3 mm.

## Qué significa

- Con la misma geometría, el S11 de la banda alta cambia hasta 15 dB al mover un 15 % el paso de la malla. El diseño no depende de las
  constantes probadas: depende de cómo caen las líneas de la malla sobre sus bordes.
- No se cambian las constantes de `bibanda.py` (ninguna es mejor que la actual en robustez).
- Opciones (decisión del usuario): (a) **quitar `multibanda` de la J-pole y la IFA en la interfaz** (las herramientas y `bibanda.py`
  se quedan) y dejar el Sierpinski de dos bandas, que sí está simulado en las dos bandas con S11 ≤ −11 dB; (b) dejarlas con el aviso grave actual y la
  verificación de malla de F2.3 (siempre activa con dos bandas), que ya avisa «sensible»; (c) explorar otra topología (diplexor, idea I3).
