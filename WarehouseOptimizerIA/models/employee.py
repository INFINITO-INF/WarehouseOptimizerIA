# models/employee.py
from typing import List, Tuple
from models.package import Package
from config.constants import (
    WEIGHT_PENALTY_FACTOR,
    VOLUME_PENALTY_FACTOR,
    MIN_SPEED_RATIO,
    LARGE_LOAD_VOLUME_THRESHOLD
)

class Employee:
    def __init__(
        self,
        emp_id: int,
        name: str,
        base_speed: float,
        origin: Tuple[int, int],
        destination: Tuple[int, int],
        waypoints: List[Tuple[int, int]] = None,
        base_radius_m: float = 0.35
    ):
        self.emp_id = emp_id
        self.name = name
        self.base_speed = base_speed
        self.origin = origin
        self.destination = destination
        self.waypoints: List[Tuple[int, int]] = list(waypoints) if waypoints else []
        self.base_radius_m = base_radius_m
        self.packages: List[Package] = []
        
        # Resultados tras calcular ruta
        self.path: List[Tuple[int, int]] = []
        self.timestamps: List[float] = []

    def add_package(self, package: Package) -> None:
        self.packages.append(package)

    @property
    def full_itinerary(self) -> List[Tuple[int, int]]:
        """Retorna la secuencia completa: [Origen, Parada 1, Parada 2, ..., Destino]."""
        return [self.origin] + self.waypoints + [self.destination]

    @property
    def total_weight(self) -> float:
        return round(sum(p.weight for p in self.packages), 2)

    @property
    def total_volume(self) -> float:
        return round(sum(p.volume for p in self.packages), 4)

    @property
    def effective_speed(self) -> float:
        penalty = (self.total_weight * WEIGHT_PENALTY_FACTOR) + (self.total_volume * VOLUME_PENALTY_FACTOR)
        multiplier = max(MIN_SPEED_RATIO, 1.0 - penalty)
        return round(self.base_speed * multiplier, 3)

    @property
    def effective_radius_m(self) -> float:
        extra_radius = sum(p.footprint_area for p in self.packages) * 0.25
        return round(self.base_radius_m + extra_radius, 3)

    @property
    def clearance_cells(self) -> int:
        return 1 if self.total_volume >= LARGE_LOAD_VOLUME_THRESHOLD else 0