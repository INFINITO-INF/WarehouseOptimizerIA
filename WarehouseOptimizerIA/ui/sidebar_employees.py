# ui/sidebar_employees.py
from typing import List, Tuple, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QListWidget,
    QGroupBox, QFormLayout, QMessageBox, QDialog, QDialogButtonBox
)
from models.employee import Employee
from models.package import Package

class AddPackageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Paquete a Empleado")
        self.setFixedWidth(340)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.input_name = QLineEdit("Caja Estándar")

        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(0.1, 3.0)
        self.spin_width.setSingleStep(0.1)
        self.spin_width.setValue(0.5)
        self.spin_width.setSuffix(" m")

        self.spin_length = QDoubleSpinBox()
        self.spin_length.setRange(0.1, 3.0)
        self.spin_length.setSingleStep(0.1)
        self.spin_length.setValue(0.4)
        self.spin_length.setSuffix(" m")

        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(0.1, 3.0)
        self.spin_height.setSingleStep(0.1)
        self.spin_height.setValue(0.4)
        self.spin_height.setSuffix(" m")

        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setRange(0.1, 150.0)
        self.spin_weight.setSingleStep(1.0)
        self.spin_weight.setValue(8.0)
        self.spin_weight.setSuffix(" kg")

        form.addRow("Descripción:", self.input_name)
        form.addRow("Ancho (X):", self.spin_width)
        form.addRow("Largo (Y):", self.spin_length)
        form.addRow("Alto (Z):", self.spin_height)
        form.addRow("Peso:", self.spin_weight)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_package(self) -> Package:
        return Package(
            name=self.input_name.text().strip() or "Paquete",
            width=self.spin_width.value(),
            length=self.spin_length.value(),
            height=self.spin_height.value(),
            weight=self.spin_weight.value()
        )


class SidebarEmployeesWidget(QWidget):
    def __init__(self, on_employees_changed: Callable, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self.on_employees_changed = on_employees_changed
        self.employees: List[Employee] = []
        self.draft_packages: List[Package] = []
        self.draft_waypoints: List[Tuple[int, int]] = []
        self._next_id = 1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        group_new = QGroupBox("NUEVO AGENTE (EMPLEADO)")
        form_layout = QVBoxLayout(group_new)
        form_layout.setSpacing(6)

        form = QFormLayout()
        form.setSpacing(6)

        self.input_emp_name = QLineEdit("Operador 1")

        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.3, 5.0)
        self.spin_speed.setSingleStep(0.1)
        self.spin_speed.setValue(1.5)
        self.spin_speed.setSuffix(" m/s")

        self.combo_origin = QComboBox()
        self.combo_dest = QComboBox()

        form.addRow("Identificador:", self.input_emp_name)
        form.addRow("Velocidad Base:", self.spin_speed)
        form.addRow("Punto Origen:", self.combo_origin)
        form.addRow("Destino Final:", self.combo_dest)
        form_layout.addLayout(form)

        # Sub-sección: Paradas Intermedias (Picking List)
        wp_label = QLabel("Paradas Intermedias (Picking List en orden):")
        wp_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        form_layout.addWidget(wp_label)

        wp_row = QHBoxLayout()
        self.combo_waypoint = QComboBox()
        self.btn_add_wp = QPushButton("+ Parada")
        self.btn_add_wp.setFixedWidth(80)
        self.btn_add_wp.clicked.connect(self.add_draft_waypoint)
        self.btn_clear_wp = QPushButton("Limpiar")
        self.btn_clear_wp.setFixedWidth(65)
        self.btn_clear_wp.clicked.connect(self.clear_draft_waypoints)
        wp_row.addWidget(self.combo_waypoint, 1)
        wp_row.addWidget(self.btn_add_wp)
        wp_row.addWidget(self.btn_clear_wp)
        form_layout.addLayout(wp_row)

        self.list_draft_wps = QListWidget()
        self.list_draft_wps.setFixedHeight(55)
        form_layout.addWidget(self.list_draft_wps)

        # Sub-sección: Paquetes
        pkg_header = QHBoxLayout()
        pkg_label = QLabel("Paquetes asignados:")
        pkg_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.btn_add_pkg = QPushButton("+ Agregar paquete")
        self.btn_add_pkg.clicked.connect(self.open_add_package_dialog)
        self.btn_clear_pkgs = QPushButton("Limpiar")
        self.btn_clear_pkgs.setFixedWidth(65)
        self.btn_clear_pkgs.clicked.connect(self.clear_draft_packages)
        pkg_header.addWidget(pkg_label)
        pkg_header.addStretch()
        pkg_header.addWidget(self.btn_add_pkg)
        pkg_header.addWidget(self.btn_clear_pkgs)
        form_layout.addLayout(pkg_header)

        self.list_draft_pkgs = QListWidget()
        self.list_draft_pkgs.setFixedHeight(60)
        form_layout.addWidget(self.list_draft_pkgs)

        self.btn_add_emp = QPushButton("+ Agregar empleado al almacén")
        self.btn_add_emp.setObjectName("PrimaryButton")
        self.btn_add_emp.setMinimumHeight(32)
        self.btn_add_emp.clicked.connect(self.create_employee)
        form_layout.addWidget(self.btn_add_emp)

        # Grupo 2: Lista de Empleados Activos
        group_active = QGroupBox("EMPLEADOS ACTIVOS EN SIMULACIÓN")
        active_layout = QVBoxLayout(group_active)

        self.list_employees = QListWidget()
        active_layout.addWidget(self.list_employees)

        btn_row = QHBoxLayout()
        self.btn_remove_emp = QPushButton("Eliminar seleccionado")
        self.btn_remove_emp.clicked.connect(self.remove_selected_employee)
        self.btn_clear_emps = QPushButton("Vaciar todos")
        self.btn_clear_emps.clicked.connect(self.clear_all_employees)
        btn_row.addWidget(self.btn_remove_emp)
        btn_row.addWidget(self.btn_clear_emps)
        active_layout.addLayout(btn_row)

        layout.addWidget(group_new)
        layout.addWidget(group_active, 1)

    def update_endpoints(
        self,
        origins: List[Tuple[int, int]],
        destinations: List[Tuple[int, int]],
        waypoints: List[Tuple[int, int]]
    ):
        curr_orig = self.combo_origin.currentData()
        curr_dest = self.combo_dest.currentData()
        curr_wp = self.combo_waypoint.currentData()

        self.combo_origin.clear()
        for r, c in origins:
            self.combo_origin.addItem(f"Origen ({r}, {c})", (r, c))

        self.combo_dest.clear()
        for r, c in destinations:
            self.combo_dest.addItem(f"Meta ({r}, {c})", (r, c))

        self.combo_waypoint.clear()
        for r, c in waypoints:
            self.combo_waypoint.addItem(f"Parada ({r}, {c})", (r, c))

        if curr_orig in origins:
            self.combo_origin.setCurrentIndex(origins.index(curr_orig))
        if curr_dest in destinations:
            self.combo_dest.setCurrentIndex(destinations.index(curr_dest))
        if curr_wp in waypoints:
            self.combo_waypoint.setCurrentIndex(waypoints.index(curr_wp))

    def add_draft_waypoint(self):
        wp = self.combo_waypoint.currentData()
        if wp is None:
            QMessageBox.information(
                self,
                "Sin paradas en el mapa",
                "Selecciona el pincel 'Parada Picking (Violeta)' en la barra superior "
                "y haz clic en la cuadrícula para marcar estanterías de recogida."
            )
            return
        self.draft_waypoints.append(wp)
        step_num = len(self.draft_waypoints)
        self.list_draft_wps.addItem(f"Parada #{step_num}: Celda {wp}")

    def clear_draft_waypoints(self):
        self.draft_waypoints.clear()
        self.list_draft_wps.clear()

    def open_add_package_dialog(self):
        dlg = AddPackageDialog(self)
        if dlg.exec() == QDialog.Accepted:
            pkg = dlg.get_package()
            self.draft_packages.append(pkg)
            self.list_draft_pkgs.addItem(
                f"{pkg.name} ({pkg.width}x{pkg.length}x{pkg.height}m | {pkg.weight}kg)"
            )

    def clear_draft_packages(self):
        self.draft_packages.clear()
        self.list_draft_pkgs.clear()

    def create_employee(self):
        origin = self.combo_origin.currentData()
        destination = self.combo_dest.currentData()

        if origin is None or destination is None:
            QMessageBox.warning(
                self,
                "Faltan puntos en el mapa",
                "Señala al menos un Punto de Origen (Verde) y un Punto de Destino (Azul) en la cuadrícula."
            )
            return

        name = self.input_emp_name.text().strip() or f"Operador {self._next_id}"
        emp = Employee(
            emp_id=self._next_id,
            name=name,
            base_speed=self.spin_speed.value(),
            origin=origin,
            destination=destination,
            waypoints=self.draft_waypoints
        )
        for p in self.draft_packages:
            emp.add_package(p)

        self.employees.append(emp)
        self._next_id += 1
        self.input_emp_name.setText(f"Operador {self._next_id}")
        self.clear_draft_packages()
        self.clear_draft_waypoints()
        self._refresh_employee_list()
        self.on_employees_changed()

    def remove_selected_employee(self):
        row = self.list_employees.currentRow()
        if 0 <= row < len(self.employees):
            self.employees.pop(row)
            self._refresh_employee_list()
            self.on_employees_changed()

    def clear_all_employees(self):
        self.employees.clear()
        self._next_id = 1
        self.input_emp_name.setText("Operador 1")
        self._refresh_employee_list()
        self.on_employees_changed()

    def _refresh_employee_list(self):
        self.list_employees.clear()
        for emp in self.employees:
            stops_txt = f" | {len(emp.waypoints)} paradas" if emp.waypoints else ""
            item_text = (
                f"#{emp.emp_id} {emp.name}: {emp.origin} -> {emp.destination}{stops_txt}\n"
                f"   Vel: {emp.effective_speed} m/s | Paq: {len(emp.packages)} ({emp.total_weight}kg)"
            )
            self.list_employees.addItem(item_text)