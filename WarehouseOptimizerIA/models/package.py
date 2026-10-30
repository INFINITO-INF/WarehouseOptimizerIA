# models/package.py
from dataclasses import dataclass

@dataclass
class Package:
    name: str
    width: float   # Metros (X)
    length: float  # Metros (Y)
    height: float  # Metros (Z)
    weight: float  # Kilogramos (kg)

    @property
    def volume(self) -> float:
        """Retorna el volumen del paquete en metros cúbicos (m³)."""
        return round(self.width * self.length * self.height, 4)

    @property
    def footprint_area(self) -> float:
        """Retorna el área de base que ocupa el paquete en m²."""
        return round(self.width * self.length, 4)
