# ui/simulator_tab.py
from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsSimpleTextItem,
    QRadioButton, QButtonGroup, QCheckBox, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont

from config.constants import (
    CELL_FREE, CELL_OBSTACLE_IMAGE, CELL_OBSTACLE_EXTRA,
    CELL_ORIGIN, CELL_DESTINATION, CELL_WAYPOINT
)
from models.warehouse_grid import WarehouseGrid
from services.simulation_engine import SimulationEngine
from ui.sidebar_employees import SidebarEmployeesWidget
from ui.report_console import ReportConsoleWidget

class InteractiveGridCanvas(QGraphicsView):
    AGENT_COLORS = [
        "#38BDF8", "#F59E0B", "#A855F7", "#EC4899",
        "#10B981", "#F97316", "#6366F1", "#14B8A6"
    ]

    def __init__(self, on_grid_modified, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setStyleSheet("background-color: #14171F; border: 1px solid #2E3440; border-radius: 4px;")

        self.grid: WarehouseGrid = None
        self.cell_px = 26
        self.edit_mode = CELL_ORIGIN
        self.on_grid_modified = on_grid_modified

        self.agent_items: Dict[int, QGraphicsEllipseItem] = {}
        self.agent_labels: Dict[int, QGraphicsSimpleTextItem] = {}

    def set_warehouse_grid(self, grid: WarehouseGrid):
        self.grid = grid
        self.cell_px = max(16, min(36, int(720 / max(grid.cols, grid.rows))))
        self.redraw_static_grid()

    def redraw_static_grid(self, employees=None):
        self.scene.clear()
        self.agent_items.clear()
        self.agent_labels.clear()

        if self.grid is None:
            return

        color_map = {
            CELL_FREE: QColor("#1E222B"),
            CELL_OBSTACLE_IMAGE: QColor("#475569"),
            CELL_OBSTACLE_EXTRA: QColor("#B45309"),
            CELL_ORIGIN: QColor("#15803D"),
            CELL_DESTINATION: QColor("#1D4ED8"),
            CELL_WAYPOINT: QColor("#7C3AED"),  # Violeta formal para paradas de Picking
        }
        grid_pen = QPen(QColor("#282E3B"), 1)

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                val = int(self.grid.grid[r, c])
                brush = QBrush(color_map.get(val, QColor("#1E222B")))
                self.scene.addRect(
                    c * self.cell_px, r * self.cell_px,
                    self.cell_px, self.cell_px,
                    grid_pen, brush
                )

        if employees:
            for idx, emp in enumerate(employees):
                color = QColor(self.AGENT_COLORS[idx % len(self.AGENT_COLORS)])
                if len(emp.path) > 1:
                    path_pen = QPen(color, 2.5, Qt.DashLine)
                    for i in range(1, len(emp.path)):
                        r1, c1 = emp.path[i - 1]
                        r2, c2 = emp.path[i]
                        x1 = (c1 + 0.5) * self.cell_px
                        y1 = (r1 + 0.5) * self.cell_px
                        x2 = (c2 + 0.5) * self.cell_px
                        y2 = (r2 + 0.5) * self.cell_px
                        self.scene.addLine(x1, y1, x2, y2, path_pen)

                radius_ratio = min(0.95, max(0.35, emp.effective_radius_m / self.grid.cell_size_m))
                radius_px = radius_ratio * self.cell_px
                start_r, start_c = emp.origin
                cx = (start_c + 0.5) * self.cell_px
                cy = (start_r + 0.5) * self.cell_px

                circle = QGraphicsEllipseItem(-radius_px / 2, -radius_px / 2, radius_px, radius_px)
                circle.setPos(cx, cy)
                circle.setBrush(QBrush(color))
                circle.setPen(QPen(QColor("#0F172A"), 1.5))
                circle.setZValue(10)
                self.scene.addItem(circle)

                lbl = QGraphicsSimpleTextItem(f"E{emp.emp_id}")
                lbl.setBrush(QBrush(QColor("#F8FAFC")))
                lbl.setFont(QFont("Segoe UI", 7, QFont.Bold))
                lbl.setPos(cx - 6, cy - 6)
                lbl.setZValue(11)
                self.scene.addItem(lbl)

                self.agent_items[emp.emp_id] = circle
                self.agent_labels[emp.emp_id] = lbl

        self.scene.setSceneRect(0, 0, self.grid.cols * self.cell_px, self.grid.rows * self.cell_px)

    def update_agent_position(self, emp_id: int, row_float: float, col_float: float):
        if emp_id in self.agent_items:
            cx = (col_float + 0.5) * self.cell_px
            cy = (row_float + 0.5) * self.cell_px
            self.agent_items[emp_id].setPos(QPointF(cx, cy))
            self.agent_labels[emp_id].setPos(QPointF(cx - 6, cy - 6))

    def mousePressEvent(self, event):
        self._apply_brush(event.position().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._apply_brush(event.position().toPoint())
        super().mouseMoveEvent(event)

    def _apply_brush(self, pos):
        if self.grid is None:
            return
        scene_pt = self.mapToScene(pos)
        c = int(scene_pt.x() // self.cell_px)
        r = int(scene_pt.y() // self.cell_px)

        if not self.grid.in_bounds(r, c):
            return

        if self.grid.grid[r, c] == CELL_OBSTACLE_IMAGE and self.edit_mode != CELL_FREE:
            return

        if (r, c) in self.grid.origins and self.edit_mode != CELL_ORIGIN:
            self.grid.origins.remove((r, c))
        if (r, c) in self.grid.destinations and self.edit_mode != CELL_DESTINATION:
            self.grid.destinations.remove((r, c))
        if (r, c) in self.grid.waypoints and self.edit_mode != CELL_WAYPOINT:
            self.grid.waypoints.remove((r, c))

        if self.edit_mode == CELL_ORIGIN:
            self.grid.set_origin(r, c)
        elif self.edit_mode == CELL_DESTINATION:
            self.grid.set_destination(r, c)
        elif self.edit_mode == CELL_WAYPOINT:
            self.grid.set_waypoint(r, c)
        elif self.edit_mode == CELL_OBSTACLE_EXTRA:
            self.grid.add_extra_obstacle(r, c)
        elif self.edit_mode == CELL_FREE:
            self.grid.grid[r, c] = CELL_FREE

        self.redraw_static_grid()
        self.on_grid_modified()


class SimulatorTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid: WarehouseGrid = None
        self.sim_engine: SimulationEngine = None

        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(33)
        self.anim_timer.timeout.connect(self._on_animation_tick)
        self.elapsed_sim_sec = 0.0
        self.max_sim_sec = 0.0

        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #232834; border: 1px solid #2E3440; border-radius: 5px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 8, 10, 8)
        tb_layout.setSpacing(10)

        lbl_mode = QLabel("Pincel:")
        lbl_mode.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        tb_layout.addWidget(lbl_mode)

        self.mode_group = QButtonGroup(self)
        rb_origin = QRadioButton("Origen (Verde)")
        rb_wp = QRadioButton("Parada Picking (Violeta)")
        rb_dest = QRadioButton("Destino (Azul)")
        rb_extra = QRadioButton("Obstáculo (Ámbar)")
        rb_erase = QRadioButton("Borrar")
        rb_origin.setChecked(True)

        self.mode_group.addButton(rb_origin, CELL_ORIGIN)
        self.mode_group.addButton(rb_wp, CELL_WAYPOINT)
        self.mode_group.addButton(rb_dest, CELL_DESTINATION)
        self.mode_group.addButton(rb_extra, CELL_OBSTACLE_EXTRA)
        self.mode_group.addButton(rb_erase, CELL_FREE)
        self.mode_group.idClicked.connect(self._change_brush_mode)

        tb_layout.addWidget(rb_origin)
        tb_layout.addWidget(rb_wp)
        tb_layout.addWidget(rb_dest)
        tb_layout.addWidget(rb_extra)
        tb_layout.addWidget(rb_erase)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #3B4252;")
        tb_layout.addWidget(sep)

        self.chk_avoid_collisions = QCheckBox("Evitar choques")
        self.chk_avoid_collisions.setChecked(True)
        self.chk_disallow_same_route = QCheckBox("No repetir ruta")
        self.chk_disallow_same_route.setChecked(False)

        tb_layout.addWidget(self.chk_avoid_collisions)
        tb_layout.addWidget(self.chk_disallow_same_route)
        tb_layout.addStretch()

        self.lbl_clock = QLabel("Tiempo: 0.0 s")
        self.lbl_clock.setStyleSheet("font-family: Consolas; font-weight: bold; color: #38BDF8; font-size: 13px;")
        tb_layout.addWidget(self.lbl_clock)

        self.btn_run = QPushButton("▶ Iniciar Simulación IA")
        self.btn_run.setObjectName("PrimaryButton")
        self.btn_run.setMinimumHeight(32)
        self.btn_run.clicked.connect(self.start_simulation)
        tb_layout.addWidget(self.btn_run)

        root_layout.addWidget(toolbar)

        v_splitter = QSplitter(Qt.Vertical)

        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.canvas = InteractiveGridCanvas(on_grid_modified=self._sync_endpoints)
        self.sidebar = SidebarEmployeesWidget(on_employees_changed=self._on_employees_updated)

        top_layout.addWidget(self.canvas, 1)
        top_layout.addWidget(self.sidebar)

        self.report_console = ReportConsoleWidget()

        v_splitter.addWidget(top_container)
        v_splitter.addWidget(self.report_console)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 2)

        root_layout.addWidget(v_splitter, 1)

    def load_warehouse_grid(self, grid: WarehouseGrid):
        self.anim_timer.stop()
        self.grid = grid

        if not self.grid.origins:
            self._place_default_point(mode="origin")
        if not self.grid.destinations:
            self._place_default_point(mode="dest")
        if not self.grid.waypoints:
            self._place_default_point(mode="waypoint")

        self.canvas.set_warehouse_grid(self.grid)
        self._sync_endpoints()

    def _place_default_point(self, mode: str):
        if mode == "origin":
            r_range, c_range = range(1, self.grid.rows - 1), range(1, self.grid.cols - 1)
        elif mode == "dest":
            r_range, c_range = range(self.grid.rows - 2, 0, -1), range(self.grid.cols - 2, 0, -1)
        else:
            r_range, c_range = range(self.grid.rows // 2, self.grid.rows - 1), range(self.grid.cols // 2, self.grid.cols - 1)

        for r in r_range:
            for c in c_range:
                if not self.grid.is_obstacle(r, c) and self.grid.grid[r, c] == CELL_FREE:
                    if mode == "origin":
                        self.grid.set_origin(r, c)
                    elif mode == "dest":
                        self.grid.set_destination(r, c)
                    else:
                        self.grid.set_waypoint(r, c)
                    return

    def _change_brush_mode(self, mode_id: int):
        self.canvas.edit_mode = mode_id

    def _sync_endpoints(self):
        if self.grid:
            self.sidebar.update_endpoints(
                self.grid.origins,
                self.grid.destinations,
                self.grid.waypoints
            )
            self.canvas.redraw_static_grid(self.sidebar.employees)

    def _on_employees_updated(self):
        self.canvas.redraw_static_grid(self.sidebar.employees)

    def start_simulation(self):
        if self.grid is None:
            return
        if not self.sidebar.employees:
            if self.grid.origins and self.grid.destinations:
                self.sidebar.create_employee()

        self.anim_timer.stop()
        self.sim_engine = SimulationEngine(self.grid)
        self.sim_engine.avoid_collisions = self.chk_avoid_collisions.isChecked()
        self.sim_engine.disallow_same_route = self.chk_disallow_same_route.isChecked()

        for emp in self.sidebar.employees:
            self.sim_engine.add_employee(emp)

        report_text = self.sim_engine.run_simulation()
        self.report_console.set_report(report_text)

        self.canvas.redraw_static_grid(self.sidebar.employees)
        self.elapsed_sim_sec = 0.0
        self.max_sim_sec = max(
            (emp.timestamps[-1] for emp in self.sidebar.employees if emp.timestamps),
            default=0.0
        )

        if self.max_sim_sec > 0:
            self.anim_timer.start()

    def _on_animation_tick(self):
        self.elapsed_sim_sec += 0.033 * 2.5
        if self.elapsed_sim_sec >= self.max_sim_sec:
            self.elapsed_sim_sec = self.max_sim_sec
            self.anim_timer.stop()

        self.lbl_clock.setText(f"Tiempo: {self.elapsed_sim_sec:.1f} / {self.max_sim_sec:.1f} s")

        for emp in self.sidebar.employees:
            if not emp.path or not emp.timestamps:
                continue

            t = self.elapsed_sim_sec
            if t >= emp.timestamps[-1]:
                r, c = emp.path[-1]
                self.canvas.update_agent_position(emp.emp_id, float(r), float(c))
                continue

            for i in range(len(emp.timestamps) - 1):
                t0, t1 = emp.timestamps[i], emp.timestamps[i + 1]
                if t0 <= t <= t1:
                    ratio = 0.0 if (t1 - t0) == 0 else (t - t0) / (t1 - t0)
                    r0, c0 = emp.path[i]
                    r1, c1 = emp.path[i + 1]
                    curr_r = r0 + (r1 - r0) * ratio
                    curr_c = c0 + (c1 - c0) * ratio
                    self.canvas.update_agent_position(emp.emp_id, curr_r, curr_c)
                    break