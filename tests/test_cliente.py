# tests/test_cliente.py
import unittest
from sistema_atencion import SistemaAtencion
from cliente import Cliente

class TestCliente(unittest.TestCase):
    def test_creacion_cliente(self):
        sistema = SistemaAtencion()
        c = Cliente(1, sistema, origen=(0.2, 0.3), destino=(0.8, 0.9))
        self.assertEqual(c.id_cliente, 1)
        self.assertFalse(c.solicitud_enviada)

    def test_calificacion_rango(self):
        sistema = SistemaAtencion()
        c = Cliente(2, sistema, origen=(0.1, 0.1), destino=(0.2, 0.2))
        val = c.calificar_servicio()
        self.assertTrue(3.5 <= val <= 5.0)

if __name__ == "__main__":
    unittest.main()
