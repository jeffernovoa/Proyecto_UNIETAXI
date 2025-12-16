# tests/test_sistema.py
import unittest
from sistema_atencion import SistemaAtencion
from cliente import Cliente
from taxi import Taxi

class TestSistema(unittest.TestCase):
    def test_match_sin_taxis(self):
        sistema = SistemaAtencion()
        c = Cliente(1, sistema, origen=(0.5, 0.5), destino=(0.6, 0.6))
        sistema.recibir_solicitud(c)
        sistema.procesar_solicitudes()
        self.assertEqual(sistema.viajes_activos(), 0)  # Reencola solicitud

    def test_match_con_empate_distancia(self):
        sistema = SistemaAtencion()
        c = Cliente(2, sistema, origen=(0.5, 0.5), destino=(0.7, 0.7))
        t1 = Taxi(1, sistema, ubicacion_inicial=(0.52, 0.52), calificacion=4.5)
        t2 = Taxi(2, sistema, ubicacion_inicial=(0.52, 0.52), calificacion=4.9)
        sistema.recibir_solicitud(c)
        sistema.procesar_solicitudes()
        # t2 debe ser elegido por mayor calificación
        self.assertTrue(t2.ocupado)

    def test_cierre_contable_con_viaje_activo(self):
        sistema = SistemaAtencion()
        c = Cliente(3, sistema, origen=(0.2, 0.2), destino=(0.8, 0.8))
        t = Taxi(3, sistema, ubicacion_inicial=(0.21, 0.21))
        # Fuerza asignación
        sistema.recibir_solicitud(c)
        sistema.procesar_solicitudes()
        sistema.cierre_contable()  # No debe fallar aunque haya viajes activos
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
