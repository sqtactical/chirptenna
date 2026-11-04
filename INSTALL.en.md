# Installing Chirptenna on Windows (step by step)

This guide is for people who have never used Python. You don't need to know how to program or
be an administrator. An installer downloads and sets up everything; it takes about
**10 minutes** (mostly downloading).

*[Versión en castellano](INSTALAR.md)*. The program's interface is in Spanish.

## What you need

- 64-bit Windows 10 or 11.
- An internet connection during installation (about 250 MB is downloaded).
- About 1.5 GB of free disk space (2.5 GB more if you install KiCad).
- Optional: a **NanoVNA-H** to measure the antennas.

## 1. Download the program

1. Go to the project page on GitHub: https://github.com/sqtactical/chirptenna
2. Click the green **Code** button, then **Download ZIP**.
3. Find the file in your **Downloads** folder (`chirptenna-main.zip`).
4. Right-click it → **Extract All…** → choose a folder you will keep, for example `Documents`.
   You will get a `chirptenna-main` folder.

> If you later delete or move that folder, the desktop shortcut will stop working: run the
> installer again from the new location.

## 2. Run the installer

1. Open the `chirptenna-main` folder and **double-click `instalar.bat`**.
2. Windows may show a blue warning: **“Windows protected your PC”**. This is normal for programs
   downloaded from the internet that are not sold in a store. Click **More info** →
   **Run anyway**.
3. A black window opens and goes through the steps:

   | Step | What it does | Size |
   |---|---|---|
   | 1 | Installs **Python 3.14** from python.org, for your user only, after checking its digital signature | 33 MB |
   | 2 | Downloads the **openEMS 0.37** simulator from its official page and checks the file (SHA-256) | 65 MB |
   | 3 | Creates a Python environment just for the program, so nothing else is affected | — |
   | 4 | Installs the libraries the program uses | ~150 MB |
   | 5 | Checks whether you have **KiCad** (see section 3) | — |
   | 6 | Asks whether you want a **desktop shortcut** (press Enter for yes) | — |

4. At the end it should say **“Instalación terminada”** (installation finished). Press any key to
   close the window.

If something fails, the window says what happened. Fix it (usually the internet connection) and
run `instalar.bat` again: whatever was already done is skipped.

## 3. Install KiCad (optional but recommended)

KiCad is free PCB design software. Chirptenna uses it to produce the **Gerber files** you send to
the manufacturer (e.g. JLCPCB) and to check the board (DRC). Without KiCad you can design, simulate
and export the DXF and the KiCad board, but not the Gerbers.

1. Go to https://www.kicad.org/download/windows/ and download the latest version.
2. Run its installer and keep **all the default options**.
3. No need to run `instalar.bat` again: Chirptenna finds KiCad by itself.

## 4. Open Chirptenna

- Double-click the **Chirptenna** shortcut on the desktop, or `iniciar.bat` in the program folder.
- A black window opens (**keep it open** while you use the program) and, a moment later, your
  browser at **http://localhost:8080**. The program runs on your computer; nothing is sent to the
  internet.
- To close the program, close the black window.

Your designs are saved in `Documents\Chirptenna\disenos`.

## 5. NanoVNA (optional)

Plug it in over USB. Windows 10 and 11 recognise it without any driver. In Chirptenna, the
**Medir** (Measure) tab has an assistant that walks you through calibrating and measuring.

## Updating to a new version

Download the new ZIP (step 1), replace the old folder and run `instalar.bat` again. Your designs
are not touched.

## Common problems

| Problem | Solution |
|---|---|
| The browser says “This site can't be reached” | Wait a few seconds and reload: the program takes a moment to start. Check the black window for errors |
| The black window closes by itself | Run `instalar.bat` again: it will say if something is missing |
| “Port 8080 is in use” | Chirptenna is already open in another black window: use that one, or close it and start again |
| The antivirus blocks the download | Allow `python.org` and `github.com`, or install manually (below) |
| You want to see what is installed without changing anything | Open a command prompt in the program folder and run `instalar.bat -Comprobar` |

## Uninstalling

1. Delete the program folder (`chirptenna-main`) and the desktop shortcut.
2. Delete these folders (paste the path into the File Explorer address bar):
   - `%LOCALAPPDATA%\antenas` (Python environment, downloads and simulation cache)
   - `%LOCALAPPDATA%\Programs\openEMS`
3. If the installer installed Python and you don't use it for anything else: **Settings → Apps** →
   “Python 3.14…” → Uninstall.
4. Your designs are in `Documents\Chirptenna`: delete them only if you no longer want them.

## Manual installation (for console users)

The same steps the installer performs:

1. 64-bit Python **3.13 or 3.14** (openEMS 0.37 wheels only exist for those):
   https://www.python.org/downloads/windows/
2. openEMS: download `openEMS_x64_v0.37.0_msvc.zip` from
   https://github.com/thliebig/openEMS-Project/releases/tag/v0.37.0 (SHA-256
   `e4f14fd6e9be7d0c1fd9c244768c21c1c2b62b8aa81f08253ebf6e06040cda5a`) and extract it so that
   `%LOCALAPPDATA%\Programs\openEMS\openEMS\openEMS.exe` exists (or set `CSXCAD_INSTALL_PATH` to its folder).
3. Create the environment **outside long paths** (inside OneDrive or deep folders Windows exceeds 260
   characters and shapely's DLLs fail to load):

   ```bash
   python -m venv %LOCALAPPDATA%\antenas\venv
   ```

4. Install the packages from the program folder:

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   ```bash
   %LOCALAPPDATA%\antenas\venv\Scripts\python.exe -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS CSXCAD
   ```

5. KiCad 8 or later (optional). It is looked up in `Program Files\KiCad\<version>\bin\kicad-cli.exe`, on
   the PATH or in the `KICAD_CLI` environment variable.
6. Start it with `iniciar.bat` or `%LOCALAPPDATA%\antenas\venv\Scripts\python.exe gui\app.py`.

Installer options: `-Comprobar` (report only), `-SinPreguntas` (no questions), `-SinAccesoDirecto`
(no shortcut) and `-Python <path to python.exe>` (use an existing Python 3.13/3.14).
