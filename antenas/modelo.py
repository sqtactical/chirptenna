"""Representación común de una antena generada."""
from dataclasses import dataclass, field

from shapely.geometry import Polygon
from shapely.ops import unary_union


@dataclass
class Antena:
    """Antena impresa lista para exportar o simular. Coordenadas en mm, y hacia arriba.

    capas: geometrías de cobre por capa ('F.Cu' cara superior, 'B.Cu' inferior).
    radiador: solo la parte radiante (para la huella de KiCad), en F.Cu.
    contorno: polígono del borde de la placa de prueba.
    puerto: dónde se alimenta: punto en el borde de la placa (para el SMA), dirección
            hacia dentro y punto de alimentación del radiador.
    """
    tipo: str
    parametros: dict
    capas: dict
    radiador: Polygon
    contorno: Polygon
    puerto: dict
    zona_libre: Polygon = None        # región sin cobre alrededor del radiador
    info: dict = field(default_factory=dict)
    ajuste: dict = None               # componentes, marcas y tramos para ajustar (ver ajuste.py)
    vias: list = field(default_factory=list)   # [(x, y)] vías que unen F.Cu y B.Cu (antena, no las del SMA)
    taladros: list = field(default_factory=list)   # [(x, y, diámetro)] taladros sin metalizar (tornillos)
    # Reflector separado por aire, debajo de la cara inferior (panel): {'contorno': polígono,
    # 'separacion_mm': de la cara inferior al reflector, 'hilos': [(x, y)] conductores verticales del
    # reflector a la cara inferior (malla del coaxial), 'taladros': [(x, y, diámetro)]}
    reflector: dict = None

    def cobre(self, capa):
        g = self.capas.get(capa)
        return unary_union(g) if isinstance(g, (list, tuple)) else g
