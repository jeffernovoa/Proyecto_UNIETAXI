# tests/test_afiliacion.py
import unittest
from afiliacion import Afiliador

class TestAfiliacion(unittest.TestCase):
    def test_solicitud_cliente(self):
        af = Afiliador()
        af.cargar_base_datos()
        res = af.solicitar_afiliacion_cliente({"id": 999, "nombre": "Nuevo", "tarjeta": "4111-xxxx-9999"})
        self.assertIn(res["estado"], ["admitido", "rechazado"])

    def test_solicitud_taxi_invalido(self):
        af = Afiliador()
        af.cargar_base_datos()
        datos = {
            "id": 1001,
            "conductor": "Test",
            "placa": "UNI-1001",
            "licencia_vigente": False,  # invalida
            "antecedentes_penales": False,
            "certificado_medico": True,
            "seguro_vigente": True,
            "placa_ok": True,
            "impuestos_solventes": True
        }
        res = af.solicitar_afiliacion_taxi(datos)
        self.assertEqual(res["estado"], "rechazado")
        self.assertIn("Licencia vencida", res["motivo"])

if __name__ == "__main__":
    unittest.main()
