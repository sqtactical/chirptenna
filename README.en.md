<p align="center"><img src="docs/logo/chirptenna_texto.png" alt="Chirptenna" width="560"></p>

# Chirptenna: PCB antenna generator

[![Comprobar](https://github.com/sqtactical/chirptenna/actions/workflows/comprobar.yml/badge.svg)](https://github.com/sqtactical/chirptenna/actions/workflows/comprobar.yml)

*[Versión en castellano](README.md)*

> **Status: alpha (v0.2.0-alpha).** Validated in simulation only: no manufactured board has been
> measured yet. **Real measurements wanted**: if you build an antenna and measure it, share it with
> the [“Real measurement”](../../issues/new/choose) template. How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md).
> Release notes: [CHANGELOG.md](CHANGELOG.md).

**Chirptenna** (from *chirp*, LoRa's modulation, and *antenna*) is a program that generates **PCB-printed antennas** (fractal, directional and reference designs)
for a target frequency, **tunes them by simulating with openEMS** (FDTD) and **exports them to
KiCad, Gerber and DXF**, ready to manufacture. It has a browser-based GUI and command-line tools.
Aimed at Meshtastic LoRa nodes (433 / 868 MHz) and at 2.4 GHz.

It also includes **NanoVNA-H** control (PC-side calibration and antenna measurement) and
**calibration coupons** to measure the real εr of the FR4, so that simulations match the
manufactured boards.

> **Project status:** everything described here is **simulated, not measured**. Boards have
> been ordered; the εr of JLC's FR4 (4.5 by default) is still to be measured with the coupon.
> Treat it as a work in progress.

> The code and comments are in **Spanish**; the GUI and the web version speak **Spanish, English, French and German** (language selector in the header).

## What it does

1. You pick the antenna type, the band (433, 868, 915 ISM, 1.2 GHz amateur, GPS L1, Iridium, 2.4 GHz, 5.8 GHz or custom; those other than 868 and 2.4 GHz are not simulated, and FR4 is very lossy at 5.8 GHz) and the substrate.
2. The program sizes the antenna with formulas **calibrated against earlier simulations** and
   checks JLC's manufacturing rules.
3. Optionally it **simulates it with openEMS** and adjusts its size until it resonates at the
   requested frequency (S11, Smith chart, radiation pattern, gain and efficiency).
4. It exports it: a KiCad test board with an edge-mount SMA or IPEX, Gerbers and drill files for
   JLC, DXF, and a footprint to embed it in another board. It passes KiCad's DRC and prints the
   Chirptenna logo and the labels you choose on the silkscreen (type and frequency, simulation
   result, licence, date, free text…).
5. It can add **post-manufacture tuning** without components: an overlength with cut marks
   labelled in MHz, and segments closed with solder bridges (or an optional π network).
6. It saves each design in **My designs** (`Documents\Chirptenna\disenos`) with its simulation,
   export and measurements, and a **NanoVNA assistant** walks you through calibrating over the
   antenna's range, checking, measuring (also live while you trim) and what to cut or fit in the
   π network, with the measured curve overlaid on the simulated one.
7. Yagis and the panel can have **lightening cutouts**: FR4-free windows between the copper and the
   edge (not simulated yet: the frequency may rise slightly).
8. **Interface in Spanish, English, French and German** (selector in the header; also in the web lite version).
   Languages are `antenas/idiomas/<code>.json` files: adding one means translating a file.
9. **GPU acceleration** (experimental, NVIDIA cards): with an openEMS build that has the GPU engine, simulations
   run ~10 times faster. Frequency, S11 and impedance match the CPU; gain and efficiency come out a little high, so
   confirm the final design on the CPU. See [`RETOMAR.md`](RETOMAR.md).

## Screenshots

**Choose antenna** (*Elegir antena*): the first thing you see, a gallery of types grouped by use, with a drawing, a description and a status.

![Antenna type gallery](docs/capturas/galeria.png)

**Design** (*Diseño*): pick the type and band; the program sizes the antenna and warns about known issues.

![Design tab with a 2.4 GHz Sierpinski monopole](docs/capturas/diseno.png)

**openEMS simulation** (*Simulación*): S11, VSWR, Smith chart with the band marked, radiation pattern and a
3D pattern with the board inside (here a 2450 MHz Yagi: 7.2 dBi towards the directors).

![Simulation tab of a 2450 MHz Yagi](docs/capturas/simulacion.png)

**Manufacture** (*Fabricar*): JLC rules, KiCad/Gerber/DXF export and the silkscreen labels.

![Manufacture tab with checks, export and silkscreen](docs/capturas/fabricar.png)

The resulting board (KiCad render): top side and bottom side with the logo and labels.

<p align="center"><img src="docs/capturas/placa_yagi.png" alt="Yagi board: top and bottom sides" width="640"></p>

**Measure** (*Medir*): NanoVNA assistant (connect, calibrate, check, measure) with the measurement overlaid on the simulation.

![Measure tab with the NanoVNA assistant](docs/capturas/medir.png)

## Antenna types

| Type | Family | Simulation status |
|---|---|---|
| Straight, meander and Koch monopoles | monopole | ✅ validated (2.4 GHz and 868 MHz) |
| Sierpinski monopole | monopole | ✅ validated (2.4 GHz and 868 MHz) |
| Hilbert monopole | monopole | ⚠️ resonates, but does not match without a π network |
| Rectangular patch | patch | ✅ validated (narrowband) |
| Minkowski patch | patch | ⚠️ iteration 1 fine; iteration 3 has low efficiency on FR4 |
| Printed dipole (straight or Koch; printed balun or centre-fed coax) | dipole | ✅ validated (2.4 GHz and 868 MHz) |
| Bowtie dipole or Sierpinski bowtie | dipole_bowtie | ✅ validated (2.4 GHz and 868 MHz); twice the bandwidth of the straight one |
| J-pole and Koch J-pole | jpole | ✅ Koch validated (2.4 GHz and 868 MHz); the straight one almost matches (−8 to −9 dB) |
| Double-sided Yagi with boom | yagi | ✅ straight elements (6–7 dBi; 2.4 GHz and 868 MHz); Koch is experimental |
| Quasi-Yagi with Koch dipole | yagi | ⚠️ experimental |
| 2×2 / 4×4 panel of dipoles, bowties or Sierpinski bowties over a reflector | panel | ✅ 2×2 ≈ 12.1 dBi (dipoles) and 12.6 dBi (Sierpinski), 4×4 ≈ 14.6–16.6 dBi; single element, untuned |
| 2×2 / 4×4 patch array | array | ⚠️ validation not finished |
| Printed coaxial collinear (COCO) | collinear | ⚠️ radiates, but FR4 losses eat the gain (useless at 868 MHz) |
| Franklin collinear | collinear | ⚠️ matches, but with little bandwidth and ~2.5 dBi |

## ⚠️ Known issues

**Everything validated so far is in simulation**, with εr 4.5 for JLC's FR4. No manufactured board
and no real εr has been measured yet (that is what the coupons are for). Always measure an antenna
before trusting it. The GUI shows these warnings when you pick the type and when you export.

| Type / option | Issue |
|---|---|
| Hilbert monopole | Resonates, but matches very poorly without a π network (−2.7 dB at 2.4 GHz, −4.6 dB at 868 MHz). At 868 MHz each simulation takes over 3 h. |
| Meander monopole | Frequency jumps a few % with small height changes; with a small ground plane it may not reach −10 dB. |
| Monopoles with IPEX | The straight monopole with IPEX matched poorly (−7 dB): the centre-pad transition is under review. Fine with SMA. |
| Rectangular patch | Narrowband on 1.6 mm FR4 (~36 MHz): does not cover the whole 2.4 GHz ISM band. η ~47 %. |
| Minkowski patch | Iteration 1: η ~33 % and ~1 dBi. Iteration 3: it matches (−17.5 dB) but η ~30 % and < 1 dBi. |
| Straight J-pole | Resonates but barely matches (−8 to −9 dB). The Koch J-pole matches better. |
| Yagi with boom, Koch elements | Poor match and radiates more backwards than towards the directors. Use straight elements. |
| Yagi with boom, folded dipole | Radiates backwards (F/B −3.6 dB). Use direct feed (reflector at ~0.39 λ0, longer board). |
| Yagi with boom, λ/4 transformer | Narrow band (~50 MHz) and η ~55 %. |
| Koch quasi-Yagi | Radiates backwards and matches poorly (−3.5 dB). Experimental. |
| Dipole panel | The tuning does not iterate the frequency (rippled S11): the initial size is calibrated with the 2×2 at 2.4 GHz. With a fine mesh the beam comes out straight ahead (0–3°). The single-element panel resonates far from the target. The “symmetric” layout worsens the match. |
| Patch array | Validation not finished: the 2×2 resonates 16 % low with the default size, η ~22 % and each simulation takes hours. |
| COCO collinear | Radiates, but FR4 losses leave η ~53 % and ~1.9 dBi at 2.4 GHz; at 868 MHz, η 26 %, −2 dBi and S11 −7.8 dB. |
| Franklin collinear | Matches (−19 dB at 2.4 GHz, −35 dB at 868 MHz) but with 62 and 23 MHz of bandwidth and 2.2–2.8 dBi. Experimental. |
| Lightening cutouts | Lightened Yagi simulated: −1.3 dBi and the reflector has to be readjusted; for the rest, not simulated. |
| Outside 2.4 GHz | Simulated at 868 MHz: the straight, meander, Koch and Sierpinski monopoles, the dipole, the Koch J-pole, the Yagi with boom and the Franklin and COCO collinears; the rest, only at 2.4 GHz. |

## Requirements

- 64-bit **Windows 10/11** (development platform; the code only depends on it for default paths).
- **Python 3.13 or 3.14** (openEMS 0.37 wheels only exist for those versions).
- **openEMS v0.37** with its Python wheels (`openEMS`, `CSXCAD`).
- **KiCad 8 or later** (`kicad-cli`, tested with 10) to produce Gerbers and run the DRC. Without
  it, the `.kicad_pcb` and DXF are still exported, but not the Gerbers.
- Optional: a **NanoVNA-H** (DiSlord firmware) for measurements.

## Try it without installing

**[Chirptenna web lite](https://sqtactical.github.io/chirptenna/)** (Spanish, English, French and German): design the antenna in
your browser and download it for **KiCad** (`.kicad_pcb`, footprint, DXF and `diseno.json`). Everything runs in your
browser (Python via Pyodide); nothing is sent to any server. It doesn't simulate or run KiCad's DRC: open the board
in KiCad, run its DRC and plot the Gerbers there (the zip includes a README with the steps). To simulate and measure,
install the application.

## Installation

**No Python knowledge needed:** download the ZIP of the latest version from
[Releases](https://github.com/sqtactical/chirptenna/releases), double-click **`instalar.bat`**, then open the
program with the desktop shortcut or **`iniciar.bat`**. The installer downloads Python and openEMS
from their official sites (checking the signature and SHA-256), creates the environment and installs
the packages, without administrator rights. Step-by-step guide, troubleshooting, uninstalling and
manual installation: **[INSTALL.en.md](INSTALL.en.md)**.

**User manual:** **[MANUAL.en.md](MANUAL.en.md)** (Spanish original: [MANUAL.md](MANUAL.md)). It covers every tab, measuring
with the NanoVNA and tuning the manufactured antenna (cut marks, solder bridges and the **π network**, with
worked examples and which components to buy).

## Usage

**GUI** (http://localhost:8080):

```bash
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui/app.py
```

The tabs follow the workflow: **Design → Simulation → Manufacture → Measure → My designs** (the
interface is in Spanish). Set `CHIRPTENNA_DISENOS` to store designs elsewhere.

**Simulate and tune several designs from the command line**:

```bash
python -m antenas.validar_lote salidas/lote --malla adaptada --hilos 6 monopolo_recto:866.5:normal "dipolo:2441.75:normal:{\"alimentacion\":1}"
```

**Simulation queue** (at most two workers at once):

```bash
python herramientas/cola.py añadir my_job python -m antenas.validar_lote salidas/lote monopolo_koch:2441.75:normal
```

```bash
python herramientas/cola.py trabajar --hilos 6
```

**Recalibrate the estimates** with every simulation done so far:

```bash
python herramientas/calibrar_estimaciones.py
```

**Generate the εr calibration coupons**:

```bash
cd cupon && python generar_cupon.py
```

Simulations are slow: from minutes (2.4 GHz monopoles) to hours (arrays, or anything at 868 MHz
with thin traces). They are cached in `%TEMP%\antenas_sim`.

## Layout

| Folder | Contents |
|---|---|
| `antenas/` | Main package: catalogue (`tipos`), geometry, generators, openEMS simulation, tuning, export, design tips |
| `gui/` | NiceGUI interface |
| `vna/` | NanoVNA control, PC calibration and measurements |
| `cupon/` | εr coupon generator and ring simulations |
| `fase0/` | Initial openEMS validation (dipole and monopole) |
| `referencias/` | Models of commercial antennas, to compare simulation and measurement |
| `herramientas/` | Simulation queue, estimate calibration, diagnostics |
| `analisis/`, `placa_sim/` | Tools to study existing boards from their Gerbers |
| `docs/logo/` | Logo (a cricket with Koch-curve antennae) and the script that draws it |

`salidas/` (exports), `placas/` (third-party Gerbers) and the generated coupons are not in the
repository: they are regenerated with the program.

## Licence

- **Code:** [GNU AGPL v3.0](LICENSE) (v0.1.0-alpha was released under GPL v3.0; later versions, under AGPL).
  You may use, modify and sell it, but if you distribute a modified version **or offer it as a network
  service**, you must publish its source code under the same licence.
- **Designs published by the author** (exported antennas and coupons): [CC BY-NC 4.0](LICENSE-DISENOS.md).
- Designs you generate yourself with the program are yours.
