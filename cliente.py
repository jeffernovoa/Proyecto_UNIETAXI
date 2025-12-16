# cliente.py
"""
Cliente (hilo):
- Genera solicitud al sistema con origen/destino.
- Cambia estado en viaje cuando el taxi lo recoge.
- Califica al finalizar.
"""

import time
import random

class Cliente:
    def __init__(self, id_cliente, sistema, origen, destino, nombre=None, tarjeta="****-****", calificacion_media=5.0, admitido=True):
        self.id_cliente = id_cliente
        self.sistema = sistema
        self.origen = origen  # (x,y) normalizados [0,1]
        self.destino = destino
        self.nombre = nombre or f"Cliente-{id_cliente}"
        self.tarjeta = tarjeta
        self.calificacion_media = calificacion_media
        self.solicitud_enviada = False
        self.en_viaje = False
        self.admitido = admitido

    def run(self):
        # Solo clientes admitidos participan en simulación
        while True:
            if self.admitido and not self.solicitud_enviada:
                if random.random() < 0.05:
                    self.empujar_solicitud()
            time.sleep(1)

    def empujar_solicitud(self):
        self.sistema.recibir_solicitud(self)
        self.sistema.procesar_solicitudes()

    def calificar_servicio(self):
        return round(random.uniform(3.5, 5.0), 1)
