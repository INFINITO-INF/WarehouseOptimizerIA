# services/image_scanner.py
import cv2
import numpy as np
import os
from models.warehouse_grid import WarehouseGrid

class ImageScanner:
    @staticmethod
    def scan_image_to_grid(
        image_path: str,
        real_width_m: float,
        real_length_m: float,
        cell_size_m: float = 1.0,
        threshold_val: int = 180,
        invert_colors: bool = True
    ) -> WarehouseGrid:
        """
        Lee una imagen del almacén, detecta obstáculos oscuros sobre fondo claro
        y la convierte en un objeto WarehouseGrid.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen en la ruta: {image_path}")

        img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            raise ValueError("El archivo de imagen está corrupto o el formato no es válido.")

        # 1. Filtro Gaussiano para limpiar ruido del plano
        blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)

        # 2. Binarización: Si invert_colors=True, lo oscuro (paredes/estantes) pasa a ser 255 (1 = obstáculo)
        thresh_type = cv2.THRESH_BINARY_INV if invert_colors else cv2.THRESH_BINARY
        _, binary = cv2.threshold(blurred, threshold_val, 255, thresh_type)

        # 3. Crear el modelo de cuadrícula según las medidas reales en metros
        warehouse = WarehouseGrid(real_width_m, real_length_m, cell_size_m)

        # 4. Redimensionar la imagen binarizada al número exacto de filas y columnas
        resized = cv2.resize(
            binary,
            (warehouse.cols, warehouse.rows),
            interpolation=cv2.INTER_AREA
        )

        # Si más del 25% del bloque tiene obstáculo, la celda se marca como obstáculo
        obstacle_matrix = (resized > 64).astype(int)
        warehouse.load_from_binary_matrix(obstacle_matrix)
        return warehouse

    @staticmethod
    def generate_sample_warehouse_image(output_path: str) -> str:
        """
        Crea un plano sintético de almacén en blanco y negro (600x400 px)
        con pasillos y estanterías para probar el backend de inmediato.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Fondo blanco (suelo libre = 255)
        img = np.full((400, 600), 255, dtype=np.uint8)

        # Dibujar estanterías de retail (bloques negros = 0)
        cv2.rectangle(img, (120, 60), (180, 300), 0, -1)   # Estante 1
        cv2.rectangle(img, (270, 80), (330, 340), 0, -1)   # Estante 2
        cv2.rectangle(img, (420, 60), (480, 300), 0, -1)   # Estante 3

        cv2.imwrite(output_path, img)
        return output_path
