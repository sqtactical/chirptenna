<#
Instalador de Chirptenna para Windows 10/11, sin permisos de administrador.

Se lanza con instalar.bat (doble clic). Hace, saltándose lo que ya esté hecho:
  1. Python 3.14 de python.org (instalación solo para el usuario; se comprueba la firma digital).
  2. openEMS 0.37 de su página oficial en GitHub (se comprueba el SHA-256) en %LOCALAPPDATA%\Programs\openEMS.
  3. Entorno de Python propio en %LOCALAPPDATA%\antenas\venv (fuera de OneDrive: rutas largas).
  4. Paquetes de Python (versiones exactas de requirements-lock.txt) y los módulos de openEMS.
  5. Comprueba KiCad (opcional: hace falta para sacar los Gerber).
  6. Si hay una GPU NVIDIA compatible, el openEMS con motor GPU de la release de Chirptenna (opcional, 12 MB, se
     comprueba el SHA-256) en %LOCALAPPDATA%\Programs\gpu-build: simula ~10 veces más rápido. Guía: docs/GPU.md.
  7. Acceso directo «Chirptenna» en el escritorio.

Opciones:  -Comprobar          solo dice qué falta, sin descargar ni cambiar nada
           -SinPreguntas       no pregunta (acceso directo sí, no abre la web de KiCad)
           -SinAccesoDirecto   no crea el acceso directo del escritorio
           -SinGPU             no instala el motor de GPU (se simula en la CPU)
           -Python <ruta>      usa ese python.exe (3.13 o 3.14) en vez de buscarlo o instalarlo
#>
param([switch]$Comprobar, [switch]$SinPreguntas, [switch]$SinAccesoDirecto, [switch]$SinGPU, [string]$Python = '')

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'          # la barra de progreso hace muy lenta la descarga en PowerShell 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Raiz       = Split-Path -Parent $PSScriptRoot
$Base       = Join-Path $env:LOCALAPPDATA 'antenas'
$Venv       = Join-Path $Base 'venv'
$PyVenv     = Join-Path $Venv 'Scripts\python.exe'
$Descargas  = Join-Path $Base 'descargas'
$DirOpenEMS = Join-Path $env:LOCALAPPDATA 'Programs\openEMS\openEMS'
$DirGPU     = Join-Path $env:LOCALAPPDATA 'Programs\gpu-build'

# Versiones fijadas (comprobadas): las wheels de openEMS 0.37 solo existen para Python 3.13 y 3.14
$PY_VERSION  = '3.14.10'
$PY_URL      = "https://www.python.org/ftp/python/$PY_VERSION/python-$PY_VERSION-amd64.exe"
$OEMS_URL    = 'https://github.com/thliebig/openEMS-Project/releases/download/v0.37.0/openEMS_x64_v0.37.0_msvc.zip'
$OEMS_SHA256 = 'E4F14FD6E9BE7D0C1FD9C244768C21C1C2B62B8AA81F08253EBF6E06040CDA5A'
$KICAD_WEB   = 'https://www.kicad.org/download/windows/'
# openEMS con motor GPU (NVIDIA): lo compila .github/workflows/compilar-gpu.yml y está adjunto a la release v0.2.0-alpha
$GPU_URL     = 'https://github.com/sqtactical/chirptenna/releases/download/v0.2.0-alpha/openEMS-gpu-win64-cuda12.9-sm75-80-86-89-120.zip'
$GPU_SHA256  = '9CB3D3E6DD7239C7A8F211DF05FAF17E7AB4557D70C114BF3A3AF1A424AF6B3D'
$GPU_CC      = @('7.5', '8.0', '8.6', '8.9', '12.0')   # compute capability incluidas: RTX 20, A100, RTX 30, RTX 40, RTX 50

$faltan = New-Object System.Collections.ArrayList

function Paso($n, $t) { Write-Host ''; Write-Host "[$n/7] $t" -ForegroundColor Cyan }
function Bien($t)     { Write-Host "   OK  $t" -ForegroundColor Green }
function Aviso($t)    { Write-Host "   !   $t" -ForegroundColor Yellow }
function Falla($t)    { Write-Host "   X   $t" -ForegroundColor Red }

function Preguntar($texto, $porDefecto) {
    if ($SinPreguntas) { return $porDefecto }
    $r = Read-Host "   $texto"
    if ([string]::IsNullOrWhiteSpace($r)) { return $porDefecto }
    return $r.Trim().ToLower().StartsWith('s')
}

function Descargar($url, $destino) {
    New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
    Write-Host "   Descargando $url"
    Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing
}

function Version-Python($exe) {
    try {
        $v = & $exe -c "import sys; print('%d.%d' % sys.version_info[:2])"
        if ($LASTEXITCODE -eq 0 -and $v) { return "$v".Trim() }
    } catch {}
    return $null
}

function Buscar-Python {
    foreach ($v in '314', '313') {
        foreach ($c in @((Join-Path $env:LOCALAPPDATA "Programs\Python\Python$v\python.exe"),
                         (Join-Path $env:ProgramFiles "Python$v\python.exe"))) {
            if (Test-Path $c) { return $c }
        }
    }
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        foreach ($v in '3.14', '3.13') {
            try {
                $r = & py.exe "-$v" -c "import sys; print(sys.executable)"
                if ($LASTEXITCODE -eq 0 -and $r) { return "$r".Trim() }
            } catch {}
        }
    }
    return $null
}

function Buscar-KiCad {
    $c = @()
    foreach ($base in @($env:ProgramFiles, 'C:\Program Files') | Select-Object -Unique) {
        $dir = Join-Path $base 'KiCad'
        if (Test-Path $dir) {
            foreach ($d in Get-ChildItem $dir -Directory) {
                $exe = Join-Path $d.FullName 'bin\kicad-cli.exe'
                $v = [version]'0.0'
                [void][version]::TryParse($d.Name, [ref]$v)
                if (Test-Path $exe) { $c += [pscustomobject]@{ Version = $v; Ruta = $exe } }
            }
        }
    }
    # la versión más nueva (ordenar como texto pondría 9.0 delante de 10.0)
    if ($c.Count -gt 0) { return ($c | Sort-Object Version -Descending | Select-Object -First 1).Ruta }
    $g = Get-Command kicad-cli.exe -ErrorAction SilentlyContinue
    if ($g) { return $g.Source }
    return $null
}

function Buscar-GPU {
    # (nombre, compute capability) de la primera GPU NVIDIA que ve nvidia-smi, o $null
    $smi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    $exe = if ($smi) { $smi.Source } else {
        @((Join-Path $env:SystemRoot 'System32\nvidia-smi.exe'),
          (Join-Path $env:ProgramFiles 'NVIDIA Corporation\NVSMI\nvidia-smi.exe')) | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if (-not $exe) { return $null }
    try {
        $l = & $exe --query-gpu=name,compute_cap --format=csv,noheader 2>$null | Select-Object -First 1
        if ($LASTEXITCODE -ne 0 -or -not $l) { return $null }
        $p = "$l".Split(',')
        return [pscustomobject]@{ Nombre = $p[0].Trim(); Cap = $(if ($p.Count -gt 1) { $p[1].Trim() } else { '' }) }
    } catch { return $null }
}

Write-Host ''
Write-Host '  Chirptenna: instalación' -ForegroundColor White
Write-Host "  Programa en: $Raiz"
if ($Comprobar) { Write-Host '  Modo comprobación: no se descarga ni se cambia nada.' -ForegroundColor Yellow }

try {
    # ------------------------------------------------------------------ 1. Python
    Paso 1 "Python 3.13 o 3.14"
    if ($Python) {
        if (-not (Test-Path $Python)) { throw "No existe $Python" }
        if ((Version-Python $Python) -notin @('3.13', '3.14')) { throw "$Python no es Python 3.13 ni 3.14" }
        $python = $Python
    } else {
        $python = Buscar-Python
    }
    if ($python) {
        Bien "Python $(Version-Python $python) en $python"
    } elseif ($Comprobar) {
        Falla 'No hay Python 3.13 ni 3.14'; [void]$faltan.Add('Python')
    } else {
        $exe = Join-Path $Descargas "python-$PY_VERSION-amd64.exe"
        Descargar $PY_URL $exe
        $firma = Get-AuthenticodeSignature $exe
        if ($firma.Status -ne 'Valid' -or $firma.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            throw "La firma del instalador de Python no es válida ($($firma.Status)). No se ejecuta."
        }
        Write-Host '   Instalando Python (solo para este usuario, 1–2 min)...'
        $p = Start-Process -FilePath $exe -Wait -PassThru -ArgumentList @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=0', 'Include_test=0', 'Include_doc=0', 'Include_launcher=0')
        if ($p.ExitCode -ne 0) { throw "El instalador de Python terminó con el código $($p.ExitCode)" }
        $python = Buscar-Python
        if (-not $python) { throw 'Python se instaló pero no se encuentra.' }
        Bien "Python $(Version-Python $python) instalado en $python"
    }

    # ------------------------------------------------------------------ 2. openEMS
    Paso 2 'openEMS 0.37 (simulador electromagnético)'
    $exeOEMS = Join-Path $DirOpenEMS 'openEMS.exe'
    if (Test-Path $exeOEMS) {
        Bien "openEMS en $DirOpenEMS"
    } elseif ($Comprobar) {
        Falla "No está en $DirOpenEMS"; [void]$faltan.Add('openEMS')
    } else {
        $zip = Join-Path $Descargas 'openEMS_x64_v0.37.0_msvc.zip'
        if (-not (Test-Path $zip) -or (Get-FileHash $zip -Algorithm SHA256).Hash -ne $OEMS_SHA256) {
            Descargar $OEMS_URL $zip
        }
        $hash = (Get-FileHash $zip -Algorithm SHA256).Hash
        if ($hash -ne $OEMS_SHA256) { throw "El SHA-256 de openEMS no coincide ($hash). No se instala." }
        Bien 'Descarga comprobada (SHA-256)'
        $tmp = Join-Path $Descargas 'openEMS_tmp'
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
        Write-Host '   Descomprimiendo...'
        Expand-Archive -Path $zip -DestinationPath $tmp
        $encontrado = Get-ChildItem $tmp -Recurse -Filter 'openEMS.exe' | Select-Object -First 1
        if (-not $encontrado) { throw 'El zip de openEMS no contiene openEMS.exe' }
        New-Item -ItemType Directory -Force -Path (Split-Path $DirOpenEMS) | Out-Null
        Move-Item -Path $encontrado.DirectoryName -Destination $DirOpenEMS
        Remove-Item $tmp -Recurse -Force
        Bien "openEMS instalado en $DirOpenEMS"
    }

    # ------------------------------------------------------------------ 3. Entorno de Python
    Paso 3 "Entorno de Python del programa ($Venv)"
    $vVenv = $null
    if (Test-Path $PyVenv) { $vVenv = Version-Python $PyVenv }
    if ($vVenv -in @('3.13', '3.14')) {
        Bien "Ya existe (Python $vVenv)"
    } elseif ($Comprobar) {
        if ($vVenv) { Falla "Existe pero es Python $vVenv (hace falta 3.13 o 3.14)" } else { Falla 'No existe' }
        [void]$faltan.Add('entorno de Python')
    } else {
        if (-not $python) { throw 'Falta Python' }
        if ($vVenv) {
            $viejo = "$Venv.antiguo_" + (Get-Date -Format 'yyyyMMdd_HHmmss')
            Aviso "El entorno existente es Python ${vVenv}; se aparta a $viejo"
            Move-Item $Venv $viejo
        }
        New-Item -ItemType Directory -Force -Path $Base | Out-Null
        & $python -m venv $Venv
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de Python' }
        Bien 'Entorno creado'
    }

    # ------------------------------------------------------------------ 4. Paquetes
    Paso 4 'Paquetes de Python (numpy, shapely, nicegui…) y módulos de openEMS'
    if ($Comprobar) {
        if (Test-Path $PyVenv) {
            # antenas.simulacion fija CSXCAD_INSTALL_PATH antes de importar openEMS (sin ella no cargan sus DLL)
            Push-Location $Raiz
            try { & $PyVenv -c "import numpy, shapely, nicegui, plotly, h5py, ezdxf, serial, antenas.simulacion" }
            finally { Pop-Location }
            if ($LASTEXITCODE -eq 0) { Bien 'Todos instalados' } else { Falla 'Faltan paquetes'; [void]$faltan.Add('paquetes') }
        } else { Falla 'Sin entorno'; [void]$faltan.Add('paquetes') }
    } else {
        Write-Host '   Instalando (la primera vez descarga ~150 MB, 2–5 min)...'
        # Versiones exactas probadas (requirements-lock.txt); si falta, los rangos de requirements.txt
        $req = Join-Path $Raiz 'requirements-lock.txt'
        if (-not (Test-Path $req)) { $req = Join-Path $Raiz 'requirements.txt' }
        & $PyVenv -m pip install --disable-pip-version-check -q -r $req
        if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de los paquetes (¿hay conexión a internet?)' }
        & $PyVenv -m pip install --disable-pip-version-check -q --no-index --find-links (Join-Path $DirOpenEMS 'python') openEMS CSXCAD
        if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de los módulos de openEMS' }
        Bien 'Paquetes instalados'
    }

    # ------------------------------------------------------------------ 5. KiCad
    Paso 5 'KiCad 8 o posterior (opcional: para los Gerber y el DRC)'
    $kicad = Buscar-KiCad
    if ($kicad) {
        Bien "kicad-cli en $kicad"
    } else {
        Aviso 'No está instalado. Sin KiCad se diseña, se simula y se exporta el DXF y la placa KiCad, pero no los Gerber.'
        Aviso "Descárgalo de $KICAD_WEB e instálalo con las opciones por defecto."
        if (-not $Comprobar -and (Preguntar '¿Abrir ahora la página de descarga de KiCad? (s/N)' $false)) {
            Start-Process $KICAD_WEB
        }
    }

    # ------------------------------------------------------------------ 6. GPU (opcional)
    Paso 6 'Aceleración por GPU NVIDIA (opcional: simula ~10 veces más rápido)'
    $exeGPU = Join-Path $DirGPU 'opt\bin\openEMS.exe'
    $gpu = Buscar-GPU
    if (Test-Path $exeGPU) {
        Bien "openEMS con GPU en $DirGPU"
    } elseif ($SinGPU) {
        Aviso 'Sin motor de GPU (opción -SinGPU): se simula en la CPU.'
    } elseif (-not $gpu) {
        Aviso 'No se encuentra una GPU NVIDIA (nvidia-smi): se simula en la CPU. Es lo normal sin tarjeta dedicada.'
    } else {
        Bien "GPU: $($gpu.Nombre) (compute capability $($gpu.Cap))"
        if ($gpu.Cap -and ($gpu.Cap -notin $GPU_CC)) {
            Aviso "El paquete de GPU incluye las arquitecturas $($GPU_CC -join ', ') y la tuya es $($gpu.Cap): se simula en la CPU (compilarlo para tu tarjeta: docs/GPU.md)."
        } elseif ($Comprobar) {
            Aviso 'Hay una GPU compatible pero no está instalado el motor de GPU (opcional): instalar.bat lo instala.'
        } elseif (Preguntar '¿Instalar el motor de GPU (12 MB)? (S/n)' $true) {
            try {
                $zipGPU = Join-Path $Descargas 'openEMS-gpu-win64.zip'
                if (-not (Test-Path $zipGPU) -or (Get-FileHash $zipGPU -Algorithm SHA256).Hash -ne $GPU_SHA256) {
                    Descargar $GPU_URL $zipGPU
                }
                $hash = (Get-FileHash $zipGPU -Algorithm SHA256).Hash
                if ($hash -ne $GPU_SHA256) { throw "el SHA-256 no coincide ($hash)" }
                Bien 'Descarga comprobada (SHA-256)'
                New-Item -ItemType Directory -Force -Path $DirGPU | Out-Null
                Expand-Archive -Path $zipGPU -DestinationPath $DirGPU -Force
                if (-not (Test-Path $exeGPU)) { throw 'el paquete no contiene opt\bin\openEMS.exe' }
                Bien "Motor de GPU instalado en $DirGPU"
                Push-Location $Raiz
                try {
                    $r = & $PyVenv -c "from antenas import gpu; ok, m = gpu.disponible(); print('OK' if ok else 'NO ' + str(m))"
                } finally { Pop-Location }
                if ("$r".Trim() -eq 'OK') { Bien 'El programa lo reconoce: la simulación usará la GPU (casilla en la pestaña Simulación)' }
                else { Aviso "El programa no lo reconoce ($r): se simula en la CPU." }
            } catch {
                Aviso "No se pudo instalar el motor de GPU ($($_.Exception.Message)): se simula en la CPU."
                if ((Test-Path $DirGPU) -and -not (Test-Path $exeGPU)) { Remove-Item $DirGPU -Recurse -Force -ErrorAction SilentlyContinue }
            }
        } else {
            Aviso 'Sin motor de GPU: se simula en la CPU (puedes instalarlo después con instalar.bat).'
        }
    }

    # ------------------------------------------------------------------ 7. Acceso directo
    Paso 7 'Acceso directo en el escritorio'
    $escritorio = [Environment]::GetFolderPath('Desktop')
    $lnk = Join-Path $escritorio 'Chirptenna.lnk'
    if ($Comprobar) {
        if (Test-Path $lnk) { Bien "Existe: $lnk" } else { Aviso 'No hay acceso directo (opcional)' }
    } elseif ($SinAccesoDirecto) {
        Aviso 'Sin acceso directo (opción -SinAccesoDirecto): abre el programa con iniciar.bat'
    } elseif (Preguntar '¿Crear el acceso directo «Chirptenna» en el escritorio? (S/n)' $true) {
        $ico = Join-Path $Base 'chirptenna.ico'
        $png = Join-Path $Raiz 'docs\logo\chirptenna.png'
        if (Test-Path $png) {
            & $PyVenv -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGBA').save(sys.argv[2], sizes=[(16,16),(32,32),(48,48),(256,256)])" $png $ico
        }
        $ws = New-Object -ComObject WScript.Shell
        $s = $ws.CreateShortcut($lnk)
        $s.TargetPath = Join-Path $Raiz 'iniciar.bat'
        $s.WorkingDirectory = $Raiz
        $s.Description = 'Chirptenna: generador de antenas para PCB'
        if (Test-Path $ico) { $s.IconLocation = $ico }
        $s.Save()
        Bien "Creado: $lnk"
    } else {
        Aviso 'Sin acceso directo: abre el programa con iniciar.bat'
    }

    # ------------------------------------------------------------------ Comprobación final
    if (-not $Comprobar) {
        Write-Host ''
        Write-Host 'Comprobación final...' -ForegroundColor Cyan
        Push-Location $Raiz
        try {
            & $PyVenv -c "import antenas.simulacion, antenas.exportar, nicegui; print('   OK  el programa carga bien')"
            if ($LASTEXITCODE -ne 0) { throw 'El programa no carga: revisa los mensajes de arriba' }
        } finally { Pop-Location }
        Write-Host ''
        Write-Host '  Instalación terminada.' -ForegroundColor Green
        Write-Host '  Abre Chirptenna con el acceso directo del escritorio o con iniciar.bat:'
        Write-Host '  se abrirá el navegador en http://localhost:8080'
    } elseif ($faltan.Count -eq 0) {
        Write-Host ''; Write-Host '  Todo instalado.' -ForegroundColor Green
    } else {
        Write-Host ''; Write-Host ("  Falta: " + ($faltan -join ', ') + '. Ejecuta instalar.bat sin -Comprobar.') -ForegroundColor Yellow
    }
    exit 0
} catch {
    Write-Host ''
    Falla $_.Exception.Message
    Write-Host '  La instalación no ha terminado. Corrige el problema y vuelve a ejecutar instalar.bat:'
    Write-Host '  lo que ya esté hecho no se repite.'
    exit 1
}
