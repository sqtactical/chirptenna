# Fases 4 y 5 · v0.6 (adaptación y medida) y v1.0

Antes de nada: [`00_como_trabajar.md`](00_como_trabajar.md).

---

## F4.1 · Componentes concentrados en cualquier tipo

- **Quién**: Agente. **Depende de**: F2.6 (bobinas en la simulación).
- **Archivos**: `antenas/ajuste.py`, `antenas/simulacion.py`.
- **Pasos**:
  1. Hoy la red en π (`ajuste.red_pi`) dibuja los pads Z1/Z2/Z3 pero la simulación los deja abiertos o puenteados.
     Parámetros nuevos por posición: `z1`, `z2`, `z3` con formato de texto «C 1,2 pF», «L 3,9 nH», «0R» o vacío.
  2. Modelo de componente real: C con ESR = 1/(ωCQ) y L serie parásita (0,4 nH en 0402); L con ESR = ωL/Q y C
     paralela parásita (SRF). Tabla de Q y parásitos típicos por encapsulado en `ajuste.py`, citando la fuente
     (hojas de datos de Murata GJM/LQW o similares; si no las tienes, pide al usuario los valores).
  3. `simulacion.simular` los monta como `AddLumpedElement` en los huecos de los pads (como
     `ajuste['condensadores']`); el hueco no cuenta para la malla.
- **Prueba**: línea de 50 Ω acabada en 50 Ω con un C serie de 1 pF a 2,4 GHz → Z = 50 − j66 Ω (±5 %). Monopolo
  con la red calculada por `redes_l` → S11 ≤ −15 dB en el objetivo.
- **Hecho cuando**: las dos pruebas pasan en GPU.

## F4.2 · Adaptación automática tras simular

- **Quién**: Agente. **Depende de**: F4.1.
- **Pasos**:
  1. Botón «Calcular red de adaptación» en Simulación (para cualquier tipo con `ajuste` = 1): toma la Z simulada
     en el plano de la red (de-embedding de la línea entre el puerto y la red: `ajuste.distancia_conector_a_red`),
     llama a `redes_l`, redondea a E24 y **calcula por circuito** (sin FDTD) el S11 resultante en toda la banda,
     con tolerancia ±5 % de los componentes (peor caso de las 4 esquinas).
  2. Opción «comprobar con simulación» que lanza F4.1 con esos valores.
  3. Elige entre las redes posibles la de mayor banda a −10 dB; a igualdad, la de menos componentes.
- **Prueba**: IFA a 868 MHz desadaptada a propósito (`separacion_toma` ×1,5) → la red la devuelve a ≤ −15 dB; el
  cálculo por circuito y la simulación coinciden en ±3 dB en el objetivo.
- **Hecho cuando**: la prueba pasa y el resultado va al LÉEME de fabricación como lista de piezas.

## F4.3 · Asistente con medida: lista de piezas y tolerancias

- **Quién**: Agente; probarlo con hardware, Usuario delante.
- **Pasos**:
  1. Amplía `ajuste.asistente` (ya parte de un `.s1p`): además de la red, banda esperada, sensibilidad a la
     tolerancia y referencias de compra (valor, encapsulado, dieléctrico C0G; sin números de pieza inventados:
     solo la descripción, salvo que el usuario dé un catálogo).
  2. De-embedding en la medida: si el plano de calibración está en el conector y la red a `d` mm, girar la Z
     medida con la εeff de la línea (ya hay `distancia_red_mm` y `eps_eff` en la firma: comprueba que se usan).
- **Prueba**: con un `.s1p` sintético (carga 20 − j30 Ω tras 15 mm de línea) el asistente propone una red que,
  aplicada por circuito, da ≤ −20 dB.
- **Hecho cuando**: la prueba pasa y el usuario ha adaptado una antena real siguiendo el asistente.

## F4.4 · Más analizadores

- **Quién**: Agente para el código; **Usuario delante** y con el equipo para probar. **Bloqueada** sin hardware.
- **Pasos**: `vna/` hoy habla el protocolo de texto del NanoVNA-H. LiteVNA y NanoVNA V2 usan un protocolo binario
  distinto. Crea una interfaz común (`medir(f_ini, f_fin, puntos)`, `info()`) con dos implementaciones y que
  `asistente_vna.py` elija por VID:PID. No toques el driver actual más que para ajustarlo a la interfaz.
- **Hecho cuando**: una medida a 5,8 GHz con el equipo nuevo, verificada con la carga.

## F4.5 · Informe en PDF

- **Quién**: Agente.
- **Pasos**: `antenas/informe.py` con matplotlib (`PdfPages`, sin dependencias nuevas): portada (nombre, tipo,
  banda, sustrato, vista), parámetros, S11/ROE/Smith, cortes del diagrama, ganancia y η, tolerancias (F3.9), red
  de adaptación y avisos de `problemas`/`consejos`. Botón en Fabricar. Textos con `tr`.
- **Prueba**: generar el informe de un diseño con y sin simulación; abrirlo y revisar que no hay texto cortado.
- **Hecho cuando**: el PDF sale en los 4 idiomas sin errores.

## F4.6 · Exportar el diagrama

- **Quién**: Agente.
- **Pasos**: CSV (θ, φ, ganancia en dBi) desde los datos de NF2FF; y, si el usuario lo pide, el formato de antena
  de la herramienta de cobertura que use (que diga cuál).
- **Hecho cuando**: el CSV reproduce el máximo de ganancia del resultado (±0,1 dB).

---

# Fase 5 · v1.0

Lista de comprobación, no tareas nuevas. Cada punto se marca con la evidencia (ruta del archivo o enlace).

- [ ] 8–10 tipos con estado «Medida» en 868 MHz y 2,4 GHz, con `.s1p` en la biblioteca pública.
- [ ] Dos antenas integradas (una de 2,4 GHz y una de 868 MHz) fabricadas, medidas y a ≤ 3 % de la simulación.
- [ ] Una de ellas montada en un producto real del usuario, con alcance comprobado frente a la antena anterior.
- [ ] Traducciones en/fr/de revisadas por un hablante nativo cada una (abrir una *issue* pidiendo ayuda).
- [ ] Manual con el caso completo de integración.
- [ ] `comprobar_tipos`, `prueba_interfaz`, `prueba_web` y `pytest` en verde en la CI.
- [ ] Instalación desde cero probada en un segundo ordenador.
- [ ] Biblioteca pública de diseños medidos: carpeta `disenos/` o repositorio aparte, cada diseño con
  `diseno.json`, Gerber, `.s1p`, foto y licencia CC BY-NC (`LICENSE-DISENOS.md`). **Decisión del usuario** dónde.
