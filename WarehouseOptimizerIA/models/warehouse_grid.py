# models/warehouse_grid.py
import numpy as np
from typing import Tuple, List
from config.constants import (
    CELL_FREE,
    CELL_OBSTACLE_IMAGE,
    CELL_OBSTACLE_EXTRA,
    CELL_ORIGIN,
    CELL_DESTINATION,
    CELL_WAYPOINT
)

class WarehouseGrid:
    def __init__(self, real_width_m: float, real_length_m: float, cell_size_m: float = 1.0):
        self.real_width_m = real_width_m
        self.real_length_m = real_length_m
        self.cell_size_m = cell_size_m

        self.cols = max(1, int(round(real_width_m / cell_size_m)))
        self.rows = max(1, int(round(real_length_m / cell_size_m)))

        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.origins: List[Tuple[int, int]] = []
        self.destinations: List[Tuple[int, int]] = []
        self.waypoints: List[Tuple[int, int]] = []

    def load_from_binary_matrix(self, binary_matrix: np.ndarray) -> None:
        if binary_matrix.shape != (self.rows, self.cols):
            raise ValueError("Las dimensiones de la matriz escaneada no coinciden con la cuadrícula.")
        self.grid = np.where(binary_matrix > 0, CELL_OBSTACLE_IMAGE, CELL_FREE)

    def add_extra_obstacle(self, row: int, col: int) -> None:
        if self.in_bounds(row, col):
            self.grid[row, col] = CELL_OBSTACLE_EXTRA

    def set_origin(self, row: int, col: int) -> None:
        if self.in_bounds(row, col) and not self.is_obstacle(row, col):
            self.grid[row, col] = CELL_ORIGIN
            if (row, col) not in self.origins:
                self.origins.append((row, col))

    def set_destination(self, row: int, col: int) -> None:
        if self.in_bounds(row, col) and not self.is_obstacle(row, col):
            self.grid[row, col] = CELL_DESTINATION
            if (row, col) not in self.destinations:
                self.destinations.append((row, col))

    def set_waypoint(self, row: int, col: int) -> None:
        if self.in_bounds(row, col) and not self.is_obstacle(row, col):
            self.grid[row, col] = CELL_WAYPOINT
            if (row, col) not in self.waypoints:
                self.waypoints.append((row, col))

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_obstacle(self, row: int, col: int) -> bool:
        return self.grid[row, col] in (CELL_OBSTACLE_IMAGE, CELL_OBSTACLE_EXTRA)

    def is_walkable(self, row: int, col: int, clearance: int = 0) -> bool:
        if not self.in_bounds(row, col) or self.is_obstacle(row, col):
            return False

        if clearance > 0:
            for dr in range(-clearance, clearance + 1):
                for dc in range(-clearance, clearance + 1):
                    nr, nc = row + dr, col + dc
                    if not self.in_bounds(nr, nc) or self.is_obstacle(nr, nc):
                        return False
        return True

    @property
    def obstacle_percentage(self) -> float:
        total = self.rows * self.cols
        obstacles = np.isin(self.grid, [CELL_OBSTACLE_IMAGE, CELL_OBSTACLE_EXTRA]).sum()
        return round((obstacles / total) * 100, 2)