# tests/test_taxi.py
import unittest
from sistema_atencion import SistemaAtencion
from taxi import Taxi

class TestTaxi(unittest.TestCase):
    def test_creacion_taxi(self):
        sistema = SistemaAtencion()
        t = Taxi(5, sistema, ubicacion_inicial=(0.5, 0.5), calificacion=4.7)
        self.assertEqual(t.id_taxi, 5)
        self.assertFalse(t.ocupado)

    def test_registro_disponible(self):
        sistema = SistemaAtencion()
        t = Taxi(1, sistema, ubicacion_inicial=(0.3, 0.3))
        self.assertIn(t, sistema.taxis_disponibles)

if __name__ == "__main__":
    unittest.main()
