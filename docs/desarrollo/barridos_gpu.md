# Barridos en GPU: qué va y qué no (06-11-2026)

Generado por `python herramientas/resumen_barridos.py` a partir de `salidas/_barridos/*/resumen.json`.
Solo simulación (openEMS en GPU, FR4 de 1,6 mm con εr 4,5): sin medir ninguna placa. La ganancia y la eficiencia en GPU salen algo altas. «Peor S11» es el peor valor en toda la banda de uso; va ≤ −10 dB, justo hasta −6 dB. Etiquetas: `A_` = tamaño base de `dimensionar`; `B_` = barrido de parámetros; sin prefijo = campaña de los tipos nuevos.

| Tipo | f (MHz) | Barrido | Configs | Peor S11 (dB) | Veredicto | f res. (MHz) | Banda −10 dB | G (dBi) | η (%) | Mejor |
|---|---|---|---|---|---|---|---|---|---|---|
| colineal_coco | 2441.75 | A_colineal_coco_24GHz | 1 | -2.2 | **no va** | 2604.1 | [2557, 2652] | 1.4 | 45.0 | `{}` |
| colineal_coco | 5800 | A_colineal_coco_58GHz | 1 | -1.7 | **no va** | 6902.6 | [6771, 7037] | 0.35 | 44.5 | `{}` |
| colineal_dipolos | 5800 | A_colineal_dipolos_58GHz | 1 | -8.7 | **justo** | 5029.9 | [4949, 5112] | 1.75 | 37.0 | `{}` |
| colineal_franklin | 2441.75 | A_colineal_franklin_24GHz | 1 | -6.9 | **justo** | 2790.4 | [2738, 2844] | 2.34 | 80.6 | `{}` |
| colineal_franklin | 5800 | A_colineal_franklin_58GHz | 1 | -2.5 | **no va** | 5242.4 | [5154, 5332] | 1.86 | 56.9 | `{}` |
| dipolo | 2441.75 | A_dipolo_24GHz | 1 | -11.7 | **va** | 2558.8 | [2370, 2762] | 2.48 | 97.9 | `{}` |
| dipolo | 5800 | A_dipolo_58GHz | 1 | -17.7 | **va** | 5867.4 | [5429, 6341] | 2.53 | 87.5 | `{}` |
| dipolo_bowtie | 2441.75 | A_dipolo_bowtie_24GHz | 1 | -18.3 | **va** | 2591.8 | [2185, 3075] | 2.47 | 98.7 | `{}` |
| dipolo_bowtie | 5800 | A_dipolo_bowtie_58GHz | 1 | -8.3 | **justo** | 7153.9 | [6303, 8120] | 2.7 | 90.2 | `{}` |
| dipolo_sleeve | 2441.75 | sleeve_2g4 | 9 | -17.1 | **va** | 2441.1 | [2294, 2598] | 2.78 | 99.0 | `{"alto": 23.6, "largo_masa": 20.0}` |
| dipolo_sleeve | 5800 | A_dipolo_sleeve_58GHz | 1 | -6.2 | **justo** | 5113.8 | [4783, 5467] | 3.08 | 91.0 | `{}` |
| ifa | 2441.75 | ifa_2g4 | 9 | -8.2 | **justo** | 2392.7 | [2359, 2427] | 2.12 | 88.5 | `{"separacion_toma": 3.5, "largo_brazo": 20.0}` |
| ifa | 5800 | A_ifa_58GHz | 1 | -4.3 | **no va** | 6167.3 | None | 3.79 | 86.0 | `{}` |
| jpole | 2441.75 | A_jpole_24GHz | 1 | -1.5 | **no va** | 2390.5 | None | 1.57 | 72.9 | `{}` |
| jpole | 5800 | A_jpole_58GHz | 1 | -0.9 | **no va** | 5397.4 | None | 2.22 | 70.9 | `{}` |
| jpole_koch | 2441.75 | A_jpole_koch_24GHz | 1 | -3.0 | **no va** | 2510.0 | [2486, 2535] | 3.01 | 92.6 | `{}` |
| jpole_koch | 5800 | A_jpole_koch_58GHz | 1 | -1.0 | **no va** | 4391.4 | None | 1.65 | 79.1 | `{}` |
| monopolo_hilbert | 2441.75 | A_monopolo_hilbert_24GHz | 1 | -2.1 | **no va** | 2271.6 | None | -1.36 | 45.9 | `{}` |
| monopolo_koch | 2441.75 | A_monopolo_koch_24GHz | 1 | -16.1 | **va** | 2488.0 | [2323, 2665] | 2.73 | 97.5 | `{}` |
| monopolo_koch | 5800 | A_monopolo_koch_58GHz | 1 | -11.3 | **va** | 5421.5 | [4876, 6028] | 3.18 | 91.2 | `{}` |
| monopolo_meandro | 2441.75 | A_monopolo_meandro_24GHz | 1 | -11.3 | **va** | 2362.4 | [2222, 2512] | 2.81 | 97.0 | `{}` |
| monopolo_meandro | 5800 | A_monopolo_meandro_58GHz | 1 | -8.6 | **justo** | 5367.0 | [5027, 5730] | 2.92 | 89.3 | `{}` |
| monopolo_recto | 2441.75 | A_monopolo_recto_24GHz | 1 | -9.4 | **justo** | 2318.6 | [2181, 2465] | 2.95 | 98.5 | `{}` |
| monopolo_recto | 2441.75 | prueba_herramienta | 3 | -12.5 | **va** | 2508.4 | [2355, 2671] | 2.83 | 98.6 | `{"alto": 22.0}` |
| monopolo_recto | 5800 | A_monopolo_recto_58GHz | 1 | -7.7 | **justo** | 5038.7 | [4601, 5518] | 3.27 | 90.5 | `{}` |
| monopolo_sierpinski | 2441.75 | A_monopolo_sierpinski_24GHz | 1 | -20.0 | **va** | 2451.3 | [2165, 2775] | 2.68 | 97.3 | `{}` |
| monopolo_sierpinski | 5800 | A_monopolo_sierpinski_58GHz | 1 | -14.6 | **va** | 6206.8 | [4744, 8120] | 3.61 | 93.3 | `{}` |
| panel_dipolos | 2441.75 | A_panel_dipolos_24GHz | 1 | -6.9 | **justo** | 2615.7 | [2520, 2715] | 12.24 | 72.8 | `{}` |
| panel_dipolos | 5800 | A_panel_dipolos_58GHz | 1 | -4.6 | **no va** | 4836.3 | [4675, 5003] | 12.09 | 76.7 | `{}` |
| parche_apilado | 5800 | A_parche_apilado_58GHz | 1 | -3.0 | **no va** | 6606.5 | None | 4.86 | 51.4 | `{}` |
| parche_circular | 2441.75 | parche_circular_2g4 | 8 | -5.1 | **no va** | 2458.8 | [2445, 2473] | 2.46 | 43.0 | `{"corte": 0.16, "diagonal": 1}` |
| parche_circular | 5800 | A_parche_circular_58GHz | 1 | -5.6 | **no va** | 5647.9 | [5529, 5769] | 4.19 | 59.1 | `{}` |
| parche_minkowski | 2441.75 | A_parche_minkowski_24GHz | 1 | -1.7 | **no va** | 2497.0 | [2479, 2515] | 0.89 | 30.7 | `{}` |
| parche_minkowski | 5800 | A_parche_minkowski_58GHz | 1 | -8.5 | **justo** | 5830.3 | [5746, 5916] | 3.3 | 48.1 | `{}` |
| parche_ranura | 5800 | A_parche_ranura_58GHz | 1 | -0.6 | **no va** | 6271.5 | None | -8.22 | 6.2 | `{}` |
| parche_rectangular | 2441.75 | A_parche_rectangular_24GHz | 1 | -5.4 | **no va** | 2435.2 | [2416, 2455] | 3.05 | 47.1 | `{}` |
| parche_rectangular | 5800 | A_parche_rectangular_58GHz | 1 | -5.4 | **no va** | 5646.1 | [5533, 5761] | 4.91 | 63.0 | `{}` |
| pifa | 2441.75 | pifa_2g4 | 9 | -9.3 | **justo** | 2665.7 | [2416, 2941] | 2.52 | 92.2 | `{"separacion_toma": 7.0, "largo_brazo": 20.0}` |
| pifa | 5800 | A_pifa_58GHz | 1 | -9.0 | **justo** | 3586.6 | [3480, 3697] | 3.41 | 89.4 | `{}` |
| vivaldi | 5800 | A_vivaldi_58GHz | 1 | -6.5 | **justo** | 6417.7 | None | 2.23 | 80.1 | `{}` |
| yagi_boom | 2441.75 | A_yagi_boom_24GHz | 1 | -3.3 | **no va** | 2461.0 | None | 3.37 | 61.4 | `{}` |
| yagi_boom | 5800 | A_yagi_boom_58GHz | 1 | -4.8 | **no va** | 5991.1 | None | 5.37 | 70.4 | `{}` |
| yagi_koch | 2441.75 | A_yagi_koch_24GHz | 1 | -3.1 | **no va** | 2476.1 | None | 2.84 | 53.5 | `{}` |
