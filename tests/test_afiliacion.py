# tests/test_afiliacion.py
"""
Valida el flujo de afiliación:
- Cliente rechazado por tarjeta inválida.
- Taxi rechazado por licencia vencida.
"""

import unittest
from afiliacion import Afiliador

class TestAfiliacion(unittest.TestCase):
    def test_cliente_rechazado_por_tarjeta(self):
        af = Afiliador()
        res = af.solicitar_afiliacion_cliente({"id": 999, "nombre": "Test", "tarjeta": "123"})
        self.assertEqual(res["estado"], "rechazado")
        self.assertIn("Tarjeta inválida", res["motivo"])

    def test_taxi_rechazado_por_licencia(self):
        af = Afiliador()
        datos = {
            "id": 100, "conductor": "Test", "placa": "UNI-100",
            "licencia_vigente": False,  # causa de rechazo
            "antecedentes_penales": False, "certificado_medico": True,
            "seguro_vigente": True, "placa_ok": True, "impuestos_solventes": True
        }
        res = af.solicitar_afiliacion_taxi(datos)
        self.assertEqual(res["estado"], "rechazado")
        self.assertIn("Licencia vencida", res["motivo"])

if __name__ == "__main__":
    unittest.main()
