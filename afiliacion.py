# afiliacion.py
"""
Módulo de afiliación:
- Carga/Inicializa registros de clientes y taxis (con mezcla de admitidos/rechazados).
- Validaciones simuladas para solicitudes nuevas (cliente: tarjeta; taxi: requisitos).
- Persistencia en data/clientes.json y data/taxis.json.
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
        """
        Carga datos desde JSON o genera registros iniciales si están vacíos.
        """
        DATA_DIR.mkdir(exist_ok=True)
        self.registro_clientes = self._load_or_gen("clientes.json", self._generar_clientes_fake, 40)
        self.registro_taxis = self._load_or_gen("taxis.json", self._generar_taxis_fake, 30)

    def _load_or_gen(self, fname, gen_fn, n):
        """
        Carga JSON si existe y tiene contenido; si no, genera registros y persiste.
        """
        fp = DATA_DIR / fname
        if not fp.exists() or fp.stat().st_size == 0:
            data = gen_fn(n)
            self._persist(fname, data)
            return data
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except Exception:
            data = gen_fn(n)
            self._persist(fname, data)
            return data

    def _persist(self, fname, payload):
        """Escribe un JSON con indentación para legibilidad."""
        with open(DATA_DIR / fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _generar_clientes_fake(self, n):
        """
        Genera clientes fake con probabilidad de admisión y motivo de rechazo.
        """
        res = []
        for i in range(n):
            nombre = f"Cliente-{i}"
            tarjeta = f"4111-xxxx-{i:04d}"
            admitido = random.random() < 0.85
            motivo = "" if admitido else random.choice(["Tarjeta inválida", "Identidad no verificada"])
            res.append({"id": i, "nombre": nombre, "tarjeta": tarjeta, "estado": "admitido" if admitido else "rechazado", "motivo": motivo})
        return res

    def _generar_taxis_fake(self, n):
        """
        Genera taxis fake con validaciones simuladas y motivo de rechazo.
        """
        res = []
        for i in range(n):
            conductor = f"Conductor-{i}"
            placa = f"UNI-{i:03d}"
            ok_licencia = random.random() < 0.9
            ok_antecedentes = random.random() < 0.95
            ok_medico = random.random() < 0.9
            ok_seguro = random.random() < 0.85
            ok_placa = random.random() < 0.95
            ok_impuestos = random.random() < 0.9
            checks = [ok_licencia, ok_antecedentes, ok_medico, ok_seguro, ok_placa, ok_impuestos]
            admitido = all(checks)
            motivos = []
            if not ok_licencia: motivos.append("Licencia vencida")
            if not ok_antecedentes: motivos.append("Antecedentes penales")
            if not ok_medico: motivos.append("Certificado médico vencido")
            if not ok_seguro: motivos.append("Seguro inválido")
            if not ok_placa: motivos.append("Placa en mal estado")
            if not ok_impuestos: motivos.append("Impuestos no solventes")
            res.append({
                "id": i, "conductor": conductor, "placa": placa,
                "estado": "admitido" if admitido else "rechazado",
                "motivo": ", ".join(motivos) if not admitido else ""
            })
        return res

    # Solicitudes formales (nuevas afiliaciones)
    def solicitar_afiliacion_cliente(self, datos_cliente):
        """
        Evalúa una solicitud de cliente: tarjeta válida y probabilidad de verificación.
        """
        nombre = datos_cliente.get("nombre", "SinNombre")
        tarjeta = datos_cliente.get("tarjeta", "")
        ok_tarjeta = tarjeta.startswith("4") and len(tarjeta) >= 12
        admitido = ok_tarjeta and (random.random() < 0.95)
        motivo = "" if admitido else ("Tarjeta inválida" if not ok_tarjeta else "Identidad no verificada")
        rec = {"id": datos_cliente.get("id"), "nombre": nombre, "tarjeta": tarjeta, "estado": "admitido" if admitido else "rechazado", "motivo": motivo}
        self.registro_clientes.append(rec)
        self._persist("clientes.json", self.registro_clientes)
        return rec

    def solicitar_afiliacion_taxi(self, datos_taxi):
        """
        Evalúa una solicitud de taxi: requisitos simulados (todos deben cumplirse).
        """
        ok_licencia = datos_taxi.get("licencia_vigente", False)
        ok_antecedentes = not datos_taxi.get("antecedentes_penales", True)
        ok_medico = datos_taxi.get("certificado_medico", False)
        ok_seguro = datos_taxi.get("seguro_vigente", False)
        ok_placa = datos_taxi.get("placa_ok", False)
        ok_impuestos = datos_taxi.get("impuestos_solventes", False)
        admitido = all([ok_licencia, ok_antecedentes, ok_medico, ok_seguro, ok_placa, ok_impuestos])
        motivos = []
        if not ok_licencia: motivos.append("Licencia vencida")
        if not ok_antecedentes: motivos.append("Antecedentes penales")
        if not ok_medico: motivos.append("Certificado médico vencido")
        if not ok_seguro: motivos.append("Seguro inválido")
        if not ok_placa: motivos.append("Placa en mal estado")
        if not ok_impuestos: motivos.append("Impuestos no solventes")
        rec = {
            "id": datos_taxi.get("id"),
            "conductor": datos_taxi.get("conductor", f"Conductor-{datos_taxi.get('id')}"),
            "placa": datos_taxi.get("placa", f"UNI-{datos_taxi.get('id'):03d}"),
            "estado": "admitido" if admitido else "rechazado",
            "motivo": ", ".join(motivos) if not admitido else ""
        }
        self.registro_taxis.append(rec)
        self._persist("taxis.json", self.registro_taxis)
        return rec

    # Hooks para integrar con Sistema (no se requiere acción directa aquí)
    def afiliar_clientes_sistema(self, sistema):  # noqa
        pass

    def afiliar_taxis_sistema(self, sistema):  # noqa
        pass
