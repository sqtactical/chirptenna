# Hook Stop: si hay archivos del proyecto modificados desde la última revisión de
# CLAUDE.md / RETOMAR.md, pide a Claude (una vez por tanda de cambios) que los revise.
#
# - El proyecto es la carpeta padre de .claude\ (donde está este script).
# - La referencia es la fecha más reciente de CLAUDE.md, RETOMAR.md y la marca
#   .claude\ultima_revision_claude_md. Al avisar se actualiza la marca, así que
#   no se repite el aviso hasta que vuelva a cambiar algo.
# - Con stop_hook_active (Claude ya está respondiendo a este aviso) no hace nada.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$entrada = [Console]::In.ReadToEnd()
if ($entrada) {
    try { $datos = $entrada | ConvertFrom-Json } catch { $datos = $null }
    if ($datos -and $datos.stop_hook_active) { exit 0 }
}

$proyecto = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$marca = Join-Path $PSScriptRoot '..\ultima_revision_claude_md'
$docs = @('CLAUDE.md', 'RETOMAR.md') | ForEach-Object { Join-Path $proyecto $_ } | Where-Object { Test-Path $_ }

$referencia = [datetime]::MinValue
foreach ($f in @($docs) + @($marca)) {
    if (Test-Path $f) {
        $t = (Get-Item $f).LastWriteTime
        if ($t -gt $referencia) { $referencia = $t }
    }
}

# Carpetas y archivos que no cuentan como "cambio del proyecto"
$excluirCarpetas = '\\(\.claude|\.git|__pycache__|\.venv|venv|Backup_[^\\]*|Graficas_Extractos[^\\]*)\\'
$excluirArchivos = '^(CLAUDE\.md|RETOMAR\.md|AGENTS\.md|~\$.*|_sesion\..*|.*\.asv|.*\.tmp)$'

$cambiados = Get-ChildItem $proyecto -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -gt $referencia -and
        $_.FullName -notmatch $excluirCarpetas -and
        $_.Name -notmatch $excluirArchivos
    } |
    Sort-Object LastWriteTime -Descending

if (-not $cambiados) { exit 0 }

# Marca de revisión: el aviso sale una sola vez por tanda de cambios
Set-Content -Path $marca -Value (Get-Date -Format s) -Encoding ASCII

$lista = ($cambiados | Select-Object -First 15 | ForEach-Object {
    '  - ' + $_.FullName.Substring($proyecto.Length + 1)
}) -join "`n"
$resto = $cambiados.Count - 15
if ($resto -gt 0) { $lista += "`n  - ... y $resto más" }

$motivo = @"
Hay archivos del proyecto modificados desde la última revisión de CLAUDE.md$(if (Test-Path (Join-Path $proyecto 'RETOMAR.md')) { ' / RETOMAR.md' }):
$lista

Antes de terminar, revisa si algo de lo hecho o aprendido en esta sesión debe quedar en CLAUDE.md (estructura, cómo se ejecuta, reglas, convenciones, problemas conocidos, lecciones) o en RETOMAR.md si existe (estado y siguientes pasos), y actualízalos de forma concisa. Si no hay nada nuevo que merezca guardarse, no cambies nada y termina sin mencionarlo.
"@

@{ decision = 'block'; reason = $motivo } | ConvertTo-Json -Compress
exit 0
