# Placas pedidas a JLC (2,4 GHz) y guion de medida

Pedido de la serie Y52–Y62 de JLCPCB (FR4 de 1,6 mm, HASL, 5 unidades de cada una), estado «Shipped» el 08-11-2026. Los diseños salen de
`salidas/pedido_2G4/<diseño>/` (cada carpeta tiene su `ficha.json` con la clave y los parámetros exactos, el `.kicad_pcb`, los Gerber y
el zip de JLC; `salidas/` es local y no va al repositorio). Se exportaron **antes de añadir el logo**, así que las placas no lo llevan.

## Qué se ha pedido

| Pedido JLC | Placa | Qué es | Simulado (ficha original) | Re-simulado hoy (`verificacion.json`) |
|---|---|---|---|---|
| Y52 | `cupon_A_JLC` | cupón de εr: anillos resonantes de 868 MHz y 2,4 GHz | — | — |
| Y53 | `cupon_B_JLC` | cupón de εr: anillo de 5,8 GHz, líneas abiertas y en L, CPWG, microstrip de 100 Ω | — | — |
| Y54 | `yagi_recta_2dir_2G4` | Yagi con boom, elementos rectos, 2 directores (49 × 100 mm) | 2445 MHz, S11 −19,7 dB, 7,2 dBi, η 75 % | — |
| Y55 | `parche_rectangular_2G4` | parche rectangular (56 × 64 mm) | 2434 MHz, −12,6 dB, 2,9 dBi, η 47 % | 2438 MHz, banda 2417–2458 MHz, −13,1 dB |
| Y56 | `monopolo_sierpinski_2G4` | monopolo de Sierpinski (25 × 43 mm) | 2462 MHz, −59 dB, 2,2 dBi, η 94 % | 2430 MHz, −22,9 dB |
| Y57 | `monopolo_koch_2G4_ajustable` | monopolo de Koch con marcas de corte (16 × 51 mm) | 2328 MHz (largo a propósito, se recorta), −28 dB, 2,0 dBi | 2343 MHz, −13,1 dB a 2441 MHz |
| Y58 | `jpole_koch_2G4` | J-pole de Koch (21 × 79 mm) | 2460 MHz, −12,5 dB, 2,2 dBi, η 86 % | 2460 MHz, banda 2432–2489 MHz, −11,4 dB |
| Y59 | `dipolo_coaxial_2G4` | dipolo con coaxial soldado al centro (48 × 9 mm) | 2464 MHz, −39 dB, 1,8 dBi, η 96 % | — |
| Y62 | `Albatastic_StickTracker` | no es de este proyecto (otra placa del usuario) | — | — |

El meandro y el panel 2×2 estaban preparados en `pedido_2G4/` pero **no se pidieron**. Los diseños **bibanda** y los de 868 MHz de la
campaña de GPU tampoco: la J-pole unida y la IFA bibanda son lo siguiente a fabricar.

## Guion de medida con el NanoVNA

Reglas de `CLAUDE.md` (obligatorias): nunca enviar `save` al equipo, restaurar el barrido y el estado de calibración al terminar, y medir
con el usuario delante (hay que cambiar estándares y conexiones a mano).

1. **Calibración.** `python vna\calibrar_pc.py verificar completa_50k_2700M` (50 kHz–2,7 GHz, OSL + THRU) con la carga puesta. Si falla,
   recalibrar con `calibrar_pc.py` (un paso por ejecución).
2. **Cupones primero (dan la εr).** Medir la resonancia de cada anillo (cupón A: 868 MHz y 2,4 GHz; cupón B: 5,8 GHz) y las líneas
   abiertas y en L (`vna\medir_linea.py`, `vna\medir_antena_pc.py`). Con la frecuencia medida de cada anillo, `cupon/simular_anillo.py
   <anillo>` da la εr que la reproduce (la caché es por radio; probar εr de 4,0 a 4,8). Anotar también tanδ si hay pérdida visible.
3. **Antenas.** Una por una, soldando el SMA con cuidado (que el vivo y la masa queden como en el render del diseño) y con una ferrita en
   el cable (las antenas con masa pequeña usan el cable como parte de la antena). `python vna\medir_antena_pc.py <nombre>
   completa_50k_2700M --zoom 2000 3000` guarda el `.s1p`, el `.json` (bandas a −10 dB) y el `.png`. Medir lejos de objetos metálicos y
   de la mano; repetir con la antena girada 90° para ver cuánto influye el cable.
4. **Comparar.** `python vna\comparar.py comparacion.png simulado.s1p medido.s1p --banda 2400 2483.5` y rellenar una tabla: resonancia
   simulada y medida, desplazamiento en %, S11 en 2441,75 MHz y banda a −10 dB. Si todas se desplazan en el mismo sentido y porcentaje, la
   causa es la εr (no la geometría): `python herramientas/sensibilidad_er.py` da la resonancia simulada con εr de 4,2, 4,5 y 4,8 para
   comparar. Una regla aproximada para una microstrip o un parche: Δf/f ≈ −½·q·Δεr/εr con q ≈ 0,6–1.
5. **Ajustar.** Las que lo permiten (monopolo de Koch con marcas) se recortan por las marcas hasta 2441,75 MHz; la pestaña «Medir» de la
   interfaz lo guía y compara con la medida anterior.
6. **Volver al generador.** Con la εr medida, cambiar el sustrato en `antenas/materiales.py` (hoy 4,5, «pendiente de medir con el
   cupón»), regenerar `antenas/calibracion_estimaciones.json` (`herramientas/calibrar_estimaciones.py`) y volver a simular lo que importe.

## Sensibilidad a la εr (simulada)

`herramientas/sensibilidad_er.py` simula cada diseño pedido con la geometría impresa y εr 4,2, 4,5 y 4,8. Resultados en
`salidas/_barridos/SENS_er_pedido/` (cuando acabe, se resume aquí).
