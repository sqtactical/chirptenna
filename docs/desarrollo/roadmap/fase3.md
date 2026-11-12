# Fase 3 · v0.5: integrar la antena en la PCB de un producto

Antes de nada: [`00_como_trabajar.md`](00_como_trabajar.md). Es el núcleo de la hoja de ruta: hoy el programa
genera una placa que solo es antena; aquí la antena pasa a ser **una esquina de la placa del usuario**.

Orden obligatorio: F3.1 → F3.2 → F3.3. El resto, en cualquier orden después.

## Idea general y vocabulario

- **Placa anfitriona**: la PCB del producto. Tiene un contorno, un plano de masa grande y componentes.
- **Zona de antena**: rectángulo reservado en un borde o esquina, **sin cobre en ninguna capa** salvo la antena.
- **Punto de alimentación**: donde la línea de 50 Ω del producto entrega la señal a la antena.
- Tipos que tienen sentido integrados: `ifa`, `monopolo_meandro`, monopolo recto, `monopolo_koch`, `bucle` y
  (F3.7) antena chip. Dipolos, Yagi, paneles y parches no entran en esta fase.

Decisión de diseño ya tomada: **no se crea un generador nuevo por tipo**. Se envuelve la antena que ya genera
`tipos.generar` y se le cambia la placa: módulo nuevo `antenas/integracion.py`.

---

## F3.1 · Antena integrada en una placa rectangular

- **Quién**: Agente.
- **Archivos**: nuevo `antenas/integracion.py`; `antenas/tipos.py`, `antenas/guia.py`, `gui/app.py`,
  `herramientas/construir_web.py` (`NUCLEO`), `herramientas/comprobar_tipos.py`.
- **Pasos**:
  1. Estudia cómo genera un monopolo su placa: lee en `tipos.py` el generador del monopolo recto y de la IFA y
     apunta qué campos de `Antena` (`antenas/modelo.py`) rellena: capas, contorno, puerto, zona libre, `info`.
  2. Parámetros nuevos, comunes a los tipos integrables (añádelos como `Parametro`, con ayuda en `guia.AYUDAS`):
     - `integrada` (0/1),
     - `placa_x`, `placa_y` [mm]: tamaño de la placa anfitriona,
     - `posicion`: 0 = esquina superior izquierda, 1 = esquina superior derecha, 2 = centrada en el borde superior,
     - `zona_x`, `zona_y` [mm]: zona de antena (0 = automática: lo que ocupa la antena + margen),
     - `margen_zona` [mm]: cobre retirado alrededor del radiador (por defecto 2).
  3. `integracion.integrar(antena, p, sustrato)`:
     a. contorno = rectángulo `placa_x` × `placa_y`;
     b. masa (B.Cu) = todo el rectángulo menos la zona de antena y menos `BORDE_COBRE` del borde;
     c. coloca la antena de forma que su punto de alimentación quede en el borde de la masa y el radiador dentro
        de la zona; si el radiador no cabe, lanza un error claro con la medida que falta;
     d. el conector: de momento se mantiene el SMA o el IPEX en el borde de la masa (sirve para medir el
        prototipo); el punto de alimentación sin conector llega en F3.4;
     e. rellena `info`: `placa_mm`, `zona_antena_mm`, `masa_mm`, `integrada` = True, y `hueco_minimo_mm` /
        `pista_minima_mm` como el tipo original.
  4. `tipos.generar`: si `integrada` = 1 y el tipo está en `integracion.TIPOS`, pasa el resultado por `integrar`.
  5. `tipos.dimensionar`: con `integrada` = 1 la masa ya no es la «mínima» ni λ/4: usa `placa_y − zona_y` como
     largo de masa en el modelo de `largo_masa_monopolo` (lección 15). La IFA depende sobre todo del largo de la
     masa en el eje del brazo: deja un aviso si `placa_x` < λ/4.
  6. Interfaz: en Diseño, interruptor «Antena integrada en una placa» que muestra esos parámetros como básicos.
     Cambiarlos redimensiona (como `masa` y `multibanda`: busca `cambiar_param` en `gui/app.py` y su equivalente
     en `web/app.js`).
  7. Añade `integracion` a `construir_web.NUCLEO` y dos variantes a `comprobar_tipos.py`: IFA y meandro
     integrados en una placa de 30 × 50 mm a 2441,75 MHz, y de 40 × 80 mm a 868 MHz.
- **Prueba**:
  1. `comprobar_tipos.py` con las variantes nuevas: DRC limpio.
  2. Simula la IFA integrada de 30 × 50 mm a 2,4 GHz y compárala con la IFA suelta: debe resonar a ±10 % y con
     η > 60 %. Si no resuena, revisa primero que la zona de antena no tenga masa debajo (mira la vista).
  3. Verificación de malla (F2.3) «estable».
- **Hecho cuando**: las tres pruebas pasan y la vista muestra placa, masa, zona y antena.
- **HECHA (12-11)**: `integracion.py` + `tipos._generar_monopolo`; sin `bucle` (su generador es aparte). Notas: (a) con la esquina izquierda o
  derecha, si el conector no cabe (necesita ~4,5 mm a cada lado de la alimentación) se corre la esquina y la zona crece, en lugar de fallar;
  (b) la IFA de 868 MHz no cabe en 40 × 80 mm (la zona mide ~66 mm de ancho): el caso de `comprobar_tipos` usa 80 × 120 mm; el meandro sí
  cabe en 40 × 80; (c) la estimación de la IFA integrada sale ~12 % baja con el brazo por defecto y `ajustar` la corrige en 2 iteraciones.
  Resultados en GPU (FR4 1,6 mm, 2441,75 MHz, placa 30 × 50): IFA suelta 2430 MHz, banda 2324–2539, 2,18 dBi, η 90 %; integrada 2465 MHz,
  banda 2360–2575, 1,62 dBi, η 88 %, `verificar_malla` «estable» (−2,0 y −4,3 %). `comprobar_tipos`: DRC limpio en los 4 casos nuevos.
  No probado: meandro integrado simulado, ni 868 MHz.

## F3.2 · Ajuste por simulación de la antena integrada

- **Quién**: Agente. **Depende de**: F3.1.
- **Pasos**:
  1. Comprueba que `simulacion.ajustar` funciona con `integrada` = 1: escala el largo del radiador con la malla
     fija y no toca `placa_x`/`placa_y`/`zona_*` (pásalos en `fijos` a `dimensionar`).
  2. Si la zona es demasiado pequeña para llegar a la frecuencia, el ajuste debe pararse y decir cuánta zona
     hace falta, no topar contra el límite en silencio (lección 50).
  3. Barrido de referencia con `barrido.py`: IFA a 2,4 GHz en placas de 20 × 30, 30 × 50, 50 × 80 y 80 × 120 mm.
     Guarda la tabla en `docs/desarrollo/integracion_ifa.md`: f, banda, η, ganancia frente al tamaño de la masa.
  4. Con esa tabla, añade a `consejos.py` el aviso «masa corta: banda y eficiencia reducidas» con el umbral que
     salga de los datos.
- **Hecho cuando**: IFA y meandro integrados se centran en ≤ 3 simulaciones en una placa de 30 × 50 mm a 2,4 GHz
  y de 40 × 80 mm a 868 MHz, o está documentado el tamaño mínimo que lo permite.
- **HECHA en parte (12-11)**: tabla en `docs/desarrollo/integracion_ifa.md`. **IFA**: se centra en 2 simulaciones a 2,4 GHz en 30 × 50 mm
  (3–4 en 25 × 40, 50 × 80 y 80 × 120; no cabe en 20 × 30) y el ancho de banda crece con la placa (124 → 314 MHz); a 868 MHz no cabe en
  40 × 80 y en 80 × 120 hace falta 5 simulaciones. **Meandro: no adapta** (−2,8 a −9,3 dB) en ninguna placa probada; queda sin validar en modo
  integrado. Parar con un mensaje claro si la zona no cabe ya lo hace `integracion.geometria` (dice cuántos mm faltan). `consejos.py` lleva
  tres avisos nuevos (antena integrada, IFA con placa < 0,22 λ de ancho y meandro integrado).

## F3.3 · Exportar para integrar: huella con zona de exclusión

- **Quién**: Agente. **Depende de**: F3.1.
- **Archivos**: `antenas/exportar.py` (`huella_kicad`, `exportar_todo`), LÉEME de exportación (`web_api`/`presentacion`).
- **Pasos**:
  1. Mira qué escribe hoy `huella_kicad` (un `.kicad_mod` con el cobre como pads). La huella integrable necesita:
     a. el radiador como pad(s) custom en F.Cu con número «1» (alimentación);
     b. si el tipo lleva vía a masa (IFA, bucle), un pad pasante «2» en su sitio, para conectarlo a GND;
     c. una **zona de exclusión** que cubra la zona de antena en todas las capas de cobre: en formato KiCad,
        `(zone … (layers "*.Cu") (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed)
        (copperpour not_allowed) (footprints not_allowed)) (polygon (pts …)))` dentro de la huella. Las vías y
        pads propios de la antena deben quedar permitidos: comprueba en KiCad 10 si los pads de la propia huella
        chocan con su keepout; si chocan, recorta la zona alrededor de ellos;
     d. en `F.Fab` o `Dwgs.User`, el borde de la zona y el texto «borde de la placa aquí» en el lado que debe
        coincidir con Edge.Cuts;
     e. el origen de la huella en el punto de alimentación.
  2. Genera un `.kicad_pcb` de prueba que use la huella: placa de 30 × 50 mm, zona de masa GND en las dos caras
     (KiCad debe retirarla sola de la zona de exclusión), y pásale el DRC (`exportar.drc`).
  3. `exportar_todo`: con `integrada` = 1 escribe además `<nombre>_integrar.kicad_mod` y el `.kicad_pcb` de
     ejemplo, y el LÉEME explica los pasos: copiar la huella a la biblioteca, colocarla con su borde sobre
     Edge.Cuts, conectar el pad 1 a la línea de 50 Ω y el 2 a GND, coser la masa con vías junto a la zona.
  4. La web lite debe incluirla en el zip (`web_api.exportar`).
- **Prueba**: DRC del `.kicad_pcb` de ejemplo sin errores; render con `kicad-cli pcb render` y mirar que la masa no
  entra en la zona; `prueba_web.py` en la CI.
- **Hecho cuando**: la huella se coloca en una placa de KiCad y el relleno de masa respeta la zona sin tocar nada
  a mano. Pide al usuario que lo pruebe en un proyecto suyo: es el uso real.
- **HECHA en parte (12-11), falta la prueba del usuario**: `exportar.huella_kicad(..., integrar=True)` → `Antenas.pretty/<nombre>_integrar.kicad_mod`
  (zona de exclusión en F.Cu y B.Cu, pad pasante de la vía de la IFA, lado que debe coincidir con Edge.Cuts en `Dwgs.User`) y
  `exportar.placa_ejemplo_integrada` → `<nombre>_ejemplo_integrada.kicad_pcb` (placa con masa en las dos caras, vías de cosido y la huella en su
  esquina). `exportar_todo` y `web_api.exportar` los incluyen (LÉEME con los pasos, en es/en/fr/de) y la interfaz de escritorio ofrece
  su descarga. DRC con `kicad-cli --refill-zones` (nuevo parámetro `exportar.drc(rellenar=True)`): limpio en la IFA y el monopolo recto
  (`comprobar_tipos` 12/12). **Descubierto**: `kicad-cli pcb drc --refill-zones` **no aplica la zona de exclusión que va dentro de la huella**
  (probado con variantes de capas, nombre y atributos, y con la huella oficial del ESP32: solo la zona a nivel de placa recorta el relleno), así
  que el ejemplo lleva la misma zona también a nivel de placa. Si KiCad con interfaz la aplica o no está **sin comprobar**: ahí queda la
  prueba del usuario (colocar la huella en un proyecto suyo, rellenar las masas con «B» y mirar que no entran en la zona). Fuera:
  la IFA tiene el pad 1 y el 2 sobre el mismo cobre (cortocircuito en continua, el de la propia antena): el LÉEME lo explica.

## F3.4 · Alimentación desde un chip

- **Quién**: Agente. **Depende de**: F3.1.
- **Archivos**: `antenas/conector.py`, `antenas/ajuste.py` (`red_pi`), `antenas/simulacion.py`.
- **Pasos**:
  1. Valor nuevo del parámetro `conector`: «pad de RF» (sin conector). Mira cómo `conector.aplicar_ipex` mueve
     el puerto al pad del IPEX: el pad de RF es igual pero sin huella, con un pad de 0,5 × 0,5 mm (o el ancho de
     la línea) y una vía a masa al lado para la referencia.
  2. Parámetros: `largo_linea` [mm] del pad a la antena y `linea`: 0 = microstrip, 1 = CPWG (coplanar con masa,
     hueco calculado; `cupon/generar_cupon.py` ya sintetiza una CPWG de 50 Ω con valla de vías: reutilízalo).
  3. Con `ajuste` = 1 la red en π va **junto al pad de RF** (así se monta en un producto), no junto a la antena.
  4. Opción «punto de prueba U.FL»: huella de IPEX en derivación con un puente de 0 Ω para elegir chip o conector.
  5. En la simulación el puerto va en el pad (como con IPEX). Comprueba que todas sus coordenadas caen en líneas
     de malla (lección 37).
- **Prueba**: monopolo y IFA con «pad de RF» a 2,4 GHz: mismo resultado que con IPEX ±2 % en frecuencia; DRC limpio.
- **Hecho cuando**: se puede exportar una antena integrada sin ningún conector y simularla.
- **HECHA en parte (12-11)**: valor `conector` = 3 «Pad de RF» (`conector.PAD_RF`): la línea de 50 Ω acaba en un pad (`exportar._pad_rf`:
  rect del ancho de la línea, máscara abierta, y dos pads pasantes de masa a cada lado, a 2 mm del borde); masa mínima 6 mm, ancho mínimo 12 mm
  (las vías de masa del pad lo fijan; con integrada, `tipos` pide a `integracion.geometria` ese semiancho). La red en π va a `y_c = 7 mm`, junto al
  pad. El cobre es idéntico al del SMA, así que la simulación (puerto en el arranque de la línea) es la misma: no se ha simulado aparte.
  DRC limpio con monopolo recto, IFA, IFA integrada (30 × 50) y Koch integrado; `comprobar_tipos` 84/84. **Sin hacer**: línea CPWG
  (`linea` = 1, `largo_linea`) y el punto de prueba U.FL con puente de 0 Ω (pasos 2 y 4); la comparación con IPEX ±2 % no se midió.

## F3.5 · Apilados de 4 capas

- **Quién**: Agente; valores del apilado, comprobarlos en la calculadora de impedancias de JLC (**no fiarse de
  memoria**: pídeselos al usuario o búscalos en la web de JLC y cita la fuente).
- **Archivos**: `antenas/materiales.py`, `antenas/modelo.py`, `antenas/simulacion.py`, `antenas/exportar.py`.
- **Pasos**:
  1. Modelo del sustrato: añade a la entrada del sustrato `capas` = 4 y `h_ref` (distancia de F.Cu a la capa de
     masa In1.Cu, ~0,2 mm en los apilados 7628) además del grosor total.
  2. `ancho_microstrip` con `h_ref`: la línea de 50 Ω sale de ~0,35 mm. Los generadores usan el ancho de 50 Ω del
     sustrato: comprueba que nada asume 2,9 mm (busca números fijos).
  3. Antena: bajo la zona de antena **no hay cobre en ninguna de las 4 capas**; fuera, masa en In1.Cu, In2.Cu y
     B.Cu. `Antena` necesita capas interiores: generaliza el dict de capas (hoy F.Cu/B.Cu) sin romper lo que hay.
  4. Simulación: dieléctrico del grosor total; lámina de masa en z de In1.Cu fuera de la zona de antena; las
     otras masas se pueden fundir con ella (unidas por vías). 2 celdas en z entre F.Cu e In1.Cu (como el flex,
     lección 71) para no hundir el paso de tiempo.
  5. Exportación: `.kicad_pcb` de 4 capas (bloque `layers` y `setup`/`stackup`), zonas en las capas interiores,
     vías de cosido.
- **Prueba**: IFA integrada a 2,4 GHz en 4 capas: resuena a ±5 % de la de 2 capas (el radiador ve el grosor
  total, no `h_ref`); DRC limpio; `FDTD timestep` razonable.
- **Hecho cuando**: se diseña, simula y exporta una antena integrada en 4 capas.

## F3.6 · Importar una placa de KiCad

- **Quién**: Agente. **Depende de**: F3.1.
- **Archivos**: nuevos `antenas/sexp.py` (lector de expresiones S) y `antenas/importar_kicad.py`.
- **Pasos**:
  1. `sexp.leer(texto)` → listas anidadas. Sin dependencias (debe ir en la web). Prueba unitaria con un
     `.kicad_pcb` exportado por el propio programa.
  2. `importar_kicad.placa(ruta)` devuelve: contorno (shapely) uniendo los `gr_line`, `gr_arc`, `gr_rect`,
     `gr_circle` y `gr_poly` de `Edge.Cuts` (también los de dentro de huellas); cobre por capa (zonas con
     `filled_polygon`, pistas con su ancho, pads); taladros; grosor (`general/thickness`).
  3. Arcos: KiCad da inicio, punto medio y fin; discretiza a ≤ 0,1 mm de flecha.
  4. Modo integrada con placa importada: `placa_x/placa_y` se sustituyen por el contorno importado; el usuario
     elige la esquina o marca la zona; el cobre importado dentro de la zona se avisa («tienes cobre en la zona
     de antena») y fuera se usa como masa en la simulación (simplificado: unión de todo el cobre, con huecos
     < 1 mm cerrados para no afinar la malla; lección 9).
  5. Interfaz: botón «Importar placa (.kicad_pcb)» en el modo integrado; la vista dibuja el cobre importado en gris.
- **Prueba**: importar una placa exportada por el programa y comprobar que contorno y área de cobre coinciden
  (±1 %); importar una placa real del usuario (pídesela; **no uses `placas/`**, son Gerber, no KiCad).
- **Hecho cuando**: una placa real se importa, se ve y se simula con la antena en su esquina.

## F3.7 · Entorno: carcasa, batería, mano

- **Quién**: Agente.
- **Archivos**: `antenas/modelo.py` (`Antena.entorno`), `antenas/simulacion.py`, `gui/app.py`.
- **Pasos**:
  1. `Antena.entorno`: lista de bloques `{'tipo': 'dielectrico'|'metal', 'caja': (x0,y0,z0,x1,y1,z1), 'er':…,
     'tand':…, 'nombre':…}`.
  2. Simulación: `AddMaterial`/`AddMetal` + `AddBox` con prioridad menor que el cobre; líneas de malla en sus
     caras; la caja de aire debe contenerlos.
  3. Predefinidos en la interfaz: carcasa de ABS (εr 2,8, tanδ 0,01, 1,5 mm de pared a 1 mm de la placa),
     batería (bloque metálico), mano (εr ~30, σ ~1 S/m, bloque de 80 × 40 × 20 mm a 5 mm).
  4. Resultado: desplazamiento de frecuencia y cambio de η respecto a la antena sola, en la pestaña Simulación.
- **Prueba**: bloque de εr 1 y tanδ 0 → resultado idéntico al de sin bloque (±0,2 %). Carcasa de ABS sobre un
  monopolo de 2,4 GHz → la frecuencia **baja** (1–5 %). Si sube, hay un error.
- **Hecho cuando**: las dos pruebas pasan y el aviso sale en `consejos`.
- **HECHA (12-11)**: `Antena.entorno` + `antenas/entorno.py` (predefinidos `carcasa`, `bateria`, `mano`), soporte en `simulacion.simular` (material o PEC,
  caras en la malla, dominio ampliado, clave de la caché) y `simulacion.efecto_entorno` (lo usa `simular_cli` con `entorno` en el trabajo y la
  interfaz: selector «Entorno» en Simulación y un aviso con el cambio de f, η y ganancia). **La prueba del bloque de εr 1 no se puede hacer con la
  antena sola**: añadir un bloque añade líneas de malla y mueve la frecuencia un ~2 % por sí solo (monopolo de 2,4 GHz, +2,0 % con un bloque de
  aire 5 mm sobre la placa), así que `efecto_entorno` compara dos simulaciones con la MISMA malla: una con los bloques y otra con ellos convertidos
  en aire (`entorno.neutro`). Con esa comparación el bloque de εr 1 es idéntico por construcción. Resultados (monopolo recto 2,4 GHz, FR4, GPU, paso
  0,5 mm): **carcasa de ABS −6,6 %** (η 100 %), **mano −3,7 %** (η de 97 a 23 %, ganancia de 2,9 a −1,3 dBi), **batería detrás +6,0 %** (η igual). La carcasa
  queda algo por encima del 1–5 % de la guía (dos láminas de 1,5 mm, a 1 mm, que sobresalen 3 mm); baja, como debe. Sin simular: otras antenas,
  otras frecuencias ni la IFA integrada con carcasa. `consejos.py` avisa del entorno en monopolos, bucle, dipolos y J-pole.

## F3.8 · Antenas chip

- **Quién**: Agente; qué modelos, **decisión del usuario**.
- **Pasos**:
  1. Tipo `antena_chip`: huella del fabricante, zona libre y red de adaptación de la hoja de datos (pídele al
     usuario el modelo y su hoja; no inventes dimensiones).
  2. Simulación: modelo simplificado (bloque cerámico de εr alta con el electrodo) solo si reproduce la hoja de
     datos a ±5 %; si no, el tipo se queda en «solo huella y reglas» y se dice claro.
- **Hecho cuando**: la huella pasa el DRC y el estado refleja si hay simulación fiable.

## F3.9 · Tolerancias de fabricación

- **Quién**: Agente.
- **Archivos**: `herramientas/sensibilidad_er.py` (ya existe: léelo primero), `antenas/simular_cli.py`, `gui/app.py`.
- **Pasos**:
  1. Función `simulacion.tolerancias(...)`: simula el diseño con εr ±5 %, grosor ±10 % y cobre ±0,05 mm
     (`buffer` de las capas), una variable cada vez, malla fija: 6 simulaciones sin NF2FF.
  2. Resultado: desplazamiento de frecuencia por variable, suma cuadrática, y «banda que sobrevive» = intersección
     de las bandas a −10 dB de los 7 casos frente a la banda objetivo.
  3. Interfaz: botón «Analizar tolerancias» en Simulación con una tabla y el veredicto: «cubre la banda con
     margen», «justo» o «no cubre: necesita ajuste tras fabricar».
- **Prueba**: monopolo recto a 2,4 GHz (banda ancha) → «cubre»; parche rectangular (banda ~36 MHz) → «no cubre».
- **Hecho cuando**: las dos pruebas dan lo esperado.
- **HECHA (12-11)**: `simulacion.tolerancias` (6 simulaciones sin diagrama, malla fija del paso de la nominal; εr ±5 %, h ±10 %, `buffer` ±0,05 mm
  de las dos caras), `simular_cli` (`tolerancias` + `banda_MHz` en el trabajo) y casilla «Analizar tolerancias» en Simulación (no es un botón: va
  como «Verificar con otra malla», con el resultado en el aviso y el veredicto). Veredicto: `cubre` si la banda que sobrevive (intersección de las 7
  bandas) contiene la objetivo; `justo` si la nominal la cubre y la que sobrevive no; `no_cubre` en otro caso. **Pruebas (2,4 GHz, banda 2400–2483,5
  MHz, GPU)**: monopolo recto → `cubre` (εr ±5 % mueve ±0,8 %, grosor ±0,2 %, cobre +2,0/+0,2 %; suma cuadrática 2,2 %; sobrevive 2276–2512 MHz);
  parche rectangular → `no_cubre` (εr ±5 % mueve +2,5/−2,3 %, grosor ±0,4 %, cobre ±0,07 %; suma 2,5 %; la banda nominal 2424–2469 MHz ni cubre la
  objetivo y la intersección queda vacía). Al parche le basta la εr para salirse de la banda. Sin simular: otros tipos ni 868 MHz.

## F3.10 · Reglas de integración

- **Quién**: Agente. **Depende de**: F3.2 y F3.7 (los umbrales salen de sus datos, no de memoria).
- **Pasos**: en `consejos.py`, categoría nueva «integración»: masa mínima, nada de cobre ni componentes en la
  zona, vías de cosido cada λ/20 en el borde de la masa, distancia a batería y blindajes, línea de 50 Ω corta y
  con masa continua debajo, red en π junto al chip. Sección nueva en `MANUAL.md` / `MANUAL.en.md`: «Integrar la
  antena en tu placa», con el caso de un nodo LoRa de 868 MHz en 40 × 80 mm.
- **Hecho cuando**: los consejos salen en la interfaz con `integrada` = 1 y el manual tiene el caso completo.
- **HECHA (12-11)**: `consejos.consejos` añade cinco reglas de categoría «integración» (icono propio en escritorio y web) cuando `info['integrada']`; el
  cosido (λ/20) y la distancia (λ/10) salen de la frecuencia. Manual: capítulo 14 en `MANUAL.md` y `MANUAL.en.md` (el glosario pasa a 15). El caso de
  868 MHz en 40 × 80 mm **no sale** (la IFA necesita ~66 mm de zona; mínimo ~80 × 100 mm, meandro no adapta): el manual lo cuenta y da las salidas (2,4 GHz,
  antena externa, chip pendiente de F3.8). Test `test_consejos_integracion`; no se ha mirado la interfaz con una antena integrada en el navegador.
