# Estado real de Chirptenna

*Archivo generado por `herramientas/estado_real.py` a partir de `antenas/problemas.ESTADO`; no se edita a mano.*

## Qué está medido

- Ninguna placa fabricada se ha medido todavía. Los cupones de εr (`cupon/`) y las primeras antenas de 2,4 GHz están pedidos a JLCPCB; hasta que lleguen y se midan con el NanoVNA, todo lo de abajo es **simulación**.
- Lo que sí está medido: el NanoVNA (calibración OSL + THRU, `vna/`) y el latiguillo; nada del generador.

## Tipos de antena

27 tipos: **17 validados en simulación**, 5 pendientes de validación y 5 que no funcionan. «Validada» significa que openEMS la da adaptada (S11 ≤ −10 dB en la banda) y radiando; no significa medida.

### Validados en simulación

| Tipo | Clave | Estado |
|---|---|---|
| Antena F invertida (J-pole en F) | `ifa` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Antena PIFA (F invertida plana) | `pifa` | Validada en simulación (868 MHz, 2,4 y 5,8 GHz) |
| Colineal de dipolos en serie (línea microstrip) | `colineal_dipolos` | Validada en simulación (2,4 GHz) |
| Dipolo bowtie (pajarita) | `dipolo_bowtie` | Validada en simulación (bowtie y bowtie de Sierpinski; de 868 MHz a 5,8 GHz) |
| Dipolo con manga (sleeve) | `dipolo_sleeve` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Dipolo impreso (recto o de Koch) | `dipolo` | Validada en simulación (recto y Koch; de 868 MHz a 5,8 GHz) |
| J-pole de Koch (fractal) | `jpole_koch` | Validada en simulación (868 MHz y 1,2 GHz; 2,4 GHz casi) |
| J-pole impresa | `jpole` | Validada en simulación (de 868 MHz a 2,4 GHz) |
| Monopolo de Koch | `monopolo_koch` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Monopolo de Sierpinski | `monopolo_sierpinski` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Monopolo de punta de flecha de Sierpinski | `monopolo_flecha` | Validada en simulación a 2,4 GHz con la iteración 1 (las iteraciones 2 y 3 no adaptan) |
| Monopolo en meandro (referencia compacta) | `monopolo_meandro` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Monopolo recto (referencia) | `monopolo_recto` | Validada en simulación (de 868 MHz a 5,8 GHz) |
| Panel de dipolos 2×2 / 4×4 sobre reflector (directivo) | `panel_dipolos` | Validada en simulación (2×2 con dipolos o Sierpinski, 2,4 GHz) |
| Parche rectangular (referencia) | `parche_rectangular` | Validada en simulación (banda estrecha; a 5,8 GHz con ranura) |
| Vivaldi antipodal | `vivaldi` | Validada en simulación (2,4 y 5,8 GHz) |
| Yagi impresa de doble cara con boom (directiva) | `yagi_boom` | Validada en simulación con elementos rectos (868 MHz, 2,4 y 5,8 GHz) |

### Pendientes de validación

| Tipo | Clave | Estado |
|---|---|---|
| Array de parches 2×2 / 4×4 (directivo) | `array_parches` | Pendiente de validación |
| Bucle impreso (pequeño, con condensador y red en π) | `bucle` | Simulado (868 MHz y 2,4 GHz): adapta con la red en L calculada; η ~40–50 %, banda estrecha |
| Colineal Franklin (horquillas) | `colineal_franklin` | Adapta, pero con poca banda y poca ganancia |
| Parche con ranura en U | `parche_ranura` | Sin testear ni validar |
| Parche de Minkowski | `parche_minkowski` | Pendiente de validación (eficiencia baja en FR4) |

### No funcionan

| Tipo | Clave | Estado |
|---|---|---|
| Colineal coaxial impresa (COCO) | `colineal_coco` | No adapta bien ni radia con eficiencia en FR4 (−4 dB, η 24–35 %) |
| Monopolo de Hilbert | `monopolo_hilbert` | No funciona sin red en π |
| Parche con parásito acoplado (alternativa plana al apilado) | `parche_apilado` | No adapta en simulación (−0,6 dB, η 7 %) |
| Parche de polarización circular (esquinas cortadas) | `parche_circular` | No adapta ni da polarización circular en simulación (−4 a −6 dB, razón axial ≥ 6 dB) |
| Quasi-Yagi impresa con dipolo de Koch (directiva) | `yagi_koch` | No funciona: radia hacia atrás |

## Límites conocidos

- **Unión soldada de la colineal modular**: no está simulada (la cadena se simula como una pieza) ni medida; la cola de milano no se ha probado en una placa real y no se ha consultado a JLC el ancho mínimo de las ranuras fresadas.
- **Colineal modular a 868 MHz**: sin centrar (resuena a 1034 MHz); solo está centrada a 2,4 GHz.
- **Red de adaptación en π**: −38 dB por circuito frente a −10 dB en la FDTD con los mismos componentes (F4.1 sin resolver). Se fía más de la FDTD.
- **Bibandas** (`multibanda` = 1 en J-pole e IFA): dependen de la malla; ninguna cumple −8 dB en las dos bandas con tres pasos de malla distintos.
- **Importación de placas KiCad** y **zona de exclusión de la huella integrada**: sin probar con una placa real ni con KiCad con interfaz.
- **εr del FR4 de 4 capas** (4,4 de la calculadora de JLC, la web de JLC da 4,6): por comprobar.
- **Parches**: la banda de ~36 MHz en FR4 no cubre la ISM de 2,4 GHz; la eficiencia en FR4 ronda el 47 %.
- **Eficiencia y ganancia de la colineal modular en FR4**: no suben con más de 4 módulos (en RO4350B sí).
- **Antena de chip** (F3.8): sin modelo del fabricante; no se ha simulado.

## Cómo se comprueba

- `python -m pytest pruebas` (sin openEMS, < 5 s): geometría, exportación, tamaños iniciales, idiomas, método de momentos de hilos, optimización, y `pruebas/test_verdad.py` (el generador frente a fórmulas de libro: microstrip de Hammerstad, dipolo, monopolo y parche por el modelo de la cavidad).
- `python herramientas/comprobar_tipos.py` (~2 min, KiCad): genera y exporta los tipos a 868 y 2441,75 MHz y pasa el DRC. Va en la CI.
- `python herramientas/verdad.py` (openEMS, minutos): simula un dipolo, un monopolo y un parche y los compara con el libro. **No** va en la CI; se pasa antes de una release.
- `herramientas/validar_lote`, `barrido.py` y `campana.py`: las simulaciones de validación de cada tipo; los resultados están en `docs/desarrollo/barridos_gpu.md` y `resultados_07-11.md`.
- La simulación nunca devuelve un resultado analítico si falla: `simular` lanza el error, y los avisos (η < 10 %, S11 plano, malla sensible) salen en el resultado.
