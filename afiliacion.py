# afiliacion.py
"""
Afiliación y validaciones simuladas:
- Clientes: datos personales y tarjeta de crédito (formato básico).
- Taxis: licencia vigente, antecedentes, certificado médico, seguro, placa y impuestos.
- Registro persistente en data/clientes.json y data/taxis.json con estado y motivo.
- Flujo formal: solicitud, evaluación, respuesta.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path("data")

class Afiliador:
    def __init__(self):
        self.registro_clientes = []
        self.registro_taxis = []

    def cargar_base_datos(self):
        DATA_DIR.mkdir(exist_ok=True)
        # Simular base (si no existe, crear registros mezclados)
        if not (DATA_DIR / "clientes.json").exists():
            self.registro_clientes = self._generar_clientes_fake(40)
            self._persist("clientes.json", self.registro_clientes)
        else:
            self.registro_clientes = self._load("clientes.json")

        if not (DATA_DIR / "taxis.json").exists():
            self.registro_taxis = self._generar_taxis_fake(30)
            self._persist("taxis.json", self.registro_taxis)
        else:
            self.registro_taxis = self._load("taxis.json")

    def _load(self, fname):
        with open(DATA_DIR / fname, "r", encoding="utf-8") as f:
            return json.load(f)

    def _persist(self, fname, payload):
        with open(DATA_DIR / fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _generar_clientes_fake(self, n):
        res = []
        for i in range(n):
            nombre = f"Cliente-{i}"
            tarjeta = f"4111-xxxx-{i:04d}"
            # Simular validaciones: 85% admitidos
            admitido = random.random() < 0.85
            motivo = "" if admitido else random.choice(["Tarjeta inválida", "Identidad no verificada"])
            res.append({
                "id": i,
                "nombre": nombre,
                "tarjeta": tarjeta,
                "estado": "admitido" if admitido else "rechazado",
                "motivo": motivo
            })
        return res

    def _generar_taxis_fake(self, n):
        res = []
        for i in range(n):
            conductor = f"Conductor-{i}"
            placa = f"UNI-{i:03d}"
            # Validaciones múltiples: 75% admitidos
            ok_licencia = random.random() < 0.9
            ok_antecedentes = random.random() < 0.95
            ok_medico = random.random() < 0.9
            ok_seguro = random.random() < 0.85
            ok_placa = random.random() < 0.95
            ok_impuestos = random.random() < 0.9
            checks = [ok_licencia, ok_antecedentes, ok_medico, ok_seguro, ok_placa, ok_impuestos]
            admitido = all(checks) and (random.random() < 0.95)  # pequeño ruido
            motivo = ""
            if not admitido:
                motivos = []
                if not ok_licencia: motivos.append("Licencia vencida")
                if not ok_antecedentes: motivos.append("Antecedentes penales")
                if not ok_medico: motivos.append("Certificado médico vencido")
                if not ok_seguro: motivos.append("Seguro inválido")
                if not ok_placa: motivos.append("Placa en mal estado")
                if not ok_impuestos: motivos.append("Impuestos no solventes")
                motivo = ", ".join(motivos) or "Evaluación negativa"
            res.append({
                "id": i,
                "conductor": conductor,
                "placa": placa,
                "estado": "admitido" if admitido else "rechazado",
                "motivo": motivo
            })
        return res

    # Flujo formal de solicitud y respuesta
    def solicitar_afiliacion_cliente(self, datos_cliente):
        evaluado = self._evaluar_cliente(datos_cliente)
        self.registro_clientes.append(evaluado)
        self._persist("clientes.json", self.registro_clientes)
        return evaluado

    def solicitar_afiliacion_taxi(self, datos_taxi):
        evaluado = self._evaluar_taxi(datos_taxi)
        self.registro_taxis.append(evaluado)
        self._persist("taxis.json", self.registro_taxis)
        return evaluado

    def _evaluar_cliente(self, datos):
        # Validación simple de tarjeta y nombre
        nombre = datos.get("nombre", "SinNombre")
        tarjeta = datos.get("tarjeta", "")
        ok_tarjeta = tarjeta.startswith("4") and len(tarjeta) >= 12
        admitido = ok_tarjeta and (random.random() < 0.95)
        motivo = "" if admitido else ("Tarjeta inválida" if not ok_tarjeta else "Identidad no verificada")
        return {"id": datos.get("id"), "nombre": nombre, "tarjeta": tarjeta, "estado": "admitido" if admitido else "rechazado", "motivo": motivo}

    def _evaluar_taxi(self, datos):
        ok_licencia = datos.get("licencia_vigente", False)
        ok_antecedentes = not datos.get("antecedentes_penales", True)
        ok_medico = datos.get("certificado_medico", False)
        ok_seguro = datos.get("seguro_vigente", False)
        ok_placa = datos.get("placa_ok", False)
        ok_impuestos = datos.get("impuestos_solventes", False)
        admitido = all([ok_licencia, ok_antecedentes, ok_medico, ok_seguro, ok_placa, ok_impuestos])
        motivo = ""
        if not admitido:
            motivos = []
            if not ok_licencia: motivos.append("Licencia vencida")
            if not ok_antecedentes: motivos.append("Antecedentes penales")
            if not ok_medico: motivos.append("Certificado médico vencido")
            if not ok_seguro: motivos.append("Seguro inválido")
            if not ok_placa: motivos.append("Placa en mal estado")
            if not ok_impuestos: motivos.append("Impuestos no solventes")
            motivo = ", ".join(motivos)
        return {
            "id": datos.get("id"),
            "conductor": datos.get("conductor", f"Conductor-{datos.get('id')}"),
            "placa": datos.get("placa", f"UNI-{datos.get('id'):03d}"),
            "estado": "admitido" if admitido else "rechazado",
            "motivo": motivo
        }

    # Afiliar en el sistema (cargar conjuntos admitidos)
    def afiliar_clientes_sistema(self, sistema):
        # No requiere acción directa en sistema; se usan para generación de clientes
        pass

    def afiliar_taxis_sistema(self, sistema):
        # Ídem; la selección en utils respeta estado admitido
        pass
