# Manual de Chirptenna

*Versión alpha. Instalación: [INSTALAR.md](INSTALAR.md). Este manual está en castellano, como la interfaz.*

Este manual explica cómo usar Chirptenna de principio a fin: diseñar una antena, simularla, mandarla a
fabricar, medirla y **ajustarla** una vez fabricada, con marcas de corte, puentes y la **red en π**.

> **Antes de nada:** Chirptenna está en alpha y lo que calcula está validado **solo en simulación**. La
> placa real casi nunca sale exactamente en la frecuencia: el FR4 varía de un lote a otro, y la caja, la
> batería y el cable la desplazan. Por eso las antenas llevan opciones de ajuste y por eso **hay que medir**
> antes de fiarse.

**Índice**

1. [Conceptos en 5 minutos](#1-conceptos-en-5-minutos)
2. [El flujo de trabajo](#2-el-flujo-de-trabajo)
3. [La barra del diseño](#3-la-barra-del-diseño)
4. [Pestaña Diseño](#4-pestaña-diseño)
5. [Pestaña Simulación](#5-pestaña-simulación)
6. [Pestaña Fabricar](#6-pestaña-fabricar)
7. [Montar la placa](#7-montar-la-placa)
8. [Pestaña Medir](#8-pestaña-medir)
9. [Ajustar la antena fabricada](#9-ajustar-la-antena-fabricada)
10. [La red en π a fondo](#10-la-red-en-π-a-fondo)
11. [Pestaña Mis diseños](#11-pestaña-mis-diseños)
12. [Qué antena elegir](#12-qué-antena-elegir)
13. [Problemas frecuentes](#13-problemas-frecuentes)
14. [Glosario](#14-glosario)

---

## 1. Conceptos en 5 minutos

- **Frecuencia de resonancia.** La frecuencia a la que la antena «encaja» con la radio. Depende sobre todo
  de su longitud: **más larga, frecuencia más baja**; más corta, más alta.
- **S11 (pérdida de retorno), en dB.** Cuánta potencia rebota en la antena y vuelve a la radio. Cuanto más
  negativo, mejor:

  | S11 | ROE | Potencia que entra en la antena | Valoración |
  |---|---|---|---|
  | −3 dB | 5,8 | 50 % | Mala |
  | −6 dB | 3,0 | 75 % | Floja |
  | **−10 dB** | **1,9** | **90 %** | **Buena: el criterio habitual** |
  | −15 dB | 1,4 | 97 % | Muy buena |
  | −20 dB | 1,2 | 99 % | Excelente (pasado este punto, mejorar no se nota) |

- **ROE (VSWR).** Lo mismo que S11 con otra escala: 1 es perfecto; por debajo de 2 está bien.
- **Banda a −10 dB.** El tramo de frecuencias en el que S11 está por debajo de −10 dB. Tu banda de uso
  (por ejemplo, 869,4–869,65 MHz en Meshtastic EU) tiene que caer **dentro**, con algo de margen.
- **Impedancia (Z = R + jX).** La radio y el cable son de **50 Ω**. La antena ideal presenta R = 50 Ω y
  X = 0. Si R se aleja de 50 o X no es cero, parte de la potencia rebota.
  - X positiva = la antena se comporta como una **bobina** (inductiva), típico si es **demasiado larga**.
  - X negativa = se comporta como un **condensador** (capacitiva), típico si es **demasiado corta**.
- **Carta de Smith.** Un dibujo de la impedancia en cada frecuencia. El **centro** es 50 Ω perfecto, la
  mitad de **arriba** es inductiva y la de **abajo**, capacitiva. Chirptenna dibuja el círculo de ROE 2
  (dentro de él = S11 < −10 dB), los bordes de tu banda (●) y el objetivo (★). Ajustar una antena es
  llevar la ★ al centro.
- **Ganancia (dBi)** y **eficiencia (η).** La ganancia dice cuánto concentra la antena en su mejor
  dirección. La eficiencia, qué parte de la potencia que entra se radia de verdad: el resto se pierde en
  calor, sobre todo en el FR4. Una antena puede estar perfectamente adaptada (S11 −20 dB) y aun así radiar
  poco si su η es baja.

---

## 2. El flujo de trabajo

Las pestañas siguen el orden del trabajo:

```
Diseño ──► Simulación ──► Fabricar ──► (JLC) ──► montar ──► Medir ──► ajustar ──► Medir…
 tipo,      openEMS:       reglas,                SMA y       NanoVNA    cortar,
 banda,     S11, Smith,    Gerber,                componentes o .s1p     puentes,
 tamaño     diagrama       serigrafía                                    red en π
```

- **Simular es opcional.** El tamaño inicial sale de fórmulas calibradas con simulaciones anteriores y
  suele quedar a un 0–3 % de lo que da la simulación. Simular sirve para confirmar la banda, ver el
  diagrama de radiación y afinar antes de pagar la fabricación.
- **Guarda el diseño** (botón **Guardar diseño**). Cada diseño guarda en su carpeta la simulación, los
  archivos de fabricación y las medidas, para poder compararlos después.

---

## 3. La barra del diseño

Está siempre arriba:

| Campo | Qué es |
|---|---|
| **Nombre del diseño** | El nombre de la carpeta en *Mis diseños*. Cambiarlo y guardar crea un diseño nuevo (sirve para hacer variantes) |
| **Tipo de antena** | Ver [qué antena elegir](#12-qué-antena-elegir). Bajo la barra aparecen los **problemas conocidos** del tipo: léelos |
| **Banda de uso** | 433, 868 o 2,4 GHz rellenan el centro y el ancho. Con **Otra** los pones a mano (p. ej. 915 MHz en América) |
| **Centro [MHz]** | La frecuencia objetivo. Para Meshtastic, pon la frecuencia real de tu canal (en EU_868 con LongFast, 869,525 MHz; mírala en la app de Meshtastic) |
| **Ancho [MHz]** | El ancho que tiene que cubrir la antena. Pon el de tu canal o tu banda; el programa añade margen |

> **Truco para Meshtastic:** centra la antena en tu canal, no en el centro de la banda de 868 MHz. Así,
> con los 5–10 MHz de banda de un monopolo, te queda margen a los dos lados para lo que desplacen la caja y
> la batería.

---

## 4. Pestaña Diseño

### Tamaño y material

- **Sustrato.** El material y el grosor de la placa: FR4 de JLC de 1,6 / 1,2 / 1,0 / 0,8 mm o Rogers
  RO4350B. El FR4 de 1,6 mm es el más barato y el que se ha usado para validar. El RO4350B pierde mucho
  menos (más eficiencia, sobre todo en parches y arrays), pero es bastante más caro.
- **Ajustar tamaño a la frecuencia.** Recalcula las medidas para que la antena resuene en el centro
  elegido. **Púlsalo siempre que cambies de banda, de tipo o de sustrato.** Respeta las medidas que hayas
  fijado a mano.
- **Ampliar ancho de banda.** Si la banda estimada no cubre el ancho pedido, ensancha la pista (monopolos y
  Yagi) o el parche, manteniendo la frecuencia. Te dice si ya cubre la banda o hasta dónde ha llegado.

### Parámetros

Cambian según el tipo. Los más habituales:

- **Medidas de la antena** (largo, ancho de pista, iteración del fractal…). Al pasar el ratón por encima se
  ve una ayuda. La **iteración** de un fractal la hace más compacta, pero suele estrechar la banda y bajar
  la eficiencia.
- **Plano de masa** (monopolos): un plano de masa de **λ/4 o más** es lo ideal. Uno más corto encoge la
  placa, pero obliga a alargar el radiador y hace la antena más sensible a lo que se conecte detrás.
- **Conector:** SMA de canto (para probar y medir) o IPEX/U.FL (para integrarla). Con IPEX la adaptación
  aún está en revisión: lee los problemas conocidos.
- **Ajuste tras fabricar** (monopolos, parches, J-pole, quasi-Yagi). Ponlo en **Ajustable** para una
  primera tirada: añade las [opciones de ajuste](#9-ajustar-la-antena-fabricada) (sobrelargo con marcas,
  tramos con puentes y red en π). Cuando tengas una versión ya ajustada y medida, puedes fabricar la
  definitiva sin ellas.
- **Aligerado** (Yagi y panel): ventanas sin FR4 para que pese menos. **Sin simular**: quitar FR4 sube un
  poco la frecuencia.

### Resultado y consejos

- **Resultado (estimación):** tamaño de la placa, frecuencia estimada, banda, ganancia aproximada y
  avisos. Son estimaciones; la simulación las precisa.
- **Consejos:** recomendaciones para ese diseño concreto (pista demasiado fina, plano de masa corto, banda
  justa…).

---

## 5. Pestaña Simulación

Simula la antena con **openEMS** (un simulador electromagnético de onda completa, FDTD).

1. **Precisión:**
   - **rápida** para tantear (±3 %);
   - **normal** para diseñar;
   - **fina** para la comprobación final, más lenta.
2. **Ajustar a la frecuencia simulando:** si está marcado, simula, corrige el tamaño y repite (2–5
   simulaciones) hasta que el centro de la banda a −10 dB cae en el objetivo. Si no, hace una sola.
3. **Simular.** El registro muestra el progreso. Puedes seguir usando el resto de la interfaz.

**Cuánto tarda:** de 1 a 15 minutos cada simulación en un monopolo de 2,4 GHz. A 868 MHz, con pistas finas,
o en arrays y paneles, puede llegar a horas. Los resultados quedan en caché: repetir la misma geometría es
instantáneo.

### Cómo leer los resultados

- **S11** y **ROE**: la curva tiene que bajar de −10 dB (o de ROE 2) en toda tu banda (zona sombreada).
- **Carta de Smith:** cuanto más cerca del centro pase la ★, mejor. Si la curva da un **bucle** cerca del
  centro, la banda es más ancha.
- **Diagrama de radiación:** cortes polares y vista 3D con la placa dibujada dentro. Mira hacia dónde
  apunta el máximo (la flecha). En las directivas (Yagi, panel) debe apuntar **hacia delante**.
- **Ganancia y eficiencia:** una η por debajo del 50 % indica pérdidas grandes en el FR4. Si sale por debajo
  del 10 %, el programa avisa: algo en el modelo no está bien.

Si el diseño estaba guardado y no lo has cambiado, el resultado se guarda con él. Si la simulación ajustó el
tamaño, pulsa **Aplicar los parámetros ajustados** para pasarlos al diseño.

---

## 6. Pestaña Fabricar

### Comprobaciones de fabricación

Elige las **reglas del fabricante** (JLC estándar, JLC mínimo o holgado). La lista avisa de pistas o huecos
por debajo de lo que el fabricante puede hacer, de cobre demasiado cerca del borde y de los **problemas
conocidos** del tipo de antena.

### Exportar

**Exportar KiCad + Gerber + DXF** guarda el diseño y crea en su carpeta `fabricacion`:

| Archivo | Para qué |
|---|---|
| **Gerber para JLC (.zip)** | Se sube tal cual a JLCPCB (u otro fabricante). Lleva cobre, máscara, serigrafía, contorno y taladros |
| **Placa de prueba KiCad (.kicad_pcb)** | La placa completa con su conector, para abrirla o modificarla en KiCad |
| **Huella KiCad (.kicad_mod)** | Solo la antena, para meterla dentro de **tu propia placa** |
| **DXF** | El dibujo para EasyEDA u otros programas |
| Reflector (panel) | Una segunda placa (o chapa) que hace de reflector |

Al acabar se pasa el **DRC de KiCad**. Debe salir sin errores.

**Al pedir en JLCPCB:** sube el zip de Gerber y elige 2 capas, el **material y el grosor del sustrato que
pusiste en el diseño** (FR4 de 1,6 mm por defecto), cualquier color de máscara y el acabado que quieras
(HASL o ENIG). El grosor importa: cambiarlo desplaza la frecuencia y estropea la línea de 50 Ω.

> **Si vas a meter la antena en tu placa con la huella:** respeta la **zona libre** sin cobre ni componentes
> alrededor del radiador, y usa la misma línea de 50 Ω y el mismo grosor de placa. El plano de masa de tu
> placa pasa a formar parte de la antena: en un monopolo, su tamaño cambia la frecuencia.

### Serigrafía (inscripciones)

Van en la cara de abajo, espejadas para leerse al darle la vuelta. Puedes elegir:
- el **logo de Chirptenna** (grande, pequeño o ninguno);
- el tipo y la frecuencia, el nombre del diseño, el resultado de la simulación, la licencia, la fecha;
- texto libre.

Si no cabe todo, se mantienen el logo y la primera línea. Las **marcas de corte**, «vivo»/«malla» y las
referencias de los componentes (Z1, Z2, Z3, JP…) se ponen siempre: hacen falta para ajustar.

---

## 7. Montar la placa

1. **Conector SMA de canto:** centra el pin en la pista de 50 Ω y suelda el pin central por arriba. Suelda
   las patas de masa **por las dos caras**: una masa mal soldada cambia la medida.
2. **Red en π:** si el diseño la lleva, la placa trae tres posiciones (huella 0603 o 0402):
   - **Z1**, en serie con la pista, con un hueco que hay que cerrar. Para la primera medida pon una
     **resistencia de 0 Ω** (o un puente de estaño);
   - **Z2** (lado del conector) y **Z3** (lado de la antena), de la pista a masa. **Déjalas vacías.**
3. **Tramos con puentes:** vienen **abiertos**. No los cierres todavía.
4. Limpia los restos de flux con alcohol isopropílico: a 2,4 GHz, una capa gruesa de flux se nota.

---

## 8. Pestaña Medir

### Con un NanoVNA (asistente)

El asistente tiene cuatro pasos:

1. **Conectar el NanoVNA.** Pulsa **Buscar el NanoVNA**. Solo se lee su estado: su calibración y sus slots
   guardados no se tocan nunca.
2. **Calibración.** Elige una calibración guardada o **Calibrar ahora**:
   - Calibra **al final del latiguillo que vayas a usar con la antena**. Ahí queda el plano de medida.
   - El rango que propone va de 0,6 a 1,4 veces la frecuencia del diseño. 301 puntos es buen compromiso.
   - Sigue las instrucciones: **OPEN** (nada conectado), **SHORT** (cortocircuito) y **LOAD** (carga de
     50 Ω), cada uno en el extremo del latiguillo. Si pones el estándar equivocado, el programa lo detecta y
     avisa.
   - **Guardar calibración** la deja en el PC para otras veces. Vale mientras uses el mismo latiguillo y el
     mismo rango.
3. **Comprobar la calibración.** Pon la **carga de 50 Ω** y pulsa **Comprobar**. Bien calibrado, |S11|
   queda por debajo de **−30 dB**. Si no, repite la calibración.
4. **Medir y ajustar.** Conecta la antena:
   - Escribe una **etiqueta** que diga qué has cambiado («sin cortar», «Z1 3,3 nH»…) y pulsa **Medir y
     guardar**. La medida se guarda en el diseño y se superpone a la simulación.
   - El modo **En vivo** repite la medida cada pocos segundos alrededor de la banda, **sin guardarla**, y
     muestra la resonancia, el S11 en el objetivo y la primera recomendación. Sirve para ir cortando poco a
     poco. **Guardar esta medida** guarda la última.

### Con otro analizador

Mide con su programa, exporta un **`.s1p`** (Touchstone de 1 puerto) y súbelo en **…o sube un .s1p**.
También puedes saltar el NanoVNA con **Saltar (subir un .s1p)**.

### Cómo medir bien

- Mide la antena **en las condiciones de uso**: dentro de su caja, con la batería y la placa del nodo
  conectadas si van pegadas. La caja de plástico suele **bajar** la frecuencia un 1–5 %.
- **Aléjate:** ni la mano ni el cuerpo a menos de un palmo, y nada metálico cerca. Deja el NanoVNA sobre la
  mesa y la antena al borde, apuntando hacia fuera.
- Usa siempre **el mismo latiguillo** con el que calibraste, y no lo dobles entre la calibración y la
  medida.
- Si la curva cambia al tocar el cable, la malla del coaxial está radiando: prueba con un latiguillo más
  corto o con unas ferritas en el cable.

---

## 9. Ajustar la antena fabricada

### El orden importa

1. **Primero la frecuencia**: llevar la resonancia a tu canal **cortando** (marcas) o **alargando**
   (puentes).
2. **Después la adaptación**: si en tu canal S11 sigue por encima de −10/−15 dB, mejorarla con la **red en
   π**.

No uses la red en π para corregir una antena muy desplazada de frecuencia: se puede adaptar, pero la banda
se estrecha mucho y las pérdidas en los componentes suben. Como referencia, la red en π corrige bien
desvíos de hasta un 2–3 %; más allá, corta o cierra puentes primero.

### El asistente de ajuste

En **Simulado frente a medido**, pulsa **Analizar** en una medida (las nuevas se analizan solas). El
asistente dice:

- la **resonancia medida** y cuánto se desvía del objetivo (en %);
- el **S11 y la impedancia Z en tu frecuencia objetivo**. La Z está **trasladada a la posición de la red
  en π**: descuenta el tramo de pista entre el SMA y Z1;
- **qué hacer**: qué marca cortar, cuántos puentes cerrar o qué poner en la red en π;
- si hay una medida anterior, **qué ha cambiado** respecto a ella.

### Marcas de corte (subir la frecuencia)

Con el **sobrelargo** activado, la antena sale alargada a propósito (un 3 % por defecto), así que resuena
**por debajo** del objetivo. La serigrafía marca varios puntos de corte con la **frecuencia en MHz** que
queda si cortas por ahí.

- El asistente te dice por qué marca cortar, **corrigiendo los números serigrafiados** con lo que has
  medido. Ojo: los números impresos son la estimación del diseño, y el asistente es más fiable.
- **Corta poco a poco.** Primero una marca menos de lo que dice, mide y sigue. Cortar se puede deshacer
  muy mal.
- Corta con una cuchilla o un cúter, de lado a lado de la pista. Levanta el trozo de cobre con la punta
  y comprueba con un polímetro que no queda ningún hilo uniendo las dos partes.
- En el **parche rectangular**, las marcas son líneas paralelas al borde superior: corta el parche entero
  por la marca.

### Tramos con puentes (bajar la frecuencia)

Al final del radiador hay varios tramos sueltos, separados por un hueco. Cada puente que cierras
**alarga** la antena y **baja** la frecuencia un paso (1,5 % por defecto; la nota del diseño dice el paso
real).

- Ciérralos **en orden, empezando por el más cercano al radiador**. Un puente cerrado más allá de uno
  abierto no hace nada.
- Puente de estaño: una gota de estaño que una los dos medios pads. Con resistencia de 0 Ω: suéldala en
  su huella.
- Para volver atrás, quita el estaño con malla desoldadora.

**Marcas y puentes juntos:** con los dos activados puedes ir en las dos direcciones. Si la antena sale
alta, cierras puentes; si sale baja, cortas por las marcas.

---

## 10. La red en π a fondo

### Qué es

Tres posiciones de componente en la pista de 50 Ω, entre el conector y la antena:

```
 SMA ───┬────[ Z1 ]────┬─── antena
        │              │
      [Z2]           [Z3]
        │              │
       GND            GND
  (lado conector) (lado antena)
```

- **Z1** va **en serie**. De fábrica, una resistencia de 0 Ω (o un puente).
- **Z2** y **Z3** van **a masa** (en derivación). De fábrica, vacías.

Con bobinas y condensadores en esas posiciones se «transforma» la impedancia de la antena para que la
radio vea 50 Ω. En la práctica casi siempre bastan **dos componentes**: **Z1 más una de las dos
derivaciones**. Eso es una red en L, y es lo que propone el asistente.

### Qué derivación usar

Depende de la parte real R de la impedancia medida en Z1:

| Antena medida | Derivación | Montaje |
|---|---|---|
| **R menor que 50 Ω** (lo más común en monopolos con plano de masa pequeño) | **Z2**, lado del conector | Z1 en serie junto a la antena, y la derivación hacia el conector |
| **R mayor que 50 Ω** | **Z3**, lado de la antena | Derivación junto a la antena, y Z1 en serie hacia el conector |

El asistente ya lo hace por ti: indica la posición y los valores comerciales (serie E24), y el S11 que
quedaría con ellos.

### Paso a paso

1. **Ajusta antes la frecuencia** con marcas o puentes (apartado 9).
2. **Mide con la red de fábrica** (Z1 = 0 Ω, Z2 y Z3 vacías), en las condiciones de uso y con etiqueta
   «red de fábrica».
3. Si en tu frecuencia **S11 ya es mejor que −15 dB**, el asistente te dirá que lo dejes así: **no toques
   nada**. Cada componente añade algo de pérdida.
4. Si no, mira la propuesta del asistente y las **alternativas**. Normalmente hay dos soluciones; elige
   siguiendo [los criterios de abajo](#qué-solución-elegir).
5. **Monta primero la derivación** (Z2 o Z3) y **después cambia Z1**. Mide con una etiqueta que diga lo que
   has puesto («Z1 3,3 nH, Z2 1,2 pF»).
6. El asistente muestra el cambio respecto a la medida anterior y una propuesta nueva. Con valores reales,
   lo normal es necesitar **una o dos vueltas**: subir o bajar un valor de la serie E24.
7. Cuando esté bien, apunta los valores en las **notas del diseño** (*Mis diseños*) y en la medida.

### Qué solución elegir

- **Paso bajo (Z1 bobina, derivación condensador):** la preferida. Atenúa los armónicos de la radio y no
  tiene pegas.
- **Paso alto (Z1 condensador, derivación bobina):** vale igual, y la bobina a masa descarga la estática de
  la antena. A cambio, deja pasar los armónicos.
- **Evita valores extremos:**
  - condensadores de menos de **0,5 pF** o bobinas de menos de **1 nH**: la capacidad de los pads y de las
    soldaduras ya es de ese orden (0,1–0,3 pF), así que el valor real se parecerá poco al nominal;
  - condensadores en serie muy grandes (más de ~50 pF a 868 MHz o ~20 pF a 2,4 GHz): son casi un
    cortocircuito y equivalen a dejar el 0 Ω.
- Si las dos soluciones dan un S11 parecido, elige la de **valores más «normales»** (unos pocos nH o pF).

### Qué componentes comprar

- **Condensadores:** cerámicos **C0G/NP0** (no X7R ni Y5V: varían con la temperatura y la tensión). A
  2,4 GHz, con tolerancia de **±0,1 pF** o ±0,05 pF en valores por debajo de 5 pF.
- **Bobinas:** de **RF**, de hilo bobinado o multicapa de alta Q (por ejemplo, Murata LQW/LQG o Coilcraft
  0402HP/0603HP), con tolerancia de ±2 % o ±0,1 nH. Comprueba que su **frecuencia de autorresonancia
  (SRF) sea al menos el doble** de tu frecuencia. Las bobinas de potencia o de filtrado no sirven.
- **Tamaño:** el mismo que la huella de la placa (0603 por defecto, más fácil de soldar a mano).
- **Un kit de muestras** de condensadores y bobinas de RF en 0603 o 0402 sale muy a cuenta si vas a ajustar
  varias antenas.

### Leer la carta de Smith mientras ajustas

Cada componente mueve el punto de la impedancia en un sentido fijo:

| Componente | Posición | Mueve el punto… |
|---|---|---|
| Bobina en **serie** (Z1) | serie | hacia **arriba**, siguiendo su círculo de R constante (sentido horario) |
| Condensador en **serie** (Z1) | serie | hacia **abajo**, siguiendo su círculo de R constante (antihorario) |
| Condensador a **masa** (Z2/Z3) | derivación | en sentido **horario**, siguiendo su círculo de G constante |
| Bobina a **masa** (Z2/Z3) | derivación | en sentido **antihorario**, siguiendo su círculo de G constante |

Cuánto mueve cada uno:
- **bobina en serie**: más nH, más se mueve;
- **condensador en serie**: al revés, cuanto **más pequeño** (menos pF), más se mueve;
- **condensador a masa**: más pF, más se mueve;
- **bobina a masa**: al revés, cuanto **más pequeña** (menos nH), más se mueve.

Así se corrige el siguiente paso aunque el asistente no esté delante. Si la ★ se ha quedado un poco por
encima del centro (inductiva), baja un valor de la bobina serie o sube el condensador serie.

### Ejemplos

Calculados con el mismo asistente:

**Monopolo de 868 MHz con plano de masa corto**, medido a 869,525 MHz: Z = 22 − 18j Ω, S11 −7 dB.
R es menor que 50 Ω, así que la derivación va en **Z2** (lado del conector):
- solución 1: Z1 = **27 pF**, Z2 = **8,2 nH** → S11 ≈ −44 dB (paso alto);
- solución 2: Z1 = **7,5 nH**, Z2 = **4,3 pF** → S11 ≈ −27 dB (paso bajo).

Las dos dejan la antena muy por debajo de −15 dB. La 2 filtra armónicos, y −27 dB es de sobra.

**Monopolo de 2,4 GHz**, medido a 2441,75 MHz: Z = 95 + 30j Ω, S11 −8,7 dB. R es mayor que 50 Ω, así que la
derivación va en **Z3** (lado de la antena):
- solución 1: Z1 = **1,2 pF**, Z3 = **9,1 nH** → S11 ≈ −32 dB;
- solución 2: Z1 = **3,3 nH**, Z3 = **0,82 pF** → S11 ≈ −31 dB.

Aquí la solución 2 lleva un condensador de 0,82 pF, demasiado cerca de la capacidad de los pads: la 1 será
más predecible.

### Límites de la red en π

- **Ajustar la adaptación no arregla una antena que radia poco.** Si la η simulada es baja (parche de
  Minkowski de iteración 3, COCO), la red en π consigue que la potencia entre, pero no que se radie.
- Con **R por debajo de ~10 Ω o por encima de ~250 Ω**, la adaptación será muy estrecha y con pérdidas.
  Mejor rediseñar: plano de masa más grande, otra iteración u otro tipo.
- Una red ajustada para un entorno (dentro de la caja) no vale para otro (al aire). Ajusta **en el
  entorno final**.

### Qué tipos la llevan

Monopolos (recto, meandro, Koch, Hilbert y Sierpinski), parches, array de parches y quasi-Yagi. La J-pole
se ajusta solo con marcas y puentes. La Yagi con boom, el panel, el dipolo y las colineales todavía no
tienen opciones de ajuste.

---

## 11. Pestaña Mis diseños

Cada diseño es una carpeta en `Documentos\Chirptenna\disenos\<nombre>` con:
- `diseno.json` (tipo, parámetros, banda, serigrafía);
- `simulacion/`;
- `fabricacion/`;
- `medidas/`.

En la tabla puedes:
- **Abrir** un diseño;
- abrir su **carpeta**;
- **Renombrar**;
- **Archivar**: lo aparta a `_archivados` y no borra nada.

Las **notas del diseño** sirven de cuaderno: fecha del pedido, lote, qué marca cortaste, qué componentes
pusiste. Dentro de seis meses te alegrarás de tenerlas.

Para compartir un diseño, comprime su carpeta. Otra persona puede copiarla en su biblioteca y abrirla.

---

## 12. Qué antena elegir

| Para… | Recomendado | Por qué |
|---|---|---|
| Un nodo Meshtastic portátil (868/915 MHz) | **Monopolo de Koch** o **meandro**, con ajuste y red en π | Compactos, omnidireccionales, validados a 868 MHz |
| La antena de referencia para comparar | **Monopolo recto** | El más predecible: si este no sale, el problema es la medida o el material |
| 2,4 GHz compacto | **Monopolo de Koch** o **Sierpinski** | Validados a 2,4 GHz; el Sierpinski tiene más ancho de banda |
| Un enlace punto a punto | **Yagi con boom** (elementos rectos) o **panel 2×2/4×4** | 6–7 dBi la Yagi, 12–17 dBi el panel, en simulación |
| Una antena sin plano de masa | **J-pole de Koch** o **dipolo** | No dependen de la placa a la que se conectan |
| Experimentar | Hilbert, Minkowski, quasi-Yagi, COCO, Franklin | Tienen problemas conocidos: léelos antes |

La tabla completa de qué está validado está en el [README](README.md#tipos-de-antena).

---

## 13. Problemas frecuentes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La resonancia medida está un 3–8 % por **debajo** de la simulada | εr del FR4 real distinta de 4,5, caja de plástico, flux | Normal en alpha. Cierra menos puentes o corta por las marcas. Si te pasa siempre, compártelo en una issue «Medida real»: sirve para calibrar el programa |
| Sale por **encima** | Placa más fina de lo pedido, conector mal soldado | Revisa el grosor y las soldaduras; cierra puentes |
| **Dos o más mínimos** en S11 | Plano de masa pequeño, o el latiguillo radia | Fíate del que esté cerca de la frecuencia esperada. Prueba con un latiguillo más corto o ferritas |
| La curva cambia al tocar el cable | La malla del coaxial radia | Latiguillo corto, ferritas, o medir con la placa del nodo conectada |
| S11 bueno pero el alcance es malo | Eficiencia baja (FR4) o antena tapada | Mira la η simulada; aleja la antena de la batería y de los metales |
| Nada baja de −3 dB | Antena desconectada o en cortocircuito | Revisa Z1 (¿está puesta?), los puentes y las soldaduras del SMA. Mira la Z: ~0 Ω es un corto; muy alta, un circuito abierto |
| El asistente propone valores raros (≪1 pF, ≫100 nH) | Antena muy desadaptada o medida mal | Revisa la calibración (carga < −30 dB). Ajusta la frecuencia primero |

---

## 14. Glosario

| Término | Significado |
|---|---|
| **λ (lambda)** | Longitud de onda. A 868 MHz son 34,5 cm; a 2,44 GHz, 12,3 cm. En la placa es más corta (λg) por el FR4 |
| **εr** | Permitividad del sustrato. Cuanto mayor, más corta queda la antena. FR4 ≈ 4,5 |
| **Microstrip / línea de 50 Ω** | La pista que lleva la señal del conector a la antena, con masa debajo. Su ancho fija los 50 Ω |
| **Plano de masa** | La zona de cobre conectada a masa. En los monopolos es la «otra mitad» de la antena |
| **Balun** | Lo que adapta una línea desequilibrada (coaxial) a una antena equilibrada (dipolo) |
| **OSL / SOL** | Calibración con OPEN, SHORT y LOAD |
| **`.s1p`** | Archivo Touchstone con la medida de S11 |
| **DRC** | *Design Rule Check*: comprobación automática de la placa en KiCad |
| **Gerber** | Los archivos que se envían al fabricante |
| **E24** | Serie de valores comerciales (1,0 · 1,1 · 1,2 · 1,3 · 1,5 · 1,6 · 1,8 · 2,0 · 2,2 · 2,4 · 2,7 · 3,0 · 3,3 · 3,6 · 3,9 · 4,3 · 4,7 · 5,1 · 5,6 · 6,2 · 6,8 · 7,5 · 8,2 · 9,1 × 10ⁿ) |
| **Derivación (shunt)** | Componente entre la pista y masa |

---

¿Has fabricado y medido una antena? Compártelo con la plantilla
[«Medida real»](https://github.com/sqtactical/chirptenna/issues/new/choose): es lo que más ayuda al
proyecto en esta fase. Para dudas, [Discussions](https://github.com/sqtactical/chirptenna/discussions).
