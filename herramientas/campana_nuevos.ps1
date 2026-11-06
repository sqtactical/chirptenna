# Campaña de barridos en GPU de los tipos sin validar (06-11). Cada línea es un barrido de herramientas/barrido.py;
# los resultados van a salidas/_barridos/<etiqueta>/ (resumen.json, resumen.csv, resultados.jsonl). Una GPU: en serie.
# Uso:  powershell -File herramientas/campana_nuevos.ps1
$py = "$env:LOCALAPPDATA\antenas\venv\Scripts\python.exe"
$b = { param($etiqueta, [string[]]$args_)
    if (Test-Path "salidas/_barridos/$etiqueta/resumen.json") { "(ya hecho) $etiqueta"; return }   # reanuda: salta los terminados
    & $py -X utf8 herramientas/barrido.py @args_ --etiqueta $etiqueta --top 2 }
& $b 'ifa_2g4'           @('ifa', '2,4 GHz', 'separacion_toma=2,3.5,5', 'largo_brazo=18,20,22')
& $b 'pifa_2g4'          @('pifa', '2,4 GHz', 'separacion_toma=5,7,9', 'largo_brazo=16,18,20')
& $b 'sleeve_2g4'        @('dipolo_sleeve', '2,4 GHz', 'alto=21,23.6,26', 'largo_masa=20,24,28')
& $b 'parche_circular_2g4' @('parche_circular', '2,4 GHz', 'corte=0.08,0.12,0.16,0.2', 'diagonal=0,1')
& $b 'parche_ranura_2g4' @('parche_ranura', '2,4 GHz', 'ranura_ancho=0.4,0.5,0.6', 'ranura_largo=0.3,0.4,0.5')
& $b 'parche_apilado_2g4' @('parche_apilado', '2,4 GHz', 'parasito_hueco=0.6,1,1.6', 'parasito_factor=0.92,0.96,1')
& $b 'vivaldi_2g4'       @('vivaldi', '2,4 GHz', 'ancho_apertura=40,48,56', 'largo_aleta=45,55,65')
& $b 'colineal_dipolos_2g4' @('colineal_dipolos', '2,4 GHz', 'factor_linea=0.9,1,1.1', 'largo_brazo=20,22,24')