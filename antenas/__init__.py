"""Generador de antenas (fractales) impresas en PCB.

Módulos:
  geometria    – curvas fractales (sistemas L, Hilbert, Sierpinski) y utilidades de polígonos
  materiales   – sustratos (FR4 y Rogers de JLC) y síntesis de microstrip
  modelo       – clase Antena: cobre por capas, contorno, puerto y metadatos
  tipos        – catálogo de antenas y su dimensionado orientativo
  fabricacion  – comprobaciones de reglas del fabricante (pista/hueco mínimos)
  exportar     – huella y placa de KiCad, Gerber (kicad-cli), DXF y vista previa
"""
