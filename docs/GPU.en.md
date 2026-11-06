# Building openEMS with GPU support (NVIDIA, Windows)

Chirptenna can simulate on the GPU: ~10× faster than the CPU (RTX 3050 Laptop; same results within the tuning error).
But the openEMS the installer sets up (v0.37.0) **does not include the GPU engine**: it only exists on the `master`
branch of [openEMS](https://github.com/thliebig/openEMS), so you have to build it.

> **Verification (2026-11-06):** the GitHub Actions workflow `compilar-gpu.yml`, which repeats these steps on a clean machine,
> built fine (CUDA 12.9.1, MSVC 14.44, architectures 75, 80, 86, 89 and 120) and its 12 MB package worked on the RTX 3050
> Laptop: same resonance frequency, same S11 and same gain as the hand-built one (29 s with 0.65 M cells). Debugging it
> required adding `fparser.lib`, `FPARSER_ROOT_DIR` and forward-slash paths for `nvcc`, already included below. It has not
> been tried on any GPU other than the 3050 (compute capability 8.6).
>
> **Status of this guide (original text): reconstructed, not verified from scratch.** It comes from what was left installed on the
> development machine (versions, CMake options, folders), not from repeating the build on a clean machine. If a step
> fails, it is probably a detail that was done by hand and not written down: tell us or fix this guide. Verification from
> scratch is pending (see «To do» at the end). The Spanish version, [`GPU.md`](GPU.md), is the reference one.
>
> **Automatic build:** the GitHub Actions workflow `.github/workflows/compilar-gpu.yml` («Compilar openEMS con GPU»,
> manual run) does these steps on a Windows runner and leaves a `.zip` with the result, for several GPU architectures
> at once. It is the recommended way if you do not want to build by hand.

**First, the GPU architecture.** The GPU plugin is built **for a specific GPU architecture**
(`CMAKE_CUDA_ARCHITECTURES`). Here it was built only for `86` (RTX 3050 Laptop, compute capability 8.6). On another
NVIDIA card that binary may not work, or only through just-in-time compilation (PTX), so **build it for your card**
(step 6). Your compute capability: `nvidia-smi --query-gpu=name,compute_cap --format=csv`.

## Requirements

- 64-bit Windows 10/11, **no administrator rights needed**: everything goes in a user folder.
- An NVIDIA GPU with a recent driver (here, 592.82). Only compute capability 8.6 has been tried; CUDA 12.9 also builds
  for older architectures, but this has not been checked with the openEMS plugin.
- Visual Studio Build Tools with the **Windows SDK** (any recent version; only the SDK and its headers are used).
- The project's **Python 3.14** (the `venv` from `instalar.bat`) for `herramientas/comparar_gpu.py` and for using it.
- **Space and time:** here the working folder took **14 GB** (8.8 GB of vcpkg build cache, deletable afterwards; 1.5 GB
  of portable MSVC; 2.2 GB of downloads). Expect **several hours**, mostly vcpkg building Boost.

The default working folder is `%LOCALAPPDATA%\Programs\gpu-build` (the program looks there; if you use another one,
`OPENEMS_GPU_DIR` must point to its `opt\bin`).

```powershell
$gb = "$env:LOCALAPPDATA\Programs\gpu-build"
New-Item -ItemType Directory -Force $gb, "$gb\dl", "$gb\src", "$gb\build", "$gb\opt" | Out-Null
```

## 1. Portable tools

Versions that worked. Unzip only; nothing to install.

| Tool | Version | Folder |
|---|---|---|
| CMake | 4.4.5 (Windows x64 zip from cmake.org) | `gpu-build\cmake-4.4.5-windows-x86_64` |
| Ninja | 1.13.2 (`ninja-win.zip` from github.com/ninja-build/ninja) | `gpu-build\ninja` |
| Git | MinGit (the project's, `%LOCALAPPDATA%\Programs\MinGit`) | — |
| vcpkg | commit `29718cfe` (2026-11-05), `git clone https://github.com/microsoft/vcpkg` | `gpu-build\vcpkg` |

```powershell
& git clone https://github.com/microsoft/vcpkg "$gb\vcpkg"
& "$gb\vcpkg\bootstrap-vcpkg.bat" -disableMetrics
```

## 2. CUDA 12.9.1 (compiler and runtime only, no installer)

NVIDIA publishes the components separately at `https://developer.download.nvidia.com/compute/cuda/redist/`. Four are
needed, from version 12.9.1 (`redistrib_12.9.1.json` gives the exact paths):

| Package | Version |
|---|---|
| `cuda_nvcc` | 12.9.86 |
| `cuda_cudart` | 12.9.79 |
| `cuda_cccl` | 12.9.27 |
| `cuda_profiler_api` | 12.9.79 |

Each is a `.zip` (`cuda_nvcc/windows-x86_64/cuda_nvcc-windows-x86_64-12.9.86-archive.zip`, etc.). Unzip **all of them into
the same folder**, `gpu-build\cuda`, so that `bin\` (with `nvcc.exe`), `include\`, `lib\` and `nvvm\` end up together. The
CUDA driver is not installed separately: it comes with the normal graphics driver.

## 3. HIP 7.2.4 headers

The plugin is written against HIP; on NVIDIA it is built as CUDA with the `OPENEMS_HIP_AS_CUDA` option. Only the
**headers** are needed: from ROCm 7.2.4's `hip-dev` `.deb` package
(`https://repo.radeon.com/rocm/apt/7.2.4/pool/main/h/hip-dev/hip-dev_7.2.53211.70204-93~22.04_amd64.deb`, SHA-256
`2cd2af092216138e00df81ff8507395a578c657273f2f3825ae267facf4bcf53`; it is the Ubuntu 22.04 one, but only the headers
are used) extract `opt/rocm-7.2.4/include` to `gpu-build\hip\opt\rocm-7.2.4\include` (a `.deb` is an `ar` archive
with a `data.tar.gz` inside; 7-Zip works, twice).

## 4. Portable MSVC 14.44

`nvcc` 12.9 **does not support** Visual Studio 18's MSVC 14.51 (its `cudafe++` fails with `ACCESS_VIOLATION`). An
MSVC 14.4x (VS 2022 17.x) is needed. It was downloaded portable with `vsdownload.py` from
[msvc-wine](https://github.com/mstorsjo/msvc-wine) (Martin Storsjö) into `gpu-build\msvc17`; the compiler used was
`msvc17\VC\Tools\MSVC\14.44.35207`. The exact download parameters are still to be confirmed (`python vsdownload.py
--help`: MSVC version, `--dest`, accepting the licence). An alternative is to install the «MSVC v143» component from the
Visual Studio installer.

## 5. Sources

`master` changes every few days: to reproduce the result, pin the commits that worked.

| Project | Repository | Tested commit |
|---|---|---|
| fparser | `https://github.com/thliebig/fparser` | `4b9c845` (2026-04-29) |
| CSXCAD | `https://github.com/thliebig/CSXCAD` | `626b99f` (2026-10-21) |
| openEMS | `https://github.com/thliebig/openEMS` | `5fecbb5` (2026-11-02) |

```powershell
foreach ($p in @(@('fparser','4b9c845'), @('CSXCAD','626b99f'), @('openEMS','5fecbb5'))) {
    & git clone "https://github.com/thliebig/$($p[0])" "$gb\src\$($p[0])"
    & git -C "$gb\src\$($p[0])" checkout $p[1]
}
```

## 6. Build

Shared variables. Run the CMake and build commands with the MSVC environment loaded (an «x64 Native Tools Command
Prompt», or `vcvars64.bat` from `msvc17\VC\Auxiliary\Build` or from Visual Studio Build Tools), so the compiler finds the
Windows SDK.

```powershell
$cmake = "$gb\cmake-4.4.5-windows-x86_64\bin\cmake.exe"
$ninja = "$gb\ninja\ninja.exe"
$vcpkg = "$gb\vcpkg\scripts\buildsystems\vcpkg.cmake"
$comun = "-G", "Ninja", "-DCMAKE_MAKE_PROGRAM=$ninja", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=$gb\opt"
```

**fparser:**

```powershell
& $cmake -S "$gb\src\fparser" -B "$gb\build\fparser" @comun
& $cmake --build "$gb\build\fparser"; & $cmake --install "$gb\build\fparser"
# this commit installs only the DLL and the header: CSXCAD also needs fparser.lib in opt\lib
New-Item -ItemType Directory -Force "$gb\opt\lib" | Out-Null
Copy-Item (Get-ChildItem "$gb\build\fparser" -Recurse -Filter fparser.lib | Select-Object -First 1).FullName "$gb\opt\lib"
```

**CSXCAD** (vcpkg fetches `tinyxml` and `hdf5` on its own; it uses the `x64-windows-release` triplet):

```powershell
$vc = "-DCMAKE_TOOLCHAIN_FILE=$vcpkg", "-DVCPKG_TARGET_TRIPLET=x64-windows-release", "-DVCPKG_HOST_TRIPLET=x64-windows-release"
& $cmake -S "$gb\src\CSXCAD" -B "$gb\build\CSXCAD" @comun @vc "-DCMAKE_PREFIX_PATH=$gb\opt" -DCSXCAD_BUILD_TESTS=OFF
& $cmake --build "$gb\build\CSXCAD"; & $cmake --install "$gb\build\CSXCAD"
```

**openEMS (CPU):** leaves `openEMS.exe`, `openEMS.dll` and the vcpkg DLLs (Boost, HDF5…) in `opt\bin`.

```powershell
& $cmake -S "$gb\src\openEMS" -B "$gb\build\openEMS" @comun @vc "-DCSXCAD_ROOT_DIR=$gb\opt" "-DFPARSER_ROOT_DIR=$gb\opt" "-DCMAKE_PREFIX_PATH=$gb\opt"
& $cmake --build "$gb\build\openEMS"; & $cmake --install "$gb\build\openEMS"
```

**GPU plugin (NVIDIA):** another CMake configuration over the same sources, with `nvcc` and MSVC 14.44 as the CUDA
compiler. **Set your card's architecture here** (`86` = RTX 30xx; `75` = RTX 20xx; `89` = RTX 40xx; `120` = RTX 50xx; or
`native`, which CMake resolves from the installed GPU).

```powershell
$cl = "$gb\msvc17\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$arq = "86"        # ← your GPU's (nvidia-smi --query-gpu=compute_cap)
& $cmake -S "$gb\src\openEMS" -B "$gb\build\openEMS_gpu" @comun @vc `
    "-DCMAKE_CXX_COMPILER=$cl" "-DCMAKE_CUDA_COMPILER=$gb\cuda\bin\nvcc.exe" "-DCMAKE_CUDA_HOST_COMPILER=$cl" `
    "-DCMAKE_CUDA_ARCHITECTURES=$arq" "-DHIP_INCLUDE_DIR=$gb\hip\opt\rocm-7.2.4\include" `
    -DOPENEMS_GPU_PLUGINS=ON -DOPENEMS_HIP_AS_CUDA=ON "-DCSXCAD_ROOT_DIR=$gb\opt" "-DFPARSER_ROOT_DIR=$gb\opt" "-DCMAKE_PREFIX_PATH=$gb\opt"
& $cmake --build "$gb\build\openEMS_gpu" --target openEMS_gpu_hip_nvidia
& $cmake --install "$gb\build\openEMS_gpu"
```

When it finishes, `opt\bin\openEMS\plugins\openEMS_gpu_hip_nvidia.dll` must exist. **`cudart64_12.dll`** must also sit
next to `openEMS.exe`, in `opt\bin` (copy it from `cuda\bin` if `install` did not).

> It is **better** to build everything with the same MSVC 14.44 rather than mixing. Here fparser, CSXCAD and openEMS (CPU)
> were built with Visual Studio 18's 14.51 and only the plugin with 14.44; it worked, but it is not the safest combination.

## 7. Check that it works

```powershell
& "$gb\opt\bin\openEMS.exe" --help        # must start without DLL errors
& "$env:LOCALAPPDATA\antenas\venv\Scripts\python.exe" herramientas\comparar_gpu.py monopolo_recto
```

`comparar_gpu.py` simulates the type on CPU and GPU and compares frequency, S11 and impedance. Expected (RTX 3050 Laptop,
2.44 GHz, normal precision): ~10–13× faster; resonance frequency within 0.06 %, S11 within 0.6 dB, impedance within 3 Ω.
If the GPU does not respond, the program warns and falls back to the CPU.

## 8. Using it

- Interface: the **«GPU acceleration (experimental)»** checkbox in the Simulation tab (shown if the engine is found).
- Environment variables: `ANTENAS_GPU=0` forces the CPU; `OPENEMS_GPU_DIR` points to another folder with the GPU `openEMS.exe`.
- With **a single GPU only one simulation should run at a time** (the CPU allows two).
- The Python `openEMS 0.37` wheel **cannot choose an engine**, so `antenas/gpu.py` writes the XML with `FDTD.Write2XML`
  and calls the `master` `openEMS.exe` directly with `--engine=gpu`.
- Gain and efficiency come out somewhat high compared with the CPU: confirm the final design with `ANTENAS_GPU=0`.
- Video memory limits the simulation size (4 GB on the RTX 3050 Laptop; the exact limit has not been measured).

## Known problems

| Symptom | Cause and fix |
|---|---|
| `cudafe++` gives `ACCESS_VIOLATION` while building | `nvcc` 12.9 with VS 18's MSVC 14.51: use MSVC 14.44 (step 4). |
| The plugin builds but the simulation says there is no GPU | Wrong architecture in `CMAKE_CUDA_ARCHITECTURES`, old driver, or missing `cudart64_12.dll` (probable causes). |
| `openEMS.exe` does not start (missing DLL) | Copy the vcpkg DLLs (`build\openEMS\vcpkg_installed\x64-windows-release\bin`) to `opt\bin`. |
| vcpkg takes hours | It is Boost. The cache (`vcpkg\buildtrees`, 8 GB) can be deleted afterwards. |
| Works in the test but fails on a large antenna | Out of video memory: use the CPU or a coarser mesh. |

## Other cards (untested)

The GPU engine has more backends: **AMD** (ROCm/HIP, `openEMS_gpu_hip_amd` plugin, with ROCm installed), **Intel Arc**
(SYCL, in [PR #243](https://github.com/thliebig/openEMS/pull/243), still a draft, with oneAPI's `icpx`) and **Apple
Silicon** (Metal built in; the published speed-up is ~1×, not worth it). None of them has been tried here.

## To do

- [x] Verified from scratch on GitHub Actions (a clean Windows runner) and the result tested on an RTX 3050.
- [ ] Try the package on another NVIDIA GPU (RTX 20, 40 or 50): the workflow already builds for those architectures, untested.
- [ ] Publish the `.zip` as a release asset and offer it from the installer.
- [ ] A script (`herramientas/compilar_gpu.ps1`) that does steps 1–6 and only asks for the GPU architecture.
- [ ] Offer the GPU openEMS as an installer option (today only the CPU 0.37 is installed).
