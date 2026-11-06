# Chirptenna manual

*Alpha version. Installation: [INSTALL.en.md](INSTALL.en.md). This is the English translation of [MANUAL.md](MANUAL.md); the interface has
an English mode (selector at the top right), and the names in **bold** are the ones it shows.*

This manual explains how to use Chirptenna from start to finish: design an antenna, simulate it, send it to be
manufactured, measure it and **tune** it once built, with cut marks, bridges and the **π network**.

> **First of all:** Chirptenna is in alpha and what it computes is validated **in simulation only**. The real
> board almost never comes out exactly on frequency: FR4 varies from batch to batch, and the case, the
> battery and the cable shift it. That is why the antennas have tuning options and why **you have to measure**
> before trusting them.

**Contents**

1. [Concepts in 5 minutes](#1-concepts-in-5-minutes)
2. [The workflow](#2-the-workflow)
3. [The design bar](#3-the-design-bar)
4. [Design tab](#4-design-tab)
5. [Simulation tab](#5-simulation-tab)
6. [Manufacture tab](#6-manufacture-tab)
7. [Assembling the board](#7-assembling-the-board)
8. [Measure tab](#8-measure-tab)
9. [Tuning the manufactured antenna](#9-tuning-the-manufactured-antenna)
10. [The π network in depth](#10-the-π-network-in-depth)
11. [My designs tab](#11-my-designs-tab)
12. [Which antenna to choose](#12-which-antenna-to-choose)
13. [Common problems](#13-common-problems)
14. [Glossary](#14-glossary)

---

## 1. Concepts in 5 minutes

- **Resonant frequency.** The frequency at which the antenna «fits» the radio. It mainly depends on its
  length: **longer, lower frequency**; shorter, higher.
- **S11 (return loss), in dB.** How much power bounces off the antenna and comes back to the radio. The more
  negative, the better:

  | S11 | VSWR | Power that enters the antenna | Rating |
  |---|---|---|---|
  | −3 dB | 5.8 | 50 % | Bad |
  | −6 dB | 3.0 | 75 % | Poor |
  | **−10 dB** | **1.9** | **90 %** | **Good: the usual criterion** |
  | −15 dB | 1.4 | 97 % | Very good |
  | −20 dB | 1.2 | 99 % | Excellent (beyond this point, improving is not noticeable) |

- **VSWR.** The same as S11 on another scale: 1 is perfect; below 2 is fine.
- **Band at −10 dB.** The range of frequencies where S11 is below −10 dB. Your band of use (for example,
  869.4–869.65 MHz on Meshtastic EU) has to fall **inside** it, with some margin.
- **Impedance (Z = R + jX).** The radio and the cable are **50 Ω**. The ideal antenna presents R = 50 Ω and
  X = 0. If R is far from 50 or X is not zero, part of the power bounces back.
  - Positive X = the antenna behaves like a **coil** (inductive), typical if it is **too long**.
  - Negative X = it behaves like a **capacitor** (capacitive), typical if it is **too short**.
- **Smith chart.** A drawing of the impedance at each frequency. The **centre** is a perfect 50 Ω, the
  **upper** half is inductive and the **lower** half, capacitive. Chirptenna draws the VSWR-2 circle
  (inside it = S11 < −10 dB), the edges of your band (●) and the target (★). Tuning an antenna is
  moving the ★ to the centre.
- **Gain (dBi)** and **efficiency (η).** Gain says how much the antenna concentrates in its best
  direction. Efficiency, what share of the power that goes in is really radiated: the rest is lost as
  heat, mostly in the FR4. An antenna can be perfectly matched (S11 −20 dB) and still radiate
  little if its η is low.

---

## 2. The workflow

The tabs follow the order of the work:

```
Design ──► Simulation ──► Manufacture ──► (JLC) ──► assemble ──► Measure ──► tune ──► Measure…
 type,      openEMS:        rules,                    SMA and      NanoVNA    cut,
 band,      S11, Smith,     Gerber,                   components   or .s1p    bridges,
 size       pattern         silkscreen                                        π network
```

- **Simulating is optional.** The initial size comes from formulas calibrated with earlier simulations and is
  usually within 0–3 % of what the simulation gives. Simulating is for confirming the band, seeing the
  radiation pattern and fine-tuning before paying for manufacturing.
- **Save the design** (**Save design** button). Each design keeps in its folder the simulation, the
  manufacturing files and the measurements, so you can compare them later.

---

## 3. The design bar

When you open the program you get the **Choose antenna** tab: the types grouped by use (portable node, fixed link, no
ground plane and experimental), each with a drawing, a description and its status: **Validated** (in simulation),
**Pending validation** or **Does not work**. Clicking one sizes it for the chosen band and moves to Design.

The bar is always at the top:

| Field | What it is |
|---|---|
| **Design name** | The folder name in *My designs*. Changing it and saving creates a new design (useful for variants) |
| **Antenna type** | See [which antenna to choose](#12-which-antenna-to-choose). The list shows the description and status of each type. Under the bar the type's **known problems** appear: read them |
| **Band of use** | 433, 868, 2.4 or 5.8 GHz fill in the centre and the width (5.8 GHz: not simulated or validated, and FR4 is very lossy; the Hilbert and the Koch quasi-Yagi cannot be manufactured there). With **Other** you enter them by hand (e.g. 915 MHz in the Americas) |
| **Centre [MHz]** | The target frequency. For Meshtastic, enter the real frequency of your channel (on EU_868 with LongFast, 869.525 MHz; check it in the Meshtastic app) |
| **Width [MHz]** | The width the antenna has to cover. Enter that of your channel or band; the program adds margin |

> **Meshtastic tip:** centre the antenna on your channel, not on the centre of the 868 MHz band. That way,
> with the 5–10 MHz bandwidth of a monopole, you keep margin on both sides for whatever the case and the
> battery shift.

---

## 4. Design tab

### Size and material

- **Substrate.** The material and thickness of the board: JLC FR4 of 1.6 / 1.2 / 1.0 / 0.8 mm or Rogers
  RO4350B. 1.6 mm FR4 is the cheapest and the one used for validation. RO4350B loses far
  less (more efficiency, especially in patches and arrays), but is considerably more expensive.
- **Resize to the frequency.** Recomputes the dimensions so that the antenna resonates at the chosen
  centre. **Press it whenever you change band, type or substrate.** It respects the dimensions you have
  set by hand.
- **Widen bandwidth.** If the estimated band does not cover the requested width, it widens the track (monopoles and
  Yagi) or the patch, keeping the frequency. It tells you whether it already covers the band or how far it got.

### Parameters

They change with the type. The **basic** ones come first; the rest are folded under **Advanced settings** (margins,
gaps, track widths, fine tuning options…), and you normally do not need to touch them. Each parameter has a
**?** button: press it to see what it does. The most common ones:

- **Antenna dimensions** (length, track width, fractal iteration…). The **iteration** of a fractal makes it more compact, but usually narrows the band and lowers
  the efficiency.
- **Ground plane** (monopoles): a ground plane of **λ/4 or more** is ideal. A shorter one shrinks the
  board, but forces you to lengthen the radiator and makes the antenna more sensitive to whatever is connected behind it.
- **Connector:** edge-mount SMA (to test and measure) or IPEX/U.FL (to integrate it). With IPEX the match
  is still under review: read the known problems.
- **Tuning after manufacture** (monopoles, patches, J-pole, quasi-Yagi). Set it to **Tunable** for a
  first batch: it adds the [tuning options](#9-tuning-the-manufactured-antenna) (extra length with marks,
  sections with bridges and π network). Once you have a tuned and measured version, you can manufacture
  the final one without them.
- **Lightening windows** (Yagi and panel): windows without FR4 to reduce weight. **Not simulated**: removing FR4 raises the
  frequency a little.

### Result and tips

- **Result (estimate):** board size, estimated frequency, band, approximate gain and
  warnings. They are estimates; the simulation refines them.
- **Tips:** recommendations for that specific design (track too thin, short ground plane, tight
  band…).

---

## 5. Simulation tab

Simulates the antenna with **openEMS** (a full-wave electromagnetic simulator, FDTD).

1. **Precision:**
   - **fast** for a quick look (±3 %);
   - **normal** for designing;
   - **fine** for the final check, slower.
2. **Tune to the frequency by simulating:** if checked, it simulates, corrects the size and repeats (2–5
   simulations) until the centre of the −10 dB band falls on the target. If not, it runs just one.
3. **Simulate.** The log shows the progress. You can keep using the rest of the interface.

**GPU acceleration (experimental).** If you have an NVIDIA card and an openEMS build with a GPU engine (see
`RETOMAR.md`), the checkbox appears enabled and simulations are about 10 times faster. In tests, frequency,
S11 and impedance agree with the CPU, but gain and efficiency come out a little high: confirm the final
values on the CPU.

**How long it takes:** 1 to 15 minutes per simulation for a 2.4 GHz monopole. At 868 MHz, with thin tracks,
or on arrays and panels, it can take hours. Results are cached: repeating the same geometry is
instant.

### How to read the results

- **S11** and **VSWR**: the curve must drop below −10 dB (or VSWR 2) across your whole band (shaded area).
- **Smith chart:** the closer the ★ passes to the centre, the better. If the curve makes a **loop** near the
  centre, the band is wider.
- **Radiation pattern:** polar cuts and a 3D view with the board drawn inside. Look at where the
  maximum points (the arrow). On directional antennas (Yagi, panel) it must point **forwards**.
- **Gain and efficiency:** an η below 50 % indicates large losses in the FR4. If it comes out below
  10 %, the program warns you: something in the model is not right.

If the design was saved and you have not changed it, the result is saved with it. If the simulation tuned the
size, press **Apply the tuned parameters** to pass them to the design.

---

## 6. Manufacture tab

### Manufacturing checks

Choose the **manufacturer rules** (JLC standard, JLC minimum or relaxed). The list warns about tracks or gaps
below what the manufacturer can do, copper too close to the edge and the **known
problems** of the antenna type.

### Export

**Export KiCad + Gerber + DXF** saves the design and creates in its `fabricacion` folder:

| File | What it is for |
|---|---|
| **Gerber for JLC (.zip)** | Upload as is to JLCPCB (or another manufacturer). It has copper, mask, silkscreen, outline and drills |
| **KiCad test board (.kicad_pcb)** | The full board with its connector, to open or modify in KiCad |
| **KiCad footprint (.kicad_mod)** | Just the antenna, to put inside **your own board** |
| **DXF** | The drawing for EasyEDA or other programs |
| Reflector (panel) | A second board (or sheet) that acts as the reflector |

When it finishes, the **KiCad DRC** is run. It must come out with no errors.

**When ordering at JLCPCB:** upload the Gerber zip and choose 2 layers, the **material and thickness of the substrate you
set in the design** (1.6 mm FR4 by default), any mask colour and the finish you want
(HASL or ENIG). The thickness matters: changing it shifts the frequency and spoils the 50 Ω line.

> **If you are going to put the antenna on your board using the footprint:** respect the **keep-out area** with no copper or components
> around the radiator, and use the same 50 Ω line and the same board thickness. The ground plane of your
> board becomes part of the antenna: on a monopole, its size changes the frequency.

### Silkscreen (inscriptions)

They go on the bottom face, mirrored so they read when you turn the board over. You can choose:
- the **Chirptenna logo** (large, small or none);
- the type and frequency, the design name, the simulation result, the licence, the date;
- free text.

If everything does not fit, the logo and the first line are kept. The **cut marks**, the «vivo»/«malla»
(live/braid) labels and the component references (Z1, Z2, Z3, JP…) are always added: they are needed for tuning. The
labels on the board use the interface language.

---

## 7. Assembling the board

1. **Edge-mount SMA connector:** centre the pin on the 50 Ω track and solder the centre pin on top. Solder
   the ground legs **on both faces**: a badly soldered ground changes the measurement.
2. **π network:** if the design has it, the board comes with three positions (0603 or 0402 footprint):
   - **Z1**, in series with the track, with a gap that has to be closed. For the first measurement fit a
     **0 Ω resistor** (or a solder bridge);
   - **Z2** (connector side) and **Z3** (antenna side), from the track to ground. **Leave them empty.**
3. **Sections with bridges:** they come **open**. Do not close them yet.
4. Clean flux residue with isopropyl alcohol: at 2.4 GHz, a thick layer of flux is noticeable.

---

## 8. Measure tab

### With a NanoVNA (assistant)

The assistant has four steps:

1. **Connect the NanoVNA.** Press **Find the NanoVNA**. Only its status is read: its calibration and saved
   slots are never touched.
2. **Calibration.** Choose a saved calibration or **Calibrate now**:
   - Calibrate **at the end of the patch cable you will use with the antenna**. That is where the measurement plane ends up.
   - The range it proposes goes from 0.6 to 1.4 times the design frequency. 301 points is a good compromise.
   - Follow the instructions: **OPEN** (nothing connected), **SHORT** (short circuit) and **LOAD** (50 Ω
     load), each at the end of the patch cable. If you fit the wrong standard, the program detects it and
     warns you.
   - **Save calibration** keeps it on the PC for other times. It is valid as long as you use the same patch cable and the
     same range.
3. **Check the calibration.** Fit the **50 Ω load** and press **Check**. Well calibrated, |S11|
   stays below **−30 dB**. If not, repeat the calibration.
4. **Measure and tune.** Connect the antenna:
   - Write a **label** saying what you changed («uncut», «Z1 3.3 nH»…) and press **Measure and
     save**. The measurement is saved in the design and overlaid on the simulation.
   - **Live** mode repeats the measurement every few seconds around the band, **without saving it**, and
     shows the resonance, the S11 at the target and the first recommendation. It is for cutting little by
     little. **Save this measurement** saves the latest one.

### With another analyser

Measure with its software, export an **`.s1p`** (1-port Touchstone) and upload it with **…or upload an .s1p**.
You can also skip the NanoVNA with **Skip (upload an .s1p)**.

### How to measure properly

- Measure the antenna **under the conditions of use**: inside its case, with the battery and the node board
  connected if they sit next to it. The plastic case usually **lowers** the frequency by 1–5 %.
- **Keep away:** neither your hand nor your body within a hand's width, and nothing metallic nearby. Leave the NanoVNA on the
  table and the antenna at the edge, pointing outwards.
- Always use **the same patch cable** you calibrated with, and do not bend it between the calibration and the
  measurement.
- If the curve changes when you touch the cable, the coax braid is radiating: try a shorter patch cable
  or a few ferrites on the cable.

---

## 9. Tuning the manufactured antenna

### Order matters

1. **Frequency first**: bring the resonance to your channel by **cutting** (marks) or **lengthening**
   (bridges).
2. **Then the match**: if at your channel S11 is still above −10/−15 dB, improve it with the **π
   network**.

Do not use the π network to correct an antenna that is far off in frequency: it can be matched, but the band
narrows a lot and the losses in the components rise. As a reference, the π network corrects deviations of
up to 2–3 % well; beyond that, cut or close bridges first.

### The tuning assistant

In **Simulated versus measured**, press **Analyze** on a measurement (new ones are analysed automatically). The
assistant tells you:

- the **measured resonance** and how far it deviates from the target (in %);
- the **S11 and the impedance Z at your target frequency**. Z is **translated to the position of the π
  network**: it subtracts the stretch of track between the SMA and Z1;
- **what to do**: which mark to cut, how many bridges to close or what to fit in the π network;
- if there is an earlier measurement, **what has changed** compared with it.

### Cut marks (raising the frequency)

With the **extra length** enabled, the antenna comes out deliberately lengthened (3 % by default), so it resonates
**below** the target. The silkscreen marks several cut points with the **frequency in MHz** that
remains if you cut there.

- The assistant tells you which mark to cut, **correcting the silkscreened numbers** with what you have
  measured. Note: the printed numbers are the design's estimate, and the assistant is more reliable.
- **Cut little by little.** First one mark fewer than it says, measure and carry on. Cutting is very hard to
  undo.
- Cut with a blade or a cutter, from side to side of the track. Lift the piece of copper with the tip
  and check with a multimeter that no thread remains joining the two parts.
- On the **rectangular patch**, the marks are lines parallel to the top edge: cut the whole patch
  at the mark.

### Sections with bridges (lowering the frequency)

At the end of the radiator there are several loose sections, separated by a gap. Each bridge you close
**lengthens** the antenna and **lowers** the frequency one step (1.5 % by default; the design note gives the real
step).

- Close them **in order, starting with the one nearest the radiator**. A bridge closed beyond an
  open one does nothing.
- Solder bridge: a drop of solder joining the two half pads. With a 0 Ω resistor: solder it in
  its footprint.
- To go back, remove the solder with desoldering braid.

**Marks and bridges together:** with both enabled you can go in both directions. If the antenna comes out
high, you close bridges; if it comes out low, you cut at the marks.

---

## 10. The π network in depth

### What it is

Three component positions on the 50 Ω track, between the connector and the antenna:

```
 SMA ───┬────[ Z1 ]────┬─── antenna
        │              │
      [Z2]           [Z3]
        │              │
       GND            GND
  (connector side) (antenna side)
```

- **Z1** is **in series**. From the factory, a 0 Ω resistor (or a bridge).
- **Z2** and **Z3** go **to ground** (shunt). From the factory, empty.

With coils and capacitors in those positions the antenna's impedance is «transformed» so that the
radio sees 50 Ω. In practice **two components** are almost always enough: **Z1 plus one of the two
shunts**. That is an L network, and it is what the assistant proposes.

### Which shunt to use

It depends on the real part R of the impedance measured at Z1:

| Measured antenna | Shunt | Assembly |
|---|---|---|
| **R below 50 Ω** (the most common on monopoles with a small ground plane) | **Z2**, connector side | Z1 in series next to the antenna, and the shunt towards the connector |
| **R above 50 Ω** | **Z3**, antenna side | Shunt next to the antenna, and Z1 in series towards the connector |

The assistant already does this for you: it indicates the position and the commercial values (E24 series), and the S11
that would result with them.

### Step by step

1. **Tune the frequency first** with marks or bridges (section 9).
2. **Measure with the factory network** (Z1 = 0 Ω, Z2 and Z3 empty), under the conditions of use and with the label
   «factory network».
3. If at your frequency **S11 is already better than −15 dB**, the assistant will tell you to leave it as it is: **do not touch
   anything**. Every component adds some loss.
4. If not, look at the assistant's proposal and the **alternatives**. There are usually two solutions; choose
   following [the criteria below](#which-solution-to-choose).
5. **Fit the shunt first** (Z2 or Z3) and **then change Z1**. Measure with a label saying what
   you fitted («Z1 3.3 nH, Z2 1.2 pF»).
6. The assistant shows the change compared with the previous measurement and a new proposal. With real values,
   it is normal to need **one or two rounds**: going up or down one value of the E24 series.
7. When it is right, write the values in the **design notes** (*My designs*) and in the measurement.

### Which solution to choose

- **Low-pass (Z1 coil, shunt capacitor):** the preferred one. It attenuates the radio's harmonics and has
  no drawbacks.
- **High-pass (Z1 capacitor, shunt coil):** just as valid, and the coil to ground discharges static from
  the antenna. In return, it lets harmonics through.
- **Avoid extreme values:**
  - capacitors below **0.5 pF** or coils below **1 nH**: the capacitance of the pads and of the
    solder joints is already of that order (0.1–0.3 pF), so the real value will differ a lot from the nominal one;
  - very large series capacitors (more than ~50 pF at 868 MHz or ~20 pF at 2.4 GHz): they are almost a
    short circuit and equivalent to leaving the 0 Ω.
- If the two solutions give a similar S11, choose the one with the **more «normal» values** (a few nH or pF).

### Which components to buy

- **Capacitors:** **C0G/NP0** ceramics (not X7R or Y5V: they vary with temperature and voltage). At
  2.4 GHz, with a tolerance of **±0.1 pF** or ±0.05 pF for values below 5 pF.
- **Coils:** **RF** ones, wire-wound or high-Q multilayer (for example, Murata LQW/LQG or Coilcraft
  0402HP/0603HP), with a tolerance of ±2 % or ±0.1 nH. Check that their **self-resonant frequency
  (SRF) is at least double** your frequency. Power or filter inductors are no good.
- **Size:** the same as the board footprint (0603 by default, easier to solder by hand).
- **A sample kit** of RF capacitors and coils in 0603 or 0402 pays for itself if you are going to tune
  several antennas.

### Reading the Smith chart while tuning

Each component moves the impedance point in a fixed direction:

| Component | Position | Moves the point… |
|---|---|---|
| **Series** coil (Z1) | series | **up**, following its constant-R circle (clockwise) |
| **Series** capacitor (Z1) | series | **down**, following its constant-R circle (counter-clockwise) |
| Capacitor to **ground** (Z2/Z3) | shunt | **clockwise**, following its constant-G circle |
| Coil to **ground** (Z2/Z3) | shunt | **counter-clockwise**, following its constant-G circle |

How much each one moves it:
- **series coil**: more nH, the more it moves;
- **series capacitor**: the opposite, the **smaller** (fewer pF), the more it moves;
- **capacitor to ground**: more pF, the more it moves;
- **coil to ground**: the opposite, the **smaller** (fewer nH), the more it moves.

That way you can correct the next step even without the assistant at hand. If the ★ has ended up a little
above the centre (inductive), lower the series coil value or raise the series capacitor.

### Examples

Computed with the same assistant:

**868 MHz monopole with a short ground plane**, measured at 869.525 MHz: Z = 22 − 18j Ω, S11 −7 dB.
R is below 50 Ω, so the shunt goes in **Z2** (connector side):
- solution 1: Z1 = **27 pF**, Z2 = **8.2 nH** → S11 ≈ −44 dB (high-pass);
- solution 2: Z1 = **7.5 nH**, Z2 = **4.3 pF** → S11 ≈ −27 dB (low-pass).

Both leave the antenna well below −15 dB. Number 2 filters harmonics, and −27 dB is more than enough.

**2.4 GHz monopole**, measured at 2441.75 MHz: Z = 95 + 30j Ω, S11 −8.7 dB. R is above 50 Ω, so the
shunt goes in **Z3** (antenna side):
- solution 1: Z1 = **1.2 pF**, Z3 = **9.1 nH** → S11 ≈ −32 dB;
- solution 2: Z1 = **3.3 nH**, Z3 = **0.82 pF** → S11 ≈ −31 dB.

Here solution 2 has a 0.82 pF capacitor, too close to the capacitance of the pads: number 1 will be
more predictable.

### Limits of the π network

- **Adjusting the match does not fix an antenna that radiates little.** If the simulated η is low (Minkowski
  patch of iteration 3, COCO), the π network gets the power in, but not radiated.
- With **R below ~10 Ω or above ~250 Ω**, the match will be very narrow and lossy.
  Better to redesign: larger ground plane, another iteration or another type.
- A network tuned for one environment (inside the case) is not valid for another (in free air). Tune **in the
  final environment**.

### Which types have it

Monopoles (straight, meander, Koch, Hilbert and Sierpinski), patches, patch array and quasi-Yagi. The J-pole
is tuned only with marks and bridges. The Yagi with boom, the panel, the dipole and the collinears do not yet
have tuning options.

---

## 11. My designs tab

Each design is a folder in `Documentos\Chirptenna\disenos\<name>` with:
- `diseno.json` (type, parameters, band, silkscreen);
- `simulacion/`;
- `fabricacion/`;
- `medidas/`.

In the table you can:
- **Open** a design;
- open its **folder**;
- **Rename**;
- **Archive**: moves it to `_archivados` and deletes nothing.

The **design notes** work as a notebook: order date, batch, which mark you cut, which components
you fitted. In six months you will be glad to have them.

To share a design, compress its folder. Another person can copy it into their library and open it.

---

## 12. Which antenna to choose

| For… | Recommended | Why |
|---|---|---|
| A portable Meshtastic node (868/915 MHz) | **Koch monopole** or **meander**, with tuning and π network | Compact, omnidirectional, validated at 868 MHz |
| The reference antenna for comparison | **Straight monopole** | The most predictable: if this one does not work out, the problem is the measurement or the material |
| Compact 2.4 GHz | **Koch monopole** or **Sierpinski** | Validated at 2.4 GHz; the Sierpinski has more bandwidth |
| A point-to-point link | **Yagi with boom** (straight elements) or **2×2/4×4 panel** | 6–7 dBi the Yagi, 12–17 dBi the panel, in simulation |
| An antenna without a ground plane | **Koch J-pole** or **dipole** | They do not depend on the board they are connected to |
| Experimenting | Hilbert, Minkowski, quasi-Yagi, COCO, Franklin | They have known problems: read them first |

The full table of what is validated is in the [README](README.en.md#antenna-types).

---

## 13. Common problems

| Symptom | Probable cause | What to do |
|---|---|---|
| The measured resonance is 3–8 % **below** the simulated one | Real FR4 εr different from 4.5, plastic case, flux | Normal in alpha. Close fewer bridges or cut at the marks. If it always happens to you, share it in a «Real measurement» issue: it helps calibrate the program |
| It comes out **above** | Board thinner than ordered, badly soldered connector | Check the thickness and the solder joints; close bridges |
| **Two or more minima** in S11 | Small ground plane, or the patch cable radiates | Trust the one near the expected frequency. Try a shorter patch cable or ferrites |
| The curve changes when you touch the cable | The coax braid radiates | Short patch cable, ferrites, or measure with the node board connected |
| Good S11 but poor range | Low efficiency (FR4) or covered antenna | Look at the simulated η; move the antenna away from the battery and metals |
| Nothing goes below −3 dB | Antenna disconnected or short-circuited | Check Z1 (is it fitted?), the bridges and the SMA solder joints. Look at Z: ~0 Ω is a short; very high, an open circuit |
| The assistant proposes odd values (≪1 pF, ≫100 nH) | Antenna badly mismatched or badly measured | Check the calibration (load < −30 dB). Tune the frequency first |

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **λ (lambda)** | Wavelength. At 868 MHz it is 34.5 cm; at 2.44 GHz, 12.3 cm. On the board it is shorter (λg) because of the FR4 |
| **εr** | Permittivity of the substrate. The higher it is, the shorter the antenna ends up. FR4 ≈ 4.5 |
| **Microstrip / 50 Ω line** | The track that carries the signal from the connector to the antenna, with ground underneath. Its width sets the 50 Ω |
| **Ground plane** | The copper area connected to ground. On monopoles it is the «other half» of the antenna |
| **Balun** | What matches an unbalanced line (coax) to a balanced antenna (dipole) |
| **OSL / SOL** | Calibration with OPEN, SHORT and LOAD |
| **`.s1p`** | Touchstone file with the S11 measurement |
| **DRC** | *Design Rule Check*: automatic board check in KiCad |
| **Gerber** | The files that are sent to the manufacturer |
| **E24** | Series of commercial values (1.0 · 1.1 · 1.2 · 1.3 · 1.5 · 1.6 · 1.8 · 2.0 · 2.2 · 2.4 · 2.7 · 3.0 · 3.3 · 3.6 · 3.9 · 4.3 · 4.7 · 5.1 · 5.6 · 6.2 · 6.8 · 7.5 · 8.2 · 9.1 × 10ⁿ) |
| **Shunt** | Component between the track and ground |

---

Have you manufactured and measured an antenna? Share it with the
[«Real measurement»](https://github.com/sqtactical/chirptenna/issues/new/choose) template: it is what helps the
project most at this stage. For questions, [Discussions](https://github.com/sqtactical/chirptenna/discussions).
