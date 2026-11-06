"""Generador de antenas (fractales) impresas en PCB.

Chirptenna · Copyright (C) 2026 sqtactical · Software libre bajo la GNU AGPL v3.0 (ver LICENSE).

Módulos:
  geometria    – curvas fractales (sistemas L, Hilbert, Sierpinski) y utilidades de polígonos
  materiales   – sustratos (FR4 y Rogers de JLC) y síntesis de microstrip
  modelo       – clase Antena: cobre por capas, contorno, puerto y metadatos
  tipos        – catálogo de antenas y su dimensionado orientativo
  fabricacion  – comprobaciones de reglas del fabricante (pista/hueco mínimos)
  exportar     – huella y placa de KiCad, Gerber (kicad-cli), DXF y vista previa
"""

# Versión del programa (alpha: validado solo en simulación). Subirla en cada release de GitHub.
__version__ = '0.2.0-alpha'
