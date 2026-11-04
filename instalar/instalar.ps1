<#
Instalador de Chirptenna para Windows 10/11, sin permisos de administrador.

Se lanza con instalar.bat (doble clic). Hace, saltándose lo que ya esté hecho:
  1. Python 3.14 de python.org (instalación solo para el usuario; se comprueba la firma digital).
  2. openEMS 0.37 de su página oficial en GitHub (se comprueba el SHA-256) en %LOCALAPPDATA%\Programs\openEMS.
  3. Entorno de Python propio en %LOCALAPPDATA%\antenas\venv (fuera de OneDrive: rutas largas).
  4. Paquetes de Python (requirements.txt) y los módulos de openEMS.
  5. Comprueba KiCad (opcional: hace falta para sacar los Gerber).
  6. Acceso directo «Chirptenna» en el escritorio.

Opciones:  -Comprobar          solo dice qué falta, sin descargar ni cambiar nada
           -SinPreguntas       no pregunta (acceso directo sí, no abre la web de KiCad)
           -SinAccesoDirecto   no crea el acceso directo del escritorio
           -Python <ruta>      usa ese python.exe (3.13 o 3.14) en vez de buscarlo o instalarlo
#>
param([switch]$Comprobar, [switch]$SinPreguntas, [switch]$SinAccesoDirecto, [string]$Python = '')

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'          # la barra de progreso hace muy lenta la descarga en PowerShell 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Raiz       = Split-Path -Parent $PSScriptRoot
$Base       = Join-Path $env:LOCALAPPDATA 'antenas'
$Venv       = Join-Path $Base 'venv'
$PyVenv     = Join-Path $Venv 'Scripts\python.exe'
$Descargas  = Join-Path $Base 'descargas'
$DirOpenEMS = Join-Path $env:LOCALAPPDATA 'Programs\openEMS\openEMS'

# Versiones fijadas (comprobadas): las wheels de openEMS 0.37 solo existen para Python 3.13 y 3.14
$PY_VERSION  = '3.14.10'
$PY_URL      = "https://www.python.org/ftp/python/$PY_VERSION/python-$PY_VERSION-amd64.exe"
$OEMS_URL    = 'https://github.com/thliebig/openEMS-Project/releases/download/v0.37.0/openEMS_x64_v0.37.0_msvc.zip'
$OEMS_SHA256 = 'E4F14FD6E9BE7D0C1FD9C244768C21C1C2B62B8AA81F08253EBF6E06040CDA5A'
$KICAD_WEB   = 'https://www.kicad.org/download/windows/'

$faltan = New-Object System.Collections.ArrayList

function Paso($n, $t) { Write-Host ''; Write-Host "[$n/6] $t" -ForegroundColor Cyan }
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
        & $PyVenv -m pip install --disable-pip-version-check -q -r (Join-Path $Raiz 'requirements.txt')
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

    # ------------------------------------------------------------------ 6. Acceso directo
    Paso 6 'Acceso directo en el escritorio'
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
