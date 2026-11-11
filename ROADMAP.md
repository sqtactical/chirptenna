# Chirptenna · hoja de ruta

Plan a medio plazo del proyecto (escrito el 11-11-2026, tras la v0.3.0-alpha). El estado del día a día está en
[`RETOMAR.md`](RETOMAR.md); lo estable (estructura, reglas, lecciones) en [`CLAUDE.md`](CLAUDE.md). Este archivo dice
**hacia dónde va el proyecto y en qué orden**: al terminar una tarea de aquí, márcala (`[x]`) y anota la fecha.

## Objetivo

Que Chirptenna sirva para **integrar una antena en la PCB de un producto real** (tracker, nodo LoRa, mando,
sensor), no solo para generar antenas sueltas con su conector. Eso exige tres cosas, por este orden:

1. **Confianza**: que lo simulado coincida con lo medido (hoy todo está validado solo en simulación).
2. **Integración**: que la antena se diseñe con la placa, la masa y el entorno del producto, y se lleve a KiCad
   como parte de ese diseño.
3. **Adaptación**: que el programa calcule y simule la red de adaptación de cualquier antena, porque dentro de un
   producto ninguna antena queda en 50 Ω sin ella.

## Principios

- **Medir antes de ampliar.** No se añaden tipos nuevos hasta cerrar la fase 1. Un tipo medido vale más que diez
  simulados.
- **Menos tipos, mejor hechos.** Cada tipo cuesta galería, avisos, tres traducciones, dos README y manual. Lo que
  no funciona se aparta de la vista.
- **La malla manda.** Ningún resultado se da por bueno con un solo paso de malla si el tipo es sensible (bibanda,
  panel, arrays).
- **Honestidad en los estados.** «Validada» significa simulada; «Medida» será un estado aparte con su gráfica.

## Guías paso a paso

Este archivo es el índice. Cada tarea está desarrollada (quién la hace, archivos, pasos, cómo probarla y cuándo
está hecha) en `docs/desarrollo/roadmap/`:

| Guía | Contenido |
|---|---|
| [`00_como_trabajar.md`](docs/desarrollo/roadmap/00_como_trabajar.md) | **Leer primero**: comandos, reglas, definición de «hecho», informe y cuándo preguntar |
| [`fase1.md`](docs/desarrollo/roadmap/fase1.md) | F1.1–F1.11: predicciones, cupones y εr, medir antenas, comparar, malla, recalibrar, estado «Medida» |
| [`fase2.md`](docs/desarrollo/roadmap/fase2.md) | F2.1–F2.10: galería, verificación de malla, panel, bibanda, bucle, segundo pedido, GPU, pruebas |
| [`fase3.md`](docs/desarrollo/roadmap/fase3.md) | F3.1–F3.10: antena integrada, huella con zona de exclusión, pad de RF, 4 capas, importar KiCad, entorno, tolerancias |
| [`fase4.md`](docs/desarrollo/roadmap/fase4.md) | F4.1–F4.6: componentes concentrados, adaptación automática, analizadores, informe; lista de la v1.0 |
| [`ideas.md`](docs/desarrollo/roadmap/ideas.md) | I1–I15: primer experimento barato de cada idea y criterio para seguir o abandonar |

Sin hardware se pueden adelantar ya: F1.1, F1.2 y F2.2–F2.6.

## Fase 1 · Validación en hardware (al llegar el pedido de JLC)

Pedido en camino (2,4 GHz, FR4 1,6 mm): cupones A y B, meandro, Sierpinski, Koch ajustable, J-pole de Koch,
parche, dipolo con coaxial y Yagi recta de 2 directores.

- [ ] **εr real del FR4.** Medir los anillos y líneas de los cupones A y B con el NanoVNA; ajustar εr y tanδ en la
  simulación del cupón (`cupon/simular_anillo.py`) hasta casar las resonancias. Resultado: εr y tanδ por frecuencia
  (868 MHz, 2,4 GHz; 5,8 GHz necesita otro analizador) en `materiales.SUSTRATOS`.
- [x] (11-11, tareas F1.1 y F1.2) **Predicciones escritas** (`docs/desarrollo/medidas/predicciones_2G4.md`) y **herramienta
  `herramientas/comparar_medida.py`** probada con una medida sintética (desviación de 3 % medida como 3,0 %).
- [ ] **Medir las seis antenas** (Y54–Y59; el meandro y el panel no se pidieron) (S11, banda a −10 dB, R/X) con `vna/medir_antena_pc.py` y guardar los `.s1p`.
- [ ] **Comparar simulación y medida** tipo por tipo: desviación de frecuencia, de banda y de profundidad de S11.
  Herramienta nueva `herramientas/comparar_medida.py <diseño> <s1p>`: superpone las curvas y da los tres números.
- [ ] **Fijar la malla de referencia**: repetir cada simulación con 2–3 pasos y quedarse con el criterio que más se
  acerque a la medida. Documentarlo como regla de `simulacion.simular`.
- [ ] **Recalibrar** `calibracion_estimaciones.json` con la εr medida y volver a simular los diseños por defecto.
- [ ] **Estado «Medida»** en `problemas.ESTADO` y en la galería, con la gráfica medida frente a simulada visible
  en la pestaña Simulación.
- [ ] **Probar el flujo de ajuste real**: marcas de corte y puentes del Koch ajustable, y la red en π de un
  monopolo, siguiendo el asistente. Apuntar lo que confunda en la interfaz.
- [ ] **Medida de alcance o ganancia relativa** (opcional): dos placas iguales enfrentadas y S21, o RSSI con un
  módulo LoRa/BLE, para comprobar la eficiencia de forma aproximada.

Criterio de salida: frecuencia simulada a ≤ 2 % de la medida en al menos 5 de los 7 tipos, o la causa de la
diferencia identificada.

## Fase 2 · v0.4: consolidar

- [ ] **Subir lo pendiente**: commits locales de PTFE/flex/hélice y del bucle.
- [x] (11-11, F2.2) **Podar la galería**: grupo «Experimental» plegado por defecto con lo que no funciona o es frágil (parches en
  FR4 fuera de 5,8 GHz, Minkowski, circular, ranura en U, apilado, array, COCO, Franklin, Hilbert, flecha it. 3).
  Sigue disponible, pero no es lo primero que ve un usuario nuevo.
- [x] (11-11, F2.3) **Comprobación de malla automática**: opción «Verificar con otra malla» en Simulación (y obligatoria en
  bibanda): repite con el paso ±15 % y avisa si la frecuencia cambia > 2 % o S11 > 3 dB.
- [ ] **Panel calibrado por banda** (`K_MALLA_FINA_PANEL` solo vale a 2,4 GHz; a 5,8 GHz resuena un 17 % baja).
- [ ] **Bibanda robusta**: J-pole unida e IFA de dos ramas rediseñadas para que aguanten el cambio de malla, o
  retiradas de la interfaz si no se consigue. El Sierpinski de dos bandas es la referencia.
- [ ] **Bucle**: calibrar el anillo redondo, simular en 0,8 mm y que `ajustar` calcule solo la red en L a partir de
  la Z sin la línea (hoy es un script aparte).
- [ ] **Yagi comercial B**: cerrar el modelo cuando haya cotas con calibre, grosor del FR4 y foto macro.
- [ ] **Segundo pedido a JLC**: 868 MHz (monopolo, Koch, IFA, J-pole recta), Sierpinski de dos bandas, bucle con su
  red, y una antena **integrada en una placa con forma de producto** (ver fase 3) para validar ese flujo.
- [ ] **Instalador con GPU opcional** (SHA-256 fijado) y prueba en otra GPU.
- [ ] **Deuda**: tests unitarios de `geometria`, `ajuste.redes_l` y `tipos.dimensionar` (hoy solo hay pruebas de
  generación y de interfaz); partir `gui/app.py` por pestañas.

## Fase 3 · v0.5: integración en la PCB de un producto

Es el núcleo de la hoja de ruta. Hoy el programa genera una placa cuya única función es ser antena; aquí pasa a
diseñar la antena **dentro** de otra placa.

- [ ] **Modo «antena integrada»**: el usuario da el contorno de su placa (rectángulo con medidas, o importado), la
  esquina o el borde donde va la antena y el tamaño de la zona reservada. El programa elige los tipos que caben
  (IFA, meandro, monopolo, bucle, antena chip) y dimensiona con **la masa real del producto**, no con la mínima.
- [ ] **Importar una placa de KiCad** (`.kicad_pcb`): leer `Edge.Cuts`, las zonas de masa y las zonas prohibidas;
  mostrarla en la vista y usarla como plano de masa en la simulación.
- [ ] **Exportar para integrar**: además de la placa suelta, una **huella con zona de exclusión** (keepout en
  todas las capas bajo el radiador, masa retirada, vías de cosido en el borde de la masa) y el punto de
  alimentación con net, lista para colocar en el diseño del usuario. Guía «cómo pegarla en tu placa».
- [ ] **Alimentación desde un chip, no desde un SMA**: línea de 50 Ω (microstrip o CPWG, calculada con el apilado
  elegido) desde un pad de RF hasta la antena, con la red en π junto al chip y punto de prueba U.FL opcional.
- [ ] **Apilados de 4 capas de JLC** (JLC04161H-7628 y similares): la microstrip de 50 Ω pasa de 2,9 mm a ~0,35 mm
  porque la masa está a 0,2 mm. Imprescindible para placas de producto.
- [ ] **Entorno**: bloques dieléctricos y metálicos en la simulación (carcasa de plástico, batería, pantalla,
  blindaje, mano). Aviso de cuánto se desplaza la frecuencia con cada uno.
- [ ] **Reglas de integración** en `consejos`: distancia mínima a la batería y a los blindajes, masa bajo el
  radiador, cosido de vías, por dónde no pasar pistas.
- [ ] **Antenas chip y cerámicas**: tipo nuevo con la huella, la zona libre y la red recomendada por el fabricante
  (Johanson 2450AT, etc.); modelo simplificado para la simulación.
- [ ] **Tolerancias de fabricación**: barrido automático de εr ±5 %, grosor ±10 % y sobreataque del cobre; el
  resultado es el margen de banda que sobrevive a la fabricación.

## Fase 4 · v0.6: adaptación y medida

- [ ] **Red de adaptación para cualquier tipo**: componentes concentrados en la simulación (ya existen para el
  condensador del bucle), valores E24/E96 con sus parásitos y Q reales, y S11 resultante antes de fabricar.
- [ ] **Asistente de adaptación con medida**: de un `.s1p` medido a la red (L, π o T) con valores comerciales,
  sensibilidad a la tolerancia de los componentes y lista de piezas (LCSC).
- [ ] **De-embedding de la línea** en la medida (hoy solo en la simulación).
- [ ] **Más analizadores**: LiteVNA y NanoVNA V2 (hasta 6 GHz), para medir 5,8 GHz.
- [ ] **Informe del diseño en PDF**: geometría, S11, diagrama, ganancia, eficiencia, tolerancias y lista de piezas.
- [ ] **Exportar el diagrama** 3D y los cortes en formatos de intercambio (CSV, y el formato de antena de
  herramientas de cobertura de radio).

## Fase 5 · v1.0

- [ ] 8–10 tipos **medidos** en 868 MHz y 2,4 GHz, con sus `.s1p` publicados.
- [ ] Al menos **dos antenas integradas en placas de producto** fabricadas y medidas.
- [ ] Traducciones revisadas por hablantes nativos.
- [ ] Manual con un caso completo: «antena para un nodo LoRa de 868 MHz en una placa de 30 × 50 mm».
- [ ] **Biblioteca pública de diseños medidos** (carpeta o repositorio aparte, licencia CC BY-NC de los diseños).

## Ideas a más largo plazo (sin orden)

| Idea | Para qué | Coste |
|---|---|---|
| Optimizador automático de varios parámetros (S11 + ganancia + tamaño) con GPU | Dejar de barrer a mano | Alto |
| Parche de GPS de verdad: sonda coaxial con posición variable y razón axial en los resultados | GPS/Iridium con polarización circular | Medio |
| Diplexor impreso 868 MHz / 2,4 GHz | Dos antenas buenas en un solo conector, en vez de una bibanda frágil | Medio |
| Diversidad y MIMO: dos antenas en la misma placa, aislamiento (S21) y correlación | Wi-Fi, LTE | Alto |
| Arrays 2×1, 3×3 y 1×N, con y sin reflector | Más ganancia a medida | Medio |
| Colineal con elementos bowtie y colineales acortadas con fractales | Menos largo a 868 MHz | Medio |
| Hélice de modo normal a 868 MHz y Yagi plana de una capa en flex | Sacar partido al flex | Bajo |
| Hélice cuadrifilar con su red de 90° | GPS en flex | Alto |
| Bandas nuevas: 433 MHz, LTE-M/NB-IoT (700–960 MHz), UWB (6–8 GHz) | Más productos | Medio |
| Antenas para NFC (bobinas de 13,56 MHz con su sintonía) | Otro uso muy pedido en PCB | Medio |
| Importar una antena desde Gerber o DXF y simularla | Analizar antenas de terceros | Medio |
| Estimación de SAR y de potencia radiada frente a los límites (ETSI, FCC) | Certificación | Alto |
| Complemento para KiCad (botón «insertar antena») | Integración directa | Alto |
| Simulación en Linux y macOS | Más usuarios | Medio |
| Simulación en la nube o en el navegador para la versión web | Web lite con resultados | Alto |

## Lo que no se va a hacer por ahora

- Más tipos fractales por el mero hecho de serlo: Koch no acorta a 868 MHz e Hilbert no adapta; el único fractal
  con una ventaja clara es el Sierpinski de dos bandas.
- Forzar los parches en FR4 fuera de 5,8 GHz: los limita la pérdida del material, no el diseño.
- Añadir tipos antes de cerrar la fase 1.
