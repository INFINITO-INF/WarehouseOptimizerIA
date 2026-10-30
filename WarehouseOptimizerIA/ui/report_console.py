# ui/report_console.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont

class ReportConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(6)

        # Cabecera del panel de reporte
        header_layout = QHBoxLayout()
        title = QLabel("REGISTRO Y REPORTE TÉCNICO DE SIMULACIÓN (TEXTO)")
        title.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 11px; letter-spacing: 0.5px;")

        self.btn_export = QPushButton("Exportar a .TXT")
        self.btn_export.setFixedWidth(130)
        self.btn_export.clicked.connect(self.export_report)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setFixedWidth(90)
        self.btn_clear.clicked.connect(lambda: self.text_area.clear())

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_clear)
        header_layout.addWidget(self.btn_export)

        # Área de texto monoespaciada formal
        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.Monospace)
        self.text_area.setFont(font)
        self.text_area.setPlaceholderText(
            "Aquí se imprimirán los resultados detallados de la simulación, variables físicas, "
            "espacio discretizado y rutas elegidas por cada agente de IA..."
        )

        layout.addLayout(header_layout)
        layout.addWidget(self.text_area)

    def set_report(self, report_text: str):
        self.text_area.setPlainText(report_text)
        # También imprimimos en la consola estándar de Visual Studio 2026
        print("\n" + report_text)

    def export_report(self):
        content = self.text_area.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Reporte vacío", "Aún no hay resultados de simulación para exportar.")
            return

        os.makedirs("outputs", exist_ok=True)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte de Simulación",
            os.path.join("outputs", "reporte_simulacion.txt"),
            "Archivos de Texto (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Exportación exitosa", f"Reporte guardado en:\n{file_path}")