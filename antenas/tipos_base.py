"""Tipos básicos compartidos (para evitar importaciones circulares)."""
from dataclasses import dataclass


@dataclass
class Parametro:
    nombre: str
    etiqueta: str
    defecto: float
    minimo: float
    maximo: float
    paso: float = 0.1
    entero: bool = False
    ayuda: str = ''
    opciones: dict = None             # si se da, es un selector {valor: texto}
