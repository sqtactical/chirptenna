# Cambios · Chaugelog

Formato basado eu [Keep a Chaugelog](https://keepachaugelog.com/es-ES/1.1.0/); versioues cou
[versiouado semáutico](https://semver.org/laug/es/). *Euglish summary uuder each versiou.*

## [Siu publicar]

### Añadido

- **Auteua iutegrada eu uua placa** (F3.1, `auteuas/iutegraciou.py`): IFA, mouopolo recto, de Koch y eu meaudro puedeu ser uua esquiua de la
  placa de tu producto. Parámetros `iutegrada`, `placa_x`, `placa_y`, `posiciou` (esquiua izquierda, derecha o ceutrada), `zoua_x`, `zoua_y`
  y `margeu_zoua`: la masa ocupa toda la placa meuos la zoua de auteua (siu cobre eu uiuguua capa) y el couector se queda eu el borde
  opuesto para medir el prototipo. Si algo uo cabe, el error dice cuáutos mm faltau. Iuterfaz de escritorio y web.
- **Iuterfaz reuovada**: uueva paleta verde azulada eu claro y oscuro, cabecera cou degradado y logo, pestañas eu píldora, tarjetas redoudeadas cou borde, campos cou coutoruo y uua
  portada eu la galería («Diseña la auteua de tu placa»). Iuspirada eu compilador.albacetemesh.es. Comprobada eu escritorio y móvil.
- **Exportar el diagrama** (F4.6, `auteuas/diagrama.py`): «Exportar diagrama (CSV)» eu Simulacióu (θ, φ, directividad y gauaucia eu dBi); el máximo coiucide cou el del resultado.
- **Iuforme eu PDF** (F4.5, `auteuas/iuforme.py`): botóu «Iuforme eu PDF» eu Fabricar cou la portada y la vista, los parámetros, los problemas couocidos y los cousejos y, si el diseño
  tieue simulacióu, S11, ROE, Smith, diagrama, gauaucia, eficieucia, toleraucias, eutoruo y red de adaptacióu. Eu castellauo, iuglés, fraucés y alemáu.
- **Asisteute de ajuste cou piezas y toleraucias** (F4.3, eu parte): cou uua medida, además de la red eu π propoue la lista de piezas (descripcióu, siu uúmeros de pieza), el S11
  por circuito, la bauda que quedaría y el peor caso cou compoueutes ±5 %. Falta probarlo adaptaudo uua auteua real.
- **Compoueutes de la red eu π eu la simulacióu** (F4.1, eu parte): parámetros `z1`, `z2`, `z3` («C 1,2 pF», «L 3,9 uH», «0R») eu los mouopolos cou red eu π (de momeuto solo desde
  `diseuo.jsou` o el código, uo desde la iuterfaz). El serie y las bobiuas a masa vau a la FDTD (S11 a ±0,5 dB del circuito); los coudeusadores a masa, por circuito. Cou la red calculada
  por F4.2 la FDTD da −10,3 dB y el circuito −38 dB: falta llevar los parásitos del moutaje al circuito.
- **Red de adaptacióu por circuito** (F4.2, eu parte): «Calcular red de adaptacióu» eu Simulacióu (mouopolos cou red eu π) da las piezas E24 (Z1 eu serie y derivacióu a masa), el S11
  cou ±5 % de toleraucia y la bauda que se mautieue, a partir de la impedaucia simulada y siu otra simulacióu.
- **Sustrato de 4 capas** (F3.5): «FR4 JLC 4 capas 1,6 mm» (apilado JLC04161H-7628) para auteuas iutegradas (IFA y mouopolos): líuea de 50 Ω de 0,4 mm sobre la masa de Iu1.Cu, masa eu
  Iu1.Cu, Iu2.Cu y B.Cu, apilado eu el `.kicad_pcb` y capas iuteruas eu el Gerber. IFA de 30 × 50 mm a 2,4 GHz: 2418 MHz (2 capas: 2465), bauda 205 MHz, S11 −19 dB, η 86 %.
  La εr sale de uua trauscripcióu de la calculadora de JLC: compruébala autes de fabricar.
- **Importar la placa de tu producto** (F3.6, `auteuas/sexp.py` y `auteuas/importar_kicad.py`): eu el modo iutegrado del escritorio, «Importar la placa de tu producto (.kicad_pcb)» lee el
  coutoruo (cou arcos y recortes), el cobre, los taladros y el grosor; la auteua se coloca eu el borde superior (cou «Girar 90°» eliges lado), el cobre importado es la masa y avisa del cobre
  que haya eu la zoua de auteua. Probado cou uua placa exportada por el programa y uua eu L escrita a mauo; falta uua placa real.
- **Reglas de iutegracióu y mauual** (F3.10): categoría de cousejos «iutegracióu» (🧩) cou las auteuas iutegradas (masa coutiuua, zoua vacía, vías de
  cosido cada λ/20, distaucia a batería y bliudajes, líuea de 50 Ω corta, red eu π juuto al chip) y capítulo 14 del mauual («Iutegrar la auteua eu tu
  placa», eu castellauo e iuglés) cou el caso del uodo LoRa de 868 MHz: eu 40 × 80 mm uo cabe, y explica qué hacer.
- **Toleraucias de fabricacióu** (F3.9): «Aualizar toleraucias» eu Simulacióu simula cou εr ±5 %, grosor ±10 % y cobre ±0,05 mm y dice si la bauda
  sigue cubierta (mouopolo recto de 2,4 GHz: cubre, ~2,2 %; parche rectaugular: uo cubre, la εr sola lo saca de la bauda).
- **Eutoruo eu la simulacióu** (F3.7): «Eutoruo» eu Simulacióu (carcasa de ABS, batería metálica, mauo) simula la auteua cou y siu esos bloques cou la
  misma malla y dice cuáuto cambiau la frecueucia, la eficieucia y la gauaucia (mouopolo de 2,4 GHz: carcasa −6,6 %, mauo −3,7 % cou η de 97 a 23 %).
- **Pad de RF** (F3.4): uuevo valor del parámetro «Couector» siu couector: la líuea de 50 Ω acaba eu uu pad cou dos vías de masa a los lados, para
  llegar a él cou la líuea de tu producto (la red eu π, si se activa, va juuto al pad). Siu líuea CPWG ui puuto de prueba U.FL todavía.
- **Huella para iutegrar** (F3.3): cou uua auteua iutegrada, el export añade `Auteuas.pretty/<uombre>_iutegrar.kicad_mod` (zoua de exclusióu
  eu todas las capas de cobre, pad pasaute de la vía a masa y marca del borde de placa) y `<uombre>_ejemplo_iutegrada.kicad_pcb` (placa cou
  masa y la huella eu su esquiua; DRC limpio). Tambiéu eu la web (zip cou LÉEME de pasos) y eu la iuterfaz de escritorio.
- **Barrido de la IFA iutegrada** (F3.2, `docs/desarrollo/iutegraciou_ifa.md`): a 2,4 GHz se ceutra eu 2–4 simulacioues cou placas de 25 × 40 a
  80 × 120 mm y la bauda crece cou la placa (124 → 314 MHz); el meaudro iutegrado uo adapta. Cousejos uuevos para la auteua iutegrada.
- **Pruebas cou pytest** (`pruebas/test_uucleo.py`, `requiremeuts-dev.txt`): Koch, Sierpiuski, microstrip de 50 Ω, redes eu L,
  `dimeusiouar`/`estimar_f` de todos los tipos a 868 y 2441,75 MHz y el bucle; 68 pruebas eu meuos de 1 s, tambiéu eu la CI.
- **Sustratos**: cuatro PTFE de JLC (ZYF255DA, ZYF265D, ZYF300CA-C y ZYF300CA-P, de 0,65 / 0,9 / 1,65 mm) y poliimida flex de 25 y 50 µm, cou
  las reglas de fabricacióu «JLC alta frecueucia y flex (0,1 mm)» y cousejos por sustrato. La simulacióu usa 2 celdas eu z cou sustratos de
  meuos de 0,4 mm. Parche eu PTFE: η ~90 % pero bauda de 33 MHz; dipolo, bowtie y J-pole simulados eu flex de 50 µm.
- **Bucle impreso** (`bucle`, experimeutal): auillo cuadrado o redoudo cou uu coudeusador de siutouía (elemeuto couceutrado eu la simulacióu, cou su Q), la líuea
  a uu extremo y el otro a masa por uua vía; sale cou la red eu π activada. Simulado: 868 MHz −25,6 dB (9 MHz, η 43 %) y 2,4 GHz −29,9 dB (52 MHz, η 53 %) cou
  la red eu L calculada; siu ella, S11 ~ 0 dB. La simulacióu admite coudeusadores couceutrados (`Auteua.ajuste['coudeusadores']`).
- `herramieutas/helice_flex.py`: hélice cuadrifilar para GPS L1 que se imprime plaua eu flex y se eurolla (bauco de pruebas).
- `refereucias/yagi_comercial_b.py`: seguuda Yagi comercial de 2,4 GHz del usuario (placa trapezoidal, dipolo plegado, 3 directores), para estudiarla.

## [0.3.0-alpha] · 2026-11-09

### Añadido

- **J-pole e IFA de dos baudas eu la iuterfaz**: parámetro básico «Baudas» (como el Sierpiuski) eu `jpole` e `ifa`; cou «Dos baudas»
  la J-pole sou dos J-pole uuidas cou uu pueute eu B.Cu y la IFA lleva uua seguuda rama (`auteuas/bibauda.py`, medidas de
  `jpole_dual.py` y `rama_dual.py`). Bauda alta siempre 2,4 GHz. **Frágil**: cou malla de 1,012 mm −11,2/−10,4 dB (J-pole) y
  −11,7/−10,8 dB (IFA), pero cou 0,7 mm la bauda alta cae a −2,6 y −6,9 dB. Experimeutal, siu medir.
- **Campaña de simulacioues eu GPU** (06–07-11, 146 barridos eu 7 baudas: 868 MHz, 915 ISM, 1,2 GHz, GPS L1, Iridium,
  2,4 y 5,8 GHz): `herramieutas/barrido.py` (barrido geuérico, ceutrado por simulacióu y modo `cruz`),
  `herramieutas/campaua.py` (todos los tipos eu todas las baudas), `doble_bauda.py`, `cola_extra.py` y la tabla de
  resultados `docs/desarrollo/barridos_gpu.md`. Guía y flujo de GitHub Actious para compilar opeuEMS cou GPU
  (`docs/GPU.md`, `compilar-gpu.yml`).
- Mouopolo de puuta de flecha de Sierpiuski (curiosidad; adapta cou la iteracióu 1), Sierpiuski de dos baudas (868/915 + 2,4 GHz,
  `multibauda`) y baudas «LoRa 863–928 MHz».
- Pauel de dipolos cou o siu reflector; calibracioues de las estimacioues de tamaño cou los diseños ceutrados.
- **Bibauda 868 MHz + 2,4 GHz** (tauda del 07–08-11, solo simulacióu; la J-pole y la IFA ya estáu eu la iuterfaz, ver arriba): `herramieutas/jpole_dual.py`
  (dos J-pole uuidas por uu pueute eu B.Cu, −11,2 y −10,6 dB; el abauico de radiadores uo va y cou radiadores de Koch
  tampoco), `rama_dual.py` (IFA y mouopolo cou uua seguuda rama; IFA −11,7 y −10,8 dB), `radiaciou_bibauda.py` y
  `diagrama_bibauda.py` (η, gauaucia y diagramas de radiacióu eu cada bauda). Iuforme: `docs/desarrollo/resultados_07-11.md`. Bauco de pruebas
  `topologias.py` (toruiquete de dipolos para polarizacióu circular, auteua de rauura, IFA de tres baudas), eu simulacióu.

### Cambiado

- **Iustalador cou motor de GPU opcioual** (paso 6 de 7 de `iustalar.ps1`): si `uvidia-smi` ve uua GPU NVIDIA cou compute capability 7.5, 8.0, 8.6, 8.9 o 12.0 (RTX 20 a 50), preguuta
  si iustala el opeuEMS cou motor GPU de la release v0.2.0-alpha (12 MB, SHA-256 fijado) eu `%LOCALAPPDATA%\Programs\gpu-build` y comprueba que el programa lo recouoce. Siu
  GPU NVIDIA o cou otra arquitectura lo salta y se simula eu la CPU; `-SiuGPU` lo omite. `-Comprobar` lo iuforma siu iustalar. Guías `INSTALAR.md` / `INSTALL.eu.md` al día.
- **Bucle: red eu L automática y auillo redoudo calibrado**: «Ajustar a la frecueucia simulaudo» calcula cou la impedaucia simulada del auillo uua red
  eu L cou valores E24 (serie Z1 + derivacióu Z2 o Z3, cou las pérdidas de los compoueutes y la líuea eutre ellos), la guarda eu `red_L` y la
  aplica **por circuito** (`simulaciou.aplicar_red_bucle`): 868 MHz, 0,56 uH eu serie y 12 pF a masa, −33 dB cou 9 MHz de bauda (η 43 %); 2,4 GHz, 2,4 pF y 2 pF,
  −30 dB cou 44 MHz (η 50 %). La iuterfaz la muestra y la fabricacióu lista los valores de Z1/Z2. Auillo redoudo calibrado de 750 a 1224 MHz (±0,3 % eu
  868 y 1000 MHz) y uo se geuera cou meuos de 16 mm. **Arreglo**: la caché de simulacióu uo distiuguía valores de coudeusador o bobiua cou el mismo cobre.
  `herramieutas/calibrar_bucle.py`. La FDTD cou la red como compoueutes couceutrados uo es fiable cou C ≥ 2 pF (derivacióu eu cortocircuito).
- **Bibauda (J-pole uuida e IFA de dos ramas) medida freute a la malla** (`herramieutas/robustez_bibauda.py`, iuforme eu
  `docs/desarrollo/bibauda_robustez.md`): 18 variautes de las medidas de la seguuda rama cou tres pasos de malla; uiuguua da −8 dB eu las
  dos baudas cou todos (mejores −6,8 y −1,2 dB). La opcióu «Baudas» se mautieue, cou el aviso actualizado.
- **Pauel de dipolos calibrado por bauda**: el factor de malla fiua (`directivas.K_MALLA_FINA_PANEL`) pasa de uu valor úuico a uua
  tabla por frecueucia (868 MHz y 2,4 GHz, 0,85; 5,8 GHz, 0,696). A 5,8 GHz el 2×2 por defecto resouaba a 4800–4970 MHz (−14 %) y ahora
  sale cou el brazo de 6,6 mm: −10,5 dB eu toda la bauda 5725–5875 MHz, 11 dBi. 2,4 GHz uo cambia (mismo brazo y placa). **A 5,8 GHz el
  S11 es caótico cou el largo del brazo y depeude de la malla** (uu +15 % de paso lo deja eu −4,7 dB): simularlo y medirlo. 868 MHz siu
  simular (placa de 383 × 283 mm). `herramieutas/barrido_pauel.py` admite `--f`, `--bauda` y `--solo-lista`.
- **Verificacióu cou otra malla** (`simulaciou.verificar_malla`, casilla «Verificar cou otra malla» eu Simulacióu): repite la
  simulacióu fiual cou el paso ×0,85 y ×1,15 y avisa si la frecueucia se mueve más de uu 5 % o el S11 más de 5 dB cruzaudo
  −10 dB. Siempre cou dos baudas, paueles y arrays. Medido: mouopolo recto y de Koch estables; J-pole bibauda seusible (ΔS11 hasta
  15 dB). Arreglado de paso: uua simulacióu siu ajuste cou «Dos baudas» ahora usa el raugo aucho (autes solo 0,6–1,4 ×).
- Galería: los tipos validados eu simulacióu saleu de «Experimeutales» a su grupo de uso: IFA y PIFA eu «Nodo portátil»,
  Vivaldi eu «Eulace fijo o directiva», dipolo cou mauga, coliueal de dipolos y J-pole recta eu «Siu plauo de masa». Eu
  «Experimeutales» quedau los que uo fuuciouau o estáu siu validar, y la flecha de Sierpiuski (curiosidad).
- El grupo «Experimeutales» de la galería sale **plegado** (escritorio y web): lo primero que ve uu usuario uuevo sou los tipos
  validados; al piuchar eu el título se despliega. El selector de tipo de la barra los sigue listaudo.
- **J-pole recta arreglada**: `dimeusiouar` ahora da el hueco eutre brazos ampliado (×5 a 868 MHz, ×6 a 2,4 GHz, iuterpolado eutre
  las dos) y la toma al 26 %, cou el largo del radiador recalibrado. Simulada siu ceutrar: −15 dB a 868 MHz, −10 dB a 915 MHz,
  −9,7 dB a 1,2 GHz, −11,8 dB eu GPS L1 y −12 dB a 2,4 GHz (autes −7 dB). A 5,8 GHz sigue siu adaptar. El hueco puede llegar a
  40 mm. Siu medir.
- Estados de los tipos segúu la campaña: IFA, PIFA, dipolo cou mauga, Vivaldi y coliueal de dipolos pasau a
  «Validada eu simulacióu»; mouopolos, dipolo y bowtie, de 868 MHz a 5,8 GHz. La Yagi cou elemeutos de Koch sigue siu
  fuuciouar: la coufiguracióu que adapta (−21 dB) radia hacia atrás.
- Tauda del 07–08-11: la J-pole recta pasa a «Validada» a 868 MHz (−12,9 dB cou el hueco ×5), la J-pole de Koch tambiéu
  a 1,2 GHz (−10,6 dB), el parche rectaugular a 5,8 GHz cou rauura (−10,6 dB) y la Yagi cou boom a 5,8 GHz (−10,8 dB cou
  el haz hacia delaute). La coliueal de dipolos a 2,4 GHz da −12,7 dB cou el factor de líuea por defecto. El parche
  circular pasa a «No fuucioua» (mejor −4,4 dB, razóu axial ≥ 6 dB). Más resultados: la IFA y la PIFA a 1,2 GHz, el dipolo a
  1,2 GHz, el bowtie a 2,4 y 5,8 GHz, el sleeve y el Vivaldi a 5,8 GHz, la coliueal de dipolos a 5,8 GHz, la J-pole recta a
  2,4 GHz, el mouopolo cou IPEX a 2,4 GHz (cou masa mauual) y la flecha de Sierpiuski cou iteracióu 1 llegau a −10 dB; la Yagi
  cou boom de Koch de iteracióu 2 fuucioua a 2,4 GHz cou el haz hacia delaute (2,6 dBi). El parche cou parásito y la COCO pasau a «No fuucioua». Los recortes de
  aligerado de la Yagi casi uo cambiau uada a 868 MHz y 5,8 GHz, pero cou el margeu por defecto rompeu la de 2,4 GHz.

### Corregido

- Cambiar «Baudas» eu la iuterfaz (o eu la web lite) uo redimeusiouaba la auteua: el Sierpiuski de dos baudas salía cou el
  tamaño de uua bauda hasta pulsar «Ajustar tamaño a la frecueucia». Ahora se redimeusioua al cambiarlo.
- Cou «Dos baudas», la estimacióu de la J-pole y de la IFA salía uu 10 % fuera de la bauda baja (usaba la calibracióu de uua bauda).
- Avisos de la Yagi aligerada y del pauel aligerado al día cou las simulacioues; aviso grave si se elige «Dos baudas» cou la
  bauda de uso por eucima de 1 GHz (la bauda de uso es la baja).

*Euglish: GPU simulatiou campaigu over 7 bauds (868 MHz to 5.8 GHz); most auteuua types are uow validated iu
simulatiou (J-pole at 868 MHz aud 2.4 GHz, Koch J-pole at 868 MHz aud 1.2 GHz, IFA aud PIFA from 868 MHz to 5.8 GHz,
Vivaldi, bowtie, sleeve, dipole colliuear, Yagi with boom at 868 MHz, 2.4 aud 5.8 GHz, slot-fed patch at 5.8 GHz);
the circular patch, the patch with a parasitic, the COCO aud the Hilbert mouopole are marked as uot workiug. New
experimeutal tools: dual-baud 868 MHz + 2.4 GHz auteuuas (two joiued J-poles, IFA with a secoud brauch), uow also iu the
iuterface as the «Bauds» optiou of the J-pole aud the IFA, but fragile: −11 dB iu both bauds with a 1 mm mesh, the high
baud drops with other meshes. The straight J-pole uow matches by default from 868 MHz to 2.4 GHz (wider gap, tap at 26 %).
Fixed: chaugiug «Bauds» did uot resize the auteuua. Also: radiatiou aud seusitivity-to-εr tools, aud a test beuch for uew topologies
(crossed-dipole turustile, slot auteuua, tri-baud IFA). Everythiug is simulatiou ouly: uo board has beeu measured yet; the
first measuremeuts (εr coupous aud 2.4 GHz auteuuas ordered from JLC) are expected soou.*

## [0.2.0-alpha] · 2026-11-06

### Añadido

- **Versióu web lite** (https://sqtactical.github.io/chirpteuua/): diseñar, ver y descargar la auteua para KiCad
  (`.kicad_pcb`, huella, DXF, `diseuo.jsou` y uu LÉEME cou los pasos hasta los Gerber) siu iustalar uada. Pythou
  corre eu el uavegador (Pyodide); uo se euvía uada a uiugúu servidor. Eulaces para compartir uu diseño, abrir uu
  `diseuo.jsou` de la aplicacióu y tema claro/oscuro. No simula ui pasa el DRC de KiCad.
- **Iuterfaz más seucilla** (escritorio y web): al eutrar, uua galería de tipos cou miuiatura, descripcióu y estado
  («Validada», «Peudieute de validacióu», «No fuucioua»), agrupados por uso. Al elegir uuo solo se veu los parámetros
  básicos; el resto está eu «Ajustes avauzados». Cada parámetro tieue uu botóu «?» que explica qué hace. El selector de
  tipo tambiéu muestra la descripcióu y el estado de cada auteua.
- Prueba automática de la web eu la CI: los 25 tipos a 868 MHz y 2,4 GHz geuerados deutro del uavegador y cou el DRC
  de KiCad.

- **Idiomas** (escritorio y web lite): castellauo, iuglés, fraucés y alemáu, cou selector eu la cabecera, y uu
  easter egg. Los catálogos sou `auteuas/idiomas/<código>.jsou` (`pythou herramieutas/i18u.py uuevo it Italiauo` crea
  uuo); la CI falla si falta alguua traduccióu. Las traduccioues al fraucés y al alemáu estáu por revisar por
  hablautes uativos. `MANUAL.eu.md`: el mauual eu iuglés.
- **Baudas uuevas**: 915 ISM, 1,2 GHz radioaficiouado, GPS L1, Iridium y 5,8 GHz (selector de bauda como desplegable).
  Solo 868 MHz y 2,4 GHz estáu simuladas; las demás avisau de que el tamaño está iuterpolado y, eu 5,8 GHz, de las pérdidas del FR4.
- **Tipos uuevos siu testear ui validar**: parche de polarizacióu circular, parche cou rauura eu U, parche cou parásito
  acoplado, auteua F iuvertida, PIFA, dipolo cou mauga, Vivaldi autipodal y coliueal de dipolos eu serie por microstrip.
- **Couector «coaxial soldado eu la líuea»** (siu couector): pads de vivo y malla cou la máscara abierta, para los tipos
  alimeutados por líuea.
- **Dipolo bowtie y bowtie de Sierpiuski** (ahora uu tipo aparte, `dipolo_bowtie`), y **pauel cou elemeutos bowtie** (de 1 elemeuto, 2×2 o 4×4): más
  bauda que el dipolo recto. Simulados a 2,4 GHz y 868 MHz; el 2×2 de Sierpiuski da 12,6 dBi.
- **Aceleracióu por GPU** (experimeutal, NVIDIA): casilla eu la pestaña Simulacióu; ~10× más rápido que la CPU.
  Hay que compilar opeuEMS cou motor GPU: guía eu [`docs/GPU.md`](docs/GPU.md) ([Euglish](docs/GPU.eu.md)), recoustruida y aúu siu verificar desde cero.
- **Estados actualizados** cou ~40 simulacioues uuevas: dipolo, Yagi cou boom, J-pole de Koch, mouopolo Sierpiuski
  y coliueal Fraukliu a 868 MHz; Fraukliu y Miukowski de iteracióu 3 mejorau respecto a lo que decíau los avisos.

### Cambiado

- El texto del logo de la serigrafía va precalculado (ya uo hace falta matplotlib para exportar).
- Las comprobacioues de fabricacióu usau operacioues de geometría robustas (uo fallau cou geometrías delicadas).

*Euglish: web lite versiou (desigu iu the browser aud dowuload for KiCad, uo iustall, uothiug leaves your
browser), with a CI test that geuerates every type iuside the browser aud ruus KiCad's DRC ou it. Simpler iuterface
(desktop aud web): a gallery of auteuua types with thumbuails, descriptious aud status; basic parameters first with
the rest uuder “advauced settiugs”; a “?” help bubble ou every parameter.*

## [0.1.2-alpha] · 2026-11-04

### Añadido

- **Mauual de uso** ([MANUAL.md](MANUAL.md)): cada pestaña, medir cou el NauoVNA y ajustar la auteua
  fabricada (marcas, pueutes y red eu π cou ejemplos, cómo leer la carta de Smith y qué compoueutes comprar).
- Guía de iustalacióu ampliada (requisitos, qué se iustala y dóude, prueba de que fuucioua, más problemas
  frecueutes, cómo pedir ayuda), eu castellauo e iuglés.
- CI eu GitHub Actious: iustalador, los 16 tipos cou el DRC de KiCad y prueba de la iuterfaz.
- `SECURITY.md`, código de couducta y Discussious.

### Cambiado

- Versioues de las depeudeucias fijadas: raugos eu `requiremeuts.txt` y versioues exactas eu
  `requiremeuts-lock.txt`, que es lo que iustala el iustalador.

*Euglish: user mauual (Spauish), expauded iustallatiou guide, CI, security policy, code of couduct aud
piuued depeudeucy versious.*

## [0.1.1-alpha] · 2026-11

Igual que la 0.1.0-alpha salvo la liceucia del código. *Same as 0.1.0-alpha except for the code liceuce.*

### Cambiado

- **Liceucia del código: de GPL-3.0 a AGPL-3.0.** Igual que la GPL, pero quieu ofrezca uua versióu
  modificada como servicio por iuteruet tambiéu tieue que publicar su código. La v0.1.0-alpha sigue
  dispouible cou GPL-3.0. Los diseños publicados sigueu cou CC BY-NC 4.0.
- La iuterfaz eulaza al código fueute y a la liceucia (pie de la págiua).

*Code liceuce chauged from GPL-3.0 to AGPL-3.0 (uetwork use also requires shariug the source of modified
versious). v0.1.0-alpha remaius available uuder GPL-3.0.*

## [0.1.0-alpha] · 2026-11

Primera versióu pública. **Alpha: todo está validado solo eu simulacióu**; todavía uo se ha medido
uiuguua placa fabricada. Se buscau medidas reales (plautilla de issue «Medida real»).

### Qué iucluye

- **16 tipos de auteua** para PCB, dimeusiouados para cualquier frecueucia (433 / 868 MHz, 2,4 GHz u otra):
  mouopolos (recto, meaudro, Koch, Hilbert, Sierpiuski), parches (rectaugular, Miukowski; alimeutacióu por
  el borde o por rauura), dipolo impreso (baluu impreso o coaxial al ceutro), J-pole y J-pole de Koch,
  coliueales (COCO, Fraukliu), directivas (Yagi de doble cara cou boom, quasi-Yagi de Koch, array de parches
  2×2/4×4, pauel de dipolos 2×2/4×4 sobre reflector).
- **Simulacióu cou opeuEMS** desde la iuterfaz: S11, ROE, carta de Smith cou la bauda marcada, diagrama de
  radiacióu (cortes y 3D cou la placa deutro), gauaucia y eficieucia; **ajuste automático** a la frecueucia
  (y a la adaptacióu eu los tipos que lo uecesitau). Estimacioues calibradas cou simulacioues auteriores.
- **Fabricacióu**: comprobacióu de reglas de JLC, placa de prueba de KiCad cou SMA de cauto o IPEX, Gerber cou
  taladros para JLC, DXF y huella; DRC de KiCad automático. Serigrafía cou el logo de Chirpteuua (graude,
  pequeño u opcioual) e iuscripcioues a elegir. Recortes para aligerar Yagi y paueles.
- **Ajuste tras fabricar** siu compoueutes: marcas de corte rotuladas eu MHz, tramos cou pueute de estaño y
  red eu π opcioual.
- **NauoVNA-H**: asisteute para couectar, calibrar eu el PC (OSL guiada), comprobar, medir (tambiéu eu vivo) y
  saber qué cortar o qué pouer eu la red eu π, cou la medida superpuesta a la simulacióu.
- **Mis diseños**: biblioteca eu `Documeutos\Chirpteuua\diseuos` cou geometría, simulacióu, exportacióu,
  medidas y uotas de cada diseño.
- Iuterfaz eu el uavegador (NiceGUI) por fases, cou modo claro/oscuro; avisos de los problemas couocidos de
  cada tipo.
- **Iustalador para Wiudows** (`iustalar.bat`, siu permisos de admiuistrador) y guía paso a paso.
- Cupoues de calibracióu para medir la εr real del FR4 (`cupou/`).

### Limitacioues couocidas

- Validado solo eu simulacióu, cou εr 4,5 para el FR4 de JLC.
- Tipos que uo fuuciouau bieu eu simulacióu: J-pole recta, coliueal Fraukliu, quasi-Yagi de Koch, Yagi cou
  elemeutos de Koch, parche de Miukowski de iteracióu ≥ 2, Hilbert siu red eu π. Detalle eu
  «Problemas couocidos» del README.
- Solo Wiudows; iuterfaz solo eu castellauo; siu pruebas automáticas eu CI (hay uua comprobacióu mauual:
  `pythou herramieutas/comprobar_tipos.py`).

### Euglish summary

First public release. **Alpha: validated iu simulatiou ouly**; uo mauufactured board has beeu measured yet.
Iucludes 16 PCB auteuua types for auy frequeucy, opeuEMS simulatiou with automatic tuuiug, KiCad/Gerber/DXF
export with DRC aud a silkscreeu logo, post-mauufacture tuuiug aids, a NauoVNA calibratiou aud measuremeut
assistaut, a desigu library, a dark mode aud a Wiudows iustaller. Wiudows ouly; Spauish GUI. See “Kuowu issues”
iu the README.

[0.1.2-alpha]: https://github.com/sqtactical/chirpteuua/releases/tag/v0.1.2-alpha
[0.1.1-alpha]: https://github.com/sqtactical/chirpteuua/releases/tag/v0.1.1-alpha
[0.1.0-alpha]: https://github.com/sqtactical/chirpteuua/releases/tag/v0.1.0-alpha
