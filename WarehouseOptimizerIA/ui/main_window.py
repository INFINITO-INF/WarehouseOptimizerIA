# ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget
from models.warehouse_grid import WarehouseGrid
from ui.scanner_tab import ScannerTabWidget
from ui.simulator_tab import SimulatorTabWidget

FORMAL_DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1E222B;
    color: #E2E8F0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QTabWidget::pane {
    border: 1px solid #2E3440;
    background-color: #1E222B;
}
QTabBar::tab {
    background-color: #161920;
    color: #94A3B8;
    padding: 9px 20px;
    border: 1px solid #2E3440;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 4px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #262B36;
    color: #F8FAFC;
    border-top: 2px solid #3B82F6;
}
QGroupBox {
    background-color: #242936;
    border: 1px solid #323949;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #94A3B8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QDoubleSpinBox, QComboBox, QListWidget, QPlainTextEdit {
    background-color: #161920;
    border: 1px solid #333A4B;
    border-radius: 4px;
    padding: 5px;
    color: #F1F5F9;
}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3B82F6;
}
QPushButton {
    background-color: #2E3545;
    border: 1px solid #3E475B;
    border-radius: 4px;
    padding: 6px 12px;
    color: #E2E8F0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #384152;
}
QPushButton#PrimaryButton {
    background-color: #2563EB;
    border: 1px solid #3B82F6;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton#PrimaryButton:hover {
    background-color: #1D4ED8;
}
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #CBD5E1;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimizador de Rutas IA en Almacenes Retail - Visual Studio 2026")
        self.resize(1360, 840)
        self.setStyleSheet(FORMAL_DARK_STYLESHEET)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Herramienta 1 y Herramienta 2
        self.scanner_tab = ScannerTabWidget(on_grid_ready=self._on_grid_transferred)
        self.simulator_tab = SimulatorTabWidget()

        self.tabs.addTab(self.scanner_tab, "1. Escáner de Planos e Imágenes (Herramienta 1)")
        self.tabs.addTab(self.simulator_tab, "2. Simulador de Rutas y Agentes IA (Herramienta 2)")

        # Cargar un plano inicial automáticamente para que ambas pestañas estén listas al abrir
        self.scanner_tab.load_sample_image()
        self.simulator_tab.load_warehouse_grid(self.scanner_tab.scanned_grid)

    def _on_grid_transferred(self, grid: WarehouseGrid):
        self.simulator_tab.load_warehouse_grid(grid)
        self.tabs.setCurrentWidget(self.simulator_tab)
