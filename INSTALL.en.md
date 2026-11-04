# Installing Chirptenna on Windows (step by step)

*[Versión en castellano](INSTALAR.md)* · Once installed: **[user manual](MANUAL.md)** (in Spanish, like the
interface).

This guide is for people who have never used Python. You don't need to know how to program or be an
administrator. An installer downloads and sets up everything. It takes about **10 minutes**, mostly
downloading.

**Contents**

1. [Before you start](#0-before-you-start)
2. [Download the program](#1-download-the-program)
3. [Run the installer](#2-run-the-installer)
4. [Install KiCad](#3-install-kicad-optional-but-recommended)
5. [Open Chirptenna](#4-open-chirptenna)
6. [Check that everything works](#5-check-that-everything-works)
7. [NanoVNA](#6-nanovna-optional)
8. [Updating](#updating-to-a-new-version) · [Common problems](#common-problems) · [Getting help](#getting-help) ·
   [Uninstalling](#uninstalling) · [Manual installation](#manual-installation-for-console-users)

---

## 0. Before you start

### What you need

| | Minimum | Recommended |
|---|---|---|
| System | 64-bit Windows 10 | Windows 11 |
| Memory | 8 GB | 16 GB (to simulate arrays and panels) |
| Processor | 4 cores | 6 cores or more (simulations get much faster) |
| Disk | 1.5 GB free | 4 GB (with KiCad and the simulation cache) |
| Internet | Only during installation (about 250 MB, plus 1.5 GB if you install KiCad) | |

Optional: a **NanoVNA-H** or another antenna analyser to measure what you build.

**Is my Windows 64-bit?** Press `Windows + Pause` or go to **Settings → System → About**. “System type” must
say **“64-bit operating system”**. 32-bit Windows and ARM computers (some Surface and Snapdragon laptops)
are not supported.

### What gets installed and where

The installer stays inside your user account and needs no administrator rights:

| What | Where | Why |
|---|---|---|
| The program folder | Wherever you extract it (step 1) | The program itself |
| Python 3.14 | `%LOCALAPPDATA%\Programs\Python\Python314` | The language it is written in. If you already have Python 3.13 or 3.14, it uses that |
| openEMS 0.37 | `%LOCALAPPDATA%\Programs\openEMS` | The electromagnetic simulator |
| Program environment | `%LOCALAPPDATA%\antenas\venv` | Chirptenna's libraries, kept apart from any other Python |
| Your designs | `Documents\Chirptenna\disenos` | Created the first time you save a design |

> `%LOCALAPPDATA%` is a hidden folder in your user profile (usually `C:\Users\<you>\AppData\Local`). To open
> it, paste `%LOCALAPPDATA%` into the File Explorer address bar.

---

## 1. Download the program

1. Go to the releases page: **https://github.com/sqtactical/chirptenna/releases**
2. The first release in the list is the latest (tagged *Pre-release* while the project is in alpha). Scroll to
   its **Assets** section and click **Source code (zip)**. You don't need a GitHub account.
3. The file lands in your **Downloads** folder, named like `chirptenna-0.1.1-alpha.zip`.
4. **Extract it** (don't just double-click it: that only shows what is inside and the installer won't work):
   right-click the zip → **Extract All…** → pick a folder you will keep, for example `Documents` →
   **Extract**.
5. You get a folder like `Documents\chirptenna-0.1.1-alpha`. That is **the program folder**. It must contain,
   among other things, `instalar.bat`, `iniciar.bat` and the `antenas` and `gui` folders.

> **Where should it go?** Any folder works, OneDrive included. Just avoid very long paths or odd characters.
> If you later move or delete it, the desktop shortcut will stop working: run `instalar.bat` again from the
> new place.

> Want the very latest, untested code? On the main project page, green **Code** button → **Download ZIP**
> (`chirptenna-main`). For normal use, prefer a published release.

---

## 2. Run the installer

1. Open the program folder and **double-click `instalar.bat`**. If Windows hides file extensions, it shows
   as `instalar` with a gear icon.
2. A blue warning may appear: **“Windows protected your PC”**. This happens with any program downloaded from
   the internet that doesn't come from a store. Click **More info** → **Run anyway**.
3. A black window opens and goes through the steps. Each line starts with a marker:
   - `OK` (green): that step is fine.
   - `!` (yellow): a warning. It doesn't stop the installation (for example, KiCad is missing).
   - `X` (red): an error. Installation stops and says why.

   | Step | What it does | Download | Approx. time |
   |---|---|---|---|
   | 1 | Looks for Python 3.13 or 3.14. If missing, downloads **Python 3.14** from python.org, **checks its digital signature** and installs it for your user only, without touching the PATH | 33 MB | 1–2 min |
   | 2 | Downloads the **openEMS 0.37** simulator from its official page, checks the file is exactly the expected one (**SHA-256**) and extracts it | 65 MB | 1 min |
   | 3 | Creates a Python environment just for the program, so nothing else is affected | — | seconds |
   | 4 | Installs the libraries with the **exact tested versions** (`requirements-lock.txt`) and the openEMS modules | ~150 MB | 2–5 min |
   | 5 | Checks whether you have **KiCad** (section 3). If not, warns you and offers to open its download page | — | — |
   | 6 | Asks whether you want a **desktop shortcut**. Press **Enter** for yes | — | — |

4. At the end it runs a check and should say **“OK el programa carga bien”** (the program loads fine) and
   **“Instalación terminada”** (installation finished). Press any key to close the window.

If something fails, the window says what happened. Fix it (it's almost always the internet connection or
the antivirus; see [common problems](#common-problems)) and run `instalar.bat` again: whatever was already
done is not repeated or downloaded again.

> **Is it safe?** The installer only downloads from python.org and openEMS's official GitHub page, and
> checks what it downloads before using it. If the signature or the SHA-256 don't match, it stops. You can
> read what it does in `instalar\instalar.ps1`: it is plain text with comments.

---

## 3. Install KiCad (optional but recommended)

KiCad is free PCB design software. Chirptenna uses it for two things:
- producing the **Gerber files** you send to the manufacturer (for example, JLCPCB);
- checking the board with its **DRC** (design rule check).

Without KiCad you can design, simulate and export the DXF and the KiCad board, but not the Gerbers.

1. Go to **https://www.kicad.org/download/windows/** and download the latest stable release (8 or later;
   tested with 10). It's about 1.5 GB.
2. Run KiCad's installer and keep **all the default options**. This one does ask for administrator rights.
3. No need to run `instalar.bat` again: Chirptenna finds KiCad by itself. If you installed it elsewhere,
   create a `KICAD_CLI` environment variable with the full path to `kicad-cli.exe`.

---

## 4. Open Chirptenna

1. Double-click the **Chirptenna** shortcut on the desktop, or `iniciar.bat` in the program folder.
2. A **black window** opens. That is the program itself: **keep it open** while you use it (you can
   minimise it).
3. A moment later your browser opens at **http://localhost:8080** with the interface. Chirptenna runs on your
   computer: the browser is just the screen and **nothing is sent to the internet**. The interface can only
   be reached from your own computer.
4. To close the program, **close the black window**. Closing the browser tab doesn't stop it.

> If you close the tab by mistake, open **http://localhost:8080** again (bookmark it). No need to restart
> the program while the black window is still open.

---

## 5. Check that everything works

A 2-minute test to know the installation is complete. The interface is in Spanish; the labels are quoted
as they appear:

1. In the top bar, **Tipo de antena** (antenna type) → *Monopolo recto (referencia)*, and **Banda de uso**
   (band) → *2,4 GHz*.
2. **Diseño** tab → **Ajustar tamaño a la frecuencia** (size to frequency). The antenna drawing must appear.
3. Type `prueba` in **Nombre del diseño** (design name, top left). **Fabricar** tab → **Exportar KiCad +
   Gerber + DXF**. The design is saved automatically and, when it finishes, the output folder appears with
   the files to download (Gerbers for JLC, KiCad board, footprint, DXF) and a DRC result with no errors.
   Without KiCad you get “Error al exportar: No se encuentra kicad-cli”: that's expected, and the KiCad
   board and the DXF are still written to the design's `fabricacion` folder.
4. Optional, to test the simulator: **Simulación** tab → precision **rápida** (fast) → untick «Ajustar a la
   frecuencia simulando» → **Simular**. A 2.4 GHz monopole takes a few minutes and ends with the S11 and
   radiation pattern plots.

If all of that works, you're done. Continue with the **[user manual](MANUAL.md)**.

---

## 6. NanoVNA (optional)

1. Plug it in over USB. Windows 10 and 11 recognise it by themselves as a serial (COM) port; no drivers
   needed.
2. In Chirptenna, **Medir** (Measure) tab → **Buscar el NanoVNA** (find the NanoVNA).
3. If it isn't found:
   - try another USB cable (many cables only charge and carry no data);
   - close any other program using it (NanoVNA-Saver, NanoVNA-App…). Only one program at a time can talk
     to it;
   - check in **Device Manager** → *Ports (COM & LPT)* that a “USB Serial Device” appears when you plug it in.

Tested with the **NanoVNA-H with DiSlord firmware**. Chirptenna never saves anything to the device's memory:
your calibrations in slots C0–C4 are not touched. With another analyser, measure with its own software and
upload the `.s1p` file in the **Medir** tab.

---

## Updating to a new version

1. Download and extract the new zip (step 1). You can keep it next to the old one.
2. Run `instalar.bat` from the **new** folder: it reuses Python and openEMS, updates the libraries if needed
   and points the shortcut to the new folder.
3. Once you've checked it works, delete the old folder.

**Your designs are not touched**: they live in `Documents\Chirptenna\disenos`, not in the program folder.
What's new in each version is in the [CHANGELOG](CHANGELOG.md).

---

## Common problems

### During installation

| Problem | Solution |
|---|---|
| Double-clicking `instalar.bat` flashes a window that closes at once | You are probably inside the zip without extracting it. Use **Extract All…** (step 1) |
| “Windows protected your PC” with no “Run anyway” button | Click **More info** first |
| `X` while downloading, or “Unable to connect” | Check your connection. On company or university networks with a proxy, try another network or use the [manual installation](#manual-installation-for-console-users) |
| The antivirus blocks the download or deletes a file | Allow `python.org` and `github.com`, or add an exception for `%LOCALAPPDATA%\antenas`. Run the installer again |
| “La firma del instalador de Python no es válida” or “El SHA-256 de openEMS no coincide” (invalid signature / SHA-256 mismatch) | The download is corrupt or something altered it (proxy, antivirus). Delete `%LOCALAPPDATA%\antenas\descargas` and run again. **Don't force it** |
| “Falló la instalación de los paquetes” (package installation failed) | Almost always the connection. Run `instalar.bat` again. If it persists, copy the window's messages and [ask for help](#getting-help) |
| You already had another Python (3.12, 3.11…) | No problem: the installer adds Python 3.14 separately and leaves yours alone |
| You had an environment from an old Chirptenna version with another Python | The installer moves it to `venv.antiguo_<date>` and creates a new one. You can delete the old one |

### When opening the program

| Problem | Solution |
|---|---|
| The browser says “This site can't be reached” | Wait a few seconds and reload: the first start takes a moment. Check the black window for errors |
| The black window says “Chirptenna no esta instalado” | Run `instalar.bat` |
| The black window closes by itself | Run `instalar.bat` again: it will say if something is missing |
| “Port 8080 is in use” or “address already in use” | Chirptenna is already open in another black window: use that one, or close it and start again |
| The shortcut does nothing | You moved or deleted the program folder. Run `instalar.bat` from where it is now |
| The interface looks broken or half-loaded | Reload with `Ctrl + F5`. Use a current browser (Edge, Chrome or Firefox) |

### While using it

| Problem | Solution |
|---|---|
| On export: “Error al exportar: No se encuentra kicad-cli” | Install KiCad (section 3). If it's in another folder, set `KICAD_CLI` |
| A simulation doesn't progress or is very slow | Simulations take time: minutes to hours depending on the antenna and band (longer at 868 MHz). The log in the Simulación tab shows progress. Use the **rápida** (fast) precision to explore |
| The disk is filling up | The simulation cache is in `%TEMP%\antenas_sim`. You can delete it entirely; anything in it can be recomputed |

**To see what is installed without changing anything:** open a command prompt in the program folder (in File
Explorer, type `cmd` in the address bar and press Enter) and run:

```bash
instalar.bat -Comprobar
```

---

## Getting help

If none of the above solves it, open an issue at
**https://github.com/sqtactical/chirptenna/issues/new/choose** → “Bug”. Include:

1. Your Windows version and the Chirptenna version (shown at the very bottom of the interface, or in the zip
   name).
2. The output of `instalar.bat -Comprobar` (select it in the window and copy it).
3. The full error message from the black window.

Before pasting, **remove your user name** from the paths if you don't want it shown (`C:\Users\<you>\...`).
For questions that aren't bugs, use [Discussions](https://github.com/sqtactical/chirptenna/discussions).

---

## Uninstalling

1. Delete the program folder and the desktop shortcut.
2. Delete these folders (paste each path into the File Explorer address bar):
   - `%LOCALAPPDATA%\antenas` (Python environment and downloads);
   - `%LOCALAPPDATA%\Programs\openEMS`;
   - `%TEMP%\antenas_sim` (simulation cache).
3. If the installer installed Python and you don't use it for anything else: **Settings → Apps** →
   “Python 3.14…” → Uninstall.
4. Your designs are in `Documents\Chirptenna`: delete them only if you no longer want them.

---

## Manual installation (for console users)

The same steps the installer performs:

1. 64-bit Python **3.13 or 3.14** (openEMS 0.37 wheels only exist for those):
   https://www.python.org/downloads/windows/
2. openEMS: download `openEMS_x64_v0.37.0_msvc.zip` from
   https://github.com/thliebig/openEMS-Project/releases/tag/v0.37.0 (SHA-256
   `e4f14fd6e9be7d0c1fd9c244768c21c1c2b62b8aa81f08253ebf6e06040cda5a`) and extract it so that
   `%LOCALAPPDATA%\Programs\openEMS\openEMS\openEMS.exe` exists (or set `CSXCAD_INSTALL_PATH` to its folder).
3. Create the environment **outside long paths**. Inside OneDrive or deep folders, Windows exceeds 260
   characters and shapely's DLLs fail to load:

   ```bash
   python -m venv %LOCALAPPDATA%\antenas\venv
   ```

4. Install the packages from the program folder. `requirements-lock.txt` has the exact tested versions;
   `requirements.txt`, the accepted ranges:

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install -r requirements-lock.txt
   ```

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS CSXCAD
   ```

5. KiCad 8 or later (optional). It is looked up in `Program Files\KiCad\<version>\bin\kicad-cli.exe`, on the
   PATH or in the `KICAD_CLI` environment variable.
6. Start it with `iniciar.bat` or `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui\app.py`. Options:
   `--puerto 8081` (another port), `--disenos <folder>` (another design library, same as the
   `CHIRPTENNA_DISENOS` variable).

Installer options: `-Comprobar` (report only), `-SinPreguntas` (no questions), `-SinAccesoDirecto` (no
shortcut) and `-Python <path to python.exe>` (use an existing Python 3.13/3.14).
