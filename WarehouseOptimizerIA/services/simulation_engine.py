# services/simulation_engine.py
import math
from typing import List, Set, Tuple
from models.warehouse_grid import WarehouseGrid
from models.employee import Employee
from services.pathfinder import MultiAgentPathfinder

class SimulationEngine:
    def __init__(self, grid: WarehouseGrid):
        self.grid = grid
        self.employees: List[Employee] = []
        self.avoid_collisions: bool = True
        self.disallow_same_route: bool = False

    def add_employee(self, employee: Employee) -> None:
        self.grid.set_origin(*employee.origin)
        for wp in employee.waypoints:
            self.grid.set_waypoint(*wp)
        self.grid.set_destination(*employee.destination)
        self.employees.append(employee)

    def run_simulation(self) -> str:
        reserved_spacetime: Set[Tuple[int, int, int]] = set()
        reserved_edges: Set[Tuple[int, int, int, int, int]] = set()
        blocked_route_cells: Set[Tuple[int, int]] = set()

        for emp in self.employees:
            itinerary = emp.full_itinerary
            combined_path: List[Tuple[int, int]] = []
            current_t = 0
            route_broken = False

            # Calcular cada tramo: Origen -> Parada 1 -> Parada 2 -> ... -> Destino
            for i in range(len(itinerary) - 1):
                seg_start = itinerary[i]
                seg_goal = itinerary[i + 1]

                segment = MultiAgentPathfinder.find_path(
                    grid=self.grid,
                    start=seg_start,
                    goal=seg_goal,
                    clearance=emp.clearance_cells,
                    avoid_employee_collisions=self.avoid_collisions,
                    disallow_same_route=self.disallow_same_route,
                    reserved_spacetime=reserved_spacetime,
                    reserved_edges=reserved_edges,
                    blocked_route_cells=blocked_route_cells,
                    start_time_step=current_t
                )

                if not segment:
                    route_broken = True
                    break

                if i == 0:
                    combined_path.extend(segment)
                else:
                    # Evitar duplicar el nodo de unión entre el fin de un tramo y el inicio del siguiente
                    combined_path.extend(segment[1:])

                current_t = len(combined_path) - 1

            emp.path = [] if route_broken else combined_path
            self._calculate_real_timestamps(emp)

            # Registrar reservas espaciotemporales y de celdas para los siguientes empleados
            special_nodes = set(itinerary)
            for t_idx, (r, c) in enumerate(emp.path):
                reserved_spacetime.add((r, c, t_idx))
                if t_idx > 0:
                    prev_r, prev_c = emp.path[t_idx - 1]
                    reserved_edges.add((prev_r, prev_c, r, c, t_idx))
                if (r, c) not in special_nodes:
                    blocked_route_cells.add((r, c))

        return self.generate_text_report()

    def _calculate_real_timestamps(self, emp: Employee) -> None:
        emp.timestamps = []
        if not emp.path:
            return

        current_time = 0.0
        emp.timestamps.append(0.0)

        for i in range(1, len(emp.path)):
            r1, c1 = emp.path[i - 1]
            r2, c2 = emp.path[i]
            dist_cells = math.hypot(r2 - r1, c2 - c1)

            if dist_cells == 0:
                step_time = self.grid.cell_size_m / emp.effective_speed
            else:
                dist_meters = dist_cells * self.grid.cell_size_m
                step_time = dist_meters / emp.effective_speed

            current_time += step_time
            emp.timestamps.append(round(current_time, 2))

    def generate_text_report(self) -> str:
        lines = []
        lines.append("=" * 75)
        lines.append("   REPORTE DE SIMULACIÓN IA - OPTIMIZACIÓN DE RUTAS EN ALMACÉN RETAIL")
        lines.append("=" * 75)

        lines.append("\n[1] PARÁMETROS DEL ESPACIO Y CUADRÍCULA:")
        lines.append(f"  - Dimensiones reales del almacén : {self.grid.real_width_m}m (Ancho) x {self.grid.real_length_m}m (Largo)")
        lines.append(f"  - Tamaño por celda               : {self.grid.cell_size_m}m x {self.grid.cell_size_m}m")
        lines.append(f"  - Resolución de la matriz        : {self.grid.rows} filas x {self.grid.cols} columnas ({self.grid.rows * self.grid.cols} celdas)")
        lines.append(f"  - Porcentaje de obstáculos       : {self.grid.obstacle_percentage}%")

        lines.append("\n[2] REGLAS DE NAVEGACIÓN (CHECKS):")
        lines.append(f"  - Evitar colisión entre empleados : {'ACTIVADO' if self.avoid_collisions else 'DESACTIVADO'}")
        lines.append(f"  - Prohibir repetir la misma ruta  : {'ACTIVADO' if self.disallow_same_route else 'DESACTIVADO'}")

        lines.append("\n[3] MAPA DISCRETIZADO DEL ALMACÉN (# = Obstáculo, O = Origen, P = Parada, D = Meta):")
        lines.append(self._render_ascii_map())

        lines.append("\n[4] DETALLE DE AGENTES (EMPLEADOS), CARGA, PICKING LIST Y RUTAS ELEGIDAS:")
        for emp in self.employees:
            lines.append("-" * 75)
            lines.append(f"  AGENTE #{emp.emp_id}: {emp.name}")
            itinerary_str = " -> ".join(str(pt) for pt in emp.full_itinerary)
            lines.append(f"  - Secuencia de Visita     : {itinerary_str} ({len(emp.waypoints)} paradas intermedias)")
            lines.append(f"  - Velocidad Base          : {emp.base_speed} m/s")
            lines.append(f"  - Paquetes Asignados ({len(emp.packages)})  :")
            if emp.packages:
                for p in emp.packages:
                    lines.append(f"      * {p.name}: {p.width}x{p.length}x{p.height} m (Vol: {p.volume} m³) | Peso: {p.weight} kg")
            else:
                lines.append("      * Sin paquetes (Tránsito ligero)")

            lines.append(f"  - Peso Total / Volumen    : {emp.total_weight} kg / {emp.total_volume} m³")
            lines.append(f"  - Velocidad Real Efectiva : {emp.effective_speed} m/s")
            lines.append(f"  - Radio Físico Ocupado    : {emp.effective_radius_m} m (Margen extra celdas: {emp.clearance_cells})")

            if emp.path:
                total_dist_m = 0.0
                for i in range(1, len(emp.path)):
                    r1, c1 = emp.path[i - 1]
                    r2, c2 = emp.path[i]
                    total_dist_m += math.hypot(r2 - r1, c2 - c1) * self.grid.cell_size_m

                lines.append(f"  - Distancia Total Recorrida: {round(total_dist_m, 2)} metros ({len(emp.path)} nodos)")
                lines.append(f"  - Tiempo Total Estimado   : {emp.timestamps[-1]} segundos")
                formatted_path = " -> ".join([f"{coord}[{t}s]" for coord, t in zip(emp.path, emp.timestamps)])
                lines.append(f"  - Ruta Paso a Paso        : {formatted_path}")
            else:
                lines.append("  - ESTADO DE RUTA          : ¡RUTA BLOQUEADA! Alguna parada o meta es inaccesible.")

        lines.append("=" * 75)
        return "\n".join(lines)

    def _render_ascii_map(self) -> str:
        symbols = {0: ".", 1: "#", 2: "X", 3: "O", 4: "D", 5: "P"}
        canvas = [[symbols.get(int(self.grid.grid[r, c]), ".") for c in range(self.grid.cols)] for r in range(self.grid.rows)]

        for emp in self.employees:
            for r, c in emp.path:
                if canvas[r][c] == ".":
                    canvas[r][c] = str(emp.emp_id)

        return "\n".join(["    " + " ".join(row) for row in canvas])