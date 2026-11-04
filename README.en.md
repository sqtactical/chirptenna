<p align="center"><img src="docs/logo/chirptenna_texto.png" alt="Chirptenna" width="560"></p>

# Chirptenna: PCB antenna generator

*[Versión en castellano](README.md)*

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
   JLC, DXF, and a footprint to embed it in another board. It passes KiCad's DRC and labels the
   silkscreen.
5. It can add **post-manufacture tuning** without components: an overlength with cut marks
   labelled in MHz, and segments closed with solder bridges (or an optional π network).

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

## Requirements

- **Windows** (development platform; the code only depends on it for default paths).
- **Python 3.12 or later** (developed with 3.14).
- **openEMS v0.37** with its Python wheels (`openEMS`, `CSXCAD`).
- **KiCad 10** (`kicad-cli`) to produce Gerbers and run the DRC. Without it, the `.kicad_pcb`
  and DXF are still exported, but not the Gerbers.
- Optional: a **NanoVNA-H** (DiSlord firmware) for measurements.

## Installation

Create the virtual environment **outside long paths** (inside OneDrive or deep folders Windows
exceeds 260 characters and shapely's DLLs fail to load):

```bash
python -m venv %LOCALAPPDATA%\antenas\venv
```

```bash
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS
```

## Usage

**GUI** (http://localhost:8080):

```bash
%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui/app.py
```

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

- **Code:** [GNU GPL v3.0](LICENSE).
- **Designs published by the author** (exported antennas and coupons): [CC BY-NC 4.0](LICENSE-DISENOS.md).
- Designs you generate yourself with the program are yours.
