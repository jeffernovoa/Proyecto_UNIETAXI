# taxi.py
"""
Taxi (hilo):
- Patrulla cuando está libre.
- Al asignarse, se mueve a origen (pickup) y luego a destino.
- Actualiza progreso para ETA en tiempo real.
- Finalmente reporta finalización y se libera.
"""

import time
import random
from utils import mover_hacia, distancia_euclidiana

class Taxi:
    def __init__(self, id_taxi, sistema, ubicacion_inicial, placa=None, calificacion=4.5, nombre_conductor=None, admitido=True):
        self.id_taxi = id_taxi
        self.sistema = sistema
        self.ubicacion = ubicacion_inicial
        self.placa = placa or f"UNI-{id_taxi:03d}"
        self.calificacion = calificacion
        self.nombre_conductor = nombre_conductor or f"Conductor-{id_taxi}"
        self.ocupado = False
        self.cliente_actual = None
        self.admitido = admitido

        if self.admitido:
            self.sistema.registrar_taxi_disponible(self)

    def run(self):
        while True:
            if self.cliente_actual and self.ocupado:
                self.realizar_servicio()
            else:
                self.patrullar()
            time.sleep(0.2)

    def asignar_servicio(self, cliente):
        self.cliente_actual = cliente
        self.ocupado = True

    def realizar_servicio(self):
        cliente = self.cliente_actual
        if not cliente:
            return

        # 1) Moverse al origen
        while distancia_euclidiana(self.ubicacion, cliente.origen) > 0.01:
            self.ubicacion = mover_hacia(self.ubicacion, cliente.origen, paso=0.01)
            # progreso negativo indica acercamiento al pickup (-0.2..0)
            self.sistema.actualizar_progreso(self, progreso=0.0)
            time.sleep(0.05)

        # 2) Recoger y moverse al destino
        cliente.en_viaje = True
        dist_total = distancia_euclidiana(cliente.origen, cliente.destino)
        dist_recorrida = 0.0
        prev = self.ubicacion
        while distancia_euclidiana(self.ubicacion, cliente.destino) > 0.01:
            self.ubicacion = mover_hacia(self.ubicacion, cliente.destino, paso=0.012)
            dist_recorrida += distancia_euclidiana(prev, self.ubicacion)
            prev = self.ubicacion
            progreso = min(1.0, dist_recorrida / max(1e-6, dist_total))
            self.sistema.actualizar_progreso(self, progreso=progreso)
            time.sleep(0.05)

        # 3) Finalización
        cliente.en_viaje = False
        calificacion = cliente.calificar_servicio()
        self.sistema.finalizar_viaje(self, cliente, calificacion)

        # 4) Liberar
        self.cliente_actual = None
        self.ocupado = False

    def patrullar(self):
        jitter = (random.uniform(-0.003, 0.003), random.uniform(-0.003, 0.003))
        nx = min(1.0, max(0.0, self.ubicacion[0] + jitter[0]))
        ny = min(1.0, max(0.0, self.ubicacion[1] + jitter[1]))
        self.ubicacion = (nx, ny)
