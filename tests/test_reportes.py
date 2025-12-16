# tests/test_reportes.py
import unittest
import os
from pathlib import Path
from sistema_atencion import SistemaAtencion
from reportes import Reportes

class TestReportes(unittest.TestCase):
    def test_generar_reporte_mensual(self):
        sistema = SistemaAtencion()
        rep = Reportes(sistema)
        rep.generar_reporte_mensual()
        self.assertTrue(Path("docs/reporte_mensual.md").exists())

if __name__ == "__main__":
    unittest.main()
