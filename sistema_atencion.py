# sistema_atencion.py
"""
Núcleo del sistema de atención UNIETAXI.
Gestiona:
- Cola de solicitudes y lista de taxis disponibles (con locks).
- Matching cliente-taxi por distancia y desempate por calificación.
- Asignación de viaje con datos del taxi y ETA.
- Progreso, ETA en tiempo real y finalización con contabilidad (20% empresa).
- Seguimiento de calidad y persistencia en JSON.
- Agregación de calificaciones por taxi y por cliente.
"""

import threading
import time
import random
import json
from queue import Queue
from pathlib import Path
from utils import distancia_euclidiana, calcular_costo_viaje, to_eta, ensure_data_files

DATA_DIR = Path("data")

class SistemaAtencion:
    def __init__(self):
        # Estructuras compartidas
        self.solicitudes = Queue()
        self.taxis_disponibles = []
        self.lock_taxis = threading.Lock()
        self.lock_contabilidad = threading.Lock()
        self.lock_viajes = threading.Lock()

        # Estado del sistema
        self.viajes = []
        self.ganancias_por_taxi = {}
        self.ganancia_empresa = 0.0
        self.rating_taxi = {}  # taxi_id -> (promedio, n)

        # Parámetros
        self.radio_busqueda = 0.2
        self.max_seguimientos_diarios = 5

        # Inicializa archivos
        ensure_data_files()

    # ---------------------------
    # Registro y validación
    # ---------------------------
    def registrar_cliente(self, datos):
        """
        Registra un cliente con validación básica de tarjeta y persiste en clientes.json.
        """
        admitido = datos.get("tarjeta", "").startswith("4") and len(datos.get("tarjeta", "")) >= 12
        rec = {
            "id": datos.get("id"),
            "nombre": datos.get("nombre"),
            "tarjeta": datos.get("tarjeta"),
            "estado": "admitido" if admitido else "rechazado",
            "motivo": "" if admitido else "Tarjeta inválida"
        }
        self._persist_list("clientes.json", rec)
        return rec

    def registrar_taxi(self, datos):
        """
        Registra un taxi con validaciones simuladas (licencia, antecedentes, etc.).
        """
        checks = [
            datos.get("licencia_vigente", False),
            not datos.get("antecedentes_penales", True),
            datos.get("certificado_medico", False),
            datos.get("seguro_vigente", False),
            datos.get("placa_ok", False),
            datos.get("impuestos_solventes", False)
        ]
        admitido = all(checks)
        motivos = []
        if not datos.get("licencia_vigente", False): motivos.append("Licencia vencida")
        if datos.get("antecedentes_penales", False): motivos.append("Antecedentes penales")
        if not datos.get("certificado_medico", False): motivos.append("Certificado médico vencido")
        if not datos.get("seguro_vigente", False): motivos.append("Seguro inválido")
        if not datos.get("placa_ok", False): motivos.append("Placa en mal estado")
        if not datos.get("impuestos_solventes", False): motivos.append("Impuestos no solventes")
        rec = {
            "id": datos.get("id"),
            "conductor": datos.get("conductor"),
            "placa": datos.get("placa"),
            "estado": "admitido" if admitido else "rechazado",
            "motivo": ", ".join(motivos) if not admitido else ""
        }
        self._persist_list("taxis.json", rec)
        return rec

    def _persist_list(self, fname, item):
        """
        Añade un item a un archivo JSON tipo lista (clientes/taxis), creando si es necesario.
        """
        fp = DATA_DIR / fname
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        except Exception:
            data = []
        data.append(item)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Gestión de taxis
    # ---------------------------
    def registrar_taxi_disponible(self, taxi):
        """Agrega el taxi a la lista de disponibles (con exclusión mutua)."""
        with self.lock_taxis:
            if taxi not in self.taxis_disponibles:
                self.taxis_disponibles.append(taxi)

    def desregistrar_taxi_disponible(self, taxi):
        """Elimina el taxi de la lista de disponibles (con exclusión mutua)."""
        with self.lock_taxis:
            if taxi in self.taxis_disponibles:
                self.taxis_disponibles.remove(taxi)

    # ---------------------------
    # Métricas rápidas
    # ---------------------------
    def num_solicitudes(self):
        return self.solicitudes.qsize()

    def viajes_activos(self):
        with self.lock_viajes:
            return len([v for v in self.viajes if v.get("estado") == "activo"])

    def listar_viajes_activos(self):
        with self.lock_viajes:
            return [v for v in self.viajes if v.get("estado") == "activo"]

    # ---------------------------
    # Solicitudes y matching
    # ---------------------------
    def recibir_solicitud(self, cliente):
        """Encola la solicitud del cliente."""
        self.solicitudes.put(cliente)

    def procesar_solicitudes(self):
        """
        Intenta asignar taxis a las solicitudes en cola.
        Reencola si no hay taxis cercanos para evitar bucles vacíos.
        """
        while not self.solicitudes.empty():
            cliente = self.solicitudes.get()
            taxi_asignado = self.seleccionar_taxi_cliente(cliente)
            if taxi_asignado:
                self.asignar_viaje(cliente, taxi_asignado)
                cliente.solicitud_enviada = True
            else:
                self.solicitudes.put(cliente)
                break

    def seleccionar_taxi_cliente(self, cliente):
        """
        Selecciona el taxi más cercano dentro del radio; desempata por calificación del taxi.
        """
        candidatos = []
        with self.lock_taxis:
            for taxi in self.taxis_disponibles:
                if taxi.ocupado:
                    continue
                d = distancia_euclidiana(taxi.ubicacion, cliente.origen)
                if d <= self.radio_busqueda:
                    candidatos.append((d, taxi))
        if not candidatos:
            return None
        candidatos.sort(key=lambda dt: (dt[0], -dt[1].calificacion))
        return candidatos[0][1]

    def asignar_viaje(self, cliente, taxi):
        """
        Crea un viaje activo con datos del taxi y ETA de recogida, y asigna el servicio al taxi.
        """
        taxi.ocupado = True
        self.desregistrar_taxi_disponible(taxi)

        costo = calcular_costo_viaje(cliente.origen, cliente.destino)
        eta_pickup = to_eta(taxi.ubicacion, cliente.origen, velocidad=0.2)
        viaje = {
            "cliente_id": cliente.id_cliente,
            "taxi_id": taxi.id_taxi,
            "origen": cliente.origen,
            "destino": cliente.destino,
            "estado": "activo",
            "inicio_ts": time.time(),
            "costo_estimado": costo,
            "calificacion_cliente": None,
            "placa_taxi": taxi.placa,
            "conductor": taxi.nombre_conductor,
            "eta_pickup": eta_pickup,
            "progreso": 0.0,
            "taxi_calificacion": taxi.calificacion
        }
        with self.lock_viajes:
            self.viajes.append(viaje)
            self.persistir_viajes()

        taxi.asignar_servicio(cliente)
        return {"placa": taxi.placa, "conductor": taxi.nombre_conductor, "eta_pickup": eta_pickup}

    # ---------------------------
    # Progreso y ETA
    # ---------------------------
    def actualizar_progreso(self, taxi, progreso):
        """Actualiza el progreso (0..1) del viaje activo asociado al taxi."""
        with self.lock_viajes:
            for v in self.viajes:
                if v["estado"] == "activo" and v["taxi_id"] == taxi.id_taxi and taxi.cliente_actual and v["cliente_id"] == taxi.cliente_actual.id_cliente:
                    v["progreso"] = max(0.0, min(1.0, progreso))
                    break

    def calcular_eta(self, viaje):
        """
        Calcula ETA restante del trayecto activo:
        - Aproximación con distancia origen->destino y velocidad media 0.24.
        """
        dist_total = distancia_euclidiana(viaje["origen"], viaje["destino"])
        t_total = dist_total / 0.24
        p = viaje.get("progreso", 0.0)
        return max(0.0, (1.0 - p) * t_total)

    # ---------------------------
    # Finalización y contabilidad
    # ---------------------------
    def actualizar_rating_taxi(self, taxi_id, calificacion):
        """Actualiza promedio y cuenta de calificaciones por taxi."""
        prom, n = self.rating_taxi.get(taxi_id, (0.0, 0))
        n2 = n + 1
        prom2 = (prom * n + calificacion) / n2
        self.rating_taxi[taxi_id] = (prom2, n2)

    def finalizar_viaje(self, taxi, cliente, calificacion):
        """
        Finaliza el viaje:
        - Calcula comisiones (20% empresa) y pagos por taxi.
        - Actualiza registro del viaje y libera taxi.
        """
        costo = calcular_costo_viaje(cliente.origen, cliente.destino)
        comision_empresa = costo * 0.20
        pago_taxista = costo - comision_empresa

        # Actualiza contabilidad
        with self.lock_contabilidad:
            self.ganancia_empresa += comision_empresa
            self.ganancias_por_taxi[taxi.id_taxi] = self.ganancias_por_taxi.get(taxi.id_taxi, 0.0) + pago_taxista
            self.persistir_contabilidad()

        # Marca viaje como finalizado
        with self.lock_viajes:
            for v in self.viajes:
                if v["cliente_id"] == cliente.id_cliente and v["taxi_id"] == taxi.id_taxi and v["estado"] == "activo":
                    v["estado"] = "finalizado"
                    v["fin_ts"] = time.time()
                    v["calificacion_cliente"] = calificacion
                    break
            self.persistir_viajes()

        # Métrica de calidad
        self.actualizar_rating_taxi(taxi.id_taxi, calificacion)

        # Libera taxi
        taxi.ocupado = False
        self.registrar_taxi_disponible(taxi)

    # ---------------------------
    # Seguimiento de calidad
    # ---------------------------
    def seguimiento_calidad(self):
        """Marca hasta 5 viajes finalizados como auditados aleatoriamente."""
        with self.lock_viajes:
            finalizados = [v for v in self.viajes if v.get("estado") == "finalizado"]
        if not finalizados:
            return
        seleccion = random.sample(finalizados, k=min(self.max_seguimientos_diarios, len(finalizados)))
        with self.lock_viajes:
            for v in seleccion:
                v["seguimiento_auditoria"] = True
            self.persistir_viajes()

    # ---------------------------
    # Contabilidad y persistencia
    # ---------------------------
    def cierre_contable(self):
        """Persiste el estado contable; pensado para ejecución manual."""
        with self.lock_contabilidad:
            self.persistir_contabilidad()

    def cierre_contable_programado(self):
        """Alias del cierre contable para el scheduler diario."""
        self.cierre_contable()

    def persistir_viajes(self):
        """Guarda el listado de viajes en data/viajes.json."""
        DATA_DIR.mkdir(exist_ok=True)
        with open(DATA_DIR / "viajes.json", "w", encoding="utf-8") as f:
            json.dump(self.viajes, f, ensure_ascii=False, indent=2)

    def persistir_contabilidad(self):
        """Guarda contabilidad en data/contabilidad.json."""
        DATA_DIR.mkdir(exist_ok=True)
        payload = {
            "ganancias_por_taxi": self.ganancias_por_taxi,
            "ganancia_empresa": self.ganancia_empresa,
            "ts": time.time()
        }
        with open(DATA_DIR / "contabilidad.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Agregaciones de calidad
    # ---------------------------
    def agregacion_calidad_por_taxi(self):
        """Devuelve taxi_id -> (promedio, cantidad) usando viajes finalizados."""
        res = {}
        with self.lock_viajes:
            for v in self.viajes:
                if v.get("estado") == "finalizado" and v.get("calificacion_cliente") is not None:
                    tid = v["taxi_id"]
                    prom, n = res.get(tid, (0.0, 0))
                    n2 = n + 1
                    prom2 = (prom * n + v["calificacion_cliente"]) / n2
                    res[tid] = (prom2, n2)
        return res

    def agregacion_calidad_por_cliente(self):
        """Devuelve cliente_id -> (promedio, cantidad) usando viajes finalizados."""
        res = {}
        with self.lock_viajes:
            for v in self.viajes:
                if v.get("estado") == "finalizado" and v.get("calificacion_cliente") is not None:
                    cid = v["cliente_id"]
                    prom, n = res.get(cid, (0.0, 0))
                    n2 = n + 1
                    prom2 = (prom * n + v["calificacion_cliente"]) / n2
                    res[cid] = (prom2, n2)
        return res
