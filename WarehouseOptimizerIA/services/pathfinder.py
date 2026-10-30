# services/pathfinder.py
import heapq
import math
from typing import List, Tuple, Set, Dict
from models.warehouse_grid import WarehouseGrid
from config.constants import MAX_TIME_STEPS

class MultiAgentPathfinder:
    DIRECTIONS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
        (0, 0)
    ]

    @staticmethod
    def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @classmethod
    def find_path(
        cls,
        grid: WarehouseGrid,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        clearance: int = 0,
        avoid_employee_collisions: bool = True,
        disallow_same_route: bool = False,
        reserved_spacetime: Set[Tuple[int, int, int]] = None,
        reserved_edges: Set[Tuple[int, int, int, int, int]] = None,
        blocked_route_cells: Set[Tuple[int, int]] = None,
        start_time_step: int = 0
    ) -> List[Tuple[int, int]]:
        if reserved_spacetime is None:
            reserved_spacetime = set()
        if reserved_edges is None:
            reserved_edges = set()
        if blocked_route_cells is None:
            blocked_route_cells = set()

        open_heap = []
        heapq.heappush(open_heap, (cls.heuristic(start, goal), 0.0, start_time_step, start[0], start[1]))

        came_from: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
        g_score: Dict[Tuple[int, int, int], float] = {(start[0], start[1], start_time_step): 0.0}

        while open_heap:
            f, g, t, r, c = heapq.heappop(open_heap)

            if (r, c) == goal:
                path = []
                curr = (r, c, t)
                while curr in came_from:
                    path.append((curr[0], curr[1]))
                    curr = came_from[curr]
                path.append(start)
                path.reverse()
                return path

            if t >= MAX_TIME_STEPS:
                continue

            for dr, dc in cls.DIRECTIONS:
                nr, nc = r + dr, c + dc
                nt = t + 1

                eff_clearance = 0 if (nr, nc) in (start, goal) else clearance
                if not grid.is_walkable(nr, nc, clearance=eff_clearance):
                    continue

                if abs(dr) == 1 and abs(dc) == 1:
                    if not (grid.is_walkable(r + dr, c, 0) and grid.is_walkable(r, c + dc, 0)):
                        continue

                if disallow_same_route and (nr, nc) not in (start, goal):
                    if (nr, nc) in blocked_route_cells:
                        continue

                if avoid_employee_collisions:
                    if (nr, nc, nt) in reserved_spacetime:
                        continue
                    if (nr, nc, r, c, nt) in reserved_edges:
                        continue
                else:
                    if dr == 0 and dc == 0:
                        continue

                if dr == 0 and dc == 0:
                    step_cost = 1.05
                elif abs(dr) + abs(dc) == 2:
                    step_cost = math.sqrt(2)
                else:
                    step_cost = 1.0

                tentative_g = g + step_cost
                state_key = (nr, nc, nt) if avoid_employee_collisions else (nr, nc, 0)

                if tentative_g < g_score.get(state_key, float("inf")):
                    g_score[state_key] = tentative_g
                    came_from[(nr, nc, nt)] = (r, c, t)
                    f_val = tentative_g + cls.heuristic((nr, nc), goal)
                    heapq.heappush(open_heap, (f_val, tentative_g, nt, nr, nc))

        return []