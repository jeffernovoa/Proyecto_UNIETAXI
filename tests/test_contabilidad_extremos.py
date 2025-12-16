# tests/test_contabilidad_extremos.py
"""
Valida contabilidad en situaciones extremas:
- Cierre sin viajes: ganancia empresa permanece en 0.
- Seguimiento de calidad cuando no hay finalizados: no falla.
"""

import unittest
from sistema_atencion import SistemaAtencion

class TestContabilidadExtremos(unittest.TestCase):
    def test_cierre_sin_viajes(self):
        sistema = SistemaAtencion()
        sistema.cierre_contable()
        self.assertEqual(sistema.ganancia_empresa, 0.0)

    def test_seguimiento_sin_finalizados(self):
        sistema = SistemaAtencion()
        sistema.seguimiento_calidad()
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
