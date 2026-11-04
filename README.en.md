<p align="center"><img src="docs/logo/chirptenna_texto.png" alt="Chirptenna" width="560"></p>

# Chirptenna: PCB antenna generator

*[Versión en castellano](README.md)*

> **Status: alpha (v0.1.0-alpha).** Validated in simulation only: no manufactured board has been
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

> The code, comments and GUI are in **Spanish**.

## What it does

1. You pick the antenna type, the band (433, 868, 2.4 GHz or custom) and the substrate.
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

## Antenna types

| Type | Family | Simulation status |
|---|---|---|
| Straight, meander and Koch monopoles | monopole | ✅ validated (2.4 GHz and 868 MHz) |
| Sierpinski monopole | monopole | ✅ validated (2.4 GHz) |
| Hilbert monopole | monopole | ⚠️ resonates, but does not match without a π network |
| Rectangular patch | patch | ✅ validated (narrowband) |
| Minkowski patch | patch | ⚠️ iteration 1 fine; iteration 3 has low efficiency on FR4 |
| Printed dipole (printed balun or centre-fed coax) | dipole | ✅ validated (2.4 GHz) |
| J-pole and Koch J-pole | jpole | ✅ Koch validated; straight one under review |
| Double-sided Yagi with boom | yagi | ✅ straight elements (6–7 dBi); Koch is experimental |
| Quasi-Yagi with Koch dipole | yagi | ⚠️ experimental |
| 2×2 / 4×4 dipole panel over a reflector | panel | ✅ 2×2 ≈ 12.7 dBi, 4×4 ≈ 16.6 dBi |
| 2×2 / 4×4 patch array | array | ⚠️ validation not finished |
| Printed coaxial collinear (COCO) | collinear | ⚠️ radiates, but FR4 losses eat the gain |
| Franklin collinear | collinear | ⚠️ experimental |

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
| Minkowski patch | Iteration 1: η ~33 %. Iteration ≥ 2: edge impedance ~14 Ω, S11 ≈ −5 dB and η ~23 % (inset feed does not fix it). |
| Straight J-pole | Resonates but matches poorly (R ≈ 6–10 Ω). Use the Koch J-pole. |
| Yagi with boom, Koch elements | Poor match and radiates more backwards than towards the directors. Use straight elements. |
| Yagi with boom, folded dipole | Radiates backwards (F/B −3.6 dB). Use direct feed (reflector at ~0.39 λ0, longer board). |
| Yagi with boom, λ/4 transformer | Narrow band (~50 MHz) and η ~55 %. |
| Koch quasi-Yagi | Radiates backwards and matches poorly (−3.5 dB). Experimental. |
| Dipole panel | In simulation the beam tilts ~9° (probably an artefact). The “symmetric” layout worsens the match. |
| Patch array | Validation not finished: the band centre jumps a lot and each simulation takes hours. |
| COCO collinear | Radiates, but FR4 losses leave η ~53 % and ~1.9 dBi. |
| Franklin collinear | Poor match (−5.3 dB) and only ~1.8 dBi. Experimental. |
| Lightening cutouts | Not simulated: removing FR4 raises the frequency slightly. |
| Outside 2.4 GHz | Only the straight, meander and Koch monopoles are also validated at 868 MHz. |

## Requirements

- 64-bit **Windows 10/11** (development platform; the code only depends on it for default paths).
- **Python 3.13 or 3.14** (openEMS 0.37 wheels only exist for those versions).
- **openEMS v0.37** with its Python wheels (`openEMS`, `CSXCAD`).
- **KiCad 8 or later** (`kicad-cli`, tested with 10) to produce Gerbers and run the DRC. Without
  it, the `.kicad_pcb` and DXF are still exported, but not the Gerbers.
- Optional: a **NanoVNA-H** (DiSlord firmware) for measurements.

## Installation

**No Python knowledge needed:** download the ZIP of the latest version from
[Releases](https://github.com/sqtactical/chirptenna/releases), double-click **`instalar.bat`**, then open the
program with the desktop shortcut or **`iniciar.bat`**. The installer downloads Python and openEMS
from their official sites (checking the signature and SHA-256), creates the environment and installs
the packages, without administrator rights. Step-by-step guide, troubleshooting, uninstalling and
manual installation: **[INSTALL.en.md](INSTALL.en.md)**.

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
