# Fase 0 — Entorno y validación de openEMS

## Entorno

- openEMS v0.37.0 (MSVC, Windows) en `%LOCALAPPDATA%\Programs\openEMS\openEMS`
- Python 3.14 en `%LOCALAPPDATA%\antenas\venv` (fuera del proyecto: en OneDrive la ruta supera los 260
  caracteres de Windows y fallan las DLL de shapely) con las wheels `openems-0.37.0` y `csxcad-0.7.0`
- `comun.py` fija `CSXCAD_INSTALL_PATH` al importarse; no se tocan variables del sistema

Recrear el entorno:

```
python -m venv %LOCALAPPDATA%\antenas\venv
%LOCALAPPDATA%\antenas\venv\Scripts\python -m pip install -r requirements.txt
%LOCALAPPDATA%\antenas\venv\Scripts\python -m pip install --no-index --find-links %LOCALAPPDATA%\Programs\openEMS\openEMS\python openEMS
```

## Prueba A — dipolo λ/2 en espacio libre (`test_dipolo.py [refinado]`)

| Malla | Celdas | Tiempo | L/λ en resonancia | R en resonancia |
|---|---|---|---|---|
| ×1 | 172 k | 29 s | 0,4559 | 73,0 Ω |
| ×2 | 900 k | 130 s | 0,4611 | 72,2 Ω |
| ×4 | 5,5 M | 35 min | 0,4647 | 71,9 Ω |
| Teoría (λ/d ≈ 260) | | | ≈ 0,47 | ≈ 70–73 Ω |

Converge hacia la teoría. Con la malla por defecto (×1) la frecuencia sale ~2 % baja.

## Prueba B — monopolo impreso 2,45 GHz, FR4 1,6 mm (`test_monopolo.py`)

Placa 40 × 69 mm, masa 40 × 40 mm, línea de 50 Ω de 3,06 mm, tira radiante de 2 mm.

| Iteración | Longitud tira | Centro banda −10 dB | Banda −10 dB |
|---|---|---|---|
| 1 (fórmula) | 18,62 mm | 3,110 GHz (+27 %) | 2,85–3,39 GHz |
| 2 (ajuste) | 23,63 mm | 2,463 GHz (+0,5 %) | 2,02–3,00 GHz |

A 2,45 GHz: directividad 3,6 dBi, ganancia 3,1 dBi, eficiencia de radiación 90 %,
eficiencia total 85 %. Diagrama omnidireccional en el plano transversal a la tira.
Unos 4 min por simulación (~1 M celdas).

## Lecciones para el programa

1. La fórmula analítica falla un 27 %; la simulación en el bucle es imprescindible.
2. El criterio de ajuste debe ser el **centro de la banda a −10 dB** (o la cobertura de la
   banda objetivo), no el mínimo de S11: con planos de masa pequeños aparecen varios mínimos.
3. El centro de NF2FF se pasa en **metros**, no en unidades de malla.
4. Conviene un ajuste de "precisión de malla" (×1 rápido para iterar, ×2 para el diseño final).
5. La caché por geometría evita repetir simulaciones.
