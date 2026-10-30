# config/constants.py

# Estados de las celdas en la cuadrícula
CELL_FREE = 0
CELL_OBSTACLE_IMAGE = 1   # Detectado por el escáner OpenCV
CELL_OBSTACLE_EXTRA = 2   # Agregado manualmente en la Herramienta 2
CELL_ORIGIN = 3           # Punto de inicio
CELL_DESTINATION = 4      # Punto de destino final
CELL_WAYPOINT = 5         # Parada intermedia (Picking / Recogida)

# Parámetros físicos y de penalización
WEIGHT_PENALTY_FACTOR = 0.015    # Reducción de velocidad de 1.5% por cada kg de carga
VOLUME_PENALTY_FACTOR = 0.25     # Reducción de velocidad de 25% por cada m³ de volumen
MIN_SPEED_RATIO = 0.20           # El empleado nunca irá a menos del 20% de su velocidad base

# Umbral de volumen (m³) a partir del cual el empleado necesita mayor margen de espacio
LARGE_LOAD_VOLUME_THRESHOLD = 0.35 

# Parámetros de IA y Simulación
DEFAULT_CELL_SIZE_M = 1.0        # Cada celda equivale a 1m x 1m por defecto
SHARED_ROUTE_PENALTY = 50.0      # Costo extra para evitar que tomen la misma ruta
MAX_TIME_STEPS = 800             # Aumentado para soportar rutas multi-parada