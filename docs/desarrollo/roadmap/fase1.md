# Fase 1 · Validación en hardware

Antes de nada: [`00_como_trabajar.md`](00_como_trabajar.md). Objetivo de la fase: saber cuánto se parece la
simulación a la realidad y dejar el programa calibrado con la εr medida.

Material: pedido de JLC de 2,4 GHz (FR4 1,6 mm). Lista y diseños en `docs/desarrollo/placas_pedidas_2G4.md` y
`salidas/pedido_2G4/` (local). NanoVNA-H (hasta 2,7 GHz con la calibración `completa_50k_2700M`).

Las tareas F1.1 y F1.2 se pueden hacer **antes** de que lleguen las placas.

---

## F1.1 · Tabla de predicciones

- **Quién**: Agente. **Depende de**: nada.
- **Para qué**: apuntar lo que predice la simulación antes de medir, para no ajustar el relato después.
- **Pasos**:
  1. Lee `docs/desarrollo/placas_pedidas_2G4.md` y, por cada antena del pedido, localiza su `diseno.json` en
     `salidas/pedido_2G4/<nombre>/`.
  2. Por cada una, busca su simulación guardada (`resultado.json` junto al diseño, o en la biblioteca con
     `biblioteca.leer_simulacion`). Si no hay, simúlala con sus parámetros exactos (`simulacion.simular`, GPU,
     `nf2ff=True`), **sin ajustar**: se mide lo que se fabricó, no lo que hoy generaría el programa.
  3. Repite cada simulación con εr 4,2 y 4,8 (el sustrato es un dict: copia el de `tipos.sustrato(...)` y cambia
     la εr; mira cómo lo hace `herramientas/sensibilidad_er.py`).
  4. Escribe `docs/desarrollo/medidas/predicciones_2G4.md` con una tabla: antena, f de resonancia (MHz) con εr
     4,2 / 4,5 / 4,8, banda a −10 dB, S11 mínimo, ganancia, η.
- **Hecho cuando**: la tabla tiene las antenas pedidas y las 3 columnas de εr, y la pendiente Δf/Δεr de cada una.
- **HECHA el 11-11-2026**: `docs/desarrollo/medidas/predicciones_2G4.md`. Se pidieron **6** antenas (no 7: el meandro no
  se pidió). Las simulaciones con las 3 εr ya existían (`herramientas/sensibilidad_er.py`, 08-11,
  `salidas/_barridos/SENS_er_pedido/`), así que no se repitieron.

## F1.2 · Herramienta de comparación

- **Quién**: Agente. **Depende de**: nada.
- **Archivos**: nuevo `herramientas/comparar_medida.py`.
- **Pasos**:
  1. Entrada: `<carpeta del diseño o resultado.json> <medida.s1p> [--salida carpeta]`.
  2. Lee el `.s1p` con `ajuste.leer_s1p` y la simulación con el `datos.npz` / `resultado.json` del diseño (mira en
     `antenas/graficas.py` qué claves usa la interfaz para pintar S11).
  3. Calcula para las dos curvas, con `simulacion.centro_banda`: centro de la banda a −10 dB, bordes, ancho,
     frecuencia y valor del mínimo de S11.
  4. Escribe un `.json` (claves con unidad en el nombre: `f_centro_sim_MHz`, `f_centro_med_MHz`,
     `desviacion_f_pct`, `ancho_sim_MHz`, `ancho_med_MHz`, `s11_min_sim_dB`, `s11_min_med_dB`) y un `.png`
     (matplotlib, backend `Agg`) con las dos curvas superpuestas y la banda objetivo sombreada.
  5. Pruébala con un `.s1p` falso: exporta la propia simulación a `.s1p` desplazada un 3 % en frecuencia y
     comprueba que `desviacion_f_pct` da 3,0 ± 0,1.
- **Hecho cuando**: la prueba del paso 5 pasa y el PNG se lee bien.
- **HECHA el 11-11-2026**: `herramientas/comparar_medida.py <simulado> <medida.s1p> [--banda a b] [--ventana a b]
  [--salida carpeta]`. El simulado puede ser la carpeta de una simulación, un `datos.npz` o un `.s1p`. Probada con
  +3 %, −3 % y 0 % de desplazamiento: da 3,0, −3,0 y 0,0 %. Usa `--ventana 2000 3000` con las medidas reales (el
  barrido de 50 kHz–2,7 GHz tiene otros mínimos).

## F1.3 · Comprobar la calibración del NanoVNA

- **Quién**: Usuario delante. **Depende de**: nada.
- **Pasos**:
  1. Pide al usuario: NanoVNA conectado por USB, encendido, latiguillo puesto en el puerto 1 y la **carga de 50 Ω**
     en su extremo.
  2. Cuando confirme: `cd vna; & $PY calibrar_pc.py verificar completa_50k_2700M`.
  3. Si la carga no da < −35 dB en todo el rango, o avisa de estándar mal puesto, hay que recalibrar
     (`calibrar_pc.py iniciar … → open → short → load → thru → terminar`, un paso por ejecución, pidiendo al usuario
     cada cambio de estándar).
- **Hecho cuando**: `verificar` da el visto bueno. Apunta la fecha en `RETOMAR.md`.

## F1.4 · Medir los cupones y sacar εr

- **Quién**: Usuario delante para medir; Agente para el cálculo. **Depende de**: F1.3 y las placas.
- **Pasos de medida**:
  1. Lee `cupon/generar_cupon.py` y el `diseno.json` de `cupon/cupon_A` y `cupon_B`: ahí están los radios de los
     anillos, los largos de las líneas y dónde se suelda cada conector. Enséñale al usuario la vista
     (`cupon/vista_gerber.py <cupón>`; si se suelda por debajo, imagen espejada, lección 7).
  2. Cada estructura se mide por separado. Pide al usuario que suelde o conecte **una** y espera a que confirme.
  3. Anillos (868 MHz y 2,4 GHz; el de 5,8 GHz queda fuera del NanoVNA): medida de transmisión o de reflexión
     según cómo esté diseñado el acoplo (míralo en `generar_cupon.py`; `vna/medir_linea.py` y
     `medir_antena_pc.py` tienen su uso en el docstring). Guarda con nombres `cupon_A_anillo868`, etc.
  4. Líneas abiertas S80 y S30 y líneas en L: `medir_linea.py` (retardo → εeff).
- **Pasos de cálculo**:
  5. Anillo: las resonancias cumplen `2π·r·√εeff = n·λ0`. Saca εeff de cada resonancia medida y, de ella, εr
     invirtiendo `materiales.eps_eff_microstrip(er, h, w)` por bisección.
  6. Afínalo con la simulación: `cupon/simular_anillo.py <anillo>` con εr 4,2 / 4,5 / 4,8; interpola la εr que da
     la resonancia medida. Si fórmula y simulación difieren > 2 %, manda la simulación (lleva el
     `CORRECCION_ANILLO` del diseño).
  7. tanδ: del factor Q de la resonancia (ancho a −3 dB), restando la pérdida del cobre que da la simulación con
     tanδ = 0. Si sale ruidoso, deja 0,02 y dilo.
  8. Líneas: εeff = (c·retardo / longitud)², comparando S80 con S30 para quitar el efecto del conector.
  9. Escribe `docs/desarrollo/medidas/er_fr4.md`: εr y tanδ a 868 MHz y 2,4 GHz, con el método, la dispersión
     entre estructuras y los `.s1p` usados.
- **Hecho cuando**: hay una εr por frecuencia con su incertidumbre (± la dispersión entre anillo y líneas). Si la
  dispersión supera ±0,15, no sigas: revisa soldaduras y medidas con el usuario.

## F1.5 · Medir las antenas

- **Quién**: Usuario delante. **Depende de**: F1.3 y las placas.
- **Pasos**:
  1. Por cada antena: el usuario suelda el SMA (o el coaxial del dipolo), la deja **lejos de metal y de la mesa**
     (≥ 30 cm, sobre cartón o colgada) y confirma.
  2. `cd vna; & $PY medir_antena_pc.py <nombre> completa_50k_2700M --zoom 2200 2700`.
  3. Mide dos veces recolocando el cable. Si el centro de banda cambia > 1 % entre las dos, el cable radia:
     anótalo (los monopolos pequeños y la J-pole son sensibles) y pide una ferrita si el usuario tiene.
  4. Guarda la medida también en la biblioteca del diseño (`biblioteca.guardar_medida`) si el diseño está en
     «Mis diseños».
- **Hecho cuando**: hay `.s1p` + `.json` + `.png` de las 6 antenas pedidas en `vna/medidas/`.

## F1.6 · Comparar simulación y medida

- **Quién**: Agente. **Depende de**: F1.2, F1.4, F1.5.
- **Pasos**:
  1. Vuelve a simular cada antena con la **εr medida** (F1.4), con el paso de malla por defecto.
  2. `comparar_medida.py` para cada una.
  3. Escribe `docs/desarrollo/medidas/sim_vs_medida_2G4.md`: tabla con desviación de frecuencia (%), de ancho de
     banda (%) y de S11 mínimo (dB), con la εr supuesta (4,5) y con la medida.
  4. Clasifica: ≤ 2 % bien; 2–5 % regular; > 5 % mal. Para cada «mal», una hipótesis (cable, conector no
     modelado, malla, masa pequeña) y la prueba que la confirmaría.
- **Hecho cuando**: la tabla existe y cada desviación > 2 % tiene causa probable.
- **Criterio de salida de la fase**: ≤ 2 % en al menos 5 de 7, o las causas identificadas.

## F1.7 · Malla de referencia

- **Quién**: Agente. **Depende de**: F1.6.
- **Pasos**:
  1. Con la εr medida, simula cada antena con tres pasos de malla: por defecto, ×0,7 y ×1,3 (mira en
     `simulacion.simular` cómo se fuerza el paso; `barrido.py` usa `--max-celdas` y un paso fijo).
  2. Tabla: desviación respecto a la medida con cada paso y tiempo de simulación.
  3. Si un paso gana de forma consistente, propón al usuario (**decisión suya**) cambiar el valor por defecto.
- **Hecho cuando**: `docs/desarrollo/medidas/malla_referencia.md` con la tabla y la recomendación.

## F1.8 · Recalibrar con la εr medida

- **Quién**: Agente; el cambio de valor por defecto, **decisión del usuario**. **Depende de**: F1.4, F1.6.
- **Pasos**:
  1. Añade a `materiales.SUSTRATOS` una entrada nueva «FR4 JLC 1,6 mm (medido)» con la εr y tanδ de F1.4. No
     toques la existente todavía.
  2. Pregunta al usuario si pasa a ser el sustrato por defecto. Si dice que sí: cámbialo, vuelve a simular los
     diseños que usa `herramientas/calibrar_estimaciones.py` (lee su cabecera: qué carpetas `_validacion*` y
     `V_jpole_defecto_*` usa; lección 69), regenera `calibracion_estimaciones.json` y reinicia la interfaz.
  3. Comprueba con 3 tipos (monopolo recto, Koch, J-pole de Koch) que `dimensionar` + una simulación queda a ≤ 3 %
     del objetivo.
- **Hecho cuando**: el paso 3 pasa y la sección «Sustratos» de los README dice de dónde sale el valor.

## F1.9 · Estado «Medida» en la interfaz

- **Quién**: Agente. **Depende de**: F1.6.
- **Archivos**: `antenas/problemas.py` (`ESTADO`), `antenas/guia.py`, `gui/app.py`, `web/app.js`, README.
- **Pasos**:
  1. Mira cómo se definen y pintan los estados actuales («Validada», «Pendiente de validación», «No funciona»):
     `Grep` de `ESTADO` en `antenas/` y `gui/app.py` y de la clase CSS del estado en `web/`.
  2. Añade el estado «Medida» (color propio, con variante oscura; lección 47) y asígnalo solo a los tipos con
     desviación ≤ 5 % en F1.6, indicando banda y sustrato en el comentario.
  3. En la pestaña Simulación: si el diseño tiene medidas en la biblioteca (`biblioteca.medidas`), superpone la
     última en la gráfica de S11 (traza discontinua, leyenda «Medida»). Toda figura pasa por `T(fig)`.
  4. Traducciones, README (tabla de tipos) y `MANUAL`.
- **Prueba**: `prueba_interfaz.py`; abrir un diseño con medida y ver las dos curvas en claro y en oscuro.
- **Hecho cuando**: la galería muestra «Medida» en los tipos que toca y la gráfica superpone la medida.

## F1.10 · Probar el ajuste real

- **Quién**: Usuario delante. **Depende de**: F1.5.
- **Pasos**:
  1. Koch ajustable: sigue el asistente de la pestaña Medir con su `.s1p`. Anota qué corte o puente recomienda,
     pide al usuario que lo haga, vuelve a medir. Compara el desplazamiento real con el rotulado en la placa.
  2. Si hay una placa con red en π: mide sin componentes (puente de 0 Ω en serie), pasa el `.s1p` al asistente,
     monta los valores que da y vuelve a medir.
  3. Apunta cada cosa confusa de la interfaz o del manual en `docs/desarrollo/medidas/notas_ajuste.md`.
- **Hecho cuando**: una antena desplazada a propósito queda centrada tras seguir el asistente, o está escrito por
  qué no.

## F1.11 · Ganancia relativa (opcional)

- **Quién**: Usuario delante. **Depende de**: F1.5.
- **Pasos**: dos antenas a 1 m, una en cada puerto del NanoVNA, medir S21 (`calibracion` con THRU). Usando el
  dipolo como referencia (2,15 dBi), `G = G_ref + S21_antena − S21_ref`. Comparar con la ganancia simulada.
- **Hecho cuando**: tabla de ganancia medida frente a simulada, con ±2 dB de incertidumbre asumida.
