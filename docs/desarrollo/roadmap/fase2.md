# Fase 2 · v0.4: consolidar

Antes de nada: [`00_como_trabajar.md`](00_como_trabajar.md). Objetivo: menos cosas a medias, resultados que no
dependan de la malla y un segundo pedido que valide 868 MHz y la primera antena integrada.

F2.1–F2.6 no necesitan hardware y se pueden adelantar mientras llegan las placas.

---

## F2.1 · Subir lo pendiente

- **Quién**: Decisión del usuario (subir a GitHub es publicar).
- **Pasos**: `& $GIT status`, `& $GIT log --oneline origin/main..main`; enseña la lista al usuario; si dice que sí,
  `& $GIT push`. Después mira la CI con `gh run list` (`GH_CONFIG_DIR`, ver `CLAUDE.md`). Si falla solo la descarga
  de KiCad (504), relanza el trabajo fallido.
- **Hecho cuando**: CI en verde en `main`.

## F2.2 · Grupo «Experimental» en la galería

- **Quién**: Agente; la lista final, **decisión del usuario**.
- **Archivos**: `antenas/guia.py` (`GRUPOS`, `TIPOS`), `gui/app.py`, `web/app.js`, `web/index.html`, README, MANUAL.
- **Pasos**:
  1. Propón la lista a partir de `problemas.ESTADO`: todo tipo con estado «No funciona» y los frágiles (bibanda
     J-pole/IFA no es un tipo sino una opción: se queda con su aviso). Candidatos: `parche_minkowski`,
     `parche_circular`, `parche_ranura`, `parche_apilado`, array de parches, COCO, Franklin, Hilbert,
     `monopolo_flecha`. Pregunta al usuario.
  2. En `guia.GRUPOS` crea el grupo «Experimental (no funcionan todavía)» al final y mueve ahí los tipos.
  3. En la galería de escritorio y de la web, ese grupo sale **plegado** (`ui.expansion` en NiceGUI; `<details>`
     en la web). El selector de tipo de la barra los sigue listando, al final.
  4. `guia.comprobar()` debe seguir pasando (lo ejecuta `comprobar_tipos.py`).
  5. Traducciones; captura nueva de la galería si la del README cambia (`docs/capturas`, ver `CLAUDE.md`).
- **Prueba**: `comprobar_tipos.py`, `prueba_interfaz.py`, `construir_web.py`; abrir la galería en claro y oscuro.
- **Hecho cuando**: un usuario nuevo solo ve arriba tipos «Validada» o «Pendiente»; nada desaparece.
- **HECHA el 11-11-2026**: el grupo `experimental` ya existía en `guia.GRUPOS` con todos los candidatos (los 5 «No funciona»,
  los «Pendiente» sin validar, la flecha y el bucle); solo faltaba plegarlo: `ui.expansion` en `gui/app.py` y `<details>` en
  `web/app.js`. 16 tarjetas visibles plegado, 27 desplegado. `i18n faltan` 0, `construir_web` y `prueba_interfaz` bien.
  Pendiente de la CI: `prueba_web.py`.

## F2.3 · Verificación con otra malla

- **Quién**: Agente.
- **Archivos**: `antenas/simulacion.py`, `antenas/simular_cli.py`, `gui/app.py`.
- **Pasos**:
  1. Localiza en `simulacion.simular` cómo se calcula el paso en la placa (lección 20) y si admite un paso
     impuesto (lo usa `ajustar` para mantener la malla fija, lección 21). Si no hay parámetro, añade
     `factor_paso=1.0` que multiplique el paso calculado; la clave de la caché debe incluirlo.
  2. Función nueva `simulacion.verificar_malla(antena, sustrato, f_centro, factores=(0.85, 1.15), …)`: simula con
     cada factor (sin NF2FF, es más rápido) y devuelve por cada uno f de centro de banda, S11 en `f_centro` y la
     diferencia con la simulación base.
  3. Veredicto: «estable» si |Δf| ≤ 2 % y |ΔS11| ≤ 3 dB en los dos; si no, «sensible a la malla».
  4. `simular_cli`: opción `verificar_malla` en el `trabajo.json`; el resultado va a `resultado.json`
     (`verificacion_malla`).
  5. Interfaz, pestaña Simulación: casilla «Verificar con otra malla (tarda el triple)». Marcada por defecto
     cuando `multibanda` = 1 o la familia es `panel`/`array`. El veredicto se muestra con el resultado; si es
     «sensible», aviso visible (`texto-aviso`).
- **Prueba**: monopolo recto a 2441,75 MHz debe dar «estable»; J-pole con `multibanda` = 1 a 868 MHz debe dar
  «sensible» (lección 70). Si el monopolo sale «sensible», hay un fallo en la herramienta.
- **Hecho cuando**: las dos pruebas dan lo esperado y `prueba_interfaz.py` pasa.

## F2.4 · Panel calibrado por banda

- **Quién**: Agente. **Depende de**: nada (mejor tras F1.7).
- **Archivos**: `antenas/directivas.py` (`K_MALLA_FINA_PANEL`, `K_BOWTIE_PANEL`), `herramientas/barrido_panel.py`.
- **Pasos**:
  1. Lee las lecciones 52 y 63. El factor actual sale de 2,4 GHz; a 5,8 GHz el 2×2 resuena a 4800 MHz.
  2. Con `barrido_panel.py 2x2 recto <largos>` busca, a 868 MHz y a 5,8 GHz, el largo del brazo con el mejor
     **peor S11 en toda la banda** (no el centro de banda). 5–6 largos por banda, ±10 % alrededor del actual.
     A 868 MHz estima antes el tiempo: la placa es grande.
  3. Convierte `K_MALLA_FINA_PANEL` en una tabla por frecuencia interpolada en log f (como `JPOLE_HUECO` en
     `tipos.py`).
  4. Comprueba que 2,4 GHz no cambia (mismo largo que antes, ±0,05 mm).
- **Hecho cuando**: con los valores por defecto, el peor S11 en banda es ≤ −10 dB a 2,4 GHz y a 5,8 GHz, y está
  escrito qué pasa a 868 MHz. Actualiza `problemas.py` y los README.

## F2.5 · Bibanda robusta (o retirada)

- **Quién**: Agente; retirar la opción, **decisión del usuario**.
- **Archivos**: `antenas/bibanda.py`, `herramientas/jpole_dual.py`, `herramientas/rama_dual.py`.
- **Pasos**:
  1. Define la medida de robustez: peor S11 en cada banda con tres pasos de malla (0,7 / 1,0 / 1,15 mm a
     868 MHz). El diseño vale si da ≤ −8 dB en **las dos bandas con los tres pasos**.
  2. IFA de dos ramas: barre `IFA_H2` (0,5–0,8) × `IFA_X_BRAZO` (1,10–1,25), 12 puntos, con los tres pasos
     (36 simulaciones de banda ancha: lanza en cola y estima el tiempo antes).
  3. J-pole unida: barre `JPOLE_SEP2` y `JPOLE_TOMA2` igual. Respeta que cada hueco sea mayor que `ancho_pista`
     (lección 65 a).
  4. Si algún punto cumple, pon esas constantes en `bibanda.py` y cambia el aviso de `problemas.py`. Si ninguno
     cumple, presenta los datos al usuario y propón quitar la opción `multibanda` de `jpole` e `ifa` de la
     interfaz (las herramientas se quedan).
- **Hecho cuando**: hay constantes robustas con su tabla en `docs/desarrollo/`, o la decisión del usuario apuntada.

## F2.6 · Bucle: red en L automática y anillo redondo

- **Quién**: Agente.
- **Archivos**: `antenas/simulacion.py` (`ajustar`), `antenas/bucle.py`, `antenas/ajuste.py`.
- **Pasos**:
  1. Red automática: en `ajustar`, para la familia `bucle`, tras la simulación quita la línea de 50 Ω de la Z de
     entrada (`puerto['largo_linea_mm']`; el de-embedding está en `simulacion` y en `fase0/comun.py`), llama a
     `ajuste.redes_l(zl, f_obj)` y guarda en el resultado las dos redes con valores E24 (`red_L`).
  2. Segunda simulación con esos valores montados como elementos concentrados en Z1/Z2/Z3 de la red en π
     (reutiliza `ajuste['condensadores']`; para bobinas hace falta `LEtype=2` en `AddLumpedElement`: añádelo con
     su ESR = ωL/Q). Guarda S11 y banda finales.
  3. Interfaz: mostrar en Simulación «Red recomendada: Z1 = …, Z2 = …» y volcarlo en el LÉEME de fabricación.
  4. Anillo redondo: 4 simulaciones (868 MHz y 2,4 GHz, dos tamaños) y añade su factor a `bucle.CALIBRACION`
     (hoy solo está el cuadrado).
- **Prueba**: 868 MHz por defecto debe reproducir ≈ −25 dB y ~9 MHz de banda; 2,4 GHz ≈ −30 dB y ~52 MHz
  (lección 72). Una bobina de prueba de 10 nH en serie con 50 Ω debe dar Z = 50 + j·2πf·10e-9 (±5 %).
- **Hecho cuando**: el bucle por defecto sale adaptado sin scripts aparte y el estado en `problemas.py` lo dice.

## F2.7 · Yagi comercial B

- **Quién**: Usuario delante (datos). **Bloqueada** hasta tener: grosor del FR4 (calibre), cotas con calibre de
  dipolo, directores y reflector, y una foto macro de la zona de alimentación por las dos caras.
- **Pasos**: con los datos, corrige `referencias/yagi_comercial_b.py`, simula las variantes y, si el usuario puede,
  mide la antena real (`medir_antena_pc.py`) para compararla.
- **Hecho cuando**: el modelo resuena a 2,4 GHz ±3 % con el haz hacia los directores, o está escrito qué dato falta.

## F2.8 · Segundo pedido a JLC

- **Quién**: Decisión del usuario (cuesta dinero). **Depende de**: F1.6, F1.8 y, para la placa integrada, F3.1.
- **Pasos**:
  1. Propón la lista: 868 MHz (monopolo recto, Koch, IFA, J-pole recta), Sierpinski de dos bandas, bucle de
     868 MHz con su red, una antena integrada en una placa de producto (F3.1) y, si sobra sitio, un cupón.
  2. Cada diseño: dimensionado con la εr medida, simulado y, si es sensible, verificado con F2.3.
  3. Exporta con `exportar.exportar_todo` a `salidas/pedido_868/`, DRC limpio, y escribe
     `docs/desarrollo/placas_pedidas_868.md` con parámetros y predicción (como F1.1).
  4. El usuario revisa los Gerber y hace el pedido.
- **Hecho cuando**: carpeta lista, predicciones escritas y el visto bueno del usuario.

## F2.9 · GPU en el instalador

- **Quién**: Agente; probar en otra GPU, Usuario.
- **Pasos**: en `instalar/instalar.ps1`, paso opcional que descarga el zip de GPU de la release (flujo
  `compilar-gpu.yml`), comprueba su SHA-256 fijado y lo deja donde lo busca `antenas/gpu.py`. `-Comprobar` debe
  informar de si hay GPU. Mantén el `.ps1` en UTF-8 con BOM y CRLF. Actualiza `INSTALAR.md` e `INSTALL.en.md`.
- **Prueba**: instalación desde cero con `LOCALAPPDATA` temporal (ver `CLAUDE.md`) y `comparar_gpu.py` con un
  monopolo.
- **Hecho cuando**: instala y simula en GPU en una instalación limpia.

## F2.10 · Deuda técnica

- **Quién**: Agente.
- **Pasos**:
  1. Carpeta `pruebas/` con pytest (añádelo a `requirements.txt` y al lock): `geometria` (longitud de Koch por
     iteración, área de Sierpinski), `ajuste.redes_l` (la red resultante lleva Z a 50 Ω ±0,5), `materiales`
     (`ancho_microstrip(50, 4.5, 1.6)` ≈ 2,9–3,0 mm), `tipos.dimensionar` (todos los tipos a 868 y 2441,75 MHz:
     `estimar_f` del resultado a ≤ 1 % del objetivo), `bucle.estimar_f`.
  2. Añádelo a `.github/workflows/comprobar.yml`.
  3. Partir `gui/app.py` por pestañas solo si el usuario lo pide: es grande pero funciona.
- **Hecho cuando**: `pytest` pasa en local y en la CI en menos de 1 minuto.
