# Ideas a más largo plazo: primer experimento de cada una

Antes de nada: [`00_como_trabajar.md`](00_como_trabajar.md). Estas ideas **no tienen fecha** y no se empiezan
antes de cerrar la fase 1. Cada una lleva un **primer experimento barato** con un criterio para seguir o
abandonar: no construyas la función completa hasta que el experimento pase. El resultado (pase o no) se apunta
en `docs/desarrollo/` y en una línea de `RETOMAR.md`.

---

## I1 · Optimizador automático

- **Experimento**: script `herramientas/optimizar.py` que minimice el peor S11 en la banda de la IFA a 868 MHz
  moviendo 3 parámetros (`largo`, `altura`, `separacion_toma`) con Nelder-Mead (implementación propia de ~40
  líneas con numpy; scipy no está en `requirements.txt`), malla fija, 40 simulaciones como máximo.
- **Seguir si**: llega a ≤ −15 dB partiendo de un punto con −5 dB, en menos simulaciones que un barrido en rejilla
  de 4 × 4 × 4.
- **Después**: función objetivo con pesos (S11, ganancia, tamaño), botón en la interfaz, reanudable.

## I2 · Parche de GPS con polarización circular

- **Experimento**: en `herramientas/topologias.py`, parche casi cuadrado con esquinas cortadas y **sonda coaxial**
  (puerto `pasante`: necesita las claves `borde` y `direccion`, lección 68) sobre la diagonal, en RO4350B o PTFE
  de 1,65 mm, para GPS L1 (1575,42 MHz). Barre la posición de la sonda (5 puntos) y el corte (4 puntos).
- **Seguir si**: razón axial ≤ 3 dB en el cénit (`ar_dB_theta0`), sentido RHCP (`pol_theta0`) y S11 ≤ −10 dB a la
  vez en algún punto.
- **Después**: sustituir el `parche_circular` actual, que no da polarización circular (lección 66).

## I3 · Diplexor impreso 868 MHz / 2,4 GHz

- **Experimento**: por circuito (sin FDTD): paso bajo y paso alto de 3 elementos con valores E24 que den
  pérdida < 0,5 dB en cada banda y aislamiento > 20 dB. Luego una placa con dos puertos de antena y uno común.
- **Seguir si**: el cálculo por circuito cumple con tolerancias de ±5 %.
- **Después**: tipo «combinador» que une dos antenas del catálogo en una placa.

## I4 · Dos antenas en una placa (diversidad, MIMO)

- **Experimento**: `simulacion.simular` solo admite un puerto. Mira `herramientas/helice_flex.py`: simula dos
  puertos por separado y combina. Haz lo mismo con dos IFA en esquinas opuestas de una placa de 50 × 80 mm a
  2,4 GHz y saca S21.
- **Seguir si**: se obtiene un S21 creíble (−10 a −25 dB) y cambia con la separación como cabe esperar.
- **Después**: segundo puerto en `Antena` y en los resultados.

## I5 · Arrays 2×1, 3×3, 1×N, con y sin reflector

- Notas previas en `RETOMAR.md` («Idea pendiente: más tipos de arrays»).
- **Experimento**: en `directivas.py`, el panel admite 2×2 y 4×4; añade 2×1 sin reflector con dipolos rectos a
  2,4 GHz y simúlalo con `barrido_panel.py`.
- **Seguir si**: ganancia ≥ 4,5 dBi con S11 ≤ −10 dB.

## I6 · Colineales con bowtie y colineales acortadas

- Notas previas en `RETOMAR.md` («Idea pendiente: colineales…»).
- **Experimento**: parámetro de forma de brazo en `colineal_dipolos` (tira / bowtie) y barrido a 2,4 GHz.
- **Seguir si**: misma ganancia (±0,5 dB) con ≥ 15 % menos de largo, o ≥ 30 % más de banda.

## I7 · Flex: hélice de modo normal y Yagi de una capa

- **Experimento**: hélice de modo normal para 868 MHz como hilo PEC (parte de `helice_flex.py`, un solo hilo y un
  puerto): diámetro 8 mm, altura 30–50 mm.
- **Seguir si**: resuena en 868 MHz con R ≥ 5 Ω y η ≥ 50 %.
- La Yagi de una capa (todos los elementos en F.Cu, alimentación por coaxial): variante de `directivas` sin boom
  en B.Cu; simular en «Flex PI 50 µm» a 2,4 GHz; seguir si ≥ 5 dBi con el haz hacia delante.

## I8 · Hélice cuadrifilar con red de 90°

- **Experimento**: por circuito, híbrido de 90° con componentes concentrados que alimente los dos pares con R de
  entrada de 15 Ω (lección 71).
- **Seguir si**: desequilibrio de amplitud < 1 dB y de fase < 10° en 1575 ± 5 MHz con tolerancias de ±5 %.

## I9 · Bandas nuevas (433 MHz, LTE-M/NB-IoT, UWB)

- **Experimento**: añadir la banda a `presentacion.BANDAS` y pasar `campana.py` etapa A solo con monopolos, IFA y
  meandro. A 433 MHz estima antes el tiempo de simulación (placas de > 150 mm).
- **Seguir si**: algún tipo cubre la banda entera a −10 dB (LTE 700–960 MHz pide un 30 % de banda: probablemente
  solo con red de adaptación o con un monopolo ancho).

## I10 · Bobinas NFC (13,56 MHz)

- No es una antena radiante: es una bobina con sintonía. openEMS no es práctico a 13,56 MHz.
- **Experimento**: módulo de cálculo analítico (inductancia de espiral rectangular, capacidad de sintonía, Q) y
  exportación de la espiral; validar contra una bobina de referencia de una hoja de aplicación (pedir al usuario
  cuál).
- **Seguir si**: la inductancia calculada queda a ±10 % de la de referencia.

## I11 · Importar una antena desde Gerber o DXF

- `placa_sim/simular_placa.py` ya importa Gerber a openEMS: léelo primero.
- **Experimento**: importar el DXF que exporta el propio programa para un monopolo y comprobar que la simulación
  da lo mismo que el original (±1 %).

## I12 · Complemento para KiCad

- **Depende de**: F3.3 (huella integrable).
- **Experimento**: plugin de acción mínimo (Python de KiCad) que lance la interfaz y, al guardar, inserte la
  huella en la placa abierta. Comprobar antes qué API ofrece KiCad 10 (ha cambiado respecto a la 8).

## I13 · Linux y macOS

- **Experimento**: flujo de CI en Ubuntu que instale openEMS (paquete o compilado), las dependencias y pase
  `comprobar_tipos.py` y una simulación corta de un monopolo.
- **Seguir si**: la frecuencia coincide con la de Windows (±0,5 %).

## I14 · SAR y límites de potencia

- Solo orientativo; nunca sustituye a un laboratorio. No empezar sin que el usuario lo pida expresamente.

## I15 · Simulación para la web lite

- **Experimento**: medir cuánto tarda en CPU de un servidor pequeño el monopolo de 2,4 GHz con malla ×1.
- **Seguir si**: < 5 min. Implica un servicio con coste: **decisión del usuario**.
