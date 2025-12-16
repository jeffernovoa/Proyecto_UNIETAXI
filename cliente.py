# cliente.py
"""
Hilo Cliente:
- Cuando está admitido y no ha solicitado, puede generar una solicitud (autónoma o por GUI).
- Cambia estado en_viaje cuando el taxi lo recoge.
- Al finalizar el viaje, emite una calificación para el taxi.
"""

import time
import random

class Cliente:
    def __init__(self, id_cliente, sistema, origen, destino, nombre=None, tarjeta="4111-xxxx-0000", calificacion_media=5.0, admitido=True):
        self.id_cliente = id_cliente
        self.sistema = sistema
        self.origen = origen
        self.destino = destino
        self.nombre = nombre or f"Cliente-{id_cliente}"
        self.tarjeta = tarjeta
        self.calificacion_media = calificacion_media
        self.solicitud_enviada = False
        self.en_viaje = False
        self.admitido = admitido

    def run(self):
        """Bucle del hilo cliente: genera solicitud con baja probabilidad si es admitido."""
        while True:
            if self.admitido and not self.solicitud_enviada:
                if random.random() < 0.05:
                    self.empujar_solicitud()
            time.sleep(1)

    def empujar_solicitud(self):
        """Encola solicitud del cliente y dispara el procesamiento."""
        self.sistema.recibir_solicitud(self)
        self.solicitud_enviada = True

    def calificar_servicio(self):
        """Devuelve una calificación simulada (3.5 a 5.0)."""
        return round(random.uniform(3.5, 5.0), 1)
