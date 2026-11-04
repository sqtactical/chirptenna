# Evita la suspensión por inactividad mientras haya simulaciones de openEMS en marcha
# (procesos de antenas.validar_lote, antenas.simular_cli, antenas.comparar_mallas o referencias.*, o
# cualquier python con mucha CPU).
# Deja que la pantalla se apague y se bloquee: eso no para las simulaciones; la suspensión, sí.
# No cambia la configuración de energía: usa SetThreadExecutionState, que se anula al cerrar este proceso.
# Termina solo tras 10 minutos sin simulaciones.
Add-Type -Namespace Win32 -Name Energia -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
'@
$ES_CONTINUOUS = [uint32]'0x80000000'
$ES_SYSTEM_REQUIRED = [uint32]'0x00000001'
$patron = 'antenas\.(validar_lote|simular_cli|comparar_mallas)|referencias\.'
$sin_simulaciones = 0
$cpu_antes = @{}
while ($sin_simulaciones -lt 10) {
    $hay = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
             Where-Object { $_.CommandLine -match $patron }).Count -gt 0
    # También cuenta cualquier python que haya gastado > 30 s de CPU en el último minuto (scripts
    # sueltos que llaman a simulacion.simular): openEMS usa varios hilos a plena carga.
    $cpu_ahora = @{}
    foreach ($p in @(Get-Process python -ErrorAction SilentlyContinue)) {
        $cpu_ahora[$p.Id] = $p.TotalProcessorTime.TotalSeconds
        if ($cpu_antes.ContainsKey($p.Id) -and ($cpu_ahora[$p.Id] - $cpu_antes[$p.Id]) -gt 30) { $hay = $true }
    }
    $cpu_antes = $cpu_ahora
    if ($hay) {
        [void][Win32.Energia]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED)
        $sin_simulaciones = 0
    } else {
        [void][Win32.Energia]::SetThreadExecutionState($ES_CONTINUOUS)
        $sin_simulaciones++
    }
    Start-Sleep -Seconds 60
}
[void][Win32.Energia]::SetThreadExecutionState($ES_CONTINUOUS)
Write-Output 'Sin simulaciones durante 10 minutos: se permite de nuevo la suspensión.'
