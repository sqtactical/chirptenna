# Compilar openEMS con GPU (NVIDIA, Windows)

Chirptenna puede simular con la GPU: ~10× más rápido que la CPU (RTX 3050 Laptop, mismos resultados dentro del error de
ajuste). Pero el openEMS que instala el instalador (v0.37.0) **no trae el motor GPU**: está solo en la rama `master`
de [openEMS](https://github.com/thliebig/openEMS), así que hay que compilarlo.

> **Estado de esta guía: reconstruida, no verificada desde cero.** Sale de lo que quedó instalado en el ordenador de
> desarrollo (versiones, opciones de CMake, carpetas), no de repetir la compilación en una máquina limpia. Si algún
> paso falla, es probable que sea un detalle que se hizo a mano y no quedó anotado: avisa o corrige esta guía.
> La verificación de cero está pendiente (ver «Pendiente» al final).

**Antes de nada: la arquitectura de la GPU.** El plugin de GPU se compila **para una arquitectura de GPU concreta**
(`CMAKE_CUDA_ARCHITECTURES`). Aquí se compiló solo para `86` (RTX 3050 Laptop, *compute capability* 8.6). En otra tarjeta
NVIDIA ese binario puede no funcionar o funcionar solo por compilación en el momento (PTX), así que **hay que compilarlo
para tu tarjeta** (paso 6). Tu *compute capability* sale con `nvidia-smi --query-gpu=name,compute_cap --format=csv`.

## Requisitos

- Windows 10/11 de 64 bits, **sin necesidad de administrador**: todo va en una carpeta del usuario.
- Una GPU NVIDIA con controlador reciente (aquí, 592.82). Solo se ha probado una *compute capability* 8.6; CUDA 12.9
  compila también para arquitecturas anteriores, pero no se ha comprobado con el plugin de openEMS.
- Visual Studio Build Tools con el **Windows SDK** (cualquier versión reciente; solo se usa el SDK y sus cabeceras).
- **Python 3.14** del proyecto (el `venv` de `instalar.bat`) para `herramientas/comparar_gpu.py` y para usarlo.
- **Espacio y tiempo:** aquí la carpeta de trabajo ocupó **14 GB** (8,8 GB de la caché de compilación de vcpkg, que se
  puede borrar después; 1,5 GB del MSVC portable; 2,2 GB de descargas). Cuenta con **varias horas**, sobre todo vcpkg
  compilando Boost, y con haberlo hecho antes en una máquina conocida: la primera vez da tropiezos.

La carpeta de trabajo por defecto es `%LOCALAPPDATA%\Programs\gpu-build` (el programa la busca ahí; si usas otra,
`OPENEMS_GPU_DIR` debe apuntar a su `opt\bin`).

```powershell
$gb = "$env:LOCALAPPDATA\Programs\gpu-build"
New-Item -ItemType Directory -Force $gb, "$gb\dl", "$gb\src", "$gb\build", "$gb\opt" | Out-Null
```

## 1. Herramientas portables

Versiones con las que funcionó. Basta descomprimir; no hace falta instalar nada.

| Herramienta | Versión | Carpeta |
|---|---|---|
| CMake | 4.4.5 (zip de Windows x64 de cmake.org) | `gpu-build\cmake-4.4.5-windows-x86_64` |
| Ninja | 1.13.2 (`ninja-win.zip` de github.com/ninja-build/ninja) | `gpu-build\ninja` |
| Git | MinGit (el del proyecto, `%LOCALAPPDATA%\Programs\MinGit`) | — |
| vcpkg | commit `29718cfe` (05-11-2026), `git clone https://github.com/microsoft/vcpkg` | `gpu-build\vcpkg` |

```powershell
& git clone https://github.com/microsoft/vcpkg "$gb\vcpkg"
& "$gb\vcpkg\bootstrap-vcpkg.bat" -disableMetrics
```

## 2. CUDA 12.9.1 (solo el compilador y el *runtime*, sin instalador)

NVIDIA publica los componentes sueltos en `https://developer.download.nvidia.com/compute/cuda/redist/`. Hacen falta
cuatro, de la versión 12.9.1 (`redistrib_12.9.1.json` da las rutas exactas):

| Paquete | Versión |
|---|---|
| `cuda_nvcc` | 12.9.86 |
| `cuda_cudart` | 12.9.79 |
| `cuda_cccl` | 12.9.27 |
| `cuda_profiler_api` | 12.9.79 |

Cada uno es un `.zip` (`cuda_nvcc/windows-x86_64/cuda_nvcc-windows-x86_64-12.9.86-archive.zip`, etc.). Se descomprimen
**todos en la misma carpeta**, `gpu-build\cuda`, de modo que queden juntas `bin\` (con `nvcc.exe`), `include\`, `lib\` y
`nvvm\`. No se instala el controlador de CUDA aparte: lo trae el controlador normal de la tarjeta.

## 3. Cabeceras de HIP 7.2.4

El plugin se escribe contra HIP; en NVIDIA se compila como CUDA con la opción `OPENEMS_HIP_AS_CUDA`. Solo hacen falta
las **cabeceras**: del paquete `.deb` `hip-dev` de ROCm 7.2.4 (repositorio de AMD, `repo.radeon.com/rocm/apt/7.2.4`;
la URL exacta está por confirmar) se extrae `opt/rocm-7.2.4/include` a `gpu-build\hip\opt\rocm-7.2.4\include`
(un `.deb` es un archivo `ar` con `data.tar.gz` dentro; sirve 7-Zip dos veces).

## 4. MSVC 14.44 portable

`nvcc` 12.9 **no soporta** el MSVC 14.51 de Visual Studio 18 (su `cudafe++` falla con `ACCESS_VIOLATION`). Hace falta un
MSVC 14.4x (VS 2022 17.x). Se bajó portable con `vsdownload.py` de [msvc-wine](https://github.com/mstorsjo/msvc-wine)
(Martin Storsjö) a `gpu-build\msvc17`; el compilador usado fue `msvc17\VC\Tools\MSVC\14.44.35207`. Los parámetros
exactos de la descarga están por confirmar (`python vsdownload.py --help`: versión de MSVC, `--dest`, aceptar la licencia).
Es una alternativa a instalar el componente «MSVC v143» desde el instalador de Visual Studio.

## 5. Fuentes

`master` cambia cada pocos días: para repetir el resultado, fija los commits con los que funcionó.

| Proyecto | Repositorio | Commit probado |
|---|---|---|
| fparser | `https://github.com/thliebig/fparser` | `4b9c845` (29-04-2026) |
| CSXCAD | `https://github.com/thliebig/CSXCAD` | `626b99f` (21-10-2026) |
| openEMS | `https://github.com/thliebig/openEMS` | `5fecbb5` (02-11-2026) |

```powershell
foreach ($p in @(@('fparser','4b9c845'), @('CSXCAD','626b99f'), @('openEMS','5fecbb5'))) {
    & git clone "https://github.com/thliebig/$($p[0])" "$gb\src\$($p[0])"
    & git -C "$gb\src\$($p[0])" checkout $p[1]
}
```

## 6. Compilar

Variables comunes. Las órdenes de CMake y de compilación hay que lanzarlas con el entorno de MSVC cargado (un
«x64 Native Tools Command Prompt», o `vcvars64.bat` de `msvc17\VC\Auxiliary\Build` o de Visual Studio Build Tools), para
que el compilador encuentre el SDK de Windows.

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
```

**CSXCAD** (vcpkg baja `tinyxml` y `hdf5` solo; usa el *triplet* `x64-windows-release`):

```powershell
$vc = "-DCMAKE_TOOLCHAIN_FILE=$vcpkg", "-DVCPKG_TARGET_TRIPLET=x64-windows-release", "-DVCPKG_HOST_TRIPLET=x64-windows-release"
& $cmake -S "$gb\src\CSXCAD" -B "$gb\build\CSXCAD" @comun @vc "-DCMAKE_PREFIX_PATH=$gb\opt" -DCSXCAD_BUILD_TESTS=OFF
& $cmake --build "$gb\build\CSXCAD"; & $cmake --install "$gb\build\CSXCAD"
```

**openEMS (CPU):** deja `openEMS.exe`, `openEMS.dll` y las DLL de vcpkg (Boost, HDF5…) en `opt\bin`.

```powershell
& $cmake -S "$gb\src\openEMS" -B "$gb\build\openEMS" @comun @vc "-DCSXCAD_ROOT_DIR=$gb\opt" "-DCMAKE_PREFIX_PATH=$gb\opt"
& $cmake --build "$gb\build\openEMS"; & $cmake --install "$gb\build\openEMS"
```

**Plugin de GPU (NVIDIA):** otra configuración de CMake sobre las mismas fuentes, con `nvcc` y el MSVC 14.44 como
compilador de CUDA. **Aquí se pone la arquitectura de tu tarjeta** (`86` = RTX 30xx; `75` = RTX 20xx; `89` = RTX 40xx;
`120` = RTX 50xx; o `native`, que CMake resuelve con la GPU instalada).

```powershell
$cl = "$gb\msvc17\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$arq = "86"        # ← la de tu GPU (nvidia-smi --query-gpu=compute_cap)
& $cmake -S "$gb\src\openEMS" -B "$gb\build\openEMS_gpu" @comun @vc `
    "-DCMAKE_CXX_COMPILER=$cl" "-DCMAKE_CUDA_COMPILER=$gb\cuda\bin\nvcc.exe" "-DCMAKE_CUDA_HOST_COMPILER=$cl" `
    "-DCMAKE_CUDA_ARCHITECTURES=$arq" "-DHIP_INCLUDE_DIR=$gb\hip\opt\rocm-7.2.4\include" `
    -DOPENEMS_GPU_PLUGINS=ON -DOPENEMS_HIP_AS_CUDA=ON "-DCSXCAD_ROOT_DIR=$gb\opt" "-DCMAKE_PREFIX_PATH=$gb\opt"
& $cmake --build "$gb\build\openEMS_gpu" --target openEMS_gpu_hip_nvidia
& $cmake --install "$gb\build\openEMS_gpu"
```

Al terminar debe existir `opt\bin\openEMS\plugins\openEMS_gpu_hip_nvidia.dll`. Junto a `openEMS.exe`, en `opt\bin`, tiene
que estar también **`cudart64_12.dll`** (cópiala de `cuda\bin` si el `install` no la dejó).

> **Conviene** compilar todo con el mismo MSVC 14.44 en vez de mezclar. Aquí fparser, CSXCAD y openEMS (CPU) se
> compilaron con el 14.51 de Visual Studio 18 y solo el plugin con el 14.44; funcionó, pero no es la combinación más
> segura.

## 7. Comprobar que funciona

```powershell
& "$gb\opt\bin\openEMS.exe" --help        # debe arrancar sin errores de DLL
& "$env:LOCALAPPDATA\antenas\venv\Scripts\python.exe" herramientas\comparar_gpu.py monopolo_recto
```

`comparar_gpu.py` simula el tipo en CPU y en GPU y compara frecuencia, S11 e impedancia. Lo esperado (RTX 3050 Laptop, 2,44 GHz,
precisión normal): ~10-13× más rápido; frecuencia de resonancia dentro del 0,06 %, S11 dentro de 0,6 dB, impedancia
dentro de 3 Ω. Si la GPU no responde, el programa avisa y usa la CPU.

## 8. Usarlo

- Interfaz: casilla **«Aceleración por GPU (experimental)»** en la pestaña Simulación (aparece si encuentra el motor).
- Variables de entorno: `ANTENAS_GPU=0` fuerza la CPU; `OPENEMS_GPU_DIR` apunta a otra carpeta con el `openEMS.exe` de GPU.
- Con **una sola GPU solo debe correr una simulación a la vez** (la CPU admite dos).
- El wheel `openEMS 0.37` de Python **no elige motor**, así que `antenas/gpu.py` escribe el XML con `FDTD.Write2XML` y
  llama directamente al `openEMS.exe` de `master` con `--engine=gpu`.
- La ganancia y la eficiencia salen algo altas respecto a la CPU: confirma el diseño final con `ANTENAS_GPU=0`.
- La memoria de la tarjeta limita el tamaño de la simulación (4 GB en la RTX 3050 Laptop; el límite exacto no se ha medido).

## Problemas conocidos

| Síntoma | Causa y arreglo |
|---|---|
| `cudafe++` da `ACCESS_VIOLATION` al compilar | `nvcc` 12.9 con el MSVC 14.51 de VS 18: usar el MSVC 14.44 (paso 4). |
| El plugin compila pero la simulación dice que no hay GPU | Arquitectura equivocada en `CMAKE_CUDA_ARCHITECTURES`, controlador antiguo o falta `cudart64_12.dll`. |
| `openEMS.exe` no arranca (falta una DLL) | Copia a `opt\bin` las DLL de vcpkg (`build\openEMS\vcpkg_installed\x64-windows-release\bin`). |
| vcpkg tarda horas | Es Boost. La caché (`vcpkg\buildtrees`, 8 GB) se puede borrar al acabar. |
| Funciona en la prueba y falla con una antena grande | Se quedó sin memoria de vídeo: usa la CPU o una malla más gruesa. |

## Otras tarjetas (sin probar)

El motor GPU tiene más *backends*: **AMD** (ROCm/HIP, plugin `openEMS_gpu_hip_amd`, con ROCm instalado), **Intel Arc**
(SYCL, en la [PR #243](https://github.com/thliebig/openEMS/pull/243), en borrador, con `icpx` de oneAPI) y **Apple
Silicon** (Metal integrado; la ganancia publicada es ~1×, no compensa). No se han probado aquí.

## Pendiente

- [ ] **Verificar la guía desde cero** en una carpeta limpia (o mejor, otra máquina con otra GPU NVIDIA), y corregir lo
      que se haya quedado sin anotar (URL del `.deb` de HIP, parámetros de `vsdownload.py`, comando de `cudart`).
- [ ] Un script (`herramientas/compilar_gpu.ps1`) que haga los pasos 1-6 y pida solo la arquitectura de la GPU.
- [ ] Ofrecer el openEMS con GPU como opción del instalador (hoy solo se instala el 0.37 de CPU).
