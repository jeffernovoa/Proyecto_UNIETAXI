# tests/test_matching_tiebreak.py
"""
Valida el desempate por calificación en matching:
- Dos taxis a misma distancia; asigna el de mayor calificación.
"""

import unittest
from sistema_atencion import SistemaAtencion
from cliente import Cliente
from taxi import Taxi

class TestMatchingTiebreak(unittest.TestCase):
    def test_empate_distancia_desempate_por_calificacion(self):
        sistema = SistemaAtencion()
        c = Cliente(1, sistema, origen=(0.5, 0.5), destino=(0.6, 0.6))
        t1 = Taxi(1, sistema, ubicacion_inicial=(0.51, 0.51), calificacion=4.5)
        t2 = Taxi(2, sistema, ubicacion_inicial=(0.51, 0.51), calificacion=4.9)
        sistema.recibir_solicitud(c)
        sistema.procesar_solicitudes()
        self.assertTrue(t2.ocupado)
        self.assertFalse(t1.ocupado)

if __name__ == "__main__":
    unittest.main()
