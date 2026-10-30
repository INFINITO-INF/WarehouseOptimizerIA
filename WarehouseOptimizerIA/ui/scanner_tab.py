# ui/scanner_tab.py
import os
import cv2
import numpy as np
from typing import Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QDoubleSpinBox, QSlider, QCheckBox, QPushButton, QLabel,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from services.image_scanner import ImageScanner
from models.warehouse_grid import WarehouseGrid

class ScannerTabWidget(QWidget):
    def __init__(self, on_grid_ready: Callable[[WarehouseGrid], None], parent=None):
        super().__init__(parent)
        self.on_grid_ready = on_grid_ready
        self.current_image_path = ""
        self.scanned_grid: WarehouseGrid = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        # Panel izquierdo: Controles del Escáner
        controls_panel = QGroupBox("PARÁMETROS DEL ESCÁNER DE ALMACÉN")
        controls_panel.setFixedWidth(360)
        c_layout = QVBoxLayout(controls_panel)
        c_layout.setSpacing(12)

        btn_load_layout = QHBoxLayout()
        self.btn_browse = QPushButton("Subir Imagen de Almacén...")
        self.btn_browse.clicked.connect(self.browse_image)
        self.btn_sample = QPushButton("Generar Plano Demo")
        self.btn_sample.clicked.connect(self.load_sample_image)
        btn_load_layout.addWidget(self.btn_browse)
        btn_load_layout.addWidget(self.btn_sample)
        c_layout.addLayout(btn_load_layout)

        self.lbl_path = QLabel("Ningún archivo seleccionado")
        self.lbl_path.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.lbl_path.setWordWrap(True)
        c_layout.addWidget(self.lbl_path)

        form = QFormLayout()
        form.setSpacing(10)

        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(5.0, 300.0)
        self.spin_width.setValue(30.0)
        self.spin_width.setSuffix(" m")

        self.spin_length = QDoubleSpinBox()
        self.spin_length.setRange(5.0, 300.0)
        self.spin_length.setValue(20.0)
        self.spin_length.setSuffix(" m")

        self.spin_cell = QDoubleSpinBox()
        self.spin_cell.setRange(0.25, 5.0)
        self.spin_cell.setSingleStep(0.25)
        self.spin_cell.setValue(1.0)
        self.spin_cell.setSuffix(" m")

        self.slider_thresh = QSlider(Qt.Horizontal)
        self.slider_thresh.setRange(20, 240)
        self.slider_thresh.setValue(180)
        self.slider_thresh.valueChanged.connect(self.preview_scan)

        self.chk_invert = QCheckBox("Obstáculos oscuros sobre fondo claro")
        self.chk_invert.setChecked(True)
        self.chk_invert.toggled.connect(self.preview_scan)

        form.addRow("Ancho Aprox. (X):", self.spin_width)
        form.addRow("Largo Aprox. (Y):", self.spin_length)
        form.addRow("Tamaño de Celda:", self.spin_cell)
        form.addRow("Sensibilidad Umbral:", self.slider_thresh)
        form.addRow("", self.chk_invert)
        c_layout.addLayout(form)

        self.btn_process = QPushButton("Analizar Imagen y Generar Cuadrícula")
        self.btn_process.clicked.connect(self.preview_scan)
        c_layout.addWidget(self.btn_process)

        self.lbl_stats = QLabel("Esperando escaneo...")
        self.lbl_stats.setStyleSheet("color: #CBD5E1; background: #181B22; padding: 8px; border-radius: 4px;")
        self.lbl_stats.setWordWrap(True)
        c_layout.addWidget(self.lbl_stats)

        c_layout.addStretch()

        self.btn_send_sim = QPushButton("Transferir Cuadrícula al Simulador (Herramienta 2) ->")
        self.btn_send_sim.setObjectName("PrimaryButton")
        self.btn_send_sim.setMinimumHeight(38)
        self.btn_send_sim.clicked.connect(self.confirm_and_transfer)
        c_layout.addWidget(self.btn_send_sim)

        # Panel derecho: Previsualización comparativa
        preview_panel = QGroupBox("PREVISUALIZACIÓN DE DETECCIÓN DE OBSTÁCULOS Y DISCRETIZACIÓN")
        p_layout = QHBoxLayout(preview_panel)

        self.lbl_orig_img = QLabel("Imagen Original")
        self.lbl_orig_img.setAlignment(Qt.AlignCenter)
        self.lbl_orig_img.setStyleSheet("background-color: #161920; border: 1px solid #2E3440; border-radius: 4px;")

        self.lbl_grid_img = QLabel("Cuadrícula Detectada")
        self.lbl_grid_img.setAlignment(Qt.AlignCenter)
        self.lbl_grid_img.setStyleSheet("background-color: #161920; border: 1px solid #2E3440; border-radius: 4px;")

        p_layout.addWidget(self.lbl_orig_img, 1)
        p_layout.addWidget(self.lbl_grid_img, 1)

        main_layout.addWidget(controls_panel)
        main_layout.addWidget(preview_panel, 1)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Plano de Almacén",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.current_image_path = file_path
            self.lbl_path.setText(f"Archivo: {os.path.basename(file_path)}")
            self.preview_scan()

    def load_sample_image(self):
        sample_path = os.path.join("outputs", "plano_almacen_demo.png")
        ImageScanner.generate_sample_warehouse_image(sample_path)
        self.current_image_path = sample_path
        self.lbl_path.setText(f"Archivo Demo: {os.path.basename(sample_path)}")
        self.preview_scan()

    def preview_scan(self):
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            return

        try:
            self.scanned_grid = ImageScanner.scan_image_to_grid(
                image_path=self.current_image_path,
                real_width_m=self.spin_width.value(),
                real_length_m=self.spin_length.value(),
                cell_size_m=self.spin_cell.value(),
                threshold_val=self.slider_thresh.value(),
                invert_colors=self.chk_invert.isChecked()
            )
            self._render_previews()
            self.lbl_stats.setText(
                f"Dimensiones: {self.scanned_grid.real_width_m}m x {self.scanned_grid.real_length_m}m\n"
                f"Matriz generada: {self.scanned_grid.rows} filas x {self.scanned_grid.cols} columnas\n"
                f"Área con obstáculos: {self.scanned_grid.obstacle_percentage}%"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de Escaneo", str(e))

    def _render_previews(self):
        # Mostrar imagen original
        orig_pix = QPixmap(self.current_image_path)
        if not orig_pix.isNull():
            lbl_size = self.lbl_orig_img.size()
            w_target = max(240, lbl_size.width())
            h_target = max(180, lbl_size.height())
            self.lbl_orig_img.setPixmap(orig_pix.scaled(
                w_target, h_target, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

        # Construir previsualización de la cuadrícula detectada
        rows, cols = self.scanned_grid.rows, self.scanned_grid.cols
        vis = np.zeros((rows, cols, 3), dtype=np.uint8)
        vis[self.scanned_grid.grid == 0] = [38, 43, 54]    # Suelo libre (Slate oscuro)
        vis[self.scanned_grid.grid == 1] = [100, 116, 139] # Obstáculo detectado (Gris acero)

        # Escalar con bordes de celda visibles (CORREGIDO: cv2.INTER_NEAREST en lugar de Qt.FastTransformation)
        scale = max(8, min(480 // max(1, cols), 400 // max(1, rows)))
        vis_large = cv2.resize(vis, (cols * scale, rows * scale), interpolation=cv2.INTER_NEAREST)

        # Dibujar líneas de cuadrícula sutiles
        for r in range(rows):
            cv2.line(vis_large, (0, r * scale), (cols * scale, r * scale), (24, 27, 34), 1)
        for c in range(cols):
            cv2.line(vis_large, (c * scale, 0), (c * scale, rows * scale), (24, 27, 34), 1)

        h, w, ch = vis_large.shape
        qimg = QImage(vis_large.data, w, h, ch * w, QImage.Format_RGB888)
        self.lbl_grid_img.setPixmap(QPixmap.fromImage(qimg))

    def confirm_and_transfer(self):
        if self.scanned_grid is None:
            self.load_sample_image()
        if self.scanned_grid is not None:
            self.on_grid_ready(self.scanned_grid)
