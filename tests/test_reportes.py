# tests/test_reportes.py
"""
Valida la generación del reporte mensual:
- Crea/actualiza docs/reporte_mensual.md.
"""

import unittest
from sistema_atencion import SistemaAtencion
from reportes import Reportes
from pathlib import Path

class TestReportes(unittest.TestCase):
    def test_reporte_mensual_creado(self):
        sistema = SistemaAtencion()
        rep = Reportes(sistema)
        rep.generar_reporte_mensual()
        self.assertTrue(Path("docs/reporte_mensual.md").exists())

if __name__ == "__main__":
    unittest.main()
