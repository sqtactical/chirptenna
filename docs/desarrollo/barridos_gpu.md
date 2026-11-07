# Barridos en GPU: qué va y qué no (07-11-2026)

Generado por `python herramientas/resumen_barridos.py` a partir de `salidas/_barridos/*/resumen.json`.
Solo simulación (openEMS en GPU, FR4 de 1,6 mm con εr 4,5): sin medir ninguna placa. La ganancia y la eficiencia en GPU salen algo altas. En las Yagi se prefiere la mejor configuración cuyo haz sale hacia los directores («haz atrás» = solo adapta radiando al revés). «Peor S11» es el peor valor en toda la banda de uso; va ≤ −10 dB, justo hasta −6 dB. Etiquetas: `A_` = tamaño base de `dimensionar`; `B_` = barrido de parámetros; sin prefijo = campaña de los tipos nuevos.

| Tipo | f (MHz) | Barrido | Configs | Peor S11 (dB) | Veredicto | f res. (MHz) | Banda −10 dB | G (dBi) | η (%) | Mejor |
|---|---|---|---|---|---|---|---|---|---|---|
| array_parches | 5800 | A_array_parches_58GHz | 1 | -4.8 | **no va** | 7147.0 | [7057, 7238] | 5.46 | 41.6 | `{}` |
| colineal_coco | 2441.75 | A_colineal_coco_24GHz | 1 | -2.2 | **no va** | 2604.1 | [2557, 2652] | 1.4 | 45.0 | `{}` |
| colineal_coco | 5800 | A_colineal_coco_58GHz | 1 | -1.7 | **no va** | 6902.6 | [6771, 7037] | 0.35 | 44.5 | `{}` |
| colineal_dipolos | 2441.75 | C_colineal_dipolos_24GHz | 5 | -10.8 | **va** | 2207.5 | [1934, 2520] | 2.64 | 56.4 | `{"factor_linea": 1.1, "elementos": 4}` |
| colineal_dipolos | 2441.75 | X_colineal_dipolos_FR4_24GHz | 2 | -10.9 | **va** | 2217.1 | [1861, 2642] | 3.6 | 42.0 | `{"elementos": 6}` |
| colineal_dipolos | 2441.75 | X_colineal_dipolos_RO4350B_24GHz | 2 | -6.3 | **justo** | 1963.0 | [1903, 2025] | 7.16 | 87.3 | `{"elementos": 6}` |
| colineal_dipolos | 2441.75 | colineal_dipolos_2g4 | 9 | -15.9 | **va** | 2455.8 | [2266, 2662] | 4.41 | 68.6 | `{"factor_linea": 0.9, "largo_brazo": 22.0}` |
| colineal_dipolos | 5800 | A_colineal_dipolos_58GHz | 1 | -8.7 | **justo** | 5029.9 | [4949, 5112] | 1.75 | 37.0 | `{}` |
| colineal_franklin | 2441.75 | A_colineal_franklin_24GHz | 1 | -6.9 | **justo** | 2790.4 | [2738, 2844] | 2.34 | 80.6 | `{}` |
| colineal_franklin | 2441.75 | C_colineal_franklin_24GHz | 6 | -7.7 | **justo** | 2442.5 | [2425, 2460] | 3.19 | 81.9 | `{"factor_horquilla": 1.0, "elementos": 1}` |
| colineal_franklin | 5800 | A_colineal_franklin_58GHz | 1 | -2.5 | **no va** | 5242.4 | [5154, 5332] | 1.86 | 56.9 | `{}` |
| dipolo | 866.5 | C_dipolo_868 | 1 | -14.1 | **va** | 861.9 | [824, 901] | 2.17 | 97.5 | `{}` |
| dipolo | 915 | C_dipolo_915ISM | 1 | -14.0 | **va** | 911.6 | [872, 953] | 2.03 | 95.5 | `{}` |
| dipolo | 1270 | A_dipolo_12GHz | 1 | -9.0 | **justo** | 1225.8 | [1168, 1287] | 2.1 | 96.2 | `{}` |
| dipolo | 1270 | C_dipolo_12GHz | 1 | -7.1 | **justo** | 1199.6 | [1143, 1259] | 2.1 | 95.6 | `{}` |
| dipolo | 1575.42 | C_dipolo_GPSL1 | 1 | -12.5 | **va** | 1539.3 | [1463, 1620] | 2.42 | 98.5 | `{}` |
| dipolo | 1621.25 | C_dipolo_Iridium | 1 | -14.2 | **va** | 1599.1 | [1517, 1685] | 3.01 | 104.9 | `{}` |
| dipolo | 2441.75 | A_dipolo_24GHz | 1 | -11.7 | **va** | 2558.8 | [2370, 2762] | 2.48 | 97.9 | `{}` |
| dipolo | 2441.75 | C_dipolo_24GHz | 4 | -13.6 | **va** | 2445.7 | [2294, 2608] | 2.46 | 97.3 | `{"ancho_pista": 1.5, "iteracion": 0}` |
| dipolo | 2441.75 | X_dipolo_brazos_anchos_24GHz | 4 | -13.6 | **va** | 2445.7 | [2294, 2608] | 2.46 | 97.3 | `{"ancho_pista": 1.5}` |
| dipolo | 5800 | A_dipolo_58GHz | 1 | -17.7 | **va** | 5867.4 | [5429, 6341] | 2.53 | 87.5 | `{}` |
| dipolo | 5800 | C_dipolo_58GHz | 1 | -13.5 | **va** | 5999.2 | [5560, 6473] | 2.34 | 86.7 | `{}` |
| dipolo_bowtie | 866.5 | C_dipolo_bowtie_868 | 1 | -28.3 | **va** | 872.1 | [793, 959] | 1.77 | 95.6 | `{}` |
| dipolo_bowtie | 915 | C_dipolo_bowtie_915ISM | 1 | -18.8 | **va** | 910.3 | [828, 1000] | 2.29 | 98.9 | `{}` |
| dipolo_bowtie | 1270 | A_dipolo_bowtie_12GHz | 1 | -12.6 | **va** | 1221.9 | [1109, 1346] | 2.06 | 96.7 | `{}` |
| dipolo_bowtie | 1270 | C_dipolo_bowtie_12GHz | 1 | -15.8 | **va** | 1255.9 | [1139, 1385] | 1.69 | 94.2 | `{}` |
| dipolo_bowtie | 1575.42 | C_dipolo_bowtie_GPSL1 | 1 | -22.0 | **va** | 1577.5 | [1414, 1760] | 2.12 | 97.5 | `{}` |
| dipolo_bowtie | 1621.25 | C_dipolo_bowtie_Iridium | 1 | -21.2 | **va** | 1610.3 | [1450, 1788] | 2.53 | 102.9 | `{}` |
| dipolo_bowtie | 2441.75 | A_dipolo_bowtie_24GHz | 1 | -18.3 | **va** | 2591.8 | [2185, 3075] | 2.47 | 98.7 | `{}` |
| dipolo_bowtie | 2441.75 | C_dipolo_bowtie_24GHz | 5 | -22.5 | **va** | 2593.8 | [2222, 3028] | 2.1 | 96.0 | `{"apertura": 55.0, "forma": 1}` |
| dipolo_bowtie | 2441.75 | F_dipolo_flecha_24GHz | 3 | -3.3 | **no va** | 2494.0 | None | 0.82 | 69.8 | `{"forma": 3, "alimentacion": 0, "iteracion_s": 3}` |
| dipolo_bowtie | 5800 | A_dipolo_bowtie_58GHz | 1 | -8.3 | **justo** | 7153.9 | [6303, 8120] | 2.7 | 90.2 | `{}` |
| dipolo_bowtie | 5800 | C_dipolo_bowtie_58GHz | 1 | -7.6 | **justo** | 6211.9 | [5877, 6566] | 3.07 | 83.3 | `{}` |
| dipolo_sleeve | 866.5 | C_dipolo_sleeve_868 | 5 | -18.4 | **va** | 867.7 | [811, 928] | 2.3 | 96.6 | `{"largo_masa": 67.63, "ancho_pista": 2.82}` |
| dipolo_sleeve | 915 | C_dipolo_sleeve_915ISM | 1 | -16.9 | **va** | 920.0 | [861, 983] | 2.01 | 94.1 | `{}` |
| dipolo_sleeve | 1270 | A_dipolo_sleeve_12GHz | 1 | -14.4 | **va** | 1264.2 | [1183, 1351] | 2.68 | 99.2 | `{}` |
| dipolo_sleeve | 1270 | C_dipolo_sleeve_12GHz | 1 | -13.1 | **va** | 1251.6 | [1172, 1337] | 2.64 | 98.8 | `{}` |
| dipolo_sleeve | 1575.42 | C_dipolo_sleeve_GPSL1 | 1 | -15.3 | **va** | 1555.4 | [1458, 1659] | 2.46 | 96.4 | `{}` |
| dipolo_sleeve | 1621.25 | C_dipolo_sleeve_Iridium | 1 | -14.8 | **va** | 1589.3 | [1490, 1695] | 3.16 | 104.0 | `{}` |
| dipolo_sleeve | 2441.75 | C_dipolo_sleeve_24GHz | 5 | -13.6 | **va** | 2418.4 | [2274, 2572] | 2.88 | 98.1 | `{"largo_masa": 24.0, "ancho_pista": 1.0}` |
| dipolo_sleeve | 2441.75 | sleeve_2g4 | 9 | -17.1 | **va** | 2441.1 | [2294, 2598] | 2.78 | 99.0 | `{"alto": 23.6, "largo_masa": 20.0}` |
| dipolo_sleeve | 5800 | A_dipolo_sleeve_58GHz | 1 | -6.2 | **justo** | 5113.8 | [4783, 5467] | 3.08 | 91.0 | `{}` |
| dipolo_sleeve | 5800 | C_dipolo_sleeve_58GHz | 5 | -13.1 | **va** | 5652.0 | [5286, 6044] | 3.07 | 91.8 | `{"largo_masa": 10.1, "ancho_pista": 0.252}` |
| ifa | 866.5 | C_ifa_868 | 8 | -17.0 | **va** | 864.9 | [837, 894] | 2.02 | 91.0 | `{"separacion_toma": 15.776, "altura": 13.811, "ancho_pista": 1.692}` |
| ifa | 1270 | A_ifa_12GHz | 1 | -2.0 | **no va** | 1215.2 | None | -0.07 | 62.8 | `{}` |
| ifa | 2441.75 | C_ifa_24GHz | 7 | -11.3 | **va** | 2391.3 | [2285, 2502] | 2.24 | 90.4 | `{"separacion_toma": 3.5, "altura": 7.0, "ancho_pista": 1.0}` |
| ifa | 2441.75 | ifa_2g4 | 9 | -8.2 | **justo** | 2392.7 | [2359, 2427] | 2.12 | 88.5 | `{"separacion_toma": 3.5, "largo_brazo": 20.0}` |
| ifa | 5800 | A_ifa_58GHz | 1 | -4.3 | **no va** | 6167.3 | None | 3.79 | 86.0 | `{}` |
| ifa | 5800 | C_ifa_58GHz | 7 | -11.0 | **va** | 5761.8 | [5479, 6059] | 2.58 | 86.3 | `{"separacion_toma": 1.47, "altura": 2.95, "ancho_pista": 0.42}` |
| jpole | 1270 | A_jpole_12GHz | 1 | -4.0 | **no va** | 1333.6 | None | 2.07 | 82.0 | `{}` |
| jpole | 2441.75 | A_jpole_24GHz | 1 | -1.5 | **no va** | 2390.5 | None | 1.57 | 72.9 | `{}` |
| jpole | 2441.75 | C_jpole_24GHz | 3 | -2.8 | **no va** | 2546.0 | None | 1.58 | 74.0 | `{"toma": 0.26, "hueco": 1.0}` |
| jpole | 5800 | A_jpole_58GHz | 1 | -0.9 | **no va** | 5397.4 | None | 2.22 | 70.9 | `{}` |
| jpole_koch | 866.5 | C_jpole_koch_868 | 5 | -19.8 | **va** | 869.4 | [847, 892] | 2.96 | 94.4 | `{"toma": 0.268, "hueco": 4.512}` |
| jpole_koch | 1270 | A_jpole_koch_12GHz | 1 | -0.8 | **no va** | 1483.7 | [1472, 1496] | 2.41 | 70.2 | `{}` |
| jpole_koch | 2441.75 | A_jpole_koch_24GHz | 1 | -3.0 | **no va** | 2510.0 | [2486, 2535] | 3.01 | 92.6 | `{}` |
| jpole_koch | 2441.75 | C_jpole_koch_24GHz | 5 | -9.2 | **justo** | 2455.9 | [2406, 2507] | 2.71 | 89.3 | `{"toma": 0.26, "hueco": 1.0}` |
| jpole_koch | 5800 | A_jpole_koch_58GHz | 1 | -1.0 | **no va** | 4391.4 | None | 1.65 | 79.1 | `{}` |
| jpole_koch | 5800 | Y_jpole_koch_58GHz | 1 | -1.8 | **no va** | 6793.3 | [6616, 6975] | -0.22 | 45.9 | `{}` |
| monopolo_flecha | 2441.75 | C_monopolo_flecha_24GHz | 6 | -6.8 | **justo** | 2388.6 | None | 1.29 | 81.8 | `{"iteracion": 2, "ancho_pista": 0.265}` |
| monopolo_flecha | 2441.75 | H_flecha_armonicos_24GHz | 5 | -5.3 | **no va** | 1559.1 | [1483, 1639] | 2.7 | 69.8 | `{"alto": 38.82}` |
| monopolo_hilbert | 2441.75 | A_monopolo_hilbert_24GHz | 1 | -2.1 | **no va** | 2271.6 | None | -1.36 | 45.9 | `{}` |
| monopolo_hilbert | 2441.75 | H_hilbert_armonicos_24GHz | 3 | -2.8 | **no va** | 3088.8 | [2989, 3192] | 1.79 | 70.1 | `{"lado": 10.36}` |
| monopolo_koch | 866.5 | C_monopolo_koch_868 | 1 | -22.7 | **va** | 869.9 | [820, 923] | 2.54 | 99.8 | `{}` |
| monopolo_koch | 915 | C_monopolo_koch_915ISM | 1 | -19.7 | **va** | 917.4 | [865, 973] | 2.62 | 100.4 | `{}` |
| monopolo_koch | 1270 | A_monopolo_koch_12GHz | 1 | -11.6 | **va** | 1307.6 | [1228, 1393] | 2.58 | 99.1 | `{}` |
| monopolo_koch | 1270 | C_monopolo_koch_12GHz | 1 | -15.8 | **va** | 1281.8 | [1202, 1367] | 2.56 | 98.9 | `{}` |
| monopolo_koch | 1575.42 | C_monopolo_koch_GPSL1 | 1 | -24.4 | **va** | 1578.7 | [1484, 1679] | 2.38 | 96.7 | `{}` |
| monopolo_koch | 1621.25 | C_monopolo_koch_Iridium | 1 | -26.0 | **va** | 1633.7 | [1534, 1740] | 3.33 | 106.6 | `{}` |
| monopolo_koch | 2441.75 | A_monopolo_koch_24GHz | 1 | -16.1 | **va** | 2488.0 | [2323, 2665] | 2.73 | 97.5 | `{}` |
| monopolo_koch | 2441.75 | C_monopolo_koch_24GHz | 5 | -19.1 | **va** | 2442.5 | [2281, 2616] | 2.53 | 95.5 | `{"iteracion": 2, "ancho_pista": 1.0}` |
| monopolo_koch | 5800 | A_monopolo_koch_58GHz | 1 | -11.3 | **va** | 5421.5 | [4876, 6028] | 3.18 | 91.2 | `{}` |
| monopolo_koch | 5800 | C_monopolo_koch_58GHz | 1 | -19.4 | **va** | 5852.9 | [5139, 6666] | 3.33 | 91.6 | `{}` |
| monopolo_meandro | 866.5 | C_monopolo_meandro_868 | 1 | -21.0 | **va** | 864.6 | [819, 913] | 2.24 | 96.0 | `{}` |
| monopolo_meandro | 915 | C_monopolo_meandro_915ISM | 1 | -19.0 | **va** | 916.4 | [867, 968] | 2.22 | 95.7 | `{}` |
| monopolo_meandro | 1270 | A_monopolo_meandro_12GHz | 1 | -7.0 | **justo** | 1342.9 | [1272, 1418] | 1.82 | 90.9 | `{}` |
| monopolo_meandro | 1270 | C_monopolo_meandro_12GHz | 1 | -15.6 | **va** | 1269.4 | [1203, 1339] | 1.86 | 91.8 | `{}` |
| monopolo_meandro | 1575.42 | C_monopolo_meandro_GPSL1 | 1 | -20.1 | **va** | 1594.6 | [1502, 1693] | 2.62 | 98.0 | `{}` |
| monopolo_meandro | 1621.25 | C_monopolo_meandro_Iridium | 1 | -23.9 | **va** | 1617.4 | [1526, 1714] | 2.73 | 99.4 | `{}` |
| monopolo_meandro | 2441.75 | A_monopolo_meandro_24GHz | 1 | -11.3 | **va** | 2362.4 | [2222, 2512] | 2.81 | 97.0 | `{}` |
| monopolo_meandro | 2441.75 | C_monopolo_meandro_24GHz | 5 | -9.1 | **justo** | 2612.3 | [2419, 2821] | 2.47 | 93.0 | `{"ancho_meandro": 4.72, "vueltas": 3}` |
| monopolo_meandro | 5800 | A_monopolo_meandro_58GHz | 1 | -8.6 | **justo** | 5367.0 | [5027, 5730] | 2.92 | 89.3 | `{}` |
| monopolo_meandro | 5800 | C_monopolo_meandro_58GHz | 1 | -15.4 | **va** | 5988.6 | [5456, 6573] | 3.04 | 88.2 | `{}` |
| monopolo_recto | 866.5 | C_monopolo_recto_868 | 1 | -11.2 | **va** | 879.3 | [851, 909] | 2.62 | 100.3 | `{}` |
| monopolo_recto | 915 | C_monopolo_recto_915ISM | 1 | -12.0 | **va** | 914.4 | [882, 948] | 2.31 | 97.1 | `{}` |
| monopolo_recto | 1270 | A_monopolo_recto_12GHz | 1 | -7.3 | **justo** | 1205.8 | [1154, 1260] | 2.38 | 96.4 | `{}` |
| monopolo_recto | 1270 | C_monopolo_recto_12GHz | 1 | -12.4 | **va** | 1274.2 | [1218, 1333] | 2.29 | 96.5 | `{}` |
| monopolo_recto | 1575.42 | C_monopolo_recto_GPSL1 | 1 | -11.4 | **va** | 1536.5 | [1466, 1610] | 2.81 | 99.9 | `{}` |
| monopolo_recto | 1621.25 | C_monopolo_recto_Iridium | 1 | -11.5 | **va** | 1574.0 | [1500, 1652] | 3.51 | 107.9 | `{}` |
| monopolo_recto | 2441.75 | A_monopolo_recto_24GHz | 1 | -9.4 | **justo** | 2318.6 | [2181, 2465] | 2.95 | 98.5 | `{}` |
| monopolo_recto | 2441.75 | C_monopolo_recto_24GHz | 3 | -15.1 | **va** | 2433.8 | [2287, 2590] | 2.82 | 98.3 | `{"ancho_pista": 1.0}` |
| monopolo_recto | 2441.75 | prueba_herramienta | 3 | -12.5 | **va** | 2508.4 | [2355, 2671] | 2.83 | 98.6 | `{"alto": 22.0}` |
| monopolo_recto | 5800 | A_monopolo_recto_58GHz | 1 | -7.7 | **justo** | 5038.7 | [4601, 5518] | 3.27 | 90.5 | `{}` |
| monopolo_recto | 5800 | C_monopolo_recto_58GHz | 1 | -14.1 | **va** | 5730.8 | [5077, 6469] | 3.5 | 92.0 | `{}` |
| monopolo_sierpinski | 866.5 | C_monopolo_sierpinski_868 | 1 | -19.4 | **va** | 859.6 | [768, 962] | 2.38 | 97.8 | `{}` |
| monopolo_sierpinski | 915 | C_monopolo_sierpinski_915ISM | 1 | -18.3 | **va** | 912.1 | [814, 1022] | 2.12 | 95.9 | `{}` |
| monopolo_sierpinski | 1270 | A_monopolo_sierpinski_12GHz | 1 | -19.0 | **va** | 1279.4 | [1138, 1438] | 2.63 | 99.2 | `{}` |
| monopolo_sierpinski | 1270 | C_monopolo_sierpinski_12GHz | 1 | -19.0 | **va** | 1279.4 | [1138, 1438] | 2.63 | 99.2 | `{}` |
| monopolo_sierpinski | 1575.42 | C_monopolo_sierpinski_GPSL1 | 1 | -23.2 | **va** | 1583.3 | [1407, 1781] | 2.45 | 97.1 | `{}` |
| monopolo_sierpinski | 1621.25 | C_monopolo_sierpinski_Iridium | 1 | -29.6 | **va** | 1647.0 | [1459, 1859] | 3.15 | 104.5 | `{}` |
| monopolo_sierpinski | 2441.75 | A_monopolo_sierpinski_24GHz | 1 | -20.0 | **va** | 2451.3 | [2165, 2775] | 2.68 | 97.3 | `{}` |
| monopolo_sierpinski | 2441.75 | C_monopolo_sierpinski_24GHz | 5 | -20.0 | **va** | 2451.3 | [2165, 2775] | 2.68 | 97.3 | `{"iteracion": 2, "apertura": 60.0}` |
| monopolo_sierpinski | 5800 | A_monopolo_sierpinski_58GHz | 1 | -14.6 | **va** | 6206.8 | [4744, 8120] | 3.61 | 93.3 | `{}` |
| monopolo_sierpinski | 5800 | C_monopolo_sierpinski_58GHz | 1 | -12.2 | **va** | 6045.4 | [4501, 8120] | 3.51 | 92.6 | `{}` |
| panel_dipolos | 2441.75 | A_panel_dipolos_24GHz | 1 | -6.9 | **justo** | 2615.7 | [2520, 2715] | 12.24 | 72.8 | `{}` |
| panel_dipolos | 2441.75 | C_panel_dipolos_24GHz | 3 | -7.6 | **justo** | 2594.6 | [2499, 2694] | 12.41 | 73.0 | `{"separacion_reflector": 0.224}` |
| panel_dipolos | 2441.75 | X_panel_sin_reflector_24GHz | 4 | -11.4 | **va** | 2479.6 | [2364, 2601] | 12.97 | 80.0 | `{"elemento": 1, "tamano": 2, "reflector": 1}` |
| panel_dipolos | 2441.75 | Y_panel_largo_24GHz | 3 | -9.1 | **justo** | 2872.7 | [2414, 3418] | 12.56 | 75.0 | `{"largo_brazo": 20.671}` |
| panel_dipolos | 5800 | A_panel_dipolos_58GHz | 1 | -4.6 | **no va** | 4836.3 | [4675, 5003] | 12.09 | 76.7 | `{}` |
| panel_dipolos | 5800 | C_panel_dipolos_58GHz | 3 | -5.4 | **no va** | 4804.1 | [4663, 4949] | 12.64 | 77.4 | `{"separacion_reflector": 0.2}` |
| panel_dipolos | 5800 | Y_panel_largo_58GHz | 3 | -4.6 | **no va** | 4836.3 | [4675, 5003] | 12.09 | 76.7 | `{"largo_brazo": 8.06}` |
| parche_apilado | 2441.75 | parche_apilado_2g4 | 9 | -2.8 | **no va** | 2901.6 | None | 1.79 | 34.9 | `{"parasito_hueco": 0.6, "parasito_factor": 0.96}` |
| parche_apilado | 5800 | A_parche_apilado_58GHz | 1 | -3.0 | **no va** | 6606.5 | None | 4.86 | 51.4 | `{}` |
| parche_circular | 2441.75 | C_parche_circular_24GHz | 3 | -6.0 | **justo** | 2448.2 | [2434, 2463] | 2.44 | 43.0 | `{"corte": 0.15}` |
| parche_circular | 2441.75 | parche_circular_2g4 | 8 | -5.1 | **no va** | 2458.8 | [2445, 2473] | 2.46 | 43.0 | `{"corte": 0.16, "diagonal": 1}` |
| parche_circular | 5800 | A_parche_circular_58GHz | 1 | -5.6 | **no va** | 5647.9 | [5529, 5769] | 4.19 | 59.1 | `{}` |
| parche_minkowski | 2441.75 | A_parche_minkowski_24GHz | 1 | -1.7 | **no va** | 2497.0 | [2479, 2515] | 0.89 | 30.7 | `{}` |
| parche_minkowski | 2441.75 | C_parche_minkowski_24GHz | 4 | -3.9 | **no va** | 2431.9 | [2414, 2450] | 1.1 | 33.1 | `{"iteracion": 1, "profundidad": 0.5}` |
| parche_minkowski | 5800 | A_parche_minkowski_58GHz | 1 | -8.5 | **justo** | 5830.3 | [5746, 5916] | 3.3 | 48.1 | `{}` |
| parche_minkowski | 5800 | C_parche_minkowski_58GHz | 4 | -8.5 | **justo** | 5830.3 | [5746, 5916] | 3.3 | 48.1 | `{"iteracion": 1, "profundidad": 0.5}` |
| parche_ranura | 2441.75 | parche_ranura_2g4 | 9 | -0.5 | **no va** | 2826.8 | None | -8.07 | 4.3 | `{"ranura_ancho": 0.4, "ranura_largo": 0.3}` |
| parche_ranura | 5800 | A_parche_ranura_58GHz | 1 | -0.6 | **no va** | 6271.5 | None | -8.22 | 6.2 | `{}` |
| parche_rectangular | 1270 | A_parche_rectangular_12GHz | 1 | -1.4 | **no va** | 1610.8 | None | 1.53 | 33.5 | `{}` |
| parche_rectangular | 2441.75 | A_parche_rectangular_24GHz | 1 | -5.4 | **no va** | 2435.2 | [2416, 2455] | 3.05 | 47.1 | `{}` |
| parche_rectangular | 2441.75 | C_parche_rectangular_24GHz | 4 | -5.4 | **no va** | 2435.2 | [2416, 2455] | 3.05 | 47.1 | `{"ancho": 35.56, "alimentacion": 0}` |
| parche_rectangular | 2441.75 | X_parche_RO4350B_24GHz | 1 | -2.5 | **no va** | 2418.9 | [2401, 2437] | 6.37 | 89.1 | `{}` |
| parche_rectangular | 2441.75 | X_parche_margen_masa_24GHz | 3 | -5.4 | **no va** | 2435.2 | [2416, 2455] | 3.05 | 47.1 | `{"masa": 0, "margen_masa": 7.5}` |
| parche_rectangular | 5800 | A_parche_rectangular_58GHz | 1 | -5.4 | **no va** | 5646.1 | [5533, 5761] | 4.91 | 63.0 | `{}` |
| parche_rectangular | 5800 | C_parche_rectangular_58GHz | 4 | -12.0 | **va** | 5793.2 | [5688, 5901] | 5.37 | 65.7 | `{"ancho": 17.964, "alimentacion": 0}` |
| pifa | 866.5 | C_pifa_868 | 7 | -12.2 | **va** | 827.3 | [761, 899] | 2.63 | 96.3 | `{"separacion_toma": 19.73, "altura": 16.91, "ancho_pista": 19.73}` |
| pifa | 1270 | A_pifa_12GHz | 1 | -6.1 | **justo** | 1324.9 | None | 1.37 | 82.0 | `{}` |
| pifa | 2441.75 | C_pifa_24GHz | 7 | -22.1 | **va** | 2547.9 | [2237, 2902] | 2.72 | 93.8 | `{"separacion_toma": 7.0, "altura": 6.0, "ancho_pista": 7.0}` |
| pifa | 2441.75 | pifa_2g4 | 9 | -9.3 | **justo** | 2665.7 | [2416, 2941] | 2.52 | 92.2 | `{"separacion_toma": 7.0, "largo_brazo": 20.0}` |
| pifa | 5800 | A_pifa_58GHz | 1 | -9.0 | **justo** | 3586.6 | [3480, 3697] | 3.41 | 89.4 | `{}` |
| pifa | 5800 | C_pifa_58GHz | 7 | -13.9 | **va** | 5588.2 | [4768, 6550] | 2.72 | 88.6 | `{"separacion_toma": 2.95, "altura": 3.542, "ancho_pista": 2.95}` |
| vivaldi | 2441.75 | C_vivaldi_24GHz | 5 | -17.7 | **va** | 2544.9 | [2230, 2904] | 2.73 | 88.0 | `{"largo_aleta": 77.941, "tasa": 3.0}` |
| vivaldi | 2441.75 | vivaldi_2g4 | 9 | -12.2 | **va** | 2765.1 | [2237, 3418] | 2.28 | 92.3 | `{"ancho_apertura": 56.0, "largo_aleta": 45.0}` |
| vivaldi | 5800 | A_vivaldi_58GHz | 1 | -6.5 | **justo** | 6417.7 | None | 2.23 | 80.1 | `{}` |
| vivaldi | 5800 | C_vivaldi_58GHz | 5 | -18.3 | **va** | 6059.1 | [5116, 7177] | 2.49 | 83.6 | `{"largo_aleta": 30.753, "tasa": 3.0}` |
| yagi_boom | 866.5 | C_yagi_boom_868 | 6 | -15.3 | **va** | 865.8 | [841, 892] | 9.36 | 87.0 | `{"directores": 3, "separacion_reflector": 0.204}` |
| yagi_boom | 2441.75 | A_yagi_boom_24GHz | 1 | -3.3 | **no va** | 2461.0 | None | 3.37 | 61.4 | `{}` |
| yagi_boom | 2441.75 | C_yagi_boom_24GHz | 5 | -13.7 | **va** | 2471.0 | [2362, 2585] | 7.16 | 79.0 | `{"directores": 2, "separacion_reflector": 0.4}` |
| yagi_boom | 2441.75 | X_yagi_koch_it1_24GHz | 7 | -8.6 | **justo** | 2508.4 | [2442, 2577] | 4.81 | 77.6 | `{"directores": 2, "iteracion": 1, "factor_director": 0.81, "factor_reflector": 1.05}` |
| yagi_boom | 5800 | A_yagi_boom_58GHz | 1 | -4.8 | **no va (haz atrás)** | 5991.1 | None | 5.37 | 70.4 | `{}` |
| yagi_boom | 5800 | C_yagi_boom_58GHz | 5 | -18.8 | **va (haz atrás)** | 6308.4 | [5560, 7157] | 6.82 | 75.4 | `{"directores": 2, "separacion_reflector": 0.39}` |
| yagi_koch | 2441.75 | A_yagi_koch_24GHz | 1 | -3.1 | **no va (haz atrás)** | 2476.1 | None | 2.84 | 53.5 | `{}` |
